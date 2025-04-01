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
from gemini_service import (
    check_gemini_api_key, get_chat_response, get_financial_analysis,
    get_available_models
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
    st.session_state.selected_category = "commodities"
if 'selected_symbol' not in st.session_state:
    st.session_state.selected_symbol = "XAU/USD"
if 'selected_timeframe' not in st.session_state:
    st.session_state.selected_timeframe = "5min"
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

# Inicializace session state pro Gemini AI chat
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'chat_tab' not in st.session_state:
    st.session_state.chat_tab = "chat"  # "chat" nebo "analysis"
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'gemini_model' not in st.session_state:
    st.session_state.gemini_model = "gemini-1.5-pro"

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

def on_chat_submit():
    """Zpracování odeslání zprávy v chatu."""
    if st.session_state.chat_input and st.session_state.chat_input.strip():
        user_message = st.session_state.chat_input
        
        # Přidání zprávy uživatele do historie
        st.session_state.chat_messages.append({"role": "user", "content": user_message})
        
        # Získání odpovědi od AI
        ai_response = get_chat_response(
            st.session_state.chat_messages,
            model_name=st.session_state.gemini_model
        )
        
        if ai_response:
            # Přidání odpovědi AI do historie
            st.session_state.chat_messages.append({"role": "assistant", "content": ai_response})
        else:
            # Přidání zprávy o chybě
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": "Omlouvám se, ale nepodařilo se získat odpověď. Zkontrolujte, prosím, zda je nastaven platný API klíč pro Gemini."}
            )
        
        # Vyčištění vstupního pole
        st.session_state.chat_input = ""

def get_ai_analysis():
    """Získání AI analýzy pro aktuální symbol."""
    if st.session_state.quote_data:
        analysis = get_financial_analysis(
            st.session_state.selected_symbol,
            st.session_state.quote_data,
            st.session_state.historical_data,
            model_name=st.session_state.gemini_model
        )
        
        if analysis:
            st.session_state.analysis_result = analysis
        else:
            st.session_state.analysis_result = "Nepodařilo se získat analýzu. Zkontrolujte, prosím, zda je nastaven platný API klíč pro Gemini."
    else:
        st.session_state.analysis_result = "Pro analýzu je potřeba načíst data o ceně."

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

# ----------------------------- Gemini AI asistent -----------------------------

# Kontrola Gemini API klíče
gemini_api_status = check_gemini_api_key()

st.markdown("---")
st.header("💬 Gemini AI Asistent")

if not gemini_api_status:
    st.warning("""
    API klíč pro Gemini nebyl nalezen nebo nefunguje. Prosím, nastavte platný API klíč jako proměnnou prostředí.
    
    ```
    GEMINI_API_KEY=váš_api_klíč
    ```
    
    API klíč můžete získat na [ai.google.dev](https://ai.google.dev/).
    """)
else:
    # Záložky pro chat a analýzu
    chat_tab, analysis_tab = st.tabs(["💬 Chat", "📊 Analýza"])
    
    # Záložka s chatem
    with chat_tab:
        st.markdown("### Chat s AI asistentem")
        st.markdown("Zeptejte se na cokoliv ohledně finančních trhů, vybraných instrumentů nebo obchodování.")
        
        # Zobrazení historie zpráv
        for message in st.session_state.chat_messages:
            if message["role"] == "user":
                st.chat_message("user", avatar="👤").write(message["content"])
            else:
                st.chat_message("assistant", avatar="🤖").write(message["content"])
        
        # Vstupní pole pro chat
        st.chat_input(
            "Napište zprávu...",
            key="chat_input",
            on_submit=on_chat_submit
        )
    
    # Záložka s analýzou
    with analysis_tab:
        st.markdown("### AI Analýza vybraného instrumentu")
        st.markdown(f"Analýza pro symbol **{st.session_state.selected_symbol}**")
        
        if st.button("Získat AI analýzu"):
            with st.spinner("Generuji analýzu..."):
                get_ai_analysis()
        
        if st.session_state.analysis_result:
            st.markdown(st.session_state.analysis_result)
        else:
            st.info("Klikněte na tlačítko 'Získat AI analýzu' pro vygenerování analýzy vybraného instrumentu.")
        
        st.caption("Analýza je generována pomocí umělé inteligence a má pouze informativní charakter. Nejedná se o investiční doporučení.")

# Patička
st.markdown("---")
st.caption("Data poskytována službou [Twelve Data](https://twelvedata.com/) | AI asistent powered by [Google Gemini](https://ai.google.dev/)")
st.caption("© 2023-2025 Finanční Dashboard")
