"""
事件系统

提供事件分发和处理的核心系统。
"""

import logging
from enum import Enum
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime

class EventType(Enum):
    """事件类型枚举"""
    # 系统事件
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    
    # 用户事件
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    
    # 数据事件
    DATA_UPDATED = "data_updated"
    
    # 训练事件
    TRAINING_STARTED = "training_started"
    TRAINING_COMPLETED = "training_completed"
    TRAINING_FAILED = "training_failed"
    
    # 量化交易事件（新增）
    STRATEGY_REQUEST = "strategy_request"
    STRATEGY_BUILDING = "strategy_building"
    STRATEGY_READY = "strategy_ready"
    STRATEGY_ERROR = "strategy_error"
    STRATEGY_DEPLOYED = "strategy_deployed"

class Event:
    """事件类，表示系统中的一个事件"""
    
    def __init__(self, type: EventType, data: Dict[str, Any] = None):
        """
        初始化事件
        
        参数:
            type: 事件类型
            data: 事件数据
        """
        self.type = type
        self.data = data if data else {}
        self.timestamp = datetime.now()
    
    def __str__(self) -> str:
        """返回事件的字符串表示"""
        return f"Event({self.type.value}, {self.timestamp})"

class EventDispatcher:
    """事件分发器，负责事件的分发和处理"""
    
    _instance = None
    _handlers: Dict[EventType, List[Callable]] = {}
    _logger = logging.getLogger("event_system")
    
    def __new__(cls):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super(EventDispatcher, cls).__new__(cls)
        return cls._instance
    
    def register_handler(self, event_type: EventType, handler: Callable) -> None:
        """
        注册事件处理程序
        
        参数:
            event_type: 要处理的事件类型
            handler: 处理事件的函数
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            self._logger.info(f"已注册处理程序: {event_type.value}")
    
    def unregister_handler(self, event_type: EventType, handler: Callable) -> bool:
        """
        取消注册事件处理程序
        
        参数:
            event_type: 事件类型
            handler: 要取消注册的处理程序
            
        返回:
            是否成功取消注册
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            self._logger.info(f"已取消注册处理程序: {event_type.value}")
            return True
        return False
    
    def dispatch(self, event: Event) -> None:
        """
        分发事件
        
        参数:
            event: 要分发的事件
        """
        self._logger.info(f"分发事件: {event}")
        
        if event.type not in self._handlers:
            self._logger.warning(f"没有处理程序处理事件类型: {event.type.value}")
            return
        
        for handler in self._handlers[event.type]:
            try:
                handler(event)
            except Exception as e:
                self._logger.error(f"事件处理程序引发异常: {e}")
    
    def get_handlers(self, event_type: Optional[EventType] = None) -> Dict[EventType, List[Callable]]:
        """
        获取事件处理程序
        
        参数:
            event_type: 可选，指定事件类型
            
        返回:
            事件处理程序映射或特定事件类型的处理程序列表
        """
        if event_type:
            return {event_type: self._handlers.get(event_type, [])}
        return self._handlers

# 装饰器，用于注册事件处理程序
def event_handler(event_type: EventType):
    """
    事件处理程序装饰器
    
    参数:
        event_type: 要处理的事件类型
    
    返回:
        装饰器函数
    """
    def decorator(func):
        dispatcher = EventDispatcher()
        dispatcher.register_handler(event_type, func)
        return func
    return decorator

# 为了与 __init__.py 兼容，添加 EventBus 别名
EventBus = EventDispatcher

# 获取事件总线实例的辅助函数
def get_event_bus() -> EventDispatcher:
    """获取事件总线单例实例。"""
    return EventDispatcher()

# 添加策略请求事件处理器
@event_handler(EventType.STRATEGY_REQUEST)
def handle_strategy_request(event):
    """处理策略请求事件。"""
    try:
        from ..quantitative.strategy_manager import get_strategy_manager
        
        # 调用窗口9的策略构建逻辑
        strategy_manager = get_strategy_manager()
        strategy_manager.build_strategy(event.data)
    except ImportError as e:
        logging.getLogger("event_system").error(f"无法导入策略管理器: {e}")
    except Exception as e:
        logging.getLogger("event_system").error(f"处理策略请求失败: {e}")