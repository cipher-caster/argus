Call the Argus trading API and produce a trade management report.

Make these API calls (backend at http://localhost:8000):
1. GET /api/trading/positions?status=PENDING
2. GET /api/trading/history?limit=10
3. GET /api/trading/config

If the backend is down, say so and suggest `docker-compose up -d`.

Format the output as follows:

---

## Argus Trade Manager — {today's date}

### Config
- **Status:** {Enabled ✅ / Paused ⏸}
- Initial Capital: ${initial_capital} | Max Positions: {max_concurrent_positions}
- Risk Per Trade: {max_position_size_pct}% | Min Conviction: {min_conviction}
- Order Expiry: {order_expiry_hours}h | Max Drawdown: {max_drawdown_pct}%

---

### Pending Orders ({count})

For each PENDING position (waiting to be filled):
`{SYMBOL} {LONG/SHORT}` | Entry @ **${intended_entry}** | TP: ${intended_tp} (+{tp_pct:.1f}%) | SL: ${intended_sl} (-{sl_pct:.1f}%)
Size: ${quote_amount:.0f} USDT | Risk: ${risk_amount:.2f} | Created: {time ago}
Conviction: {conviction} | {fired_reason}

---

### Recent Trade History (last 10 closed)

For each closed position:
{WIN ✅ / LOSS ❌ / EXPIRED ⬜} `{SYMBOL} {LONG/SHORT}` | Entry **${actual_entry}** → Exit **${actual_exit}** | PnL **{pnl_pct:+.1f}%** (${pnl_usd:+.2f})
Held: {time from filled_at to closed_at} | {fired_reason}

---

### Actions
- Enable trading: `PUT /api/trading/config {"enabled": true}`
- Close position: `POST /api/trading/close/{id}`
- Close all: `POST /api/trading/close-all`
- Pause: `POST /api/trading/pause`

Or use the dashboard Trading widget to toggle status.
