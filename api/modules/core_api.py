"""
核心 API 模块

提供对核心系统功能的 API 访问。
"""

from flask import Blueprint, request, jsonify
from typing import Dict, List, Any

from config import config
from api.base_api import BaseAPI


class CoreAPI(BaseAPI):
    """核心系统功能的 API 模块"""

    def __init__(self):
        """初始化核心 API 模块"""
        super().__init__()
        self.name = "core"
        self.description = "核心系统 API 端点"
        self.version = "1.0.0"
        self.route_prefix = f"/api/{self.name}"

    def register_endpoints(self, bp: Blueprint) -> None:
        """
        注册核心 API 端点

        参数:
            bp: Flask 蓝图
        """

        @bp.route("/status", methods=["GET"])
        def system_status():
            """获取系统状态信息"""
            return jsonify(
                {
                    "status": "operational",
                    "environment": config.get("system.environment", "production"),
                    "debug_mode": config.get("system.debug_mode", False),
                    "version": "1.0.0",
                }
            )

        @bp.route("/config", methods=["GET"])
        def get_config():
            """获取系统配置（仅安全值）"""
            # 仅返回安全的配置值
            safe_config = {
                "system": {
                    "environment": config.get("system.environment", "production"),
                    "log_level": config.get("system.log_level", "INFO"),
                },
                "api": {"enabled": config.get("api.enabled", True)},
                "ui": {
                    "default_mode": config.get("ui.default_mode", "console"),
                    "theme": config.get("ui.theme", "light"),
                },
            }
            return jsonify(safe_config)

    def get_endpoints_info(self) -> List[Dict[str, str]]:
        """
        获取有关可用端点的信息

        返回:
            端点信息字典列表
        """
        # 从父类获取基本端点
        endpoints = super().get_endpoints_info()

        # 添加核心特定的端点
        endpoints.extend(
            [
                {
                    "path": f"{self.route_prefix}/status",
                    "method": "GET",
                    "description": "获取系统状态信息",
                },
                {
                    "path": f"{self.route_prefix}/config",
                    "method": "GET",
                    "description": "获取系统配置（仅安全值）",
                },
            ]
        )

        return endpoints