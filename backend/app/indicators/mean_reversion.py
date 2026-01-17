import pandas as pd
import pandas_ta as ta
from typing import Dict, Any

def detect_mean_reversion(df: pd.DataFrame, atr_mult: float = 3.0) -> Dict[str, Any]:
    """
    Detects mean reversion (contrarian) opportunities based on ATR extension from EMA200.
    Identifies 'Overextended' coins.
    """
    if df.empty or len(df) < 200:
        return {"is_extended": False, "opportunity": "NONE"}

    if 'ema200' not in df.columns:
        df['ema200'] = ta.ema(df['close'], length=200)
    if 'atr' not in df.columns:
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)

    last = df.iloc[-1]
    price = last['close']
    ema = last['ema200']
    atr = last['atr']
    
    if pd.isna(ema) or pd.isna(atr):
        return {"is_extended": False, "opportunity": "NONE"}

    dist_from_mean = price - ema
    abs_dist = abs(dist_from_mean)
    extension_atr = abs_dist / atr if atr > 0 else 0
    
    is_extended = extension_atr > atr_mult
    
    opportunity = "NONE"
    if is_extended:
        opportunity = "SPOT_BUY" if dist_from_mean < 0 else "DE-RISK_LONG"
        
    return {
        "is_extended": is_extended,
        "extension_atr": round(extension_atr, 2),
        "opportunity": opportunity,
        "price": float(price),
        "mean": float(ema),
        "target": float(ema) # Reversion target is the mean
    }
