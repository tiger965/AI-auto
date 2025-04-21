# api/modules/gpt_claude_bridge.py
"""
GPT-Claude协作桥接模块
负责GPT和Claude之间的通信与协作，GPT作为"大脑"负责决策，Claude作为"执行臂"负责代码实现
"""

import os
import json
import time
import requests
from typing import Dict, List, Any, Optional, Union


class GPTClaudeBridge:
    """GPT与Claude协作的桥接模块"""

    def __init__(self, config_path=None):
        """
        初始化GPT-Claude桥接

        参数:
            config_path (str, optional): 配置文件路径
        """
        self.gpt_api_key = os.environ.get("GPT_API_KEY", "")
        self.claude_api_key = os.environ.get("CLAUDE_API_KEY", "")

        # 从配置文件加载（如果提供）
        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                self.gpt_api_key = config.get("gpt_api_key", self.gpt_api_key)
                self.claude_api_key = config.get(
                    "claude_api_key", self.claude_api_key)
                self.gpt_endpoint = config.get(
                    "gpt_endpoint", "https://api.openai.com/v1/chat/completions"
                )
                self.claude_endpoint = config.get(
                    "claude_endpoint", "https://api.anthropic.com/v1/messages"
                )
                self.gpt_model = config.get("gpt_model", "gpt-4")
                self.claude_model = config.get(
                    "claude_model", "claude-3-sonnet-20240229"
                )
        else:
            # 默认设置
            self.gpt_endpoint = "https://api.openai.com/v1/chat/completions"
            self.claude_endpoint = "https://api.anthropic.com/v1/messages"
            self.gpt_model = "gpt-4"
            self.claude_model = "claude-3-sonnet-20240229"

        self.conversation_history = []
        print("GPT-Claude桥接初始化成功")

    def process_prompt(self, prompt: str) -> str:
        """
        处理提示词，先经过GPT进行决策，再由Claude执行

        参数:
            prompt (str): 用户提交的提示词

        返回:
            str: 处理结果
        """
        # 记录到对话历史
        self.conversation_history.append({"role": "user", "content": prompt})

        # 模拟处理，实际应用中应连接到API
        try:
            # 1. 发送到GPT进行决策分析
            gpt_response = self._call_gpt(prompt)

            # 2. 将GPT的决策传递给Claude执行
            claude_response = self._call_claude(gpt_response)

            # 3. 记录响应并返回结果
            self.conversation_history.append(
                {"role": "assistant", "content": claude_response}
            )
            return claude_response

        except Exception as e:
            error_message = f"处理提示词时出错: {str(e)}"
            print(error_message)
            return error_message

    def _call_gpt(self, prompt: str) -> str:
        """
        调用GPT API进行决策分析

        参数:
            prompt (str): 用户提示词

        返回:
            str: GPT的决策分析结果
        """
        print(f"调用GPT进行决策分析: {prompt[:50]}...")

        # 实际应用中连接到GPT API
        # 目前使用模拟响应用于测试
        if not self.gpt_api_key:
            return "模拟GPT分析: 建议使用RSI+MACD的交叉策略，短期过度买入卖出信号"

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.gpt_api_key}",
            }

            data = {
                "model": self.gpt_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的量化交易策略分析师，负责分析市场数据并提出交易策略建议。",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
            }

            response = requests.post(
                self.gpt_endpoint, headers=headers, json=data, timeout=30
            )

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(f"GPT API错误: {response.status_code} - {response.text}")
                return f"GPT API返回错误: {response.status_code}"

        except Exception as e:
            print(f"调用GPT时出错: {str(e)}")
            return "模拟GPT分析: 建议使用基于趋势跟踪的策略，结合移动平均线和成交量指标"

    def _call_claude(self, gpt_decision: str) -> str:
        """
        调用Claude API将GPT的决策转化为代码

        参数:
            gpt_decision (str): GPT的决策分析结果

        返回:
            str: Claude生成的代码或执行结果
        """
        print(f"调用Claude执行决策: {gpt_decision[:50]}...")

        # 实际应用中连接到Claude API
        # 目前使用模拟响应用于测试
        if not self.claude_api_key:
            return "模拟Claude执行结果:\n```python\ndef strategy(data):\n    # 基于GPT建议实现的RSI+MACD策略\n    # ...\n    return signals\n```"

        try:
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.claude_api_key,
                "anthropic-version": "2023-06-01",
            }

            data = {
                "model": self.claude_model,
                "messages": [
                    {
                        "role": "user",
                        "content": f"我需要你将以下交易策略分析转化为Python代码:\n\n{gpt_decision}\n\n请生成可以在Freqtrade框架中运行的完整策略代码。",
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 4000,
            }

            response = requests.post(
                self.claude_endpoint, headers=headers, json=data, timeout=30
            )

            if response.status_code == 200:
                return response.json()["content"][0]["text"]
            else:
                print(
                    f"Claude API错误: {response.status_code} - {response.text}")
                return f"Claude API返回错误: {response.status_code}"

        except Exception as e:
            print(f"调用Claude时出错: {str(e)}")
            return "模拟Claude执行结果:\n```python\n# 基于趋势跟踪的策略实现\nclass TrendFollowingStrategy(IStrategy):\n    # 参数定义\n    # 策略逻辑\n    # 信号生成\n```"

    def generate_strategy(
        self, strategy_prompt: str, market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根据提示和市场数据生成完整交易策略

        参数:
            strategy_prompt (str): 策略描述提示
            market_data (dict): 市场数据

        返回:
            dict: 生成的策略信息
        """
        # 构建完整的提示，包含市场数据
        full_prompt = f"""
基于以下市场数据，生成交易策略:
    
市场: {market_data.get('symbol', 'BTC/USDT')}
时间框架: {market_data.get('timeframe', '1h')}
当前趋势: {market_data.get('recent_trend', '未知')}

策略要求:
{strategy_prompt}

请生成完整的交易策略，包括入场条件、出场条件、风险管理和参数设置。
        """

        # 获取GPT和Claude的合作结果
        strategy_content = self.process_prompt(full_prompt)

        # 构建策略对象
        strategy = {
            "name": f"策略_{int(time.time())}",
            "description": strategy_prompt,
            "content": strategy_content,
            "market_data": market_data,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
        }

        return strategy

    def convert_to_code(self, strategy_description: str) -> str:
        """
        将策略描述转换为可执行代码

        参数:
            strategy_description (str): 策略描述文本

        返回:
            str: 生成的代码
        """
        code_prompt = f"""
请将以下交易策略描述转换为完整的Python代码:
    
{strategy_description}

代码应该可以在Freqtrade框架中使用，需要包含完整的类定义、参数配置和交易逻辑。
        """

        # 直接使用Claude来生成代码
        return self._call_claude(code_prompt)

    def test_connection(self, test_message="测试连接") -> str:
        """
        测试与API的连接

        参数:
            test_message (str): 测试消息

        返回:
            str: 连接测试结果
        """
        try:
            # 简单的连接测试
            gpt_result = "连接成功" if self.gpt_api_key else "未配置GPT API密钥"
            claude_result = (
                "连接成功" if self.claude_api_key else "未配置Claude API密钥"
            )

            return f"GPT连接状态: {gpt_result}\nClaude连接状态: {claude_result}\n测试消息: {test_message}"
        except Exception as e:
            return f"连接测试失败: {str(e)}"