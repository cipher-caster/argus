import numpy as np
import pandas as pd

from app.indicators.screener import run_oracle_screener


def test_screener_handles_nan_indicators():
    """Verify that run_oracle_screener handles DataFrames with NaN indicators gracefully."""

    # Create a DataFrame with constant prices (simulating a new asset with little history)
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=300),
            "open": [100.0] * 300,
            "high": [110.0] * 300,
            "low": [90.0] * 300,
            "close": [105.0] * 300,
            "volume": [1000.0] * 300,
        }
    )

    df_data = {"NEWCOIN/USDT": df}
    btc_df = pd.DataFrame()  # Empty BTC df

    # Should NOT crash — if it does, pytest surfaces the real traceback
    results = run_oracle_screener(df_data, btc_df)
    assert isinstance(results, list)
    # Every returned item must have the required screener fields
    for item in results:
        assert "symbol" in item
        assert "score" in item
        assert -4 <= item["score"] <= 4


def test_screener_handles_empty_btc_macro():
    """Verify screener handles scenario with no BTC data for relative strength."""
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=300),
            "open": [100.0] * 300,
            "high": [110.0] * 300,
            "low": [90.0] * 300,
            "close": [105.0] * 300,
            "volume": [1000.0] * 300,
        }
    )

    df_data = {"BTC/USDT": df}
    results = run_oracle_screener(df_data, pd.DataFrame())
    assert isinstance(results, list)
    # All returned items should have valid structure
    for item in results:
        assert "symbol" in item
        assert "score" in item
        assert isinstance(item["score"], int)


def test_screener_filters_low_scores():
    """Screener should only include items with abs(score) >= 2."""
    np.random.seed(42)
    prices = np.linspace(50, 200, 300)  # Strong uptrend to get a high score
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=300, freq="1h"),
            "open": prices,
            "high": prices * 1.005,
            "low": prices * 0.995,
            "close": prices,
            "volume": np.ones(300) * 1000,
        }
    )

    df_data = {"TRENDCOIN/USDT": df}
    results = run_oracle_screener(df_data, pd.DataFrame())
    for item in results:
        assert abs(item["score"]) >= 2, f"Score {item['score']} should be filtered (abs < 2)"


def test_screener_returns_sorted_by_score_strength():
    """Results should be sorted by abs(score) descending."""
    np.random.seed(42)
    # Create two coins with different trend strengths
    strong_prices = np.linspace(50, 300, 300)
    mild_prices = np.linspace(90, 130, 300)

    def make_df(prices):
        return pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=300, freq="1h"),
                "open": prices,
                "high": prices * 1.005,
                "low": prices * 0.995,
                "close": prices,
                "volume": np.ones(300) * 1000,
            }
        )

    df_data = {"STRONG/USDT": make_df(strong_prices), "MILD/USDT": make_df(mild_prices)}
    results = run_oracle_screener(df_data, pd.DataFrame())

    if len(results) >= 2:
        scores = [abs(r["score"]) for r in results]
        assert scores == sorted(scores, reverse=True), (
            "Results should be sorted by abs(score) descending"
        )
