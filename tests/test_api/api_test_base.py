"""
API测试基础类
提供所有API测试的通用功能，包括模拟环境设置、请求发送等
"""

import requests
import config.paths
import logging
import json
import time
from unittest import mock
from typing import Dict, Any, Union, Optional

from . import TEST_CONFIG, BASE_API_URL, logger


class MockResponse:
    """模拟API响应类"""

    def __init__(
        self, data: Any, status_code: int = 200, headers: Optional[Dict] = None
    ):
        self.data = data
        self.status_code = status_code
        self.headers = headers or {}
        self.text = json.dumps(data) if isinstance(
            data, (dict, list)) else str(data)

    def json(self):
        if isinstance(self.data, (dict, list)):
            return self.data
        else:
            raise ValueError("Response data is not JSON serializable")

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"Mock HTTP Error: {self.status_code}")


class APITestBase:
    """API测试基类"""

    def __init__(self):
        self.base_url = BASE_API_URL
        self.timeout = TEST_CONFIG["timeout"]
        self.max_retries = TEST_CONFIG["max_retries"]
        self.logger = logger
        self.mock_enabled = False
        self.mock_responses = {}

    def enable_mock(self):
        """启用模拟模式"""
        self.mock_enabled = True
        self.logger.info("启用API模拟模式")

    def disable_mock(self):
        """禁用模拟模式"""
        self.mock_enabled = False
        self.logger.info("禁用API模拟模式")

    def register_mock_response(
        self, endpoint: str, method: str, response_data: Any, status_code: int = 200
    ):
        """注册模拟响应"""
        key = f"{method.upper()}:{endpoint}"
        self.mock_responses[key] = MockResponse(response_data, status_code)
        self.logger.debug(f"注册模拟响应: {key}")

    def _get_mock_response(self, endpoint: str, method: str) -> Optional[MockResponse]:
        """获取模拟响应"""
        key = f"{method.upper()}:{endpoint}"
        return self.mock_responses.get(key)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> requests.Response:
        """发送API请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if headers:
            default_headers.update(headers)

        # 检查是否使用模拟模式
        if self.mock_enabled:
            mock_response = self._get_mock_response(endpoint, method)
            if mock_response:
                self.logger.info(f"返回模拟响应: {method} {endpoint}")
                return mock_response
            else:
                self.logger.warning(f"未找到模拟响应: {method} {endpoint}")

        # 实际发送请求
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"发送请求: {method} {url}")
                response = requests.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=default_headers,
                    timeout=self.timeout,
                )

                # 记录响应
                log_msg = f"响应状态码: {response.status_code}"
                if response.status_code < 400:
                    self.logger.info(log_msg)
                else:
                    self.logger.error(log_msg)
                    self.logger.error(f"错误响应: {response.text}")

                return response

            except requests.RequestException as e:
                self.logger.error(
                    f"请求异常 (尝试 {attempt+1}/{self.max_retries}): {str(e)}"
                )
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(0.5)  # 重试前等待

    # 便捷请求方法
    def get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> requests.Response:
        """GET请求"""
        return self._make_request("GET", endpoint, params=params, headers=headers)

    def post(
        self, endpoint: str, data: Optional[Dict] = None, headers: Optional[Dict] = None
    ) -> requests.Response:
        """POST请求"""
        return self._make_request("POST", endpoint, json_data=data, headers=headers)

    def put(
        self, endpoint: str, data: Optional[Dict] = None, headers: Optional[Dict] = None
    ) -> requests.Response:
        """PUT请求"""
        return self._make_request("PUT", endpoint, json_data=data, headers=headers)

    def delete(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> requests.Response:
        """DELETE请求"""
        return self._make_request("DELETE", endpoint, params=params, headers=headers)

    # 测试辅助方法
    def validate_response_schema(
        self, response: requests.Response, expected_schema: Dict
    ) -> bool:
        """验证响应是否符合期望的模式"""
        try:
            response_data = response.json()
            # 这里可以实现模式验证逻辑，例如使用jsonschema库
            # 此处仅做简单示例
            for key, type_info in expected_schema.items():
                if key not in response_data:
                    self.logger.error(f"响应缺少必须字段: {key}")
                    return False

                if not isinstance(response_data[key], type_info):
                    self.logger.error(
                        f"字段类型不匹配: {key}, 期望 {type_info}, 实际 {type(response_data[key])}"
                    )
                    return False

            return True
        except Exception as e:
            self.logger.error(f"验证响应模式失败: {str(e)}")
            return False

    def measure_performance(self, func, *args, **kwargs) -> float:
        """测量函数执行性能"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time
        self.logger.info(f"性能测量: {func.__name__} 耗时 {elapsed:.4f} 秒")
        return elapsed