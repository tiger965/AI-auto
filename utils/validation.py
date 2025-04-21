# -*- coding: utf-8 -*-
"""
数据验证工具模块: validation
功能描述: 提供各种数据验证和检查功能
版本: 1.0
创建日期: 2025-04-17
"""

import re
import logging
from typing import Any, Union, Dict, List, Tuple, Optional, Callable

# 配置日志记录器
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """
    验证错误异常类

    用于在验证失败时抛出的异常，可包含字段名和错误信息。
    """

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        self.message = message
        super().__init__(self.full_message)

    @property
    def full_message(self) -> str:
        """获取完整的错误信息，包含字段名（如果有）"""
        if self.field:
            return f"验证错误 [{self.field}]: {self.message}"
        return f"验证错误: {self.message}"


def is_valid_email(email: str) -> bool:
    """
    验证字符串是否为有效的电子邮件格式

    Args:
        email: 要验证的电子邮件地址

    Returns:
        是否为有效的电子邮件格式

    Examples:
        >>> is_valid_email("user@example.com")
        True
        >>> is_valid_email("invalid-email")
        False
    """
    if not isinstance(email, str):
        return False

    # RFC 5322 标准的电子邮件正则表达式
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_url(
    url: str,
    require_protocol: bool = True,
    allowed_protocols: Optional[List[str]] = None,
) -> bool:
    """
    验证字符串是否为有效的URL

    Args:
        url: 要验证的URL
        require_protocol: 是否要求包含协议（http://, https://等）
        allowed_protocols: 允许的协议列表，默认为['http', 'https']

    Returns:
        是否为有效的URL

    Examples:
        >>> is_valid_url("https://www.example.com")
        True
        >>> is_valid_url("example.com", require_protocol=False)
        True
    """
    if not isinstance(url, str):
        return False

    if not url:
        return False

    # 默认允许的协议
    if allowed_protocols is None:
        allowed_protocols = ["http", "https"]

    # 构建正则表达式
    if require_protocol:
        protocols_pattern = "|".join(allowed_protocols)
        pattern = f"^({protocols_pattern})://([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\\.)+[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(:[0-9]+)?(/[^\\s]*)?$"
    else:
        pattern = "^(([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\\.)+[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(:[0-9]+)?(/[^\\s]*)?|((http|https)://([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\\.)+[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(:[0-9]+)?(/[^\\s]*)?)?)$"

    return bool(re.match(pattern, url))


def is_valid_ip(ip: str, version: Optional[int] = None) -> bool:
    """
    验证字符串是否为有效的IP地址

    Args:
        ip: 要验证的IP地址
        version: IP版本，4表示IPv4，6表示IPv6，None表示两者都可以

    Returns:
        是否为有效的IP地址

    Examples:
        >>> is_valid_ip("192.168.1.1")
        True
        >>> is_valid_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334", version=6)
        True
    """
    if not isinstance(ip, str):
        return False

    # IPv4验证
    def is_ipv4(ip_str: str) -> bool:
        try:
            parts = ip_str.split(".")
            if len(parts) != 4:
                return False

            for part in parts:
                if not part.isdigit():
                    return False
                num = int(part)
                if num < 0 or num > 255:
                    return False
            return True
        except (ValueError, AttributeError):
            return False

    # IPv6验证
    def is_ipv6(ip_str: str) -> bool:
        try:
            parts = ip_str.split(":")
            if len(parts) > 8:
                return False

            # 检查是否有空部分（双冒号缩写）
            if ip_str.count("::") > 1:
                return False

            # 验证每个部分
            for part in parts:
                if part == "":
                    continue
                if len(part) > 4:
                    return False
                int(part, 16)  # 尝试将部分解析为十六进制
            return True
        except (ValueError, AttributeError):
            return False

    # 根据指定版本验证
    if version == 4:
        return is_ipv4(ip)
    elif version == 6:
        return is_ipv6(ip)
    else:
        return is_ipv4(ip) or is_ipv6(ip)


def is_valid_phone_number(
    phone: str, country_code: Optional[str] = None, strict: bool = False
) -> bool:
    """
    验证字符串是否为有效的电话号码

    Args:
        phone: 要验证的电话号码
        country_code: 国家/地区代码 (如 'US', 'CN')，用于特定格式验证
        strict: 是否使用严格验证模式

    Returns:
        是否为有效的电话号码

    Examples:
        >>> is_valid_phone_number("+1-555-123-4567")
        True
        >>> is_valid_phone_number("13800138000", country_code="CN")
        True
    """
    if not isinstance(phone, str):
        return False

    # 清理电话号码，移除非数字字符
    cleaned = re.sub(r"[^\d+]", "", phone)

    # 基本验证：只检查长度和可能的国际前缀
    if not strict:
        # 简单验证：至少有7个数字，可能以+开头
        return bool(re.match(r"^\+?[\d]{7,15}$", cleaned))

    # 针对特定国家/地区的严格验证
    if country_code:
        country_code = country_code.upper()

        # 中国大陆手机号
        if country_code == "CN":
            return bool(re.match(r"^(?:\+86)?1[3-9]\d{9}$", cleaned))

        # 美国/加拿大电话号码
        elif country_code in ["US", "CA"]:
            return bool(re.match(r"^(?:\+1)?[2-9]\d{2}[2-9]\d{6}$", cleaned))

        # 更多国家/地区可根据需要添加

    # 默认使用E.164格式检查，允许最多15位数字，以+开头
    return bool(re.match(r"^\+[1-9]\d{1,14}$", cleaned))


def is_numeric(value: Any) -> bool:
    """
    检查值是否为数值或可转换为数值

    Args:
        value: 要检查的值

    Returns:
        是否为数值或可转换为数值

    Examples:
        >>> is_numeric(123)
        True
        >>> is_numeric("123")
        True
        >>> is_numeric("abc")
        False
    """
    # 如果是数值类型，直接返回True
    if isinstance(value, (int, float)):
        return True

    # 如果是字符串，尝试转换
    if isinstance(value, str):
        # 处理空字符串
        if not value.strip():
            return False

        # 尝试转换为浮点数
        try:
            float(value)
            return True
        except ValueError:
            return False

    # 其他类型尝试转换
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def is_alphanumeric(
    value: str, allow_spaces: bool = False, allow_underscore: bool = False
) -> bool:
    """
    检查字符串是否只包含字母和数字（可选择允许空格和下划线）

    Args:
        value: 要检查的字符串
        allow_spaces: 是否允许空格
        allow_underscore: 是否允许下划线

    Returns:
        是否只包含允许的字符

    Examples:
        >>> is_alphanumeric("abc123")
        True
        >>> is_alphanumeric("abc 123", allow_spaces=True)
        True
    """
    if not isinstance(value, str):
        return False

    if not value:
        return False

    # 构建正则表达式模式
    pattern = r"^[a-zA-Z0-9"
    if allow_spaces:
        pattern += r" "
    if allow_underscore:
        pattern += r"_"
    pattern += r"]+$"

    return bool(re.match(pattern, value))


def validate_length(
    value: Union[str, List, Dict, Tuple],
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    field_name: Optional[str] = None,
    raise_exception: bool = False,
) -> bool:
    """
    验证值的长度是否在指定范围内

    Args:
        value: 要验证的值（字符串、列表、字典或元组）
        min_length: 最小长度，None表示不限制
        max_length: 最大长度，None表示不限制
        field_name: 字段名称，用于错误消息
        raise_exception: 验证失败时是否抛出异常

    Returns:
        长度是否在指定范围内

    Raises:
        ValidationError: 验证失败且raise_exception为True时抛出

    Examples:
        >>> validate_length("abc", min_length=2, max_length=5)
        True
        >>> validate_length([1, 2, 3], max_length=2)
        False
    """
    if not hasattr(value, "__len__"):
        if raise_exception:
            raise ValidationError("值不支持长度验证", field_name)
        return False

    length = len(value)

    # 检查最小长度
    if min_length is not None and length < min_length:
        if raise_exception:
            message = f"长度应不小于{min_length}，当前长度为{length}"
            raise ValidationError(message, field_name)
        return False

    # 检查最大长度
    if max_length is not None and length > max_length:
        if raise_exception:
            message = f"长度应不大于{max_length}，当前长度为{length}"
            raise ValidationError(message, field_name)
        return False

    return True


def validate_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    inclusive: bool = True,
    field_name: Optional[str] = None,
    raise_exception: bool = False,
) -> bool:
    """
    验证数值是否在指定范围内

    Args:
        value: 要验证的数值
        min_value: 最小值，None表示不限制
        max_value: 最大值，None表示不限制
        inclusive: 是否包含边界值
        field_name: 字段名称，用于错误消息
        raise_exception: 验证失败时是否抛出异常

    Returns:
        值是否在指定范围内

    Raises:
        ValidationError: 验证失败且raise_exception为True时抛出
        TypeError: 值不是数值类型且raise_exception为True时抛出

    Examples:
        >>> validate_range(5, min_value=1, max_value=10)
        True
        >>> validate_range(10, min_value=1, max_value=10, inclusive=False)
        False
    """
    # 检查类型
    if not isinstance(value, (int, float)):
        if raise_exception:
            raise TypeError(f"值应为数值类型，当前类型为{type(value).__name__}")
        return False

    # 检查最小值
    if min_value is not None:
        if inclusive and value < min_value:
            if raise_exception:
                message = f"值应大于或等于{min_value}，当前值为{value}"
                raise ValidationError(message, field_name)
            return False
        elif not inclusive and value <= min_value:
            if raise_exception:
                message = f"值应大于{min_value}，当前值为{value}"
                raise ValidationError(message, field_name)
            return False

    # 检查最大值
    if max_value is not None:
        if inclusive and value > max_value:
            if raise_exception:
                message = f"值应小于或等于{max_value}，当前值为{value}"
                raise ValidationError(message, field_name)
            return False
        elif not inclusive and value >= max_value:
            if raise_exception:
                message = f"值应小于{max_value}，当前值为{value}"
                raise ValidationError(message, field_name)
            return False

    return True


def validate_format(
    value: str,
    pattern: str,
    field_name: Optional[str] = None,
    error_message: Optional[str] = None,
    raise_exception: bool = False,
) -> bool:
    """
    根据正则表达式验证字符串格式

    Args:
        value: 要验证的字符串
        pattern: 正则表达式模式
        field_name: 字段名称，用于错误消息
        error_message: 自定义错误消息
        raise_exception: 验证失败时是否抛出异常

    Returns:
        字符串是否匹配指定模式

    Raises:
        ValidationError: 验证失败且raise_exception为True时抛出

    Examples:
        >>> validate_format("ABC123", r'^[A-Z]+[0-9]+$')
        True
        >>> validate_format("abc123", r'^[A-Z]+[0-9]+$')
        False
    """
    # 检查类型
    if not isinstance(value, str):
        if raise_exception:
            raise TypeError(f"值应为字符串类型，当前类型为{type(value).__name__}")
        return False

    # 执行正则表达式匹配
    if not re.match(pattern, value):
        if raise_exception:
            message = error_message or f"值不符合指定格式模式: {pattern}"
            raise ValidationError(message, field_name)
        return False

    return True