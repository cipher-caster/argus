"""
Unit tests for custom exception handling

This module tests that custom exceptions are raised correctly and contain
appropriate error messages for debugging.
"""

from app.exceptions import (
    ArgusException,
    CacheError,
    CalculationError,
    DataProviderError,
    ValidationError,
)


class TestCustomExceptions:
    """Test suite for custom exception hierarchy"""

    def test_argus_exception_is_base_exception(self):
        """ArgusException should inherit from Exception"""
        error = ArgusException("Base error")
        assert isinstance(error, Exception)
        assert str(error) == "Base error"

    def test_data_provider_error_message(self):
        """Should create DataProviderError with message"""
        error = DataProviderError("API timeout after 30s")
        assert str(error) == "API timeout after 30s"
        assert isinstance(error, ArgusException)
        assert isinstance(error, Exception)

    def test_cache_error_inheritance(self):
        """Should inherit from ArgusException"""
        error = CacheError("Redis connection refused")
        assert isinstance(error, ArgusException)
        assert isinstance(error, Exception)
        assert str(error) == "Redis connection refused"

    def test_calculation_error_for_indicators(self):
        """Should create CalculationError for indicator failures"""
        error = CalculationError("Insufficient data for RSI calculation")
        assert isinstance(error, ArgusException)
        assert "Insufficient data" in str(error)

    def test_validation_error_for_inputs(self):
        """Should create ValidationError for invalid inputs"""
        error = ValidationError("Invalid timeframe: 2h")
        assert isinstance(error, ArgusException)
        assert "Invalid timeframe" in str(error)

    def test_exceptions_can_be_caught_by_base_class(self):
        """All custom exceptions should be catchable by ArgusException"""
        exceptions = [
            DataProviderError("test"),
            CacheError("test"),
            CalculationError("test"),
            ValidationError("test"),
        ]

        for exc in exceptions:
            try:
                raise exc
            except ArgusException as e:
                assert str(e) == "test"

    def test_exception_with_nested_cause(self):
        """Custom exceptions should preserve exception chaining"""
        original_error = ValueError("Original cause")

        try:
            try:
                raise original_error
            except ValueError as e:
                raise DataProviderError("API failed") from e
        except DataProviderError as caught:
            assert str(caught) == "API failed"
            assert caught.__cause__ == original_error


class TestExceptionUsagePatterns:
    """Test common exception raising patterns"""

    def test_data_provider_error_scenarios(self):
        """Common scenarios that should raise DataProviderError"""
        scenarios = [
            "Binance API timeout",
            "CoinGecko rate limit exceeded: 429",
            "Invalid response from exchange: malformed JSON",
        ]

        for scenario in scenarios:
            error = DataProviderError(scenario)
            assert isinstance(error, DataProviderError)
            assert len(str(error)) > 0

    def test_cache_error_scenarios(self):
        """Common scenarios that should raise CacheError"""
        scenarios = [
            "Redis connection refused on localhost:6379",
            "Cache key 'market:tickers' not found",
            "JSON deserialization failed for cached data",
        ]

        for scenario in scenarios:
            error = CacheError(scenario)
            assert isinstance(error, CacheError)

    def test_calculation_error_scenarios(self):
        """Common scenarios that should raise CalculationError"""
        scenarios = [
            "Insufficient data: need 14 rows for RSI, got 5",
            "Invalid indicator parameter: period must be > 0",
            "Mathematical error: division by zero in volatility calc",
        ]

        for scenario in scenarios:
            error = CalculationError(scenario)
            assert isinstance(error, CalculationError)

    def test_validation_error_scenarios(self):
        """Common scenarios that should raise ValidationError"""
        scenarios = [
            "Invalid symbol format: must be 'BASE/QUOTE'",
            "Invalid timeframe: '2h' not in allowed values",
            "Limit parameter out of range: must be between 1 and 1000",
        ]

        for scenario in scenarios:
            error = ValidationError(scenario)
            assert isinstance(error, ValidationError)
