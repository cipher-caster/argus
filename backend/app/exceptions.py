"""
Custom exceptions for Argus backend

This module defines domain-specific exceptions for better error handling
and debugging throughout the application.
"""


class ArgusException(Exception):
    """Base exception for all Argus errors"""
    pass


class DataProviderError(ArgusException):
    """
    Raised when external data provider fails.
    
    Examples:
        - Binance API timeout
        - CoinGecko rate limit exceeded
        - Invalid response from exchange
    """
    pass


class CacheError(ArgusException):
    """
    Raised when Redis cache operation fails.
    
    Examples:
        - Redis connection refused
        - Cache key not found when expected
        - Serialization/deserialization errors
    """
    pass


class CalculationError(ArgusException):
    """
    Raised when indicator calculation fails.
    
    Examples:
        - Insufficient data for indicator
        - Invalid indicator parameters
        - Mathematical errors (division by zero, etc.)
    """
    pass


class ValidationError(ArgusException):
    """
    Raised when input validation fails.
    
    Examples:
        - Invalid symbol format
        - Invalid timeframe
        - Out of range parameters
    """
    pass
