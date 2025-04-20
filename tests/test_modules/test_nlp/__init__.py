"""
NLP模块测试包
负责测试自然语言处理功能的各个组件，包括分词、嵌入和情感分析。
"""

import unittest
import os
import sys

# 添加项目根目录到sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 用于存储测试数据的目录
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

# 如果测试数据目录不存在，则创建
if not os.path.exists(TEST_DATA_DIR):
    os.makedirs(TEST_DATA_DIR)# NLP测试初始化文件
