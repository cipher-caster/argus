import pandas as pd
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class StructureScanner:
    """
    "The Weekly Trap" Engine.
    Identifies the "Monday Range" (High/Low of the first trading day) and
    scans for Breakouts, Traps, and Fakeouts.
    """

    def analyze(self, df_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Scans all DataFrames for Monday Range structure.
        Assumes DF is Daily or Hourly. Ideally Hourly for precision, but logic handles Daily.
        """
        results = []
        
        for symbol, df in df_data.items():
            if df.empty or len(df) < 7:
                continue

            try:
                # 1. Identify current week's Monday
                # Ensure we use timestamp column as index if present (standard from get_candles_df)
                if 'timestamp' in df.columns:
                    df = df.set_index('timestamp')

                # Convert index to datetime if not already
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index)
                
                last_ts = df.index[-1]
                current_week = last_ts.week
                current_year = last_ts.year
                
                # Filter for this week's data
                this_week_df = df[(df.index.isocalendar().week == current_week) & (df.index.year == current_year)]
                
                if this_week_df.empty:
                    continue

                # Find Monday (Dayofweek 0)
                monday_df = this_week_df[this_week_df.index.dayofweek == 0]
                
                # If no Monday data yet (e.g., today is Sunday start of week?), skip
                if monday_df.empty:
                    # Fallback: Use last week's Monday if currently early Monday? 
                    # For now, simplistic: if no Monday, no range.
                    continue

                # Monday Range
                monday_high = monday_df['high'].max()
                monday_low = monday_df['low'].min()
                
                current_price = float(df['close'].iloc[-1])
                
                # 2. Determine Status
                status = "TRAPPED" # Default
                
                if current_price > monday_high:
                    status = "BREAKOUT_UP"
                elif current_price < monday_low:
                    status = "BREAKOUT_DOWN"
                else:
                    # Check for Fakeout (Swept low then reclaimed?)
                    # Simplistic check: Did we go below low previously in the week but are now inside?
                    # Get lows of week excluding Monday
                    post_monday_df = this_week_df[this_week_df.index > monday_df.index[-1]]
                    if not post_monday_df.empty:
                         min_post_mon = post_monday_df['low'].min()
                         if min_post_mon < monday_low and current_price > monday_low:
                             status = "FAKEOUT_LOW" # Bullish Reclaim

                results.append({
                    "symbol": symbol,
                    "price": current_price,
                    "monday_high": float(monday_high),
                    "monday_low": float(monday_low),
                    "status": status,
                    "range_pct": round((monday_high - monday_low) / monday_low * 100, 2)
                })

            except Exception as e:
                logger.warning(f"Structure scan failed for {symbol}: {e}")
                continue
                
        return sorted(results, key=lambda x: x['status'])

