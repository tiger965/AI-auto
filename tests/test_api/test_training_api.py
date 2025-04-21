""" "
训练API接口测试模块
测试模型训练、微调和评估相关的API接口
"""

import config.paths
import json
import os
import uuid
import time
from typing import Dict, Any, List

from .api_test_base import APITestBase
from . import TEST_CONFIG, logger


class TestTrainingAPI(APITestBase):
    """训练API测试类"""

    def __init__(self):
        super().__init__()
        self.auth_token = None
        self.test_user = {"username": "test_user", "password": "test_password"}
        # 测试数据
        self.test_model_id = "model-test-12345"
        self.test_dataset_id = "dataset-test-67890"
        self.test_job_id = f"job-{uuid.uuid4()}"

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

        # 模拟模型列表
        self.register_mock_response(
            "training/models",
            "GET",
            {
                "total": 2,
                "models": [
                    {
                        "id": self.test_model_id,
                        "name": "测试模型",
                        "base_model": "gpt-3.5-turbo",
                        "description": "用于测试的模型",
                        "status": "ready",
                        "created_at": "2025-04-18T10:00:00Z",
                    },
                    {
                        "id": "model-general",
                        "name": "通用模型",
                        "base_model": "gpt-4",
                        "description": "通用对话模型",
                        "status": "training",
                        "created_at": "2025-04-19T08:00:00Z",
                    },
                ],
            },
            200,
        )

        # 模拟数据集列表
        self.register_mock_response(
            "training/datasets",
            "GET",
            {
                "total": 2,
                "datasets": [
                    {
                        "id": self.test_dataset_id,
                        "name": "测试数据集",
                        "description": "用于测试的数据集",
                        "samples": 1000,
                        "created_at": "2025-04-18T09:00:00Z",
                    },
                    {
                        "id": "dataset-general",
                        "name": "通用数据集",
                        "description": "通用对话数据",
                        "samples": 5000,
                        "created_at": "2025-04-15T08:00:00Z",
                    },
                ],
            },
            200,
        )

        # 模拟模型详情
        self.register_mock_response(
            f"training/models/{self.test_model_id}",
            "GET",
            {
                "id": self.test_model_id,
                "name": "测试模型",
                "base_model": "gpt-3.5-turbo",
                "description": "用于测试的模型",
                "status": "ready",
                "metrics": {"accuracy": 0.85, "f1_score": 0.82, "loss": 0.15},
                "parameters": {"learning_rate": 1e-5, "epochs": 3, "batch_size": 16},
                "created_at": "2025-04-18T10:00:00Z",
                "updated_at": "2025-04-19T08:30:00Z",
            },
            200,
        )

        # 模拟数据集详情
        self.register_mock_response(
            f"training/datasets/{self.test_dataset_id}",
            "GET",
            {
                "id": self.test_dataset_id,
                "name": "测试数据集",
                "description": "用于测试的数据集",
                "samples": 1000,
                "format": "jsonl",
                "fields": ["prompt", "completion"],
                "statistics": {
                    "avg_prompt_length": 50.2,
                    "avg_completion_length": 120.5,
                    "categories": {"general": 500, "technical": 300, "creative": 200},
                },
                "created_at": "2025-04-18T09:00:00Z",
            },
            200,
        )

        # 模拟创建训练任务
        self.register_mock_response(
            "training/jobs",
            "POST",
            {
                "id": self.test_job_id,
                "model_id": self.test_model_id,
                "dataset_id": self.test_dataset_id,
                "status": "queued",
                "created_at": "2025-04-19T11:00:00Z",
                "parameters": {"learning_rate": 1e-5, "epochs": 3, "batch_size": 16},
            },
            200,
        )

        # 模拟训练任务列表
        self.register_mock_response(
            "training/jobs",
            "GET",
            {
                "total": 2,
                "jobs": [
                    {
                        "id": self.test_job_id,
                        "model_id": self.test_model_id,
                        "dataset_id": self.test_dataset_id,
                        "status": "running",
                        "progress": 45,
                        "created_at": "2025-04-19T11:00:00Z",
                    },
                    {
                        "id": "job-another",
                        "model_id": "model-general",
                        "dataset_id": "dataset-general",
                        "status": "completed",
                        "progress": 100,
                        "created_at": "2025-04-18T14:00:00Z",
                    },
                ],
            },
            200,
        )

        # 模拟训练任务详情
        self.register_mock_response(
            f"training/jobs/{self.test_job_id}",
            "GET",
            {
                "id": self.test_job_id,
                "model_id": self.test_model_id,
                "dataset_id": self.test_dataset_id,
                "status": "running",
                "progress": 45,
                "metrics": {"current_loss": 0.25, "current_accuracy": 0.75, "epoch": 1},
                "parameters": {"learning_rate": 1e-5, "epochs": 3, "batch_size": 16},
                "created_at": "2025-04-19T11:00:00Z",
                "updated_at": "2025-04-19T11:30:00Z",
                "logs": [
                    {"timestamp": "2025-04-19T11:00:10Z", "message": "任务已启动"},
                    {"timestamp": "2025-04-19T11:15:00Z", "message": "第1轮训练完成"},
                ],
            },
            200,
        )

        # 模拟取消训练任务
        self.register_mock_response(
            f"training/jobs/{self.test_job_id}/cancel",
            "POST",
            {"id": self.test_job_id, "status": "cancelled", "message": "任务已取消"},
            200,
        )

        # 模拟模型评估
        self.register_mock_response(
            f"training/models/{self.test_model_id}/evaluate",
            "POST",
            {
                "id": f"eval-{uuid.uuid4()}",
                "model_id": self.test_model_id,
                "dataset_id": "dataset-eval",
                "metrics": {
                    "accuracy": 0.88,
                    "f1_score": 0.85,
                    "precision": 0.87,
                    "recall": 0.84,
                    "loss": 0.12,
                },
                "created_at": "2025-04-19T12:00:00Z",
            },
            200,
        )

        # 模拟上传数据集
        self.register_mock_response(
            "training/datasets",
            "POST",
            {
                "id": f"dataset-{uuid.uuid4()}",
                "name": "新测试数据集",
                "description": "新上传的测试数据集",
                "samples": 500,
                "format": "jsonl",
                "created_at": "2025-04-19T13:00:00Z",
                "status": "processing",
            },
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

    def test_get_models(self):
        """测试获取模型列表接口"""
        headers = self._get_headers_with_token()

        response = self.get("training/models", headers=headers)

        assert response.status_code == 200

        response_data = response.json()
        assert "total" in response_data
        assert "models" in response_data
        assert isinstance(response_data["models"], list)

        if response_data["total"] > 0:
            first_model = response_data["models"][0]
            assert "id" in first_model
            assert "name" in first_model
            assert "base_model" in first_model
            assert "status" in first_model

    def test_get_datasets(self):
        """测试获取数据集列表接口"""
        headers = self._get_headers_with_token()

        response = self.get("training/datasets", headers=headers)

        assert response.status_code == 200

        response_data = response.json()
        assert "total" in response_data
        assert "datasets" in response_data
        assert isinstance(response_data["datasets"], list)

        if response_data["total"] > 0:
            first_dataset = response_data["datasets"][0]
            assert "id" in first_dataset
            assert "name" in first_dataset
            assert "samples" in first_dataset

    def test_get_model_details(self):
        """测试获取模型详情接口"""
        headers = self._get_headers_with_token()

        response = self.get(
            f"training/models/{self.test_model_id}", headers=headers)

        assert response.status_code == 200

        response_data = response.json()
        assert "id" in response_data
        assert "name" in response_data
        assert "base_model" in response_data
        assert "status" in response_data
        assert "metrics" in response_data
        assert "parameters" in response_data

    def test_get_dataset_details(self):
        """测试获取数据集详情接口"""
        headers = self._get_headers_with_token()

        response = self.get(
            f"training/datasets/{self.test_dataset_id}", headers=headers
        )

        assert response.status_code == 200

        response_data = response.json()
        assert "id" in response_data
        assert "name" in response_data
        assert "samples" in response_data
        assert "format" in response_data
        assert "statistics" in response_data

    def test_create_training_job(self):
        """测试创建训练任务接口"""
        headers = self._get_headers_with_token()
        data = {
            "model_id": self.test_model_id,
            "dataset_id": self.test_dataset_id,
            "parameters": {"learning_rate": 1e-5, "epochs": 3, "batch_size": 16},
        }

        response = self.post("training/jobs", data=data, headers=headers)

        assert response.status_code == 200

        response_data = response.json()
        assert "id" in response_data
        assert "model_id" in response_data
        assert "dataset_id" in response_data
        assert "status" in response_data
        assert "parameters" in response_data

    def test_get_jobs(self):
        """测试获取训练任务列表接口"""
        headers = self._get_headers_with_token()

        response = self.get("training/jobs", headers=headers)

        assert response.status_code == 200

        response_data = response.json()
        assert "total" in response_data
        assert "jobs" in response_data
        assert isinstance(response_data["jobs"], list)

        if response_data["total"] > 0:
            first_job = response_data["jobs"][0]
            assert "id" in first_job
            assert "model_id" in first_job
            assert "dataset_id" in first_job
            assert "status" in first_job
            assert "progress" in first_job

    def test_get_job_details(self):
        """测试获取训练任务详情接口"""
        headers = self._get_headers_with_token()

        response = self.get(
            f"training/jobs/{self.test_job_id}", headers=headers)

        assert response.status_code == 200

        response_data = response.json()
        assert "id" in response_data
        assert "model_id" in response_data
        assert "dataset_id" in response_data
        assert "status" in response_data
        assert "progress" in response_data
        assert "metrics" in response_data
        assert "parameters" in response_data
        assert "logs" in response_data

    def test_cancel_job(self):
        """测试取消训练任务接口"""
        headers = self._get_headers_with_token()

        response = self.post(
            f"training/jobs/{self.test_job_id}/cancel", data={}, headers=headers
        )

        assert response.status_code == 200

        response_data = response.json()
        assert "id" in response_data
        assert "status" in response_data
        assert response_data["status"] == "cancelled"

    def test_evaluate_model(self):
        """测试模型评估接口"""
        headers = self._get_headers_with_token()
        data = {
            "dataset_id": "dataset-eval",
            "metrics": ["accuracy", "f1_score", "precision", "recall"],
        }

        response = self.post(
            f"training/models/{self.test_model_id}/evaluate", data=data, headers=headers
        )

        assert response.status_code == 200

        response_data = response.json()
        assert "id" in response_data
        assert "model_id" in response_data
        assert "dataset_id" in response_data
        assert "metrics" in response_data
        assert "accuracy" in response_data["metrics"]
        assert "f1_score" in response_data["metrics"]

    def test_upload_dataset(self):
        """测试上传数据集接口"""
        headers = self._get_headers_with_token()
        data = {
            "name": "新测试数据集",
            "description": "新上传的测试数据集",
            "format": "jsonl",
            "data": [
                {"prompt": "问题1", "completion": "回答1"},
                {"prompt": "问题2", "completion": "回答2"},
            ],
        }

        response = self.post("training/datasets", data=data, headers=headers)

        assert response.status_code == 200

        response_data = response.json()
        assert "id" in response_data
        assert "name" in response_data
        assert "samples" in response_data
        assert "format" in response_data
        assert "status" in response_data

    def test_invalid_dataset(self):
        """测试无效数据集上传处理"""
        headers = self._get_headers_with_token()

        # 缺少必要字段
        data = {
            "name": "新测试数据集",
            "format": "jsonl",
            # 缺少数据字段
        }

        response = self.post("training/datasets", data=data, headers=headers)
        assert response.status_code == 400

        # 无效的格式
        data = {
            "name": "新测试数据集",
            "description": "新上传的测试数据集",
            "format": "invalid_format",
            "data": [{"prompt": "问题", "completion": "回答"}],
        }

        response = self.post("training/datasets", data=data, headers=headers)
        assert response.status_code == 400

    @pytest.mark.parametrize("model_status", ["training", "ready", "failed"])
    def test_model_status_handling(self, model_status: str):
        """测试不同模型状态的处理"""
        if self.mock_enabled:
            # 为不同状态注册模拟响应
            self.register_mock_response(
                f"training/models/model-{model_status}",
                "GET",
                {
                    "id": f"model-{model_status}",
                    "name": f"{model_status}状态模型",
                    "base_model": "gpt-3.5-turbo",
                    "status": model_status,
                    "created_at": "2025-04-19T10:00:00Z",
                },
                200,
            )

            headers = self._get_headers_with_token()
            response = self.get(
                f"training/models/model-{model_status}", headers=headers
            )

            assert response.status_code == 200
            assert response.json()["status"] == model_status

            # 对于不同状态，测试对应操作
            if model_status == "training":
                # 不应允许评估训练中的模型
                data = {"dataset_id": "dataset-eval"}
                response = self.post(
                    f"training/models/model-{model_status}/evaluate",
                    data=data,
                    headers=headers,
                )
                assert response.status_code in [400, 409]  # 错误请求或冲突

            elif model_status == "failed":
                # 对失败模型应返回错误详情
                assert "error" in response.json() or "error_details" in response.json()

    def test_performance_with_large_dataset(self):
        """测试大型数据集的性能"""
        headers = self._get_headers_with_token()

        # 注册大型数据集的模拟响应
        if self.mock_enabled:
            self.register_mock_response(
                "training/datasets/dataset-large",
                "GET",
                {
                    "id": "dataset-large",
                    "name": "大型数据集",
                    "samples": 10000,
                    "format": "jsonl",
                    "created_at": "2025-04-19T10:00:00Z",
                },
                200,
            )

        elapsed = self.measure_performance(
            self.get, "training/datasets/dataset-large", headers=headers
        )

        logger.info(f"大型数据集响应时间: {elapsed:.4f}秒")

        # 性能断言 - 响应时间不超过1秒
        assert elapsed < 1.0, f"大型数据集API性能不佳: 响应时间为 {elapsed:.4f}秒"