"""
API管理器接口测试模块
测试API管理、认证和权限相关接口
"""

import pytest
import json
import os
from typing import Dict, Any

from .api_test_base import APITestBase
from . import TEST_CONFIG, logger

class TestAPIManager(APITestBase):
    """API管理器测试类"""
    
    def __init__(self):
        super().__init__()
        self.auth_token = None
        self.test_user = {
            "username": "test_user",
            "password": "test_password"
        }
        
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
            200
        )
        
        # 模拟API列表响应
        self.register_mock_response(
            "system/apis", 
            "GET", 
            {
                "total": 3,
                "apis": [
                    {"id": 1, "name": "core_api", "status": "active", "version": "1.0"},
                    {"id": 2, "name": "knowledge_api", "status": "active", "version": "1.0"},
                    {"id": 3, "name": "training_api", "status": "active", "version": "1.0"}
                ]
            },
            200
        )
        
        # 模拟API状态响应
        self.register_mock_response(
            "system/status", 
            "GET", 
            {"status": "healthy", "uptime": 3600, "version": "1.0.0"},
            200
        )
        
        # 模拟权限检查响应
        self.register_mock_response(
            "auth/check_permission", 
            "POST", 
            {"has_permission": True, "resource": "api:core", "action": "read"},
            200
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
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
        return headers
    
    @pytest.mark.parametrize("username,password,expected_status", [
        ("test_user", "test_password", 200),
        ("wrong_user", "test_password", 401),
        ("test_user", "wrong_password", 401),
        ("", "", 400),
    ])
    def test_login(self, username: str, password: str, expected_status: int):
        """测试登录接口"""
        data = {"username": username, "password": password}
        response = self.post("auth/login", data=data)
        
        assert response.status_code == expected_status
        
        if expected_status == 200:
            response_data = response.json()
            assert "token" in response_data
            assert "user_id" in response_data
    
    def test_get_api_list(self):
        """测试获取API列表接口"""
        headers = self._get_headers_with_token()
        response = self.get("system/apis", headers=headers)
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert "total" in response_data
        assert "apis" in response_data
        assert isinstance(response_data["apis"], list)
        
        # 验证API列表内容
        if response_data["total"] > 0:
            first_api = response_data["apis"][0]
            assert "id" in first_api
            assert "name" in first_api
            assert "status" in first_api
    
    def test_api_status(self):
        """测试API状态接口"""
        headers = self._get_headers_with_token()
        response = self.get("system/status", headers=headers)
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert "status" in response_data
        assert "uptime" in response_data
        assert "version" in response_data
    
    def test_check_permissions(self):
        """测试权限检查接口"""
        headers = self._get_headers_with_token()
        data = {
            "resource": "api:core",
            "action": "read"
        }
        
        response = self.post("auth/check_permission", data=data, headers=headers)
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert "has_permission" in response_data
        assert isinstance(response_data["has_permission"], bool)
    
    def test_invalid_token(self):
        """测试无效的认证令牌"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer invalid_token"
        }
        
        response = self.get("system/apis", headers=headers)
        assert response.status_code in [401, 403]  # 未授权或禁止访问
    
    @pytest.mark.parametrize("endpoint", [
        "system/apis",
        "system/status",
        "auth/check_permission"
    ])
    def test_api_performance(self, endpoint: str):
        """测试API性能"""
        headers = self._get_headers_with_token()
        
        # 测量API响应时间
        data = None
        method = self.get
        
        if endpoint == "auth/check_permission":
            method = self.post
            data = {"resource": "api:core", "action": "read"}
        
        # 使用性能测量工具执行请求
        if data:
            elapsed = self.measure_performance(method, endpoint, data=data, headers=headers)
        else:
            elapsed = self.measure_performance(method, endpoint, headers=headers)
        
        # 性能断言 - 响应时间不超过1秒
        assert elapsed < 1.0, f"API性能不佳: {endpoint} 响应时间为 {elapsed:.4f}秒"