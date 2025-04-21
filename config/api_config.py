"""
API配置管理模块

该模块负责管理与API相关的所有配置信息，包括:
- API端点URL
- 认证密钥和令牌
- 请求超时设置
- 重试策略
"""

from typing import Dict, Any, Optional
import os
import logging
from config.config_loader import load_config, get_standardized_env_var_name


class APIConfig:
    """API配置管理类"""

    def __init__(self) -> None:
        """初始化API配置管理器"""
        self._config_type = "api"
        self._config_prefix = "API"

    def get_config(
        self, environment: str = "development", use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取指定环境的API配置

        参数:
            environment: 环境名称，默认为 "development"
            use_cache: 是否使用缓存，默认为 True

        返回:
            包含API配置的字典
        """
        # 使用配置加载器加载配置
        config = load_config(
            self._config_type,
            environment,
            validators=[self.validate_config],
            use_cache=use_cache,
        )

        # 环境变量覆盖
        self._override_from_environment(config)

        return config

    def _override_from_environment(self, settings: Dict[str, Any]) -> None:
        """从环境变量覆盖配置"""
        changes = []  # 记录变更

        # API服务器URL
        server_url_var = self._get_env_var_name("SERVER_URL")
        if server_url_var in os.environ:
            old_value = settings.get("server", {}).get("url", "")
            settings.setdefault("server", {})[
                "url"] = os.environ[server_url_var]
            changes.append(
                {
                    "key": "server.url",
                    "old_value": old_value,
                    "new_value": settings["server"]["url"],
                }
            )

        # API版本
        version_var = self._get_env_var_name("VERSION")
        if version_var in os.environ:
            old_value = settings.get("server", {}).get("version", "")
            settings.setdefault("server", {})[
                "version"] = os.environ[version_var]
            changes.append(
                {
                    "key": "server.version",
                    "old_value": old_value,
                    "new_value": settings["server"]["version"],
                }
            )

        # 超时设置
        timeout_var = self._get_env_var_name("TIMEOUT")
        if timeout_var in os.environ:
            try:
                old_value = settings.get("request", {}).get("timeout", 0)
                timeout_value = int(os.environ[timeout_var])
                settings.setdefault("request", {})["timeout"] = timeout_value
                changes.append(
                    {
                        "key": "request.timeout",
                        "old_value": old_value,
                        "new_value": timeout_value,
                    }
                )
            except ValueError:
                pass

        # 重试次数
        retries_var = self._get_env_var_name("MAX_RETRIES")
        if retries_var in os.environ:
            try:
                old_value = settings.get("request", {}).get("max_retries", 0)
                retries_value = int(os.environ[retries_var])
                settings.setdefault("request", {})[
                    "max_retries"] = retries_value
                changes.append(
                    {
                        "key": "request.max_retries",
                        "old_value": old_value,
                        "new_value": retries_value,
                    }
                )
            except ValueError:
                pass

        # 添加审计日志
        if changes:
            audit_logger = logging.getLogger("audit")
            for change in changes:
                audit_logger.info(
                    f"配置变更: {change['key']} 从 {change['old_value']} 变更为 {change['new_value']}"
                )

    def _get_env_var_name(self, key: str) -> str:
        """获取标准化的环境变量名"""
        return get_standardized_env_var_name(f"{self._config_prefix}_{key}")

    def validate_config(self, config: Dict[str, Any]) -> None:
        """验证配置项是否有效，无效则抛出异常"""
        # 验证服务器URL
        server = config.get("server", {})
        if not server.get("url"):
            raise ValueError("API服务器URL不能为空")

        # 验证请求超时设置
        request = config.get("request", {})
        if "timeout" in request and (
            not isinstance(request["timeout"], int) or request["timeout"] <= 0
        ):
            raise ValueError("请求超时必须是正整数")

        # 验证最大重试次数
        if "max_retries" in request and (
            not isinstance(request["max_retries"],
                           int) or request["max_retries"] < 0
        ):
            raise ValueError("最大重试次数必须是非负整数")