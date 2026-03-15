import importlib.metadata
import pandas as pd
import sys
import os

# Add /app to path
sys.path.append("/app")

from app.indicators.calculator import calculate_indicator

def test_mss_detection():
    # Create mock data with a Bullish MSS
    # Pivot High at candle 2 (lookback 2)
    # Price breaks Pivot High at candle 5
    data = {
        "timestamp": [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000],
        "open":  [90, 95, 100, 95, 90, 105, 110, 115],
        "high":  [95, 100, 110, 100, 95, 115, 120, 125], # Pivot High 110 at index 2
        "low":   [85, 90, 95, 90, 85, 100, 105, 110],
        "close": [92, 98, 105, 92, 88, 112, 115, 120], # Break 110 at index 5
        "volume": [100, 100, 100, 100, 100, 100, 100, 100]
    }
    df = pd.DataFrame(data)
    
    result = calculate_indicator(df, "mss", {"lookback": 2})
    
    print(f"Calculated MSS: {result.data}")
    
    # We expect an MSS at index 5
    assert len(result.data) > 0
    assert result.data[0]['type'] == 'bullish'
    assert result.data[0]['price'] == 110.0
    print("✅ MSS Detection Test Passed!")

if __name__ == "__main__":
    test_mss_detection()
