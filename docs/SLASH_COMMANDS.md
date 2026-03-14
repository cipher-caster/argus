# Argus Slash Commands & Intelligence Reports

**Last Updated**: 2026-03-14

This document covers the Claude Code slash commands available in this project, how to use them, and how to interpret the output — including signal logic, price levels, spot setup guidance, and long-term HODL analysis.

---

## Available Commands

| Command | Description |
|---|---|
| `/read [COIN]` | Deep-dive report on a single coin |
| `/read [COIN] [timeframe]` | Same with a specific Oracle micro timeframe |
| `/read market` | Full market overview |
| `/read [COIN] hold` | HODL/long-term accumulation analysis |

**Keyword synonyms for HODL mode**: `hold`, `hodl`, `long`, `invest`, `accumulate`, `swing`, `position`

**Examples**:
```
/read BTC
/read ETH 4h
/read SOL hold
/read market
/read BTC long
/read MATIC accumulate
```

**Requires**: Argus backend running at `http://localhost:8000`.
If offline: `docker-compose up -d`

---

## What APIs Are Called

### Coin Report (`/read BTC`)

| Call | Endpoint | Purpose |
|---|---|---|
| 1 | `GET /api/ticker/BTC%2FUSDT` | Live price |
| 2 | `GET /api/strategy/oracle/BTC%2FUSDT?micro_tf=1h&macro_tf=1d` | Oracle signal + backtest |
| 3 | `GET /api/strategy/titan/BTC%2FUSDT?timeframe=4h` | Titan signal + indicators |
| 4 | `GET /api/market/coins?search=BTC&page_size=10` | 24H/7D change, volume, market cap |

### HODL mode adds:

| Call | Endpoint | Purpose |
|---|---|---|
| 5 | `GET /api/strategy/oracle/BTC%2FUSDT?micro_tf=12h&macro_tf=1d` | Intermediate swing view |
| 6 | `GET /api/strategy/oracle/BTC%2FUSDT?micro_tf=1d&macro_tf=1w` | Daily structure + weekly macro |
| 7 | `GET /api/strategy/titan/BTC%2FUSDT?timeframe=1d` | Daily Titan trend |
| 8 | `GET /api/strategy/titan/BTC%2FUSDT?timeframe=1w` | Weekly Titan trend + SuperTrend |

### Market Report (`/read market`)

| Call | Endpoint | Purpose |
|---|---|---|
| 1 | `GET /api/market/summary` | Top gainers, losers, volume |
| 2 | `GET /api/analytics/signal-summary` | Sentiment, market state |
| 3 | `GET /api/analytics/screener?timeframe=1h&limit=20` | Top Oracle signals |
| 4 | `GET /api/analytics/best-setups?timeframe=4h&limit=10` | Best confluence setups |
| 5 | `GET /api/indicators/market/dashboard` | BTC volatility, ADX, dominance |

---

## How to Read the Report

### Price Section

Standard market data. Key things to check:
- **7D Change** — is the coin in a broader recovery or still falling?
- **24H Range** — is current price near the top (resistance) or bottom (support) of the day's range?
- **Volume** — low volume on a move = weak; high volume = conviction

---

### Oracle Signal Section

Oracle uses **Prophet v9.0** — a 4-voter scoring system (Earnest Brain) filtered by a macro check.

#### Earnest Score (-4 to +4)

| Score | Signal | Meaning |
|---|---|---|
| +3 to +4 | STRONG_BUY | All voters bullish, high conviction long |
| +1 to +2 | BUY | Majority bullish, moderate setup |
| 0 | NEUTRAL | Split vote, no edge — wait |
| -1 to -2 | SELL | Majority bearish |
| -3 to -4 | STRONG_SELL | All voters bearish, high conviction short |

#### The 4 Voters

| Voter | Bullish (+1) | Bearish (-1) | Neutral (0) |
|---|---|---|---|
| **RSI** | 50–70 (momentum building) | 30–50 (momentum fading) | ≥70 overbought or ≤30 oversold |
| **Bollinger** | Price in upper band | Price in lower band | Near midband |
| **ADX** | ADX > 20 & price above EMA200 | ADX > 20 & price below EMA200 | ADX ≤ 20 (no trend) |
| **EMA** | Price above EMA200 | Price below EMA200 | — |

**How to read a split vote (score = 0)**:
- Check which specific voters are bullish vs bearish
- Example: RSI -1, BB -1, ADX +1, EMA +1 → price is above EMA200 with ADX trend, but momentum is fading. The macro structure is bullish but current candles are weak. Good context for a dip buy.

#### Macro Filter (1D/1W)

Three macro checks that filter the Earnest score:

| Flag | What it checks | Bullish when |
|---|---|---|
| `trend` | EMA200 slope on daily | Price trending above EMA200 |
| `cloud` | Ichimoku Cloud (daily) | Price above cloud |
| `obv` | OBV momentum | Volume flowing into the coin |

- All three `true` = strong macro bull — run the earnest signal at full size
- Mix of true/false = caution, reduce size
- All three `false` = macro bear — avoid longs even on bullish earnest scores

#### Oracle State

| State | What it means | How to trade |
|---|---|---|
| `TRENDING` | Strong directional move | Ride the trend, trail stop |
| `RANGING` | Sideways consolidation | Tighter TP, avoid chasing breakouts |
| `SLEEPING` | No volatility, no signal | Wait. Don't force a trade |
| `VOLATILE` / `DANGER` | High ATR, erratic moves | Reduce size significantly, widen stops |

---

### Backtest Performance Section

Oracle runs a live backtest on recent historical signals using:
- **TP = ATR × 3.0** (take profit)
- **SL = ATR × 1.5** (stop loss)
- **Reward-to-risk ratio: 2:1**
- **Break-even win rate: 33.3%**

| Win Rate | Rating | What it means |
|---|---|---|
| > 50% | ✅ Green | Edge confirmed — this setup has historically been profitable |
| 33–50% | 🟡 Yellow | Marginal — above break-even but thin edge |
| < 33% | 🔴 Red | Below break-even — current regime is unfavorable |
| `null` | — | Fewer than 10 trades — insufficient data, treat as unproven |

**Important**: A low win rate doesn't mean the coin is bad — it means Oracle's *current signal logic* isn't working well in the current market regime for this coin. Check manually or use Titan as a second opinion.

---

### Titan Signal Section

Titan is a **hybrid trend + momentum strategy**. It uses SuperTrend, EMA crossovers, MACD, and RSI.

#### Signal Types

| Signal | Meaning | Action |
|---|---|---|
| `BUY` | Trend confirmed bullish, momentum aligned | Enter at market |
| `SELL` | Trend confirmed bearish, momentum aligned | Short or exit longs |
| `BUY_LIMIT` | Bullish structure but waiting for pullback | Set a limit order at the entry price shown |
| `SELL_LIMIT` | Bearish structure but waiting for bounce | Set a limit order at the entry price shown |
| `WAIT_OB` | Oversold — potential bounce setup | Watch for reversal candle, then enter |
| `WAIT_OS` | Overbought — potential rejection | Wait for distribution candle, then short |

#### Confidence

| Level | Meaning | Sizing |
|---|---|---|
| 80% | Strong conviction | Full position size |
| 60% | Moderate conviction | Half to 3/4 size |
| 0% | No conviction | Avoid or paper trade only |

#### Key Indicators in Titan

From `titan.indicators` in the API response:

| Indicator | What to check |
|---|---|
| `supertrend` | The most important level. Price above = bullish trend. Price below = bearish trend. A 4H close through it flips the Titan trend. |
| `ema20` | Short-term momentum. Price above = short-term bullish. Below = short-term bearish. |
| `ema50` | Medium-term trend. When EMA20 crosses EMA50 upward = bullish. Downward = bearish. |
| `rsi` | Momentum. 50+ = building. 70+ = overbought (caution). 30– = oversold (bounce watch). |
| `macd` | Direction of momentum. `UP` = bullish momentum building. `DOWN` = bearish momentum. |
| `adx` | Trend strength. > 20 = trending. ≤ 20 = ranging/choppy. |

---

### Spot Setup Section

Always shown for every coin report. Gives a ready-to-use buy plan for spot traders (no leverage, no shorting).

**Stance labels:**
- **BUY** — setup is active, enter at the given price
- **WAIT** — not yet, but here's the exact price that triggers it
- **AVOID** — macro is bearish, wait for support confirmation

**How to use it:**
1. Check the stance first
2. If WAIT — set a price alert at the Entry level, not before
3. Use TP1 as your first sell target (take 50–70% of position)
4. Use TP2 as your second sell target (remaining position)
5. Set the Cut Loss as a hard stop — if price closes below it on the relevant timeframe, exit

**Risk/Reward**: A minimum of 1.5:1 to TP1 is required for a valid setup. Below 1.5:1 means the entry is too late and risk outweighs reward.

---

### Key Levels & What to Watch Section

This section translates all the technical data into plain conditional setups.

**How to read IF/THEN statements:**
- The IF is the trigger — a specific price + candle close timeframe
- The THEN is the consequence — what changes in Oracle/Titan, where price likely goes next
- Always wait for a **close** (not just a touch) at the stated timeframe

**Invalidation levels:**
- The most important lines in the report
- Bull case invalidated = the level below current price where the bullish thesis breaks down → exit longs
- Bear case invalidated = the level above where the bearish thesis breaks down → cover shorts, watch for reversal

---

### Long-Term / HODL Section

*(Only shown when long-term keywords are used: `hold`, `hodl`, `long`, `invest`, `accumulate`)*

Uses a **3-timeframe stack**: 12H Oracle + 1D Oracle + 1W Titan

#### How to read the Macro Trend table

| Timeframe | Role | What it tells you |
|---|---|---|
| **12H** | Intermediate swing | Is the current multi-day move bullish or bearish? Early trend changes show here first |
| **1D** | Structural trend | The main daily trend. This is what most swing traders follow |
| **1W** | Macro direction | The big picture. This determines whether you're in a bull or bear market for this coin |

**Alignment rule**: If all 3 agree → high conviction in that direction. If 12H is recovering but 1D and 1W are still bearish → early signal, not confirmed yet. Wait for 1D to agree before sizing up.

#### Accumulation Zones

Three zones are given for DCA planning:

| Zone | When to use |
|---|---|
| **Strong Accumulation** | Near current price — for when you believe the floor is in. Only valid if 12H is showing recovery signals |
| **Aggressive Accumulation** | A meaningful pullback — better entry, better RR. The ideal first tranche |
| **Deep Value** | Major support / capitulation zone — only deploy if macro confirms a flush |

#### DCA Strategy

- **3 tranches** spread across the zones
- Default split: 40% / 35% / 25% (heaviest at best entry, lightest as insurance at deep value)
- If 1W Titan is in a confirmed SELL, delay Tranche 1 — don't start DCA until there's at least a 12H BUY signal
- Dollar-cost average means you don't need to nail the exact bottom

#### Long-Term Targets

Derived from:
- **T1**: First major resistance (often the weekly EMA20 or nearest historical STRONG_BUY cluster)
- **T2**: Structural resistance (weekly SuperTrend or prior swing high)
- **T3**: Previous cycle high or 2–3× from accumulation zone

**Hold verdict labels:**
- **ACCUMULATE** — macro supports it, DCA can begin now
- **WAIT TO ACCUMULATE** — macro is unclear/recovering, wait for confirmation before Tranche 1
- **AVOID FOR NOW** — strong macro downtrend, don't DCA yet — wait for 1W Titan to turn bullish

---

## Reading the Chart (on /chart/SYMBOL)

The Argus chart at `http://localhost:3000/chart/BTC-USDT` gives you a live OHLCV view with optional overlays. Here's how to use the indicators alongside the `/read` report:

### EMA overlays

Add **EMA 20** and **EMA 50** from the indicator panel. Cross-reference with Titan:
- Price above EMA20 and EMA50, with EMA20 > EMA50 → bullish structure (Titan likely BUY)
- Price below both, EMA20 < EMA50 → bearish structure (Titan likely SELL)
- EMAs converging (flat) → ranging market, Oracle likely SLEEPING or NEUTRAL

### Bollinger Bands

Add from indicator panel. Cross-reference with Oracle Bollinger voter:
- Price walking the upper band → BB voter = +1 (bullish momentum)
- Price in the lower band → BB voter = -1 (bearish momentum)
- Price in the middle → BB voter = 0 (no signal)
- Band width expanding → increased volatility (Oracle state → VOLATILE)
- Band width squeezing → consolidation coming (Oracle state → SLEEPING, breakout setup)

### RSI

- **Above 50**: RSI voter = +1. Momentum is with buyers
- **Below 50**: RSI voter = -1. Momentum with sellers
- **70+**: Overbought — RSI voter goes neutral (0). Titan may show WAIT_OS
- **30–**: Oversold — RSI voter goes neutral (0). Titan may show WAIT_OB
- **Divergence** (price makes new high but RSI doesn't): potential reversal signal not captured by Oracle, use manually

### MACD

Shows the same MACD crossover that Titan tracks in `momentum.macd_crossed`:
- Cross **UP** on the chart = Titan momentum turns bullish
- Cross **DOWN** on the chart = Titan momentum turns bearish
- MACD histogram expanding above zero = strong bullish momentum
- MACD histogram shrinking → momentum fading, check for potential exit

### Candle patterns to watch (not tracked by Oracle/Titan — manual)

These won't show in the `/read` report but are important context on the chart:
- **Long wick rejections** at key levels (SuperTrend, EMA20) → confirms the level is holding
- **Engulfing candles** at support → early reversal signal before Oracle flips
- **Inside bars** near resistance → indecision, breakout incoming
- **Volume spike** on a green candle at support → institutional accumulation

---

## Quick Reference

### What to do with each signal combination

| Oracle | Titan | Spot Action |
|---|---|---|
| STRONG_BUY | BUY | Enter full position at market |
| BUY | BUY | Enter 50–75% position |
| BUY | BUY_LIMIT | Wait for limit entry price, then enter |
| NEUTRAL (positive split) | BUY | Enter 25–50%, wait for Oracle to confirm |
| NEUTRAL | NEUTRAL | Set alerts at Key Levels, don't enter |
| NEUTRAL | BUY_LIMIT | Watchlist — if limit fills and Oracle improves, add |
| SELL | any | No spot buy. Wait for HODL zone if long-term |
| STRONG_SELL | any | No spot buy. Check Accumulation Zone for DCA plan |

### When to override "wait"

- If HODL mode shows ACCUMULATE with all 3 macro TFs recovering: DCA tranche 1 even with NEUTRAL short-term signal
- If price is at the Deep Value accumulation zone: start a small position regardless of short-term signal — the RR at that level justifies it

---

## Related Documents

- [API Reference](./backend/API.md) — full endpoint documentation
- [Oracle Screener](./analytics/ORACLE_SCREENER.md) — Oracle voter logic in detail
- [Titan Strategy](./analytics/TITAN_STRATEGY.md) — Titan signal generation
- [Strategies Overview](./strategies/OVERVIEW.md) — Oracle + Titan combined
- [AI Agent Guide](./AI_AGENT_GUIDE.md) — codebase overview for developers/agents
