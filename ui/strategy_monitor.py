import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
"""
ui/strategy_monitor.py
功能描述: 实现策略监控界面和用户交互，提供数据可视化和控制功能
版本: 1.0.0
创建日期: 2025-04-20
"""

from api.modules.trading_api import get_strategy_data
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
import os
import threading
import asyncio
import config.paths as pd
import modules.nlp as np
from flask import Flask, jsonify, request, render_template, send_from_directory
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import plotly

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('strategy_monitor')

# 全局常量
DEFAULT_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "../templates")
DEFAULT_STATIC_PATH = os.path.join(os.path.dirname(__file__), "../static")
DEFAULT_DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/monitor")
DEFAULT_PORT = 5000
DEFAULT_HOST = "0.0.0.0"
REFRESH_INTERVAL = 60  # 秒

# 监控状态
MONITOR_STATUS = {
    "initialized": False,
    "config": None,
    "flask_app": None,
    "flask_server": None,
    "active_strategies": {},
    "last_error": None,
    "update_thread": None,
    "running": False
}


class MonitorInitError(Exception):
    """监控初始化异常"""
    pass


app = Flask(__name__)


def initialize_monitor(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    初始化监控系统

    Args:
        config (Optional[Dict[str, Any]], optional): 配置参数. Defaults to None.

    Returns:
        bool: 初始化是否成功
    """
    global MONITOR_STATUS

    if config is None:
        # 使用默认配置
        config = {
            "template_path": DEFAULT_TEMPLATE_PATH,
            "static_path": DEFAULT_STATIC_PATH,
            "data_path": DEFAULT_DATA_PATH,
            "port": DEFAULT_PORT,
            "host": DEFAULT_HOST,
            "refresh_interval": REFRESH_INTERVAL,
            "debug": False
        }

    try:
        # 创建存储目录
        os.makedirs(config["data_path"], exist_ok=True)

        # 设置Flask应用
        global app
        app.template_folder = config["template_path"]
        app.static_folder = config["static_path"]

        # 加载活跃策略数据（如果存在）
        strategies_path = os.path.join(
            config["data_path"], "active_strategies.json")
        if os.path.exists(strategies_path):
            with open(strategies_path, 'r') as f:
                MONITOR_STATUS["active_strategies"] = json.load(f)

        # 设置路由
        _setup_routes()

        # 更新状态
        MONITOR_STATUS["initialized"] = True
        MONITOR_STATUS["config"] = config
        MONITOR_STATUS["flask_app"] = app
        MONITOR_STATUS["last_error"] = None

        # 启动自动更新线程
        _start_update_thread()

        logger.info("Strategy monitor initialized successfully")
        return True

    except Exception as e:
        MONITOR_STATUS["initialized"] = False
        MONITOR_STATUS["last_error"] = str(e)
        logger.error(f"Failed to initialize monitor: {str(e)}")
        return False


def _setup_routes():
    """设置Flask路由"""

    @app.route('/')
    def index():
        """主页"""
        return render_template('index.html')

    @app.route('/api/strategies', methods=['GET'])
    def get_strategies():
        """获取所有策略列表"""
        return jsonify(get_active_strategies_status())

    @app.route('/api/strategy/<strategy_id>', methods=['GET'])
    def get_strategy(strategy_id):
        """获取指定策略详情"""
        if strategy_id in MONITOR_STATUS["active_strategies"]:
            return jsonify(MONITOR_STATUS["active_strategies"][strategy_id])
        else:
            return jsonify({"error": f"Strategy {strategy_id} not found"}), 404

    @app.route('/api/strategy/<strategy_id>/performance', methods=['GET'])
    def get_strategy_performance(strategy_id):
        """获取指定策略性能数据"""
        timeframe = request.args.get('timeframe', '1d')
        chart_data = generate_performance_chart(strategy_id, timeframe)
        return jsonify(chart_data)

    @app.route('/api/dashboard/update', methods=['GET'])
    def update_dashboard():
        """更新仪表板数据"""
        strategy_id = request.args.get('strategy_id')
        result = update_strategy_dashboard(strategy_id)
        return jsonify(result)

    @app.route('/api/dashboard/metrics', methods=['GET'])
    def get_dashboard_metrics():
        """获取仪表板指标数据"""
        metrics = _calculate_dashboard_metrics()
        return jsonify(metrics)


def _save_monitor_state():
    """保存监控状态到磁盘"""
    if not MONITOR_STATUS["initialized"]:
        return False

    try:
        config = MONITOR_STATUS["config"]

        # 保存活跃策略
        strategies_path = os.path.join(
            config["data_path"], "active_strategies.json")
        with open(strategies_path, 'w') as f:
            json.dump(MONITOR_STATUS["active_strategies"], f, indent=2)

        return True

    except Exception as e:
        logger.error(f"Failed to save monitor state: {str(e)}")
        return False


def _start_update_thread():
    """启动自动更新线程"""
    if not MONITOR_STATUS["initialized"] or MONITOR_STATUS["running"]:
        return

    def update_loop():
        MONITOR_STATUS["running"] = True
        while MONITOR_STATUS["running"]:
            try:
                # 更新所有策略状态
                update_strategy_dashboard()

                # 保存状态
                _save_monitor_state()

            except Exception as e:
                logger.error(f"Error in update thread: {str(e)}")

            # 等待指定时间
            time.sleep(MONITOR_STATUS["config"]["refresh_interval"])

    # 创建并启动线程
    update_thread = threading.Thread(target=update_loop)
    update_thread.daemon = True
    update_thread.start()

    MONITOR_STATUS["update_thread"] = update_thread
    logger.info("Update thread started")


def update_strategy_dashboard(strategy_id: Optional[str] = None) -> Dict[str, Any]:
    """
    更新策略仪表板数据

    Args:
        strategy_id (Optional[str], optional): 策略ID，如果为None则更新所有策略. Defaults to None.

    Returns:
        Dict[str, Any]: 更新结果
    """
    if not MONITOR_STATUS["initialized"]:
        raise MonitorInitError("Monitor not initialized")

    update_time = datetime.now().isoformat()
    results = {
        "update_time": update_time,
        "updated_strategies": []
    }

    try:
        # 如果指定了策略ID，只更新该策略
        if strategy_id:
            if strategy_id in MONITOR_STATUS["active_strategies"]:
                strategy_data = MONITOR_STATUS["active_strategies"][strategy_id]

                # 从交易API获取最新数据
                updated_data = _fetch_strategy_data(strategy_id)

                if updated_data:
                    strategy_data.update(updated_data)
                    strategy_data["last_update"] = update_time
                    results["updated_strategies"].append(strategy_id)
            else:
                results["error"] = f"Strategy {strategy_id} not found"
        else:
            # 更新所有活跃策略
            for s_id in list(MONITOR_STATUS["active_strategies"].keys()):
                strategy_data = MONITOR_STATUS["active_strategies"][s_id]

                # 从交易API获取最新数据
                updated_data = _fetch_strategy_data(s_id)

                if updated_data:
                    strategy_data.update(updated_data)
                    strategy_data["last_update"] = update_time
                    results["updated_strategies"].append(s_id)

        # 保存状态
        _save_monitor_state()

        return results

    except Exception as e:
        logger.error(f"Error updating dashboard: {str(e)}")
        results["error"] = str(e)
        return results


def _fetch_strategy_data(strategy_id: str) -> Dict[str, Any]:
    """
    从交易API获取策略数据

    Args:
        strategy_id (str): 策略ID

    Returns:
        Dict[str, Any]: 策略数据
    """
    # 实际项目中，这里应该调用trading_api.py的接口获取数据
    try:
        # 导入trading_api模块
        import sys
        sys.path.append(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))

        # 调用API获取数据
        return get_strategy_data(strategy_id)
    except ImportError:
        logger.warning(
            "Could not import trading_api module, using demo data instead")
        return _generate_dummy_data(strategy_id)
    except Exception as e:
        logger.error(f"Error fetching data from API: {str(e)}")
        return _generate_dummy_data(strategy_id)


def _generate_dummy_data(strategy_id: str) -> Dict[str, Any]:
    """
    生成模拟数据用于演示
    
    Args:
        strategy_id (str): 策略ID
        
    Returns:
        Dict[str, Any]: 模拟数据
    """
    now = datetime.now()

    # 检查策略是否已存在
    if strategy_id in MONITOR_STATUS["active_strategies"]:
        # 更新现有策略
        strategy_data = MONITOR_STATUS["active_strategies"][strategy_id]
        last_updated = datetime.fromisoformat(
            strategy_data.get("last_update", now.isoformat()))

        # 计算时间差
        time_diff = (now - last_updated).total_seconds()

        # 生成新的价格点
        price_points = strategy_data.get("price_data", [])
        if price_points:
            last_price = price_points[-1]["price"]
            last_time = datetime.fromisoformat(price_points[-1]["time"])

            # 每5分钟一个点
            num_new_points = int(time_diff / 300)

            for i in range(1, num_new_points + 1):
                point_time = last_time + timedelta(minutes=5 * i)

                # 模拟价格变动
                price_change = np.random.normal(
                    0, last_price * 0.005)  # 0.5%标准差
                new_price = max(0.01, last_price + price_change)

                price_points.append({
                    "time": point_time.isoformat(),
                    "price": new_price
                })

            # 保留最近的100个点
            if len(price_points) > 100:
                price_points = price_points[-100:]

        # 更新交易
        trades = strategy_data.get("trades", [])

        # 随机生成新交易
        if np.random.random() < 0.3:  # 30%概率生成新交易
            entry_time = last_updated + \
                timedelta(minutes=np.random.randint(5, 30))
            exit_time = entry_time + \
                timedelta(minutes=np.random.randint(15, 240))

            direction = np.random.choice(["long", "short"])
            entry_price = np.random.uniform(0.9, 1.1) * last_price
            exit_price = np.random.uniform(0.9, 1.1) * last_price

            profit = (
                exit_price - entry_price) if direction == "long" else (entry_price - exit_price)
            size = np.random.uniform(0.1, 2.0)
            profit_amount = profit * size

            trades.append({
                "id": f"trade_{len(trades) + 1}",
                "strategy_id": strategy_id,
                "direction": direction,
                "entry_time": entry_time.isoformat(),
                "exit_time": exit_time.isoformat(),
                "entry_price": entry_price,
                "exit_price": exit_price,
                "size": size,
                "profit": profit_amount,
                "status": "closed"
            })

        # 更新权益曲线
        equity_curve = strategy_data.get("equity_curve", [])
        if equity_curve:
            last_equity = equity_curve[-1]["equity"]
            last_equity_time = datetime.fromisoformat(equity_curve[-1]["time"])

            # 每天一个点
            days_diff = (now - last_equity_time).days

            for i in range(1, days_diff + 1):
                point_time = last_equity_time + timedelta(days=i)

                # 模拟权益变动
                daily_return = np.random.normal(0.0005, 0.01)  # 均值0.05%，标准差1%
                new_equity = last_equity * (1 + daily_return)

                equity_curve.append({
                    "time": point_time.isoformat(),
                    "equity": new_equity
                })

            # 保留最近的365个点
            if len(equity_curve) > 365:
                equity_curve = equity_curve[-365:]

        return {
            "price_data": price_points,
            "trades": trades,
            "equity_curve": equity_curve
        }

    else:
        # 创建新策略

        # 生成过去100个5分钟价格点
        base_price = np.random.uniform(10, 1000)
        price_points = []

        for i in range(100):
            point_time = now - timedelta(minutes=5 * (100 - i))

            if i == 0:
                price = base_price
            else:
                price_change = np.random.normal(0, price * 0.005)  # 0.5%标准差
                price = max(0.01, price_points[-1]["price"] + price_change)

            price_points.append({
                "time": point_time.isoformat(),
                "price": price
            })

        # 生成交易历史
        trades = []
        num_trades = np.random.randint(5, 15)

        for i in range(num_trades):
            entry_time = now - timedelta(days=np.random.randint(1, 30))
            exit_time = entry_time + \
                timedelta(minutes=np.random.randint(15, 1440))

            direction = np.random.choice(["long", "short"])
            entry_price = np.random.uniform(0.9, 1.1) * base_price
            exit_price = np.random.uniform(0.9, 1.1) * base_price

            profit = (
                exit_price - entry_price) if direction == "long" else (entry_price - exit_price)
            size = np.random.uniform(0.1, 2.0)
            profit_amount = profit * size

            trades.append({
                "id": f"trade_{i+1}",
                "strategy_id": strategy_id,
                "direction": direction,
                "entry_time": entry_time.isoformat(),
                "exit_time": exit_time.isoformat(),
                "entry_price": entry_price,
                "exit_price": exit_price,
                "size": size,
                "profit": profit_amount,
                "status": "closed"
            })

        # 生成权益曲线
        equity_curve = []
        initial_equity = 10000
        current_equity = initial_equity

        for i in range(365):
            point_time = now - timedelta(days=(365 - i))

            daily_return = np.random.normal(0.0005, 0.01)  # 均值0.05%，标准差1%
            current_equity *= (1 + daily_return)

            equity_curve.append({
                "time": point_time.isoformat(),
                "equity": current_equity
            })

        # 策略信息
        strategy_info = {
            "id": strategy_id,
            "name": f"Strategy {strategy_id}",
            "description": f"Auto-generated strategy {strategy_id} for demonstration",
            "market": np.random.choice(["BTC/USD", "ETH/USD", "XRP/USD", "ADA/USD"]),
            "timeframe": np.random.choice(["1m", "5m", "15m", "1h", "4h", "1d"]),
            "status": np.random.choice(["active", "paused", "testing"]),
            "created_date": (now - timedelta(days=np.random.randint(10, 100))).isoformat(),
            "price_data": price_points,
            "trades": trades,
            "equity_curve": equity_curve,
            "last_update": now.isoformat()
        }

        # 添加到活跃策略
        MONITOR_STATUS["active_strategies"][strategy_id] = strategy_info

        return strategy_info


def generate_performance_chart(strategy_id: str, timeframe: str = "1d") -> Dict[str, Any]:
    """
    生成策略性能图表
    
    Args:
        strategy_id (str): 策略ID
        timeframe (str, optional): 时间周期. Defaults to "1d".
        
    Returns:
        Dict[str, Any]: 图表数据
    """
    if not MONITOR_STATUS["initialized"]:
        raise MonitorInitError("Monitor not initialized")

    # 检查策略是否存在
    if strategy_id not in MONITOR_STATUS["active_strategies"]:
        return {
            "error": f"Strategy {strategy_id} not found"
        }

    strategy_data = MONITOR_STATUS["active_strategies"][strategy_id]

    # 处理时间周期
    now = datetime.now()
    if timeframe == "1d":
        start_time = now - timedelta(days=1)
    elif timeframe == "1w":
        start_time = now - timedelta(days=7)
    elif timeframe == "1m":
        start_time = now - timedelta(days=30)
    elif timeframe == "3m":
        start_time = now - timedelta(days=90)
    elif timeframe == "6m":
        start_time = now - timedelta(days=180)
    elif timeframe == "1y":
        start_time = now - timedelta(days=365)
    else:
        start_time = now - timedelta(days=30)  # 默认30天

    # 提取价格数据
    price_data = strategy_data.get("price_data", [])
    filtered_price_data = []

    for point in price_data:
        point_time = datetime.fromisoformat(point["time"])
        if point_time >= start_time:
            filtered_price_data.append(point)

    # 转换为DataFrame
    price_df = pd.DataFrame(filtered_price_data)
    if not price_df.empty:
        price_df["time"] = pd.to_datetime(price_df["time"])

    # 提取权益曲线数据
    equity_data = strategy_data.get("equity_curve", [])
    filtered_equity_data = []

    for point in equity_data:
        point_time = datetime.fromisoformat(point["time"])
        if point_time >= start_time:
            filtered_equity_data.append(point)

    # 转换为DataFrame
    equity_df = pd.DataFrame(filtered_equity_data)
    if not equity_df.empty:
        equity_df["time"] = pd.to_datetime(equity_df["time"])

    # 提取交易数据
    trades = strategy_data.get("trades", [])
    filtered_trades = []

    for trade in trades:
        exit_time = datetime.fromisoformat(trade["exit_time"])
        if exit_time >= start_time:
            filtered_trades.append(trade)

    # 转换为DataFrame
    trades_df = pd.DataFrame(filtered_trades)
    if not trades_df.empty:
        trades_df["entry_time"] = pd.to_datetime(trades_df["entry_time"])
        trades_df["exit_time"] = pd.to_datetime(trades_df["exit_time"])

    # 使用Plotly创建图表
    try:
        # 创建子图
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=("Price", "Equity"),
            row_heights=[0.7, 0.3]
        )

        # 添加价格线
        if not price_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=price_df["time"],
                    y=price_df["price"],
                    mode='lines',
                    name='Price',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )

        # 添加交易标记
        if not trades_df.empty:
            for _, trade in trades_df.iterrows():
                color = 'green' if trade["profit"] > 0 else 'red'

                # 入场标记
                fig.add_trace(
                    go.Scatter(
                        x=[trade["entry_time"]],
                        y=[trade["entry_price"]],
                        mode='markers',
                        marker=dict(
                            symbol='triangle-up' if trade["direction"] == "long" else 'triangle-down',
                            size=10,
                            color=color,
                            line=dict(width=2, color='black')
                        ),
                        name=f"Entry: {trade['direction']}",
                        showlegend=False
                    ),
                    row=1, col=1
                )

                # 出场标记
                fig.add_trace(
                    go.Scatter(
                        x=[trade["exit_time"]],
                        y=[trade["exit_price"]],
                        mode='markers',
                        marker=dict(
                            symbol='circle',
                            size=10,
                            color=color,
                            line=dict(width=2, color='black')
                        ),
                        name=f"Exit: {trade['profit']:.2f}",
                        showlegend=False
                    ),
                    row=1, col=1
                )

        # 添加权益曲线
        if not equity_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=equity_df["time"],
                    y=equity_df["equity"],
                    mode='lines',
                    name='Equity',
                    line=dict(color='purple')
                ),
                row=2, col=1
            )

        # 更新布局
        fig.update_layout(
            title=f"Strategy Performance: {strategy_data.get('name', strategy_id)}",
            xaxis_title="Time",
            yaxis_title="Price",
            yaxis2_title="Equity",
            height=800,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom",
                        y=1.02, xanchor="right", x=1)
        )

        # 转换为JSON
        chart_json = json.loads(fig.to_json())

        return {
            "chart": chart_json,
            "stats": _calculate_performance_stats(strategy_id, timeframe)
        }

    except Exception as e:
        logger.error(
            f"Error generating chart for strategy {strategy_id}: {str(e)}")
        return {
            "error": str(e)
        }


def _calculate_performance_stats(strategy_id: str, timeframe: str) -> Dict[str, Any]:
    """
    计算策略性能统计
    
    Args:
        strategy_id (str): 策略ID
        timeframe (str): 时间周期
        
    Returns:
        Dict[str, Any]: 性能统计
    """
    strategy_data = MONITOR_STATUS["active_strategies"].get(strategy_id, {})

    # 处理时间周期
    now = datetime.now()
    if timeframe == "1d":
        start_time = now - timedelta(days=1)
    elif timeframe == "1w":
        start_time = now - timedelta(days=7)
    elif timeframe == "1m":
        start_time = now - timedelta(days=30)
    elif timeframe == "3m":
        start_time = now - timedelta(days=90)
    elif timeframe == "6m":
        start_time = now - timedelta(days=180)
    elif timeframe == "1y":
        start_time = now - timedelta(days=365)
    else:
        start_time = now - timedelta(days=30)  # 默认30天

    # 提取交易数据
    trades = strategy_data.get("trades", [])
    filtered_trades = []

    for trade in trades:
        exit_time = datetime.fromisoformat(trade["exit_time"])
        if exit_time >= start_time:
            filtered_trades.append(trade)

    # 计算统计数据
    total_trades = len(filtered_trades)

    if total_trades == 0:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "average_profit": 0,
            "max_drawdown": 0,
            "sharpe_ratio": 0
        }

    winning_trades = sum(1 for trade in filtered_trades if trade["profit"] > 0)
    losing_trades = total_trades - winning_trades

    win_rate = winning_trades / total_trades if total_trades > 0 else 0

    total_profit = sum(trade["profit"]
                       for trade in filtered_trades if trade["profit"] > 0)
    total_loss = abs(sum(trade["profit"]
                     for trade in filtered_trades if trade["profit"] < 0))

    profit_factor = total_profit / \
        total_loss if total_loss > 0 else float('inf')

    average_profit = sum(trade["profit"] for trade in filtered_trades) / \
        total_trades if total_trades > 0 else 0

    # 计算夏普比率和最大回撤
    equity_curve = strategy_data.get("equity_curve", [])
    filtered_equity = []

    for point in equity_curve:
        point_time = datetime.fromisoformat(point["time"])
        if point_time >= start_time:
            filtered_equity.append(point)

    if filtered_equity:
        equity_values = [point["equity"] for point in filtered_equity]

        # 计算日收益率
        daily_returns = []
        for i in range(1, len(equity_values)):
            daily_return = (
                equity_values[i] - equity_values[i-1]) / equity_values[i-1]
            daily_returns.append(daily_return)

        # 夏普比率
        risk_free_rate = 0.02 / 252  # 假设无风险利率2%
        avg_return = np.mean(daily_returns) if daily_returns else 0
        std_return = np.std(daily_returns) if daily_returns else 1

        sharpe_ratio = (avg_return - risk_free_rate) / \
            std_return * np.sqrt(252) if std_return > 0 else 0

        # 最大回撤
        max_equity = equity_values[0]
        max_drawdown = 0

        for equity in equity_values:
            max_equity = max(max_equity, equity)
            drawdown = (max_equity - equity) / max_equity
            max_drawdown = max(max_drawdown, drawdown)
    else:
        sharpe_ratio = 0
        max_drawdown = 0

    return {
        "total_trades": total_trades,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "average_profit": average_profit,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe_ratio
    }


def get_active_strategies_status() -> Dict[str, Any]:
    """
    获取所有活跃策略状态
    
    Returns:
        Dict[str, Any]: 策略状态信息
    """
    if not MONITOR_STATUS["initialized"]:
        raise MonitorInitError("Monitor not initialized")

    strategies = {}

    for strategy_id, strategy_data in MONITOR_STATUS["active_strategies"].items():
        # 提取关键信息，不包括详细的价格和交易数据
        strategies[strategy_id] = {
            "id": strategy_id,
            "name": strategy_data.get("name", strategy_id),
            "description": strategy_data.get("description", ""),
            "market": strategy_data.get("market", "unknown"),
            "timeframe": strategy_data.get("timeframe", "unknown"),
            "status": strategy_data.get("status", "unknown"),
            "created_date": strategy_data.get("created_date", ""),
            "last_update": strategy_data.get("last_update", ""),
            "trade_count": len(strategy_data.get("trades", [])),
            "current_price": strategy_data.get("price_data", [{}])[-1].get("price", 0) if strategy_data.get("price_data") else 0,
            "current_equity": strategy_data.get("equity_curve", [{}])[-1].get("equity", 0) if strategy_data.get("equity_curve") else 0
        }

    return {
        "strategies": strategies,
        "summary": _calculate_dashboard_metrics(),
        "timestamp": datetime.now().isoformat()
    }


def _calculate_dashboard_metrics() -> Dict[str, Any]:
    """
    计算仪表板汇总指标
    
    Returns:
        Dict[str, Any]: 仪表板指标
    """
    active_strategies = MONITOR_STATUS["active_strategies"]

    if not active_strategies:
        return {
            "total_strategies": 0,
            "active_count": 0,
            "paused_count": 0,
            "total_trades": 0,
            "winning_trades": 0,
            "total_profit": 0,
            "best_strategy": None,
            "worst_strategy": None
        }

    # 基本计数
    total_strategies = len(active_strategies)
    active_count = sum(1 for s in active_strategies.values()
                       if s.get("status") == "active")
    paused_count = sum(1 for s in active_strategies.values()
                       if s.get("status") == "paused")

    # 交易统计
    all_trades = []
    for strategy in active_strategies.values():
        all_trades.extend(strategy.get("trades", []))

    total_trades = len(all_trades)
    winning_trades = sum(
        1 for trade in all_trades if trade.get("profit", 0) > 0)
    total_profit = sum(trade.get("profit", 0) for trade in all_trades)

    # 找出最佳和最差策略
    strategy_performance = []

    for strategy_id, strategy in active_strategies.items():
        trades = strategy.get("trades", [])

        if not trades:
            continue

        strategy_profit = sum(trade.get("profit", 0) for trade in trades)
        strategy_trade_count = len(trades)

        if strategy_trade_count > 0:
            strategy_performance.append({
                "id": strategy_id,
                "name": strategy.get("name", strategy_id),
                "profit": strategy_profit,
                "trade_count": strategy_trade_count,
                "avg_profit": strategy_profit / strategy_trade_count
            })

    best_strategy = None
    worst_strategy = None

    if strategy_performance:
        best_strategy = max(strategy_performance,
                            key=lambda x: x["avg_profit"])
        worst_strategy = min(strategy_performance,
                             key=lambda x: x["avg_profit"])

    return {
        "total_strategies": total_strategies,
        "active_count": active_count,
        "paused_count": paused_count,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "win_rate": winning_trades / total_trades if total_trades > 0 else 0,
        "total_profit": total_profit,
        "best_strategy": best_strategy,
        "worst_strategy": worst_strategy
    }


def run_server():
    """启动Flask服务器"""
    if not MONITOR_STATUS["initialized"]:
        raise MonitorInitError("Monitor not initialized")

    config = MONITOR_STATUS["config"]

    def start_server():
        app.run(
            host=config["host"],
            port=config["port"],
            debug=config["debug"]
        )

    # 创建并启动线程
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    MONITOR_STATUS["flask_server"] = server_thread
    logger.info(f"Server started at http://{config['host']}:{config['port']}")


def shutdown():
    """关闭监控系统"""
    global MONITOR_STATUS

    if not MONITOR_STATUS["initialized"]:
        return True

    try:
        # 停止更新线程
        MONITOR_STATUS["running"] = False

        # 保存状态
        _save_monitor_state()

        # 重置状态
        MONITOR_STATUS = {
            "initialized": False,
            "config": None,
            "flask_app": None,
            "flask_server": None,
            "active_strategies": {},
            "last_error": None,
            "update_thread": None,
            "running": False
        }

        logger.info("Monitor system shutdown successfully")
        return True

    except Exception as e:
        logger.error(f"Error shutting down monitor: {str(e)}")
        return False