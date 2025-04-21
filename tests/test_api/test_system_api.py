""" "
系统API接口测试模块
测试系统配置、监控和管理相关的API接口
"""

import config.paths
import json
import os
import time
from typing import Dict, Any, List

from .api_test_base import APITestBase
from . import TEST_CONFIG, logger


class TestSystemAPI(APITestBase):
    """系统API测试类"""

    def __init__(self):
        super().__init__()
        self.auth_token = None
        self.test_user = {"username": "test_user", "password": "test_password"}

    def setup_method(self):
        """每个测试方法前执行的设置"""
        # 如果为离线测试模式，注册模拟响应
        if os.environ.get("OFFLINE_TEST", "False") == "True":
            self.enable_mock()
            self._register_mock_responses()
        else:
            # 获取测试认证令牌
            self._get_auth_token()

    def teardown_method(self):
        """每个测试方法后执行的清理"""
        if self.mock_enabled:
            self.disable_mock()

    def _register_mock_responses(self):
        """注册模拟API响应"""
        # 模拟登录响应
        self.register_mock_response(
            "auth/login",
            "POST",
            {"token": "mock_token_12345", "user_id": 1, "role": "admin"},
            200,
        )

        # 模拟系统状态
        self.register_mock_response(
            "system/status",
            "GET",
            {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": 3600,
                "environment": "test",
                "services": [
                    {"name": "api", "status": "healthy", "version": "1.0.0"},
                    {"name": "database", "status": "healthy", "version": "5.7"},
                    {"name": "ai_engine", "status": "healthy", "version": "2.1"},
                ],
            },
            200,
        )

        # 模拟系统配置
        self.register_mock_response(
            "system/config",
            "GET",
            {
                "api_rate_limit": 100,
                "max_tokens_per_request": 2000,
                "default_model": "gpt-3.5-turbo",
                "log_level": "info",
                "maintenance_mode": False,
            },
            200,
        )

        # 模拟更新系统配置
        self.register_mock_response(
            "system/config",
            "PUT",
            {
                "api_rate_limit": 120,
                "max_tokens_per_request": 2000,
                "default_model": "gpt-3.5-turbo",
                "log_level": "info",
                "maintenance_mode": False,
            },
            200,
        )

        # 模拟系统资源使用
        self.register_mock_response(
            "system/resources",
            "GET",
            {
                "cpu_usage": 25.5,
                "memory_usage": 45.2,
                "disk_usage": 30.1,
                "network": {"rx_bytes": 1024000, "tx_bytes": 512000},
            },
            200,
        )

        # 模拟系统日志
        self.register_mock_response(
            "system/logs",
            "GET",
            {
                "total": 100,
                "page": 1,
                "page_size": 10,
                "logs": [
                    {
                        "timestamp": "2025-04-19T10:00:00Z",
                        "level": "info",
                        "component": "api",
                        "message": "API 服务启动",
                    },
                    {
                        "timestamp": "2025-04-19T10:01:00Z",
                        "level": "info",
                        "component": "database",
                        "message": "数据库连接成功",
                    },
                ],
            },
            200,
        )

        # 模拟启用维护模式
        self.register_mock_response(
            "system/maintenance",
            "POST",
            {"maintenance_mode": True, "message": "系统已进入维护模式"},
            200,
        )

        # 模拟禁用维护模式
        self.register_mock_response(
            "system/maintenance",
            "DELETE",
            {"maintenance_mode": False, "message": "系统已退出维护模式"},
            200,
        )

    def _get_auth_token(self):
        """获取认证令牌"""
        if not self.mock_enabled:
            response = self.post("auth/login", data=self.test_user)
            if response.status_code == 200:
                response_data = response.json()
                self.auth_token = response_data.get("token")
                logger.info("成功获取认证令牌")
            else:
                logger.error(f"获取认证令牌失败: {response.status_code}")

    def _get_headers_with_token(self) -> Dict[str, str]:
        """获取带认证令牌的请求头"""
        headers = {"Content-Type": "application/json",
                   "Accept": "application/json"}

        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        return headers

    def test_get_system_status(self):
        """测试获取系统状态接口"""
        headers = self._get_headers_with_token()

        response = self.get("system/status", headers=headers)

        assert response.status_code == 200

        response_data = response.json()
        assert "status" in response_data
        assert "version" in response_data
        assert "uptime" in response_data
        assert "services" in response_data
        assert isinstance(response_data["services"], list)

        # 验证服务状态格式
        if len(response_data["services"]) > 0:
            first_service = response_data["services"][0]
            assert "name" in first_service
            assert "status" in first_service
            assert "version" in first_service

    def test_get_system_config(self):
        """测试获取系统配置接口"""
        headers = self._get_headers_with_token()

        response = self.get("system/config", headers=headers)

        assert response.status_code == 200

        response_data = response.json()
        assert "api_rate_limit" in response_data
        assert "max_tokens_per_request" in response_data
        assert "default_model" in response_data
        assert "log_level" in response_data
        assert "maintenance_mode" in response_data

    def test_update_system_config(self):
        """测试更新系统配置接口"""
        headers = self._get_headers_with_token()
        data = {"api_rate_limit": 120}  # 修改API速率限制

        response = self.put("system/config", data=data, headers=headers)

        assert response.status_code == 200

        response_data = response.json()
        assert "api_rate_limit" in response_data
        assert response_data["api_rate_limit"] == 120

    def test_get_system_resources(self):
        """测试获取系统资源使用接口"""
        headers = self._get_headers_with_token()

        response = self.get("system/resources", headers=headers)

        assert response.status_code == 200

        response_data = response.json()
        assert "cpu_usage" in response_data
        assert "memory_usage" in response_data
        assert "disk_usage" in response_data
        assert "network" in response_data
        assert "rx_bytes" in response_data["network"]
        assert "tx_bytes" in response_data["network"]

    def test_get_system_logs(self):
        """测试获取系统日志接口"""
        headers = self._get_headers_with_token()
        params = {"page": 1, "page_size": 10, "level": "info"}

        response = self.get("system/logs", params=params, headers=headers)

        assert response.status_code == 200

        response_data = response.json()
        assert "total" in response_data
        assert "page" in response_data
        assert "page_size" in response_data
        assert "logs" in response_data
        assert isinstance(response_data["logs"], list)

        if len(response_data["logs"]) > 0:
            first_log = response_data["logs"][0]
            assert "timestamp" in first_log
            assert "level" in first_log
            assert "component" in first_log
            assert "message" in first_log

    def test_maintenance_mode(self):
        """测试维护模式接口"""
        headers = self._get_headers_with_token()

        # 启用维护模式
        response = self.post("system/maintenance", data={}, headers=headers)

        assert response.status_code == 200

        response_data = response.json()
        assert "maintenance_mode" in response_data
        assert response_data["maintenance_mode"] is True

        # 禁用维护模式
        response = self.delete("system/maintenance", headers=headers)

        assert response.status_code == 200

        response_data = response.json()
        assert "maintenance_mode" in response_data
        assert response_data["maintenance_mode"] is False

    def test_unauthorized_access(self):
        """测试未授权访问"""
        # 不带认证令牌
        headers = {"Content-Type": "application/json",
                   "Accept": "application/json"}

        response = self.get("system/config", headers=headers)
        assert response.status_code in [401, 403]  # 未授权或禁止访问

    def test_service_health_monitoring(self):
        """测试服务健康监控"""
        headers = self._get_headers_with_token()

        # 执行多次状态检查，确保稳定性
        results = []
        for _ in range(3):
            response = self.get("system/status", headers=headers)
            assert response.status_code == 200

            response_data = response.json()
            results.append(response_data["status"])

            if not self.mock_enabled:
                time.sleep(1)  # 真实环境中稍作等待

        # 所有检查应返回相同的状态
        assert all(status == "healthy" for status in results), "服务健康状态不稳定"

    @pytest.mark.parametrize(
        "invalid_config",
        [
            {"api_rate_limit": -1},  # 无效的速率限制
            {"log_level": "invalid_level"},  # 无效的日志级别
            {"unknown_field": "value"},  # 未知字段
        ],
    )
    def test_invalid_config_update(self, invalid_config: Dict):
        """测试无效的配置更新处理"""
        headers = self._get_headers_with_token()

        response = self.put(
            "system/config", data=invalid_config, headers=headers)

        # 应返回错误响应
        assert response.status_code in [400, 422]