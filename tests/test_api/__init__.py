"""
API测试模块初始化文件
这个模块负责测试所有API接口的功能、错误处理和性能
"""

import pytest
import logging
import os
import sys

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_tests.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("api_tests")

# 添加测试环境变量
os.environ["TEST_MODE"] = "True"

# 测试配置
TEST_CONFIG = {
    "timeout": 5,  # API请求超时时间(秒)
    "max_retries": 3,  # 最大重试次数
    "mock_server_port": 8888,  # 模拟服务器端口
    "test_data_path": os.path.join(os.path.dirname(__file__), "test_data"),  # 测试数据路径
}

# 确保测试数据目录存在
if not os.path.exists(TEST_CONFIG["test_data_path"]):
    os.makedirs(TEST_CONFIG["test_data_path"])

# API基础URL (可以在测试前修改为测试环境URL)
BASE_API_URL = "http://localhost:8000/api/v1"

# 导出所有测试模块
__all__ = [
    "test_api_manager",
    "test_core_api",
    "test_knowledge_api",
    "test_system_api",
    "test_training_api"
]