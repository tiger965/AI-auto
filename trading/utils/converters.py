""" "
Data conversion utilities for trading system.

This module provides functions for converting data between different formats
and representations used in the trading system.
"""

import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any

import modules.nlp as np
import config.paths as pd


def timeframe_to_seconds(timeframe: str) -> int:
    """
    Convert a timeframe string to seconds.

    Args:
        timeframe: Timeframe string (e.g., '1m', '5m', '1h', '1d').

    Returns:
        Number of seconds in the timeframe.

    Raises:
        ValueError: If the timeframe format is invalid.
    """
    timeframe_match = re.match(r"(\d+)([mhdwM])", timeframe)
    if not timeframe_match:
        raise ValueError(f"Invalid timeframe format: {timeframe}")

    amount, unit = timeframe_match.groups()
    amount = int(amount)

    seconds_per_unit = {
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 24 * 60 * 60,
        "M": 30 * 24 * 60 * 60,
    }

    return amount * seconds_per_unit[unit]


def timeframe_to_minutes(timeframe: str) -> int:
    """
    Convert a timeframe string to minutes.

    Args:
        timeframe: Timeframe string (e.g., '1m', '5m', '1h', '1d').

    Returns:
        Number of minutes in the timeframe.

    Raises:
        ValueError: If the timeframe format is invalid.
    """
    return timeframe_to_seconds(timeframe) // 60


def format_timeframe(timeframe: str) -> str:
    """
    Format a timeframe string to a more human-readable format.

    Args:
        timeframe: Timeframe string (e.g., '1m', '5m', '1h', '1d').

    Returns:
        Formatted timeframe string (e.g., '1 minute', '5 minutes', '1 hour', '1 day').

    Raises:
        ValueError: If the timeframe format is invalid.
    """
    timeframe_match = re.match(r"(\d+)([mhdwM])", timeframe)
    if not timeframe_match:
        raise ValueError(f"Invalid timeframe format: {timeframe}")

    amount, unit = timeframe_match.groups()
    amount = int(amount)

    unit_names = {
        "m": "minute",
        "h": "hour",
        "d": "day",
        "w": "week",
        "M": "month",
    }

    unit_name = unit_names[unit]
    if amount != 1:
        unit_name += "s"

    return f"{amount} {unit_name}"


def format_ms_time(ms_timestamp: int) -> str:
    """
    Format a millisecond timestamp to a human-readable date and time string.

    Args:
        ms_timestamp: Millisecond timestamp.

    Returns:
        Formatted date and time string.
    """
    dt = datetime.fromtimestamp(ms_timestamp / 1000.0)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def timestamp_to_datetime(timestamp: Union[int, float]) -> datetime:
    """
    Convert a timestamp to a datetime object.

    Args:
        timestamp: Timestamp in seconds or milliseconds.

    Returns:
        Datetime object.
    """
    # Determine if the timestamp is in seconds or milliseconds
    if timestamp > 1e10:  # Threshold to distinguish between seconds and milliseconds
        timestamp = timestamp / 1000.0

    return datetime.fromtimestamp(timestamp)


def datetime_to_timestamp(
    dt: datetime, in_milliseconds: bool = True
) -> Union[int, float]:
    """
    Convert a datetime object to a timestamp.

    Args:
        dt: Datetime object.
        in_milliseconds: Whether to return the timestamp in milliseconds (True) or seconds (False).

    Returns:
        Timestamp in milliseconds or seconds.
    """
    timestamp = dt.timestamp()
    if in_milliseconds:
        return int(timestamp * 1000)
    return timestamp


def format_price(price: float, precision: int = 8) -> str:
    """
    Format a price to a string with a specified precision.

    Args:
        price: Price value.
        precision: Number of decimal places.

    Returns:
        Formatted price string.
    """
    return f"{price:.{precision}f}"


def parse_timerange(timerange: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Parse a timerange string to start and end datetime objects.

    Timerange format:
        - 'date-YYYYMMDD-YYYYMMDD': Specific date range
        - 'date-YYYYMMDD-': From date to now
        - 'date--YYYYMMDD': From inception to date

    Args:
        timerange: Timerange string.

    Returns:
        Tuple of start and end datetime objects.

    Raises:
        ValueError: If the timerange format is invalid.
    """
    if not timerange:
        return None, None

    parts = timerange.split("-")
    if len(parts) != 3:
        raise ValueError(f"Invalid timerange format: {timerange}")

    timerange_type, start, end = parts

    if timerange_type != "date":
        raise ValueError(f"Unsupported timerange type: {timerange_type}")

    start_dt = None
    end_dt = None

    if start:
        try:
            start_dt = datetime.strptime(start, "%Y%m%d")
        except ValueError:
            raise ValueError(f"Invalid start date format: {start}")

    if end:
        try:
            end_dt = datetime.strptime(end, "%Y%m%d")
            # Set end time to end of day
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
        except ValueError:
            raise ValueError(f"Invalid end date format: {end}")

    return start_dt, end_dt


def timerange_to_timestamps(timerange: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Convert a timerange string to start and end timestamps in milliseconds.

    Args:
        timerange: Timerange string.

    Returns:
        Tuple of start and end timestamps in milliseconds.

    Raises:
        ValueError: If the timerange format is invalid.
    """
    start_dt, end_dt = parse_timerange(timerange)

    start_ts = None
    end_ts = None

    if start_dt:
        start_ts = datetime_to_timestamp(start_dt)

    if end_dt:
        end_ts = datetime_to_timestamp(end_dt)

    return start_ts, end_ts


def freqtrade_ohlcv_to_dataframe(ohlcv_data: List[List[Any]]) -> pd.DataFrame:
    """
    Convert Freqtrade OHLCV data to a pandas DataFrame.

    Args:
        ohlcv_data: OHLCV data in Freqtrade format.

    Returns:
        Pandas DataFrame with OHLCV data.
    """
    df = pd.DataFrame(
        ohlcv_data, columns=["date", "open", "high", "low", "close", "volume"]
    )
    df["date"] = pd.to_datetime(df["date"], unit="ms")
    df.set_index("date", inplace=True)
    return df


def dataframe_to_freqtrade_ohlcv(df: pd.DataFrame) -> List[List[Any]]:
    """
    Convert a pandas DataFrame to Freqtrade OHLCV data.

    Args:
        df: Pandas DataFrame with OHLCV data.

    Returns:
        OHLCV data in Freqtrade format.
    """
    # Ensure the DataFrame has the necessary columns
    required_columns = ["open", "high", "low", "close", "volume"]
    if not all(col in df.columns for col in required_columns):
        raise ValueError(
            f"DataFrame must have the following columns: {required_columns}"
        )

    # Convert to the format expected by Freqtrade
    df = df.reset_index()
    df["date"] = df["date"].apply(lambda x: int(datetime_to_timestamp(x)))

    return df[["date", "open", "high", "low", "close", "volume"]].values.tolist()


def freqtrade_trade_to_dict(trade: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a Freqtrade trade to a standardized dictionary format.

    Args:
        trade: Trade in Freqtrade format.

    Returns:
        Trade in standardized dictionary format.
    """
    standardized_trade = {
        "trade_id": trade.get("trade_id", None),
        "pair": trade.get("pair", None),
        "open_date": timestamp_to_datetime(trade.get("open_date_timestamp", 0)),
        "close_date": (
            timestamp_to_datetime(trade.get("close_date_timestamp", 0))
            if trade.get("close_date_timestamp")
            else None
        ),
        "open_rate": float(trade.get("open_rate", 0)),
        "close_rate": (
            float(trade.get("close_rate", 0)) if trade.get(
                "close_rate") else None
        ),
        "amount": float(trade.get("amount", 0)),
        "profit_ratio": (
            float(trade.get("profit_ratio", 0)) if trade.get(
                "profit_ratio") else None
        ),
        "profit_abs": (
            float(trade.get("profit_abs", 0)) if trade.get(
                "profit_abs") else None
        ),
        "stake_amount": float(trade.get("stake_amount", 0)),
        "fee_open": float(trade.get("fee_open", 0)) if trade.get("fee_open") else 0,
        "fee_close": float(trade.get("fee_close", 0)) if trade.get("fee_close") else 0,
        "trade_duration": (
            int(trade.get("trade_duration", 0)) if trade.get(
                "trade_duration") else None
        ),
        "is_open": bool(trade.get("is_open", False)),
        "exit_reason": trade.get("exit_reason", None),
        "strategy": trade.get("strategy", None),
        "enter_tag": trade.get("enter_tag", None),
    }

    return standardized_trade


def convert_ohlcv_format(
    ohlcv_data: Union[List[List[Any]], pd.DataFrame],
    source_format: str,
    target_format: str,
) -> Union[List[List[Any]], pd.DataFrame]:
    """
    Convert OHLCV data between different formats.

    Supported formats:
        - 'freqtrade': List of lists in Freqtrade format
        - 'dataframe': Pandas DataFrame with 'date' as index

    Args:
        ohlcv_data: OHLCV data in source format.
        source_format: Source data format ('freqtrade' or 'dataframe').
        target_format: Target data format ('freqtrade' or 'dataframe').

    Returns:
        OHLCV data in target format.

    Raises:
        ValueError: If the source or target format is unsupported.
    """
    if source_format == target_format:
        return ohlcv_data

    if source_format == "freqtrade" and target_format == "dataframe":
        return freqtrade_ohlcv_to_dataframe(ohlcv_data)

    if source_format == "dataframe" and target_format == "freqtrade":
        return dataframe_to_freqtrade_ohlcv(ohlcv_data)

    raise ValueError(
        f"Unsupported conversion: {source_format} to {target_format}")


# Export public components
__all__ = [
    "timeframe_to_seconds",
    "timeframe_to_minutes",
    "format_timeframe",
    "format_ms_time",
    "timestamp_to_datetime",
    "datetime_to_timestamp",
    "format_price",
    "parse_timerange",
    "timerange_to_timestamps",
    "freqtrade_ohlcv_to_dataframe",
    "dataframe_to_freqtrade_ohlcv",
    "freqtrade_trade_to_dict",
    "convert_ohlcv_format",
]