# The Weekly Trap (Structure Scanner)

**"The Weekly Trap"** is a market structure engine based on the **Monday Range** theory.

## Core Philosophy

In crypto, the trading range established on **Monday** often defines the boundaries for the rest of the week.

- **Monday High**: Major Weekly Resistance
- **Monday Low**: Major Weekly Support

The "Trap" refers to price action that spends the majority of the week chopping _inside_ this range, only to breakout (or fakeout) later in the week.

## Zones & Logic

The engine identifies the Monday Range for every asset and classifies its current price action:

### 1. 🟢 WEEKLY BREAKOUT (Bull)

**Logic**: Price has successfully closed **above** the Monday High.

- **Meaning**: The asset has escaped the weekly chop zone and is exploring new highs.
- **Action**: Look for retests of the Monday High (now Support) to enter longs.

### 2. 🔵 FAKEOUT / RECLAIM (Smart Money)

**Logic**: Price broke **below** the Monday Low, swept liquidity, and has now **reclaimed** the range (Price > Monday Low).

- **Meaning**: "Smart Money" trapped the bears who shorted the breakdown, and is now reversing price back into the range.
- **Action**: These are high-probability long setups with invalidation below the sweep low.

### 3. 🔴 WEEKLY BREAKDOWN (Bear)

**Logic**: Price has accepted **below** the Monday Low.

- **Meaning**: The asset is weak and likely searching for lower support.
- **Action**: Look for retests of the Monday Low (now Resistance) to enter shorts.

### 4. ⚪ TRAPPED (The Kill Zone)

**Logic**: Price is trading **between** the Monday High and Monday Low.

- **Meaning**: No clear direction. Chop market.
- **Action**: **DO NOT TRADE.** This is where accounts are slowly bled out. Wait for a breakout or a range rotation to the edges.

## Technical Implementation

- **Source**: `backend/app/indicators/structure.py`
- **Data**: Scans Hourly/Daily candles to identify the High and Low of the first trading day (Monday) of the current week.
- **Resets**: The range resets every week (Monday 00:00 UTC).
