"""
trading/gpt_claude/gpt_claude_bridge.py
功能描述: 实现GPT-4o和Claude之间的高效通信桥接，处理策略生成和反馈的完整流程
版本: 1.0.0
创建日期: 2025-04-20
"""

import json
import asyncio
import logging
import time
import aiohttp
from typing import Dict, Any, Optional, List, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("gpt_claude_bridge")

# 全局常量
MAX_RETRY_COUNT = 3
RETRY_DELAY = 2  # 秒
DEFAULT_TIMEOUT = 30  # 秒

# 通信桥接状态
BRIDGE_STATUS = {
    "initialized": False,
    "gpt_connection": None,
    "claude_connection": None,
    "last_error": None,
    "active_requests": {},
}


class ModelConnectionError(Exception):
    """模型连接异常"""

    pass


class StrategyValidationError(Exception):
    """策略验证异常"""

    pass


async def _connect_to_model(model_type: str, api_key: str, endpoint: str) -> Dict:
    """
    连接到AI模型服务

    Args:
        model_type (str): 模型类型，'gpt' 或 'claude'
        api_key (str): API密钥
        endpoint (str): API端点URL

    Returns:
        Dict: 连接对象

    Raises:
        ModelConnectionError: 连接失败时抛出
    """
    try:
        # 创建会话并验证连接
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            async with session.post(
                endpoint,
                headers=headers,
                json={"type": "connection_test"},
                timeout=DEFAULT_TIMEOUT,
            ) as response:
                if response.status != 200:
                    raise ModelConnectionError(
                        f"Failed to connect to {model_type}. Status: {response.status}"
                    )

                return {
                    "session": aiohttp.ClientSession(),
                    "headers": headers,
                    "endpoint": endpoint,
                    "model_type": model_type,
                    "status": "connected",
                }
    except Exception as e:
        logger.error(f"Error connecting to {model_type}: {str(e)}")
        raise ModelConnectionError(
            f"Failed to connect to {model_type}: {str(e)}")


def initialize_bridge(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    初始化GPT-Claude通信桥接

    Args:
        config (Optional[Dict[str, Any]], optional): 配置参数. Defaults to None.

    Returns:
        bool: 初始化是否成功
    """
    global BRIDGE_STATUS

    if config is None:
        # 使用默认配置
        config = {
            "gpt": {
                "api_key": "",  # 需从环境变量或安全存储中获取
                "endpoint": "https://api.openai.com/v1/chat/completions",
                "model": "gpt-4o",
            },
            "claude": {
                "api_key": "",  # 需从环境变量或安全存储中获取
                "endpoint": "https://api.anthropic.com/v1/messages",
                "model": "claude-3-opus-20240229",
            },
            "timeout": DEFAULT_TIMEOUT,
            "retry_count": MAX_RETRY_COUNT,
        }

    try:
        # 获取API密钥（实际项目中应从安全存储获取）
        import os

        config["gpt"]["api_key"] = os.environ.get(
            "GPT_API_KEY", config["gpt"]["api_key"]
        )
        config["claude"]["api_key"] = os.environ.get(
            "CLAUDE_API_KEY", config["claude"]["api_key"]
        )

        # 异步初始化连接
        loop = asyncio.get_event_loop()
        gpt_connection, claude_connection = loop.run_until_complete(
            asyncio.gather(
                _connect_to_model(
                    "gpt", config["gpt"]["api_key"], config["gpt"]["endpoint"]
                ),
                _connect_to_model(
                    "claude", config["claude"]["api_key"], config["claude"]["endpoint"]
                ),
            )
        )

        # 更新状态
        BRIDGE_STATUS["initialized"] = True
        BRIDGE_STATUS["gpt_connection"] = gpt_connection
        BRIDGE_STATUS["claude_connection"] = claude_connection
        BRIDGE_STATUS["config"] = config
        BRIDGE_STATUS["last_error"] = None

        logger.info("GPT-Claude bridge initialized successfully")
        return True

    except Exception as e:
        BRIDGE_STATUS["initialized"] = False
        BRIDGE_STATUS["last_error"] = str(e)
        logger.error(f"Failed to initialize bridge: {str(e)}")
        return False


async def _send_request_to_model(
    model_connection: Dict, payload: Dict[str, Any], timeout: int = DEFAULT_TIMEOUT
) -> Dict[str, Any]:
    """
    发送请求到模型

    Args:
        model_connection (Dict): 模型连接对象
        payload (Dict[str, Any]): 请求负载
        timeout (int, optional): 超时时间(秒). Defaults to DEFAULT_TIMEOUT.

    Returns:
        Dict[str, Any]: 模型响应
    """
    session = model_connection["session"]
    headers = model_connection["headers"]
    endpoint = model_connection["endpoint"]
    model_type = model_connection["model_type"]

    # 添加模型特定格式
    if model_type == "gpt":
        model_name = BRIDGE_STATUS["config"]["gpt"]["model"]
        request_payload = {
            "model": model_name,
            "messages": payload["messages"],
            "temperature": payload.get("temperature", 0.7),
            "max_tokens": payload.get("max_tokens", 4000),
        }
    else:  # claude
        model_name = BRIDGE_STATUS["config"]["claude"]["model"]
        request_payload = {
            "model": model_name,
            "messages": payload["messages"],
            "temperature": payload.get("temperature", 0.7),
            "max_tokens": payload.get("max_tokens", 4000),
        }

    # 发送请求并处理重试
    retry_count = 0
    while retry_count < MAX_RETRY_COUNT:
        try:
            async with session.post(
                endpoint, headers=headers, json=request_payload, timeout=timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error from {model_type}: {error_text}")
                    raise Exception(
                        f"Failed request to {model_type}. Status: {response.status}"
                    )

                return await response.json()

        except Exception as e:
            retry_count += 1
            logger.warning(
                f"Retry {retry_count}/{MAX_RETRY_COUNT} for {model_type}: {str(e)}"
            )

            if retry_count >= MAX_RETRY_COUNT:
                raise Exception(
                    f"Max retries reached for {model_type}: {str(e)}")

            await asyncio.sleep(RETRY_DELAY * retry_count)  # 指数级退避


def _validate_strategy_structure(
    strategy_structure: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """
    验证策略结构是否符合要求

    Args:
        strategy_structure (Dict[str, Any]): 策略结构

    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    # 检查必要字段
    required_fields = [
        "strategy_id",
        "name",
        "description",
        "parameters",
        "entry_conditions",
        "exit_conditions",
    ]
    for field in required_fields:
        if field not in strategy_structure:
            return False, f"Missing required field: {field}"

    # 检查参数结构
    if not isinstance(strategy_structure["parameters"], dict):
        return False, "Parameters must be a dictionary"

    # 检查条件结构
    if (
        not isinstance(strategy_structure["entry_conditions"], list)
        or not strategy_structure["entry_conditions"]
    ):
        return False, "Entry conditions must be a non-empty list"

    if (
        not isinstance(strategy_structure["exit_conditions"], list)
        or not strategy_structure["exit_conditions"]
    ):
        return False, "Exit conditions must be a non-empty list"

    # 可以添加更多验证规则...

    return True, None


async def _send_to_gpt_async(
    strategy_request: Dict[str, Any], timeout: int = DEFAULT_TIMEOUT
) -> Dict[str, Any]:
    """
    异步发送策略需求到GPT

    Args:
        strategy_request (Dict[str, Any]): 策略请求
        timeout (int, optional): 超时时间(秒). Defaults to DEFAULT_TIMEOUT.

    Returns:
        Dict[str, Any]: GPT生成的策略结构
    """
    if not BRIDGE_STATUS["initialized"]:
        raise Exception("Bridge not initialized")

    # 构建请求
    system_prompt = """You are an expert trading strategy developer. Your task is to generate 
    a complete trading strategy based on the requirements provided. The strategy should follow 
    the specified JSON structure with clear entry and exit conditions."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(strategy_request)},
    ]

    payload = {
        "messages": messages,
        "temperature": 0.2,  # 低温度以确保更确定性的输出
        "max_tokens": 4000,
    }

    # 发送到GPT
    response = await _send_request_to_model(
        BRIDGE_STATUS["gpt_connection"], payload, timeout
    )

    # 解析响应
    try:
        if "choices" in response and len(response["choices"]) > 0:
            strategy_text = response["choices"][0]["message"]["content"]

            # 尝试解析JSON
            strategy_json_str = strategy_text
            # 如果策略包含在代码块中，提取它
            if "```json" in strategy_text and "```" in strategy_text:
                start = strategy_text.find("```json") + 7
                end = strategy_text.find("```", start)
                strategy_json_str = strategy_text[start:end].strip()
            elif "```" in strategy_text:
                start = strategy_text.find("```") + 3
                end = strategy_text.find("```", start)
                strategy_json_str = strategy_text[start:end].strip()

            strategy_structure = json.loads(strategy_json_str)

            # 验证策略结构
            is_valid, error_msg = _validate_strategy_structure(
                strategy_structure)
            if not is_valid:
                raise StrategyValidationError(
                    f"Invalid strategy structure: {error_msg}"
                )

            return strategy_structure
        else:
            raise Exception("Invalid response format from GPT")
    except json.JSONDecodeError:
        raise Exception("Failed to parse strategy JSON from GPT response")


def send_to_gpt(
    strategy_request: Dict[str, Any], timeout: int = DEFAULT_TIMEOUT
) -> Dict[str, Any]:
    """
    发送策略需求到GPT

    Args:
        strategy_request (Dict[str, Any]): 策略请求，包含市场、时间周期、风险等级等
        timeout (int, optional): 超时时间(秒). Defaults to 30.

    Returns:
        Dict[str, Any]: GPT生成的策略结构
    """
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_send_to_gpt_async(strategy_request, timeout))


async def _receive_from_gpt_async(strategy_structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    异步接收GPT生成的策略结构并发送给Claude进行分析和改进

    Args:
        strategy_structure (Dict[str, Any]): GPT生成的策略结构

    Returns:
        Dict[str, Any]: Claude分析和改进后的策略结构
    """
    if not BRIDGE_STATUS["initialized"]:
        raise Exception("Bridge not initialized")

    # 验证策略结构
    is_valid, error_msg = _validate_strategy_structure(strategy_structure)
    if not is_valid:
        raise StrategyValidationError(
            f"Invalid strategy structure: {error_msg}")

    # 构建发送给Claude的请求
    system_prompt = """You are an expert trading strategy analyzer. Your task is to analyze 
    the provided trading strategy, identify potential weaknesses, and suggest improvements. 
    Return the improved strategy in the same JSON format."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(strategy_structure)},
    ]

    payload = {"messages": messages, "temperature": 0.3, "max_tokens": 4000}

    # 发送到Claude
    response = await _send_request_to_model(
        BRIDGE_STATUS["claude_connection"], payload, DEFAULT_TIMEOUT
    )

    # 解析响应
    try:
        if "content" in response:
            strategy_text = response["content"][0]["text"]

            # 尝试解析JSON
            strategy_json_str = strategy_text
            # 如果策略包含在代码块中，提取它
            if "```json" in strategy_text and "```" in strategy_text:
                start = strategy_text.find("```json") + 7
                end = strategy_text.find("```", start)
                strategy_json_str = strategy_text[start:end].strip()
            elif "```" in strategy_text:
                start = strategy_text.find("```") + 3
                end = strategy_text.find("```", start)
                strategy_json_str = strategy_text[start:end].strip()

            improved_strategy = json.loads(strategy_json_str)

            # 验证改进后的策略结构
            is_valid, error_msg = _validate_strategy_structure(
                improved_strategy)
            if not is_valid:
                raise StrategyValidationError(
                    f"Invalid improved strategy structure: {error_msg}"
                )

            # 保留原策略ID
            improved_strategy["strategy_id"] = strategy_structure["strategy_id"]
            improved_strategy["original_strategy"] = strategy_structure
            improved_strategy["improvement_timestamp"] = time.time()

            return improved_strategy
        else:
            raise Exception("Invalid response format from Claude")
    except json.JSONDecodeError:
        raise Exception("Failed to parse strategy JSON from Claude response")


def receive_from_gpt(strategy_structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    接收GPT生成的策略结构并进行分析和改进

    Args:
        strategy_structure (Dict[str, Any]): GPT生成的策略结构

    Returns:
        Dict[str, Any]: 分析和改进后的策略结构
    """
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_receive_from_gpt_async(strategy_structure))


async def _send_feedback_to_gpt_async(
    strategy_id: str, performance_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    异步发送性能反馈给GPT用于学习

    Args:
        strategy_id (str): 策略ID
        performance_data (Dict[str, Any]): 策略性能数据

    Returns:
        Dict[str, Any]: GPT的反馈和学习结果
    """
    if not BRIDGE_STATUS["initialized"]:
        raise Exception("Bridge not initialized")

    # 构建请求
    system_prompt = """You are an expert trading strategy optimizer. Your task is to analyze 
    the performance data of a strategy and provide insights on how to improve it. Focus on 
    identifying patterns in winning and losing trades."""

    feedback_request = {
        "strategy_id": strategy_id,
        "performance_data": performance_data,
        "request_type": "strategy_feedback",
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(feedback_request)},
    ]

    payload = {"messages": messages, "temperature": 0.3, "max_tokens": 4000}

    # 发送到GPT
    response = await _send_request_to_model(
        BRIDGE_STATUS["gpt_connection"], payload, DEFAULT_TIMEOUT
    )

    # 解析响应
    try:
        if "choices" in response and len(response["choices"]) > 0:
            feedback_text = response["choices"][0]["message"]["content"]

            # 尝试解析JSON
            try:
                if "```json" in feedback_text and "```" in feedback_text:
                    start = feedback_text.find("```json") + 7
                    end = feedback_text.find("```", start)
                    feedback_json_str = feedback_text[start:end].strip()
                elif "```" in feedback_text:
                    start = feedback_text.find("```") + 3
                    end = feedback_text.find("```", start)
                    feedback_json_str = feedback_text[start:end].strip()
                else:
                    feedback_json_str = feedback_text

                feedback_data = json.loads(feedback_json_str)
            except:
                # 如果无法解析为JSON，使用文本格式
                feedback_data = {
                    "strategy_id": strategy_id,
                    "analysis": feedback_text,
                    "timestamp": time.time(),
                }

            return feedback_data
        else:
            raise Exception("Invalid response format from GPT")
    except Exception as e:
        logger.error(f"Error processing feedback response: {str(e)}")
        # 返回基本反馈以避免失败
        return {"strategy_id": strategy_id, "error": str(e), "timestamp": time.time()}


def send_feedback_to_gpt(
    strategy_id: str, performance_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    发送性能反馈给GPT用于学习

    Args:
        strategy_id (str): 策略ID
        performance_data (Dict[str, Any]): 策略性能数据

    Returns:
        Dict[str, Any]: GPT的反馈和学习结果
    """
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        _send_feedback_to_gpt_async(strategy_id, performance_data)
    )


# 辅助功能：关闭桥接连接
def close_bridge() -> bool:
    """
    关闭GPT-Claude通信桥接连接

    Returns:
        bool: 是否成功关闭
    """
    global BRIDGE_STATUS

    if not BRIDGE_STATUS["initialized"]:
        return True

    try:
        # 关闭会话
        for connection_name in ["gpt_connection", "claude_connection"]:
            if (
                BRIDGE_STATUS[connection_name]
                and "session" in BRIDGE_STATUS[connection_name]
            ):
                session = BRIDGE_STATUS[connection_name]["session"]

                # 异步关闭会话
                loop = asyncio.get_event_loop()
                loop.run_until_complete(session.close())

        # 重置状态
        BRIDGE_STATUS = {
            "initialized": False,
            "gpt_connection": None,
            "claude_connection": None,
            "last_error": None,
            "active_requests": {},
        }

        logger.info("GPT-Claude bridge closed successfully")
        return True

    except Exception as e:
        logger.error(f"Error closing bridge: {str(e)}")
        BRIDGE_STATUS["last_error"] = str(e)
        return False


# 健康检查
def get_bridge_status() -> Dict[str, Any]:
    """
    获取桥接状态

    Returns:
        Dict[str, Any]: 桥接状态信息
    """
    status_copy = BRIDGE_STATUS.copy()

    # 移除敏感信息
    if "gpt_connection" in status_copy and status_copy["gpt_connection"]:
        if "headers" in status_copy["gpt_connection"]:
            status_copy["gpt_connection"]["headers"] = "**REDACTED**"

    if "claude_connection" in status_copy and status_copy["claude_connection"]:
        if "headers" in status_copy["claude_connection"]:
            status_copy["claude_connection"]["headers"] = "**REDACTED**"

    if "config" in status_copy and status_copy["config"]:
        if "gpt" in status_copy["config"] and "api_key" in status_copy["config"]["gpt"]:
            status_copy["config"]["gpt"]["api_key"] = "**REDACTED**"
        if (
            "claude" in status_copy["config"]
            and "api_key" in status_copy["config"]["claude"]
        ):
            status_copy["config"]["claude"]["api_key"] = "**REDACTED**"

    return status_copy