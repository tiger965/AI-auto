#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统缓存与备份文件自动清理任务
-----------------------------
此脚本自动清理项目中的缓存和备份文件，包括.bak、.pyc和__pycache__目录等。
通过系统调度器定期执行，保持项目结构整洁。
"""

from system import scheduler
from system import cache
import os
import sys
import time
import logging
import shutil
import datetime
from typing import Dict, List, Set, Tuple

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入系统模块

# 配置日志
logger = logging.getLogger(__name__)

# 缓存文件类型定义
CACHE_TYPES = {
    "bak": [".bak", ".backup", ".old", ".import.bak", ".line.bak", ".indent.bak"],
    "pyc": [".pyc", ".pyo"],
    "pycache": ["__pycache__"],
    "temp": [".tmp", ".temp"],
}

# 缓存目录路径
CACHE_DIR = os.path.join(project_root, "system", "cache")


class BackupFileCleaner:
    """备份文件清理器类"""

    def __init__(self, cache_dir: str = None):
        """
        初始化备份文件清理器

        Args:
            cache_dir: 缓存目录路径，默认为system/cache
        """
        self.cache_dir = cache_dir or CACHE_DIR
        self.stats = {
            "processed_files": 0,
            "moved_files": 0,
            "deleted_files": 0,
            "cleaned_dirs": 0,
            "errors": 0,
        }

        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)

        # 创建缓存类型子目录
        for cache_type in CACHE_TYPES:
            os.makedirs(os.path.join(self.cache_dir,
                        cache_type), exist_ok=True)

    def find_cache_files(self, search_dir: str = None) -> Dict[str, List[str]]:
        """
        查找所有缓存文件

        Args:
            search_dir: 搜索目录，默认为项目根目录

        Returns:
            Dict[str, List[str]]: 按类型分类的缓存文件列表
        """
        search_dir = search_dir or project_root
        result = {cache_type: [] for cache_type in CACHE_TYPES}

        logger.info(f"开始扫描目录: {search_dir}")

        for root, dirs, files in os.walk(search_dir):
            # 跳过缓存目录自身
            if os.path.abspath(root).startswith(os.path.abspath(self.cache_dir)):
                continue

            # 跳过.git目录
            if ".git" in root:
                continue

            # 查找匹配的文件
            for file in files:
                file_path = os.path.join(root, file)
                self.stats["processed_files"] += 1

                for cache_type, extensions in CACHE_TYPES.items():
                    for ext in extensions:
                        if ext.startswith(".") and file.endswith(ext):
                            result[cache_type].append(file_path)

            # 查找匹配的目录
            for dir_name in list(dirs):
                dir_path = os.path.join(root, dir_name)

                for cache_type, patterns in CACHE_TYPES.items():
                    for pattern in patterns:
                        if not pattern.startswith(".") and dir_name == pattern:
                            result[cache_type].append(dir_path)
                            # 从dirs中移除，避免递归进入
                            dirs.remove(dir_name)
                            break

        total_files = sum(len(files) for files in result.values())
        logger.info(f"扫描完成，共找到 {total_files} 个缓存文件")

        return result

    def process_cache_files(
        self,
        cache_files: Dict[str, List[str]],
        move_to_cache: bool = True,
        delete_old: bool = False,
        max_age_days: int = 7,
    ) -> Dict:
        """
        处理缓存文件

        Args:
            cache_files: 缓存文件列表
            move_to_cache: 是否移动文件到缓存目录
            delete_old: 是否删除旧文件
            max_age_days: 最大保留天数

        Returns:
            Dict: 处理统计信息
        """
        # 当前时间
        now = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60

        for cache_type, files in cache_files.items():
            logger.info(f"处理 {cache_type} 类型文件: {len(files)} 个")

            # 缓存目录
            type_cache_dir = os.path.join(self.cache_dir, cache_type)
            os.makedirs(type_cache_dir, exist_ok=True)

            for file_path in files:
                try:
                    # 检查文件是否存在
                    if not os.path.exists(file_path):
                        continue

                    # 获取文件修改时间
                    file_age = now - os.path.getmtime(file_path)

                    # 如果启用了直接删除旧文件选项且文件够旧，直接删除
                    if delete_old and file_age > max_age_seconds:
                        if os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                        else:
                            os.remove(file_path)
                        self.stats["deleted_files"] += 1
                        logger.debug(f"已删除旧文件: {file_path}")
                        continue

                    # 移动文件到缓存目录
                    if move_to_cache:
                        # 计算目标路径，保留原目录结构
                        rel_path = os.path.relpath(
                            os.path.dirname(file_path), project_root
                        )
                        if rel_path == ".":
                            rel_path = ""
                        target_dir = os.path.join(type_cache_dir, rel_path)
                        os.makedirs(target_dir, exist_ok=True)

                        file_name = os.path.basename(file_path)
                        target_path = os.path.join(target_dir, file_name)

                        # 如果目标文件已存在，添加时间戳
                        if os.path.exists(target_path):
                            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                            name, ext = os.path.splitext(file_name)
                            target_path = os.path.join(
                                target_dir, f"{name}_{timestamp}{ext}"
                            )

                        # 移动文件
                        if os.path.isdir(file_path):
                            # 对于目录，使用shutil.copytree复制后删除原目录
                            if os.path.exists(target_path):
                                shutil.rmtree(target_path)
                            shutil.copytree(file_path, target_path)
                            shutil.rmtree(file_path)
                        else:
                            # 对于文件，使用shutil.move
                            shutil.move(file_path, target_path)

                        self.stats["moved_files"] += 1
                        logger.debug(f"已移动: {file_path} -> {target_path}")

                except Exception as e:
                    logger.error(f"处理文件失败: {file_path}, 错误: {str(e)}")
                    self.stats["errors"] += 1

        return self.stats

    def clean_empty_dirs(self, start_dir: str = None) -> int:
        """
        清理空目录

        Args:
            start_dir: 起始目录，默认为项目根目录

        Returns:
            int: 清理的空目录数量
        """
        start_dir = start_dir or project_root
        cleaned_dirs = 0

        logger.info(f"开始清理空目录: {start_dir}")

        for root, dirs, files in os.walk(start_dir, topdown=False):
            # 跳过缓存目录自身
            if os.path.abspath(root).startswith(os.path.abspath(self.cache_dir)):
                continue

            # 跳过.git目录
            if ".git" in root:
                continue

            # 如果目录为空，删除它
            if not files and not dirs:
                try:
                    os.rmdir(root)
                    cleaned_dirs += 1
                    logger.debug(f"已删除空目录: {root}")
                except Exception as e:
                    logger.error(f"删除目录失败: {root}, 错误: {str(e)}")
                    self.stats["errors"] += 1

        self.stats["cleaned_dirs"] = cleaned_dirs
        logger.info(f"空目录清理完成，共删除 {cleaned_dirs} 个目录")

        return cleaned_dirs

    def cleanup_old_cache(self, max_age_days: int = 30) -> int:
        """
        清理旧缓存文件

        Args:
            max_age_days: 最大保留天数

        Returns:
            int: 清理的文件数量
        """
        if not os.path.exists(self.cache_dir):
            logger.warning(f"缓存目录不存在: {self.cache_dir}")
            return 0

        now = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        removed_files = 0

        logger.info(f"开始清理旧缓存文件 (>{max_age_days}天)")

        for root, dirs, files in os.walk(self.cache_dir, topdown=False):
            for file in files:
                file_path = os.path.join(root, file)

                # 跳过重要的索引文件
                if file == "index.json":
                    continue

                try:
                    file_age = now - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        removed_files += 1
                        logger.debug(f"已删除旧缓存: {file_path}")
                except Exception as e:
                    logger.error(f"删除文件失败: {file_path}, 错误: {str(e)}")
                    self.stats["errors"] += 1

            # 删除空目录
            if not os.listdir(root) and root != self.cache_dir:
                try:
                    os.rmdir(root)
                    logger.debug(f"已删除空缓存目录: {root}")
                except Exception as e:
                    logger.error(f"删除目录失败: {root}, 错误: {str(e)}")

        self.stats["deleted_files"] += removed_files
        logger.info(f"旧缓存清理完成，共删除 {removed_files} 个文件")

        return removed_files

    def run_cleanup(
        self,
        move_to_cache: bool = True,
        delete_old: bool = True,
        clean_empty_dirs: bool = True,
        cleanup_cache: bool = True,
        max_age_days: int = 7,
        cache_max_age_days: int = 30,
    ) -> Dict:
        """
        运行完整清理流程

        Args:
            move_to_cache: 是否移动文件到缓存目录
            delete_old: 是否删除旧文件
            clean_empty_dirs: 是否清理空目录
            cleanup_cache: 是否清理旧缓存
            max_age_days: 备份文件最大保留天数
            cache_max_age_days: 缓存文件最大保留天数

        Returns:
            Dict: 处理统计信息
        """
        logger.info("=== 开始系统缓存与备份文件清理 ===")
        start_time = time.time()

        # 查找缓存文件
        cache_files = self.find_cache_files()

        # 处理缓存文件
        self.process_cache_files(
            cache_files,
            move_to_cache=move_to_cache,
            delete_old=delete_old,
            max_age_days=max_age_days,
        )

        # 清理空目录
        if clean_empty_dirs:
            self.clean_empty_dirs()

        # 清理旧缓存
        if cleanup_cache:
            self.cleanup_old_cache(max_age_days=cache_max_age_days)

        # 计算总耗时
        elapsed_time = time.time() - start_time
        self.stats["elapsed_time"] = elapsed_time

        logger.info("=== 清理完成 ===")
        logger.info(f"总计处理文件: {self.stats['processed_files']}")
        logger.info(f"已移动: {self.stats['moved_files']}")
        logger.info(f"已删除: {self.stats['deleted_files']}")
        logger.info(f"清理空目录: {self.stats['cleaned_dirs']}")
        logger.info(f"错误数: {self.stats['errors']}")
        logger.info(f"耗时: {elapsed_time:.2f}秒")

        return self.stats


# 计划任务定义：每日自动清理缓存和备份文件
def scheduled_cleanup():
    """计划任务：定期清理缓存和备份文件"""
    logger.info("执行计划任务：清理缓存和备份文件")

    try:
        cleaner = BackupFileCleaner()
        stats = cleaner.run_cleanup(
            move_to_cache=True,  # 移动到缓存目录而不是直接删除
            delete_old=True,  # 删除超过一定天数的旧文件
            clean_empty_dirs=True,  # 清理空目录
            cleanup_cache=True,  # 清理旧缓存
            max_age_days=7,  # 备份文件保留7天
            cache_max_age_days=30,  # 缓存文件保留30天
        )

        logger.info(f"清理任务完成: {stats}")
        return stats
    except Exception as e:
        logger.error(f"清理任务失败: {str(e)}", exc_info=True)
        return {"error": str(e)}


# 启动时执行：注册计划任务
def register_cleanup_task():
    """注册清理任务到系统调度器"""
    try:
        # 导入调度器模块
        from system.scheduler import schedule_cron

        # 注册每日凌晨3点运行的清理任务
        task_id = schedule_cron(
            scheduled_cleanup,
            "0 3 * * *",  # 每天凌晨3点
            name="system_backup_cleanup",
            max_retries=3,
            retry_delay=300,  # 5分钟
        )

        # 注册系统启动时运行的清理任务
        from system.scheduler import publish_event

        publish_event({"type": "system.startup", "data": {"cleanup": True}})

        logger.info(f"已注册缓存清理任务，任务ID: {task_id}")
        return task_id
    except ImportError:
        logger.error("无法导入调度器模块，清理任务注册失败")
        return None
    except Exception as e:
        logger.error(f"注册清理任务失败: {str(e)}")
        return None


# 注册启动时任务
def register_startup_handler():
    """注册系统启动事件处理器"""
    try:
        # 导入调度器模块
        from system.scheduler import schedule_event

        # 注册启动事件处理器
        task_id = schedule_event(
            lambda event: BackupFileCleaner().run_cleanup(),
            "system.startup",
            event_filter=lambda e: e.get("data", {}).get("cleanup", False),
            name="startup_cleanup",
            max_retries=1,
        )

        logger.info(f"已注册启动清理任务，任务ID: {task_id}")
        return task_id
    except ImportError:
        logger.error("无法导入调度器模块，启动任务注册失败")
        return None
    except Exception as e:
        logger.error(f"注册启动任务失败: {str(e)}")
        return None


# 手动运行清理
def run_manual_cleanup(args=None):
    """手动运行清理任务"""
    import argparse

    if not args:
        # 解析命令行参数
        parser = argparse.ArgumentParser(description="系统缓存与备份文件清理工具")
        parser.add_argument(
            "--move", action="store_true", default=True, help="移动文件到缓存目录"
        )
        parser.add_argument(
            "--no-move",
            action="store_false",
            dest="move",
            help="不移动文件到缓存目录（直接删除）",
        )
        parser.add_argument(
            "--delete-old", action="store_true", default=True, help="删除旧文件"
        )
        parser.add_argument(
            "--keep-old", action="store_false", dest="delete_old", help="保留旧文件"
        )
        parser.add_argument("--max-age", type=int, default=7, help="备份文件保留天数")
        parser.add_argument(
            "--cache-age", type=int, default=30, help="缓存文件保留天数"
        )
        args = parser.parse_args()

    # 运行清理
    cleaner = BackupFileCleaner()
    stats = cleaner.run_cleanup(
        move_to_cache=args.move,
        delete_old=args.delete_old,
        max_age_days=args.max_age,
        cache_max_age_days=args.cache_age,
    )

    return stats


# 初始化：在系统启动时执行
def initialize():
    """初始化函数"""
    # 注册计划任务
    register_cleanup_task()

    # 注册启动事件处理器
    register_startup_handler()

    logger.info("备份文件清理系统已初始化")


# 主函数
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 手动运行清理
    run_manual_cleanup()