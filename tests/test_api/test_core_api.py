""""
核心API接口测试模块
测试系统核心功能相关的API接口
""""

import config.paths
import json
import os
from typing import Dict, Any

from .api_test_base import APITestBase
from . import TEST_CONFIG, logger

class TestCoreAPI(APITestBase):
    """核心API测试类"""
    
    def __init__(self):
        super().__init__()
        self.auth_token = None
        self.test_user = {
            "username": "test_user",
            "password": "test_password"
        }
        # 测试数据
        self.test_prompt = "测试一个简单的AI提示"
        self.test_conversation_id = "test-conv-12345"
        
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
        
        # 模拟AI响应生成
        self.register_mock_response(
            "core/generate", 
            "POST", 
            {
                "id": "resp-12345",
                "text": "这是一个模拟的AI响应，基于您的提示生成。",
                "model": "gpt-test",
                "created_at": "2025-04-19T10:00:00Z",
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30
                }
            },
            200
        )
        
        # 模拟对话历史
        self.register_mock_response(
            f"core/conversations/{self.test_conversation_id}", 
            "GET", 
            {
                "id": self.test_conversation_id,
                "title": "测试对话",
                "created_at": "2025-04-19T09:00:00Z",
                "messages": [
                    {
                        "id": "msg-1",
                        "role": "user",
                        "content": "你好，AI",
                        "created_at": "2025-04-19T09:00:00Z"
                    },
                    {
                        "id": "msg-2",
                        "role": "assistant",
                        "content": "你好！我是AI助手，有什么可以帮助你的吗？",
                        "created_at": "2025-04-19T09:00:10Z"
                    }
                ]
            },
            200
        )
        
        # 模拟添加消息到对话
        self.register_mock_response(
            f"core/conversations/{self.test_conversation_id}/messages", 
            "POST", 
            {
                "id": "msg-3",
                "role": "user",
                "content": self.test_prompt,
                "created_at": "2025-04-19T10:05:00Z"
            },
            200
        )
        
        # 模拟错误响应
        self.register_mock_response(
            "core/generate", 
            "GET", 
            {"error": "Method not allowed", "code": "method_not_allowed"},
            405
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
    
    def test_generate_response(self):
        """测试生成AI响应接口"""
        headers = self._get_headers_with_token()
        data = {
            "prompt": self.test_prompt,
            "max_tokens": 100,
            "temperature": I0.7,
            "model": "gpt-test"
        }
        
        response = self.post("core/generate", data=data, headers=headers)
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert "id" in response_data
        assert "text" in response_data
        assert "model" in response_data
        assert "usage" in response_data
        assert "prompt_tokens" in response_data["usage"]
        assert "completion_tokens" in response_data["usage"]
        
    def test_generate_response_invalid_params(self):
        """测试生成AI响应接口 - 无效参数"""
        headers = self._get_headers_with_token()
        
        # 缺少必需参数
        data = {
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        response = self.post("core/generate", data=data, headers=headers)
        assert response.status_code == 400
        
        # 无效的温度值
        data = {
            "prompt": self.test_prompt,
            "max_tokens": 100,
            "temperature": 2.5  # 超出有效范围
        }
        
        response = self.post("core/generate", data=data, headers=headers)
        assert response.status_code == 400
    
    def test_get_conversation_history(self):
        """测试获取对话历史接口"""
        headers = self._get_headers_with_token()
        
        response = self.get(f"core/conversations/{self.test_conversation_id}", headers=headers)
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert "id" in response_data
        assert "title" in response_data
        assert "messages" in response_data
        assert isinstance(response_data["messages"], list)
        
        if len(response_data["messages"]) > 0:
            first_message = response_data["messages"][0]
            assert "id" in first_message
            assert "role" in first_message
            assert "content" in first_message
            assert "created_at" in first_message
    
    def test_add_message_to_conversation(self):
        """测试添加消息到对话接口"""
        headers = self._get_headers_with_token()
        data = {
            "role": "user",
            "content": self.test_prompt
        }
        
        response = self.post(f"core/conversations/{self.test_conversation_id}/messages", 
                           data=data, headers=headers)
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert "id" in response_data
        assert "role" in response_data
        assert "content" in response_data
        assert response_data["content"] == self.test_prompt
    
    def test_method_not_allowed(self):
        """测试方法不允许错误处理"""
        headers = self._get_headers_with_token()
        
        # 使用错误的HTTP方法
        response = self.get("core/generate", headers=headers)
        
        assert response.status_code == 405
        
        response_data = response.json()
        assert "error" in response_data
        assert "code" in response_data
    
    @pytest.mark.parametrize("num_requests", [1, 5, 10])
    def test_api_performance_under_load(self, num_requests: int):
        """测试API在负载下的性能"""
        headers = self._get_headers_with_token()
        data = {
            "prompt": self.test_prompt,
            "max_tokens": 50,
            "temperature": 0.7,
            "model": "gpt-test"
        }
        
        total_time = 0
        
        for _ in range(num_requests):
            elapsed = self.measure_performance(
                self.post, "core/generate", data=data, headers=headers
            )
            total_time += elapsed
        
        avg_time = total_time / num_requests
        logger.info(f"负载测试 ({num_requests} 请求) 平均响应时间: {avg_time:.4f}秒")
        
        # 性能断言 - 平均响应时间不超过2秒
        assert avg_time < 2.0, f"API性能不佳: 平均响应时间为 {avg_time:.4f}秒"