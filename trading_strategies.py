import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from enum import Enum

class TradeType(Enum):
    """Typy obchodních příkazů."""
    BUY = "NÁKUP"  # Dlouhá pozice
    SELL = "PRODEJ"  # Krátká pozice
    
class TradeStatus(Enum):
    """Stavy obchodů."""
    OPEN = "OTEVŘENÝ"  # Aktivní obchod
    CLOSED_PROFIT = "UZAVŘENÝ (ZISK)"  # Uzavřený obchod se ziskem
    CLOSED_LOSS = "UZAVŘENÝ (ZTRÁTA)"  # Uzavřený obchod se ztrátou
    CLOSED_EVEN = "UZAVŘENÝ (BREAK-EVEN)"  # Uzavřený obchod na nule

@dataclass
class Trade:
    """Reprezentace jednoho obchodu."""
    symbol: str  # Symbol instrumentu
    trade_type: TradeType  # Typ obchodu (NÁKUP/PRODEJ)
    entry_price: float  # Vstupní cena
    entry_time: Any  # Čas vstupu
    stop_loss: float  # Stop-loss úroveň
    take_profit: List[float]  # Seznam take-profit úrovní
    status: TradeStatus = TradeStatus.OPEN  # Výchozí stav: otevřený
    exit_price: Optional[float] = None  # Výstupní cena (None pro otevřené obchody)
    exit_time: Optional[Any] = None  # Čas výstupu (None pro otevřené obchody)
    profit_pips: Optional[float] = None  # Zisk/ztráta v pipech
    profit_percentage: Optional[float] = None  # Zisk/ztráta v procentech
    exit_reason: Optional[str] = None  # Důvod ukončení obchodu
    
    def calculate_risk_reward(self) -> float:
        """Vypočítá poměr rizika k zisku pro první cíl."""
        if not self.take_profit:
            return 0.0
            
        if self.trade_type == TradeType.BUY:
            risk = self.entry_price - self.stop_loss
            reward = self.take_profit[0] - self.entry_price
        else:  # SELL
            risk = self.stop_loss - self.entry_price
            reward = self.entry_price - self.take_profit[0]
            
        if risk <= 0:
            return 0.0  # Neplatný poměr rizika k zisku
            
        return reward / risk
        
    def calculate_profit(self, current_price: float) -> Tuple[float, float]:
        """Vypočítá aktuální zisk/ztrátu obchodu."""
        if self.trade_type == TradeType.BUY:
            diff_pips = current_price - self.entry_price
        else:  # SELL
            diff_pips = self.entry_price - current_price
            
        # Převod na procenta
        percentage = (diff_pips / self.entry_price) * 100
        
        return diff_pips, percentage
        
    def check_exit_conditions(self, high: float, low: float, time: Any) -> bool:
        """
        Zkontroluje, zda byly splněny podmínky pro ukončení obchodu.
        Vrací True, pokud byl obchod uzavřen, jinak False.
        """
        if self.status != TradeStatus.OPEN:
            return False  # Obchod je již uzavřen
            
        # Kontrola stop-loss
        if self.trade_type == TradeType.BUY and low <= self.stop_loss:
            self.exit_price = self.stop_loss
            self.exit_time = time
            self.status = TradeStatus.CLOSED_LOSS
            self.exit_reason = "Stop-Loss"
            self.profit_pips, self.profit_percentage = self.calculate_profit(self.exit_price)
            return True
            
        elif self.trade_type == TradeType.SELL and high >= self.stop_loss:
            self.exit_price = self.stop_loss
            self.exit_time = time
            self.status = TradeStatus.CLOSED_LOSS
            self.exit_reason = "Stop-Loss"
            self.profit_pips, self.profit_percentage = self.calculate_profit(self.exit_price)
            return True
            
        # Kontrola take-profit úrovní
        for i, tp_level in enumerate(self.take_profit):
            if self.trade_type == TradeType.BUY and high >= tp_level:
                self.exit_price = tp_level
                self.exit_time = time
                self.status = TradeStatus.CLOSED_PROFIT
                self.exit_reason = f"Take-Profit {i+1}"
                self.profit_pips, self.profit_percentage = self.calculate_profit(self.exit_price)
                return True
                
            elif self.trade_type == TradeType.SELL and low <= tp_level:
                self.exit_price = tp_level
                self.exit_time = time
                self.status = TradeStatus.CLOSED_PROFIT
                self.exit_reason = f"Take-Profit {i+1}"
                self.profit_pips, self.profit_percentage = self.calculate_profit(self.exit_price)
                return True
                
        return False  # Žádná podmínka pro ukončení nebyla splněna


class TradingStrategy:
    """Základní třída pro obchodní strategie."""
    
    def __init__(self, name: str, parameters: Dict[str, Any] = None):
        """
        Inicializace strategie.
        
        Args:
            name: Název strategie
            parameters: Slovník parametrů strategie
        """
        self.name = name
        self.parameters = parameters or {}
        self.trades: List[Trade] = []
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generuje obchodní signály na základě historických dat.
        
        Args:
            df: DataFrame s historickými daty (OHLCV)
            
        Returns:
            DataFrame s přidanými sloupci pro signály
        """
        raise NotImplementedError("Tuto metodu musí implementovat potomci.")
        
    def backtest(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Spustí backtest strategie na historických datech.
        
        Args:
            df: DataFrame s historickými daty (OHLCV)
            
        Returns:
            Slovník s výsledky backtestu
        """
        # Resetování obchodů
        self.trades = []
        
        # Generování signálů
        signals_df = self.generate_signals(df)
        
        # Simulace obchodů
        self._simulate_trades(signals_df)
        
        # Výpočet metrik výkonnosti
        metrics = self._calculate_performance_metrics()
        
        return {
            "strategy_name": self.name,
            "parameters": self.parameters,
            "metrics": metrics,
            "trades": self.trades
        }
        
    def _simulate_trades(self, df: pd.DataFrame) -> None:
        """
        Simuluje obchody na základě signálů.
        
        Args:
            df: DataFrame se signály
        """
        raise NotImplementedError("Tuto metodu musí implementovat potomci.")
        
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """
        Vypočítá metriky výkonnosti strategie.
        
        Returns:
            Slovník s metrikami výkonnosti
        """
        if not self.trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "max_drawdown": 0.0,
                "avg_profit": 0.0,
                "avg_loss": 0.0,
                "expectancy": 0.0,
                "total_profit": 0.0
            }
            
        # Celkový počet obchodů
        total_trades = len(self.trades)
        
        # Uzavřené obchody
        closed_trades = [t for t in self.trades if t.status != TradeStatus.OPEN]
        closed_count = len(closed_trades)
        
        if closed_count == 0:
            return {
                "total_trades": total_trades,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "max_drawdown": 0.0,
                "avg_profit": 0.0,
                "avg_loss": 0.0,
                "expectancy": 0.0,
                "total_profit": 0.0
            }
            
        # Ziskové obchody
        winning_trades = [t for t in closed_trades if t.status == TradeStatus.CLOSED_PROFIT]
        winning_count = len(winning_trades)
        
        # Ztrátové obchody
        losing_trades = [t for t in closed_trades if t.status == TradeStatus.CLOSED_LOSS]
        losing_count = len(losing_trades)
        
        # Win rate
        win_rate = winning_count / closed_count if closed_count > 0 else 0.0
        
        # Celkový zisk/ztráta
        total_profit = sum(t.profit_percentage for t in closed_trades) if closed_trades else 0.0
        
        # Hrubý zisk
        gross_profit = sum(t.profit_percentage for t in winning_trades) if winning_trades else 0.0
        
        # Hrubá ztráta
        gross_loss = abs(sum(t.profit_percentage for t in losing_trades)) if losing_trades else 0.0
        
        # Profit factor
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0.0
        
        # Průměrný zisk
        avg_profit = gross_profit / winning_count if winning_count > 0 else 0.0
        
        # Průměrná ztráta
        avg_loss = gross_loss / losing_count if losing_count > 0 else 0.0
        
        # Očekávaná hodnota obchodu
        expectancy = (win_rate * avg_profit) - ((1 - win_rate) * avg_loss)
        
        # Maximum drawdown (zjednodušená implementace)
        # Pro přesnější výpočet by bylo třeba sledovat equity průběžně v čase
        max_drawdown = 0.0
        if closed_trades:
            equity_curve = []
            running_balance = 0.0
            
            for trade in sorted(closed_trades, key=lambda t: t.entry_time):
                if trade.profit_percentage is not None:
                    running_balance += trade.profit_percentage
                    equity_curve.append(running_balance)
            
            if equity_curve:
                peak = 0.0
                for balance in equity_curve:
                    if balance > peak:
                        peak = balance
                    drawdown = peak - balance
                    max_drawdown = max(max_drawdown, drawdown)
        
        return {
            "total_trades": total_trades,
            "closed_trades": closed_count,
            "winning_trades": winning_count,
            "losing_trades": losing_count,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "avg_profit": avg_profit,
            "avg_loss": avg_loss,
            "expectancy": expectancy,
            "total_profit": total_profit
        }
        
    def plot_equity_curve(self, figsize=(12, 6)) -> None:
        """
        Vykreslí equity křivku strategie.
        
        Args:
            figsize: Velikost grafu
        """
        if not self.trades:
            print("Žádné obchody k vykreslení.")
            return
            
        # Uzavřené obchody
        closed_trades = [t for t in self.trades if t.status != TradeStatus.OPEN and t.exit_time is not None]
        
        if not closed_trades:
            print("Žádné uzavřené obchody k vykreslení.")
            return
            
        # Seřazení obchodů podle času ukončení
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
            title=f"Equity křivka - {self.name}",
            xaxis_title="Datum/Čas",
            yaxis_title="Kumulativní zisk/ztráta (%)",
            hovermode="closest",
            template="plotly_white"
        )
        
        return fig


class MovingAverageCrossover(TradingStrategy):
    """Strategie založená na křížení klouzavých průměrů."""
    
    def __init__(self, name: str = "MA Crossover", parameters: Dict[str, Any] = None):
        """
        Inicializace strategie.
        
        Args:
            name: Název strategie
            parameters: Slovník parametrů strategie
        """
        default_params = {
            "fast_ma_period": 9,  # Období krátkodobého klouzavého průměru
            "slow_ma_period": 21,  # Období dlouhodobého klouzavého průměru
            "ma_type": "sma",  # Typ klouzavého průměru ('sma' nebo 'ema')
            "risk_reward_ratio": 2.5,  # Minimální poměr rizika k zisku
            "stop_loss_pips": 0.5,  # Stop-loss v % od vstupní ceny
            "take_profit_pips": [1.25, 2.0, 3.0],  # Take-profit úrovně v % od vstupní ceny
            "use_atr_for_sl": False,  # Použít ATR pro nastavení stop-loss?
            "atr_multiplier": 1.5,  # Násobič ATR pro stop-loss
            "atr_period": 14,  # Období pro ATR
            "trade_direction": "both",  # Směr obchodování ('long', 'short', 'both')
            "use_rsi_filter": False,  # Použít RSI filtr?
            "rsi_period": 14,  # Období pro RSI
            "rsi_overbought": 70,  # Hranice překoupenosti
            "rsi_oversold": 30  # Hranice přeprodanosti
        }
        
        # Sloučení výchozích parametrů s uživatelskými
        merged_params = {**default_params, **(parameters or {})}
        
        super().__init__(name, merged_params)
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generuje obchodní signály na základě křížení klouzavých průměrů.
        
        Args:
            df: DataFrame s historickými daty (OHLCV)
            
        Returns:
            DataFrame s přidanými sloupci pro signály
        """
        # Kopie DataFramu
        result = df.copy()
        
        # Získání parametrů
        fast_period = self.parameters["fast_ma_period"]
        slow_period = self.parameters["slow_ma_period"]
        ma_type = self.parameters["ma_type"]
        
        # Výpočet klouzavých průměrů
        if ma_type.lower() == "sma":
            result[f'fast_ma'] = result['close'].rolling(window=fast_period).mean()
            result[f'slow_ma'] = result['close'].rolling(window=slow_period).mean()
        elif ma_type.lower() == "ema":
            result[f'fast_ma'] = result['close'].ewm(span=fast_period, adjust=False).mean()
            result[f'slow_ma'] = result['close'].ewm(span=slow_period, adjust=False).mean()
        else:
            raise ValueError(f"Neznámý typ klouzavého průměru: {ma_type}")
        
        # Výpočet RSI, pokud je potřeba
        if self.parameters["use_rsi_filter"]:
            rsi_period = self.parameters["rsi_period"]
            delta = result['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=rsi_period).mean()
            avg_loss = loss.rolling(window=rsi_period).mean()
            rs = avg_gain / avg_loss
            result['rsi'] = 100 - (100 / (1 + rs))
        
        # Výpočet ATR, pokud je potřeba
        if self.parameters["use_atr_for_sl"]:
            atr_period = self.parameters["atr_period"]
            tr1 = result['high'] - result['low']
            tr2 = abs(result['high'] - result['close'].shift())
            tr3 = abs(result['low'] - result['close'].shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            result['atr'] = tr.rolling(window=atr_period).mean()
        
        # Inicializace signálů
        result['buy_signal'] = False
        result['sell_signal'] = False
        
        # Generování signálů na základě křížení klouzavých průměrů
        # Buy signal: fast_ma křižuje slow_ma zespoda
        # Sell signal: fast_ma křižuje slow_ma shora
        for i in range(1, len(result)):
            # Předchozí stav: fast_ma < slow_ma
            prev_fast_below_slow = result['fast_ma'].iloc[i-1] < result['slow_ma'].iloc[i-1]
            
            # Aktuální stav: fast_ma > slow_ma
            curr_fast_above_slow = result['fast_ma'].iloc[i] > result['slow_ma'].iloc[i]
            
            # Buy signal
            if prev_fast_below_slow and curr_fast_above_slow:
                # Aplikace filtrů
                if self._apply_filters(result, i, "buy"):
                    result.loc[result.index[i], 'buy_signal'] = True
            
            # Sell signal
            elif not prev_fast_below_slow and not curr_fast_above_slow:
                # Aplikace filtrů
                if self._apply_filters(result, i, "sell"):
                    result.loc[result.index[i], 'sell_signal'] = True
        
        return result
        
    def _apply_filters(self, df: pd.DataFrame, index: int, signal_type: str) -> bool:
        """
        Aplikuje filtry na signál.
        
        Args:
            df: DataFrame s daty
            index: Index aktuálního záznamu
            signal_type: Typ signálu ('buy' nebo 'sell')
            
        Returns:
            True, pokud signál prošel všemi filtry, jinak False
        """
        # Směr obchodování
        trade_direction = self.parameters["trade_direction"]
        if trade_direction == "long" and signal_type == "sell":
            return False
        if trade_direction == "short" and signal_type == "buy":
            return False
        
        # RSI filtr
        if self.parameters["use_rsi_filter"]:
            rsi = df['rsi'].iloc[index]
            if signal_type == "buy" and rsi >= self.parameters["rsi_overbought"]:
                return False
            if signal_type == "sell" and rsi <= self.parameters["rsi_oversold"]:
                return False
        
        return True
        
    def _simulate_trades(self, df: pd.DataFrame) -> None:
        """
        Simuluje obchody na základě signálů.
        
        Args:
            df: DataFrame se signály
        """
        for i in range(len(df) - 1):  # -1, protože potřebujeme i+1 pro kontrolu uzavření
            # Buy signál
            if df['buy_signal'].iloc[i]:
                entry_price = df['close'].iloc[i]
                entry_time = df.index[i]
                
                # Nastavení stop-loss
                if self.parameters["use_atr_for_sl"]:
                    stop_loss = entry_price - (df['atr'].iloc[i] * self.parameters["atr_multiplier"])
                else:
                    stop_loss = entry_price * (1 - self.parameters["stop_loss_pips"] / 100)
                
                # Nastavení take-profit úrovní
                take_profit = [entry_price * (1 + tp_pips / 100) for tp_pips in self.parameters["take_profit_pips"]]
                
                # Kontrola minimálního poměru rizika k zisku
                risk = entry_price - stop_loss
                reward = take_profit[0] - entry_price
                rr_ratio = reward / risk if risk > 0 else 0
                
                if rr_ratio >= self.parameters["risk_reward_ratio"]:
                    # Vytvoření obchodu
                    trade = Trade(
                        symbol=df.get('symbol', ['Unknown'])[0] if isinstance(df.get('symbol'), pd.Series) else "Unknown",
                        trade_type=TradeType.BUY,
                        entry_price=entry_price,
                        entry_time=entry_time,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        status=TradeStatus.OPEN
                    )
                    
                    # Simulace výsledku obchodu
                    for j in range(i + 1, len(df)):
                        if trade.check_exit_conditions(df['high'].iloc[j], df['low'].iloc[j], df.index[j]):
                            break
                    
                    # Pokud obchod nebyl uzavřen, uzavřeme ho na poslední ceně
                    if trade.status == TradeStatus.OPEN:
                        trade.exit_price = df['close'].iloc[-1]
                        trade.exit_time = df.index[-1]
                        trade.status = TradeStatus.CLOSED_PROFIT if trade.exit_price > trade.entry_price else TradeStatus.CLOSED_LOSS
                        trade.profit_pips, trade.profit_percentage = trade.calculate_profit(trade.exit_price)
                        trade.exit_reason = "Konec backtestu"
                    
                    # Přidání obchodu do seznamu
                    self.trades.append(trade)
            
            # Sell signál
            if df['sell_signal'].iloc[i]:
                entry_price = df['close'].iloc[i]
                entry_time = df.index[i]
                
                # Nastavení stop-loss
                if self.parameters["use_atr_for_sl"]:
                    stop_loss = entry_price + (df['atr'].iloc[i] * self.parameters["atr_multiplier"])
                else:
                    stop_loss = entry_price * (1 + self.parameters["stop_loss_pips"] / 100)
                
                # Nastavení take-profit úrovní
                take_profit = [entry_price * (1 - tp_pips / 100) for tp_pips in self.parameters["take_profit_pips"]]
                
                # Kontrola minimálního poměru rizika k zisku
                risk = stop_loss - entry_price
                reward = entry_price - take_profit[0]
                rr_ratio = reward / risk if risk > 0 else 0
                
                if rr_ratio >= self.parameters["risk_reward_ratio"]:
                    # Vytvoření obchodu
                    trade = Trade(
                        symbol=df.get('symbol', ['Unknown'])[0] if isinstance(df.get('symbol'), pd.Series) else "Unknown",
                        trade_type=TradeType.SELL,
                        entry_price=entry_price,
                        entry_time=entry_time,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        status=TradeStatus.OPEN
                    )
                    
                    # Simulace výsledku obchodu
                    for j in range(i + 1, len(df)):
                        if trade.check_exit_conditions(df['high'].iloc[j], df['low'].iloc[j], df.index[j]):
                            break
                    
                    # Pokud obchod nebyl uzavřen, uzavřeme ho na poslední ceně
                    if trade.status == TradeStatus.OPEN:
                        trade.exit_price = df['close'].iloc[-1]
                        trade.exit_time = df.index[-1]
                        trade.status = TradeStatus.CLOSED_PROFIT if trade.exit_price < trade.entry_price else TradeStatus.CLOSED_LOSS
                        trade.profit_pips, trade.profit_percentage = trade.calculate_profit(trade.exit_price)
                        trade.exit_reason = "Konec backtestu"
                    
                    # Přidání obchodu do seznamu
                    self.trades.append(trade)


class RSIStrategy(TradingStrategy):
    """Strategie založená na RSI (Relative Strength Index)."""
    
    def __init__(self, name: str = "RSI Strategy", parameters: Dict[str, Any] = None):
        """
        Inicializace strategie.
        
        Args:
            name: Název strategie
            parameters: Slovník parametrů strategie
        """
        default_params = {
            "rsi_period": 14,  # Období pro RSI
            "rsi_overbought": 70,  # Hranice překoupenosti
            "rsi_oversold": 30,  # Hranice přeprodanosti
            "exit_rsi_level": 50,  # RSI úroveň pro výstup
            "use_ma_filter": False,  # Použít filtr klouzavého průměru?
            "ma_period": 200,  # Období klouzavého průměru
            "ma_type": "sma",  # Typ klouzavého průměru ('sma' nebo 'ema')
            "risk_reward_ratio": 2.5,  # Minimální poměr rizika k zisku
            "stop_loss_pips": 0.5,  # Stop-loss v % od vstupní ceny
            "take_profit_pips": [1.25, 2.0, 3.0],  # Take-profit úrovně v % od vstupní ceny
            "use_atr_for_sl": False,  # Použít ATR pro nastavení stop-loss?
            "atr_multiplier": 1.5,  # Násobič ATR pro stop-loss
            "atr_period": 14,  # Období pro ATR
            "trade_direction": "both",  # Směr obchodování ('long', 'short', 'both')
            "wait_for_exit_before_new_entry": True  # Čekat na výstup před novým vstupem?
        }
        
        # Sloučení výchozích parametrů s uživatelskými
        merged_params = {**default_params, **(parameters or {})}
        
        super().__init__(name, merged_params)
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generuje obchodní signály na základě RSI.
        
        Args:
            df: DataFrame s historickými daty (OHLCV)
            
        Returns:
            DataFrame s přidanými sloupci pro signály
        """
        # Kopie DataFramu
        result = df.copy()
        
        # Výpočet RSI
        rsi_period = self.parameters["rsi_period"]
        delta = result['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=rsi_period).mean()
        avg_loss = loss.rolling(window=rsi_period).mean()
        rs = avg_gain / avg_loss
        result['rsi'] = 100 - (100 / (1 + rs))
        
        # Výpočet klouzavého průměru, pokud je potřeba
        if self.parameters["use_ma_filter"]:
            ma_period = self.parameters["ma_period"]
            ma_type = self.parameters["ma_type"]
            
            if ma_type.lower() == "sma":
                result['ma'] = result['close'].rolling(window=ma_period).mean()
            elif ma_type.lower() == "ema":
                result['ma'] = result['close'].ewm(span=ma_period, adjust=False).mean()
            else:
                raise ValueError(f"Neznámý typ klouzavého průměru: {ma_type}")
        
        # Výpočet ATR, pokud je potřeba
        if self.parameters["use_atr_for_sl"]:
            atr_period = self.parameters["atr_period"]
            tr1 = result['high'] - result['low']
            tr2 = abs(result['high'] - result['close'].shift())
            tr3 = abs(result['low'] - result['close'].shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            result['atr'] = tr.rolling(window=atr_period).mean()
        
        # Inicializace signálů
        result['buy_signal'] = False
        result['sell_signal'] = False
        result['exit_long_signal'] = False
        result['exit_short_signal'] = False
        
        # Generování signálů na základě RSI
        for i in range(1, len(result)):
            # RSI přechází z přeprodané oblasti
            rsi_oversold_exit = (result['rsi'].iloc[i-1] <= self.parameters["rsi_oversold"] and 
                            result['rsi'].iloc[i] > self.parameters["rsi_oversold"])
            
            # RSI přechází z překoupené oblasti
            rsi_overbought_exit = (result['rsi'].iloc[i-1] >= self.parameters["rsi_overbought"] and 
                                result['rsi'].iloc[i] < self.parameters["rsi_overbought"])
            
            # RSI přechází přes výstupní úroveň směrem nahoru
            rsi_exit_up = (result['rsi'].iloc[i-1] < self.parameters["exit_rsi_level"] and 
                        result['rsi'].iloc[i] >= self.parameters["exit_rsi_level"])
            
            # RSI přechází přes výstupní úroveň směrem dolů
            rsi_exit_down = (result['rsi'].iloc[i-1] > self.parameters["exit_rsi_level"] and 
                            result['rsi'].iloc[i] <= self.parameters["exit_rsi_level"])
            
            # Aplikace filtrů a generování signálů
            # Buy signal: RSI opouští přeprodanou oblast
            if rsi_oversold_exit and self._apply_filters(result, i, "buy"):
                result.loc[result.index[i], 'buy_signal'] = True
            
            # Sell signal: RSI opouští překoupenou oblast
            if rsi_overbought_exit and self._apply_filters(result, i, "sell"):
                result.loc[result.index[i], 'sell_signal'] = True
            
            # Exit long signal: RSI klesá pod výstupní úroveň
            if rsi_exit_down:
                result.loc[result.index[i], 'exit_long_signal'] = True
            
            # Exit short signal: RSI stoupá nad výstupní úroveň
            if rsi_exit_up:
                result.loc[result.index[i], 'exit_short_signal'] = True
        
        return result
        
    def _apply_filters(self, df: pd.DataFrame, index: int, signal_type: str) -> bool:
        """
        Aplikuje filtry na signál.
        
        Args:
            df: DataFrame s daty
            index: Index aktuálního záznamu
            signal_type: Typ signálu ('buy' nebo 'sell')
            
        Returns:
            True, pokud signál prošel všemi filtry, jinak False
        """
        # Směr obchodování
        trade_direction = self.parameters["trade_direction"]
        if trade_direction == "long" and signal_type == "sell":
            return False
        if trade_direction == "short" and signal_type == "buy":
            return False
        
        # Filtr klouzavého průměru
        if self.parameters["use_ma_filter"]:
            price = df['close'].iloc[index]
            ma = df['ma'].iloc[index]
            
            if signal_type == "buy" and price < ma:
                return False
            if signal_type == "sell" and price > ma:
                return False
        
        return True
        
    def _simulate_trades(self, df: pd.DataFrame) -> None:
        """
        Simuluje obchody na základě signálů.
        
        Args:
            df: DataFrame se signály
        """
        # Sledování aktivních obchodů
        active_long = False
        active_short = False
        
        for i in range(len(df) - 1):  # -1, protože potřebujeme i+1 pro kontrolu uzavření
            # Výstup z long pozice
            if active_long and df['exit_long_signal'].iloc[i]:
                active_long = False
            
            # Výstup z short pozice
            if active_short and df['exit_short_signal'].iloc[i]:
                active_short = False
            
            # Buy signál
            if df['buy_signal'].iloc[i] and (not active_long or not self.parameters["wait_for_exit_before_new_entry"]):
                entry_price = df['close'].iloc[i]
                entry_time = df.index[i]
                
                # Nastavení stop-loss
                if self.parameters["use_atr_for_sl"]:
                    stop_loss = entry_price - (df['atr'].iloc[i] * self.parameters["atr_multiplier"])
                else:
                    stop_loss = entry_price * (1 - self.parameters["stop_loss_pips"] / 100)
                
                # Nastavení take-profit úrovní
                take_profit = [entry_price * (1 + tp_pips / 100) for tp_pips in self.parameters["take_profit_pips"]]
                
                # Kontrola minimálního poměru rizika k zisku
                risk = entry_price - stop_loss
                reward = take_profit[0] - entry_price
                rr_ratio = reward / risk if risk > 0 else 0
                
                if rr_ratio >= self.parameters["risk_reward_ratio"]:
                    active_long = True
                    
                    # Vytvoření obchodu
                    trade = Trade(
                        symbol=df.get('symbol', ['Unknown'])[0] if isinstance(df.get('symbol'), pd.Series) else "Unknown",
                        trade_type=TradeType.BUY,
                        entry_price=entry_price,
                        entry_time=entry_time,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        status=TradeStatus.OPEN
                    )
                    
                    # Simulace výsledku obchodu
                    for j in range(i + 1, len(df)):
                        # Kontrola výstupu podle ceny
                        if trade.check_exit_conditions(df['high'].iloc[j], df['low'].iloc[j], df.index[j]):
                            active_long = False
                            break
                        
                        # Výstup podle RSI
                        if df['exit_long_signal'].iloc[j]:
                            trade.exit_price = df['close'].iloc[j]
                            trade.exit_time = df.index[j]
                            trade.status = TradeStatus.CLOSED_PROFIT if trade.exit_price > trade.entry_price else TradeStatus.CLOSED_LOSS
                            trade.profit_pips, trade.profit_percentage = trade.calculate_profit(trade.exit_price)
                            trade.exit_reason = "RSI Exit"
                            active_long = False
                            break
                    
                    # Pokud obchod nebyl uzavřen, uzavřeme ho na poslední ceně
                    if trade.status == TradeStatus.OPEN:
                        trade.exit_price = df['close'].iloc[-1]
                        trade.exit_time = df.index[-1]
                        trade.status = TradeStatus.CLOSED_PROFIT if trade.exit_price > trade.entry_price else TradeStatus.CLOSED_LOSS
                        trade.profit_pips, trade.profit_percentage = trade.calculate_profit(trade.exit_price)
                        trade.exit_reason = "Konec backtestu"
                        active_long = False
                    
                    # Přidání obchodu do seznamu
                    self.trades.append(trade)
            
            # Sell signál
            if df['sell_signal'].iloc[i] and (not active_short or not self.parameters["wait_for_exit_before_new_entry"]):
                entry_price = df['close'].iloc[i]
                entry_time = df.index[i]
                
                # Nastavení stop-loss
                if self.parameters["use_atr_for_sl"]:
                    stop_loss = entry_price + (df['atr'].iloc[i] * self.parameters["atr_multiplier"])
                else:
                    stop_loss = entry_price * (1 + self.parameters["stop_loss_pips"] / 100)
                
                # Nastavení take-profit úrovní
                take_profit = [entry_price * (1 - tp_pips / 100) for tp_pips in self.parameters["take_profit_pips"]]
                
                # Kontrola minimálního poměru rizika k zisku
                risk = stop_loss - entry_price
                reward = entry_price - take_profit[0]
                rr_ratio = reward / risk if risk > 0 else 0
                
                if rr_ratio >= self.parameters["risk_reward_ratio"]:
                    active_short = True
                    
                    # Vytvoření obchodu
                    trade = Trade(
                        symbol=df.get('symbol', ['Unknown'])[0] if isinstance(df.get('symbol'), pd.Series) else "Unknown",
                        trade_type=TradeType.SELL,
                        entry_price=entry_price,
                        entry_time=entry_time,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        status=TradeStatus.OPEN
                    )
                    
                    # Simulace výsledku obchodu
                    for j in range(i + 1, len(df)):
                        # Kontrola výstupu podle ceny
                        if trade.check_exit_conditions(df['high'].iloc[j], df['low'].iloc[j], df.index[j]):
                            active_short = False
                            break
                        
                        # Výstup podle RSI
                        if df['exit_short_signal'].iloc[j]:
                            trade.exit_price = df['close'].iloc[j]
                            trade.exit_time = df.index[j]
                            trade.status = TradeStatus.CLOSED_PROFIT if trade.exit_price < trade.entry_price else TradeStatus.CLOSED_LOSS
                            trade.profit_pips, trade.profit_percentage = trade.calculate_profit(trade.exit_price)
                            trade.exit_reason = "RSI Exit"
                            active_short = False
                            break
                    
                    # Pokud obchod nebyl uzavřen, uzavřeme ho na poslední ceně
                    if trade.status == TradeStatus.OPEN:
                        trade.exit_price = df['close'].iloc[-1]
                        trade.exit_time = df.index[-1]
                        trade.status = TradeStatus.CLOSED_PROFIT if trade.exit_price < trade.entry_price else TradeStatus.CLOSED_LOSS
                        trade.profit_pips, trade.profit_percentage = trade.calculate_profit(trade.exit_price)
                        trade.exit_reason = "Konec backtestu"
                        active_short = False
                    
                    # Přidání obchodu do seznamu
                    self.trades.append(trade)


def plot_strategy_comparison(results_list: List[Dict[str, Any]]) -> go.Figure:
    """
    Vykreslí porovnání výkonnosti více strategií.
    
    Args:
        results_list: Seznam slovníků s výsledky backtestů
        
    Returns:
        Plotly Figure s porovnáním
    """
    if not results_list:
        return go.Figure()
    
    # Extrakce názvů strategií a metrik
    strategy_names = [result["strategy_name"] for result in results_list]
    total_profits = [result["metrics"]["total_profit"] for result in results_list]
    win_rates = [result["metrics"]["win_rate"] * 100 for result in results_list]
    profit_factors = [result["metrics"]["profit_factor"] for result in results_list]
    max_drawdowns = [result["metrics"]["max_drawdown"] for result in results_list]
    
    # Vytvoření grafu s více panely
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Celkový zisk (%)", "Win Rate (%)", "Profit Factor", "Max. Drawdown (%)"),
        specs=[[{"type": "bar"}, {"type": "bar"}], [{"type": "bar"}, {"type": "bar"}]]
    )
    
    # Celkový zisk
    fig.add_trace(
        go.Bar(
            x=strategy_names,
            y=total_profits,
            marker_color=['green' if profit >= 0 else 'red' for profit in total_profits],
            name="Celkový zisk (%)"
        ),
        row=1, col=1
    )
    
    # Win Rate
    fig.add_trace(
        go.Bar(
            x=strategy_names,
            y=win_rates,
            marker_color='blue',
            name="Win Rate (%)"
        ),
        row=1, col=2
    )
    
    # Profit Factor
    fig.add_trace(
        go.Bar(
            x=strategy_names,
            y=profit_factors,
            marker_color=['green' if pf >= 1 else 'red' for pf in profit_factors],
            name="Profit Factor"
        ),
        row=2, col=1
    )
    
    # Max Drawdown
    fig.add_trace(
        go.Bar(
            x=strategy_names,
            y=max_drawdowns,
            marker_color='red',
            name="Max. Drawdown (%)"
        ),
        row=2, col=2
    )
    
    # Nastavení grafu
    fig.update_layout(
        title="Porovnání obchodních strategií",
        height=700,
        template="plotly_white",
        showlegend=False
    )
    
    return fig