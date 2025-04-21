"""
配置模块，提供项目配置读取功能
"""

_default_config = {
    "modules": {
        "trading": {
            "enabled": True
        },
        "data": {
            "enabled": True
        },
        "ui": {
            "enabled": True
        }
    }
}

def get_config():
    """
    获取配置信息
    
    Returns:
        dict: 配置字典
    """
    return _default_config

def get(path, default=None):
    """
    通过路径获取配置值
    
    Args:
        path (str): 点分隔的配置路径，例如 "modules.trading.enabled"
        default: 如果路径不存在，返回的默认值
        
    Returns:
        配置值或默认值
    """
    config = _default_config
    parts = path.split('.')
    
    for part in parts:
        if isinstance(config, dict) and part in config:
            config = config[part]
        else:
            return default
            
    return config