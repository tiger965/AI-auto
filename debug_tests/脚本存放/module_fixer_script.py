#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI分析引擎模块修复脚本
-------------------
此脚本针对性修复modules目录下各子模块的__init__.py文件中的try-except问题
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
            # 创建文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# -*- coding: utf-8 -*-\n\n")
            print(f"已创建新文件: {file_path}")
            return True

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 创建备份
        with open(file_path + ".bak", "w", encoding="utf-8") as f:
            f.write(content)

        # 检查是否有try-except语法错误
        try_pattern = r"try:(?:\s*\n\s*)(except.*?:)(?:\s*\n)"
        if re.search(try_pattern, content, re.DOTALL):
            # 修复try-except块
            fixed_content = re.sub(
                try_pattern, "try:\n    pass\n\\1\n    pass\n", content, flags=re.DOTALL
            )

            # 保存修复后的文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)

            print(f"已修复文件: {file_path}")
            return True
        else:
            # 如果没有找到try-except模式，尝试重新创建一个干净的文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# -*- coding: utf-8 -*-\n\n# 初始化AI分析引擎模块\n\n")
            print(f"已重置文件: {file_path}")
            return True
    except Exception as e:
        print(f"修复文件时出错: {file_path}, 错误: {str(e)}")
        return False


def main():
    """主函数"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    modules_dir = os.path.abspath(os.path.join(script_dir, MODULES_DIR))

    print(f"=== AI分析引擎模块修复 ===")
    print(f"模块目录: {modules_dir}")

    success_count = 0
    failure_count = 0

    for module_name in MODULE_NAMES:
        module_path = os.path.join(modules_dir, module_name)
        init_file = os.path.join(module_path, "__init__.py")

        print(f"\n处理模块: {module_name}")
        if not os.path.exists(module_path):
            try:
                os.makedirs(module_path)
                print(f"已创建模块目录: {module_path}")
            except Exception as e:
                print(f"创建模块目录失败: {module_path}, 错误: {str(e)}")
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