# -*- coding: utf-8 -*-
"""
文件处理工具模块: file_utils
功能描述: 提供文件读写、目录管理、路径处理等功能
版本: 1.0
创建日期: 2025-04-17
"""

import os
import time
import shutil
import logging
import pathlib
from typing import List, Union, Optional, Any, Tuple, Dict, BinaryIO, TextIO

# 配置日志记录器
logger = logging.getLogger(__name__)

def read_file(
    file_path: str, 
    encoding: str = 'utf-8', 
    mode: str = 'r'
) -> Union[str, bytes]:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
        encoding: 文件编码，默认为'utf-8'
        mode: 读取模式，'r'为文本模式，'rb'为二进制模式
    
    Returns:
        文件内容，根据mode返回字符串或字节
    
    Raises:
        FileNotFoundError: 文件不存在
        IOError: 读取过程中发生IO错误
        UnicodeDecodeError: 编码错误
    
    Examples:
        >>> content = read_file('config.json')
        >>> binary_data = read_file('image.png', mode='rb')
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        if not os.path.isfile(file_path):
            raise ValueError(f"路径不是一个文件: {file_path}")
            
        with open(file_path, mode=mode, encoding=None if 'b' in mode else encoding) as f:
            content = f.read()
            logger.debug(f"成功读取文件: {file_path}")
            return content
            
    except FileNotFoundError as e:
        logger.error(f"文件不存在: {file_path}")
        raise
    except UnicodeDecodeError as e:
        logger.error(f"文件编码错误 {file_path}: {str(e)}")
        raise
    except IOError as e:
        logger.error(f"读取文件时发生IO错误 {file_path}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"读取文件时发生未预期错误 {file_path}: {str(e)}")
        raise

def write_file(
    file_path: str, 
    content: Union[str, bytes], 
    encoding: str = 'utf-8', 
    mode: str = 'w',
    create_dirs: bool = True
) -> bool:
    """
    写入内容到文件
    
    Args:
        file_path: 文件路径
        content: 要写入的内容
        encoding: 文件编码，默认为'utf-8'
        mode: 写入模式，'w'为覆盖写入，'a'为追加写入，加'b'为二进制模式
        create_dirs: 如果目录不存在，是否创建目录
    
    Returns:
        写入是否成功
    
    Raises:
        IOError: 写入过程中发生IO错误
        PermissionError: 没有写入权限
    
    Examples:
        >>> write_file('output.txt', 'Hello, World!')
        >>> write_file('data.bin', binary_data, mode='wb')
    """
    try:
        directory = os.path.dirname(file_path)
        
        # 如果目录不存在且create_dirs为True，创建目录
        if directory and not os.path.exists(directory):
            if create_dirs:
                os.makedirs(directory, exist_ok=True)
                logger.debug(f"创建目录: {directory}")
            else:
                raise FileNotFoundError(f"目录不存在: {directory}")
        
        with open(file_path, mode=mode, encoding=None if 'b' in mode else encoding) as f:
            f.write(content)
            logger.debug(f"成功写入文件: {file_path}")
            
        return True
        
    except PermissionError as e:
        logger.error(f"没有写入权限 {file_path}: {str(e)}")
        raise
    except IOError as e:
        logger.error(f"写入文件时发生IO错误 {file_path}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"写入文件时发生未预期错误 {file_path}: {str(e)}")
        raise

def ensure_directory_exists(directory: str) -> bool:
    """
    确保目录存在，如不存在则创建
    
    Args:
        directory: 目录路径
    
    Returns:
        目录是否存在或创建成功
    
    Raises:
        PermissionError: 没有创建目录的权限
    
    Examples:
        >>> ensure_directory_exists('data/processed')
    """
    try:
        if not directory:
            return False
            
        if os.path.exists(directory):
            if os.path.isdir(directory):
                logger.debug(f"目录已存在: {directory}")
                return True
            else:
                logger.error(f"路径存在但不是目录: {directory}")
                return False
        
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"成功创建目录: {directory}")
        return True
        
    except PermissionError as e:
        logger.error(f"没有创建目录的权限 {directory}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"创建目录时发生错误 {directory}: {str(e)}")
        raise
        
def list_files(
    directory: str, 
    extension: Optional[str] = None, 
    recursive: bool = False,
    full_path: bool = False
) -> List[str]:
    """
    列出目录中的文件
    
    Args:
        directory: 目录路径
        extension: 文件扩展名过滤（例如'.txt'，'.py'）
        recursive: 是否递归搜索子目录
        full_path: 是否返回完整路径
    
    Returns:
        文件列表
    
    Raises:
        FileNotFoundError: 目录不存在
        NotADirectoryError: 路径不是目录
    
    Examples:
        >>> list_files('/path/to/data')
        >>> list_files('/path/to/data', extension='.csv', recursive=True)
    """
    try:
        if not os.path.exists(directory):
            raise FileNotFoundError(f"目录不存在: {directory}")
            
        if not os.path.isdir(directory):
            raise NotADirectoryError(f"路径不是目录: {directory}")
            
        result = []
        
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    if extension is None or file.endswith(extension):
                        if full_path:
                            result.append(os.path.join(root, file))
                        else:
                            result.append(file)
        else:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path):
                    if extension is None or item.endswith(extension):
                        if full_path:
                            result.append(item_path)
                        else:
                            result.append(item)
        
        return result
        
    except FileNotFoundError:
        logger.error(f"目录不存在: {directory}")
        raise
    except NotADirectoryError:
        logger.error(f"路径不是目录: {directory}")
        raise
    except PermissionError as e:
        logger.error(f"没有读取目录的权限 {directory}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"列出文件时发生错误 {directory}: {str(e)}")
        raise

def get_file_extension(file_path: str) -> str:
    """
    获取文件扩展名
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件扩展名（带点，如'.txt'），如果没有扩展名则返回空字符串
    
    Examples:
        >>> get_file_extension('document.txt')
        '.txt'
        >>> get_file_extension('data.tar.gz')
        '.gz'
    """
    _, ext = os.path.splitext(file_path)
    return ext.lower()

def join_paths(*paths: str) -> str:
    """
    连接路径组件
    
    Args:
        *paths: 路径组件
    
    Returns:
        连接后的路径
    
    Examples:
        >>> join_paths('data', 'processed', 'output.csv')
        'data/processed/output.csv' # 在POSIX系统上
    """
    return os.path.join(*paths)

def is_valid_path(path: str) -> bool:
    """
    检查路径是否有效（语法上合法，不检查是否存在）
    
    Args:
        path: 要检查的路径
    
    Returns:
        路径是否有效
    
    Examples:
        >>> is_valid_path('data/file.txt')
        True
        >>> is_valid_path('invalid\\:*?"<>|')
        False # 在POSIX系统上可能返回True
    """
    try:
        pathlib.Path(path)
        return True
    except (TypeError, ValueError):
        return False

def get_file_size(file_path: str, human_readable: bool = False) -> Union[int, str]:
    """
    获取文件大小
    
    Args:
        file_path: 文件路径
        human_readable: 是否以人类可读格式返回（如 '1.5 MB'）
    
    Returns:
        文件大小（字节数或人类可读字符串）
    
    Raises:
        FileNotFoundError: 文件不存在
        
    Examples:
        >>> get_file_size('large_file.zip')
        1048576
        >>> get_file_size('large_file.zip', human_readable=True)
        '1.0 MB'
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
        
    if not os.path.isfile(file_path):
        raise ValueError(f"路径不是一个文件: {file_path}")
        
    size_bytes = os.path.getsize(file_path)
    
    if human_readable:
        return bytes_to_human_readable(size_bytes)
    return size_bytes

def get_file_creation_time(file_path: str, format: Optional[str] = None) -> Union[float, str]:
    """
    获取文件创建时间
    
    Args:
        file_path: 文件路径
        format: 时间格式化字符串，如果为None则返回时间戳
    
    Returns:
        文件创建时间（时间戳或格式化字符串）
    
    Raises:
        FileNotFoundError: 文件不存在
        
    Examples:
        >>> get_file_creation_time('document.txt')
        1648156956.123
        >>> get_file_creation_time('document.txt', format='%Y-%m-%d %H:%M:%S')
        '2022-03-24 15:35:56'
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 获取创建时间，不同系统有不同的属性
    if hasattr(os.path, 'getctime'):
        creation_time = os.path.getctime(file_path)
    else:
        # 在不支持创建时间的系统上，使用修改时间作为替代
        creation_time = os.path.getmtime(file_path)
    
    if format:
        return time.strftime(format, time.localtime(creation_time))
    return creation_time

def get_file_modification_time(file_path: str, format: Optional[str] = None) -> Union[float, str]:
    """
    获取文件最后修改时间
    
    Args:
        file_path: 文件路径
        format: 时间格式化字符串，如果为None则返回时间戳
    
    Returns:
        文件最后修改时间（时间戳或格式化字符串）
    
    Raises:
        FileNotFoundError: 文件不存在
        
    Examples:
        >>> get_file_modification_time('document.txt')
        1648156956.123
        >>> get_file_modification_time('document.txt', format='%Y-%m-%d %H:%M:%S')
        '2022-03-24 15:35:56'
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    modification_time = os.path.getmtime(file_path)
    
    if format:
        return time.strftime(format, time.localtime(modification_time))
    return modification_time

def bytes_to_human_readable(size_bytes: int) -> str:
    """
    将字节大小转换为人类可读格式
    
    Args:
        size_bytes: 字节大小
    
    Returns:
        格式化后的字符串 (如 '1.5 MB')
    
    Examples:
        >>> bytes_to_human_readable(1500)
        '1.5 KB'
    """
    if size_bytes < 0:
        raise ValueError("字节大小不能为负数")
        
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    size = float(size_bytes)
    unit_index = 0
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"