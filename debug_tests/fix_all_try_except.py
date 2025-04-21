#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python try-except修复工具 - 强效版
---------------------------
专门修复项目中所有缺少except或finally块的try语句
采用直接文本替换方法，不依赖语法分析
"""

import os
import sys
import re
import shutil
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("TryExceptFixer")

# 统计计数
fixed_files = 0
scanned_files = 0


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


def get_all_python_files(directory):
    """获取目录中所有的Python文件"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # 排除某些目录
        if any(
            excluded in root for excluded in ["__pycache__", ".git", "venv", ".idea"]
        ):
            continue

        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                python_files.append(full_path)

    return python_files


def fix_try_except_in_file(file_path):
    """修复文件中的try-except问题"""
    global fixed_files, scanned_files
    scanned_files += 1

    # 创建备份
    backup_path = f"{file_path}.try_except_fix.bak"
    if not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 查找所有try:语句
        try_pattern = r"(\s*)try\s*:"

        # 使用正则表达式查找所有try语句的位置
        try_matches = list(re.finditer(try_pattern, content))

        if not try_matches:
            # 没有try语句，不需要修复
            return False

        # 标记是否需要修复
        need_fix = False

        # 从后向前处理，避免位置偏移
        for match in reversed(try_matches):
            try_pos = match.start()
            try_end = match.end()
            indent = match.group(1)  # 缩进空格

            # 查找对应的except或finally
            # 跳过注释和字符串
            code_after_try = content[try_end:]

            # 检查是否存在对应的except或finally块
            except_match = re.search(
                r"^\s*except\b", code_after_try, re.MULTILINE)
            finally_match = re.search(
                r"^\s*finally\b", code_after_try, re.MULTILINE)

            # 如果没有找到except或finally
            if not except_match and not finally_match:
                # 找到下一个非空白、非注释、与try同级或更低级的行
                lines_after = code_after_try.split("\n")
                next_line_pos = -1

                for i, line in enumerate(lines_after):
                    if line.strip() and not line.strip().startswith("#"):
                        # 检查缩进级别
                        if len(line) - len(line.lstrip()) <= len(indent):
                            next_line_pos = i
                            break

                if next_line_pos != -1:
                    # 修复：在此位置插入except块
                    lines = content.split("\n")
                    try_line_no = content[:try_pos].count("\n")
                    insert_pos = try_line_no + next_line_pos + 1

                    # 创建标准的except块
                    except_block = [
                        f"{indent}except Exception as e:",
                        f'{indent}    print(f"错误: {{str(e)}}")',
                    ]

                    # 插入except块
                    for i, line in enumerate(except_block):
                        lines.insert(insert_pos + i, line)

                    # 更新内容
                    content = "\n".join(lines)
                    need_fix = True
                    logger.info(
                        f"在文件 {file_path} 的第 {try_line_no+1} 行附近添加了except块"
                    )
                else:
                    # 文件末尾的try块
                    lines = content.split("\n")
                    try_line_no = content[:try_pos].count("\n")

                    # 添加到文件末尾
                    lines.append(f"{indent}except Exception as e:")
                    lines.append(f'{indent}    print(f"错误: {{str(e)}}")')

                    content = "\n".join(lines)
                    need_fix = True
                    logger.info(f"在文件 {file_path} 的末尾添加了except块")

        if need_fix:
            # 写回文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            fixed_files += 1
            return True

        return False

    except Exception as e:
        logger.error(f"修复文件 {file_path} 时出错: {str(e)}")
        # 恢复备份
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
        return False


def fix_specific_files(file_paths):
    """修复指定文件列表"""
    fixed_count = 0

    for file_path in file_paths:
        if os.path.exists(file_path):
            if fix_try_except_in_file(file_path):
                fixed_count += 1

    return fixed_count


def fix_all_python_files():
    """修复项目中所有Python文件的try-except问题"""
    project_root = find_project_root()
    python_files = get_all_python_files(project_root)

    logger.info(f"开始扫描 {len(python_files)} 个Python文件...")

    # 首先修复关键文件
    critical_files = [
        os.path.join(project_root, "core", "__init__.py"),
        os.path.join(project_root, "ui", "cli", "__init__.py"),
        os.path.join(project_root, "config", "__init__.py"),
        os.path.join(project_root, "modules", "__init__.py"),
    ]

    fixed_critical = fix_specific_files(
        [f for f in critical_files if f in python_files]
    )
    logger.info(f"已修复 {fixed_critical} 个关键文件")

    # 修复其他文件
    for file_path in python_files:
        if file_path not in critical_files:
            fix_try_except_in_file(file_path)

    logger.info(
        f"扫描完成，总共扫描了 {scanned_files} 个文件，修复了 {fixed_files} 个文件"
    )


if __name__ == "__main__":
    logger.info("===== 开始修复项目中所有缺少except或finally块的try语句 =====")
    fix_all_python_files()
    logger.info("===== 修复完成 =====")