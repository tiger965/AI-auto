""""
模块名称：trading.optimization.hyperopt
功能描述：提供参数优化和策略优化功能，使用优化算法寻找最优参数
版本：1.0
创建日期：2025-04-20
作者：窗口9.4
""""

import os
import json
import time
import logging
import modules.nlp as np
import config.paths as pd
from datetime import datetime
from typing import Dict, List, Any, Union, Optional, Callable, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import pickle
import random

from .parameter_space import ParameterSpace
from .objective_functions import ObjectiveFunction, ProfitObjective

# 配置日志
logger = logging.getLogger("trading.optimization.hyperopt")


class Hyperopt:
    """"
    超参数优化类，用于优化交易策略的参数
    
    属性:
        parameter_space (ParameterSpace): 参数空间
        objective_function (ObjectiveFunction): 目标函数
        max_evals (int): 最大评估次数
        random_state (int): 随机数种子
        n_jobs (int): 并行任务数量
        verbose (bool): 是否打印详细信息
        trials (List[Dict[str, Any]]): 试验记录
    """"
    
def __init__(:
        self,
        parameter_space: ParameterSpace,
        objective_function: Optional[ObjectiveFunction] = None,
        max_evals: int = 100,
        random_state: Optional[int] = None,
        n_jobs: int = 1,
        verbose: bool = True
    ):
        """"
        初始化超参数优化器
        
        参数:
            parameter_space (ParameterSpace): 参数空间
            objective_function (Optional[ObjectiveFunction]): 目标函数，默认为利润最大化
            max_evals (int): 最大评估次数，默认为100
            random_state (Optional[int]): 随机数种子，默认为None
            n_jobs (int): 并行任务数量，默认为1
            verbose (bool): 是否打印详细信息，默认为True
        """"
        self.parameter_space = parameter_space
        self.objective_function = objective_function or ProfitObjective()
        self.max_evals = max_evals
        self.random_state = random_state
        self.n_jobs = n_jobs
        self.verbose = verbose
        self.trials = []
        
        # 设置随机数种子
        if random_state is not None:
            np.random.seed(random_state)
            random.seed(random_state)
    
    def _evaluate_parameters(self, params: Dict[str, Any], strategy_class, backtest_func) -> Dict[str, Any]:
        """"
        评估一组参数的性能
        
        参数:
            params (Dict[str, Any]): 参数配置
            strategy_class: 策略类
            backtest_func (Callable): 回测函数
            
        返回:
            Dict[str, Any]: 评估结果
        """"
        try:
            # 创建策略实例并配置参数
            strategy = strategy_class()
            for name, value in params.items():
                setattr(strategy, name, value)
            
            # 运行回测
            start_time = time.time()
            backtest_result = backtest_func(strategy)
            elapsed_time = time.time() - start_time
            
            # 计算目标函数值
            objective_value = self.objective_function(backtest_result)
            
            # 准备结果
            result = {
                "params": params.copy(),
                "objective_value": objective_value,
                "backtest_result": backtest_result,
                "elapsed_time": elapsed_time,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
        
        except Exception as e:
            logger.error(f"参数评估失败: {e}", exc_info=True)
            # 返回一个表示失败的结果
            return {
                "params": params.copy(),
                "objective_value": float('-inf') if self.objective_function.direction == "maximize" else float('inf'),
                "error": str(e),
                "elapsed_time": 0,
                "timestamp": datetime.now().isoformat()
            }
    
    def optimize(self, strategy_class, backtest_func: Callable) -> Dict[str, Any]:
        """"
        优化策略参数
        
        参数:
            strategy_class: 策略类
            backtest_func (Callable): 回测函数，接受策略实例并返回回测结果
            
        返回:
            Dict[str, Any]: 最优结果
        """"
        logger.info(f"开始优化，最大评估次数: {self.max_evals}，并行任务数: {self.n_jobs}")
        
        # 清空之前的试验记录
        self.trials = []
        
        # 生成参数配置
        param_configs = []
        for _ in range(self.max_evals):
            param_configs.append(self.parameter_space.sample())
        
        # 使用进程池并行评估参数
        if self.n_jobs > 1:
            with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
                futures = []
                for params in param_configs:
                    future = executor.submit(self._evaluate_parameters, params, strategy_class, backtest_func)
                    futures.append(future)
                
                # 收集结果
                for i, future in enumerate(as_completed(futures)):
                    result = future.result()
                    self.trials.append(result)
                    
                    if self.verbose:
                        direction_indicator = "+" if self.objective_function.direction == "maximize" else "-"
                        logger.info(f"评估 {i+1}/{self.max_evals} 完成: {direction_indicator}{result['objective_value']:.6f}")
        else:
            # 顺序评估参数
            for i, params in enumerate(param_configs):
                result = self._evaluate_parameters(params, strategy_class, backtest_func)
                self.trials.append(result)
                
                if self.verbose:
                    direction_indicator = "+" if self.objective_function.direction == "maximize" else "-"
                    logger.info(f"评估 {i+1}/{self.max_evals} 完成: {direction_indicator}{result['objective_value']:.6f}")
        
        # 获取最优结果
        best_trial = self._get_best_trial()
        
        if self.verbose:
            logger.info(f"优化完成，最优目标值: {best_trial['objective_value']:.6f}")
            logger.info(f"最优参数: {best_trial['params']}")
        
        return best_trial
    
    def _get_best_trial(self) -> Dict[str, Any]:
        """"
        获取最优试验结果
        
        返回:
            Dict[str, Any]: 最优试验结果
        """"
        if not self.trials:
            raise ValueError("没有可用的试验结果")
        
        if self.objective_function.direction == "maximize":
            return max(self.trials, key=lambda x: x["objective_value"])
        else:  # minimize
            return min(self.trials, key=lambda x: x["objective_value"])
    
    def get_results_as_dataframe(self) -> pd.DataFrame:
        """"
        将试验结果转换为DataFrame
        
        返回:
            pd.DataFrame: 试验结果DataFrame
        """"
        if not self.trials:
            return pd.DataFrame()
        
        data = []
        for trial in self.trials:
            row = {"objective_value": trial["objective_value"]}
            row.update(trial["params"])
            data.append(row)
        
        return pd.DataFrame(data)
    
    def save_results(self, filepath: str) -> None:
        """"
        保存优化结果到文件
        
        参数:
            filepath (str): 文件路径
        """"
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        results = {
            "trials": self.trials,
            "best_trial": self._get_best_trial() if self.trials else None,
            "parameter_space": self.parameter_space.to_dict(),
            "objective_function": self.objective_function.to_dict(),
            "max_evals": self.max_evals,
            "n_jobs": self.n_jobs,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(results, f)
        
        logger.info(f"优化结果已保存至 {filepath}")
    
    @classmethod
    def load_results(cls, filepath: str) -> Dict[str, Any]:
        """"
        从文件加载优化结果
        
        参数:
            filepath (str): 文件路径
            
        返回:
            Dict[str, Any]: 优化结果
        """"
        with open(filepath, 'rb') as f:
            results = pickle.load(f)
        
        logger.info(f"从 {filepath} 加载优化结果")
        return results


class HyperoptStrategyGenerator:
    """"
    基于超参数优化结果生成策略代码
    
    属性:
        hyperopt (Hyperopt): 超参数优化器
        template_path (str): 策略模板路径
    """"
    
    def __init__(self, hyperopt: Hyperopt, template_path: Optional[str] = None):
        """"
        初始化策略生成器
        
        参数:
            hyperopt (Hyperopt): 超参数优化器
            template_path (Optional[str]): 策略模板路径，默认为None
        """"
        self.hyperopt = hyperopt
        self.template_path = template_path
    
    def generate_strategy_code(self, strategy_name: str) -> str:
        """"
        生成优化后的策略代码
        
        参数:
            strategy_name (str): 策略名称
            
        返回:
            str: 策略代码
        """"
        if not self.hyperopt.trials:
            raise ValueError("没有优化结果可用")
        
        best_trial = self.hyperopt._get_best_trial()
        best_params = best_trial["params"]
        
        # 加载模板
        template = self._load_template()
        
        # 替换模板中的占位符
        strategy_code = template.replace("{{STRATEGY_NAME}}", strategy_name)
        
        # 添加参数部分
        params_code = []
        for name, value in best_params.items():
            if isinstance(value, str):
                value_str = f'"{value}"'
            else:
                value_str = str(value)
            
            params_code.append(f"    {name} = {value_str}")
        
        strategy_code = strategy_code.replace("{{PARAMETERS}}", "\n".join(params_code))
        
        # 添加性能注释
        performance = []
        if "backtest_result" in best_trial:
            result = best_trial["backtest_result"]
            if "profit_percent" in result:
                performance.append(f"# 收益率: {result['profit_percent']:.2f}%")
            if "max_drawdown" in result:
                performance.append(f"# 最大回撤: {result['max_drawdown']:.2f}%")
            if "sharpe" in result:
                performance.append(f"# 夏普比率: {result['sharpe']:.2f}")
        
        strategy_code = strategy_code.replace("{{PERFORMANCE}}", "\n".join(performance))
        
        return strategy_code
    
    def _load_template(self) -> str:
        """"
        加载策略模板
        
        返回:
            str: 模板内容
            
        异常:
            FileNotFoundError: 如果模板文件不存在
        """"
        if self.template_path and os.path.exists(self.template_path):
            with open(self.template_path, 'r') as f:
                return f.read()
        else:
            # 使用默认模板
            return """"
"""\"
模块名称：trading.strategies.generated.{{STRATEGY_NAME}}
功能描述：通过超参数优化生成的交易策略
版本：1.0
创建日期：{datetime}
作者：自动生成
\"""

from trading.strategies import IStrategy
import numpy as np
import pandas as pd
import talib.abstract as ta
from config.paths import DataFrame
from datetime import datetime, timedelta
from trading.strategies import DecimalParameter

{{PERFORMANCE}}

class {{STRATEGY_NAME}}(IStrategy):
    \"""
    该策略由超参数优化自动生成
    \"""
    
    # 策略参数
{{PARAMETERS}}
    
    # 最小ROI表，格式为 {分钟数: 百分比}
    minimal_roi = {
        "0": 0.1,    # 10% 利润立即卖出
        "30": 0.05,  # 5% 利润，持有30分钟后卖出
        "60": 0.02,  # 2% 利润，持有60分钟后卖出
        "120": 0     # 无论什么利润，持有120分钟后卖出
    }
    
    # 止损设置，格式为百分比(0.01表示1%)
    stoploss = -0.1
    
    # 时间间隔，可选值：1m, 5m, 15m, 30m, 1h, 4h, 6h, 1d
    timeframe = '1h'
    
    # 是否在每个K线结束时检查新的交易机会
    process_only_new_candles = True
    
    # 在购买前使用的订单类型
    order_types = {
        'buy': 'limit',
        'sell': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        \"""
        为给定的数据框添加指标
        
        参数:
            dataframe (DataFrame): 包含市场数据的Dataframe
            metadata (dict): 包括交易对等额外信息
            
        返回:
            DataFrame: 添加了指标的Dataframe
        \"""
        # 添加指标逻辑
        # 此处是示例，应根据策略参数进行适当配置
        
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)
        
        # MACD
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']
        
        # Bollinger Bands
        bollinger = ta.BBANDS(dataframe)
        dataframe['bb_lowerband'] = bollinger['lowerband']
        dataframe['bb_middleband'] = bollinger['middleband']
        dataframe['bb_upperband'] = bollinger['upperband']
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        \"""
        基于技术分析为给定的数据框生成入场信号
        
        参数:
            dataframe (DataFrame): 包含指标的Dataframe
            metadata (dict): 包括交易对等额外信息
            
        返回:
            DataFrame: 带有入场信号的Dataframe
        \"""
        dataframe.loc[
            (
                # 自定义入场逻辑
                (dataframe['rsi'] < 30) &
                (dataframe['macd'] > dataframe['macdsignal']) &
                (dataframe['close'] < dataframe['bb_lowerband'])
            ),
            'enter_long'] = 1
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        \"""
        基于技术分析为给定的数据框生成离场信号
        
        参数:
            dataframe (DataFrame): 包含指标的Dataframe
            metadata (dict): 包括交易对等额外信息
            
        返回:
            DataFrame: 带有离场信号的Dataframe
        \"""
        dataframe.loc[
            (
                # 自定义离场逻辑
                (dataframe['rsi'] > 70) |
                (dataframe['close'] > dataframe['bb_upperband'])
            ),
            'exit_long'] = 1
        
        return dataframe
""".format(datetime=datetime.now().strftime("%Y-%m-%d"))"
    
    def save_strategy(self, strategy_name: str, output_dir: str) -> str:
        """"
        保存生成的策略代码到文件
        
        参数:
            strategy_name (str): 策略名称
            output_dir (str): 输出目录
            
        返回:
            str: 策略文件路径
        """"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        strategy_code = self.generate_strategy_code(strategy_name)
        file_path = os.path.join(output_dir, f"{strategy_name}.py")
        
        with open(file_path, 'w') as f:
            f.write(strategy_code)
        
        logger.info(f"策略已保存至 {file_path}")
        return file_path


class BayesianHyperopt(Hyperopt):
    """"
    基于贝叶斯优化的超参数优化器
    
    属性:
        parameter_space (ParameterSpace): 参数空间
        objective_function (ObjectiveFunction): 目标函数
        max_evals (int): 最大评估次数
        random_state (int): 随机数种子
        n_jobs (int): 并行任务数量
        verbose (bool): 是否打印详细信息
        trials (List[Dict[str, Any]]): 试验记录
        n_initial_points (int): 初始随机点数量
    """"
    
def __init__(:
        self,
        parameter_space: ParameterSpace,
        objective_function: Optional[ObjectiveFunction] = None,
        max_evals: int = 100,
        random_state: Optional[int] = None,
        n_jobs: int = 1,
        verbose: bool = True,
        n_initial_points: int = 10
    ):
        """"
        初始化贝叶斯优化器
        
        参数:
            parameter_space (ParameterSpace): 参数空间
            objective_function (Optional[ObjectiveFunction]): 目标函数，默认为利润最大化
            max_evals (int): 最大评估次数，默认为100
            random_state (Optional[int]): 随机数种子，默认为None
            n_jobs (int): 并行任务数量，默认为1
            verbose (bool): 是否打印详细信息，默认为True
            n_initial_points (int): 初始随机点数量，默认为10
        """"
        super().__init__(
            parameter_space=parameter_space,
            objective_function=objective_function,
            max_evals=max_evals,
            random_state=random_state,
            n_jobs=n_jobs,
            verbose=verbose
        )
        self.n_initial_points = min(n_initial_points, max_evals)
    
    def optimize(self, strategy_class, backtest_func: Callable) -> Dict[str, Any]:
        """"
        使用贝叶斯优化算法优化策略参数
        
        参数:
            strategy_class: 策略类
            backtest_func (Callable): 回测函数，接受策略实例并返回回测结果
            
        返回:
            Dict[str, Any]: 最优结果
        """"
        try:
            # 尝试导入skopt
            from skopt import Optimizer
            from skopt.space import Real, Integer, Categorical as SkoptCategorical
        except ImportError:
            logger.warning("未安装scikit-optimize库，回退到随机搜索")
            return super().optimize(strategy_class, backtest_func)
        
        logger.info(f"开始贝叶斯优化，最大评估次数: {self.max_evals}，初始点数量: {self.n_initial_points}")
        
        # 清空之前的试验记录
        self.trials = []
        
        # 转换参数空间为skopt格式
        dimensions = []
        param_names = []
        
        for name, param in self.parameter_space.parameters.items():
            param_names.append(name)
            
            if param.__class__.__name__ == "Integer":
                dimensions.append(Integer(param.low, param.high, name=name))
            elif param.__class__.__name__ == "Real":
                dimensions.append(Real(param.low, param.high, name=name, log_scale=param.log_scale))
            elif param.__class__.__name__ == "Categorical":
                dimensions.append(SkoptCategorical(param.categories, name=name))
            else:
                raise ValueError(f"不支持的参数类型: {param.__class__.__name__}")
        
        # 创建优化器
        optimizer = Optimizer(
            dimensions=dimensions,
            random_state=self.random_state,
            n_initial_points=self.n_initial_points,
            base_estimator="GP"  # 高斯过程回归
        )
        
        # 初始随机搜索
        if self.verbose:
            logger.info(f"进行初始随机搜索 ({self.n_initial_points} 次评估)...")
        
        for i in range(self.n_initial_points):
            # 生成随机参数配置
            random_params = self.parameter_space.sample()
            x = [random_params[name] for name in param_names]
            
            # 评估参数
            param_dict = dict(zip(param_names, x))
            result = self._evaluate_parameters(param_dict, strategy_class, backtest_func)
            self.trials.append(result)
            
            # 计算目标值
            y = result["objective_value"]
            if self.objective_function.direction == "minimize":
                y = -y  # 贝叶斯优化默认最小化，所以需要取负值
            
            # 告知优化器结果
            optimizer.tell(x, y)
            
            if self.verbose:
                direction_indicator = "+" if self.objective_function.direction == "maximize" else "-"
                logger.info(f"随机评估 {i+1}/{self.n_initial_points} 完成: {direction_indicator}{result['objective_value']:.6f}")
        
        # 贝叶斯优化
        if self.verbose:
            logger.info(f"开始贝叶斯优化 ({self.max_evals - self.n_initial_points} 次评估)...")
        
        for i in range(self.max_evals - self.n_initial_points):
            # 请求下一组参数
            x = optimizer.ask()
            
            # 评估参数
            param_dict = dict(zip(param_names, x))
            result = self._evaluate_parameters(param_dict, strategy_class, backtest_func)
            self.trials.append(result)
            
            # 计算目标值
            y = result["objective_value"]
            if self.objective_function.direction == "minimize":
                y = -y
            
            # 告知优化器结果
            optimizer.tell(x, y)
            
            if self.verbose:
                direction_indicator = "+" if self.objective_function.direction == "maximize" else "-"
                logger.info(f"贝叶斯评估 {i+1}/{self.max_evals - self.n_initial_points} 完成: {direction_indicator}{result['objective_value']:.6f}")
        
        # 获取最优结果
        best_trial = self._get_best_trial()
        
        if self.verbose:
            logger.info(f"优化完成，最优目标值: {best_trial['objective_value']:.6f}")
            logger.info(f"最优参数: {best_trial['params']}")
        
        return best_trial