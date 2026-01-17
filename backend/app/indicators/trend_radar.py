import pandas as pd
import pandas_ta as ta
from typing import Dict, List, Any

class TrendRadar:
    """
    "The Trend God" Engine
    Analyzes the position of all assets relative to their 200-Day EMA.
    Categorizes them into tactical buckets for the "Trend Radar" dashboard.
    """

    def __init__(self):
        self.ema_len = 200
        # Thresholds
        self.retest_threshold = 0.05  # Within 5% above EMA
        self.extended_threshold = 0.30 # > 30% above EMA
    
    def analyze(self, df_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Scans all provided DataFrames and returns the Trend Radar map.
        """
        results = []
        buckets = {
            "RETESTING": [],
            "BULLISH": [],
            "OVEREXTENDED": [],
            "LOST": [],
            "FLIPPENING": []
        }
        
        for symbol, df in df_data.items():
            if df.empty or len(df) < self.ema_len:
                continue

            # Ensure EMA is present
            if 'ema200' not in df.columns:
                df['ema200'] = ta.ema(df['close'], length=self.ema_len)

            row = df.iloc[-1]
            prev_row = df.iloc[-2]
            
            if pd.isna(row['ema200']):
                continue

            price = float(row['close'])
            ema = float(row['ema200'])
            
            # Distance Percentage
            dist_pct = (price - ema) / ema
            
            # Categorize
            status = "NEUTRAL"
            
            # Check for Flippening first (Crossed recently)
            # Bullish Flip: Prev < EMA, Curr > EMA
            # Bearish Flip: Prev > EMA, Curr < EMA
            crossed_up = prev_row['close'] < prev_row['ema200'] and row['close'] > row['ema200']
            crossed_down = prev_row['close'] > prev_row['ema200'] and row['close'] < row['ema200']
            
            if crossed_up or crossed_down:
                status = "FLIPPENING"
                buckets["FLIPPENING"].append(symbol)
            elif price < ema:
                status = "LOST"
                buckets["LOST"].append(symbol)
            else:
                # Above EMA
                if dist_pct <= self.retest_threshold:
                    status = "RETESTING"
                    buckets["RETESTING"].append(symbol)
                elif dist_pct >= self.extended_threshold:
                    status = "OVEREXTENDED"
                    buckets["OVEREXTENDED"].append(symbol)
                else:
                    status = "BULLISH"
                    buckets["BULLISH"].append(symbol)

            results.append({
                "symbol": symbol,
                "price": price,
                "ema200": ema,
                "distance_pct": round(dist_pct * 100, 2),
                "status": status,
                "volume": float(row['volume']) if 'volume' in row else 0
            })

        # Sort results by distance percentage (descending)
        results = sorted(results, key=lambda x: x['distance_pct'], reverse=True)

        return {
            "map": results,
            "buckets": buckets,
            "summary": {
                "total_bullish": len(buckets["BULLISH"]) + len(buckets["OVEREXTENDED"]) + len(buckets["RETESTING"]),
                "total_bearish": len(buckets["LOST"]) + len(buckets.get("FLIPPENING", []))
            }
        }
    
    def _fix_buckets_keys(self, buckets):
        # Helper not needed if we utilize the dict correctly above.
        # But wait, I used "overextended" and "retesting" lowercase in the summary calc above?
        # Let's fix that in the actual code I write.
        pass
