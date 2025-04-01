import os
import subprocess
import shutil
import time
from pathlib import Path

def create_static_site():
    """
    Vytvoří statickou verzi Streamlit aplikace pomocí streamlit-static-export
    """
    print("Začínám export statické verze dashboardu...")
    
    # Zjistíme, jestli máme nainstalovaný streamlit-static-export
    try:
        subprocess.run(["pip", "install", "streamlit-static-export"], check=True)
        print("Streamlit-static-export byl nainstalován")
    except subprocess.CalledProcessError:
        print("Nepodařilo se nainstalovat streamlit-static-export")
        return False
    
    # Vytvoříme adresář pro statickou verzi, pokud neexistuje
    static_dir = Path("static_site")
    if static_dir.exists():
        shutil.rmtree(static_dir)
    static_dir.mkdir(exist_ok=True)
    
    # Spustíme export
    try:
        # Nastavíme cestu k hlavnímu skriptu
        app_path = "app.py"
        
        # Exportujeme aplikaci
        print("Exportuji aplikaci do statické verze...")
        subprocess.run(
            ["streamlit", "run", app_path, "--browser.serverAddress=localhost", "--server.port=5000"],
            env={**os.environ, "STREAMLIT_STATIC_EXPORT_OUT_DIR": "static_site"},
            timeout=60  # Dáme tomu 60 sekund na export
        )
        
        print("Export dokončen! Statická verze je v adresáři 'static_site'")
        return True
    except Exception as e:
        print(f"Chyba při exportu: {e}")
        return False

if __name__ == "__main__":
    create_static_site()