import os
import google.generativeai as genai
from typing import Optional, Dict, Any, List
import time
import pandas as pd

# Načtení API klíče z Replit Secrets
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Nastavení pro řízení četnosti požadavků a opakování při chybách
MAX_RETRIES = 3
RETRY_DELAY = 2  # sekundy mezi pokusy

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
    
    # Implementace opakování pokusů při selhání    
    for attempt in range(MAX_RETRIES):
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
            response = chat.send_message("Odpověz v Českém jazyce. Jsi finanční asistent, který pomáhá s analýzou finančních trhů a komodit. Zaměřuješ se na analýzu zlata (GOLD, XAU/USD), měnových párů a dalších finančních instrumentů.")
            
            return response.text
        except Exception as e:
            print(f"Chyba při získávání odpovědi od Gemini (pokus {attempt+1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                print(f"Zkouším znovu za {RETRY_DELAY} sekund...")
                time.sleep(RETRY_DELAY)
            else:
                return None

def get_financial_analysis(
    symbol: str, 
    price_data: Dict[str, Any],
    historical_data: Any = None,
    model_name: str = "gemini-1.5-pro"
) -> Optional[str]:
    """
    Získá finanční analýzu a doporučení pro daný symbol od Gemini AI.
    Nyní používá pouze reálná data a poskytuje konkrétní obchodní signály.
    
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
    
    # Implementace opakování pokusů při selhání    
    for attempt in range(MAX_RETRIES):
        try:
            # Vytvoříme generativní model
            model = genai.GenerativeModel(model_name)
            
            # Určení typu instrumentu pro lepší analýzu
            instrument_type = "komodita"
            if symbol == "I:XAUUSD" or symbol == "GOLD" or symbol == "XAU/USD":
                instrument_type = "zlato"
            elif symbol == "I:XAGUSD" or symbol == "SILVER" or symbol == "XAG/USD":
                instrument_type = "stříbro"
            elif "/" in symbol:
                instrument_type = "měnový pár"
            elif symbol in ["AAPL", "MSFT", "GOOG", "AMZN"]:
                instrument_type = "akcie"
            
            # Aktuální cena a základní údaje
            current_price = price_data.get('close', price_data.get('price', 0))
            
            # Sestavíme detailní prompt s reálnými daty pro AI
            prompt = f"""
            Jsi profesionální obchodník a finanční analytik se zaměřením na trhy.
            Poskytni detailní analýzu s konkrétními obchodními signály pro {symbol} ({instrument_type}).
            
            Aktuální reálná data:
            - Aktuální cena: {current_price} {price_data.get('currency', 'USD')}
            - Změna: {price_data.get('percent_change', 0)}%
            - Otevírací cena: {price_data.get('open', 0)}
            - Nejvyšší cena: {price_data.get('high', 0)}
            - Nejnižší cena: {price_data.get('low', 0)}
            - Předchozí zavírací cena: {price_data.get('previous_close', 0)}
            - Datum/čas: {price_data.get('datetime', 'Není k dispozici')}
            """
            
            # Přidání historických dat, pokud jsou k dispozici
            if historical_data is not None and not historical_data.empty:
                # Získáme více záznamů pro lepší analýzu
                max_rows = 30
                
                # Získáme nejnovější záznamy
                recent_data = historical_data.tail(max_rows)
                
                prompt += """
                Poslední historická data (nejnovější nahoře):
                """
                
                # Přidání historických dat
                data_lines = []
                for index, row in recent_data.iterrows():
                    # Ošetření správného formátu datumu (může být ve sloupci 'date' nebo 'datetime')
                    date_str = ""
                    if 'date' in row and pd.notna(row['date']):
                        if isinstance(row['date'], str):
                            date_str = row['date']
                        else:
                            try:
                                date_str = row['date'].strftime('%Y-%m-%d %H:%M')
                            except:
                                date_str = str(row['date'])
                    elif 'datetime' in row and pd.notna(row['datetime']):
                        if isinstance(row['datetime'], str):
                            date_str = row['datetime']
                        else:
                            try:
                                date_str = row['datetime'].strftime('%Y-%m-%d %H:%M')
                            except:
                                date_str = str(row['datetime'])
                    else:
                        date_str = "N/A"
                    
                    # Formátování datového řádku
                    data_lines.append(f"{date_str}: O: {row['open']:.2f}, H: {row['high']:.2f}, L: {row['low']:.2f}, C: {row['close']:.2f}, Vol: {row.get('volume', 'N/A')}")
                
                prompt += "\n".join(reversed(data_lines[-20:]))  # Posledních 20 řádků v opačném pořadí (nejnovější nahoře)
                    
                # Výpočet některých technických indikátorů
                # Průměrná změna za posledních N období
                if len(historical_data) > 1:
                    price_changes = historical_data['close'].pct_change().dropna()
                    avg_change = price_changes.mean() * 100
                    volatility = price_changes.std() * 100
                    
                    # Výpočet klíčových úrovní podpory a odporu
                    last_price = historical_data['close'].iloc[-1]
                    recent_highs = historical_data['high'].tail(30)
                    recent_lows = historical_data['low'].tail(30)
                    
                    # Najdeme lokální maxima a minima
                    resistance_levels = sorted([price for price in recent_highs if price > last_price])[:3]
                    support_levels = sorted([price for price in recent_lows if price < last_price], reverse=True)[:3]
                    
                    prompt += f"""
                    Technické ukazatele (5-minutový timeframe):
                    - Průměrná procentuální změna: {avg_change:.4f}%
                    - Volatilita (směrodatná odchylka): {volatility:.4f}%
                    """
                    
                    # Přidání úrovní podpory a odporu
                    if resistance_levels:
                        prompt += f"- Úrovně odporu (resistance): {', '.join([f'{level:.2f}' for level in resistance_levels])}\n"
                    if support_levels:
                        prompt += f"- Úrovně podpory (support): {', '.join([f'{level:.2f}' for level in support_levels])}\n"
                    
                    # Přidání SMA a EMA, pokud jsou k dispozici
                    if 'sma_20' in historical_data.columns and 'sma_50' in historical_data.columns:
                        latest = historical_data.iloc[-1]
                        prompt += f"""
                        - SMA 20: {latest['sma_20']:.2f}
                        - SMA 50: {latest['sma_50']:.2f}
                        - SMA křížení: {"SMA 20 nad SMA 50 (býčí)" if latest['sma_20'] > latest['sma_50'] else "SMA 50 nad SMA 20 (medvědí)"}
                        """
                    
                    if 'ema_20' in historical_data.columns and 'ema_50' in historical_data.columns:
                        latest = historical_data.iloc[-1]
                        prompt += f"""
                        - EMA 20: {latest['ema_20']:.2f}
                        - EMA 50: {latest['ema_50']:.2f}
                        - EMA křížení: {"EMA 20 nad EMA 50 (býčí)" if latest['ema_20'] > latest['ema_50'] else "EMA 50 nad EMA 20 (medvědí)"}
                        """
                    
                    # RSI pokud je k dispozici
                    if 'rsi_14' in historical_data.columns:
                        latest = historical_data.iloc[-1]
                        prompt += f"""
                        - RSI(14): {latest['rsi_14']:.2f} ({"Překoupený" if latest['rsi_14'] > 70 else "Přeprodaný" if latest['rsi_14'] < 30 else "Neutrální"})
                        """
            
            # Instrukce pro detailní analýzu s konkrétními obchodními signály
            prompt += """
            Poskytni následující analýzu pro 5-minutový timeframe:
            
            1. Shrnutí aktuální situace na trhu
            2. Detailní technická analýza:
               - Identifikace hlavního trendu
               - Přesné úrovně podpory a odporu
               - Klíčové cenové formace (svíčkové vzory, trojúhelníky, hlavy a ramena, apod.)
               - Momentové indikátory a divergence
            
            3. KONKRÉTNÍ OBCHODNÍ SIGNÁLY PRO 5M TIMEFRAME:
               - Doporučení pro NÁKUP nebo PRODEJ, případně VYČKÁNÍ
               - PŘESNÁ vstupní cena
               - PŘESNÁ cena pro stoploss
               - PŘESNÉ cíle pro zisk (take profit 1, 2, 3)
               - Výpočet poměru rizika k zisku (Risk:Reward ratio) - VŽDY DOPORUČUJ POUZE OBCHODY S POMĚREM RIZIKA K ZISKU MINIMÁLNĚ 1:2,5
            
            4. Rizikové faktory, které mohou ovlivnit tento obchod
            
            Formátuj výstup pomocí markdown a používej vhodné nadpisy a odrážky pro přehlednost.
            Odpověz v češtině. Buď konkrétní a přesný, zejména v číslech pro vstup, stoploss a take profit.
            Nezapomeň, že analýza je pro 5-minutový timeframe a obchodník potřebuje přesné hodnoty, ne obecná doporučení.
            
            DŮLEŽITÉ: Doporučuj POUZE obchody, které mají MINIMÁLNÍ poměr rizika k zisku 1:2,5. Pokud aktuální situace neumožňuje takový poměr, doporuč VYČKÁNÍ na lepší příležitost a vysvětli, na jaké cenové úrovně čekat.
            """
            
            # Získáme odpověď
            response = model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            print(f"Chyba při získávání finanční analýzy od Gemini (pokus {attempt+1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                print(f"Zkouším znovu za {RETRY_DELAY} sekund...")
                time.sleep(RETRY_DELAY)
            else:
                return None