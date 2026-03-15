import importlib.metadata
import pandas as pd
import sys
import os
sys.path.append("/app")
from app.strategies.oracle import OracleStrategy

def debug_fvg():
    # Mock data: 
    # Candle 2 creates Bullish FVG [110, 120]
    # Candle 5 mitgates it by dropping to 100
    data = {
        "timestamp": [1000, 2000, 3000, 4000, 5000, 6000],
        "open":  [100, 115, 125, 130, 130, 105],
        "high":  [110, 130, 140, 135, 135, 110],
        "low":   [95, 115, 120, 125, 125, 100], 
        "close": [105, 125, 135, 128, 128, 102],
        "volume": [100, 100, 100, 100, 100, 100]
    }
    df = pd.DataFrame(data)
    
    # Manually add required indicators for _calculate_earnest_score
    df['rsi'] = 60
    df['bb_upper'] = 150
    df['bb_mid'] = 120
    df['bb_lower'] = 90
    df['adx'] = 30
    df['ema200'] = 80
    df['conversion'] = 100
    df['base'] = 100
    df['span_a'] = 100
    df['span_b'] = 100
    
    strategy = OracleStrategy()
    strategy._add_indicators(df)
    
    print("--- FVG State Tracking ---")
    for i in range(len(df)):
        row = df.iloc[i]
        score_data = strategy._calculate_earnest_score(row)
        score = score_data['voters']['smc_fvg']
        print(f"Candle {i}: Price {row['close']} | FVG {row['active_fvg_type']} | Voter Score: {score}")

if __name__ == '__main__':
    debug_fvg()
