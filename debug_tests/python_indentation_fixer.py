#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python文件缩进修复工具
------------------
自动修复项目中Python文件的缩进错误
"""

import os
import re
import sys
import logging
from typing import List, Tuple, Dict, Set, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("PythonFixer")


class PythonIndentationFixer:
    """Python文件缩进修复器"""

    def __init__(self, project_root: str = None):
        """
        初始化修复器

        Args:
            project_root: 项目根目录，默认为当前目录的上一级
        """
        if project_root is None:
            # 默认为当前目录的上一级
            self.project_root = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        else:
            self.project_root = os.path.abspath(project_root)

        # 统计信息
        self.stats = {
            "files_scanned": 0,
            "files_fixed": 0,
            "errors_found": 0,
            "errors_fixed": 0,
        }

        # 记录已处理的文件
        self.processed_files = set()

    def scan_python_files(self, start_dir: str = None) -> List[str]:
        """
        扫描Python文件

        Args:
            start_dir: 起始目录，默认为项目根目录

        Returns:
            List[str]: Python文件列表
        """
        start_dir = start_dir or self.project_root
        python_files = []

        logger.info(f"开始扫描Python文件: {start_dir}")

        for root, dirs, files in os.walk(start_dir):
            # 跳过.git目录
            if ".git" in dirs:
                dirs.remove(".git")

            # 跳过__pycache__目录
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")

            # 查找Python文件
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)

        self.stats["files_scanned"] = len(python_files)
        logger.info(f"扫描完成，共找到 {len(python_files)} 个Python文件")

        return python_files

    def check_file_indentation(self, file_path: str) -> Tuple[bool, List[int]]:
        """
        检查文件缩进是否正确

        Args:
            file_path: 文件路径

        Returns:
            Tuple[bool, List[int]]: (是否有错误, 错误行号列表)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 尝试编译代码
            try:
                compile(content, file_path, "exec")
                return False, []
            except IndentationError as e:
                # 记录错误行号
                self.stats["errors_found"] += 1
                return True, [e.lineno]
            except SyntaxError as e:
                # 可能是缩进导致的语法错误
                if "unexpected indent" in str(e) or "unindent does not match" in str(e):
                    self.stats["errors_found"] += 1
                    return True, [e.lineno]
                return False, []
            except Exception:
                return False, []

        except Exception as e:
            logger.error(f"检查文件出错: {file_path}, 错误: {str(e)}")
            return False, []

    def fix_file_indentation(self, file_path: str) -> bool:
        """
        修复文件缩进

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否修复成功
        """
        try:
            # 检查文件是否已处理
            if file_path in self.processed_files:
                return True

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # 分析并修复缩进
            fixed_lines = self._fix_indentation(lines)

            # 如果有修改，写入文件
            if fixed_lines != lines:
                # 创建备份
                backup_path = file_path + ".indent.bak"
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                logger.info(f"已创建备份: {backup_path}")

                # 写入修复后的内容
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(fixed_lines)

                # 再次检查是否有缩进错误
                has_error, _ = self.check_file_indentation(file_path)
                if not has_error:
                    logger.info(f"已修复文件: {file_path}")
                    self.stats["files_fixed"] += 1
                    self.stats["errors_fixed"] += 1
                    self.processed_files.add(file_path)
                    return True
                else:
                    # 修复失败，恢复备份
                    with open(backup_path, "r", encoding="utf-8") as f:
                        original_content = f.read()
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(original_content)
                    logger.warning(f"修复失败，已恢复备份: {file_path}")
                    return False
            else:
                # 内容没有变化，可能是其他语法错误
                logger.info(f"文件无需修改: {file_path}")
                self.processed_files.add(file_path)
                return True

        except Exception as e:
            logger.error(f"修复文件出错: {file_path}, 错误: {str(e)}")
            return False

    def _fix_indentation(self, lines: List[str]) -> List[str]:
        """
        修复缩进

        Args:
            lines: 文件行列表

        Returns:
            List[str]: 修复后的行列表
        """
        fixed_lines = []
        indent_stack = [0]  # 缩进栈，初始为0

        # 检测缩进类型（空格或制表符）
        indent_char = " "
        indent_size = 4
        for line in lines:
            if line.startswith(" "):
                # 计算前导空格数
                leading_spaces = len(line) - len(line.lstrip(" "))
                if leading_spaces > 0:
                    indent_char = " "
                    # 尝试确定缩进大小
                    if leading_spaces in [2, 4, 8]:
                        indent_size = leading_spaces
                    break
            elif line.startswith("\t"):
                indent_char = "\t"
                indent_size = 1
                break

        # 处理每一行
        for i, line in enumerate(lines):
            # 跳过空行和注释行
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                fixed_lines.append(line)
                continue

            # 计算当前行的缩进级别
            if indent_char == " ":
                current_indent = len(line) - len(line.lstrip(" "))
                current_level = current_indent // indent_size
            else:
                current_indent = len(line) - len(line.lstrip("\t"))
                current_level = current_indent

            # 检查是否有冒号结尾（开始新的代码块）
            if stripped.endswith(":"):
                # 这一行结束后，下一行应该增加一级缩进
                expected_next_level = current_level + 1
                indent_stack.append(expected_next_level)

            # 检查是否有减少缩进的关键字
            elif stripped.startswith(
                ("elif ", "else:", "except", "finally:", "except:")
            ):
                # 与前一个if/try语句同级
                if len(indent_stack) > 1:
                    expected_level = indent_stack[-2]
                    if current_level > expected_level:
                        # 缩进过多，减少缩进
                        new_indent = expected_level * indent_size
                        fixed_line = indent_char * new_indent + line.lstrip()
                        fixed_lines.append(fixed_line)
                        continue
                    elif current_level < expected_level:
                        # 缩进不足，增加缩进
                        new_indent = expected_level * indent_size
                        fixed_line = indent_char * new_indent + line.lstrip()
                        fixed_lines.append(fixed_line)
                        continue

                # 更新缩进栈
                if stripped.endswith(":"):
                    expected_next_level = indent_stack[-2] + 1
                    indent_stack.pop()  # 移除旧的期望缩进
                    indent_stack.append(expected_next_level)

            # 检查当前行缩进是否合理
            if indent_stack and current_level > indent_stack[-1] + 1:
                # 缩进过多，减少到合理范围
                new_indent = indent_stack[-1] * indent_size
                fixed_line = indent_char * new_indent + line.lstrip()
                fixed_lines.append(fixed_line)
                continue

            # 检查是否结束了代码块
            while indent_stack and current_level < indent_stack[-1]:
                indent_stack.pop()

            # 保持原样
            fixed_lines.append(line)

        return fixed_lines

    def fix_specific_file(self, file_path: str) -> bool:
        """
        修复指定文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否修复成功
        """
        if not file_path.endswith(".py"):
            logger.warning(f"不是Python文件: {file_path}")
            return False

        logger.info(f"检查文件: {file_path}")
        has_error, error_lines = self.check_file_indentation(file_path)

        if has_error:
            logger.info(f"发现缩进错误，正在修复: {file_path}, 错误行: {error_lines}")
            return self.fix_file_indentation(file_path)
        else:
            logger.info(f"文件无缩进错误: {file_path}")
            return True

    def fix_all_python_files(self, start_dir: str = None) -> Dict:
        """
        修复所有Python文件的缩进

        Args:
            start_dir: 起始目录，默认为项目根目录

        Returns:
            Dict: 统计信息
        """
        python_files = self.scan_python_files(start_dir)

        fixed_files = []
        failed_files = []

        for file_path in python_files:
            logger.info(f"检查文件: {file_path}")
            has_error, error_lines = self.check_file_indentation(file_path)

            if has_error:
                logger.info(
                    f"发现缩进错误，正在修复: {file_path}, 错误行: {error_lines}"
                )
                if self.fix_file_indentation(file_path):
                    fixed_files.append(file_path)
                else:
                    failed_files.append(file_path)

        logger.info("=== 修复完成 ===")
        logger.info(f"扫描文件数: {self.stats['files_scanned']}")
        logger.info(f"发现错误数: {self.stats['errors_found']}")
        logger.info(f"修复文件数: {self.stats['files_fixed']}")
        logger.info(f"修复错误数: {self.stats['errors_fixed']}")

        return {
            "stats": self.stats,
            "fixed_files": fixed_files,
            "failed_files": failed_files,
        }


# 命令行入口
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Python文件缩进修复工具")
    parser.add_argument("--root", type=str, default=None, help="项目根目录")
    parser.add_argument("--file", type=str, default=None, help="指定文件路径")

    args = parser.parse_args()

    fixer = PythonIndentationFixer(args.root)

    if args.file:
        # 修复单个文件
        file_path = os.path.abspath(args.file)
        success = fixer.fix_specific_file(file_path)
        sys.exit(0 if success else 1)
    else:
        # 修复所有文件
        result = fixer.fix_all_python_files()
        if result["failed_files"]:
            logger.warning("有些文件修复失败:")
            for file in result["failed_files"]:
                logger.warning(f"  - {file}")
        sys.exit(0 if not result["failed_files"] else 1)


if __name__ == "__main__":
    main()