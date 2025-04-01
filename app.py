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
from strategy_comparison import strategy_comparison_app

# Konfigurace stránky
st.set_page_config(
    page_title="Finanční dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Nastavení vlastního CSS stylu podle vzorového obrázku
st.markdown("""
<style>
    .main {
        background-color: #0e0b2b;
        color: white;
    }
    .stApp {
        background: linear-gradient(135deg, #0e0b2b 0%, #2a1964 50%, #4e0979 100%);
    }
    h1, h2, h3, h4 {
        color: #f0f0f0 !important;
    }
    .css-1kyxreq, .css-10trblm {
        color: #f0f0f0 !important;
    }
    .sidebar .sidebar-content {
        background-color: rgba(20, 10, 50, 0.8);
    }
    .stButton>button {
        background-color: #6c22df;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 5px 15px;
    }
    .stButton>button:hover {
        background-color: #8540e9;
    }
    .css-1vq4p4l, .css-f9cq9g {
        border: 2px solid rgba(108, 34, 223, 0.2);
        border-radius: 10px;
        background-color: rgba(10, 5, 25, 0.6);
        margin-bottom: 15px;
        padding: 10px;
    }
    .stPlotlyChart {
        border: 2px solid rgba(108, 34, 223, 0.2);
        border-radius: 10px;
        background-color: rgba(10, 5, 25, 0.3);
        padding: 10px;
    }
    .css-1r6slb0 {
        background-color: rgba(10, 5, 25, 0.5);
        border-radius: 5px;
    }
    .st-br {
        border-color: rgba(255, 255, 255, 0.1);
    }
    .css-1d0tddh {
        color: #f0f0f0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Nadpis aplikace s futuristickým designem
st.markdown("""
<div style="text-align: center; padding: 20px 0; background: linear-gradient(90deg, #300964 0%, #6c22df 50%, #300964 100%); 
border-radius: 15px; margin-bottom: 20px; box-shadow: 0 0 20px rgba(108, 34, 223, 0.5);">
    <h1 style="color: white; font-weight: bold; margin: 0; text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);">
        🌟 Finanční Intelligence Dashboard 🌟
    </h1>
    <p style="color: #d0d0ff; font-size: 1.1em; margin: 5px 0 0 0;">
        Pokročilá analýza trhů s využitím umělé inteligence a reálných dat
    </p>
</div>
""", unsafe_allow_html=True)

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
        user_input = st.chat_input("Napište zprávu...")
        if user_input:
            # Přidání zprávy uživatele do historie
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            
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
            
            # Vyvolání překreslení stránky
            st.rerun()
    
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

# Automatické obnovování dat v reálném čase
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False
if "refresh_interval" not in st.session_state:
    st.session_state.refresh_interval = 60  # výchozí interval obnovení v sekundách

with st.sidebar:
    st.markdown("---")
    st.subheader("Automatické obnovování")
    
    auto_refresh = st.checkbox("Povolit automatické obnovování dat", value=st.session_state.auto_refresh)
    
    if auto_refresh != st.session_state.auto_refresh:
        st.session_state.auto_refresh = auto_refresh
        # Při změně stavu obnovíme stránku
        st.rerun()
    
    refresh_interval = st.slider(
        "Interval obnovení (sekundy)",
        min_value=5,
        max_value=300,
        value=st.session_state.refresh_interval,
        step=5
    )
    
    if refresh_interval != st.session_state.refresh_interval:
        st.session_state.refresh_interval = refresh_interval
        # Při změně intervalu obnovíme stránku
        st.rerun()
    
    # Informace o příštím obnovení
    if st.session_state.auto_refresh and st.session_state.last_refresh:
        next_refresh = st.session_state.last_refresh + st.session_state.refresh_interval
        time_to_refresh = max(0, next_refresh - time.time())
        st.text(f"Příští obnovení za: {int(time_to_refresh)} s")

# Automatické obnovení pomocí JavaScript
if st.session_state.auto_refresh:
    # Přepočítáme zbývající čas do příštího obnovení
    if st.session_state.last_refresh:
        next_refresh = st.session_state.last_refresh + st.session_state.refresh_interval
        time_to_refresh = max(0, next_refresh - time.time())
        # Pouze pokud je čas k dalšímu obnovení menší než interval, obnovíme
        if time_to_refresh <= 0:
            update_data()  # Obnovíme data
            # Pokud nejsme na stránce, nastane obnovení při příštím načtení
        
        # JavaScript pro automatické obnovení stránky po uplynutí času
        # ms_to_refresh = int(time_to_refresh * 1000)
        # if ms_to_refresh > 0:
        #     st.markdown(f"""
        #     <script>
        #         setTimeout(function(){{ window.location.reload(); }}, {ms_to_refresh});
        #     </script>
        #     """, unsafe_allow_html=True)

# Přidání menu pro přepínání mezi nástroji
st.sidebar.markdown("---")
st.sidebar.header("Navigace")
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = "📈 Dashboard"

app_mode = st.sidebar.radio(
    "Výběr aplikace",
    ["📈 Dashboard", "🧪 Porovnání strategií"],
    index=0 if st.session_state.app_mode == "📈 Dashboard" else 1
)

# Aktualizace stavu aplikace
if app_mode != st.session_state.app_mode:
    st.session_state.app_mode = app_mode
    st.rerun()

# Pokud je vybrán nástroj pro porovnání strategií, zobrazíme ho
if app_mode == "🧪 Porovnání strategií":
    # Skrýt standardní obsah dashboardu v případě přepnutí na nástroj porovnání strategií
    st.markdown("<style>.main-content {display: none;}</style>", unsafe_allow_html=True)
    # Před zobrazením nástroje pro porovnání strategií přidáme sekci pro vymazání paměti
    placeholder = st.empty()
    with placeholder.container():
        strategy_comparison_app()
    st.stop()  # Zastavíme vykonávání zbytku kódu
    
# Patička
st.markdown("---")
st.caption("Data poskytována službou [Twelve Data](https://twelvedata.com/) | AI asistent powered by [Google Gemini](https://ai.google.dev/)")
st.caption("© 2023-2025 Finanční Dashboard")
