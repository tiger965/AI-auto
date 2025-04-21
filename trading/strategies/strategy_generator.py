"""
模块名称: strategies.strategy_generator
功能描述: 与GPT通信并生成新策略的工具
版本: 1.0
创建日期: 2025-04-20
作者: 窗口9.2开发者
"""

import logging
import json
import os
from typing import Dict, List, Optional, Any, Union, Tuple

# 设置日志
logger = logging.getLogger(__name__)


class StrategyTemplate:
    """
    策略模板类，用于构建GPT策略生成提示

    属性:
        name (str): 模板名称
        description (str): 模板描述
        template_structure (Dict): 模板结构
    """

    def __init__(self, name: str, description: str, template_structure: Dict):
        """
        初始化策略模板

        参数:
            name (str): 模板名称
            description (str): 模板描述
            template_structure (Dict): 模板结构
        """
        self.name = name
        self.description = description
        self.template_structure = template_structure

    def to_dict(self) -> Dict:
        """
        将模板转换为字典

        返回:
            Dict: 包含模板信息的字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "template_structure": self.template_structure,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "StrategyTemplate":
        """
        从字典创建模板

        参数:
            data (Dict): 包含模板信息的字典

        返回:
            StrategyTemplate: 策略模板实例
        """
        return cls(
            name=data["name"],
            description=data["description"],
            template_structure=data["template_structure"],
        )


class StrategyGenerator:
    """
    策略生成器类，用于与GPT通信并生成策略

    属性:
        templates_dir (str): 模板目录
        generated_dir (str): 生成策略目录
        available_templates (Dict[str, StrategyTemplate]): 可用模板
    """

    def __init__(self, gpt_interface=None):
        """
        初始化策略生成器

        参数:
            gpt_interface: GPT接口对象
        """
        self.gpt_interface = gpt_interface
        self.templates_dir = os.path.join(
            os.path.dirname(__file__), "templates")
        self.generated_dir = os.path.join(
            os.path.dirname(__file__), "generated")

        # 加载可用模板
        self.available_templates = self._load_templates()

        logger.info(
            f"策略生成器初始化完成，加载了 {len(self.available_templates)} 个模板"
        )

    def _load_templates(self) -> Dict[str, StrategyTemplate]:
        """
        加载可用的策略模板

        返回:
            Dict[str, StrategyTemplate]: 模板名称到模板对象的映射
        """
        templates = {}

        # 基础策略模板
        basic_template = StrategyTemplate(
            name="basic",
            description="基础策略模板，包含简单的技术指标和交易规则",
            template_structure={
                "base_class": "BasicStrategy",
                "indicators": ["SMA", "RSI"],
                "entry_conditions": ["价格上涨", "RSI低于超卖水平"],
                "exit_conditions": ["价格下跌", "RSI高于超买水平"],
            },
        )
        templates["basic"] = basic_template

        # 高级策略模板
        advanced_template = StrategyTemplate(
            name="advanced",
            description="高级策略模板，包含复杂的技术指标、市场状态检测和风险管理",
            template_structure={
                "base_class": "AdvancedStrategy",
                "indicators": ["EMA", "MACD", "Bollinger Bands", "RSI", "ATR"],
                "market_states": ["趋势市场", "震荡市场"],
                "entry_conditions": ["多重指标确认", "趋势方向识别", "支撑位回调"],
                "exit_conditions": ["趋势反转", "超买信号", "自定义止盈"],
                "risk_management": ["动态止损", "仓位管理"],
            },
        )
        templates["advanced"] = advanced_template

        return templates

    def list_templates(self) -> List[Dict]:
        """
        列出所有可用模板

        返回:
            List[Dict]: 包含模板信息的字典列表
        """
        return [template.to_dict() for template in self.available_templates.values()]

    def generate_strategy(
        self, template_name: str, strategy_name: str, parameters: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[str]]:
        """
        使用GPT生成新策略

        参数:
            template_name (str): 模板名称
            strategy_name (str): 策略名称
            parameters (Dict[str, Any]): 策略参数

        返回:
            Tuple[bool, str, Optional[str]]:
                - 是否成功
                - 消息
                - 生成的策略代码（如果成功）
        """
        if not self.gpt_interface:
            return False, "未配置GPT接口", None

        if template_name not in self.available_templates:
            return False, f"模板 '{template_name}' 不存在", None

        template = self.available_templates[template_name]

        try:
            # 构建GPT提示
            prompt = self._build_strategy_prompt(
                template, strategy_name, parameters)

            # 调用GPT接口
            response = self.gpt_interface.generate_code(prompt)

            if not response:
                return False, "GPT生成策略失败", None

            # 保存生成的策略
            file_path = os.path.join(
                self.generated_dir, f"{strategy_name.lower()}.py")
            with open(file_path, "w") as f:
                f.write(response)

            logger.info(f"成功生成策略 {strategy_name} 并保存到 {file_path}")
            return True, f"成功生成策略 {strategy_name}", response

        except Exception as e:
            logger.error(f"生成策略时出错: {e}")
            return False, f"生成策略时出错: {e}", None

    def _build_strategy_prompt(
        self, template: StrategyTemplate, strategy_name: str, parameters: Dict[str, Any]
    ) -> str:
        """
        构建策略生成提示

        参数:
            template (StrategyTemplate): 策略模板
            strategy_name (str): 策略名称
            parameters (Dict[str, Any]): 策略参数

        返回:
            str: GPT提示
        """
        base_class = template.template_structure.get(
            "base_class", "BasicStrategy")

        prompt = f"""
        请生成一个名为 {strategy_name} 的量化交易策略，继承自 {base_class}。
        
        策略说明:
        {parameters.get('description', '一个加密货币量化交易策略')}
        
        策略应该包含以下功能:
        1. 使用以下技术指标: {', '.join(parameters.get('indicators', template.template_structure.get('indicators', [])))}
        2. 入场条件: {parameters.get('entry_conditions', '根据指标生成买入信号')}
        3. 出场条件: {parameters.get('exit_conditions', '根据指标生成卖出信号')}
        
        请确保:
        - 策略遵循 Freqtrade 框架规范
        - 代码包含完整的文档注释
        - 实现必要的方法: populate_indicators, populate_entry_trend, populate_exit_trend
        - 参数可配置且有合理的默认值
        
        请直接返回完整的 Python 代码，不需要额外解释。
        """

        return prompt

    def validate_generated_strategy(self, strategy_code: str) -> Tuple[bool, str]:
        """
        验证生成的策略代码

        参数:
            strategy_code (str): 策略代码

        返回:
            Tuple[bool, str]: 是否有效，错误消息
        """
        # 检查必要的方法是否存在
        required_methods = [
            "populate_indicators",
            "populate_entry_trend",
            "populate_exit_trend",
        ]

        for method in required_methods:
            if f"def {method}" not in strategy_code:
                return False, f"缺少必要方法: {method}"

        # TODO: 添加更多验证，如语法检查等

        return True, "策略代码验证通过"


# 导出类
__all__ = ["StrategyTemplate", "StrategyGenerator"]