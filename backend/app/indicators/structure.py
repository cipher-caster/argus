import pandas as pd
from typing import Dict, List, Any
import logging

from app.exceptions import CalculationError, ValidationError

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
        
        The "Monday Range" strategy identifies the high/low established on the first
        trading day of the week and monitors for breakouts, traps, and fakeouts.
        
        Args:
            df_data: Dictionary mapping symbols to their OHLCV DataFrames
            
        Returns:
            List of dicts containing structure analysis for each symbol
            
        Raises:
            ValidationError: When DataFrame structure is invalid
            CalculationError: When analysis fails for technical reasons
        """
        if not df_data or not isinstance(df_data, dict):
            raise ValidationError("df_data must be a non-empty dictionary")
        
        results = []
        
        for symbol, df in df_data.items():
            if df.empty or len(df) < 7:
                logger.debug(f"Skipping {symbol}: insufficient data ({len(df)} rows)")
                continue

            try:
                # Validate required columns
                required_cols = {'high', 'low', 'close'}
                if not required_cols.issubset(df.columns):
                    missing = required_cols - set(df.columns)
                    logger.warning(f"Skipping {symbol}: missing columns {missing}")
                    continue
                
                # 1. Identify current week's Monday
                # Ensure we use timestamp column as index if present (standard from get_candles_df)
                if 'timestamp' in df.columns:
                    df = df.set_index('timestamp')

                # Convert index to datetime if not already
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index)
                
                last_ts = df.index[-1]
                # Use .dt.isocalendar().week for pandas compatibility (fixes deprecation warning)
                current_week = last_ts.isocalendar().week
                current_year = last_ts.year
                
                # Filter for this week's data
                week_numbers = df.index.isocalendar().week
                this_week_df = df[(week_numbers == current_week) & (df.index.year == current_year)]
                
                if this_week_df.empty:
                    logger.debug(f"Skipping {symbol}: no data for current week")
                    continue

                # Find Monday (Dayofweek 0)
                monday_df = this_week_df[this_week_df.index.dayofweek == 0]
                
                # If no Monday data yet (e.g., today is Sunday start of week?), skip
                if monday_df.empty:
                    # Fallback: Use last week's Monday if currently early Monday?
                    # For now, simplistic: if no Monday, no range.
                    logger.debug(f"Skipping {symbol}: no Monday data yet")
                    continue

                # Monday Range
                monday_high = monday_df['high'].max()
                monday_low = monday_df['low'].min()
                
                current_price = float(df['close'].iloc[-1])
                
                # 2. Determine Status
                status = "TRAPPED"  # Default
                
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
                             status = "FAKEOUT_LOW"  # Bullish Reclaim

                results.append({
                    "symbol": symbol,
                    "price": current_price,
                    "monday_high": float(monday_high),
                    "monday_low": float(monday_low),
                    "status": status,
                    "range_pct": round((monday_high - monday_low) / monday_low * 100, 2)
                })

            except (KeyError, IndexError) as e:
                logger.warning(f"Structure scan failed for {symbol}: data issue - {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error in structure scan for {symbol}: {e}", exc_info=True)
                continue
                
        return sorted(results, key=lambda x: x['status'])

