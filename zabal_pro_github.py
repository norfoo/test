"""
Zabalí projekt bota pro nahrání na GitHub (limit 25 MB na soubor).

Použití: zkopíruj tento soubor do hlavní složky bota a spusť
    python zabal_pro_github.py

Vytvoří vedle složky bota složku PRO_GITHUB, ve které bude:
  kod.zip        - všechny malé soubory (kód, reporty .md, konfigurace)
  data_01.zip ...- velké soubory (data, výsledky), každý zip < 24 MB
  obsah.txt      - seznam všech souborů a velikostí
Originální soubory se nijak nemění.
Vynechá: .env, session soubory, klíče, venv, __pycache__, .git, logy.
Telegram tokeny nalezené v kódu v kopii nahradí textem REDACTED.
"""
import os
import re
import sys
import zipfile
from pathlib import Path

LIMIT = 24 * 1024 * 1024          # cílová velikost jednoho zipu
VELKY = 1 * 1024 * 1024           # soubor nad 1 MB jde do dat
SKIP_DIRS = {".git", "venv", ".venv", "env", "__pycache__", "node_modules",
             ".idea", ".vscode", "PRO_GITHUB", ".mypy_cache", ".pytest_cache"}
SKIP_EXT = {".pyc", ".pyo", ".log", ".session", ".session-journal", ".key",
            ".pem", ".p12", ".pfx", ".exe", ".dll"}
TEXT_EXT = {".py", ".md", ".txt", ".toml", ".yaml", ".yml", ".ini", ".cfg",
            ".json", ".mq5", ".mqh", ".mq4", ".pine", ".sh", ".bat", ".ps1",
            ".sql", ".html", ".js", ".csv"}
TG_TOKEN = re.compile(rb"\b\d{8,10}:[A-Za-z0-9_-]{35}\b")
PODEZRELE = re.compile(rb"(password|passwd|heslo|api_key|apikey|secret)\s*[=:]\s*[\"'][^\"']{4,}[\"']", re.I)


def je_tajny(p: Path) -> bool:
    n = p.name.lower()
    if n.startswith(".env") and n != ".env.example":
        return True
    if p.suffix.lower() in SKIP_EXT:
        return True
    return any(k in n for k in ("credential", "secret", "token"))


def main():
    root = Path.cwd()
    out = root.parent / "PRO_GITHUB"
    out.mkdir(exist_ok=True)
    for f in out.glob("*"):
        f.unlink()

    kod, data, vynechano, varovani = [], [], [], []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            rel = p.relative_to(root)
            if p.resolve() == Path(__file__).resolve():
                continue
            if je_tajny(p):
                vynechano.append(rel)
                continue
            size = p.stat().st_size
            if size <= VELKY and p.suffix.lower() in TEXT_EXT:
                kod.append((rel, size))
            elif size <= VELKY and size < 200 * 1024:
                kod.append((rel, size))
            else:
                data.append((rel, size))

    # kód
    with zipfile.ZipFile(out / "kod.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel, _ in kod:
            obsah = (root / rel).read_bytes()
            if TG_TOKEN.search(obsah):
                obsah = TG_TOKEN.sub(b"REDACTED_TELEGRAM_TOKEN", obsah)
                varovani.append(f"{rel}: Telegram token nahrazen v kopii")
            if PODEZRELE.search(obsah):
                varovani.append(f"{rel}: možná heslo/klíč přímo v kódu, zkontroluj")
            z.writestr(str(rel).replace("\\", "/"), obsah)

    # data - od nejmenších, plní zipy do limitu, příliš velké dělí na části
    data.sort(key=lambda x: x[1])
    cislo, z, aktualni = 0, None, 0

    def novy_zip():
        nonlocal cislo, z, aktualni
        if z:
            z.close()
        cislo += 1
        z = zipfile.ZipFile(out / f"data_{cislo:02d}.zip", "w", zipfile.ZIP_LZMA)
        aktualni = 0

    for rel, size in data:
        jmeno = str(rel).replace("\\", "/")
        # odhad po kompresi: zkusíme zapsat a zkontrolovat velikost
        if z is None or aktualni > LIMIT * 0.6:
            novy_zip()
        z.write(root / rel, jmeno)
        z.fp.flush()
        aktualni = (out / f"data_{cislo:02d}.zip").stat().st_size
        if aktualni > LIMIT:
            # tento soubor se nevešel, přesuň ho do vlastního zipu
            z.close()
            _odeber_posledni(out / f"data_{cislo:02d}.zip", jmeno)
            cislo += 1
            cil = out / f"data_{cislo:02d}.zip"
            with zipfile.ZipFile(cil, "w", zipfile.ZIP_LZMA) as zz:
                zz.write(root / rel, jmeno)
            if cil.stat().st_size > LIMIT:
                _rozdel(cil)
            z = None
    if z:
        z.close()

    # obsah
    with open(out / "obsah.txt", "w", encoding="utf-8") as f:
        f.write("=== KOD ===\n")
        for rel, size in sorted(kod):
            f.write(f"{size/1024:10.1f} kB  {rel}\n")
        f.write("\n=== DATA ===\n")
        for rel, size in sorted(data):
            f.write(f"{size/1024/1024:10.1f} MB  {rel}\n")
        f.write("\n=== VYNECHANO (tajne) ===\n")
        for rel in vynechano:
            f.write(f"  {rel}\n")
        f.write("\n=== VAROVANI ===\n")
        for v in varovani:
            f.write(f"  {v}\n")

    print(f"\nHotovo -> {out}")
    for f in sorted(out.iterdir()):
        print(f"  {f.name:22s} {f.stat().st_size/1024/1024:6.1f} MB")
    if vynechano:
        print(f"\nVynecháno {len(vynechano)} tajných souborů (.env, session...), to je správně.")
    for v in varovani:
        print("POZOR:", v)
    print("\nNahraj na GitHub VŠECHNY soubory ze složky PRO_GITHUB.")


def _odeber_posledni(path: Path, jmeno: str):
    tmp = path.with_suffix(".tmp")
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_LZMA) as dst:
        for info in src.infolist():
            if info.filename != jmeno:
                dst.writestr(info, src.read(info.filename))
    tmp.replace(path)
    with zipfile.ZipFile(path) as zz:
        prazdny = not zz.namelist()
    if prazdny:
        path.unlink()


def _rozdel(path: Path):
    raw = path.read_bytes()
    path.unlink()
    for i in range(0, len(raw), LIMIT):
        part = path.with_name(f"{path.name}.part{i // LIMIT + 1}")
        part.write_bytes(raw[i:i + LIMIT])


if __name__ == "__main__":
    if sys.version_info < (3, 6):
        sys.exit("Potřeba Python 3.6+")
    main()
