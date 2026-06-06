
import asyncio
import pandas as pd
import pandas_ta as ta
from typing import Dict, List, Any
import logging
from prettytable import PrettyTable

# Adjust path to find app module
import sys
import os
sys.path.append(os.getcwd())

from app.providers import get_provider
from app.strategies.titan import TitanStrategy

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

async def fetch_data(symbol: str, timeframe: str, limit: int = 1000) -> pd.DataFrame:
    """Fetch historical data using the configured provider with Pagination"""
    provider = get_provider()
    try:
        all_candles = []
        BATCH_SIZE = 1000
        start_ts = None
        
        while len(all_candles) < limit:
            remaining = limit - len(all_candles)
            fetch_limit = min(remaining, BATCH_SIZE)

            # CCXT pages forward from `since`. To get `limit` candles ending now,
            # compute a start timestamp and page forward in BATCH_SIZE chunks.
            tf_ms = 3600 * 1000  # default 1h
            if start_ts is None:  # only calculate once
                if timeframe == '4h': tf_ms = 4 * 3600 * 1000
                elif timeframe == '1d': tf_ms = 24 * 3600 * 1000
                elif timeframe == '15m': tf_ms = 15 * 60 * 1000
                
                now = pd.Timestamp.now().timestamp() * 1000
                start_ts = int(now - (limit * tf_ms))
            
            # If we already have candles, continue from last one's close time
            if all_candles:
                 start_ts = all_candles[-1].timestamp + 1

            batch = await provider.get_ohlcv(symbol, timeframe, limit=BATCH_SIZE, since=start_ts)
            
            if not batch:
                break
                
            all_candles.extend(batch)
            
            if len(batch) < BATCH_SIZE: # End of data
                break
                
        # Trim excess
        all_candles = all_candles[-limit:]
        
        data = [{
            'timestamp': c.timestamp,
            'open': c.open,
            'high': c.high,
            'low': c.low,
            'close': c.close,
            'volume': c.volume
        } for c in all_candles]
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    finally:
        await provider.close()

class Backtester:
    def __init__(self, initial_capital=1000):
        self.initial_capital = initial_capital
        self.balance = initial_capital
        self.trades = []
        self.active_trade = None
        self.equity_curve = []

    def run_titan(self, df: pd.DataFrame, stake: float = 100.0):
        """
        Run Titan Strategy Backtest.
        Optimized to calculate indicators once, then iterate for signals.
        """
        logger.info(f"Running Titan Backtest on {len(df)} candles...")

        # Pre-calculate indicators once (ema200, rsi, macd, supertrend, atr) in-place,
        # then iterate — far faster than calling analyze() on growing windows.
        titan = TitanStrategy()
        titan._add_indicators(df)

        for idx in range(200, len(df)):  # start once the 200 EMA is valid
            row = df.iloc[idx]

            # Manage an open trade before looking for a new entry
            if self.active_trade:
                self._check_exit(row)
                continue

            # Replicate Titan's signal logic inline to avoid the full analyze() call.

            # Trend
            ema = row['ema200']
            trend = "BULLISH" if row['close'] > ema else "BEARISH"
            
            # Momentum (RSI + MACD)
            rsi = row['rsi']
            macd = row['macd']
            macd_sig = row['macd_signal']
            
            rsi_bullish = rsi > 50
            macd_bullish = macd > macd_sig
            mom_score = (1 if rsi_bullish else 0) + (1 if macd_bullish else 0)
            
            # Volatility
            # Skip squeeze check for speed, assume normal
            
            # Signal Logic
            signal_type = "NEUTRAL"
            
            # SuperTrend (titan uses it)
            st_dir = row.get('supertrend_dir', 0)
            st_bullish = st_dir > 0
            
            if trend == "BULLISH":
                # Buy dip (RSI < 45) or MACD breakout, gated by a bullish SuperTrend
                if st_bullish:
                    if rsi < 45: signal_type = "BUY"
                    elif macd_bullish and not rsi_bullish: pass
                    elif macd > macd_sig: signal_type = "BUY"
            elif trend == "BEARISH":
                if not st_bullish:
                    if rsi > 55: signal_type = "SELL"
                    elif macd < macd_sig: signal_type = "SELL"
            
            # Entry
            if signal_type in ["BUY", "SELL"]:
                price = row['close']
                atr = row['atr']
                ts = row['timestamp']

                # V3 Monday-range filter: only trade a breakout of this week's
                # Monday high/low (pandas dayofweek: 0=Mon, 6=Sun).
                day_of_week = ts.dayofweek

                monday_high = None
                monday_low = None

                if day_of_week == 0:
                    # Monday itself builds the range — no trade.
                    continue
                else:
                    # Tue-Sun: find this week's Monday candles. Scanning back up to
                    # 42 candles (7 days * 6 4h-candles) is cheap.
                    current_week = ts.isocalendar().week
                    lookback = df.iloc[max(0, idx-42):idx]
                    monday_candles = lookback[
                        (lookback['timestamp'].dt.dayofweek == 0) & 
                        (lookback['timestamp'].dt.isocalendar().week == current_week)
                    ]
                    
                    if not monday_candles.empty:
                        monday_high = monday_candles['high'].max()
                        monday_low = monday_candles['low'].min()
                    else:
                        # No Monday data found? Skip.
                        continue
                        
                # 2. Apply Filter
                is_valid = False
                if signal_type == "BUY" and monday_high:
                    if price > monday_high: is_valid = True # Price above Monday Range => Bullish Expansion
                elif signal_type == "SELL" and monday_low:
                    if price < monday_low: is_valid = True # Price below Monday Range => Bearish Expansion
                    
                if not is_valid:
                    continue

                # Open the trade with a trailing-stop exit (uncapped upside, dynamic SL)
                side = "LONG" if signal_type == "BUY" else "SHORT"
                
                self.active_trade = {
                    "entry_time": row['timestamp'],
                    "symbol": "TEST",
                    "side": side,
                    "entry_price": price,
                    "stake": stake,
                    "sl": None, # Dynamic
                    "tp": None, # Uncapped
                    "amount": stake / price
                }

    def _check_exit(self, row):
        t = self.active_trade
        price = row['close']
        st_val = row.get('supertrend', 0)
        st_dir = row.get('supertrend_dir', 0)
        
        result = None
        
        # Calculate Duration
        current_ts = row['timestamp']
        # Approx bars held
        # Since we iterate, we can track index or just time diff.
        # 1d = 86400s.
        time_diff = (current_ts - t['entry_time']).total_seconds()
        days_held = time_diff / 86400
        
        # Time-based exit: close stagnant trades held longer than MAX_HOLD_DAYS.
        MAX_HOLD_DAYS = 10
        
        if days_held >= MAX_HOLD_DAYS:
             result = "TIME_LIMIT"
             exit_price = price
        
        # Exit Condition: SuperTrend Flip (Trend Change)
        # Long Exit: Price closes below SuperTrend (or ST Dir becomes -1)
        # Short Exit: Price closes above SuperTrend (or ST Dir becomes 1)
        
        if not result:
            if t['side'] == "LONG":
                # If SuperTrend flips Bearish (-1), we exit
                if st_dir < 0: 
                    result = "TRAIL_STOP"
                    exit_price = price # Close at the candle that confirmed the flip
                elif price < st_val: # Double check price vs line
                     result = "TRAIL_STOP"
                     exit_price = price
                     
            else: # SHORT
                # If SuperTrend flips Bullish (1), we exit
                if st_dir > 0:
                    result = "TRAIL_STOP"
                    exit_price = price
                elif price > st_val:
                    result = "TRAIL_STOP"
                    exit_price = price
                
        if result:
            # Calculate PnL
            if t['side'] == "LONG":
                raw_pnl = (exit_price - t['entry_price']) * t['amount']
            else:
                raw_pnl = (t['entry_price'] - exit_price) * t['amount']
                
            # Fee (0.1% total)
            fee = t['stake'] * 0.001
            net_pnl = raw_pnl - fee
            
            self.trades.append({
                "entry_time": t['entry_time'],
                "exit_time": row['timestamp'],
                "side": t['side'],
                "result": result,
                "pnl": net_pnl,
                "roi": (net_pnl / t['stake']) * 100,
                "duration": days_held
            })
            self.active_trade = None

    def report(self):
        if not self.trades:
            return "No trades executed."
            
        total_pnl = sum(t['pnl'] for t in self.trades)
        wins = len([t for t in self.trades if t['pnl'] > 0])
        total = len(self.trades)
        win_rate = (wins / total) * 100
        
        longs = [t for t in self.trades if t['side'] == "LONG"]
        shorts = [t for t in self.trades if t['side'] == "SHORT"]
        
        long_pnl = sum(t['pnl'] for t in longs)
        short_pnl = sum(t['pnl'] for t in shorts)
        
        t = PrettyTable(["Metric", "Value"])
        t.add_row(["Total Trades", total])
        t.add_row(["Win Rate", f"{win_rate:.1f}%"])
        t.add_row(["Total PnL", f"${total_pnl:.2f}"])
        t.add_row(["Avg PnL/Trade", f"${total_pnl/total:.2f}"])
        t.add_row(["Long PnL", f"${long_pnl:.2f} ({len(longs)})"])
        t.add_row(["Short PnL", f"${short_pnl:.2f} ({len(shorts)})"])
        
        return str(t)

async def main():
    print("Fetching data (~2500 4h candles per symbol)...")

    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]

    print("\n--- TITAN STRATEGY RESULTS (V3 Filtered - 4H) ---")

    for symbol in symbols:
        df = await fetch_data(symbol, "4h", limit=2500)
        runner = Backtester()
        runner.run_titan(df, stake=100.0)
        print(f"\n{symbol} (4h):")
        print(runner.report())

if __name__ == "__main__":
    asyncio.run(main())
