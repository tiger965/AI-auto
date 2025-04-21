# -*- coding: utf-8 -*-
"""
字符串处理工具模块: string_utils
功能描述: 提供字符串处理、验证、转换等功能
版本: 1.0
创建日期: 2025-04-17
"""

import re
import random
import string
import unicodedata
import logging
from typing import Optional, List, Tuple, Union, Dict, Any

# 配置日志记录器
logger = logging.getLogger(__name__)


def is_empty_string(s: Optional[str]) -> bool:
    """
    检查字符串是否为空(None, '', 或只包含空白字符)

    Args:
        s: 要检查的字符串

    Returns:
        如果为空则返回True，否则返回False

    Examples:
        >>> is_empty_string(None)
        True
        >>> is_empty_string("")
        True
        >>> is_empty_string("  ")
        True
        >>> is_empty_string("Hello")
        False
    """
    return s is None or (isinstance(s, str) and s.strip() == "")


def trim_string(s: str) -> str:
    """
    移除字符串首尾的空白字符

    Args:
        s: 输入字符串

    Returns:
        处理后的字符串

    Examples:
        >>> trim_string("  Hello, World!  ")
        'Hello, World!'
    """
    if not isinstance(s, str):
        raise TypeError("输入必须是字符串类型")
    return s.strip()


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """
    截断字符串到指定长度，超过则添加后缀

    Args:
        s: 输入字符串
        max_length: 最大长度
        suffix: 超长时添加的后缀

    Returns:
        处理后的字符串

    Examples:
        >>> truncate_string("This is a long text", 10)
        'This is a...'
    """
    if not isinstance(s, str):
        raise TypeError("输入必须是字符串类型")

    if max_length < 0:
        raise ValueError("最大长度不能为负数")

    if len(s) <= max_length:
        return s

    # 确保有足够空间放置后缀
    if max_length <= len(suffix):
        return suffix[:max_length]

    truncated_length = max_length - len(suffix)
    return s[:truncated_length] + suffix


def normalize_string(s: str, form: str = "NFKC", remove_accents: bool = False) -> str:
    """
    标准化字符串，可选择去除重音符号

    Args:
        s: 输入字符串
        form: Unicode标准化形式，可选'NFC', 'NFKC', 'NFD', 'NFKD'
        remove_accents: 是否去除重音符号

    Returns:
        标准化后的字符串

    Examples:
        >>> normalize_string("café")
        'café'
        >>> normalize_string("café", remove_accents=True)
        'cafe'
    """
    if not isinstance(s, str):
        raise TypeError("输入必须是字符串类型")

    # 验证标准化形式
    valid_forms = ["NFC", "NFKC", "NFD", "NFKD"]
    if form not in valid_forms:
        raise ValueError(
            f"无效的标准化形式: {form}，有效值为: {', '.join(valid_forms)}"
        )

    # 进行Unicode标准化
    normalized = unicodedata.normalize(form, s)

    # 如果需要去除重音符号
    if remove_accents and form in ["NFD", "NFKD"]:
        # 去除所有组合用字符
        normalized = "".join(
            [c for c in normalized if not unicodedata.combining(c)])
    elif remove_accents:
        # 如果不是分解形式，先分解再去除重音符号
        normalized = unicodedata.normalize("NFD", normalized)
        normalized = "".join(
            [c for c in normalized if not unicodedata.combining(c)])

    return normalized


def generate_random_string(
    length: int,
    include_uppercase: bool = True,
    include_lowercase: bool = True,
    include_digits: bool = True,
    include_special: bool = False,
    exclude_chars: str = "",
) -> str:
    """
    生成指定长度的随机字符串

    Args:
        length: 字符串长度
        include_uppercase: 是否包含大写字母
        include_lowercase: 是否包含小写字母
        include_digits: 是否包含数字
        include_special: 是否包含特殊字符
        exclude_chars: 要排除的字符

    Returns:
        随机生成的字符串

    Examples:
        >>> generate_random_string(10)
        'aB3cD7eF9g'
        >>> generate_random_string(8, include_special=True)
        'a$3D!8f*'
    """
    if length < 0:
        raise ValueError("长度不能为负数")

    # 构建字符集
    charset = ""
    if include_uppercase:
        charset += string.ascii_uppercase
    if include_lowercase:
        charset += string.ascii_lowercase
    if include_digits:
        charset += string.digits
    if include_special:
        charset += string.punctuation

    # 排除指定字符
    if exclude_chars:
        charset = "".join([c for c in charset if c not in exclude_chars])

    if not charset:
        raise ValueError("没有可用于生成随机字符串的字符集")

    # 生成随机字符串
    try:
        return "".join(random.choice(charset) for _ in range(length))
    except Exception as e:
        logger.error(f"生成随机字符串时发生错误: {str(e)}")
        raise


def extract_between_delimiters(
    s: str, start_delimiter: str, end_delimiter: str, include_delimiters: bool = False
) -> List[str]:
    """
    提取两个定界符之间的所有内容

    Args:
        s: 输入字符串
        start_delimiter: 开始定界符
        end_delimiter: 结束定界符
        include_delimiters: 是否在结果中包含定界符

    Returns:
        包含所有匹配项的列表

    Examples:
        >>> extract_between_delimiters("Hello [world] and [Python]", "[", "]")
        ['world', 'Python']
        >>> extract_between_delimiters("<p>First</p><p>Second</p>", "<p>", "</p>", True)
        ['<p>First</p>', '<p>Second</p>']
    """
    if not isinstance(s, str):
        raise TypeError("输入必须是字符串类型")

    if not start_delimiter or not end_delimiter:
        raise ValueError("定界符不能为空")

    try:
        # 转义特殊字符以避免正则表达式错误
        escaped_start = re.escape(start_delimiter)
        escaped_end = re.escape(end_delimiter)

        # 构建正则表达式模式
        if include_delimiters:
            pattern = f"{escaped_start}.*?{escaped_end}"
        else:
            pattern = f"{escaped_start}(.*?){escaped_end}"

        # 查找所有匹配项
        matches = re.findall(pattern, s, re.DOTALL)

        return matches
    except Exception as e:
        logger.error(f"提取内容时发生错误: {str(e)}")
        raise


def count_words(s: str) -> int:
    """
    计算字符串中的单词数量

    Args:
        s: 输入字符串

    Returns:
        单词数量

    Examples:
        >>> count_words("Hello, world! This is a test.")
        6
    """
    if not isinstance(s, str):
        raise TypeError("输入必须是字符串类型")

    # 移除首尾空白
    s = s.strip()
    if not s:
        return 0

    # 使用空白字符分割并计数非空单词
    return len([word for word in re.split(r"\s+", s) if word])


def count_chars(
    s: str, ignore_spaces: bool = False, ignore_punctuation: bool = False
) -> int:
    """
    计算字符串中的字符数量

    Args:
        s: 输入字符串
        ignore_spaces: 是否忽略空格
        ignore_punctuation: 是否忽略标点符号

    Returns:
        字符数量

    Examples:
        >>> count_chars("Hello, world!")
        13
        >>> count_chars("Hello, world!", ignore_punctuation=True)
        11
    """
    if not isinstance(s, str):
        raise TypeError("输入必须是字符串类型")

    if not s:
        return 0

    # 创建要排除的字符列表
    excluded_chars = ""
    if ignore_spaces:
        excluded_chars += " \t\n\r\f\v"
    if ignore_punctuation:
        excluded_chars += string.punctuation

    # 如果有要排除的字符
    if excluded_chars:
        filtered_string = "".join([c for c in s if c not in excluded_chars])
        return len(filtered_string)

    return len(s)


def slugify(
    s: str,
    separator: str = "-",
    lowercase: bool = True,
    max_length: Optional[int] = None,
) -> str:
    """
    将字符串转换为slug格式(用于URL等)

    Args:
        s: 输入字符串
        separator: 分隔符
        lowercase: 是否转换为小写
        max_length: 最大长度，超过则截断

    Returns:
        slug格式的字符串

    Examples:
        >>> slugify("Hello, World!")
        'hello-world'
        >>> slugify("Привет, мир!", separator="_")
        'privet_mir'
    """
    if not isinstance(s, str):
        raise TypeError("输入必须是字符串类型")

    # 标准化字符串并去除重音
    s = normalize_string(s, form="NFKD", remove_accents=True)

    # 替换非字母数字字符为分隔符
    slug = re.sub(r"[^\w\s-]", "", s)

    # 替换空白为分隔符
    slug = re.sub(r"[\s_-]+", separator, slug)

    # 移除前后的分隔符
    slug = slug.strip(separator)

    # 转换为小写
    if lowercase:
        slug = slug.lower()

    # 截断到最大长度
    if max_length is not None and max_length > 0:
        slug = slug[:max_length].rstrip(separator)

    return slug


def to_camel_case(s: str, capitalize_first: bool = False) -> str:
    """
    将下划线或连字符分隔的字符串转换为驼峰命名格式

    Args:
        s: 输入字符串
        capitalize_first: 首字母是否大写(大驼峰/小驼峰)

    Returns:
        驼峰命名格式的字符串

    Examples:
        >>> to_camel_case("hello_world")
        'helloWorld'
        >>> to_camel_case("hello-world", capitalize_first=True)
        'HelloWorld'
    """
    if not isinstance(s, str):
        raise TypeError("输入必须是字符串类型")

    if not s:
        return s

    # 替换所有连字符为下划线以统一处理
    s = s.replace("-", "_")

    # 分割字符串
    components = s.split("_")

    # 处理第一个单词
    if capitalize_first:
        # 大驼峰
        result = "".join(word.title() for word in components)
    else:
        # 小驼峰
        result = components[0].lower() + "".join(
            word.title() for word in components[1:]
        )

    return result