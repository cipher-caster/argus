# The Confluence Engine (Market State)

**"The Confluence Engine"** is a global market sentiment aggregator. It answers the question: _"Is the market actually moving, or am I forcing it?"_

## Core Philosophy

Individual charts can be deceiving. A single coin might look bullish, but if 90% of the market is dumping, that setup is likely to fail. Conversely, if 90% of the market is "Sleeping" (low volatility), taking aggressive breakout trades is a clear path to losses.

This engine aggregates the **Earnest Score** (Prophet's multi-voter system) across the Top 50-100 coins to determine the Global State.

## Market States

### 1. 💤 MARKET SLEEPING (Cash is King)

**Logic**: >60% of coins have low "Sleeping" volatility scores.

- **Meaning**: Volume has dried up. No major moves are happening.
- **Strategy**: **Stay Cash.** Do not force trades. Wait for the wake-up call.

### 2. 🌊 BULL TSUNAMI (Aggressive Longs)

**Logic**: >50% of coins have a Bullish Consensus (Score >= 3/4).

- **Meaning**: The entire market is bidding. A rising tide lifts all boats.
- **Strategy**: Aggressive Longs. Breakouts work better. Pullbacks are shallow.

### 3. 🌊 BEAR TSUNAMI (Aggressive Shorts)

**Logic**: >50% of coins have a Bearish Consensus (Score <= -3/-4).

- **Meaning**: The entire market is dumping.
- **Strategy**: Aggressive Shorts. Supports are likely to break.

### 4. ⚡ CHOP / VOLATILE (PvP Mode)

**Logic**: Mixed signals. No clear majority.

- **Meaning**: The market is fighting. Some coins pumping, some dumping.
- **Strategy**: **Reduce Position Size.** Tighten stops. Take profits early ("Scalp Mode").

## Technical Implementation

- **Source**: `backend/app/indicators/confluence.py`
- **Logic**: Iterates through the results of the `OracleScreener` (Top 50 coins).
- **Consensus**: Counts how many coins are in "Strong Bull", "Strong Bear", or "Sleeping" states and calculates the percentage dominance.
