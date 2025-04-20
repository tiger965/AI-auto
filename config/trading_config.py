"""
量化交易配置模块

该模块负责管理量化交易相关的配置，包括:
- Freqtrade框架路径
- 策略生成和存储路径
- 交易所连接信息
- 默认交易参数
"""
from typing import Dict, Any, Optional
import os
import logging
from config.config_loader import load_config, get_standardized_env_var_name
from config.credentials import Credentials

class TradingConfig:
    """量化交易配置管理类"""
    
    def __init__(self) -> None:
        """初始化交易配置管理器"""
        self._config_type = "trading"
        self._config_prefix = "TRADING"
        self._credentials = Credentials()
        
    def get_config(self, environment: str = "development", use_cache: bool = True) -> Dict[str, Any]:
        """
        获取指定环境的交易配置
        
        参数:
            environment: 环境名称，默认为 "development"
            use_cache: 是否使用缓存，默认为 True
            
        返回:
            包含交易配置的字典
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
        
        # 加载交易所凭证
        self._load_exchange_credentials(config, environment)
        
        return config
            
    def _override_from_environment(self, settings: Dict[str, Any]) -> None:
        """从环境变量覆盖配置"""
        changes = []  # 记录变更
        
        # Freqtrade路径
        freqtrade_path_var = self._get_env_var_name("FREQTRADE_PATH")
        if freqtrade_path_var in os.environ:
            old_value = settings.get("freqtrade", {}).get("base_path", "")
            settings.setdefault("freqtrade", {})["base_path"] = os.environ[freqtrade_path_var]
            changes.append({
                "key": "freqtrade.base_path",
                "old_value": old_value,
                "new_value": settings["freqtrade"]["base_path"]
            })
            
        # 策略路径
        strategy_path_var = self._get_env_var_name("STRATEGY_PATH")
        if strategy_path_var in os.environ:
            old_value = settings.get("freqtrade", {}).get("strategy_path", "")
            settings.setdefault("freqtrade", {})["strategy_path"] = os.environ[strategy_path_var]
            changes.append({
                "key": "freqtrade.strategy_path",
                "old_value": old_value,
                "new_value": settings["freqtrade"]["strategy_path"]
            })
            
        # 交易所名称
        exchange_var = self._get_env_var_name("EXCHANGE")
        if exchange_var in os.environ:
            old_value = settings.get("exchange", {}).get("name", "")
            settings.setdefault("exchange", {})["name"] = os.environ[exchange_var]
            changes.append({
                "key": "exchange.name",
                "old_value": old_value,
                "new_value": settings["exchange"]["name"]
            })
            
        # 默认时间周期
        timeframe_var = self._get_env_var_name("DEFAULT_TIMEFRAME")
        if timeframe_var in os.environ:
            old_value = settings.get("strategy", {}).get("default_timeframe", "")
            settings.setdefault("strategy", {})["default_timeframe"] = os.environ[timeframe_var]
            changes.append({
                "key": "strategy.default_timeframe",
                "old_value": old_value,
                "new_value": settings["strategy"]["default_timeframe"]
            })
                
        # 添加审计日志
        if changes:
            audit_logger = logging.getLogger("audit")
            for change in changes:
                audit_logger.info(f"交易配置变更: {change['key']} 从 {change['old_value']} 变更为 {change['new_value']}")
    
    def _get_env_var_name(self, key: str) -> str:
        """获取标准化的环境变量名"""
        return get_standardized_env_var_name(f"{self._config_prefix}_{key}")
    
    def _load_exchange_credentials(self, config: Dict[str, Any], environment: str) -> None:
        """加载交易所凭证"""
        # 获取凭证配置
        creds = self._credentials.get_config(environment)
        
        # 检查是否存在交易所凭证
        if "exchanges" in creds and config.get("exchange", {}).get("name") in creds["exchanges"]:
            exchange_name = config["exchange"]["name"]
            exchange_creds = creds["exchanges"][exchange_name]
            
            # 添加到配置中
            config.setdefault("exchange", {}).update({
                "api_key": exchange_creds.get("api_key", ""),
                "secret": exchange_creds.get("secret", "")
            })
        
    def validate_config(self, config: Dict[str, Any]) -> None:
        """验证配置项是否有效，无效则抛出异常"""
        # 验证Freqtrade配置
        freqtrade = config.get("freqtrade", {})
        if not freqtrade.get("base_path"):
            raise ValueError("Freqtrade基础路径不能为空")
            
        if not freqtrade.get("strategy_path"):
            raise ValueError("策略路径不能为空")
            
        # 验证交易所配置
        exchange = config.get("exchange", {})
        if not exchange.get("name"):
            raise ValueError("交易所名称不能为空")
            
        # 验证策略配置
        strategy = config.get("strategy", {})
        if not strategy.get("default_timeframe"):
            raise ValueError("默认时间周期不能为空")
            
        if "default_stoploss" not in strategy:
            raise ValueError("默认止损设置不能为空")
            
        if "default_roi" not in strategy:
            raise ValueError("默认利润目标不能为空")