# ui/components/strategy_monitor.py
"""
策略监控UI组件
提供策略运行状态的可视化监控界面
"""

import os
import time
import json
from typing import Dict, List, Any, Optional


class StrategyMonitor:
    """策略监控UI组件"""

    def __init__(self, config_path=None):
        """
        初始化策略监控器

        参数:
            config_path (str, optional): UI配置文件路径
        """
        self.active_strategies = {}  # 当前活跃的策略
        self.performance_data = {}  # 性能数据
        self.last_update = time.time()
        self.refresh_interval = 5  # 默认刷新间隔(秒)

        # 从配置文件加载设置（如果提供）
        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                self.refresh_interval = config.get(
                    "refresh_interval", self.refresh_interval
                )
                self.chart_settings = config.get("chart_settings", {})
                self.display_mode = config.get("display_mode", "detailed")
        else:
            # 默认显示设置
            self.chart_settings = {
                "show_profit_chart": True,
                "show_trade_markers": True,
                "color_scheme": "light",
                "chart_height": 400,
            }
            self.display_mode = "detailed"

        print("策略监控器初始化成功")

    def get_status(self) -> Dict[str, Any]:
        """
        获取当前监控状态

        返回:
            dict: 包含当前活跃策略和性能数据的状态信息
        """
        # 构建状态信息
        status = {
            "active_strategies": len(self.active_strategies),
            "total_profit": self._calculate_total_profit(),
            "last_update": self.last_update,
            "running_time": self._get_running_time(),
            "display_mode": self.display_mode,
            "status": "运行中" if self.active_strategies else "空闲",
        }

        return status

    def update_strategy_status(self, data: Dict[str, Any]) -> bool:
        """
        更新策略状态数据

        参数:
            data (dict): 包含策略和评估信息的数据

        返回:
            bool: 更新是否成功
        """
        try:
            # 更新时间戳
            self.last_update = time.time()

            # 提取策略信息和评估结果
            strategy = data.get("strategy", {})
            evaluation = data.get("evaluation", {})

            if not strategy:
                print("警告: 更新数据中缺少策略信息")
                return False

            # 获取策略ID
            strategy_id = strategy.get("id", str(hash(str(strategy))))

            # 更新活跃策略
            self.active_strategies[strategy_id] = {
                "name": strategy.get("name", "未命名策略"),
                "description": strategy.get("description", ""),
                "status": "运行中",
                "last_update": self.last_update,
            }

            # 更新性能数据
            if evaluation:
                if strategy_id not in self.performance_data:
                    self.performance_data[strategy_id] = []

                # 添加时间戳到评估数据
                evaluation_with_time = evaluation.copy()
                evaluation_with_time["timestamp"] = self.last_update

                self.performance_data[strategy_id].append(evaluation_with_time)

            print(f"策略'{strategy.get('name', '未命名')}' 状态已更新")
            return True

        except Exception as e:
            print(f"更新策略状态出错: {str(e)}")
            return False

    def _calculate_total_profit(self) -> float:
        """
        计算所有策略的总利润

        返回:
            float: 总利润
        """
        total_profit = 0.0

        for strategy_id, performances in self.performance_data.items():
            if performances:
                # 获取最新的性能数据
                latest = performances[-1]
                total_profit += latest.get("profit", 0.0)

        return total_profit

    def _get_running_time(self) -> str:
        """
        获取系统运行时间的格式化字符串

        返回:
            str: 格式化的运行时间
        """
        # 模拟运行时间为当前时间减去一个随机值
        # 实际应用中应该记录系统启动时间
        start_time = time.time() - 3600  # 假设系统已运行1小时

        elapsed = time.time() - start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def render_dashboard(self) -> str:
        """
        生成仪表盘HTML内容

        返回:
            str: 仪表盘HTML
        """
        # 这个方法会生成HTML内容用于显示
        # 在实际应用中，会使用前端框架和模板引擎

        # 简单的HTML示例
        html = f"""
        <div class="dashboard">
            <h1>策略监控仪表盘</h1>
            <div class="status-panel">
                <p>状态: {self.get_status()['status']}</p>
                <p>活跃策略: {self.get_status()['active_strategies']}</p>
                <p>总利润: ${self.get_status()['total_profit']:.2f}</p>
                <p>运行时间: {self.get_status()['running_time']}</p>
                <p>最后更新: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.last_update))}</p>
            </div>
            <div class="strategy-list">
                <h2>活跃策略</h2>
                <ul>
        """

        # 添加策略列表
        for strategy_id, strategy in self.active_strategies.items():
            profit = 0.0
            if (
                strategy_id in self.performance_data
                and self.performance_data[strategy_id]
            ):
                profit = self.performance_data[strategy_id][-1].get(
                    "profit", 0.0)

            html += f"""
                <li>
                    <span class="strategy-name">{strategy['name']}</span>
                    <span class="strategy-profit">${profit:.2f}</span>
                    <span class="strategy-status">{strategy['status']}</span>
                </li>
            """

        html += """
                </ul>
            </div>
        </div>
        """

        return html

    def start_strategy(self, strategy_id: str) -> bool:
        """
        启动策略

        参数:
            strategy_id (str): 策略ID

        返回:
            bool: 启动是否成功
        """
        if strategy_id in self.active_strategies:
            self.active_strategies[strategy_id]["status"] = "运行中"
            print(f"策略 {strategy_id} 已启动")
            return True
        else:
            print(f"找不到策略 {strategy_id}")
            return False

    def stop_strategy(self, strategy_id: str) -> bool:
        """
        停止策略

        参数:
            strategy_id (str): 策略ID

        返回:
            bool: 停止是否成功
        """
        if strategy_id in self.active_strategies:
            self.active_strategies[strategy_id]["status"] = "已停止"
            print(f"策略 {strategy_id} 已停止")
            return True
        else:
            print(f"找不到策略 {strategy_id}")
            return False

    def clear_all_strategies(self) -> bool:
        """
        清除所有策略

        返回:
            bool: 操作是否成功
        """
        self.active_strategies = {}
        print("所有策略已清除")
        return True

    def export_performance_data(self, file_path: str) -> bool:
        """
        导出性能数据到文件

        参数:
            file_path (str): 导出文件路径

        返回:
            bool: 导出是否成功
        """
        try:
            with open(file_path, "w") as f:
                json.dump(self.performance_data, f, indent=4)
            print(f"性能数据已导出到 {file_path}")
            return True
        except Exception as e:
            print(f"导出性能数据出错: {str(e)}")
            return False