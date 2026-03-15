---
name: argus-market-intelligence
description: Provides real-time cryptocurrency market analysis and signal reporting using the Argus platform. Use when the user asks for market summaries, coin deep-dives (BTC, SOL, etc.), trading signals (Oracle/Titan), or long-term investment (HODL) views.
---

# Argus Market Intelligence

## Overview

This skill transforms Gemini CLI into a specialized crypto market analyst using the Argus analytics platform. It can fetch live data from the local Argus API and generate structured intelligence reports.

## Core Workflows

### 1. Market Health Check
Before any analysis, ensure the Argus stack is operational:
- **Location:** `/home/mjm/Documents/projects/argus/`
- **Action:** Run `docker compose up -d backend worker redis db` (Exclude `frontend` to save resources).
- **Verification:** `curl -s http://localhost:8000/api/market/summary` (Wait for sync if `cache-empty`).

### 2. Market Pulse Report
Generate a high-level overview of the entire market.
- **Trigger:** "How is the market?", "Market summary", "Top signals".
- **Data Source:** `/api/market/summary`, `/api/analytics/signal-summary`, `/api/analytics/screener`, `/api/analytics/best-setups`.
- **No Noise:** Exclude SMC technicals (FVG/MSS) to maintain high-level awareness.
- **Template:** See `references/report_templates.md#market-report`.

### 3. Coin Deep-Dive
Detailed analysis for a specific symbol (e.g., BTC, SOL, ETH).
- **Trigger:** "Report on BTC", "Analyze SOL", "Is ETH a buy?".
- **Data Source:** `/api/ticker/{SYMBOL}`, `/api/strategy/oracle/{SYMBOL}`, `/api/strategy/titan/{SYMBOL}`.
- **SMC Layer:** Include FVG, MSS, and Sweep data ONLY for deep-dives to ensure no-noise reporting.
- **Template:** See `references/report_templates.md#coin-report`.

### 4. Long-Term (HODL) Analysis
Strategic view for long-term accumulation.
- **Trigger:** "Should I hold BTC?", "Long term view for SOL", "Accumulate ETH".
- **Data Source:** High-timeframe Oracle (12H, 1D, 1W) and Titan (1D, 1W) data.
- **Template:** See `references/report_templates.md#hodl-view`.

## Resource Guides

- **Interpretation:** See `references/interpretation_guide.md` for Oracle scores, Titan signals, and MTF confluence meanings.
- **Templates:** See `references/report_templates.md` for report structures.

## Usage Constraints
- **Selective Depth:** Maintain high-level summaries for general market pulse. Do not include SMC technicals unless specifically requested or a 100% Elite Confluence signal is detected.
- **API Base:** `http://localhost:8000`
- **Symbol Format:** `BASE/USDT` (URL encode as `BASE%2FUSDT`).
- **Communication:** Adhere to Amazon 4Cs. No fluff.
