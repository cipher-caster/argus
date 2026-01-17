import pandas as pd
from typing import Dict, Any

def calculate_relative_strength(df_alt: pd.DataFrame, df_btc: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculates Altcoin strength relative to BTC.
    """
    if df_alt.empty or df_btc.empty:
        return {"performance_relative_pct": 0.0, "strength": "NEUTRAL", "current_ratio": 1.0}

    # Align dataframes by timestamp
    df_merged = pd.merge(
        df_alt[['timestamp', 'close']].rename(columns={'close': 'alt_close'}),
        df_btc[['timestamp', 'close']].rename(columns={'close': 'btc_close'}),
        on='timestamp'
    )
    
    if df_merged.empty:
        return {"performance_relative_pct": 0.0, "strength": "NEUTRAL", "current_ratio": 1.0}
        
    df_merged['ratio'] = df_merged['alt_close'] / df_merged['btc_close']
    
    # Calculate 7-day performance relative to BTC
    lookback = min(len(df_merged), 24 * 7) # Assuming hourly data
    current_ratio = df_merged['ratio'].iloc[-1]
    prev_ratio = df_merged['ratio'].iloc[-lookback]
    
    perf_rel = ((current_ratio - prev_ratio) / prev_ratio) * 100
    
    strength = "OUTPERFORMING" if perf_rel > 2.0 else ("UNDERPERFORMING" if perf_rel < -2.0 else "NEUTRAL")
    
    return {
        "performance_relative_pct": round(perf_rel, 2),
        "strength": strength,
        "current_ratio": float(current_ratio)
    }
