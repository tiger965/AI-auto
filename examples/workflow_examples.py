"""
工作流示例模块

本模块展示完整的AI自动化工作流程示例，将各个功能模块组合起来完成端到端任务，包括：
1. 文本分类工作流
2. 数据分析工作流
3. 内容生成工作流
4. 异常处理工作流
5. 自定义工作流构建

运行环境要求：
- Python 3.8+
- 已安装所有依赖库
- 配置文件正确设置
- 模型文件已下载到项目模型目录

预期输出：
展示完整工作流的运行过程和结果
"""

import os
import sys
import time
import json
import logging
import pandas as pd
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径，以便导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目中的模块（根据实际项目结构调整导入路径）
from myproject.core import model, data_processor, post_processor
from myproject.api import client
from myproject.utils import config, file_utils
from myproject.workflow import workflow_manager, task
from myproject.exceptions import WorkflowError

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_all():
    """运行所有工作流示例"""
    print("开始运行工作流示例...")
    
    # 运行文本分类工作流示例
    run_text_classification_workflow()
    
    # 运行数据分析工作流示例
    run_data_analysis_workflow()
    
    # 运行内容生成工作流示例
    run_content_generation_workflow()
    
    # 运行错误处理工作流示例
    run_error_handling_workflow()
    
    # 运行自定义工作流构建示例
    run_custom_workflow_builder_example()
    
    print("工作流示例运行完成！")

def run_text_classification_workflow():
    """
    文本分类工作流示例
    
    展示如何构建一个完整的文本分类流程
    """
    print("\n--- 文本分类工作流示例 ---")
    
    try:
        # 1. 定义工作流配置
        workflow_config = {
            "name": "text_classification_workflow",
            "description": "文本分类完整工作流",
            "model": {
                "name": "text-classifier",
                "path": "./models/text-classifier",
                "max_length": 256
            },
            "data": {
                "input_format": "csv",
                "text_column": "text",
                "batch_size": 16
            },
            "output": {
                "format": "json",
                "path": "./output/classification_results.json"
            }
        }
        
        print("初始化文本分类工作流")
        
        # 2. 创建工作流管理器
        workflow = workflow_manager.WorkflowManager(workflow_config)
        
        # 3. 定义和添加工作流任务
        
        # 3.1 准备主题任务
        @workflow.task(name="prepare_topic")
        def prepare_generation_topic():
            print("执行主题准备任务...")
            
            # 模拟输入主题和关键词
            topic_data = {
                "main_topic": "人工智能应用",
                "subtopics": ["自然语言处理", "计算机视觉", "推荐系统"],
                "keywords": ["深度学习", "神经网络", "机器学习", "大模型", "自动化"],
                "target_audience": "技术爱好者和企业决策者",
                "tone": "专业但易于理解"
            }
            
            print(f"主题准备完成: {topic_data['main_topic']}")
            return topic_data
        
        # 3.2 内容生成任务
        @workflow.task(name="generate_content", depends_on=["prepare_topic"])
        def generate_content(topic_data):
            print("执行内容生成任务...")
            
            # 模拟内容生成模型
            print(f"使用模型 {workflow_config['model']['name']} 生成内容")
            print(f"主题: {topic_data['main_topic']}")
            print(f"子主题: {', '.join(topic_data['subtopics'])}")
            print(f"生成参数: 温度={workflow_config['generation']['temperature']}, top_p={workflow_config['generation']['top_p']}")
            
            # 为不同内容类型生成内容
            generated_contents = {}
            
            # 1. 生成文章内容
            article_content = f"""
            # {topic_data['main_topic']}：技术与应用

            在当今数字化时代，{topic_data['main_topic']}正在各个领域掀起变革浪潮。本文将探讨三个关键领域的最新进展：{topic_data['subtopics'][0]}、{topic_data['subtopics'][1]}和{topic_data['subtopics'][2]}。

            ## {topic_data['subtopics'][0]}
            {topic_data['subtopics'][0]}是{topic_data['main_topic']}中最活跃的研究领域之一。借助{topic_data['keywords'][0]}和{topic_data['keywords'][1]}技术，现代{topic_data['subtopics'][0]}系统能够理解和生成人类语言，为智能客服、自动翻译和内容创作等应用提供强大支持。

            ## {topic_data['subtopics'][1]}
            {topic_data['subtopics'][1]}技术让计算机拥有了"看"的能力。通过{topic_data['keywords'][1]}技术，计算机可以识别图像中的物体、人脸和场景，广泛应用于安防监控、医疗诊断和自动驾驶等领域。

            ## {topic_data['subtopics'][2]}
            随着电子商务和内容平台的兴起，{topic_data['subtopics'][2]}变得愈发重要。基于{topic_data['keywords'][2]}的{topic_data['subtopics'][2]}能够分析用户行为数据，为用户提供个性化的产品和内容推荐，提升用户体验和平台效益。

            # 未来展望
            随着{topic_data['keywords'][3]}的快速发展，我们预计未来{topic_data['main_topic']}将向更高精度、更强解释性和更广应用场景方向发展，为企业和社会创造更大价值。
            """
            generated_contents["article"] = article_content
            
            # 2. 生成社交媒体内容
            social_media_content = f"""
            📱 #{topic_data['keywords'][0]} #{topic_data['keywords'][3]} #{topic_data['main_topic'].replace(' ', '')}

            🔍 想了解{topic_data['main_topic']}如何改变我们的世界吗？
            
            🚀 从{topic_data['subtopics'][0]}到{topic_data['subtopics'][1]}，再到{topic_data['subtopics'][2]}，AI正在各个领域掀起革命！
            
            💡 无论是提升效率还是创造新可能，{topic_data['main_topic']}都将是未来技术发展的核心驱动力。
            
            👉 点击链接了解更多关于{topic_data['main_topic']}的最新研究和应用案例！#技术创新
            """
            generated_contents["social_media"] = social_media_content
            
            # 3. 生成邮件营销内容
            email_content = f"""
            主题: 探索{topic_data['main_topic']}为您的业务带来的革命性变化
            
            尊敬的决策者：
            
            希望这封邮件找到您一切安好。
            
            在当今竞争激烈的商业环境中，{topic_data['main_topic']}正在成为企业保持竞争力的关键因素。我们团队专注于{topic_data['subtopics'][0]}、{topic_data['subtopics'][1]}和{topic_data['subtopics'][2]}等领域的前沿技术开发，帮助企业实现数字化转型。
            
            我们的解决方案基于最新的{topic_data['keywords'][0]}和{topic_data['keywords'][3]}技术，能够帮助您：
            
            - 优化业务流程，提高运营效率
            - 增强客户体验，提高客户满意度
            - 挖掘数据价值，支持精准决策
            
            如果您有兴趣了解更多关于{topic_data['main_topic']}如何为您的业务创造价值，请回复此邮件或致电我们，我们很乐意安排一次深入交流。
            
            期待您的回音！
            
            此致
            
            AI解决方案团队
            """
            generated_contents["email"] = email_content
            
            print(f"成功生成{len(generated_contents)}种类型的内容")
            return generated_contents
        
        # 3.3 内容优化任务
        @workflow.task(name="optimize_content", depends_on=["generate_content"])
        def optimize_content(contents):
            print("执行内容优化任务...")
            
            optimization_results = {}
            
            for content_type, content in contents.items():
                print(f"优化{content_type}类型内容...")
                
                # 模拟内容优化过程
                optimized_content = content
                optimization_metrics = {}
                
                # 1. 可读性检查
                if workflow_config["optimization"]["readability_check"]:
                    # 模拟可读性分析
                    readability_score = 75 + (hash(content) % 15)  # 生成65-90之间的模拟分数
                    optimization_metrics["readability"] = readability_score
                    print(f"  可读性分数: {readability_score}")
                    
                    # 基于分数进行优化（这里只是示例）
                    if readability_score < 70:
                        print("  应用可读性优化：简化句子结构，减少专业术语")
                        # 实际项目中会有真实的优化逻辑
                
                # 2. 情感分析
                if workflow_config["optimization"]["sentiment_analysis"]:
                    # 模拟情感分析
                    sentiment_score = 0.6 + (hash(content) % 5) / 10  # 生成0.6-1.0之间的模拟分数
                    sentiment_label = "积极" if sentiment_score > 0.7 else "中性"
                    optimization_metrics["sentiment"] = {
                        "score": sentiment_score,
                        "label": sentiment_label
                    }
                    print(f"  情感分析: {sentiment_label} (分数: {sentiment_score:.2f})")
                
                # 3. 语法检查
                if workflow_config["optimization"]["grammar_check"]:
                    # 模拟语法检查
                    grammar_errors = abs(hash(content) % 5)  # 生成0-4之间的模拟错误数
                    optimization_metrics["grammar_errors"] = grammar_errors
                    print(f"  语法错误数: {grammar_errors}")
                    
                    if grammar_errors > 0:
                        print(f"  修复了{grammar_errors}个语法错误")
                        # 实际项目中会有真实的语法修复逻辑
                
                # 存储优化结果
                optimization_results[content_type] = {
                    "original": content,
                    "optimized": optimized_content,
                    "metrics": optimization_metrics
                }
            
            print("内容优化完成")
            return optimization_results
        
        # 3.4 内容导出任务
        @workflow.task(name="export_content", depends_on=["optimize_content"])
        def export_content(optimization_results):
            print("执行内容导出任务...")
            
            # 创建输出目录
            output_dir = "./output/generated_content/"
            os.makedirs(output_dir, exist_ok=True)
            
            exported_files = []
            
            # 导出各类型内容
            for content_type, result in optimization_results.items():
                # 确定文件名和格式
                if content_type == "article":
                    file_path = os.path.join(output_dir, "article.md")
                    content = result["optimized"]
                elif content_type == "social_media":
                    file_path = os.path.join(output_dir, "social_media_post.txt")
                    content = result["optimized"]
                elif content_type == "email":
                    file_path = os.path.join(output_dir, "marketing_email.txt")
                    content = result["optimized"]
                else:
                    file_path = os.path.join(output_dir, f"{content_type}_content.txt")
                    content = result["optimized"]
                
                # 写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"已导出{content_type}内容到: {file_path}")
                exported_files.append(file_path)
            
            # 生成摘要报告
            summary_path = os.path.join(output_dir, "generation_summary.json")
            
            summary = {
                "generation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "content_types": list(optimization_results.keys()),
                "optimization_metrics": {
                    content_type: result["metrics"]
                    for content_type, result in optimization_results.items()
                },
                "exported_files": exported_files
            }
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)
            
            print(f"已生成内容摘要报告: {summary_path}")
            return {
                "exported_files": exported_files,
                "summary_path": summary_path
            }
        
        # 4. 执行工作流
        print("\n开始执行内容生成工作流...")
        result = workflow.run()
        
        # 5. 总结工作流执行结果
        print("\n内容生成工作流执行完成")
        print(f"总执行时间: {workflow.execution_time:.2f}秒")
        print(f"任务执行顺序: {', '.join(workflow.execution_order)}")
        print(f"生成的内容类型: {', '.join(list(optimization_results.keys()))}")
        print(f"导出的文件数量: {len(result['exported_files'])}")
        print(f"摘要报告路径: {result['summary_path']}")
        
    except WorkflowError as e:
        print(f"工作流错误: {e}")
    except Exception as e:
        print(f"未预期错误: {e}")

def run_error_handling_workflow():
    """
    错误处理工作流示例
    
    展示如何在工作流中处理各种异常情况
    """
    print("\n--- 错误处理工作流示例 ---")
    
    try:
        # 1. 定义工作流配置
        workflow_config = {
            "name": "error_handling_workflow",
            "description": "错误处理示例工作流",
            "error_handling": {
                "max_retries": 3,
                "retry_delay": 2,  # 秒
                "fallback_enabled": True
            }
        }
        
        print("初始化错误处理工作流")
        
        # 2. 创建工作流管理器
        workflow = workflow_manager.WorkflowManager(workflow_config)
        
        # 3. 定义和添加工作流任务
        
        # 3.1 正常任务
        @workflow.task(name="normal_task")
        def run_normal_task():
            print("执行正常任务...")
            
            # 模拟正常任务处理
            data = {"status": "success", "value": 42}
            
            print(f"正常任务完成: {data}")
            return data
        
        # 3.2 有时会失败的任务
        @workflow.task(name="intermittent_failure_task", depends_on=["normal_task"])
        def run_intermittent_failure(input_data):
            print("执行间歇性失败任务...")
            
            # 获取最大重试次数
            max_retries = workflow_config["error_handling"]["max_retries"]
            
            # 模拟任务有时会失败
            # 在实际应用中，这里可能是网络请求、数据库操作等可能会失败的操作
            
            # 当前重试次数（任务状态变量）
            if not hasattr(run_intermittent_failure, "retry_count"):
                run_intermittent_failure.retry_count = 0
            
            # 模拟失败情况
            if run_intermittent_failure.retry_count < 2:  # 前两次失败，第三次成功
                run_intermittent_failure.retry_count += 1
                failure_chance = 1.0  # 100%失败
            else:
                failure_chance = 0.0  # 0%失败（必定成功）
            
            # 根据失败概率决定是否抛出异常
            if random.random() < failure_chance:
                error_message = "模拟的间歇性任务失败"
                print(f"任务失败: {error_message} (重试 {run_intermittent_failure.retry_count}/{max_retries})")
                
                # 根据重试次数调整异常类型
                if run_intermittent_failure.retry_count == 1:
                    raise ConnectionError(error_message)  # 模拟连接错误
                else:
                    raise TimeoutError(error_message)  # 模拟超时错误
            
            # 任务成功
            result = {
                "processed_value": input_data["value"] * 2,
                "retry_count": run_intermittent_failure.retry_count
            }
            
            print(f"间歇性任务完成: {result}, 重试次数: {run_intermittent_failure.retry_count}")
            return result
        
        # 3.3 始终会失败的任务及其备用任务
        @workflow.task(name="always_failing_task", depends_on=["intermittent_failure_task"])
        def run_always_failing_task(input_data):
            print("执行始终失败任务...")
            
            # 模拟始终会失败的任务
            error_message = "始终失败的任务错误"
            print(f"任务失败: {error_message}")
            
            # 抛出异常
            raise RuntimeError(error_message)
        
        # 备用任务: 当主任务失败时执行
        @workflow.task(name="fallback_task", fallback_for="always_failing_task")
        def run_fallback_task(input_data):
            print("执行备用任务...")
            
            # 备用处理逻辑
            fallback_result = {
                "fallback_value": input_data["processed_value"] / 2,
                "is_fallback": True
            }
            
            print(f"备用任务完成: {fallback_result}")
            return fallback_result
        
        # 3.4 条件分支任务
        @workflow.task(name="conditional_task", depends_on=["always_failing_task", "fallback_task"])
        def run_conditional_task(failing_task_result=None, fallback_task_result=None):
            print("执行条件分支任务...")
            
            # 检查哪个前置任务成功完成了
            if failing_task_result is not None:
                # 始终失败的任务竟然成功了
                result_source = "always_failing_task"
                base_value = failing_task_result
            elif fallback_task_result is not None:
                # 使用备用任务的结果
                result_source = "fallback_task"
                base_value = fallback_task_result
            else:
                # 两个任务都失败了
                error_message = "所有前置任务都失败了"
                print(f"条件分支任务失败: {error_message}")
                raise ValueError(error_message)
            
            # 根据结果来源执行不同的逻辑
            if result_source == "always_failing_task":
                result = {
                    "source": result_source,
                    "final_value": base_value["processed_value"] * 10,
                    "message": "使用了始终失败任务的结果（意外情况）"
                }
            else:
                result = {
                    "source": result_source,
                    "final_value": base_value["fallback_value"] * 5,
                    "message": "使用了备用任务的结果（预期情况）"
                }
            
            print(f"条件分支任务完成: {result}")
            return result
        
        # 3.5 清理任务(总是执行)
        @workflow.task(name="cleanup_task", always_run=True)
        def run_cleanup_task():
            print("执行清理任务...")
            
            # 模拟资源清理
            print("释放资源，清理临时文件...")
            
            # 返回清理结果
            cleanup_result = {
                "status": "success",
                "message": "资源已清理，临时文件已删除"
            }
            
            print(f"清理任务完成: {cleanup_result}")
            return cleanup_result
        
        # 4. 执行工作流
        print("\n开始执行错误处理工作流...")
        # 添加重试和错误处理配置
        workflow.configure_error_handling(
            retry_exceptions=[ConnectionError, TimeoutError],
            max_retries=workflow_config["error_handling"]["max_retries"],
            retry_delay=workflow_config["error_handling"]["retry_delay"],
            fallback_enabled=workflow_config["error_handling"]["fallback_enabled"]
        )
        
        result = workflow.run()
        
        # 5. 总结工作流执行结果
        print("\n错误处理工作流执行完成")
        print(f"总执行时间: {workflow.execution_time:.2f}秒")
        print(f"任务执行顺序: {', '.join(workflow.execution_order)}")
        
        # 结果分析
        if "conditional_task" in result:
            conditional_result = result["conditional_task"]
            print(f"最终结果来源: {conditional_result['source']}")
            print(f"最终值: {conditional_result['final_value']}")
            print(f"消息: {conditional_result['message']}")
        
        if "cleanup_task" in result:
            print(f"清理状态: {result['cleanup_task']['status']}")
        
    except WorkflowError as e:
        print(f"工作流错误: {e}")
    except Exception as e:
        print(f"未预期错误: {e}")

def run_custom_workflow_builder_example():
    """
    自定义工作流构建示例
    
    展示如何使用低级API构建和执行自定义工作流
    """
    print("\n--- 自定义工作流构建示例 ---")
    
    try:
        from myproject.workflow.task import Task
        from myproject.workflow.workflow_builder import WorkflowBuilder
        
        print("初始化自定义工作流构建器")
        
        # 1. 创建工作流构建器
        builder = WorkflowBuilder(name="custom_workflow", description="自定义构建的工作流")
        
        # 2. 定义工作流任务函数
        
        def data_loading_func(filepath="./data/sample.csv"):
            """数据加载任务函数"""
            print(f"加载数据文件: {filepath}")
            # 模拟数据加载
            return {"rows": 100, "columns": 5, "status": "loaded"}
        
        def data_processing_func(data):
            """数据处理任务函数"""
            print(f"处理数据: {data['rows']}行, {data['columns']}列")
            # 模拟数据处理
            return {"processed_items": data["rows"], "status": "processed"}
        
        def model_training_func(processed_data):
            """模型训练任务函数"""
            print(f"训练模型，使用{processed_data['processed_items']}条数据")
            # 模拟模型训练
            return {"model_accuracy": 0.92, "training_time": 120, "status": "trained"}
        
        def model_evaluation_func(model_data):
            """模型评估任务函数"""
            print(f"评估模型，准确率: {model_data['model_accuracy']}")
            # 模拟模型评估
            metrics = {
                "precision": 0.89,
                "recall": 0.94,
                "f1": 0.91,
                "base_accuracy": model_data["model_accuracy"]
            }
            return metrics
        
        def result_reporting_func(evaluation_metrics):
            """结果报告任务函数"""
            print("生成评估报告")
            # 模拟报告生成
            report = {
                "metrics": evaluation_metrics,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "completed"
            }
            print(f"生成报告: {report}")
            return report
        
        # 3. 创建工作流任务
        load_task = Task(
            name="load_data",
            func=data_loading_func,
            retry_on_failure=True,
            max_retries=2
        )
        
        process_task = Task(
            name="process_data",
            func=data_processing_func,
            depends_on=["load_data"]
        )
        
        train_task = Task(
            name="train_model",
            func=model_training_func,
            depends_on=["process_data"]
        )
        
        evaluate_task = Task(
            name="evaluate_model",
            func=model_evaluation_func,
            depends_on=["train_model"]
        )
        
        report_task = Task(
            name="report_results",
            func=result_reporting_func,
            depends_on=["evaluate_model"]
        )
        
        # 4. 添加任务到工作流构建器
        builder.add_task(load_task)
        builder.add_task(process_task)
        builder.add_task(train_task)
        builder.add_task(evaluate_task)
        builder.add_task(report_task)
        
        # 5. 构建工作流
        print("构建自定义工作流")
        custom_workflow = builder.build()
        
        # 6. 可视化工作流（假设有可视化模块）
        print("\n工作流任务依赖关系:")
        # 简单文本展示依赖关系
        for task_name, task_obj in custom_workflow.tasks.items():
            dependencies = task_obj.depends_on if task_obj.depends_on else []
            dependency_str = ", ".join(dependencies) if dependencies else "无"
            print(f"  任务: {task_name}, 依赖于: {dependency_str}")
        
        # 7. 执行自定义工作流
        print("\n开始执行自定义工作流...")
        result = custom_workflow.run()
        
        # 8. 总结工作流执行结果
        print("\n自定义工作流执行完成")
        print(f"总执行时间: {custom_workflow.execution_time:.2f}秒")
        print(f"任务执行顺序: {', '.join(custom_workflow.execution_order)}")
        
        # 结果分析
        final_report = result["report_results"]
        print("\n工作流最终报告:")
        print(f"准确率: {final_report['metrics']['base_accuracy']:.2f}")
        print(f"精确率: {final_report['metrics']['precision']:.2f}")
        print(f"召回率: {final_report['metrics']['recall']:.2f}")
        print(f"F1分数: {final_report['metrics']['f1']:.2f}")
        print(f"完成时间: {final_report['timestamp']}")
        
    except Exception as e:
        print(f"自定义工作流构建错误: {e}")

if __name__ == "__main__":
    # 运行所有工作流示例
    run_all()
3.1 数据加载任务
        @workflow.task(name="load_data")
        def load_classification_data(input_path):
            print("执行数据加载任务...")
            # 模拟加载分类数据
            sample_data = [
                {"id": 1, "text": "这个产品非常好用，强烈推荐！"},
                {"id": 2, "text": "使用体验一般，有待改进"},
                {"id": 3, "text": "完全不符合预期，太失望了"},
                {"id": 4, "text": "物超所值，很满意这次购买"}
            ]
            print(f"加载了{len(sample_data)}条数据")
            return sample_data
        
        # 3.2 数据预处理任务
        @workflow.task(name="preprocess_data", depends_on=["load_data"])
        def preprocess_classification_data(data):
            print("执行数据预处理任务...")
            processor = data_processor.DataProcessor()
            
            processed_data = []
            for item in data:
                processed_text = processor.process_text(
                    item["text"],
                    lowercase=True,
                    remove_special_chars=True
                )
                processed_data.append({
                    "id": item["id"],
                    "original_text": item["text"],
                    "processed_text": processed_text
                })
            
            print(f"预处理完成，处理了{len(processed_data)}条数据")
            return processed_data
        
        # 3.3 模型推理任务
        @workflow.task(name="model_inference", depends_on=["preprocess_data"])
        def run_classification_model(data):
            print("执行模型推理任务...")
            
            # 加载模型配置
            model_config = config.ModelConfig(
                model_name=workflow_config["model"]["name"],
                model_path=workflow_config["model"]["path"],
                max_length=workflow_config["model"]["max_length"]
            )
            
            # 初始化模型（这里模拟模型推理）
            # 在实际应用中，这里会加载真实的模型并执行推理
            classification_results = []
            
            print("模型推理中...")
            for item in data:
                # 模拟分类结果
                if "好" in item["original_text"] or "推荐" in item["original_text"] or "满意" in item["original_text"]:
                    sentiment = "positive"
                    confidence = 0.92
                elif "一般" in item["original_text"] or "待改进" in item["original_text"]:
                    sentiment = "neutral"
                    confidence = 0.78
                else:
                    sentiment = "negative"
                    confidence = 0.85
                
                classification_results.append({
                    "id": item["id"],
                    "text": item["original_text"],
                    "predicted_class": sentiment,
                    "confidence": confidence
                })
            
            print(f"推理完成，生成了{len(classification_results)}条分类结果")
            return classification_results
        
        # 3.4 结果后处理任务
        @workflow.task(name="post_process_results", depends_on=["model_inference"])
        def post_process_classification_results(results):
            print("执行结果后处理任务...")
            
            processor = post_processor.PostProcessor()
            
            # 筛选高置信度结果
            filtered_results = processor.rank_and_filter(
                results,
                score_key='confidence',
                min_score=0.8
            )
            
            # 添加处理时间戳
            processed_results = []
            for result in filtered_results:
                processed_results.append({
                    **result,
                    "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            print(f"后处理完成，保留了{len(processed_results)}条高置信度结果")
            return processed_results
        
        # 3.5 结果保存任务
        @workflow.task(name="save_results", depends_on=["post_process_results"])
        def save_classification_results(processed_results):
            print("执行结果保存任务...")
            
            output_path = workflow_config["output"]["path"]
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 保存结果
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_results, f, ensure_ascii=False, indent=2)
            
            print(f"结果已保存到: {output_path}")
            return {"status": "success", "output_path": output_path}
        
        # 4. 执行工作流
        print("\n开始执行文本分类工作流...")
        result = workflow.run(input_path="./data/sample_texts.csv")
        
        # 5. 总结工作流执行结果
        print("\n文本分类工作流执行完成")
        print(f"总执行时间: {workflow.execution_time:.2f}秒")
        print(f"任务执行顺序: {', '.join(workflow.execution_order)}")
        
        # 显示最终分类结果
        print("\n分类结果示例:")
        for i, item in enumerate(result):
            if i >= 2:  # 只显示前2条结果
                break
            print(f"样本{item['id']}:")
            print(f"  文本: {item['text']}")
            print(f"  分类: {item['predicted_class']}")
            print(f"  置信度: {item['confidence']}")
        
    except WorkflowError as e:
        print(f"工作流错误: {e}")
    except Exception as e:
        print(f"未预期错误: {e}")

def run_data_analysis_workflow():
    """
    数据分析工作流示例
    
    展示如何构建一个数据分析和可视化的完整流程
    """
    print("\n--- 数据分析工作流示例 ---")
    
    try:
        # 1. 定义工作流配置
        workflow_config = {
            "name": "data_analysis_workflow",
            "description": "数据分析与可视化工作流",
            "data": {
                "input_format": "csv",
                "input_path": "./data/sales_data.csv"
            },
            "analysis": {
                "metrics": ["sum", "mean", "median", "trend"],
                "group_by": "product_category"
            },
            "visualization": {
                "charts": ["bar", "line", "pie"],
                "output_dir": "./output/charts/"
            }
        }
        
        print("初始化数据分析工作流")
        
        # 2. 创建工作流管理器
        workflow = workflow_manager.WorkflowManager(workflow_config)
        
        # 3. 定义和添加工作流任务
        
        # 3.1 数据加载任务
        @workflow.task(name="load_data")
        def load_analysis_data():
            print("执行数据加载任务...")
            
            # 模拟销售数据
            sample_data = {
                "product_category": ["电子产品", "家居用品", "食品饮料", "电子产品", "家居用品", 
                                    "食品饮料", "电子产品", "家居用品", "食品饮料"],
                "product_name": ["智能手机", "沙发", "矿泉水", "笔记本电脑", "床垫", 
                                "巧克力", "平板电脑", "餐桌", "咖啡"],
                "sales_amount": [12000, 8500, 1200, 15000, 6800, 900, 8000, 7500, 1500],
                "sales_date": ["2023-01-15", "2023-01-20", "2023-01-25", "2023-02-10", 
                              "2023-02-15", "2023-02-20", "2023-03-05", "2023-03-10", "2023-03-15"]
            }
            
            # 转换为DataFrame（实际使用中通常会从文件加载）
            sales_df = pd.DataFrame(sample_data)
            print(f"加载了销售数据: {len(sales_df)}行, {len(sales_df.columns)}列")
            
            return sales_df
        
        # 3.2 数据处理任务
        @workflow.task(name="process_data", depends_on=["load_data"])
        def process_analysis_data(df):
            print("执行数据处理任务...")
            
            # 转换日期列
            df['sales_date'] = pd.to_datetime(df['sales_date'])
            
            # 添加月份列
            df['sales_month'] = df['sales_date'].dt.strftime('%Y-%m')
            
            # 检查缺失值
            missing_values = df.isnull().sum().sum()
            print(f"数据中的缺失值数量: {missing_values}")
            
            # 添加一些派生特征
            df['price_category'] = pd.cut(
                df['sales_amount'], 
                bins=[0, 5000, 10000, float('inf')],
                labels=['低价', '中价', '高价']
            )
            
            print("数据处理完成")
            return df
        
        # 3.3 分析任务
        @workflow.task(name="analyze_data", depends_on=["process_data"])
        def analyze_data(df):
            print("执行数据分析任务...")
            
            results = {}
            
            # 按产品类别分组分析
            group_by = workflow_config["analysis"]["group_by"]
            print(f"按{group_by}分组分析...")
            
            # 计算各类别销售总额
            category_sales = df.groupby(group_by)['sales_amount'].sum().to_dict()
            results['category_sales'] = category_sales
            
            # 计算各类别平均销售额
            category_avg_sales = df.groupby(group_by)['sales_amount'].mean().to_dict()
            results['category_avg_sales'] = category_avg_sales
            
            # 计算总体统计信息
            results['total_sales'] = df['sales_amount'].sum()
            results['avg_sale'] = df['sales_amount'].mean()
            results['max_sale'] = df['sales_amount'].max()
            results['min_sale'] = df['sales_amount'].min()
            
            # 按月份统计销售趋势
            monthly_trend = df.groupby('sales_month')['sales_amount'].sum().to_dict()
            results['monthly_trend'] = monthly_trend
            
            print("数据分析完成")
            return results
        
        # 3.4 可视化任务
        @workflow.task(name="visualize_data", depends_on=["analyze_data"])
        def visualize_data(analysis_results):
            print("执行数据可视化任务...")
            
            # 导入可视化模块（示例代码，实际项目中应该有真实实现）
            from myproject.extensions import visualization
            
            # 确保输出目录存在
            output_dir = workflow_config["visualization"]["output_dir"]
            os.makedirs(output_dir, exist_ok=True)
            
            visualization_results = []
            
            # 1. 创建产品类别销售柱状图
            category_sales = analysis_results['category_sales']
            bar_chart_path = os.path.join(output_dir, "category_sales_bar.png")
            
            # 这里是模拟生成图表，实际项目中会调用真实的图表生成函数
            print(f"生成产品类别销售柱状图: {bar_chart_path}")
            # visualization.create_bar_chart(
            #     labels=list(category_sales.keys()),
            #     values=list(category_sales.values()),
            #     title="各产品类别销售总额",
            #     output_path=bar_chart_path
            # )
            visualization_results.append({
                "type": "bar_chart",
                "title": "各产品类别销售总额",
                "path": bar_chart_path
            })
            
            # 2. 创建月度销售趋势线图
            monthly_trend = analysis_results['monthly_trend']
            line_chart_path = os.path.join(output_dir, "monthly_sales_trend.png")
            
            print(f"生成月度销售趋势线图: {line_chart_path}")
            # visualization.create_line_chart(
            #     labels=list(monthly_trend.keys()),
            #     values=list(monthly_trend.values()),
            #     title="月度销售趋势",
            #     output_path=line_chart_path
            # )
            visualization_results.append({
                "type": "line_chart",
                "title": "月度销售趋势",
                "path": line_chart_path
            })
            
            # 3. 创建产品类别销售占比饼图
            pie_chart_path = os.path.join(output_dir, "category_sales_pie.png")
            
            print(f"生成产品类别销售占比饼图: {pie_chart_path}")
            # visualization.create_pie_chart(
            #     labels=list(category_sales.keys()),
            #     values=list(category_sales.values()),
            #     title="各产品类别销售占比",
            #     output_path=pie_chart_path
            # )
            visualization_results.append({
                "type": "pie_chart",
                "title": "各产品类别销售占比",
                "path": pie_chart_path
            })
            
            print(f"可视化任务完成，生成了{len(visualization_results)}个图表")
            return visualization_results
        
        # 3.5 报告生成任务
        @workflow.task(name="generate_report", depends_on=["analyze_data", "visualize_data"])
        def generate_analysis_report(analysis_results, visualization_results):
            print("执行报告生成任务...")
            
            # 生成报告的文件路径
            report_path = os.path.join(
                workflow_config["visualization"]["output_dir"],
                "sales_analysis_report.html"
            )
            
            # 准备报告内容
            report_content = f"""
            <html>
            <head>
                <title>销售数据分析报告</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #2c3e50; }}
                    .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
                    .chart-container {{ margin: 20px 0; }}
                </style>
            </head>
            <body>
                <h1>销售数据分析报告</h1>
                <div class="summary">
                    <h2>销售总览</h2>
                    <p>总销售额: {analysis_results['total_sales']} 元</p>
                    <p>平均销售额: {analysis_results['avg_sale']:.2f} 元</p>
                    <p>最高销售额: {analysis_results['max_sale']} 元</p>
                    <p>最低销售额: {analysis_results['min_sale']} 元</p>
                </div>
                
                <h2>产品类别分析</h2>
                <div class="chart-container">
                    <h3>各产品类别销售总额</h3>
                    <img src="category_sales_bar.png" alt="产品类别销售柱状图">
                    
                    <h3>产品类别销售占比</h3>
                    <img src="category_sales_pie.png" alt="产品类别销售占比饼图">
                </div>
                
                <h2>销售趋势分析</h2>
                <div class="chart-container">
                    <h3>月度销售趋势</h3>
                    <img src="monthly_sales_trend.png" alt="月度销售趋势线图">
                </div>
                
                <h2>类别详细分析</h2>
                <table border="1" cellpadding="5">
                    <tr>
                        <th>产品类别</th>
                        <th>总销售额</th>
                        <th>平均销售额</th>
                    </tr>
            """
            
            # 添加各产品类别的详细数据
            for category in analysis_results['category_sales']:
                report_content += f"""
                    <tr>
                        <td>{category}</td>
                        <td>{analysis_results['category_sales'][category]} 元</td>
                        <td>{analysis_results['category_avg_sales'][category]:.2f} 元</td>
                    </tr>
                """
            
            # 完成报告内容
            report_content += """
                </table>
                
                <h2>结论与建议</h2>
                <p>根据以上分析，我们可以得出以下结论：</p>
                <ul>
                    <li>电子产品类别的销售额最高，应继续加强该类别的营销</li>
                    <li>食品饮料类别的销售额相对较低，但利润率可能较高，需进一步分析</li>
                    <li>销售趋势呈逐月上升，表明营销策略有效</li>
                </ul>
            </body>
            </html>
            """
            
            # 写入报告文件
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"分析报告已生成: {report_path}")
            return {"report_path": report_path}
        
        # 4. 执行工作流
        print("\n开始执行数据分析工作流...")
        result = workflow.run()
        
        # 5. 总结工作流执行结果
        print("\n数据分析工作流执行完成")
        print(f"总执行时间: {workflow.execution_time:.2f}秒")
        print(f"任务执行顺序: {', '.join(workflow.execution_order)}")
        print(f"分析报告路径: {result['report_path']}")
        
    except WorkflowError as e:
        print(f"工作流错误: {e}")
    except Exception as e:
        print(f"未预期错误: {e}")

def run_content_generation_workflow():
    """
    内容生成工作流示例
    
    展示如何构建一个内容生成和优化的完整流程
    """
    print("\n--- 内容生成工作流示例 ---")
    
    try:
        # 1. 定义工作流配置
        workflow_config = {
            "name": "content_generation_workflow",
            "description": "内容生成与优化工作流",
            "model": {
                "name": "content-generator",
                "path": "./models/content-generator",
                "max_length": 1024
            },
            "generation": {
                "temperature": 0.7,
                "top_p": 0.9,
                "content_types": ["article", "social_media", "email"]
            },
            "optimization": {
                "readability_check": True,
                "sentiment_analysis": True,
                "grammar_check": True
            }
        }
        
        print("初始化内容生成工作流")
        
        # 2. 创建工作流管理器
        workflow = workflow_manager.WorkflowManager(workflow_config)
        
        # 3. 定义和添加工作流任务
        
        #