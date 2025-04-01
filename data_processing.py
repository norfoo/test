import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

def format_quote_data(quote_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formátuje data o aktuální kotaci pro zobrazení.
    
    Args:
        quote_data: Slovník s daty o kotaci z API
        
    Returns:
        Formátovaný slovník s daty o kotaci
    """
    if not quote_data:
        return {}
    
    # Získání nejdůležitějších hodnot
    formatted_data = {
        'symbol': quote_data.get('symbol', ''),
        'name': quote_data.get('name', ''),
        'exchange': quote_data.get('exchange', ''),
        'currency': quote_data.get('currency', ''),
        'open': quote_data.get('open', ''),
        'high': quote_data.get('high', ''),
        'low': quote_data.get('low', ''),
        'close': quote_data.get('close', ''),
        'previous_close': quote_data.get('previous_close', ''),
        'change': quote_data.get('change', ''),
        'percent_change': quote_data.get('percent_change', ''),
        'fifty_two_week': {
            'low': quote_data.get('fifty_two_week', {}).get('low', '') if 'fifty_two_week' in quote_data else '',
            'high': quote_data.get('fifty_two_week', {}).get('high', '') if 'fifty_two_week' in quote_data else '',
        },
        'datetime': quote_data.get('datetime', '')
    }
    
    return formatted_data

def format_numeric_value(value: str) -> str:
    """
    Formátuje číselné hodnoty pro zobrazení.
    
    Args:
        value: Hodnota k formátování
        
    Returns:
        Formátovaná hodnota
    """
    try:
        # Zkusíme převést na float a formátovat
        float_value = float(value)
        if float_value > 1000:
            return f"{float_value:,.2f}".replace(",", " ").replace(".", ",")
        elif float_value > 0:
            # Přizpůsobíme počet desetinných míst podle velikosti čísla
            if float_value < 0.01:
                return f"{float_value:.6f}".replace(".", ",")
            elif float_value < 0.1:
                return f"{float_value:.4f}".replace(".", ",")
            else:
                return f"{float_value:.2f}".replace(".", ",")
        else:
            return value
    except:
        # Pokud nejde převést na float, vrátíme původní hodnotu
        return value

def prepare_ohlc_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Připraví data pro OHLC graf.
    
    Args:
        df: DataFrame s historickými daty
        
    Returns:
        Připravený DataFrame pro OHLC graf
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Přejmenujeme sloupce pro plotly
    if 'datetime' in df.columns:
        df = df.rename(columns={'datetime': 'date'})
    
    # Seřadíme podle data (sestupně - od nejnovějšího)
    if 'date' in df.columns:
        df = df.sort_values('date')
    
    return df

def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vypočítá technické indikátory.
    
    Args:
        df: DataFrame s historickými daty
        
    Returns:
        DataFrame s přidanými technickými indikátory
    """
    if df is None or df.empty or 'close' not in df.columns:
        return df
    
    # Kopie DataFrame
    result = df.copy()
    
    # 50-denní jednoduchý klouzavý průměr (SMA)
    result['SMA_50'] = result['close'].rolling(window=50, min_periods=1).mean()
    
    # 200-denní jednoduchý klouzavý průměr (SMA)
    result['SMA_200'] = result['close'].rolling(window=200, min_periods=1).mean()
    
    # 14-denní relativní síla indexu (RSI)
    delta = result['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14, min_periods=1).mean()
    avg_loss = loss.rolling(window=14, min_periods=1).mean()
    rs = avg_gain / avg_loss
    result['RSI_14'] = 100 - (100 / (1 + rs))
    
    return result

def get_market_status(quote_data: Dict[str, Any]) -> str:
    """
    Určí stav trhu na základě dat o kotaci.
    
    Args:
        quote_data: Slovník s daty o kotaci
        
    Returns:
        Stav trhu ("Otevřeno", "Zavřeno" nebo "Neznámý stav")
    """
    if not quote_data:
        return "Neznámý stav"
    
    # Zkusíme získat informaci o stavu trhu
    if 'is_market_open' in quote_data:
        return "Otevřeno" if quote_data['is_market_open'] else "Zavřeno"
    
    # Pokud není k dispozici přímá informace, pokusíme se to odhadnout
    try:
        # Pokusíme se porovnat datum poslední kotace s aktuálním datem
        if 'datetime' in quote_data:
            quote_date = datetime.strptime(quote_data['datetime'], "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            
            # Pokud je poslední kotace starší než 1 den, pravděpodobně je trh zavřený
            if (now - quote_date) > timedelta(days=1):
                return "Zavřeno"
            else:
                return "Otevřeno"
    except:
        pass
    
    return "Neznámý stav"

def get_instrument_categories() -> List[Dict[str, str]]:
    """
    Vrátí kategorie finančních nástrojů.
    
    Returns:
        Seznam kategorií finančních nástrojů
    """
    categories = [
        {"id": "forex", "name": "Měnové páry"},
        {"id": "stocks", "name": "Akcie"},
        {"id": "indices", "name": "Indexy"},
        {"id": "commodities", "name": "Komodity"},
        {"id": "etfs", "name": "ETF"}
    ]
    
    return categories

def get_timeframes() -> List[Dict[str, str]]:
    """
    Vrátí dostupné časové rámce pro grafy.
    
    Returns:
        Seznam časových rámců
    """
    timeframes = [
        {"id": "1day", "name": "Denní"},
        {"id": "1week", "name": "Týdenní"},
        {"id": "1month", "name": "Měsíční"},
        {"id": "1h", "name": "Hodinový"},
        {"id": "4h", "name": "4 hodiny"},
        {"id": "15min", "name": "15 minut"},
        {"id": "5min", "name": "5 minut"},
        {"id": "1min", "name": "1 minuta"}
    ]
    
    return timeframes

def search_local_instruments(query: str, instruments: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Vyhledá nástroje v lokálním seznamu podle dotazu.
    
    Args:
        query: Dotaz pro vyhledávání
        instruments: Seznam nástrojů k prohledání
        
    Returns:
        Seznam nalezených nástrojů
    """
    if not query:
        return instruments[:10]  # Vrátí prvních 10 nástrojů, pokud není zadán dotaz
    
    query = query.lower()
    results = []
    
    for instrument in instruments:
        # Vyhledáváme v symbolu a názvu
        if query in instrument.get('symbol', '').lower() or query in instrument.get('name', '').lower():
            results.append(instrument)
    
    return results[:10]  # Omezíme na prvních 10 výsledků
