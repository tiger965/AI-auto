"""
上下文管理测试模块

用于测试核心引擎中的上下文管理组件，包括上下文创建、数据存储、
上下文继承、数据隔离和生命周期管理等功能。
"""

import unittest
import time
import threading
import json
import pickle
import os
from unittest.mock import MagicMock, patch

# 导入上下文管理组件
from core.context.context_manager import ContextManager
from core.context.context import Context
from core.context.context_serializer import ContextSerializer
from core.context.context_factory import ContextFactory


class TestContext(unittest.TestCase):
    """上下文管理测试类"""

    def setUp(self):
        """测试前准备工作"""
        # 创建上下文管理器实例
        self.context_manager = ContextManager()

        # 测试数据目录
        self.test_data_dir = "./test_data/context"
        os.makedirs(self.test_data_dir, exist_ok=True)

    def tearDown(self):
        """测试后清理工作"""
        # 清理所有上下文
        self.context_manager.clear_all_contexts()

        # 清理测试文件
        for file in os.listdir(self.test_data_dir):
            file_path = os.path.join(self.test_data_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

    def test_context_creation(self):
        """测试上下文创建"""
        # 创建上下文
        context = self.context_manager.create_context("test_context")

        # 验证上下文属性
        self.assertEqual("test_context", context.name)
        self.assertIsNotNone(context.id)
        self.assertIsNotNone(context.created_at)

        # 验证上下文已在管理器中注册
        self.assertIn("test_context", self.context_manager.get_context_names())
        self.assertEqual(
            context, self.context_manager.get_context("test_context"))

    def test_context_data_storage(self):
        """测试上下文数据存储与访问"""
        # 创建上下文
        context = self.context_manager.create_context("data_context")

        # 存储不同类型的数据
        context.set("string_value", "测试字符串")
        context.set("int_value", 100)
        context.set("float_value", 3.14)
        context.set("bool_value", True)
        context.set("list_value", [1, 2, 3])
        context.set("dict_value", {"key": "value"})
        context.set("none_value", None)

        # 验证数据存储与访问
        self.assertEqual("测试字符串", context.get("string_value"))
        self.assertEqual(100, context.get("int_value"))
        self.assertEqual(3.14, context.get("float_value"))
        self.assertTrue(context.get("bool_value"))
        self.assertEqual([1, 2, 3], context.get("list_value"))
        self.assertEqual({"key": "value"}, context.get("dict_value"))
        self.assertIsNone(context.get("none_value"))

        # 验证获取不存在的键
        self.assertIsNone(context.get("non_existent_key"))
        self.assertEqual("默认值", context.get("non_existent_key", "默认值"))

        # 验证键存在检查
        self.assertTrue(context.has("string_value"))
        self.assertFalse(context.has("non_existent_key"))

    def test_context_data_update(self):
        """测试上下文数据更新"""
        # 创建上下文
        context = self.context_manager.create_context("update_context")

        # 存储初始数据
        context.set("key", "initial_value")
        self.assertEqual("initial_value", context.get("key"))

        # 更新数据
        context.set("key", "updated_value")
        self.assertEqual("updated_value", context.get("key"))

        # 更新复杂数据类型
        context.set("list_key", [1, 2])
        self.assertEqual([1, 2], context.get("list_key"))

        context.set("list_key", [3, 4, 5])
        self.assertEqual([3, 4, 5], context.get("list_key"))

        # 测试字典更新
        context.set("dict_key", {"a": 1})
        context.update("dict_key", {"b": 2})
        self.assertEqual({"a": 1, "b": 2}, context.get("dict_key"))

        # 测试列表追加
        context.append("list_key", 6)
        self.assertEqual([3, 4, 5, 6], context.get("list_key"))

    def test_context_data_removal(self):
        """测试上下文数据移除"""
        # 创建上下文
        context = self.context_manager.create_context("removal_context")

        # 存储数据
        context.set("key1", "value1")
        context.set("key2", "value2")

        # 验证数据存在
        self.assertTrue(context.has("key1"))
        self.assertTrue(context.has("key2"))

        # 移除单个键
        context.remove("key1")
        self.assertFalse(context.has("key1"))
        self.assertTrue(context.has("key2"))

        # 移除不存在的键（不应抛出异常）
        context.remove("non_existent_key")

        # 清除所有数据
        context.clear()
        self.assertFalse(context.has("key2"))

    def test_context_inheritance(self):
        """测试上下文继承"""
        # 创建父上下文
        parent_context = self.context_manager.create_context("parent_context")
        parent_context.set("parent_key", "parent_value")
        parent_context.set("common_key", "parent_common_value")

        # 创建子上下文
        child_context = self.context_manager.create_context(
            "child_context", parent=parent_context
        )
        child_context.set("child_key", "child_value")
        child_context.set("common_key", "child_common_value")

        # 验证子上下文从父上下文继承数据
        self.assertEqual("parent_value", child_context.get("parent_key"))
        self.assertEqual("child_value", child_context.get("child_key"))

        # 验证子上下文覆盖父上下文的同名数据
        self.assertEqual("child_common_value", child_context.get("common_key"))

        # 验证修改父上下文不影响子上下文的覆盖值
        parent_context.set("common_key", "updated_parent_common_value")
        self.assertEqual("child_common_value", child_context.get("common_key"))

        # 验证修改父上下文的新值在子上下文可见
        parent_context.set("new_parent_key", "new_parent_value")
        self.assertEqual("new_parent_value",
                         child_context.get("new_parent_key"))

    def test_multi_level_inheritance(self):
        """测试多级继承"""
        # 创建三级上下文继承链
        grand_parent = self.context_manager.create_context("grand_parent")
        parent = self.context_manager.create_context(
            "parent", parent=grand_parent)
        child = self.context_manager.create_context("child", parent=parent)

        # 设置不同级别的数据
        grand_parent.set("level1", "grand_parent_value")
        grand_parent.set("common", "grand_parent_common")

        parent.set("level2", "parent_value")
        parent.set("common", "parent_common")

        child.set("level3", "child_value")
        child.set("common", "child_common")

        # 验证继承链中的数据访问
        self.assertEqual("grand_parent_value", child.get("level1"))
        self.assertEqual("parent_value", child.get("level2"))
        self.assertEqual("child_value", child.get("level3"))

        # 验证覆盖规则（最近的优先）
        self.assertEqual("child_common", child.get("common"))
        self.assertEqual("parent_common", parent.get("common"))

        # 修改最顶层并验证
        grand_parent.set("new_top_level", "top_value")
        self.assertEqual("top_value", child.get("new_top_level"))

    def test_context_snapshot(self):
        """测试上下文快照功能"""
        # 创建上下文
        context = self.context_manager.create_context("snapshot_context")

        # 添加初始数据
        context.set("key1", "value1")
        context.set("key2", "value2")

        # 创建快照
        snapshot1 = context.create_snapshot()

        # 修改数据
        context.set("key1", "updated_value1")
        context.set("key3", "value3")

        # 创建第二个快照
        snapshot2 = context.create_snapshot()

        # 恢复到第一个快照
        context.restore_snapshot(snapshot1)

        # 验证恢复后的状态
        self.assertEqual("value1", context.get("key1"))
        self.assertEqual("value2", context.get("key2"))
        self.assertFalse(context.has("key3"))

        # 恢复到第二个快照
        context.restore_snapshot(snapshot2)

        # 验证恢复后的状态
        self.assertEqual("updated_value1", context.get("key1"))
        self.assertEqual("value2", context.get("key2"))
        self.assertEqual("value3", context.get("key3"))

    def test_context_serialization(self):
        """测试上下文序列化"""
        # 创建上下文序列化器
        serializer = ContextSerializer()

        # 创建具有各种数据类型的上下文
        context = self.context_manager.create_context("serialization_context")
        context.set("string", "字符串值")
        context.set("number", 123.45)
        context.set("boolean", True)
        context.set("list", [1, 2, 3, "四", "五"])
        context.set("dict", {"name": "测试", "value": 100})
        context.set("nested", {"items": [{"id": 1}, {"id": 2}]})

        # 序列化上下文
        serialized = serializer.serialize(context)

        # 反序列化上下文
        deserialized = serializer.deserialize(serialized)

        # 验证反序列化结果
        self.assertEqual(context.name, deserialized.name)
        self.assertEqual(context.id, deserialized.id)
        self.assertEqual("字符串值", deserialized.get("string"))
        self.assertEqual(123.45, deserialized.get("number"))
        self.assertEqual(True, deserialized.get("boolean"))
        self.assertEqual([1, 2, 3, "四", "五"], deserialized.get("list"))
        self.assertEqual({"name": "测试", "value": 100},
                         deserialized.get("dict"))
        self.assertEqual(
            {"items": [{"id": 1}, {"id": 2}]}, deserialized.get("nested"))

    def test_context_persistence(self):
        """测试上下文持久化"""
        # 创建上下文
        context = self.context_manager.create_context("persistence_context")
        context.set("key1", "value1")
        context.set("key2", [1, 2, 3])

        # 持久化上下文
        file_path = os.path.join(self.test_data_dir, "test_context.json")
        self.context_manager.save_context(context, file_path)

        # 清除当前上下文
        self.context_manager.clear_all_contexts()

        # 加载上下文
        loaded_context = self.context_manager.load_context(file_path)

        # 验证加载的上下文
        self.assertEqual("persistence_context", loaded_context.name)
        self.assertEqual("value1", loaded_context.get("key1"))
        self.assertEqual([1, 2, 3], loaded_context.get("key2"))

    def test_context_factory(self):
        """测试上下文工厂"""
        # 创建上下文工厂
        factory = ContextFactory()

        # 使用工厂创建不同类型的上下文
        trading_context = factory.create_trading_context("trading_test")
        analysis_context = factory.create_analysis_context("analysis_test")
        user_context = factory.create_user_context("user_test")

        # 验证上下文类型和初始数据
        self.assertEqual("trading", trading_context.get("type"))
        self.assertEqual("analysis", analysis_context.get("type"))
        self.assertEqual("user", user_context.get("type"))

        # 验证特定类型上下文的默认数据
        self.assertIsNotNone(trading_context.get("account"))
        self.assertIsNotNone(analysis_context.get("models"))
        self.assertIsNotNone(user_context.get("preferences"))

    def test_context_expiration(self):
        """测试上下文过期功能"""
        # 创建临时上下文（寿命1秒）
        temp_context = self.context_manager.create_context(
            "temp_context", ttl=1)
        temp_context.set("key", "value")

        # 验证可以立即访问
        self.assertEqual("value", temp_context.get("key"))

        # 等待过期
        time.sleep(1.5)

        # 验证上下文已过期
        self.assertFalse(self.context_manager.has_context("temp_context"))

        # 创建另一个长寿命上下文
        long_context = self.context_manager.create_context(
            "long_context", ttl=60)

        # 验证未过期
        self.assertTrue(self.context_manager.has_context("long_context"))

    def test_context_events(self):
        """测试上下文事件"""
        # 事件记录器
        events = []

        # 设置事件监听器
        def on_context_changed(context_name, key, value):
            events.append(
                {"type": "changed", "context": context_name,
                    "key": key, "value": value}
            )

        def on_context_created(context):
            events.append({"type": "created", "context": context.name})

        def on_context_destroyed(context_name):
            events.append({"type": "destroyed", "context": context_name})

        # 注册事件监听器
        self.context_manager.on_context_changed = on_context_changed
        self.context_manager.on_context_created = on_context_created
        self.context_manager.on_context_destroyed = on_context_destroyed

        # 创建上下文
        context = self.context_manager.create_context("event_context")

        # 设置值
        context.set("key1", "value1")

        # 销毁上下文
        self.context_manager.destroy_context("event_context")

        # 验证事件触发
        self.assertEqual(3, len(events))
        self.assertEqual("created", events[0]["type"])
        self.assertEqual("event_context", events[0]["context"])

        self.assertEqual("changed", events[1]["type"])
        self.assertEqual("event_context", events[1]["context"])
        self.assertEqual("key1", events[1]["key"])
        self.assertEqual("value1", events[1]["value"])

        self.assertEqual("destroyed", events[2]["type"])
        self.assertEqual("event_context", events[2]["context"])

    def test_concurrent_context_access(self):
        """测试并发上下文访问"""
        # 创建共享上下文
        shared_context = self.context_manager.create_context("shared_context")
        shared_context.set("counter", 0)

        # 线程安全的累加器
        def increment_counter(repeat_count):
            for _ in range(repeat_count):
                current = shared_context.get("counter")
                # 模拟一些处理时间，增加并发冲突的可能性
                time.sleep(0.001)
                shared_context.set("counter", current + 1)

        # 创建多个线程
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=increment_counter, args=(10,))
            threads.append(thread)

        # 启动所有线程
        for thread in threads:
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证最终计数器值（应为5*10=50）
        self.assertEqual(50, shared_context.get("counter"))

    def test_context_search(self):
        """测试上下文搜索功能"""
        # 创建多个上下文
        self.context_manager.create_context("user_context_1").set("type", "user").set(
            "name", "Alice"
        )
        self.context_manager.create_context("user_context_2").set("type", "user").set(
            "name", "Bob"
        )
        self.context_manager.create_context("trading_context_1").set(
            "type", "trading"
        ).set("symbol", "AAPL")
        self.context_manager.create_context("trading_context_2").set(
            "type", "trading"
        ).set("symbol", "GOOGL")

        # 按类型搜索
        user_contexts = self.context_manager.search_contexts(
            lambda ctx: ctx.get("type") == "user"
        )
        trading_contexts = self.context_manager.search_contexts(
            lambda ctx: ctx.get("type") == "trading"
        )

        # 验证搜索结果
        self.assertEqual(2, len(user_contexts))
        self.assertEqual(2, len(trading_contexts))

        # 按名称搜索
        alice_contexts = self.context_manager.search_contexts(
            lambda ctx: ctx.get("name") == "Alice"
        )

        # 验证搜索结果
        self.assertEqual(1, len(alice_contexts))
        self.assertEqual("user_context_1", alice_contexts[0].name)

        # 复杂搜索条件
        apple_trading_contexts = self.context_manager.search_contexts(
            lambda ctx: ctx.get("type") == "trading" and ctx.get(
                "symbol") == "AAPL"
        )

        # 验证搜索结果
        self.assertEqual(1, len(apple_trading_contexts))
        self.assertEqual("trading_context_1", apple_trading_contexts[0].name)

    def test_context_transaction(self):
        """测试上下文事务功能"""
        # 创建上下文
        context = self.context_manager.create_context("transaction_context")
        context.set("initial_key", "initial_value")

        # 开始事务
        context.begin_transaction()

        # 在事务中修改数据
        context.set("key1", "value1")
        context.set("key2", "value2")
        context.set("initial_key", "updated_value")

        # 验证事务中可以看到修改
        self.assertEqual("value1", context.get("key1"))
        self.assertEqual("value2", context.get("key2"))
        self.assertEqual("updated_value", context.get("initial_key"))

        # 回滚事务
        context.rollback_transaction()

        # 验证修改已回滚
        self.assertFalse(context.has("key1"))
        self.assertFalse(context.has("key2"))
        self.assertEqual("initial_value", context.get("initial_key"))

        # 再次开始事务
        context.begin_transaction()

        # 在事务中修改数据
        context.set("key3", "value3")

        # 提交事务
        context.commit_transaction()

        # 验证修改已永久生效
        self.assertEqual("value3", context.get("key3"))

    def test_context_validation(self):
        """测试上下文数据验证"""
        # 创建带验证规则的上下文
        validation_rules = {
            "age": lambda x: isinstance(x, int) and x >= 0,
            "email": lambda x: isinstance(x, str) and "@" in x,
        }

        context = self.context_manager.create_context("validation_context")
        context.set_validation_rules(validation_rules)

        # 测试有效数据
        context.set("age", 25)
        context.set("email", "test@example.com")

        # 验证设置成功
        self.assertEqual(25, context.get("age"))
        self.assertEqual("test@example.com", context.get("email"))

        # 测试无效数据
        with self.assertRaises(ValueError):
            context.set("age", -5)

        with self.assertRaises(ValueError):
            context.set("email", "invalid_email")

        # 验证无效设置没有影响现有数据
        self.assertEqual(25, context.get("age"))

    def test_context_batch_operations(self):
        """测试上下文批量操作"""
        # 创建上下文
        context = self.context_manager.create_context("batch_context")

        # 批量设置数据
        batch_data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3",
            "key4": "value4",
        }

        context.set_batch(batch_data)

        # 验证批量设置成功
        for key, value in batch_data.items():
            self.assertEqual(value, context.get(key))

        # 批量获取数据
        keys = ["key1", "key3", "non_existent"]
        values = context.get_batch(keys)

        # 验证批量获取结果
        self.assertEqual("value1", values["key1"])
        self.assertEqual("value3", values["key3"])
        self.assertIsNone(values["non_existent"])

        # 批量删除数据
        context.remove_batch(["key1", "key2"])

        # 验证批量删除成功
        self.assertFalse(context.has("key1"))
        self.assertFalse(context.has("key2"))
        self.assertTrue(context.has("key3"))

    def test_context_namespaces(self):
        """测试上下文命名空间"""
        # 创建上下文
        context = self.context_manager.create_context("namespace_context")

        # 在不同命名空间中设置数据
        context.set("key", "default_value")
        context.set("key", "user_value", namespace="user")
        context.set("key", "system_value", namespace="system")

        # 验证不同命名空间的数据隔离
        self.assertEqual("default_value", context.get("key"))
        self.assertEqual("user_value", context.get("key", namespace="user"))
        self.assertEqual("system_value", context.get(
            "key", namespace="system"))

        # 获取命名空间列表
        namespaces = context.get_namespaces()
        self.assertIn("default", namespaces)
        self.assertIn("user", namespaces)
        self.assertIn("system", namespaces)

        # 清除特定命名空间
        context.clear_namespace("user")

        # 验证特定命名空间已清除
        self.assertEqual("default_value", context.get("key"))
        self.assertIsNone(context.get("key", namespace="user"))
        self.assertEqual("system_value", context.get(
            "key", namespace="system"))

    def test_context_export_import(self):
        """测试上下文导出和导入"""
        # 创建上下文并添加数据
        original_context = self.context_manager.create_context(
            "export_context")
        original_context.set("string_key", "string_value")
        original_context.set("number_key", 12345)
        original_context.set("complex_key", {"nested": [1, 2, 3]})

        # 导出上下文数据
        exported_data = original_context.export_data()

        # 创建新上下文并导入数据
        new_context = self.context_manager.create_context("import_context")
        new_context.import_data(exported_data)

        # 验证数据已成功导入
        self.assertEqual("string_value", new_context.get("string_key"))
        self.assertEqual(12345, new_context.get("number_key"))
        self.assertEqual({"nested": [1, 2, 3]}, new_context.get("complex_key"))

    def test_context_metadata(self):
        """测试上下文元数据"""
        # 创建上下文
        context = self.context_manager.create_context("metadata_context")

        # 设置元数据
        context.set_metadata("creator", "test_user")
        context.set_metadata("priority", "high")
        context.set_metadata("tags", ["test", "context", "metadata"])

        # 获取元数据
        self.assertEqual("test_user", context.get_metadata("creator"))
        self.assertEqual("high", context.get_metadata("priority"))
        self.assertEqual(["test", "context", "metadata"],
                         context.get_metadata("tags"))

        # 获取所有元数据
        all_metadata = context.get_all_metadata()
        self.assertEqual("test_user", all_metadata["creator"])
        self.assertEqual("high", all_metadata["priority"])

        # 更新元数据
        context.set_metadata("priority", "medium")
        self.assertEqual("medium", context.get_metadata("priority"))

        # 删除元数据
        context.remove_metadata("tags")
        self.assertIsNone(context.get_metadata("tags"))

    def test_context_size_limits(self):
        """测试上下文大小限制"""
        # 创建带大小限制的上下文
        size_limited_context = self.context_manager.create_context(
            "size_limited_context", max_size=1000
        )

        # 添加数据直到接近限制
        large_data = "x" * 900
        size_limited_context.set("large_key", large_data)

        # 验证可以添加小数据
        size_limited_context.set("small_key", "small_value")

        # 尝试添加过大的数据
        too_large_data = "y" * 200  # 加上现有数据会超过1000字节
        with self.assertRaises(ValueError):
            size_limited_context.set("too_large_key", too_large_data)

        # 验证现有数据未受影响
        self.assertEqual(large_data, size_limited_context.get("large_key"))
        self.assertEqual("small_value", size_limited_context.get("small_key"))

    def test_context_history(self):
        """测试上下文历史记录"""
        # 创建带历史记录的上下文
        history_context = self.context_manager.create_context(
            "history_context", track_history=True
        )

        # 修改数据并创建历史记录
        history_context.set("key", "value1")
        history_context.set("key", "value2")
        history_context.set("key", "value3")

        # 获取历史记录
        history = history_context.get_history("key")

        # 验证历史记录
        self.assertEqual(3, len(history))
        self.assertEqual("value1", history[0]["value"])
        self.assertEqual("value2", history[1]["value"])
        self.assertEqual("value3", history[2]["value"])

        # 回滚到特定版本
        history_context.revert_to_version("key", 1)  # 回滚到第二个值

        # 验证回滚结果
        self.assertEqual("value2", history_context.get("key"))

        # 检查历史记录已更新
        updated_history = history_context.get_history("key")
        self.assertEqual(4, len(updated_history))
        self.assertEqual("value2", updated_history[3]["value"])


def run_tests():
    """运行所有上下文管理测试"""
    unittest.main()


if __name__ == "__main__":
    run_tests()