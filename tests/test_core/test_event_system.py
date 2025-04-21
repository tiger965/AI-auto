"""
事件系统测试模块

用于测试核心引擎中的事件系统组件，包括事件发布、订阅、
优先级处理、事件过滤和错误处理等功能。
"""

import unittest
import time
from unittest.mock import MagicMock, patch

# 导入事件系统组件
from core.event_system.event_manager import EventManager
from core.event_system.event import Event
from core.event_system.event_subscriber import EventSubscriber
from core.event_system.event_filter import EventFilter


class TestEventSystem(unittest.TestCase):
    """事件系统测试类"""

    def setUp(self):
        """测试前准备工作"""
        # 创建事件管理器实例
        self.event_manager = EventManager()
        # 用于记录测试中的事件处理结果
        self.test_results = []

    def tearDown(self):
        """测试后清理工作"""
        # 清空测试结果
        self.test_results = []

    def event_handler(self, event):
        """测试用事件处理器"""
        # 将事件数据记录到测试结果
        self.test_results.append(
            {
                "event_type": event.event_type,
                "data": event.data,
                "timestamp": event.timestamp,
            }
        )

    def test_event_initialization(self):
        """测试事件初始化"""
        # 创建测试事件
        event = Event("test_event", {"message": "Hello World"})

        # 验证事件属性
        self.assertEqual("test_event", event.event_type)
        self.assertEqual({"message": "Hello World"}, event.data)
        self.assertIsNotNone(event.timestamp)
        self.assertIsNone(event.priority)  # 默认优先级应为None

    def test_event_priority(self):
        """测试事件优先级"""
        # 创建带优先级的事件
        high_priority_event = Event(
            "priority_event", {"level": "high"}, priority=1)
        low_priority_event = Event(
            "priority_event", {"level": "low"}, priority=10)

        # 验证优先级设置
        self.assertEqual(1, high_priority_event.priority)
        self.assertEqual(10, low_priority_event.priority)

        # 测试优先级比较
        self.assertTrue(high_priority_event > low_priority_event)

    def test_subscriber_registration(self):
        """测试订阅者注册"""
        # 创建订阅者
        subscriber = EventSubscriber("test_subscriber")

        # 向事件管理器注册订阅者
        self.event_manager.register_subscriber(subscriber)

        # 验证订阅者已正确注册
        self.assertIn(subscriber, self.event_manager.get_subscribers())

    def test_event_subscription(self):
        """测试事件订阅"""
        # 创建订阅者
        subscriber = EventSubscriber("test_subscriber")

        # 订阅测试事件
        subscriber.subscribe("test_event", self.event_handler)

        # 验证事件订阅是否成功
        self.assertTrue(subscriber.is_subscribed("test_event"))
        self.assertFalse(subscriber.is_subscribed("non_existent_event"))

    def test_event_publishing(self):
        """测试事件发布"""
        # 创建订阅者并注册
        subscriber = EventSubscriber("test_subscriber")
        subscriber.subscribe("test_event", self.event_handler)
        self.event_manager.register_subscriber(subscriber)

        # 创建并发布事件
        event = Event("test_event", {"message": "Hello World"})
        self.event_manager.publish_event(event)

        # 处理事件队列
        self.event_manager.process_events()

        # 验证事件处理结果
        self.assertEqual(1, len(self.test_results))
        self.assertEqual("test_event", self.test_results[0]["event_type"])
        self.assertEqual({"message": "Hello World"},
                         self.test_results[0]["data"])

    def test_multiple_subscribers(self):
        """测试多个订阅者"""
        # 创建订阅者
        subscriber1 = EventSubscriber("subscriber1")
        subscriber2 = EventSubscriber("subscriber2")

        # 设置订阅
        subscriber1.subscribe("common_event", self.event_handler)
        subscriber2.subscribe("common_event", self.event_handler)

        # 注册订阅者
        self.event_manager.register_subscriber(subscriber1)
        self.event_manager.register_subscriber(subscriber2)

        # 发布事件
        event = Event("common_event", {
                      "message": "Hello Multiple Subscribers"})
        self.event_manager.publish_event(event)

        # 处理事件队列
        self.event_manager.process_events()

        # 验证两个订阅者都收到事件
        self.assertEqual(2, len(self.test_results))
        for result in self.test_results:
            self.assertEqual("common_event", result["event_type"])
            self.assertEqual(
                {"message": "Hello Multiple Subscribers"}, result["data"])

    def test_event_filtering(self):
        """测试事件过滤"""

        # 创建测试过滤器
        def filter_func(event):
            return "important" in event.data

        event_filter = EventFilter(filter_func)

        # 创建订阅者并设置过滤器
        subscriber = EventSubscriber("filtered_subscriber")
        subscriber.subscribe(
            "filtered_event", self.event_handler, event_filter=event_filter
        )

        # 注册订阅者
        self.event_manager.register_subscriber(subscriber)

        # 发布应该被过滤的事件
        filtered_event = Event(
            "filtered_event", {"message": "Regular message"})
        self.event_manager.publish_event(filtered_event)

        # 发布应该通过过滤的事件
        passing_event = Event(
            "filtered_event", {"message": "important message"})
        self.event_manager.publish_event(passing_event)

        # 处理事件队列
        self.event_manager.process_events()

        # 验证只有通过过滤的事件被处理
        self.assertEqual(1, len(self.test_results))
        self.assertEqual({"message": "important message"},
                         self.test_results[0]["data"])

    def test_event_priority_processing(self):
        """测试事件优先级处理"""
        # 创建有序列表记录处理顺序
        processing_order = []

        # 定义带序号的处理器
        def handler1(event):
            processing_order.append(1)

        def handler2(event):
            processing_order.append(2)

        def handler3(event):
            processing_order.append(3)

        # 创建订阅者
        subscriber = EventSubscriber("priority_subscriber")

        # 订阅同一事件，不同优先级
        subscriber.subscribe("priority_test", handler3, priority=3)
        subscriber.subscribe("priority_test", handler1, priority=1)
        subscriber.subscribe("priority_test", handler2, priority=2)

        # 注册订阅者
        self.event_manager.register_subscriber(subscriber)

        # 发布事件
        event = Event("priority_test", {})
        self.event_manager.publish_event(event)

        # 处理事件队列
        self.event_manager.process_events()

        # 验证处理顺序是按照优先级从高到低
        self.assertEqual([1, 2, 3], processing_order)

    def test_event_unsubscription(self):
        """测试取消事件订阅"""
        # 创建订阅者
        subscriber = EventSubscriber("test_subscriber")

        # 订阅事件
        subscriber.subscribe("test_event", self.event_handler)

        # 验证订阅成功
        self.assertTrue(subscriber.is_subscribed("test_event"))

        # 取消订阅
        subscriber.unsubscribe("test_event")

        # 验证取消订阅成功
        self.assertFalse(subscriber.is_subscribed("test_event"))

    def test_subscriber_deregistration(self):
        """测试取消订阅者注册"""
        # 创建订阅者
        subscriber = EventSubscriber("test_subscriber")

        # 注册订阅者
        self.event_manager.register_subscriber(subscriber)
        self.assertIn(subscriber, self.event_manager.get_subscribers())

        # 取消注册
        self.event_manager.deregister_subscriber(subscriber)

        # 验证取消注册成功
        self.assertNotIn(subscriber, self.event_manager.get_subscribers())

    def test_async_event_processing(self):
        """测试异步事件处理"""

        # 模拟异步处理需要的延迟
        def delayed_handler(event):
            time.sleep(0.1)  # 模拟处理延迟
            self.test_results.append(event.data)

        # 创建订阅者
        subscriber = EventSubscriber("async_subscriber")
        subscriber.subscribe("async_event", delayed_handler)

        # 注册订阅者
        self.event_manager.register_subscriber(subscriber)

        # 发布多个事件
        for i in range(5):
            event = Event("async_event", {"index": i})
            self.event_manager.publish_event(event)

        # 异步处理事件
        self.event_manager.process_events_async()

        # 等待所有事件处理完成
        self.event_manager.wait_for_completion()

        # 验证所有事件都被处理
        self.assertEqual(5, len(self.test_results))
        indices = [result["index"] for result in self.test_results]
        self.assertEqual(list(range(5)), sorted(indices))

    def test_error_handling(self):
        """测试错误处理"""

        # 定义会抛出异常的处理器
        def error_handler(event):
            raise RuntimeError("测试异常")

        # 设置错误处理回调
        error_events = []

        def on_error(event, exception):
            error_events.append((event, exception))

        # 替换事件管理器的错误处理方法
        self.event_manager.set_error_handler(on_error)

        # 创建订阅者
        subscriber = EventSubscriber("error_subscriber")
        subscriber.subscribe("error_event", error_handler)

        # 注册订阅者
        self.event_manager.register_subscriber(subscriber)

        # 发布事件
        event = Event("error_event", {"message": "This will cause an error"})
        self.event_manager.publish_event(event)

        # 处理事件
        self.event_manager.process_events()

        # 验证错误被正确捕获
        self.assertEqual(1, len(error_events))
        self.assertEqual(event, error_events[0][0])
        self.assertIsInstance(error_events[0][1], RuntimeError)
        self.assertEqual("测试异常", str(error_events[0][1]))

    def test_event_replay(self):
        """测试事件重放"""
        # 创建订阅者
        subscriber = EventSubscriber("replay_subscriber")
        subscriber.subscribe("replay_event", self.event_handler)

        # 注册订阅者
        self.event_manager.register_subscriber(subscriber)

        # 启用事件历史记录
        self.event_manager.enable_event_history()

        # 发布事件
        event1 = Event("replay_event", {"message": "First event"})
        event2 = Event("replay_event", {"message": "Second event"})

        self.event_manager.publish_event(event1)
        self.event_manager.publish_event(event2)

        # 处理事件
        self.event_manager.process_events()

        # 清空测试结果
        self.test_results = []

        # 重放事件
        self.event_manager.replay_events("replay_event")

        # 验证事件被重放
        self.assertEqual(2, len(self.test_results))
        self.assertEqual({"message": "First event"},
                         self.test_results[0]["data"])
        self.assertEqual({"message": "Second event"},
                         self.test_results[1]["data"])

    def test_wildcard_subscription(self):
        """测试通配符订阅"""
        # 创建订阅者
        subscriber = EventSubscriber("wildcard_subscriber")

        # 使用通配符订阅多种事件
        subscriber.subscribe("market.*", self.event_handler)

        # 注册订阅者
        self.event_manager.register_subscriber(subscriber)

        # 发布各种市场事件
        self.event_manager.publish_event(
            Event("market.update", {"symbol": "AAPL"}))
        self.event_manager.publish_event(
            Event("market.trade", {"symbol": "GOOGL"}))
        self.event_manager.publish_event(
            Event("market.alert", {"symbol": "MSFT"}))

        # 发布非市场事件
        self.event_manager.publish_event(
            Event("system.status", {"status": "OK"}))

        # 处理事件
        self.event_manager.process_events()

        # 验证只有市场事件被处理
        self.assertEqual(3, len(self.test_results))
        event_types = [result["event_type"] for result in self.test_results]
        self.assertIn("market.update", event_types)
        self.assertIn("market.trade", event_types)
        self.assertIn("market.alert", event_types)
        self.assertNotIn("system.status", event_types)


def run_tests():
    """运行所有事件系统测试"""
    unittest.main()


if __name__ == "__main__":
    run_tests()