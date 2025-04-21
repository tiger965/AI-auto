#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目__init__.py文件查找与修复工具
--------------------------
此脚本在整个项目中查找有语法错误的__init__.py文件，
特别是修复"try"语句后缺少缩进块的问题。
"""

import os
import sys
import re


def find_init_files(start_dir):
    """递归查找所有__init__.py文件"""
    init_files = []
    for root, dirs, files in os.walk(start_dir):
        if "__init__.py" in files:
            init_files.append(os.path.join(root, "__init__.py"))
    return init_files


def check_and_fix_file(file_path):
    """检查并修复文件中的语法错误"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查是否有语法错误
        has_error = False

        # 查找"try:"后面没有缩进块的情况
        try_pattern = r"try:\s*\n\s*(?!    )"
        if re.search(try_pattern, content):
            has_error = True
            content = re.sub(try_pattern, "try:\n    pass\n", content)

        # 查找"except:"后面没有缩进块的情况
        except_pattern = r"except.*:\s*\n\s*(?!    )"
        if re.search(except_pattern, content):
            has_error = True
            content = re.sub(
                except_pattern, lambda m: m.group(
                    0).rstrip() + "\n    pass\n", content
            )

        # 查找"else:"后面没有缩进块的情况
        else_pattern = r"else:\s*\n\s*(?!    )"
        if re.search(else_pattern, content):
            has_error = True
            content = re.sub(else_pattern, "else:\n    pass\n", content)

        # 查找"finally:"后面没有缩进块的情况
        finally_pattern = r"finally:\s*\n\s*(?!    )"
        if re.search(finally_pattern, content):
            has_error = True
            content = re.sub(finally_pattern, "finally:\n    pass\n", content)

        # 查找其他可能的语法错误（缺少缩进的代码块）
        block_pattern = r"(if|elif|else|for|while|def|class|with).*:\s*\n\s*(?!    )"
        if re.search(block_pattern, content):
            has_error = True
            content = re.sub(
                block_pattern, lambda m: m.group(
                    0).rstrip() + "\n    pass\n", content
            )

        # 如果有错误，保存修复后的文件
        if has_error:
            # 备份原文件
            backup_path = file_path + ".bak"
            with open(backup_path, "w", encoding="utf-8") as f:
                with open(file_path, "r", encoding="utf-8") as original:
                    f.write(original.read())

            # 写入修复后的内容
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return True, "已修复语法错误"

        return False, "文件没有检测到语法错误"

    except Exception as e:
        return False, f"检查文件时出错: {str(e)}"


def main():
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # 假设脚本在debug_tests目录下

    print(f"=== 项目__init__.py文件查找与修复工具 ===")
    print(f"项目根目录: {project_root}")

    # 特别关注的目录
    focus_dirs = [
        os.path.join(project_root, "modules"),
        os.path.join(project_root, "modules", "audio"),
        os.path.join(project_root, "modules", "nlp"),
        os.path.join(project_root, "modules", "video"),
        os.path.join(project_root, "modules", "vision"),
    ]

    # 先检查关注的目录
    print("\n检查特别关注的目录...")
    for dir_path in focus_dirs:
        if os.path.exists(dir_path):
            init_path = os.path.join(dir_path, "__init__.py")
            if os.path.exists(init_path):
                fixed, message = check_and_fix_file(init_path)
                status = "已修复" if fixed else "无需修复"
                print(f"{status}: {init_path} - {message}")
            else:
                print(f"创建文件: {init_path}")
                with open(init_path, "w", encoding="utf-8") as f:
                    f.write("# -*- coding: utf-8 -*-\n\n")
        else:
            print(f"目录不存在: {dir_path}")

    # 查找整个项目中的所有__init__.py文件
    print("\n查找整个项目中的__init__.py文件...")
    init_files = find_init_files(project_root)
    print(f"找到 {len(init_files)} 个__init__.py文件")

    # 检查并修复文件
    print("\n开始检查和修复文件...")
    fixed_count = 0
    for file_path in init_files:
        fixed, message = check_and_fix_file(file_path)
        if fixed:
            fixed_count += 1
            print(f"已修复: {file_path} - {message}")

    print(f"\n总共修复了 {fixed_count} 个文件")
    print("完成！")


if __name__ == "__main__":
    main()