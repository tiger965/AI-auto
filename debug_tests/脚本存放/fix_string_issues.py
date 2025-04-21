#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复Python Triple-Quoted F-String错误
专门用于修复未闭合的三引号f-string问题
"""

import os
import sys
import re
import traceback


def fix_unterminated_fstring(file_path):
    """修复未闭合的三引号f-string"""
    print(f"正在处理文件: {file_path}")

    try:
        # 读取文件内容
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        # 创建备份
        backup_path = file_path + ".fstring.bak"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        fixed = False
        # 查找并修复f-string问题
        for i in range(len(lines)):
            # 检查是否是f-string开始
            if 'f"""' in lines[i] or "f'''" in lines[i]:
                # 判断是否有对应的结束引号
                has_end_quotes = False

                # 检查当前行是否有结束引号
                if (
                    '"""' in lines[i].split('f"""', 1)[1]
                    or "'''" in lines[i].split("f'''", 1)[1]
                ):
                    has_end_quotes = True

                # 如果当前行没有结束引号，检查后续行
                if not has_end_quotes:
                    # 确定使用的是哪种引号
                    quote_type = '"""' if 'f"""' in lines[i] else "'''"

                    # 寻找匹配的结束引号
                    j = i + 1
                    while j < len(lines) and quote_type not in lines[j]:
                        j += 1

                    # 如果没有找到结束引号，添加一个
                    if j >= len(lines):
                        print(
                            f"发现未闭合的f-string，开始于第{i+1}行: {lines[i].strip()}"
                        )
                        lines[i] = lines[i].rstrip() + " " + quote_type + "\n"
                        print(f"修复后: {lines[i].strip()}")
                        fixed = True

        # 如果文件被修改，保存更新后的内容
        if fixed:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            print(f"文件已成功修复: {file_path}")
        else:
            # 尝试更深入的分析和修复
            content = "".join(lines)
            # 特殊处理第45行问题
            match = re.search(r'(f""".*?)(?:"""|\Z)', content, re.DOTALL)
            if match and '"""' not in match.group(1):
                modified_content = content.replace(
                    match.group(1), match.group(1) + '"""'
                )
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(modified_content)
                print(f"已修复特殊情况: 添加缺失的结束引号")
                fixed = True

            if not fixed:
                print(f"未发现需要修复的问题，或者问题过于复杂无法自动修复")

        return fixed

    except Exception as e:
        print(f"修复过程中出错: {str(e)}")
        traceback.print_exc()
        return False


def fix_specific_line(file_path, line_number, error_message):
    """修复特定行的错误"""
    print(f"尝试修复文件 {file_path} 的第 {line_number} 行")

    try:
        # 读取文件内容
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        # 创建备份
        backup_path = file_path + ".line.bak"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        # 确保行号在有效范围内
        if line_number <= 0 or line_number > len(lines):
            print(f"行号 {line_number} 超出文件范围")
            return False

        # 获取需要修复的行
        line_index = line_number - 1
        problem_line = lines[line_index]

        print(f"原始行: {problem_line.strip()}")

        # 根据错误类型进行修复
        if "unterminated triple-quoted f-string literal" in error_message:
            # 检查是使用的哪种引号
            if 'f"""' in problem_line:
                quote_type = '"""'
            elif "f'''" in problem_line:
                quote_type = "'''"
            else:
                # 可能是在多行中间，向上寻找开始的引号
                prev_index = line_index - 1
                while prev_index >= 0:
                    if 'f"""' in lines[prev_index]:
                        quote_type = '"""'
                        break
                    elif "f'''" in lines[prev_index]:
                        quote_type = "'''"
                        break
                    prev_index -= 1

                if prev_index < 0:
                    print("无法确定引号类型")
                    return False

            # 添加缺失的结束引号
            lines[line_index] = problem_line.rstrip() + " " + quote_type + "\n"
            print(f"修复后: {lines[line_index].strip()}")

            # 保存修复后的文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            print(f"文件已成功修复: {file_path}")
            return True

        # 如果是其他类型的错误，可以在这里添加更多的处理逻辑

        print("未知错误类型，无法自动修复")
        return False

    except Exception as e:
        print(f"修复过程中出错: {str(e)}")
        traceback.print_exc()
        return False


def fix_f_write_issue(file_path, line_number):
    """修复f.write(f"...")问题"""
    print(f"尝试修复文件 {file_path} 的第 {line_number} 行的f.write问题")

    try:
        # 读取文件内容
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        # 创建备份
        backup_path = file_path + ".fwrite.bak"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        # 确保行号在有效范围内
        if line_number <= 0 or line_number > len(lines):
            print(f"行号 {line_number} 超出文件范围")
            return False

        # 获取需要修复的行
        line_index = line_number - 1
        problem_line = lines[line_index]

        print(f"原始行: {problem_line.strip()}")

        # 检查是否是f.write问题
        if "f.write(f" in problem_line:
            # 修复方法1：替换为正常字符串
            fixed_line = problem_line.replace('f.write(f"', 'f.write("')

            # 如果这不起作用，尝试修复方法2
            if fixed_line == problem_line:
                # 查找引号
                start_pos = problem_line.find('f.write(f"')
                if start_pos >= 0:
                    # 移除f前缀
                    fixed_line = (
                        problem_line[:start_pos]
                        + 'f.write("'
                        + problem_line[start_pos + 9:]
                    )

            lines[line_index] = fixed_line
            print(f"修复后: {lines[line_index].strip()}")

            # 保存修复后的文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            print(f"文件已成功修复: {file_path}")
            return True

        print("未发现f.write问题，无法修复")
        return False

    except Exception as e:
        print(f"修复过程中出错: {str(e)}")
        traceback.print_exc()
        return False


def main():
    """主函数"""

    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法: python fix_fstring_quotes.py <文件路径> [<行号> [<错误信息>]]")
        return

    file_path = sys.argv[1]

    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        return

    # 如果提供了行号和错误信息，尝试修复特定行
    if len(sys.argv) >= 3:
        try:
            line_number = int(sys.argv[2])
            error_message = sys.argv[3] if len(sys.argv) >= 4 else ""

            # 检查是否是f.write问题
            if "f.write(f" in error_message:
                fix_f_write_issue(file_path, line_number)
            else:
                fix_specific_line(file_path, line_number, error_message)

        except ValueError:
            print(f"错误: 无效的行号 - {sys.argv[2]}")
            return
    else:
        # 尝试修复整个文件
        fix_unterminated_fstring(file_path)


if __name__ == "__main__":
    main()