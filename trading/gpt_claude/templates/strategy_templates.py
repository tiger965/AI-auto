""""
模块名称：strategy_templates
功能描述：提供策略模板和策略生成的功能，用于GPT策略生成和Claude实现
版本：1.0
创建日期：2025-04-20
作者：开发窗口9.6
""""

import json
import logging
import os
import time
from typing import Dict, List, Optional, Union, Any
from jinja2 import Template

# 配置日志
logger = logging.getLogger(__name__)


class StrategyTemplate:
    """"
    策略模板，用于生成策略代码和配置
    """"
    
    def __init__(self, template_id: str, name: str, description: str, template_content: str):
        """"
        初始化策略模板
        
        参数:
            template_id (str): 模板ID
            name (str): 模板名称
            description (str): 模板描述
            template_content (str): 模板内容，使用Jinja2模板语法
        """"
        self.template_id = template_id
        self.name = name
        self.description = description
        self.template_content = template_content
        self.template = Template(template_content)
    
    def render(self, context: Dict[str, Any]) -> str:
        """"
        渲染策略模板
        
        参数:
            context (Dict[str, Any]): 模板上下文数据
            
        返回:
            str: 渲染后的策略代码
            
        异常:
            TemplateRenderError: 渲染失败时抛出
        """"
        try:
            return self.template.render(**context)
        except Exception as e:
            logger.error(f"渲染模板 {self.template_id} 失败: {str(e)}")
            raise TemplateRenderError(f"渲染模板失败: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """"
        将模板转换为字典
        
        返回:
            Dict[str, Any]: 表示模板的字典
        """"
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "created_at": time.time()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], template_content: str) -> 'StrategyTemplate':
        """"
        从字典创建模板
        
        参数:
            data (Dict[str, Any]): 模板数据
            template_content (str): 模板内容
            
        返回:
            StrategyTemplate: 策略模板实例
        """"
        return cls(
            template_id=data["template_id"],
            name=data["name"],
            description=data["description"],
            template_content=template_content
        )


class StrategyTemplateManager:
    """"
    策略模板管理器，管理和存储策略模板
    """"
    
    def __init__(self, templates_dir: str = None):
        """"
        初始化策略模板管理器
        
        参数:
            templates_dir (str, optional): 模板存储目录
        """"
        self.templates_dir = templates_dir or "data/templates"
        self.templates = {}
        self._load_templates()
    
    def add_template(self, template: StrategyTemplate) -> None:
        """"
        添加策略模板
        
        参数:
            template (StrategyTemplate): 策略模板
        """"
        self.templates[template.template_id] = template
        self._save_template(template)
        logger.info(f"已添加模板: {template.template_id}")
    
    def get_template(self, template_id: str) -> Optional[StrategyTemplate]:
        """"
        获取策略模板
        
        参数:
            template_id (str): 模板ID
            
        返回:
            Optional[StrategyTemplate]: 策略模板，如果不存在则返回None
        """"
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """"
        列出所有策略模板
        
        返回:
            List[Dict[str, Any]]: 模板信息列表
        """"
        return [template.to_dict() for template in self.templates.values()]
    
    def remove_template(self, template_id: str) -> bool:
        """"
        移除策略模板
        
        参数:
            template_id (str): 模板ID
            
        返回:
            bool: 是否成功移除
        """"
        if template_id in self.templates:
            del self.templates[template_id]
            
            try:
                # 删除模板文件
                template_path = os.path.join(self.templates_dir, f"{template_id}.json")
                content_path = os.path.join(self.templates_dir, f"{template_id}.template")
                
                if os.path.exists(template_path):
                    os.remove(template_path)
                
                if os.path.exists(content_path):
                    os.remove(content_path)
                
                logger.info(f"已移除模板: {template_id}")
                return True
            except Exception as e:
                logger.error(f"移除模板文件失败: {str(e)}")
                return False
        else:
            logger.warning(f"模板不存在: {template_id}")
            return False
    
    def create_strategy_from_template(self, template_id: str, strategy_name: str, strategy_params: Dict[str, Any]) -> Dict[str, Any]:
        """"
        从模板创建策略
        
        参数:
            template_id (str): 模板ID
            strategy_name (str): 策略名称
            strategy_params (Dict[str, Any]): 策略参数
            
        返回:
            Dict[str, Any]: 创建的策略信息
            
        异常:
            TemplateNotFoundError: 模板不存在时抛出
            TemplateRenderError: 渲染失败时抛出
        """"
        template = self.get_template(template_id)
        
        if not template:
            raise TemplateNotFoundError(f"模板不存在: {template_id}")
        
        try:
            # 准备渲染上下文
            context = {
                "strategy_name": strategy_name,
                "params": strategy_params,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "template_id": template_id
            }
            
            # 渲染策略代码
            strategy_code = template.render(context)
            
            # 创建策略信息
            strategy_info = {
                "strategy_id": f"strategy-{int(time.time())}",
                "name": strategy_name,
                "template_id": template_id,
                "params": strategy_params,
                "created_at": time.time(),
                "code": strategy_code
            }
            
            # 保存策略代码
            self._save_strategy(strategy_info)
            
            return strategy_info
        except Exception as e:
            logger.error(f"从模板 {template_id} 创建策略失败: {str(e)}")
            raise TemplateRenderError(f"创建策略失败: {str(e)}")
    
    def create_prompt_for_gpt(self, task_type: str, market_data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """"
        为GPT创建提示，用于生成策略
        
        参数:
            task_type (str): 任务类型，如"strategy_generation", "strategy_optimization"
            market_data (Dict[str, Any]): 市场数据
            config (Dict[str, Any]): 配置
            
        返回:
            str: 提示文本
        """"
        # 加载提示模板
        prompt_template_path = os.path.join(self.templates_dir, f"prompt_{task_type}.template")
        
        if not os.path.exists(prompt_template_path):
            logger.warning(f"提示模板不存在: {prompt_template_path}，使用默认模板")
            
            if task_type == "strategy_generation":
                prompt_template = """"
                你是一个先进的量化交易策略生成系统。
                请根据以下市场数据和配置生成一个完整的量化交易策略。
                
                市场数据:
                {{market_data_json}}
                
                配置要求:
                {{config_json}}
                
                你的策略应该包含以下部分:
                1. 策略名称和描述
                2. 策略参数和配置
                3. 入场条件和逻辑
                4. 出场条件和逻辑
                5. 风险管理规则
                6. 资金管理规则
                
                请以JSON格式返回你的策略，确保它可以被解析为有效的JSON对象。
                """"
            elif task_type == "strategy_optimization":
                prompt_template = """"
                你是一个先进的量化交易策略优化系统。
                请根据以下现有策略、市场数据和性能反馈，优化交易策略。
                
                现有策略:
                {{strategy_json}}
                
                市场数据:
                {{market_data_json}}
                
                性能反馈:
                {{feedback_json}}
                
                配置要求:
                {{config_json}}
                
                请优化策略的以下方面:
                1. 参数调整
                2. 入场和出场条件
                3. 风险管理规则
                4. 资金管理规则
                
                请以JSON格式返回优化后的策略，确保它可以被解析为有效的JSON对象。
                """"
            else:
                prompt_template = """"
                你是一个先进的量化交易策略系统。
                请根据以下数据执行所需的任务。
                
                任务类型: {{task_type}}
                
                数据:
                {{data_json}}
                
                配置要求:
                {{config_json}}
                
                请以JSON格式返回你的结果，确保它可以被解析为有效的JSON对象。
                """"
        else:
            with open(prompt_template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        
        # 创建模板
        template = Template(prompt_template)
        
        # 准备上下文
        context = {
            "task_type": task_type,
            "market_data_json": json.dumps(market_data, ensure_ascii=False, indent=2),
            "config_json": json.dumps(config, ensure_ascii=False, indent=2),
            "strategy_json": json.dumps(config.get("strategy", {}), ensure_ascii=False, indent=2),
            "feedback_json": json.dumps(config.get("feedback", {}), ensure_ascii=False, indent=2),
            "data_json": json.dumps({"market_data": market_data, **config}, ensure_ascii=False, indent=2)
        }
        
        # 渲染提示
        try:
            prompt = template.render(**context)
            return prompt
        except Exception as e:
            logger.error(f"渲染提示模板失败: {str(e)}")
            # 返回简单的默认提示
            return f"请根据以下数据生成量化交易策略: {json.dumps({'market_data': market_data, **config}, ensure_ascii=False)}"
    
    def parse_gpt_response(self, response: str) -> Dict[str, Any]:
        """"
        解析GPT的响应，提取策略信息
        
        参数:
            response (str): GPT的响应文本
            
        返回:
            Dict[str, Any]: 解析后的策略信息
        """"
        try:
            # 尝试直接解析JSON
            try:
                strategy_data = json.loads(response)
            except json.JSONDecodeError:
                # 如果不是有效的JSON，尝试提取JSON部分
                import re
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
                if json_match:
                    try:
                        strategy_data = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        # 如果JSON提取失败，尝试修复常见错误
                        json_text = json_match.group(1)
                        json_text = json_text.replace("'", '"')  # 替换单引号为双引号'
                        try:
                            strategy_data = json.loads(json_text)
                        except json.JSONDecodeError:
                            raise ParsingError(f"无法解析JSON响应: {response}")
                else:
                    # 如果找不到JSON块，则认为整个响应是自然语言
                    raise ParsingError(f"响应不包含有效的JSON格式: {response}")
            
            # 验证必要的字段
            required_fields = ["name", "description", "parameters", "entry_conditions", "exit_conditions"]
            missing_fields = [field for field in required_fields if field not in strategy_data]
            
            if missing_fields:
                logger.warning(f"解析的策略数据缺少必要字段: {missing_fields}")
                # 添加默认值
                for field in missing_fields:
                    strategy_data[field] = f"Default {field}"
            
            # 添加策略ID和时间戳
            strategy_data["strategy_id"] = f"strategy-{int(time.time())}"
            strategy_data["generated_at"] = time.time()
            
            return strategy_data
        except Exception as e:
            logger.error(f"解析GPT响应失败: {str(e)}")
            raise ParsingError(f"无法解析策略响应: {str(e)}")
    
    def _load_templates(self) -> None:
        """"
        从存储目录加载所有模板
        """"
        try:
            # 确保目录存在
            os.makedirs(self.templates_dir, exist_ok=True)
            
            # 遍历目录查找模板文件
            template_files = [f for f in os.listdir(self.templates_dir) if f.endswith(".json")]
            
            for file_name in template_files:
                try:
                    # 获取模板ID
                    template_id = file_name.replace(".json", "")
                    
                    # 加载模板数据
                    template_path = os.path.join(self.templates_dir, file_name)
                    content_path = os.path.join(self.templates_dir, f"{template_id}.template")
                    
                    with open(template_path, "r", encoding="utf-8") as f:
                        template_data = json.load(f)
                    
                    # 加载模板内容
                    if os.path.exists(content_path):
                        with open(content_path, "r", encoding="utf-8") as f:
                            template_content = f.read()
                    else:
                        logger.warning(f"模板内容文件不存在: {content_path}")
                        template_content = "# 默认模板内容\n# 此模板内容文件丢失，已生成默认内容\n"
                    
                    # 创建模板实例
                    template = StrategyTemplate.from_dict(template_data, template_content)
                    self.templates[template_id] = template
                    
                    logger.info(f"已加载模板: {template_id}")
                except Exception as e:
                    logger.error(f"加载模板 {file_name} 失败: {str(e)}")
            
            logger.info(f"共加载了 {len(self.templates)} 个模板")
        except Exception as e:
            logger.error(f"加载模板失败: {str(e)}")
    
    def _save_template(self, template: StrategyTemplate) -> None:
        """"
        保存模板到存储
        
        参数:
            template (StrategyTemplate): 要保存的模板
        """"
        try:
            # 确保目录存在
            os.makedirs(self.templates_dir, exist_ok=True)
            
            # 保存模板数据
            template_path = os.path.join(self.templates_dir, f"{template.template_id}.json")
            content_path = os.path.join(self.templates_dir, f"{template.template_id}.template")
            
            with open(template_path, "w", encoding="utf-8") as f:
                json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 保存模板内容
            with open(content_path, "w", encoding="utf-8") as f:
                f.write(template.template_content)
            
            logger.info(f"已保存模板: {template.template_id}")
        except Exception as e:
            logger.error(f"保存模板 {template.template_id} 失败: {str(e)}")
    
    def _save_strategy(self, strategy_info: Dict[str, Any]) -> None:
        """"
        保存生成的策略
        
        参数:
            strategy_info (Dict[str, Any]): 策略信息
        """"
        try:
            # 确保目录存在
            strategies_dir = os.path.join(self.templates_dir, "../strategies")
            os.makedirs(strategies_dir, exist_ok=True)
            
            # 保存策略信息
            strategy_path = os.path.join(strategies_dir, f"{strategy_info['strategy_id']}.json")
            code_path = os.path.join(strategies_dir, f"{strategy_info['strategy_id']}.py")
            
            # 保存策略元数据
            strategy_meta = {k: v for k, v in strategy_info.items() if k != "code"}
            with open(strategy_path, "w", encoding="utf-8") as f:
                json.dump(strategy_meta, f, ensure_ascii=False, indent=2)
            
            # 保存策略代码
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(strategy_info["code"])
            
            logger.info(f"已保存策略: {strategy_info['strategy_id']}")
        except Exception as e:
            logger.error(f"保存策略 {strategy_info.get('strategy_id', 'unknown')} 失败: {str(e)}")
    
    def load_default_templates(self) -> None:
        """"
        加载默认模板
        """"
        # 基本策略模板
        basic_template = StrategyTemplate(
            template_id="basic_strategy",
            name="基本交易策略",
            description="适用于大多数市场的基本交易策略模板",
            template_content="""# -*- coding: utf-8 -*-"
"""\"
模块名称：{{ strategy_name }}
功能描述：基于{{ template_id }}模板生成的交易策略
版本：1.0
创建日期：{{ created_at }}
作者：GPT-Claude AI系统
"""\"

from typing import Dict, List, Optional, Any
import config.paths as pd
import modules.nlp as np
import api


class {{ strategy_name.replace(' ', '') }}:
    """\"
    {{ params.get('description', '基本交易策略') }}
    """\"
    
    def __init__(self):
        """\"
        初始化策略
        """\"
        # 策略参数
        self.name = "{{ strategy_name }}"
        self.timeframe = "{{ params.get('timeframe', '1h') }}"
        self.risk_level = "{{ params.get('risk_level', 'medium') }}"
        
        # 指标参数
        self.fast_period = {{ params.get('fast_period', 12) }}
        self.slow_period = {{ params.get('slow_period', 26) }}
        self.signal_period = {{ params.get('signal_period', 9) }}
        self.rsi_period = {{ params.get('rsi_period', 14) }}
        self.rsi_overbought = {{ params.get('rsi_overbought', 70) }}
        self.rsi_oversold = {{ params.get('rsi_oversold', 30) }}
        
        # 策略状态
        self.position = None
        self.last_signal = None
    
    def populate_indicators(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """\"
        计算技术指标
        
        参数:
            dataframe (pd.DataFrame): 价格数据
            
        返回:
            pd.DataFrame: 添加了指标的数据
        """\"
        # 计算MACD
        dataframe['macd'], dataframe['macdsignal'], dataframe['macdhist'] = talib.MACD(
            dataframe['close'],
            fastperiod=self.fast_period,
            slowperiod=self.slow_period,
            signalperiod=self.signal_period
        )
        
        # 计算RSI
        dataframe['rsi'] = talib.RSI(dataframe['close'], timeperiod=self.rsi_period)
        
        # 计算移动平均线
        dataframe['sma'] = talib.SMA(dataframe['close'], timeperiod=self.slow_period)
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """\"
        确定入场信号
        
        参数:
            dataframe (pd.DataFrame): 带有指标的价格数据
            
        返回:
            pd.DataFrame: 添加了入场信号的数据
        """\"
        dataframe['buy_signal'] = False
        
        # 定义买入条件
        {% if params.get('entry_condition', '') == 'macd_cross' %}
        # MACD交叉信号线
        buy_condition = (
            (dataframe['macd'] > dataframe['macdsignal']) &
            (dataframe['macd'].shift(1) <= dataframe['macdsignal'].shift(1)) &
            (dataframe['rsi'] > 30)
        )
        {% elif params.get('entry_condition', '') == 'rsi_oversold' %}
        # RSI超卖反弹
        buy_condition = (
            (dataframe['rsi'] < self.rsi_oversold) &
            (dataframe['rsi'].shift(1) < self.rsi_oversold) &
            (dataframe['rsi'] > dataframe['rsi'].shift(1))
        )
        {% else %}
        # 默认条件：MACD柱状图由负转正
        buy_condition = (
            (dataframe['macdhist'] > 0) &
            (dataframe['macdhist'].shift(1) <= 0) &
            (dataframe['close'] > dataframe['sma'])
        )
        {% endif %}
        
        dataframe.loc[buy_condition, 'buy_signal'] = True
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """\"
        确定出场信号
        
        参数:
            dataframe (pd.DataFrame): 带有指标的价格数据
            
        返回:
            pd.DataFrame: 添加了出场信号的数据
        """\"
        dataframe['sell_signal'] = False
        
        # 定义卖出条件
        {% if params.get('exit_condition', '') == 'macd_cross_down' %}
        # MACD交叉信号线向下
        sell_condition = (
            (dataframe['macd'] < dataframe['macdsignal']) &
            (dataframe['macd'].shift(1) >= dataframe['macdsignal'].shift(1))
        )
        {% elif params.get('exit_condition', '') == 'rsi_overbought' %}
        # RSI超买回落
        sell_condition = (
            (dataframe['rsi'] > self.rsi_overbought) &
            (dataframe['rsi'].shift(1) > self.rsi_overbought) &
            (dataframe['rsi'] < dataframe['rsi'].shift(1))
        )
        {% else %}
        # 默认条件：MACD柱状图由正转负
        sell_condition = (
            (dataframe['macdhist'] < 0) &
            (dataframe['macdhist'].shift(1) >= 0)
        )
        {% endif %}
        
        dataframe.loc[sell_condition, 'sell_signal'] = True
        
        return dataframe
    
    def calculate_profit_target(self, entry_price: float) -> float:
        """\"
        计算止盈目标价格
        
        参数:
            entry_price (float): 入场价格
            
        返回:
            float: 止盈目标价格
        """\"
        return entry_price * (1 + {{ params.get('profit_target', 0.03) }})
    
    def calculate_stop_loss(self, entry_price: float) -> float:
        """\"
        计算止损价格
        
        参数:
            entry_price (float): 入场价格
            
        返回:
            float: 止损价格
        """\"
        return entry_price * (1 - {{ params.get('stop_loss', 0.02) }})
""""
        )
        self.add_template(basic_template)
        
        # 趋势跟踪策略模板
        trend_template = StrategyTemplate(
            template_id="trend_following",
            name="趋势跟踪策略",
            description="适用于强趋势市场的趋势跟踪策略模板",
            template_content="""# -*- coding: utf-8 -*-"
"""\"
模块名称：{{ strategy_name }}
功能描述：基于{{ template_id }}模板生成的趋势跟踪交易策略
版本：1.0
创建日期：{{ created_at }}
作者：GPT-Claude AI系统
"""\"

from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
import talib


class {{ strategy_name.replace(' ', '') }}:
    """\"
    {{ params.get('description', '趋势跟踪交易策略') }}
    """\"
    
    def __init__(self):
        """\"
        初始化策略
        """\"
        # 策略参数
        self.name = "{{ strategy_name }}"
        self.timeframe = "{{ params.get('timeframe', '4h') }}"
        self.risk_level = "{{ params.get('risk_level', 'medium') }}"
        
        # 指标参数
        self.atr_period = {{ params.get('atr_period', 14) }}
        self.ema_short = {{ params.get('ema_short', 20) }}
        self.ema_long = {{ params.get('ema_long', 50) }}
        self.adx_period = {{ params.get('adx_period', 14) }}
        self.adx_threshold = {{ params.get('adx_threshold', 25) }}
        
        # 资金管理参数
        self.risk_per_trade = {{ params.get('risk_per_trade', 0.01) }}
        self.trailing_stop = {{ params.get('trailing_stop', 2.0) }}
        
        # 策略状态
        self.position = None
        self.last_signal = None
        self.trail_price = None
    
    def populate_indicators(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """\"
        计算技术指标
        
        参数:
            dataframe (pd.DataFrame): 价格数据
            
        返回:
            pd.DataFrame: 添加了指标的数据
        """\"
        # 计算EMA
        dataframe['ema_short'] = talib.EMA(dataframe['close'], timeperiod=self.ema_short)
        dataframe['ema_long'] = talib.EMA(dataframe['close'], timeperiod=self.ema_long)
        
        # 计算ATR
        dataframe['atr'] = talib.ATR(
            dataframe['high'],
            dataframe['low'],
            dataframe['close'],
            timeperiod=self.atr_period
        )
        
        # 计算ADX
        dataframe['adx'] = talib.ADX(
            dataframe['high'],
            dataframe['low'],
            dataframe['close'],
            timeperiod=self.adx_period
        )
        
        # 计算趋势方向
        dataframe['trend_up'] = dataframe['ema_short'] > dataframe['ema_long']
        dataframe['trend_down'] = dataframe['ema_short'] < dataframe['ema_long']
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """\"
        确定入场信号
        
        参数:
            dataframe (pd.DataFrame): 带有指标的价格数据
            
        返回:
            pd.DataFrame: 添加了入场信号的数据
        """\"
        dataframe['buy_signal'] = False
        
        # 定义买入条件：上升趋势确认，ADX强度足够
        {% if params.get('entry_condition', '') == 'aggressive' %}
        # 更激进的入场条件
        buy_condition = (
            (dataframe['ema_short'] > dataframe['ema_long']) &
            (dataframe['ema_short'].shift(1) <= dataframe['ema_long'].shift(1)) &
            (dataframe['adx'] > self.adx_threshold * 0.8)
        )
        {% elif params.get('entry_condition', '') == 'conservative' %}
        # 更保守的入场条件
        buy_condition = (
            (dataframe['ema_short'] > dataframe['ema_long']) &
            (dataframe['ema_short'].shift(1) <= dataframe['ema_long'].shift(1)) &
            (dataframe['adx'] > self.adx_threshold * 1.2) &
            (dataframe['close'] > dataframe['ema_short'])
        )
        {% else %}
        # 默认入场条件
        buy_condition = (
            (dataframe['ema_short'] > dataframe['ema_long']) &
            (dataframe['ema_short'].shift(1) <= dataframe['ema_long'].shift(1)) &
            (dataframe['adx'] > self.adx_threshold)
        )
        {% endif %}
        
        dataframe.loc[buy_condition, 'buy_signal'] = True
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """\"
        确定出场信号
        
        参数:
            dataframe (pd.DataFrame): 带有指标的价格数据
            
        返回:
            pd.DataFrame: 添加了出场信号的数据
        """\"
        dataframe['sell_signal'] = False
        
        # 定义卖出条件：趋势反转或跟踪止损
        {% if params.get('exit_condition', '') == 'fast' %}
        # 更快速的出场条件
        sell_condition = (
            (dataframe['ema_short'] < dataframe['ema_long']) |
            (dataframe['adx'] < self.adx_threshold * 0.8)
        )
        {% elif params.get('exit_condition', '') == 'trailing' %}
        # 跟踪止损出场
        # 注意：这部分需要在回测引擎中实现
        sell_condition = False
        {% else %}
        # 默认出场条件
        sell_condition = (
            (dataframe['ema_short'] < dataframe['ema_long']) &
            (dataframe['ema_short'].shift(1) >= dataframe['ema_long'].shift(1))
        )
        {% endif %}
        
        dataframe.loc[sell_condition, 'sell_signal'] = True
        
        return dataframe
    
    def calculate_position_size(self, capital: float, entry_price: float, stop_loss_price: float) -> float:
        """\"
        计算仓位大小
        
        参数:
            capital (float): 可用资金
            entry_price (float): 入场价格
            stop_loss_price (float): 止损价格
            
        返回:
            float: 仓位大小（单位）
        """\"
        risk_amount = capital * self.risk_per_trade
        risk_per_unit = abs(entry_price - stop_loss_price)
        position_size = risk_amount / risk_per_unit
        
        return position_size
    
    def calculate_stop_loss(self, entry_price: float, dataframe: pd.DataFrame, index: int) -> float:
        """\"
        计算止损价格
        
        参数:
            entry_price (float): 入场价格
            dataframe (pd.DataFrame): 价格数据
            index (int): 当前数据索引
            
        返回:
            float: 止损价格
        """\"
        # 基于ATR的止损
        atr = dataframe.loc[index, 'atr']
        stop_distance = atr * {{ params.get('stop_loss_atr', 2.0) }}
        
        # 入场点下方ATR的倍数
        return entry_price - stop_distance
    
    def update_trailing_stop(self, current_price: float) -> float:
        """\"
        更新跟踪止损价格
        
        参数:
            current_price (float): 当前价格
            
        返回:
            float: 更新后的跟踪止损价格
        """\"
        if self.trail_price is None or current_price > self.trail_price:
            self.trail_price = current_price
            
        # 计算跟踪止损价格：最高价下方ATR的倍数
        stop_price = self.trail_price * (1 - self.trailing_stop / 100)
        
        return stop_price
""""
        )
        self.add_template(trend_template)
        
        # 完全由GPT生成的策略模板
        gpt_template = StrategyTemplate(
            template_id="gpt_generated",
            name="GPT生成策略",
            description="完全由GPT生成的策略，不使用预定义模板",
            template_content="# 此模板不包含预定义内容，将完全由GPT根据市场数据和配置生成"
        )
        self.add_template(gpt_template)
        
        logger.info("已加载默认模板")


class TemplateRenderError(Exception):
    """"
    模板渲染错误
    """"
    pass


class TemplateNotFoundError(Exception):
    """"
    模板不存在错误
    """"
    pass


class ParsingError(Exception):
    """"
    响应解析错误
    """"
    pass