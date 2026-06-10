"""
Optimization API routes — experiment log and trade analysis endpoints.
"""

import json
import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc
from sqlmodel import select

from app.schemas.optimization import OptimizationExperiment
from app.storage import Database, RedisClient
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
    try:
        async with Database.get_session() as session:
            stmt = select(OptimizationExperiment)
            if run_id:
                stmt = stmt.where(OptimizationExperiment.run_id == run_id)
            stmt = stmt.order_by(desc(OptimizationExperiment.ev_per_trade)).limit(limit)
            result = await session.execute(stmt)
            experiments = result.scalars().all()
    except Exception as exc:
        logger.error("list_experiments: DB query failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve experiments")

    return [_exp_to_dict(e) for e in experiments]


@router.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: int):
    """Get a single experiment with full coin_results breakdown."""
    try:
        async with Database.get_session() as session:
            result = await session.execute(
                select(OptimizationExperiment).where(OptimizationExperiment.id == experiment_id)
            )
            exp = result.scalar_one_or_none()
    except Exception as exc:
        logger.error(
            "get_experiment: DB query failed for id=%s: %s", experiment_id, exc, exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve experiment")

    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    d = _exp_to_dict(exp)
    d["coin_results"] = json.loads(exp.coin_results or "{}")
    return d


@router.get("/best")
async def get_best_experiment(min_signals: int = Query(30, ge=1)):
    """Return the highest EV/trade experiment with at least min_signals."""
    try:
        async with Database.get_session() as session:
            result = await session.execute(
                select(OptimizationExperiment)
                .where(OptimizationExperiment.total_signals >= min_signals)
                .order_by(desc(OptimizationExperiment.ev_per_trade))
                .limit(1)
            )
            exp = result.scalar_one_or_none()
    except Exception as exc:
        logger.error("get_best_experiment: DB query failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve best experiment")

    if not exp:
        raise HTTPException(
            status_code=404, detail=f"No experiments with >= {min_signals} signals found"
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
        try:
            result = await session.execute(
                select(OptimizationExperiment).where(
                    OptimizationExperiment.id == body.experiment_id
                )
            )
            exp = result.scalar_one_or_none()
        except Exception as exc:
            logger.error("apply_experiment: DB lookup failed: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=500, detail="Failed to apply experiment — no changes were committed"
            )

    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    r = RedisClient.get_instance()

    # Snapshot existing Redis values so we can roll back on failure
    sl_cfg_raw_original = None
    t_cfg_raw_original = None

    try:
        # Snapshot originals for potential rollback
        sl_cfg_raw_original = await r.get("signal_log:config")
        t_cfg_raw_original = await r.get("trading:config")

        # Update signal_log:config
        sl_cfg = json.loads(sl_cfg_raw_original) if sl_cfg_raw_original else {}
        sl_cfg["min_titan_confidence"] = exp.min_titan_confidence
        sl_cfg["block_sleeping"] = exp.block_sleeping
        sl_cfg["block_volatile"] = exp.block_volatile
        sl_cfg["macro_guard"] = exp.macro_guard
        sl_cfg["sl_mult"] = exp.sl_mult
        sl_cfg["tp_mult"] = exp.tp_mult
        sl_cfg["tp_adaptive"] = exp.tp_adaptive
        await r.set("signal_log:config", json.dumps(sl_cfg))

        # Update trading:config
        t_cfg = json.loads(t_cfg_raw_original) if t_cfg_raw_original else {}
        t_cfg["min_conviction"] = exp.min_conviction
        await r.set("trading:config", json.dumps(t_cfg))

        # Mark production in DB (SQLAlchemy session rolls back automatically on exception)
        async with Database.get_session() as session:
            prev = await session.execute(
                select(OptimizationExperiment).where(OptimizationExperiment.is_production == True)
            )
            for p in prev.scalars().all():
                p.is_production = False
                session.add(p)
            result2 = await session.execute(
                select(OptimizationExperiment).where(
                    OptimizationExperiment.id == body.experiment_id
                )
            )
            exp2 = result2.scalar_one()
            exp2.is_production = True
            session.add(exp2)
            await session.commit()

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "apply_experiment: operation failed for experiment_id=%s, attempting Redis rollback: %s",
            body.experiment_id,
            exc,
            exc_info=True,
        )
        # Attempt to restore original Redis values
        try:
            if sl_cfg_raw_original is not None:
                await r.set("signal_log:config", sl_cfg_raw_original)
            if t_cfg_raw_original is not None:
                await r.set("trading:config", t_cfg_raw_original)
        except Exception as rollback_exc:
            logger.error(
                "apply_experiment: Redis rollback also failed: %s", rollback_exc, exc_info=True
            )
        raise HTTPException(
            status_code=500, detail="Failed to apply experiment — no changes were committed"
        )

    return {
        "status": "applied",
        "experiment_id": body.experiment_id,
        "name": exp.name,
        "signal_log_config_updated": {
            "min_titan_confidence": exp.min_titan_confidence,
            "block_sleeping": exp.block_sleeping,
            "macro_guard": exp.macro_guard,
            "sl_mult": exp.sl_mult,
            "tp_mult": exp.tp_mult,
            "tp_adaptive": exp.tp_adaptive,
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
