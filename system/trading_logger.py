"""
Trading Logger System
--------------------
专用日志系统，用于记录量化交易系统中的策略生成和执行过程。
支持JSON格式日志记录、日志轮换和级别过滤，并提供策略执行状态跟踪机制。

Classes:
  - TradingLogger: 主日志记录器类，负责记录策略相关事件
  - StrategyTracker: 策略执行状态跟踪器
  - LogRotator: 日志文件轮换管理器

Usage:
  logger = TradingLogger()
  logger.log_strategy("strategy_001", "GENERATED", {"algorithm": "MACD", "parameters": {...}})
  logger.log_execution("strategy_001", "BUY", {"symbol": "AAPL", "price": 150.25, "quantity": 100})
"""

import os
import json
import gzip
import shutil
import logging
from datetime import datetime, timedelta
from enum import Enum
import threading
import time


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LogRotator:
    """日志文件轮换管理器"""
    
    def __init__(self, base_dir, max_size_mb=10, max_files=5, compression=True):
        """
        初始化日志轮换管理器
        
        Args:
            base_dir: 基础日志目录
            max_size_mb: 单个日志文件最大大小(MB)
            max_files: 每个策略保留的最大日志文件数
            compression: 是否压缩旧日志文件
        """
        self.base_dir = base_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_files = max_files
        self.compression = compression
        # 跟踪每个策略日志的当前大小
        self.file_sizes = {}
        self.lock = threading.Lock()
    
    def check_rotation(self, strategy_id):
        """
        检查指定策略的日志文件是否需要轮换
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            bool: 是否需要轮换
        """
        log_file = f"{self.base_dir}/{strategy_id}.json"
        
        # 如果文件不存在，无需轮换
        if not os.path.exists(log_file):
            self.file_sizes[strategy_id] = 0
            return False
        
        # 更新文件大小缓存
        current_size = os.path.getsize(log_file)
        self.file_sizes[strategy_id] = current_size
        
        # 检查是否超过大小限制
        return current_size >= self.max_size_bytes
    
    def rotate(self, strategy_id):
        """
        执行日志文件轮换
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            str: 新的日志文件路径
        """
        with self.lock:
            log_file = f"{self.base_dir}/{strategy_id}.json"
            
            # 如果文件不存在，无需轮换
            if not os.path.exists(log_file):
                return log_file
            
            # 移动旧的日志文件
            self._shift_old_logs(strategy_id)
            
            # 重置文件大小缓存
            self.file_sizes[strategy_id] = 0
            
            return log_file
    
    def _shift_old_logs(self, strategy_id):
        """
        移动旧的日志文件，删除超过限制的文件
        
        Args:
            strategy_id: 策略ID
        """
        # 删除最旧的日志文件(如果达到最大文件数)
        oldest_log = f"{self.base_dir}/{strategy_id}.{self.max_files-1}.json"
        if os.path.exists(oldest_log):
            os.remove(oldest_log)
        elif os.path.exists(f"{oldest_log}.gz"):
            os.remove(f"{oldest_log}.gz")
        
        # 移动现有的日志文件
        for i in range(self.max_files-2, -1, -1):
            if i == 0:
                old_file = f"{self.base_dir}/{strategy_id}.json"
            else:
                old_file = f"{self.base_dir}/{strategy_id}.{i}.json"
            
            new_file = f"{self.base_dir}/{strategy_id}.{i+1}.json"
            
            # 处理压缩文件
            if not os.path.exists(old_file) and os.path.exists(f"{old_file}.gz"):
                old_file = f"{old_file}.gz"
                new_file = f"{new_file}.gz"
            
            if os.path.exists(old_file):
                shutil.move(old_file, new_file)
                
                # 压缩旧的日志文件
                if self.compression and i == 0 and not new_file.endswith('.gz'):
                    self._compress_file(new_file)
    
    def _compress_file(self, file_path):
        """
        压缩指定的文件
        
        Args:
            file_path: 要压缩的文件路径
        """
        with open(file_path, 'rb') as f_in:
            with gzip.open(f"{file_path}.gz", 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 删除原始文件
        os.remove(file_path)


class StrategyTracker:
    """策略执行状态跟踪器"""
    
    def __init__(self):
        """初始化策略跟踪器"""
        self.strategies = {}
        self.lock = threading.Lock()
    
    def update_status(self, strategy_id, status, details=None):
        """
        更新策略状态
        
        Args:
            strategy_id: 策略ID
            status: 新状态
            details: 状态详情
            
        Returns:
            dict: 更新后的策略状态信息
        """
        with self.lock:
            if strategy_id not in self.strategies:
                self.strategies[strategy_id] = {
                    'status': status,
                    'details': details or {},
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'history': []
                }
            else:
                # 保存旧状态到历史记录
                old_status = self.strategies[strategy_id]['status']
                if old_status != status:
                    self.strategies[strategy_id]['history'].append({
                        'from_status': old_status,
                        'to_status': status,
                        'timestamp': datetime.now().isoformat(),
                        'details': details
                    })
                
                # 更新当前状态
                self.strategies[strategy_id]['status'] = status
                if details:
                    self.strategies[strategy_id]['details'].update(details)
                self.strategies[strategy_id]['updated_at'] = datetime.now().isoformat()
            
            return self.strategies[strategy_id]
    
    def get_status(self, strategy_id):
        """
        获取策略当前状态
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            dict: 策略状态信息，如果不存在则返回None
        """
        return self.strategies.get(strategy_id)
    
    def get_all_strategies(self, status=None):
        """
        获取所有策略状态，可选按状态过滤
        
        Args:
            status: 可选的状态过滤条件
            
        Returns:
            dict: 策略ID到状态的映射
        """
        if status is None:
            return self.strategies
        
        return {
            strategy_id: info 
            for strategy_id, info in self.strategies.items() 
            if info['status'] == status
        }


class TradingLogger:
    """交易日志记录器"""
    
    def __init__(self, log_dir="logs/trading", min_level=LogLevel.INFO, 
                 rotation_size_mb=10, max_files=5, enable_console=False):
        """
        初始化交易日志记录器
        
        Args:
            log_dir: 日志目录
            min_level: 最小日志级别
            rotation_size_mb: 日志轮换大小(MB)
            max_files: 每个策略保留的最大日志文件数
            enable_console: 是否同时输出到控制台
        """
        self.log_dir = log_dir
        self.min_level = min_level
        os.makedirs(log_dir, exist_ok=True)
        
        # 配置Python标准日志
        self.logger = logging.getLogger('trading')
        self.logger.setLevel(logging.DEBUG)
        
        # 清除现有处理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 文件处理器
        file_handler = logging.FileHandler(f"{log_dir}/trading_system.log")
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 控制台处理器(可选)
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # 日志轮换器
        self.rotator = LogRotator(log_dir, max_size_mb=rotation_size_mb, max_files=max_files)
        
        # 策略跟踪器
        self.tracker = StrategyTracker()
    
    def log_strategy(self, strategy_id, event, data=None, level=LogLevel.INFO):
        """
        记录策略事件到JSON文件
        
        Args:
            strategy_id: 策略ID
            event: 事件名称
            data: 事件数据
            level: 日志级别
            
        Returns:
            bool: 是否成功记录
        """
        # 检查日志级别
        if level.value < self.min_level.value:
            return False
        
        # 创建日志条目
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "strategy_id": strategy_id,
            "event": event,
            "level": level.name,
            "data": data
        }
        
        # 检查是否需要轮换日志
        if self.rotator.check_rotation(strategy_id):
            self.rotator.rotate(strategy_id)
        
        # 写入日志文件
        try:
            with open(f"{self.log_dir}/{strategy_id}.json", "a") as f:
                json.dump(log_entry, f)
                f.write("\n")
            
            # 同时记录到标准日志
            self.logger.log(
                level.value, 
                f"Strategy {strategy_id}: {event} - {json.dumps(data) if data else ''}"
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to write log for strategy {strategy_id}: {str(e)}")
            return False
    
    def log_execution(self, strategy_id, action, details, level=LogLevel.INFO):
        """
        记录策略执行操作
        
        Args:
            strategy_id: 策略ID
            action: 执行动作(如BUY, SELL)
            details: 执行详情
            level: 日志级别
            
        Returns:
            bool: 是否成功记录
        """
        # 更新策略状态
        self.tracker.update_status(strategy_id, f"EXECUTED_{action}", details)
        
        # 记录日志
        return self.log_strategy(
            strategy_id,
            f"EXECUTION_{action}",
            details,
            level
        )
    
    def log_error(self, strategy_id, error_msg, details=None):
        """
        记录策略错误
        
        Args:
            strategy_id: 策略ID
            error_msg: 错误消息
            details: 错误详情
            
        Returns:
            bool: 是否成功记录
        """
        # 更新策略状态
        self.tracker.update_status(strategy_id, "ERROR", {"error_msg": error_msg, "details": details})
        
        # 记录日志
        return self.log_strategy(
            strategy_id,
            "ERROR",
            {
                "message": error_msg,
                "details": details
            },
            LogLevel.ERROR
        )
    
    def get_strategy_status(self, strategy_id):
        """
        获取策略当前状态
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            dict: 策略状态信息
        """
        return self.tracker.get_status(strategy_id)
    
    def get_active_strategies(self):
        """
        获取所有活跃状态的策略
        
        Returns:
            dict: 活跃策略状态信息
        """
        # 过滤非错误和非完成状态的策略
        all_strategies = self.tracker.get_all_strategies()
        return {
            strategy_id: info 
            for strategy_id, info in all_strategies.items() 
            if not (info['status'].startswith('ERROR') or info['status'] == 'COMPLETED')
        }
    
    def summarize_strategy_performance(self, strategy_id, time_period=None):
        """
        汇总策略性能
        
        Args:
            strategy_id: 策略ID
            time_period: 时间段(天)，如None表示全部历史
            
        Returns:
            dict: 性能汇总信息
        """
        # 加载策略日志
        log_file = f"{self.log_dir}/{strategy_id}.json"
        if not os.path.exists(log_file):
            return {"error": "Strategy logs not found"}
        
        executions = []
        errors = 0
        signals = 0
        
        # 设置时间筛选
        cutoff_time = None
        if time_period:
            cutoff_time = datetime.now() - timedelta(days=time_period)
        
        with open(log_file, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    
                    # 时间过滤
                    if cutoff_time:
                        entry_time = datetime.fromisoformat(entry["timestamp"])
                        if entry_time < cutoff_time:
                            continue
                    
                    # 分类统计
                    if entry["event"].startswith("EXECUTION_"):
                        executions.append(entry)
                    elif entry["event"] == "ERROR":
                        errors += 1
                    elif entry["event"] == "SIGNAL":
                        signals += 1
                except json.JSONDecodeError:
                    continue
        
        # 计算执行结果
        buys = [e for e in executions if e["event"] == "EXECUTION_BUY"]
        sells = [e for e in executions if e["event"] == "EXECUTION_SELL"]
        
        return {
            "strategy_id": strategy_id,
            "total_executions": len(executions),
            "buys": len(buys),
            "sells": len(sells),
            "errors": errors,
            "signals": signals,
            "period_days": time_period,
            "current_status": self.get_strategy_status(strategy_id)
        }


# 示例用法
if __name__ == "__main__":
    # 创建日志记录器
    logger = TradingLogger(log_dir="./logs/trading", enable_console=True)
    
    # 记录策略生成
    strategy_id = f"macd_crossover_{int(time.time())}"
    logger.log_strategy(
        strategy_id, 
        "GENERATED", 
        {
            "algorithm": "MACD_CROSSOVER",
            "parameters": {
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9,
                "symbols": ["AAPL", "MSFT", "GOOG"]
            }
        }
    )
    
    # 记录信号
    logger.log_strategy(
        strategy_id,
        "SIGNAL",
        {
            "symbol": "AAPL",
            "direction": "BUY",
            "strength": 0.75,
            "price": 150.25
        }
    )
    
    # 记录执行
    logger.log_execution(
        strategy_id,
        "BUY",
        {
            "symbol": "AAPL",
            "price": 150.25,
            "quantity": 100,
            "timestamp": datetime.now().isoformat(),
            "execution_id": "exec_12345"
        }
    )
    
    # 记录错误
    logger.log_error(
        strategy_id,
        "API connection timeout",
        {
            "api": "trading_broker",
            "timeout": 30,
            "retry_count": 3
        }
    )
    
    # 获取策略状态
    status = logger.get_strategy_status(strategy_id)
    print(f"Strategy {strategy_id} status: {status['status']}")
    
    # 性能汇总
    performance = logger.summarize_strategy_performance(strategy_id)
    print(f"Strategy performance: {json.dumps(performance, indent=2)}")