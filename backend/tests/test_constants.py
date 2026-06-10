import pytest

from app.constants import DEFAULT_TIMEFRAME_MS, TIMEFRAME_MS


def test_all_standard_timeframes_present():
    for tf in ("1m", "5m", "15m", "30m", "1h", "4h", "12h", "1d", "1w"):
        assert tf in TIMEFRAME_MS, f"Missing timeframe: {tf}"


def test_timeframe_values_are_positive():
    for tf, ms in TIMEFRAME_MS.items():
        assert ms > 0, f"{tf} has non-positive ms value"


@pytest.mark.parametrize(
    ("timeframe", "expected_ms"),
    [
        ("4h", 4 * 60 * 60 * 1000),
        ("1d", 24 * 60 * 60 * 1000),
        ("1w", 7 * 24 * 60 * 60 * 1000),
    ],
)
def test_timeframe_duration(timeframe, expected_ms):
    assert TIMEFRAME_MS[timeframe] == expected_ms


def test_default_is_1h():
    assert DEFAULT_TIMEFRAME_MS == 60 * 60 * 1000


def test_missing_timeframe_uses_default():
    result = TIMEFRAME_MS.get("99x", DEFAULT_TIMEFRAME_MS)
    assert result == DEFAULT_TIMEFRAME_MS
