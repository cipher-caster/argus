# Titan Unified Strategy (Titan Radar)

**"The Titan System"** is a professional-grade hybrid trading strategy that combines **Trend Following** with **Momentum Scalping**. It is designed to capture high-probability setups by aligning multiple technical factors.

## Core Philosophy

The strategy operates on a simple principle: **Trend is King**, but **Momentum is Queen**.

1.  **Respect the Trend**: Never trade against the 200 EMA.
2.  **Time the Entry**: Use Momentum (RSI + MACD) to find precise entry points.
3.  **Manage Risk**: Use ATR-based targets to ensure positive expectancy.

---

## The Titan Radar

The **Titan Radar** scans the top 50 perpetual markets in real-time to find assets that meet the strict criteria of the Titan System.

### 1. Trend Filter (The "Titan Trend")

Every asset is first filtered by its relationship to the **200-period Exponential Moving Average (EMA)**.

- **BULLISH**: Price > 200 EMA. Only look for Longs.
- **BEARISH**: Price < 200 EMA. Only look for Shorts.

### 2. Signal Generation

Once the trend is established, the system looks for specific momentum setups:

#### **Bullish Setups (Long)**

- **Dip Buy**: Trend is Bullish + RSI pulls back to Oversold territory (< 45).
- **Momentum Breakout**: Trend is Bullish + MACD crosses UP.

#### **Bearish Setups (Short)**

- **Rally Sell**: Trend is Bearish + RSI rallies to Overbought territory (> 55).
- **Momentum Breakdown**: Trend is Bearish + MACD crosses DOWN.

### 3. Risk Management Targets

The Radar automatically calculates key levels based on **ATR (Average True Range)**:

- **Entry**: Current Market Price.
- **Stop Loss (SL)**: 1.5x ATR from Entry.
- **Take Profit (TP)**: 3.0x ATR from Entry (targeting a 2:1 Risk/Reward ratio).

### 4. Sizing Advice

Based on the confluence of indicators, the system provides position sizing advice:

- **Aggressive (10%)**: High confidence (Trend + Momentum + Volatility align).
- **Standard (1-2%)**: Normal confidence.
- **Conservative**: Choppy or weak signals.

---

## Indicators Used

- **EMA 200**: Trend Baseline.
- **RSI 14**: Momentum and Overbought/Oversold levels.
- **MACD (12/26/9)**: Momentum trend confirmation.
- **Bollinger Bands (20/2)**: Volatility ("Squeeze") detection.
- **ATR 14**: Volatility-based Stop Loss and Take Profit.

## Technical Implementation

- **Source**: `backend/app/strategies/titan.py`
- **API Endpoint**: `GET /api/analytics/titan-radar`
- **Update Frequency**: Real-time (on every candle close for the selected timeframe, usually 4H).
