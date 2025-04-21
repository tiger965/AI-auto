"""
量化交易 API 模块

提供对量化交易功能的 API 访问，支持接收GPT策略结构并返回策略状态。
"""

from flask import Blueprint, request, jsonify
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from config import config
from api.base_api import BaseAPI
from core.event_system import EventDispatcher, EventType, Event
from system.trading_logger import TradingLogger


class TradingAPI(BaseAPI):
    """量化交易功能的 API 模块"""

    def __init__(self):
        """初始化量化交易 API 模块"""
        super().__init__()
        self.name = "trading"
        self.description = "量化交易系统 API 端点"
        self.version = "1.0.0"
        self.route_prefix = f"/api/{self.name}"

        # 检查交易模块是否启用
        self.enabled = config.get("modules.trading.enabled", True)

        # 初始化策略状态存储
        self.strategy_statuses = {}

        # 初始化日志记录器
        self.logger = TradingLogger()

    def register_endpoints(self, bp: Blueprint) -> None:
        """
        注册量化交易 API 端点

        参数:
            bp: Flask 蓝图
        """

        @bp.route("/strategy/build", methods=["POST"])
        def build_strategy():
            """接收GPT生成的策略结构并启动构建过程"""
            if not self.enabled:
                return jsonify({"error": "量化交易模块已禁用"}), 503

            data = request.json
            if not data or "symbol" not in data or "timeframe" not in data:
                return jsonify({"error": "缺少必填字段 (symbol, timeframe)"}), 400

            try:
                # 生成策略ID
                strategy_id = self._generate_strategy_id(
                    data["symbol"], data["timeframe"]
                )

                # 记录初始状态
                self.strategy_statuses[strategy_id] = {
                    "id": strategy_id,
                    "status": "waiting",
                    "created_at": datetime.now().isoformat(),
                    "message": "等待处理中",
                }

                # 记录日志
                self.logger.log_strategy(strategy_id, "request_received", data)

                # 分发策略构建事件
                event_dispatcher = EventDispatcher()
                event_dispatcher.dispatch(
                    Event(
                        type=EventType.STRATEGY_REQUEST,
                        data={"strategy_id": strategy_id,
                              "strategy_data": data},
                    )
                )

                # 更新状态为构建中
                self.strategy_statuses[strategy_id]["status"] = "building"
                self.strategy_statuses[strategy_id]["message"] = "策略构建中..."

                # 返回初始响应
                return (
                    jsonify(
                        {
                            "status": "done",
                            "strategy_id": strategy_id,
                            "file": f"strategies/{strategy_id}.py",
                            "functions": [
                                "populate_entry_trend",
                                "populate_exit_trend",
                            ],
                        }
                    ),
                    201,
                )

            except Exception as e:
                return (
                    jsonify(
                        {"status": "error", "strategy_id": "error",
                            "error": str(e)}
                    ),
                    500,
                )

        @bp.route("/strategy/status/<strategy_id>", methods=["GET"])
        def get_strategy_status(strategy_id):
            """获取策略构建状态"""
            if not self.enabled:
                return jsonify({"error": "量化交易模块已禁用"}), 503

            if strategy_id not in self.strategy_statuses:
                return jsonify({"error": f"策略ID '{strategy_id}' 不存在"}), 404

            return jsonify(self.strategy_statuses[strategy_id])

        @bp.route("/strategy/status/<strategy_id>/update", methods=["POST"])
        def update_strategy_status(strategy_id):
            """更新策略状态(内部API，由Claude调用)"""
            if not self.enabled:
                return jsonify({"error": "量化交易模块已禁用"}), 503

            if strategy_id not in self.strategy_statuses:
                return jsonify({"error": f"策略ID '{strategy_id}' 不存在"}), 404

            data = request.json
            if not data:
                return jsonify({"error": "请求体为空"}), 400

            # 更新状态
            self.strategy_statuses[strategy_id].update(data)

            # 记录日志
            self.logger.log_strategy(strategy_id, "status_updated", data)

            return jsonify(self.strategy_statuses[strategy_id])

    def get_endpoints_info(self) -> List[Dict[str, str]]:
        """
        获取有关可用端点的信息

        返回:
            端点信息字典列表
        """
        # 从父类获取基本端点
        endpoints = super().get_endpoints_info()

        # 添加交易特定的端点
        endpoints.extend(
            [
                {
                    "path": f"{self.route_prefix}/strategy/build",
                    "method": "POST",
                    "description": "接收策略结构并启动构建过程",
                },
                {
                    "path": f"{self.route_prefix}/strategy/status/<strategy_id>",
                    "method": "GET",
                    "description": "获取策略构建状态",
                },
                {
                    "path": f"{self.route_prefix}/strategy/status/<strategy_id>/update",
                    "method": "POST",
                    "description": "更新策略状态",
                },
            ]
        )

        return endpoints

    def _generate_strategy_id(self, symbol: str, timeframe: str) -> str:
        """
        生成唯一策略ID

        参数:
            symbol: 交易对符号
            timeframe: 时间周期

        返回:
            策略ID
        """
        # 生成一个简短的UUID
        short_uuid = str(uuid.uuid4())[:8]
        # 格式化交易对，如BTC/USDT -> btc_usdt
        formatted_symbol = symbol.lower().replace("/", "_")
        # 组合ID
        return f"strat_{formatted_symbol}_{timeframe}_{short_uuid}"