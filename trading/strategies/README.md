# 量化交易策略模板系统

本模块提供了一个完整的量化交易策略框架，实现了与Freqtrade框架兼容的策略模板系统，支持基本策略和高级策略的开发，以及GPT自动生成策略功能。

## 目录结构

```
trading/strategies/
├── __init__.py                      # 模块入口点
├── templates/                       # 策略模板
│   ├── __init__.py
│   ├── basic_strategy.py            # 基础策略模板
│   ├── advanced_strategy.py         # 高级策略模板
│   └── strategy_template_reference.py # 参考模板
├── generated/                       # GPT生成的策略
│   ├── __init__.py
│   └── macd_crossover_strategy.py   # 示例生成策略
├── strategy_generator.py            # 策略生成器
├── strategy_validator.py            # 策略验证器
└── strategy_factory.py              # 策略工厂
```

## 主要功能

1. **策略模板**：提供基础和高级策略模板，兼容Freqtrade框架
2. **策略生成**：使用GPT自动生成基于模板的策略
3. **策略验证**：验证策略有效性和兼容性
4. **策略工厂**：管理和创建策略实例

## 快速开始

### 使用现有策略模板

```python
from trading.strategies import BasicStrategy, AdvancedStrategy

# 创建基础策略实例
basic_strategy = BasicStrategy()

# 创建高级策略实例
advanced_strategy = AdvancedStrategy()

# 使用策略处理数据
import pandas as pd

# 准备数据
data = pd.read_csv('ohlcv_data.csv')
metadata = {'pair': 'BTC/USDT'}

# 计算指标
data_with_indicators = basic_strategy.populate_indicators(data, metadata)

# 生成买入信号
data_with_buy_signals = basic_strategy.populate_entry_trend(data_with_indicators, metadata)

# 生成卖出信号
data_with_signals = basic_strategy.populate_exit_trend(data_with_buy_signals, metadata)
```

### 使用策略工厂

```python
from trading.strategies.strategy_factory import strategy_factory

# 列出可用模板
templates = strategy_factory.list_templates()
print(f"可用模板: {list(templates.keys())}")

# 列出可用策略
strategies = strategy_factory.list_strategies()
print(f"可用策略: {list(strategies.keys())}")

# 基于模板创建新策略
new_strategy = strategy_factory.create_from_template(
    template_name='BasicStrategy',
    class_name='MyCustomStrategy',
    parameters={
        'stoploss': -0.05,
        'timeframe': '30m'
    }
)

# 创建已有策略的实例
macd_strategy = strategy_factory.create_strategy('MacdCrossoverStrategy')
```

### 使用策略生成器

```python
from trading.strategies.strategy_generator import StrategyGenerator

# 创建策略生成器实例（需要传入GPT接口）
generator = StrategyGenerator(gpt_interface=my_gpt_interface)

# 列出可用模板
templates = generator.list_templates()

# 生成新策略
success, message, strategy_code = generator.generate_strategy(
    template_name='basic',
    strategy_name='MyMacdStrategy',
    parameters={
        'description': '使用MACD指标的趋势跟踪策略',
        'indicators': ['MACD', 'RSI', 'SMA'],
        'entry_conditions': 'MACD金叉且RSI低于50',
        'exit_conditions': 'MACD死叉或RSI高于70'
    }
)

if success:
    # 保存生成的策略
    from trading.strategies import save_generated_strategy
    save_generated_strategy('MyMacdStrategy', strategy_code)
```

### 验证策略

```python
from trading.strategies.strategy_validator import StrategyValidator

# 验证策略类
is_valid, issues = StrategyValidator.validate_strategy_class(MyCustomStrategy)

if is_valid:
    print("策略验证通过!")
else:
    print(f"策略验证失败: {issues}")

# 验证策略文件
is_valid, issues, strategy_class = StrategyValidator.validate_strategy_file(
    'path/to/strategy_file.py'
)

# 动态测试策略
is_valid, issues, test_results = StrategyValidator.dynamic_test(MyCustomStrategy)
```

## 开发自定义策略

### 基础策略模板

基础策略模板提供了简单的技术指标和交易规则实现，适合初学者和简单策略开发。

主要功能：
- SMA指标计算
- RSI指标计算
- 基于SMA和RSI的简单交易规则

### 高级策略模板

高级策略模板提供了更丰富的功能，包括市场状态检测、多重确认信号和风险管理，适合有经验的交易者和复杂策略开发。

主要功能：
- 全套技术指标（SMA、EMA、RSI、MACD、布林带等）
- 市场状态分类（趋势、震荡）
- 趋势方向识别
- 基于多重确认的信号生成
- 自定义止损
- 追踪止损

### 策略参考模板

策略参考模板提供了Freqtrade框架支持的所有功能的示例实现，可作为开发新策略的参考。

## 与GPT-4o集成

本模块设计了与GPT-4o进行集成的接口，使GPT能够根据需求生成新的交易策略。生成的策略保存在`generated/`目录中，可以直接被系统调用。

## 单元测试

每个策略模板都有对应的单元测试，确保策略功能正常。测试位于`tests/`目录中。

## 代码规范

本模块遵循项目的统一开发规范，包括命名规范、文档规范、错误处理规范等。详见项目总文档。