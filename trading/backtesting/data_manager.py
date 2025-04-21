""" "
模块名称：trading.backtesting.data_manager
功能描述：回测数据管理系统，负责获取、处理和维护回测所需的历史数据
版本：1.0
创建日期：2025-04-20
作者：窗口9.3开发者
"""

import os
import logging
import config.paths as pd
import modules.nlp as np
from typing import Dict, List, Union, Optional, Tuple
from datetime import datetime, timedelta

# 设置日志记录器
logger = logging.getLogger(__name__)


class DataManager:
    """
    数据管理器类，用于获取和处理回测所需的历史交易数据

    属性:
        data_dir (str): 数据存储目录
        pairs (List[str]): 交易对列表
        timeframes (List[str]): 时间周期列表
        start_date (datetime): 回测开始日期
        end_date (datetime): 回测结束日期
        data_cache (Dict): 数据缓存，用于存储已加载的数据
    """

    def __init__(
        self,
        data_dir: str = "data/historical",
        pairs: List[str] = None,
        timeframes: List[str] = None,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ):
        """
        初始化数据管理器

        参数:
            data_dir (str): 数据存储目录，默认为"data/historical"
            pairs (List[str]): 交易对列表，例如 ["BTC/USDT", "ETH/USDT"]
            timeframes (List[str]): 时间周期列表，例如 ["1h", "4h", "1d"]
            start_date (Union[str, datetime]): 回测开始日期，格式为 "YYYY-MM-DD" 或 datetime 对象
            end_date (Union[str, datetime]): 回测结束日期，格式为 "YYYY-MM-DD" 或 datetime 对象

        返回:
            无

        异常:
            ValueError: 当参数无效时抛出异常
        """
        self.data_dir = data_dir
        self.pairs = pairs or []
        self.timeframes = timeframes or ["1h"]
        self.data_cache = {}

        # 处理日期参数
        self.start_date = self._parse_date(start_date) if start_date else None
        self.end_date = self._parse_date(end_date) if end_date else None

        # 验证参数
        self._validate_params()

        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)

        logger.info(
            f"初始化数据管理器: 交易对={self.pairs}, 时间周期={self.timeframes}"
        )

    def _validate_params(self) -> None:
        """
        验证初始化参数的有效性

        参数:
            无

        返回:
            无

        异常:
            ValueError: 当参数无效时抛出异常
        """
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValueError("开始日期必须早于结束日期")

        for timeframe in self.timeframes:
            if timeframe not in [
                "1m",
                "5m",
                "15m",
                "30m",
                "1h",
                "2h",
                "4h",
                "6h",
                "12h",
                "1d",
                "3d",
                "1w",
            ]:
                raise ValueError(f"不支持的时间周期: {timeframe}")

    def _parse_date(self, date_input: Union[str, datetime]) -> datetime:
        """
        解析日期输入，支持字符串或 datetime 对象

        参数:
            date_input (Union[str, datetime]): 日期输入，格式为 "YYYY-MM-DD" 或 datetime 对象

        返回:
            datetime: 解析后的 datetime 对象

        异常:
            ValueError: 当日期格式无效时抛出异常
        """
        if isinstance(date_input, datetime):
            return date_input

        try:
            return datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"无效的日期格式: {date_input}，应为 YYYY-MM-DD")

    def load_data(
        self,
        pair: str,
        timeframe: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> pd.DataFrame:
        """
        加载指定交易对和时间周期的历史数据

        参数:
            pair (str): 交易对，例如 "BTC/USDT"
            timeframe (str): 时间周期，例如 "1h"
            start_date (Union[str, datetime], 可选): 开始日期，默认为 None，使用初始化时的设置
            end_date (Union[str, datetime], 可选): 结束日期，默认为 None，使用初始化时的设置

        返回:
            pd.DataFrame: 包含历史数据的 DataFrame，列包括 [date, open, high, low, close, volume]

        异常:
            FileNotFoundError: 当数据文件不存在时抛出异常
            ValueError: 当参数无效时抛出异常
        """
        # 处理日期参数
        start = self._parse_date(start_date) if start_date else self.start_date
        end = self._parse_date(end_date) if end_date else self.end_date

        # 验证参数
        if pair not in self.pairs:
            self.pairs.append(pair)

        if timeframe not in self.timeframes:
            self.timeframes.append(timeframe)

        # 检查缓存
        cache_key = f"{pair}_{timeframe}"
        if cache_key in self.data_cache:
            df = self.data_cache[cache_key]
            # 根据日期范围过滤
            if start:
                df = df[df["date"] >= start]
            if end:
                df = df[df["date"] <= end]
            return df

        # 构建文件路径
        file_path = self._get_data_file_path(pair, timeframe)

        try:
            # 加载数据
            df = self._load_data_from_file(file_path)

            # 根据日期范围过滤
            if start:
                df = df[df["date"] >= start]
            if end:
                df = df[df["date"] <= end]

            # 存入缓存
            self.data_cache[cache_key] = df.copy()

            return df

        except FileNotFoundError:
            logger.error(f"数据文件不存在: {file_path}")
            raise FileNotFoundError(
                f"找不到交易对 {pair} 和时间周期 {timeframe} 的数据文件"
            )

    def _get_data_file_path(self, pair: str, timeframe: str) -> str:
        """
        获取数据文件路径

        参数:
            pair (str): 交易对
            timeframe (str): 时间周期

        返回:
            str: 数据文件路径
        """
        # 将交易对名称转换为适合文件名的格式
        pair_filename = pair.replace("/", "_")
        return os.path.join(self.data_dir, f"{pair_filename}_{timeframe}.csv")

    def _load_data_from_file(self, file_path: str) -> pd.DataFrame:
        """
        从文件中加载数据

        参数:
            file_path (str): 数据文件路径

        返回:
            pd.DataFrame: 加载的数据 DataFrame

        异常:
            FileNotFoundError: 当文件不存在时抛出异常
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"数据文件不存在: {file_path}")

        # 读取 CSV 文件
        df = pd.read_csv(file_path)

        # 确保日期列是 datetime 类型
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        elif "timestamp" in df.columns:
            df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
            df = df.drop("timestamp", axis=1)

        # 确保数据列名符合标准
        required_columns = ["date", "open", "high", "low", "close", "volume"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"数据文件缺少必要的列: {col}")

        # 按日期排序
        df = df.sort_values("date")

        return df

    def download_data(
        self,
        pair: str,
        timeframe: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        exchange: str = "binance",
    ) -> pd.DataFrame:
        """
        下载历史数据并保存

        注意：此方法需要与实际的数据提供者集成，当前仅为占位实现

        参数:
            pair (str): 交易对
            timeframe (str): 时间周期
            start_date (Union[str, datetime]): 开始日期
            end_date (Union[str, datetime]): 结束日期
            exchange (str): 交易所名称，默认为 "binance"

        返回:
            pd.DataFrame: 下载的数据 DataFrame

        异常:
            RuntimeError: 下载失败时抛出异常
        """
        # 这里应该实现与数据提供者的集成
        # 当前仅为提示实现，实际项目中需要与相应的API集成
        logger.info(
            f"下载数据: {pair}, {timeframe}, {start_date} - {end_date}, 交易所: {exchange}"
        )

        # TODO: 实现与数据提供者的集成
        # 例如: 使用 ccxt 库下载数据
        # 或者与 freqtrade 的数据下载功能集成

        raise NotImplementedError("数据下载功能尚未实现，请手动准备数据文件")

    def prepare_data_for_backtesting(
        self,
        pairs: List[str] = None,
        timeframes: List[str] = None,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        准备回测所需的所有数据

        参数:
            pairs (List[str], 可选): 交易对列表
            timeframes (List[str], 可选): 时间周期列表
            start_date (Union[str, datetime], 可选): 开始日期
            end_date (Union[str, datetime], 可选): 结束日期

        返回:
            Dict[str, Dict[str, pd.DataFrame]]: 按交易对和时间周期组织的数据字典
            示例: {'BTC/USDT': {'1h': df1, '4h': df2}, 'ETH/USDT': {'1h': df3}}

        异常:
            ValueError: 当参数无效时抛出异常
        """
        pairs = pairs or self.pairs
        timeframes = timeframes or self.timeframes

        if not pairs:
            raise ValueError("未指定交易对")

        if not timeframes:
            raise ValueError("未指定时间周期")

        result = {}

        for pair in pairs:
            result[pair] = {}
            for timeframe in timeframes:
                try:
                    df = self.load_data(pair, timeframe, start_date, end_date)
                    result[pair][timeframe] = df
                except FileNotFoundError:
                    logger.warning(
                        f"找不到交易对 {pair} 和时间周期 {timeframe} 的数据，跳过"
                    )

        return result

    def generate_mock_data(
        self,
        pair: str,
        timeframe: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        volatility: float = 0.02,
        trend: float = 0.0001,
        seed: int = None,
    ) -> pd.DataFrame:
        """
        生成模拟数据用于测试

        参数:
            pair (str): 交易对
            timeframe (str): 时间周期
            start_date (Union[str, datetime]): 开始日期
            end_date (Union[str, datetime]): 结束日期
            volatility (float): 波动率参数
            trend (float): 趋势参数
            seed (int, 可选): 随机种子

        返回:
            pd.DataFrame: 生成的模拟数据

        异常:
            ValueError: 当参数无效时抛出异常
        """
        # 处理日期参数
        start = self._parse_date(start_date)
        end = self._parse_date(end_date)

        if start >= end:
            raise ValueError("开始日期必须早于结束日期")

        # 设置随机种子以确保可重复性
        if seed:
            np.random.seed(seed)

        # 生成日期序列
        timeframe_to_minutes = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "2h": 120,
            "4h": 240,
            "6h": 360,
            "12h": 720,
            "1d": 1440,
            "3d": 4320,
            "1w": 10080,
        }

        if timeframe not in timeframe_to_minutes:
            raise ValueError(f"不支持的时间周期: {timeframe}")

        minutes = timeframe_to_minutes[timeframe]
        date_range = []
        current_date = start

        while current_date <= end:
            date_range.append(current_date)
            current_date += timedelta(minutes=minutes)

        # 生成价格数据
        n = len(date_range)
        closes = np.zeros(n)
        opens = np.zeros(n)
        highs = np.zeros(n)
        lows = np.zeros(n)
        volumes = np.zeros(n)

        # 初始价格
        price = 1000.0
        closes[0] = price

        # 生成价格序列
        for i in range(1, n):
            # 添加随机波动和趋势
            price_change = np.random.normal(trend, volatility) * price
            price += price_change
            closes[i] = max(0.01, price)  # 确保价格为正

        # 基于收盘价生成其他价格数据
        for i in range(n):
            # 为每个K线生成开盘价、最高价、最低价
            if i == 0:
                opens[i] = closes[i] * (1 - np.random.uniform(0, 0.005))
            else:
                opens[i] = closes[i - 1]

            price_range = closes[i] * volatility
            highs[i] = max(closes[i], opens[i]) + \
                np.random.uniform(0, price_range)
            lows[i] = min(closes[i], opens[i]) - \
                np.random.uniform(0, price_range)
            lows[i] = max(0.01, lows[i])  # 确保价格为正

            # 生成交易量
            volumes[i] = np.random.uniform(50, 200) * closes[i]

        # 创建 DataFrame
        df = pd.DataFrame(
            {
                "date": date_range,
                "open": opens,
                "high": highs,
                "low": lows,
                "close": closes,
                "volume": volumes,
            }
        )

        # 保存模拟数据
        file_path = self._get_data_file_path(pair, timeframe)
        df.to_csv(file_path, index=False)
        logger.info(f"生成并保存模拟数据: {file_path}")

        # 更新缓存
        cache_key = f"{pair}_{timeframe}"
        self.data_cache[cache_key] = df.copy()

        return df