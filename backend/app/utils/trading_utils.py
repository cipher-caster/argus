"""Shared trading utilities."""


def calculate_conviction(
    confidence: int,
    regime_aligned: bool,
    is_market_signal: bool,
) -> int:
    """
    Compute conviction score (0–100) from Titan confidence + context bonuses.

    Args:
        confidence: Titan confidence value (0–100)
        regime_aligned: True if signal direction matches current BTC regime
        is_market_signal: True for market (non-limit) signals (BUY/SELL vs BUY_LIMIT/SELL_LIMIT)

    Returns:
        Integer conviction score clamped to [0, 100]
    """
    base_pts = (confidence / 100) * 60
    regime_bonus = 20 if regime_aligned else 0
    signal_bonus = 10 if is_market_signal else 0
    return int(min(100, base_pts + regime_bonus + signal_bonus))
