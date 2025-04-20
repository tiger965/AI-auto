"""
配置模块

该模块提供应用程序配置管理功能，包括API配置、应用设置、
凭证管理、路径管理、日志配置和交易配置。
"""
from typing import Dict, Any, Optional
import logging

# 全局环境变量前缀
ENV_PREFIX = "MYAPP"

# 导入配置管理类
from config.api_config import APIConfig
from config.app_settings import AppSettings
from config.credentials import Credentials
from config.paths import Paths
from config.logging_config import LoggingConfig
from config.trading_config import TradingConfig

# 导入配置加载工具
from config.config_loader import (
    load_config,
    load_yaml_config,
    clear_config_cache,
    get_standardized_env_var_name,
    get_config_directories,
    create_config_directories
)

# 创建配置管理器实例
api_config = APIConfig()
app_settings = AppSettings()
credentials = Credentials()
paths = Paths()
logging_config = LoggingConfig()
trading_config = TradingConfig()

def get_all_configs(environment: str = "development") -> Dict[str, Dict[str, Any]]:
    """
    获取所有配置
    
    参数:
        environment: 环境名称，默认为"development"
        
    返回:
        包含所有配置的字典
    """
    return {
        "api": api_config.get_config(environment),
        "app": app_settings.get_config(environment),
        "credentials": credentials.get_config(environment),
        "paths": paths.get_config(environment),
        "logging": logging_config.get_config(environment),
        "trading": trading_config.get_config(environment)
    }

def validate_all_configs(environment: str = "development") -> None:
    """
    验证所有配置
    
    参数:
        environment: 环境名称，默认为"development"
        
    抛出:
        如果任何配置验证失败，则抛出异常
    """
    # 获取所有配置会触发验证
    get_all_configs(environment)
    logging.info(f"所有配置验证通过，环境: {environment}")

def initialize(environment: str = "development") -> None:
    """
    初始化配置模块
    
    参数:
        environment: 环境名称，默认为"development"
    """
    # 创建配置目录结构
    create_config_directories()
    
    # 配置日志系统
    logging_config.setup_basic_logging()
    
    # 确保路径存在
    paths.ensure_directories_exist()
    
    # 验证所有配置
    validate_all_configs(environment)
    
    # 配置完整日志系统
    logging_config.configure_logging(environment)
    
    logging.info(f"配置模块已初始化，环境: {environment}")

def get_environment() -> str:
    """
    获取当前环境
    
    返回:
        当前环境名称
    """
    import os
    env_var = get_standardized_env_var_name("ENVIRONMENT")
    return os.environ.get(env_var, "development")