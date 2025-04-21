"""
日志记录系统配置模块

该模块负责配置应用程序的日志记录系统，包括:
- 日志级别设置
- 日志格式化器
- 日志处理器配置
- 审计日志设置
"""

from typing import Dict, Any, Optional
import os
import logging
import logging.config
from config.config_loader import load_config, get_standardized_env_var_name


class LoggingConfig:
    """日志配置管理类"""

    def __init__(self) -> None:
        """初始化日志配置管理器"""
        self._config_type = "logging"
        self._config_prefix = "LOG"

    def get_config(
        self, environment: str = "development", use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取指定环境的日志配置

        参数:
            environment: 环境名称，默认为 "development"
            use_cache: 是否使用缓存，默认为 True

        返回:
            包含日志配置的字典
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

    def configure_logging(self, environment: str = "development") -> None:
        """
        配置日志系统

        参数:
            environment: 环境名称，默认为 "development"
        """
        config = self.get_config(environment)

        # 如果配置包含完整的logging.config格式，直接使用
        if "version" in config:
            logging.config.dictConfig(config)
            return

        # 否则使用基本配置
        root_logger = logging.getLogger()

        # 清除现有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # 设置默认级别
        level = getattr(logging, config.get("level", "INFO"))
        root_logger.setLevel(level)

        # 控制台处理器
        if config.get("console", {}).get("enabled", True):
            console_handler = logging.StreamHandler()
            console_level = getattr(
                logging, config.get("console", {}).get("level", "INFO")
            )
            console_handler.setLevel(console_level)

            # 格式化器
            formatter = logging.Formatter(
                config.get("console", {}).get(
                    "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # 文件处理器
        if config.get("file", {}).get("enabled", False):
            from config.paths import Paths

            paths_config = Paths().get_config(environment)
            log_dir = paths_config.get("dirs", {}).get("logs", "logs")

            # 确保日志目录存在
            os.makedirs(log_dir, exist_ok=True)

            # 日志文件路径
            log_file = os.path.join(
                log_dir, config.get("file", {}).get("filename", "app.log")
            )

            file_handler = logging.FileHandler(log_file)
            file_level = getattr(logging, config.get(
                "file", {}).get("level", "INFO"))
            file_handler.setLevel(file_level)

            # 格式化器
            formatter = logging.Formatter(
                config.get("file", {}).get(
                    "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        # 配置审计日志
        if config.get("audit", {}).get("enabled", False):
            self._configure_audit_logging(config, environment)

        logging.info(f"日志系统已配置，环境: {environment}")

    def _configure_audit_logging(
        self, config: Dict[str, Any], environment: str
    ) -> None:
        """配置审计日志"""
        # 获取路径配置
        from config.paths import Paths

        paths_config = Paths().get_config(environment)
        log_dir = paths_config.get("dirs", {}).get("logs", "logs")

        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)

        # 审计日志文件路径
        audit_file = os.path.join(
            log_dir, config.get("audit", {}).get("filename", "audit.log")
        )

        # 创建审计日志记录器
        audit_logger = logging.getLogger("audit")
        audit_logger.setLevel(logging.INFO)
        audit_logger.propagate = False

        # 清除现有处理器
        for handler in audit_logger.handlers[:]:
            audit_logger.removeHandler(handler)

        # 文件处理器
        handler = logging.FileHandler(audit_file)
        handler.setLevel(logging.INFO)

        # 格式化器
        formatter = logging.Formatter(
            config.get("audit", {}).get("format", "%(asctime)s - %(message)s")
        )
        handler.setFormatter(formatter)
        audit_logger.addHandler(handler)

        logging.info(f"审计日志已配置，文件: {audit_file}")

    def _override_from_environment(self, settings: Dict[str, Any]) -> None:
        """从环境变量覆盖配置"""
        changes = []  # 记录变更

        # 日志级别
        level_var = self._get_env_var_name("LEVEL")
        if level_var in os.environ:
            old_value = settings.get("level", "")
            settings["level"] = os.environ[level_var]
            changes.append(
                {"key": "level", "old_value": old_value,
                    "new_value": settings["level"]}
            )

        # 控制台日志级别
        console_level_var = self._get_env_var_name("CONSOLE_LEVEL")
        if console_level_var in os.environ:
            old_value = settings.get("console", {}).get("level", "")
            settings.setdefault("console", {})[
                "level"] = os.environ[console_level_var]
            changes.append(
                {
                    "key": "console.level",
                    "old_value": old_value,
                    "new_value": settings["console"]["level"],
                }
            )

        # 文件日志级别
        file_level_var = self._get_env_var_name("FILE_LEVEL")
        if file_level_var in os.environ:
            old_value = settings.get("file", {}).get("level", "")
            settings.setdefault("file", {})[
                "level"] = os.environ[file_level_var]
            changes.append(
                {
                    "key": "file.level",
                    "old_value": old_value,
                    "new_value": settings["file"]["level"],
                }
            )

        # 添加审计日志
        if changes:
            # 这里我们不使用审计日志器，因为它可能尚未配置
            # 在配置结束后应用程序可以记录这些变更
            pass

    def _get_env_var_name(self, key: str) -> str:
        """获取标准化的环境变量名"""
        return get_standardized_env_var_name(f"{self._config_prefix}_{key}")

    def validate_config(self, config: Dict[str, Any]) -> None:
        """验证配置项是否有效，无效则抛出异常"""
        # 验证日志级别
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        # 主日志级别
        if "level" in config and config["level"] not in valid_levels:
            raise ValueError(f"无效的日志级别: {config['level']}")

        # 控制台日志级别
        if (
            "console" in config
            and "level" in config["console"]
            and config["console"]["level"] not in valid_levels
        ):
            raise ValueError(f"无效的控制台日志级别: {config['console']['level']}")

        # 文件日志级别
        if (
            "file" in config
            and "level" in config["file"]
            and config["file"]["level"] not in valid_levels
        ):
            raise ValueError(f"无效的文件日志级别: {config['file']['level']}")

    def setup_basic_logging(self) -> None:
        """设置基本日志配置，用于在完整配置加载前"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logging.info("基本日志配置已设置")