""" "
模块名称：communication
功能描述：实现GPT和Claude之间的通信协议，管理AI组件间的消息传递
版本：1.0
创建日期：2025-04-20
作者：开发窗口9.6
"""

import json
import logging
import time
from typing import Dict, List, Optional, Union, Any
from abc import ABC, abstractmethod
import requests

# 配置日志
logger = logging.getLogger(__name__)


class AIComponent(ABC):
    """
    AI组件的抽象基类

    所有AI交互组件必须继承此类并实现必要方法
    """

    @abstractmethod
    def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送消息到AI组件

        参数:
            message (Dict[str, Any]): 要发送的消息，包含指令和数据

        返回:
            Dict[str, Any]: AI组件的响应

        异常:
            CommunicationError: 通信失败时抛出
        """
        pass

    @abstractmethod
    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理AI组件的响应

        参数:
            response (Dict[str, Any]): AI组件的原始响应

        返回:
            Dict[str, Any]: 处理后的响应
        """
        pass


class GptCommunicator(AIComponent):
    """
    GPT通信器，负责与GPT-4o API的通信
    """

    def __init__(self, api_key: str, model: str = "gpt-4o", endpoint: str = None):
        """
        初始化GPT通信器

        参数:
            api_key (str): GPT API密钥
            model (str): 使用的GPT模型，默认为"gpt-4o"
            endpoint (str, optional): 自定义API端点
        """
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint or "https://api.openai.com/v1/chat/completions"
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"}
        )

    def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送消息到GPT API

        参数:
            message (Dict[str, Any]): 包含指令和数据的消息

        返回:
            Dict[str, Any]: GPT的响应

        异常:
            CommunicationError: 通信失败时抛出
        """
        try:
            # 准备请求数据
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": message.get(
                            "system_prompt", "你是一个量化交易策略决策系统"
                        ),
                    },
                    {"role": "user", "content": json.dumps(
                        message.get("content", {}))},
                ],
                "temperature": message.get("temperature", 0.2),
            }

            # 发送请求
            response = self.session.post(self.endpoint, json=payload)
            response.raise_for_status()

            return response.json()
        except requests.RequestException as e:
            logger.error(f"GPT通信失败: {str(e)}")
            raise CommunicationError(f"无法连接到GPT API: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"GPT响应解析失败: {str(e)}")
            raise CommunicationError(f"无法解析GPT响应: {str(e)}")

    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理GPT的响应

        参数:
            response (Dict[str, Any]): GPT的原始响应

        返回:
            Dict[str, Any]: 处理后的响应，包含决策结果
        """
        try:
            # 提取GPT的文本响应
            content = (
                response.get("choices", [{}])[0].get(
                    "message", {}).get("content", "")
            )

            # 尝试解析JSON内容
            try:
                decision_data = json.loads(content)
            except json.JSONDecodeError:
                # 如果不是有效的JSON，尝试提取JSON部分
                import re

                json_match = re.search(r"```json\s*([\s\S]*?)\s*```", content)
                if json_match:
                    try:
                        decision_data = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        decision_data = {
                            "error": "无法解析JSON响应",
                            "raw_content": content,
                        }
                else:
                    decision_data = {
                        "error": "响应不是有效的JSON格式",
                        "raw_content": content,
                    }

            return {
                "timestamp": time.time(),
                "model": self.model,
                "decision": decision_data,
                "raw_response": response,
            }
        except Exception as e:
            logger.error(f"处理GPT响应时出错: {str(e)}")
            return {
                "timestamp": time.time(),
                "model": self.model,
                "error": str(e),
                "raw_response": response,
            }


class ClaudeCommunicator(AIComponent):
    """
    Claude通信器，负责与Claude API的通信
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-sonnet-20240229",
        endpoint: str = None,
    ):
        """
        初始化Claude通信器

        参数:
            api_key (str): Claude API密钥
            model (str): 使用的Claude模型，默认为"claude-3-sonnet-20240229"
            endpoint (str, optional): 自定义API端点
        """
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint or "https://api.anthropic.com/v1/messages"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
        )

    def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送消息到Claude API

        参数:
            message (Dict[str, Any]): 包含指令和数据的消息

        返回:
            Dict[str, Any]: Claude的响应

        异常:
            CommunicationError: 通信失败时抛出
        """
        try:
            # 准备请求数据
            payload = {
                "model": self.model,
                "system": message.get("system_prompt", "你是一个量化交易策略执行系统"),
                "messages": [
                    {"role": "user", "content": json.dumps(
                        message.get("content", {}))}
                ],
                "temperature": message.get("temperature", 0.2),
                "max_tokens": message.get("max_tokens", 4000),
            }

            # 发送请求
            response = self.session.post(self.endpoint, json=payload)
            response.raise_for_status()

            return response.json()
        except requests.RequestException as e:
            logger.error(f"Claude通信失败: {str(e)}")
            raise CommunicationError(f"无法连接到Claude API: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Claude响应解析失败: {str(e)}")
            raise CommunicationError(f"无法解析Claude响应: {str(e)}")

    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理Claude的响应

        参数:
            response (Dict[str, Any]): Claude的原始响应

        返回:
            Dict[str, Any]: 处理后的响应，包含执行结果
        """
        try:
            # 提取Claude的文本响应
            content = response.get("content", [{}])[0].get("text", "")

            # 尝试解析JSON内容
            try:
                execution_data = json.loads(content)
            except json.JSONDecodeError:
                # 如果不是有效的JSON，尝试提取JSON部分
                import re

                json_match = re.search(r"```json\s*([\s\S]*?)\s*```", content)
                if json_match:
                    try:
                        execution_data = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        execution_data = {
                            "error": "无法解析JSON响应",
                            "raw_content": content,
                        }
                else:
                    execution_data = {
                        "error": "响应不是有效的JSON格式",
                        "raw_content": content,
                    }

            return {
                "timestamp": time.time(),
                "model": self.model,
                "execution": execution_data,
                "raw_response": response,
            }
        except Exception as e:
            logger.error(f"处理Claude响应时出错: {str(e)}")
            return {
                "timestamp": time.time(),
                "model": self.model,
                "error": str(e),
                "raw_response": response,
            }


class CommunicationManager:
    """
    通信管理器，协调GPT和Claude之间的通信
    """

    def __init__(
        self, gpt_communicator: GptCommunicator, claude_communicator: ClaudeCommunicator
    ):
        """
        初始化通信管理器

        参数:
            gpt_communicator (GptCommunicator): GPT通信器实例
            claude_communicator (ClaudeCommunicator): Claude通信器实例
        """
        self.gpt = gpt_communicator
        self.claude = claude_communicator
        self.conversation_history = []

    def execute_trading_workflow(
        self, market_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行完整的交易工作流，从GPT决策到Claude执行

        参数:
            market_data (Dict[str, Any]): 市场数据
            config (Dict[str, Any]): 交易配置

        返回:
            Dict[str, Any]: 执行结果，包含决策和执行细节
        """
        try:
            # 1. 准备发送给GPT的市场数据和配置
            gpt_message = self._prepare_gpt_message(market_data, config)

            # 2. 获取GPT的决策
            gpt_response = self.gpt.send_message(gpt_message)
            gpt_result = self.gpt.process_response(gpt_response)

            # 3. 准备发送给Claude的执行指令
            claude_message = self._prepare_claude_message(
                gpt_result, market_data, config
            )

            # 4. 获取Claude的执行结果
            claude_response = self.claude.send_message(claude_message)
            claude_result = self.claude.process_response(claude_response)

            # 5. 保存交互历史
            interaction = {
                "timestamp": time.time(),
                "market_data": market_data,
                "config": config,
                "gpt_decision": gpt_result,
                "claude_execution": claude_result,
            }
            self.conversation_history.append(interaction)

            # 6. 返回完整的执行结果
            return {
                "workflow_id": f"wf-{int(time.time())}",
                "timestamp": time.time(),
                "gpt_decision": gpt_result.get("decision", {}),
                "claude_execution": claude_result.get("execution", {}),
                "status": (
                    "completed"
                    if "error" not in gpt_result and "error" not in claude_result
                    else "error"
                ),
                "errors": self._collect_errors(gpt_result, claude_result),
            }
        except Exception as e:
            logger.error(f"交易工作流执行失败: {str(e)}")
            return {
                "workflow_id": f"wf-{int(time.time())}",
                "timestamp": time.time(),
                "status": "failed",
                "error": str(e),
            }

    def _prepare_gpt_message(
        self, market_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        准备发送给GPT的消息

        参数:
            market_data (Dict[str, Any]): 市场数据
            config (Dict[str, Any]): 交易配置

        返回:
            Dict[str, Any]: 格式化的GPT消息
        """
        system_prompt = """
        你是一个先进的量化交易策略决策系统。
        你的任务是分析市场数据，并根据配置选择和组合合适的交易策略。
        你需要提供详细的决策理由，以及完整的策略参数配置。
        你的输出必须是一个有效的JSON对象，包含以下字段：
        - strategy_selection: 选择的策略列表
        - parameters: 每个策略的参数配置
        - allocation: 资金分配比例
        - reasoning: 决策原因
        - market_analysis: 市场分析结果
        """

        content = {
            "market_data": market_data,
            "available_strategies": config.get("available_strategies", []),
            "risk_profile": config.get("risk_profile", "medium"),
            "time_horizon": config.get("time_horizon", "medium"),
            "constraints": config.get("constraints", {}),
        }

        return {
            "system_prompt": system_prompt,
            "content": content,
            "temperature": config.get("gpt_temperature", 0.2),
        }

    def _prepare_claude_message(
        self,
        gpt_result: Dict[str, Any],
        market_data: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        准备发送给Claude的消息

        参数:
            gpt_result (Dict[str, Any]): GPT的决策结果
            market_data (Dict[str, Any]): 市场数据
            config (Dict[str, Any]): 交易配置

        返回:
            Dict[str, Any]: 格式化的Claude消息
        """
        system_prompt = """
        你是一个高效的量化交易策略执行系统。
        你的任务是根据GPT的决策执行交易策略，并提供详细的执行报告。
        你需要验证策略参数，执行交易操作，并评估执行效果。
        你的输出必须是一个有效的JSON对象，包含以下字段：
        - execution_id: 执行ID
        - strategies_executed: 已执行的策略列表
        - execution_details: 执行细节
        - performance_metrics: 性能指标
        - validation_results: 验证结果
        - warnings: 执行警告
        """

        content = {
            "gpt_decision": gpt_result.get("decision", {}),
            "market_data": market_data,
            "execution_config": config.get("execution", {}),
            "constraints": config.get("constraints", {}),
        }

        return {
            "system_prompt": system_prompt,
            "content": content,
            "temperature": config.get("claude_temperature", 0.2),
            "max_tokens": config.get("claude_max_tokens", 4000),
        }

    def _collect_errors(
        self, gpt_result: Dict[str, Any], claude_result: Dict[str, Any]
    ) -> List[str]:
        """
        收集GPT和Claude结果中的错误

        参数:
            gpt_result (Dict[str, Any]): GPT的结果
            claude_result (Dict[str, Any]): Claude的结果

        返回:
            List[str]: 错误列表
        """
        errors = []

        if "error" in gpt_result:
            errors.append(f"GPT错误: {gpt_result['error']}")

        if "error" in claude_result:
            errors.append(f"Claude错误: {claude_result['error']}")

        if (
            "decision" in gpt_result
            and isinstance(gpt_result["decision"], dict)
            and "error" in gpt_result["decision"]
        ):
            errors.append(f"GPT决策错误: {gpt_result['decision']['error']}")

        if (
            "execution" in claude_result
            and isinstance(claude_result["execution"], dict)
            and "error" in claude_result["execution"]
        ):
            errors.append(f"Claude执行错误: {claude_result['execution']['error']}")

        return errors


class CommunicationError(Exception):
    """
    通信错误，在AI组件通信失败时抛出
    """

    pass