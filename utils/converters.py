# -*- coding: utf-8 -*-
"""
数据转换工具模块: converters
功能描述: 提供各种数据类型之间的转换功能，并包含增强的日志记录
版本: 1.1
创建日期: 2025-04-17
"""

import json
import datetime
import logging
import time
import traceback
from typing import Any, Union, Dict, List, Tuple, Optional, Set, TypeVar, Callable

# 配置日志记录器，使用更详细的格式
logger = logging.getLogger(__name__)

# 类型变量定义，用于泛型提示
T = TypeVar("T")


def to_int(
    value: Any,
    default: Optional[int] = None,
    strict: bool = False,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    """
    将值转换为整数

    Args:
        value: 要转换的值
        default: 转换失败时返回的默认值
        strict: 是否使用严格模式，严格模式下布尔值和浮点数不会被转换
        context: 上下文信息，用于增强日志记录

    Returns:
        转换后的整数，失败则返回默认值

    Examples:
        >>> to_int("123")
        123
        >>> to_int("abc", default=0)
        0
        >>> to_int(True)
        1
        >>> to_int(True, strict=True)
        None
    """
    log_context = context or {}
    function_name = "to_int"

    if value is None:
        logger.debug(
            f"转换为整数: 输入为None，返回默认值 {default}",
            extra={"function": function_name,
                   "input_type": "None", **log_context},
        )
        return default

    # 已经是整数类型
    if isinstance(value, int) and not isinstance(value, bool):
        logger.debug(
            f"转换为整数: 输入已经是整数 {value}",
            extra={"function": function_name,
                   "input_type": "int", **log_context},
        )
        return value

    # 严格模式下不转换布尔值
    if strict and isinstance(value, bool):
        logger.debug(
            f"转换为整数: 严格模式下不转换布尔值 {value}，返回默认值 {default}",
            extra={
                "function": function_name,
                "input_type": "bool",
                "strict_mode": True,
                **log_context,
            },
        )
        return default

    # 严格模式下不转换浮点数
    if strict and isinstance(value, float):
        logger.debug(
            f"转换为整数: 严格模式下不转换浮点数 {value}，返回默认值 {default}",
            extra={
                "function": function_name,
                "input_type": "float",
                "strict_mode": True,
                **log_context,
            },
        )
        return default

    try:
        # 尝试转换为整数
        result = int(float(value))
        logger.debug(
            f"转换为整数: 成功将 {value} ({type(value).__name__}) 转换为 {result}",
            extra={
                "function": function_name,
                "input_type": type(value).__name__,
                "result": result,
                **log_context,
            },
        )
        return result
    except (ValueError, TypeError) as e:
        logger.debug(
            f"转换为整数: 无法将 {value} ({type(value).__name__}) 转换为整数: {str(e)}",
            extra={
                "function": function_name,
                "input_type": type(value).__name__,
                "error": str(e),
                **log_context,
            },
        )
        return default


def to_float(
    value: Any,
    default: Optional[float] = None,
    strict: bool = False,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[float]:
    """
    将值转换为浮点数

    Args:
        value: 要转换的值
        default: 转换失败时返回的默认值
        strict: 是否使用严格模式，严格模式下布尔值不会被转换
        context: 上下文信息，用于增强日志记录

    Returns:
        转换后的浮点数，失败则返回默认值

    Examples:
        >>> to_float("123.45")
        123.45
        >>> to_float("abc", default=0.0)
        0.0
    """
    log_context = context or {}
    function_name = "to_float"

    if value is None:
        logger.debug(
            f"转换为浮点数: 输入为None，返回默认值 {default}",
            extra={"function": function_name,
                   "input_type": "None", **log_context},
        )
        return default

    # 已经是浮点数类型
    if isinstance(value, float):
        logger.debug(
            f"转换为浮点数: 输入已经是浮点数 {value}",
            extra={"function": function_name,
                   "input_type": "float", **log_context},
        )
        return value

    # 已经是整数类型
    if isinstance(value, int) and not isinstance(value, bool):
        result = float(value)
        logger.debug(
            f"转换为浮点数: 将整数 {value} 转换为浮点数 {result}",
            extra={
                "function": function_name,
                "input_type": "int",
                "result": result,
                **log_context,
            },
        )
        return result

    # 严格模式下不转换布尔值
    if strict and isinstance(value, bool):
        logger.debug(
            f"转换为浮点数: 严格模式下不转换布尔值 {value}，返回默认值 {default}",
            extra={
                "function": function_name,
                "input_type": "bool",
                "strict_mode": True,
                **log_context,
            },
        )
        return default

    try:
        # 尝试转换为浮点数
        result = float(value)
        logger.debug(
            f"转换为浮点数: 成功将 {value} ({type(value).__name__}) 转换为 {result}",
            extra={
                "function": function_name,
                "input_type": type(value).__name__,
                "result": result,
                **log_context,
            },
        )
        return result
    except (ValueError, TypeError) as e:
        logger.debug(
            f"转换为浮点数: 无法将 {value} ({type(value).__name__}) 转换为浮点数: {str(e)}",
            extra={
                "function": function_name,
                "input_type": type(value).__name__,
                "error": str(e),
                **log_context,
            },
        )
        return default


def to_bool(
    value: Any, default: Optional[bool] = None, context: Optional[Dict[str, Any]] = None
) -> Optional[bool]:
    """
    将值转换为布尔值

    Args:
        value: 要转换的值
        default: 转换失败时返回的默认值
        context: 上下文信息，用于增强日志记录

    Returns:
        转换后的布尔值，失败则返回默认值

    Examples:
        >>> to_bool("true")
        True
        >>> to_bool("false")
        False
        >>> to_bool(1)
        True
        >>> to_bool(0)
        False
        >>> to_bool("yes")
        True
        >>> to_bool("no")
        False
    """
    log_context = context or {}
    function_name = "to_bool"

    if value is None:
        logger.debug(
            f"转换为布尔值: 输入为None，返回默认值 {default}",
            extra={"function": function_name,
                   "input_type": "None", **log_context},
        )
        return default

    # 已经是布尔类型
    if isinstance(value, bool):
        logger.debug(
            f"转换为布尔值: 输入已经是布尔值 {value}",
            extra={"function": function_name,
                   "input_type": "bool", **log_context},
        )
        return value

    # 数字转换：0为False，其他为True
    if isinstance(value, (int, float)):
        result = bool(value)
        logger.debug(
            f"转换为布尔值: 将数值 {value} 转换为布尔值 {result}",
            extra={
                "function": function_name,
                "input_type": type(value).__name__,
                "result": result,
                **log_context,
            },
        )
        return result

    # 字符串转换
    if isinstance(value, str):
        value_lower = value.lower().strip()

        # True表示
        if value_lower in ("true", "yes", "y", "1", "t"):
            logger.debug(
                f"转换为布尔值: 将字符串 '{value}' 转换为 True",
                extra={
                    "function": function_name,
                    "input_type": "str",
                    "result": True,
                    **log_context,
                },
            )
            return True

        # False表示
        if value_lower in ("false", "no", "n", "0", "f"):
            logger.debug(
                f"转换为布尔值: 将字符串 '{value}' 转换为 False",
                extra={
                    "function": function_name,
                    "input_type": "str",
                    "result": False,
                    **log_context,
                },
            )
            return False

    # 非空容器为True，空容器为False
    if hasattr(value, "__len__"):
        result = bool(len(value))
        logger.debug(
            f"转换为布尔值: 将容器 {type(value).__name__} 转换为布尔值 {result}",
            extra={
                "function": function_name,
                "input_type": type(value).__name__,
                "result": result,
                **log_context,
            },
        )
        return result

    # 其他情况尝试bool()转换
    try:
        result = bool(value)
        logger.debug(
            f"转换为布尔值: 成功将 {value} ({type(value).__name__}) 转换为 {result}",
            extra={
                "function": function_name,
                "input_type": type(value).__name__,
                "result": result,
                **log_context,
            },
        )
        return result
    except (ValueError, TypeError) as e:
        logger.debug(
            f"转换为布尔值: 无法将 {value} ({type(value).__name__}) 转换为布尔值: {str(e)}",
            extra={
                "function": function_name,
                "input_type": type(value).__name__,
                "error": str(e),
                **log_context,
            },
        )
        return default


def to_string(
    value: Any,
    default: Optional[str] = None,
    format_spec: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    将值转换为字符串

    Args:
        value: 要转换的值
        default: 转换失败时返回的默认值
        format_spec: 格式说明符，用于格式化输出
        context: 上下文信息，用于增强日志记录

    Returns:
        转换后的字符串，失败则返回默认值

    Examples:
        >>> to_string(123)
        '123'
        >>> to_string(None, default="N/A")
        'N/A'
        >>> to_string(123.456, format_spec=".2f")
        '123.46'
    """
    log_context = context or {}
    function_name = "to_string"

    if value is None:
        logger.debug(
            f"转换为字符串: 输入为None，返回默认值 {default}",
            extra={"function": function_name,
                   "input_type": "None", **log_context},
        )
        return default

    # 已经是字符串类型
    if isinstance(value, str):
        if format_spec is None:
            logger.debug(
                f"转换为字符串: 输入已经是字符串 '{value}'",
                extra={"function": function_name,
                       "input_type": "str", **log_context},
            )
            return value
        else:
            result = format(value, format_spec)
            logger.debug(
                f"转换为字符串: 使用格式说明符 '{format_spec}' 格式化字符串 '{value}' 为 '{result}'",
                extra={
                    "function": function_name,
                    "input_type": "str",
                    "format_spec": format_spec,
                    "result": result,
                    **log_context,
                },
            )
            return result

    try:
        # 使用格式说明符
        if format_spec is not None:
            result = format(value, format_spec)
            logger.debug(
                f"转换为字符串: 使用格式说明符 '{format_spec}' 将 {value} ({type(value).__name__}) 格式化为 '{result}'",
                extra={
                    "function": function_name,
                    "input_type": type(value).__name__,
                    "format_spec": format_spec,
                    "result": result,
                    **log_context,
                },
            )
            return result

        # 普通转换
        result = str(value)
        logger.debug(
            f"转换为字符串: 成功将 {value} ({type(value).__name__}) 转换为 '{result}'",
            extra={
                "function": function_name,
                "input_type": type(value).__name__,
                "result": result,
                **log_context,
            },
        )
        return result
    except (ValueError, TypeError) as e:
        logger.debug(
            f"转换为字符串: 无法将 {value} ({type(value).__name__}) 转换为字符串: {str(e)}",
            extra={
                "function": function_name,
                "input_type": type(value).__name__,
                "error": str(e),
                **log_context,
            },
        )
        return default


def to_date(
    value: Any,
    default: Optional[datetime.date] = None,
    formats: Optional[List[str]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[datetime.date]:
    """
    将值转换为日期

    Args:
        value: 要转换的值(字符串、时间戳、datetime对象)
        default: 转换失败时返回的默认值
        formats: 日期格式字符串列表，用于尝试解析字符串
        context: 上下文信息，用于增强日志记录

    Returns:
        转换后的日期，失败则返回默认值

    Examples:
        >>> to_date("2023-01-15")
        datetime.date(2023, 1, 15)
        >>> to_date(datetime.datetime(2023, 1, 15, 12, 30))
        datetime.date(2023, 1, 15)
    """
    log_context = context or {}
    function_name = "to_date"

    if value is None:
        logger.debug(
            f"转换为日期: 输入为None，返回默认值 {default}",
            extra={"function": function_name,
                   "input_type": "None", **log_context},
        )
        return default

    # 已经是date类型
    if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        logger.debug(
            f"转换为日期: 输入已经是日期 {value}",
            extra={"function": function_name,
                   "input_type": "date", **log_context},
        )
        return value

    # 如果是datetime类型，提取日期部分
    if isinstance(value, datetime.datetime):
        result = value.date()
        logger.debug(
            f"转换为日期: 从datetime对象 {value} 提取日期部分 {result}",
            extra={
                "function": function_name,
                "input_type": "datetime",
                "result": str(result),
                **log_context,
            },
        )
        return result

    # 默认格式列表
    if formats is None:
        formats = [
            "%Y-%m-%d",  # 2023-01-15
            "%d/%m/%Y",  # 15/01/2023
            "%m/%d/%Y",  # 01/15/2023
            "%Y/%m/%d",  # 2023/01/15
            "%d-%m-%Y",  # 15-01-2023
            "%m-%d-%Y",  # 01-15-2023
            "%Y.%m.%d",  # 2023.01.15
            "%d.%m.%Y",  # 15.01.2023
            "%m.%d.%Y",  # 01.15.2023
            "%b %d, %Y",  # Jan 15, 2023
            "%d %b %Y",  # 15 Jan 2023
            "%B %d, %Y",  # January 15, 2023
            "%d %B %Y",  # 15 January 2023
        ]

    # 处理字符串
    if isinstance(value, str):
        value = value.strip()

        # 尝试每种格式
        for fmt in formats:
            try:
                result = datetime.datetime.strptime(value, fmt).date()
                logger.debug(
                    f"转换为日期: 使用格式 '{fmt}' 成功解析字符串 '{value}' 为日期 {result}",
                    extra={
                        "function": function_name,
                        "input_type": "str",
                        "format": fmt,
                        "result": str(result),
                        **log_context,
                    },
                )
                return result
            except ValueError:
                continue

        logger.debug(
            f"转换为日期: 无法解析日期字符串 '{value}'，尝试了 {len(formats)} 种格式",
            extra={
                "function": function_name,
                "input_type": "str",
                "formats_tried": len(formats),
                **log_context,
            },
        )
        return default

    # 处理时间戳（整数或浮点数）
    if isinstance(value, (int, float)):
        try:
            # 假设这是一个Unix时间戳
            result = datetime.datetime.fromtimestamp(value).date()
            logger.debug(
                f"转换为日期: 将时间戳 {value} 转换为日期 {result}",
                extra={
                    "function": function_name,
                    "input_type": type(value).__name__,
                    "result": str(result),
                    **log_context,
                },
            )
            return result
        except (ValueError, OSError, OverflowError) as e:
            logger.debug(
                f"转换为日期: 无法将时间戳 {value} 转换为日期: {str(e)}",
                extra={
                    "function": function_name,
                    "input_type": type(value).__name__,
                    "error": str(e),
                    **log_context,
                },
            )
            return default

    # 其他类型无法转换
    logger.debug(
        f"转换为日期: 无法将 {type(value).__name__} 类型转换为日期",
        extra={
            "function": function_name,
            "input_type": type(value).__name__,
            **log_context,
        },
    )
    return default


def to_datetime(
    value: Any,
    default: Optional[datetime.datetime] = None,
    formats: Optional[List[str]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[datetime.datetime]:
    """
    将值转换为日期时间

    Args:
        value: 要转换的值(字符串、时间戳、date对象)
        default: 转换失败时返回的默认值
        formats: 日期时间格式字符串列表，用于尝试解析字符串
        context: 上下文信息，用于增强日志记录

    Returns:
        转换后的日期时间，失败则返回默认值

    Examples:
        >>> to_datetime("2023-01-15 12:30:45")
        datetime.datetime(2023, 1, 15, 12, 30, 45)
        >>> to_datetime(datetime.date(2023, 1, 15))
        datetime.datetime(2023, 1, 15, 0, 0)
    """
    log_context = context or {}
    function_name = "to_datetime"

    if value is None:
        logger.debug(
            f"转换为日期时间: 输入为None，返回默认值 {default}",
            extra={"function": function_name,
                   "input_type": "None", **log_context},
        )
        return default

    # 已经是datetime类型
    if isinstance(value, datetime.datetime):
        logger.debug(
            f"转换为日期时间: 输入已经是日期时间 {value}",
            extra={"function": function_name,
                   "input_type": "datetime", **log_context},
        )
        return value

    # 如果是date类型，转换为当天0点的datetime
    if isinstance(value, datetime.date):
        result = datetime.datetime.combine(value, datetime.time())
        logger.debug(
            f"转换为日期时间: 将日期 {value} 转换为日期时间 {result}",
            extra={
                "function": function_name,
                "input_type": "date",
                "result": str(result),
                **log_context,
            },
        )
        return result

    # 默认格式列表
    if formats is None:
        formats = [
            "%Y-%m-%d %H:%M:%S",  # 2023-01-15 12:30:45
            "%Y-%m-%d %H:%M",  # 2023-01-15 12:30
            "%Y-%m-%dT%H:%M:%S",  # 2023-01-15T12:30:45
            "%Y-%m-%dT%H:%M:%S.%f",  # 2023-01-15T12:30:45.123456
            "%Y-%m-%dT%H:%M:%S.%fZ",  # 2023-01-15T12:30:45.123456Z (ISO 8601)
            "%Y-%m-%d",  # 2023-01-15 (默认时间为00:00:00)
            "%d/%m/%Y %H:%M:%S",  # 15/01/2023 12:30:45
            "%m/%d/%Y %H:%M:%S",  # 01/15/2023 12:30:45
            "%Y/%m/%d %H:%M:%S",  # 2023/01/15 12:30:45
            "%d-%m-%Y %H:%M:%S",  # 15-01-2023 12:30:45
            "%m-%d-%Y %H:%M:%S",  # 01-15-2023 12:30:45
            "%Y.%m.%d %H:%M:%S",  # 2023.01.15 12:30:45
            "%d.%m.%Y %H:%M:%S",  # 15.01.2023 12:30:45
            "%m.%d.%Y %H:%M:%S",  # 01.15.2023 12:30:45
            "%b %d, %Y %H:%M:%S",  # Jan 15, 2023 12:30:45
            "%d %b %Y %H:%M:%S",  # 15 Jan 2023 12:30:45
            "%B %d, %Y %H:%M:%S",  # January 15, 2023 12:30:45
            "%d %B %Y %H:%M:%S",  # 15 January 2023 12:30:45
        ]

    # 处理字符串
    if isinstance(value, str):
        value = value.strip()

        # 尝试每种格式
        for fmt in formats:
            try:
                result = datetime.datetime.strptime(value, fmt)
                logger.debug(
                    f"转换为日期时间: 使用格式 '{fmt}' 成功解析字符串 '{value}' 为日期时间 {result}",
                    extra={
                        "function": function_name,
                        "input_type": "str",
                        "format": fmt,
                        "result": str(result),
                        **log_context,
                    },
                )
                return result
            except ValueError:
                continue

        logger.debug(
            f"转换为日期时间: 无法解析日期时间字符串 '{value}'，尝试了 {len(formats)} 种格式",
            extra={
                "function": function_name,
                "input_type": "str",
                "formats_tried": len(formats),
                **log_context,
            },
        )
        return default

    # 处理时间戳（整数或浮点数）
    if isinstance(value, (int, float)):
        try:
            # 假设这是一个Unix时间戳
            result = datetime.datetime.fromtimestamp(value)
            logger.debug(
                f"转换为日期时间: 将时间戳 {value} 转换为日期时间 {result}",
                extra={
                    "function": function_name,
                    "input_type": type(value).__name__,
                    "result": str(result),
                    **log_context,
                },
            )
            return result
        except (ValueError, OSError, OverflowError) as e:
            logger.debug(
                f"转换为日期时间: 无法将时间戳 {value} 转换为日期时间: {str(e)}",
                extra={
                    "function": function_name,
                    "input_type": type(value).__name__,
                    "error": str(e),
                    **log_context,
                },
            )
            return default

    # 其他类型无法转换
    logger.debug(
        f"转换为日期时间: 无法将 {type(value).__name__} 类型转换为日期时间",
        extra={
            "function": function_name,
            "input_type": type(value).__name__,
            **log_context,
        },
    )
    return default


def to_list(
    value: Any,
    item_type: Optional[Callable[[Any], T]] = None,
    separator: str = ",",
    default: Optional[List[Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[List[Any]]:
    """
    将值转换为列表

    Args:
        value: 要转换的值
        item_type: 元素类型转换函数，用于转换列表中每个元素的类型
        separator: 分隔符，用于分割字符串
        default: 转换失败时返回的默认值
        context: 上下文信息，用于增强日志记录

    Returns:
        转换后的列表，失败则返回默认值

    Examples:
        >>> to_list("1,2,3")
        ['1', '2', '3']
        >>> to_list("1,2,3", item_type=int)
        [1, 2, 3]
        >>> to_list(["1", "2", "3"], item_type=int)
        [1, 2, 3]
    """
    log_context = context or {}
    function_name = "to_list"

    if value is None:
        logger.debug(
            f"转换为列表: 输入为None，返回默认值 {default}",
            extra={"function": function_name,
                   "input_type": "None", **log_context},
        )
        return default

    # 已经是列表类型
    if isinstance(value, list):
        # 如果需要转换元素类型
        if item_type:
            try:
                result = [item_type(item) for item in value]
                logger.debug(
                    f"转换为列表: 将列表中的元素转换为 {item_type.__name__} 类型",
                    extra={
                        "function": function_name,
                        "input_type": "list",
                        "item_type": item_type.__name__,
                        **log_context,
                    },
                )
                return result
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"转换为列表: 转换列表元素类型时出错: {str(e)}",
                    extra={
                        "function": function_name,
                        "input_type": "list",
                        "error": str(e),
                        **log_context,
                    },
                )
                return default
        else:
            logger.debug(
                f"转换为列表: 输入已经是列表，长度为 {len(value)}",
                extra={
                    "function": function_name,
                    "input_type": "list",
                    "length": len(value),
                    **log_context,
                },
            )
            return value

    # 元组转换为列表
    if isinstance(value, tuple):
        # 如果需要转换元素类型
        if item_type:
            try:
                result = [item_type(item) for item in value]
                logger.debug(
                    f"转换为列表: 将元组转换为列表，并将元素转换为 {item_type.__name__} 类型",
                    extra={
                        "function": function_name,
                        "input_type": "tuple",
                        "item_type": item_type.__name__,
                        **log_context,
                    },
                )
                return result
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"转换为列表: 转换元组元素类型时出错: {str(e)}",
                    extra={
                        "function": function_name,
                        "input_type": "tuple",
                        "error": str(e),
                        **log_context,
                    },
                )
                return default
        else:
            result = list(value)
            logger.debug(
                f"转换为列表: 将元组转换为列表，长度为 {len(result)}",
                extra={
                    "function": function_name,
                    "input_type": "tuple",
                    "length": len(result),
                    **log_context,
                },
            )
            return result

    # 集合转换为列表
    if isinstance(value, set):
        # 如果需要转换元素类型
        if item_type:
            try:
                result = [item_type(item) for item in value]
                logger.debug(
                    f"转换为列表: 将集合转换为列表，并将元素转换为 {item_type.__name__} 类型",
                    extra={
                        "function": function_name,
                        "input_type": "set",
                        "item_type": item_type.__name__,
                        **log_context,
                    },
                )
                return result
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"转换为列表: 转换集合元素类型时出错: {str(e)}",
                    extra={
                        "function": function_name,
                        "input_type": "set",
                        "error": str(e),
                        **log_context,
                    },
                )
                return default
        else:
            result = list(value)
            logger.debug(
                f"转换为列表: 将集合转换为列表，长度为 {len(result)}",
                extra={
                    "function": function_name,
                    "input_type": "set",
                    "length": len(result),
                    **log_context,
                },
            )
            return result

    # 字符串转换为列表（使用分隔符分割）
    if isinstance(value, str):
        # 空字符串特殊处理
        if not value.strip():
            empty_list = []
            logger.debug(
                f"转换为列表: 输入为空字符串，返回空列表",
                extra={
                    "function": function_name,
                    "input_type": "str",
                    "length": 0,
                    **log_context,
                },
            )
            return empty_list

        # 使用分隔符分割
        parts = [part.strip() for part in value.split(separator)]

        # 如果需要转换元素类型
        if item_type:
            try:
                result = [item_type(item) for item in parts]
                logger.debug(
                    f"转换为列表: 将字符串 '{value}' 分割并转换为 {item_type.__name__} 类型元素的列表，长度为 {len(result)}",
                    extra={
                        "function": function_name,
                        "input_type": "str",
                        "item_type": item_type.__name__,
                        "length": len(result),
                        **log_context,
                    },
                )
                return result
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"转换为列表: 转换字符串分割后的元素类型时出错: {str(e)}",
                    extra={
                        "function": function_name,
                        "input_type": "str",
                        "error": str(e),
                        **log_context,
                    },
                )
                return default
        else:
            logger.debug(
                f"转换为列表: 将字符串 '{value}' 分割为列表，长度为 {len(parts)}",
                extra={
                    "function": function_name,
                    "input_type": "str",
                    "length": len(parts),
                    **log_context,
                },
            )
            return parts

    # 字典转换为列表（返回键的列表）
    if isinstance(value, dict):
        result = list(value.keys())
        logger.debug(
            f"转换为列表: 将字典的键转换为列表，长度为 {len(result)}",
            extra={
                "function": function_name,
                "input_type": "dict",
                "length": len(result),
                **log_context,
            },
        )
        return result

    # JSON字符串尝试解析
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                # 如果需要转换元素类型
                if item_type:
                    try:
                        result = [item_type(item) for item in parsed]
                        logger.debug(
                            f"转换为列表: 将JSON字符串解析为列表，并将元素转换为 {item_type.__name__} 类型",
                            extra={
                                "function": function_name,
                                "input_type": "json_str",
                                "item_type": item_type.__name__,
                                **log_context,
                            },
                        )
                        return result
                    except (ValueError, TypeError) as e:
                        logger.warning(
                            f"转换为列表: 转换JSON解析后的元素类型时出错: {str(e)}",
                            extra={
                                "function": function_name,
                                "input_type": "json_str",
                                "error": str(e),
                                **log_context,
                            },
                        )
                        return default
                else:
                    logger.debug(
                        f"转换为列表: 将JSON字符串解析为列表，长度为 {len(parsed)}",
                        extra={
                            "function": function_name,
                            "input_type": "json_str",
                            "length": len(parsed),
                            **log_context,
                        },
                    )
                    return parsed
        except json.JSONDecodeError:
            # 非JSON字符串，忽略错误继续尝试其他方法
            pass

    # 单个元素转换为只有一个元素的列表
    try:
        if item_type:
            result = [item_type(value)]
        else:
            result = [value]
        logger.debug(
            f"转换为列表: 将单个元素 {value} ({type(value).__name__}) 转换为单元素列表",
            extra={
                "function": function_name,
                "input_type": type(value).__name__,
                **log_context,
            },
        )
        return result
    except (ValueError, TypeError) as e:
        logger.warning(
            f"转换为列表: 无法将 {value} ({type(value).__name__}) 转换为列表: {str(e)}",
            extra={
                "function": function_name,
                "input_type": type(value).__name__,
                "error": str(e),
                **log_context,
            },
        )
        return default


def to_dict(
    value: Any,
    key_type: Optional[Callable[[Any], Any]] = None,
    value_type: Optional[Callable[[Any], Any]] = None,
    default: Optional[Dict[Any, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[Any, Any]]:
    """
    将值转换为字典

    Args:
        value: 要转换的值
        key_type: 键类型转换函数
        value_type: 值类型转换函数
        default: 转换失败时返回的默认值
        context: 上下文信息，用于增强日志记录

    Returns:
        转换后的字典，失败则返回默认值

    Examples:
        >>> to_dict('{"a": 1, "b": 2}')
        {'a': 1, 'b': 2}
        >>> to_dict([('a', '1'), ('b', '2')], value_type=int)
        {'a': 1, 'b': 2}
    """
    log_context = context or {}
    function_name = "to_dict"

    if value is None:
        logger.debug(
            f"转换为字典: 输入为None，返回默认值 {default}",
            extra={"function": function_name,
                   "input_type": "None", **log_context},
        )
        return default

    # 已经是字典类型
    if isinstance(value, dict):
        # 如果需要转换键值类型
        if key_type or value_type:
            try:
                result = {}
                for k, v in value.items():
                    new_key = key_type(k) if key_type else k
                    new_value = value_type(v) if value_type else v
                    result[new_key] = new_value

                logger.debug(
                    f"转换为字典: 转换字典键值类型，键数量为 {len(result)}",
                    extra={
                        "function": function_name,
                        "input_type": "dict",
                        "key_type": key_type.__name__ if key_type else "None",
                        "value_type": value_type.__name__ if value_type else "None",
                        **log_context,
                    },
                )
                return result
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"转换为字典: 转换字典键值类型时出错: {str(e)}",
                    extra={
                        "function": function_name,
                        "input_type": "dict",
                        "error": str(e),
                        **log_context,
                    },
                )
                return default
        else:
            logger.debug(
                f"转换为字典: 输入已经是字典，键数量为 {len(value)}",
                extra={
                    "function": function_name,
                    "input_type": "dict",
                    "length": len(value),
                    **log_context,
                },
            )
            return value

    # JSON字符串转字典
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                # 如果需要转换键值类型
                if key_type or value_type:
                    try:
                        result = {}
                        for k, v in parsed.items():
                            new_key = key_type(k) if key_type else k
                            new_value = value_type(v) if value_type else v
                            result[new_key] = new_value

                        logger.debug(
                            f"转换为字典: 将JSON字符串解析为字典并转换键值类型，键数量为 {len(result)}",
                            extra={
                                "function": function_name,
                                "input_type": "json_str",
                                "key_type": key_type.__name__ if key_type else "None",
                                "value_type": (
                                    value_type.__name__ if value_type else "None"
                                ),
                                **log_context,
                            },
                        )
                        return result
                    except (ValueError, TypeError) as e:
                        logger.warning(
                            f"转换为字典: 转换JSON解析后的字典键值类型时出错: {str(e)}",
                            extra={
                                "function": function_name,
                                "input_type": "json_str",
                                "error": str(e),
                                **log_context,
                            },
                        )
                        return default
                else:
                    logger.debug(
                        f"转换为字典: 将JSON字符串解析为字典，键数量为 {len(parsed)}",
                        extra={
                            "function": function_name,
                            "input_type": "json_str",
                            "length": len(parsed),
                            **log_context,
                        },
                    )
                    return parsed
            else:
                logger.warning(
                    f"转换为字典: JSON字符串解析结果不是字典，而是 {type(parsed).__name__}",
                    extra={
                        "function": function_name,
                        "input_type": "json_str",
                        "parsed_type": type(parsed).__name__,
                        **log_context,
                    },
                )
                return default
        except json.JSONDecodeError as e:
            logger.debug(
                f"转换为字典: 无法将字符串解析为JSON: {str(e)}",
                extra={
                    "function": function_name,
                    "input_type": "str",
                    "error": str(e),
                    **log_context,
                },
            )
            # 非JSON字符串，继续尝试其他方法

    # 列表或元组转字典 [(key1, value1), (key2, value2)]
    if isinstance(value, (list, tuple)):
        try:
            # 检查列表或元组的每个元素是否都是有两个元素的序列
            if all(
                isinstance(item, (list, tuple)) and len(item) == 2 for item in value
            ):
                result = {}
                for k, v in value:
                    new_key = key_type(k) if key_type else k
                    new_value = value_type(v) if value_type else v
                    result[new_key] = new_value

                logger.debug(
                    f"转换为字典: 将键值对列表转换为字典，键数量为 {len(result)}",
                    extra={
                        "function": function_name,
                        "input_type": type(value).__name__,
                        "key_type": key_type.__name__ if key_type else "None",
                        "value_type": value_type.__name__ if value_type else "None",
                        **log_context,
                    },
                )
                return result
            else:
                logger.warning(
                    f"转换为字典: 列表或元组中的元素不是有效的键值对",
                    extra={
                        "function": function_name,
                        "input_type": type(value).__name__,
                        **log_context,
                    },
                )
                return default
        except (ValueError, TypeError) as e:
            logger.warning(
                f"转换为字典: 将键值对列表转换为字典时出错: {str(e)}",
                extra={
                    "function": function_name,
                    "input_type": type(value).__name__,
                    "error": str(e),
                    **log_context,
                },
            )
            return default

    # 对象转字典（尝试使用__dict__属性）
    if hasattr(value, "__dict__"):
        try:
            result = value.__dict__
            # 如果需要转换键值类型
            if key_type or value_type:
                converted = {}
                for k, v in result.items():
                    new_key = key_type(k) if key_type else k
                    new_value = value_type(v) if value_type else v
                    converted[new_key] = new_value
                result = converted

            logger.debug(
                f"转换为字典: 将对象的__dict__属性转换为字典，键数量为 {len(result)}",
                extra={
                    "function": function_name,
                    "input_type": type(value).__name__,
                    "key_type": key_type.__name__ if key_type else "None",
                    "value_type": value_type.__name__ if value_type else "None",
                    **log_context,
                },
            )
            return result
        except (ValueError, TypeError) as e:
            logger.warning(
                f"转换为字典: 将对象的__dict__属性转换为字典时出错: {str(e)}",
                extra={
                    "function": function_name,
                    "input_type": type(value).__name__,
                    "error": str(e),
                    **log_context,
                },
            )
            return default

    # 无法转换
    logger.warning(
        f"转换为字典: 无法将 {type(value).__name__} 类型转换为字典",
        extra={
            "function": function_name,
            "input_type": type(value).__name__,
            **log_context,
        },
    )
    return default


def bytes_to_human_readable(
    size_bytes: int,
    decimal_places: int = 1,
    binary_units: bool = False,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    将字节大小转换为人类可读格式

    Args:
        size_bytes: 字节大小
        decimal_places: 小数位数
        binary_units: 是否使用二进制单位(KiB, MiB等)
        context: 上下文信息，用于增强日志记录

    Returns:
        格式化后的字符串 (如 '1.5 MB' 或 '1.5 MiB')

    Examples:
        >>> bytes_to_human_readable(1500)
        '1.5 KB'
        >>> bytes_to_human_readable(1500, binary_units=True)
        '1.5 KiB'
    """
    log_context = context or {}
    function_name = "bytes_to_human_readable"

    if size_bytes < 0:
        logger.error(
            f"转换字节大小: 字节大小不能为负数: {size_bytes}",
            extra={"function": function_name,
                   "size_bytes": size_bytes, **log_context},
        )
        raise ValueError("字节大小不能为负数")

    # 设置单位和除数
    if binary_units:
        units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
        divisor = 1024.0
    else:
        units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
        divisor = 1000.0

    size = float(size_bytes)
    unit_index = 0

    while size >= divisor and unit_index < len(units) - 1:
        size /= divisor
        unit_index += 1

    # 格式化数值为指定小数位数
    format_string = f"{{:.{decimal_places}f}} {{}}"
    result = format_string.format(size, units[unit_index])

    logger.debug(
        f"转换字节大小: 将 {size_bytes} 字节转换为 {result}",
        extra={
            "function": function_name,
            "size_bytes": size_bytes,
            "result": result,
            "binary_units": binary_units,
            **log_context,
        },
    )

    return result


def seconds_to_human_readable(
    seconds: Union[int, float],
    format_type: str = "full",
    max_units: int = 2,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    将秒数转换为人类可读的时间格式

    Args:
        seconds: 秒数
        format_type: 格式类型，'full'(完整), 'short'(简短), 'iso'(ISO 8601)
        max_units: 最大显示单位数量 (仅对'full'和'short'有效)
        context: 上下文信息，用于增强日志记录

    Returns:
        格式化后的时间字符串

    Examples:
        >>> seconds_to_human_readable(3661)
        '1 hour, 1 minute'
        >>> seconds_to_human_readable(3661, format_type='short')
        '1h 1m'
        >>> seconds_to_human_readable(3661, format_type='iso')
        'PT1H1M1S'
    """
    log_context = context or {}
    function_name = "seconds_to_human_readable"

    if seconds < 0:
        logger.error(
            f"转换时间: 秒数不能为负数: {seconds}",
            extra={"function": function_name,
                   "seconds": seconds, **log_context},
        )
        raise ValueError("秒数不能为负数")

    # 检查格式类型
    valid_formats = ["full", "short", "iso"]
    if format_type not in valid_formats:
        logger.warning(
            f"转换时间: 无效的格式类型 '{format_type}'，使用默认值 'full'",
            extra={
                "function": function_name,
                "format_type": format_type,
                **log_context,
            },
        )
        format_type = "full"

    # ISO 8601 格式
    if format_type == "iso":
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        result = f"PT{int(hours)}H{int(minutes)}M{int(seconds)}S"

        logger.debug(
            f"转换时间: 将 {seconds} 秒转换为ISO格式 {result}",
            extra={
                "function": function_name,
                "seconds": seconds,
                "result": result,
                **log_context,
            },
        )
        return result

    # 时间单位定义
    time_divisions = [
        (60, "second", "seconds", "s"),
        (60, "minute", "minutes", "m"),
        (24, "hour", "hours", "h"),
        (7, "day", "days", "d"),
        (4.348, "week", "weeks", "w"),
        (12, "month", "months", "mo"),
        (float("inf"), "year", "years", "y"),
    ]

    # 计算每个单位的值
    result_values = []
    unit_count = 0
    current_seconds = float(seconds)

    for division, singular, plural, abbr in time_divisions:
        current_value = current_seconds % division
        current_seconds //= division

        if current_value > 0 or current_seconds == 0:
            # 根据格式类型选择单位表示
            if format_type == "full":
                unit_text = singular if current_value == 1 else plural
                result_values.insert(0, f"{int(current_value)} {unit_text}")
            else:  # short format
                result_values.insert(0, f"{int(current_value)}{abbr}")

            unit_count += 1

        if current_seconds == 0 or unit_count >= max_units:
            break

    # 拼接结果
    if format_type == "full":
        result = ", ".join(result_values[:max_units])
    else:  # short format
        result = " ".join(result_values[:max_units])

    logger.debug(
        f"转换时间: 将 {seconds} 秒转换为 {format_type} 格式 '{result}'",
        extra={
            "function": function_name,
            "seconds": seconds,
            "format_type": format_type,
            "result": result,
            **log_context,
        },
    )

    return result