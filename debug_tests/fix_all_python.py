#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python语法修复工具 - 全项目修复
---------------------------
自动扫描并修复项目中所有Python文件的语法错误，
特别关注缺少except或finally块的try语句问题
"""

import os
import sys
import re
import ast
import shutil
import logging
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("PythonSyntaxFixer")

# 全局计数器
fixed_files = 0
scanned_files = 0
error_files = 0


def find_project_root():
    """查找项目根目录"""
    # 从当前目录开始查找
    current_dir = os.getcwd()

    # 尝试找到项目根目录的标志性文件/目录
    possible_roots = [
        # 常见的项目根目录标志
        os.path.join(current_dir, "organized_project"),
        os.path.join(current_dir, "key", "code", "organized_project"),
        "c:\\Users\\tiger\\Desktop\\key\\code\\organized_project",
    ]

    for root in possible_roots:
        if os.path.exists(root):
            logger.info(f"找到项目根目录: {root}")
            return root

    # 如果找不到确切目录，使用默认路径
    default_path = "c:\\Users\\tiger\\Desktop\\key\\code\\organized_project"
    logger.warning(f"无法确定项目根目录，使用默认路径: {default_path}")
    return default_path


def find_python_files(directory):
    """查找目录中的所有Python文件"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # 跳过缓存目录和虚拟环境
        if "__pycache__" in root or ".venv" in root or ".git" in root:
            continue

        # 查找所有.py文件
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                python_files.append(full_path)

    logger.info(f"找到 {len(python_files)} 个Python文件")
    return python_files


def check_syntax(file_path):
    """检查Python文件的语法"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        # 尝试解析代码
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, e
    except Exception as e:
        return False, e


def fix_try_except_blocks(source):
    """修复缺少except或finally块的try语句"""
    lines = source.split("\n")
    fixed_lines = []
    i = 0
    in_try_block = False
    try_line = -1
    indentation = ""

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 检测try语句
        if stripped.startswith("try:"):
            in_try_block = True
            try_line = i
            # 获取缩进
            indentation = line[: line.find("try")]

        # 如果在try块中，检查是否有对应的except或finally
        if in_try_block and i > try_line:
            # 如果遇到与try同级别的非注释代码行
            if (
                stripped
                and not stripped.startswith("#")
                and not stripped.startswith("except")
                and not stripped.startswith("finally")
                and line.startswith(indentation)
                and len(line) > len(indentation)
            ):
                
                # 如果遇到下一个与try同缩进的语句，说明没有except或finally
                if line.startswith(indentation) and not line.startswith(
                    indentation + " "
                ):
                    # 添加一个except块
                    fixed_lines.append(f"{indentation}except Exception as e:")
                    fixed_lines.append(
                        f'{indentation}    logger.error(f"错误: {{str(e)}}")'
                    )
                    fixed_lines.append(line)
                    in_try_block = False
                    i += 1
                    continue

            # 如果遇到except或finally，标记try块结束
            if stripped.startswith("except") or stripped.startswith("finally"):
                in_try_block = False

        fixed_lines.append(line)
        i += 1

    # 如果文件结束时仍在try块中，添加except
    if in_try_block:
        fixed_lines.append(f"{indentation}except Exception as e:")
        fixed_lines.append(f'{indentation}    logger.error(f"错误: {{str(e)}}")')

    return "\n".join(fixed_lines)


def fix_missing_pass(source):
    """修复缺少pass语句的空代码块"""
    lines = source.split("\n")
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)

        # 检查以冒号结尾的行
        if line.strip().endswith(":"):
            # 获取当前行的缩进
            current_indent = len(line) - len(line.lstrip())
            expected_indent = current_indent + 4  # 预期的子块缩进

            # 检查下一行
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                next_indent = len(next_line) - len(next_line.lstrip())

                # 如果下一行缩进不够或是空行，添加pass
                if next_indent < expected_indent or not next_line.strip():
                    indent_str = " " * expected_indent
                    fixed_lines.append(f"{indent_str}pass")
            else:
                # 文件结束，添加pass
                indent_str = " " * (current_indent + 4)
                fixed_lines.append(f"{indent_str}pass")

        i += 1

    return "\n".join(fixed_lines)


def fix_indentation(source):
    """修复Python代码的缩进问题"""
    lines = source.split("\n")
    fixed_lines = []
    stack = [0]  # 缩进栈，初始为0

    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            # 空行或注释行保持不变
            fixed_lines.append(line)
            continue

        # 计算当前行的缩进
        indent = len(line) - len(line.lstrip())
        content = line.strip()

        # 检查是否需要减少缩进
        while indent < stack[-1]:
            stack.pop()

        # 检查是否需要增加缩进
        if content.endswith(":"):
            # 冒号结尾的行，下一行应该增加缩进
            next_indent = stack[-1] + 4
            stack.append(next_indent)

        # 应用当前缩进
        new_line = " " * stack[-1] + content
        fixed_lines.append(new_line)

    return "\n".join(fixed_lines)


def remove_invalid_imports(source):
    """移除无效的导入语句"""
    # 查找如 "import api" 这样的孤立导入
    pattern = r"^\s*import\s+\w+\s*$"
    lines = source.split("\n")
    fixed_lines = []

    for line in lines:
        if re.match(pattern, line.strip()) and not line.strip().startswith("#"):
            # 尝试检查这是否是一个有效的模块
            module_name = line.strip().split()[1]
            try:
                # 尝试导入模块
                __import__(module_name)
                fixed_lines.append(line)
            except ImportError:
                # 如果导入失败，添加注释
                fixed_lines.append(f"# {line.strip()}  # 无效导入，已注释")
        else:
            fixed_lines.append(line)

    return "\n".join(fixed_lines)


def fix_python_file(file_path):
    """修复Python文件中的语法错误"""
    global fixed_files, scanned_files, error_files

    scanned_files += 1
    original_file = file_path
    backup_file = f"{file_path}.syntax_fix.bak"

    # 检查文件语法
    is_valid, error = check_syntax(file_path)
    if is_valid:
        logger.debug(f"文件语法正确，无需修复: {file_path}")
        return

    try:
        # 创建备份
        shutil.copy2(file_path, backup_file)
        logger.info(f"已创建备份: {backup_file}")

        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 应用修复
        fixed_content = content
        fixed_content = fix_try_except_blocks(fixed_content)
        fixed_content = fix_missing_pass(fixed_content)
        fixed_content = remove_invalid_imports(fixed_content)

        # 写入修复后的内容
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(fixed_content)

        # 验证修复结果
        is_fixed, new_error = check_syntax(file_path)
        if is_fixed:
            logger.info(f"成功修复文件: {file_path}")
            fixed_files += 1
        else:
            logger.error(f"修复失败，仍存在语法错误: {file_path}")
            logger.error(f"错误信息: {str(new_error)}")
            # 恢复备份
            shutil.copy2(backup_file, file_path)
            logger.info(f"已恢复原文件")
            error_files += 1

    except Exception as e:
        logger.error(f"修复文件时发生错误: {file_path}")
        logger.error(f"错误信息: {str(e)}")
        error_files += 1


def fix_all_python_files():
    """修复项目中所有Python文件的语法错误"""
    project_root = find_project_root()
    python_files = find_python_files(project_root)

    # 使用多线程加速处理
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(fix_python_file, python_files)

    # 显示统计信息
    logger.info("===== 修复完成 =====")
    logger.info(f"扫描文件: {scanned_files}")
    logger.info(f"修复文件: {fixed_files}")
    logger.info(f"失败文件: {error_files}")

    if fixed_files > 0:
        logger.info("修复成功! 现在可以尝试启动系统。")
    else:
        logger.warning("没有文件被修复，可能需要手动检查错误。")


if __name__ == "__main__":
    logger.info("===== 开始扫描并修复Python语法错误 =====")
    fix_all_python_files()