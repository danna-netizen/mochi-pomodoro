"""
Genera pomodoro/index.html a partir de page.template.html y los archivos de app/.

Uso:  python build.py

Vuelve a correrlo cada vez que cambies MochiPomodoro.pyw o LEEME.txt:
mete los archivos dentro de la página (en base64) y recalcula las huellas
SHA-256 que se muestran en la sección de seguridad.
"""
import base64
import datetime
import hashlib
import io
import re
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = HERE / "app"
PY = APP / "MochiPomodoro.pyw"
TXT = APP / "LEEME.txt"

SEALS = [
    ("#FF8FB1", "#FFE6EE", "&lt;/&gt;", "Código abierto", "Lo puedes leer completo"),
    ("#6FC7B6", "#DDF5F0", "0", "Cero conexiones", "Funciona sin internet"),
    ("#A98EF0", "#ECE6FD", "✓", "Sin permisos", "Nada de administrador"),
    ("#FF8FB1", "#FFE6EE", "#", "Huella SHA-256", "Publicada y comprobable"),
    ("#6FC7B6", "#DDF5F0", "✿", "Sin instalador", "Ni .exe, ni registro"),
]


def seal_svg(i, color, soft, glyph, title, sub):
    ring = "VERIFICABLE · TRANSPARENTE · MOCHI ✿ POMODORO ·"
    return f"""<div class="seal">
        <svg viewBox="0 0 120 120" role="img" aria-label="Sello: {title}">
          <defs><path id="sp{i}" d="M60,60 m-41,0 a41,41 0 1,1 82,0 a41,41 0 1,1 -82,0"/></defs>
          <circle cx="60" cy="60" r="57" fill="{soft}"/>
          <circle cx="60" cy="60" r="51" fill="none" stroke="{color}" stroke-width="1.5" stroke-dasharray="2 4"/>
          <text font-family="Fredoka, sans-serif" font-size="8" font-weight="600" fill="{color}">
            <textPath href="#sp{i}" textLength="252" lengthAdjust="spacing">{ring}</textPath></text>
          <circle cx="60" cy="60" r="30" fill="#fff" stroke="{color}" stroke-width="2"/>
          <text x="60" y="68" text-anchor="middle" font-family="Fredoka, sans-serif" font-size="22" font-weight="600" fill="{color}">{glyph}</text>
        </svg>
        <b>{title}</b><span>{sub}</span>
      </div>"""


def zip_kb(py_bytes, txt_bytes):
    """Tamaño real del .zip (comprimido) que armará la página."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("MochiPomodoro/MochiPomodoro.pyw", py_bytes)
        z.writestr("MochiPomodoro/LEEME.txt", txt_bytes)
    return max(1, round(len(buf.getvalue()) / 1024))


def main():
    py_bytes, txt_bytes = PY.read_bytes(), TXT.read_bytes()
    version = re.search(r'^VERSION = "([^"]+)"', py_bytes.decode("utf-8"), re.M).group(1)
    today = datetime.date.today()
    months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
              "septiembre", "octubre", "noviembre", "diciembre"]

    values = {
        "VERSION": version,
        "PY_B64": base64.b64encode(py_bytes).decode(),
        "TXT_B64": base64.b64encode(txt_bytes).decode(),
        "SHA_PY": hashlib.sha256(py_bytes).hexdigest(),
        "SHA_TXT": hashlib.sha256(txt_bytes).hexdigest(),
        "SIZE_PY": f"{len(py_bytes):,}",
        "SIZE_KB": zip_kb(py_bytes, txt_bytes),
        "LINES": py_bytes.decode("utf-8").count("\n"),
        "DATE": f"el {today.day} de {months[today.month - 1]} de {today.year}",
        "DATE_ISO": today.isoformat(),
        "SEALS": "\n      ".join(seal_svg(i, *s) for i, s in enumerate(SEALS)),
    }
    html = (HERE / "page.template.html").read_text(encoding="utf-8")
    for key, val in values.items():
        html = html.replace("{{" + key + "}}", str(val))
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if leftover:
        raise SystemExit(f"Faltan valores para: {leftover}")
    (HERE / "index.html").write_text(html, encoding="utf-8", newline="\n")
    print(f"index.html listo  ·  v{version}  ·  SHA-256 .pyw {values['SHA_PY'][:16]}…")


if __name__ == "__main__":
    main()
