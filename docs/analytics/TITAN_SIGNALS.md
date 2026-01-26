# Titan Signals (Predictive Engine)

The **Titan Signals** dashboard is the operational heart of the strategy. Unlike the general scanner, which identifies current conditions, the Signals engine is **Predictive**—it tells you where the market _will_ be an ideal trade.

## Predictive Logic

The engine uses a combination of **Overbought/Oversold (OB/OS)** filters and **Support/Resistance** estimation to generate orders.

### 1. Wait States (FO-MO Prevention)

The system actively prevents "FOMO" (Fear Of Missing Out) by entering **Wait States** when momentum is overextended.

- **WAIT_OB (Wait Overbought)**: Price is above the 200 EMA (Bullish), but RSI > 70.
  - _Logic_: Do not market buy.
  - _Action_: Recommends a **Limit Buy** at the **EMA 20** or **SuperTrend** support level.
- **WAIT_OS (Wait Oversold)**: Price is below the 200 EMA (Bearish), but RSI < 30.
  - _Logic_: Do not market sell.
  - _Action_: Recommends a **Limit Sell** at the **EMA 20** or **SuperTrend** resistance level.

### 2. Signal Types

| Signal         | Condition                           | Action                                |
| :------------- | :---------------------------------- | :------------------------------------ |
| **BUY**        | Bullish Trend + RSI Pullback (< 45) | **Market Buy**                        |
| **BUY_LIMIT**  | Bullish Trend + Strong Momentum     | **Limit Buy** at Support (EMA 20)     |
| **WAIT_OB**    | Bullish Trend + RSI > 70            | **Wait** for Pullback to Support      |
| **SELL**       | Bearish Trend + RSI Rally (> 55)    | **Market Sell**                       |
| **SELL_LIMIT** | Bearish Trend + Strong Momentum     | **Limit Sell** at Resistance (EMA 20) |
| **WAIT_OS**    | Bearish Trend + RSI < 30            | **Wait** for Bounce to Resistance     |

## Entry & Target Calculation

The system calculates an **Ideal Entry** based on the proximity to established support/resistance.

- **Ideal Entry**: The higher of EMA 20 or SuperTrend (for Longs) or the lower (for Shorts).
- **Distance**: The dashboard displays the `% Distance` from current price to the Ideal Entry.
- **Stop Loss (SL)**: Calculated as `1.5 x ATR` from the Entry point.
- **Take Profit (TP)**: Calculated as `3.0 x ATR` from the Entry point (2:1 R:R).

## Confidence & Sizing

Confidence is mapped to the strength of the alignment:

- **80% (High)**: Perfect Dip/Rally setup.
- **60% (Medium)**: Trend following with Limit Entry.
- **0% (Wait)**: Correction in progress.

## Technical Implementation

- **Backend**: `backend/app/strategies/titan.py` -> `_generate_signal` method.
- **Frontend**: `frontend/src/components/analytics/TitanSignalsPanel.tsx`
- **API Data**: `TitanRadarItem` schema includes `reasons` and `entry` price.
