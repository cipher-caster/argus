import pandas as pd
from typing import Dict, Any, Optional

def detect_liquidity_sweeps(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detects liquidity sweeps of Previous Weekly High/Low (PWH/PWL) 
    and Previous Monthly High/Low (PMH/PML).
    """
    if df.empty or len(df) < 2:
        return {"bull_sweep": False, "bear_sweep": False}

    # In a real system, we'd fetch W/M candles explicitly.
    # Here we approximate from the daily/4h history if needed, 
    # but let's assume PWH/PWL/PMH/PML are passed in or calculated from OHLCV.
    
    # Simple logic for detecting a sweep & reclaim:
    # Bull Sweep: low < Level and close > Level
    # Bear Sweep: high > Level and close < Level
    
    # For now, let's extract the "Recent Levels" from the dataframe 
    # (this assumes the dataframe has been pre-processed with these structural markers)
    
    last = df.iloc[-1]
    
    # Placeholder for level detection if not provided:
    # We look for the highest high of the last 20 bars (approx monthly)
    # and last 5 bars (approx weekly) for daily data.
    
    res = {
        "bull_sweep": False,
        "bear_sweep": False,
        "swept_level": None,
        "type": None
    }
    
    # Assuming the caller might provide these as columns
    levels = {
        "PWH": last.get('pwh'),
        "PWL": last.get('pwl'),
        "PMH": last.get('pmh'),
        "PML": last.get('pml')
    }
    
    for label, level in levels.items():
        if pd.isna(level): continue
        
        if last['low'] < level and last['close'] > level:
            res["bull_sweep"] = True
            res["swept_level"] = float(level)
            res["type"] = label
            break
        elif last['high'] > level and last['close'] < level:
            res["bear_sweep"] = True
            res["swept_level"] = float(level)
            res["type"] = label
            break
            
    return res
