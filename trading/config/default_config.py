""" "
Default configuration for trading system.

This module defines the default configuration values for the trading system.
All values can be overridden by user configuration.
"""

from typing import Dict, Any

# Default configuration dictionary
DEFAULT_CONFIG: Dict[str, Any] = {
    # General settings
    "dry_run": True,  # Run in simulation mode
    "debug": False,  # Enable debug mode
    "log_level": "INFO",  # Logging level
    # Exchange settings
    "exchange": {
        "name": "binance",  # Default exchange
        "key": "",  # API key
        "secret": "",  # API secret
        "ccxt_config": {},  # Additional CCXT config
        "ccxt_async_config": {},  # Additional CCXT async config
        "pair_whitelist": [],  # List of pairs to trade
        "pair_blacklist": [],  # List of pairs to exclude
    },
    # Trading parameters
    "trading": {
        "stake_currency": "USDT",  # Stake currency
        "stake_amount": 100,  # Amount to stake per trade
        "max_open_trades": 3,  # Maximum number of open trades
        "minimal_roi": {  # Minimal ROI configuration
            "0": 0.10,  # 10% profit after 0 minutes
            "30": 0.05,  # 5% profit after 30 minutes
            "60": 0.02,  # 2% profit after 60 minutes
            "120": 0.01,  # 1% profit after 2 hours
        },
        "stoploss": -0.10,  # 10% stop loss
        "trailing_stop": False,  # Enable trailing stop
        # Move stop to 1% profit when reaching this positive profit
        "trailing_stop_positive": 0.01,
        # Offset from current price for trailing stop
        "trailing_stop_positive_offset": 0.02,
        # Only activate trailing stop when offset is reached
        "trailing_only_offset_is_reached": False,
    },
    # Strategy settings
    "strategy": {
        "name": "BasicStrategy",  # Default strategy name
        "parameters": {},  # Strategy-specific parameters
    },
    # Backtesting settings
    "backtesting": {
        "timeframe": "5m",  # Default timeframe for backtesting
        "timerange": "",  # Backtesting timerange
        "days": 30,  # Number of days to backtest
        "export": "",  # Export results to CSV file
    },
    # Optimization settings
    "optimization": {
        "enable": False,  # Enable optimization
        "max_trials": 100,  # Maximum number of trials
        "epochs": 10,  # Number of epochs
        "spaces": ["buy", "sell"],  # Parameter spaces to optimize
        "hyperopt_loss": "ShortTradeDurHyperOptLoss",  # Default hyperopt loss function
    },
    # GPT-Claude integration
    "gpt_claude": {
        "enable": False,  # Enable GPT-Claude integration
        "api_key": "",  # API key for GPT/Claude
        "model": "claude-3-sonnet-20240229",  # Default model
        "strategy_template": "basic",  # Strategy template to use
        "max_tokens": 4000,  # Maximum tokens to generate
        "temperature": 0.7,  # Temperature for generation
    },
    # User interface
    "ui": {
        "enable": True,  # Enable UI
        "server": {
            "host": "127.0.0.1",  # UI server host
            "port": 8080,  # UI server port
            "username": "",  # Basic auth username
            "password": "",  # Basic auth password
        },
        "features": {
            "strategy_editor": True,  # Enable strategy editor
            "backtesting": True,  # Enable backtesting in UI
            "trading": True,  # Enable live trading in UI
        },
    },
    # Data handling
    "data": {
        "directory": "user_data/data",  # Data directory
        "pairs": [],  # List of pairs to download data for
        # Timeframes to download
        "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
        "exchange": "binance",  # Exchange to download data from
        "dataformat_ohlcv": "json",  # Format for OHLCV data files
        "dataformat_trades": "jsongz",  # Format for trades data files
    },
}

# Export public components
__all__ = ["DEFAULT_CONFIG"]