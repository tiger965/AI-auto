#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单脚本：修复master_test.py的缩进问题
"""

import os

# 文件路径
file_path = (
    r"C:\Users\tiger\Desktop\key\code\organized_project\debug_tests\master_test.py"
)
backup_path = file_path + ".indent.bak"

# 创建备份
with open(file_path, "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

with open(backup_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"已备份原文件: {backup_path}")

# 读取文件
with open(file_path, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

# 修复缩进
fixed_lines = []
in_with_block = False
current_line_num = 0

for line in lines:
    current_line_num += 1

    # 检测with语句开始
    if "with open" in line and line.strip().endswith("as f:"):
        in_with_block = True
        fixed_lines.append(line)
        continue

    # 处理with块内的行
    if in_with_block and "f.write" in line:
        # 确保这一行有正确的缩进
        if not line.startswith("    "):
            line = "    " + line.lstrip()

    # 检测with块结束
    if in_with_block and (
        line.strip() == ""
        or (not "f.write" in line and not line.strip().startswith("#"))
    ):
        in_with_block = False

    fixed_lines.append(line)

# 保存修复后的文件
with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(fixed_lines)

print(f"文件已修复: {file_path}")
print("请尝试运行测试脚本")