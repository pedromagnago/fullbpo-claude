#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# assistir_video.sh — baixa um vídeo público (TikTok, Instagram, YouTube,
# Kwai, etc.), extrai a LEGENDA/transcrição e alguns FRAMES para o Claude
# "assistir" o vídeo (ler o que é falado + enxergar o que aparece na tela).
#
# Uso:
#   assistir_video.sh <URL> [pasta_saida] [num_frames]
#
# Saída: imprime um bloco "===== MANIFESTO =====" no final com os caminhos
# absolutos dos arquivos que o Claude deve LER (transcrição, dados e frames).
#
# Variáveis de ambiente opcionais:
#   WHISPER_MODEL   modelo do faster-whisper p/ fallback de áudio (padrão: base)
#   COOKIES_FROM    navegador p/ cookies (ex: chrome) — só p/ vídeo que exige login
# ---------------------------------------------------------------------------
set -uo pipefail

URL="${1:-}"
OUTDIR="${2:-}"
NUM_FRAMES="${3:-6}"
WHISPER_MODEL="${WHISPER_MODEL:-base}"

if [[ -z "$URL" ]]; then
  echo "ERRO: informe a URL do vídeo. Uso: assistir_video.sh <URL> [pasta_saida] [num_frames]" >&2
  exit 2
fi
if [[ -z "$OUTDIR" ]]; then
  OUTDIR="$(mktemp -d 2>/dev/null || echo /tmp/assistir-video-$$)"
fi
mkdir -p "$OUTDIR/frames"
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
  log "Convertendo legenda ($SUB) em texto..."
  python3 - "$SUB" <<'PY'
import sys, re
linhas, ult = [], None
for ln in open(sys.argv[1], encoding="utf-8", errors="ignore"):
    ln = ln.strip()
    if not ln or ln == "WEBVTT" or "-->" in ln or ln.isdigit(): continue
    if ln.startswith(("Kind:","Language:","NOTE")): continue
    ln = re.sub(r"<[^>]+>", "", ln)          # tira tags <c> etc.
    if ln and ln != ult:                     # dedup linhas repetidas seguidas
        linhas.append(ln); ult = ln
open("transcricao.txt","w",encoding="utf-8").write("\n".join(linhas)+"\n")
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

# --- 6. frames uniformemente espaçados --------------------------------------
FRAMES_OK=0
if [[ -n "$CLIP" ]]; then
  DUR="$(python3 -c "import json,glob;d=json.load(open(glob.glob('video.info.json')[0]));print(int(d.get('duration') or 0))" 2>/dev/null || echo 0)"
  [[ "$DUR" -lt 1 ]] && DUR=30
  N="$NUM_FRAMES"; [[ "$N" -lt 1 ]] && N=1
  log "Extraindo $N frames de um vídeo de ${DUR}s..."
  for ((i=0; i<N; i++)); do
    T="$(python3 -c "print(round($DUR*($i+0.5)/$N,1))")"
    IDX="$(printf '%02d' $((i+1)))"
    if "$FF" -ss "$T" -i "$CLIP" -frames:v 1 -q:v 3 -y "frames/frame_${IDX}.jpg" >/dev/null 2>&1; then
      FRAMES_OK=$((FRAMES_OK+1))
    fi
  done
fi

# --- 7. MANIFESTO (o que o Claude deve LER) ---------------------------------
echo ""
echo "===== MANIFESTO ====="
echo "pasta: $OUTDIR"
echo "fonte_transcricao: $TRANSC_FONTE"
[[ -f "$OUTDIR/dados.txt" ]]        && echo "dados: $OUTDIR/dados.txt"
[[ -n "$TRANSC" ]]                  && echo "transcricao: $OUTDIR/$TRANSC"
if [[ "$FRAMES_OK" -gt 0 ]]; then
  echo "frames ($FRAMES_OK):"
  for f in "$OUTDIR"/frames/frame_*.jpg; do [[ -e "$f" ]] && echo "  $f"; done
fi
echo "===== FIM ====="
