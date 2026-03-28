# /read — Argus Market Intelligence Report

**Usage:**
- `/read BTC` — deep-dive report on a single coin
- `/read ETH` — single coin on a specific timeframe (default: 4h Titan)
- `/read market` — full market overview
- `/read` — same as `/read market`

---

## How to Execute This Skill

The argument is: `$ARGUMENTS`

Parse `$ARGUMENTS`:
- If empty or equals `market` → run **Market Report** (section A)
- Otherwise → extract coin ticker (e.g., `BTC`, `SOL`, `ETH`) and optional timeframe → run **Coin Report** (section B)

The Argus backend runs at **http://localhost:8000**. Use `Bash` with `curl -s` to call every endpoint — **do not use `WebFetch`** for localhost URLs, as it upgrades HTTP to HTTPS and will fail.

Symbols are always in `BASE/USDT` format (e.g., `BTC/USDT`). When used in a URL path, encode the slash: `BTC%2FUSDT`.

---

## Section A — Market Report

Fetch all of these in parallel using multiple `Bash` calls with `curl -s`:

1. `GET http://localhost:8000/api/market/summary`
2. `GET http://localhost:8000/api/strategy/regime`
3. `GET http://localhost:8000/api/analytics/best-setups?timeframe=4h&limit=10`
4. `GET http://localhost:8000/api/indicators/market/dashboard`
5. `GET http://localhost:8000/api/analytics/signal-log?source=live&limit=20`
6. `GET http://localhost:8000/api/analytics/signal-log?source=counter&limit=5`

### Output format

```
## Argus Market Report — {current time}

### Market Pulse
- Regime: {regime.regime} (BTC {regime.btc_price} vs EMA50 {regime.ema50_value})
- Direction filter: {BEAR → SHORT only, BULL → LONG only}
- BTC Dominance: {dashboard.btc_dominance}
- BTC Volatility: {dashboard.btc_volatility}/100
- ADX Trend Strength: {dashboard.market_adx}/100

### Best Setups (4H — Titan + Regime)
List up to 5 from best_setups.data, showing:
  {symbol} {direction} | Conviction {conviction}/100 | Entry {entry} | TP {tp} | SL {sl}
  Win Rate: {win_rate}% ({total_trades} trades) or "Insufficient data" if null
  MTF: 4H {✓/✗} 1D {✓/✗} 12H {✓/✗} 1W {✓/✗} (skip row if timeframe_confirmation is null)
  Reason: {reason}

### Active Signals (Live)
From signal_log.data, filter for outcome="OPEN":
If none: "No active signals — waiting for next 4H candle setup"
If any, list each:
  {symbol} {direction} | Entry {entry} | TP {tp} (+X%) | SL {sl} (-X%) | Conviction {conviction}/100 | Age {time since fired_at}
Then show summary: Win Rate {summary.win_rate}% ({summary.win} W / {summary.loss} L) or "No closed trades yet" if win_rate is null
Counter-regime tracking: {count of source=counter OPEN signals from fetch #6} setups observed (not traded)

### Top Movers (24H)
From market/summary:
  Gainers: top 3 with % change
  Losers: top 3 with % change
  Volume Leaders: top 3

### Summary
2–3 sentence narrative: what is the overall market bias, which setups stand out, any caution flags (e.g., low win rate, no MTF confluence, low ADX = choppy market).
```

---

## Section B — Coin Report

First, resolve the coin ticker to `BASE/USDT` format (e.g., `BTC` → `BTC/USDT`, `SOL` → `SOL/USDT`).

Parse optional timeframe from `$ARGUMENTS` (e.g., `BTC 1d` → `timeframe=1d`, default `timeframe=4h`).

Also check `$ARGUMENTS` for long-term intent keywords: `long`, `hold`, `hodl`, `invest`, `accumulate`, `swing`, `position`. If any are present, set `long_term_mode = true`.

Fetch all of these in parallel:

1. `GET http://localhost:8000/api/market/tickers?symbols=BTC%2FUSDT`
2. `GET http://localhost:8000/api/strategy/regime`
3. `GET http://localhost:8000/api/strategy/titan/BTC%2FUSDT?timeframe=4h`
4. `GET http://localhost:8000/api/market/coins?search=BTC&page=1&page_size=10`
5. `GET http://localhost:8000/api/analytics/signal-log?symbol=BTC&source=live&limit=10`

If `long_term_mode = true`, also fetch these in parallel with the above:

6. `GET http://localhost:8000/api/strategy/titan/BTC%2FUSDT?timeframe=1d`
7. `GET http://localhost:8000/api/strategy/titan/BTC%2FUSDT?timeframe=1w`

Replace `BTC%2FUSDT` with the actual encoded symbol. The `market/coins` response is paginated — find the matching coin by checking the `symbol` field in the returned list.

### Output format

```
## Argus Report: {BASE} — {current time}

### Price
- Current: {ticker.price}
- 1H Change: {market_coins[0].change_1h}%
- 24H Change: {market_coins[0].change_24h}%
- 7D Change: {market_coins[0].change_7d}%
- 24H Range: {market_coins[0].low_24h} – {market_coins[0].high_24h}
- Volume (24H): {market_coins[0].volume_24h}
- Market Cap: {market_coins[0].market_cap} (Rank #{market_coins[0].rank})

### Market Regime
- Regime: {regime.regime} (BULL / BEAR / UNKNOWN)
- BTC Price vs EMA50: {regime.btc_price} vs {regime.ema50_value}
- Direction filter: {BEAR → SHORT only, BULL → LONG only, UNKNOWN → all}

### Titan Signal ({titan timeframe})
- Signal: {titan.signal}
- Confidence: {titan.confidence}%
- Trend: {titan.trend}
- Entry: {titan.entry} | TP: {titan.tp} | SL: {titan.sl}
- Advice: {titan.advice}
- Reasons:
  {list titan.reasons}

### Signal Log ({BASE})
From signal_log.data:
If any OPEN signals exist for this coin:
  Active: {direction} | Entry {entry} | TP {tp} (+X%) | SL {sl} (-X%) | Conviction {conviction}/100 | Fired {time since fired_at}
If recent closed signals (WIN/LOSS):
  Recent: {direction} {outcome} | Entry {entry} → Resolved @ {resolved_price} | Regime at resolution: {regime_at_resolution} | Time to resolve: {time_to_resolution_ms/3600000:.1f}h
  Track Record: {summary.win_rate}% WR ({summary.win}W / {summary.loss}L)
If no signals: "No signal log entries for {BASE} yet"

### Spot Setup

This section is always included. It gives a plain buy/sell plan for spot trading (no leverage, no shorting).

**Logic rules:**

1. If regime is BULL AND Titan signal is BUY or BUY_LIMIT:
   - Entry: use Titan entry if it's a LIMIT (below current price), otherwise current price
   - TP1: Titan TP level
   - TP2: next major resistance above TP1 (use EMA levels or round numbers)
   - Cut Loss: Titan SL level or SuperTrend
   - Stance: "BUY — {reason in one sentence}"

2. If regime is BULL but Titan is NEUTRAL/WAIT, OR regime is UNKNOWN:
   - Do NOT say "no trade" and leave it at that
   - Instead, give a conditional spot plan: the specific price where it becomes a buy, the TP levels from that entry, and the cut loss
   - Entry: "Wait for 4H close above {nearest resistance}" — use EMA20 or first resistance level
   - TP1: next resistance after entry
   - TP2: major resistance / recent swing high
   - Cut Loss: SuperTrend or EMA50 (whichever is more relevant)
   - Stance: "WAIT — not a buy yet. Becomes a spot buy on confirmation above {level}"

3. If regime is BEAR:
   - No spot buy — regime filters out longs in bear markets
   - Give the level where regime would flip (BTC reclaims weekly EMA50)
   - Stance: "AVOID — bear regime. Spot re-entry when BTC reclaims ${regime.ema50_value} (weekly EMA50)"

**Always calculate and show the Risk/Reward ratio:**
- RR = (TP1 - Entry) / (Entry - Cut Loss)
- Show it as e.g. "1.8:1 to TP1, 3.2:1 to TP2"
- If RR to TP1 is below 1.5:1, note it as "tight RR — consider waiting for better entry"

**Output format:**
```
### Spot Setup
Stance: {BUY / WAIT / AVOID} — {one sentence reason}

| Level     | Price     | Notes                          |
|-----------|-----------|--------------------------------|
| Entry     | $X,XXX    | {market / limit / on break of} |
| TP1       | $X,XXX    | {+X% — first resistance / ...} |
| TP2       | $X,XXX    | {+X% — swing high / ...}       |
| Cut Loss  | $X,XXX    | {-X% — SuperTrend / EMA50 / ...}|

Risk/Reward: {X.X}:1 to TP1 | {X.X}:1 to TP2
```

### Key Levels & What to Watch

Extract the following levels from the Titan indicators (titan.indicators):

**Resistance levels** (above current price) — list in ascending order:
- EMA20: {titan.indicators.ema20} — label as "Immediate resistance" if above price
- Recent swing high: identify from price action context
- Any round number confluence near those levels (e.g., $2,100, $2,200)

**Support levels** (below current price) — list in descending order:
- EMA50: {titan.indicators.ema50} — label as "First support"
- SuperTrend: {titan.indicators.supertrend} — label as "Trend floor — break = bearish"
- Recent swing low: identify from price action context

**Conditional setups — write these as IF/THEN statements:**

For each key level, write one line:
- IF price reclaims [level] with a 1H candle close above → [what signal to expect / suggested action]
- IF price loses [level] on 4H close → [what that means for bias / where next support is]

Rules for writing conditionals:
- Be specific: name the exact price, the timeframe for confirmation (1H close, 4H close), and the action
- Reference the SuperTrend as the line between bullish and bearish Titan trend
- Reference regime flip level: BTC weekly EMA50 (from regime endpoint)
- If Titan is NEUTRAL, explain what price action would trigger a BUY or SELL signal
- Include a "key invalidation" line: the level where the current neutral/wait thesis is proven wrong in either direction

**Example format:**
```
🔴 Resistance: $2,074 (EMA20) — currently acting as a lid
   → IF 1H closes above $2,074 with volume: watch for RSI to confirm; Titan tilts toward BUY
   → Target on break: $2,150 (recent swing high cluster)

🟡 Support: $2,047 (EMA50) — first cushion
   → IF 4H closes below $2,047: momentum weakening, Titan confidence drops

🔴 Critical: $2,022 (SuperTrend) — trend floor
   → IF 4H closes below $2,022: Titan flips BEARISH confirmed, bias = SHORT, next support ~$1,980

📍 Invalidation levels:
   Bull case invalidated below: $2,022 (SuperTrend break)
   Bear case invalidated above: $2,150 (reclaim of swing high)
```

### Long-Term / HODL View
*(Only include this section if `long_term_mode = true`)*

This section uses the regime + multi-TF Titan data (fetched in calls 6–7) to answer: "Is this a good coin to buy and hold? Where do I accumulate? What are realistic targets?"

**Macro Trend — Multi-Timeframe Stack:**
Use the regime + higher-TF Titan responses to build a layered picture:

| Timeframe | Titan Signal | Titan Trend | Confidence |
|-----------|--------------|-------------|------------|
| 4H        | {titan_4h.signal} | {titan_4h.trend} | {titan_4h.confidence}% |
| 1D        | {titan_1d.signal} | {titan_1d.trend} | {titan_1d.confidence}% |
| 1W        | {titan_1w.signal} | {titan_1w.trend} | {titan_1w.confidence}% |

Regime: {regime.regime} (BTC vs weekly EMA50)

Combined macro verdict: **BULLISH / BEARISH / NEUTRAL** — one word + one sentence reasoning.
Rule: if regime + 2 or more Titan timeframes agree on direction, that is the macro verdict. If they disagree, it's NEUTRAL/CAUTION.

**Accumulation Zones:**
Derive 2–3 price zones where a long-term buyer should consider buying, based on:
- 1W Titan SuperTrend (strongest long-term floor)
- 1D Titan SL level
- Weekly EMA50 (regime flip level — major structural support/resistance)
- Label each zone: "Strong Accumulation", "Aggressive Accumulation", "Deep Value"

Format:
```
🟢 Strong Accumulation:  $X,XXX – $X,XXX  (near current price / slight dip)
🟡 Aggressive Acc.:      $X,XXX – $X,XXX  (meaningful pullback, better RR)
🔵 Deep Value:           $X,XXX – $X,XXX  (major support / capitulation zone)
```

**DCA Strategy:**
Based on the zones above, suggest a simple 3-tranche DCA plan:
- Tranche 1 (e.g., 40% of position): at or near current price if macro is not bearish, otherwise at Strong Accumulation zone
- Tranche 2 (e.g., 35%): at Aggressive Accumulation zone
- Tranche 3 (e.g., 25%): at Deep Value zone
- If macro is strongly bearish (1W Titan SELL + BEAR regime), delay Tranche 1 and say so

**Long-Term Targets:**
Derive realistic upside targets for a hold of 3–12 months:
- Target 1: nearest major resistance above current price (from Titan levels + round numbers)
- Target 2: previous cycle high or 2× accumulation zone price
- Target 3: stretch target (3×+ from accumulation zone)
- For each, state approximate % gain from current price

**Hold or Avoid:**
End with a clear one-line verdict:
- "ACCUMULATE — macro trend supports long-term holding. Use the DCA plan above."
- "WAIT TO ACCUMULATE — macro is bearish/unclear. Start DCA only at Aggressive zone or below."
- "AVOID FOR NOW — strong macro downtrend. Re-evaluate when 1W Titan turns bullish."

### Summary
3–4 sentences. Do NOT just say "wait." Instead:
1. State the current situation in one sentence (price relative to key levels, regime + Titan alignment)
2. Give the bull trigger: the specific price and confirmation needed to go long
3. Give the bear trigger: the specific price that confirms the downside
4. State the recommended stance right now: what to monitor, where to set alerts

If `long_term_mode = true`, add a 5th sentence summarizing the HODL verdict and best accumulation zone.
```

---

## Interpretation Reference

### Regime (BTC Weekly EMA50)
| Regime | Meaning |
|--------|---------|
| BULL | BTC above weekly EMA50 — favor LONG setups |
| BEAR | BTC below weekly EMA50 — favor SHORT setups |
| UNKNOWN | Insufficient data — no direction filter |

### Titan Signals
- `BUY` / `SELL` — market entry now, trend confirmed
- `BUY_LIMIT` / `SELL_LIMIT` — wait for pullback to limit entry price before entering
- `WAIT_OB` — wait for oversold bounce (mean reversion setup)
- `WAIT_OS` — wait for overbought rejection

### Titan Confidence
- `80%` — strong conviction, full size
- `60%` — moderate, half to 3/4 size
- `0%` — low, avoid or paper trade only

### MTF Confluence (Eliz + Mayne Framework)
- **Eliz lane**: 4H (entry trigger) + 1D (swing structure)
- **Mayne lane**: 12H (higher-TF bias) + 1W (macro/weekly direction)
- All 4 confirmed = maximum conviction
- 2–3 confirmed = tradeable but size down
- 0–1 confirmed = avoid, no confluence

### Win Rate Context
- Break-even at 2:1 RR = **33.3%**
- < 33% = historically unprofitable setup, trade with caution
- 33–50% = acceptable
- > 50% = edge confirmed, can size up
- `null` = fewer than 10 historical trades, insufficient data

---

## Error Handling

- If any endpoint returns a non-200 status or times out, note it in the report as "Unavailable" and continue with available data.
- If the backend is not running (connection refused), report: "Argus backend is offline. Start it with `docker-compose up -d`."
- If the coin is not found in `/api/market/coins`, skip that section and note it.

---

## Logging (STRICTLY NO PII)

**STRICT MANDATE:** NEVER include personal information, names or user-specific identifiers, or user-specific context in these logs. All reports must be strictly technical and market-focused.

After displaying the report to the user, always save it to `docs/market-reports/` using the Write tool.

**File naming:**
- Market report: `docs/market-reports/YYYY-MM-DD-market.md`
- Coin report: `docs/market-reports/YYYY-MM-DD-{BASE}.md` (e.g., `2026-03-24-BTC.md`)
- If the file already exists, append to it — do not create a new file.

**File content:**
- First run of the day: write the full report with a `# Argus ...` H1 heading.
- Subsequent runs (file exists): append a `---` divider followed by `## HH:MM` timestamp heading, then the report body (skip the H1, start from Market Pulse / Price section).

Do not announce the logging step — just do it silently after displaying the report.
