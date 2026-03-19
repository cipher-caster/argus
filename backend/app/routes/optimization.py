"""
Optimization API routes — experiment log and trade analysis endpoints.
"""
import json
import logging
import time

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import select
from sqlalchemy import desc

from app.storage import Database, RedisClient
from app.schemas.optimization import OptimizationExperiment
from app.trading.analyzer import TradeAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/optimization", tags=["optimization"])
analysis_router = APIRouter(prefix="/api/trading", tags=["trading"])


# ---------------------------------------------------------------------------
# Experiment endpoints
# ---------------------------------------------------------------------------

@router.get("/experiments")
async def list_experiments(
    run_id: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """List experiments, optionally filtered by run_id, sorted by EV/trade desc."""
    async with Database.get_session() as session:
        stmt = select(OptimizationExperiment)
        if run_id:
            stmt = stmt.where(OptimizationExperiment.run_id == run_id)
        stmt = stmt.order_by(desc(OptimizationExperiment.ev_per_trade)).limit(limit)
        result = await session.execute(stmt)
        experiments = result.scalars().all()

    return [_exp_to_dict(e) for e in experiments]


@router.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: int):
    """Get a single experiment with full coin_results breakdown."""
    async with Database.get_session() as session:
        result = await session.execute(
            select(OptimizationExperiment).where(OptimizationExperiment.id == experiment_id)
        )
        exp = result.scalar_one_or_none()

    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    d = _exp_to_dict(exp)
    d["coin_results"] = json.loads(exp.coin_results or "{}")
    return d


@router.get("/best")
async def get_best_experiment(min_signals: int = Query(30, ge=1)):
    """Return the highest EV/trade experiment with at least min_signals."""
    async with Database.get_session() as session:
        result = await session.execute(
            select(OptimizationExperiment)
            .where(OptimizationExperiment.total_signals >= min_signals)
            .order_by(desc(OptimizationExperiment.ev_per_trade))
            .limit(1)
        )
        exp = result.scalar_one_or_none()

    if not exp:
        raise HTTPException(
            status_code=404,
            detail=f"No experiments with >= {min_signals} signals found"
        )

    d = _exp_to_dict(exp)
    d["coin_results"] = json.loads(exp.coin_results or "{}")
    return d


class ApplyRequest(BaseModel):
    experiment_id: int


@router.post("/apply")
async def apply_experiment(body: ApplyRequest):
    """
    Apply an experiment's config to Redis (signal_log:config + trading:config)
    and mark it as is_production=True.
    """
    async with Database.get_session() as session:
        result = await session.execute(
            select(OptimizationExperiment).where(OptimizationExperiment.id == body.experiment_id)
        )
        exp = result.scalar_one_or_none()

    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    r = RedisClient.get_instance()

    # Update signal_log:config
    sl_cfg_raw = await r.get("signal_log:config")
    sl_cfg = json.loads(sl_cfg_raw) if sl_cfg_raw else {}
    sl_cfg["min_titan_confidence"] = exp.min_titan_confidence
    sl_cfg["block_sleeping"] = exp.block_sleeping
    sl_cfg["block_volatile"] = exp.block_volatile
    sl_cfg["macro_guard"] = exp.macro_guard
    await r.set("signal_log:config", json.dumps(sl_cfg))

    # Update trading:config
    t_cfg_raw = await r.get("trading:config")
    t_cfg = json.loads(t_cfg_raw) if t_cfg_raw else {}
    t_cfg["min_conviction"] = exp.min_conviction
    await r.set("trading:config", json.dumps(t_cfg))

    # Mark production in DB
    async with Database.get_session() as session:
        prev = await session.execute(
            select(OptimizationExperiment).where(OptimizationExperiment.is_production == True)
        )
        for p in prev.scalars().all():
            p.is_production = False
            session.add(p)
        result2 = await session.execute(
            select(OptimizationExperiment).where(OptimizationExperiment.id == body.experiment_id)
        )
        exp2 = result2.scalar_one()
        exp2.is_production = True
        session.add(exp2)
        await session.commit()

    return {
        "status": "applied",
        "experiment_id": body.experiment_id,
        "name": exp.name,
        "signal_log_config_updated": {
            "min_titan_confidence": exp.min_titan_confidence,
            "block_sleeping": exp.block_sleeping,
            "macro_guard": exp.macro_guard,
        },
        "trading_config_updated": {
            "min_conviction": exp.min_conviction,
        },
    }


# ---------------------------------------------------------------------------
# Trade analysis endpoints (mounted under /api/trading)
# ---------------------------------------------------------------------------

@analysis_router.get("/analysis")
async def get_trade_analysis():
    """Analyze closed paper trading positions."""
    return await TradeAnalyzer.analyze_closed_trades()


@analysis_router.get("/analysis/recommendations")
async def get_recommendations():
    """Rule-based config recommendations from closed trade patterns."""
    return await TradeAnalyzer.recommend_config()


@analysis_router.get("/analysis/report")
async def get_analysis_report():
    """Full markdown report of trade analysis."""
    report = await TradeAnalyzer.generate_report()
    return {"report": report}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _exp_to_dict(e: OptimizationExperiment) -> dict:
    return {
        "id": e.id,
        "run_id": e.run_id,
        "name": e.name,
        "created_at": e.created_at,
        "symbols": e.symbols,
        "params": {
            "sl_mult": e.sl_mult,
            "tp_mult": e.tp_mult,
            "tp_adaptive": e.tp_adaptive,
            "min_titan_confidence": e.min_titan_confidence,
            "block_sleeping": e.block_sleeping,
            "block_volatile": e.block_volatile,
            "macro_guard": e.macro_guard,
            "strict_macro": e.strict_macro,
            "min_conviction": e.min_conviction,
        },
        "results": {
            "total_signals": e.total_signals,
            "wins": e.wins,
            "losses": e.losses,
            "reviews": e.reviews,
            "win_rate": e.win_rate,
            "total_r": e.total_r,
            "ev_per_trade": e.ev_per_trade,
            "avg_rr": e.avg_rr,
        },
        "notes": e.notes,
        "is_production": e.is_production,
    }
