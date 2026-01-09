import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Dict, Any, Optional

class OracleStrategy:
    """
    Manila Prophet v9.0 Implementation
    Combines 'Earnest' Micro-Analysis with 'Prophet' Macro-Context.
    """

    def __init__(self):
        # Settings (matching Pine Script v9.0)
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

        # 7. Historical Signals (Backtest)
        signals = self._calculate_historical_signals(df_micro, df_macro)
        
        return {
            "signal": self._synthesize_signal(earnest_result['score'], macro_result['score']),
            "confidence": f"{abs(earnest_result['score'])}/4",
            "bias": macro_result['bias'],
            "state": state_result['state'],
            "volatility": state_result['volatility_tag'],
            "earnest": earnest_result,
            "macro": macro_result,
            "targets": targets,
            "advice": self._generate_advice(earnest_result, macro_result, state_result, targets),
            "historical_signals": signals
        }

    def _calculate_historical_signals(self, df_micro: pd.DataFrame, df_macro: pd.DataFrame) -> list:
        """Calculates BUY/SELL signals for all historical candles."""
        signals = []
        
        # For each candle in micro (skipping early ones without indicators)
        # We need a macro bias for each micro timestamp.
        # We can simplify by taking the macro bias at that time.
        
        # Pre-calculate macro biases
        macro_biases = {}
        for idx, row in df_macro.iterrows():
            macro_biases[row['timestamp']] = self._calculate_macro_bias(row)

        for idx, row in df_micro.iterrows():
            if pd.isna(row['rsi']) or pd.isna(row['ema200']):
                continue
                
            # Find corresponding macro bias (nearest previous or same day)
            # Simplification: use the most recent macro bias relative to micro timestamp
            macro_ts = [ts for ts in macro_biases.keys() if ts <= row['timestamp']]
            if not macro_ts: continue
            m_bias = macro_biases[max(macro_ts)]
            
            e_score = self._calculate_earnest_score(row)['score']
            sig = self._synthesize_signal(e_score, m_bias['score'])
            
            if sig in ["STRONG_BUY", "BUY", "STRONG_SELL", "SELL"]:
                signals.append({
                    "timestamp": int(row['timestamp'].timestamp() * 1000),
                    "signal": sig,
                    "price": float(row['close'])
                })
        
        return signals

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

    def _calculate_earnest_score(self, row: pd.Series) -> Dict[str, Any]:
        """Calculates the -4 to +4 Earnest Voter Score."""
        score = 0
        details = {}

        # Voter 1: RSI
        # Pine: if rsi > 50 and rsi < 70 (+1) else if rsi < 50 and rsi > 30 (-1)
        rsi = row['rsi']
        if 50 < rsi < 70:
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
        if row['adx'] > self.adx_limit:
            val = 1 if row['close'] > row['ema200'] else -1
            score += val
            details['adx'] = val
        else:
            details['adx'] = 0

        # Voter 4: EMA
        # Pine: close > ema ? +1 : -1
        val = 1 if row['close'] > row['ema200'] else -1
        score += val
        details['ema'] = int(val)

        return {"score": int(score), "voters": details}

    def _calculate_macro_bias(self, row: pd.Series) -> Dict[str, Any]:
        """Calculates the Daily Macro Trend (Prophet Logic)."""
        score = 0
        
        # 1. Trend (Price > EMA200)
        trend_ok = bool(row['close'] > row['ema200'])
        if trend_ok: score += 1
        
        # 2. Cloud (Price > Cloud Top)
        # Note: In initial bars, cloud might be NaN due to shift
        cloud_val = row['cloud_top'] if pd.notna(row['cloud_top']) else 0
        cloud_ok = bool(row['close'] > cloud_val)
        if cloud_ok: score += 1
        
        # 3. OBV (OBV > OBV_MA)
        obv_ok = bool(row['obv'] > row['obv_ma'])
        if obv_ok: score += 1
        
        bias = "NEUTRAL"
        if score >= 2: bias = "BULLISH"
        elif score == 0: bias = "BEARISH"
        
        return {"score": int(score), "bias": bias, "details": {"trend": trend_ok, "cloud": cloud_ok, "obv": obv_ok}}

    def _detect_market_state(self, row: pd.Series) -> Dict[str, Any]:
        """Detects Volatility and Chop."""
        # Chop
        is_chop = bool(row['adx'] < self.adx_limit)
        state = "SLEEPING" if is_chop else ("SUPER TREND" if row['adx'] > 40 else "TRENDING")
        
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
        Calculates Support/Resistance targets based on Monthly/Weekly levels.
        Note: In a real implementation, we need explicit Weekly/Monthly OHLCV data.
        For now, we will approximate using the Macro (Daily) ranges or simple ATR extensions.
        """
        # Simplification: Using current price +/- ATR multiples for immediate targets
        # since we don't have the full Weekly/Monthly history passed in yet.
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
        """Combines Micro and Macro for a final verdict."""
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
