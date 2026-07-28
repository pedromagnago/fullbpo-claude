#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# montar_pdf.py — gera o DOSSIÊ em PDF a partir do mesmo central.json da Central.
# A Central (HTML de abas com iframes) não imprime bem inteira; então aqui a
# gente imprime CADA peça (as abas "embed") separada via Chromium headless e
# junta tudo num PDF único, na ordem das abas, com marcadores por seção.
#
# Uso:
#   python3 montar_pdf.py <central.json> [saida.pdf]
#
# Requisitos: Chromium (headless) + pypdf.
#   - Chromium: define FULLBPO_CHROME=/caminho/chromium, ou o script procura
#     nos nomes/paths comuns (inclui /opt/pw-browsers/chromium).
#   - pip install pypdf
# Motivo: entregar o relatório sem depender de publicar/compartilhar artifact.
# ---------------------------------------------------------------------------
import sys, os, json, shutil, subprocess, tempfile

def achar_chrome():
    c = os.environ.get("FULLBPO_CHROME")
    if c and os.path.exists(c): return c
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome"):
        p = shutil.which(name)
        if p: return p
    for p in ("/opt/pw-browsers/chromium", "/usr/bin/chromium", "/usr/bin/chromium-browser",
              "/usr/bin/google-chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if os.path.exists(p): return p
    raise SystemExit("ERRO: Chromium não encontrado. Defina FULLBPO_CHROME=/caminho/para/chromium.")

def imprimir(chrome, html_path, pdf_path, timeout=180):
    cmd = [chrome, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
           "--run-all-compositor-stages-before-draw", f"--print-to-pdf={pdf_path}",
           "file://" + os.path.abspath(html_path)]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
    return os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0

def main():
    if len(sys.argv) < 2:
        print("uso: montar_pdf.py <central.json> [saida.pdf]"); sys.exit(2)
    central = sys.argv[1]
    d = json.load(open(central, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(central))
    out = sys.argv[2] if len(sys.argv) > 2 else "central.pdf"
    try:
        from pypdf import PdfWriter, PdfReader
    except ImportError:
        raise SystemExit("ERRO: pypdf não instalado. Rode: pip install pypdf")

    chrome = achar_chrome()
    tabs = [t for t in d.get("tabs", []) if t.get("tipo", "embed") == "embed" and t.get("src")]
    if not tabs:
        raise SystemExit("ERRO: central.json não tem abas 'embed' com src.")

    writer = PdfWriter()
    total, feitas = 0, 0
    with tempfile.TemporaryDirectory() as tmp:
        for i, t in enumerate(tabs):
            src = os.path.join(base, t["src"])
            if not os.path.exists(src):
                print(f"  aviso: pula '{t.get('label')}' — arquivo não achado: {t['src']}"); continue
            pdf_i = os.path.join(tmp, f"{i:02d}.pdf")
            if not imprimir(chrome, src, pdf_i):
                print(f"  aviso: falha ao imprimir '{t.get('label')}'"); continue
            r = PdfReader(pdf_i); n = len(r.pages)
            for p in r.pages: writer.add_page(p)
            writer.add_outline_item(t.get("label", f"Seção {i+1}"), total)
            total += n; feitas += 1
            print(f"  ✓ {t.get('label'):<28} {n} págs")

    if feitas == 0:
        raise SystemExit("ERRO: nenhuma aba foi impressa.")
    writer.add_metadata({"/Title": f"{d.get('cliente','Dossiê')} — {d.get('subtitulo','')}".strip(" —"),
                         "/Author": "FullBPO"})
    with open(out, "wb") as fh: writer.write(fh)
    print(f">> {out}: {total} páginas de {feitas} seções ({os.path.getsize(out)//1024} KB)")

if __name__ == "__main__":
    main()
