#!/usr/bin/env python3
"""Prepara um vídeo para o Claude "assistir": baixa, extrai frames e áudio.

O Claude não processa vídeo direto, mas LÊ imagens. Então este script quebra o
vídeo em frames (imagens) que o Claude lê com a ferramenta Read, e opcionalmente
transcreve o áudio (faster-whisper, 100% local). Serve para Reel/Story do
Instagram, YouTube, TikTok, vídeo de WhatsApp, link .mp4 direto ou arquivo local.

Uso:
    python3 ver_video.py "<url-ou-arquivo>" [--out PASTA] [--frames N] [--transcrever]

Saída: imprime um manifesto (pasta, duração, lista de frames, áudio) e, se pedido,
a transcrição. Depois o Claude lê os frames listados.

Dependências (auto-instaladas na 1ª vez): yt-dlp, imageio-ffmpeg.
Para --transcrever: faster-whisper (baixa um modelo ~140 MB na 1ª vez).
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import subprocess
import sys
import tempfile


def _garantir(pacote: str, modulo: str) -> None:
    """Importa `modulo`; se faltar, instala `pacote` via pip e tenta de novo."""
    try:
        __import__(modulo)
    except ImportError:
        print(f"[setup] instalando {pacote}...", file=sys.stderr)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet",
             "--disable-pip-version-check", pacote],
            check=True,
        )
        __import__(modulo)


def _ffmpeg() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _duracao_seg(ffmpeg: str, arquivo: str) -> float:
    """Lê a duração (s) parseando o stderr do ffmpeg. 0.0 se não achar."""
    out = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", arquivo],
        capture_output=True, text=True,
    ).stderr
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", out)
    if not m:
        return 0.0
    h, mm, ss = m.groups()
    return int(h) * 3600 + int(mm) * 60 + float(ss)


def _baixar(url: str, pasta: str) -> str:
    """Baixa o vídeo com yt-dlp. Devolve o caminho do arquivo baixado."""
    alvo = os.path.join(pasta, "source.%(ext)s")
    print(f"[download] {url}", file=sys.stderr)
    subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--no-playlist", "--no-warnings",
         "-o", alvo, url],
        check=True,
    )
    achados = [f for f in glob.glob(os.path.join(pasta, "source.*"))
               if not f.endswith((".part", ".ytdl"))]
    if not achados:
        raise SystemExit("Falhou: nada baixado (vídeo privado? exige login?).")
    return max(achados, key=os.path.getsize)


def _extrair_frames(ffmpeg: str, arquivo: str, pasta: str,
                    alvo_frames: int, dur: float) -> list[str]:
    frames_dir = os.path.join(pasta, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    # intervalo escolhido p/ render ~alvo_frames imagens, seja qual for a duração
    intervalo = max(1, round(dur / alvo_frames)) if dur > 0 else 2
    subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", arquivo,
         "-vf", f"fps=1/{intervalo},scale=480:-1", "-frames:v", "80",
         "-q:v", "3", os.path.join(frames_dir, "f_%03d.jpg")],
        check=True,
    )
    return sorted(glob.glob(os.path.join(frames_dir, "f_*.jpg")))


def _extrair_audio(ffmpeg: str, arquivo: str, pasta: str) -> str | None:
    audio = os.path.join(pasta, "audio.mp3")
    r = subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", arquivo,
         "-vn", "-ac", "1", "-ar", "16000", "-q:a", "5", audio],
        capture_output=True,
    )
    return audio if r.returncode == 0 and os.path.exists(audio) else None


def _transcrever(audio: str) -> None:
    _garantir("faster-whisper", "faster_whisper")
    from faster_whisper import WhisperModel
    print("[transcrição] carregando modelo base (local)...", file=sys.stderr)
    modelo = WhisperModel("base", device="cpu", compute_type="int8")
    segmentos, info = modelo.transcribe(audio, beam_size=1, vad_filter=True)
    print(f"\n=== TRANSCRIÇÃO (idioma: {info.language}) ===")
    corrido = []
    for s in segmentos:
        print(f"[{s.start:6.1f}s] {s.text.strip()}")
        corrido.append(s.text.strip())
    print("\n--- texto corrido ---")
    print(" ".join(corrido))


def main() -> None:
    ap = argparse.ArgumentParser(description="Prepara vídeo p/ o Claude assistir.")
    ap.add_argument("entrada", help="URL do vídeo ou caminho de arquivo local")
    ap.add_argument("--out", default=None, help="pasta de saída (padrão: temp)")
    ap.add_argument("--frames", type=int, default=30,
                    help="nº aproximado de frames a extrair (padrão: 30)")
    ap.add_argument("--transcrever", action="store_true",
                    help="também transcrever o áudio (faster-whisper local)")
    args = ap.parse_args()

    _garantir("yt-dlp", "yt_dlp")
    _garantir("imageio-ffmpeg", "imageio_ffmpeg")
    ffmpeg = _ffmpeg()

    pasta = args.out or tempfile.mkdtemp(prefix="assistir-video-")
    os.makedirs(pasta, exist_ok=True)

    if os.path.exists(args.entrada):
        arquivo = args.entrada
    else:
        arquivo = _baixar(args.entrada, pasta)

    dur = _duracao_seg(ffmpeg, arquivo)
    frames = _extrair_frames(ffmpeg, arquivo, pasta, args.frames, dur)
    audio = _extrair_audio(ffmpeg, arquivo, pasta)

    print("\n=== MANIFESTO ===")
    print(f"pasta:    {pasta}")
    print(f"vídeo:    {arquivo}")
    print(f"duração:  {dur:.1f}s")
    print(f"frames:   {len(frames)}")
    print(f"áudio:    {audio or '(sem faixa de áudio)'}")
    print("\n=== FRAMES (leia estes com a ferramenta Read) ===")
    for f in frames:
        print(f)

    if args.transcrever:
        if audio:
            _transcrever(audio)
        else:
            print("\n[transcrição] pulada: vídeo sem áudio.", file=sys.stderr)


if __name__ == "__main__":
    main()
