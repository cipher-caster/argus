import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Dict, Any, Optional

from app.indicators.calculator import _mss_to_list, _sweep_to_list

# Per-symbol risk parameter overrides.
# NOTE: TP overrides were removed 2026-03-27 after discovering the backtest
# lookup bug (symbol="BTC/USDT" was checked as "BTC/USDTUSDT" — never matched).
# All prior "validation" of TP=4.0x overrides used TP=2.0x data. When the bug
# was fixed, TP=4.0x hurt both BTC and ETH vs the TP=2.0x default.
# BTC SL=1.75x also untested — removed pending proper validation.
SYMBOL_OVERRIDES: Dict[str, Dict[str, float]] = {}


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
        # Default risk parameters (overridable per-symbol)
        self.default_sl_mult = 1.5
        self.default_tp_mult = 2.0

    def analyze(self, df: pd.DataFrame, symbol: str = None) -> Dict[str, Any]:
        """
        Analyze the provided DataFrame for Titan setups.
        :param symbol: Optional symbol (e.g. "BTCUSDT") for per-symbol risk overrides.
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
        
        # SMC: Check for recent sweeps (last 5 candles)
        recent_df = df.tail(5)
        recent_sweep_type = None
        bull_sweeps = recent_df[recent_df['sweep_type'] == 'bullish']
        bear_sweeps = recent_df[recent_df['sweep_type'] == 'bearish']
        
        if not bull_sweeps.empty:
            recent_sweep_type = 'bullish'
        elif not bear_sweeps.empty:
            recent_sweep_type = 'bearish'

        # 6. Signal Generation (Enhanced with Predictive Logic)
        signal = self._generate_signal(trend, momentum, volatility, row, recent_sweep_type)
        
        # 7. Targets & Risk Management
        # Pass signal type to calculate directional targets (TP/SL)
        # If signal is WAIT, we still calculate hypothetical targets based on Ideal Entry
        target_signal = signal['type']
        if "WAIT" in target_signal:
             # Infer direction from trend
             target_signal = "BUY" if trend == "BULLISH" else "SELL"
             
        targets = self._calculate_risk_levels(row, target_signal, signal.get('ideal_entry', row['close']), symbol=symbol)
        
        # 8. Sizing Advice (Kelly)
        sizing = self._calculate_sizing(signal['confidence'])

        return {
            "signal": signal['type'], # BUY, SELL, NEUTRAL, WAIT_OB, WAIT_VOL, STRONG_BUY...
            "confidence": signal['confidence'], # 0-100%
            "trend": trend,
            "momentum": momentum,
            "volatility": volatility,
            "targets": targets,
            "sizing": sizing,
            "indicators": {
                "rsi": row.get('rsi'),
                "macd": row.get('macd'),
                "adx": row.get('adx'),
                "supertrend": row.get('supertrend'),
                "ema20": row.get('ema20'),  # We need to add this to _add_indicators
                "ema50": row.get('ema50')   # And this
            }
        }

    def _add_indicators(self, df: pd.DataFrame):
        """Adds technical indicators to the DataFrame in-place."""
        
        # EMA 200 (Macro)
        df['ema200'] = ta.ema(df['close'], length=self.ema_len)
        # EMA 20 (Fast Pullback Support)
        df['ema20'] = ta.ema(df['close'], length=20)
        # EMA 50 (Medium Pullback Support)
        df['ema50'] = ta.ema(df['close'], length=50)
        
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

        # SMC: Market Structure Shift
        shifts = _mss_to_list(df, lookback=2)
        df['mss_type'] = None
        df['mss_price'] = None
        for shift in shifts:
            idx = df[df['timestamp'] == shift['timestamp']].index
            if not idx.empty:
                df.loc[idx, 'mss_type'] = shift['type']
                df.loc[idx, 'mss_price'] = shift['price']

        # SMC: Liquidity Sweep
        sweeps = _sweep_to_list(df, lookback=24)
        df['sweep_type'] = None
        for sweep in sweeps:
            idx = df[df['timestamp'] == sweep['timestamp']].index
            if not idx.empty:
                df.loc[idx, 'sweep_type'] = sweep['type']

        # HTF Levels: 24H and 7D High/Low for Confluence
        df['htf_24h_high'] = df['high'].rolling(24).max()
        df['htf_24h_low'] = df['low'].rolling(24).min()
        df['htf_7d_high'] = df['high'].rolling(24 * 7).max()
        df['htf_7d_low'] = df['low'].rolling(24 * 7).min()

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
            "rsi_val": float(rsi),
            "is_overbought": bool(rsi_overbought),
            "is_oversold": bool(rsi_oversold),
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

    def _generate_signal(self, trend: str, momentum: Dict[str, Any], volatility: Dict[str, Any], row: pd.Series, recent_sweep: str = None) -> Dict[str, Any]:
        """
        Synthesizes indicators into a Signal.
        Now includes PREDICTIVE Logic (Wait for pullback) and SMC Confluence.
        """
        
        signal_type = "NEUTRAL"
        confidence = 0
        reasons = []
        ideal_entry = row['close']
        
        # SuperTrend confirmation
        st_bullish = row.get('supertrend_dir', 0) > 0
        st_val = row.get('supertrend', 0)
        ema20 = row.get('ema20', row['close'])
        mss_type = row.get('mss_type')
        atr = row.get('atr', row['close'] * 0.01)
        
        # HTF Confluence Check (Proximity to 24H or 7D levels)
        near_htf_low = False
        near_htf_high = False
        if not pd.isna(row.get('htf_24h_low')):
            near_htf_low = abs(row['close'] - row['htf_24h_low']) <= atr or abs(row['close'] - row.get('htf_7d_low', 0)) <= atr
        if not pd.isna(row.get('htf_24h_high')):
            near_htf_high = abs(row['close'] - row['htf_24h_high']) <= atr or abs(row['close'] - row.get('htf_7d_high', 0)) <= atr

        # BULLISH SETUP
        if trend == "BULLISH":
            # SMC TRIGGER: Bullish MSS + Sweep Confluence
            if mss_type == 'bullish':
                if recent_sweep == 'bullish' and near_htf_low:
                    signal_type = "STRONG_BUY"
                    confidence = 100
                    reasons.append("SMC: ELITE CONFLUENCE (Sweep + MSS + HTF Support).")
                elif recent_sweep == 'bullish':
                    signal_type = "STRONG_BUY"
                    confidence = 95
                    reasons.append("SMC: High-Conviction Sweep + MSS Combo.")
                else:
                    signal_type = "STRONG_BUY"
                    confidence = 90
                    reasons.append("SMC: Bullish Market Structure Shift detected.")
                
                reasons.append("Trend: Macro Bullish Alignment.")
                ideal_entry = row['close']

            # Overbought Check
            elif momentum['rsi_val'] > 70:
                signal_type = "WAIT_OB" # Overbought
                confidence = 0
                reasons.append("Status: Overbought (RSI > 70)")
                reasons.append(f"Action: Wait for pullback to EMA20 (${ema20:.2f})")
                ideal_entry = ema20
            
            elif st_bullish:
                # Active Bull Trend
                if momentum['rsi_val'] < 45:
                    signal_type = "BUY" # Dip Buy (Market Entry ok)
                    confidence = 80
                    reasons.append("Trend: Uptrend")
                    reasons.append("Setup: Perfect Dip (RSI < 45)")
                    ideal_entry = row['close'] # Market buy
                else:
                    # Standard Trend - Recommend Limit Entry at Support
                    signal_type = "BUY_LIMIT"
                    confidence = 60
                    # Ideal entry is between current price and SuperTrend
                    ideal_entry = max(ema20, st_val)
                    reasons.append("Trend: Strong Bullish")
                    reasons.append(f"Setup: Place Limit at Support (${ideal_entry:.2f})")

            else:
                 signal_type = "NEUTRAL"
                 reasons.append("Trend: Bullish but SuperTrend Bearish (Correction)")
            
        # BEARISH SETUP
        elif trend == "BEARISH":
            # SMC TRIGGER: Bearish MSS + Sweep Confluence
            if mss_type == 'bearish':
                if recent_sweep == 'bearish' and near_htf_high:
                    signal_type = "STRONG_SELL"
                    confidence = 100
                    reasons.append("SMC: ELITE CONFLUENCE (Sweep + MSS + HTF Resistance).")
                elif recent_sweep == 'bearish':
                    signal_type = "STRONG_SELL"
                    confidence = 95
                    reasons.append("SMC: High-Conviction Sweep + MSS Combo.")
                else:
                    signal_type = "STRONG_SELL"
                    confidence = 90
                    reasons.append("SMC: Bearish Market Structure Shift detected.")
                
                reasons.append("Trend: Macro Bearish Alignment.")
                ideal_entry = row['close']

            # Oversold Check
            elif momentum['rsi_val'] < 30:
                signal_type = "WAIT_OS" # Oversold
                confidence = 0
                reasons.append("Status: Oversold (RSI < 30)")
                reasons.append(f"Action: Wait for bounce to EMA20 (${ema20:.2f})")
                ideal_entry = ema20
                
            elif not st_bullish:
                 # Active Bear Trend
                 if momentum['rsi_val'] > 55:
                     signal_type = "SELL" # Rally Sell
                     confidence = 80
                     reasons.append("Trend: Downtrend")
                     reasons.append("Setup: Perfect Rally (RSI > 55)")
                     ideal_entry = row['close']
                 else:
                     signal_type = "SELL_LIMIT"
                     confidence = 60
                     ideal_entry = min(ema20, st_val)
                     reasons.append("Trend: Strong Bearish")
                     reasons.append(f"Setup: Limit Sell at Resistance (${ideal_entry:.2f})")
            else:
                 signal_type = "NEUTRAL"
                 reasons.append("Trend: Bearish but SuperTrend Bullish (Relief Rally)")

        return {
            "type": signal_type,
            "confidence": confidence,
            "reasons": reasons,
            "ideal_entry": ideal_entry
        }

    def _calculate_risk_levels(self, row: pd.Series, signal_type: str, entry_price: float = None, adx: float = None, symbol: str = None) -> Dict[str, float]:
        """
        Calculates TP/SL based on ATR with fixed targets.
        - Default TP = 2.0x ATR (backtested optimal across alts)
        - Per-symbol overrides for BTC/ETH (TP = 4.0x ATR)
        - SL default 1.5x ATR (overridable per-symbol)
        """
        atr = row.get('atr', 0)
        price = entry_price if entry_price else row['close']

        if atr == 0:
            return {"entry": price, "tp": 0, "sl": 0}

        # Per-symbol overrides (e.g. BTC needs wider stops)
        overrides = SYMBOL_OVERRIDES.get(symbol, {}) if symbol else {}
        sl_mult = overrides.get("sl_mult", self.default_sl_mult)
        tp_override = overrides.get("tp_mult", None)

        # TP multiplier: use per-symbol override if set, else fixed default
        tp_mult = tp_override if tp_override is not None else self.default_tp_mult
        rr = round(tp_mult / sl_mult, 2)

        # Long Logic
        if "BUY" in signal_type or signal_type == "STRONG_BUY":
            sl = price - (atr * sl_mult)
            tp = price + (atr * tp_mult)
            return {"entry": price, "sl": sl, "tp": tp, "r_r": rr}

        # Short Logic
        elif "SELL" in signal_type or signal_type == "STRONG_SELL":
            sl = price + (atr * sl_mult)
            tp = price - (atr * tp_mult)
            return {"entry": price, "sl": sl, "tp": tp, "r_r": rr}

        return {"entry": price, "sl": 0, "tp": 0}

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
