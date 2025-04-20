"""
文件系统路径统一管理模块

该模块负责统一管理应用程序使用的文件系统路径，包括:
- 配置文件目录
- 数据存储目录
- 日志文件目录
- 临时文件目录
"""
from typing import Dict, Any, Optional
from pathlib import Path
import os
import logging
from config.config_loader import load_config, get_standardized_env_var_name, get_config_directories

class Paths:
    """路径管理类"""
    
    def __init__(self) -> None:
        """初始化路径管理器"""
        self._config_type = "paths"
        self._config_prefix = "PATH"
        
    def get_config(self, environment: str = "development", use_cache: bool = True) -> Dict[str, Any]:
        """
        获取指定环境的路径配置
        
        参数:
            environment: 环境名称，默认为 "development"
            use_cache: 是否使用缓存，默认为 True
            
        返回:
            包含路径配置的字典
        """
        # 使用配置加载器加载配置
        config = load_config(
            self._config_type,
            environment,
            validators=[self.validate_config],
            use_cache=use_cache
        )
        
        # 环境变量覆盖
        self._override_from_environment(config)
        
        # 解析相对路径
        self._resolve_relative_paths(config)
        
        return config
            
    def _override_from_environment(self, settings: Dict[str, Any]) -> None:
        """从环境变量覆盖配置"""
        changes = []  # 记录变更
        
        # 数据目录
        data_dir_var = self._get_env_var_name("DATA_DIR")
        if data_dir_var in os.environ:
            old_value = settings.get("dirs", {}).get("data", "")
            settings.setdefault("dirs", {})["data"] = os.environ[data_dir_var]
            changes.append({
                "key": "dirs.data",
                "old_value": old_value,
                "new_value": settings["dirs"]["data"]
            })
            
        # 日志目录
        logs_dir_var = self._get_env_var_name("LOGS_DIR")
        if logs_dir_var in os.environ:
            old_value = settings.get("dirs", {}).get("logs", "")
            settings.setdefault("dirs", {})["logs"] = os.environ[logs_dir_var]
            changes.append({
                "key": "dirs.logs",
                "old_value": old_value,
                "new_value": settings["dirs"]["logs"]
            })
            
        # 临时目录
        temp_dir_var = self._get_env_var_name("TEMP_DIR")
        if temp_dir_var in os.environ:
            old_value = settings.get("dirs", {}).get("temp", "")
            settings.setdefault("dirs", {})["temp"] = os.environ[temp_dir_var]
            changes.append({
                "key": "dirs.temp",
                "old_value": old_value,
                "new_value": settings["dirs"]["temp"]
            })
                
        # 添加审计日志
        if changes:
            audit_logger = logging.getLogger("audit")
            for change in changes:
                audit_logger.info(f"配置变更: {change['key']} 从 {change['old_value']} 变更为 {change['new_value']}")
    
    def _get_env_var_name(self, key: str) -> str:
        """获取标准化的环境变量名"""
        return get_standardized_env_var_name(f"{self._config_prefix}_{key}")
    
    def _resolve_relative_paths(self, config: Dict[str, Any]) -> None:
        """解析相对路径为绝对路径"""
        base_dir = Path(os.path.abspath(os.path.dirname(__file__))).parent
        
        if "dirs" in config:
            for key, path_str in config["dirs"].items():
                if path_str and not os.path.isabs(path_str):
                    config["dirs"][key] = str(base_dir / path_str)
                    
            # 确保目录存在
            for key, path_str in config["dirs"].items():
                try:
                    os.makedirs(path_str, exist_ok=True)
                except Exception as e:
                    logging.warning(f"无法创建目录 {path_str}: {str(e)}")
        
    def validate_config(self, config: Dict[str, Any]) -> None:
        """验证配置项是否有效，无效则抛出异常"""
        # 验证必要的目录配置
        dirs = config.get("dirs", {})
        required_dirs = ["data", "logs", "temp"]
        
        for dir_name in required_dirs:
            if dir_name not in dirs or not dirs[dir_name]:
                raise ValueError(f"必须提供 {dir_name} 目录路径")
                
    def ensure_directories_exist(self) -> None:
        """确保所有配置的目录存在"""
        config = self.get_config()
        
        if "dirs" in config:
            for dir_name, dir_path in config["dirs"].items():
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    logging.info(f"目录已创建/确认: {dir_path}")
                except Exception as e:
                    logging.error(f"创建目录 {dir_path} 失败: {str(e)}")