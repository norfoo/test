import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any
import datetime

from trading_strategies import (
    TradingStrategy, MovingAverageCrossover, RSIStrategy,
    TradeType, TradeStatus, Trade, plot_strategy_comparison
)
from api_service import get_time_series
from data_processing import prepare_ohlc_data, calculate_technical_indicators

def strategy_comparison_app():
    """
    Hlavní funkce pro aplikaci porovnání obchodních strategií.
    """
    st.title("Interaktivní nástroj pro porovnání obchodních strategií")
    
    # Sidebar pro výběr instrumentu a časového rozsahu
    st.sidebar.header("Nastavení backtestu")
    
    symbol = st.sidebar.text_input("Symbol (např. XAU/USD, EUR/USD, AAPL)", value="XAU/USD")
    
    # Výběr časového rámce pro data
    timeframe_options = {
        "1min": "1 minuta", 
        "5min": "5 minut", 
        "15min": "15 minut", 
        "30min": "30 minut", 
        "1h": "1 hodina", 
        "4h": "4 hodiny",
        "1day": "1 den"
    }
    timeframe = st.sidebar.selectbox(
        "Časový rámec pro data",
        options=list(timeframe_options.keys()),
        format_func=lambda x: timeframe_options[x],
        index=1  # Výchozí: 5min
    )
    
    # Počet historických záznamů
    lookback_period = st.sidebar.slider(
        "Počet historických záznamů",
        min_value=50,
        max_value=1000,
        value=200,
        step=50
    )
    
    # Tlačítko pro načtení dat
    data_load_button = st.sidebar.button("Načíst historická data")
    
    # Sekce pro strategie
    st.sidebar.header("Aktivní strategie")
    
    # Přepínače pro jednotlivé strategie
    use_ma_crossover = st.sidebar.checkbox("Moving Average Crossover", value=True)
    use_rsi_strategy = st.sidebar.checkbox("RSI Strategy", value=True)
    
    # Kontejner pro dočasné uložení dat
    if 'historical_data' not in st.session_state:
        st.session_state.historical_data = None
    
    if 'backtest_results' not in st.session_state:
        st.session_state.backtest_results = []
    
    # Načtení historických dat
    if data_load_button:
        with st.spinner("Načítám historická data..."):
            historical_data = get_time_series(symbol, timeframe, lookback_period)
            
            if historical_data is not None and not historical_data.empty:
                st.session_state.historical_data = historical_data
                st.session_state.historical_data = prepare_ohlc_data(historical_data)
                st.session_state.historical_data = calculate_technical_indicators(st.session_state.historical_data)
                st.success(f"Úspěšně načteno {len(historical_data)} záznamů pro {symbol}")
            else:
                st.error("Nepodařilo se načíst historická data. Zkontrolujte symbol a zkuste to znovu.")
    
    # Zobrazení dat a výsledků
    if st.session_state.historical_data is not None:
        # Záložky pro různé sekce
        tabs = st.tabs(["Data", "Nastavení strategií", "Výsledky backtestu", "Porovnání strategií"])
        
        # Záložka s daty
        with tabs[0]:
            st.header("Historická data")
            st.dataframe(st.session_state.historical_data.tail(50))
            
            # Cenový graf
            fig = go.Figure()
            
            # Candlestick graf
            fig.add_trace(go.Candlestick(
                x=st.session_state.historical_data.index,
                open=st.session_state.historical_data['open'],
                high=st.session_state.historical_data['high'],
                low=st.session_state.historical_data['low'],
                close=st.session_state.historical_data['close'],
                name="OHLC"
            ))
            
            # Nastavení grafu
            fig.update_layout(
                title=f"Cenový graf - {symbol} ({timeframe})",
                xaxis_title="Datum/Čas",
                yaxis_title="Cena",
                xaxis_rangeslider_visible=False,
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Záložka s nastavením strategií
        with tabs[1]:
            st.header("Nastavení obchodních strategií")
            
            # Moving Average Crossover nastavení
            if use_ma_crossover:
                st.subheader("Moving Average Crossover")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    ma_type = st.selectbox(
                        "Typ klouzavého průměru",
                        options=["SMA", "EMA"],
                        index=1,
                        key="ma_crossover_ma_type"
                    )
                    
                    fast_ma_period = st.slider(
                        "Období krátkodobého MA",
                        min_value=3,
                        max_value=50,
                        value=9,
                        step=1,
                        key="ma_crossover_fast_period"
                    )
                    
                    slow_ma_period = st.slider(
                        "Období dlouhodobého MA",
                        min_value=10,
                        max_value=200,
                        value=21,
                        step=1,
                        key="ma_crossover_slow_period"
                    )
                    
                    trade_direction = st.selectbox(
                        "Směr obchodování",
                        options=["long", "short", "both"],
                        index=2,
                        format_func=lambda x: {"long": "Pouze long", "short": "Pouze short", "both": "Long i short"}[x],
                        key="ma_crossover_trade_direction"
                    )
                
                with col2:
                    use_rsi_filter = st.checkbox(
                        "Použít RSI filtr",
                        value=False,
                        key="ma_crossover_use_rsi_filter"
                    )
                    
                    if use_rsi_filter:
                        rsi_period = st.slider(
                            "RSI období",
                            min_value=2,
                            max_value=30,
                            value=14,
                            step=1,
                            key="ma_crossover_rsi_period"
                        )
                        
                        rsi_overbought = st.slider(
                            "RSI přeprodanost",
                            min_value=50,
                            max_value=90,
                            value=70,
                            step=1,
                            key="ma_crossover_rsi_overbought"
                        )
                        
                        rsi_oversold = st.slider(
                            "RSI překoupenost",
                            min_value=10,
                            max_value=50,
                            value=30,
                            step=1,
                            key="ma_crossover_rsi_oversold"
                        )
                    
                    use_atr_for_sl = st.checkbox(
                        "Použít ATR pro stop-loss",
                        value=True,
                        key="ma_crossover_use_atr_for_sl"
                    )
                    
                    if use_atr_for_sl:
                        atr_period = st.slider(
                            "ATR období",
                            min_value=5,
                            max_value=30,
                            value=14,
                            step=1,
                            key="ma_crossover_atr_period"
                        )
                        
                        atr_multiplier = st.slider(
                            "ATR násobič",
                            min_value=0.5,
                            max_value=3.0,
                            value=1.5,
                            step=0.1,
                            key="ma_crossover_atr_multiplier"
                        )
                    else:
                        stop_loss_pips = st.slider(
                            "Stop-loss (% od vstupní ceny)",
                            min_value=0.1,
                            max_value=2.0,
                            value=0.5,
                            step=0.1,
                            key="ma_crossover_stop_loss_pips"
                        )
                    
                    take_profit_pips = st.text_input(
                        "Take-profit úrovně (% od vstupní ceny, oddělené čárkou)",
                        value="1.25, 2.0, 3.0",
                        key="ma_crossover_take_profit_pips"
                    )
                    
                    risk_reward_ratio = st.slider(
                        "Minimální poměr rizika k zisku",
                        min_value=1.0,
                        max_value=5.0,
                        value=2.5,
                        step=0.1,
                        key="ma_crossover_risk_reward_ratio"
                    )
            
            # RSI Strategy nastavení
            if use_rsi_strategy:
                st.subheader("RSI Strategy")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    rsi_period_strategy = st.slider(
                        "RSI období",
                        min_value=2,
                        max_value=30,
                        value=14,
                        step=1,
                        key="rsi_strategy_period"
                    )
                    
                    rsi_overbought_strategy = st.slider(
                        "RSI hranice překoupenosti",
                        min_value=50,
                        max_value=90,
                        value=70,
                        step=1,
                        key="rsi_strategy_overbought"
                    )
                    
                    rsi_oversold_strategy = st.slider(
                        "RSI hranice přeprodanosti",
                        min_value=10,
                        max_value=50,
                        value=30,
                        step=1,
                        key="rsi_strategy_oversold"
                    )
                    
                    exit_rsi_level = st.slider(
                        "RSI úroveň pro výstup",
                        min_value=30,
                        max_value=70,
                        value=50,
                        step=1,
                        key="rsi_strategy_exit_level"
                    )
                    
                    trade_direction_rsi = st.selectbox(
                        "Směr obchodování",
                        options=["long", "short", "both"],
                        index=2,
                        format_func=lambda x: {"long": "Pouze long", "short": "Pouze short", "both": "Long i short"}[x],
                        key="rsi_strategy_trade_direction"
                    )
                
                with col2:
                    use_ma_filter_rsi = st.checkbox(
                        "Použít MA filtr",
                        value=False,
                        key="rsi_strategy_use_ma_filter"
                    )
                    
                    if use_ma_filter_rsi:
                        ma_type_rsi = st.selectbox(
                            "Typ klouzavého průměru",
                            options=["SMA", "EMA"],
                            index=0,
                            key="rsi_strategy_ma_type"
                        )
                        
                        ma_period_rsi = st.slider(
                            "MA období",
                            min_value=10,
                            max_value=200,
                            value=200,
                            step=5,
                            key="rsi_strategy_ma_period"
                        )
                    
                    use_atr_for_sl_rsi = st.checkbox(
                        "Použít ATR pro stop-loss",
                        value=True,
                        key="rsi_strategy_use_atr_for_sl"
                    )
                    
                    if use_atr_for_sl_rsi:
                        atr_period_rsi = st.slider(
                            "ATR období",
                            min_value=5,
                            max_value=30,
                            value=14,
                            step=1,
                            key="rsi_strategy_atr_period"
                        )
                        
                        atr_multiplier_rsi = st.slider(
                            "ATR násobič",
                            min_value=0.5,
                            max_value=3.0,
                            value=1.5,
                            step=0.1,
                            key="rsi_strategy_atr_multiplier"
                        )
                    else:
                        stop_loss_pips_rsi = st.slider(
                            "Stop-loss (% od vstupní ceny)",
                            min_value=0.1,
                            max_value=2.0,
                            value=0.5,
                            step=0.1,
                            key="rsi_strategy_stop_loss_pips"
                        )
                    
                    take_profit_pips_rsi = st.text_input(
                        "Take-profit úrovně (% od vstupní ceny, oddělené čárkou)",
                        value="1.25, 2.0, 3.0",
                        key="rsi_strategy_take_profit_pips"
                    )
                    
                    risk_reward_ratio_rsi = st.slider(
                        "Minimální poměr rizika k zisku",
                        min_value=1.0,
                        max_value=5.0,
                        value=2.5,
                        step=0.1,
                        key="rsi_strategy_risk_reward_ratio"
                    )
                    
                    wait_for_exit = st.checkbox(
                        "Čekat na výstup před novým vstupem",
                        value=True,
                        key="rsi_strategy_wait_for_exit"
                    )
            
            # Tlačítko pro spuštění backtestu
            if st.button("Spustit backtest"):
                with st.spinner("Probíhá backtest..."):
                    backtest_results = []
                    
                    # Moving Average Crossover
                    if use_ma_crossover:
                        # Parsování parametrů
                        ma_crossover_params = {
                            "fast_ma_period": int(fast_ma_period),
                            "slow_ma_period": int(slow_ma_period),
                            "ma_type": ma_type.lower(),
                            "trade_direction": trade_direction,
                            "risk_reward_ratio": float(risk_reward_ratio),
                            "use_atr_for_sl": use_atr_for_sl,
                        }
                        
                        if use_atr_for_sl:
                            ma_crossover_params.update({
                                "atr_period": int(atr_period),
                                "atr_multiplier": float(atr_multiplier)
                            })
                        else:
                            ma_crossover_params.update({
                                "stop_loss_pips": float(stop_loss_pips)
                            })
                        
                        # Parse take-profit úrovně
                        try:
                            take_profit_list = [float(x.strip()) for x in take_profit_pips.split(",")]
                            ma_crossover_params["take_profit_pips"] = take_profit_list
                        except:
                            st.warning("Neplatný formát take-profit úrovní. Použity výchozí hodnoty.")
                        
                        if use_rsi_filter:
                            ma_crossover_params.update({
                                "use_rsi_filter": True,
                                "rsi_period": int(rsi_period),
                                "rsi_overbought": int(rsi_overbought),
                                "rsi_oversold": int(rsi_oversold)
                            })
                        
                        # Vytvoření strategie
                        ma_strategy = MovingAverageCrossover(
                            name=f"MA Crossover ({ma_type} {fast_ma_period}/{slow_ma_period})",
                            parameters=ma_crossover_params
                        )
                        
                        # Spuštění backtestu
                        ma_results = ma_strategy.backtest(st.session_state.historical_data)
                        backtest_results.append(ma_results)
                    
                    # RSI Strategy
                    if use_rsi_strategy:
                        # Parsování parametrů
                        rsi_strategy_params = {
                            "rsi_period": int(rsi_period_strategy),
                            "rsi_overbought": int(rsi_overbought_strategy),
                            "rsi_oversold": int(rsi_oversold_strategy),
                            "exit_rsi_level": int(exit_rsi_level),
                            "trade_direction": trade_direction_rsi,
                            "risk_reward_ratio": float(risk_reward_ratio_rsi),
                            "use_atr_for_sl": use_atr_for_sl_rsi,
                            "wait_for_exit_before_new_entry": wait_for_exit
                        }
                        
                        if use_atr_for_sl_rsi:
                            rsi_strategy_params.update({
                                "atr_period": int(atr_period_rsi),
                                "atr_multiplier": float(atr_multiplier_rsi)
                            })
                        else:
                            rsi_strategy_params.update({
                                "stop_loss_pips": float(stop_loss_pips_rsi)
                            })
                        
                        # Parse take-profit úrovně
                        try:
                            take_profit_list = [float(x.strip()) for x in take_profit_pips_rsi.split(",")]
                            rsi_strategy_params["take_profit_pips"] = take_profit_list
                        except:
                            st.warning("Neplatný formát take-profit úrovní. Použity výchozí hodnoty.")
                        
                        if use_ma_filter_rsi:
                            rsi_strategy_params.update({
                                "use_ma_filter": True,
                                "ma_period": int(ma_period_rsi),
                                "ma_type": ma_type_rsi.lower()
                            })
                        
                        # Vytvoření strategie
                        rsi_strategy = RSIStrategy(
                            name=f"RSI Strategy (RSI {rsi_period_strategy})",
                            parameters=rsi_strategy_params
                        )
                        
                        # Spuštění backtestu
                        rsi_results = rsi_strategy.backtest(st.session_state.historical_data)
                        backtest_results.append(rsi_results)
                    
                    # Uložení výsledků
                    st.session_state.backtest_results = backtest_results
                    
                    st.success("Backtest dokončen!")
        
        # Záložka s výsledky backtestu
        with tabs[2]:
            if st.session_state.backtest_results:
                st.header("Výsledky backtestu")
                
                # Výběr strategie
                strategy_names = [result["strategy_name"] for result in st.session_state.backtest_results]
                selected_strategy = st.selectbox("Vyberte strategii", options=strategy_names)
                
                # Získání výsledků zvolené strategie
                selected_result = next((result for result in st.session_state.backtest_results 
                                       if result["strategy_name"] == selected_strategy), None)
                
                if selected_result:
                    # Základní metriky
                    metrics = selected_result["metrics"]
                    
                    # Zobrazení metrik v multi-columns
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Celkový zisk/ztráta", f"{metrics['total_profit']:.2f}%")
                        st.metric("Počet obchodů", f"{metrics['total_trades']}")
                    
                    with col2:
                        st.metric("Win Rate", f"{metrics['win_rate']*100:.2f}%")
                        st.metric("Ziskové obchody", f"{metrics['winning_trades']}")
                    
                    with col3:
                        st.metric("Profit Factor", f"{metrics['profit_factor']:.2f}")
                        st.metric("Ztrátové obchody", f"{metrics['losing_trades']}")
                    
                    with col4:
                        st.metric("Max. Drawdown", f"{metrics['max_drawdown']:.2f}%")
                        st.metric("Očekávaná hodnota", f"{metrics['expectancy']:.4f}%")
                    
                    # Equity křivka
                    trades = selected_result["trades"]
                    
                    if trades:
                        # Seřazení obchodů podle času ukončení
                        closed_trades = [t for t in trades if t.status != TradeStatus.OPEN and t.exit_time is not None]
                        
                        if closed_trades:
                            sorted_trades = sorted(closed_trades, key=lambda t: t.exit_time)
                            
                            # Příprava dat
                            dates = [t.exit_time for t in sorted_trades]
                            profits = [t.profit_percentage for t in sorted_trades]
                            cumulative_profits = np.cumsum(profits)
                            
                            # Vytvoření grafu
                            fig = go.Figure()
                            
                            # Equity křivka
                            fig.add_trace(go.Scatter(
                                x=dates,
                                y=cumulative_profits,
                                mode='lines',
                                name='Kumulativní zisk/ztráta (%)',
                                line=dict(color='blue', width=2)
                            ))
                            
                            # Přidání jednotlivých obchodů
                            for i, trade in enumerate(sorted_trades):
                                color = 'green' if trade.status == TradeStatus.CLOSED_PROFIT else 'red'
                                fig.add_trace(go.Scatter(
                                    x=[trade.exit_time],
                                    y=[cumulative_profits[i]],
                                    mode='markers',
                                    marker=dict(color=color, size=8),
                                    name=f"Obchod {i+1}",
                                    showlegend=False,
                                    hoverinfo='text',
                                    hovertext=f"Obchod {i+1}<br>Typ: {trade.trade_type.value}<br>Vstup: {trade.entry_price:.2f}<br>Výstup: {trade.exit_price:.2f}<br>Zisk/Ztráta: {trade.profit_percentage:.2f}%<br>Důvod: {trade.exit_reason}"
                                ))
                            
                            # Nastavení grafu
                            fig.update_layout(
                                title=f"Equity křivka - {selected_strategy}",
                                xaxis_title="Datum/Čas",
                                yaxis_title="Kumulativní zisk/ztráta (%)",
                                hovermode="closest",
                                template="plotly_white"
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    
                        # Tabulka obchodů
                        if trades:
                            st.subheader("Seznam obchodů")
                            
                            # Připravíme data pro tabulku
                            trade_data = []
                            for i, trade in enumerate(trades):
                                trade_data.append({
                                    "Č.": i + 1,
                                    "Typ": trade.trade_type.value,
                                    "Vstup. cena": f"{trade.entry_price:.2f}",
                                    "Stop-Loss": f"{trade.stop_loss:.2f}",
                                    "Výstup. cena": f"{trade.exit_price:.2f}" if trade.exit_price is not None else "N/A",
                                    "Zisk/Ztráta (%)": f"{trade.profit_percentage:.2f}%" if trade.profit_percentage is not None else "N/A",
                                    "Stav": trade.status.value,
                                    "Důvod výstupu": trade.exit_reason if trade.exit_reason is not None else "N/A"
                                })
                            
                            trade_df = pd.DataFrame(trade_data)
                            st.dataframe(trade_df, use_container_width=True)
                    else:
                        st.info("Žádné obchody nebyly generovány.")
            else:
                st.info("Nejsou k dispozici žádné výsledky backtestu. Spusťte backtest v záložce 'Nastavení strategií'.")
        
        # Záložka s porovnáním strategií
        with tabs[3]:
            if st.session_state.backtest_results and len(st.session_state.backtest_results) > 1:
                st.header("Porovnání strategií")
                
                # Vytvoření porovnávacího grafu
                comparison_fig = plot_strategy_comparison(st.session_state.backtest_results)
                st.plotly_chart(comparison_fig, use_container_width=True)
                
                # Tabulka s metrikami pro porovnání
                st.subheader("Porovnání metrik výkonnosti")
                
                comparison_data = []
                for result in st.session_state.backtest_results:
                    comparison_data.append({
                        "Strategie": result["strategy_name"],
                        "Celkový zisk/ztráta (%)": f"{result['metrics']['total_profit']:.2f}%",
                        "Win Rate (%)": f"{result['metrics']['win_rate']*100:.2f}%",
                        "Počet obchodů": result['metrics']['total_trades'],
                        "Ziskové obchody": result['metrics']['winning_trades'],
                        "Ztrátové obchody": result['metrics']['losing_trades'],
                        "Profit Factor": f"{result['metrics']['profit_factor']:.2f}",
                        "Max. Drawdown (%)": f"{result['metrics']['max_drawdown']:.2f}%",
                        "Očekávaná hodnota (%)": f"{result['metrics']['expectancy']:.4f}%"
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df, use_container_width=True)
            else:
                st.info("Pro porovnání strategií musíte spustit backtest alespoň pro dvě strategie.")
    else:
        st.info("Nejprve načtěte historická data pomocí tlačítka 'Načíst historická data' v postranním panelu.")

# Spuštění aplikace
if __name__ == "__main__":
    strategy_comparison_app()