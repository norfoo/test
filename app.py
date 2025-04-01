import streamlit as st
import pandas as pd
import time

from api_service import (
    get_current_quote, get_time_series, search_symbols,
    get_forex_pairs, get_stocks, get_indices, get_commodities, get_etfs,
    check_api_key
)
from data_processing import (
    format_quote_data, prepare_ohlc_data, calculate_technical_indicators, 
    get_market_status, get_instrument_categories, get_timeframes,
    search_local_instruments
)
from visualization import (
    create_ohlc_chart, display_price_indicators, display_quote_details,
    display_market_status, display_api_status, display_no_data_message,
    display_error_message, display_loading_message, display_instructions
)

# Konfigurace stránky
st.set_page_config(
    page_title="Finanční dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Nadpis aplikace
st.title("📈 Finanční dashboard")
st.markdown("Dashboard pro sledování finančních trhů s využitím Twelve Data API")

# Kontrola API klíče
api_status = check_api_key()
display_api_status(api_status)

# Inicializace session state pro uchování stavu aplikace
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = "forex"
if 'selected_symbol' not in st.session_state:
    st.session_state.selected_symbol = "EUR/USD"
if 'selected_timeframe' not in st.session_state:
    st.session_state.selected_timeframe = "1day"
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'quote_data' not in st.session_state:
    st.session_state.quote_data = None
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = None
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None
if 'instruments' not in st.session_state:
    st.session_state.instruments = {}
if 'is_loading' not in st.session_state:
    st.session_state.is_loading = False

# ----------------------------- Funkce -----------------------------

def load_instruments(category):
    """Načte nástroje pro danou kategorii."""
    if category not in st.session_state.instruments:
        if category == "forex":
            st.session_state.instruments[category] = get_forex_pairs()
        elif category == "stocks":
            st.session_state.instruments[category] = get_stocks()
        elif category == "indices":
            st.session_state.instruments[category] = get_indices()
        elif category == "commodities":
            st.session_state.instruments[category] = get_commodities()
        elif category == "etfs":
            st.session_state.instruments[category] = get_etfs()
        else:
            st.session_state.instruments[category] = []
    
    return st.session_state.instruments[category]

def update_data():
    """Aktualizuje data o ceně a historické údaje."""
    st.session_state.is_loading = True
    
    # Získání aktuálních dat o ceně
    quote_data = get_current_quote(st.session_state.selected_symbol)
    if quote_data:
        st.session_state.quote_data = format_quote_data(quote_data)
    else:
        st.session_state.quote_data = None
    
    # Získání historických dat
    historical_data = get_time_series(
        st.session_state.selected_symbol, 
        interval=st.session_state.selected_timeframe,
        outputsize=500  # Získáme více dat pro lepší graf
    )
    
    if historical_data is not None and not historical_data.empty:
        # Příprava dat pro graf
        df = prepare_ohlc_data(historical_data)
        # Výpočet technických indikátorů
        df = calculate_technical_indicators(df)
        st.session_state.historical_data = df
    else:
        st.session_state.historical_data = None
    
    st.session_state.last_refresh = time.time()
    st.session_state.is_loading = False

def on_symbol_change():
    """Akce při změně symbolu."""
    update_data()

def on_category_change():
    """Akce při změně kategorie nástrojů."""
    # Načtení nástrojů pro vybranou kategorii
    instruments = load_instruments(st.session_state.selected_category)
    if instruments:
        # Výběr prvního nástroje z dané kategorie
        st.session_state.selected_symbol = instruments[0].get('symbol', '')
        update_data()

def on_timeframe_change():
    """Akce při změně časového rámce."""
    update_data()

def on_search():
    """Akce při vyhledávání symbolu."""
    if st.session_state.search_query:
        # Vyhledání symbolu přes API
        results = search_symbols(st.session_state.search_query)
        if results:
            # Aktualizace vybraného symbolu na první výsledek
            st.session_state.selected_symbol = results[0].get('symbol', '')
            update_data()

# ----------------------------- Postranní panel -----------------------------

with st.sidebar:
    st.header("Nastavení")
    
    # Výběr kategorie
    categories = get_instrument_categories()
    category_options = {cat["name"]: cat["id"] for cat in categories}
    selected_category_name = st.selectbox(
        "Kategorie",
        list(category_options.keys()),
        index=list(category_options.keys()).index(next(
            (cat["name"] for cat in categories if cat["id"] == st.session_state.selected_category), 
            categories[0]["name"]
        ))
    )
    
    # Aktualizace vybrané kategorie v session state
    selected_category = category_options[selected_category_name]
    if selected_category != st.session_state.selected_category:
        st.session_state.selected_category = selected_category
        on_category_change()
    
    # Načtení nástrojů pro vybranou kategorii
    instruments = load_instruments(st.session_state.selected_category)
    
    # Vyhledávání
    st.session_state.search_query = st.text_input(
        "Vyhledat symbol",
        value=st.session_state.search_query
    )
    
    if st.button("Hledat"):
        on_search()
    
    # Výběr symbolu
    if instruments:
        symbol_options = {inst.get('name', ''): inst.get('symbol', '') for inst in instruments}
        selected_name = st.selectbox(
            "Nástroj",
            list(symbol_options.keys()),
            index=0 if st.session_state.selected_symbol not in symbol_options.values() else 
                  list(symbol_options.values()).index(st.session_state.selected_symbol)
        )
        
        # Aktualizace vybraného symbolu v session state
        selected_symbol = symbol_options[selected_name]
        if selected_symbol != st.session_state.selected_symbol:
            st.session_state.selected_symbol = selected_symbol
            on_symbol_change()
    
    # Výběr časového rámce
    timeframes = get_timeframes()
    timeframe_options = {tf["name"]: tf["id"] for tf in timeframes}
    selected_timeframe_name = st.selectbox(
        "Časový rámec",
        list(timeframe_options.keys()),
        index=list(timeframe_options.values()).index(st.session_state.selected_timeframe)
    )
    
    # Aktualizace vybraného časového rámce v session state
    selected_timeframe = timeframe_options[selected_timeframe_name]
    if selected_timeframe != st.session_state.selected_timeframe:
        st.session_state.selected_timeframe = selected_timeframe
        on_timeframe_change()
    
    # Tlačítko pro obnovení dat
    if st.button("Obnovit data"):
        update_data()
    
    # Zobrazení času poslední aktualizace
    if st.session_state.last_refresh:
        last_refresh_time = time.strftime('%H:%M:%S', time.localtime(st.session_state.last_refresh))
        st.text(f"Poslední aktualizace: {last_refresh_time}")
    
    # Instrukce a pomoc
    display_instructions()

# ----------------------------- Hlavní obsah -----------------------------

# Při prvním načtení stránky nebo když nejsou data
if st.session_state.quote_data is None or st.session_state.historical_data is None:
    if not api_status:
        st.warning("""
        API klíč nebyl nalezen nebo nefunguje. Prosím, nastavte platný API klíč jako proměnnou prostředí.
        
        ```
        TWELVE_DATA_API_KEY=váš_api_klíč
        ```
        
        API klíč můžete získat na [twelvedata.com](https://twelvedata.com/).
        """)
    else:
        # Automatické načtení dat při prvním spuštění
        update_data()

# Zobrazení stavu načítání
if st.session_state.is_loading:
    loading_message = display_loading_message()

# Zobrazení dat o ceně
if st.session_state.quote_data:
    # Záhlaví s informacemi o vybraném nástroji
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"{st.session_state.quote_data.get('name', st.session_state.selected_symbol)}")
        st.caption(f"Symbol: {st.session_state.selected_symbol}")
    with col2:
        market_status = get_market_status(st.session_state.quote_data)
        display_market_status(market_status)
    
    # Zobrazení indikátorů ceny
    display_price_indicators(st.session_state.quote_data)
    
    # Zobrazení detailních informací
    display_quote_details(st.session_state.quote_data)
    
    # Zobrazení grafu
    if st.session_state.historical_data is not None and not st.session_state.historical_data.empty:
        # Vytvoření grafu
        chart_title = f"Vývoj ceny {st.session_state.selected_symbol} ({st.session_state.selected_timeframe})"
        fig = create_ohlc_chart(st.session_state.historical_data, title=chart_title)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            display_no_data_message()
    else:
        display_no_data_message()
else:
    if not st.session_state.is_loading and api_status:
        display_no_data_message()

# Odstraníme indikátor načítání po dokončení
if st.session_state.is_loading and 'loading_message' in locals():
    loading_message.empty()

# Patička
st.markdown("---")
st.caption("Data poskytována službou [Twelve Data](https://twelvedata.com/)")
st.caption("© 2023 Finanční Dashboard")
