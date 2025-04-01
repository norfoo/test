import os
import subprocess
import time
import shutil
from pathlib import Path

def create_static_site():
    """
    Vytvoří statickou verzi dashboardu pomocí metody stahování HTML
    """
    print("Začínám export statické verze dashboardu...")
    
    # Vytvoříme adresář pro statickou verzi, pokud neexistuje
    static_dir = Path("static_site")
    if static_dir.exists():
        print("Mažu předchozí verzi...")
        shutil.rmtree(static_dir)
    
    print("Vytvářím adresář pro statickou verzi...")
    static_dir.mkdir(exist_ok=True)
    
    # Zkontrolujeme, zda je workflow spuštěný, pokud ne, spustíme ho
    try:
        # Spustíme aplikaci - nespouštíme znovu, pokud už běží
        subprocess.run(["wget", "--spider", "http://localhost:5000"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Dashboard již běží na portu 5000")
        app_process = None
    except subprocess.CalledProcessError:
        print("Spouštím dashboard na pozadí...")
        app_process = subprocess.Popen(["streamlit", "run", "app.py", "--server.port=5000"])
        # Počkáme, až se server spustí
        time.sleep(10)
    
    try:
        # Stáhneme HTML a další soubory pomocí wget
        print("Stahuji statickou verzi...")
        subprocess.run([
            "wget",
            "--recursive",
            "--no-clobber",
            "--page-requisites",
            "--html-extension",
            "--convert-links",
            "--restrict-file-names=windows",
            "--domains=localhost",
            "--no-parent",
            "http://localhost:5000"
        ], cwd=static_dir, check=True)
        
        # Vytvoříme index.html s odkazem na staženou stránku
        index_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0;url=localhost:5000/index.html">
    <title>Finanční Dashboard</title>
</head>
<body>
    <p>Přesměrování na <a href="localhost:5000/index.html">dashboard</a>.</p>
</body>
</html>"""
        
        with open(static_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(index_content)
        
        # Vytvoříme tar.gz archiv statické verze
        print("Vytvářím komprimovaný archiv...")
        shutil.make_archive("financni-dashboard-web", "gztar", "static_site")
        
        print("Export dokončen! Statická verze je v adresáři 'static_site' a archivu 'financni-dashboard-web.tar.gz'")
        return True
        
    except Exception as e:
        print(f"Chyba při exportu: {e}")
        return False
    finally:
        # Ukončíme aplikaci, pokud jsme ji spustili
        if app_process is not None:
            print("Ukončuji dashboard...")
            app_process.terminate()
            app_process.wait()

if __name__ == "__main__":
    create_static_site()