# GEMINI.md — Argus Market Intelligence Skill

This document instructs Gemini CLI on how to serve as a market analyst using the Argus platform.

## 🎯 Activation Intent
Use this skill when the user asks for:
- "crypto market summary"
- "how is the market doing"
- "give me an update on [COIN]" (e.g., BTC, SOL)
- "top crypto signals"
- "best setups right now"

## 🚀 Step 1: Ensure Project is Running
1. Go to the project root: `/home/mjm/Documents/projects/argus/`
2. Run `docker compose up -d backend worker redis db` (Frontend is optional for summaries).
3. Verify backend is alive: `curl -s http://localhost:8000/api/market/summary`
   - If `total_coins` is 0 or it says `cache-empty`, wait 30–60s for the worker to sync.

## 📊 Step 2: Fetch Data
Fetch these endpoints via `curl` (since `web_fetch` might not hit localhost):
- `http://localhost:8000/api/market/summary`
- `http://localhost:8000/api/analytics/signal-summary`
- `http://localhost:8000/api/analytics/screener?timeframe=1h&limit=10`
- `http://localhost:8000/api/analytics/best-setups?timeframe=4h&limit=5`
- `http://localhost:8000/api/indicators/market/dashboard`

## 📝 Step 3: Format the Report
Follow the template defined in `.claude/commands/read.md`.

### Template Summary:
- **Market Pulse**: State, Sentiment (Bullish/Bearish %), BTC Dominance, Volatility, ADX.
- **Top Signals**: Highlights from `signal-summary`.
- **Oracle Screener (1H)**: Top 5 by score (symbol, bias, state).
- **Best Setups (4H)**: Top 5 by conviction (symbol, entry, TP, SL, win rate).
- **Top Movers**: Top 3 Gainers/Losers/Volume from `market/summary`.
- **Narrative Summary**: 2-3 sentences on overall bias and standout setups.

## 🔍 Step 4: Individual Coin Deep-Dive
If the user asks about a specific coin (e.g., "Tell me about SOL"):
1. Fetch:
   - `http://localhost:8000/api/ticker/{SYMBOL}%2FUSDT`
   - `http://localhost:8000/api/strategy/oracle/{SYMBOL}%2FUSDT?micro_tf=4h&macro_tf=1d`
   - `http://localhost:8000/api/strategy/titan/{SYMBOL}%2FUSDT?timeframe=4h`
2. Format using the "Coin Report" section in `.claude/commands/read.md`.
3. Include: Price, Oracle Signal (Score, Bias, Advice), Titan Signal (Trend, Confidence), Spot Setup (Entry, TP, SL), and Key Levels (Support/Resistance).

---
**Last Updated**: 2026-03-15
**Version**: 1.0.0
