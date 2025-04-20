"""
AI自动化项目示例模块

本模块包含AI自动化项目的各种示例，展示如何使用项目中的各个功能模块。
包括API调用示例、核心功能示例和完整工作流示例。

使用方法：
    from examples import api_examples, core_examples, workflow_examples
    
    # 运行API示例
    api_examples.run_basic_api_example()
    
    # 运行核心功能示例
    core_examples.run_model_inference_example()
    
    # 运行工作流示例
    workflow_examples.run_complete_workflow()
"""

# 版本信息
__version__ = '0.1.0'

# 导出示例模块，便于直接导入
from . import api_examples
from . import core_examples
from . import workflow_examples

# 示例运行入口函数
def run_all_examples():
    """运行所有示例代码的入口函数"""
    print("正在运行所有示例...")
    
    # 运行API示例
    print("\n=== 运行API示例 ===")
    api_examples.run_all()
    
    # 运行核心功能示例
    print("\n=== 运行核心功能示例 ===")
    core_examples.run_all()
    
    # 运行工作流示例
    print("\n=== 运行工作流示例 ===")
    workflow_examples.run_all()
    
    print("\n所有示例运行完成！")

if __name__ == "__main__":
    # 当直接运行此模块时，运行所有示例
    run_all_examples()