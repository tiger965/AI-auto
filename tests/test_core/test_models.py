"""
模型组件测试模块

用于测试核心引擎中的模型组件，包括模型加载、初始化、预测功能、
模型缓存、资源管理、版本控制和性能评估等功能。
"""

import unittest
import time
import os
import json
import numpy as np
import threading
from unittest.mock import MagicMock, patch

# 导入模型组件
from core.models.model_manager import ModelManager
from core.models.model import Model
from core.models.model_loader import ModelLoader
from core.models.model_metadata import ModelMetadata
from core.models.model_registry import ModelRegistry
from core.models.model_version import ModelVersion
from core.models.model_adapter import ModelAdapter
from core.models.model_optimizer import ModelOptimizer
from core.models.model_validator import ModelValidator


class TestModels(unittest.TestCase):
    """模型组件测试类"""

    def setUp(self):
        """测试前准备工作"""
        # 创建模型管理器实例
        self.model_manager = ModelManager()

        # 测试数据目录
        self.test_data_dir = "./test_data/models"
        os.makedirs(self.test_data_dir, exist_ok=True)

        # 创建模拟模型
        self.mock_model_path = os.path.join(
            self.test_data_dir, "mock_model.json")
        with open(self.mock_model_path, "w") as f:
            json.dump(
                {
                    "name": "mock_model",
                    "version": "1.0.0",
                    "parameters": {"weights": [0.1, 0.2, 0.3], "bias": 0.05},
                },
                f,
            )

    def tearDown(self):
        """测试后清理工作"""
        # 释放所有模型资源
        self.model_manager.unload_all_models()

        # 清理模型缓存
        self.model_manager.clear_model_cache()

    def test_model_initialization(self):
        """测试模型初始化"""
        # 创建模型实例
        model = Model("test_model")

        # 验证模型属性
        self.assertEqual("test_model", model.name)
        self.assertIsNone(model.version)
        self.assertFalse(model.is_loaded)

        # 初始化模型
        model.initialize({"param1": 10, "param2": "value"})

        # 验证模型已初始化
        self.assertTrue(model.is_initialized)
        self.assertEqual(10, model.get_parameter("param1"))
        self.assertEqual("value", model.get_parameter("param2"))

    def test_model_loading(self):
        """测试模型加载"""
        # 创建模型加载器
        loader = ModelLoader()

        # 加载模型
        model = loader.load_model(self.mock_model_path)

        # 验证模型加载正确
        self.assertEqual("mock_model", model.name)
        self.assertEqual("1.0.0", model.version)
        self.assertTrue(model.is_loaded)

        # 验证模型参数
        self.assertEqual([0.1, 0.2, 0.3], model.get_parameter("weights"))
        self.assertEqual(0.05, model.get_parameter("bias"))

    def test_model_manager_loading(self):
        """测试模型管理器加载功能"""
        # 使用模型管理器加载模型
        model = self.model_manager.load_model(self.mock_model_path)

        # 验证模型加载正确
        self.assertEqual("mock_model", model.name)
        self.assertTrue(model.is_loaded)

        # 验证模型已在管理器中注册
        self.assertIn(
            "mock_model", self.model_manager.get_loaded_model_names())
        self.assertEqual(model, self.model_manager.get_model("mock_model"))

    def test_model_prediction(self):
        """测试模型预测功能"""
        # 创建模型
        model = Model("prediction_model")

        # 模拟预测函数
        def mock_predict(inputs):
            return {"result": sum(inputs["features"]) + model.get_parameter("bias")}

        # 设置模型参数和预测函数
        model.initialize({"bias": 1.0})
        model.set_predict_function(mock_predict)

        # 执行预测
        prediction = model.predict({"features": [1, 2, 3]})

        # 验证预测结果
        self.assertEqual(7.0, prediction["result"])  # 1+2+3+1(bias)=7

    def test_model_batch_prediction(self):
        """测试批量预测功能"""
        # 创建模型
        model = Model("batch_model")

        # 模拟批量预测函数
        def mock_batch_predict(batch_inputs):
            results = []
            bias = model.get_parameter("bias")
            for inputs in batch_inputs:
                results.append({"result": sum(inputs["features"]) + bias})
            return results

        # 设置模型参数和预测函数
        model.initialize({"bias": 1.0})
        model.set_batch_predict_function(mock_batch_predict)

        # 执行批量预测
        batch_data = [{"features": [1, 2]}, {
            "features": [3, 4]}, {"features": [5, 6]}]
        predictions = model.predict_batch(batch_data)

        # 验证预测结果
        self.assertEqual(3, len(predictions))
        self.assertEqual(4.0, predictions[0]["result"])  # 1+2+1(bias)=4
        self.assertEqual(8.0, predictions[1]["result"])  # 3+4+1(bias)=8
        self.assertEqual(12.0, predictions[2]["result"])  # 5+6+1(bias)=12

    def test_model_caching(self):
        """测试模型缓存机制"""

        # 模拟耗时的模型加载过程
        def slow_load_model(path):
            time.sleep(0.5)
            return Model("cached_model")

        # 替换模型加载器的加载方法
        original_load = ModelLoader.load_model
        ModelLoader.load_model = slow_load_model

        try:
            # 首次加载模型（应该耗时）
            start_time = time.time()
            model1 = self.model_manager.load_model(
                "dummy_path", use_cache=True)
            first_load_time = time.time() - start_time

            # 再次加载同一模型（应该从缓存获取，几乎不耗时）
            start_time = time.time()
            model2 = self.model_manager.load_model(
                "dummy_path", use_cache=True)
            cached_load_time = time.time() - start_time

            # 验证模型缓存有效
            self.assertIs(model1, model2)  # 应该是同一个对象实例
            self.assertLess(
                cached_load_time, first_load_time * 0.1
            )  # 缓存加载应该快10倍以上

            # 测试禁用缓存
            start_time = time.time()
            model3 = self.model_manager.load_model(
                "dummy_path", use_cache=False)
            no_cache_load_time = time.time() - start_time

            # 验证未使用缓存
            self.assertIsNot(model1, model3)  # 应该是不同的对象实例
            self.assertGreater(
                no_cache_load_time, cached_load_time * 5
            )  # 非缓存加载应该慢很多

        finally:
            # 恢复原始加载方法
            ModelLoader.load_model = original_load

    def test_model_unloading(self):
        """测试模型卸载功能"""
        # 加载模型
        model = self.model_manager.load_model(self.mock_model_path)
        self.assertIn(
            "mock_model", self.model_manager.get_loaded_model_names())

        # 卸载模型
        self.model_manager.unload_model("mock_model")

        # 验证模型已卸载
        self.assertNotIn(
            "mock_model", self.model_manager.get_loaded_model_names())

        # 尝试访问已卸载的模型
        with self.assertRaises(KeyError):
            self.model_manager.get_model("mock_model")

    def test_model_registry(self):
        """测试模型注册表"""
        # 创建模型注册表
        registry = ModelRegistry()

        # 注册模型
        model_metadata = ModelMetadata(
            name="registered_model",
            version="1.0.0",
            description="测试模型",
            author="测试作者",
            creation_date="2025-04-20",
            tags=["test", "model"],
            parameters={"param1": "value1"},
        )

        registry.register_model(model_metadata, self.mock_model_path)

        # 验证模型已注册
        self.assertTrue(registry.is_registered("registered_model"))

        # 获取注册的模型信息
        registered_model = registry.get_model_info("registered_model")
        self.assertEqual("registered_model", registered_model.name)
        self.assertEqual("1.0.0", registered_model.version)
        self.assertEqual("测试模型", registered_model.description)

        # 获取模型路径
        model_path = registry.get_model_path("registered_model")
        self.assertEqual(self.mock_model_path, model_path)

        # 获取所有注册模型
        all_models = registry.get_all_models()
        self.assertEqual(1, len(all_models))
        self.assertEqual("registered_model", all_models[0].name)

        # 按标签搜索模型
        test_models = registry.search_models_by_tag("test")
        self.assertEqual(1, len(test_models))
        self.assertEqual("registered_model", test_models[0].name)

    def test_model_versioning(self):
        """测试模型版本控制"""
        # 创建具有版本的模型元数据
        v1 = ModelMetadata(name="versioned_model", version="1.0.0")
        v2 = ModelMetadata(name="versioned_model", version="1.1.0")
        v3 = ModelMetadata(name="versioned_model", version="2.0.0")

        # 创建注册表
        registry = ModelRegistry()

        # 注册不同版本
        registry.register_model(v1, "path_to_v1")
        registry.register_model(v2, "path_to_v2")
        registry.register_model(v3, "path_to_v3")

        # 获取特定版本
        model_v1 = registry.get_model_version("versioned_model", "1.0.0")
        self.assertEqual("1.0.0", model_v1.version)

        # 获取最新版本
        latest_model = registry.get_latest_version("versioned_model")
        self.assertEqual("2.0.0", latest_model.version)

        # 获取所有版本
        all_versions = registry.get_all_versions("versioned_model")
        self.assertEqual(3, len(all_versions))

        # 版本比较
        version1 = ModelVersion.from_string("1.0.0")
        version2 = ModelVersion.from_string("1.1.0")
        self.assertTrue(version2 > version1)

        # 验证语义化版本规则
        self.assertTrue(
            ModelVersion.from_string(
                "1.0.1") > ModelVersion.from_string("1.0.0")
        )
        self.assertTrue(
            ModelVersion.from_string(
                "1.1.0") > ModelVersion.from_string("1.0.9")
        )
        self.assertTrue(
            ModelVersion.from_string(
                "2.0.0") > ModelVersion.from_string("1.9.9")
        )

    def test_model_adapter(self):
        """测试模型适配器"""
        # 创建原始模型（假设它有不兼容的接口）
        original_model = MagicMock()
        original_model.some_predict_method = lambda x: {
            "original_output": x * 2}

        # 创建适配器
        adapter = ModelAdapter(original_model)

        # 定义适配函数
        def adapt_input(inputs):
            return inputs["value"]

        def adapt_output(original_output):
            return {"result": original_output["original_output"]}

        # 设置适配函数
        adapter.set_input_adapter(adapt_input)
        adapter.set_output_adapter(adapt_output)

        # 测试适配后的预测
        result = adapter.predict({"value": 5})

        # 验证适配结果
        self.assertEqual({"result": 10}, result)

    def test_model_optimizer(self):
        """测试模型优化器"""
        # 创建模型
        model = Model("optimize_model")
        model.initialize({"weights": [1.0, 2.0, 3.0], "bias": 0.5})

        # 定义简单的目标函数（使权重之和最小化）
        def objective_function(model_params):
            return sum(model_params["weights"])

        # 创建优化器
        optimizer = ModelOptimizer()

        # 设置优化参数
        optimization_params = {
            "learning_rate": 0.1,
            "iterations": 5,
            "objective": objective_function,
        }

        # 执行优化
        optimized_model = optimizer.optimize(model, optimization_params)

        # 验证优化结果
        optimized_weights = optimized_model.get_parameter("weights")
        original_weights = model.get_parameter("weights")

        # 优化后的权重总和应该小于原始权重总和
        self.assertLess(sum(optimized_weights), sum(original_weights))

    def test_model_validator(self):
        """测试模型验证器"""
        # 创建模型
        model = Model("validation_model")
        model.initialize({"weights": [1.0, 2.0, 3.0], "bias": 0.5})

        # 设置预测函数
        def predict_func(inputs):
            weights = model.get_parameter("weights")
            bias = model.get_parameter("bias")
            return {
                "prediction": sum(w * x for w, x in zip(weights, inputs["features"]))
                + bias
            }

        model.set_predict_function(predict_func)

        # 创建验证数据
        validation_data = [
            (
                {"features": [1, 1, 1]},
                {"prediction": 6.5},
            ),  # 1*1 + 2*1 + 3*1 + 0.5 = 6.5
            (
                {"features": [0, 1, 0]},
                {"prediction": 2.5},
            ),  # 1*0 + 2*1 + 3*0 + 0.5 = 2.5
            (
                {"features": [1, 0, 1]},
                {"prediction": 4.5},
            ),  # 1*1 + 2*0 + 3*1 + 0.5 = 4.5
        ]

        # 创建验证器
        validator = ModelValidator()

        # 执行验证
        validation_result = validator.validate(model, validation_data)

        # 验证结果应该为完全匹配
        self.assertTrue(validation_result.is_valid)
        self.assertEqual(1.0, validation_result.accuracy)
        self.assertEqual(0.0, validation_result.error)

        # 测试不匹配的情况
        invalid_data = [
            ({"features": [1, 1, 1]}, {"prediction": 7.0}),  # 不正确的预期结果
            ({"features": [0, 1, 0]}, {"prediction": 2.5}),
        ]

        invalid_result = validator.validate(model, invalid_data)

        # 验证结果应该显示不完全匹配
        self.assertFalse(invalid_result.is_valid)
        self.assertEqual(0.5, invalid_result.accuracy)  # 只有一半匹配
        self.assertGreater(invalid_result.error, 0.0)

    def test_concurrent_model_access(self):
        """测试并发模型访问"""
        # 创建共享模型
        model = Model("concurrent_model")
        model.initialize({"counter": 0})

        # 定义累加预测函数
        def increment_counter(inputs):
            current = model.get_parameter("counter")
            # 模拟一些处理时间，增加并发冲突的可能性
            time.sleep(0.001)
            model.set_parameter("counter", current + 1)
            return {"counter": current + 1}

        model.set_predict_function(increment_counter)

        # 添加到模型管理器
        self.model_manager.register_model(model)

        # 并发访问函数
        def concurrent_predict(repeat_count):
            for _ in range(repeat_count):
                self.model_manager.get_model("concurrent_model").predict({})

        # 创建多个线程
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=concurrent_predict, args=(10,))
            threads.append(thread)

        # 启动所有线程
        for thread in threads:
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证最终计数器值（应为5*10=50）
        final_counter = model.get_parameter("counter")
        self.assertEqual(50, final_counter)

    def test_model_memory_management(self):
        """测试模型内存管理"""
        # 设置内存限制（假设单位为MB）
        self.model_manager.set_memory_limit(100)

        # 模拟大型模型
        large_model = Model("large_model")
        large_model.initialize({"size": 60})  # 假设占用60MB内存
        large_model.memory_usage = 60  # 手动设置内存占用，实际情况应自动计算

        medium_model = Model("medium_model")
        medium_model.initialize({"size": 30})  # 假设占用30MB内存
        medium_model.memory_usage = 30

        small_model = Model("small_model")
        small_model.initialize({"size": 20})  # 假设占用20MB内存
        small_model.memory_usage = 20

        # 加载模型
        self.model_manager.register_model(large_model)
        self.model_manager.register_model(medium_model)

        # 验证当前内存使用
        self.assertEqual(90, self.model_manager.get_memory_usage())

        # 尝试加载超出内存限制的模型
        with self.assertRaises(MemoryError):
            self.model_manager.register_model(
                small_model)  # 总共需要110MB > 100MB限制

        # 卸载中型模型
        self.model_manager.unload_model("medium_model")

        # 验证内存已释放
        self.assertEqual(60, self.model_manager.get_memory_usage())

        # 现在应该可以加载小型模型
        self.model_manager.register_model(small_model)  # 总共需要80MB < 100MB限制

        # 验证模型加载成功
        self.assertEqual(80, self.model_manager.get_memory_usage())
        self.assertIn(
            "small_model", self.model_manager.get_loaded_model_names())

    def test_model_ensemble(self):
        """测试模型集成"""
        # 创建多个基础模型
        model1 = Model("model1")
        model1.initialize({"weight": 1.0})
        model1.set_predict_function(
            lambda x: {"prediction": x["input"]
                       * model1.get_parameter("weight")}
        )

        model2 = Model("model2")
        model2.initialize({"weight": 2.0})
        model2.set_predict_function(
            lambda x: {"prediction": x["input"]
                       * model2.get_parameter("weight")}
        )

        model3 = Model("model3")
        model3.initialize({"weight": 3.0})
        model3.set_predict_function(
            lambda x: {"prediction": x["input"]
                       * model3.get_parameter("weight")}
        )

        # 注册模型
        self.model_manager.register_model(model1)
        self.model_manager.register_model(model2)
        self.model_manager.register_model(model3)

        # 创建集成模型（平均所有模型的预测）
        def ensemble_predict(inputs):
            predictions = []
            for model_name in ["model1", "model2", "model3"]:
                model = self.model_manager.get_model(model_name)
                predictions.append(model.predict(inputs)["prediction"])
            return {"prediction": sum(predictions) / len(predictions)}

        ensemble = Model("ensemble_model")
        ensemble.set_predict_function(ensemble_predict)
        self.model_manager.register_model(ensemble)

        # 测试集成预测
        result = ensemble.predict({"input": 2.0})

        # 验证结果：(2*1 + 2*2 + 2*3)/3 = 4
        self.assertEqual(4.0, result["prediction"])

    def test_model_metadata(self):
        """测试模型元数据"""
        # 创建模型元数据
        metadata = ModelMetadata(
            name="metadata_model",
            version="1.0.0",
            description="测试模型描述",
            author="测试作者",
            creation_date="2025-04-20",
            tags=["test", "model", "metadata"],
            parameters={"param1": "value1", "param2": "value2"},
            input_schema={
                "type": "object",
                "properties": {"feature": {"type": "number"}},
            },
            output_schema={
                "type": "object",
                "properties": {"prediction": {"type": "number"}},
            },
        )

        # 验证元数据属性
        self.assertEqual("metadata_model", metadata.name)
        self.assertEqual("1.0.0", metadata.version)
        self.assertEqual("测试模型描述", metadata.description)
        self.assertEqual("测试作者", metadata.author)

        # 测试标签操作
        self.assertTrue(metadata.has_tag("test"))
        self.assertFalse(metadata.has_tag("non_existent"))

        metadata.add_tag("new_tag")
        self.assertTrue(metadata.has_tag("new_tag"))

        metadata.remove_tag("test")
        self.assertFalse(metadata.has_tag("test"))

        # 测试参数访问
        self.assertEqual("value1", metadata.get_parameter("param1"))
        self.assertEqual("value2", metadata.get_parameter("param2"))

        # 测试序列化和反序列化
        serialized = metadata.to_json()
        deserialized = ModelMetadata.from_json(serialized)

        self.assertEqual(metadata.name, deserialized.name)
        self.assertEqual(metadata.version, deserialized.version)
        self.assertEqual(metadata.description, deserialized.description)

    def test_model_metrics(self):
        """测试模型指标收集"""
        # 创建带指标收集的模型
        model = Model("metrics_model", collect_metrics=True)

        # 设置预测函数（模拟一些处理时间）
        def predict_with_delay(inputs):
            time.sleep(0.01)
            return {"result": inputs["value"] * 2}

        model.set_predict_function(predict_with_delay)

        # 执行一系列预测
        for i in range(10):
            model.predict({"value": i})

        # 获取指标
        metrics = model.get_metrics()

        # 验证指标
        self.assertEqual(10, metrics["prediction_count"])
        self.assertGreater(metrics["total_prediction_time"], 0)
        self.assertGreater(metrics["average_prediction_time"], 0)
        self.assertLess(metrics["average_prediction_time"], 0.1)  # 应该小于100ms

        # 验证最慢和最快的预测时间
        self.assertLessEqual(
            metrics["min_prediction_time"], metrics["average_prediction_time"]
        )
        self.assertGreaterEqual(
            metrics["max_prediction_time"], metrics["average_prediction_time"]
        )

        # 重置指标
        model.reset_metrics()
        reset_metrics = model.get_metrics()

        # 验证重置是否成功
        self.assertEqual(0, reset_metrics["prediction_count"])
        self.assertEqual(0, reset_metrics["total_prediction_time"])

    def test_model_export_import(self):
        """测试模型导出和导入"""
        # 创建要导出的模型
        model = Model("export_model")
        model.initialize(
            {"weights": [0.1, 0.2, 0.3], "bias": 0.5, "activation": "relu"}
        )

        # 设置元数据
        model.metadata = ModelMetadata(
            name="export_model", version="1.0.0", description="导出测试模型"
        )

        # 导出模型
        export_path = os.path.join(self.test_data_dir, "exported_model.json")
        model.export(export_path)

        # 清理当前模型
        self.model_manager.unload_all_models()

        # 导入模型
        imported_model = Model.import_model(export_path)

        # 验证导入的模型
        self.assertEqual("export_model", imported_model.name)
        self.assertEqual("1.0.0", imported_model.metadata.version)
        self.assertEqual("导出测试模型", imported_model.metadata.description)

        # 验证导入的参数
        self.assertEqual(
            [0.1, 0.2, 0.3], imported_model.get_parameter("weights"))
        self.assertEqual(0.5, imported_model.get_parameter("bias"))
        self.assertEqual("relu", imported_model.get_parameter("activation"))

    def test_model_auto_reload(self):
        """测试模型自动重新加载"""
        # 创建初始模型文件
        model_path = os.path.join(self.test_data_dir, "auto_reload_model.json")
        with open(model_path, "w") as f:
            json.dump(
                {
                    "name": "auto_reload_model",
                    "version": "1.0.0",
                    "parameters": {"value": 10},
                },
                f,
            )

        # 加载模型，启用自动重新加载
        model = self.model_manager.load_model(model_path, auto_reload=True)
        self.assertEqual(10, model.get_parameter("value"))

        # 修改模型文件
        time.sleep(0.1)  # 确保文件修改时间有变化
        with open(model_path, "w") as f:
            json.dump(
                {
                    "name": "auto_reload_model",
                    "version": "1.0.1",
                    "parameters": {"value": 20},
                },
                f,
            )

        # 触发重新加载检查
        self.model_manager.check_for_model_updates()

        # 获取更新后的模型
        updated_model = self.model_manager.get_model("auto_reload_model")

        # 验证模型已更新
        self.assertEqual("1.0.1", updated_model.version)
        self.assertEqual(20, updated_model.get_parameter("value"))

    def test_model_batch_registration(self):
        """测试批量模型注册"""
        # 创建多个模型
        models = [
            Model("batch_model_1"),
            Model("batch_model_2"),
            Model("batch_model_3"),
        ]

        # 初始化模型
        for i, model in enumerate(models):
            model.initialize({"index": i})

        # 批量注册模型
        self.model_manager.register_models(models)

        # 验证所有模型都已注册
        for i, model_name in enumerate(
            ["batch_model_1", "batch_model_2", "batch_model_3"]
        ):
            registered_model = self.model_manager.get_model(model_name)
            self.assertEqual(i, registered_model.get_parameter("index"))

    def test_model_dependencies(self):
        """测试模型依赖关系"""
        # 创建具有依赖关系的模型
        base_model = Model("base_model")
        base_model.initialize({"base_value": 5})

        dependent_model = Model("dependent_model")
        dependent_model.initialize({"multiplier": 2})
        dependent_model.add_dependency("base_model")

        # 设置依赖模型的预测函数
        def dependent_predict(inputs):
            # 获取基础模型
            base = self.model_manager.get_model("base_model")
            base_value = base.get_parameter("base_value")
            multiplier = dependent_model.get_parameter("multiplier")
            return {"result": inputs["value"] * multiplier + base_value}

        dependent_model.set_predict_function(dependent_predict)

        # 注册模型
        self.model_manager.register_model(base_model)
        self.model_manager.register_model(dependent_model)

        # 测试依赖模型预测
        result = dependent_model.predict({"value": 3})

        # 验证结果：3*2+5=11
        self.assertEqual(11, result["result"])

        # 测试模型依赖检查
        dependencies = self.model_manager.get_model_dependencies(
            "dependent_model")
        self.assertEqual(1, len(dependencies))
        self.assertEqual("base_model", dependencies[0])

        # 测试依赖图
        dependency_graph = self.model_manager.build_dependency_graph()
        self.assertIn("base_model", dependency_graph)
        self.assertIn("dependent_model", dependency_graph)
        self.assertEqual(0, len(dependency_graph["base_model"]))  # 无依赖
        self.assertEqual(1, len(dependency_graph["dependent_model"]))  # 一个依赖
        self.assertEqual("base_model", dependency_graph["dependent_model"][0])

    def test_model_versioned_dependencies(self):
        """测试模型版本化依赖关系"""
        # 创建注册表
        registry = ModelRegistry()

        # 注册基础模型的多个版本
        base_v1 = ModelMetadata(name="base", version="1.0.0")
        base_v2 = ModelMetadata(name="base", version="2.0.0")
        registry.register_model(base_v1, "path_to_base_v1")
        registry.register_model(base_v2, "path_to_base_v2")

        # 创建依赖于特定版本的模型
        dependent_v1 = ModelMetadata(name="dependent", version="1.0.0")
        dependent_v1.add_dependency("base", "1.0.0")  # 依赖base的1.0.0版本

        dependent_v2 = ModelMetadata(name="dependent", version="2.0.0")
        dependent_v2.add_dependency("base", "2.0.0")  # 依赖base的2.0.0版本

        # 注册依赖模型
        registry.register_model(dependent_v1, "path_to_dependent_v1")
        registry.register_model(dependent_v2, "path_to_dependent_v2")

        # 验证依赖关系
        deps_v1 = registry.get_model_dependencies("dependent", "1.0.0")
        self.assertEqual(1, len(deps_v1))
        self.assertEqual(("base", "1.0.0"), deps_v1[0])

        deps_v2 = registry.get_model_dependencies("dependent", "2.0.0")
        self.assertEqual(1, len(deps_v2))
        self.assertEqual(("base", "2.0.0"), deps_v2[0])

    def test_model_lazy_loading(self):
        """测试模型延迟加载"""
        # 创建需要延迟加载的模型
        lazy_model_path = os.path.join(self.test_data_dir, "lazy_model.json")
        with open(lazy_model_path, "w") as f:
            json.dump(
                {
                    "name": "lazy_model",
                    "version": "1.0.0",
                    "parameters": {"lazy_value": 100},
                },
                f,
            )

        # 注册模型，但使用延迟加载
        self.model_manager.register_model_path(
            "lazy_model", lazy_model_path, lazy_loading=True
        )

        # 验证模型已注册但未实际加载
        self.assertIn(
            "lazy_model", self.model_manager.get_registered_model_names())
        self.assertNotIn(
            "lazy_model", self.model_manager.get_loaded_model_names())

        # 访问模型，触发加载
        model = self.model_manager.get_model("lazy_model")

        # 验证模型现在已加载
        self.assertIn(
            "lazy_model", self.model_manager.get_loaded_model_names())
        self.assertEqual(100, model.get_parameter("lazy_value"))

    def test_model_incremental_update(self):
        """测试模型增量更新"""
        # 创建模型
        model = Model("incremental_model")
        model.initialize({"weights": [0.1, 0.2, 0.3], "bias": 0.5})

        # 注册模型
        self.model_manager.register_model(model)

        # 准备增量更新
        updates = {"weights[0]": 0.15, "bias": 0.6}  # 更新第一个权重  # 更新偏置

        # 执行增量更新
        self.model_manager.update_model_parameters(
            "incremental_model", updates)

        # 获取更新后的模型
        updated_model = self.model_manager.get_model("incremental_model")

        # 验证更新结果
        self.assertEqual([0.15, 0.2, 0.3],
                         updated_model.get_parameter("weights"))
        self.assertEqual(0.6, updated_model.get_parameter("bias"))

    def test_model_streaming_prediction(self):
        """测试模型流式预测"""
        # 创建支持流式预测的模型
        streaming_model = Model("streaming_model")

        # 设置模拟流式预测函数
        def stream_predict(inputs, callback):
            # 模拟分批次产生结果
            for i in range(5):
                time.sleep(0.01)  # 模拟处理时间
                callback({"chunk": i, "value": inputs["value"] * i})

        streaming_model.set_stream_predict_function(stream_predict)

        # 注册模型
        self.model_manager.register_model(streaming_model)

        # 收集流式预测结果
        results = []

        # 设置回调函数
        def collect_result(result):
            results.append(result)

        # 执行流式预测
        streaming_model.predict_stream({"value": 2}, collect_result)

        # 等待所有结果生成
        time.sleep(0.1)

        # 验证流式结果
        self.assertEqual(5, len(results))
        self.assertEqual({"chunk": 0, "value": 0}, results[0])  # 2*0=0
        self.assertEqual({"chunk": 1, "value": 2}, results[1])  # 2*1=2
        self.assertEqual({"chunk": 2, "value": 4}, results[2])  # 2*2=4
        self.assertEqual({"chunk": 3, "value": 6}, results[3])  # 2*3=6
        self.assertEqual({"chunk": 4, "value": 8}, results[4])  # 2*4=8

    def test_model_gpu_management(self):
        """测试模型GPU资源管理"""
        # 模拟GPU可用性检查
        with patch(
            "core.models.model_manager.ModelManager.check_gpu_availability"
        ) as mock_check:
            mock_check.return_value = True  # 假设有GPU可用

            # 设置GPU使用策略
            self.model_manager.set_gpu_policy(
                {
                    "use_gpu": True,
                    "memory_limit": 4096,  # 假设4GB限制
                    "preferred_models": ["high_priority_model"],
                }
            )

            # 创建模拟模型
            high_priority = Model("high_priority_model")
            high_priority.gpu_memory_required = 3000  # 需要3GB GPU内存

            low_priority = Model("low_priority_model")
            low_priority.gpu_memory_required = 2000  # 需要2GB GPU内存

            # 注册高优先级模型
            self.model_manager.register_model(high_priority)

            # 验证GPU分配
            self.assertTrue(high_priority.use_gpu)
            self.assertEqual(3000, self.model_manager.get_gpu_memory_usage())

            # 尝试注册低优先级模型（会导致超出限制）
            # 由于低优先级，应该被分配到CPU
            self.model_manager.register_model(low_priority)

            # 验证低优先级模型使用CPU
            self.assertFalse(low_priority.use_gpu)
            self.assertEqual(
                3000, self.model_manager.get_gpu_memory_usage()
            )  # GPU内存使用不变

    def test_model_fallback(self):
        """测试模型回退机制"""
        # 创建主模型和回退模型
        primary_model = Model("primary_model")
        primary_model.set_predict_function(
            lambda x: {"result": x["value"] * 2})

        fallback_model = Model("fallback_model")
        fallback_model.set_predict_function(
            lambda x: {"result": x["value"] + 1})

        # 注册模型
        self.model_manager.register_model(primary_model)
        self.model_manager.register_model(fallback_model)

        # 配置回退关系
        self.model_manager.set_fallback_model(
            "primary_model", "fallback_model")

        # 正常预测
        result = self.model_manager.predict_with_fallback(
            "primary_model", {"value": 5})
        self.assertEqual(10, result["result"])  # 5*2=10

        # 模拟主模型失败
        def failing_predict(x):
            raise RuntimeError("模拟预测失败")

        primary_model.set_predict_function(failing_predict)

        # 带回退的预测应该使用回退模型
        result = self.model_manager.predict_with_fallback(
            "primary_model", {"value": 5})
        self.assertEqual(6, result["result"])  # 5+1=6（回退模型结果）

    def test_model_warm_up(self):
        """测试模型预热功能"""
        # 创建需要预热的模型
        warm_up_model = Model("warm_up_model")

        # 初始指标
        warm_up_time = []

        # 设置预热效果明显的预测函数
        def predict_with_warmup(inputs):
            # 首次调用较慢，后续调用变快
            if not hasattr(predict_with_warmup, "warmed_up"):
                time.sleep(0.05)  # 模拟首次较慢
                predict_with_warmup.warmed_up = True
                warm_up_time.append(time.time())
            return {"result": inputs["value"] * 2}

        warm_up_model.set_predict_function(predict_with_warmup)

        # 注册模型
        start_time = time.time()
        self.model_manager.register_model(warm_up_model, warm_up=True)

        # 检查模型是否已预热
        self.assertTrue(hasattr(predict_with_warmup, "warmed_up"))

        # 验证预热发生在注册期间
        self.assertEqual(1, len(warm_up_time))
        self.assertLess(start_time, warm_up_time[0])
        self.assertLess(warm_up_time[0], time.time())

        # 预测应该立即使用预热后的模型
        start_time = time.time()
        result = warm_up_model.predict({"value": 3})
        predict_time = time.time() - start_time

        # 验证结果正确且速度快（已预热）
        self.assertEqual(6, result["result"])  # 3*2=6
        self.assertLess(predict_time, 0.01)  # 应该明显快于预热时间

    def test_model_quantization(self):
        """测试模型量化功能"""
        # 创建原始模型（模拟使用浮点参数）
        original_model = Model("original_model")
        original_model.initialize(
            {
                "weights": np.array([0.123, 0.456, 0.789], dtype=np.float32),
                "bias": np.array([0.012, 0.345], dtype=np.float32),
            }
        )

        # 模拟量化器
        class MockQuantizer:
            def quantize(self, model):
                # 简单的量化：将float32转为int8，然后缩放
                quantized = Model(f"{model.name}_quantized")

                # 量化权重（例如使用简单的线性量化）
                weights = model.get_parameter("weights")
                scale = 127.0 / max(abs(weights.max()), abs(weights.min()))
                quantized_weights = np.array(
                    np.round(weights * scale), dtype=np.int8)

                # 量化偏置
                bias = model.get_parameter("bias")
                scale_bias = 127.0 / max(abs(bias.max()), abs(bias.min()))
                quantized_bias = np.array(
                    np.round(bias * scale_bias), dtype=np.int8)

                # 存储量化参数和比例因子
                quantized.initialize(
                    {
                        "weights": quantized_weights,
                        "bias": quantized_bias,
                        "weight_scale": scale,
                        "bias_scale": scale_bias,
                    }
                )

                return quantized

        # 执行量化
        quantizer = MockQuantizer()
        quantized_model = quantizer.quantize(original_model)

        # 验证量化结果
        self.assertEqual("original_model_quantized", quantized_model.name)
        self.assertEqual(
            np.int8, quantized_model.get_parameter("weights").dtype)
        self.assertEqual(np.int8, quantized_model.get_parameter("bias").dtype)

        # 检查内存占用减少
        original_size = (
            original_model.get_parameter("weights").nbytes
            + original_model.get_parameter("bias").nbytes
        )
        quantized_size = (
            quantized_model.get_parameter("weights").nbytes
            + quantized_model.get_parameter("bias").nbytes
        )

        # 量化后的大小应该小于原始大小（float32->int8）
        self.assertLess(quantized_size, original_size)
        self.assertEqual(
            quantized_size, original_size // 4
        )  # float32(4字节) -> int8(1字节)


def run_tests():
    """运行所有模型组件测试"""
    unittest.main()


if __name__ == "__main__":
    run_tests()