# -*- coding: utf-8 -*-
"""
数据模块: 数据转换器
功能描述: 提供数据格式转换、清洗和预处理功能
版本: 1.0.0
作者: 窗口6开发人员
创建日期: 2025-04-17
"""

import os
import re
import json
import logging
import copy
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass

# 尝试导入可选依赖
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

# 从配置加载器获取配置
try:
    from ...config.config_loader import ConfigLoader
    config_loader = ConfigLoader()
    TRANSFORMER_CONFIG = config_loader.load("modules.data.data_transformer")
except ImportError:
    TRANSFORMER_CONFIG = {
        "default_output_format": "json",
        "preserve_original": True
    }

# 初始化日志记录器
logger = logging.getLogger(__name__)

@dataclass
class TransformerConfig:
    """数据转换器配置类"""
    
    output_format: str = "json"  # 输出格式: json, csv, xml, yaml, dict, list, dataframe
    preserve_original: bool = True  # 是否保留原始数据
    encoding: str = "utf-8"  # 文本编码
    indent: int = 2  # JSON/YAML缩进
    delimiter: str = ","  # CSV分隔符
    date_format: str = "%Y-%m-%d"  # 日期格式
    float_precision: int = 6  # 浮点数精度
    na_rep: str = ""  # 缺失值替代字符串
    
    def __post_init__(self):
        """数据校验和默认值设置"""
        valid_formats = ["json", "csv", "xml", "yaml", "dict", "list", "dataframe", "text"]
        if self.output_format not in valid_formats:
            logger.warning(f"无效的输出格式: {self.output_format}，使用默认格式: json")
            self.output_format = "json"
        
        # 确保indent为非负整数
        if self.indent < 0:
            logger.warning(f"无效的缩进值: {self.indent}，使用默认值: 2")
            self.indent = 2
        
        # 确保float_precision为正整数
        if self.float_precision <= 0:
            logger.warning(f"无效的浮点数精度: {self.float_precision}，使用默认值: 6")
            self.float_precision = 6


class DataTransformer:
    """数据转换器类"""
    
    def __init__(self, config: Optional[Union[Dict[str, Any], TransformerConfig]] = None):
        """
        初始化数据转换器
        
        参数:
            config: 转换器配置，可以是TransformerConfig实例或字典
        """
        if config is None:
            self.config = TransformerConfig(**TRANSFORMER_CONFIG)
        elif isinstance(config, dict):
            self.config = TransformerConfig(**config)
        else:
            self.config = config
        
        # 注册格式转换器
        self.format_converters = {
            "json": self._to_json,
            "csv": self._to_csv,
            "xml": self._to_xml,
            "yaml": self._to_yaml,
            "dict": self._to_dict,
            "list": self._to_list,
            "dataframe": self._to_dataframe,
            "text": self._to_text
        }
        
        # 注册数据清洗函数
        self.cleaning_funcs = {
            "drop_duplicates": self._drop_duplicates,
            "drop_na": self._drop_na,
            "fill_na": self._fill_na,
            "replace_values": self._replace_values,
            "normalize_whitespace": self._normalize_whitespace,
            "strip_html": self._strip_html,
            "extract_numbers": self._extract_numbers,
            "convert_types": self._convert_types,
            "trim_strings": self._trim_strings,
            "filter_rows": self._filter_rows,
            "select_columns": self._select_columns,
            "rename_columns": self._rename_columns,
            "apply_function": self._apply_function
        }
        
        logger.info(f"数据转换器初始化，输出格式: {self.config.output_format}")
    
    def transform(self, 
                 data: Any, 
                 output_format: Optional[str] = None,
                 preprocessing: Optional[List[Dict[str, Any]]] = None,
                 **kwargs) -> Any:
        """
        转换数据格式
        
        参数:
            data: 输入数据
            output_format: 输出格式，如果为None则使用配置中的默认值
            preprocessing: 预处理步骤列表，每个步骤是一个操作字典
            **kwargs: 其他参数，将覆盖配置中的对应值
            
        返回:
            转换后的数据
        """
        # 处理输出格式参数
        if output_format is None:
            output_format = self.config.output_format
        
        # 合并配置和参数
        config = copy.deepcopy(vars(self.config))
        config.update(kwargs)
        
        # 保留原始数据的副本（如果需要）
        if config.get("preserve_original", True):
            try:
                # 尝试进行深拷贝
                original_data = copy.deepcopy(data)
            except:
                # 如果无法深拷贝，则使用原始数据
                original_data = data
                logger.warning("无法创建数据的深拷贝，将直接修改原始数据")
        else:
            # 不需要保留原始数据
            original_data = data
        
        # 应用预处理步骤
        processed_data = self.preprocess(original_data, preprocessing)
        
        # 转换为目标格式
        converter = self.format_converters.get(output_format.lower())
        if converter:
            return converter(processed_data, config)
        else:
            logger.error(f"不支持的输出格式: {output_format}")
            return processed_data
    
    def preprocess(self, 
                  data: Any,
                  preprocessing: Optional[List[Dict[str, Any]]]) -> Any:
        """
        预处理数据
        
        参数:
            data: 输入数据
            preprocessing: 预处理步骤列表，每个步骤是一个操作字典
            
        返回:
            预处理后的数据
        """
        if not preprocessing:
            return data
        
        # 逐步应用预处理操作
        result = data
        for step in preprocessing:
            if not isinstance(step, dict) or "operation" not in step:
                logger.warning(f"跳过无效的预处理步骤: {step}")
                continue
            
            operation = step.pop("operation")
            func = self.cleaning_funcs.get(operation)
            
            if func:
                try:
                    result = func(result, **step)
                except Exception as e:
                    logger.error(f"预处理操作 '{operation}' 失败: {str(e)}")
            else:
                logger.warning(f"不支持的预处理操作: {operation}")
        
        return result
    
    # 格式转换函数
    
    def _to_json(self, data: Any, config: Dict[str, Any]) -> str:
        """
        将数据转换为JSON字符串
        
        参数:
            data: 输入数据
            config: 转换配置
            
        返回:
            JSON字符串
        """
        try:
            # 尝试转换为可序列化的对象
            serializable_data = self._ensure_json_serializable(data)
            
            # 序列化为JSON
            return json.dumps(
                serializable_data, 
                indent=config.get("indent", 2),
                ensure_ascii=False,
                default=str  # 用于处理无法序列化的对象
            )
        
        except Exception as e:
            logger.error(f"转换为JSON失败: {str(e)}")
            return "{}"
    
    def _to_csv(self, data: Any, config: Dict[str, Any]) -> str:
        """
        将数据转换为CSV字符串
        
        参数:
            data: 输入数据（应为表格数据）
            config: 转换配置
            
        返回:
            CSV字符串
        """
        if not PANDAS_AVAILABLE:
            logger.error("pandas库未安装，无法转换为CSV")
            return ""
        
        try:
            # 转换为DataFrame
            df = self._ensure_dataframe(data)
            
            if df is None:
                return ""
            
            # 转换为CSV
            return df.to_csv(
                index=config.get("include_index", False),
                sep=config.get("delimiter", ","),
                date_format=config.get("date_format", "%Y-%m-%d"),
                float_format=f"%.{config.get('float_precision', 6)}f",
                na_rep=config.get("na_rep", "")
            )
        
        except Exception as e:
            logger.error(f"转换为CSV失败: {str(e)}")
            return ""
    
    def _to_xml(self, data: Any, config: Dict[str, Any]) -> str:
        """
        将数据转换为XML字符串
        
        参数:
            data: 输入数据
            config: 转换配置
            
        返回:
            XML字符串
        """
        if not LXML_AVAILABLE:
            logger.error("lxml库未安装，无法转换为XML")
            return "<root></root>"
        
        try:
            # 创建XML根元素
            root_tag = config.get("root_tag", "root")
            root = etree.Element(root_tag)
            
            # 转换为XML元素
            self._dict_to_xml(root, data, config)
            
            # 序列化为XML字符串
            xml_str = etree.tostring(
                root,
                pretty_print=True,
                encoding=config.get("encoding", "utf-8"),
                xml_declaration=True
            )
            
            return xml_str.decode(config.get("encoding", "utf-8"))
        
        except Exception as e:
            logger.error(f"转换为XML失败: {str(e)}")
            return "<root></root>"
    
    def _dict_to_xml(self, parent: etree.Element, data: Any, config: Dict[str, Any]):
        """
        将字典或其他数据结构转换为XML元素
        
        参数:
            parent: 父XML元素
            data: 输入数据
            config: 转换配置
        """
        if isinstance(data, dict):
            # 处理字典
            for key, value in data.items():
                if key.startswith('@'):
                    # 处理属性（以@开头的键）
                    parent.set(key[1:], str(value))
                elif key == '#text':
                    # 处理文本内容（#text键）
                    parent.text = str(value)
                else:
                    # 创建子元素
                    # 检查是否是有效的XML标签名
                    tag = self._sanitize_xml_tag(key)
                    child = etree.SubElement(parent, tag)
                    self._dict_to_xml(child, value, config)
        
        elif isinstance(data, list):
            # 处理列表
            item_tag = config.get("item_tag", "item")
            for item in data:
                child = etree.SubElement(parent, item_tag)
                self._dict_to_xml(child, item, config)
        
        else:
            # 处理基本类型
            parent.text = str(data)
    
    def _sanitize_xml_tag(self, tag: str) -> str:
        """
        清理并返回有效的XML标签名
        
        参数:
            tag: 原始标签名
            
        返回:
            有效的XML标签名
        """
        # 移除无效字符
        tag = re.sub(r'[^\w.-]', '_', tag)
        
        # 确保不以数字、点或连字符开头
        if not tag or not re.match(r'^[a-zA-Z_]', tag):
            tag = 'tag_' + tag
        
        return tag
    
    def _to_yaml(self, data: Any, config: Dict[str, Any]) -> str:
        """
        将数据转换为YAML字符串
        
        参数:
            data: 输入数据
            config: 转换配置
            
        返回:
            YAML字符串
        """
        if not YAML_AVAILABLE:
            logger.error("yaml库未安装，无法转换为YAML")
            return ""
        
        try:
            # 尝试转换为可序列化的对象
            serializable_data = self._ensure_json_serializable(data)
            
            # 序列化为YAML
            return yaml.dump(
                serializable_data,
                default_flow_style=False,
                indent=config.get("indent", 2),
                allow_unicode=True,
                encoding=None  # 返回str而不是bytes
            )
        
        except Exception as e:
            logger.error(f"转换为YAML失败: {str(e)}")
            return ""
    
    def _to_dict(self, data: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        将数据转换为字典
        
        参数:
            data: 输入数据
            config: 转换配置
            
        返回:
            字典
        """
        try:
            if isinstance(data, dict):
                # 已经是字典，直接返回
                return data
            
            elif isinstance(data, str):
                # 尝试解析JSON或YAML字符串
                try:
                    return json.loads(data)
                except:
                    if YAML_AVAILABLE:
                        try:
                            return yaml.safe_load(data)
                        except:
                            pass
                    
                    # 如果都失败，把字符串作为键值对分割
                    result = {}
                    try:
                        lines = data.strip().split('\n')
                        for line in lines:
                            if ':' in line:
                                key, value = line.split(':', 1)
                                result[key.strip()] = value.strip()
                    except:
                        result = {"value": data}
                    
                    return result
            
            elif PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                # 转换DataFrame为字典
                return data.to_dict(orient=config.get("orient", "records"))
            
            elif isinstance(data, list):
                # 将列表转换为字典（使用索引作为键）
                return {str(i): item for i, item in enumerate(data)}
            
            else:
                # 尝试使用__dict__属性
                if hasattr(data, '__dict__'):
                    return data.__dict__
                
                # 尝试使用vars()
                try:
                    return vars(data)
                except:
                    pass
                
                # 如果都失败，包装在字典中
                return {"value": data}
        
        except Exception as e:
            logger.error(f"转换为字典失败: {str(e)}")
            return {}
    
    def _to_list(self, data: Any, config: Dict[str, Any]) -> List[Any]:
        """
        将数据转换为列表
        
        参数:
            data: 输入数据
            config: 转换配置
            
        返回:
            列表
        """
        try:
            if isinstance(data, list):
                # 已经是列表，直接返回
                return data
            
            elif isinstance(data, str):
                # 尝试解析JSON或YAML字符串
                try:
                    parsed = json.loads(data)
                    if isinstance(parsed, list):
                        return parsed
                    else:
                        return [parsed]
                except:
                    if YAML_AVAILABLE:
                        try:
                            parsed = yaml.safe_load(data)
                            if isinstance(parsed, list):
                                return parsed
                            else:
                                return [parsed]
                        except:
                            pass
                    
                    # 如果都失败，按行分割字符串
                    delimiter = config.get("delimiter", "\n")
                    return data.split(delimiter)
            
            elif isinstance(data, dict):
                # 转换字典为列表
                orient = config.get("orient", "records")
                if orient == "values":
                    return list(data.values())
                elif orient == "items":
                    return list(data.items())
                else:
                    return [data]
            
            elif PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                # 转换DataFrame为列表
                orient = config.get("orient", "records")
                if orient == "values":
                    return data.values.tolist()
                else:
                    return data.to_dict(orient=orient)
            
            else:
                # 包装在列表中
                return [data]
        
        except Exception as e:
            logger.error(f"转换为列表失败: {str(e)}")
            return []
    
    def _to_dataframe(self, data: Any, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        将数据转换为DataFrame
        
        参数:
            data: 输入数据
            config: 转换配置
            
        返回:
            DataFrame，如果转换失败则返回None
        """
        if not PANDAS_AVAILABLE:
            logger.error("pandas库未安装，无法转换为DataFrame")
            return None
        
        try:
            return self._ensure_dataframe(data)
        
        except Exception as e:
            logger.error(f"转换为DataFrame失败: {str(e)}")
            return None
    
    def _to_text(self, data: Any, config: Dict[str, Any]) -> str:
        """
        将数据转换为文本字符串
        
        参数:
            data: 输入数据
            config: 转换配置
            
        返回:
            文本字符串
        """
        try:
            if isinstance(data, str):
                # 已经是字符串，直接返回
                return data
            
            elif isinstance(data, (dict, list)):
                # 转换为JSON字符串
                return json.dumps(
                    data,
                    indent=config.get("indent", 2),
                    ensure_ascii=False,
                    default=str
                )
            
            elif PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                # 转换DataFrame为字符串
                format_type = config.get("text_format", "string")
                if format_type == "csv":
                    return data.to_csv(
                        index=config.get("include_index", False),
                        sep=config.get("delimiter", ","),
                        date_format=config.get("date_format", "%Y-%m-%d"),
                        float_format=f"%.{config.get('float_precision', 6)}f",
                        na_rep=config.get("na_rep", "")
                    )
                elif format_type == "json":
                    return data.to_json(orient=config.get("orient", "records"))
                else:
                    return str(data)
            
            else:
                # 转换为字符串
                return str(data)
        
        except Exception as e:
            logger.error(f"转换为文本失败: {str(e)}")
            return ""
    
    # 辅助函数
    
    def _ensure_json_serializable(self, data: Any) -> Any:
        """
        确保数据可以被JSON序列化
        
        参数:
            data: 输入数据
            
        返回:
            可JSON序列化的数据
        """
        if isinstance(data, (str, int, float, bool, type(None))):
            # 基本类型，直接返回
            return data
        
        elif isinstance(data, dict):
            # 递归处理字典
            return {k: self._ensure_json_serializable(v) for k, v in data.items()}
        
        elif isinstance(data, (list, tuple)):
            # 递归处理列表或元组
            return [self._ensure_json_serializable(item) for item in data]
        
        elif PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            # 转换DataFrame为字典列表
            return data.to_dict(orient="records")
        
        elif NUMPY_AVAILABLE and isinstance(data, np.ndarray):
            # 转换NumPy数组为列表
            return data.tolist()
        
        elif NUMPY_AVAILABLE and isinstance(data, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64,
                                                 np.uint8, np.uint16, np.uint32, np.uint64)):
            # 转换NumPy整数类型为Python整数
            return int(data)
        
        elif NUMPY_AVAILABLE and isinstance(data, (np.float_, np.float16, np.float32, np.float64)):
            # 转换NumPy浮点类型为Python浮点数
            return float(data)
        
        elif NUMPY_AVAILABLE and isinstance(data, (np.bool_)):
            # 转换NumPy布尔类型为Python布尔值
            return bool(data)
        
        elif hasattr(data, 'isoformat'):
            # 处理日期时间对象
            return data.isoformat()
        
        elif hasattr(data, '__dict__'):
            # 转换对象为字典
            return self._ensure_json_serializable(data.__dict__)
        
        else:
            # 转换为字符串
            return str(data)
    
    def _ensure_dataframe(self, data: Any) -> Optional[pd.DataFrame]:
        """
        确保数据是pandas DataFrame
        
        参数:
            data: 输入数据
            
        返回:
            DataFrame对象，如果转换失败则返回None
        """
        if not PANDAS_AVAILABLE:
            logger.error("pandas库未安装，无法转换为DataFrame")
            return None
        
        if isinstance(data, pd.DataFrame):
            # 已经是DataFrame，直接返回
            return data
        
        elif isinstance(data, dict):
            # 处理不同类型的字典
            if all(isinstance(v, (list, tuple)) for v in data.values()):
                # 列数据字典 {列名: 列数据}
                return pd.DataFrame(data)
            else:
                # 常规字典
                return pd.DataFrame([data])
        
        elif isinstance(data, list):
            if not data:
                # 空列表
                return pd.DataFrame()
            elif all(isinstance(item, dict) for item in data):
                # 字典列表
                return pd.DataFrame(data)
            elif all(isinstance(item, (list, tuple)) for item in data):
                # 二维数组
                return pd.DataFrame(data)
            else:
                # 一维数组
                return pd.DataFrame({"value": data})
        
        elif isinstance(data, str):
            # 尝试解析JSON或CSV字符串
            try:
                # 尝试解析为JSON
                parsed = json.loads(data)
                return self._ensure_dataframe(parsed)
            except:
                # 尝试解析为CSV
                try:
                    from io import StringIO
                    return pd.read_csv(StringIO(data))
                except:
                    # 如果都失败，创建单行DataFrame
                    return pd.DataFrame({"value": [data]})
        
        elif NUMPY_AVAILABLE and isinstance(data, np.ndarray):
            # 转换NumPy数组
            return pd.DataFrame(data)
        
        else:
            # 其他类型转换为单个元素的DataFrame
            return pd.DataFrame({"value": [data]})
    
    # 数据清洗函数
    
    def _drop_duplicates(self, data: Any, **kwargs) -> Any:
        """
        删除重复数据
        
        参数:
            data: 输入数据
            **kwargs: 其他参数，如 subset, keep
            
        返回:
            处理后的数据
        """
        # 对DataFrame处理
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            return data.drop_duplicates(**kwargs)
        
        # 对列表处理
        elif isinstance(data, list):
            if not data:
                return []
            
            # 如果是字典列表，转换为DataFrame处理后再转回
            if all(isinstance(item, dict) for item in data):
                if PANDAS_AVAILABLE:
                    df = pd.DataFrame(data)
                    df = df.drop_duplicates(**kwargs)
                    return df.to_dict(orient="records")
                else:
                    # 没有pandas，使用简单逻辑
                    result = []
                    seen = set()
                    
                    for item in data:
                        # 将字典转换为不可变对象
                        item_tuple = tuple(sorted(item.items()))
                        if item_tuple not in seen:
                            seen.add(item_tuple)
                            result.append(item)
                    
                    return result
            else:
                # 简单列表去重
                keep = kwargs.get("keep", "first")
                if keep == "first":
                    result = []
                    seen = set()
                    for item in data:
                        if item not in seen:
                            seen.add(item)
                            result.append(item)
                    return result
                elif keep == "last":
                    result = []
                    seen = set()
                    for item in reversed(data):
                        if item not in seen:
                            seen.add(item)
                            result.append(item)
                    return list(reversed(result))
                else:  # keep == False
                    from collections import Counter
                    counter = Counter(data)
                    return [item for item in data if counter[item] == 1]
        
        # 对字典处理
        elif isinstance(data, dict):
            # 字典值去重
            result = {}
            for key, value in data.items():
                if isinstance(value, list):
                    result[key] = self._drop_duplicates(value, **kwargs)
                else:
                    result[key] = value
            return result
        
        # 其他类型原样返回
        else:
            return data
    
    def _drop_na(self, data: Any, **kwargs) -> Any:
        """
        删除空值
        
        参数:
            data: 输入数据
            **kwargs: 其他参数，如 subset, how
            
        返回:
            处理后的数据
        """
        # 空值判断函数
        def is_na(value):
            if value is None:
                return True
            if isinstance(value, str) and not value.strip():
                return True
            if PANDAS_AVAILABLE and pd.isna(value):
                return True
            if NUMPY_AVAILABLE and (isinstance(value, np.float) and np.isnan(value)):
                return True
            return False
        
        # 对DataFrame处理
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            return data.dropna(**kwargs)
        
        # 对列表处理
        elif isinstance(data, list):
            # 字典列表
            if all(isinstance(item, dict) for item in data):
                subset = kwargs.get("subset")
                how = kwargs.get("how", "any")
                
                if subset:
                    # 指定字段检查
                    if how == "any":
                        # 任一字段为空则删除
                        return [item for item in data if not any(is_na(item.get(field)) for field in subset)]
                    else:  # how == "all"
                        # 所有字段为空才删除
                        return [item for item in data if not all(is_na(item.get(field)) for field in subset)]
                else:
                    # 所有字段检查
                    if how == "any":
                        # 任一字段为空则删除
                        return [item for item in data if not any(is_na(value) for value in item.values())]
                    else:  # how == "all"
                        # 所有字段为空才删除
                        return [item for item in data if item and not all(is_na(value) for value in item.values())]
            
            # 普通列表
            else:
                return [item for item in data if not is_na(item)]
        
        # 对字典处理
        elif isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if not is_na(value):
                    result[key] = value
            return result
        
        # 其他类型判断是否为空
        else:
            return None if is_na(data) else data
    
    def _fill_na(self, data: Any, **kwargs) -> Any:
        """
        填充空值
        
        参数:
            data: 输入数据
            **kwargs: 其他参数，如 value, method, fill_dict
            
        返回:
            处理后的数据
        """
        # 空值判断函数
        def is_na(value):
            if value is None:
                return True
            if isinstance(value, str) and not value.strip():
                return True
            if PANDAS_AVAILABLE and pd.isna(value):
                return True
            if NUMPY_AVAILABLE and (isinstance(value, np.float) and np.isnan(value)):
                return True
            return False
        
        # 获取填充值和方法
        value = kwargs.get("value")
        method = kwargs.get("method")
        fill_dict = kwargs.get("fill_dict", {})
        
        # 对DataFrame处理
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            if fill_dict:
                return data.fillna(value=fill_dict)
            else:
                return data.fillna(value=value, method=method)
        
        # 对列表处理
        elif isinstance(data, list):
            # 字典列表
            if all(isinstance(item, dict) for item in data):
                result = []
                for item in data:
                    new_item = {}
                    for k, v in item.items():
                        if is_na(v):
                            if k in fill_dict:
                                new_item[k] = fill_dict[k]
                            else:
                                new_item[k] = value
                        else:
                            new_item[k] = v
                    result.append(new_item)
                return result
            
            # 普通列表，前向填充
            elif method == "ffill" or method == "pad":
                result = []
                last_valid = value
                for item in data:
                    if is_na(item):
                        result.append(last_valid)
                    else:
                        result.append(item)
                        last_valid = item
                return result
            
            # 普通列表，后向填充
            elif method == "bfill" or method == "backfill":
                result = list(data)
                last_valid = value
                for i in range(len(result) - 1, -1, -1):
                    if is_na(result[i]):
                        result[i] = last_valid
                    else:
                        last_valid = result[i]
                return result
            
            # 普通列表，常数填充
            else:
                return [value if is_na(item) else item for item in data]
        
        # 对字典处理
        elif isinstance(data, dict):
            result = {}
            for key, val in data.items():
                if is_na(val):
                    if key in fill_dict:
                        result[key] = fill_dict[key]
                    else:
                        result[key] = value
                else:
                    result[key] = val
            return result
        
        # 其他类型判断是否为空
        else:
            return value if is_na(data) else data
    
    def _replace_values(self, data: Any, **kwargs) -> Any:
        """
        替换值
        
        参数:
            data: 输入数据
            **kwargs: 其他参数，如 to_replace, value, replace_dict
            
        返回:
            处理后的数据
        """
        to_replace = kwargs.get("to_replace")
        value = kwargs.get("value")
        replace_dict = kwargs.get("replace_dict", {})
        
        # 替换函数
        def replace_value(val):
            if replace_dict:
                return replace_dict.get(val, val)
            elif to_replace is not None:
                return value if val == to_replace else val
            else:
                return val
        
        # 对DataFrame处理
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            if replace_dict:
                return data.replace(replace_dict)
            else:
                return data.replace(to_replace, value)
        
        # 对列表处理
        elif isinstance(data, list):
            # 字典列表
            if all(isinstance(item, dict) for item in data):
                result = []
                for item in data:
                    new_item = {}
                    for k, v in item.items():
                        new_item[k] = replace_value(v)
                    result.append(new_item)
                return result
            
            # 普通列表
            else:
                return [replace_value(item) for item in data]
        
        # 对字典处理
        elif isinstance(data, dict):
            result = {}
            for key, val in data.items():
                result[key] = replace_value(val)
            return result
        
        # 其他类型直接替换
        else:
            return replace_value(data)
    
    def _normalize_whitespace(self, data: Any, **kwargs) -> Any:
        """
        规范化空白字符
        
        参数:
            data: 输入数据
            **kwargs: 其他参数，如 collapse, strip
            
        返回:
            处理后的数据
        """
        collapse = kwargs.get("collapse", True)  # 是否合并连续空白
        strip = kwargs.get("strip", True)  # 是否去除首尾空白
        
        # 处理字符串函数
        def process_string(text):
            if not isinstance(text, str):
                return text
            
            if collapse:
                text = re.sub(r'\s+', ' ', text)
            
            if strip:
                text = text.strip()
            
            return text
        
        # 递归处理函数
        def process_data(val):
            if isinstance(val, str):
                return process_string(val)
            elif isinstance(val, list):
                return [process_data(item) for item in val]
            elif isinstance(val, dict):
                return {k: process_data(v) for k, v in val.items()}
            else:
                return val
        
        # 对DataFrame处理
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            # 只处理字符串列
            return data.applymap(lambda x: process_string(x) if isinstance(x, str) else x)
        
        # 其他数据类型
        return process_data(data)
    
    def _strip_html(self, data: Any, **kwargs) -> Any:
        """
        去除HTML标签
        
        参数:
            data: 输入数据
            **kwargs: 其他参数，如 keep_links
            
        返回:
            处理后的数据
        """
        keep_links = kwargs.get("keep_links", False)  # 是否保留链接
        
        # 处理HTML函数
        def strip_html_tags(text):
            if not isinstance(text, str):
                return text
            
            if keep_links:
                # 保留链接，替换<a>标签为文本和URL
                text = re.sub(r'<a\s+[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'\2 (\1)', text)
            
            # 去除所有HTML标签
            text = re.sub(r'<[^>]*>', '', text)
            
            # 替换HTML实体
            text = re.sub(r'&nbsp;', ' ', text)
            text = re.sub(r'&lt;', '<', text)
            text = re.sub(r'&gt;', '>', text)
            text = re.sub(r'&amp;', '&', text)
            text = re.sub(r'&quot;', '"', text)
            text = re.sub(r'&apos;', "'", text)
            
            return text
        
        # 递归处理函数
        def process_data(val):
            if isinstance(val, str):
                return strip_html_tags(val)
            elif isinstance(val, list):
                return [process_data(item) for item in val]
            elif isinstance(val, dict):
                return {k: process_data(v) for k, v in val.items()}
            else:
                return val
        
        # 对DataFrame处理
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            # 只处理字符串列
            return data.applymap(lambda x: strip_html_tags(x) if isinstance(x, str) else x)
        
        # 其他数据类型
        return process_data(data)
    
    def _extract_numbers(self, data: Any, **kwargs) -> Any:
        """
        提取数字
        
        参数:
            data: 输入数据
            **kwargs: 其他参数，如 as_float, pattern
            
        返回:
            处理后的数据
        """
        as_float = kwargs.get("as_float", True)  # 是否转换为浮点数
        pattern = kwargs.get("pattern")  # 自定义正则表达式
        
        # 提取数字函数
        def extract_numbers_from_string(text):
            if not isinstance(text, str):
                return text
            
            if pattern:
                # 使用自定义正则表达式
                numbers = re.findall(pattern, text)
            else:
                # 提取所有数字（包括小数和负数）
                numbers = re.findall(r'-?\d+\.?\d*', text)
            
            if not numbers:
                return None
            
            if as_float:
                try:
                    if len(numbers) == 1:
                        return float(numbers[0])
                    else:
                        return [float(num) for num in numbers]
                except:
                    return numbers
            else:
                return numbers[0] if len(numbers) == 1 else numbers
        
        # 递归处理函数
        def process_data(val):
            if isinstance(val, str):
                return extract_numbers_from_string(val)
            elif isinstance(val, list):
                return [process_data(item) for item in val]
            elif isinstance(val, dict):
                return {k: process_data(v) for k, v in val.items()}
            else:
                return val
        
        # 对DataFrame处理
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            # 只处理字符串列
            return data.applymap(lambda x: extract_numbers_from_string(x) if isinstance(x, str) else x)
        
        # 其他数据类型
        return process_data(data)
    
    def _convert_types(self, data: Any, **kwargs) -> Any:
        """
        转换数据类型
        
        参数:
            data: 输入数据
            **kwargs: 其他参数，如 dtypes
            
        返回:
            处理后的数据
        """
        dtypes = kwargs.get("dtypes", {})  # 类型映射 {字段: 类型}
        
        # 类型转换函数
        def convert_value(val, dtype):
            if dtype == "int":
                try:
                    return int(val)
                except:
                    return 0
            elif dtype == "float":
                try:
                    return float(val)
                except:
                    return 0.0
            elif dtype == "str":
                return str(val)
            elif dtype == "bool":
                if isinstance(val, str):
                    return val.lower() in ["true", "yes", "1", "y", "t"]
                else:
                    return bool(val)
            else:
                return val
        
        # 对DataFrame处理
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            # 转换指定列的类型
            for col, dtype in dtypes.items():
                if col in data.columns:
                    try:
                        if dtype == "int":
                            data[col] = data[col].astype(int)
                        elif dtype == "float":
                            data[col] = data[col].astype(float)
                        elif dtype == "str":
                            data[col] = data[col].astype(str)
                        elif dtype == "bool":
                            data[col] = data[col].astype(bool)
                        else:
                            data[col] = data[col].astype(dtype)
                    except:
                        pass
            return data
        
        # 对列表处理
        elif isinstance(data, list):
            # 字典列表
            if all(isinstance(item, dict) for item in data):
                result = []
                for item in data:
                    new_item = {}
                    for k, v in item.items():
                        if k in dtypes:
                            new_item[k] = convert_value(v, dtypes[k])
                        else:
                            new_item[k] = v
                    result.append(new_item)
                return result
            
            # 普通列表
            else:
                # 尝试整体转换
                list_type = kwargs.get("list_type")
                if list_type:
                    try:
                        if list_type == "int":
                            return [int(x) for x in data]
                        elif list_type == "float":
                            return [float(x) for x in data]
                        elif list_type == "str":
                            return [str(x) for x in data]
                        elif list_type == "bool":
                            return [bool(x) for x in data]
                    except:
                        pass
                return data
        
        # 对字典处理
        elif isinstance(data, dict):
            result = {}
            for key, val in data.items():
                if key in dtypes:
                    result[key] = convert_value(val, dtypes[key])
                else:
                    result[key] = val
            return result
        
        # 其他类型判断
        else:
            dtype = kwargs.get("dtype")
            if dtype:
                return convert_value(data, dtype)
            else:
                return data
    
    def _trim_strings(self, data: Any, **kwargs) -> Any:
        """
        修剪字符串
        
        参数:
            data: 输入数据
            **kwargs: 其他参数，如 chars, side
            
        返回:
            处理后的数据
        """
        chars = kwargs.get("chars")  # 要删除的字符集
        side = kwargs.get("side", "both")  # 修剪侧: left, right, both
        
        # 字符串修剪函数
        def trim_string(text):
            if not isinstance(text, str):
                return text
            
            if side == "left":
                return text.lstrip(chars)
            elif side == "right":
                return text.rstrip(chars)
            else:  # both
                return text.strip(chars)
        
        # 递归处理函数
        def process_data(val):
            if isinstance(val, str):
                return trim_string(val)
            elif isinstance(val, list):
                return [process_data(item) for item in val]
            elif isinstance(val, dict):
                return {k: process_data(v) for k, v in val.items()}
            else:
                return val
        
        # 对DataFrame处理
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            # 只处理字符串列
            return data.applymap(lambda x: trim_string(x) if isinstance(x, str) else x)
        
        # 其他数据类型
        return process_data(data)
    
    def _filter_rows(self, data: Any, **kwargs) -> Any:
        """
        过滤行
        
        参数:
            data: 输入数据
            **kwargs: 其他参数，如 condition, column, value, operator
            
        返回:
            处理后的数据
        """
        condition = kwargs.get("condition")  # 条件表达式
        column = kwargs.get("column")  # 列名
        value = kwargs.get("value")  # 比较值
        operator = kwargs.get("operator", "==")  # 比较操作符
        
        # 条件判断函数
        def evaluate_condition(item):
            if condition:
                # 使用eval执行条件表达式
                try:
                    return eval(condition, {"item": item})
                except:
                    return True
            elif column is not None and value is not None:
                # 使用指定列和操作符比较
                if isinstance(item, dict):
                    col_value = item.get(column)
                    
                    if operator == "==":
                        return col_value == value
                    elif operator == "!=":
                        return col_value != value
                    elif operator == ">":
                        return col_value > value
                    elif operator == ">=":
                        return col_value >= value
                    elif operator == "<":
                        return col_value < value
                    elif operator == "<=":
                        return col_value <= value
                    elif operator == "in":
                        return col_value in value
                    elif operator == "not in":
                        return col_value not in value
                    elif operator == "contains":
                        if isinstance(col_value, str) and isinstance(value, str):
                            return value in col_value
                        return False
                    else:
                        return True
                else:
                    return True
            else:
                return True
        
        # 对DataFrame处理
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            if condition:
                # 使用query方法执行条件表达式
                try:
                    return data.query(condition)
                except:
                    return data
            elif column is not None and value is not None:
                # 使用指定列和操作符过滤
                if column in data.columns:
                    if operator == "==":
                        return data[data[column] == value]
                    elif operator == "!=":
                        return data[data[column] != value]
                    elif operator == ">":
                        return data[data[column] > value]
                    elif operator == ">=":
                        return data[data[column] >= value]
                    elif operator == "<":
                        return data[data[column] < value]
                    elif operator == "<=":
                        return data[data[column] <= value]
                    elif operator == "in":
                        return data[data[column].isin(value)]
                    elif operator == "not in":
                        return data[~data[column].isin(value)]
                    elif operator == "contains":
                        if isinstance(value, str):
                            return data[data[column].astype(str).str.contains(value)]
                        return data
                    else:
                        return data
                else:
                    return data
            else:
                return data
        
        # 对列表处理
        elif isinstance(data, list):
            return [item for item in data if evaluate_condition(item)]
        
        # 其他类型无法过滤
        else:
            return data
    
    def _select_columns(self, data: Any, **kwargs) -> Any:
        """
        选择列
        
        参数:
            data: 输入数据
            **kwargs: 其他参数，如 columns, exclude
            
        返回:
            处理后的数据
        """
        columns = kwargs.get("columns", [])  # 要选择的列
        exclude = kwargs.get("exclude", [])  # 要排除的列
        
        # 对DataFrame处理
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            if columns:
                # 选择指定列
                columns = [col for col in columns if col in data.columns]
                return data[columns]
            elif exclude:
                # 排除指定列
                columns = [col for col in data.columns if col not in exclude]
                return data[columns]
            else:
                return data
        
        # 对列表处理
        elif isinstance(data, list):
            # 字典列表
            if all(isinstance(item, dict) for item in data):
                result = []
                for item in data:
                    if columns:
                        # 选择指定列
                        new_item = {k: item.get(k) for k in columns if k in item}
                    elif exclude:
                        # 排除指定列
                        new_item = {k: v for k, v in item.items() if k not in exclude}
                    else:
                        new_item = item
                    result.append(new_item)
                return result
            else:
                return data
        
        # 对字典处理
        elif isinstance(data, dict):
            if columns:
                # 选择指定键
                return {k: data.get(k) for k in columns if k in data}
            elif exclude:
                # 排除指定键
                return {k: v for k, v in data.items() if k not in exclude}
            else:
                return data
        
        # 其他类型无法选择列
        else:
            return data
    
    def _rename_columns(self, data: Any, **kwargs) -> Any:
        """
        重命名列
        
        参数:
            data: 输入数据
            **kwargs: 其他参数，如 columns (字典 {旧名: 新名})
            
        返回:
            处理后的数据
        """
        columns = kwargs.get("columns", {})  # 重命名映射 {旧名: 新名}
        
        if not columns:
            return data
        
        # 对DataFrame处理
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            return data.rename(columns=columns)
        
        # 对列表处理
        elif isinstance(data, list):
            # 字典列表
            if all(isinstance(item, dict) for item in data):
                result = []
                for item in data:
                    new_item = {}
                    for k, v in item.items():
                        if k in columns:
                            new_item[columns[k]] = v
                        else:
                            new_item[k] = v
                    result.append(new_item)
                return result
            else:
                return data
        
        # 对字典处理
        elif isinstance(data, dict):
            result = {}
            for k, v in data.items():
                if k in columns:
                    result[columns[k]] = v
                else:
                    result[k] = v
            return result
        
        # 其他类型无法重命名
        else:
            return data
    
    def _apply_function(self, data: Any, **kwargs) -> Any:
        """
        应用函数
        
        参数:
            data: 输入数据
            **kwargs: 其他参数，如 function, columns
            
        返回:
            处理后的数据
        """
        function = kwargs.get("function")  # 函数表达式
        columns = kwargs.get("columns")  # 要应用的列
        
        if not function:
            return data
        
        # 创建计算函数
        def compute_function(value):
            try:
                # 创建局部变量
                import math
                import re
                import datetime
                import random
                
                # 定义常用的辅助函数
                def to_upper(s):
                    return s.upper() if isinstance(s, str) else s
                
                def to_lower(s):
                    return s.lower() if isinstance(s, str) else s
                
                def capitalize(s):
                    return s.capitalize() if isinstance(s, str) else s
                
                def length(s):
                    return len(s) if hasattr(s, '__len__') else 0
                
                def is_numeric(s):
                    if isinstance(s, (int, float)):
                        return True
                    if isinstance(s, str):
                        return s.replace('.', '', 1).isdigit()
                    return False
                
                # 执行函数表达式
                result = eval(function, {
                    "math": math,
                    "re": re,
                    "datetime": datetime,
                    "random": random,
                    "x": value,
                    "value": value,
                    "to_upper": to_upper,
                    "to_lower": to_lower,
                    "capitalize": capitalize,
                    "len": length,
                    "is_numeric": is_numeric
                })
                
                return result
            except Exception as e:
                logger.error(f"应用函数失败: {str(e)}")
                return value
        
        # 对DataFrame处理
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            result = data.copy()
            
            # 确定要处理的列
            if columns:
                cols_to_process = [col for col in columns if col in result.columns]
            else:
                cols_to_process = result.columns
            
            # 对每列应用函数
            for col in cols_to_process:
                result[col] = result[col].apply(compute_function)
            
            return result
        
        # 对列表处理
        elif isinstance(data, list):
            # 字典列表
            if all(isinstance(item, dict) for item in data):
                result = []
                for item in data:
                    new_item = {}
                    for k, v in item.items():
                        if columns is None or k in columns:
                            new_item[k] = compute_function(v)
                        else:
                            new_item[k] = v
                    result.append(new_item)
                return result
            
            # 普通列表
            else:
                return [compute_function(item) for item in data]
        
        # 对字典处理
        elif isinstance(data, dict):
            result = {}
            for k, v in data.items():
                if columns is None or k in columns:
                    result[k] = compute_function(v)
                else:
                    result[k] = v
            return result
        
        # 其他类型直接应用函数
        else:
            return compute_function(data)


# 辅助函数

def flatten_dict(d: Dict[str, Any], 
                parent_key: str = '',
                separator: str = '.') -> Dict[str, Any]:
    """
    展平嵌套字典
    
    参数:
        d: 输入字典
        parent_key: 父键前缀
        separator: 键分隔符
        
    返回:
        展平后的字典
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + separator + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, separator).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: Dict[str, Any], 
                  separator: str = '.') -> Dict[str, Any]:
    """
    还原展平的字典为嵌套字典
    
    参数:
        d: 展平的字典
        separator: 键分隔符
        
    返回:
        嵌套字典
    """
    result = {}
    for key, value in d.items():
        parts = key.split(separator)
        
        # 循环构建嵌套字典
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    return result


def merge_dicts(dict1: Dict[str, Any], 
               dict2: Dict[str, Any],
               overwrite: bool = True) -> Dict[str, Any]:
    """
    合并两个字典
    
    参数:
        dict1: 第一个字典
        dict2: 第二个字典
        overwrite: 是否覆盖第一个字典中的值
        
    返回:
        合并后的字典
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # 递归合并嵌套字典
            result[key] = merge_dicts(result[key], value, overwrite)
        elif key not in result or overwrite:
            # 添加或覆盖值
            result[key] = value
    
    return result


def convert_keys_case(data: Dict[str, Any], 
                     case: str = 'snake') -> Dict[str, Any]:
    """
    转换字典键的命名风格
    
    参数:
        data: 输入字典
        case: 目标命名风格，可选值为 'snake', 'camel', 'pascal', 'kebab'
        
    返回:
        转换后的字典
    """
    if not isinstance(data, dict):
        return data
    
    # 转换函数
    def to_snake_case(s):
        s = re.sub(r'[-\s]', '_', s)
        s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s)
        return s.lower()
    
    def to_camel_case(s):
        s = to_snake_case(s)
        components = s.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    
    def to_pascal_case(s):
        s = to_snake_case(s)
        return ''.join(x.title() for x in s.split('_'))
    
    def to_kebab_case(s):
        s = to_snake_case(s)
        return s.replace('_', '-')
    
    # 选择转换函数
    if case == 'snake':
        converter = to_snake_case
    elif case == 'camel':
        converter = to_camel_case
    elif case == 'pascal':
        converter = to_pascal_case
    elif case == 'kebab':
        converter = to_kebab_case
    else:
        return data
    
    # 转换字典键
    result = {}
    for key, value in data.items():
        new_key = converter(key)
        if isinstance(value, dict):
            result[new_key] = convert_keys_case(value, case)
        elif isinstance(value, list):
            result[new_key] = [
                convert_keys_case(item, case) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[new_key] = value
    
    return result