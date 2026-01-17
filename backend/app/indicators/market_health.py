import pandas as pd
import pandas_ta as ta
from typing import Dict, List, Any

def calculate_market_health(df_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Calculates aggregate market health based on Trend (200D EMA) and Volatility Regimes.
    """
    total_coins = len(df_data)
    
    # Default structure with zeroed values
    default_result = {
        "summary": {
            "total_coins": total_coins,
            "bullish_pct": 0.0,
            "bearish_pct": 0.0,
            "squeezing_pct": 0.0,
        },
        "volatility": {
            "DANGER": 0.0,
            "ACTIVE": 0.0,
            "STABLE": 0.0
        }
    }

    if total_coins == 0:
        return default_result

    bullish_count = 0
    bearish_count = 0
    volatility_distribution = {"DANGER": 0, "ACTIVE": 0, "STABLE": 0}
    squeeze_count = 0

    for symbol, df in df_data.items():
        if df.empty:
            continue
            
        # Ensure indicators are present
        if 'ema200' not in df.columns:
            df['ema200'] = ta.ema(df['close'], length=200)
        if 'atr' not in df.columns:
            df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        
        last_row = df.iloc[-1]
        
        # 1. Trend Health
        if 'ema200' in last_row and not pd.isna(last_row['ema200']):
            if last_row['close'] > last_row['ema200']:
                bullish_count += 1
            else:
                bearish_count += 1
            
        # 2. Volatility Regime
        if 'atr' in last_row and not pd.isna(last_row['atr']):
            norm_atr = (last_row['atr'] / last_row['close']) * 100 if last_row['close'] > 0 else 0
            if norm_atr > 2.0:
                volatility_distribution["DANGER"] += 1
            elif norm_atr < 0.5:
                volatility_distribution["STABLE"] += 1
            else:
                volatility_distribution["ACTIVE"] += 1
            
        # 3. Squeeze Detection (Optional, can be expensive)
        try:
            bb = ta.bbands(df['close'], length=20, std=2)
            if bb is not None and not bb.empty:
                upper = bb[f'BBU_20_2.0'].iloc[-1]
                lower = bb[f'BBL_20_2.0'].iloc[-1]
                mid = bb[f'BBM_20_2.0'].iloc[-1]
                bandwidth = (upper - lower) / mid if mid > 0 else 0
                if bandwidth < 0.1:
                    squeeze_count += 1
        except Exception:
            pass

    return {
        "summary": {
            "total_coins": total_coins,
            "bullish_pct": round((bullish_count / total_coins) * 100, 1),
            "bearish_pct": round((bearish_count / total_coins) * 100, 1),
            "squeezing_pct": round((squeeze_count / total_coins) * 100, 1),
        },
        "volatility": {
            k: round((v / total_coins) * 100, 1) for k, v in volatility_distribution.items()
        }
    }
