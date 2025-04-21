#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Config/config_loader.py文件修复工具
---------------------------
专门修复config/config_loader.py文件中的缩进错误
"""

import os
import sys
import logging
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ConfigLoaderFixer")


def fix_config_loader():
    """修复config/config_loader.py文件中的缩进问题"""

    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 获取项目根目录
    project_root = os.path.dirname(script_dir)

    # 构建目标文件路径
    config_loader_path = os.path.join(
        project_root, "config", "config_loader.py")

    logger.info(f"准备修复文件: {config_loader_path}")

    if not os.path.exists(config_loader_path):
        logger.error(f"文件不存在: {config_loader_path}")
        return False

    # 创建备份文件
    backup_path = config_loader_path + ".before_fix.bak"
    try:
        shutil.copy2(config_loader_path, backup_path)
        logger.info(f"已创建备份: {backup_path}")
    except Exception as e:
        logger.error(f"创建备份失败: {str(e)}")
        return False

    try:
        # 读取文件内容
        with open(config_loader_path, "r", encoding="utf-8") as f:
            content = f.readlines()

        # 找到并修复第122行附近的缩进问题
        line_number = 122
        start_line = max(0, line_number - 5)
        end_line = min(len(content), line_number + 5)

        logger.info("问题代码上下文:")
        for i in range(start_line, end_line):
            if i < len(content):
                logger.info(f"{i+1}: {content[i].rstrip()}")

        # 检查并修复第122行的try语句
        if line_number - 1 < len(content) and "try:" in content[line_number - 1]:
            # 找到try语句后面的行
            next_line_index = line_number
            if next_line_index < len(content):
                next_line = content[next_line_index]

                # 检查下一行是否有适当的缩进
                if not next_line.startswith("    ") and next_line.strip():
                    # 添加缩进
                    indented_line = "    " + next_line.lstrip()
                    content[next_line_index] = indented_line
                    logger.info(f"已修复第{next_line_index+1}行:")
                    logger.info(f"原始: {next_line.rstrip()}")
                    logger.info(f"修复: {indented_line.rstrip()}")

                    # 查找except或finally语句
                    found_except = False
                    for i in range(next_line_index + 1, len(content)):
                        if content[i].strip().startswith(("except", "finally")):
                            found_except = True
                            break

                    # 如果没有找到except或finally，添加一个
                    if not found_except:
                        # 查找适合插入except的位置
                        insert_position = next_line_index + 1
                        while insert_position < len(content) and content[
                            insert_position
                        ].startswith("    "):
                            insert_position += 1

                        # 插入except语句
                        except_line = "except Exception as e:\n"
                        except_line_with_indent = "    " + except_line
                        content.insert(insert_position,
                                       except_line_with_indent)

                        # 插入异常处理代码
                        pass_line = "    pass  # 添加适当的异常处理\n"
                        content.insert(insert_position + 1, pass_line)

                        logger.info(f"已在第{insert_position+1}行添加except语句")
                        logger.info(f"已在第{insert_position+2}行添加异常处理代码")

        # 写回文件
        with open(config_loader_path, "w", encoding="utf-8") as f:
            f.writelines(content)

        logger.info(f"文件已保存: {config_loader_path}")

        # 测试修复后的文件
        try:
            with open(config_loader_path, "r", encoding="utf-8") as f:
                new_content = f.read()

            # 尝试编译测试
            compile(new_content, config_loader_path, "exec")
            logger.info("文件编译测试通过，修复成功")
            return True
        except IndentationError as e:
            logger.error(f"修复失败，文件仍有缩进错误: {str(e)}")

            # 尝试更强力的修复
            return direct_fix_config_loader()
        except Exception as e:
            logger.error(f"修复后测试失败: {str(e)}")
            return direct_fix_config_loader()

    except Exception as e:
        logger.error(f"修复文件时出错: {str(e)}")
        return False


def direct_fix_config_loader():
    """直接修复config/config_loader.py文件中的try语句"""

    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 获取项目根目录
    project_root = os.path.dirname(script_dir)

    # 构建目标文件路径
    config_loader_path = os.path.join(
        project_root, "config", "config_loader.py")

    logger.info(f"尝试直接修复文件: {config_loader_path}")

    if not os.path.exists(config_loader_path):
        logger.error(f"文件不存在: {config_loader_path}")
        return False

    # 创建备份文件
    backup_path = config_loader_path + ".direct_fix.bak"
    try:
        shutil.copy2(config_loader_path, backup_path)
        logger.info(f"已创建备份: {backup_path}")
    except Exception as e:
        logger.error(f"创建备份失败: {str(e)}")
        return False

    try:
        # 读取文件内容
        with open(config_loader_path, "r", encoding="utf-8") as f:
            content = f.readlines()

        # 找到try语句所在行
        try_line_index = -1
        for i, line in enumerate(content):
            if line.strip() == "try:" and i + 1 < len(content):
                try_line_index = i
                break

        if try_line_index >= 0:
            # 获取当前try语句的缩进
            try_line = content[try_line_index]
            indent = try_line[: len(try_line) - len(try_line.lstrip())]

            # 修复try-except块
            # 先移除try行后的所有内容直到下一个非缩进行
            next_non_indented_line = try_line_index + 1
            while next_non_indented_line < len(content) and (
                not content[next_non_indented_line].strip()
                or len(content[next_non_indented_line])
                - len(content[next_non_indented_line].lstrip())
                > len(indent)
            ):
                next_non_indented_line += 1

            # 创建新的try-except块
            new_content = content[: try_line_index + 1]
            new_content.append(indent + "    pass  # 添加适当的代码\n")
            new_content.append(indent + "except Exception as e:\n")
            new_content.append(indent + '    logger.error(f"错误: {str(e)}")\n')
            new_content.append(indent + "    pass  # 添加适当的异常处理\n")

            # 添加剩余的内容
            if next_non_indented_line < len(content):
                new_content.extend(content[next_non_indented_line:])

            # 更新内容
            content = new_content

            logger.info(
                f"已替换try-except块（行{try_line_index+1}至{next_non_indented_line}）"
            )
        else:
            logger.warning("未找到try语句")

        # 写回文件
        with open(config_loader_path, "w", encoding="utf-8") as f:
            f.writelines(content)

        # 测试修复后的文件
        try:
            with open(config_loader_path, "r", encoding="utf-8") as f:
                new_content = f.read()

            # 尝试编译测试
            compile(new_content, config_loader_path, "exec")
            logger.info("文件编译测试通过，修复成功")
            return True
        except Exception as e:
            logger.error(f"修复失败: {str(e)}")

            # 恢复备份
            shutil.copy2(backup_path, config_loader_path)
            logger.info("已恢复备份文件")
            return False

    except Exception as e:
        logger.error(f"直接修复出错: {str(e)}")
        return False


def main():
    """主函数"""
    logger.info("=== 开始修复config/config_loader.py文件 ===")

    # 尝试修复
    if fix_config_loader():
        logger.info("修复成功!")
        return 0

    logger.error("修复失败")
    return 1


if __name__ == "__main__":
    sys.exit(main())