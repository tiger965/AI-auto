"""
工作流测试模块

用于测试核心引擎中的工作流组件，包括工作流创建、任务执行、
条件分支、错误处理、工作流状态持久化和并行执行等功能。
"""

import unittest
import time
import os
import json
import threading
import concurrent.futures
from unittest.mock import MagicMock, patch

# 导入工作流组件
from core.workflow.workflow_manager import WorkflowManager
from core.workflow.workflow import Workflow
from core.workflow.task import Task
from core.workflow.task_result import TaskResult
from core.workflow.workflow_context import WorkflowContext
from core.workflow.workflow_executor import WorkflowExecutor
from core.workflow.workflow_validator import WorkflowValidator
from core.workflow.workflow_template import WorkflowTemplate
from core.workflow.conditional_branch import ConditionalBranch


class TestWorkflow(unittest.TestCase):
    """工作流组件测试类"""

    def setUp(self):
        """测试前准备工作"""
        # 创建工作流管理器实例
        self.workflow_manager = WorkflowManager()

        # 测试数据目录
        self.test_data_dir = "./test_data/workflow"
        os.makedirs(self.test_data_dir, exist_ok=True)

        # 执行顺序跟踪
        self.execution_order = []

        # 创建基本任务
        self.task1 = Task("task1", self.task_function1)
        self.task2 = Task("task2", self.task_function2)
        self.task3 = Task("task3", self.task_function3)

    def tearDown(self):
        """测试后清理工作"""
        # 重置工作流管理器
        self.workflow_manager = WorkflowManager()

        # 清空执行顺序
        self.execution_order = []

    def task_function1(self, context):
        """测试任务1"""
        self.execution_order.append(1)
        context.set("task1_result", "Task 1 executed")
        return TaskResult.success({"message": "Task 1 completed"})

    def task_function2(self, context):
        """测试任务2"""
        self.execution_order.append(2)
        context.set("task2_result", "Task 2 executed")
        return TaskResult.success({"message": "Task 2 completed"})

    def task_function3(self, context):
        """测试任务3"""
        self.execution_order.append(3)
        context.set("task3_result", "Task 3 executed")
        return TaskResult.success({"message": "Task 3 completed"})

    def test_task_creation(self):
        """测试任务创建"""
        # 创建任务
        task = Task("test_task", lambda ctx: TaskResult.success(
            {"result": "success"}))

        # 验证任务属性
        self.assertEqual("test_task", task.name)
        self.assertTrue(callable(task.function))
        self.assertFalse(task.is_async)

        # 创建异步任务
        async_task = Task(
            "async_task",
            lambda ctx: TaskResult.success({"result": "async"}),
            is_async=True,
        )
        self.assertTrue(async_task.is_async)

    def test_workflow_creation(self):
        """测试工作流创建"""
        # 创建工作流
        workflow = Workflow("test_workflow")

        # 验证工作流属性
        self.assertEqual("test_workflow", workflow.name)
        self.assertEqual(0, len(workflow.tasks))

        # 添加任务
        workflow.add_task(self.task1)
        workflow.add_task(self.task2)

        # 验证任务添加成功
        self.assertEqual(2, len(workflow.tasks))
        self.assertEqual("task1", workflow.tasks[0].name)
        self.assertEqual("task2", workflow.tasks[1].name)

    def test_workflow_registration(self):
        """测试工作流注册"""
        # 创建工作流
        workflow = Workflow("registration_workflow")
        workflow.add_task(self.task1)

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 验证工作流已注册
        self.assertTrue(self.workflow_manager.has_workflow(
            "registration_workflow"))

        # 获取已注册的工作流
        registered_workflow = self.workflow_manager.get_workflow(
            "registration_workflow"
        )
        self.assertEqual("registration_workflow", registered_workflow.name)
        self.assertEqual(1, len(registered_workflow.tasks))

    def test_workflow_execution(self):
        """测试工作流执行"""
        # 创建工作流
        workflow = Workflow("execution_workflow")
        workflow.add_task(self.task1)
        workflow.add_task(self.task2)
        workflow.add_task(self.task3)

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 执行工作流
        result = self.workflow_manager.execute_workflow("execution_workflow")

        # 验证执行顺序
        self.assertEqual([1, 2, 3], self.execution_order)

        # 验证执行结果
        self.assertTrue(result.is_success)
        self.assertEqual(3, len(result.task_results))
        self.assertEqual(
            "Task 1 completed", result.task_results["task1"].data["message"]
        )
        self.assertEqual(
            "Task 2 completed", result.task_results["task2"].data["message"]
        )
        self.assertEqual(
            "Task 3 completed", result.task_results["task3"].data["message"]
        )

    def test_workflow_context(self):
        """测试工作流上下文"""

        # 创建特殊任务来测试上下文
        def context_writer(context):
            context.set("key1", "value1")
            return TaskResult.success()

        def context_reader(context):
            value = context.get("key1")
            context.set("key2", f"read_{value}")
            return TaskResult.success({"read_value": value})

        # 创建任务
        task_writer = Task("writer", context_writer)
        task_reader = Task("reader", context_reader)

        # 创建工作流
        workflow = Workflow("context_workflow")
        workflow.add_task(task_writer)
        workflow.add_task(task_reader)

        # 注册并执行工作流
        self.workflow_manager.register_workflow(workflow)
        result = self.workflow_manager.execute_workflow("context_workflow")

        # 获取工作流上下文
        context = result.context

        # 验证上下文数据
        self.assertEqual("value1", context.get("key1"))
        self.assertEqual("read_value1", context.get("key2"))

        # 验证任务结果
        self.assertEqual(
            "value1", result.task_results["reader"].data["read_value"])

    def test_initial_context(self):
        """测试初始上下文"""

        # 创建上下文读取任务
        def read_initial_context(context):
            return TaskResult.success(
                {
                    "initial_value": context.get("initial_key"),
                    "workflow_name": context.get("workflow_name"),
                }
            )

        # 创建工作流
        workflow = Workflow("initial_context_workflow")
        workflow.add_task(Task("reader", read_initial_context))

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 创建初始上下文
        initial_context = WorkflowContext()
        initial_context.set("initial_key", "initial_value")

        # 执行工作流，传入初始上下文
        result = self.workflow_manager.execute_workflow(
            "initial_context_workflow", initial_context
        )

        # 验证任务能够读取初始上下文
        task_result = result.task_results["reader"]
        self.assertEqual("initial_value", task_result.data["initial_value"])
        self.assertEqual("initial_context_workflow",
                         task_result.data["workflow_name"])

    def test_conditional_workflow(self):
        """测试条件工作流"""

        # 创建条件任务
        def condition_task(context):
            condition_value = context.get("condition", False)
            context.set("condition_result", condition_value)
            if condition_value:
                return TaskResult.success({"path": "true_path"})
            else:
                return TaskResult.success({"path": "false_path"})

        # 创建条件分支处理
        def true_branch_task(context):
            self.execution_order.append("true")
            return TaskResult.success({"branch": "true"})

        def false_branch_task(context):
            self.execution_order.append("false")
            return TaskResult.success({"branch": "false"})

        # 创建任务
        condition = Task("condition", condition_task)
        true_task = Task("true_task", true_branch_task)
        false_task = Task("false_task", false_branch_task)

        # 创建工作流
        workflow = Workflow("conditional_workflow")
        workflow.add_task(condition)

        # 添加条件分支
        workflow.add_conditional_branch(
            ConditionalBranch(
                "condition", "path", {
                    "true_path": true_task, "false_path": false_task}
            )
        )

        # 添加最终任务
        workflow.add_task(self.task3)

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 执行条件为真的情况
        true_context = WorkflowContext()
        true_context.set("condition", True)
        true_result = self.workflow_manager.execute_workflow(
            "conditional_workflow", true_context
        )

        # 验证执行路径
        self.assertEqual(["true", 3], self.execution_order)
        self.assertEqual(
            "true", true_result.task_results["true_task"].data["branch"])

        # 重置执行顺序
        self.execution_order = []

        # 执行条件为假的情况
        false_context = WorkflowContext()
        false_context.set("condition", False)
        false_result = self.workflow_manager.execute_workflow(
            "conditional_workflow", false_context
        )

        # 验证执行路径
        self.assertEqual(["false", 3], self.execution_order)
        self.assertEqual(
            "false", false_result.task_results["false_task"].data["branch"]
        )

    def test_nested_conditions(self):
        """测试嵌套条件"""

        # 创建多层条件任务
        def level1_condition(context):
            return TaskResult.success({"path": "nested"})

        def level2_condition(context):
            return TaskResult.success({"path": "deep"})

        def leaf_task(context):
            self.execution_order.append("leaf")
            return TaskResult.success({"reached": "leaf"})

        # 创建任务
        condition1 = Task("condition1", level1_condition)
        condition2 = Task("condition2", level2_condition)
        leaf = Task("leaf", leaf_task)

        # 创建嵌套工作流
        workflow = Workflow("nested_workflow")
        workflow.add_task(condition1)

        # 创建第二层分支
        level2_branch = Workflow("level2_workflow")
        level2_branch.add_task(condition2)
        level2_branch.add_conditional_branch(
            ConditionalBranch("condition2", "path", {"deep": leaf})
        )

        # 添加第一层分支
        workflow.add_conditional_branch(
            ConditionalBranch("condition1", "path", {"nested": level2_branch})
        )

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 执行工作流
        result = self.workflow_manager.execute_workflow("nested_workflow")

        # 验证执行路径
        self.assertEqual(["leaf"], self.execution_order)
        self.assertEqual("leaf", result.task_results["leaf"].data["reached"])

    def test_error_handling(self):
        """测试错误处理"""

        # 创建会抛出异常的任务
        def failing_task(context):
            raise ValueError("测试异常")

        # 创建错误处理任务
        def error_handler(context, exception):
            self.execution_order.append("error_handler")
            context.set("error_message", str(exception))
            return TaskResult.success({"handled": True})

        # 创建任务
        task_fail = Task("failing", failing_task)

        # 创建工作流
        workflow = Workflow("error_workflow")
        workflow.add_task(self.task1)
        workflow.add_task(task_fail)
        workflow.add_task(self.task3)  # 由于前一个任务失败，这个不应该执行

        # 设置错误处理器
        workflow.set_error_handler(error_handler)

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 执行工作流
        result = self.workflow_manager.execute_workflow("error_workflow")

        # 验证执行顺序（应该是任务1和错误处理器）
        self.assertEqual([1, "error_handler"], self.execution_order)

        # 验证执行结果
        self.assertFalse(result.is_success)  # 整体工作流应该失败
        self.assertEqual("failing", result.failed_task_name)
        self.assertIsInstance(result.exception, ValueError)
        self.assertEqual("测试异常", str(result.exception))

        # 验证错误处理器结果
        self.assertTrue(result.error_handled)
        self.assertEqual("测试异常", result.context.get("error_message"))

    def test_task_retry(self):
        """测试任务重试"""
        # 创建一个会失败几次然后成功的任务
        retry_count = [0]  # 使用列表以便在闭包中修改

        def retry_task(context):
            retry_count[0] += 1
            if retry_count[0] <= 2:  # 前两次失败
                raise RuntimeError(f"失败 #{retry_count[0]}")
            # 第三次成功
            return TaskResult.success({"attempts": retry_count[0]})

        # 创建任务，设置重试参数
        task_retry = Task("retry_task", retry_task)
        task_retry.set_retry_policy(max_retries=3, retry_delay=0.1)

        # 创建工作流
        workflow = Workflow("retry_workflow")
        workflow.add_task(task_retry)

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 执行工作流
        result = self.workflow_manager.execute_workflow("retry_workflow")

        # 验证执行结果
        self.assertTrue(result.is_success)  # 工作流应该成功
        self.assertEqual(3, retry_count[0])  # 应该尝试了3次
        self.assertEqual(3, result.task_results["retry_task"].data["attempts"])

    def test_task_timeout(self):
        """测试任务超时"""

        # 创建一个会超时的任务
        def timeout_task(context):
            time.sleep(0.5)  # 任务执行时间超过超时时间
            return TaskResult.success({"completed": True})

        # 创建任务，设置超时参数
        task_timeout = Task("timeout_task", timeout_task)
        task_timeout.set_timeout(0.1)  # 设置超时时间为100毫秒

        # 创建工作流
        workflow = Workflow("timeout_workflow")
        workflow.add_task(task_timeout)

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 执行工作流
        result = self.workflow_manager.execute_workflow("timeout_workflow")

        # 验证执行结果
        self.assertFalse(result.is_success)  # 工作流应该失败
        self.assertEqual("timeout_task", result.failed_task_name)
        self.assertIsInstance(result.exception, TimeoutError)
        self.assertIn("任务执行超时", str(result.exception))

    def test_parallel_task_execution(self):
        """测试并行任务执行"""

        # 创建慢速任务
        def slow_task1(context):
            time.sleep(0.1)
            self.execution_order.append("slow1")
            return TaskResult.success({"task": "slow1"})

        def slow_task2(context):
            time.sleep(0.1)
            self.execution_order.append("slow2")
            return TaskResult.success({"task": "slow2"})

        # 创建任务
        task_slow1 = Task("slow1", slow_task1)
        task_slow2 = Task("slow2", slow_task2)

        # 创建并行任务集
        parallel_tasks = [task_slow1, task_slow2]

        # 创建工作流执行器
        executor = WorkflowExecutor()

        # 创建上下文
        context = WorkflowContext()

        # 串行执行（基准测试）
        start_time = time.time()
        serial_results = {}
        for task in parallel_tasks:
            serial_results[task.name] = executor.execute_task(task, context)
        serial_time = time.time() - start_time

        # 重置执行顺序
        self.execution_order = []

        # 并行执行
        start_time = time.time()
        parallel_results = executor.execute_tasks_parallel(
            parallel_tasks, context)
        parallel_time = time.time() - start_time

        # 验证结果正确性
        self.assertEqual(2, len(parallel_results))
        self.assertTrue(parallel_results["slow1"].is_success)
        self.assertTrue(parallel_results["slow2"].is_success)

        # 验证执行时间（并行应该比串行快）
        # 注意：不严格比较，因为线程启动有开销
        self.assertLess(parallel_time, serial_time * 0.8 + 0.1)

        # 验证任务都执行了
        self.assertEqual(2, len(self.execution_order))
        self.assertIn("slow1", self.execution_order)
        self.assertIn("slow2", self.execution_order)

    def test_parallel_workflow(self):
        """测试并行工作流"""
        # 创建工作流
        workflow = Workflow("parallel_workflow")

        # 添加串行任务
        workflow.add_task(self.task1)

        # 添加并行任务组
        parallel_tasks = [
            Task("parallel1", lambda ctx: self._parallel_task(ctx, "p1")),
            Task("parallel2", lambda ctx: self._parallel_task(ctx, "p2")),
            Task("parallel3", lambda ctx: self._parallel_task(ctx, "p3")),
        ]
        workflow.add_parallel_tasks(parallel_tasks)

        # 添加最后的串行任务
        workflow.add_task(self.task3)

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 执行工作流
        result = self.workflow_manager.execute_workflow("parallel_workflow")

        # 验证执行结果
        self.assertTrue(result.is_success)

        # 验证执行顺序：task1 应该是第一个，并行任务顺序不定，task3 应该是最后一个
        self.assertEqual(1, self.execution_order[0])  # 第一个任务
        self.assertEqual(3, self.execution_order[-1])  # 最后一个任务

        # 验证所有并行任务都执行了
        self.assertIn("p1", self.execution_order)
        self.assertIn("p2", self.execution_order)
        self.assertIn("p3", self.execution_order)

    def _parallel_task(self, context, name):
        """用于并行执行的辅助任务"""
        self.execution_order.append(name)
        time.sleep(0.05)  # 模拟一些工作
        return TaskResult.success({"name": name})

    def test_workflow_persistence(self):
        """测试工作流持久化"""
        # 创建工作流
        workflow = Workflow("persistence_workflow")
        workflow.add_task(self.task1)
        workflow.add_task(self.task2)
        workflow.description = "测试持久化工作流"

        # 序列化工作流
        workflow_path = os.path.join(self.test_data_dir, "workflow.json")
        workflow.save(workflow_path)

        # 重置工作流管理器
        self.workflow_manager = WorkflowManager()

        # 从文件加载工作流
        loaded_workflow = Workflow.load(workflow_path)

        # 验证加载的工作流
        self.assertEqual("persistence_workflow", loaded_workflow.name)
        self.assertEqual("测试持久化工作流", loaded_workflow.description)
        self.assertEqual(2, len(loaded_workflow.tasks))

        # 注册加载的工作流
        self.workflow_manager.register_workflow(loaded_workflow)

        # 执行加载的工作流
        result = self.workflow_manager.execute_workflow("persistence_workflow")

        # 验证执行结果
        self.assertTrue(result.is_success)
        self.assertEqual([1, 2], self.execution_order)

    def test_workflow_template(self):
        """测试工作流模板"""
        # 创建工作流模板
        template = WorkflowTemplate("template_workflow")
        template.add_task_template("task1", "first_task")
        template.add_task_template("task2", "second_task")
        template.set_parameter("param1", "default_value")

        # 创建任务工厂函数
        def task_factory(task_name, task_type, params):
            if task_type == "first_task":
                return Task(
                    task_name,
                    lambda ctx: TaskResult.success(
                        {"type": task_type, "param": ctx.get("param1")}
                    ),
                )
            elif task_type == "second_task":
                return Task(
                    task_name,
                    lambda ctx: TaskResult.success(
                        {"type": task_type, "param": ctx.get("param1")}
                    ),
                )
            else:
                raise ValueError(f"未知任务类型: {task_type}")

        # 从模板创建工作流实例
        params = {"param1": "custom_value"}
        workflow = template.instantiate(
            "instance_workflow", task_factory, params)

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 执行工作流
        result = self.workflow_manager.execute_workflow("instance_workflow")

        # 验证执行结果
        self.assertTrue(result.is_success)
        self.assertEqual(
            "first_task", result.task_results["task1"].data["type"])
        self.assertEqual(
            "second_task", result.task_results["task2"].data["type"])
        self.assertEqual(
            "custom_value", result.task_results["task1"].data["param"])
        self.assertEqual(
            "custom_value", result.task_results["task2"].data["param"])

    def test_workflow_validation(self):
        """测试工作流验证"""
        # 创建有效和无效工作流
        valid_workflow = Workflow("valid_workflow")
        valid_workflow.add_task(self.task1)
        valid_workflow.add_task(self.task2)

        invalid_workflow = Workflow("invalid_workflow")
        # 无任务的工作流

        circular_workflow = Workflow("circular_workflow")
        circular_workflow.add_task(self.task1)
        # 添加循环依赖（假设支持这种配置）
        circular_workflow.add_dependency("task1", "task3")
        circular_workflow.add_task(self.task3)
        circular_workflow.add_dependency("task3", "task1")

        # 创建验证器
        validator = WorkflowValidator()

        # 验证工作流
        valid_result = validator.validate(valid_workflow)
        invalid_result = validator.validate(invalid_workflow)
        circular_result = validator.validate(circular_workflow)

        # 验证结果
        self.assertTrue(valid_result.is_valid)
        self.assertFalse(invalid_result.is_valid)
        self.assertIn("工作流没有任务", invalid_result.errors[0])

        self.assertFalse(circular_result.is_valid)
        self.assertIn("循环依赖", circular_result.errors[0])

    def test_workflow_execution_history(self):
        """测试工作流执行历史"""
        # 创建工作流
        workflow = Workflow("history_workflow")
        workflow.add_task(self.task1)
        workflow.add_task(self.task2)

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 启用执行历史记录
        self.workflow_manager.enable_execution_history()

        # 多次执行工作流
        for i in range(3):
            context = WorkflowContext()
            context.set("execution_id", f"run_{i}")
            self.workflow_manager.execute_workflow("history_workflow", context)
            # 重置执行顺序以便下次执行
            self.execution_order = []

        # 获取执行历史
        history = self.workflow_manager.get_workflow_execution_history(
            "history_workflow"
        )

        # 验证历史记录
        self.assertEqual(3, len(history))
        for i, entry in enumerate(history):
            self.assertEqual("history_workflow", entry.workflow_name)
            self.assertTrue(entry.is_success)
            self.assertEqual(f"run_{i}", entry.context.get("execution_id"))
            self.assertEqual(2, len(entry.task_results))

    def test_workflow_metrics(self):
        """测试工作流指标收集"""
        # 创建工作流
        workflow = Workflow("metrics_workflow")
        workflow.add_task(self.task1)
        workflow.add_task(self.task2)

        # 启用指标收集
        workflow.enable_metrics()

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 执行工作流
        self.workflow_manager.execute_workflow("metrics_workflow")

        # 获取工作流指标
        metrics = self.workflow_manager.get_workflow_metrics(
            "metrics_workflow")

        # 验证指标
        self.assertEqual(1, metrics.execution_count)
        self.assertGreater(metrics.average_execution_time, 0)
        self.assertGreater(metrics.last_execution_time, 0)

        # 验证任务指标
        self.assertEqual(2, len(metrics.task_metrics))
        self.assertIn("task1", metrics.task_metrics)
        self.assertIn("task2", metrics.task_metrics)

        # 重新执行工作流
        self.execution_order = []
        self.workflow_manager.execute_workflow("metrics_workflow")

        # 重新获取指标
        updated_metrics = self.workflow_manager.get_workflow_metrics(
            "metrics_workflow")

        # 验证更新后的指标
        self.assertEqual(2, updated_metrics.execution_count)

    def test_dynamic_workflow(self):
        """测试动态工作流生成"""

        # 创建动态生成工作流的任务
        def dynamic_workflow_generator(context):
            # 根据上下文生成不同的工作流
            task_count = context.get("task_count", 1)

            # 创建动态工作流
            workflow = Workflow("generated_workflow")

            # 添加指定数量的任务
            for i in range(task_count):
                task_name = f"dynamic_task_{i}"

                # 创建任务函数
                def task_func(ctx, index=i):
                    self.execution_order.append(f"dynamic_{index}")
                    return TaskResult.success({"task_index": index})

                # 添加任务
                workflow.add_task(Task(task_name, task_func))

            # 返回生成的工作流
            return TaskResult.success({"workflow": workflow})

        # 创建工作流生成器工作流
        generator_workflow = Workflow("generator_workflow")
        generator_workflow.add_task(
            Task("generator", dynamic_workflow_generator))

        # 注册工作流
        self.workflow_manager.register_workflow(generator_workflow)

        # 执行生成器工作流，生成包含3个任务的工作流
        context = WorkflowContext()
        context.set("task_count", 3)
        result = self.workflow_manager.execute_workflow(
            "generator_workflow", context)

        # 获取生成的工作流
        generated_workflow = result.task_results["generator"].data["workflow"]

        # 验证生成的工作流
        self.assertEqual("generated_workflow", generated_workflow.name)
        self.assertEqual(3, len(generated_workflow.tasks))

        # 注册并执行生成的工作流
        self.workflow_manager.register_workflow(generated_workflow)
        generated_result = self.workflow_manager.execute_workflow(
            "generated_workflow")

        # 验证执行结果
        self.assertTrue(generated_result.is_success)
        self.assertEqual(3, len(generated_result.task_results))

        # 验证执行顺序
        self.assertEqual(
            ["dynamic_0", "dynamic_1", "dynamic_2"], self.execution_order)

    def test_workflow_versioning(self):
        """测试工作流版本控制"""
        # 创建多个版本的工作流
        workflow_v1 = Workflow("versioned_workflow")
        workflow_v1.version = "1.0.0"
        workflow_v1.add_task(self.task1)

        workflow_v2 = Workflow("versioned_workflow")
        workflow_v2.version = "2.0.0"
        workflow_v2.add_task(self.task1)
        workflow_v2.add_task(self.task2)

        # 注册不同版本
        self.workflow_manager.register_workflow(workflow_v1)
        self.workflow_manager.register_workflow(workflow_v2)

        # 执行指定版本
        result_v1 = self.workflow_manager.execute_workflow(
            "versioned_workflow", version="1.0.0"
        )

        # 重置执行顺序
        self.execution_order = []

        # 执行最新版本（不指定版本）
        result_v2 = self.workflow_manager.execute_workflow(
            "versioned_workflow")

        # 验证版本1执行结果
        self.assertTrue(result_v1.is_success)
        self.assertEqual([1], self.execution_order)

        # 验证版本2执行结果（当前执行顺序）
        self.assertTrue(result_v2.is_success)
        self.assertEqual([1, 2], self.execution_order)

    def test_workflow_progress_tracking(self):
        """测试工作流进度跟踪"""

        # 创建带进度的任务
        def progress_task1(context):
            # 报告进度50%
            if hasattr(context, "report_progress"):
                context.report_progress("progress_task1", 0.5)
            time.sleep(0.05)
            return TaskResult.success()

        def progress_task2(context):
            # 报告进度分阶段
            if hasattr(context, "report_progress"):
                context.report_progress("progress_task2", 0.3)
                time.sleep(0.03)
                context.report_progress("progress_task2", 0.7)
                time.sleep(0.03)
                context.report_progress("progress_task2", 1.0)
            return TaskResult.success()

        # 创建工作流
        workflow = Workflow("progress_workflow")
        workflow.add_task(Task("progress_task1", progress_task1))
        workflow.add_task(Task("progress_task2", progress_task2))

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 创建进度监听器
        progress_updates = []

        def progress_listener(workflow_name, task_name, progress):
            progress_updates.append((workflow_name, task_name, progress))

        # 启用进度跟踪
        self.workflow_manager.set_progress_listener(progress_listener)

        # 执行工作流
        result = self.workflow_manager.execute_workflow("progress_workflow")

        # 验证执行结果
        self.assertTrue(result.is_success)

        # 验证进度更新
        self.assertGreaterEqual(len(progress_updates), 3)  # 至少应有3次更新

        # 检查第一个任务的进度更新
        task1_updates = [
            p for p in progress_updates if p[1] == "progress_task1"]
        self.assertGreaterEqual(len(task1_updates), 1)

        # 检查第二个任务的进度更新
        task2_updates = [
            p for p in progress_updates if p[1] == "progress_task2"]
        self.assertGreaterEqual(len(task2_updates), 3)

        # 验证工作流总体进度更新
        workflow_updates = [p for p in progress_updates if p[1] is None]
        self.assertGreaterEqual(len(workflow_updates), 1)

    def test_workflow_dependency_injection(self):
        """测试工作流依赖注入"""

        # 创建依赖服务
        class DataService:
            def get_data(self):
                return {"service_data": "injected_value"}

        # 创建需要依赖的任务
        def task_with_dependency(context):
            # 获取注入的服务
            data_service = context.get_service("data_service")

            # 使用服务
            data = data_service.get_data()

            return TaskResult.success(data)

        # 创建工作流
        workflow = Workflow("dependency_workflow")
        workflow.add_task(Task("dependency_task", task_with_dependency))

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 创建依赖服务实例
        data_service = DataService()

        # 创建包含服务的上下文
        context = WorkflowContext()
        context.register_service("data_service", data_service)

        # 执行工作流
        result = self.workflow_manager.execute_workflow(
            "dependency_workflow", context)

        # 验证执行结果
        self.assertTrue(result.is_success)
        self.assertEqual(
            "injected_value",
            result.task_results["dependency_task"].data["service_data"],
        )

    def test_workflow_task_dependencies(self):
        """测试工作流任务依赖关系"""
        # 创建具有依赖关系的工作流
        workflow = Workflow("dependency_workflow")

        # 添加任务
        workflow.add_task(self.task1)
        workflow.add_task(self.task2)
        workflow.add_task(self.task3)

        # 设置依赖：task2依赖task1，task3依赖task2
        workflow.add_dependency("task2", "task1")
        workflow.add_dependency("task3", "task2")

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 执行工作流
        result = self.workflow_manager.execute_workflow("dependency_workflow")

        # 验证执行顺序满足依赖关系
        self.assertEqual([1, 2, 3], self.execution_order)

        # 创建另一个依赖关系不同的工作流
        workflow2 = Workflow("dependency_workflow2")

        # 添加任务
        workflow2.add_task(self.task1)
        workflow2.add_task(self.task2)
        workflow2.add_task(self.task3)

        # 设置不同的依赖：task3依赖task1，task2独立
        workflow2.add_dependency("task3", "task1")

        # 重置执行顺序
        self.execution_order = []

        # 注册工作流
        self.workflow_manager.register_workflow(workflow2)

        # 执行工作流
        result2 = self.workflow_manager.execute_workflow(
            "dependency_workflow2")

        # 验证执行顺序（由于task2和其他任务没有依赖关系，顺序可能变化）
        self.assertIn(1, self.execution_order)
        self.assertIn(2, self.execution_order)
        self.assertIn(3, self.execution_order)

        # 验证依赖关系：task1必须在task3之前执行
        task1_idx = self.execution_order.index(1)
        task3_idx = self.execution_order.index(3)
        self.assertLess(task1_idx, task3_idx)

    def test_workflow_cancellation(self):
        """测试工作流取消"""

        # 创建长时间运行的任务
        def long_running_task(context):
            for i in range(10):
                # 检查取消信号
                if context.is_cancelled():
                    return TaskResult.cancelled("任务被取消")
                time.sleep(0.1)
                self.execution_order.append(i)
            return TaskResult.success()

        # 创建工作流
        workflow = Workflow("cancellation_workflow")
        workflow.add_task(Task("long_task", long_running_task))

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 在另一个线程中执行工作流
        execution_thread = threading.Thread(
            target=self.workflow_manager.execute_workflow,
            args=("cancellation_workflow",),
        )

        # 启动执行
        execution_thread.start()

        # 等待一段时间后取消
        time.sleep(0.25)  # 让任务运行一点时间

        # 取消工作流
        self.workflow_manager.cancel_workflow("cancellation_workflow")

        # 等待执行线程结束
        execution_thread.join(timeout=1.0)

        # 验证工作流被取消
        self.assertLess(len(self.execution_order), 10)  # 应该在完成前被取消

    def test_workflow_result_transformation(self):
        """测试工作流结果转换"""

        # 创建产生结果的任务
        def data_task(context):
            return TaskResult.success(
                {"values": [1, 2, 3, 4, 5], "metadata": {"source": "test"}}
            )

        # 创建工作流
        workflow = Workflow("transform_workflow")
        workflow.add_task(Task("data_task", data_task))

        # 设置结果转换函数
        def result_transformer(workflow_result):
            if workflow_result.is_success:
                # 提取数据任务的结果
                data = workflow_result.task_results["data_task"].data

                # 计算统计量
                values = data["values"]
                transformed = {
                    "count": len(values),
                    "sum": sum(values),
                    "average": sum(values) / len(values),
                    "source": data["metadata"]["source"],
                }

                return transformed
            else:
                return {"error": str(workflow_result.exception)}

        workflow.set_result_transformer(result_transformer)

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 执行工作流
        result = self.workflow_manager.execute_workflow("transform_workflow")

        # 验证执行结果经过转换
        self.assertEqual(5, result.transformed_result["count"])
        self.assertEqual(15, result.transformed_result["sum"])
        self.assertEqual(3.0, result.transformed_result["average"])
        self.assertEqual("test", result.transformed_result["source"])

    def test_workflow_data_passing(self):
        """测试工作流数据传递"""

        # 创建数据生产者任务
        def producer_task(context):
            return TaskResult.success({"data": "produced_value"})

        # 创建数据消费者任务
        def consumer_task(context):
            # 从上一个任务获取结果
            producer_result = context.get_task_result("producer")
            data = producer_result.data["data"]

            # 使用数据
            return TaskResult.success(
                {"consumed": data, "modified": data + "_modified"}
            )

        # 创建工作流
        workflow = Workflow("data_passing_workflow")
        workflow.add_task(Task("producer", producer_task))
        workflow.add_task(Task("consumer", consumer_task))

        # 注册工作流
        self.workflow_manager.register_workflow(workflow)

        # 执行工作流
        result = self.workflow_manager.execute_workflow(
            "data_passing_workflow")

        # 验证数据传递
        self.assertEqual("produced_value",
                         result.task_results["producer"].data["data"])
        self.assertEqual(
            "produced_value", result.task_results["consumer"].data["consumed"]
        )
        self.assertEqual(
            "produced_value_modified", result.task_results["consumer"].data["modified"]
        )

    def test_workflow_subworkflow(self):
        """测试子工作流"""
        # 创建子工作流
        subworkflow = Workflow("sub_workflow")
        subworkflow.add_task(
            Task("sub_task1", lambda ctx: TaskResult.success(
                {"sub": "value1"}))
        )
        subworkflow.add_task(
            Task("sub_task2", lambda ctx: TaskResult.success(
                {"sub": "value2"}))
        )

        # 创建主工作流
        main_workflow = Workflow("main_workflow")
        main_workflow.add_task(self.task1)
        main_workflow.add_subworkflow(subworkflow)
        main_workflow.add_task(self.task3)

        # 注册工作流
        self.workflow_manager.register_workflow(main_workflow)

        # 执行工作流
        result = self.workflow_manager.execute_workflow("main_workflow")

        # 验证执行结果
        self.assertTrue(result.is_success)

        # 验证主工作流任务执行
        self.assertIn("task1", result.task_results)
        self.assertIn("task3", result.task_results)

        # 验证子工作流结果
        self.assertIn("sub_workflow", result.subworkflow_results)

        sub_result = result.subworkflow_results["sub_workflow"]
        self.assertTrue(sub_result.is_success)
        self.assertIn("sub_task1", sub_result.task_results)
        self.assertIn("sub_task2", sub_result.task_results)
        self.assertEqual(
            "value1", sub_result.task_results["sub_task1"].data["sub"])
        self.assertEqual(
            "value2", sub_result.task_results["sub_task2"].data["sub"])


def run_tests():
    """运行所有工作流组件测试"""
    unittest.main()


if __name__ == "__main__":
    run_tests()