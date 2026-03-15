import importlib.metadata
import pandas as pd
import sys
import os

# Add /app to path
sys.path.append("/app")

from app.indicators.calculator import calculate_indicator

def test_sweep_detection():
    # Create mock data with a Bullish Sweep
    # Lookback 5
    # Range Low will be 100
    data = {
        "timestamp": [1000, 2000, 3000, 4000, 5000, 6000],
        "open":  [110, 110, 110, 110, 110, 105],
        "high":  [120, 120, 120, 120, 120, 115],
        "low":   [100, 105, 102, 108, 101, 95], # Range low 100, candle 5 goes to 95
        "close": [115, 115, 115, 115, 115, 102], # Candle 5 closes at 102 (> 100)
        "volume": [100, 100, 100, 100, 100, 100]
    }
    df = pd.DataFrame(data)
    
    result = calculate_indicator(df, "sweep", {"lookback": 5})
    
    print(f"Calculated Sweeps: {result.data}")
    
    assert len(result.data) > 0
    assert result.data[0]['type'] == 'bullish'
    assert result.data[0]['level'] == 100.0
    print("✅ Sweep Detection Test Passed!")

if __name__ == "__main__":
    test_sweep_detection()
