import logging
import pandas as pd
from typing import List, Dict, Any
from app.strategies.oracle import OracleStrategy

logger = logging.getLogger(__name__)

def run_oracle_screener(df_data: Dict[str, pd.DataFrame], btc_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Orchestrates the Oracle analysis across multiple symbols and returns a summarized screener list.
    """
    oracle = OracleStrategy()
    results = []
    
    # 1. Pre-calculate BTC indicators if available
    if not btc_df.empty:
        oracle._add_indicators(btc_df)
        btc_macro = btc_df.iloc[-1]
    else:
        btc_macro = None

    for symbol, df in df_data.items():
        if df.empty or len(df) < 50:
            continue
            
        try:
            # 2. Add indicators to current coin
            oracle._add_indicators(df)
            last_row = df.iloc[-1]
            
            # 3. Calculate Earnest Score (Micro)
            # Uses RSI, ADX, BB, EMA from df
            earnest = oracle._calculate_earnest_score(last_row)
            
            # 4. Calculate Market State
            state = oracle._detect_market_state(last_row)
            
            # 5. Opportunity Tag
            opp = "NONE"
            if earnest['score'] >= 3: opp = "LONG"
            elif earnest['score'] <= -3: opp = "SHORT"
            
            # 6. Relative Strength (vs BTC)
            strength_tag = "NEUTRAL"
            if btc_macro is not None:
                # Basic relative performance: Coin % change vs BTC % change
                coin_pct = (df['close'].iloc[-1] / df['close'].iloc[0] - 1)
                btc_pct = (btc_df['close'].iloc[-1] / btc_df['close'].iloc[0] - 1)
                rel = coin_pct - btc_pct
                if rel > 0.05: strength_tag = "STRONG"
                elif rel < -0.05: strength_tag = "WEAK"

            # 7. Filter for meaningful setups (abs(score) >= 2)
            if abs(earnest['score']) >= 2:
                results.append({
                    "symbol": symbol,
                    "price": float(last_row['close']),
                    "score": earnest['score'],
                    "confidence": f"{abs(earnest['score'])}/4",
                    "bias": "BULLISH" if pd.notna(last_row.get('ema200')) and last_row['close'] > last_row['ema200'] else "BEARISH",
                    "state": state['state'],
                    "liquidity": "ACTIVE" if state['volatility_tag'] != "DANGER" else "HIGH",
                    "strength_vs_btc": strength_tag,
                    "opportunity": opp,
                    "advice": oracle._generate_advice(earnest, {"score": 0, "bias": "NEUTRAL"}, state, {"tp1": 0, "tp2": 0, "sl": 0}, "earnest")
                })
        except Exception as e:
            logger.warning(f"Screener error for {symbol}: {e}")
            continue

    # Sort by score strength
    return sorted(results, key=lambda x: abs(x['score']), reverse=True)
