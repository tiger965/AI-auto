#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模块检查与修复脚本
---------------
此脚本检查AI分析引擎模块的实际内容并进行手动修复
"""

import os
import sys

# 模块路径配置
MODULES_DIR = "../modules"  # 相对于脚本所在目录的路径
MODULE_NAMES = ["audio", "nlp", "video", "vision"]


def check_and_create_clean_init(module_dir, module_name):
    """检查并创建干净的__init__.py文件"""
    init_file = os.path.join(module_dir, "__init__.py")

    # 首先确保目录存在
    if not os.path.exists(module_dir):
        try:
            os.makedirs(module_dir)
            print(f"已创建目录: {module_dir}")
        except Exception as e:
            print(f"创建目录失败: {module_dir}, 错误: {str(e)}")
            return False

    # 创建全新的__init__.py文件
    try:
        with open(init_file, "w", encoding="utf-8") as f:
            f.write(
                f"""# -*- coding: utf-8 -*-
\"\"\"
{module_name} 模块初始化
\"\"\"

class {module_name.capitalize()}Analyzer:
    \"\"\"
    {module_name.capitalize()}分析器类
    \"\"\"
    
    def __init__(self):
        \"\"\"初始化{module_name.capitalize()}分析器\"\"\"
        self.name = "{module_name.capitalize()}Analyzer"
    
    def analyze(self, data):
        \"\"\"分析数据\"\"\"
        return {{"status": "success", "analyzer": self.name}}
    
    def method1(self):
        \"\"\"测试方法1\"\"\"
        return "method1 result"

# 全局分析器实例
analyzer = {module_name.capitalize()}Analyzer()
"""
            )
        print(f"已创建干净的初始化文件: {init_file}")
        return True
    except Exception as e:
        print(f"创建初始化文件失败: {init_file}, 错误: {str(e)}")
        return False


def check_module_content(module_dir):
    """检查模块内容"""
    init_file = os.path.join(module_dir, "__init__.py")
    if os.path.exists(init_file):
        try:
            with open(init_file, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"\n文件内容 ({init_file}):")
            print("-" * 50)
            print(content)
            print("-" * 50)
        except Exception as e:
            print(f"读取文件失败: {init_file}, 错误: {str(e)}")
    else:
        print(f"文件不存在: {init_file}")


def main():
    """主函数"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    modules_dir = os.path.abspath(os.path.join(script_dir, MODULES_DIR))

    print(f"=== AI分析引擎模块检查与修复 ===")
    print(f"模块根目录: {modules_dir}")

    # 检查模块目录是否存在
    if not os.path.exists(modules_dir):
        print(f"模块根目录不存在: {modules_dir}")
        try:
            os.makedirs(modules_dir)
            print(f"已创建模块根目录: {modules_dir}")
        except Exception as e:
            print(f"创建模块根目录失败: {modules_dir}, 错误: {str(e)}")
            return

    # 确保模块根目录有__init__.py
    root_init = os.path.join(modules_dir, "__init__.py")
    if not os.path.exists(root_init):
        try:
            with open(root_init, "w", encoding="utf-8") as f:
                f.write(
                    """# -*- coding: utf-8 -*-
\"\"\"
AI分析引擎模块
\"\"\"
"""
                )
            print(f"已创建模块根目录初始化文件: {root_init}")
        except Exception as e:
            print(f"创建模块根目录初始化文件失败: {root_init}, 错误: {str(e)}")

    # 检查并修复每个子模块
    for module_name in MODULE_NAMES:
        module_dir = os.path.join(modules_dir, module_name)
        print(f"\n处理模块: {module_name}")

        # 显示当前内容
        check_module_content(module_dir)

        # 询问是否创建干净的初始化文件
        choice = input(f"是否为{module_name}模块创建干净的初始化文件? (y/n): ")
        if choice.lower() == "y":
            check_and_create_clean_init(module_dir, module_name)
            # 再次显示内容
            check_module_content(module_dir)

    print("\n=== 处理完成 ===")


if __name__ == "__main__":
    main()