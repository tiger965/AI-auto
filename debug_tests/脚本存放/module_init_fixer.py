#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI分析引擎模块__init__.py文件修复脚本
-------------------------------
此脚本检查并修复modules下各个子模块的__init__.py文件中的语法错误。
主要针对"try"语句后缺少缩进块的问题。
"""

import os
import sys
import re

# 模块路径配置
MODULES_DIR = "../modules"  # 相对于脚本所在目录的路径
MODULE_NAMES = ["audio", "nlp", "video", "vision"]


def fix_init_file(file_path):
    """修复__init__.py文件中的语法错误"""
    try:
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return False

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 查找"try:"后面没有缩进块的情况
        pattern = r"try:\s*\n\s*(?!    )"  # 匹配try:后面没有四个空格缩进的行

        if re.search(pattern, content):
            # 修复try块
            fixed_content = re.sub(
                r"try:\s*\n\s*(?!    )",
                "try:\n    pass\n",  # 添加一个pass语句作为占位符
                content,
            )

            # 保存修复后的文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)

            print(f"已修复文件: {file_path}")
            return True
        else:
            print(f"文件无需修复: {file_path}")
            return True
    except Exception as e:
        print(f"修复文件时出错: {file_path}, 错误: {str(e)}")
        return False


def main():
    """主函数"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    modules_dir = os.path.abspath(os.path.join(script_dir, MODULES_DIR))

    print(f"=== AI分析引擎模块初始化文件修复 ===")
    print(f"模块目录: {modules_dir}")

    success_count = 0
    failure_count = 0

    for module_name in MODULE_NAMES:
        module_path = os.path.join(modules_dir, module_name)
        init_file = os.path.join(module_path, "__init__.py")

        print(f"\n检查模块: {module_name}")
        if not os.path.exists(module_path):
            print(f"模块目录不存在: {module_path}")
            failure_count += 1
            continue

        if fix_init_file(init_file):
            success_count += 1
        else:
            failure_count += 1

    print("\n=== 修复完成 ===")
    print(f"成功修复: {success_count}")
    print(f"修复失败: {failure_count}")


if __name__ == "__main__":
    main()