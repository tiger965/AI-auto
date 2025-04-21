#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI交易系统缓存管理工具
-------------------
自动整理项目中的.bak和缓存文件
"""

import os
import shutil
import sys
import time
from datetime import datetime

# 项目根目录(脚本所在位置的上一级目录)
script_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = (
    os.path.dirname(script_dir) if "debug_tests" in script_dir else script_dir
)

# 缓存目录
CACHE_DIR = os.path.join(PROJECT_ROOT, "system", "cache")

# 缓存类型
CACHE_TYPES = {
    "bak": [".bak", ".backup", ".old"],
    "pyc": [".pyc", ".pyo"],
    "pycache": ["__pycache__"],
    "import": [".import.bak"],
}


def log(message):
    """输出日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} - {message}")


def find_cache_files():
    """查找所有缓存文件"""
    log(f"正在扫描项目目录: {PROJECT_ROOT}")

    cache_files = {cache_type: [] for cache_type in CACHE_TYPES}

    for root, dirs, files in os.walk(PROJECT_ROOT):
        # 跳过缓存目录自身
        if os.path.normpath(root).startswith(os.path.normpath(CACHE_DIR)):
            continue

        # 查找匹配的文件
        for file in files:
            for cache_type, extensions in CACHE_TYPES.items():
                for ext in extensions:
                    if ext.startswith(".") and file.endswith(ext):
                        cache_files[cache_type].append(
                            os.path.join(root, file))

        # 查找匹配的目录
        for dir_name in list(dirs):
            for cache_type, patterns in CACHE_TYPES.items():
                for pattern in patterns:
                    if not pattern.startswith(".") and dir_name == pattern:
                        cache_files[cache_type].append(
                            os.path.join(root, dir_name))
                        dirs.remove(dir_name)  # 避免进入已匹配的目录
                        break

    return cache_files


def move_to_cache_dir(files, cache_type):
    """移动文件到缓存目录"""
    type_cache_dir = os.path.join(CACHE_DIR, cache_type)
    if not os.path.exists(type_cache_dir):
        os.makedirs(type_cache_dir, exist_ok=True)

    moved_files = 0
    for file_path in files:
        try:
            if os.path.isdir(file_path):
                # 处理目录
                dir_name = os.path.basename(file_path)
                parent_path = os.path.dirname(file_path)
                relative_path = os.path.relpath(parent_path, PROJECT_ROOT)
                target_dir = os.path.join(
                    type_cache_dir, relative_path, dir_name)

                if os.path.exists(target_dir):
                    shutil.rmtree(target_dir)

                os.makedirs(os.path.dirname(target_dir), exist_ok=True)
                shutil.move(file_path, target_dir)
                log(f"已移动目录: {file_path} -> {target_dir}")
                moved_files += 1
            else:
                # 处理文件
                file_name = os.path.basename(file_path)
                parent_path = os.path.dirname(file_path)
                relative_path = os.path.relpath(parent_path, PROJECT_ROOT)
                target_path = os.path.join(
                    type_cache_dir, relative_path, file_name)

                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                if os.path.exists(target_path):
                    os.remove(target_path)

                shutil.move(file_path, target_path)
                log(f"已移动文件: {file_path} -> {target_path}")
                moved_files += 1
        except Exception as e:
            log(f"处理失败: {file_path}, 错误: {str(e)}")

    return moved_files


def clean_empty_dirs():
    """清理空目录"""
    empty_dirs = []
    for root, dirs, files in os.walk(PROJECT_ROOT, topdown=False):
        # 跳过缓存目录自身
        if os.path.normpath(root).startswith(os.path.normpath(CACHE_DIR)):
            continue

        if not files and not dirs:
            empty_dirs.append(root)

    removed_dirs = 0
    for dir_path in empty_dirs:
        try:
            os.rmdir(dir_path)
            log(f"已删除空目录: {dir_path}")
            removed_dirs += 1
        except Exception as e:
            log(f"删除目录失败: {dir_path}, 错误: {str(e)}")

    return removed_dirs


def main():
    """主函数"""
    log("=== AI交易系统缓存管理工具 ===")
    log(f"项目根目录: {PROJECT_ROOT}")
    log(f"缓存目录: {CACHE_DIR}")

    # 确保缓存目录存在
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)
        log(f"已创建缓存目录: {CACHE_DIR}")

    # 查找缓存文件
    cache_files = find_cache_files()
    total_files = sum(len(files) for files in cache_files.values())

    if total_files == 0:
        log("未发现缓存文件，操作完成")
        return

    log(f"找到 {total_files} 个缓存文件/目录:")
    for cache_type, files in cache_files.items():
        log(f"- {cache_type}: {len(files)} 个")

    # 确认操作
    confirm = input(f"\n是否将这些文件移动到缓存目录? (y/n): ")
    if confirm.lower() != "y":
        log("操作已取消")
        return

    # 处理各类型缓存文件
    moved_total = 0
    for cache_type, files in cache_files.items():
        moved = move_to_cache_dir(files, cache_type)
        moved_total += moved
        log(f"已处理 '{cache_type}' 类型: {moved}/{len(files)} 个文件")

    # 清理空目录
    removed_dirs = clean_empty_dirs()
    log(f"已清理 {removed_dirs} 个空目录")

    log("=== 操作完成 ===")
    log(f"总处理文件: {moved_total}/{total_files}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n操作已取消")
    except Exception as e:
        log(f"发生错误: {str(e)}")
        import traceback

        traceback.print_exc()