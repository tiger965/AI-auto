"""
核心功能示例模块

本模块展示如何使用项目的核心功能模块，包括：
1. 模型加载与推理
2. 数据预处理流程
3. 结果后处理
4. 自定义配置使用
5. 扩展模块的使用

运行环境要求：
- Python 3.8+
- 已安装依赖库（torch, numpy, pandas等）
- 模型文件已下载到项目的models目录

预期输出：
各示例将展示核心功能的使用方法和结果
"""

from myproject.exceptions import ModelError, DataError
from myproject.utils import config, logging
from myproject.core import model, data_processor, post_processor
import os
import sys
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径，以便导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目中的核心模块（根据实际项目结构调整导入路径）

# 初始化日志
logger = logging.get_logger(__name__)


def run_all():
    """运行所有核心功能示例"""
    print("开始运行核心功能示例...")

    # 运行模型推理示例
    run_model_inference_example()

    # 运行数据预处理示例
    run_data_preprocessing_example()

    # 运行结果后处理示例
    run_post_processing_example()

    # 运行配置示例
    run_configuration_example()

    # 运行扩展模块示例
    run_extension_example()

    print("核心功能示例运行完成！")


def run_model_inference_example():
    """
    模型加载与推理示例

    展示如何加载模型并执行推理
    """
    print("\n--- 模型加载与推理示例 ---")

    # 1. 加载模型配置
    model_config = config.ModelConfig(
        model_name="gpt-mini",
        model_path="./models/gpt-mini",
        device="cuda" if model.is_cuda_available() else "cpu",
        precision="float16",
        max_length=100,
    )

    print(f"加载模型: {model_config.model_name}")
    print(f"运行设备: {model_config.device}")

    try:
        # 2. 初始化模型
        ai_model = model.Model(model_config)

        # 3. 执行基础推理
        input_text = "人工智能如何改变我们的生活?"
        print(f"\n执行基础推理, 输入: '{input_text}'")

        result = ai_model.generate(
            input_text, max_tokens=50, temperature=0.7, top_p=0.9
        )

        print(f"生成结果: {result.text}")
        print(f"生成耗时: {result.generation_time:.3f}秒")

        # 4. 批量推理示例
        input_texts = [
            "深度学习的核心原理是什么?",
            "机器学习与传统编程的区别在哪里?",
            "强化学习在实际场景中的应用有哪些?",
        ]

        print(f"\n执行批量推理, 共{len(input_texts)}条输入")
        batch_results = ai_model.batch_generate(
            input_texts, max_tokens=30, temperature=0.5, batch_size=2  # 每批处理数量
        )

        for i, res in enumerate(batch_results):
            print(f"\n批量结果 {i+1}:")
            print(f"输入: '{input_texts[i]}'")
            print(f"输出: '{res.text}'")

        # 5. 流式推理示例
        print("\n执行流式推理示例:")
        input_text = "请写一首关于技术创新的短诗"

        print(f"输入: '{input_text}'")
        print("流式输出:")

        # 模拟流式输出
        for token in ai_model.stream_generate(input_text, max_tokens=50):
            print(token, end="", flush=True)
            time.sleep(0.1)  # 模拟生成延迟

        print("\n流式推理完成")

        # 6. 模型性能监控示例
        print("\n模型性能监控:")
        performance = ai_model.get_performance_stats()
        print(f"平均推理时间: {performance['avg_inference_time']:.3f}秒/请求")
        print(f"吞吐量: {performance['throughput']:.2f}令牌/秒")
        print(f"内存使用: {performance['memory_usage']:.2f}MB")

    except ModelError as e:
        print(f"模型错误: {e}")
    except Exception as e:
        print(f"未预期错误: {e}")

    # 7. 释放模型资源
    if "ai_model" in locals():
        ai_model.unload()
        print("\n已释放模型资源")


def run_data_preprocessing_example():
    """
    数据预处理示例

    展示如何使用数据预处理模块处理不同类型的输入
    """
    print("\n--- 数据预处理示例 ---")

    try:
        # 1. 创建数据处理器
        processor = data_processor.DataProcessor()

        # 2. 文本数据预处理
        text_data = "这是一个包含特殊字符的文本!@#$%^，需要进行规范化处理。"
        print(f"\n文本预处理前: '{text_data}'")

        processed_text = processor.process_text(
            text_data, lowercase=True, remove_special_chars=True, max_length=100
        )

        print(f"文本预处理后: '{processed_text}'")

        # 3. 序列数据预处理（例如时间序列）
        sequence_data = np.random.randn(10)  # 模拟时间序列数据
        print(f"\n序列数据预处理前: {sequence_data}")

        normalized_sequence = processor.normalize_sequence(
            sequence_data, method="z-score"  # 使用Z-score标准化
        )

        print(f"序列数据预处理后: {normalized_sequence}")
        print(
            f"均值: {np.mean(normalized_sequence):.4f}, 标准差: {np.std(normalized_sequence):.4f}"
        )

        # 4. 分词示例
        text = "人工智能在自然语言处理领域取得了显著进展"
        print(f"\n分词前文本: '{text}'")

        tokens = processor.tokenize(text)
        print(f"分词结果: {tokens}")
        print(f"词元数量: {len(tokens)}")

        # 5. 批量数据处理
        batch_texts = [
            "第一条示例文本",
            "第二条较长的示例文本，包含更多的词语和标点符号。",
            "第三条文本",
        ]

        print(f"\n批量处理{len(batch_texts)}条文本")
        processed_batch = processor.batch_process_text(
            batch_texts,
            lowercase=True,
            remove_punctuation=True,
            padding=True,
            max_length=10,
        )

        for i, (original, processed) in enumerate(zip(batch_texts, processed_batch)):
            print(f"原始{i+1}: '{original}'")
            print(f"处理后{i+1}: '{processed}'")

        # 6. 数据增强示例
        text_for_augmentation = "人工智能技术正在快速发展"
        print(f"\n数据增强前: '{text_for_augmentation}'")

        augmented_texts = processor.augment_text(
            text_for_augmentation,
            num_samples=3,
            methods=["synonym_replacement", "random_insertion", "random_swap"],
        )

        print("数据增强后:")
        for i, aug_text in enumerate(augmented_texts):
            print(f"增强样本{i+1}: '{aug_text}'")

    except DataError as e:
        print(f"数据处理错误: {e}")
    except Exception as e:
        print(f"未预期错误: {e}")


def run_post_processing_example():
    """
    结果后处理示例

    展示如何使用后处理模块对模型输出进行处理
    """
    print("\n--- 结果后处理示例 ---")

    try:
        # 1. 创建后处理器
        processor = post_processor.PostProcessor()

        # 2. 基础文本清理
        raw_output = "这是模型生成的原始输出，可能包含[MASK]或<eos>等特殊标记，以及一些\n\n不必要的空行。"
        print(f"\n后处理前: '{raw_output}'")

        cleaned_output = processor.clean_text(
            raw_output, remove_special_tokens=True, fix_whitespace=True
        )

        print(f"基础清理后: '{cleaned_output}'")

        # 3. 格式化JSON输出
        json_output = """{"name": "AI助手", "responses": ["你好，我能帮你什么?", "需要更多信息"], "confidence": 0.92}"""
        print(f"\nJSON格式化前: '{json_output}'")

        parsed_json = processor.parse_and_format_json(json_output)
        print(f"JSON格式化后:")
        for key, value in parsed_json.items():
            print(f"  {key}: {value}")

        # 4. 情感分析后处理
        text_for_sentiment = "这个产品的设计非常出色，但价格有点贵"
        print(f"\n情感分析文本: '{text_for_sentiment}'")

        sentiment = processor.analyze_sentiment(text_for_sentiment)
        print(f"情感分析结果: {sentiment['label']}, 分数: {sentiment['score']:.2f}")

        # 5. 提取关键信息
        text_with_info = """
        订单详情：
        客户名称：张三
        订单号：ORD20230501
        商品列表：AI开发套件，高性能计算服务
        总金额：1299元
        """
        print(f"\n从文本提取关键信息: '{text_with_info}'")

        extracted_info = processor.extract_structured_data(
            text_with_info,
            patterns={
                "customer_name": r"客户名称：(.+?)\n",
                "order_id": r"订单号：(.+?)\n",
                "items": r"商品列表：(.+?)\n",
                "amount": r"总金额：(.+?)元",
            },
        )

        print("提取的结构化数据:")
        for key, value in extracted_info.items():
            print(f"  {key}: {value}")

        # 6. 结果排名和过滤
        search_results = [
            {"text": "人工智能基础教程", "score": 0.85},
            {"text": "人工智能高级应用", "score": 0.92},
            {"text": "机器学习导论", "score": 0.78},
            {"text": "深度学习实践", "score": 0.88},
            {"text": "无关的结果", "score": 0.35},
        ]
        print("\n结果排名和过滤前:")
        for result in search_results:
            print(f"  {result['text']} (分数: {result['score']})")

        filtered_results = processor.rank_and_filter(
            search_results, score_key="score", min_score=0.7, max_results=3
        )

        print("排名和过滤后的前3个高分结果:")
        for result in filtered_results:
            print(f"  {result['text']} (分数: {result['score']})")

    except Exception as e:
        print(f"后处理错误: {e}")


def run_configuration_example():
    """
    配置示例

    展示如何加载、修改和使用配置
    """
    print("\n--- 配置示例 ---")

    # 1. 从默认位置加载配置
    print("从默认位置加载配置")
    default_config = config.load_config()

    # 2. 从指定文件加载配置
    config_path = "./config/custom_config.yaml"
    print(f"从指定路径加载配置: {config_path}")
    try:
        custom_config = config.load_config(config_path)
        print("成功加载自定义配置")
    except FileNotFoundError:
        print(f"配置文件不存在: {config_path}, 将使用默认配置")
        custom_config = default_config

    # 3. 查看配置内容
    print("\n配置内容概览:")
    print(f"模型名称: {custom_config.model.name}")
    print(f"最大序列长度: {custom_config.model.max_length}")
    print(f"批处理大小: {custom_config.training.batch_size}")

    # 4. 修改配置
    print("\n修改配置:")
    original_batch_size = custom_config.training.batch_size
    custom_config.training.batch_size = 16
    print(
        f"批处理大小从 {original_batch_size} 修改为 {custom_config.training.batch_size}"
    )

    # 5. 保存修改后的配置
    new_config_path = "./config/modified_config.yaml"
    print(f"将修改后的配置保存到: {new_config_path}")
    config.save_config(custom_config, new_config_path)

    # 6. 使用环境变量覆盖配置
    print("\n使用环境变量覆盖配置:")
    # 模拟设置环境变量
    os.environ["MYPROJECT_MODEL_DEVICE"] = "cpu"
    os.environ["MYPROJECT_LOGGING_LEVEL"] = "DEBUG"

    # 重新加载配置，环境变量会覆盖文件配置
    env_config = config.load_config(use_env=True)
    print(f"设备配置(从环境变量): {env_config.model.device}")
    print(f"日志级别(从环境变量): {env_config.logging.level}")

    # 7. 创建特定模块的配置
    print("\n创建特定模块的配置:")
    data_config = config.DataConfig(
        input_dir="./data/raw",
        output_dir="./data/processed",
        cache_dir="./data/cache",
        max_samples=1000,
        validation_split=0.2,
    )

    print(f"数据输入目录: {data_config.input_dir}")
    print(f"验证集划分比例: {data_config.validation_split}")

    # 8. 配置合并示例
    print("\n配置合并示例:")
    base_config = config.ModelConfig(
        name="base-model", path="./models/base", max_length=512
    )

    override_config = {"name": "custom-model", "precision": "float16"}

    merged_config = config.merge_configs(base_config, override_config)
    print("合并后的配置:")
    print(f"名称: {merged_config.name}")  # 从override_config
    print(f"路径: {merged_config.path}")  # 从base_config
    print(f"精度: {merged_config.precision}")  # 从override_config
    print(f"最大长度: {merged_config.max_length}")  # 从base_config


def run_extension_example():
    """
    扩展模块示例

    展示如何使用和创建项目的扩展功能
    """
    print("\n--- 扩展模块示例 ---")

    # 导入扩展模块
    from myproject.extensions import visualization, metrics, export

    # 1. 使用可视化扩展
    print("\n使用可视化扩展:")

    # 创建示例数据
    labels = ["类别A", "类别B", "类别C", "类别D"]
    values = [25, 40, 30, 15]

    # 生成可视化图表
    chart = visualization.create_chart(
        chart_type="bar",
        data={"labels": labels, "values": values},
        title="示例分类结果",
        x_label="类别",
        y_label="数量",
    )

    # 显示和保存图表
    output_path = "./output/example_chart.png"
    visualization.save_chart(chart, output_path)
    print(f"图表已保存到: {output_path}")

    # 2. 使用评估指标扩展
    print("\n使用评估指标扩展:")

    # 模拟真实标签和预测结果
    y_true = [0, 1, 2, 0, 1, 2, 0, 1, 2]
    y_pred = [0, 2, 1, 0, 1, 2, 0, 1, 1]

    # 计算各种指标
    accuracy = metrics.calculate_accuracy(y_true, y_pred)
    precision = metrics.calculate_precision(y_true, y_pred, average="macro")
    recall = metrics.calculate_recall(y_true, y_pred, average="macro")
    f1 = metrics.calculate_f1(y_true, y_pred, average="macro")

    print(f"准确率: {accuracy:.4f}")
    print(f"精确率: {precision:.4f}")
    print(f"召回率: {recall:.4f}")
    print(f"F1分数: {f1:.4f}")

    # 生成分类报告
    report = metrics.classification_report(y_true, y_pred, labels=[0, 1, 2])
    print("\n分类报告:")
    print(report)

    # 3. 使用导出扩展
    print("\n使用导出扩展:")

    # 准备示例结果数据
    results = [
        {"id": 1, "input": "示例输入1", "output": "示例输出1", "score": 0.92},
        {"id": 2, "input": "示例输入2", "output": "示例输出2", "score": 0.87},
        {"id": 3, "input": "示例输入3", "output": "示例输出3", "score": 0.95},
    ]

    # 导出为CSV
    csv_path = "./output/example_results.csv"
    export.to_csv(results, csv_path)
    print(f"结果已导出为CSV: {csv_path}")

    # 导出为JSON
    json_path = "./output/example_results.json"
    export.to_json(results, json_path)
    print(f"结果已导出为JSON: {json_path}")

    # 4. 创建自定义扩展示例
    print("\n创建自定义扩展示例:")

    # 定义一个简单的自定义扩展类
    class CustomAnalyzer:
        """自定义分析器扩展"""

        def __init__(self, name="CustomAnalyzer"):
            self.name = name
            print(f"初始化自定义扩展: {name}")

        def analyze(self, data):
            """分析数据并返回结果"""
            if not data:
                return {"error": "空数据"}

            result = {
                "count": len(data),
                "summary": self._summarize(data),
                "timestamp": time.time(),
            }

            return result

        def _summarize(self, data):
            """内部方法：生成数据摘要"""
            if isinstance(data, list):
                return f"{len(data)}个项目的列表"
            elif isinstance(data, dict):
                return f"包含{len(data)}个键的字典"
            else:
                return f"{type(data).__name__}类型的数据"

    # 使用自定义扩展
    sample_data = ["项目1", "项目2", "项目3", "项目4"]
    analyzer = CustomAnalyzer("示例分析器")
    analysis_result = analyzer.analyze(sample_data)

    print("自定义扩展分析结果:")
    for key, value in analysis_result.items():
        print(f"  {key}: {value}")

    # 5. 扩展注册和发现机制示例
    print("\n扩展注册和发现机制示例:")

    # 模拟扩展注册表
    extension_registry = {}

    def register_extension(extension_class, name=None):
        """注册扩展到注册表"""
        ext_name = name or extension_class.__name__
        extension_registry[ext_name] = extension_class
        print(f"已注册扩展: {ext_name}")

    def discover_extensions():
        """发现所有已注册的扩展"""
        print(f"发现了{len(extension_registry)}个已注册扩展:")
        for name in extension_registry:
            print(f"  - {name}")

    # 注册几个扩展
    register_extension(CustomAnalyzer)
    register_extension(CustomAnalyzer, "TextAnalyzer")

    # 发现扩展
    discover_extensions()

    # 使用已注册的扩展
    ext_class = extension_registry.get("TextAnalyzer")
    if ext_class:
        print("\n使用已注册的TextAnalyzer扩展:")
        ext_instance = ext_class()
        result = ext_instance.analyze(["测试"])
        print(f"分析结果: {result}")


if __name__ == "__main__":
except Exception as e:
    print(f"错误: {str(e)}")
    # 运行所有核心功能示例
    run_all()