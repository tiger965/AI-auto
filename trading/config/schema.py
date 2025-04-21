""" "
Configuration validation schema for trading system.

This module provides validation functionality for the trading system configuration,
ensuring that the configuration is valid before it is used.
"""

from typing import Dict, Any, List, Optional, Union
import json
import logging
from pathlib import Path

# Create a logger
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised for configuration validation errors."""

    pass


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate trading system configuration.

    Args:
        config: Configuration dictionary to validate.

    Raises:
        ValidationError: If the configuration is invalid.
    """
    # Check required top-level sections
    required_sections = ["exchange", "trading", "strategy"]
    for section in required_sections:
        if section not in config:
            raise ValidationError(
                f"Missing required configuration section: {section}")

    # Validate exchange section
    _validate_exchange_section(config["exchange"])

    # Validate trading section
    _validate_trading_section(config["trading"])

    # Validate strategy section
    _validate_strategy_section(config["strategy"])

    # Validate optional sections if present
    if "backtesting" in config:
        _validate_backtesting_section(config["backtesting"])

    if "optimization" in config:
        _validate_optimization_section(config["optimization"])

    if "gpt_claude" in config:
        _validate_gpt_claude_section(config["gpt_claude"])

    if "ui" in config:
        _validate_ui_section(config["ui"])

    if "data" in config:
        _validate_data_section(config["data"])

    logger.debug("Configuration validation passed.")


def _validate_exchange_section(exchange_config: Dict[str, Any]) -> None:
    """
    Validate exchange section of the configuration.

    Args:
        exchange_config: Exchange configuration to validate.

    Raises:
        ValidationError: If the exchange configuration is invalid.
    """
    required_fields = ["name"]
    for field in required_fields:
        if field not in exchange_config:
            raise ValidationError(
                f"Missing required field in exchange configuration: {field}"
            )

    # Validate exchange name
    supported_exchanges = [
        "binance",
        "binanceus",
        "bittrex",
        "kucoin",
        "ftx",
        "kraken",
        "bitstamp",
        "coinbase",
        "huobi",
        "okex",
        "bitfinex",
    ]
    if exchange_config["name"] not in supported_exchanges:
        raise ValidationError(
            f"Unsupported exchange: {exchange_config['name']}. "
            f"Supported exchanges: {', '.join(supported_exchanges)}"
        )

    # If API key is provided, secret must also be provided and vice versa
    if "key" in exchange_config and exchange_config["key"]:
        if "secret" not in exchange_config or not exchange_config["secret"]:
            raise ValidationError(
                "Exchange API secret must be provided when API key is provided"
            )

    if "secret" in exchange_config and exchange_config["secret"]:
        if "key" not in exchange_config or not exchange_config["key"]:
            raise ValidationError(
                "Exchange API key must be provided when API secret is provided"
            )


def _validate_trading_section(trading_config: Dict[str, Any]) -> None:
    """
    Validate trading section of the configuration.

    Args:
        trading_config: Trading configuration to validate.

    Raises:
        ValidationError: If the trading configuration is invalid.
    """
    required_fields = ["stake_currency",
                       "stake_amount", "max_open_trades", "stoploss"]
    for field in required_fields:
        if field not in trading_config:
            raise ValidationError(
                f"Missing required field in trading configuration: {field}"
            )

    # Validate stake amount
    if (
        not isinstance(trading_config["stake_amount"], (int, float))
        or trading_config["stake_amount"] <= 0
    ):
        raise ValidationError("Stake amount must be a positive number")

    # Validate max_open_trades
    if (
        not isinstance(trading_config["max_open_trades"], int)
        or trading_config["max_open_trades"] < 0
    ):
        raise ValidationError("Max open trades must be a non-negative integer")

    # Validate stoploss
    if (
        not isinstance(trading_config["stoploss"], (int, float))
        or trading_config["stoploss"] > 0
    ):
        raise ValidationError("Stoploss must be a negative number")

    # Validate minimal_roi if present
    if "minimal_roi" in trading_config:
        if not isinstance(trading_config["minimal_roi"], dict):
            raise ValidationError("Minimal ROI must be a dictionary")

        for time_key, roi_value in trading_config["minimal_roi"].items():
            try:
                time_int = int(time_key)
                if time_int < 0:
                    raise ValidationError(
                        "Minimal ROI time values must be non-negative integers"
                    )
            except ValueError:
                raise ValidationError(
                    "Minimal ROI time values must be convertible to integers"
                )

            if not isinstance(roi_value, (int, float)):
                raise ValidationError("Minimal ROI values must be numbers")

    # Validate trailing stop parameters if trailing_stop is enabled
    if "trailing_stop" in trading_config and trading_config["trailing_stop"]:
        if "trailing_stop_positive" not in trading_config or not isinstance(
            trading_config["trailing_stop_positive"], (int, float)
        ):
            raise ValidationError(
                "Trailing stop positive must be a number when trailing stop is enabled"
            )

        if trading_config["trailing_stop_positive"] <= 0:
            raise ValidationError(
                "Trailing stop positive must be greater than zero")

        if "trailing_stop_positive_offset" not in trading_config or not isinstance(
            trading_config["trailing_stop_positive_offset"], (int, float)
        ):
            raise ValidationError(
                "Trailing stop positive offset must be a number when trailing stop is enabled"
            )

        if (
            trading_config["trailing_stop_positive_offset"]
            <= trading_config["trailing_stop_positive"]
        ):
            raise ValidationError(
                "Trailing stop positive offset must be greater than trailing stop positive"
            )


def _validate_strategy_section(strategy_config: Dict[str, Any]) -> None:
    """
    Validate strategy section of the configuration.

    Args:
        strategy_config: Strategy configuration to validate.

    Raises:
        ValidationError: If the strategy configuration is invalid.
    """
    if "name" not in strategy_config:
        raise ValidationError("Strategy name is required")

    if not isinstance(strategy_config["name"], str) or not strategy_config["name"]:
        raise ValidationError("Strategy name must be a non-empty string")

    if "parameters" in strategy_config and not isinstance(
        strategy_config["parameters"], dict
    ):
        raise ValidationError("Strategy parameters must be a dictionary")


def _validate_backtesting_section(backtesting_config: Dict[str, Any]) -> None:
    """
    Validate backtesting section of the configuration.

    Args:
        backtesting_config: Backtesting configuration to validate.

    Raises:
        ValidationError: If the backtesting configuration is invalid.
    """
    if "timeframe" in backtesting_config:
        _validate_timeframe(backtesting_config["timeframe"])

    if "days" in backtesting_config:
        if (
            not isinstance(backtesting_config["days"], int)
            or backtesting_config["days"] <= 0
        ):
            raise ValidationError(
                "Backtesting days must be a positive integer")

    if "timerange" in backtesting_config and backtesting_config["timerange"]:
        _validate_timerange(backtesting_config["timerange"])


def _validate_optimization_section(optimization_config: Dict[str, Any]) -> None:
    """
    Validate optimization section of the configuration.

    Args:
        optimization_config: Optimization configuration to validate.

    Raises:
        ValidationError: If the optimization configuration is invalid.
    """
    if "max_trials" in optimization_config:
        if (
            not isinstance(optimization_config["max_trials"], int)
            or optimization_config["max_trials"] <= 0
        ):
            raise ValidationError("Max trials must be a positive integer")

    if "epochs" in optimization_config:
        if (
            not isinstance(optimization_config["epochs"], int)
            or optimization_config["epochs"] <= 0
        ):
            raise ValidationError("Epochs must be a positive integer")

    if "spaces" in optimization_config:
        if not isinstance(optimization_config["spaces"], list):
            raise ValidationError("Spaces must be a list")

        valid_spaces = [
            "buy",
            "sell",
            "roi",
            "stoploss",
            "trailing",
            "protection",
            "all",
        ]
        for space in optimization_config["spaces"]:
            if space not in valid_spaces:
                raise ValidationError(
                    f"Invalid optimization space: {space}. "
                    f"Valid spaces: {', '.join(valid_spaces)}"
                )


def _validate_gpt_claude_section(gpt_claude_config: Dict[str, Any]) -> None:
    """
    Validate GPT-Claude section of the configuration.

    Args:
        gpt_claude_config: GPT-Claude configuration to validate.

    Raises:
        ValidationError: If the GPT-Claude configuration is invalid.
    """
    if "enable" in gpt_claude_config and gpt_claude_config["enable"]:
        if "api_key" not in gpt_claude_config or not gpt_claude_config["api_key"]:
            raise ValidationError(
                "API key is required when GPT-Claude integration is enabled"
            )

        if "model" in gpt_claude_config:
            valid_models = [
                "gpt-4",
                "gpt-4-32k",
                "gpt-3.5-turbo",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
            ]
            if gpt_claude_config["model"] not in valid_models:
                raise ValidationError(
                    f"Invalid model: {gpt_claude_config['model']}. "
                    f"Valid models: {', '.join(valid_models)}"
                )

        if "temperature" in gpt_claude_config:
            if not isinstance(gpt_claude_config["temperature"], (int, float)):
                raise ValidationError("Temperature must be a number")

            if (
                gpt_claude_config["temperature"] < 0
                or gpt_claude_config["temperature"] > 2
            ):
                raise ValidationError("Temperature must be between 0 and 2")


def _validate_ui_section(ui_config: Dict[str, Any]) -> None:
    """
    Validate UI section of the configuration.

    Args:
        ui_config: UI configuration to validate.

    Raises:
        ValidationError: If the UI configuration is invalid.
    """
    if "server" in ui_config:
        server_config = ui_config["server"]

        if "port" in server_config:
            if not isinstance(server_config["port"], int):
                raise ValidationError("Server port must be an integer")

            if server_config["port"] < 1 or server_config["port"] > 65535:
                raise ValidationError(
                    "Server port must be between 1 and 65535")

        # If username is provided, password must also be provided and vice versa
        if "username" in server_config and server_config["username"]:
            if "password" not in server_config or not server_config["password"]:
                raise ValidationError(
                    "Server password must be provided when username is provided"
                )

        if "password" in server_config and server_config["password"]:
            if "username" not in server_config or not server_config["username"]:
                raise ValidationError(
                    "Server username must be provided when password is provided"
                )


def _validate_data_section(data_config: Dict[str, Any]) -> None:
    """
    Validate data section of the configuration.

    Args:
        data_config: Data configuration to validate.

    Raises:
        ValidationError: If the data configuration is invalid.
    """
    if "directory" in data_config:
        if not isinstance(data_config["directory"], str):
            raise ValidationError("Data directory must be a string")

    if "timeframes" in data_config:
        if not isinstance(data_config["timeframes"], list):
            raise ValidationError("Timeframes must be a list")

        for timeframe in data_config["timeframes"]:
            _validate_timeframe(timeframe)

    if "dataformat_ohlcv" in data_config:
        valid_formats = ["json", "jsongz", "hdf5"]
        if data_config["dataformat_ohlcv"] not in valid_formats:
            raise ValidationError(
                f"Invalid OHLCV data format: {data_config['dataformat_ohlcv']}. "
                f"Valid formats: {', '.join(valid_formats)}"
            )


def _validate_timeframe(timeframe: str) -> None:
    """
    Validate timeframe string.

    Args:
        timeframe: Timeframe string to validate.

    Raises:
        ValidationError: If the timeframe is invalid.
    """
    valid_timeframes = [
        "1m",
        "3m",
        "5m",
        "15m",
        "30m",
        "1h",
        "2h",
        "4h",
        "6h",
        "8h",
        "12h",
        "1d",
        "3d",
        "1w",
        "1M",
    ]
    if timeframe not in valid_timeframes:
        raise ValidationError(
            f"Invalid timeframe: {timeframe}. "
            f"Valid timeframes: {', '.join(valid_timeframes)}"
        )


def _validate_timerange(timerange: str) -> None:
    """
    Validate timerange string.

    Args:
        timerange: Timerange string to validate.

    Raises:
        ValidationError: If the timerange is invalid.
    """
    # Timerange format: <type>-<startdate>-<enddate>
    # where <type> is one of: date, backtest
    parts = timerange.split("-")

    if len(parts) not in [2, 3]:
        raise ValidationError(
            "Timerange must have 2 or 3 parts separated by hyphens")

    timerange_type = parts[0]
    if timerange_type not in ["date", "backtest"]:
        raise ValidationError("Timerange type must be 'date' or 'backtest'")

    # Validate dates if type is 'date'
    if timerange_type == "date":
        if len(parts) != 3:
            raise ValidationError(
                "Date timerange must have 3 parts: 'date-<startdate>-<enddate>'"
            )

        try:
            # Dates should be in YYYYMMDD format
            start_date = parts[1]
            end_date = parts[2]

            if start_date and len(start_date) != 8:
                raise ValidationError("Start date must be in YYYYMMDD format")

            if end_date and len(end_date) != 8:
                raise ValidationError("End date must be in YYYYMMDD format")

            if start_date and end_date and int(start_date) > int(end_date):
                raise ValidationError(
                    "Start date must be earlier than end date")
        except ValueError:
            raise ValidationError(
                "Dates must be valid integers in YYYYMMDD format")


def load_config_file(config_file: Union[str, Path]) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.

    Args:
        config_file: Path to the configuration file.

    Returns:
        The loaded configuration dictionary.

    Raises:
        ValidationError: If the file cannot be loaded or the configuration is invalid.
    """
    if isinstance(config_file, str):
        config_file = Path(config_file)

    if not config_file.exists():
        raise ValidationError(f"Configuration file not found: {config_file}")

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in configuration file: {e}")
    except Exception as e:
        raise ValidationError(f"Error loading configuration file: {e}")

    # Validate the loaded configuration
    validate_config(config)

    return config


# Export public components
__all__ = ["validate_config", "load_config_file", "ValidationError"]