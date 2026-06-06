import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Dict, Any, Optional

from app.indicators.calculator import _fvg_to_list

class OracleStrategy:
    """
    Multi-timeframe signal strategy that combines short-term
    micro-analysis with higher-timeframe macro trend context.
    """

    def __init__(self):
        # Indicator settings
        self.rsi_len = 14
        self.adx_len = 14
        self.adx_limit = 20
        self.ema_len = 200
        self.bb_len = 20
        self.bb_std = 2.0
        self.vol_threshold = 1.3
        self.atr_gap_mult = 3.0

    def analyze(self, df_micro: pd.DataFrame, df_macro: pd.DataFrame) -> Dict[str, Any]:
        """
        Main analysis entry point.
        :param df_micro: DataFrame for the trading timeframe (e.g., 1H)
        :param df_macro: DataFrame for the trend timeframe (e.g., 1D)
        :param df_micro: DataFrame for the trading timeframe (e.g., 1H)
        :param df_macro: DataFrame for the trend timeframe (e.g., 1D)
        """
        if df_micro.empty or df_macro.empty:
            return {"error": "Insufficient data"}

        # 1. Calculate Indicators
        self._add_indicators(df_micro)
        self._add_indicators(df_macro)

        # 2. Get Latest State
        micro = df_micro.iloc[-1]
        macro = df_macro.iloc[-1]
        
        # 3. Earnest Brain (Micro Analysis)
        earnest_result = self._calculate_earnest_score(micro)
        
        # 4. Prophet Macro (Trend Analysis)
        macro_result = self._calculate_macro_bias(macro)
        
        # 5. Market State
        state_result = self._detect_market_state(micro)
        
        # 6. Targets & Advice
        targets = self._calculate_targets(micro, macro, macro_result['bias'])

        # 7. Historical Signals & Backtest Simulation
        backtest = self._run_backtest(df_micro, df_macro)
        
        return {
            "mode": "prophet",
            "signal": self._synthesize_signal(earnest_result['score'], macro_result['score']),
            "confidence": f"{abs(earnest_result['score'])}/5",
            "bias": macro_result['bias'],
            "state": state_result['state'],
            "volatility": state_result['volatility_tag'],
            "earnest": earnest_result,
            "macro": macro_result,
            "targets": targets,
            "advice": self._generate_advice(earnest_result, macro_result, state_result, targets),
            "historical_signals": backtest['signals'],
            "performance": backtest['stats']
        }

    def _run_backtest(self, df_micro: pd.DataFrame, df_macro: pd.DataFrame) -> Dict[str, Any]:
        """
        Simulates trades based on signals and calculates performance.
        Returns signals list and performance stats.
        """
        signals = []
        trades = []
        
        # Pre-calculate macro biases
        macro_biases = {}
        for idx, row in df_macro.iterrows():
            macro_biases[row['timestamp']] = self._calculate_macro_bias(row)

        # Simulation State
        active_trade = None # {'type': 'LONG', 'entry': 100, 'tp': 110, 'sl': 90}
        
        for idx, row in df_micro.iterrows():
            # 1. Manage Active Trade
            if active_trade:
                high = row['high']
                low = row['low']
                
                # Check outcome
                result = None
                pnl = 0
                
                if active_trade['type'] == 'LONG':
                    if low <= active_trade['sl']:
                        result = 'LOSS'
                        pnl = (active_trade['sl'] - active_trade['entry']) / active_trade['entry']
                    elif high >= active_trade['tp']:
                        result = 'WIN'
                        pnl = (active_trade['tp'] - active_trade['entry']) / active_trade['entry']
                
                elif active_trade['type'] == 'SHORT':
                    if high >= active_trade['sl']:
                        result = 'LOSS'
                        pnl = (active_trade['entry'] - active_trade['sl']) / active_trade['entry']
                    elif low <= active_trade['tp']:
                        result = 'WIN'
                        pnl = (active_trade['entry'] - active_trade['tp']) / active_trade['entry']
                
                if result:
                    active_trade['result'] = result
                    active_trade['pnl'] = pnl
                    ts = row['timestamp']
                    active_trade['exit_time'] = int(ts.timestamp() * 1000) if isinstance(ts, pd.Timestamp) else int(ts)
                    trades.append(active_trade)
                    active_trade = None
                    # Don't enter new trade on same bar as exit
                    continue

            # 2. Check for New Entry (if no active trade)
            if pd.isna(row['rsi']) or pd.isna(row['ema200']):
                continue
                
            macro_ts = [ts for ts in macro_biases.keys() if ts <= row['timestamp']]
            if not macro_ts: continue
            m_bias = macro_biases[max(macro_ts)]
            
            e_score = self._calculate_earnest_score(row)['score']
            sig = self._synthesize_signal(e_score, m_bias['score'])
            
            if sig in ["STRONG_BUY", "BUY", "STRONG_SELL", "SELL"]:
                # Record Signal
                signals.append({
                    "timestamp": int(row['timestamp'].timestamp() * 1000),
                    "signal": sig,
                    "price": float(row['close'])
                })
                
                # Enter Trade Simulation
                atr = float(row['atr']) if not pd.isna(row['atr']) else (float(row['close']) * 0.01)
                price = float(row['close'])
                
                if "BUY" in sig:
                    active_trade = {
                        "type": "LONG",
                        "entry": price,
                        "tp": price + (atr * 3.0), # 3R Target
                        "sl": price - (atr * 1.5), # 1.5R Stop
                        "start_time": int(row['timestamp'].timestamp() * 1000)
                    }
                elif "SELL" in sig:
                    active_trade = {
                        "type": "SHORT",
                        "entry": price,
                        "tp": price - (atr * 3.0),
                        "sl": price + (atr * 1.5),
                        "start_time": int(row['timestamp'].timestamp() * 1000)
                    }

        # Calculate Stats
        total_trades = len(trades)
        wins = len([t for t in trades if t['result'] == 'WIN'])
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        total_pnl = sum([t['pnl'] for t in trades]) * 100
        
        stats = {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 1),
            "net_profit": round(total_pnl, 2),
            "trades": trades[-5:] # Return last 5 trades for detail
        }
        
        return {"signals": signals, "stats": stats}

    def _add_indicators(self, df: pd.DataFrame):
        """Adds technical indicators to the DataFrame in-place."""
        # EMA
        df['ema200'] = ta.ema(df['close'], length=self.ema_len)
        
        # RSI
        df['rsi'] = ta.rsi(df['close'], length=self.rsi_len)
        
        # ADX
        adx_df = ta.adx(df['high'], df['low'], df['close'], length=self.adx_len)
        # pandas-ta returns columns like ADX_14, DMP_14, DMN_14
        if adx_df is not None:
             df['adx'] = adx_df[f'ADX_{self.adx_len}']

        # Bollinger Bands
        bb = ta.bbands(df['close'], length=self.bb_len, std=self.bb_std)
        if bb is not None:
            df['bb_upper'] = bb[f'BBU_{self.bb_len}_{self.bb_std}']
            df['bb_mid'] = bb[f'BBM_{self.bb_len}_{self.bb_std}']
            df['bb_lower'] = bb[f'BBL_{self.bb_len}_{self.bb_std}']

        # ATR
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        df['atr_avg'] = ta.sma(df['atr'], length=20)
        
        # OBV (On-Balance Volume)
        df['obv'] = ta.obv(df['close'], df['volume'])
        df['obv_ma'] = ta.sma(df['obv'], length=20)
        
        # Ichimoku Cloud (Simplified for Macro Check)
        # Span A: (Conversion + Base) / 2 shifted 26
        # Span B: (Leading Span B) shifted 26
        high9 = df['high'].rolling(9).max()
        low9 = df['low'].rolling(9).min()
        high26 = df['high'].rolling(26).max()
        low26 = df['low'].rolling(26).min()
        high52 = df['high'].rolling(52).max()
        low52 = df['low'].rolling(52).min()
        
        conversion = (high9 + low9) / 2
        base = (high26 + low26) / 2
        
        df['span_a'] = ((conversion + base) / 2).shift(26)
        df['span_b'] = ((high52 + low52) / 2).shift(26)
        df['cloud_top'] = df[['span_a', 'span_b']].max(axis=1)

        # SMC: Fair Value Gaps
        fvgs = _fvg_to_list(df)
        df['fvg_type'] = None
        df['fvg_top'] = None
        df['fvg_bottom'] = None
        
        # Map FVGs to the specific candle where they were created
        for fvg in fvgs:
            # We match by timestamp (which we assigned to the middle candle)
            idx = df[df['timestamp'] == fvg['timestamp']].index
            if not idx.empty:
                df.loc[idx, 'fvg_type'] = fvg['type']
                df.loc[idx, 'fvg_top'] = fvg['top']
                df.loc[idx, 'fvg_bottom'] = fvg['bottom']

        # Detect all unmitigated FVGs using a stack
        df['active_fvg_type'] = None
        open_bull_fvgs = [] # List of [bottom, top]
        open_bear_fvgs = [] 

        for i in range(len(df)):
            row = df.iloc[i]
            
            # 1. Add new FVGs to the stack
            if row['fvg_type'] == 'bullish':
                open_bull_fvgs.append([row['fvg_bottom'], row['fvg_top']])
            elif row['fvg_type'] == 'bearish':
                open_bear_fvgs.append([row['fvg_bottom'], row['fvg_top']])
            
            # 2. Check for mitigation across the entire stack
            # We keep only gaps that haven't been touched by price yet
            open_bull_fvgs = [fvg for fvg in open_bull_fvgs if row['low'] > fvg[0]]
            open_bear_fvgs = [fvg for fvg in open_bear_fvgs if row['high'] < fvg[1]]
                
            # 3. Assign the most recent active FVG type to the row
            if open_bull_fvgs:
                df.at[df.index[i], 'active_fvg_type'] = 'bullish'
            elif open_bear_fvgs:
                df.at[df.index[i], 'active_fvg_type'] = 'bearish'

    def _calculate_earnest_score(self, row: pd.Series) -> Dict[str, Any]:
        """Calculates the -4 to +4 Earnest Voter Score."""
        score = 0
        details = {}

        # Voter 1: RSI
        # Pine: if rsi > 50 and rsi < 70 (+1) else if rsi < 50 and rsi > 30 (-1)
        rsi = row.get('rsi')
        if pd.isna(rsi):
            details['rsi'] = 0
        elif 50 < rsi < 70:
            score += 1
            details['rsi'] = 1
        elif 30 < rsi < 50:
            score -= 1
            details['rsi'] = -1
        else:
            details['rsi'] = 0

        # Voter 2: Bollinger
        # Pine: if bb_position > 0.1 (+1) else if bb_position < -0.1 (-1)
        # Position = (price - mid) / (upper - lower)
        if row['bb_upper'] != row['bb_lower']:
            bb_width = row['bb_upper'] - row['bb_lower']
            bb_pos = (row['close'] - row['bb_mid']) / bb_width
            if bb_pos > 0.1:
                score += 1
                details['bb'] = 1
            elif bb_pos < -0.1:
                score -= 1
                details['bb'] = -1
            else:
                details['bb'] = 0
        else:
            details['bb'] = 0

        # Voter 3: ADX
        # Pine: if adx > limit: (close > ema ? +1 : -1)
        adx = row.get('adx')
        ema = row.get('ema200')
        if not pd.isna(adx) and adx > self.adx_limit and not pd.isna(ema):
            val = 1 if row['close'] > ema else -1
            score += val
            details['adx'] = val
        else:
            details['adx'] = 0

        # Voter 4: EMA
        # Pine: close > ema ? +1 : -1
        ema = row.get('ema200')
        if not pd.isna(ema):
            val = 1 if row['close'] > ema else -1
            score += val
            details['ema'] = int(val)
        else:
            details['ema'] = 0

        # Voter 5: SMC (FVG Confluence)
        fvg_type = row.get('active_fvg_type')
        if fvg_type == 'bullish':
            score += 1
            details['smc_fvg'] = 1
        elif fvg_type == 'bearish':
            score -= 1
            details['smc_fvg'] = -1
        else:
            details['smc_fvg'] = 0

        return {"score": int(score), "voters": details}

    def _calculate_macro_bias(self, row: pd.Series) -> Dict[str, Any]:
        """Calculates the Daily Macro Trend (Prophet Logic)."""
        score = 0
        
        # 1. Trend (Price > EMA200)
        ema = row.get('ema200')
        trend_ok = bool(row['close'] > ema) if not pd.isna(ema) else False
        if trend_ok: score += 1
        
        # 2. Cloud (Price > Cloud Top)
        # Note: In initial bars, cloud might be NaN due to shift
        cloud_val = row.get('cloud_top')
        cloud_ok = bool(row['close'] > cloud_val) if not pd.isna(cloud_val) else False
        if cloud_ok: score += 1
        
        # 3. OBV (OBV > OBV_MA)
        obv = row.get('obv')
        obv_ma = row.get('obv_ma')
        obv_ok = bool(obv > obv_ma) if not pd.isna(obv) and not pd.isna(obv_ma) else False
        if obv_ok: score += 1
        
        bias = "NEUTRAL"
        if score >= 2: bias = "BULLISH"
        elif score == 0: bias = "BEARISH"
        
        return {"score": int(score), "bias": bias, "details": {"trend": trend_ok, "cloud": cloud_ok, "obv": obv_ok}}

    def _detect_market_state(self, row: pd.Series) -> Dict[str, Any]:
        """Detects Volatility and Chop."""
        # Chop
        adx = row.get('adx')
        is_chop = bool(adx < self.adx_limit) if not pd.isna(adx) else True
        state = "SLEEPING" if is_chop else ("SUPER TREND" if adx > 40 else "TRENDING")
        
        # Volatility
        # Pine: norm_atr = (atr / close) * 100
        # This normalization helps compare volatility across coins
        norm_atr = float((row['atr'] / row['close']) * 100 if row['close'] > 0 else 0)
        
        if norm_atr > 2.0: vol_tag = "DANGER"
        elif norm_atr < 0.5: vol_tag = "STABLE"
        else: vol_tag = "ACTIVE"
        
        return {"state": state, "volatility_tag": vol_tag, "is_chop": is_chop}

    def _calculate_targets(self, micro: pd.Series, macro: pd.Series, bias: str) -> Dict[str, float]:
        """
        Calculate support/resistance targets.

        Without explicit Weekly/Monthly OHLCV data, targets are approximated from
        current price +/- ATR multiples rather than higher-timeframe levels.
        """
        atr = float(micro['atr'])
        price = float(micro['close'])
        
        if bias == "BULLISH":
            return {
                "tp1": price + (atr * 2),
                "tp2": price + (atr * 4),
                "sl": price - (atr * 1.5)
            }
        elif bias == "BEARISH":
            return {
                "tp1": price - (atr * 2),
                "tp2": price - (atr * 4),
                "sl": price + (atr * 1.5)
            }
        else:
            return {"tp1": 0.0, "tp2": 0.0, "sl": 0.0}

    def _synthesize_signal(self, earnest_score: int, macro_score: int) -> str:
        """Combines Micro and Macro for a final verdict (Prophet Logic)."""
        
        # Strong Buy: Macro Bullish + Earnest > 2
        if macro_score >= 2 and earnest_score >= 3:
            return "STRONG_BUY"
        # Buy: Earnest > 2 (Counter-trend or early reversal)
        elif earnest_score >= 3:
            return "BUY"
        # Strong Sell: Macro Bearish + Earnest < -2
        elif macro_score == 0 and earnest_score <= -3:
            return "STRONG_SELL"
        # Sell
        elif earnest_score <= -3:
            return "SELL"
        
        return "NEUTRAL"

    def _generate_advice(self, earnest, macro, state, targets) -> str:
        """Generates human-readable advice string."""
        signal = self._synthesize_signal(earnest['score'], macro['score'])
        
        if state['volatility_tag'] == "DANGER":
            return "High Volatility. Reduce leverage."
            
        if signal == "STRONG_BUY":
            return f"TITAN BULL. Full alignment. TP: {targets['tp1']:.2f}"
        elif signal == "STRONG_SELL":
            return f"TITAN BEAR. Structure broken. TP: {targets['tp1']:.2f}"
        elif signal == "BUY":
             return "Scalp Long. Watch Macro resistance."
        elif signal == "SELL":
             return "Scalp Short. Watch Macro support."
            
        return "No clear setup. Wait for breakout."
