"""
敏感凭证信息安全管理模块

该模块负责安全地管理敏感凭证信息，包括:
- API密钥和密码
- 数据库连接凭证
- OAuth令牌
- 其他需要安全存储的信息
"""

from typing import Dict, Any, Optional
from pathlib import Path
import os
import logging
import base64
from config.config_loader import (
    load_config,
    get_standardized_env_var_name,
    get_config_directories,
)


class Credentials:
    """凭证信息管理类"""

    def __init__(self) -> None:
        """初始化凭证信息管理器"""
        self._config_type = "credentials"
        self._config_prefix = "CRED"

    def get_config(
        self, environment: str = "development", use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取指定环境的凭证信息

        参数:
            environment: 环境名称，默认为 "development"
            use_cache: 是否使用缓存，默认为 True

        返回:
            包含凭证信息的字典
        """
        # 使用安全目录
        secure_dir = get_config_directories().get("secure")

        # 使用配置加载器加载配置
        config = load_config(
            self._config_type,
            environment,
            config_dir=secure_dir,
            validators=[self.validate_config],
            use_cache=use_cache,
        )

        # 解密敏感信息
        self._decrypt_sensitive_info(config)

        # 环境变量覆盖
        self._override_from_environment(config)

        return config

    def _override_from_environment(self, settings: Dict[str, Any]) -> None:
        """从环境变量覆盖配置"""
        changes = []  # 记录变更但不记录具体值，保护敏感信息

        # 数据库密码
        db_password_var = self._get_env_var_name("DB_PASSWORD")
        if db_password_var in os.environ:
            settings.setdefault("database", {})["password"] = os.environ[
                db_password_var
            ]
            changes.append({"key": "database.password"})

        # API密钥
        api_key_var = self._get_env_var_name("API_KEY")
        if api_key_var in os.environ:
            settings.setdefault("api", {})["key"] = os.environ[api_key_var]
            changes.append({"key": "api.key"})

        # OAuth客户端密钥
        oauth_secret_var = self._get_env_var_name("OAUTH_SECRET")
        if oauth_secret_var in os.environ:
            settings.setdefault("oauth", {})["client_secret"] = os.environ[
                oauth_secret_var
            ]
            changes.append({"key": "oauth.client_secret"})

        # 添加审计日志，但不记录敏感值
        if changes:
            audit_logger = logging.getLogger("audit")
            for change in changes:
                audit_logger.info(f"凭证配置变更: {change['key']} (敏感信息，值已隐藏)")

    def _get_env_var_name(self, key: str) -> str:
        """获取标准化的环境变量名"""
        return get_standardized_env_var_name(f"{self._config_prefix}_{key}")

    def _decrypt_sensitive_info(self, config: Dict[str, Any]) -> None:
        """解密配置中的敏感信息"""
        # 这里实现简单的解密示例，实际应用中应使用更安全的加密算法
        if "database" in config and "password_encrypted" in config["database"]:
            try:
                encrypted = config["database"]["password_encrypted"]
                # 简单的Base64解码示例，实际应使用更安全的加密
                config["database"]["password"] = base64.b64decode(encrypted).decode(
                    "utf-8"
                )
                del config["database"]["password_encrypted"]
            except Exception as e:
                logging.error(f"解密数据库密码失败: {str(e)}")

        if "api" in config and "key_encrypted" in config["api"]:
            try:
                encrypted = config["api"]["key_encrypted"]
                config["api"]["key"] = base64.b64decode(
                    encrypted).decode("utf-8")
                del config["api"]["key_encrypted"]
            except Exception as e:
                logging.error(f"解密API密钥失败: {str(e)}")

        if "oauth" in config and "client_secret_encrypted" in config["oauth"]:
            try:
                encrypted = config["oauth"]["client_secret_encrypted"]
                config["oauth"]["client_secret"] = base64.b64decode(encrypted).decode(
                    "utf-8"
                )
                del config["oauth"]["client_secret_encrypted"]
            except Exception as e:
                logging.error(f"解密OAuth客户端密钥失败: {str(e)}")

    def validate_config(self, config: Dict[str, Any]) -> None:
        """验证配置项是否有效，无效则抛出异常"""
        # 验证数据库凭证
        if "database" in config:
            db = config["database"]
            if "user" in db and not (
                db.get("password") or db.get("password_encrypted")
            ):
                raise ValueError("数据库密码不能为空")

        # 验证API凭证
        if "api" in config and not (
            config["api"].get("key") or config["api"].get("key_encrypted")
        ):
            raise ValueError("API密钥不能为空")

        # 验证OAuth凭证
        if "oauth" in config:
            oauth = config["oauth"]
            if oauth.get("client_id") and not (
                oauth.get("client_secret") or oauth.get(
                    "client_secret_encrypted")
            ):
                raise ValueError("OAuth客户端密钥不能为空")

    def encrypt_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        加密凭证信息

        参数:
            credentials: 包含明文凭证的字典

        返回:
            包含加密凭证的字典
        """
        result = credentials.copy()

        # 加密数据库密码
        if "database" in result and "password" in result["database"]:
            try:
                password = result["database"]["password"]
                result["database"]["password_encrypted"] = base64.b64encode(
                    password.encode("utf-8")
                ).decode("utf-8")
                del result["database"]["password"]
            except Exception as e:
                logging.error(f"加密数据库密码失败: {str(e)}")

        # 加密API密钥
        if "api" in result and "key" in result["api"]:
            try:
                key = result["api"]["key"]
                result["api"]["key_encrypted"] = base64.b64encode(
                    key.encode("utf-8")
                ).decode("utf-8")
                del result["api"]["key"]
            except Exception as e:
                logging.error(f"加密API密钥失败: {str(e)}")

        # 加密OAuth客户端密钥
        if "oauth" in result and "client_secret" in result["oauth"]:
            try:
                secret = result["oauth"]["client_secret"]
                result["oauth"]["client_secret_encrypted"] = base64.b64encode(
                    secret.encode("utf-8")
                ).decode("utf-8")
                del result["oauth"]["client_secret"]
            except Exception as e:
                logging.error(f"加密OAuth客户端密钥失败: {str(e)}")

        return result

    def save_credentials(
        self, credentials: Dict[str, Any], environment: str = "development"
    ) -> bool:
        """
        保存凭证信息

        参数:
            credentials: 包含凭证的字典
            environment: 环境名称，默认为"development"

        返回:
            保存是否成功
        """
        try:
            # 获取安全目录
            secure_dir = get_config_directories().get("secure")
            if not secure_dir:
                raise ValueError("安全目录未配置")

            # 确保目录存在
            os.makedirs(secure_dir, exist_ok=True)

            # 加密凭证
            encrypted = self.encrypt_credentials(credentials)

            # 保存到文件
            import json

            config_file = secure_dir / \
                f"{environment}_{self._config_type}.json"
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(encrypted, f, indent=2)

            logging.info(f"凭证信息已保存到 {config_file}")
            return True

        except Exception as e:
            logging.error(f"保存凭证信息失败: {str(e)}")
            return False