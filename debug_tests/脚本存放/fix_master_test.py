#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
一键修复master_test.py脚本
该脚本会备份原文件并创建一个新的修复版
"""

import os
import shutil
import re
from datetime import datetime


def fix_master_test():
    # 文件路径
    file_path = (
        r"C:\Users\tiger\Desktop\key\code\organized_project\debug_tests\master_test.py"
    )
    backup_path = file_path + ".backup"

    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        return False

    # 创建备份
    try:
        shutil.copy2(file_path, backup_path)
        print(f"已创建备份: {backup_path}")
    except Exception as e:
        print(f"创建备份时出错: {e}")
        return False

    # 读取文件内容
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return False

    # 修复第424行附近的问题 (f-string问题)
    pattern = r'with open\(f"{full_path}\.py", \'w\'\) as f:(.*?)class'
    replacement = """with open(f"{full_path}.py", 'w') as f:
    f.write(f"# 自动生成的{module_name}模块\\n")
    f.write("\"\"\"\\n")
    f.write(f"{module_name}模块\\n")
    f.write(f"自动生成于{datetime.now()}\\n")
    f.write("\"\"\"\\n")

class"""

    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # 修复class定义行的问题
    class_pattern = r"class\s+{module_name\.split\(\'.\'\)\[-1\]\.capitalize\(\)}:"
    class_replacement = "class ModuleClass:"
    content = re.sub(class_pattern, class_replacement, content)

    # 修复docstring问题
    content = content.replace('\\"\\"\\"自动生成的类\\"\\"\\"', '"""自动生成的类"""')
    content = content.replace('\\"\\"\\"初始化\\"\\"\\"', '"""初始化"""')
    content = content.replace('\\"\\"\\"示例方法1\\"\\"\\"', '"""示例方法1"""')

    # 修复打印语句问题
    print_pattern = (
        r'print\(f"{module_name\.split\(\'.\'\)\[-1\]\.capitalize\(\)}初始化"\)'
    )
    print_replacement = 'print("ModuleClass初始化")'
    content = re.sub(print_pattern, print_replacement, content)

    # 保存修复后的文件
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"文件已成功修复: {file_path}")
        return True
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return False


if __name__ == "__main__":
    fix_master_test()
    print("\n修复完成！请尝试运行测试脚本")
    print("如果修复不成功，原文件备份在 .backup 文件中")