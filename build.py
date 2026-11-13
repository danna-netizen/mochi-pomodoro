"""
Builds index.html from page.template.html and the files in app/v1 and app/v2.

Usage:  python build.py

Run it again every time you change anything in app/ or docs/WHATS-NEW-v2.pdf:
it embeds the files in the page (as base64) and recalculates the SHA-256
fingerprints shown in the security section.
"""
import base64
import datetime
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PDF = HERE / "docs" / "WHATS-NEW-v2.pdf"

# key -> (folder, files that go in the .zip, date of the fixed .zip timestamps)
RELEASES = {
    "v1": (HERE / "app" / "v1", ["MochiPomodoro.pyw", "README.txt"], "2026-11-13"),
    "v2": (HERE / "app" / "v2", ["MochiPomodoro.pyw", "README.txt", PDF], None),
}

SEALS = [
    ("#8FB07E", "#E3EDDA", "&lt;/&gt;", "Open source", "You can read all of it"),
    ("#E58FA7", "#FBE6EB", "0", "Zero connections", "Works offline"),
    ("#A48ED6", "#ECE4F7", "✓", "No permissions", "No admin needed"),
    ("#8FB07E", "#E3EDDA", "#", "SHA-256 fingerprint", "Published and checkable"),
    ("#C49A6C", "#F1E2CF", "✿", "No installer", "No .exe, no registry"),
]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]


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


def zip_kb(files):
    """Real size of the (compressed) .zip the page will build."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return max(1, round(len(buf.getvalue()) / 1024))


def pretty(date):
    return f"{MONTHS[date.month - 1]} {date.day}, {date.year}"


def main():
    today = datetime.date.today()
    values = {"SEALS": "\n      ".join(seal_svg(i, *s) for i, s in enumerate(SEALS)), "DATE": pretty(today)}
    js_releases, report = {}, []
    for key, (folder, names, fixed) in RELEASES.items():
        paths = [n if isinstance(n, Path) else folder / n for n in names]
        files = {f"MochiPomodoro/{p.name}": p.read_bytes() for p in paths}
        py = (folder / "MochiPomodoro.pyw").read_bytes()
        version = re.search(r'^VERSION = "([^"]+)"', py.decode("utf-8"), re.M).group(1)
        lines = py.decode("utf-8").count("\n")
        K = key.upper()
        values.update({
            f"{K}_VERSION": version,
            f"{K}_SIZE_KB": zip_kb(files),
            f"{K}_LINES": lines,
        })
        js_releases[key] = {
            "version": version,
            "date": fixed or today.isoformat(),
            "files": {name: base64.b64encode(data).decode() for name, data in files.items()},
        }
        rows = [f'<div class="kv"><dt>{p.name}</dt><dd class="mono">{hashlib.sha256(p.read_bytes()).hexdigest()}</dd></div>'
                for p in paths]
        rows.append(f'<div class="kv"><dt>Program size</dt><dd>{len(py):,} bytes · {lines} lines</dd></div>')
        report.append(f'<div class="rel"><h4>v{version}{" · matcha latte" if key == "v2" else " · classic"}</h4>'
                      f'<dl>\n          ' + "\n          ".join(rows) + "\n        </dl></div>")
    values["RELEASES_JSON"] = json.dumps(js_releases, separators=(",", ":"))
    values["REPORT"] = "\n        ".join(report)

    html = (HERE / "page.template.html").read_text(encoding="utf-8")
    for k, val in values.items():
        html = html.replace("{{" + k + "}}", str(val))
    leftover = re.findall(r"\{\{[A-Z0-9_]+\}\}", html)
    if leftover:
        raise SystemExit(f"Missing values for: {leftover}")
    (HERE / "index.html").write_text(html, encoding="utf-8", newline="\n")
    print(f"index.html ready  ·  v{values['V1_VERSION']} + v{values['V2_VERSION']}")


if __name__ == "__main__":
    main()
