# -*- coding: utf-8 -*-
"""
日志工具模块: logging_utils
功能描述: 提供增强的日志处理、配置和轮换功能
版本: 1.0
创建日期: 2025-04-17
"""

import trading.utils
import os
import sys
import json
import time
import logging
import logging.config
import logging.handlers
import traceback
import threading
import datetime
import socket
import platform
from typing import Dict, Any, Optional, Union, List, Tuple, Callable
from functools import wraps

# 默认日志级别映射
DEFAULT_LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# 默认日志格式化器
DEFAULT_LOG_FORMATTER = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)

# 增强的日志格式化器（包含额外信息）
ENHANCED_LOG_FORMATTER = logging.Formatter(
    '%(asctime)s [%(levelname)s] [%(module)s:%(lineno)d] [%(process)d:%(thread)d] %(name)s - %(message)s'
)

# 详细的日志格式化器（包含核心模块需要的额外信息）
DETAILED_LOG_FORMATTER = logging.Formatter(
    '%(asctime)s [%(levelname)s] [%(module)s:%(lineno)d] [%(process)d:%(thread)d] '
    '[%(function)s] %(name)s - %(message)s'
)


class JsonFormatter(logging.Formatter):
    """JSON格式的日志格式化器，方便日志聚合和分析"""

    def __init__(self, include_extra_fields: bool = True):
        super().__init__()
        self.include_extra_fields = include_extra_fields

    def format(self, record: logging.LogRecord) -> str:
        """
        将日志记录格式化为JSON字符串

        Args:
            record: 日志记录对象

        Returns:
            格式化后的JSON字符串
        """
        # 获取基本日志信息
        log_data = {
            'timestamp': datetime.datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'filename': record.filename,
            'funcName': record.funcName,
            'lineno': record.lineno,
            'process': record.process,
            'thread': record.thread,
            'threadName': record.threadName
        }

        # 添加异常信息（如果有）
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }

        # 添加额外字段
        if self.include_extra_fields and hasattr(record, 'extras'):
            log_data.update(record.extras)

        # 添加所有其他自定义属性
        if self.include_extra_fields:
            for key, value in record.__dict__.items():
                if key not in log_data and not key.startswith('_') and isinstance(value, (str, int, float, bool, type(None))):
                    log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False)


class ContextualAdapter(logging.LoggerAdapter):
    """
    上下文适配器，用于在日志记录中添加额外上下文信息
    """

    def process(self, msg, kwargs):
        """
        处理日志消息，添加上下文信息

        Args:
            msg: 原始日志消息
            kwargs: 关键字参数

        Returns:
            处理后的消息和参数
        """
        # 确保extra字段存在
        if 'extra' not in kwargs:
            kwargs['extra'] = {}

        # 将适配器上下文合并到extra中
        if hasattr(self, 'extra'):
            for key, value in self.extra.items():
                if key not in kwargs['extra']:
                    kwargs['extra'][key] = value

        return msg, kwargs


class ContextualLogger(logging.Logger):
    """
    上下文感知的日志记录器，支持额外信息的传递
    """

    def makeRecord(
        self,
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: str,
        args: Any,
        exc_info: Any,
        func: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
        sinfo: Optional[str] = None
    ) -> logging.LogRecord:
        """
        创建日志记录并添加额外信息

        Args:
            name: 记录器名称
            level: 日志级别
            fn: 文件名
            lno: 行号
            msg: 日志消息
            args: 消息参数
            exc_info: 异常信息
            func: 函数名
            extra: 额外信息
            sinfo: 堆栈信息

        Returns:
            创建的日志记录对象
        """
        # 创建基础日志记录
        record = super().makeRecord(name, level, fn, lno, msg,
                                    args, exc_info, func, extra, sinfo)

        # 添加额外上下文信息
        if extra:
            for key, value in extra.items():
                setattr(record, key, value)
            record.extras = extra

        return record

    def with_context(self, **context) -> logging.LoggerAdapter:
        """
        创建带有指定上下文的日志适配器

        Args:
            **context: 上下文键值对

        Returns:
            配置了上下文的日志适配器
        """
        return ContextualAdapter(self, context)


# 注册自定义的日志记录器类
logging.setLoggerClass(ContextualLogger)


class EnhancedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    增强的轮换文件处理器，支持自动归档
    """

    def __init__(
        self,
        filename: str,
        mode: str = 'a',
        maxBytes: int = 0,
        backupCount: int = 0,
        encoding: Optional[str] = None,
        delay: bool = False,
        archive_dir: Optional[str] = None,
        archive_prefix: str = '',
        compress_archives: bool = False
    ):
        """
        初始化处理器

        Args:
            filename: 日志文件名
            mode: 文件打开模式
            maxBytes: 单个日志文件最大字节数
            backupCount: 保留的备份文件数量
            encoding: 文件编码
            delay: 是否延迟打开文件
            archive_dir: 归档目录
            archive_prefix: 归档文件前缀
            compress_archives: 是否压缩归档
        """
        super().__init__(
            filename, mode, maxBytes, backupCount, encoding, delay
        )
        self.archive_dir = archive_dir
        self.archive_prefix = archive_prefix
        self.compress_archives = compress_archives

    def rotation_filename(self, default_name: str) -> str:
        """
        生成轮换后的文件名

        Args:
            default_name: 默认文件名

        Returns:
            轮换后的文件名
        """
        # 如果没有指定归档目录，使用父类方法
        if not self.archive_dir:
            return super().rotation_filename(default_name)

        # 确保归档目录存在
        os.makedirs(self.archive_dir, exist_ok=True)

        # 提取基本文件名
        base_filename = os.path.basename(default_name)

        # 添加前缀
        if self.archive_prefix:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            base_filename = f"{self.archive_prefix}_{timestamp}_{base_filename}"

        # 生成完整路径
        return os.path.join(self.archive_dir, base_filename)

    def doRollover(self) -> None:
        """执行日志轮换"""
        super().doRollover()

        # 如果需要压缩归档
        if self.compress_archives and self.backupCount > 0:
            import gzip
            import shutil

            # 获取最新的备份文件
            backup_file = f"{self.baseFilename}.{self.backupCount}"
            if os.path.exists(backup_file):
                gz_file = f"{backup_file}.gz"

                # 压缩文件
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(gz_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # 删除原始备份文件
                os.remove(backup_file)


class AuditLogFilter(logging.Filter):
    """
    审计日志过滤器，用于识别和处理审计日志
    """

    def __init__(self, audit_type: Optional[str] = None):
        """
        初始化过滤器

        Args:
            audit_type: 审计类型
        """
        super().__init__()
        self.audit_type = audit_type

    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录

        Args:
            record: 日志记录

        Returns:
            是否通过过滤
        """
        # 检查是否有审计类型字段
        has_audit_field = hasattr(record, 'audit_type')

        # 如果没有指定审计类型，只要有audit_type字段就通过
        if not self.audit_type:
            return has_audit_field

        # 如果指定了审计类型，检查是否匹配
        return has_audit_field and record.audit_type == self.audit_type


def get_logger(
    name: str,
    level: Optional[Union[int, str]] = None,
    context: Optional[Dict[str, Any]] = None
) -> Union[logging.Logger, ContextualAdapter]:
    """
    获取日志记录器

    Args:
        name: 记录器名称
        level: 日志级别
        context: 上下文信息

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)

    # 设置日志级别
    if level is not None:
        if isinstance(level, str):
            level = DEFAULT_LOG_LEVELS.get(level.upper(), logging.INFO)
        logger.setLevel(level)

    # 添加上下文
    if context:
        return logger.with_context(**context)

    return logger


def setup_logging(
    config_path: Optional[str] = None,
    default_level: int = logging.INFO,
    log_dir: str = 'logs',
    env_key: str = 'LOG_CONFIG',
    backup_count: int = 30,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    log_to_console: bool = True,
    log_to_file: bool = True,
    app_name: str = 'app',
    enable_json_logging: bool = False,
    enable_audit_logging: bool = False,
    enable_error_email: bool = False,
    email_config: Optional[Dict[str, Any]] = None
) -> None:
    """
    设置日志系统

    Args:
        config_path: 日志配置文件路径，如果为None则使用默认配置
        default_level: 默认日志级别
        log_dir: 日志文件目录
        env_key: 环境变量名，用于覆盖配置文件路径
        backup_count: 保留的备份日志文件数量
        max_bytes: 单个日志文件的最大大小
        log_to_console: 是否将日志输出到控制台
        log_to_file: 是否将日志输出到文件
        app_name: 应用名称，用于生成日志文件名
        enable_json_logging: 是否启用JSON格式的日志
        enable_audit_logging: 是否启用审计日志
        enable_error_email: 是否启用错误邮件通知
        email_config: 邮件配置
    """
    # 从环境变量中获取配置路径
    config_env_path = os.getenv(env_key, None)
    if config_env_path:
        config_path = config_env_path

    # 如果有配置文件，从文件加载配置
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logging.config.dictConfig(config)
            logger = logging.getLogger(__name__)
            logger.info(f"从配置文件加载日志配置: {config_path}")
            return
        except Exception as e:
            print(f"无法从配置文件加载日志配置: {str(e)}")
            print(f"使用默认配置...")

    # 使用默认配置
    # 创建日志目录
    if log_to_file and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(default_level)

    # 清除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 配置日志格式
    formatter = ENHANCED_LOG_FORMATTER
    if enable_json_logging:
        formatter = JsonFormatter()

    # 添加控制台处理器
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(default_level)
        root_logger.addHandler(console_handler)

    # 添加文件处理器
    if log_to_file:
        # 主日志文件
        main_log_file = os.path.join(log_dir, f"{app_name}.log")
        file_handler = EnhancedRotatingFileHandler(
            filename=main_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8',
            archive_dir=os.path.join(log_dir, 'archives'),
            archive_prefix=app_name,
            compress_archives=True
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(default_level)
        root_logger.addHandler(file_handler)

        # 错误日志文件
        error_log_file = os.path.join(log_dir, f"{app_name}_error.log")
        error_handler = EnhancedRotatingFileHandler(
            filename=error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)

        # 审计日志文件
        if enable_audit_logging:
            audit_log_file = os.path.join(log_dir, f"{app_name}_audit.log")
            audit_handler = EnhancedRotatingFileHandler(
                filename=audit_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            audit_handler.setFormatter(formatter)
            audit_handler.setLevel(logging.INFO)
            audit_handler.addFilter(AuditLogFilter())
            root_logger.addHandler(audit_handler)

    # 添加邮件处理器
    if enable_error_email and email_config:
        # 创建SMTP处理器
        from logging.handlers import SMTPHandler

        mail_handler = SMTPHandler(
            mailhost=email_config.get('mailhost', 'localhost'),
            fromaddr=email_config.get(
                'fromaddr', f"{app_name}@{socket.getfqdn()}"),
            toaddrs=email_config.get('toaddrs', []),
            subject=email_config.get('subject', f"[{app_name}] 错误报告"),
            credentials=email_config.get('credentials'),
            secure=email_config.get('secure')
        )
        mail_handler.setFormatter(DETAILED_LOG_FORMATTER)
        mail_handler.setLevel(logging.ERROR)
        root_logger.addHandler(mail_handler)

    # 记录启动信息
    logger = logging.getLogger(__name__)
    logger.info(
        f"日志系统初始化完成，应用: {app_name}, 日志级别: {logging.getLevelName(default_level)}")
    logger.info(
        f"系统信息: {platform.system()} {platform.release()}, Python {platform.python_version()}")
    if log_to_file:
        logger.info(f"日志文件位置: {log_dir}")


def log_function_call(level: int = logging.DEBUG):
    """
    函数调用日志装饰器

    Args:
        level: 日志级别

    Returns:
        装饰器函数
    """
    def decorator(func):
        logger = logging.getLogger(func.__module__)

        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            arg_str = ', '.join([repr(a) for a in args] +
                                [f"{k}={repr(v)}" for k, v in kwargs.items()])

            # 记录函数调用
            logger.log(level, f"调用函数 {func_name}({arg_str})")

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # 记录函数返回
                logger.log(
                    level, f"函数 {func_name} 返回: {repr(result)}, 耗时: {execution_time:.6f}秒")
                return result
            except Exception as e:
                execution_time = time.time() - start_time

                # 记录函数异常
                logger.exception(
                    f"函数 {func_name} 抛出异常: {repr(e)}, 耗时: {execution_time:.6f}秒")
                raise

        return wrapper
    return decorator


def audit_log(
    audit_type: str,
    user: Optional[str] = None,
    resource: Optional[str] = None,
    action: Optional[str] = None,
    result: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    记录审计日志

    Args:
        audit_type: 审计类型
        user: 用户标识
        resource: 资源标识
        action: 操作名称
        result: 操作结果
        details: 详细信息
    """
    logger = logging.getLogger('audit')

    # 创建审计日志内容
    message = f"审计: {audit_type}"
    if user:
        message += f", 用户: {user}"
    if resource:
        message += f", 资源: {resource}"
    if action:
        message += f", 操作: {action}"
    if result:
        message += f", 结果: {result}"

    # 添加额外信息
    extra = {
        'audit_type': audit_type,
        'timestamp': datetime.datetime.now().isoformat()
    }

    if user:
        extra['user'] = user
    if resource:
        extra['resource'] = resource
    if action:
        extra['action'] = action
    if result:
        extra['result'] = result
    if details:
        extra['details'] = details

    # 记录审计日志
    logger.info(message, extra=extra)


def setup_production_logging(
    app_name: str,
    log_dir: str = '/var/log',
    config_path: Optional[str] = None,
    env_key: str = 'PROD_LOG_CONFIG',
    backup_count: int = 90,  # 保留3个月的日志
    max_bytes: int = 50 * 1024 * 1024,  # 50MB
    enable_json_logging: bool = True,
    enable_audit_logging: bool = True,
    enable_error_email: bool = True,
    email_config: Optional[Dict[str, Any]] = None,
    syslog_address: Optional[Union[str, Tuple[str, int]]] = None
) -> None:
    """
    设置生产环境日志

    Args:
        app_name: 应用名称
        log_dir: 日志目录
        config_path: 配置文件路径
        env_key: 环境变量名
        backup_count: 保留的日志文件数量
        max_bytes: 单个日志文件最大大小
        enable_json_logging: 是否启用JSON格式日志
        enable_audit_logging: 是否启用审计日志
        enable_error_email: 是否启用错误邮件通知
        email_config: 邮件配置
        syslog_address: 系统日志服务器地址
    """
    # 确保生产环境日志目录存在
    app_log_dir = os.path.join(log_dir, app_name)
    if not os.path.exists(app_log_dir):
        try:
            os.makedirs(app_log_dir)
        except PermissionError:
            # 如果没有权限创建目录，使用默认位置
            app_log_dir = os.path.join(
                os.path.expanduser('~'), '.logs', app_name)
            os.makedirs(app_log_dir, exist_ok=True)
            print(f"无权限访问 {log_dir}，使用备用日志目录: {app_log_dir}")

    # 创建归档目录
    archive_dir = os.path.join(app_log_dir, 'archives')
    os.makedirs(archive_dir, exist_ok=True)

    # 默认邮件配置（如果未提供）
    if enable_error_email and not email_config:
        email_config = {
            'mailhost': ('smtp.example.com', 587),
            'fromaddr': f"{app_name}@{socket.getfqdn()}",
            'toaddrs': ['admin@example.com'],
            'subject': f"[{app_name}] 生产环境错误报告",
            'credentials': ('username', 'password'),
            'secure': ()
        }

    # 创建基本配置
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] [%(process)d:%(thread)d] %(name)s - %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] [%(module)s:%(lineno)d] [%(process)d:%(thread)d] [%(function)s] %(name)s - %(message)s'
            },
            'json': {
                '()': 'logging_utils.JsonFormatter',
                'include_extra_fields': True
            }
        },
        'filters': {
            'audit': {
                '()': 'logging_utils.AuditLogFilter'
            }
        },
        'handlers': {
            'console': {
                'level': 'WARNING',
                'class': 'logging.StreamHandler',
                'formatter': 'json' if enable_json_logging else 'standard'
            },
            'file': {
                'level': 'INFO',
                'class': 'logging_utils.EnhancedRotatingFileHandler',
                'filename': os.path.join(app_log_dir, f"{app_name}.log"),
                'maxBytes': max_bytes,
                'backupCount': backup_count,
                'encoding': 'utf-8',
                'formatter': 'json' if enable_json_logging else 'standard',
                'archive_dir': archive_dir,
                'archive_prefix': app_name,
                'compress_archives': True
            },
            'error_file': {
                'level': 'ERROR',
                'class': 'logging_utils.EnhancedRotatingFileHandler',
                'filename': os.path.join(app_log_dir, f"{app_name}_error.log"),
                'maxBytes': max_bytes,
                'backupCount': backup_count,
                'encoding': 'utf-8',
                'formatter': 'detailed',
                'archive_dir': archive_dir,
                'archive_prefix': f"{app_name}_error",
                'compress_archives': True
            }
        },
        'loggers': {
            '': {  # 根日志记录器
                'handlers': ['console', 'file', 'error_file'],
                'level': 'INFO',
                'propagate': True
            }
        }
    }

    # 添加审计日志处理器
    if enable_audit_logging:
        config['handlers']['audit_file'] = {
            'level': 'INFO',
            'class': 'logging_utils.EnhancedRotatingFileHandler',
            'filename': os.path.join(app_log_dir, f"{app_name}_audit.log"),
            'maxBytes': max_bytes,
            'backupCount': backup_count,
            'encoding': 'utf-8',
            'formatter': 'json' if enable_json_logging else 'detailed',
            'filters': ['audit'],
            'archive_dir': archive_dir,
            'archive_prefix': f"{app_name}_audit",
            'compress_archives': True
        }

        # 添加审计日志记录器
        config['loggers']['audit'] = {
            'handlers': ['audit_file', 'console'],
            'level': 'INFO',
            'propagate': False
        }

    # 添加邮件处理器
    if enable_error_email and email_config:
        config['handlers']['email'] = {
            'level': 'ERROR',
            'class': 'logging.handlers.SMTPHandler',
            'mailhost': email_config.get('mailhost', 'localhost'),
            'fromaddr': email_config.get('fromaddr', f"{app_name}@{socket.getfqdn()}"),
            'toaddrs': email_config.get('toaddrs', []),
            'subject': email_config.get('subject', f"[{app_name}] 错误报告"),
            'credentials': email_config.get('credentials'),
            'secure': email_config.get('secure', ()),
            'formatter': 'detailed'
        }
        config['loggers']['']['handlers'].append('email')

    # 添加系统日志处理器
    if syslog_address:
        config['handlers']['syslog'] = {
            'level': 'WARNING',
            'class': 'logging.handlers.SysLogHandler',
            'address': syslog_address,
            'facility': 'local7',
            'formatter': 'json' if enable_json_logging else 'standard'
        }
        config['loggers']['']['handlers'].append('syslog')

    # 应用配置
    logging.config.dictConfig(config)

    # 记录启动信息
    logger = logging.getLogger(__name__)
    logger.info(f"生产环境日志系统初始化完成，应用: {app_name}")
    logger.info(
        f"系统信息: {platform.system()} {platform.release()}, Python {platform.python_version()}")
    logger.info(f"日志文件位置: {app_log_dir}")

    # 记录特性启用状态
    features = []
    if enable_json_logging:
        features.append("JSON日志")
    if enable_audit_logging:
        features.append("审计日志")
    if enable_error_email:
        features.append("错误邮件通知")
    if syslog_address:
        features.append("系统日志")

    if features:
        logger.info(f"已启用功能: {', '.join(features)}")


def configure_log_rotation(log_dir: str) -> None:
    """
    配置日志轮换，适用于使用logrotate进行管理

    Args:
        log_dir: 日志目录
    """
    # 创建logrotate配置
    config = f"""
# AI项目日志轮换配置
{log_dir}/*.log {{
    daily
    rotate 90
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root adm
    sharedscripts
    postrotate
        systemctl reload rsyslog >/dev/null 2>&1 || true
    endscript
}}
"""

    # 将配置写入文件
    try:
        config_path = '/tmp/ai_project_logrotate.conf'
        with open(config_path, 'w') as f:
            f.write(config)
        print(f"日志轮换配置已生成: {config_path}")
        print(f"请以管理员权限将此文件复制到 /etc/logrotate.d/ 目录下")
    except Exception as e:
        print(f"无法创建logrotate配置: {str(e)}")


def log_memory_usage(logger: logging.Logger, level: int = logging.DEBUG, prefix: str = "内存使用") -> None:
    """
    记录当前内存使用情况

    Args:
        logger: 日志记录器
        level: 日志级别
        prefix: 日志前缀
    """
    try:
        
        process = psutil.Process()
        memory_info = process.memory_info()

        # 获取内存使用情况
        rss_mb = memory_info.rss / (1024 * 1024)
        vms_mb = memory_info.vms / (1024 * 1024)

        # 获取系统内存情况
        system_memory = psutil.virtual_memory()
        system_memory_percent = system_memory.percent

        # 记录日志
        logger.log(
            level,
            f"{prefix}: RSS={rss_mb:.2f}MB, VMS={vms_mb:.2f}MB, 系统内存使用率={system_memory_percent:.1f}%",
            extra={
                'memory_rss_mb': rss_mb,
                'memory_vms_mb': vms_mb,
                'system_memory_percent': system_memory_percent
            }
        )
    except ImportError:
        logger.warning("无法记录内存使用情况，缺少psutil库")
    except Exception as e:
        logger.warning(f"记录内存使用情况时出错: {str(e)}")


class PerformanceLogger:
    """性能日志记录器，用于跟踪函数/代码块的执行时间和资源使用"""

    def __init__(
        self,
        logger: logging.Logger,
        task_name: str,
        level: int = logging.DEBUG,
        track_memory: bool = False
    ):
        """
        初始化性能日志记录器
        
        Args:
            logger: 日志记录器
            task_name: 任务名称
            level: 日志级别
            track_memory: 是否记录内存使用
        """
        self.logger = logger
        self.task_name = task_name
        self.level = level
        self.track_memory = track_memory
        self.start_time = None
        self.start_memory = None

    def __enter__(self):
        """进入上下文"""
        self.start_time = time.time()

        if self.track_memory:
            try:
                import psutil
                self.process = psutil.Process()
                self.start_memory = self.process.memory_info().rss
            except ImportError:
                self.logger.warning("无法跟踪内存使用，缺少psutil库")
                self.track_memory = False

        self.logger.log(self.level, f"开始执行: {self.task_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        duration = time.time() - self.start_time

        if exc_type is not None:
            # 任务出现异常
            self.logger.error(
                f"执行失败: {self.task_name}, 耗时: {duration:.6f}秒, 异常: {exc_type.__name__}: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb)
            )
        else:
            # 任务正常完成
            log_data = {
                'duration': duration,
                'task_name': self.task_name
            }

            # 记录内存使用情况
            if self.track_memory:
                try:
                    end_memory = self.process.memory_info().rss
                    memory_diff = end_memory - self.start_memory
                    memory_diff_mb = memory_diff / (1024 * 1024)

                    log_message = f"执行完成: {self.task_name}, 耗时: {duration:.6f}秒, 内存变化: {memory_diff_mb:+.2f}MB"
                    log_data['memory_diff_mb'] = memory_diff_mb
                except Exception as e:
                    log_message = f"执行完成: {self.task_name}, 耗时: {duration:.6f}秒"
                    self.logger.warning(f"获取内存使用情况时出错: {str(e)}")
            else:
                log_message = f"执行完成: {self.task_name}, 耗时: {duration:.6f}秒"

            self.logger.log(self.level, log_message, extra=log_data)

        return False  # 不抑制异常


if __name__ == "__main__":
    # 简单测试
    setup_logging(log_dir="test_logs", app_name="test_app")
    logger = get_logger(__name__)

    logger.debug("这是一条调试日志")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")

    try:
        result = 1 / 0
    except Exception as e:
        logger.exception("发生异常")

    # 测试上下文日志
    context_logger = logger.with_context(user_id="12345", session_id="abc123")
    context_logger.info("这是一条带上下文的日志")

    # 测试性能日志
    with PerformanceLogger(logger, "测试任务"):
        time.sleep(0.5)  # 模拟工作

    # 测试审计日志
    audit_log("CONFIG_CHANGE", user="admin",
              resource="system_settings", action="update", result="success")

    print("日志测试完成，请查看 test_logs 目录")