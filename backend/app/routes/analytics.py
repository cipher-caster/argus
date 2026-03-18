"""
Futures analytics API routes
Uses CCXT-based OKXProvider for data fetching
Redis caching for performance optimization
"""
import logging
import time
import pandas as pd
import asyncio
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional

from app.schemas.analytics import (
    ScreenerResponse,
    MeanReversionResponse,
    MeanReversionItem,
    OracleSignalSummaryResponse,
    TitanRadarResponse,
    TitanRadarItem,
    BestSetupItem,
    BestSetupsResponse,
    SignalLogConfig,
    SignalLogItem,
    SignalLogSummary,
    SignalLogResponse,
)

from app.routes.strategy import get_candles_df, titan, oracle
from app.indicators.screener import run_oracle_screener
from app.indicators.mean_reversion import detect_mean_reversion
from app.providers import get_provider
from app.services.market_data import MarketDataService
from app.storage import RedisClient
from app.exceptions import DataProviderError, CacheError, CalculationError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

# Cache TTL in seconds.
# Must be > pre-warm interval (300s / 5min) to ensure the cache is always
# renewed before it expires. 360s gives a 60s safety buffer each cycle.
CACHE_TTL = 360  # 6 minutes


@router.get("/symbols")
async def get_supported_symbols(limit: int = 20):
    """Get list of commonly used futures symbols"""
    symbols = await MarketDataService.get_top_symbols(limit=limit)
    return {
        "symbols": symbols,
        "default": "BTCUSDT"
    }


async def fetch_all_candles(symbols: List[str], timeframe: str = "1h", limit: int = 250):
    """Helper to fetch candles for multiple symbols concurrently, reusing provider"""
    from app.providers.binance_provider import BinanceProvider

    provider = get_provider()

    # Probe non-Binance providers with a tight timeout before committing to a full
    # batch fetch. OKX (and similar) can be geo-blocked, causing every gather() call
    # to hang for the full CCXT timeout (~15s). A 4s probe detects this up-front
    # so we fall back to Binance once instead of paying the penalty 9× per job.
    if provider.name != "binance":
        try:
            await asyncio.wait_for(provider._ensure_loaded(), timeout=4.0)
        except Exception:
            await provider.close()
            logger.warning(f"{provider.name} unreachable for analytics, falling back to Binance")
            provider = BinanceProvider()

    try:
        tasks = [get_candles_df(sym, timeframe, limit, provider=provider) for sym in symbols]
        dataframes = await asyncio.gather(*tasks, return_exceptions=True)

        result = {
            sym: df for sym, df in zip(symbols, dataframes)
            if not isinstance(df, Exception) and df is not None and not df.empty
        }

        logger.info(f"Fetched candles for {len(result)}/{len(symbols)} symbols ({timeframe}, limit={limit})")
        return result
    except Exception as e:
        logger.error(f"Failed to fetch candles: {e}", exc_info=True)
        raise DataProviderError(f"Failed to fetch candle data: {e}")
    finally:
        await provider.close()


@router.get("/screener", response_model=ScreenerResponse)
async def get_oracle_screener(limit: int = 50, timeframe: str = "1h"):
    """Get Oracle analysis for top coins with specific timeframe"""
    cache_key = f"analytics:screener:{timeframe}:{limit}"
    
    # Try cache first
    cached = await RedisClient.get_json(cache_key)
    if cached:
        logger.debug(f"Cache HIT: {cache_key}")
        if isinstance(cached, list): return ScreenerResponse(data=cached, last_updated=0)
        return ScreenerResponse(**cached)
    
    # Cache miss - compute fresh data
    logger.debug(f"Cache MISS: {cache_key}")
    symbols = await MarketDataService.get_top_symbols(limit=limit)
    df_data = await fetch_all_candles(symbols, timeframe=timeframe)
    btc_df = df_data.get("BTCUSDT", pd.DataFrame())
    
    data = run_oracle_screener(df_data, btc_df)
    
    # Cache the result
    response = {"data": data, "last_updated": int(time.time() * 1000)}
    await RedisClient.set_json(cache_key, response, ttl=CACHE_TTL)
    return ScreenerResponse(**response)




@router.get("/contrarian-radar", response_model=MeanReversionResponse)
async def get_contrarian_radar(limit: int = 50, timeframe: str = "1h"):
    """Identify overextended coins for potential reversal with specific timeframe"""
    cache_key = f"analytics:contrarian:{timeframe}:{limit}"
    
    cached = await RedisClient.get_json(cache_key)
    if cached:
        if isinstance(cached, list): return MeanReversionResponse(data=[MeanReversionItem(**item) for item in cached], last_updated=0)
        return MeanReversionResponse(**cached)
    
    symbols = await MarketDataService.get_top_symbols(limit=limit)
    df_data = await fetch_all_candles(symbols, timeframe=timeframe)
    
    results = []
    for sym, df in df_data.items():
        rev = detect_mean_reversion(df)
        if rev['is_extended']:
            results.append(MeanReversionItem(symbol=sym, **rev))
    
    response = {"data": [r.model_dump() for r in results], "last_updated": int(time.time() * 1000)}
    await RedisClient.set_json(cache_key, response, ttl=CACHE_TTL)
    return MeanReversionResponse(**response)


@router.get("/signal-summary", response_model=OracleSignalSummaryResponse)
async def get_oracle_signal_summary():
    """High-level summary for the dashboard - fixed at top 20 for performance"""
    cache_key = "analytics:signal-summary"
    
    cached = await RedisClient.get_json(cache_key)
    if cached:
        return OracleSignalSummaryResponse(**cached)
    
    symbols = await MarketDataService.get_top_symbols(limit=20)
    df_data = await fetch_all_candles(symbols)
    btc_df = df_data.get("BTCUSDT", pd.DataFrame())
    
    screener_data = run_oracle_screener(df_data, btc_df)

    bullish = len([s for s in screener_data if s['score'] >= 3])
    bearish = len([s for s in screener_data if s['score'] <= -3])

    top_signals = [f"{s['symbol']} {s['score']}/4" for s in screener_data if abs(s['score']) >= 3][:5]

    # Derive market state directly from screener scores
    total = len(screener_data)
    if total > 0:
        bulls = len([s for s in screener_data if s['score'] >= 1])
        bears = len([s for s in screener_data if s['score'] <= -1])
        sleeping = len([s for s in screener_data if s['score'] == 0])
        bull_pct = bulls / total
        bear_pct = bears / total
        if bull_pct > 0.5 and bulls > 2 * max(bears, 1):
            market_state = "STRONG BULL"
        elif bear_pct > 0.5 and bears > 2 * max(bulls, 1):
            market_state = "STRONG BEAR"
        elif sleeping / total > 0.5:
            market_state = "SLEEPING"
        else:
            market_state = "NEUTRAL"
    else:
        market_state = "NEUTRAL"

    result = {
        "bullish_pct": round((bullish / len(screener_data)) * 100, 1) if screener_data else 0,
        "bearish_pct": round((bearish / len(screener_data)) * 100, 1) if screener_data else 0,
        "top_signals": top_signals,
        "market_state": market_state,
        "last_updated": int(time.time() * 1000)
    }
    
    await RedisClient.set_json(cache_key, result, ttl=CACHE_TTL)
    return OracleSignalSummaryResponse(**result)



@router.get("/best-setups", response_model=BestSetupsResponse)
async def get_best_setups(timeframe: str = "4h", limit: int = 50):
    """
    High-conviction setups where Oracle and Titan agree on direction.
    Returns max 10 results sorted by conviction score (0-100).
    """
    cache_key = f"analytics:best-setups:{timeframe}:{limit}"
    cached = await RedisClient.get_json(cache_key)
    if cached:
        return BestSetupsResponse(**cached)

    symbols = await MarketDataService.get_top_symbols(limit=limit)

    # Fetch Titan candles (primary timeframe)
    titan_candles = await fetch_all_candles(symbols, timeframe=timeframe, limit=300)

    # Reuse Oracle screener cache (1h) if available, else compute fresh
    screener_cache_key = f"analytics:screener:1h:{limit}"
    raw = await RedisClient.get_json(screener_cache_key)
    if raw is None:
        oracle_candles = await fetch_all_candles(symbols, timeframe="1h")
        btc_df = oracle_candles.get("BTCUSDT", pd.DataFrame())
        screener_list = run_oracle_screener(oracle_candles, btc_df)
    elif isinstance(raw, list):
        screener_list = raw
    else:
        screener_list = raw.get("data", [])

    oracle_lookup = {item["symbol"]: item for item in screener_list if isinstance(item, dict)}

    results = []
    for sym, df in titan_candles.items():
        try:
            t = titan.analyze(df)
            if "error" in t:
                continue

            t_signal = t["signal"]
            t_confidence = t["confidence"]

            is_long = t_signal in ("BUY", "BUY_LIMIT")
            is_short = t_signal in ("SELL", "SELL_LIMIT")
            if not (is_long or is_short) or t_confidence < 55:
                continue

            o = oracle_lookup.get(sym)
            if not o:
                continue

            o_score = o.get("score", 0)
            # Use the /5 score for conviction calculation
            oracle_pts = (abs(o_score) / 5) * 40
            titan_pts = (t_confidence / 100) * 40
            bonus = 0
            if t_signal in ("BUY", "SELL"):   # perfect setup, not just limit
                bonus += 10
            if abs(o_score) >= 4: # Strongest Oracle
                bonus += 10
            conviction = int(min(100, oracle_pts + titan_pts + bonus))

            targets = t.get("targets", {})
            price = float(df.iloc[-1]["close"])
            reasons = t.get("reasons", [])
            o_bias = o.get("bias", "NEUTRAL")
            reason = f"Oracle {o_bias} {o_score:+d}/5 | " + " | ".join(reasons[:2])

            results.append(BestSetupItem(
                symbol=sym,
                direction="LONG" if is_long else "SHORT",
                conviction=conviction,
                entry=round(float(targets.get("entry", price)), 6),
                tp=round(float(targets.get("tp", 0)), 6),
                sl=round(float(targets.get("sl", 0)), 6),
                reason=reason,
                oracle_score=o_score,
                titan_signal=t_signal,
            ))
        except Exception as e:
            logger.warning(f"best-setups error for {sym}: {e}")
            continue

    results.sort(key=lambda x: x.conviction, reverse=True)
    results = results[:10]

    # Enrich filtered results (≤10 coins) with:
    #   1. Oracle backtest stats — win_rate / total_trades
    #      Thresholds: ≥50% green, 33–49% yellow, <33% red (break-even = 33.3% at 2:1 RR).
    #      Both fields stay None when total_trades < 10 (insufficient sample).
    #
    #   2. Eliz+Mayne MTF confluence — Titan signal confirmed on 4 timeframes:
    #      Eliz lane → 4h (entry trigger) + 1d (swing structure)
    #      Mayne lane → 12h (higher-TF bias) + 1w (weekly/macro direction)
    #      A timeframe is "confirmed" if Titan agrees with the setup direction.
    if results:
        filtered_syms = [r.symbol for r in results]
        try:
            micro_dfs, daily_dfs, h12_dfs, w1_dfs = await asyncio.gather(
                fetch_all_candles(filtered_syms, timeframe="1h", limit=300),
                fetch_all_candles(filtered_syms, timeframe="1d", limit=300),
                fetch_all_candles(filtered_syms, timeframe="12h", limit=250),  # Titan needs 200+ candles
                fetch_all_candles(filtered_syms, timeframe="1w", limit=200),   # Titan needs 200+ candles
            )
            for item in results:
                is_long = item.direction == "LONG"

                # 1. Oracle backtest
                micro_df = micro_dfs.get(item.symbol)
                daily_df = daily_dfs.get(item.symbol)
                if micro_df is not None and daily_df is not None:
                    analysis = oracle.analyze(micro_df, daily_df)
                    perf = analysis.get("performance", {})
                    total = perf.get("total_trades", 0)
                    if total >= 10:
                        item.win_rate = perf.get("win_rate")
                        item.total_trades = total

                # 2. MTF confluence
                mtf_sources = {
                    "4h": titan_candles.get(item.symbol),  # Eliz — already fetched
                    "1d": daily_df,                         # Eliz — reuse from above
                    "12h": h12_dfs.get(item.symbol),        # Mayne
                    "1w": w1_dfs.get(item.symbol),          # Mayne
                }
                tf_confirmation = {}
                for tf, df in mtf_sources.items():
                    if df is None or df.empty:
                        tf_confirmation[tf] = False
                        continue
                    try:
                        t = titan.analyze(df)
                        sig = t.get("signal", "")
                        tf_confirmation[tf] = (
                            sig in ("BUY", "BUY_LIMIT") if is_long
                            else sig in ("SELL", "SELL_LIMIT")
                        )
                    except Exception:
                        tf_confirmation[tf] = False
                item.timeframe_confirmation = tf_confirmation
        except Exception as e:
            logger.warning(f"MTF enrichment failed: {e}")

    response = {"data": [r.model_dump() for r in results], "last_updated": int(time.time() * 1000)}
    await RedisClient.set_json(cache_key, response, ttl=CACHE_TTL)
    return BestSetupsResponse(**response)


@router.get("/titan-radar", response_model=TitanRadarResponse)
async def get_titan_radar(limit: int = 50, timeframe: str = "4h"):
    """Titan Unified System Scanner"""
    cache_key = f"analytics:titan:{timeframe}:{limit}"
    cached = await RedisClient.get_json(cache_key)
    if cached:
        if isinstance(cached, list): return TitanRadarResponse(data=[TitanRadarItem(**i) for i in cached], last_updated=0)
        return TitanRadarResponse(**cached)
    
    symbols = await MarketDataService.get_top_symbols(limit=limit)
    # Titan needs 200 candles. 4h is good default.
    df_data = await fetch_all_candles(symbols, timeframe=timeframe, limit=300)
    
    results = []
    for sym, df in df_data.items():
        try:
            analysis = titan.analyze(df)
            if "error" in analysis:
                logger.debug(f"Titan analysis error for {sym}: {analysis.get('error')}")
                continue
            
            # Convert analysis dict to Item
            # analysis has signal, confidence, trend, momentum(dict), vol(dict), targets(dict), sizing
            
            # Simplify momentum/vol description
            mom_str = analysis['momentum']['status']
            if analysis['momentum']['is_overbought']: mom_str += " (OB)"
            elif analysis['momentum']['is_oversold']: mom_str += " (OS)"
            
            vol_str = "SQUEEZE" if analysis['volatility']['squeeze'] else "NORMAL"
            
            item = TitanRadarItem(
                symbol=sym,
                price=df.iloc[-1]['close'],
                signal=analysis['signal'],
                confidence=analysis['confidence'],
                trend=analysis['trend'],
                momentum=mom_str,
                volatility=vol_str,
                entry=analysis.get('targets', {}).get('entry', 0), # This will now be ideal_entry from targets
                tp=analysis['targets'].get('tp', 0),
                sl=analysis['targets'].get('sl', 0),
                advice=analysis['sizing'],
                reasons=analysis.get('reasons', []),
                mss_type=analysis.get('mss_type'),
                sweep_type=analysis.get('sweep_type')
            )
            results.append(item)
        except CalculationError as e:
            logger.warning(f"Calculation error for {sym} in Titan radar: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error analyzing {sym}: {e}", exc_info=True)
            continue
            
    # Sort by confidence desc
    results.sort(key=lambda x: x.confidence, reverse=True)
    
    response = {"data": [r.model_dump() for r in results], "last_updated": int(time.time() * 1000)}
    await RedisClient.set_json(cache_key, response, ttl=CACHE_TTL)
    return TitanRadarResponse(**response)


SIGNAL_LOG_CONFIG_KEY = "signal_log:config"
SIGNAL_LOG_DEFAULTS = {
    "watchlist": [
        "BTCUSDT", "ETHUSDT", "BNBUSDT",
        "TRXUSDT", "XRPUSDT", "FETUSDT", "NEARUSDT",
        "ARBUSDT", "ATOMUSDT", "DOGEUSDT", "APTUSDT",
    ],
    "min_titan_confidence": 55,
    "review_days": 7,
    "block_sleeping": True,
    "block_volatile": True,
    "macro_guard": True,
    "block_btc_sell": True,
}


@router.get("/signal-log/config", response_model=SignalLogConfig)
async def get_signal_log_config():
    """Return current signal log configuration."""
    data = await RedisClient.get_json(SIGNAL_LOG_CONFIG_KEY)
    if data:
        return SignalLogConfig(**data)
    return SignalLogConfig(**SIGNAL_LOG_DEFAULTS)


@router.put("/signal-log/config", response_model=SignalLogConfig)
async def update_signal_log_config(config: SignalLogConfig):
    """Update signal log configuration. Persisted in Redis."""
    payload = config.model_dump()
    # Use large TTL since setex requires positive ttl (no SET without expiry)
    await RedisClient.set_json(SIGNAL_LOG_CONFIG_KEY, payload, ttl=86400 * 365)
    return config


@router.get("/signal-log", response_model=SignalLogResponse)
async def get_signal_log(symbol: Optional[str] = None, source: Optional[str] = None, limit: int = 100):
    """
    Returns logged swing signals for the watchlist (BTC/ETH/SOL/BNB).
    Each row captures what fired, when, and whether it resolved as WIN/LOSS/REVIEW/OPEN.
    Filter by source='live' or source='backtest'.
    """
    from sqlalchemy import select as sa_select, desc
    from app.schemas.signal_log import SignalLog
    from app.storage import Database

    async with Database.get_session() as session:
        stmt = sa_select(SignalLog).order_by(desc(SignalLog.fired_at)).limit(limit)
        if symbol:
            sym_upper = symbol.upper() + "USDT" if not symbol.upper().endswith("USDT") else symbol.upper()
            stmt = stmt.where(SignalLog.symbol == sym_upper)
        if source:
            stmt = stmt.where(SignalLog.source == source)

        result = await session.execute(stmt)
        rows = result.scalars().all()

    items = [SignalLogItem(**row.__dict__) for row in rows]

    wins = sum(1 for r in items if r.outcome == "WIN")
    losses = sum(1 for r in items if r.outcome == "LOSS")
    closed = wins + losses
    summary = SignalLogSummary(
        total=len(items),
        open=sum(1 for r in items if r.outcome == "OPEN"),
        win=wins,
        loss=losses,
        review=sum(1 for r in items if r.outcome == "REVIEW"),
        win_rate=round(wins / closed * 100, 1) if closed > 0 else None,
    )

    return SignalLogResponse(
        data=items,
        summary=summary,
        last_updated=int(time.time() * 1000),
    )
