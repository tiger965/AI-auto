"""
应用程序通用设置模块

该模块负责管理应用程序的通用设置，包括:
- 性能相关配置
- 功能开关
- 界面设置
- 其他通用参数
"""
from typing import Dict, Any, Optional
import os
import logging
from config.config_loader import load_config, get_standardized_env_var_name

class AppSettings:
    """应用程序设置管理类"""
    
    def __init__(self) -> None:
        """初始化应用程序设置管理器"""
        self._config_type = "app"
        self._config_prefix = "APP"
        
    def get_config(self, environment: str = "development", use_cache: bool = True) -> Dict[str, Any]:
        """
        获取指定环境的应用程序设置
        
        参数:
            environment: 环境名称，默认为 "development"
            use_cache: 是否使用缓存，默认为 True
            
        返回:
            包含应用程序设置的字典
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
        
        return config
            
    def _override_from_environment(self, settings: Dict[str, Any]) -> None:
        """从环境变量覆盖配置"""
        changes = []  # 记录变更
        
        # 应用名称
        app_name_var = self._get_env_var_name("NAME")
        if app_name_var in os.environ:
            old_value = settings.get("app", {}).get("name", "")
            settings.setdefault("app", {})["name"] = os.environ[app_name_var]
            changes.append({
                "key": "app.name",
                "old_value": old_value,
                "new_value": settings["app"]["name"]
            })
            
        # 最大工作线程数
        max_workers_var = self._get_env_var_name("MAX_WORKERS")
        if max_workers_var in os.environ:
            try:
                old_value = settings.get("app", {}).get("performance", {}).get("max_workers", 0)
                workers_value = int(os.environ[max_workers_var])
                settings.setdefault("app", {}).setdefault("performance", {})["max_workers"] = workers_value
                changes.append({
                    "key": "app.performance.max_workers",
                    "old_value": old_value,
                    "new_value": workers_value
                })
            except ValueError:
                logging.warning(f"无效的MAX_WORKERS值: {os.environ[max_workers_var]}")
                
        # 缓存大小
        cache_size_var = self._get_env_var_name("CACHE_SIZE")
        if cache_size_var in os.environ:
            try:
                old_value = settings.get("app", {}).get("performance", {}).get("cache_size", 0)
                cache_value = int(os.environ[cache_size_var])
                settings.setdefault("app", {}).setdefault("performance", {})["cache_size"] = cache_value
                changes.append({
                    "key": "app.performance.cache_size",
                    "old_value": old_value,
                    "new_value": cache_value
                })
            except ValueError:
                logging.warning(f"无效的CACHE_SIZE值: {os.environ[cache_size_var]}")
                
        # 添加审计日志
        if changes:
            audit_logger = logging.getLogger("audit")
            for change in changes:
                audit_logger.info(f"配置变更: {change['key']} 从 {change['old_value']} 变更为 {change['new_value']}")
    
    def _get_env_var_name(self, key: str) -> str:
        """获取标准化的环境变量名"""
        return get_standardized_env_var_name(f"{self._config_prefix}_{key}")
        
    def validate_config(self, config: Dict[str, Any]) -> None:
        """验证配置项是否有效，无效则抛出异常"""
        # 验证应用名称
        app = config.get("app", {})
        if not app.get("name"):
            raise ValueError("应用名称不能为空")
            
        # 验证性能设置
        perf = app.get("performance", {})
        if "max_workers" in perf and (not isinstance(perf["max_workers"], int) or perf["max_workers"] <= 0):
            raise ValueError("max_workers必须是正整数")
            
        if "cache_size" in perf and (not isinstance(perf["cache_size"], int) or perf["cache_size"] < 0):
            raise ValueError("cache_size必须是非负整数")