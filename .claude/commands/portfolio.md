Call the Argus trading API and produce a portfolio intelligence report.

Make these API calls (backend at http://localhost:8000):
1. GET /api/trading/portfolio
2. GET /api/trading/positions?status=OPEN,PENDING
3. GET /api/trading/stats

If the backend is down, say so and suggest `docker-compose up -d`.

Format the output as follows:

---

## Argus Portfolio — {today's date}

**Mode:** Paper Trading | **Status:** {Enabled/Paused}

### Balance
- Realized: **${balance}** (started at ${initial_capital})
- Unrealized: **${unrealized_pnl:+.2f}**
- Total Equity: **${total_equity}**
- Exposure: ${exposure.total_usdt} / ${initial_capital} ({exposure.pct_of_balance}%)

---

### Open Positions ({count})

For each OPEN position:
`{SYMBOL} {LONG/SHORT}` | Entry **${actual_entry}** → Now **${current_price}** | PnL **{unrealized_pnl_pct:+.1f}%** (${unrealized_pnl_usd:+.2f})
TP: ${intended_tp} | SL: ${intended_sl} | Size: ${quote_amount:.0f} | Conviction: {conviction}

### Pending Orders ({count})
For each PENDING position:
`{SYMBOL} {LONG/SHORT}` | Waiting for entry @ ${intended_entry} | TP: ${intended_tp} | SL: ${intended_sl}
Age: {time since created_at}

---

### Performance
- Total Trades: {total_trades} | Wins: {wins} | Losses: {losses}
- Win Rate: **{win_rate}%** | Profit Factor: {profit_factor}
- Avg Win: **+{avg_win_pct}%** | Avg Loss: **{avg_loss_pct}%**
- Total PnL: **${total_pnl_usd:+.2f}**
- Max Drawdown: {max_drawdown_pct}%

---

If trading is disabled (enabled: false), add a note:
> Trading is currently **paused**. Enable via `PUT /api/trading/config {"enabled": true}` or the Trading page.

If there are no positions yet, suggest enabling trading and waiting for the next 4H signal scan.
