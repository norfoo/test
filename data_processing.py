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
    Vypočítá technické indikátory pro obchodní analýzu.
    
    Args:
        df: DataFrame s historickými daty
        
    Returns:
        DataFrame s přidanými technickými indikátory
    """
    if df is None or df.empty or 'close' not in df.columns:
        return df
    
    # Kopie DataFrame
    result = df.copy()
    
    # Klouzavé průměry (SMA)
    # Krátké období pro 5-minutový timeframe
    result['sma_9'] = result['close'].rolling(window=9, min_periods=1).mean()
    result['sma_20'] = result['close'].rolling(window=20, min_periods=1).mean()
    result['sma_50'] = result['close'].rolling(window=50, min_periods=1).mean()
    
    # Exponenciální klouzavé průměry (EMA)
    # Vysoká citlivost pro 5-minutový timeframe
    result['ema_9'] = result['close'].ewm(span=9, adjust=False).mean()
    result['ema_20'] = result['close'].ewm(span=20, adjust=False).mean()
    result['ema_50'] = result['close'].ewm(span=50, adjust=False).mean()
    
    # 14-intervalový relativní síla indexu (RSI)
    delta = result['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14, min_periods=1).mean()
    avg_loss = loss.rolling(window=14, min_periods=1).mean()
    rs = avg_gain / avg_loss
    result['rsi_14'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands (20, 2)
    # Standardní nastavení vhodné i pro 5-minutový timeframe
    sma_20 = result['close'].rolling(window=20, min_periods=1).mean()
    std_20 = result['close'].rolling(window=20, min_periods=1).std()
    result['bb_upper'] = sma_20 + (std_20 * 2)
    result['bb_middle'] = sma_20
    result['bb_lower'] = sma_20 - (std_20 * 2)
    
    # MACD (Moving Average Convergence Divergence)
    # Standardní nastavení (12, 26, 9)
    result['ema_12'] = result['close'].ewm(span=12, adjust=False).mean()
    result['ema_26'] = result['close'].ewm(span=26, adjust=False).mean()
    result['macd'] = result['ema_12'] - result['ema_26']
    result['macd_signal'] = result['macd'].ewm(span=9, adjust=False).mean()
    result['macd_hist'] = result['macd'] - result['macd_signal']
    
    # Stochastic Oscillator (14, 3, 3)
    # Rychlý stochastický oscilátor
    low_14 = result['low'].rolling(window=14).min()
    high_14 = result['high'].rolling(window=14).max()
    result['stoch_k'] = 100 * ((result['close'] - low_14) / (high_14 - low_14))
    result['stoch_d'] = result['stoch_k'].rolling(window=3).mean()
    
    # Volume Weighted Average Price (VWAP) - pokud jsou k dispozici data o objemu
    if 'volume' in result.columns and result['volume'].sum() > 0:
        result['vwap'] = (result['volume'] * (result['high'] + result['low'] + result['close']) / 3).cumsum() / result['volume'].cumsum()
    
    # Average True Range (ATR) - pro nastavení stop-loss
    tr1 = result['high'] - result['low']
    tr2 = (result['high'] - result['close'].shift()).abs()
    tr3 = (result['low'] - result['close'].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    result['atr_14'] = tr.rolling(window=14).mean()
    
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
        {"id": "5min", "name": "5 minut (aktuální)"}, # Nastavíme 5min jako první volbu
        {"id": "1day", "name": "Denní"},
        {"id": "1week", "name": "Týdenní"},
        {"id": "1month", "name": "Měsíční"},
        {"id": "1h", "name": "Hodinový"},
        {"id": "4h", "name": "4 hodiny"},
        {"id": "15min", "name": "15 minut"},
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


def check_risk_reward_ratio(entry: float, stoploss: float, take_profit: float, min_ratio: float = 2.5) -> bool:
    """
    Kontroluje, zda obchodní signál splňuje minimální poměr rizika k zisku.
    
    Args:
        entry: Vstupní cena
        stoploss: Stop-loss cena
        take_profit: Take-profit cena
        min_ratio: Minimální požadovaný poměr rizika k zisku (výchozí 2.5)
        
    Returns:
        True, pokud obchodní signál splňuje minimální poměr rizika k zisku, jinak False
    """
    # Výpočet rozdílu pro riziko a zisk
    is_long = entry < take_profit  # True pro long, False pro short
    
    if is_long:
        risk = abs(entry - stoploss)
        reward = abs(take_profit - entry)
    else:
        risk = abs(stoploss - entry)
        reward = abs(entry - take_profit)
    
    # Ochrana proti dělení nulou
    if risk == 0:
        return False
    
    # Výpočet poměru rizika k zisku
    ratio = reward / risk
    
    # Kontrola, zda je splněn minimální požadovaný poměr
    return ratio >= min_ratio


def calculate_risk_reward_ratio(entry: float, stoploss: float, take_profit: float) -> float:
    """
    Vypočítá poměr rizika k zisku pro zadaný obchodní signál.
    
    Args:
        entry: Vstupní cena
        stoploss: Stop-loss cena
        take_profit: Take-profit cena
        
    Returns:
        Poměr rizika k zisku jako číslo (např. 2.5 znamená 1:2.5)
    """
    # Výpočet rozdílu pro riziko a zisk
    is_long = entry < take_profit  # True pro long, False pro short
    
    if is_long:
        risk = abs(entry - stoploss)
        reward = abs(take_profit - entry)
    else:
        risk = abs(stoploss - entry)
        reward = abs(entry - take_profit)
    
    # Ochrana proti dělení nulou
    if risk == 0:
        return 0.0
    
    # Výpočet poměru rizika k zisku
    ratio = reward / risk
    
    return ratio
