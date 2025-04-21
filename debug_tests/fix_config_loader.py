#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
config_loader.py 一键修复安装脚本
--------------------------------
自动修复 config_loader.py 文件
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
logger = logging.getLogger("ConfigLoaderFixer")

# 修复后的 config_loader.py 内容
CONFIG_LOADER_CONTENT = """
\"\"\"
配置加载器模块

该模块提供通用的配置加载功能，支持JSON和YAML格式的配置文件，
并实现了配置缓存、错误处理和验证机制。
\"\"\"
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
import os
import json
import logging
from functools import lru_cache

# 配置缓存
_config_cache = {}

def clear_config_cache() -> None:
    \"\"\"清除配置缓存\"\"\"
    global _config_cache
    _config_cache = {}
    logging.info("配置缓存已清除")

def load_config(
    config_type: str,
    environment: str = "development",
    config_dir: Optional[Path] = None,
    validators: Optional[List[Callable[[Dict[str, Any]], None]]] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    \"\"\"
    加载指定类型和环境的配置
    
    参数:
        config_type: 配置类型标识符
        environment: 环境名称，默认为"development"
        config_dir: 配置文件目录，默认为当前目录下的"config_files"
        validators: 配置验证器列表
        use_cache: 是否使用缓存，默认为True
        
    返回:
        合并后的配置字典
    \"\"\"
    # 使用缓存
    cache_key = f"{config_type}_{environment}"
    if use_cache and cache_key in _config_cache:
        return _config_cache[cache_key]
    
    if config_dir is None:
        config_dir = Path(__file__).parent / "config_files"
    
    try:
        # 创建配置目录（如果不存在）
        os.makedirs(config_dir, exist_ok=True)
        
        # 基础配置
        base_config = _load_file(config_dir / f"base_{config_type}.json")
        
        # 环境特定配置
        env_config = None
        
        # 尝试加载JSON配置
        json_file = config_dir / f"{environment}_{config_type}.json"
        if json_file.exists():
            env_config = _load_file(json_file)
        
        # 尝试加载YAML配置（如果JSON不存在）
        if env_config is None:
            yaml_file = config_dir / f"{environment}_{config_type}.yaml"
            if yaml_file.exists():
                env_config = load_yaml_config(str(yaml_file))
            else:
                yml_file = config_dir / f"{environment}_{config_type}.yml"
                if yml_file.exists():
                    env_config = load_yaml_config(str(yml_file))
        
        # 合并配置
        result = base_config.copy() if base_config else {}
        if env_config:
            deep_merge(result, env_config)
        
        # 验证配置
        if validators:
            for validator in validators:
                validator(result)
        
        # 存入缓存
        if use_cache:
            _config_cache[cache_key] = result
        
        return result
    
    except Exception as e:
        logging.error(f"加载配置失败 ({config_type}, {environment}): {str(e)}")
        # 返回空配置而不是抛出异常，以确保应用可以继续运行
        return {}

def _load_file(file_path: Path) -> Dict[str, Any]:
    \"\"\"加载配置文件\"\"\"
    try:
        if not file_path.exists():
            return {}
            
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                return load_yaml_config(str(file_path))
            else:
                return json.load(f)
    except Exception as e:
        logging.error(f"加载文件失败 ({file_path}): {str(e)}")
        return {}

def load_yaml_config(file_path: str) -> Dict[str, Any]:
    \"\"\"
    加载YAML配置文件
    
    参数:
        file_path: YAML文件路径
        
    返回:
        配置字典
    \"\"\"
    try:
        # 惰性导入yaml模块，避免不必要的依赖
        import yaml
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        logging.error("加载YAML配置失败: 缺少yaml模块。请使用pip install pyyaml安装")
        return {}
    except Exception as e:
        logging.error(f"加载YAML配置失败 ({file_path}): {str(e)}")
        return {}

def deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    \"\"\"
    深度合并两个字典
    
    参数:
        target: 目标字典（会被修改）
        source: 源字典（保持不变）
    \"\"\"
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_merge(target[key], value)
        else:
            target[key] = value

def get_standardized_env_var_name(key: str) -> str:
    \"\"\"
    获取标准化的环境变量名
    
    参数:
        key: 原始键名
        
    返回:
        标准化的环境变量名
    \"\"\"
    from config import ENV_PREFIX
    # 转换为大写并替换点和空格为下划线
    std_key = key.upper().replace(".", "_").replace(" ", "_")
    # 添加全局前缀
    return f"{ENV_PREFIX}_{std_key}" if ENV_PREFIX else std_key

@lru_cache(maxsize=32)
def get_config_directories() -> Dict[str, Path]:
    \"\"\"
    获取配置目录结构
    
    返回:
        包含各种配置目录路径的字典
    \"\"\"
    base_dir = Path(__file__).parent
    
    return {
        "base": base_dir,
        "config_files": base_dir / "config_files",
        "environments": base_dir / "environments",
        "secure": base_dir / "secure"
    }

def create_config_directories() -> None:
    \"\"\"创建配置目录结构\"\"\"
    directories = get_config_directories()
    
    for dir_path in directories.values():
        os.makedirs(dir_path, exist_ok=True)
        
    logging.info("已创建配置目录结构")
"""


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


def fix_config_loader():
    """修复 config_loader.py 文件"""
    # 查找项目根目录
    project_root = find_project_root()

    # 目标文件路径
    config_loader_path = os.path.join(
        project_root, "config", "config_loader.py")

    # 创建备份
    backup_path = f"{config_loader_path}.one_click_fix.bak"
    try:
        if os.path.exists(config_loader_path):
            shutil.copy2(config_loader_path, backup_path)
            logger.info(f"已创建备份: {backup_path}")

        # 写入修复后的内容
        with open(config_loader_path, "w", encoding="utf-8") as f:
            f.write(CONFIG_LOADER_CONTENT.strip())

        logger.info(f"已修复文件: {config_loader_path}")

        # 验证修复是否成功
        try:
            # 尝试编译文件验证语法
            with open(config_loader_path, "r", encoding="utf-8") as f:
                compile(f.read(), config_loader_path, "exec")
            logger.info("文件编译测试通过，修复成功")
            return True
        except Exception as e:
            logger.error(f"修复失败，文件编译测试不通过: {str(e)}")
            # 恢复备份
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, config_loader_path)
                logger.info("已恢复原文件")
            return False

    except Exception as e:
        logger.error(f"修复过程中出错: {str(e)}")
        return False


if __name__ == "__main__":
    logger.info("开始一键修复 config_loader.py")
    success = fix_config_loader()
    if success:
        logger.info("修复成功！")
    else:
        logger.error("修复失败，请查看日志了解详情")