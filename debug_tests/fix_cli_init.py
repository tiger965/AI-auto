#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI CLI __init__.py 一键修复脚本
---------------------------
自动修复 ui/cli/__init__.py 文件中缺少的 except 或 finally 块
"""

import os
import sys
import shutil
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("CLIInitFixer")


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


def fix_cli_init():
    """修复 ui/cli/__init__.py 文件"""
    # 查找项目根目录
    project_root = find_project_root()

    # 目标文件路径
    cli_init_path = os.path.join(project_root, "ui", "cli", "__init__.py")

    if not os.path.exists(cli_init_path):
        logger.error(f"无法找到文件: {cli_init_path}")
        return False

    # 创建备份
    backup_path = f"{cli_init_path}.before_fix.bak"
    try:
        shutil.copy2(cli_init_path, backup_path)
        logger.info(f"已创建备份: {backup_path}")

        # 读取原始内容
        with open(cli_init_path, "r", encoding="utf-8") as f:
            content = f.readlines()

        # 查找并修复问题（第25行附近的try语句块）
        fixed_content = []
        i = 0
        while i < len(content):
            line = content[i]
            fixed_content.append(line)

            # 查找第25行附近的try语句
            if i + 1 == 25 or (i >= 20 and i <= 30 and "try:" in line.strip()):
                j = i + 1
                block_content = []

                # 收集try块中的内容
                while j < len(content) and not (
                    content[j].strip().startswith("except")
                    or content[j].strip().startswith("finally")
                ):
                    block_content.append(content[j])
                    j += 1

                # 检查是否没有except或finally
                if j >= len(content) or (
                    not content[j].strip().startswith("except")
                    and not content[j].strip().startswith("finally")
                ):
                    # 添加try块中的内容
                    for block_line in block_content:
                        fixed_content.append(block_line)

                    # 添加缺少的except块
                    fixed_content.append("    except Exception as e:\n")
                    fixed_content.append(
                        '        logger.error(f"CLI初始化错误: {str(e)}")\n'
                    )

                    i = j - 1  # 调整索引，跳过已处理的内容
                else:
                    # 如果已经有except或finally，直接添加try块中的内容
                    for block_line in block_content:
                        fixed_content.append(block_line)
                    i = j - 1  # 调整索引

            i += 1

        # 写入修复后的内容
        with open(cli_init_path, "w", encoding="utf-8") as f:
            f.writelines(fixed_content)

        logger.info(f"已修复文件: {cli_init_path}")

        # 验证修复是否成功
        try:
            # 尝试编译文件验证语法
            with open(cli_init_path, "r", encoding="utf-8") as f:
                compile(f.read(), cli_init_path, "exec")
            logger.info("文件编译测试通过，修复成功")
            return True
        except Exception as e:
            logger.error(f"修复失败，文件编译测试不通过: {str(e)}")
            # 恢复备份
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, cli_init_path)
                logger.info("已恢复原文件")
            return False

    except Exception as e:
        logger.error(f"修复过程中出错: {str(e)}")
        return False


if __name__ == "__main__":
    logger.info("开始一键修复 ui/cli/__init__.py")
    success = fix_cli_init()
    if success:
        logger.info("修复成功！现在应该可以正常启动系统了。")
    else:
        logger.error("修复失败，请尝试手动编辑文件修复问题。")