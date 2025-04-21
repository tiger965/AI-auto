# -*- coding: utf-8 -*-
"""
数据模块: 数据加载器
功能描述: 提供统一的数据加载接口，支持多种数据格式
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-17
"""

from .. config.config_loader import ConfigLoader
import api
import config.paths as pd
import os
import io
import re
import json
import logging
import hashlib
import tempfile
import mimetypes
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, BinaryIO, Callable
from dataclasses import dataclass
from collections import OrderedDict
from urllib.parse import urlparse

# 尝试导入可选依赖
try:
import modules.nlp as np
NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import xml.etree.ElementTree as ET
    XML_AVAILABLE = True
except ImportError:
    XML_AVAILABLE = False

# 从配置加载器获取配置
try:
config_loader = ConfigLoader()
LOADER_CONFIG = config_loader.load("modules.data.data_loader")
except ImportError:
    LOADER_CONFIG = {
        "cache_enabled": True,
        "cache_size": 100,
        "default_format": "auto"
    }

# 初始化日志记录器
logger = logging.getLogger(__name__)


@dataclass
class LoaderConfig:
    """数据加载器配置类"""

    format: str = "auto"  # 数据格式: auto, csv, json, xml, yaml, excel, text, binary
    encoding: str = "utf-8"  # 文本编码
    cache_enabled: bool = True  # 是否启用缓存
    cache_size: int = 100  # 缓存大小
    headers: Optional[Dict[str, str]] = None  # HTTP请求头
    timeout: int = 30  # HTTP请求超时时间（秒）
    delimiter: str = ","  # CSV分隔符
    sheet_name: Optional[Union[str, int]] = 0  # Excel表名称或索引

    def __post_init__(self):
        """数据校验和默认值设置"""
        valid_formats = ["auto", "csv", "json", "xml", "yaml", "excel",
                         "text", "binary", "parquet", "feather", "pickle", "hdf5", "sql"]
        if self.format not in valid_formats:
            logger.warning(f"无效的数据格式: {self.format}，使用默认格式: auto")
            self.format = "auto"

        # 确保cache_size为正整数
        if self.cache_size <= 0:
            logger.warning(f"无效的缓存大小: {self.cache_size}，使用默认值: 100")
            self.cache_size = 100

        # 确保timeout为正整数
        if self.timeout <= 0:
            logger.warning(f"无效的超时时间: {self.timeout}，使用默认值: 30")
            self.timeout = 30

        # 初始化HTTP请求头
        if self.headers is None:
            self.headers = {
                "User-Agent": "AI-Data-Loader/1.0.0"
            }


class DataLoader:
    """数据加载器类"""

    def __init__(self, config: Optional[Union[Dict[str, Any], LoaderConfig]] = None):
        """
        初始化数据加载器

        参数:
            config: 加载器配置，可以是LoaderConfig实例或字典
        """
        if config is None:
            self.config = LoaderConfig(**LOADER_CONFIG)
        elif isinstance(config, dict):
            self.config = LoaderConfig(**config)
        else:
            self.config = config

        # 初始化数据缓存
        self.cache = OrderedDict()
        self.temp_dir = None

        # 注册数据加载处理器
        self.format_handlers = {
            "csv": self._load_csv,
            "json": self._load_json,
            "xml": self._load_xml,
            "yaml": self._load_yaml,
            "excel": self._load_excel,
            "text": self._load_text,
            "binary": self._load_binary,
            "parquet": self._load_parquet,
            "feather": self._load_feather,
            "pickle": self._load_pickle,
            "hdf5": self._load_hdf5,
            "sql": self._load_sql
        }

        logger.info(f"数据加载器初始化，默认格式: {self.config.format}")

    def _ensure_temp_dir(self):
        """确保临时目录存在"""
        if self.temp_dir is None:
            from tempfile import mkdtemp
            self.temp_dir = mkdtemp(prefix="data_loader_")
            logger.info(f"创建数据加载临时目录: {self.temp_dir}")

    def _add_to_cache(self, key: str, data: Any):
        """
        将数据添加到缓存

        参数:
            key: 缓存键
            data: 数据
        """
        if not self.config.cache_enabled:
            return

        # 限制缓存大小
        if len(self.cache) >= self.config.cache_size:
            self.cache.popitem(last=False)  # 移除最早添加的项

        self.cache[key] = data

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """
        从缓存获取数据

        参数:
            key: 缓存键

        返回:
            缓存的数据，如果不存在则返回None
        """
        if not self.config.cache_enabled or key not in self.cache:
            return None

        # 移动到末尾（最近使用）
        value = self.cache.pop(key)
        self.cache[key] = value
        return value

    def load(self,
             data_source: Union[str, Path, BinaryIO, Dict[str, Any], List[Any]],
             format: Optional[str] = None,
             cache_key: Optional[str] = None,
             **kwargs) -> Any:
        """
        加载数据

        参数:
            data_source: 数据源，可以是文件路径、URL、文件对象、字典或列表
            format: 数据格式，如果为None则使用配置中的默认值或自动检测
            cache_key: 可选的缓存键，如果为None则自动生成
            **kwargs: 其他参数，将覆盖配置中的对应值

        返回:
            加载的数据
        """
        # 处理格式参数
        if format is None:
            format = self.config.format

        # 处理缓存键
        if cache_key is None:
            if isinstance(data_source, (str, Path)):
                cache_key = str(data_source)
            else:
                # 为非字符串数据源创建哈希值作为缓存键
                cache_key = self._generate_cache_key(data_source)

        # 检查缓存
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # 处理内存中的数据
        if isinstance(data_source, (dict, list)):
            return data_source

        # 加载数据
        data = self._load_data(data_source, format, **kwargs)

        # 添加到缓存
        self._add_to_cache(cache_key, data)

        return data

    def _generate_cache_key(self, data_source: Any) -> str:
        """
        为数据源生成缓存键

        参数:
            data_source: 数据源

        返回:
            缓存键
        """
        if isinstance(data_source, (str, Path)):
            return str(data_source)
        elif hasattr(data_source, 'name') and isinstance(data_source.name, str):
            return data_source.name
        else:
            # 为对象创建唯一ID
            # 注意：这种方法不是真正持久的，但对于会话内缓存已足够
            obj_id = id(data_source)
            return f"obj_{obj_id}"

    def _load_data(self,
                   data_source: Union[str, Path, BinaryIO],
                   format: str,
                   **kwargs) -> Any:
        """
        从数据源加载数据

        参数:
            data_source: 数据源
            format: 数据格式
            **kwargs: 其他参数

        返回:
            加载的数据
        """
        # 合并配置和参数
        loader_config = {k: v for k, v in vars(self.config).items()}
        loader_config.update(kwargs)

        # 如果是URL，先下载
        if isinstance(data_source, str) and (data_source.startswith(('http://', 'https://'))):
            data_source = self._download_file(data_source, loader_config)
            if data_source is None:
                return None

        # 如果是文件路径，转换为文件对象
        if isinstance(data_source, (str, Path)):
            try:
                path = str(data_source)
                if not os.path.exists(path):
                    logger.error(f"文件路径不存在: {path}")
                    return None

                # 自动检测格式（如果需要）
                if format == "auto":
                    format = self._detect_format(path)

                # 二进制模式打开还是文本模式打开
                if format in ["binary", "excel", "parquet", "feather", "pickle", "hdf5"]:
                    mode = "rb"
                else:
                    mode = "r"

                with open(path, mode, encoding=loader_config["encoding"] if mode == "r" else None) as f:
                    return self._process_data(f, format, loader_config)

            except Exception as e:
                logger.error(f"加载文件失败: {str(e)}")
                return None

        # 如果是文件对象，直接处理
        elif hasattr(data_source, 'read') and callable(data_source.read):
            # 自动检测格式（如果需要）
            if format == "auto":
                if hasattr(data_source, 'name') and isinstance(data_source.name, str):
                    format = self._detect_format(data_source.name)
                else:
                    # 无法自动检测，使用默认的JSON
                    format = "json"

            return self._process_data(data_source, format, loader_config)

        else:
            logger.error(f"不支持的数据源类型: {type(data_source)}")
            return None

    def _download_file(self, url: str, config: Dict[str, Any]) -> Optional[str]:
        """
        下载文件到临时目录

        参数:
            url: 文件URL
            config: 加载配置

        返回:
            临时文件路径，如果下载失败则返回None
        """
        if not REQUESTS_AVAILABLE:
            logger.error("requests库未安装，无法下载文件")
            return None

        try:
            # 确保临时目录存在
            self._ensure_temp_dir()

            # 从URL中提取文件名
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)

            if not filename:
                # 使用URL的哈希值作为文件名
                filename = hashlib.md5(url.encode('utf-8')).hexdigest()

            # 创建临时文件路径
            temp_path = os.path.join(self.temp_dir, filename)

            # 下载文件
            response = requests.get(
                url,
                headers=config["headers"],
                timeout=config["timeout"],
                stream=True
            )
            response.raise_for_status()

            # 获取内容类型和文件扩展名
            content_type = response.headers.get('Content-Type', '')
            extension = mimetypes.guess_extension(content_type)

            # 如果没有扩展名但有内容类型，添加扩展名
            if extension and not temp_path.endswith(extension):
                temp_path += extension

            # 保存文件
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"文件已下载到: {temp_path}")
            return temp_path

        except Exception as e:
            logger.error(f"下载文件失败: {str(e)}")
            return None

    def _detect_format(self, file_path: str) -> str:
        """
        根据文件路径或内容检测数据格式

        参数:
            file_path: 文件路径

        返回:
            检测到的数据格式
        """
        # 根据文件扩展名检测
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()

        format_mapping = {
            '.csv': 'csv',
            '.tsv': 'csv',  # TSV也使用CSV加载器，但需要指定分隔符
            '.json': 'json',
            '.xml': 'xml',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.xls': 'excel',
            '.xlsx': 'excel',
            '.txt': 'text',
            '.log': 'text',
            '.md': 'text',
            '.parquet': 'parquet',
            '.feather': 'feather',
            '.pkl': 'pickle',
            '.pickle': 'pickle',
            '.h5': 'hdf5',
            '.hdf5': 'hdf5',
            '.sql': 'sql'
        }

        # 返回匹配的格式或默认值
        return format_mapping.get(extension, 'text')

    def _process_data(self,
                      data_source: BinaryIO,
                      format: str,
                      config: Dict[str, Any]) -> Any:
        """
        处理数据源

        参数:
            data_source: 数据源文件对象
            format: 数据格式
            config: 加载配置

        返回:
            处理后的数据
        """
        # 获取相应格式的处理器
        handler = self.format_handlers.get(format)

        if handler:
            return handler(data_source, config)
        else:
            logger.error(f"不支持的数据格式: {format}")
            return None

    def _load_csv(self, file_obj: BinaryIO, config: Dict[str, Any]) -> Any:
        """
        加载CSV数据

        参数:
            file_obj: 文件对象
            config: 加载配置

        返回:
            加载的CSV数据
        """
        if not PANDAS_AVAILABLE:
            logger.warning("pandas库未安装，将以文本方式加载CSV")
            return self._load_text(file_obj, config)

        try:
            # 准备pandas读取参数
            pd_kwargs = {
                'delimiter': config.get('delimiter', ','),
                'encoding': config.get('encoding', 'utf-8')
            }

            # 添加可选参数
            if 'header' in config:
                pd_kwargs['header'] = config['header']
            if 'index_col' in config:
                pd_kwargs['index_col'] = config['index_col']
            if 'usecols' in config:
                pd_kwargs['usecols'] = config['usecols']
            if 'dtype' in config:
                pd_kwargs['dtype'] = config['dtype']
            if 'skiprows' in config:
                pd_kwargs['skiprows'] = config['skiprows']

            # 读取CSV
            if hasattr(file_obj, 'name') and isinstance(file_obj.name, str):
                # 如果有文件名，直接使用文件路径更高效
                return pd.read_csv(file_obj.name, **pd_kwargs)
            else:
                # 否则使用文件对象
                return pd.read_csv(file_obj, **pd_kwargs)

        except Exception as e:
            logger.error(f"加载CSV失败: {str(e)}")
            return None

    def _load_json(self, file_obj: BinaryIO, config: Dict[str, Any]) -> Any:
        """
        加载JSON数据

        参数:
            file_obj: 文件对象
            config: 加载配置

        返回:
            加载的JSON数据
        """
        try:
            # 直接使用json模块加载
            if hasattr(file_obj, 'read'):
                # 如果是文件对象，读取内容
                text = file_obj.read()
                if isinstance(text, bytes):
                    text = text.decode(config.get('encoding', 'utf-8'))

                return json.loads(text)
            else:
                # 如果已经是字符串，直接加载
                return json.loads(file_obj)

        except Exception as e:
            logger.error(f"加载JSON失败: {str(e)}")
            return None

    def _load_xml(self, file_obj: BinaryIO, config: Dict[str, Any]) -> Any:
        """
        加载XML数据

        参数:
            file_obj: 文件对象
            config: 加载配置

        返回:
            加载的XML数据
        """
        if not XML_AVAILABLE:
            logger.error("xml模块不可用，无法加载XML")
            return None

        try:
            # 解析XML
            tree = ET.parse(file_obj)
            root = tree.getroot()

            # 转换为字典
            return self._xml_to_dict(root)

        except Exception as e:
            logger.error(f"加载XML失败: {str(e)}")
            return None

    def _xml_to_dict(self, element: ET.Element) -> Union[Dict[str, Any], List[Any], str]:
        """
        将XML元素转换为字典

        参数:
            element: XML元素

        返回:
            转换后的数据结构
        """
        # 处理简单元素
        if len(element) == 0:
            text = element.text
            if text is None:
                return {}
            else:
                return text.strip()

        # 处理复杂元素
        result = {}

        # 处理属性
        if element.attrib:
            result["@attributes"] = element.attrib

        # 处理子元素
        for child in element:
            child_data = self._xml_to_dict(child)

            # 如果已存在同名元素，将其转换为列表
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data

        return result

    def _load_yaml(self, file_obj: BinaryIO, config: Dict[str, Any]) -> Any:
        """
        加载YAML数据

        参数:
            file_obj: 文件对象
            config: 加载配置

        返回:
            加载的YAML数据
        """
        if not YAML_AVAILABLE:
            logger.error("yaml模块未安装，无法加载YAML")
            return None

        try:
            # 读取YAML
            return yaml.safe_load(file_obj)

        except Exception as e:
            logger.error(f"加载YAML失败: {str(e)}")
            return None

    def _load_excel(self, file_obj: BinaryIO, config: Dict[str, Any]) -> Any:
        """
        加载Excel数据

        参数:
            file_obj: 文件对象
            config: 加载配置

        返回:
            加载的Excel数据
        """
        if not PANDAS_AVAILABLE:
            logger.error("pandas库未安装，无法加载Excel")
            return None

        try:
            # 准备pandas读取参数
            pd_kwargs = {}

            # 设置表名
            sheet_name = config.get('sheet_name', 0)
            pd_kwargs['sheet_name'] = sheet_name

            # 添加可选参数
            if 'header' in config:
                pd_kwargs['header'] = config['header']
            if 'index_col' in config:
                pd_kwargs['index_col'] = config['index_col']
            if 'usecols' in config:
                pd_kwargs['usecols'] = config['usecols']
            if 'dtype' in config:
                pd_kwargs['dtype'] = config['dtype']
            if 'skiprows' in config:
                pd_kwargs['skiprows'] = config['skiprows']

            # 读取Excel
            if hasattr(file_obj, 'name') and isinstance(file_obj.name, str):
                # 如果有文件名，直接使用文件路径更高效
                return pd.read_excel(file_obj.name, **pd_kwargs)
            else:
                # 否则使用文件对象
                return pd.read_excel(file_obj, **pd_kwargs)

        except Exception as e:
            logger.error(f"加载Excel失败: {str(e)}")
            return None

    def _load_text(self, file_obj: BinaryIO, config: Dict[str, Any]) -> Any:
        """
        加载文本数据

        参数:
            file_obj: 文件对象
            config: 加载配置

        返回:
            加载的文本数据
        """
        try:
            # 读取文本
            if hasattr(file_obj, 'read'):
                # 如果是文件对象，读取内容
                text = file_obj.read()
                if isinstance(text, bytes):
                    text = text.decode(config.get('encoding', 'utf-8'))
                return text
            else:
                # 如果已经是字符串，直接返回
                return file_obj

        except Exception as e:
            logger.error(f"加载文本失败: {str(e)}")
            return None

    def _load_binary(self, file_obj: BinaryIO, config: Dict[str, Any]) -> Any:
        """
        加载二进制数据

        参数:
            file_obj: 文件对象
            config: 加载配置

        返回:
            加载的二进制数据
        """
        try:
            # 读取二进制数据
            if hasattr(file_obj, 'read'):
                # 如果是文件对象，读取内容
                data = file_obj.read()
                if not isinstance(data, bytes):
                    # 如果不是二进制，尝试编码
                    data = data.encode(config.get('encoding', 'utf-8'))
                return data
            else:
                # 如果已经是二进制数据，直接返回
                return file_obj

        except Exception as e:
            logger.error(f"加载二进制数据失败: {str(e)}")
            return None

    def _load_parquet(self, file_obj: BinaryIO, config: Dict[str, Any]) -> Any:
        """
        加载Parquet数据

        参数:
            file_obj: 文件对象
            config: 加载配置

        返回:
            加载的Parquet数据
        """
        if not PANDAS_AVAILABLE:
            logger.error("pandas库未安装，无法加载Parquet")
            return None

        try:
            # 检查是否安装了pyarrow或fastparquet
            import importlib
            parquet_engine = None

            if importlib.util.find_spec("pyarrow"):
                parquet_engine = "pyarrow"
            elif importlib.util.find_spec("fastparquet"):
                parquet_engine = "fastparquet"
            else:
                logger.error("找不到Parquet引擎（pyarrow或fastparquet），无法加载Parquet")
                return None

            # 准备pandas读取参数
            pd_kwargs = {
                'engine': parquet_engine
            }

            # 添加可选参数
            if 'columns' in config:
                pd_kwargs['columns'] = config['columns']

            # 读取Parquet
            if hasattr(file_obj, 'name') and isinstance(file_obj.name, str):
                # 如果有文件名，直接使用文件路径更高效
                return pd.read_parquet(file_obj.name, **pd_kwargs)
            else:
                # 否则使用文件对象
                return pd.read_parquet(file_obj, **pd_kwargs)

        except Exception as e:
            logger.error(f"加载Parquet失败: {str(e)}")
            return None

    def _load_feather(self, file_obj: BinaryIO, config: Dict[str, Any]) -> Any:
        """
        加载Feather数据

        参数:
            file_obj: 文件对象
            config: 加载配置

        返回:
            加载的Feather数据
        """
        if not PANDAS_AVAILABLE:
            logger.error("pandas库未安装，无法加载Feather")
            return None

        try:
            # 检查是否安装了pyarrow
            import importlib
            if not importlib.util.find_spec("pyarrow"):
                logger.error("pyarrow库未安装，无法加载Feather")
                return None

            # 准备pandas读取参数
            pd_kwargs = {}

            # 添加可选参数
            if 'columns' in config:
                pd_kwargs['columns'] = config['columns']

            # 读取Feather
            if hasattr(file_obj, 'name') and isinstance(file_obj.name, str):
                # 如果有文件名，直接使用文件路径更高效
                return pd.read_feather(file_obj.name, **pd_kwargs)
            else:
                # 否则使用文件对象
                return pd.read_feather(file_obj, **pd_kwargs)

        except Exception as e:
            logger.error(f"加载Feather失败: {str(e)}")
            return None

    def _load_pickle(self, file_obj: BinaryIO, config: Dict[str, Any]) -> Any:
        """
        加载Pickle数据

        参数:
            file_obj: 文件对象
            config: 加载配置

        返回:
            加载的Pickle数据
        """
        try:
            import pickle

            # 读取Pickle
            return pickle.load(file_obj)

        except Exception as e:
            logger.error(f"加载Pickle失败: {str(e)}")
            return None

    def _load_hdf5(self, file_obj: BinaryIO, config: Dict[str, Any]) -> Any:
        """
        加载HDF5数据

        参数:
            file_obj: 文件对象
            config: 加载配置

        返回:
            加载的HDF5数据
        """
        if not PANDAS_AVAILABLE:
            logger.error("pandas库未安装，无法加载HDF5")
            return None

        try:
            # 检查是否安装了tables
            import importlib
            if not importlib.util.find_spec("tables"):
                logger.error("tables库未安装，无法加载HDF5")
                return None

            # 准备pandas读取参数
            pd_kwargs = {}

            # 设置键名
            if 'key' in config:
                pd_kwargs['key'] = config['key']

            # 添加可选参数
            if 'columns' in config:
                pd_kwargs['columns'] = config['columns']
            if 'where' in config:
                pd_kwargs['where'] = config['where']

            # 读取HDF5
            if hasattr(file_obj, 'name') and isinstance(file_obj.name, str):
                # 如果有文件名，直接使用文件路径更高效
                return pd.read_hdf(file_obj.name, **pd_kwargs)
            else:
                # 对于文件对象，需要先保存到临时文件
                self._ensure_temp_dir()
                temp_path = os.path.join(
                    self.temp_dir, f"temp_hdf5_{id(file_obj)}.h5")

                with open(temp_path, 'wb') as f:
                    f.write(file_obj.read())

                data = pd.read_hdf(temp_path, **pd_kwargs)

                # 删除临时文件
                os.unlink(temp_path)

                return data

        except Exception as e:
            logger.error(f"加载HDF5失败: {str(e)}")
            return None

    def _load_sql(self, file_obj: BinaryIO, config: Dict[str, Any]) -> Any:
        """
        加载SQL数据

        参数:
            file_obj: 文件对象（包含SQL查询或表名）
            config: 加载配置

        返回:
            加载的SQL数据
        """
        if not PANDAS_AVAILABLE:
            logger.error("pandas库未安装，无法加载SQL")
            return None

        try:
            # 检查必要参数
            if 'connection' not in config:
                logger.error("缺少SQL连接参数")
                return None

            # 读取SQL查询或表名
            if hasattr(file_obj, 'read'):
                # 如果是文件对象，读取SQL查询
                query = file_obj.read()
                if isinstance(query, bytes):
                    query = query.decode(config.get('encoding', 'utf-8'))
            else:
                # 如果是字符串，直接使用
                query = file_obj

            # 准备pandas读取参数
            pd_kwargs = {
                'sql': query,
                'con': config['connection']
            }

            # 添加可选参数
            if 'params' in config:
                pd_kwargs['params'] = config['params']
            if 'index_col' in config:
                pd_kwargs['index_col'] = config['index_col']
            if 'parse_dates' in config:
                pd_kwargs['parse_dates'] = config['parse_dates']
            if 'chunksize' in config:
                pd_kwargs['chunksize'] = config['chunksize']

            # 读取SQL
            return pd.read_sql(**pd_kwargs)

        except Exception as e:
            logger.error(f"加载SQL失败: {str(e)}")
            return None

    def save_data(self,
                  data: Any,
                  output_path: str,
                  format: Optional[str] = None,
                  **kwargs) -> bool:
        """
        保存数据到文件

        参数:
            data: 要保存的数据
            output_path: 输出文件路径
            format: 输出格式，如果为None则根据文件扩展名自动检测
            **kwargs: 其他参数

        返回:
            是否成功保存
        """
        try:
            # 确保目录存在
            directory = os.path.dirname(output_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            # 自动检测格式（如果需要）
            if format is None:
                format = self._detect_format(output_path)

            # 根据格式保存数据
            if isinstance(data, pd.DataFrame):
                # 保存pandas数据帧
                if format == 'csv':
                    data.to_csv(output_path, **kwargs)
                elif format == 'excel':
                    data.to_excel(output_path, **kwargs)
                elif format == 'json':
                    data.to_json(output_path, **kwargs)
                elif format == 'parquet':
                    data.to_parquet(output_path, **kwargs)
                elif format == 'feather':
                    data.to_feather(output_path, **kwargs)
                elif format == 'pickle':
                    data.to_pickle(output_path, **kwargs)
                elif format == 'hdf5':
                    data.to_hdf(output_path, key=kwargs.get(
                        'key', 'data'), **kwargs)
                else:
                    # 默认导出为CSV
                    data.to_csv(output_path, **kwargs)

            elif isinstance(data, (dict, list)):
                # 保存字典或列表
                if format == 'json':
                    with open(output_path, 'w', encoding=kwargs.get('encoding', 'utf-8')) as f:
                        json.dump(data, f, **kwargs)
                elif format == 'yaml':
                    if not YAML_AVAILABLE:
                        logger.error("yaml模块未安装，无法保存YAML")
                        return False

                    with open(output_path, 'w', encoding=kwargs.get('encoding', 'utf-8')) as f:
                        yaml.dump(data, f, **kwargs)
                elif format == 'pickle':
                    import pickle
                    with open(output_path, 'wb') as f:
                        pickle.dump(data, f, **kwargs)
                else:
                    # 默认导出为JSON
                    with open(output_path, 'w', encoding=kwargs.get('encoding', 'utf-8')) as f:
                        json.dump(data, f, **kwargs)

            elif isinstance(data, str):
                # 保存文本
                with open(output_path, 'w', encoding=kwargs.get('encoding', 'utf-8')) as f:
                    f.write(data)

            elif isinstance(data, bytes):
                # 保存二进制数据
                with open(output_path, 'wb') as f:
                    f.write(data)

            else:
                # 尝试使用pickle保存其他类型
                import pickle
                with open(output_path, 'wb') as f:
                    pickle.dump(data, f, **kwargs)

            logger.info(f"数据已保存到: {output_path}")
            return True

        except Exception as e:
            logger.error(f"保存数据失败: {str(e)}")
            return False

    def clean_temp_files(self):
        """清理临时文件"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
                logger.info("已清理临时文件")
            except Exception as e:
                logger.error(f"清理临时文件失败: {str(e)}")

    def clear_cache(self):
        """清除数据缓存"""
        self.cache.clear()
        logger.info("数据缓存已清除")

    def __del__(self):
        """析构函数，清理资源"""
        self.clean_temp_files()


# 辅助函数

def is_dataframe(data: Any) -> bool:
    """
    检查数据是否为pandas DataFrame

    参数:
        data: 要检查的数据

    返回:
        是否为DataFrame
    """
    if not PANDAS_AVAILABLE:
        return False

    return isinstance(data, pd.DataFrame)


def to_dataframe(data: Any) -> Optional[pd.DataFrame]:
    """
    将数据转换为pandas DataFrame

    参数:
        data: 要转换的数据

    返回:
        转换后的DataFrame，如果转换失败则返回None
    """
    if not PANDAS_AVAILABLE:
        logger.error("pandas库未安装，无法转换为DataFrame")
        return None

    try:
        if isinstance(data, pd.DataFrame):
            # 已经是DataFrame
            return data
        elif isinstance(data, dict):
            # 字典转换为DataFrame
            return pd.DataFrame.from_dict(data)
        elif isinstance(data, list):
            # 列表转换为DataFrame
            return pd.DataFrame(data)
        elif isinstance(data, str):
            # 尝试解析JSON字符串
            try:
                json_data = json.loads(data)
                return pd.DataFrame(json_data)
            except:
                # 如果不是JSON，作为单元素
                return pd.DataFrame([data])
        else:
            # 其他类型作为单元素
            return pd.DataFrame([data])

    except Exception as e:
        logger.error(f"转换为DataFrame失败: {str(e)}")
        return None