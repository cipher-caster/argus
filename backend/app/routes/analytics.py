"""
Futures analytics API routes
Uses CCXT-based OKXProvider for data fetching
Redis caching for performance optimization
"""
import logging
import time
import pandas as pd
import asyncio
from fastapi import APIRouter, HTTPException, Query
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
from app.providers import get_provider, owns_provider
from app.services.market_data import MarketDataService
from app.storage import RedisClient
from app.exceptions import DataProviderError, CacheError, CalculationError
from app.utils.trading_utils import calculate_conviction

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

_FETCH_SEMAPHORE = asyncio.Semaphore(10)  # max 10 concurrent provider calls

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
    provider = get_provider()
    # owns_provider() is True when we created a fresh instance (worker / test context)
    # and False when get_provider() returned the shared singleton (backend API context).
    # Only close the provider if we own it — never close the app-lifetime singleton.
    _should_close = owns_provider(provider)

    try:
        async def _fetch_one(sym):
            async with _FETCH_SEMAPHORE:
                return await get_candles_df(sym, timeframe, limit, provider=provider)

        tasks = [_fetch_one(sym) for sym in symbols]
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
        if _should_close:
            await provider.close()


@router.get("/screener", response_model=ScreenerResponse)
async def get_oracle_screener(limit: int = 50, timeframe: str = Query(default="1h", pattern="^(1m|5m|15m|30m|1h|4h|12h|1d|3d|1w)$")):
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
async def get_contrarian_radar(limit: int = 50, timeframe: str = Query(default="1h", pattern="^(1m|5m|15m|30m|1h|4h|12h|1d|3d|1w)$")):
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
async def get_best_setups(timeframe: str = Query(default="4h", pattern="^(1m|5m|15m|30m|1h|4h|12h|1d|3d|1w)$"), limit: int = 50):
    """
    High-conviction Titan setups filtered by market regime.
    In BULL regime: prioritizes LONG signals.
    In BEAR regime: prioritizes SHORT signals.
    Returns max 10 results sorted by conviction score (0-100).
    """
    cache_key = f"analytics:best-setups:{timeframe}:{limit}"
    cached = await RedisClient.get_json(cache_key)
    if cached:
        return BestSetupsResponse(**cached)

    symbols = await MarketDataService.get_top_symbols(limit=limit)

    # Fetch Titan candles (primary timeframe)
    titan_candles = await fetch_all_candles(symbols, timeframe=timeframe, limit=300)

    # Detect regime from BTC weekly EMA50 (cached to avoid recomputing on every call)
    from app.trading.backtest_engine import load_candles
    import pandas_ta as _ta
    REGIME_CACHE_KEY = "market:regime"
    REGIME_CACHE_TTL = 3600  # 1 hour

    regime = "UNKNOWN"
    cached_regime = await RedisClient.get_json(REGIME_CACHE_KEY)
    if cached_regime:
        regime = cached_regime.get("regime", "UNKNOWN")
    else:
        try:
            btc_weekly = await load_candles("BTC/USDT", "1w")
            if not btc_weekly.empty and len(btc_weekly) > 50:
                btc_weekly["ema50"] = _ta.ema(btc_weekly["close"], length=50)
                last = btc_weekly.iloc[-1]
                if not pd.isna(last.get("ema50")):
                    regime = "BULL" if float(last["close"]) > float(last["ema50"]) else "BEAR"
            await RedisClient.set_json(REGIME_CACHE_KEY, {"regime": regime}, ttl=REGIME_CACHE_TTL)
        except Exception as e:
            logger.warning(f"Regime detection failed, defaulting to UNKNOWN: {e}")

    results = []
    for sym, df in titan_candles.items():
        try:
            t = titan.analyze(df, symbol=sym)
            if "error" in t:
                continue

            t_signal = t["signal"]
            t_confidence = t["confidence"]

            is_long = t_signal in ("BUY", "BUY_LIMIT", "STRONG_BUY")
            is_short = t_signal in ("SELL", "SELL_LIMIT", "STRONG_SELL")
            if not (is_long or is_short) or t_confidence < 55:
                continue

            # Regime alignment boosts conviction (counter-regime signals still shown in UI)
            regime_aligned = (regime == "BULL" and is_long) or (regime == "BEAR" and is_short)

            # Conviction: base from Titan confidence, bonus for regime alignment
            conviction = calculate_conviction(
                confidence=t_confidence,
                regime_aligned=regime_aligned,
                is_market_signal=t_signal in ("BUY", "SELL", "STRONG_BUY", "STRONG_SELL"),
            )

            targets = t.get("targets", {})
            price = float(df.iloc[-1]["close"])
            reasons = t.get("reasons", [])
            # Short regime tag for UI badges + indicator reasons
            reg_tag = "trend" if regime_aligned else "counter"
            reason = f"({reg_tag}) " + " | ".join(reasons[:2]) if reasons else f"({reg_tag}) {t_signal.replace('_', ' ')}"

            results.append(BestSetupItem(
                symbol=sym,
                direction="LONG" if is_long else "SHORT",
                conviction=conviction,
                entry=round(float(targets.get("entry", price)), 6),
                tp=round(float(targets.get("tp", 0)), 6),
                sl=round(float(targets.get("sl", 0)), 6),
                reason=reason,
                oracle_score=0,
                titan_signal=t_signal,
            ))
        except Exception as e:
            logger.warning(f"best-setups error for {sym}: {e}")
            continue

    results.sort(key=lambda x: x.conviction, reverse=True)
    results = results[:10]

    # Enrich filtered results (≤10 coins) with MTF confluence and backtest stats
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
                        t = titan.analyze(df, symbol=item.symbol)
                        sig = t.get("signal", "")
                        tf_confirmation[tf] = (
                            sig in ("BUY", "BUY_LIMIT", "STRONG_BUY") if is_long
                            else sig in ("SELL", "SELL_LIMIT", "STRONG_SELL")
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
async def get_titan_radar(limit: int = 50, timeframe: str = Query(default="4h", pattern="^(1m|5m|15m|30m|1h|4h|12h|1d|3d|1w)$")):
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
            analysis = titan.analyze(df, symbol=sym)
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


@router.get("/signal-log/stats")
async def get_signal_log_stats(source: str = "backtest", provider: Optional[str] = None, include_legacy: bool = False):
    """
    Return per-coin aggregated performance stats from signal log.
    Used by the Backtest Performance dashboard.
    Filter by provider='binance' or 'okx' when provided.
    Set include_legacy=true to include v1 methodology signals.
    """
    from sqlalchemy import select as sa_select, func, case
    from app.schemas.signal_log import SignalLog
    from app.storage import Database

    async with Database.get_session() as session:
        stmt = sa_select(SignalLog).where(SignalLog.source == source)
        if provider is not None:
            stmt = stmt.where(SignalLog.provider == provider)
        if not include_legacy:
            stmt = stmt.where(SignalLog.methodology_version != "v1")
        result = await session.execute(stmt)
        rows = result.scalars().all()

    if not rows:
        return {"coins": [], "overall": None}

    # Aggregate per coin
    from collections import defaultdict
    by_coin = defaultdict(list)
    for r in rows:
        by_coin[r.symbol].append(r)

    coins = []
    all_signals = []
    for symbol, sigs in sorted(by_coin.items()):
        all_signals.extend(sigs)
        wins = sum(1 for s in sigs if s.outcome == "WIN")
        losses = sum(1 for s in sigs if s.outcome == "LOSS")
        reviews = sum(1 for s in sigs if s.outcome == "REVIEW")
        closed = wins + losses
        wr = round(wins / closed * 100, 1) if closed > 0 else None

        longs = [s for s in sigs if s.direction == "LONG"]
        shorts = [s for s in sigs if s.direction == "SHORT"]
        long_wins = sum(1 for s in longs if s.outcome == "WIN")
        long_closed = sum(1 for s in longs if s.outcome in ("WIN", "LOSS"))
        short_wins = sum(1 for s in shorts if s.outcome == "WIN")
        short_closed = sum(1 for s in shorts if s.outcome in ("WIN", "LOSS"))

        # R profit
        total_r = 0.0
        for s in sigs:
            if s.outcome == "WIN":
                risk = abs(s.entry - s.sl)
                reward = abs(s.tp - s.entry)
                total_r += reward / risk if risk > 0 else 0
            elif s.outcome == "LOSS":
                total_r -= 1.0

        coins.append({
            "symbol": symbol,
            "base": symbol.replace("USDT", ""),
            "total": len(sigs),
            "wins": wins,
            "losses": losses,
            "reviews": reviews,
            "win_rate": wr,
            "profit_r": round(total_r, 1),
            "longs": len(longs),
            "shorts": len(shorts),
            "long_wr": round(long_wins / long_closed * 100, 1) if long_closed > 0 else None,
            "short_wr": round(short_wins / short_closed * 100, 1) if short_closed > 0 else None,
            "avg_conviction": round(sum(s.conviction for s in sigs) / len(sigs)) if sigs else 0,
        })

    # Overall stats
    total_wins = sum(c["wins"] for c in coins)
    total_losses = sum(c["losses"] for c in coins)
    total_closed = total_wins + total_losses
    overall = {
        "total_signals": len(all_signals),
        "total_coins": len(coins),
        "win_rate": round(total_wins / total_closed * 100, 1) if total_closed > 0 else None,
        "profit_r": round(sum(c["profit_r"] for c in coins), 1),
    }

    return {"coins": coins, "overall": overall}


SIGNAL_LOG_CONFIG_KEY = "signal_log:config"
SIGNAL_LOG_DEFAULTS = {
    "watchlist": [
        "BTCUSDT", "ETHUSDT", "BNBUSDT",
        "TRXUSDT", "XRPUSDT", "FETUSDT", "NEARUSDT",
        "ARBUSDT", "ATOMUSDT", "DOGEUSDT",
    ],
    "min_titan_confidence": 55,
    "review_days": 7,
    "block_sleeping": True,
    "block_volatile": True,
    "macro_guard": True,
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


@router.get("/signal-log/scan-status")
async def get_signal_log_scan_status():
    """Return the result of the last log_watchlist_setups scan (cached in Redis)."""
    data = await RedisClient.get_json("signal:scan:last")
    if not data:
        return {"available": False}
    return {"available": True, **data}


@router.get("/signal-log", response_model=SignalLogResponse)
async def get_signal_log(symbol: Optional[str] = None, source: Optional[str] = None, provider: Optional[str] = None, limit: int = 50, offset: int = 0, include_legacy: bool = False):
    """
    Returns logged swing signals for the watchlist (BTC/ETH/SOL/BNB).
    Each row captures what fired, when, and whether it resolved as WIN/LOSS/REVIEW/OPEN.
    Filter by source='live' or source='backtest'. Filter by provider='binance' or 'okx'.
    Set include_legacy=true to include v1 methodology signals (may have lookahead bias).
    """
    from sqlalchemy import select as sa_select, desc, func as sa_func, case as sa_case
    from app.schemas.signal_log import SignalLog
    from app.storage import Database

    async with Database.get_session() as session:
        # Base query with filters
        base_where = []
        if symbol:
            sym_upper = symbol.upper() + "USDT" if not symbol.upper().endswith("USDT") else symbol.upper()
            base_where.append(SignalLog.symbol == sym_upper)
        if source:
            base_where.append(SignalLog.source == source)
        else:
            base_where.append(SignalLog.source != "backtest")
        if provider:
            base_where.append(SignalLog.provider == provider)
        if not include_legacy:
            base_where.append(SignalLog.methodology_version != "v1")

        # Total count
        count_stmt = sa_select(sa_func.count()).select_from(SignalLog)
        for w in base_where:
            count_stmt = count_stmt.where(w)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # Summary stats (full dataset, not paginated)
        summary_stmt = sa_select(
            sa_func.count().label("total"),
            sa_func.sum(sa_case((SignalLog.outcome == "WIN", 1), else_=0)).label("wins"),
            sa_func.sum(sa_case((SignalLog.outcome == "LOSS", 1), else_=0)).label("losses"),
            sa_func.sum(sa_case((SignalLog.outcome == "OPEN", 1), else_=0)).label("opens"),
            sa_func.sum(sa_case((SignalLog.outcome == "REVIEW", 1), else_=0)).label("reviews"),
            sa_func.sum(sa_case((SignalLog.outcome == "REJECTED", 1), else_=0)).label("rejected"),
        ).select_from(SignalLog)
        for w in base_where:
            summary_stmt = summary_stmt.where(w)
        summary_result = await session.execute(summary_stmt)
        stats = summary_result.one()

        wins = int(stats.wins or 0)
        losses = int(stats.losses or 0)
        closed = wins + losses

        # Paginated data
        stmt = sa_select(SignalLog).order_by(desc(SignalLog.fired_at)).limit(limit).offset(offset)
        for w in base_where:
            stmt = stmt.where(w)
        result = await session.execute(stmt)
        rows = result.scalars().all()

    items = [SignalLogItem(**row.__dict__) for row in rows]

    summary = SignalLogSummary(
        total=total,
        open=int(stats.opens or 0),
        win=wins,
        loss=losses,
        review=int(stats.reviews or 0),
        rejected=int(stats.rejected or 0),
        win_rate=round(wins / closed * 100, 1) if closed > 0 else None,
    )

    return SignalLogResponse(
        data=items,
        summary=summary,
        total=total,
        last_updated=int(time.time() * 1000),
    )


@router.get("/provider-comparison")
async def get_provider_comparison():
    """
    Side-by-side win rate comparison for Binance vs OKX signals.
    Only resolved signals (WIN/LOSS) are included in rate calculations.
    Top 5 coins per provider ranked by win rate (min 3 signals).
    """
    from sqlalchemy import select as sa_select
    from app.schemas.signal_log import SignalLog
    from app.storage import Database
    from collections import defaultdict

    async with Database.get_session() as session:
        result = await session.execute(
            sa_select(SignalLog).where(SignalLog.outcome.in_(["WIN", "LOSS"]))
        )
        rows = result.scalars().all()

    if not rows:
        return {}

    by_provider: dict[str, list] = defaultdict(list)
    for row in rows:
        by_provider[row.provider].append(row)

    def _build_provider_stats(signals: list) -> dict:
        wins = sum(1 for s in signals if s.outcome == "WIN")
        losses = len(signals) - wins
        total = len(signals)
        win_rate = round(wins / total, 4) if total > 0 else 0.0

        r_profits: list[float] = []
        for s in signals:
            if s.outcome == "WIN":
                risk = abs(s.entry - s.sl)
                reward = abs(s.tp - s.entry)
                r_profits.append(reward / risk if risk > 0 else 0.0)
            else:
                r_profits.append(-1.0)
        avg_r = round(sum(r_profits) / len(r_profits), 4) if r_profits else 0.0

        by_coin: dict[str, list] = defaultdict(list)
        for s in signals:
            by_coin[s.symbol].append(s)

        top_coins = []
        for symbol, coin_sigs in by_coin.items():
            if len(coin_sigs) < 3:
                continue
            c_wins = sum(1 for s in coin_sigs if s.outcome == "WIN")
            c_total = len(coin_sigs)
            top_coins.append({
                "symbol": symbol,
                "win_rate": round(c_wins / c_total, 4),
                "total": c_total,
            })
        top_coins.sort(key=lambda x: x["win_rate"], reverse=True)
        top_coins = top_coins[:5]

        return {
            "win_rate": win_rate,
            "total": total,
            "wins": wins,
            "losses": losses,
            "avg_r_profit": avg_r,
            "top_coins": top_coins,
        }

    return {
        provider: _build_provider_stats(signals)
        for provider, signals in by_provider.items()
    }


@router.get("/signal-outcomes")
async def get_signal_outcomes():
    """
    Signal→Position analytics: join signal_log with positions to show
    which signals were traded and their actual PnL.

    Returns:
        - per-symbol breakdown of signal wins vs position PnL
        - rejection analysis (why signals were rejected)
        - regime correlation (did regime changes affect outcomes?)
    """
    from sqlalchemy import select as sa_select, desc, func
    from app.schemas.signal_log import SignalLog
    from app.schemas.trading import Position
    from app.storage import Database

    async with Database.get_session() as session:
        # All resolved signals
        signals_result = await session.execute(
            sa_select(SignalLog).where(SignalLog.outcome.in_(["WIN", "LOSS", "REVIEW"]))
            .order_by(desc(SignalLog.fired_at))
        )
        signals = signals_result.scalars().all()

        # All rejected signals
        rejected_result = await session.execute(
            sa_select(SignalLog).where(SignalLog.outcome == "REJECTED")
        )
        rejected = rejected_result.scalars().all()

        # All closed positions with their signal_log_id
        positions_result = await session.execute(
            sa_select(Position).where(Position.status == "CLOSED")
        )
        positions = positions_result.scalars().all()

    # Index positions by signal_log_id
    pos_by_signal = {p.signal_log_id: p for p in positions if p.signal_log_id}

    # Per-signal outcome analysis
    signal_outcomes = []
    for sig in signals:
        pos = pos_by_signal.get(sig.id)
        signal_outcomes.append({
            "symbol": sig.symbol,
            "direction": sig.direction,
            "signal_outcome": sig.outcome,
            "conviction": sig.conviction,
            "market_state": sig.market_state,
            "regime_at_resolution": sig.regime_at_resolution,
            "time_to_resolution_ms": sig.time_to_resolution_ms,
            "fired_at": sig.fired_at,
            # Position info (if traded)
            "was_traded": pos is not None,
            "pnl_usd": pos.pnl_usd if pos else None,
            "pnl_pct": pos.pnl_pct if pos else None,
            "position_outcome": pos.outcome if pos else None,
            "quote_amount": pos.quote_amount if pos else None,
        })

    # Rejection analysis
    rejection_counts = {}
    for sig in rejected:
        reason = sig.rejection_reason or "unknown"
        rejection_counts[reason] = rejection_counts.get(reason, 0) + 1

    # Regime correlation
    regime_wins = {}
    regime_total = {}
    for sig in signals:
        regime = sig.regime_at_resolution or sig.market_state
        if regime:
            regime_total[regime] = regime_total.get(regime, 0) + 1
            if sig.outcome == "WIN":
                regime_wins[regime] = regime_wins.get(regime, 0) + 1

    regime_stats = {
        regime: {
            "total": total,
            "wins": regime_wins.get(regime, 0),
            "win_rate": round(regime_wins.get(regime, 0) / total * 100, 1) if total > 0 else None,
        }
        for regime, total in regime_total.items()
    }

    # Conviction band analysis
    conviction_bands = {"60-69": [], "70-79": [], "80-89": [], "90-100": []}
    for sig in signals:
        if sig.conviction >= 90:
            conviction_bands["90-100"].append(sig)
        elif sig.conviction >= 80:
            conviction_bands["80-89"].append(sig)
        elif sig.conviction >= 70:
            conviction_bands["70-79"].append(sig)
        elif sig.conviction >= 60:
            conviction_bands["60-69"].append(sig)

    conviction_stats = {}
    for band, sigs in conviction_bands.items():
        wins = sum(1 for s in sigs if s.outcome == "WIN")
        total = len(sigs)
        conviction_stats[band] = {
            "total": total,
            "wins": wins,
            "win_rate": round(wins / total * 100, 1) if total > 0 else None,
        }

    return {
        "signal_outcomes": signal_outcomes,
        "rejection_analysis": {
            "total_rejected": len(rejected),
            "by_reason": rejection_counts,
        },
        "regime_correlation": regime_stats,
        "conviction_analysis": conviction_stats,
    }


