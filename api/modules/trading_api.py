# api/modules/trading_api.py
"""量化交易API模块 - Window 9"""

from config import get_config
import sys
import os
import json
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(
    0, os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
)

# 导入配置


class TradingAPI:
    """量化交易API，负责与Freqtrade交互"""

    def __init__(self):
        """初始化交易API"""
        self.config = get_config()
        self.trading_enabled = self.config.get(
            "modules", {}).get("trading", False)
        self.strategies = {}
        self.active_trades = {}

        print(
            f"量化交易API初始化完成，状态: {'启用' if self.trading_enabled else '禁用'}"
        )

    def register_strategy(self, strategy_id, strategy_config):
        """注册交易策略"""
        if not self.trading_enabled:
            print("交易模块已禁用，无法注册策略")
            return False

        if strategy_id in self.strategies:
            print(f"警告: 策略 '{strategy_id}' 已存在，将被覆盖")

        self.strategies[strategy_id] = {
            "id": strategy_id,
            "config": strategy_config,
            "created_at": datetime.now().isoformat(),
            "status": "registered",
            "performance": None,
        }

        print(f"策略 '{strategy_id}' 注册成功")
        return True

    def generate_strategy_code(self, strategy_id, strategy_params):
        """生成策略代码"""
        if not self.trading_enabled:
            print("交易模块已禁用，无法生成策略代码")
            return None

        if strategy_id not in self.strategies:
            print(f"错误: 策略 '{strategy_id}' 未注册")
            return None

        try:
            # 这里只是生成策略代码模板，实际项目中会基于GPT生成的策略结构生成完整代码
            template = f"""
# --- 策略: {strategy_id} ---
# 生成时间: {datetime.now().isoformat()}

from freqtrade.strategy.interface import IStrategy
import pandas as pd
import ta

class {strategy_id.replace('-', '_')}(IStrategy):
    \"\"\"
    {strategy_params.get('description', '自动生成的交易策略')}
    \"\"\"
    # 策略配置
    minimal_roi = {strategy_params.get('minimal_roi', {'0': 0.1})}
    stoploss = {strategy_params.get('stoploss', -0.05)}
    timeframe = '{strategy_params.get('timeframe', '1h')}'
    
    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        \"\"\"生成技术指标\"\"\"
        # 添加指标
        dataframe['rsi'] = ta.momentum.rsi(dataframe['close'], window=14)
        
        # 自定义指标逻辑
        {strategy_params.get('indicators_logic', '# 默认指标逻辑')}
        
        return dataframe
    
    def populate_buy_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        \"\"\"生成买入信号\"\"\"
        dataframe.loc[
            (
                {strategy_params.get('buy_logic', 'dataframe["rsi"] < 30')}
            ),
            'buy'] = 1
        
        return dataframe
    
    def populate_sell_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        \"\"\"生成卖出信号\"\"\"
        dataframe.loc[
            (
                {strategy_params.get('sell_logic', 'dataframe["rsi"] > 70')}
            ),
            'sell'] = 1
        
        return dataframe
"""

            # 更新策略状态
            self.strategies[strategy_id]["status"] = "code_generated"
            self.strategies[strategy_id]["generated_at"] = datetime.now(
            ).isoformat()

            print(f"策略 '{strategy_id}' 代码生成成功")
            return template

        except Exception as e:
            print(f"生成策略代码失败: {str(e)}")
            return None

    def deploy_strategy(self, strategy_id):
        """部署策略到Freqtrade"""
        if not self.trading_enabled:
            print("交易模块已禁用，无法部署策略")
            return False

        if strategy_id not in self.strategies:
            print(f"错误: 策略 '{strategy_id}' 未注册")
            return False

        if self.strategies[strategy_id]["status"] != "code_generated":
            print(f"错误: 策略 '{strategy_id}' 代码未生成，无法部署")
            return False

        try:
            # 模拟策略部署过程
            print(f"正在部署策略 '{strategy_id}' 到Freqtrade...")
            time.sleep(1)  # 模拟部署延迟

            # 更新策略状态
            self.strategies[strategy_id]["status"] = "deployed"
            self.strategies[strategy_id]["deployed_at"] = datetime.now(
            ).isoformat()

            print(f"策略 '{strategy_id}' 部署成功")
            return True

        except Exception as e:
            print(f"部署策略失败: {str(e)}")
            return False

    def start_backtest(self, strategy_id, timerange=None):
        """启动回测"""
        if not self.trading_enabled:
            print("交易模块已禁用，无法启动回测")
            return None

        if strategy_id not in self.strategies:
            print(f"错误: 策略 '{strategy_id}' 未注册")
            return None

        if self.strategies[strategy_id]["status"] != "deployed":
            print(f"错误: 策略 '{strategy_id}' 未部署，无法回测")
            return None

        try:
            # 模拟回测过程
            print(f"正在对策略 '{strategy_id}' 进行回测...")
            time.sleep(2)  # 模拟回测延迟

            # 生成模拟回测结果
            backtest_result = {
                "strategy": strategy_id,
                "timerange": timerange or "20220101-20230101",
                "total_trades": 42,
                "profit": 0.15,  # 15% 利润
                "win_rate": 0.65,  # 65% 胜率
                "avg_profit": 0.05,  # 平均每笔交易 5% 利润
                "max_drawdown": 0.12,  # 最大回撤 12%
                "sharpe_ratio": 1.2,
                "completed_at": datetime.now().isoformat(),
            }

            # 更新策略状态
            self.strategies[strategy_id]["status"] = "backtested"
            self.strategies[strategy_id]["backtest_result"] = backtest_result

            print(f"策略 '{strategy_id}' 回测完成")
            return backtest_result

        except Exception as e:
            print(f"回测失败: {str(e)}")
            return None

    def start_live_trading(self, strategy_id):
        """启动实盘交易"""
        if not self.trading_enabled:
            print("交易模块已禁用，无法启动实盘交易")
            return False

        if strategy_id not in self.strategies:
            print(f"错误: 策略 '{strategy_id}' 未注册")
            return False

        if self.strategies[strategy_id]["status"] != "backtested":
            print(f"错误: 策略 '{strategy_id}' 未完成回测，不建议直接进行实盘交易")
            return False

        try:
            # 模拟启动实盘交易
            print(f"正在启动策略 '{strategy_id}' 的实盘交易...")
            time.sleep(1)  # 模拟启动延迟

            # 更新策略状态
            self.strategies[strategy_id]["status"] = "live_trading"
            self.strategies[strategy_id]["live_started_at"] = datetime.now(
            ).isoformat()

            # 创建活跃交易记录
            self.active_trades[strategy_id] = []

            print(f"策略 '{strategy_id}' 实盘交易已启动")
            return True

        except Exception as e:
            print(f"启动实盘交易失败: {str(e)}")
            return False

    def stop_live_trading(self, strategy_id):
        """停止实盘交易"""
        if not self.trading_enabled:
            print("交易模块已禁用")
            return False

        if strategy_id not in self.strategies:
            print(f"错误: 策略 '{strategy_id}' 未注册")
            return False

        if self.strategies[strategy_id]["status"] != "live_trading":
            print(f"错误: 策略 '{strategy_id}' 不在实盘交易中")
            return False

        try:
            # 模拟停止实盘交易
            print(f"正在停止策略 '{strategy_id}' 的实盘交易...")
            time.sleep(1)  # 模拟停止延迟

            # 更新策略状态
            self.strategies[strategy_id]["status"] = "inactive"
            self.strategies[strategy_id]["live_stopped_at"] = datetime.now(
            ).isoformat()

            # 清理活跃交易记录
            if strategy_id in self.active_trades:
                del self.active_trades[strategy_id]

            print(f"策略 '{strategy_id}' 实盘交易已停止")
            return True

        except Exception as e:
            print(f"停止实盘交易失败: {str(e)}")
            return False

    def get_strategy_status(self, strategy_id=None):
        """获取策略状态"""
        if not self.trading_enabled:
            print("交易模块已禁用")
            return None

        # 返回特定策略的状态
        if strategy_id is not None:
            if strategy_id not in self.strategies:
                print(f"错误: 策略 '{strategy_id}' 未注册")
                return None

            return self.strategies[strategy_id]

        # 返回所有策略的概要状态
        summary = {
            "total_strategies": len(self.strategies),
            "status_counts": {
                "registered": 0,
                "code_generated": 0,
                "deployed": 0,
                "backtested": 0,
                "live_trading": 0,
                "inactive": 0,
            },
            "strategies": {},
        }

        for s_id, strategy in self.strategies.items():
            status = strategy.get("status", "unknown")
            summary["status_counts"][status] = (
                summary["status_counts"].get(status, 0) + 1
            )

            # 添加策略基本信息
            summary["strategies"][s_id] = {
                "status": status,
                "created_at": strategy.get("created_at", "unknown"),
            }

            # 如果策略有回测结果，添加性能数据
            if "backtest_result" in strategy:
                summary["strategies"][s_id]["profit"] = strategy["backtest_result"].get(
                    "profit", 0
                )
                summary["strategies"][s_id]["win_rate"] = strategy[
                    "backtest_result"
                ].get("win_rate", 0)

        return summary


# 为了便于测试
class TradingAPI:
    # All your existing class methods...
    
    def get_strategy_status(self, strategy_id=None):
        """获取策略状态"""
        # Existing implementation...
        return summary

# ADD THE NEW FUNCTION HERE - before the if __name__ == "__main__": line

def get_strategy_data(strategy_id=None, timeframe=None):
    """
    获取策略数据用于UI监控
    
    Args:
        strategy_id (str, optional): 策略ID，如果为None则获取所有策略数据
        timeframe (str, optional): 时间周期，如果为None则使用策略默认值
        
    Returns:
        dict: 用于可视化的策略数据
    """
    # 创建TradingAPI实例以访问策略状态
    api = TradingAPI()
    
    # Rest of the implementation...

# EXISTING CODE BELOW
if __name__ == "__main__":
    # 测试交易API
    trading_api = TradingAPI()
    # Rest of your test code...
    
if __name__ == "__main__":
    # 测试交易API
    trading_api = TradingAPI()

    # 注册策略
    strategy_id = "example-strategy-001"
    strategy_config = {
        "description": "示例交易策略",
        "minimal_roi": {"0": 0.1},
        "stoploss": -0.05,
        "timeframe": "1h",
        "indicators_logic": "# 使用RSI和MACD指标",
        "buy_logic": "dataframe['rsi'] < 30 and dataframe['macd'] > dataframe['macdsignal']",
        "sell_logic": "dataframe['rsi'] > 70 or dataframe['macd'] < dataframe['macdsignal']",
    }

    trading_api.register_strategy(strategy_id, strategy_config)

    # 生成策略代码
    code = trading_api.generate_strategy_code(strategy_id, strategy_config)
    if code:
        print("\n生成的策略代码:")
        print(code)

    # 部署策略
    if trading_api.deploy_strategy(strategy_id):
        # 进行回测
        backtest_result = trading_api.start_backtest(strategy_id)
        if backtest_result:
            print("\n回测结果:")
            for key, value in backtest_result.items():
                print(f"  {key}: {value}")

    # 获取策略状态
    status = trading_api.get_strategy_status(strategy_id)
    if status:
        print("\n策略状态:")
        print(json.dumps(status, indent=2))