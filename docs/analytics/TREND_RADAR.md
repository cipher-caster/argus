# The Trend God (Trend Radar)

**"The Trend God"** is a macro trend analysis engine designed to filter noise and identify high-probability setups based on the 200-Day Exponential Moving Average (EMA).

## Core Philosophy

In crypto markets, the **200D EMA** is the definitive "line in the sand" for trend direction.

- **Above 200 EMA**: Bull Market (Look for Longs)
- **Below 200 EMA**: Bear Market (Look for Shorts or Cash)

This engine scans the entire market and categorizes every asset based on its relationship to this key level.

## Zones & Logic

The engine places every coin into one of five tactical buckets:

### 1. 🟢 RETEST ZONE (The "Buy the Dip" Zone)

**Logic**: Price is above the 200 EMA but within striking distance (0% to +5%).

- **Meaning**: The asset is in a macro uptrend but has pulled back to support.
- **Strategy**: This is the highest Risk:Reward entry zone for spot bags or swing longs.
- **Action**: Look for lower timeframe reversal patterns (e.g., 1H bullish divergence) to enter.

### 2. 🔵 TRENDING (The "Momentum" Zone)

**Logic**: Price is safely above the 200 EMA (+5% to +30%).

- **Meaning**: The trend is healthy and established.
- **Strategy**: Standard trend-following.
- **Action**: Trade the "Prophet" strategy signals (1H/4H entries).

### 3. ⚠️ OVEREXTENDED (The "FOMO" Zone)

**Logic**: Price is significantly extended (>30%) above the 200 EMA.

- **Meaning**: The asset has moved too far, too fast, and is effectively "floating in space."
- **Strategy**: High risk of mean reversion.
- **Action**: **DO NOT FOMO LONG.** Look for "De-Risk" signals or wait for the inevitable retest.

### 4. 🔮 FLIPPENING (The "Pivot" Zone)

**Logic**: Price has crossed the 200 EMA (up or down) within the last candle.

- **Meaning**: A potential regime change is occurring right now.
- **Action**: Watch closely. If it claims the level, it enters the Retest/Trending zone. If it rejects, it confirms the bear trend.

### 5. 🔴 LOST (The "No Fly" Zone)

**Logic**: Price is below the 200 EMA.

- **Meaning**: The asset is in a macro downtrend.
- **Strategy**: Counter-trend trading only (high risk) or shorting.
- **Action**: Avoid for spot holdings. Focus on assets in the Green/Blue zones.

## Technical Implementation

- **Source**: `backend/app/indicators/trend_radar.py`
- **Data**: Requires Daily candles to compute an accurate 200D EMA.
- **Update Frequency**: Calculated every minute, but conceptually changes slowly (Daily timeframe).
