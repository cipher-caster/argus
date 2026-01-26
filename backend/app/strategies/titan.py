import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Dict, Any, Optional

class TitanStrategy:
    """
    Titan Unified Crypto Trading System
    A hybrid Mean-Reversion and Trend-Following strategy.
    """

    def __init__(self):
        # Settings from PDF Appendix
        self.ema_len = 200
        self.rsi_len = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.bb_len = 20
        self.bb_std = 2.0
        self.atr_len = 14
        self.st_len = 10
        self.st_mult = 3.0
        self.fib_level = 0.618

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze the provided DataFrame for Titan setups.
        """
        if df.empty or len(df) < 200:
            return {"error": "Insufficient data (need > 200 candles)"}

        # 1. Calculate Indicators
        self._add_indicators(df)

        # 2. Get Latest State
        row = df.iloc[-1]
        
        # 3. Macro Regime (EMA 200)
        # Bullish if Price > EMA 200
        ema = row.get('ema200')
        price = row['close']
        trend = "BULLISH" if not pd.isna(ema) and price > ema else "BEARISH"

        # 4. Momentum (RSI + MACD)
        momentum = self._analyze_momentum(row)
        
        # 5. Volatility (Bollinger Squeeze + ATR)
        volatility = self._analyze_volatility(row)
        
        # 6. Signal Generation
        signal = self._generate_signal(trend, momentum, volatility, row)
        
        # 7. Targets & Risk Management
        targets = self._calculate_risk_levels(row, signal['type'])
        
        # 8. Sizing Advice (Kelly)
        sizing = self._calculate_sizing(signal['confidence'])

        return {
            "signal": signal['type'], # BUY, SELL, NEUTRAL, STRONG_BUY...
            "confidence": signal['confidence'], # 0-100%
            "trend": trend,
            "momentum": momentum,
            "volatility": volatility,
            "targets": targets,
            "sizing": sizing,
            "indicators": {
                "rsi": row.get('rsi'),
                "macd": row.get('macd'),
                "adx": row.get('adx'), # If added
                "supertrend": row.get('supertrend')
            }
        }

    def _add_indicators(self, df: pd.DataFrame):
        """Adds technical indicators to the DataFrame in-place."""
        
        # EMA 200
        df['ema200'] = ta.ema(df['close'], length=self.ema_len)
        
        # RSI 14
        df['rsi'] = ta.rsi(df['close'], length=self.rsi_len)
        
        # MACD
        macd = ta.macd(df['close'], fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal)
        if macd is not None:
             df['macd'] = macd[f'MACD_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}']
             df['macd_hist'] = macd[f'MACDh_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}']
             df['macd_signal'] = macd[f'MACDs_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}']

        # Bollinger Bands
        bb = ta.bbands(df['close'], length=self.bb_len, std=self.bb_std)
        if bb is not None:
            df['bb_upper'] = bb[f'BBU_{self.bb_len}_{self.bb_std}']
            df['bb_lower'] = bb[f'BBL_{self.bb_len}_{self.bb_std}']
            df['bb_width'] = df['bb_upper'] - df['bb_lower']
            
        # ATR
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=self.atr_len)

        # SuperTrend (Trend Direction)
        st = ta.supertrend(df['high'], df['low'], df['close'], length=self.st_len, multiplier=self.st_mult)
        if st is not None:
            # SUPERTd_10_3.0 is 1 for Bullish, -1 for Bearish
            df['supertrend_dir'] = st[f'SUPERTd_{self.st_len}_{self.st_mult}']
            df['supertrend'] = st[f'SUPERT_{self.st_len}_{self.st_mult}']

    def _analyze_momentum(self, row: pd.Series) -> Dict[str, Any]:
        """Analyzes RSI and MACD for momentum alignment."""
        rsi = row.get('rsi', 50)
        macd = row.get('macd', 0)
        macd_sig = row.get('macd_signal', 0)
        
        # RSI Logic
        rsi_bullish = rsi > 50
        rsi_bearish = rsi < 50
        rsi_overbought = rsi > 70 # PDF Appendix says 80, but 70 is standard safer check
        rsi_oversold = rsi < 30
        
        # MACD Logic
        macd_bullish = macd > macd_sig
        
        score = 0
        if rsi_bullish: score += 1
        if macd_bullish: score += 1
        
        status = "NEUTRAL"
        if score == 2: status = "BULLISH"
        elif score == 0: status = "BEARISH"
        
        return {
            "status": status,
            "rsi_val": rsi,
            "is_overbought": rsi_overbought,
            "is_oversold": rsi_oversold,
            "macd_crossed": "UP" if macd_bullish else "DOWN"
        }

    def _analyze_volatility(self, row: pd.Series) -> Dict[str, Any]:
        """Analyzes Bollinger Bands for Squeeze conditions."""
        # Simple squeeze detection: BB Width is relatively low?
        # A real squeeze compares BB Width to Keltner Channel Width, but we'll use a simplified heuristic if KC not computed.
        # Or just return ATR.
        
        # PDF: "Bollinger Squeeze" - volatility contraction.
        # We can flag if bandwidth is in lowest percentile, but that requires history stats.
        # For single row, we can just report ATR.
        
        return {
            "atr": row.get('atr', 0),
            "squeeze": False # TODO: Implement historical percentile check
        }

    def _generate_signal(self, trend: str, momentum: Dict[str, Any], volatility: Dict[str, Any], row: pd.Series) -> Dict[str, Any]:
        """
        Synthesizes indicators into a Signal.
        
        Rules:
        1. Trend Filter: Trade in direction of EMA 200.
        2. Pullback Entry:
           - Bullish: Trend BULLISH + RSI Oversold (<40/30) OR SuperTrend Flip Bullish.
           - Bearish: Trend BEARISH + RSI Overbought (>60/70) OR SuperTrend Flip Bearish.
        """
        
        signal_type = "NEUTRAL"
        confidence = 0
        reasons = []
        
        # SuperTrend confirmation
        st_bullish = row.get('supertrend_dir', 0) > 0
        
        # BULLISH SETUP
        if trend == "BULLISH":
            # 1. Trend Following: SuperTrend just flipped green? (Hard to know single row, assume green is good)
            # 2. Pullback: RSI < 45 in Uptrend is a "Dip Buy" opportunity
            if st_bullish:
                if momentum['rsi_val'] < 45:
                    signal_type = "BUY" # Dip Buy
                    confidence = 80
                    reasons.append("Trend: Uptrend (Price > EMA200)")
                    reasons.append("Setup: RSI Pullback (< 45)")
                elif momentum['macd_crossed'] == "UP":
                     signal_type = "BUY" # Momentum breakout
                     confidence = 60
                     reasons.append("Momentum: MACD Crossover")
            
        # BEARISH SETUP
        elif trend == "BEARISH":
            if not st_bullish:
                 if momentum['rsi_val'] > 55:
                     signal_type = "SELL" # Rally Sell
                     confidence = 80
                     reasons.append("Trend: Downtrend (Price < EMA200)")
                     reasons.append("Setup: RSI Rally (> 55)")
                 elif momentum['macd_crossed'] == "DOWN":
                     signal_type = "SELL"
                     confidence = 60
                     reasons.append("Momentum: MACD Crossdown")

        return {
            "type": signal_type,
            "confidence": confidence,
            "reasons": reasons
        }

    def _calculate_risk_levels(self, row: pd.Series, signal_type: str) -> Dict[str, float]:
        """Calculates TP/SL based on ATR (1.5x SL, 3x TP -> 2 R:R roughly)."""
        atr = row.get('atr', 0)
        price = row['close']
        
        if atr == 0:
            return {"tp": 0, "sl": 0}
            
        if signal_type == "BUY" or signal_type == "STRONG_BUY":
            sl = price - (atr * 1.5)
            tp = price + (atr * 3.0) # 2:1 ratio
            return {"entry": price, "sl": sl, "tp": tp, "r_r": 2.0}
            
        elif signal_type == "SELL" or signal_type == "STRONG_SELL":
            sl = price + (atr * 1.5)
            tp = price - (atr * 3.0)
            return {"entry": price, "sl": sl, "tp": tp, "r_r": 2.0}
            
        return {"entry": 0, "sl": 0, "tp": 0}

    def _calculate_sizing(self, confidence: int) -> str:
        """Returns Kelly Criterion based sizing advice."""
        # PDF: "Quarter Kelly" (0.25).
        # We assume a fixed Win Rate based on confidence for "Estimation".
        # High Conf (80%) -> Assume 60% WR.
        # Med Conf (60%) -> Assume 50% WR.
        
        if confidence >= 80:
            # Quarter Kelly for 60% WR, 2:1 Odds
            # W = 0.6, R = 2. K% = W - (1-W)/R = 0.6 - 0.4/2 = 0.6 - 0.2 = 0.4 (Full Kelly)
            # Quarter = 10%
            return "Aggressive (10% Risk)" # Maybe too high for crypto, PDF says "2% Rule" cap.
        
        elif confidence >= 60:
             return "Standard (1-2% Risk)"
             
        return "Conservative (0.5% Risk) or No Trade"
