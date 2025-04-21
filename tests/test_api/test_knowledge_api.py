""" "
知识库API接口测试模块
测试知识检索、更新和管理相关的API接口
"""

import config.paths
import json
import os
import uuid
from typing import Dict, Any

from .api_test_base import APITestBase
from . import TEST_CONFIG, logger


class TestKnowledgeAPI(APITestBase):
    """知识库API测试类"""

    def __init__(self):
        super().__init__()
        self.auth_token = None
        self.test_user = {"username": "test_user", "password": "test_password"}
        # 测试数据
        self.test_kb_id = "kb-test-12345"
        self.test_document_id = f"doc-{uuid.uuid4()}"
        self.test_query = "什么是人工智能"

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

        # 模拟知识库列表
        self.register_mock_response(
            "knowledge/databases",
            "GET",
            {
                "total": 2,
                "databases": [
                    {
                        "id": self.test_kb_id,
                        "name": "测试知识库",
                        "description": "用于测试的知识库",
                        "document_count": 10,
                        "created_at": "2025-04-18T10:00:00Z",
                    },
                    {
                        "id": "kb-general",
                        "name": "通用知识库",
                        "description": "系统通用知识",
                        "document_count": 50,
                        "created_at": "2025-04-15T08:00:00Z",
                    },
                ],
            },
            200,
        )

        # 模拟知识库详情
        self.register_mock_response(
            f"knowledge/databases/{self.test_kb_id}",
            "GET",
            {
                "id": self.test_kb_id,
                "name": "测试知识库",
                "description": "用于测试的知识库",
                "document_count": 10,
                "total_tokens": 15000,
                "created_at": "2025-04-18T10:00:00Z",
                "updated_at": "2025-04-19T08:30:00Z",
                "documents": [
                    {
                        "id": self.test_document_id,
                        "title": "测试文档",
                        "format": "text",
                        "tokens": 1500,
                        "created_at": "2025-04-18T10:30:00Z",
                    }
                ],
            },
            200,
        )

        # .模拟知识查询
        self.register_mock_response(
            f"knowledge/databases/{self.test_kb_id}/query",
            "POST",
            {
                "query": self.test_query,
                "results": [
                    {
                        "document_id": self.test_document_id,
                        "content": "人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，它关注开发能够执行通常需要人类智能的任务的系统。",
                        "relevance_score": 0.92,
                        "metadata": {"source": "测试文档", "page": 1},
                    },
                    {
                        "document_id": "doc-other",
                        "content": "人工智能包括机器学习、深度学习、计算机视觉和自然语言处理等子领域。",
                        "relevance_score": 0.85,
                        "metadata": {"source": "AI简介", "page": 2},
                    },
                ],
            },
            200,
        )

        # 模拟文档上传
        self.register_mock_response(
            f"knowledge/databases/{self.test_kb_id}/documents",
            "POST",
            {
                "id": f"doc-{uuid.uuid4()}",
                "title": "新测试文档",
                "format": "text",
                "tokens": 1200,
                "created_at": "2025-04-19T11:00:00Z",
                "status": "processed",
            },
            200,
        )

        # 模拟文档删除
        self.register_mock_response(
            f"knowledge/databases/{self.test_kb_id}/documents/{self.test_document_id}",
            "DELETE",
            {"success": True, "message": "文档已删除"},
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

    def test_get_knowledge_databases(self):
        """测试获取知识库列表接口"""
        headers = self._get_headers_with_token()

        response = self.get("knowledge/databases", headers=headers)

        assert response.status_code == 200

        response_data = response.json()
        assert "total" in response_data
        assert "databases" in response_data
        assert isinstance(response_data["databases"], list)

        if response_data["total"] > 0:
            first_db = response_data["databases"][0]
            assert "id" in first_db
            assert "name" in first_db
            assert "document_count" in first_db

    def test_get_knowledge_database_details(self):
        """测试获取知识库详情接口"""
        headers = self._get_headers_with_token()

        response = self.get(
            f"knowledge/databases/{self.test_kb_id}", headers=headers)

        assert response.status_code == 200

        response_data = response.json()
        assert "id" in response_data
        assert "name" in response_data
        assert "document_count" in response_data
        assert "total_tokens" in response_data
        assert "documents" in response_data
        assert isinstance(response_data["documents"], list)

    def test_query_knowledge(self):
        """测试知识查询接口"""
        headers = self._get_headers_with_token()
        data = {"query": self.test_query, "max_results": 5, "threshold": 0.7}

        response = self.post(
            f"knowledge/databases/{self.test_kb_id}/query", data=data, headers=headers
        )

        assert response.status_code == 200

        response_data = response.json()
        assert "query" in response_data
        assert "results" in response_data
        assert isinstance(response_data["results"], list)

        if len(response_data["results"]) > 0:
            first_result = response_data["results"][0]
            assert "document_id" in first_result
            assert "content" in first_result
            assert "relevance_score" in first_result

    def test_upload_document(self):
        """测试文档上传接口"""
        headers = self._get_headers_with_token()
        data = {
            "title": "新测试文档",
            "content": "这是一个测试文档内容，包含人工智能相关信息。人工智能是计算机科学的一个分支。",
            "format": "text",
        }

        response = self.post(
            f"knowledge/databases/{self.test_kb_id}/documents",
            data=data,
            headers=headers,
        )

        assert response.status_code == 200

        response_data = response.json()
        assert "id" in response_data
        assert "title" in response_data
        assert "format" in response_data
        assert "tokens" in response_data
        assert "status" in response_data

    def test_delete_document(self):
        """测试文档删除接口"""
        headers = self._get_headers_with_token()

        response = self.delete(
            f"knowledge/databases/{self.test_kb_id}/documents/{self.test_document_id}",
            headers=headers,
        )

        assert response.status_code == 200

        response_data = response.json()
        assert "success" in response_data
        assert response_data["success"] is True

    def test_query_nonexistent_kb(self):
        """测试查询不存在的知识库"""
        headers = self._get_headers_with_token()
        data = {"query": self.test_query}

        response = self.post(
            "knowledge/databases/nonexistent-kb/query", data=data, headers=headers
        )

        assert response.status_code == 404

    @pytest.mark.parametrize("query_length", [5, 50, 200])
    def test_query_performance(self, query_length: int):
        """测试不同查询长度的性能"""
        headers = self._get_headers_with_token()

        # 生成指定长度的查询
        long_query = "人工智能 " * query_length
        data = {"query": long_query[:query_length], "max_results": 5}

        elapsed = self.measure_performance(
            self.post,
            f"knowledge/databases/{self.test_kb_id}/query",
            data=data,
            headers=headers,
        )

        logger.info(f"查询长度 {query_length} 的响应时间: {elapsed:.4f}秒")

        # 性能断言 - 响应时间随查询长度增加而线性增加，但不超过阈值
        max_expected_time = 0.5 + (query_length / 100)  # 简单的线性模型
        assert elapsed < max_expected_time, f"查询性能不佳: 响应时间为 {elapsed:.4f}秒"