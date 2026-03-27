import pandas as pd

from app.indicators.calculator import calculate_indicator


def test_fvg_detection():
    # Create mock data with a Bullish FVG
    # Candle 0: High 100
    # Candle 1: Big green candle
    # Candle 2: Low 110
    # Gap exists between 100 and 110
    data = {
        "timestamp": [1000, 2000, 3000, 4000],
        "open": [90, 101, 115, 112],
        "high": [100, 115, 120, 118],
        "low": [85, 101, 110, 108],
        "close": [95, 114, 112, 115],
        "volume": [100, 200, 150, 180]
    }
    df = pd.DataFrame(data)

    result = calculate_indicator(df, "fvg", {})

    assert len(result.data) > 0
    assert result.data[0]['type'] == 'bullish'
    assert result.data[0]['bottom'] == 100.0
    assert result.data[0]['top'] == 110.0


if __name__ == "__main__":
    test_fvg_detection()
