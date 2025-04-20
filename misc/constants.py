# -*- coding: utf-8 -*-
"""
常量定义模块

此模块集中定义了整个项目中使用的各种常量，包括配置参数、
错误码、状态码、系统默认值等。将常量统一管理可以提高代码
可维护性并简化配置管理流程。

版本: 1.0
作者: 窗口8
创建日期: 2025-04-19
"""

import os
from enum import Enum, auto

# ============================================================================
# 系统相关常量
# ============================================================================

# 版本信息
VERSION = '1.0.0'
BUILD_NUMBER = '20250419'
AUTHOR = '窗口8'

# 路径常量
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(ROOT_DIR, 'config')
DATA_DIR = os.path.join(ROOT_DIR, 'data')
LOGS_DIR = os.path.join(ROOT_DIR, 'logs')
TEMP_DIR = os.path.join(ROOT_DIR, 'temp')

# 文件常量
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
CREDENTIALS_FILE = os.path.join(CONFIG_DIR, 'credentials.json')
LOG_FILE = os.path.join(LOGS_DIR, 'system.log')

# 环境常量
ENV_DEV = 'development'
ENV_TEST = 'testing'
ENV_PROD = 'production'

# 默认超时设置（秒）
DEFAULT_TIMEOUT = 30
CONNECTION_TIMEOUT = 10
READ_TIMEOUT = 20
RETRY_TIMEOUT = 5

# ============================================================================
# API相关常量
# ============================================================================

# API状态码
class ApiStatus(Enum):
    SUCCESS = 200
    CREATED = 201
    ACCEPTED = 202
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    TIMEOUT = 408
    SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503
    
# API错误码
class ApiErrorCode(Enum):
    UNKNOWN_ERROR = 1000
    AUTHENTICATION_FAILED = 1001
    INVALID_PARAMETER = 1002
    RESOURCE_NOT_FOUND = 1003
    PERMISSION_DENIED = 1004
    RATE_LIMIT_EXCEEDED = 1005
    SERVICE_UNAVAILABLE = 1006
    NETWORK_ERROR = 1007
    TIMEOUT_ERROR = 1008
    DATA_FORMAT_ERROR = 1009
    RESOURCE_CONFLICT = 1010

# 内容类型
CONTENT_TYPE_JSON = 'application/json'
CONTENT_TYPE_XML = 'application/xml'
CONTENT_TYPE_FORM = 'application/x-www-form-urlencoded'
CONTENT_TYPE_MULTIPART = 'multipart/form-data'

# HTTP方法
HTTP_GET = 'GET'
HTTP_POST = 'POST'
HTTP_PUT = 'PUT'
HTTP_DELETE = 'DELETE'
HTTP_PATCH = 'PATCH'

# ============================================================================
# 核心模块常量
# ============================================================================

# 执行状态
class ExecutionStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    TIMEOUT = auto()

# 优先级级别
class PriorityLevel(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

# 日志级别
class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

# 缓存策略
class CacheStrategy(Enum):
    NO_CACHE = 0
    MEMORY_ONLY = 1
    DISK_ONLY = 2
    MEMORY_AND_DISK = 3

# 资源类型
class ResourceType(Enum):
    FILE = auto()
    DATABASE = auto()
    API = auto()
    CACHE = auto()
    MEMORY = auto()

# ============================================================================
# 模块特定常量
# ============================================================================

# NLP模块常量
NLP_DEFAULT_LANGUAGE = 'en'
NLP_DEFAULT_MODEL = 'base'
NLP_DEFAULT_EMBEDDING_SIZE = 768
NLP_MAX_TOKEN_LENGTH = 512
NLP_MAX_SEQUENCE_LENGTH = 1024

# 视觉模块常量
VISION_DEFAULT_IMAGE_SIZE = (224, 224)
VISION_DEFAULT_CONFIDENCE = 0.5
VISION_MAX_BATCH_SIZE = 32
VISION_SUPPORTED_FORMATS = ['jpg', 'jpeg', 'png', 'bmp', 'gif']

# 音频模块常量
AUDIO_DEFAULT_SAMPLE_RATE = 16000
AUDIO_DEFAULT_CHANNELS = 1
AUDIO_MAX_DURATION = 60  # 秒
AUDIO_SUPPORTED_FORMATS = ['wav', 'mp3', 'ogg', 'flac']

# 数据模块常量
DATA_MAX_BATCH_SIZE = 1000
DATA_DEFAULT_CHUNK_SIZE = 100
DATA_SUPPORTED_FORMATS = ['csv', 'json', 'xml', 'parquet', 'pickle']

# ============================================================================
# 测试相关常量
# ============================================================================

# 测试环境标识
TEST_ENV_LOCAL = 'local'
TEST_ENV_CI = 'ci'
TEST_ENV_STAGING = 'staging'

# 测试类型
class TestType(Enum):
    UNIT = auto()
    INTEGRATION = auto()
    FUNCTIONAL = auto()
    PERFORMANCE = auto()
    SECURITY = auto()

# 测试优先级
class TestPriority(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

# 测试状态
class TestStatus(Enum):
    PASSED = auto()
    FAILED = auto()
    SKIPPED = auto()
    ERROR = auto()

# 性能基准
PERFORMANCE_CPU_THRESHOLD = 70  # CPU使用率阈值（百分比）
PERFORMANCE_MEMORY_THRESHOLD = 1024  # 内存使用阈值（MB）
PERFORMANCE_RESPONSE_TIME_THRESHOLD = 500  # 响应时间阈值（毫秒）
PERFORMANCE_THROUGHPUT_THRESHOLD = 100  # 吞吐量阈值（请求/秒）

# ============================================================================
# 安全相关常量
# ============================================================================

# 密码策略
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 64
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGITS = True
PASSWORD_REQUIRE_SPECIAL = True
PASSWORD_MAX_AGE = 90  # 天

# 令牌设置
TOKEN_EXPIRY_ACCESS = 60 * 30  # 30分钟（秒）
TOKEN_EXPIRY_REFRESH = 60 * 60 * 24 * 7  # 7天（秒）
TOKEN_ALGORITHM = 'HS256'

# 安全限制
MAX_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCKOUT_DURATION = 60 * 15  # 15分钟（秒）
SESSION_TIMEOUT = 60 * 60 * 2  # 2小时（秒）
RATE_LIMIT_WINDOW = 60  # 1分钟（秒）
RATE_LIMIT_MAX_REQUESTS = 100  # 每窗口最大请求数

# ============================================================================
# UI相关常量
# ============================================================================

# 颜色主题
class ColorTheme(Enum):
    LIGHT = auto()
    DARK = auto()
    SYSTEM = auto()
    CUSTOM = auto()

# 页面布局
class PageLayout(Enum):
    SIMPLE = auto()
    STANDARD = auto()
    ADVANCED = auto()
    COMPACT = auto()

# 分页设置
PAGINATION_DEFAULT_PAGE_SIZE = 20
PAGINATION_MAX_PAGE_SIZE = 100
PAGINATION_DEFAULT_PAGE = 1

# 导航相关
DASHBOARD_PATH = '/dashboard'
PROFILE_PATH = '/profile'
SETTINGS_PATH = '/settings'
HELP_PATH = '/help'
LOGOUT_PATH = '/logout'

# ============================================================================
# 导出所有常量
# ============================================================================

__all__ = [
    # 版本信息
    'VERSION', 'BUILD_NUMBER', 'AUTHOR',
    
    # 路径常量
    'ROOT_DIR', 'CONFIG_DIR', 'DATA_DIR', 'LOGS_DIR', 'TEMP_DIR',
    
    # 文件常量
    'CONFIG_FILE', 'CREDENTIALS_FILE', 'LOG_FILE',
    
    # 环境常量
    'ENV_DEV', 'ENV_TEST', 'ENV_PROD',
    
    # 超时设置
    'DEFAULT_TIMEOUT', 'CONNECTION_TIMEOUT', 'READ_TIMEOUT', 'RETRY_TIMEOUT',
    
    # API状态和错误码
    'ApiStatus', 'ApiErrorCode',
    
    # 内容类型
    'CONTENT_TYPE_JSON', 'CONTENT_TYPE_XML', 'CONTENT_TYPE_FORM', 'CONTENT_TYPE_MULTIPART',
    
    # HTTP方法
    'HTTP_GET', 'HTTP_POST', 'HTTP_PUT', 'HTTP_DELETE', 'HTTP_PATCH',
    
    # 核心模块常量
    'ExecutionStatus', 'PriorityLevel', 'LogLevel', 'CacheStrategy', 'ResourceType',
    
    # NLP模块常量
    'NLP_DEFAULT_LANGUAGE', 'NLP_DEFAULT_MODEL', 'NLP_DEFAULT_EMBEDDING_SIZE',
    'NLP_MAX_TOKEN_LENGTH', 'NLP_MAX_SEQUENCE_LENGTH',
    
    # 视觉模块常量
    'VISION_DEFAULT_IMAGE_SIZE', 'VISION_DEFAULT_CONFIDENCE',
    'VISION_MAX_BATCH_SIZE', 'VISION_SUPPORTED_FORMATS',
    
    # 音频模块常量
    'AUDIO_DEFAULT_SAMPLE_RATE', 'AUDIO_DEFAULT_CHANNELS',
    'AUDIO_MAX_DURATION', 'AUDIO_SUPPORTED_FORMATS',
    
    # 数据模块常量
    'DATA_MAX_BATCH_SIZE', 'DATA_DEFAULT_CHUNK_SIZE', 'DATA_SUPPORTED_FORMATS',
    
    # 测试相关常量
    'TEST_ENV_LOCAL', 'TEST_ENV_CI', 'TEST_ENV_STAGING',
    'TestType', 'TestPriority', 'TestStatus',
    'PERFORMANCE_CPU_THRESHOLD', 'PERFORMANCE_MEMORY_THRESHOLD',
    'PERFORMANCE_RESPONSE_TIME_THRESHOLD', 'PERFORMANCE_THROUGHPUT_THRESHOLD',
    
    # 安全相关常量
    'PASSWORD_MIN_LENGTH', 'PASSWORD_MAX_LENGTH', 'PASSWORD_REQUIRE_UPPERCASE',
    'PASSWORD_REQUIRE_LOWERCASE', 'PASSWORD_REQUIRE_DIGITS', 'PASSWORD_REQUIRE_SPECIAL',
    'PASSWORD_MAX_AGE', 'TOKEN_EXPIRY_ACCESS', 'TOKEN_EXPIRY_REFRESH',
    'TOKEN_ALGORITHM', 'MAX_LOGIN_ATTEMPTS', 'ACCOUNT_LOCKOUT_DURATION',
    'SESSION_TIMEOUT', 'RATE_LIMIT_WINDOW', 'RATE_LIMIT_MAX_REQUESTS',
    
    # UI相关常量
    'ColorTheme', 'PageLayout', 'PAGINATION_DEFAULT_PAGE_SIZE',
    'PAGINATION_MAX_PAGE_SIZE', 'PAGINATION_DEFAULT_PAGE',
    'DASHBOARD_PATH', 'PROFILE_PATH', 'SETTINGS_PATH', 'HELP_PATH', 'LOGOUT_PATH',
]