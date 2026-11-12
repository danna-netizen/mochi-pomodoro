"""
Builds index.html from page.template.html and the files in app/.

Usage:  python build.py

Run it again every time you change MochiPomodoro.pyw or README.txt:
it embeds the files in the page (as base64) and recalculates the SHA-256
fingerprints shown in the security section.
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
TXT = APP / "README.txt"

SEALS = [
    ("#FF8FB1", "#FFE6EE", "&lt;/&gt;", "Open source", "You can read all of it"),
    ("#6FC7B6", "#DDF5F0", "0", "Zero connections", "Works offline"),
    ("#A98EF0", "#ECE6FD", "✓", "No permissions", "No admin needed"),
    ("#FF8FB1", "#FFE6EE", "#", "SHA-256 fingerprint", "Published and checkable"),
    ("#6FC7B6", "#DDF5F0", "✿", "No installer", "No .exe, no registry"),
]


def seal_svg(i, color, soft, glyph, title, sub):
    ring = "VERIFIABLE · TRANSPARENT · MOCHI ✿ POMODORO ·"
    return f"""<div class="seal">
        <svg viewBox="0 0 120 120" role="img" aria-label="Seal: {title}">
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
    """Real size of the (compressed) .zip the page will build."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("MochiPomodoro/MochiPomodoro.pyw", py_bytes)
        z.writestr("MochiPomodoro/README.txt", txt_bytes)
    return max(1, round(len(buf.getvalue()) / 1024))


def main():
    py_bytes, txt_bytes = PY.read_bytes(), TXT.read_bytes()
    version = re.search(r'^VERSION = "([^"]+)"', py_bytes.decode("utf-8"), re.M).group(1)
    today = datetime.date.today()
    months = ["January", "February", "March", "April", "May", "June", "July", "August",
              "September", "October", "November", "December"]

    values = {
        "VERSION": version,
        "PY_B64": base64.b64encode(py_bytes).decode(),
        "TXT_B64": base64.b64encode(txt_bytes).decode(),
        "SHA_PY": hashlib.sha256(py_bytes).hexdigest(),
        "SHA_TXT": hashlib.sha256(txt_bytes).hexdigest(),
        "SIZE_PY": f"{len(py_bytes):,}",
        "SIZE_KB": zip_kb(py_bytes, txt_bytes),
        "LINES": py_bytes.decode("utf-8").count("\n"),
        "DATE": f"on {months[today.month - 1]} {today.day}, {today.year}",
        "DATE_ISO": today.isoformat(),
        "SEALS": "\n      ".join(seal_svg(i, *s) for i, s in enumerate(SEALS)),
    }
    html = (HERE / "page.template.html").read_text(encoding="utf-8")
    for key, val in values.items():
        html = html.replace("{{" + key + "}}", str(val))
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if leftover:
        raise SystemExit(f"Missing values for: {leftover}")
    (HERE / "index.html").write_text(html, encoding="utf-8", newline="\n")
    print(f"index.html ready  ·  v{version}  ·  SHA-256 .pyw {values['SHA_PY'][:16]}…")


if __name__ == "__main__":
    main()
