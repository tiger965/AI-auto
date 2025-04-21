#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
高级Python语法错误修复工具
专门用于修复Python文件中的复杂语法问题
"""

import os
import sys
import re
import ast
import tokenize
import io
import traceback
import time
from collections import defaultdict


class SyntaxFixResult:
    """存储修复结果的类"""

    def __init__(self):
        self.fixed = False
        self.error_type = None
        self.error_message = None
        self.fix_method = None
        self.line_number = None
        self.column = None
        self.source_line = None


class AdvancedPythonFixer:
    """高级Python语法错误修复工具"""

    def __init__(self, root_dir, verbose=True, create_backup=True):
        self.root_dir = os.path.abspath(root_dir)
        self.verbose = verbose
        self.create_backup = create_backup
        self.stats = {
            "total_files": 0,
            "error_files": 0,
            "fixed_files": 0,
            "error_types": defaultdict(int),
            "fixed_types": defaultdict(int),
        }

        # 定义用于跟踪源代码行号的正则表达式
        self.line_regex = re.compile(r"line (\d+)")

    def log(self, message):
        """打印日志（如果启用了详细模式）"""
        if self.verbose:
            print(message)

    def backup_file(self, file_path):
        """创建文件备份"""
        if not self.create_backup:
            return True

        backup_path = file_path + ".advanced.bak"
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as src:
                content = src.read()
            with open(backup_path, "w", encoding="utf-8") as dst:
                dst.write(content)
            return True
        except Exception as e:
            self.log(f"创建备份失败: {file_path} - {str(e)}")
            return False

    def check_syntax(self, file_path):
        """检查文件语法错误并返回详细信息"""
        result = SyntaxFixResult()

        try:
            # 尝试解析文件
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # 尝试解析代码
            ast.parse(content)
            return None  # 没有语法错误

        except SyntaxError as e:
            # 捕获语法错误
            result.error_type = "SyntaxError"
            result.error_message = str(e)
            result.line_number = e.lineno
            result.column = e.offset

            # 获取错误行的内容
            if e.lineno is not None:
                lines = content.split("\n")
                if 0 <= e.lineno - 1 < len(lines):
                    result.source_line = lines[e.lineno - 1]

            return result

        except IndentationError as e:
            # 捕获缩进错误
            result.error_type = "IndentationError"
            result.error_message = str(e)
            result.line_number = e.lineno
            result.column = e.offset

            # 获取错误行的内容
            if e.lineno is not None:
                lines = content.split("\n")
                if 0 <= e.lineno - 1 < len(lines):
                    result.source_line = lines[e.lineno - 1]

            return result

        except Exception as e:
            # 捕获其他错误
            result.error_type = type(e).__name__
            result.error_message = str(e)

            # 尝试从错误消息中提取行号
            match = self.line_regex.search(str(e))
            if match:
                try:
                    result.line_number = int(match.group(1))

                    # 获取错误行的内容
                    lines = content.split("\n")
                    if 0 <= result.line_number - 1 < len(lines):
                        result.source_line = lines[result.line_number - 1]
                except:
                    pass

            return result

    def fix_indentation_error(self, content, error_info):
        """修复缩进错误"""
        if error_info.line_number is None:
            return content, False

        lines = content.split("\n")
        line_index = error_info.line_number - 1

        if line_index < 0 or line_index >= len(lines):
            return content, False

        # 检查是否是"未预期的缩进"
        if "unexpected indent" in error_info.error_message:
            # 减少缩进
            if lines[line_index].startswith(" "):
                lines[line_index] = lines[line_index][4:]  # 移除4个空格
                error_info.fix_method = "减少缩进"
                return "\n".join(lines), True

        # 检查是否是"预期的缩进"
        elif "expected an indented block" in error_info.error_message:
            # 增加缩进
            lines[line_index] = "    " + lines[line_index]
            error_info.fix_method = "增加缩进"
            return "\n".join(lines), True

        # 检查Tab和空格混合问题
        elif "\t" in lines[line_index] and " " in lines[line_index]:
            # 将所有Tab替换为4个空格
            lines[line_index] = lines[line_index].replace("\t", "    ")
            error_info.fix_method = "转换Tab为空格"
            return "\n".join(lines), True

        # 尝试根据前一行确定正确的缩进
        if line_index > 0:
            prev_line = lines[line_index - 1].rstrip()
            if prev_line.endswith(":"):
                # 前一行以冒号结束，需要缩进
                indent = " " * 4
                if lines[line_index].strip():  # 如果行不是空的
                    lines[line_index] = indent + lines[line_index].lstrip()
                    error_info.fix_method = "根据上下文调整缩进"
                    return "\n".join(lines), True

        return content, False

    def fix_syntax_error(self, content, error_info):
        """修复各种语法错误"""
        if error_info.line_number is None:
            return content, False

        lines = content.split("\n")
        line_index = error_info.line_number - 1

        if line_index < 0 or line_index >= len(lines):
            return content, False

        error_line = lines[line_index]
        error_msg = error_info.error_message.lower()

        # 修复括号不匹配
        if (
            "unexpected EOF while parsing" in error_msg
            or "unexpected end of file" in error_msg
            or "parenthesis is never closed" in error_msg
        ):
            # 统计各类括号
            open_parentheses = error_line.count("(") - error_line.count(")")
            open_brackets = error_line.count("[") - error_line.count("]")
            open_braces = error_line.count("{") - error_line.count("}")

            # 添加缺失的闭合括号
            if open_parentheses > 0:
                lines[line_index] = error_line + ")" * open_parentheses
                error_info.fix_method = "添加缺失的右括号"
                return "\n".join(lines), True
            elif open_brackets > 0:
                lines[line_index] = error_line + "]" * open_brackets
                error_info.fix_method = "添加缺失的右方括号"
                return "\n".join(lines), True
            elif open_braces > 0:
                lines[line_index] = error_line + "}" * open_braces
                error_info.fix_method = "添加缺失的右花括号"
                return "\n".join(lines), True

        # 修复缺少冒号
        if "expected ':'" in error_msg:
            # 检查这一行是否应该有冒号但缺少了
            colon_keywords = [
                "if",
                "else",
                "elif",
                "for",
                "while",
                "def",
                "class",
                "try",
                "except",
                "finally",
            ]
            for keyword in colon_keywords:
                if re.match(r"^\s*" + keyword + r"\s+.*[^:]$", error_line):
                    lines[line_index] = error_line + ":"
                    error_info.fix_method = "添加缺失的冒号"
                    return "\n".join(lines), True

        # 修复多余的右括号
        if (
            "unmatched ')'" in error_msg
            or "unmatched ']'" in error_msg
            or "unmatched '}'" in error_msg
        ):
            if ")" in error_line:
                lines[line_index] = error_line.replace(")", "", 1)
                error_info.fix_method = "移除多余的右括号"
                return "\n".join(lines), True
            elif "]" in error_line:
                lines[line_index] = error_line.replace("]", "", 1)
                error_info.fix_method = "移除多余的右方括号"
                return "\n".join(lines), True
            elif "}" in error_line:
                lines[line_index] = error_line.replace("}", "", 1)
                error_info.fix_method = "移除多余的右花括号"
                return "\n".join(lines), True

        # 修复引号不匹配
        if (
            "EOL while scanning string literal" in error_msg
            or "unterminated string literal" in error_msg
        ):
            # 检查单引号和双引号数量
            single_quotes = error_line.count("'") - error_line.count("\\'")
            double_quotes = error_line.count('"') - error_line.count('\\"')

            if single_quotes % 2 == 1:
                lines[line_index] = error_line + "'"
                error_info.fix_method = "添加缺失的单引号"
                return "\n".join(lines), True
            elif double_quotes % 2 == 1:
                lines[line_index] = error_line + '"'
                error_info.fix_method = "添加缺失的双引号"
                return "\n".join(lines), True

        # 修复缺少逗号
        if "invalid syntax" in error_msg and error_info.column:
            # 检查是否是列表或字典中缺少逗号
            col = error_info.column - 1
            if col < len(error_line) and col > 0:
                if error_line[col] in "]})" and error_line[col - 1] not in ",]})":
                    # 在可能缺少逗号的位置插入逗号
                    lines[line_index] = error_line[:col] + \
                        "," + error_line[col:]
                    error_info.fix_method = "添加缺失的逗号"
                    return "\n".join(lines), True

        # 修复未定义变量名
        if "name" in error_msg and "is not defined" in error_msg:
            # 尝试修正常见的拼写错误
            match = re.search(r"name '(\w+)' is not defined", error_msg)
            if match:
                var_name = match.group(1)
                # 常见的内置函数和关键字
                common_builtins = [
                    "print",
                    "len",
                    "range",
                    "str",
                    "int",
                    "float",
                    "list",
                    "dict",
                    "set",
                    "tuple",
                ]
                for builtin in common_builtins:
                    # 简单的编辑距离检查
                    if (
                        len(var_name) > 2
                        and builtin.startswith(var_name[0])
                        and builtin.endswith(var_name[-1])
                    ):
                        # 可能是拼写错误
                        lines[line_index] = error_line.replace(
                            var_name, builtin)
                        error_info.fix_method = (
                            f"修正可能的拼写错误: {var_name} -> {builtin}"
                        )
                        return "\n".join(lines), True

        # 修复多余的语法符号
        if "invalid syntax" in error_msg:
            # 检查多余的分号
            if error_line.strip().endswith(";"):
                lines[line_index] = error_line.rstrip(";")
                error_info.fix_method = "移除多余的分号"
                return "\n".join(lines), True

            # 尝试修复常见的Python 2/3语法差异问题
            if "print" in error_line and not error_line.strip().startswith("#"):
                if re.search(r"print\s+[^(]", error_line):
                    # 将Python 2风格的print转换为Python 3
                    modified_line = re.sub(
                        r"print\s+(.+)", r"print(\1)", error_line)
                    lines[line_index] = modified_line
                    error_info.fix_method = "转换Python 2风格的print为Python 3格式"
                    return "\n".join(lines), True

        return content, False

    def advanced_fix_file(self, file_path):
        """尝试修复文件中的复杂语法错误"""
        # 首先检查是否有语法错误
        error_info = self.check_syntax(file_path)
        if error_info is None:
            self.log(f"文件语法正确: {file_path}")
            return False

        self.log(f"\n发现错误: {file_path}")
        self.log(f"错误类型: {error_info.error_type}")
        self.log(f"错误信息: {error_info.error_message}")

        if error_info.line_number:
            self.log(f"错误行号: {error_info.line_number}")
        if error_info.source_line:
            self.log(f"错误行内容: {error_info.source_line}")

        # 更新统计数据
        self.stats["error_files"] += 1
        self.stats["error_types"][error_info.error_type] += 1

        # 创建备份
        if not self.backup_file(file_path):
            self.log(f"跳过修复 (无法创建备份): {file_path}")
            return False

        try:
            # 读取文件内容
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            fixed = False

            # 根据错误类型尝试不同的修复策略
            if error_info.error_type == "IndentationError":
                content, fixed = self.fix_indentation_error(
                    content, error_info)
            else:
                content, fixed = self.fix_syntax_error(content, error_info)

            if fixed:
                # 保存修复后的内容
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                # 验证修复是否成功
                if self.check_syntax(file_path) is None:
                    self.log(
                        f"成功修复: {file_path} (方法: {error_info.fix_method})")
                    # 更新统计数据
                    self.stats["fixed_files"] += 1
                    self.stats["fixed_types"][error_info.error_type] += 1
                    return True
                else:
                    self.log(f"修复尝试未能解决问题: {file_path}")
            else:
                self.log(f"无法修复: {file_path} (未找到适用的修复方法)")

        except Exception as e:
            self.log(f"修复过程中出错: {file_path} - {str(e)}")
            traceback.print_exc()

        return False

    def scan_and_fix_directory(self):
        """扫描目录并修复所有Python文件"""
        self.log(f"开始扫描目录: {self.root_dir}")

        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    self.stats["total_files"] += 1

                    if self.stats["total_files"] % 10 == 0:
                        self.log(f"已检查文件数: {self.stats['total_files']}...")

                    self.advanced_fix_file(file_path)

        self.log("\n== 修复完成 ==")
        self.log(f"检查的文件总数: {self.stats['total_files']}")
        self.log(f"有错误的文件数: {self.stats['error_files']}")
        self.log(f"成功修复的文件数: {self.stats['fixed_files']}")

        if self.stats["error_types"]:
            self.log("\n错误类型统计:")
            for error_type, count in self.stats["error_types"].items():
                fixed = self.stats["fixed_types"].get(error_type, 0)
                self.log(f"- {error_type}: {count} 个文件出错, {fixed} 个成功修复")

        return self.stats


def main():
    # 默认目录路径
    default_dir = r"C:\Users\tiger\Desktop\key\code\organized_project"

    # 使用命令行参数或默认路径
    directory = sys.argv[1] if len(sys.argv) > 1 else default_dir

    if not os.path.exists(directory):
        print(f"错误: 目录不存在 - {directory}")
        return

    # 创建修复器实例
    fixer = AdvancedPythonFixer(directory, verbose=True, create_backup=True)

    # 记录开始时间
    start_time = time.time()

    # 执行修复
    fixer.scan_and_fix_directory()

    # 计算总执行时间
    elapsed = time.time() - start_time
    print(f"总耗时: {elapsed:.2f} 秒")

    # 尝试运行测试脚本
    test_script = os.path.join(directory, "tests", "master_test.py")
    if os.path.exists(test_script):
        print("\n尝试运行测试脚本...")
        try:
            import subprocess

            result = subprocess.run(
                [sys.executable, test_script],
                check=False,
                capture_output=True,
                text=True,
            )
            print(result.stdout)
            if result.stderr:
                print("错误输出:", result.stderr)

            if result.returncode == 0:
                print("所有测试通过！系统已成功修复")
            else:
                print("测试未通过。请查看错误信息以进行进一步修复")
        except Exception as e:
            print(f"运行测试时出错: {str(e)}")
    else:
        print(f"测试脚本不存在: {test_script}")


if __name__ == "__main__":
    main()