"""
Routes Package
"""

from .market import router as market_router
from .indicators import router as indicators_router
from .strategy import router as strategy_router

__all__ = ['market_router', 'indicators_router', 'strategy_router']
