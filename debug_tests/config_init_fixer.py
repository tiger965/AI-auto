#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Config/__init__.py文件修复工具
------------------------
专门修复config/__init__.py文件中的缩进错误
"""

import os
import sys
import logging
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ConfigFixer")


def fix_config_init():
    """修复config/__init__.py文件的缩进问题"""

    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 获取项目根目录
    project_root = os.path.dirname(script_dir)

    # 构建目标文件路径
    config_init_path = os.path.join(project_root, "config", "__init__.py")

    logger.info(f"准备修复文件: {config_init_path}")

    if not os.path.exists(config_init_path):
        logger.error(f"文件不存在: {config_init_path}")
        return False

    # 创建备份文件
    backup_path = config_init_path + ".before_fix.bak"
    try:
        shutil.copy2(config_init_path, backup_path)
        logger.info(f"已创建备份: {backup_path}")
    except Exception as e:
        logger.error(f"创建备份失败: {str(e)}")
        return False

    try:
        # 读取文件内容
        with open(config_init_path, "r", encoding="utf-8") as f:
            content = f.readlines()

        # 找到并修复第34行附近的缩进问题
        line_number = 34
        start_line = max(0, line_number - 5)
        end_line = min(len(content), line_number + 5)

        logger.info("问题代码上下文:")
        for i in range(start_line, end_line):
            logger.info(f"{i+1}: {content[i].rstrip()}")

        # 检查并修复第34行的缩进
        if line_number - 1 < len(content):
            problem_line = content[line_number - 1]

            # 检查是否存在缩进问题
            if problem_line.startswith(" ") and not problem_line.startswith("    "):
                # 修复缩进 - 规范化为4空格缩进
                fixed_line = problem_line.lstrip()  # 移除所有前导空格

                # 检查上下文
                if line_number - 2 >= 0:
                    previous_line = content[line_number - 2]
                    # 判断是否应该有缩进
                    if previous_line.strip().endswith(":"):
                        # 应该有一级缩进
                        fixed_line = "    " + fixed_line
                    else:
                        # 获取上一行的缩进
                        prev_indent = len(previous_line) - \
                            len(previous_line.lstrip())
                        fixed_line = " " * prev_indent + fixed_line

                # 更新内容
                content[line_number - 1] = fixed_line
                logger.info(f"已修复第{line_number}行:")
                logger.info(f"原始: {problem_line.rstrip()}")
                logger.info(f"修复: {fixed_line.rstrip()}")

        # 写回文件
        with open(config_init_path, "w", encoding="utf-8") as f:
            f.writelines(content)

        logger.info(f"文件已保存: {config_init_path}")

        # 测试修复后的文件
        try:
            with open(config_init_path, "r", encoding="utf-8") as f:
                new_content = f.read()

            # 尝试编译测试
            compile(new_content, config_init_path, "exec")
            logger.info("文件编译测试通过，修复成功")
            return True
        except IndentationError as e:
            logger.error(f"修复失败，文件仍有缩进错误: {str(e)}")

            # 恢复备份
            shutil.copy2(backup_path, config_init_path)
            logger.info(f"已恢复备份文件")
            return False
        except Exception as e:
            logger.error(f"修复后测试失败: {str(e)}")
            return False

    except Exception as e:
        logger.error(f"修复文件时出错: {str(e)}")

        # 尝试恢复备份
        try:
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, config_init_path)
                logger.info(f"已恢复备份文件")
        except:
            pass

        return False


def direct_edit_config_init():
    """直接编辑修复config/__init__.py文件"""

    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 获取项目根目录
    project_root = os.path.dirname(script_dir)

    # 构建目标文件路径
    config_init_path = os.path.join(project_root, "config", "__init__.py")

    logger.info(f"准备直接修复文件: {config_init_path}")

    if not os.path.exists(config_init_path):
        logger.error(f"文件不存在: {config_init_path}")
        return False

    # 创建备份文件
    backup_path = config_init_path + ".direct_edit.bak"
    try:
        shutil.copy2(config_init_path, backup_path)
        logger.info(f"已创建备份: {backup_path}")
    except Exception as e:
        logger.error(f"创建备份失败: {str(e)}")
        return False

    try:
        # 直接修复文件的方法 - 直接重写第34行周围的代码
        with open(config_init_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 定位到global config语句
        target_line = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("global config"):
                target_line = i
                break

        if target_line >= 0:
            # 修复global config行及其周围的缩进
            if target_line > 0:
                prev_line = lines[target_line - 1].rstrip()
                # 获取上一行的缩进
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                # 设置相同的缩进
                lines[target_line] = " " * prev_indent + "global config\n"

                logger.info(f"已修复第{target_line+1}行:")
                logger.info(f"修复前: {lines[target_line].rstrip()}")
                logger.info(f"修复后: {' ' * prev_indent + 'global config'}")

        # 写回文件
        with open(config_init_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        # 测试是否修复成功
        try:
            with open(config_init_path, "r", encoding="utf-8") as f:
                content = f.read()
            compile(content, config_init_path, "exec")
            logger.info("文件编译测试通过，修复成功")
            return True
        except Exception as e:
            logger.error(f"修复失败: {str(e)}")

            # 恢复备份
            shutil.copy2(backup_path, config_init_path)
            logger.info("已恢复备份文件")
            return False

    except Exception as e:
        logger.error(f"直接修复出错: {str(e)}")
        return False


def create_new_config_init():
    """创建一个新的config/__init__.py文件"""

    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 获取项目根目录
    project_root = os.path.dirname(script_dir)

    # 构建目标文件路径
    config_dir = os.path.join(project_root, "config")
    config_init_path = os.path.join(config_dir, "__init__.py")

    logger.info(f"准备创建新的config/__init__.py文件")

    # 确保config目录存在
    if not os.path.exists(config_dir):
        try:
            os.makedirs(config_dir)
            logger.info(f"已创建目录: {config_dir}")
        except Exception as e:
            logger.error(f"创建目录失败: {str(e)}")
            return False

    # 创建备份文件
    if os.path.exists(config_init_path):
        backup_path = config_init_path + ".orig.bak"
        try:
            shutil.copy2(config_init_path, backup_path)
            logger.info(f"已创建备份: {backup_path}")
        except Exception as e:
            logger.error(f"创建备份失败: {str(e)}")
            return False

    # 创建新的__init__.py文件
    try:
        with open(config_init_path, "w", encoding="utf-8") as f:
            f.write(
                """# -*- coding: utf-8 -*-
\"\"\"
配置模块
\"\"\"

import os
import json
import logging
from typing import Dict, Any, Optional

# 模块级变量
config = {}  # 全局配置对象
config_file = None  # 配置文件路径
logger = logging.getLogger(__name__)

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    \"\"\"
    加载配置文件
    
    Args:
        config_path: 配置文件路径，None则使用默认路径
        
    Returns:
        Dict: 配置字典
    \"\"\"
    global config
    
    # 确定配置文件路径
    if config_path is None:
        config_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(config_dir, 'config.json')
    
    # 记录配置文件路径
    global config_file
    config_file = config_path
    
    # 读取配置文件
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"配置已加载: {config_path}")
    except FileNotFoundError:
        logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
        config = get_default_config()
    except json.JSONDecodeError:
        logger.error(f"配置文件格式错误: {config_path}，使用默认配置")
        config = get_default_config()
    except Exception as e:
        logger.error(f"加载配置失败: {str(e)}，使用默认配置")
        config = get_default_config()
    
    return config

def get_default_config() -> Dict[str, Any]:
    \"\"\"
    获取默认配置
    
    Returns:
        Dict: 默认配置字典
    \"\"\"
    return {
        "app_name": "AI自动化系统",
        "version": "1.0.0",
        "debug": True,
        "log_level": "info",
        "api": {
            "enabled": True,
            "port": 8000,
            "host": "127.0.0.1"
        },
        "paths": {
            "data": "data",
            "logs": "logs",
            "temp": "temp"
        }
    }

def save_config() -> bool:
    \"\"\"
    保存配置到文件
    
    Returns:
        bool: 是否成功
    \"\"\"
    global config, config_file
    
    if config_file is None:
        logger.error("未指定配置文件路径")
        return False
    
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        # 写入配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        logger.info(f"配置已保存: {config_file}")
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")
        return False

def get_config() -> Dict[str, Any]:
    \"\"\"
    获取当前配置
    
    Returns:
        Dict: 配置字典
    \"\"\"
    global config
    return config

def update_config(key: str, value: Any) -> None:
    \"\"\"
    更新配置项
    
    Args:
        key: 配置键
        value: 配置值
    \"\"\"
    global config
    config[key] = value

# 初始化时加载配置
if not config:
    load_config()
"""
            )

        logger.info(f"已创建新的config/__init__.py文件")

        # 测试新文件
        try:
            with open(config_init_path, "r", encoding="utf-8") as f:
                content = f.read()
            compile(content, config_init_path, "exec")
            logger.info("新文件编译测试通过")
            return True
        except Exception as e:
            logger.error(f"新文件测试失败: {str(e)}")
            return False

    except Exception as e:
        logger.error(f"创建新文件失败: {str(e)}")
        return False


def main():
    """主函数"""
    logger.info("=== 开始修复config/__init__.py文件 ===")

    # 首先尝试使用修复方法
    if fix_config_init():
        logger.info("修复成功!")
        return 0

    # 如果修复失败，尝试直接编辑
    logger.info("尝试使用直接编辑方法...")
    if direct_edit_config_init():
        logger.info("直接编辑修复成功!")
        return 0

    # 如果仍然失败，创建新文件
    logger.info("尝试创建新文件...")
    if create_new_config_init():
        logger.info("创建新文件成功!")
        return 0

    logger.error("所有修复方法都失败")
    return 1


if __name__ == "__main__":
    sys.exit(main())