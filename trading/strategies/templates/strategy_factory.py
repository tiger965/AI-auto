"""
模块名称: strategies.strategy_factory
功能描述: 策略工厂，提供创建和管理策略实例的工具
版本: 1.0
创建日期: 2025-04-20
作者: 窗口9.2开发者
"""

import logging
import importlib
import os
import inspect
from typing import Dict, List, Type, Optional, Any, Union
from pathlib import Path

# 设置日志
logger = logging.getLogger(__name__)


class StrategyFactory:
    """
    策略工厂类，提供创建和管理策略实例的工具

    属性:
        _strategy_registry (Dict): 已注册策略的注册表
        _template_registry (Dict): 可用模板的注册表
        _strategies_path (str): 策略目录路径
        _templates_path (str): 模板目录路径
    """

    def __init__(self):
        """
        初始化策略工厂
        """
        self._strategy_registry = {}
        self._template_registry = {}

        # 获取策略目录路径
        self._strategies_path = os.path.dirname(os.path.abspath(__file__))
        self._templates_path = os.path.join(self._strategies_path, "templates")

        # 加载可用模板和策略
        self._load_templates()
        self._load_strategies()

        logger.info(
            f"策略工厂初始化完成，加载了 {len(self._template_registry)} 个模板和 "
            f"{len(self._strategy_registry)} 个策略"
        )

    def _load_templates(self) -> None:
        """
        加载可用的策略模板
        """
        try:
            # 加载templates目录下的所有Python文件
            for file in os.listdir(self._templates_path):
                if file.endswith(".py") and not file.startswith("__"):
                    module_name = file[:-3]
                    try:
                        # 构建模块导入路径
                        import_path = f"trading.strategies.templates.{module_name}"
                        module = importlib.import_module(import_path)

                        # 查找模块中的策略类
                        for name, obj in inspect.getmembers(module):
                            if (
                                inspect.isclass(obj)
                                and name not in ["DataFrame", "Series"]
                                and hasattr(obj, "populate_indicators")
                            ):
                                self._template_registry[name] = obj
                                logger.debug(f"已加载模板: {name}")
                    except (ImportError, AttributeError) as e:
                        logger.error(f"加载模板 {module_name} 时出错: {e}")
        except Exception as e:
            logger.error(f"加载模板目录时出错: {e}")

    def _load_strategies(self) -> None:
        """
        加载已生成的策略
        """
        try:
            # 加载generated目录下的所有Python文件
            generated_path = os.path.join(self._strategies_path, "generated")
            for file in os.listdir(generated_path):
                if file.endswith(".py") and not file.startswith("__"):
                    module_name = file[:-3]
                    try:
                        # 构建模块导入路径
                        import_path = f"trading.strategies.generated.{module_name}"
                        module = importlib.import_module(import_path)

                        # 查找模块中的策略类
                        for name, obj in inspect.getmembers(module):
                            if (
                                inspect.isclass(obj)
                                and name not in ["DataFrame", "Series"]
                                and hasattr(obj, "populate_indicators")
                            ):
                                self._strategy_registry[name] = obj
                                logger.debug(f"已加载策略: {name}")
                    except (ImportError, AttributeError) as e:
                        logger.error(f"加载策略 {module_name} 时出错: {e}")
        except Exception as e:
            logger.error(f"加载策略目录时出错: {e}")

    def create_strategy(
        self, strategy_name: str, parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        创建策略实例

        参数:
            strategy_name (str): 策略名称
            parameters (Dict[str, Any], optional): 策略参数

        返回:
            Any: 策略实例，如果不存在则返回None
        """
        if strategy_name in self._strategy_registry:
            strategy_class = self._strategy_registry[strategy_name]
            try:
                # 如果提供了参数，使用参数初始化策略
                if parameters:
                    return strategy_class(**parameters)
                else:
                    return strategy_class()
            except Exception as e:
                logger.error(f"创建策略 {strategy_name} 实例时出错: {e}")
                return None
        else:
            logger.error(f"策略 {strategy_name} 不存在")
            return None

    def create_from_template(
        self,
        template_name: str,
        class_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        基于模板创建策略类和实例

        参数:
            template_name (str): 模板名称
            class_name (str): 新策略类名称
            parameters (Dict[str, Any], optional): 策略参数

        返回:
            Any: 策略实例，如果不存在则返回None
        """
        if template_name in self._template_registry:
            template_class = self._template_registry[template_name]
            try:
                # 创建新策略类
                new_class = type(
                    class_name,
                    (template_class,),
                    {"name": class_name, **
                        ({} if parameters is None else parameters)},
                )

                # 创建实例
                return new_class()
            except Exception as e:
                logger.error(
                    f"基于模板 {template_name} 创建策略 {class_name} 时出错: {e}"
                )
                return None
        else:
            logger.error(f"模板 {template_name} 不存在")
            return None

    def save_strategy(self, strategy_name: str, strategy_code: str) -> bool:
        """
        保存策略代码到文件

        参数:
            strategy_name (str): 策略名称
            strategy_code (str): 策略代码

        返回:
            bool: 保存成功返回True，否则返回False
        """
        try:
            generated_path = os.path.join(self._strategies_path, "generated")
            file_path = os.path.join(
                generated_path, f"{strategy_name.lower()}.py")

            with open(file_path, "w") as f:
                f.write(strategy_code)

            logger.info(f"成功保存策略 {strategy_name} 到 {file_path}")

            # 重新加载策略
            self._load_strategies()

            return True
        except Exception as e:
            logger.error(f"保存策略 {strategy_name} 时出错: {e}")
            return False

    def list_templates(self) -> Dict[str, Type]:
        """
        获取可用模板列表

        返回:
            Dict[str, Type]: 模板名称到模板类的映射
        """
        return self._template_registry

    def list_strategies(self) -> Dict[str, Type]:
        """
        获取可用策略列表

        返回:
            Dict[str, Type]: 策略名称到策略类的映射
        """
        return self._strategy_registry

    def get_template_details(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        获取模板详情

        参数:
            template_name (str): 模板名称

        返回:
            Dict[str, Any]: 模板详情，如果不存在则返回None
        """
        if template_name in self._template_registry:
            template_class = self._template_registry[template_name]
            return {
                "name": template_name,
                "description": template_class.__doc__,
                "attributes": {
                    name: value
                    for name, value in vars(template_class).items()
                    if not name.startswith("_") and not callable(value)
                },
                "methods": [
                    name
                    for name, value in vars(template_class).items()
                    if not name.startswith("_") and callable(value)
                ],
            }
        else:
            logger.error(f"模板 {template_name} 不存在")
            return None

    def reload(self) -> None:
        """
        重新加载所有模板和策略
        """
        self._template_registry = {}
        self._strategy_registry = {}
        self._load_templates()
        self._load_strategies()
        logger.info(
            f"重新加载完成，加载了 {len(self._template_registry)} 个模板和 "
            f"{len(self._strategy_registry)} 个策略"
        )


# 创建全局工厂实例
strategy_factory = StrategyFactory()
except Exception as e:
    print(f"错误: {str(e)}")

# 导出工厂实例
__all__ = ["strategy_factory"]