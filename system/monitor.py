# -*- coding: utf-8 -*-
"""
系统模块: 监控系统
功能描述: 监控系统资源、性能和运行状态，提供实时数据和报警功能
版本: 1.1
创建日期: 2025-04-17
"""

import os
import time
import logging
import threading
import trading.utils
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Callable

# 相对导入
from .config import logging_config
from .utils import file_utils
from .performance import benchmark

# 配置日志
logger = logging.getLogger(__name__)


class SystemMonitor:
    """
    系统监控类，负责收集和报告系统运行状态数据

    提供系统CPU、内存、磁盘、网络等资源的监控功能，
    支持阈值设置和告警功能。
    """

    def __init__(
        self,
        interval: int = 60,
        log_file: Optional[str] = None,
        enable_alerts: bool = True,
        resource_thresholds: Optional[Dict[str, float]] = None,
    ):
        """
        初始化系统监控器

        Args:
            interval: 监控检查间隔时间(秒)
            log_file: 监控日志文件路径，None则使用默认路径
            enable_alerts: 是否启用告警功能
            resource_thresholds: 资源阈值设置，格式如：
                {'cpu': 90.0, 'memory': 85.0, 'disk': 90.0}
        """
        self.interval = interval
        self.log_file = log_file
        self.enable_alerts = enable_alerts
        self.running = False
        self.monitor_thread = None
        self.alert_callbacks = []

        # 默认资源阈值
        self.resource_thresholds = {
            "cpu": 80.0,  # CPU使用率阈值（百分比）
            "memory": 80.0,  # 内存使用率阈值（百分比）
            "disk": 85.0,  # 磁盘使用率阈值（百分比）
            "swap": 60.0,  # 交换空间使用率阈值（百分比）
        }

        # 更新用户提供的阈值
        if resource_thresholds:
            self.resource_thresholds.update(resource_thresholds)

        # 历史数据存储
        self.history_data = {
            "cpu": [],
            "memory": [],
            "disk": [],
            "network": [],
            "timestamp": [],
        }
        self.history_max_len = 1440  # 存储24小时的数据（按分钟采集）

        # 性能测试管理器
        self.performance_manager = None

        logger.info("系统监控器初始化完成，监控间隔：%d秒", self.interval)

    def init_performance_manager(
        self, save_results: bool = True, results_dir: Optional[str] = None
    ):
        """
        初始化性能测试管理器

        Args:
            save_results: 是否保存测试结果
            results_dir: 结果保存目录
        """
        from .performance.benchmark import PerformanceBenchmark

        self.performance_manager = PerformanceBenchmark(
            name="system_monitor",
            description="系统监控性能测试",
            save_results=save_results,
            results_dir=results_dir,
        )
        logger.info("性能测试管理器已初始化")
        return self.performance_manager

    def start(self) -> bool:
        """
        启动系统监控

        Returns:
            bool: 启动成功返回True，否则返回False
        """
        if self.running:
            logger.warning("监控器已经在运行中")
            return False

        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("系统监控器已启动")
        return True

    def stop(self) -> bool:
        """
        停止系统监控

        Returns:
            bool: 停止成功返回True，否则返回False
        """
        if not self.running:
            logger.warning("监控器未在运行")
            return False

        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
            if self.monitor_thread.is_alive():
                logger.warning("监控线程未能正常结束")
            else:
                logger.info("系统监控器已停止")
        return True

    def register_alert_callback(self, callback: Callable[[str, Dict], None]) -> None:
        """
        注册告警回调函数

        Args:
            callback: 回调函数，接收告警类型和告警数据
        """
        if callback not in self.alert_callbacks:
            self.alert_callbacks.append(callback)
            logger.debug("已注册新的告警回调函数")

    def _monitor_loop(self) -> None:
        """监控主循环，按照指定间隔采集系统数据并检查告警条件"""
        while self.running:
            try:
                # 采集系统数据
                system_data = self.collect_system_data()

                # 保存历史数据
                self._update_history_data(system_data)

                # 检查阈值并触发告警
                if self.enable_alerts:
                    self._check_alerts(system_data)

                # 记录监控数据
                logger.debug("系统数据: %s", system_data)

            except Exception as e:
                logger.error("监控数据采集异常: %s", str(e), exc_info=True)

            # 等待下一次检查
            time.sleep(self.interval)

    def collect_system_data(self) -> Dict[str, Union[float, Dict]]:
        """
        采集当前系统资源使用情况

        Returns:
            Dict: 包含CPU、内存、磁盘、网络等使用数据的字典
        """
        data = {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "load_avg": os.getloadavg() if hasattr(os, "getloadavg") else None,
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
            },
            "swap": {
                "total": psutil.swap_memory().total,
                "used": psutil.swap_memory().used,
                "percent": psutil.swap_memory().percent,
            },
            "disk": {},
            "network": {},
        }

        # 获取磁盘信息
        for part in psutil.disk_partitions(all=False):
            if os.name == "nt" and ("cdrom" in part.opts or part.fstype == ""):
                # 在Windows上跳过CD/DVD驱动器
                continue
            usage = psutil.disk_usage(part.mountpoint)
            data["disk"][part.mountpoint] = {
                "total": usage.total,
                "used": usage.used,
                "percent": usage.percent,
            }

        # 获取网络信息
        net_io = psutil.net_io_counters()
        data["network"] = {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
        }

        return data

    def _update_history_data(self, data: Dict) -> None:
        """
        更新历史数据，保持数据量在限制范围内

        Args:
            data: 当前采集的系统数据
        """
        self.history_data["timestamp"].append(data["timestamp"])
        self.history_data["cpu"].append(data["cpu"]["percent"])
        self.history_data["memory"].append(data["memory"]["percent"])

        # 计算平均磁盘使用率
        disk_percent = 0.0
        if data["disk"]:
            disk_percent = sum(d["percent"] for d in data["disk"].values()) / len(
                data["disk"]
            )
        self.history_data["disk"].append(disk_percent)

        # 限制历史数据长度
        if len(self.history_data["timestamp"]) > self.history_max_len:
            for key in self.history_data:
                self.history_data[key] = self.history_data[key][-self.history_max_len:]

    def _check_alerts(self, data: Dict) -> None:
        """
        检查系统数据是否超过阈值，触发告警

        Args:
            data: 当前采集的系统数据
        """
        alerts = []

        # 检查CPU使用率
        if data["cpu"]["percent"] > self.resource_thresholds["cpu"]:
            alert = {
                "type": "cpu_high",
                "level": "warning",
                "message": f"CPU使用率过高: {data['cpu']['percent']}%",
                "threshold": self.resource_thresholds["cpu"],
                "value": data["cpu"]["percent"],
                "timestamp": data["timestamp"],
            }
            alerts.append(alert)
            logger.warning(alert["message"])

        # 检查内存使用率
        if data["memory"]["percent"] > self.resource_thresholds["memory"]:
            alert = {
                "type": "memory_high",
                "level": "warning",
                "message": f"内存使用率过高: {data['memory']['percent']}%",
                "threshold": self.resource_thresholds["memory"],
                "value": data["memory"]["percent"],
                "timestamp": data["timestamp"],
            }
            alerts.append(alert)
            logger.warning(alert["message"])

        # 检查磁盘使用率
        for mount, disk_data in data["disk"].items():
            if disk_data["percent"] > self.resource_thresholds["disk"]:
                alert = {
                    "type": "disk_high",
                    "level": "warning",
                    "message": f"磁盘{mount}使用率过高: {disk_data['percent']}%",
                    "threshold": self.resource_thresholds["disk"],
                    "value": disk_data["percent"],
                    "path": mount,
                    "timestamp": data["timestamp"],
                }
                alerts.append(alert)
                logger.warning(alert["message"])

        # 触发告警回调
        for alert in alerts:
            for callback in self.alert_callbacks:
                try:
                    callback(alert["type"], alert)
                except Exception as e:
                    logger.error("执行告警回调时出错: %s", str(e), exc_info=True)

    def get_current_status(self) -> Dict:
        """
        获取当前系统状态概览

        Returns:
            Dict: 系统状态概览
        """
        try:
            data = self.collect_system_data()
            status = {
                "status": "running" if self.running else "stopped",
                "timestamp": data["timestamp"],
                "resources": {
                    "cpu": {
                        "usage": data["cpu"]["percent"],
                        "status": (
                            "normal"
                            if data["cpu"]["percent"] < self.resource_thresholds["cpu"]
                            else "alert"
                        ),
                    },
                    "memory": {
                        "usage": data["memory"]["percent"],
                        "status": (
                            "normal"
                            if data["memory"]["percent"]
                            < self.resource_thresholds["memory"]
                            else "alert"
                        ),
                    },
                    "disk": {},
                },
            }

            # 添加磁盘状态
            for mount, disk_data in data["disk"].items():
                status["resources"]["disk"][mount] = {
                    "usage": disk_data["percent"],
                    "status": (
                        "normal"
                        if disk_data["percent"] < self.resource_thresholds["disk"]
                        else "alert"
                    ),
                }

            return status
        except Exception as e:
            logger.error("获取系统状态时出错: %s", str(e), exc_info=True)
            return {"status": "error", "message": str(e)}

    def get_history_data(self, resource_type: str = "all", hours: int = 1) -> Dict:
        """
        获取历史监控数据

        Args:
            resource_type: 资源类型，'all'、'cpu'、'memory'或'disk'
            hours: 返回过去多少小时的数据

        Returns:
            Dict: 历史监控数据
        """
        # 计算需要的数据点数量
        points = min(
            int(hours * 60 /
                self.interval), len(self.history_data["timestamp"])
        )

        if points == 0:
            return {"message": "没有可用的历史数据"}

        result = {"timestamp": self.history_data["timestamp"][-points:]}

        if resource_type == "all":
            result["cpu"] = self.history_data["cpu"][-points:]
            result["memory"] = self.history_data["memory"][-points:]
            result["disk"] = self.history_data["disk"][-points:]
        else:
            if resource_type in self.history_data:
                result[resource_type] = self.history_data[resource_type][-points:]
            else:
                return {"error": f"未知的资源类型: {resource_type}"}

        return result

    def run_performance_test(
        self, test_name: str, iterations: int = 5, params: Optional[Dict] = None
    ) -> Dict:
        """
        运行性能测试

        Args:
            test_name: 测试名称
            iterations: 测试迭代次数
            params: 测试参数

        Returns:
            Dict: 测试结果
        """
        if not self.performance_manager:
            self.init_performance_manager()

        # 定义测试函数
        def performance_test(params):
            start_time = time.time()

            # 根据测试类型执行不同测试
            if test_name == "cpu_performance":
                result = self._run_cpu_performance_test(params)
            elif test_name == "memory_performance":
                result = self._run_memory_performance_test(params)
            elif test_name == "disk_performance":
                result = self._run_disk_performance_test(params)
            elif test_name == "system_state":
                result = self.get_current_status()
            else:
                result = {"error": f"未知的测试类型: {test_name}"}

            # 添加执行时间
            execution_time = time.time() - start_time
            result["execution_time"] = execution_time

            return result

        # 运行测试
        test_results = self.performance_manager.run_test(
            test_func=performance_test, iterations=iterations, params=params or {}
        )

        return test_results

    def _run_cpu_performance_test(self, params: Dict) -> Dict:
        """CPU性能测试"""
        # 模拟CPU密集型操作
        duration = params.get("duration", 1.0)
        start_time = time.time()

        # 简单的CPU负载测试
        while time.time() - start_time < duration:
            _ = [i**2 for i in range(10000)]

        # 收集CPU数据
        cpu_data = psutil.cpu_percent(interval=0.1, percpu=True)

        return {
            "test_type": "cpu_performance",
            "cpu_cores": len(cpu_data),
            "cpu_usage": cpu_data,
            "average_usage": sum(cpu_data) / len(cpu_data) if cpu_data else 0,
            "duration": duration,
        }

    def _run_memory_performance_test(self, params: Dict) -> Dict:
        """内存性能测试"""
        # 内存分配测试
        size_mb = params.get("size_mb", 10)
        duration = params.get("duration", 1.0)

        # 分配内存
        data = bytearray(size_mb * 1024 * 1024)

        # 持有一段时间
        time.sleep(duration)

        # 释放内存
        del data

        # 收集内存数据
        memory = psutil.virtual_memory()

        return {
            "test_type": "memory_performance",
            "allocated_mb": size_mb,
            "memory_usage_percent": memory.percent,
            "available_mb": memory.available / (1024 * 1024),
            "duration": duration,
        }

    def _run_disk_performance_test(self, params: Dict) -> Dict:
        """磁盘性能测试"""
        # 磁盘IO测试
        size_mb = params.get("size_mb", 1)
        path = params.get("path", "./disk_test.tmp")

        try:
            # 写测试
            write_start = time.time()
            with open(path, "wb") as f:
                f.write(os.urandom(size_mb * 1024 * 1024))
            write_time = time.time() - write_start

            # 读测试
            read_start = time.time()
            with open(path, "rb") as f:
                _ = f.read()
            read_time = time.time() - read_start

            # 清理
            if os.path.exists(path):
                os.remove(path)

            return {
                "test_type": "disk_performance",
                "file_size_mb": size_mb,
                "write_time_sec": write_time,
                "read_time_sec": read_time,
                "write_speed_mbps": size_mb / write_time if write_time > 0 else 0,
                "read_speed_mbps": size_mb / read_time if read_time > 0 else 0,
            }

        except Exception as e:
            logger.error("磁盘性能测试出错: %s", str(e), exc_info=True)
            return {"test_type": "disk_performance", "error": str(e)}
        finally:
            # 确保清理临时文件
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass

    def generate_report(self, report_type: str = "daily") -> Dict:
        """
        生成系统监控报告

        Args:
            report_type: 报告类型，'daily'、'weekly'或'monthly'

        Returns:
            Dict: 包含报告数据的字典
        """
        hours = 24  # 默认为日报告
        if report_type == "weekly":
            hours = 24 * 7
        elif report_type == "monthly":
            hours = 24 * 30

        # 获取历史数据
        history = self.get_history_data(resource_type="all", hours=hours)

        # 如果没有足够的数据，返回空报告
        if "cpu" not in history or not history["cpu"]:
            return {"message": f"没有足够的数据生成{report_type}报告"}

        # 计算统计数据
        report = {
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "period_start": history["timestamp"][0],
            "period_end": history["timestamp"][-1],
            "summary": {},
            "alerts": {},
            "recommendations": [],
        }

        # CPU统计
        report["summary"]["cpu"] = {
            "avg": sum(history["cpu"]) / len(history["cpu"]),
            "max": max(history["cpu"]),
            "min": min(history["cpu"]),
        }

        # 内存统计
        report["summary"]["memory"] = {
            "avg": sum(history["memory"]) / len(history["memory"]),
            "max": max(history["memory"]),
            "min": min(history["memory"]),
        }

        # 磁盘统计
        report["summary"]["disk"] = {
            "avg": sum(history["disk"]) / len(history["disk"]),
            "max": max(history["disk"]),
            "min": min(history["disk"]),
        }

        # 计算告警次数
        cpu_alerts = sum(
            1 for x in history["cpu"] if x > self.resource_thresholds["cpu"]
        )
        memory_alerts = sum(
            1 for x in history["memory"] if x > self.resource_thresholds["memory"]
        )
        disk_alerts = sum(
            1 for x in history["disk"] if x > self.resource_thresholds["disk"]
        )

        report["alerts"] = {
            "cpu": cpu_alerts,
            "memory": memory_alerts,
            "disk": disk_alerts,
            "total": cpu_alerts + memory_alerts + disk_alerts,
        }

        # 生成建议
        if report["summary"]["cpu"]["avg"] > self.resource_thresholds["cpu"] * 0.8:
            report["recommendations"].append(
                {"resource": "cpu", "message": "考虑优化CPU密集型任务或增加CPU资源"}
            )

        if (
            report["summary"]["memory"]["avg"]
            > self.resource_thresholds["memory"] * 0.8
        ):
            report["recommendations"].append(
                {"resource": "memory", "message": "考虑优化内存使用或增加内存资源"}
            )

        if report["summary"]["disk"]["avg"] > self.resource_thresholds["disk"] * 0.8:
            report["recommendations"].append(
                {"resource": "disk", "message": "考虑清理磁盘空间或增加存储资源"}
            )

        return report