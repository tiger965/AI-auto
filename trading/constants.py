""" "
模块名称：constants
功能描述：交易系统的常量定义
版本：1.0
创建日期：2025-04-20
作者：窗口9.1开发者
"""

import os
import logging

# 配置文件路径
TRADING_CONFIG_PATH = os.path.join(
    os.path.expanduser("~"), ".trading", "config.json")

# 默认设置
DEFAULT_TIMEFRAME = "5m"  # 5分钟K线
DEFAULT_STAKE_CURRENCY = "USDT"  # 默认交易币种
DEFAULT_STAKE_AMOUNT = 100.0  # 默认每笔交易金额
MAX_OPEN_TRADES = 3  # 默认最大同时开仓数量
LOG_LEVEL = logging.INFO  # 默认日志级别

# API状态码
API_STATUS_OK = 200
API_STATUS_ERROR = 500
API_STATUS_NOT_FOUND = 404
API_STATUS_BAD_REQUEST = 400
API_STATUS_UNAUTHORIZED = 401

# 交易方向
TRADE_DIRECTION_LONG = "long"
TRADE_DIRECTION_SHORT = "short"

# 交易状态
TRADE_STATUS_OPEN = "open"
TRADE_STATUS_CLOSED = "closed"
TRADE_STATUS_CANCELED = "canceled"

# GPT-Claude交互相关常量
GPT_CLAUDE_COMMUNICATION_TIMEOUT = 30  # GPT和Claude通信超时时间（秒）
MAX_STRATEGY_GENERATION_ATTEMPTS = 3  # 最大策略生成尝试次数
STRATEGY_TEMPLATE_PATH = "trading/gpt_claude/templates/strategy_templates.py"

# 回测相关常量
DEFAULT_BACKTEST_TIMEFRAME = "1d"  # 默认回测时间周期
DEFAULT_BACKTEST_TIMERANGE = "20230101-20240101"  # 默认回测时间范围

# 性能指标相关常量
MIN_ACCEPTABLE_SHARPE = 0.5  # 最小可接受夏普比率
TARGET_PROFIT_PERCENT = 5.0  # 目标利润百分比
MAX_ACCEPTABLE_DRAWDOWN = 20.0  # 最大可接受回撤百分比