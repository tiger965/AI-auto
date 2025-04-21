"""
核心引擎测试模块

用于测试核心引擎的整体功能，包括各组件之间的集成和交互。
核心引擎整合了事件系统、工作流、模型和上下文管理等组件。
"""

import unittest
import time
import os
import threading
from unittest.mock import MagicMock, patch

# 导入核心引擎组件
from core.engine import Engine
from core.event_system.event_manager import EventManager
from core.event_system.event import Event
from core.event_system.event_subscriber import EventSubscriber
from core.workflow.workflow_manager import WorkflowManager
from core.workflow.workflow import Workflow
from core.workflow.task import Task
from core.workflow.task_result import TaskResult
from core.models.model_manager import ModelManager
from core.models.model import Model
from core.context.context_manager import ContextManager
from core.context.context import Context


class TestEngine(unittest.TestCase):
    """核心引擎测试类"""

    def setUp(self):
        """测试前准备工作"""
        # 创建核心引擎实例
        self.engine = Engine()

        # 测试数据目录
        self.test_data_dir = "./test_data/engine"
        os.makedirs(self.test_data_dir, exist_ok=True)

        # 初始化核心引擎
        self.engine.initialize()

        # 访问引擎组件
        self.event_manager = self.engine.get_component(EventManager)
        self.workflow_manager = self.engine.get_component(WorkflowManager)
        self.model_manager = self.engine.get_component(ModelManager)
        self.context_manager = self.engine.get_component(ContextManager)

        # 执行顺序跟踪
        self.execution_order = []

        # 创建测试模型
        self.test_model = Model("test_model")
        self.test_model.initialize({"param": "value"})
        self.test_model.set_predict_function(
            lambda inputs: {"result": inputs["input"] * 2}
        )

    def tearDown(self):
        """测试后清理工作"""
        # 关闭引擎
        self.engine.shutdown()

        # 清空执行顺序
        self.execution_order = []

    def test_engine_initialization(self):
        """测试引擎初始化"""
        # 验证引擎已正确初始化
        self.assertTrue(self.engine.is_initialized)

        # 验证所有组件已创建
        self.assertIsNotNone(self.event_manager)
        self.assertIsNotNone(self.workflow_manager)
        self.assertIsNotNone(self.model_manager)
        self.assertIsNotNone(self.context_manager)

    def test_component_registration(self):
        """测试组件注册"""

        # 创建自定义组件
        class CustomComponent:
            def __init__(self):
                self.initialized = False

            def initialize(self):
                self.initialized = True

            def shutdown(self):
                self.initialized = False

        # 注册自定义组件
        custom_component = CustomComponent()
        self.engine.register_component("custom", custom_component)

        # 验证组件已注册
        retrieved_component = self.engine.get_component("custom")
        self.assertIs(custom_component, retrieved_component)

        # 验证组件已初始化
        self.assertTrue(custom_component.initialized)

        # 关闭引擎后，组件应该被关闭
        self.engine.shutdown()
        self.assertFalse(custom_component.initialized)

    def test_event_workflow_integration(self):
        """测试事件系统与工作流集成"""

        # 创建由事件触发的工作流
        def event_task(context):
            event_data = context.get("event_data")
            self.execution_order.append("task_executed")
            return TaskResult.success(
                {"processed_data": event_data["value"] + "_processed"}
            )

        # 创建工作流
        workflow = Workflow("event_workflow")
        workflow.add_task(Task("event_task", event_task))

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 创建事件处理器
        def on_test_event(event):
            self.execution_order.append("event_received")

            # 创建上下文
            context = self.context_manager.create_context("event_context")
            context.set("event_data", event.data)

            # 执行工作流
            result = self.workflow_manager.execute_workflow(
                "event_workflow", context)

            # 存储结果
            self.execution_order.append(
                result.task_results["event_task"].data["processed_data"]
            )

        # 创建订阅者
        subscriber = EventSubscriber("test_subscriber")
        subscriber.subscribe("test_event", on_test_event)

        # 注册订阅者
        self.event_manager.register_subscriber(subscriber)

        # 发布事件
        event = Event("test_event", {"value": "test_value"})
        self.event_manager.publish_event(event)

        # 处理事件
        self.event_manager.process_events()

        # 验证执行顺序和结果
        self.assertEqual(
            ["event_received", "task_executed", "test_value_processed"],
            self.execution_order,
        )

    def test_model_workflow_integration(self):
        """测试模型与工作流集成"""
        # 注册测试模型
        self.model_manager.register_model(self.test_model)

        # 创建使用模型的任务
        def model_task(context):
            # 获取模型
            model = self.model_manager.get_model("test_model")

            # 使用模型进行预测
            input_value = context.get("input_value")
            prediction = model.predict({"input": input_value})

            # 存储结果
            self.execution_order.append(prediction["result"])

            return TaskResult.success(prediction)

        # 创建工作流
        workflow = Workflow("model_workflow")
        workflow.add_task(Task("model_task", model_task))

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 创建上下文
        context = self.context_manager.create_context("model_context")
        context.set("input_value", 5)

        # 执行工作流
        result = self.workflow_manager.execute_workflow(
            "model_workflow", context)

        # 验证结果
        self.assertTrue(result.is_success)
        self.assertEqual(
            10, result.task_results["model_task"].data["result"])  # 5*2=10
        self.assertEqual([10], self.execution_order)

    def test_context_sharing(self):
        """测试上下文共享"""
        # 创建全局上下文
        global_context = self.context_manager.create_context("global_context")
        global_context.set("global_value", "shared_data")

        # 创建事件处理器
        def on_context_event(event):
            # 获取全局上下文
            context = self.context_manager.get_context("global_context")

            # 更新上下文
            context.set("updated_by", "event_handler")

            self.execution_order.append("event_handled")

        # 创建订阅者
        subscriber = EventSubscriber("context_subscriber")
        subscriber.subscribe("context_event", on_context_event)

        # 注册订阅者
        self.event_manager.register_subscriber(subscriber)

        # 创建使用上下文的任务
        def context_task(context):
            # 获取全局上下文
            global_ctx = self.context_manager.get_context("global_context")

            # 读取全局值
            global_value = global_ctx.get("global_value")
            updated_by = global_ctx.get("updated_by")

            # 更新本地上下文
            context.set("task_result", f"{global_value}_from_{updated_by}")

            self.execution_order.append("task_executed")

            return TaskResult.success({"context_value": context.get("task_result")})

        # 创建工作流
        workflow = Workflow("context_workflow")
        workflow.add_task(Task("context_task", context_task))

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 发布事件
        event = Event("context_event", {})
        self.event_manager.publish_event(event)

        # 处理事件
        self.event_manager.process_events()

        # 执行工作流
        result = self.workflow_manager.execute_workflow("context_workflow")

        # 验证执行顺序
        self.assertEqual(["event_handled", "task_executed"],
                         self.execution_order)

        # 验证结果
        self.assertEqual(
            "shared_data_from_event_handler",
            result.task_results["context_task"].data["context_value"],
        )

    def test_complex_pipeline(self):
        """测试复杂管道集成"""
        # 注册测试模型
        self.model_manager.register_model(self.test_model)

        # 步骤1：创建数据准备任务
        def prepare_data(context):
            context.set("prepared_data", {"input": 5})
            self.execution_order.append("data_prepared")
            return TaskResult.success({"status": "data_prepared"})

        # 步骤2：创建模型预测任务
        def model_prediction(context):
            # 获取模型
            model = self.model_manager.get_model("test_model")

            # 使用模型进行预测
            prediction = model.predict(context.get("prepared_data"))

            # 存储结果
            context.set("prediction_result", prediction)

            self.execution_order.append("prediction_made")

            # 发布预测完成事件
            event = Event("prediction_completed", {"result": prediction})
            self.event_manager.publish_event(event)

            return TaskResult.success({"status": "prediction_completed"})

        # 步骤3：创建结果处理任务
        def process_result(context):
            prediction = context.get("prediction_result")
            processed_value = prediction["result"] * 3  # 进一步处理结果
            context.set("final_result", processed_value)

            self.execution_order.append("result_processed")

            return TaskResult.success(
                {"status": "result_processed", "value": processed_value}
            )

        # 创建由事件触发的后续工作流
        def event_task(context):
            event_data = context.get("event_data")
            result_value = event_data["result"]["result"]

            # 创建全局结果上下文
            result_context = self.context_manager.create_context(
                "result_context")
            result_context.set("event_result", result_value)

            self.execution_order.append("event_task_executed")

            return TaskResult.success({"status": "event_processed"})

        # 创建主工作流
        main_workflow = Workflow("main_pipeline")
        main_workflow.add_task(Task("prepare_data", prepare_data))
        main_workflow.add_task(Task("model_prediction", model_prediction))
        main_workflow.add_task(Task("process_result", process_result))

        # 创建事件工作流
        event_workflow = Workflow("event_pipeline")
        event_workflow.add_task(Task("event_task", event_task))

        # 注册工作流
        self.workflow_manager.register_workflow(main_workflow)
        self.workflow_manager.register_workflow(event_workflow)

        # 创建事件处理器
        def on_prediction_completed(event):
            # 创建事件上下文
            context = self.context_manager.create_context("event_context")
            context.set("event_data", event.data)

            # 执行事件工作流
            self.workflow_manager.execute_workflow("event_pipeline", context)

        # 创建订阅者
        subscriber = EventSubscriber("pipeline_subscriber")
        subscriber.subscribe("prediction_completed", on_prediction_completed)

        # 注册订阅者
        self.event_manager.register_subscriber(subscriber)

        # 执行主工作流
        result = self.workflow_manager.execute_workflow("main_pipeline")

        # 处理可能的事件
        self.event_manager.process_events()

        # 验证执行顺序
        expected_order = [
            "data_prepared",
            "prediction_made",
            "event_task_executed",
            "result_processed",
        ]
        self.assertEqual(expected_order, self.execution_order)

        # 验证主工作流结果
        self.assertTrue(result.is_success)
        self.assertEqual(
            30, result.task_results["process_result"].data["value"]
        )  # (5*2)*3=30

        # 验证事件处理结果
        result_context = self.context_manager.get_context("result_context")
        self.assertEqual(10, result_context.get("event_result"))  # 5*2=10

    def test_error_propagation(self):
        """测试错误传播"""

        # 创建会失败的任务
        def failing_task(context):
            raise ValueError("测试错误")

        # 创建工作流
        workflow = Workflow("error_workflow")
        workflow.add_task(Task("failing_task", failing_task))

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 创建错误事件订阅者
        def on_error_event(event):
            error_info = event.data
            self.execution_order.append(
                f"error_event:{error_info['error_type']}")

        # 创建订阅者
        subscriber = EventSubscriber("error_subscriber")
        subscriber.subscribe("workflow.error", on_error_event)

        # 注册订阅者
        self.event_manager.register_subscriber(subscriber)

        # 执行工作流（预期失败）
        result = self.workflow_manager.execute_workflow("error_workflow")

        # 处理可能触发的错误事件
        self.event_manager.process_events()

        # 验证结果
        self.assertFalse(result.is_success)
        self.assertEqual("failing_task", result.failed_task_name)
        self.assertIsInstance(result.exception, ValueError)

        # 验证错误事件已发布
        self.assertEqual(["error_event:ValueError"], self.execution_order)

    def test_engine_configuration(self):
        """测试引擎配置"""
        # 创建配置
        config = {
            "engine": {"name": "test_engine", "version": "1.0.0"},
            "event_system": {"max_queue_size": 100, "thread_pool_size": 2},
            "workflow": {"max_concurrent_workflows": 5},
            "model": {"default_cache_size": 10, "memory_limit_mb": 1000},
        }

        # 创建并配置引擎
        configured_engine = Engine()
        configured_engine.configure(config)
        configured_engine.initialize()

        # 验证配置已应用
        self.assertEqual("test_engine", configured_engine.name)
        self.assertEqual("1.0.0", configured_engine.version)

        # 获取组件
        event_manager = configured_engine.get_component(EventManager)
        workflow_manager = configured_engine.get_component(WorkflowManager)
        model_manager = configured_engine.get_component(ModelManager)

        # 验证组件配置
        self.assertEqual(100, event_manager.max_queue_size)
        self.assertEqual(2, event_manager.thread_pool_size)
        self.assertEqual(5, workflow_manager.max_concurrent_workflows)
        self.assertEqual(10, model_manager.default_cache_size)
        self.assertEqual(1000, model_manager.memory_limit_mb)

        # 关闭引擎
        configured_engine.shutdown()

    def test_async_execution(self):
        """测试异步执行"""

        # 创建异步任务
        def async_task(context):
            time.sleep(0.1)  # 模拟耗时操作
            context.set("async_result", "completed")
            self.execution_order.append("async_task_completed")
            return TaskResult.success({"status": "completed"})

        # 创建事件处理器
        def on_completion_event(event):
            self.execution_order.append("completion_event_received")

        # 创建订阅者
        subscriber = EventSubscriber("completion_subscriber")
        subscriber.subscribe("workflow.completed", on_completion_event)

        # 注册订阅者
        self.event_manager.register_subscriber(subscriber)

        # 创建工作流
        workflow = Workflow("async_workflow")
        workflow.add_task(Task("async_task", async_task, is_async=True))

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 异步执行工作流
        future = self.workflow_manager.execute_workflow_async("async_workflow")

        # 验证工作流立即返回，但尚未完成
        self.assertFalse(future.done())
        self.assertEqual([], self.execution_order)

        # 等待工作流完成
        result = future.result(timeout=1.0)

        # 处理事件
        self.event_manager.process_events()

        # 验证工作流已完成
        self.assertTrue(result.is_success)
        self.assertEqual(
            "completed", result.task_results["async_task"].data["status"])

        # 验证执行顺序
        self.assertEqual(
            ["async_task_completed", "completion_event_received"], self.execution_order
        )

    def test_parallel_component_execution(self):
        """测试并行组件执行"""

        # 创建需要同时使用多个组件的任务
        def multi_component_task(context):
            # 获取模型管理器
            model_mgr = self.engine.get_component(ModelManager)

            # 获取或创建模型
            if not model_mgr.has_model("parallel_model"):
                model = Model("parallel_model")
                model.initialize({"factor": 3})
                model.set_predict_function(
                    lambda x: {"result": x["value"] *
                               model.get_parameter("factor")}
                )
                model_mgr.register_model(model)

            # 使用模型
            prediction = model_mgr.get_model(
                "parallel_model").predict({"value": 5})
            context.set("model_result", prediction["result"])

            # 发布事件
            event_mgr = self.engine.get_component(EventManager)
            event = Event("parallel_event", {"prediction": prediction})
            event_mgr.publish_event(event)

            return TaskResult.success({"status": "multi_component_completed"})

        # 创建事件处理函数
        def on_parallel_event(event):
            prediction = event.data["prediction"]
            self.execution_order.append(
                f"event_received:{prediction['result']}")

        # 创建订阅者
        subscriber = EventSubscriber("parallel_subscriber")
        subscriber.subscribe("parallel_event", on_parallel_event)

        # 注册订阅者
        self.event_manager.register_subscriber(subscriber)

        # 创建工作流
        workflow = Workflow("parallel_workflow")
        workflow.add_task(Task("multi_component", multi_component_task))

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 创建多个线程同时执行工作流
        def execute_workflow():
            result = self.workflow_manager.execute_workflow(
                "parallel_workflow")
            self.assertTrue(result.is_success)

        # 创建并启动线程
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=execute_workflow)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 处理事件
        self.event_manager.process_events()

        # 验证事件结果
        self.assertEqual(5, len(self.execution_order))
        for item in self.execution_order:
            self.assertEqual("event_received:15", item)  # 5*3=15

    def test_engine_plugin_system(self):
        """测试引擎插件系统"""

        # 创建插件类
        class TestPlugin:
            def __init__(self):
                self.initialized = False
                self.engine = None
                self.event_count = 0

            def initialize(self, engine):
                self.engine = engine
                self.initialized = True

                # 注册事件处理器
                event_manager = engine.get_component(EventManager)
                subscriber = EventSubscriber("plugin_subscriber")
                subscriber.subscribe("test_plugin_event", self.handle_event)
                event_manager.register_subscriber(subscriber)

            def handle_event(self, event):
                self.event_count += 1

            def get_status(self):
                return {
                    "initialized": self.initialized,
                    "event_count": self.event_count,
                }

        # 创建引擎
        plugin_engine = Engine()

        # 创建并注册插件
        test_plugin = TestPlugin()
        plugin_engine.register_plugin("test_plugin", test_plugin)

        # 初始化引擎
        plugin_engine.initialize()

        # 验证插件已初始化
        self.assertTrue(test_plugin.initialized)
        self.assertIs(plugin_engine, test_plugin.engine)

        # 发布插件事件
        event_manager = plugin_engine.get_component(EventManager)
        event = Event("test_plugin_event", {"data": "test"})
        event_manager.publish_event(event)
        event_manager.process_events()

        # 验证插件处理了事件
        self.assertEqual(1, test_plugin.event_count)

        # 再次发布事件
        event_manager.publish_event(event)
        event_manager.process_events()

        # 验证插件继续处理事件
        self.assertEqual(2, test_plugin.event_count)

        # 关闭引擎
        plugin_engine.shutdown()

    def test_engine_services(self):
        """测试引擎服务"""

        # 创建服务类
        class LogService:
            def __init__(self):
                self.logs = []

            def log(self, message, level="INFO"):
                self.logs.append({"level": level, "message": message})

            def get_logs(self):
                return self.logs

        class NotificationService:
            def __init__(self):
                self.notifications = []

            def notify(self, message, recipient):
                self.notifications.append(
                    {"recipient": recipient, "message": message})

            def get_notifications(self):
                return self.notifications

        # 创建引擎
        service_engine = Engine()

        # 创建和注册服务
        log_service = LogService()
        notification_service = NotificationService()

        service_engine.register_service("logging", log_service)
        service_engine.register_service("notification", notification_service)

        # 初始化引擎
        service_engine.initialize()

        # 创建使用服务的任务
        def service_task(context):
            # 获取服务
            log_service = context.get_service("logging")
            notification_service = context.get_service("notification")

            # 使用服务
            log_service.log("Task started")
            log_service.log("Processing data", "DEBUG")

            notification_service.notify("Task completed", "admin")

            return TaskResult.success()

        # 创建工作流
        workflow = Workflow("service_workflow")
        workflow.add_task(Task("service_task", service_task))

        # 注册工作流
        workflow_manager = service_engine.get_component(WorkflowManager)
        workflow_manager.register_workflow(workflow)

        # 创建服务上下文
        context_manager = service_engine.get_component(ContextManager)
        context = context_manager.create_context("service_context")

        # 注册服务到上下文
        context.register_service("logging", log_service)
        context.register_service("notification", notification_service)

        # 执行工作流
        result = workflow_manager.execute_workflow("service_workflow", context)

        # 验证工作流执行成功
        self.assertTrue(result.is_success)

        # 验证服务记录
        self.assertEqual(2, len(log_service.get_logs()))
        self.assertEqual("Task started", log_service.get_logs()[0]["message"])
        self.assertEqual("DEBUG", log_service.get_logs()[1]["level"])

        self.assertEqual(1, len(notification_service.get_notifications()))
        self.assertEqual(
            "admin", notification_service.get_notifications()[0]["recipient"]
        )

        # 关闭引擎
        service_engine.shutdown()

    def test_engine_performance_monitoring(self):
        """测试引擎性能监控"""
        # 开启性能监控
        self.engine.enable_performance_monitoring()

        # 创建任务
        def monitored_task(context):
            time.sleep(0.1)  # 模拟工作
            return TaskResult.success()

        # 创建工作流
        workflow = Workflow("monitored_workflow")
        workflow.add_task(Task("monitored_task", monitored_task))

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 执行工作流
        self.workflow_manager.execute_workflow("monitored_workflow")

        # 获取性能统计
        stats = self.engine.get_performance_stats()

        # 验证有性能数据
        self.assertIn("workflow_execution", stats)
        self.assertIn("monitored_workflow", stats["workflow_execution"])
        self.assertGreaterEqual(
            stats["workflow_execution"]["monitored_workflow"]["average_execution_time"],
            0.1,
        )

        # 验证任务级别的性能数据
        self.assertIn("task_execution", stats)
        self.assertIn("monitored_task", stats["task_execution"])
        self.assertGreaterEqual(
            stats["task_execution"]["monitored_task"]["average_execution_time"], 0.1
        )

        # 验证组件级别的性能数据
        self.assertIn("component_operations", stats)
        self.assertIn("workflow_manager", stats["component_operations"])
        self.assertIn(
            "execute_workflow", stats["component_operations"]["workflow_manager"]
        )

    def test_engine_recovery(self):
        """测试引擎故障恢复"""

        # 创建需要持久化数据的任务
        def persistent_task(context):
            # 设置一些状态
            context.set("important_data", "valuable_information")

            # 持久化上下文
            context_path = os.path.join(
                self.test_data_dir, "persistent_context.json")
            self.context_manager.save_context(context, context_path)

            # 存储持久化路径
            context.set("context_path", context_path)

            return TaskResult.success({"path": context_path})

        # 创建工作流
        workflow = Workflow("recovery_workflow")
        workflow.add_task(Task("persistent_task", persistent_task))

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 执行工作流
        result = self.workflow_manager.execute_workflow("recovery_workflow")

        # 验证执行成功
        self.assertTrue(result.is_success)

        # 获取持久化路径
        context_path = result.task_results["persistent_task"].data["path"]

        # 模拟引擎崩溃和重启
        self.engine.shutdown()
        self.engine = Engine()
        self.engine.initialize()

        # 重新获取组件
        self.context_manager = self.engine.get_component(ContextManager)

        # 恢复上下文
        recovered_context = self.context_manager.load_context(context_path)

        # 验证数据已恢复
        self.assertEqual(
            "valuable_information", recovered_context.get("important_data")
        )

    def test_workflow_triggered_by_model_events(self):
        """测试由模型事件触发的工作流"""
        # 创建一个会发布事件的模型
        event_model = Model("event_model")
        event_model.initialize({"threshold": 0.5})

        # 设置模型预测函数，会发布高置信度事件
        def predict_with_event(inputs):
            value = inputs["value"]
            confidence = inputs.get("confidence", 0.8)

            result = {
                "prediction": value > event_model.get_parameter("threshold"),
                "confidence": confidence,
            }

            # 发布高置信度事件
            if confidence > 0.7:
                # 这里我们使用引擎中的事件管理器
                event_manager = self.engine.get_component(EventManager)
                event = Event(
                    "high_confidence_prediction",
                    {
                        "model": "event_model",
                        "prediction": result["prediction"],
                        "confidence": confidence,
                    },
                )
                event_manager.publish_event(event)

            return result

        event_model.set_predict_function(predict_with_event)

        # 注册模型
        self.model_manager.register_model(event_model)

        # 创建由预测事件触发的工作流
        def handle_high_confidence(context):
            event_data = context.get("event_data")
            model_name = event_data["model"]
            prediction = event_data["prediction"]
            confidence = event_data["confidence"]

            self.execution_order.append(
                f"high_confidence_handled:{model_name}:{prediction}:{confidence}"
            )

            return TaskResult.success({"status": "handled"})

        # 创建工作流
        event_workflow = Workflow("prediction_event_workflow")
        event_workflow.add_task(
            Task("handle_high_confidence", handle_high_confidence))

        # 注册工作流
        self.workflow_manager.register_workflow(event_workflow)

        # 创建事件处理器
        def on_prediction_event(event):
            context = self.context_manager.create_context(
                "prediction_event_context")
            context.set("event_data", event.data)
            self.workflow_manager.execute_workflow(
                "prediction_event_workflow", context)

        # 创建和注册订阅者
        subscriber = EventSubscriber("prediction_subscriber")
        subscriber.subscribe("high_confidence_prediction", on_prediction_event)
        self.event_manager.register_subscriber(subscriber)

        # 使用模型预测
        prediction1 = event_model.predict(
            {"value": 0.6, "confidence": 0.9}
        )  # 应该触发事件

        # 处理事件
        self.event_manager.process_events()

        # 验证事件触发的工作流执行
        self.assertEqual(
            ["high_confidence_handled:event_model:True:0.9"], self.execution_order
        )

        # 重置执行顺序
        self.execution_order = []

        # 低置信度预测不应触发事件
        prediction2 = event_model.predict({"value": 0.3, "confidence": 0.6})

        # 处理事件
        self.event_manager.process_events()

        # 验证没有触发事件
        self.assertEqual([], self.execution_order)

    def test_engine_state_management(self):
        """测试引擎状态管理"""
        # 初始化引擎状态
        self.engine.set_state("system_mode", "normal")
        self.engine.set_state("processing_enabled", True)

        # 创建依赖引擎状态的任务
        def state_dependent_task(context):
            # 获取引擎状态
            system_mode = self.engine.get_state("system_mode")
            processing_enabled = self.engine.get_state("processing_enabled")

            if system_mode == "maintenance" or not processing_enabled:
                # 在维护模式或处理禁用时拒绝任务
                self.execution_order.append("task_skipped")
                return TaskResult.skipped("系统不可用")

            # 正常处理
            self.execution_order.append("task_executed")
            return TaskResult.success({"system_mode": system_mode})

        # 创建工作流
        workflow = Workflow("state_workflow")
        workflow.add_task(Task("state_task", state_dependent_task))

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 执行工作流（正常模式）
        result1 = self.workflow_manager.execute_workflow("state_workflow")

        # 验证正常执行
        self.assertTrue(result1.is_success)
        self.assertEqual(["task_executed"], self.execution_order)
        self.assertEqual(
            "normal", result1.task_results["state_task"].data["system_mode"]
        )

        # 重置执行顺序
        self.execution_order = []

        # 切换到维护模式
        self.engine.set_state("system_mode", "maintenance")

        # 再次执行工作流
        result2 = self.workflow_manager.execute_workflow("state_workflow")

        # 验证任务被跳过
        self.assertTrue(result2.is_success)  # 工作流仍然成功，但任务被跳过
        self.assertTrue(result2.task_results["state_task"].is_skipped)
        self.assertEqual(["task_skipped"], self.execution_order)

        # 重置执行顺序
        self.execution_order = []

        # 恢复正常模式但禁用处理
        self.engine.set_state("system_mode", "normal")
        self.engine.set_state("processing_enabled", False)

        # 再次执行工作流
        result3 = self.workflow_manager.execute_workflow("state_workflow")

        # 验证任务被跳过
        self.assertTrue(result3.is_success)
        self.assertTrue(result3.task_results["state_task"].is_skipped)
        self.assertEqual(["task_skipped"], self.execution_order)

    def test_engine_hooks(self):
        """测试引擎钩子"""
        # 跟踪钩子调用
        hook_calls = []

        # 定义钩子函数
        def before_workflow_execution(workflow_name, context):
            hook_calls.append(f"before_workflow:{workflow_name}")

        def after_workflow_execution(workflow_name, result):
            hook_calls.append(
                f"after_workflow:{workflow_name}:{result.is_success}")

        def before_task_execution(workflow_name, task_name, context):
            hook_calls.append(f"before_task:{workflow_name}:{task_name}")

        def after_task_execution(workflow_name, task_name, result):
            hook_calls.append(
                f"after_task:{workflow_name}:{task_name}:{result.is_success}"
            )

        # 注册钩子函数
        self.engine.register_hook(
            "before_workflow_execution", before_workflow_execution
        )
        self.engine.register_hook(
            "after_workflow_execution", after_workflow_execution)
        self.engine.register_hook(
            "before_task_execution", before_task_execution)
        self.engine.register_hook("after_task_execution", after_task_execution)

        # 创建简单工作流
        workflow = Workflow("hook_workflow")
        workflow.add_task(
            Task("hook_task", lambda ctx: TaskResult.success({"done": True}))
        )

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 执行工作流
        result = self.workflow_manager.execute_workflow("hook_workflow")

        # 验证结果
        self.assertTrue(result.is_success)

        # 验证钩子调用顺序
        expected_calls = [
            "before_workflow:hook_workflow",
            "before_task:hook_workflow:hook_task",
            "after_task:hook_workflow:hook_task:True",
            "after_workflow:hook_workflow:True",
        ]
        self.assertEqual(expected_calls, hook_calls)

        # 清除钩子并验证
        self.engine.unregister_hook(
            "before_workflow_execution", before_workflow_execution
        )

        # 重置钩子调用记录
        hook_calls = []

        # 再次执行工作流
        self.workflow_manager.execute_workflow("hook_workflow")

        # 验证钩子调用（没有before_workflow钩子）
        expected_calls = [
            "before_task:hook_workflow:hook_task",
            "after_task:hook_workflow:hook_task:True",
            "after_workflow:hook_workflow:True",
        ]
        self.assertEqual(expected_calls, hook_calls)


def run_tests():
    """运行所有核心引擎测试"""
    unittest.main()


if __name__ == "__main__":
    run_tests()