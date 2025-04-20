# -*- coding: utf-8 -*-
"""
实用工具模块: utils
功能描述: 提供文件处理、字符串操作、数据验证和转换等通用功能
版本: 1.0
创建日期: 2025-04-17
"""

from .file_utils import (
    read_file,
    write_file,
    ensure_directory_exists,
    list_files,
    get_file_extension,
    join_paths,
    is_valid_path,
    get_file_size,
    get_file_creation_time,
    get_file_modification_time
)

from .string_utils import (
    is_empty_string,
    trim_string,
    truncate_string,
    normalize_string,
    generate_random_string,
    extract_between_delimiters,
    count_words,
    count_chars,
    slugify,
    to_camel_case
)

from .validation import (
    is_valid_email,
    is_valid_url,
    is_valid_ip,
    is_valid_phone_number,
    is_numeric,
    is_alphanumeric,
    validate_length,
    validate_range,
    validate_format,
    ValidationError
)

from .converters import (
    to_int,
    to_float,
    to_bool,
    to_string,
    to_date,
    to_datetime,
    to_list,
    to_dict,
    bytes_to_human_readable,
    seconds_to_human_readable
)

__all__ = [
    # file_utils
    'read_file', 'write_file', 'ensure_directory_exists', 'list_files',
    'get_file_extension', 'join_paths', 'is_valid_path', 'get_file_size',
    'get_file_creation_time', 'get_file_modification_time',
    
    # string_utils
    'is_empty_string', 'trim_string', 'truncate_string', 'normalize_string',
    'generate_random_string', 'extract_between_delimiters', 'count_words',
    'count_chars', 'slugify', 'to_camel_case',
    
    # validation
    'is_valid_email', 'is_valid_url', 'is_valid_ip', 'is_valid_phone_number',
    'is_numeric', 'is_alphanumeric', 'validate_length', 'validate_range',
    'validate_format', 'ValidationError',
    
    # converters
    'to_int', 'to_float', 'to_bool', 'to_string', 'to_date', 'to_datetime',
    'to_list', 'to_dict', 'bytes_to_human_readable', 'seconds_to_human_readable'
]