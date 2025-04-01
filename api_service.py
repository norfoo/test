import requests
import json
import os
import time
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

# --- Konfigurace ---
# Načtení API klíče z environment variables
API_KEY = os.environ.get('TWELVE_DATA_API_KEY')
BASE_URL = 'https://api.twelvedata.com'

# Nastavení pro řízení četnosti požadavků
MAX_RETRIES = 3  # Maximální počet pokusů při selhání požadavku
RETRY_DELAY = 2  # Čekání mezi pokusy (v sekundách)
RATE_LIMIT = 8   # Počet kreditů za minutu (Free tier limit)

def get_current_quote(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Získá poslední kotaci pro daný symbol z Twelve Data API.
    
    Args:
        symbol: Ticker symbolu (např. 'EUR/USD', 'AAPL')
        
    Returns:
        Slovník s daty o aktuální kotaci nebo None v případě chyby
    """
    # Zkontrolujeme, zda byl API klíč úspěšně načten
    if not API_KEY:
        print("Chyba: API klíč nebyl nalezen v proměnných prostředí.")
        return None

    endpoint = f"{BASE_URL}/quote"
    params = {
        'symbol': symbol,
        'apikey': API_KEY
    }

    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Chyba při volání API Twelve Data: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print("Odpověď serveru při chybě:", e.response.json())
            except json.JSONDecodeError:
                print("Odpověď serveru při chybě (není JSON):", e.response.text)
        return None
    except Exception as e:
        print(f"Nastala neočekávaná chyba: {e}")
        return None

def get_time_series(symbol: str, interval: str = '1day', outputsize: int = 30) -> Optional[pd.DataFrame]:
    """
    Získá historická data pro daný symbol z Twelve Data API.
    
    Args:
        symbol: Ticker symbolu (např. 'EUR/USD', 'AAPL')
        interval: Časový interval ('1min', '5min', '15min', '30min', '1h', '1day', '1week', '1month')
        outputsize: Počet záznamů, které chceme získat (max 5000)
        
    Returns:
        DataFrame s historickými daty nebo None v případě chyby
    """
    if not API_KEY:
        print("Chyba: API klíč nebyl nalezen v proměnných prostředí.")
        return None

    endpoint = f"{BASE_URL}/time_series"
    params = {
        'symbol': symbol,
        'interval': interval,
        'apikey': API_KEY,
        'outputsize': outputsize
    }
    
    # Implementace opakování pokusů při selhání
    for attempt in range(MAX_RETRIES):
        try:
            print(f"Získávám data pro {symbol} s intervalem {interval} (pokus {attempt+1}/{MAX_RETRIES})")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'values' in data:
                # Převod na DataFrame
                df = pd.DataFrame(data['values'])
                
                # Úprava formátu dat
                df['datetime'] = pd.to_datetime(df['datetime'])
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col])
                
                return df
            else:
                print(f"Chyba: V odpovědi nejsou data. Odpověď API: {data}")
                if 'code' in data and data.get('code') == 429:
                    print(f"Dosažen limit požadavků API. Čekám před dalším pokusem.")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY * 2)  # Delší čekání při limitu
                        continue
                    
                # Pokud nejde o limit požadavků nebo je to poslední pokus
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Chyba při volání API Twelve Data (pokus {attempt+1}/{MAX_RETRIES}): {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print("Odpověď serveru při chybě:", error_data)
                    
                    # Kontrola limitu požadavků
                    if e.response.status_code == 429 or (isinstance(error_data, dict) and error_data.get('code') == 429):
                        print("Dosažen limit požadavků API.")
                        if attempt < MAX_RETRIES - 1:
                            wait_time = RETRY_DELAY * 2
                            print(f"Čekám {wait_time} sekund před dalším pokusem...")
                            time.sleep(wait_time)
                            continue
                except json.JSONDecodeError:
                    print("Odpověď serveru při chybě (není JSON):", e.response.text)
            
            if attempt < MAX_RETRIES - 1:
                print(f"Zkouším znovu za {RETRY_DELAY} sekund...")
                time.sleep(RETRY_DELAY)
            else:
                return None
                
        except Exception as e:
            print(f"Nastala neočekávaná chyba (pokus {attempt+1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                print(f"Zkouším znovu za {RETRY_DELAY} sekund...")
                time.sleep(RETRY_DELAY)
            else:
                return None

def search_symbols(query: str) -> List[Dict[str, str]]:
    """
    Vyhledá symboly odpovídající dotazu pomocí Twelve Data API.
    
    Args:
        query: Dotaz pro vyhledávání (např. 'Apple', 'EUR')
        
    Returns:
        Seznam nalezených symbolů nebo prázdný seznam v případě chyby
    """
    if not API_KEY:
        print("Chyba: API klíč nebyl nalezen v proměnných prostředí.")
        return []

    endpoint = f"{BASE_URL}/symbol_search"
    params = {
        'symbol': query,
        'apikey': API_KEY
    }

    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
            return data['data']
        else:
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Chyba při volání API Twelve Data: {e}")
        return []
    except Exception as e:
        print(f"Nastala neočekávaná chyba: {e}")
        return []

def get_forex_pairs() -> List[Dict[str, str]]:
    """
    Získá seznam dostupných měnových párů.
    
    Returns:
        Seznam dostupných měnových párů nebo prázdný seznam v případě chyby
    """
    if not API_KEY:
        print("Chyba: API klíč nebyl nalezen v proměnných prostředí.")
        return []

    endpoint = f"{BASE_URL}/forex_pairs"
    params = {
        'apikey': API_KEY
    }

    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
            # Omezení počtu párů pro lepší UI
            return data['data'][:20]
        else:
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Chyba při volání API Twelve Data: {e}")
        return []
    except Exception as e:
        print(f"Nastala neočekávaná chyba: {e}")
        return []

def get_stocks() -> List[Dict[str, str]]:
    """
    Získá seznam dostupných akcií.
    
    Returns:
        Seznam dostupných akcií nebo prázdný seznam v případě chyby
    """
    # Použijeme nejběžnější akcie kvůli omezení API
    common_stocks = [
        {"symbol": "AAPL", "name": "Apple Inc.", "currency": "USD", "exchange": "NASDAQ", "mic_code": "XNAS", "country": "United States"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "currency": "USD", "exchange": "NASDAQ", "mic_code": "XNAS", "country": "United States"},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "currency": "USD", "exchange": "NASDAQ", "mic_code": "XNAS", "country": "United States"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "currency": "USD", "exchange": "NASDAQ", "mic_code": "XNAS", "country": "United States"},
        {"symbol": "META", "name": "Meta Platforms Inc.", "currency": "USD", "exchange": "NASDAQ", "mic_code": "XNAS", "country": "United States"},
        {"symbol": "TSLA", "name": "Tesla Inc.", "currency": "USD", "exchange": "NASDAQ", "mic_code": "XNAS", "country": "United States"},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "currency": "USD", "exchange": "NASDAQ", "mic_code": "XNAS", "country": "United States"},
        {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "currency": "USD", "exchange": "NYSE", "mic_code": "XNYS", "country": "United States"},
        {"symbol": "V", "name": "Visa Inc.", "currency": "USD", "exchange": "NYSE", "mic_code": "XNYS", "country": "United States"},
        {"symbol": "JNJ", "name": "Johnson & Johnson", "currency": "USD", "exchange": "NYSE", "mic_code": "XNYS", "country": "United States"},
    ]
    
    return common_stocks

def get_indices() -> List[Dict[str, str]]:
    """
    Získá seznam dostupných indexů.
    
    Returns:
        Seznam dostupných indexů nebo prázdný seznam v případě chyby
    """
    # Použijeme nejběžnější indexy kvůli omezení API
    common_indices = [
        {"symbol": "SPX", "name": "S&P 500", "currency": "USD", "exchange": "CBOE", "mic_code": "XCBO", "country": "United States"},
        {"symbol": "DJI", "name": "Dow Jones Industrial Average", "currency": "USD", "exchange": "DJ", "mic_code": "XDJI", "country": "United States"},
        {"symbol": "IXIC", "name": "NASDAQ Composite", "currency": "USD", "exchange": "NASDAQ", "mic_code": "XNAS", "country": "United States"},
        {"symbol": "N100", "name": "Euronext 100", "currency": "EUR", "exchange": "EURONEXT", "mic_code": "XPAR", "country": "France"},
        {"symbol": "FTSE", "name": "FTSE 100", "currency": "GBP", "exchange": "LSE", "mic_code": "XLON", "country": "United Kingdom"},
        {"symbol": "DAX", "name": "DAX", "currency": "EUR", "exchange": "XETRA", "mic_code": "XETR", "country": "Germany"},
        {"symbol": "FCHI", "name": "CAC 40", "currency": "EUR", "exchange": "EURONEXT", "mic_code": "XPAR", "country": "France"},
        {"symbol": "N225", "name": "Nikkei 225", "currency": "JPY", "exchange": "TSE", "mic_code": "XTKS", "country": "Japan"}
    ]
    
    return common_indices

def get_commodities() -> List[Dict[str, str]]:
    """
    Získá seznam dostupných komodit.
    
    Returns:
        Seznam dostupných komodit nebo prázdný seznam v případě chyby
    """
    # Použijeme nejběžnější komodity dostupné na free plánu Twelve Data API
    common_commodities = [
        {"symbol": "GOLD", "name": "Zlato (GOLD)", "currency": "USD", "exchange": "FOREX", "mic_code": "FOREX", "country": "United States"},
        {"symbol": "SILVER", "name": "Stříbro (SILVER)", "currency": "USD", "exchange": "FOREX", "mic_code": "FOREX", "country": "United States"},
        {"symbol": "COPPER", "name": "Měď (COPPER)", "currency": "USD", "exchange": "COMEX", "mic_code": "XCEC", "country": "United States"},
        {"symbol": "BRENT", "name": "Ropa Brent", "currency": "USD", "exchange": "ICE", "mic_code": "IFEU", "country": "United Kingdom"},
        {"symbol": "WTI", "name": "Ropa WTI", "currency": "USD", "exchange": "NYMEX", "mic_code": "XNYM", "country": "United States"},
        {"symbol": "NATURAL_GAS", "name": "Zemní plyn", "currency": "USD", "exchange": "NYMEX", "mic_code": "XNYM", "country": "United States"},
        {"symbol": "WHEAT", "name": "Pšenice", "currency": "USD", "exchange": "CBOT", "mic_code": "XCBT", "country": "United States"},
        {"symbol": "CORN", "name": "Kukuřice", "currency": "USD", "exchange": "CBOT", "mic_code": "XCBT", "country": "United States"}
    ]
    
    return common_commodities

def get_etfs() -> List[Dict[str, str]]:
    """
    Získá seznam dostupných ETF.
    
    Returns:
        Seznam dostupných ETF nebo prázdný seznam v případě chyby
    """
    # Použijeme nejběžnější ETF kvůli omezení API
    common_etfs = [
        {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "currency": "USD", "exchange": "NYSE", "mic_code": "ARCX", "country": "United States"},
        {"symbol": "QQQ", "name": "Invesco QQQ Trust", "currency": "USD", "exchange": "NASDAQ", "mic_code": "XNAS", "country": "United States"},
        {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF", "currency": "USD", "exchange": "NYSE", "mic_code": "ARCX", "country": "United States"},
        {"symbol": "GLD", "name": "SPDR Gold Shares", "currency": "USD", "exchange": "NYSE", "mic_code": "ARCX", "country": "United States"},
        {"symbol": "VEA", "name": "Vanguard FTSE Developed Markets ETF", "currency": "USD", "exchange": "NYSE", "mic_code": "ARCX", "country": "United States"},
        {"symbol": "VWO", "name": "Vanguard FTSE Emerging Markets ETF", "currency": "USD", "exchange": "NYSE", "mic_code": "ARCX", "country": "United States"}
    ]
    
    return common_etfs

def check_api_key() -> bool:
    """
    Kontroluje, zda je k dispozici API klíč a zda je funkční.
    
    Returns:
        True, pokud je klíč k dispozici a funkční, jinak False
    """
    if not API_KEY:
        return False
        
    # Zkusíme jednoduché volání API
    endpoint = f"{BASE_URL}/time_series"
    params = {
        'symbol': 'AAPL',
        'interval': '1day',
        'apikey': API_KEY,
        'outputsize': 1
    }
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Pokud obsahuje values, předpokládáme, že klíč funguje
        return 'values' in data
    except:
        return False
