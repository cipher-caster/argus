from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class ConfluenceAggregator:
    """
    "The Confluence Engine"
    Aggregates 'Earnest' scores across the entire market to determine
    Global Market State (Sleeping vs Trending).
    """

    def analyze(self, screener_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Input: List of results from the Oracle Screener (already computed).
        Output: Global Market State metrics.
        """
        total = len(screener_results)
        if total == 0:
            return {"state": "UNKNOWN", "consensus": 0}

        # Counters
        bullish_count = 0
        bearish_count = 0
        sleeping_count = 0
        
        # Earnest Score Distribution
        score_dist = {i: 0 for i in range(-5, 6)} # -4 to +4 (using 5 for buffer?) logic says max 4

        for res in screener_results:
            score = res.get('score', 0)
            state = res.get('state', '')
            
            # Count States
            if state == "SLEEPING":
                sleeping_count += 1
            
            # Count Bias
            if score >= 3:
                bullish_count += 1
            elif score <= -3:
                bearish_count += 1
            
            # Track distribution
            safe_score = max(-4, min(4, int(score)))
            score_dist[safe_score] = score_dist.get(safe_score, 0) + 1

        # Calculate Percentages
        sleep_pct = (sleeping_count / total) * 100
        bull_pct = (bullish_count / total) * 100
        bear_pct = (bearish_count / total) * 100
        
        # Determine Verdict
        verdict = "CHOP"
        
        if sleep_pct > 60:
            verdict = "SLEEPING"
        elif bull_pct > 50:
            verdict = "TSUNAMI_BULL"
        elif bear_pct > 50:
            verdict = "TSUNAMI_BEAR"
        elif (bull_pct + bear_pct) > 60:
             verdict = "VOLATILE" # Lots of strong signals but mixed direction?
        
        return {
            "verdict": verdict,
            "metrics": {
                "total_analyzed": total,
                "sleeping_pct": round(sleep_pct, 1),
                "bullish_pct": round(bull_pct, 1),
                "bearish_pct": round(bear_pct, 1)
            },
            "score_distribution": score_dist
        }
