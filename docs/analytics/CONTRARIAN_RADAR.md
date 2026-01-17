# Contrarian Radar (Mean Reversion)

**The Contrarian Radar** looks for opportunities where the market is **Overextended**. It bets on the law of gravity: Price always returns to the mean eventually.

## Core Logic: The Rubber Band

We use the **200-Day EMA** as the "Mean" (fair value).
We use **ATR (Average True Range)** to measure how far the rubber band can stretch before snapping back.

- **Extension Thresold**: Distance from EMA > **3x ATR**.

## Signals

### 🔴 DE-RISK LONG (Top Signal)

**Logic**: Price is **3x ATR ABOVE** the 200 EMA.

- **Meaning**: The asset is parabolic. The rubber band is stretched to maximum tension.
- **Action**:
  - **Spot Holders**: Take profits. Sell into strength.
  - **Traders**: Do not Long. Look for Shorts or wait for pullback.

### 🟢 SPOT BUY (Bottom Signal)

**Logic**: Price is **3x ATR BELOW** the 200 EMA.

- **Meaning**: The asset has capitulated. Selling is exhausted.
- **Action**:
  - **Spot**: This is a generational buy zone ("Blood in the streets").
  - **Traders**: Close shorts. Look for reversal Longs.

## Warning

Contrarian trading is inherently risky ("Catching a falling knife" or "Shorting a rocket").

- **Never use high leverage** on these signals.
- These are **Macro** signals. It might take days for the reversion to play out.
