import os
import google.generativeai as genai
from typing import Optional, Dict, Any, List

# Načtení API klíče z Replit Secrets
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

def initialize_gemini():
    """
    Inicializuje Gemini API s API klíčem.
    
    Returns:
        bool: True pokud inicializace proběhla úspěšně, jinak False
    """
    if not GEMINI_API_KEY:
        return False
        
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        return True
    except Exception as e:
        print(f"Chyba při inicializaci Gemini API: {e}")
        return False

def check_gemini_api_key() -> bool:
    """
    Kontroluje, zda je k dispozici API klíč pro Gemini a zda je funkční.
    
    Returns:
        True, pokud je klíč k dispozici a funkční, jinak False
    """
    if not GEMINI_API_KEY:
        return False
        
    try:
        # Zkusíme volat jednoduchou operaci s API, abychom ověřili, že klíč funguje
        genai.configure(api_key=GEMINI_API_KEY)
        models = genai.list_models()
        # Pokud se dostaneme sem, API klíč funguje
        return True
    except Exception as e:
        print(f"Chyba při kontrole Gemini API klíče: {e}")
        return False

def get_available_models() -> List[Dict[str, Any]]:
    """
    Získá seznam dostupných Gemini modelů.
    
    Returns:
        Seznam dostupných modelů nebo prázdný seznam v případě chyby
    """
    if not initialize_gemini():
        return []
        
    try:
        models = genai.list_models()
        # Filtrujeme pouze Gemini modely
        gemini_models = [
            {"name": model.name, "display_name": model.display_name, 
             "description": model.description}
            for model in models if "gemini" in model.name.lower()
        ]
        return gemini_models
    except Exception as e:
        print(f"Chyba při získávání dostupných modelů: {e}")
        return []

def get_chat_response(
    messages: List[Dict[str, str]], 
    model_name: str = "gemini-1.5-pro"
) -> Optional[str]:
    """
    Získá odpověď na chat zprávy od Gemini AI.
    
    Args:
        messages: Seznam zpráv ve formátu [{"role": "user", "content": "Zpráva"}, ...]
        model_name: Název modelu Gemini, který se má použít
        
    Returns:
        Odpověď od AI asistenta nebo None v případě chyby
    """
    if not initialize_gemini():
        return None
        
    try:
        # Vytvoříme generativní model
        model = genai.GenerativeModel(model_name)
        
        # Příprava formátu zpráv pro Gemini API
        formatted_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            formatted_messages.append({"role": role, "parts": [msg["content"]]})
        
        # Získáme odpověď
        chat = model.start_chat(history=formatted_messages)
        response = chat.send_message("Odpověz v Českém jazyce. Jsi finanční asistent, který pomáhá s analýzou finančních trhů.")
        
        return response.text
    except Exception as e:
        print(f"Chyba při získávání odpovědi od Gemini: {e}")
        return None

def get_financial_analysis(
    symbol: str, 
    price_data: Dict[str, Any],
    historical_data: Any = None,
    model_name: str = "gemini-1.5-pro"
) -> Optional[str]:
    """
    Získá finanční analýzu a doporučení pro daný symbol od Gemini AI.
    
    Args:
        symbol: Ticker symbolu (např. 'EUR/USD', 'AAPL')
        price_data: Slovník s daty o aktuální kotaci
        historical_data: DataFrame s historickými daty (volitelný)
        model_name: Název modelu Gemini, který se má použít
        
    Returns:
        Finanční analýza od AI asistenta nebo None v případě chyby
    """
    if not initialize_gemini():
        return None
        
    try:
        # Vytvoříme generativní model
        model = genai.GenerativeModel(model_name)
        
        # Sestavíme prompt pro AI
        prompt = f"""
        Proveď finanční analýzu pro {symbol} na základě těchto údajů:
        
        Aktuální cena: {price_data.get('close', price_data.get('price', 'Nedostupná'))}
        Změna: {price_data.get('change', 'Nedostupná')}
        Procentuální změna: {price_data.get('percent_change', 'Nedostupná')}
        
        Poskytni základní analýzu aktuální situace, možné faktory ovlivňující cenu a krátkodobý výhled.
        Zaměř se na informace užitečné pro běžného investora.
        
        Odpověz v českém jazyce a rozděl odpověď do sekcí:
        1. Shrnutí aktuální situace (2-3 věty)
        2. Klíčové faktory ovlivňující cenu (2-3 body)
        3. Krátkodobý výhled (1-2 věty)
        """
        
        # Získáme odpověď
        response = model.generate_content(prompt)
        
        return response.text
    except Exception as e:
        print(f"Chyba při získávání finanční analýzy od Gemini: {e}")
        return None