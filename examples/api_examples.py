"""
API使用示例模块

本模块展示如何使用项目的API接口进行各种操作，包括：
1. 基础API调用
2. 异步API调用
3. 批量API处理
4. API错误处理

运行环境要求：
- Python 3.8+
- 已安装依赖库（requests, aiohttp）
- 有效的API密钥配置在环境变量或配置文件中

预期输出：
各示例将展示成功的API调用结果和错误处理情况
"""

from myproject.exceptions import APIError, AuthenticationError, RateLimitError
from myproject.utils import config
from myproject.api import client
import os
import sys
import time
import json
import asyncio
import requests
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径，以便导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目中的API模块（根据实际项目结构调整导入路径）

# 加载配置
API_KEY = config.get_api_key()
API_ENDPOINT = config.get_api_endpoint()


def run_all():
    """运行所有API示例"""
    print("开始运行API示例...")

    # 运行基础API调用示例
    run_basic_api_example()

    # 运行异步API调用示例
    asyncio.run(run_async_api_example())

    # 运行批量API处理示例
    run_batch_api_example()

    # 运行API错误处理示例
    run_error_handling_example()

    print("API示例运行完成！")


def run_basic_api_example():
    """
    基础API调用示例

    展示如何初始化API客户端并执行基本调用
    """
    print("\n--- 基础API调用示例 ---")

    # 初始化API客户端
    api = client.APIClient(api_key=API_KEY, endpoint=API_ENDPOINT)

    # 执行模型推理API调用
    prompt = "为我生成一个关于人工智能的简短描述"

    print(f"发送请求: {prompt}")
    response = api.generate_text(
        prompt=prompt, max_tokens=100, temperature=0.7)

    # 打印API调用结果
    print(f"API响应状态: {response.status}")
    print(f"生成的文本: {response.text}")
    print(f"使用的token数: {response.usage.total_tokens}")

    # 示例如何获取响应的元数据
    metadata = response.metadata
    print(f"模型名称: {metadata.model}")
    print(f"请求ID: {metadata.request_id}")

    return response


async def run_async_api_example():
    """
    异步API调用示例

    展示如何使用异步API客户端同时处理多个请求
    """
    print("\n--- 异步API调用示例 ---")

    # 初始化异步API客户端
    async_api = client.AsyncAPIClient(api_key=API_KEY, endpoint=API_ENDPOINT)

    # 准备多个请求
    prompts = [
        "为我总结机器学习的定义",
        "为我总结深度学习的定义",
        "为我总结自然语言处理的定义",
    ]

    # 创建异步任务列表
    tasks = []
    for prompt in prompts:
        task = async_api.generate_text(
            prompt=prompt, max_tokens=50, temperature=0.5)
        tasks.append(task)

    print(f"异步发送 {len(tasks)} 个请求...")

    # 并行执行所有API请求
    start_time = time.time()
    responses = await asyncio.gather(*tasks)
    elapsed_time = time.time() - start_time

    # 处理所有响应
    for i, response in enumerate(responses):
        print(f"\n请求 {i+1} 结果:")
        print(f"提示: {prompts[i]}")
        print(f"生成的文本: {response.text}")

    print(f"\n异步处理完成, 总耗时: {elapsed_time:.2f}秒")
    return responses


def run_batch_api_example():
    """
    批量API处理示例

    展示如何使用批处理API更有效地处理多个请求
    """
    print("\n--- 批量API处理示例 ---")

    # 初始化API客户端
    api = client.APIClient(api_key=API_KEY, endpoint=API_ENDPOINT)

    # 准备批量请求数据
    batch_inputs = [
        {"prompt": "描述猫的特点", "max_tokens": 30},
        {"prompt": "描述狗的特点", "max_tokens": 30},
        {"prompt": "描述鸟的特点", "max_tokens": 30},
    ]

    print(f"发送批量请求, 包含 {len(batch_inputs)} 个子请求...")

    # 执行批量处理
    batch_response = api.batch_generate(
        inputs=batch_inputs, temperature=0.7, batch_size=3  # 一次处理的最大请求数
    )

    # 处理批量响应
    print(f"批量请求状态: {batch_response.status}")

    for i, result in enumerate(batch_response.results):
        print(f"\n子请求 {i+1} 结果:")
        print(f"提示: {batch_inputs[i]['prompt']}")
        print(f"生成的文本: {result.text}")

    # 显示批量处理性能统计
    print(f"\n批量处理性能:")
    print(f"总Token使用量: {batch_response.usage.total_tokens}")
    print(f"平均每个请求耗时: {batch_response.statistics.avg_time_per_request:.3f}秒")

    return batch_response


def run_error_handling_example():
    """
    API错误处理示例

    展示如何处理API调用中可能出现的各种错误
    """
    print("\n--- API错误处理示例 ---")

    # 初始化API客户端
    api = client.APIClient(api_key=API_KEY, endpoint=API_ENDPOINT)

    # 1. 演示认证错误
    try:
        print("模拟认证错误...")
        # 使用无效的API密钥
        invalid_api = client.APIClient(
            api_key="invalid_key", endpoint=API_ENDPOINT)
        response = invalid_api.generate_text(prompt="测试", max_tokens=10)
    except AuthenticationError as e:
        print(f"正确捕获认证错误: {e}")

    # 2. 演示参数错误
    try:
        print("\n模拟参数错误...")
        # 使用无效的参数值
        response = api.generate_text(prompt="测试", max_tokens=-1)  # 无效的token数
    except APIError as e:
        print(f"正确捕获参数错误: {e}")

    # 3. 演示速率限制错误
    try:
        print("\n模拟速率限制错误...")
        # 模拟速率限制(实际项目中可能需要特殊设置才能触发)
        for _ in range(5):
            # 快速发送多个请求模拟触发速率限制
            api.generate_text(prompt="测试", max_tokens=5)
    except RateLimitError as e:
        print(f"正确捕获速率限制错误: {e}")
    except Exception as e:
        print(f"注意: 在测试环境中可能无法触发真实的速率限制, 捕获其他异常: {e}")

    # 4. 演示优雅处理错误的模式
    print("\n演示优雅的错误处理模式...")

    def safe_api_call(prompt, retries=3, backoff=2):
        """安全的API调用函数，包含重试逻辑"""
        attempt = 0
        while attempt < retries:
            try:
                return api.generate_text(prompt=prompt, max_tokens=20)
            except RateLimitError:
                # 指数退避重试
                wait_time = backoff**attempt
                print(f"遇到速率限制，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                attempt += 1
            except AuthenticationError as e:
                # 认证错误不重试
                print(f"认证错误: {e}")
                return None
            except APIError as e:
                # 其他API错误可能重试
                if "server_error" in str(e).lower():
                    attempt += 1
                    print(f"服务器错误，尝试重试 ({attempt}/{retries})...")
                else:
                    print(f"API错误（不重试）: {e}")
                    return None

        print(f"达到最大重试次数 ({retries})，操作失败")
        return None

    # 测试安全API调用函数
    result = safe_api_call("测试安全API调用的示例")
    if result:
        print(f"安全API调用成功: {result.text}")
    else:
        print("安全API调用失败或被中止")


if __name__ == "__main__":
    # 运行所有API示例
    run_all()