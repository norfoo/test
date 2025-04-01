import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from typing import Optional, Dict, Any, List

def create_ohlc_chart(df: pd.DataFrame, title: str = "Vývoj ceny", show_volume: bool = True, 
                      show_sma: bool = True, height: int = 700) -> Optional[go.Figure]:
    """
    Vytvoří OHLC (Open-High-Low-Close) graf ceny s pokročilými technickými indikátory.
    
    Args:
        df: DataFrame s historickými daty (musí obsahovat sloupce date, open, high, low, close)
        title: Název grafu
        show_volume: Zobrazit objem obchodů
        show_sma: Zobrazit klouzavé průměry
        height: Výška grafu v pixelech
        
    Returns:
        Plotly Figure objekt grafu nebo None v případě chyby
    """
    try:
        if df is None or df.empty or not all(col in df.columns for col in ['date', 'open', 'high', 'low', 'close']):
            return None
        
        # Určení, kolik subplotů potřebujeme na základě dostupných dat
        has_volume = show_volume and 'volume' in df.columns and not df['volume'].isna().all()
        has_macd = 'macd' in df.columns and 'macd_signal' in df.columns
        has_rsi = 'rsi_14' in df.columns
        
        # Počet subplot grafů a jejich výšky
        num_rows = 1
        row_heights = [0.7]
        subplot_titles = ["Cena"]
        
        if has_volume:
            num_rows += 1
            row_heights.append(0.1)
            subplot_titles.append("Objem")
            
        if has_macd:
            num_rows += 1
            row_heights.append(0.1)
            subplot_titles.append("MACD")
            
        if has_rsi:
            num_rows += 1
            row_heights.append(0.1)
            subplot_titles.append("RSI")
        
        # Vytvoření subplot grafů
        fig = make_subplots(
            rows=num_rows, 
            cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.02,
            row_heights=row_heights,
            subplot_titles=subplot_titles
        )
        
        # 1. HLAVNÍ SVÍČKOVÝ GRAF
        fig.add_trace(
            go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name="OHLC",
                increasing_line_color='green',
                decreasing_line_color='red'
            ),
            row=1, col=1
        )
        
        # Přidání klouzavých průměrů
        if show_sma:
            # Krátké SMA
            if 'sma_9' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=df['sma_9'],
                        mode='lines',
                        line=dict(color='blue', width=1),
                        name="SMA 9"
                    ),
                    row=1, col=1
                )
            
            # Střednědobé SMA
            if 'sma_20' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=df['sma_20'],
                        mode='lines',
                        line=dict(color='orange', width=1),
                        name="SMA 20"
                    ),
                    row=1, col=1
                )
            
            # Dlouhodobé SMA
            if 'sma_50' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=df['sma_50'],
                        mode='lines',
                        line=dict(color='purple', width=1),
                        name="SMA 50"
                    ),
                    row=1, col=1
                )
                
            # EMA indikátory
            if 'ema_20' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=df['ema_20'],
                        mode='lines',
                        line=dict(color='green', width=1, dash='dot'),
                        name="EMA 20"
                    ),
                    row=1, col=1
                )
                
            # Bollinger Bands
            if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=df['bb_upper'],
                        mode='lines',
                        line=dict(color='rgba(250, 0, 0, 0.4)', width=1),
                        name="BB Upper"
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=df['bb_lower'],
                        mode='lines',
                        line=dict(color='rgba(250, 0, 0, 0.4)', width=1),
                        name="BB Lower",
                        fill='tonexty',
                        fillcolor='rgba(200, 200, 200, 0.2)'
                    ),
                    row=1, col=1
                )
        
        # Aktuální řádek pro další grafy
        current_row = 1
        
        # 2. VOLUME
        if has_volume:
            current_row += 1
            # Určení barvy sloupců podle pohybu ceny
            colors = ['green' if row['close'] >= row['open'] else 'red' for _, row in df.iterrows()]
            
            fig.add_trace(
                go.Bar(
                    x=df['date'],
                    y=df['volume'],
                    name="Objem",
                    marker_color=colors,
                    opacity=0.7
                ),
                row=current_row, col=1
            )
            
            # VWAP pokud je dostupný
            if 'vwap' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=df['vwap'],
                        mode='lines',
                        line=dict(color='blue', width=1.5),
                        name="VWAP"
                    ),
                    row=1, col=1
                )
        
        # 3. MACD (Moving Average Convergence Divergence)
        if has_macd:
            current_row += 1
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['macd'],
                    mode='lines',
                    line=dict(color='blue', width=1.5),
                    name="MACD"
                ),
                row=current_row, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['macd_signal'],
                    mode='lines',
                    line=dict(color='red', width=1),
                    name="Signal"
                ),
                row=current_row, col=1
            )
            
            # MACD histogram
            if 'macd_hist' in df.columns:
                colors = ['green' if val >= 0 else 'red' for val in df['macd_hist']]
                fig.add_trace(
                    go.Bar(
                        x=df['date'],
                        y=df['macd_hist'],
                        marker_color=colors,
                        name="MACD Hist"
                    ),
                    row=current_row, col=1
                )
                
                # Nulová linka pro MACD
                fig.add_shape(
                    type="line",
                    x0=df['date'].iloc[0],
                    x1=df['date'].iloc[-1],
                    y0=0, y1=0,
                    line=dict(color="gray", width=1, dash="dash"),
                    row=current_row, col=1
                )
        
        # 4. RSI (Relative Strength Index)
        if has_rsi:
            current_row += 1
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['rsi_14'],
                    mode='lines',
                    line=dict(color='purple', width=1.5),
                    name="RSI"
                ),
                row=current_row, col=1
            )
            
            # Přidání vodítek pro překoupené/přeprodané oblasti (70/30)
            fig.add_shape(
                type="line",
                x0=df['date'].iloc[0],
                x1=df['date'].iloc[-1],
                y0=70, y1=70,
                line=dict(color="red", width=1, dash="dash"),
                row=current_row, col=1
            )
            
            fig.add_shape(
                type="line",
                x0=df['date'].iloc[0],
                x1=df['date'].iloc[-1],
                y0=30, y1=30,
                line=dict(color="green", width=1, dash="dash"),
                row=current_row, col=1
            )
            
            # Přidání středové linky na 50
            fig.add_shape(
                type="line",
                x0=df['date'].iloc[0],
                x1=df['date'].iloc[-1],
                y0=50, y1=50,
                line=dict(color="gray", width=1, dash="dash"),
                row=current_row, col=1
            )
            
            # Nastavení rozsahu RSI grafu
            fig.update_yaxes(range=[0, 100], row=current_row, col=1)
        
        # Formátování layoutu grafu
        fig.update_layout(
            title=title,
            height=height,
            xaxis_rangeslider_visible=False,  # Skryjeme rangeslider pro úsporu místa
            template='plotly_white',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Nastavení os Y
        fig.update_yaxes(title_text="Cena", row=1, col=1)
        
        if has_volume:
            volume_row = 2
            fig.update_yaxes(title_text="Objem", row=volume_row, col=1)
            
        if has_macd:
            macd_row = 3 if has_volume else 2
            fig.update_yaxes(title_text="MACD", row=macd_row, col=1)
            
        if has_rsi:
            rsi_row = num_rows  # Poslední řádek
            fig.update_yaxes(title_text="RSI", row=rsi_row, col=1)
        
        return fig
        
    except Exception as e:
        print(f"Chyba při vytváření grafu: {e}")
        return None

def display_price_indicators(quote_data: Dict[str, Any]):
    """
    Zobrazí cenové indikátory ve formě metriky.
    
    Args:
        quote_data: Slovník s daty o kotaci
    """
    if not quote_data:
        st.warning("Nejsou k dispozici data o ceně.")
        return
    
    # Vytvoříme layout s 3 sloupci
    col1, col2, col3 = st.columns(3)
    
    # Aktuální cena
    with col1:
        if 'close' in quote_data and quote_data['close']:
            st.metric(
                label="Aktuální cena",
                value=f"{quote_data['close']} {quote_data.get('currency', '')}"
            )
        
    # Změna ceny
    with col2:
        if 'change' in quote_data and quote_data['change'] and 'percent_change' in quote_data and quote_data['percent_change']:
            change = float(quote_data['change'])
            st.metric(
                label="Změna",
                value=f"{quote_data['change']} {quote_data.get('currency', '')}",
                delta=f"{quote_data['percent_change']}%"
            )

    # Denní rozsah
    with col3:
        if 'low' in quote_data and quote_data['low'] and 'high' in quote_data and quote_data['high']:
            st.metric(
                label="Denní rozsah",
                value=f"{quote_data['low']} - {quote_data['high']} {quote_data.get('currency', '')}"
            )

def display_quote_details(quote_data: Dict[str, Any]):
    """
    Zobrazí detailní informace o kotaci.
    
    Args:
        quote_data: Slovník s daty o kotaci
    """
    if not quote_data:
        return
    
    # Vytvoříme expandující sekci s detaily
    with st.expander("Detailní informace", expanded=False):
        # Základní informace
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'name' in quote_data:
                st.markdown(f"**Název:**  \n{quote_data.get('name', '')}")
            if 'symbol' in quote_data:
                st.markdown(f"**Symbol:**  \n{quote_data.get('symbol', '')}")
            if 'exchange' in quote_data:
                st.markdown(f"**Burza:**  \n{quote_data.get('exchange', '')}")

        with col2:
            if 'open' in quote_data:
                st.markdown(f"**Otevírací cena:**  \n{quote_data.get('open', '')} {quote_data.get('currency', '')}")
            if 'previous_close' in quote_data:
                st.markdown(f"**Předchozí závěr:**  \n{quote_data.get('previous_close', '')} {quote_data.get('currency', '')}")
            if 'datetime' in quote_data:
                st.markdown(f"**Datum a čas:**  \n{quote_data.get('datetime', '')}")

        with col3:
            if 'fifty_two_week' in quote_data:
                st.markdown(f"**52 týdenní minimum:**  \n{quote_data.get('fifty_two_week', {}).get('low', '')} {quote_data.get('currency', '')}")
                st.markdown(f"**52 týdenní maximum:**  \n{quote_data.get('fifty_two_week', {}).get('high', '')} {quote_data.get('currency', '')}")

def display_market_status(market_status: str):
    """
    Zobrazí stav trhu.
    
    Args:
        market_status: Stav trhu ("Otevřeno", "Zavřeno" nebo "Neznámý stav")
    """
    # Barva podle stavu trhu
    if market_status == "Otevřeno":
        status_color = "green"
    elif market_status == "Zavřeno":
        status_color = "red"
    else:
        status_color = "gray"
        
    st.markdown(f"**Stav trhu:** <span style='color:{status_color};'>{market_status}</span>", unsafe_allow_html=True)

def display_api_status(api_status: bool):
    """
    Zobrazí stav API.
    
    Args:
        api_status: True, pokud je API klíč k dispozici a funkční, jinak False
    """
    if api_status:
        st.sidebar.success("API připojení: Aktivní")
    else:
        st.sidebar.error("API připojení: Neaktivní")
        st.sidebar.markdown("""
        **API klíč není nastaven nebo nefunguje.**
        
        Prosím, přidejte váš API klíč jako proměnnou prostředí s názvem `TWELVE_DATA_API_KEY`. 
        
        Twelve Data API klíč můžete získat na [twelvedata.com](https://twelvedata.com/).
        """)

def display_no_data_message():
    """Zobrazí zprávu, když nejsou k dispozici žádná data."""
    st.warning("Nejsou k dispozici žádná data. Prosím, zkontrolujte připojení k API nebo vyberte jiný symbol.")

def display_error_message(message: str):
    """
    Zobrazí chybovou zprávu.
    
    Args:
        message: Text chybové zprávy
    """
    st.error(f"Chyba: {message}")

def display_loading_message():
    """Zobrazí zprávu o načítání."""
    return st.info("Načítám data, prosím čekejte...")

def display_instructions():
    """Zobrazí instrukce pro použití aplikace."""
    with st.expander("Nápověda", expanded=False):
        st.markdown("""
        ### Jak používat aplikaci

        1. **Výběr kategorie a nástroje**
           - V postranním panelu vyberte kategorii finančního nástroje (měnové páry, akcie, indexy, komodity, ETF)
           - Z rozbalovací nabídky vyberte konkrétní nástroj nebo použijte vyhledávací pole
           
        2. **Zobrazení údajů o ceně**
           - Po výběru nástroje se v horní části zobrazí aktuální cena, změna a denní rozsah
           - Podrobnější informace naleznete v sekci "Detailní informace"
           
        3. **Graf ceny**
           - V hlavní části se zobrazí graf vývoje ceny
           - Můžete změnit časový rámec v postranním panelu
           - Najeďte myší nad graf pro zobrazení detailů, přibližte oblast tažením myši
           
        4. **Gemini AI Asistent**
           - Ve spodní části aplikace najdete AI asistenta
           - V záložce "Chat" můžete komunikovat s AI asistentem a ptát se na finanční témata
           - V záložce "Analýza" si můžete nechat vygenerovat analýzu aktuálně vybraného instrumentu
           - Pro funkčnost AI asistenta je potřeba API klíč od Google Gemini
           - Gemini API klíč je potřeba nastavit jako proměnnou prostředí s názvem `GEMINI_API_KEY`
           - Google Gemini API klíč můžete získat na [ai.google.dev](https://ai.google.dev/)
           
        5. **Nastavení API klíčů**
           - Pro funkční aplikaci je nutný API klíč od Twelve Data
           - Klíč je potřeba nastavit jako proměnnou prostředí s názvem `TWELVE_DATA_API_KEY`
           - Twelve Data API klíč můžete získat na [twelvedata.com](https://twelvedata.com/)
           - Pro funkčnost AI asistenta je potřeba nastavit Gemini API klíč jako proměnnou prostředí s názvem `GEMINI_API_KEY`
        """)
