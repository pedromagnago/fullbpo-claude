#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# assistir_video.sh — baixa um vídeo público (TikTok, Instagram, YouTube,
# Kwai, etc.), extrai a LEGENDA/transcrição e alguns FRAMES para o Claude
# "assistir" o vídeo (ler o que é falado + enxergar o que aparece na tela).
#
# Uso:
#   assistir_video.sh <URL> [pasta_saida] [max_frames]
#
# Saída: imprime um bloco "===== MANIFESTO =====" no final com os caminhos
# absolutos dos arquivos que o Claude deve LER: dados, transcrição (com
# timestamps), frames distintos (frame a frame) e contact sheets.
#
# Variáveis de ambiente opcionais:
#   FPS             amostragem por segundo antes do dedup (padrão: 2)
#   DEDUP           distância de Hamming p/ "tela nova" (padrão: 14; menor = + frames)
#   MAX_FRAMES      teto de frames distintos (padrão: 80; = 3º argumento)
#   WHISPER_MODEL   modelo do faster-whisper p/ fallback de áudio (padrão: base)
#   COOKIES_FROM    navegador p/ cookies (ex: chrome) — só p/ vídeo que exige login
# ---------------------------------------------------------------------------
set -uo pipefail

URL="${1:-}"
OUTDIR="${2:-}"
MAX_FRAMES="${3:-${MAX_FRAMES:-80}}"
FPS="${FPS:-2}"
DEDUP="${DEDUP:-14}"
WHISPER_MODEL="${WHISPER_MODEL:-base}"

if [[ -z "$URL" ]]; then
  echo "ERRO: informe a URL do vídeo. Uso: assistir_video.sh <URL> [pasta_saida] [max_frames]" >&2
  exit 2
fi
if [[ -z "$OUTDIR" ]]; then
  OUTDIR="$(mktemp -d 2>/dev/null || echo /tmp/assistir-video-$$)"
fi
mkdir -p "$OUTDIR/frames" "$OUTDIR/sheets"
cd "$OUTDIR" || { echo "ERRO: não consegui usar a pasta $OUTDIR" >&2; exit 2; }

log(){ echo ">> $*" >&2; }

# --- 1. dependências (instala só o que faltar) ------------------------------
# OBS: NÃO instalar curl_cffi. Ele faz o yt-dlp tentar "impersonation" via TLS,
# que é resetada por proxies de egresso corporativos (curl 35 / connection reset).
# O backend padrão do yt-dlp respeita HTTPS_PROXY e funciona nesses ambientes.
log "Verificando dependências..."
python3 -c "import yt_dlp" 2>/dev/null || pip install -q yt-dlp >&2
python3 -c "import imageio_ffmpeg" 2>/dev/null || pip install -q imageio-ffmpeg >&2

FF="$(python3 -c 'import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())' 2>/dev/null)"
if [[ -z "$FF" ]]; then echo "ERRO: ffmpeg indisponível." >&2; exit 3; fi

YTDLP=(python3 -m yt_dlp)
COOKIE_ARGS=()
[[ -n "${COOKIES_FROM:-}" ]] && COOKIE_ARGS=(--cookies-from-browser "$COOKIES_FROM")

# --- 2. metadados + legendas (todas as línguas, manual e automática) --------
log "Baixando metadados e legendas..."
# nota: cobre códigos de 2 e 3 letras — TikTok usa "por-PT", YouTube usa "pt"
"${YTDLP[@]}" "${COOKIE_ARGS[@]}" \
  --write-info-json --write-subs --write-auto-subs \
  --sub-langs "pt.*,por.*,en.*,eng.*,es.*,spa.*" --sub-format "vtt" \
  --convert-subs vtt --skip-download \
  -o "video.%(ext)s" "$URL" >&2 2>&1 || log "aviso: metadados/legenda parcial ou indisponível"

# --- 3. vídeo (p/ extrair os frames) ----------------------------------------
log "Baixando o vídeo..."
"${YTDLP[@]}" "${COOKIE_ARGS[@]}" -f "mp4/bestvideo*+bestaudio/best" \
  -o "clip.%(ext)s" "$URL" >&2 2>&1 || log "aviso: falha no download do vídeo (segue com legenda/dados)"
CLIP="$(ls clip.* 2>/dev/null | head -1)"

# --- 4. resumo dos dados públicos -------------------------------------------
python3 - <<'PY' >&2 2>/dev/null || true
import json, glob
f = glob.glob("video.info.json")
if not f: raise SystemExit
d = json.load(open(f[0]))
campos = ["title","description","uploader","channel","duration","view_count",
          "like_count","comment_count","repost_count","upload_date","track","webpage_url"]
with open("dados.txt","w") as out:
    for k in campos:
        v = d.get(k)
        if v not in (None,""):
            out.write(f"{k}: {v}\n")
PY

# --- 5. transcrição: legenda -> texto limpo; senão, faster-whisper ----------
SUB="$(ls video*.vtt 2>/dev/null | grep -iE 'pt' | head -1)"
[[ -z "$SUB" ]] && SUB="$(ls video*.vtt 2>/dev/null | head -1)"
TRANSC="transcricao.txt"
TRANSC_FONTE=""

if [[ -n "$SUB" ]]; then
  log "Convertendo legenda ($SUB) em texto (com timestamps)..."
  python3 - "$SUB" <<'PY'
import sys, re
def secs(ts):
    p = ts.replace(",", ".").split(":")
    return round(int(p[0])*3600 + int(p[1])*60 + float(p[2]), 1)
out, last, cur = [], None, None
for ln in open(sys.argv[1], encoding="utf-8", errors="ignore"):
    ln = ln.rstrip("\n")
    m = re.match(r"\s*(\d\d:\d\d:\d\d[.,]\d+)\s*-->", ln)
    if m: cur = secs(m.group(1)); continue
    t = ln.strip()
    if not t or t == "WEBVTT" or t.isdigit(): continue
    if t.startswith(("Kind:", "Language:", "NOTE")): continue
    t = re.sub(r"<[^>]+>", "", t)             # tira tags <c> etc.
    if t and t != last:                       # dedup linhas repetidas seguidas
        out.append(f"[{cur:6.1f}s] {t}" if cur is not None else t); last = t
open("transcricao.txt","w",encoding="utf-8").write("\n".join(out)+"\n")
PY
  TRANSC_FONTE="legenda automática da plataforma ($SUB)"
elif [[ -n "$CLIP" ]]; then
  log "Sem legenda — transcrevendo o áudio com faster-whisper (modelo: $WHISPER_MODEL)..."
  python3 -c "import faster_whisper" 2>/dev/null || pip install -q faster-whisper >&2
  "$FF" -i "$CLIP" -ar 16000 -ac 1 -y audio.wav >/dev/null 2>&1
  python3 - "$WHISPER_MODEL" <<'PY' >&2 2>&1 || log "aviso: transcrição por áudio falhou"
import sys
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[1], device="cpu", compute_type="int8")
segs, info = m.transcribe("audio.wav")
with open("transcricao.txt","w",encoding="utf-8") as out:
    for s in segs:
        out.write(f"[{s.start:6.1f}s] {s.text.strip()}\n")
print("lang detectado:", info.language)
PY
  TRANSC_FONTE="transcrição do áudio (faster-whisper/$WHISPER_MODEL)"
else
  TRANSC_FONTE="(indisponível)"
fi
[[ -f "$TRANSC" ]] || TRANSC=""

# --- 6. frame a frame: amostra densa + dedup por conteúdo -------------------
# Amostra em FPS, calcula um perceptual hash (dhash) por quadro e mantém só
# quando a TELA muda de verdade — ignora tremor de câmera e a mão do criador,
# que enganam o dedup por pixel. Preserva o timestamp de cada frame e gera
# contact sheets (grades) p/ revisão econômica de muitos frames de uma vez.
FRAMES_OK=0
if [[ -n "$CLIP" ]]; then
  log "Analisando frame a frame (fps=$FPS, dedup=$DEDUP, teto=$MAX_FRAMES)..."
  "$FF" -i "$CLIP" -vf "fps=${FPS},scale=9:8,format=gray" -f rawvideo "hashes.gray" 2>/dev/null
  # decide os timestamps das telas distintas (numpy; sem dependência de Pillow)
  python3 - "$FPS" "$DEDUP" "$MAX_FRAMES" > "kept.txt" <<'PY'
import sys, numpy as np
fps = float(sys.argv[1]); th = int(sys.argv[2]); mx = int(sys.argv[3])
d = np.fromfile("hashes.gray", dtype=np.uint8); n = d.size // 72
if n == 0: sys.exit(0)
fr = d[:n*72].reshape(n, 8, 9).astype(np.int16)
def dh(f):
    v = 0
    for b in (f[:, :8] < f[:, 1:]).flatten(): v = (v << 1) | int(b)
    return v
H = [dh(fr[i]) for i in range(n)]
ham = lambda a, b: bin(a ^ b).count("1")
kept = [0]
for i in range(1, n):
    if ham(H[i], H[kept[-1]]) >= th: kept.append(i)
if len(kept) > mx:                        # teto: rareia uniformemente e avisa
    orig = len(kept); step = orig / mx
    kept = [kept[int(k*step)] for k in range(mx)]
    sys.stderr.write(f">> aviso: {orig} telas distintas rareadas p/ MAX_FRAMES={mx}\n")
for i in kept: print(round(i/fps, 1))
PY
  # extrai cada frame distinto em resolução cheia, nomeado pelo timestamp
  IDX=0
  while read -r T; do
    [[ -z "$T" ]] && continue
    IDX=$((IDX+1))
    NAME="frame_$(printf '%03d' "$IDX")_$(printf 't%06.1fs' "$T").jpg"
    if "$FF" -ss "$T" -i "$CLIP" -frames:v 1 -q:v 3 -y "frames/$NAME" >/dev/null 2>&1; then
      FRAMES_OK=$((FRAMES_OK+1))
      printf '%s\tt=%ss\n' "$NAME" "$T" >> "frames/index.txt"
    fi
  done < "kept.txt"
  # contact sheets 4x4 na ordem cronológica (leia primeiro p/ ter a visão geral)
  if [[ "$FRAMES_OK" -gt 0 ]]; then
    "$FF" -framerate 1 -pattern_type glob -i "frames/frame_*.jpg" \
          -vf "scale=360:-1,tile=4x4:padding=6:color=white" -q:v 4 \
          "sheets/contato_%02d.jpg" >/dev/null 2>&1 || true
  fi
fi

# --- 7. MANIFESTO (o que o Claude deve LER) ---------------------------------
echo ""
echo "===== MANIFESTO ====="
echo "pasta: $OUTDIR"
echo "fonte_transcricao: $TRANSC_FONTE"
[[ -f "$OUTDIR/dados.txt" ]] && echo "dados: $OUTDIR/dados.txt"
[[ -n "$TRANSC" ]]           && echo "transcricao: $OUTDIR/$TRANSC  (com timestamps)"
if [[ "$FRAMES_OK" -gt 0 ]]; then
  echo "frames_distintos: $FRAMES_OK"
  echo "index: $OUTDIR/frames/index.txt  (frame -> timestamp, em ordem)"
  echo "frames_dir: $OUTDIR/frames/  (leia frames individuais p/ detalhe: números, textos)"
  echo "contact_sheets (LEIA PRIMEIRO — ordem cronológica):"
  for s in "$OUTDIR"/sheets/contato_*.jpg; do [[ -e "$s" ]] && echo "  $s"; done
fi
echo "===== FIM ====="
