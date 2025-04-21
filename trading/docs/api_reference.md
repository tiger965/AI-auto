量化交易模块API参考
介绍
本文档提供了量化交易模块 API 的全面参考，包含所有可用类、方法、端点和数据结构的详细信息。
目录

REST API 端点
交易API
策略界面
回测模块
优化模块
连接器模块
GPT-Claude 积分
配置
实用函数
UI 组件

REST API 端点
策略端点
获取/api/trading/strategies/
列出所有交易策略。
查询参数：

limit(int，可选)：返回策略的最大数量。默认值：10，最大值：100
offset(int，可选)：要跳过的策略数量。默认值：0
sort_by(字符串，可选)：排序依据字段。默认值："created_at"
sort_order(字符串，可选)：排序顺序（“asc”或“desc”）。默认值：“desc”

回复：
json[
  {
    "id": "strategy-001",
    "name": "BTC Trend Following",
    "description": "Simple trend following strategy for BTC/USDT",
    "created_at": "2023-06-01T10:00:00Z",
    "updated_at": "2023-06-02T14:30:00Z",
    "status": "active",
    "pairs": ["BTC/USDT"],
    "timeframe": "1h"
  },
  ...
]
POST /api/trading/strategies/
创建新的交易策略。
请求正文：
json{
  "name": "My New Strategy",
  "description": "Description of my strategy",
  "pairs": ["BTC/USDT"],
  "timeframe": "4h",
  "indicators": [
    {"name": "SMA", "params": {"length": 50}},
    {"name": "RSI", "params": {"length": 14}}
  ],
  "entry_conditions": [
    {"indicator": "RSI", "condition": "<", "value": 30}
  ],
  "exit_conditions": [
    {"indicator": "RSI", "condition": ">", "value": 70}
  ]
}
回复：
json{
  "id": "strategy-003",
  "name": "My New Strategy",
  "description": "Description of my strategy",
  "created_at": "2023-06-05T11:30:00Z",
  "updated_at": "2023-06-05T11:30:00Z",
  "status": "draft",
  "pairs": ["BTC/USDT"],
  "timeframe": "4h",
  "indicators": [
    {"name": "SMA", "params": {"length": 50}},
    {"name": "RSI", "params": {"length": 14}}
  ],
  "entry_conditions": [
    {"indicator": "RSI", "condition": "<", "value": 30}
  ],
  "exit_conditions": [
    {"indicator": "RSI", "condition": ">", "value": 70}
  ]
}
获取/api/trading/strategies/{strategy_id}
通过ID获取交易策略。
路径参数：

strategy_id（字符串，必需）：要检索的策略的 ID

回复：
json{
  "id": "strategy-001",
  "name": "BTC Trend Following",
  "description": "Simple trend following strategy for BTC/USDT",
  "created_at": "2023-06-01T10:00:00Z",
  "updated_at": "2023-06-02T14:30:00Z",
  "status": "active",
  "pairs": ["BTC/USDT"],
  "timeframe": "1h",
  "indicators": [
    {"name": "SMA", "params": {"length": 50}},
    {"name": "RSI", "params": {"length": 14}}
  ],
  "entry_conditions": [
    {"indicator": "RSI", "condition": "<", "value": 30}
  ],
  "exit_conditions": [
    {"indicator": "RSI", "condition": ">", "value": 70}
  ]
}
PUT /api/trading/strategies/{strategy_id}
更新交易策略。
路径参数：

strategy_id（字符串，必需）：要更新的策略的 ID

请求正文：
json{
  "name": "Updated Strategy Name",
  "description": "Updated description",
  "indicators": [
    {"name": "SMA", "params": {"length": 100}},
    {"name": "RSI", "params": {"length": 14}}
  ]
}
回复：
json{
  "id": "strategy-001",
  "name": "Updated Strategy Name",
  "description": "Updated description",
  "created_at": "2023-06-01T10:00:00Z",
  "updated_at": "2023-06-05T15:45:00Z",
  "status": "active",
  "pairs": ["BTC/USDT"],
  "timeframe": "1h",
  "indicators": [
    {"name": "SMA", "params": {"length": 100}},
    {"name": "RSI", "params": {"length": 14}}
  ],
  "entry_conditions": [
    {"indicator": "RSI", "condition": "<", "value": 30}
  ],
  "exit_conditions": [
    {"indicator": "RSI", "condition": ">", "value": 70}
  ]
}
删除 /api/trading/strategies/{strategy_id}
删除交易策略。
路径参数：

strategy_id(字符串，必需)：要删除的策略的 ID

回复：
json{
  "detail": "Strategy deleted successfully"
}
回测端点
POST /api/trading/backtest/
对策略进行回溯测试。
请求正文：
json{
  "strategy_id": "strategy-001",
  "timeframe": "1h",
  "pairs": ["BTC/USDT"],
  "start_date": "2023-01-01T00:00:00Z",
  "end_date": "2023-06-01T00:00:00Z",
  "initial_capital": 10000.0,
  "fee_rate": 0.1,
  "leverage": 1.0
}
回复：
json{
  "id": "backtest-001",
  "strategy_id": "strategy-001",
  "status": "running",
  "created_at": "2023-06-05T16:00:00Z",
  "config": {
    "strategy_id": "strategy-001",
    "timeframe": "1h",
    "pairs": ["BTC/USDT"],
    "start_date": "2023-01-01T00:00:00Z",
    "end_date": "2023-06-01T00:00:00Z",
    "initial_capital": 10000.0,
    "fee_rate": 0.1,
    "leverage": 1.0
  },
  "estimated_completion": "2023-06-05T16:10:00Z"
}
获取/api/trading/backtest/{backtest_id}
通过 ID 获取回测。
路径参数：

backtest_id（字符串，必需）：要检索的回测的 ID

回复：
json{
  "id": "backtest-001",
  "strategy_id": "strategy-001",
  "status": "completed",
  "created_at": "2023-06-05T16:00:00Z",
  "completed_at": "2023-06-05T16:08:30Z",
  "config": {
    "strategy_id": "strategy-001",
    "timeframe": "1h",
    "pairs": ["BTC/USDT"],
    "start_date": "2023-01-01T00:00:00Z",
    "end_date": "2023-06-01T00:00:00Z",
    "initial_capital": 10000.0
  },
  "results": {
    "total_profit": 2450.75,
    "profit_percentage": 24.5,
    "win_rate": 62.5,
    "total_trades": 48,
    "max_drawdown": 15.7,
    "sharpe_ratio": 1.42,
    "sortino_ratio": 2.18,
    "calmar_ratio": 1.56,
    "profit_factor": 1.87,
    "expectancy": 72.34,
    "avg_trade_duration": "14.3 hours",
    "best_trade": 520.75,
    "worst_trade": -310.25
  }
}
优化终点
POST /api/trading/optimize/
针对策略运行超参数优化。
请求正文：
json{
  "strategy_id": "strategy-001",
  "timeframe": "1h",
  "pairs": ["BTC/USDT"],
  "start_date": "2023-01-01T00:00:00Z",
  "end_date": "2023-06-01T00:00:00Z",
  "initial_capital": 10000.0,
  "parameter_space": {
    "sma_length": {"min": 10, "max": 100, "step": 10},
    "rsi_length": {"min": 7, "max": 21, "step": 1},
    "rsi_oversold": {"min": 20, "max": 40, "step": 5},
    "rsi_overbought": {"min": 60, "max": 80, "step": 5}
  },
  "optimization_objective": "sharpe_ratio",
  "max_trials": 100
}
回复：
json{
  "id": "optimize-001",
  "strategy_id": "strategy-001",
  "status": "running",
  "created_at": "2023-06-05T17:00:00Z",
  "config": {
    "strategy_id": "strategy-001",
    "timeframe": "1h",
    "pairs": ["BTC/USDT"],
    "start_date": "2023-01-01T00:00:00Z",
    "end_date": "2023-06-01T00:00:00Z",
    "initial_capital": 10000.0,
    "parameter_space": {
      "sma_length": {"min": 10, "max": 100, "step": 10},
      "rsi_length": {"min": 7, "max": 21, "step": 1},
      "rsi_oversold": {"min": 20, "max": 40, "step": 5},
      "rsi_overbought": {"min": 60, "max": 80, "step": 5}
    },
    "optimization_objective": "sharpe_ratio",
    "max_trials": 100
  },
  "estimated_completion": "2023-06-05T18:30:00Z"
}
获取/api/trading/optimize/{optimization_id}
通过ID获取优化作业。
路径参数：

optimization_id（字符串，必需）：要检索的优化的 ID

回复：
json{
  "id": "optimize-001",
  "strategy_id": "strategy-001",
  "status": "completed",
  "created_at": "2023-06-05T17:00:00Z",
  "completed_at": "2023-06-05T18:25:45Z",
  "config": {
    "strategy_id": "strategy-001",
    "timeframe": "1h",
    "pairs": ["BTC/USDT"],
    "start_date": "2023-01-01T00:00:00Z",
    "end_date": "2023-06-01T00:00:00Z",
    "initial_capital": 10000.0,
    "parameter_space": {
      "sma_length": {"min": 10, "max": 100, "step": 10},
      "rsi_length": {"min": 7, "max": 21, "step": 1},
      "rsi_oversold": {"min": 20, "max": 40, "step": 5},
      "rsi_overbought": {"min": 60, "max": 80, "step": 5}
    },
    "optimization_objective": "sharpe_ratio",
    "max_trials": 100
  },
  "results": {
    "best_parameters": {
      "sma_length": 50,
      "rsi_length": 14,
      "rsi_oversold": 30,
      "rsi_overbought": 70
    },
    "best_score": 1.87,
    "trials_completed": 100,
    "optimization_time": 5125.6
  }
}
实时交易终端
POST /api/trading/trading/start
开始根据策略进行实时交易。
请求正文：
json{
  "strategy_id": "strategy-001",
  "pairs": ["BTC/USDT"],
  "timeframe": "1h",
  "stake_amount": 100.0,
  "max_open_trades": 3,
  "exchange": "binance",
  "dry_run": true
}
回复：
json{
  "id": "session-001",
  "strategy_id": "strategy-001",
  "status": "running",
  "started_at": "2023-06-05T19:00:00Z",
  "config": {
    "strategy_id": "strategy-001",
    "pairs": ["BTC/USDT"],
    "timeframe": "1h",
    "stake_amount": 100.0,
    "max_open_trades": 3,
    "exchange": "binance",
    "dry_run": true
  }
}
POST /api/trading/trading/stop
停止实时交易会话。
请求正文：
json{
  "session_id": "session-001"
}
回复：
json{
  "id": "session-001",
  "strategy_id": "strategy-001",
  "status": "stopped",
  "started_at": "2023-06-05T19:00:00Z",
  "stopped_at": "2023-06-05T20:30:00Z"
}
获取/api/trading/trading/status
获取所有活跃交易时段的状态。
回复：
json{
  "active_sessions": 1,
  "sessions": [
    {
      "id": "session-001",
      "strategy_id": "strategy-001",
      "status": "running",
      "started_at": "2023-06-05T19:00:00Z",
      "pairs": ["BTC/USDT"],
      "current_positions": [
        {
          "pair": "BTC/USDT",
          "amount": 0.25,
          "entry_price": 16750.0,
          "current_price": 16950.0,
          "profit": 50.0,
          "profit_percentage": 1.19
        }
      ],
      "last_trades": [
        {
          "pair": "BTC/USDT",
          "type": "buy",
          "amount": 0.25,
          "price": 16750.0,
          "timestamp": "2023-06-05T19:15:00Z"
        }
      ]
    }
  ]
}
数据端点
获取/api/trading/data/pairs
列出所有可用的交易对。
回复：
json[
  "BTC/USDT",
  "ETH/USDT",
  "SOL/USDT",
  "ADA/USDT",
  "XRP/USDT",
  "DOT/USDT",
  "AVAX/USDT",
  "BNB/USDT"
]
获取/api/trading/data/timeframes
列出所有可用的时间范围。
回复：
json[
  "1m",
  "5m",
  "15m",
  "30m",
  "1h",
  "4h",
  "1d",
  "1w"
]
获取/api/trading/data/candles
获取历史蜡烛数据。
查询参数：

pair(字符串，必需)：交易对（例如 BTC/USDT）
timeframe（字符串，必需）：时间范围（例如 1 小时）
start_time（字符串，必需）：开始时间（ISO 格式）
end_time（字符串，必需）：结束时间（ISO 格式）
limit(int，可选)：蜡烛的最大数量。默认值：1000，最大值：5000

回复：
json[
  {
    "timestamp": "2023-01-01T00:00:00Z",
    "open": 16500.0,
    "high": 16550.0,
    "low": 16480.0,
    "close": 16520.0,
    "volume": 1250.75
  },
  {
    "timestamp": "2023-01-01T01:00:00Z",
    "open": 16520.0,
    "high": 16580.0,
    "low": 16510.0,
    "close": 16570.0,
    "volume": 1320.50
  }
]
GPT-Claude 集成端点
POST /api/trading/gpt-claude/generate-strategy
使用 GPT-Claude 生成交易策略。
请求正文：
json{
  "name": "AI Generated Strategy",
  "description": "Generate a trend following strategy for crypto",
  "pairs": ["BTC/USDT", "ETH/USDT"],
  "timeframe": "4h",
  "risk_level": "medium",
  "strategy_type": "trend_following",
  "include_indicators": ["RSI", "MACD"]
}
回复：
json{
  "id": "strategy-gpt-001",
  "name": "GPT Generated: AI Generated Strategy",
  "description": "Strategy generated by GPT-Claude based on user parameters",
  "created_at": "2023-06-05T21:30:00Z",
  "updated_at": "2023-06-05T21:30:00Z",
  "status": "draft",
  "pairs": ["BTC/USDT", "ETH/USDT"],
  "timeframe": "4h",
  "indicators": [
    {"name": "SMA", "params": {"length": 50}},
    {"name": "RSI", "params": {"length": 14}},
    {"name": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}}
  ],
  "entry_conditions": [
    {"indicator": "RSI", "condition": "<", "value": 30},
    {"indicator": "MACD", "condition": "cross_above", "value": "signal"}
  ],
  "exit_conditions": [
    {"indicator": "RSI", "condition": ">", "value": 70},
    {"indicator": "MACD", "condition": "cross_below", "value": "signal"}
  ],
  "generation_params": {
    "name": "AI Generated Strategy",
    "description": "Generate a trend following strategy for crypto",
    "pairs": ["BTC/USDT", "ETH/USDT"],
    "timeframe": "4h",
    "risk_level": "medium",
    "strategy_type": "trend_following",
    "include_indicators": ["RSI", "MACD"]
  }
}
POST /api/trading/gpt-claude/improve-strategy
使用 GPT-Claude 改进现有策略。
请求正文：
json{
  "strategy_id": "strategy-001",
  "name": "Improved Strategy",
  "description": "Improve my strategy to handle volatile markets better",
  "pairs": ["BTC/USDT"],
  "timeframe": "1h",
  "feedback": "The strategy performs poorly during high volatility periods"
}
回复：
json{
  "id": "strategy-001-improved",
  "name": "Improved: Improved Strategy",
  "description": "Strategy improved by GPT-Claude based on user feedback",
  "created_at": "2023-06-05T22:00:00Z",
  "updated_at": "2023-06-05T22:00:00Z",
  "status": "draft",
  "pairs": ["BTC/USDT"],
  "timeframe": "1h",
  "indicators": [
    {"name": "SMA", "params": {"length": 50}},
    {"name": "RSI", "params": {"length": 14}},
    {"name": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}},
    {"name": "ATR", "params": {"length": 14}}
  ],
  "entry_conditions": [
    {"indicator": "RSI", "condition": "<", "value": 30},
    {"indicator": "MACD", "condition": "cross_above", "value": "signal"},
    {"indicator": "ATR", "condition": "<", "value": "historical_percentile(75)"}
  ],
  "exit_conditions": [
    {"indicator": "RSI", "condition": ">", "value": 70},
    {"indicator": "MACD", "condition": "cross_below", "value": "signal"},
    {"indicator": "ATR", "condition": ">", "value": "historical_percentile(90)"}
  ],
  "improvement_params": {
    "strategy_id": "strategy-001",
    "name": "Improved Strategy",
    "description": "Improve my strategy to handle volatile markets better",
    "pairs": ["BTC/USDT"],
    "timeframe": "1h",
    "feedback": "The strategy performs poorly during high volatility periods"
  }
}
交易API
TradingAPI类
交易系统的主界面。
Pythonfrom trading.trading_api import TradingAPI

# Initialize the API
trading_api = TradingAPI()

# Load a strategy
strategy = trading_api.load_strategy("strategy-001")

# Run a backtest
backtest_config = {
    "timeframe": "1h",
    "pairs": ["BTC/USDT"],
    "start_date": "2023-01-01T00:00:00Z",
    "end_date": "2023-06-01T00:00:00Z",
    "initial_capital": 10000.0
}
backtest_result = trading_api.run_backtest(strategy, backtest_config)

# Start live trading
trading_config = {
    "pairs": ["BTC/USDT"],
    "timeframe": "1h",
    "stake_amount": 100.0,
    "max_open_trades": 3,
    "exchange": "binance",
    "dry_run": True
}
trading_session = trading_api.start_trading(strategy, trading_config)
方法
load_strategy(strategy_id: str) -> Strategy
通过策略 ID 加载策略。
参数：

strategy_id(str): 要加载的策略的ID

返回：

Strategy：已加载的策略对象

save_strategy(strategy: Strategy) -> str
保存策略。
参数：

strategy（策略）：保存策略

返回：

str：已保存策略的ID

run_backtest(strategy: Strategy, config: dict) -> dict
对策略进行回溯测试。
参数：

strategy（策略）：回测策略
config(dict): 回测配置

返回：

dict：回测结果

optimize_strategy(strategy: Strategy, parameter_space: dict, objective: str, max_trials: int = 100) -> dict
优化策略的参数。
参数：

strategy（策略）：优化策略
parameter_space(dict): 要搜索的参数空间
objective(str): 优化目标（例如，“profit”，“sharpe_ratio”）
max_trials(int，可选)：最大试验次数。默认值：100

返回：

dict：优化结果

start_trading(strategy: Strategy, config: dict) -> str
开始根据策略进行实时交易。
参数：

strategy（策略）：要使用的策略
config(dict): 交易配置

返回：

str：交易时段的ID

stop_trading(session_id: str) -> bool
停止实时交易会话。
参数：

session_id(str): 需要停止的交易时段的ID

返回：

bool：如果会话已成功停止，则为 True，否则为 False

get_trading_status() -> dict
获取所有活跃交易时段的状态。
返回：

dict：所有活跃交易时段的状态信息

generate_strategy_with_gpt(params: dict) -> Strategy
使用 GPT-Claude 生成交易策略。
参数：

params(dict): 策略生成的参数

返回：

Strategy：生成的策略

improve_strategy_with_gpt(strategy: Strategy, feedback: str) -> Strategy
使用 GPT-Claude 改进策略。
参数：

strategy（策略）：改进策略
feedback(str): 改进反馈

返回：

Strategy：改进策略

策略界面
策略类
所有交易策略的基类，与 Freqtrade 的策略界面兼容。
Pythonfrom trading.strategies.templates.basic_strategy import BasicStrategy

class MyCustomStrategy(BasicStrategy):
    """
    My custom trading strategy.
    """
    
    def __init__(self):
        """
        Initialize the strategy.
        """
        self.name = "My Custom Strategy"
        self.timeframe = "1h"
        self.minimal_roi = {
            "0": 0.1,
            "30": 0.05,
            "60": 0.02,
            "120": 0
        }
        self.stoploss = -0.1
        self.trailing_stop = False
        
    def populate_indicators(self, dataframe, metadata):
        """
        Generate indicators for the strategy.
        
        Args:
            dataframe: OHLCV dataframe
            metadata: Additional data (e.g., pair)
            
        Returns:
            DataFrame with indicators
        """
        # Add SMA indicator
        dataframe['sma50'] = ta.SMA(dataframe, timeperiod=50)
        
        # Add RSI indicator
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        return dataframe
    
    def populate_entry_trend(self, dataframe, metadata):
        """
        Generate entry signals.
        
        Args:
            dataframe: DataFrame with indicators
            metadata: Additional data (e.g., pair)
            
        Returns:
            DataFrame with entry signals
        """
        dataframe.loc[
            (
                (dataframe['rsi'] < 30) &
                (dataframe['close'] > dataframe['sma50'])
            ),
            'enter_long'] = 1
        
        return dataframe
    
    def populate_exit_trend(self, dataframe, metadata):
        """
        Generate exit signals.
        
        Args:
            dataframe: DataFrame with indicators
            metadata: Additional data (e.g., pair)
            
        Returns:
            DataFrame with exit signals
        """
        dataframe.loc[
            (
                (dataframe['rsi'] > 70)
            ),
            'exit_long'] = 1
        
        return dataframe
必需方法
populate_indicators(dataframe, metadata) -> DataFrame
为策略生成指标。
参数：

dataframe（数据框）：OHLCV 数据框
metadata(dict): 附加数据（例如，pair）

返回：

DataFrame：带有指标的 DataFrame

populate_entry_trend(dataframe, metadata) -> DataFrame
产生进入信号。
参数：

dataframe（DataFrame）：带有指标的 DataFrame
metadata(dict): 附加数据（例如，pair）

返回：

DataFrame：带有进入信号的数据框

populate_exit_trend(dataframe, metadata) -> DataFrame
生成退出信号。
参数：

dataframe（DataFrame）：带有指标的 DataFrame
metadata(dict): 附加数据（例如，pair）

返回：

DataFrame：带有退出信号的数据帧

可选方法
populate_buy_trend(dataframe, metadata) -> DataFrame
与 Freqtrade 兼容的旧方法。请使用populate_entry_trend。
populate_sell_trend(dataframe, metadata) -> DataFrame
与 Freqtrade 兼容的旧方法。请使用populate_exit_trend。
回测模块
BacktestEngine 类
回测策略的主要类。
Pythonfrom trading.backtesting.backtest_engine import BacktestEngine
from trading.strategies.templates.basic_strategy import BasicStrategy

# Initialize backtest engine
backtest_engine = BacktestEngine()

# Load a strategy
strategy = BasicStrategy()

# Configure backtest
config = {
    "timeframe": "1h",
    "pairs": ["BTC/USDT"],
    "start_date": "2023-01-01T00:00:00Z",
    "end_date": "2023-06-01T00:00:00Z",
    "initial_capital": 10000.0
}

# Run backtest
results = backtest_engine.run(strategy, config)

# Analyze results
performance = backtest_engine.analyze_performance(results)
方法
run(strategy, config) -> dict
对策略进行回溯测试。
参数：

strategy（策略）：回测策略
config(dict): 回测配置

返回：

dict：回测结果

analyze_performance(results) -> dict
分析回测表现。
参数：

results(dict): 回测结果

返回：

dict：绩效指标

plot_equity_curve(results, output_file=None) -> None
绘制股权曲线。
参数：

results(dict): 回测结果
output_file（str，可选）：保存图的路径

compare_strategies(strategies, config) -> dict
比较多种策略。
参数：

strategies（列表）：要比较的策略列表
config(dict): 回测配置

返回：

dict：比较结果

优化模块
HyperOptimization 类
超参数优化的主要类。
Pythonfrom trading.optimization.hyperopt import HyperOptimization
from trading.strategies.templates.basic_strategy import BasicStrategy

# Initialize optimization engine
hyperopt = HyperOptimization()

# Load a strategy
strategy = BasicStrategy()

# Define parameter space
parameter_space = {
    "sma_length": {"min": 10, "max": 100, "step": 10},
    "rsi_length": {"min": 7, "max": 21, "step": 1},
    "rsi_oversold": {"min": 20, "max": 40, "step": 5},
    "rsi_overbought": {"min": 60, "max": 80, "step": 5}
}

# Configure optimization
config = {
    "timeframe": "1h",
    "pairs": ["BTC/USDT"],
    "start_date": "2023-01-01T00:00:00Z",
    "end_date": "2023-06-01T00:00:00Z",
    "initial_capital": 10000.0
}

# Run optimization
results = hyperopt.optimize(strategy, parameter_space, "sharpe_ratio", config, max_trials=100)

# Get best parameters
best_params = results["best_parameters"]
方法
optimize(strategy, parameter_space, objective, config, max_trials=100) -> dict
优化策略的参数。
参数：

strategy（策略）：优化策略
parameter_space(dict): 要搜索的参数空间
objective(str): 优化目标（例如，“profit”，“sharpe_ratio”）
config(dict): 回测配置
max_trials(int，可选)：最大试验次数。默认值：100

返回：

dict：优化结果

apply_parameters(strategy, parameters) -> Strategy
将参数应用于策略。
参数：

strategy（策略）：更新策略
parameters(dict): 要应用的参数

返回：

Strategy：更新后的策略

plot_optimization_results(results, output_file=None) -> None
绘制优化结果。
参数：

results(dict): 优化结果
output_file（str，可选）：保存图的路径

连接器模块
BaseConnector 类
交换连接器的基类。
Pythonfrom trading.connectors.base_connector import BaseConnector

class MyCustomConnector(BaseConnector):
    """
    My custom exchange connector.
    """
    
    def __init__(self, api_key=None, api_secret=None):
        """
        Initialize the connector.
        
        Args:
            api_key: API key for the exchange
            api_secret: API secret for the exchange
        """
        super().__init__()
        self.name = "MyExchange"
        self.api_key = api_key
        self.api_secret = api_secret
        
    def get_historical_data(self, pair, timeframe, since, limit=None):
        """
        Get historical OHLCV data.
        
        Args:
            pair: Trading pair
            timeframe: Timeframe
            since: Start time
            limit: Maximum number of candles
            
        Returns:
            List of OHLCV candles
        """
        # Implementation for fetching historical data
        pass
    
    def create_order(self, pair, order_type, side, amount, price=None):
        """
        Create an order.
        
        Args:
            pair: Trading pair
            order_type: Order type (e.g., "limit", "market")
            side: Order side (e.g., "buy", "sell")
            amount: Order amount
            price: Order price (required for limit orders)
            
        Returns:
            Order information
        """
        # Implementation for creating an order
        pass
方法
get_historical_data(pair, timeframe, since, limit=None) -> list
获取历史 OHLCV 数据。
参数：

pair(str): 交易对
timeframe(str): 时间范围
since(int/str): 开始时间
limit（int，可选）：蜡烛的最大数量

返回：

list: OHLCV 蜡烛图列表

create_order(pair, order_type, side, amount, price=None) -> dict
创建订单。
参数：

pair(str): 交易对
order_type(str): 订单类型（例如，“限价”、“市价”）
side(str): 订单方（例如，“买入”、“卖出”）
amount(浮点数): 订单金额
price(浮动，可选)：订单价格（限价订单必填）

返回：

dict：订单信息

get_balance() -> dict
获取账户余额。
返回：

dict：账户余额

get_open_orders(pair=None) -> list
获取未结订单。
参数：

pair(str，可选): 交易对

返回：

list：未结订单

cancel_order(order_id) -> bool
取消订单。
参数：

order_id(str): 订单 ID

返回：

bool：如果订单取消成功则为 True，否则为 False

GPT-Claude 积分
沟通类
与 GPT-Claude 进行通信的主要类。
Pythonfrom trading.gpt_claude.communication import Communication

# Initialize communication
communication = Communication()

# Generate a strategy
strategy_params = {
    "name": "AI Generated Strategy",
    "description": "Generate a trend following strategy for crypto",
    "pairs": ["BTC/USDT", "ETH/USDT"],
    "timeframe": "4h",
    "risk_level": "medium",
    "strategy_type": "trend_following",
    "include_indicators": ["RSI", "MACD"]
}
strategy = communication.generate_strategy(strategy_params)

# Improve a strategy
feedback = "The strategy performs poorly during high volatility periods"
improved_strategy = communication.improve_strategy(strategy, feedback)
方法
generate_strategy(params) -> dict
使用 GPT-Claude 生成交易策略。
参数：

params(dict): 策略生成的参数

返回：

dict：生成的策略

improve_strategy(strategy, feedback) -> dict
使用 GPT-Claude 改进现有策略。
参数：

strategy(dict): 改进策略
feedback(str): 改进反馈

返回：

dict：改进策略

analyze_performance(results) -> str
分析绩效结果。
参数：

results(dict): 绩效结果

返回：

str：结果分析

配置
DefaultConfig 类
交易系统的默认配置。
Pythonfrom trading.config.default_config import DefaultConfig

# Load default configuration
config = DefaultConfig()

# Get configuration value
timeframe = config.get("timeframe")

# Set configuration value
config.set("timeframe", "4h")

# Save configuration
config.save("my_config.json")

# Load configuration
config.load("my_config.json")
方法
get(key, default=None) -> Any
获取配置值。
参数：

key(str): 配置键
default（任意，可选）：如果未找到键，则使用默认值

返回：

Any：配置值

set(key, value) -> None
设置配置值。
参数：

key(str): 配置键
value（任意）：配置值

save(path) -> bool
将配置保存到文件。
参数：

path(str): 保存配置的路径

返回：

bool：如果配置保存成功则为 True，否则为 False

load(path) -> bool
从文件加载配置。
参数：

path(str): 从中加载配置的路径

返回：

bool：如果配置加载成功则为 True，否则为 False

实用函数
转换器模块
用于数据转换的实用函数。
Pythonfrom trading.utils.converters import (
    timeframe_to_seconds,
    seconds_to_timeframe,
    ohlcv_to_dataframe,
    dataframe_to_ohlcv
)

# Convert timeframe to seconds
seconds = timeframe_to_seconds("1h")  # 3600

# Convert seconds to timeframe
timeframe = seconds_to_timeframe(3600)  # "1h"

# Convert OHLCV data to DataFrame
ohlcv_data = [
    [1609459200000, 16500.0, 16550.0, 16480.0, 16520.0, 1250.75],
    [1609462800000, 16520.0, 16580.0, 16510.0, 16570.0, 1320.50]
]
dataframe = ohlcv_to_dataframe(ohlcv_data)

# Convert DataFrame to OHLCV data
ohlcv_data = dataframe_to_ohlcv(dataframe)
验证器模块
用于数据验证的实用函数。
Pythonfrom trading.utils.validators import (
    validate_strategy,
    validate_backtest_config,
    validate_optimization_config,
    validate_trading_config
)

# Validate a strategy
errors = validate_strategy(strategy)
if errors:
    print("Strategy validation errors:", errors)

# Validate backtest configuration
errors = validate_backtest_config(config)
if errors:
    print("Backtest configuration errors:", errors)
UI 组件
StrategyViewer组件
使用 TradingView 风格图表可视化交易策略的组件。
Pythonfrom ui.trading.components.strategy_viewer import StrategyViewer

# Initialize the strategy viewer
viewer = StrategyViewer(strategy_id="strategy-001")

# Set the timeframe
viewer.set_timeframe("4h")

# Set the trading pair
viewer.set_pair("ETH/USDT")

# Update chart configuration
viewer.update_chart_config({
    "theme": "dark",
    "show_volume": True,
    "chart_type": "candles"
})

# Add an indicator
viewer.add_indicator({
    "name": "Bollinger Bands",
    "params": {"length": 20, "stddev": 2},
    "colors": {
        "upper": "#00FF00",
        "middle": "#FFFFFF",
        "lower": "#FF0000"
    },
    "visible": True,
    "panel": "main"
})

# Render the chart
chart_data = viewer.render()
PerformanceDashboard 组件
用于可视化交易绩效指标的仪表板组件。
Pythonfrom ui.trading.components.performance_dashboard import PerformanceDashboard

# Initialize the performance dashboard
dashboard = PerformanceDashboard(strategy_id="strategy-001")

# Set the time range
dashboard.set_time_range("3M")

# Add a metric
dashboard.add_metric("calmar_ratio")

# Update the layout
dashboard.update_layout({
    "sections": [
        {
            "title": "Performance Overview",
            "width": "100%",
            "components": ["kpi_cards", "equity_chart"]
        }
    ]
})

# Render the dashboard
dashboard_data = dashboard.render()

# Export a performance report
dashboard.export_performance_report("performance_report.pdf")
