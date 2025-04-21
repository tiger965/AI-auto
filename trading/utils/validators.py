""" "
Data validation utilities for trading system.

This module provides functions for validating data used in the trading system,
such as pair names, timeframes, and data formats.
"""

import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union, Any

import modules.nlp as np
import config.paths as pd


class ValidationException(Exception):
    """Exception raised for validation errors."""

    pass


def validate_pair(pair: str) -> bool:
    """
    Validate a trading pair name.

    Args:
        pair: Trading pair name (e.g., 'BTC/USDT').

    Returns:
        True if the pair is valid, False otherwise.
    """
    # Check for standard format BASE/QUOTE
    if not re.match(r"^[A-Z0-9]+/[A-Z0-9]+$", pair):
        return False

    base, quote = pair.split("/")

    # Base and quote must be different
    if base == quote:
        return False

    # Base and quote must be at least 2 characters
    if len(base) < 2 or len(quote) < 2:
        return False

    return True


def validate_pairs(pairs: List[str]) -> List[str]:
    """
    Validate a list of trading pairs and return only valid pairs.

    Args:
        pairs: List of trading pair names.

    Returns:
        List of valid trading pairs.
    """
    return [pair for pair in pairs if validate_pair(pair)]


def validate_timeframe(timeframe: str) -> bool:
    """
    Validate a timeframe string.

    Args:
        timeframe: Timeframe string (e.g., '1m', '5m', '1h', '1d').

    Returns:
        True if the timeframe is valid, False otherwise.
    """
    # Valid timeframe units: m (minute), h (hour), d (day), w (week), M (month)
    return bool(re.match(r"^[1-9][0-9]*[mhdwM]$", timeframe))


def validate_timestamp(timestamp: Union[int, float]) -> bool:
    """
    Validate a timestamp.

    Args:
        timestamp: Timestamp in seconds or milliseconds.

    Returns:
        True if the timestamp is valid, False otherwise.
    """
    # Determine if the timestamp is in seconds or milliseconds
    if timestamp > 1e10:  # Threshold to distinguish between seconds and milliseconds
        timestamp = timestamp / 1000.0

    # Check if timestamp is in a reasonable range
    try:
        dt = datetime.fromtimestamp(timestamp)
        # Timestamp should not be in the future or too far in the past
        return datetime(1970, 1, 1) <= dt <= datetime.now()
    except (ValueError, OverflowError):
        return False


def validate_numeric(
    value: Any, min_value: Optional[float] = None, max_value: Optional[float] = None
) -> bool:
    """
    Validate that a value is numeric and within a specified range.

    Args:
        value: Value to validate.
        min_value: Minimum allowed value (inclusive), or None for no minimum.
        max_value: Maximum allowed value (inclusive), or None for no maximum.

    Returns:
        True if the value is valid, False otherwise.
    """
    if not isinstance(value, (int, float)):
        return False

    if min_value is not None and value < min_value:
        return False

    if max_value is not None and value > max_value:
        return False

    return True


def validate_ohlcv_data(ohlcv_data: List[List[Any]]) -> bool:
    """
    Validate OHLCV data in Freqtrade format.

    Args:
        ohlcv_data: OHLCV data in Freqtrade format.

    Returns:
        True if the data is valid, False otherwise.
    """
    if not isinstance(ohlcv_data, list):
        return False

    for candle in ohlcv_data:
        # Each candle should have 6 elements: timestamp, open, high, low, close, volume
        if not isinstance(candle, list) or len(candle) != 6:
            return False

        timestamp, open_price, high, low, close, volume = candle

        # Timestamp should be a valid timestamp
        if not validate_timestamp(timestamp):
            return False

        # Prices should be numeric and positive
        for price in [open_price, high, low, close]:
            if not validate_numeric(price, min_value=0):
                return False

        # High should be >= open, close, and low
        if high < open_price or high < close or high < low:
            return False

        # Low should be <= open, close, and high
        if low > open_price or low > close or low > high:
            return False

        # Volume should be numeric and non-negative
        if not validate_numeric(volume, min_value=0):
            return False

    return True


def validate_trades_data(trades_data: List[Dict[str, Any]]) -> bool:
    """
    Validate trades data.

    Args:
        trades_data: List of trade dictionaries.

    Returns:
        True if the data is valid, False otherwise.
    """
    if not isinstance(trades_data, list):
        return False

    for trade in trades_data:
        # Each trade should be a dictionary
        if not isinstance(trade, dict):
            return False

        # Required fields
        required_fields = [
            "trade_id",
            "pair",
            "open_date_timestamp",
            "open_rate",
            "amount",
            "stake_amount",
        ]
        if not all(field in trade for field in required_fields):
            return False

        # Validate pair
        if not validate_pair(trade["pair"]):
            return False

        # Validate timestamps
        if not validate_timestamp(trade["open_date_timestamp"]):
            return False

        if (
            "close_date_timestamp" in trade
            and trade["close_date_timestamp"] is not None
        ):
            if not validate_timestamp(trade["close_date_timestamp"]):
                return False

            # Close date should be after open date
            if trade["close_date_timestamp"] <= trade["open_date_timestamp"]:
                return False

        # Validate prices and amounts
        numeric_fields = {
            "open_rate": 0,
            "close_rate": 0,
            "amount": 0,
            "stake_amount": 0,
            "fee_open": 0,
            "fee_close": 0,
        }

        for field, min_value in numeric_fields.items():
            if field in trade and trade[field] is not None:
                if not validate_numeric(trade[field], min_value=min_value):
                    return False

        # Validate profit ratio (if present)
        if "profit_ratio" in trade and trade["profit_ratio"] is not None:
            if not isinstance(trade["profit_ratio"], (int, float)):
                return False

    return True


def validate_strategy_parameters(
    parameters: Dict[str, Any], parameter_schema: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Validate strategy parameters against a schema.

    Args:
        parameters: Dictionary of parameter values.
        parameter_schema: Dictionary of parameter schemas.

    Returns:
        Dictionary of validated parameters.

    Raises:
        ValidationException: If any parameter is invalid.
    """
    validated_params = {}

    for param_name, param_schema in parameter_schema.items():
        # Check if the parameter is provided
        if param_name not in parameters:
            # Use default value if available, otherwise raise an error if required
            if "default" in param_schema:
                validated_params[param_name] = param_schema["default"]
            elif param_schema.get("required", False):
                raise ValidationException(
                    f"Missing required parameter: {param_name}")
            continue

        param_value = parameters[param_name]
        param_type = param_schema.get("type")

        # Validate parameter type
        if param_type == "int":
            if not isinstance(param_value, int):
                raise ValidationException(
                    f"Parameter {param_name} must be an integer")
        elif param_type == "float":
            if not isinstance(param_value, (int, float)):
                raise ValidationException(
                    f"Parameter {param_name} must be a number")
            param_value = float(param_value)
        elif param_type == "bool":
            if not isinstance(param_value, bool):
                raise ValidationException(
                    f"Parameter {param_name} must be a boolean")
        elif param_type == "string":
            if not isinstance(param_value, str):
                raise ValidationException(
                    f"Parameter {param_name} must be a string")
        elif param_type == "enum":
            if param_value not in param_schema.get("values", []):
                raise ValidationException(
                    f"Parameter {param_name} must be one of: {', '.join(param_schema.get('values', []))}"
                )

        # Validate parameter range
        if param_type in ["int", "float"]:
            if "min" in param_schema and param_value < param_schema["min"]:
                raise ValidationException(
                    f"Parameter {param_name} must be at least {param_schema['min']}"
                )
            if "max" in param_schema and param_value > param_schema["max"]:
                raise ValidationException(
                    f"Parameter {param_name} must be at most {param_schema['max']}"
                )

        # Validate string length
        if param_type == "string" and "max_length" in param_schema:
            if len(param_value) > param_schema["max_length"]:
                raise ValidationException(
                    f"Parameter {param_name} must be at most {param_schema['max_length']} characters long"
                )

        validated_params[param_name] = param_value

    return validated_params


def validate_backtesting_result(result: Dict[str, Any]) -> bool:
    """
    Validate a backtesting result.

    Args:
        result: Backtesting result dictionary.

    Returns:
        True if the result is valid, False otherwise.
    """
    # Required fields
    required_fields = [
        "strategy",
        "start_date",
        "end_date",
        "trades",
        "profit_ratio",
        "profit_abs",
    ]
    if not all(field in result for field in required_fields):
        return False

    # Validate strategy name
    if not isinstance(result["strategy"], str) or not result["strategy"]:
        return False

    # Validate dates
    for date_field in ["start_date", "end_date"]:
        if not validate_timestamp(result[date_field]):
            return False

    # End date should be after start date
    if result["end_date"] <= result["start_date"]:
        return False

    # Validate trades
    if not isinstance(result["trades"], list):
        return False

    # Validate profit metrics
    for profit_field in ["profit_ratio", "profit_abs"]:
        if not isinstance(result[profit_field], (int, float)):
            return False

    # Validate additional metrics if present
    additional_metrics = [
        "max_drawdown",
        "max_drawdown_abs",
        "sharpe_ratio",
        "sortino_ratio",
        "calmar_ratio",
        "winning_trades",
        "losing_trades",
    ]

    for metric in additional_metrics:
        if metric in result and not isinstance(result[metric], (int, float)):
            return False

    return True


# Export public components
__all__ = [
    "ValidationException",
    "validate_pair",
    "validate_pairs",
    "validate_timeframe",
    "validate_timestamp",
    "validate_numeric",
    "validate_ohlcv_data",
    "validate_trades_data",
    "validate_strategy_parameters",
    "validate_backtesting_result",
]