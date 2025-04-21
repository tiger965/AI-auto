# GPT-Claude 通信系统

## 概述

GPT-Claude通信系统是一个完整的AI驱动量化交易模块，用于实现GPT-4o（决策大脑）与Claude（执行实现者）之间的通信、协作与反馈机制。该系统允许两个AI模型协同工作，共同完成加密货币量化交易任务。

## 功能特点

- **AI通信协议**：实现GPT和Claude之间的标准化通信
- **策略模板系统**：支持多种预定义策略模板和GPT动态生成策略
- **反馈分析系统**：收集、评估和分析策略执行的性能
- **完整执行流程**：从市场数据分析到策略执行再到性能评估的端到端流程
- **可扩展架构**：支持添加新的AI模型、策略模板和反馈机制

## 模块结构

```
trading/gpt_claude/
├── __init__.py                # 模块入口
├── communication.py           # 通信协议实现
├── feedback_system.py         # 反馈系统实现
├── templates/                 # 策略模板
│   ├── __init__.py
│   └── strategy_templates.py  # 策略模板管理
├── example_usage.py           # 使用示例
└── README.md                  # 本文档
```

## 主要组件

### 通信组件

- **GptCommunicator**: 负责与GPT API通信，发送决策请求和接收响应
- **ClaudeCommunicator**: 负责与Claude API通信，发送执行指令和接收结果
- **CommunicationManager**: 协调GPT和Claude之间的通信，管理完整工作流

### 反馈系统

- **FeedbackCollector**: 收集和存储策略执行的反馈数据
- **PerformanceEvaluator**: 评估策略执行的性能，计算质量评分
- **FeedbackAnalyzer**: 分析反馈数据，生成改进建议

### 模板系统

- **StrategyTemplate**: 定义策略模板的结构和渲染方法
- **StrategyTemplateManager**: 管理策略模板的加载、存储和使用

## 使用方法

### 基本使用流程

1. 初始化通信组件和模板管理器
2. 准备市场数据和配置参数
3. 执行交易工作流
4. 收集反馈并分析性能
5. 优化策略

### 代码示例

```python
# 初始化通信组件
gpt_communicator = GptCommunicator(api_key="YOUR_GPT_API_KEY", model="gpt-4o")
claude_communicator = ClaudeCommunicator(api_key="YOUR_CLAUDE_API_KEY", model="claude-3-sonnet-20240229")

# 初始化通信管理器
comm_manager = CommunicationManager(
    gpt_communicator=gpt_communicator,
    claude_communicator=claude_communicator
)

# 准备市场数据和配置
market_data = {...}  # 市场数据
config = {...}       # 配置参数

# 执行交易工作流
result = comm_manager.execute_trading_workflow(market_data, config)

# 性能评估
evaluator = PerformanceEvaluator()
performance = evaluator.evaluate_execution(result, market_data)

# 反馈收集
collector = FeedbackCollector()
feedback_id = collector.add_execution_feedback(result, market_data)
collector.add_performance_feedback(feedback_id, performance)

# 反馈分析
analyzer = FeedbackAnalyzer(collector)
learning_feedback = analyzer.generate_learning_feedback(strategy_id)
```

### 策略模板使用

```python
# 初始化模板管理器
template_manager = StrategyTemplateManager()
template_manager.load_default_templates()

# 列出可用模板
templates = template_manager.list_templates()

# 从模板创建策略
strategy_info = template_manager.create_strategy_from_template(
    template_id="basic_strategy",
    strategy_name="MACD交叉策略",
    strategy_params={...}  # 策略参数
)

# 创建GPT提示
prompt = template_manager.create_prompt_for_gpt(
    task_type="strategy_generation",
    market_data=market_data,
    config=config
)
```

## 配置参数

### 通信配置

- `api_key`: API密钥
- `model`: 使用的模型名称
- `endpoint`: API端点（可选）
- `temperature`: 生成温度，控制创造性（0.0-1.0）
- `max_tokens`: 最大生成令牌数（仅用于Claude）

### 策略配置

- `available_strategies`: 可用策略列表
- `risk_profile`: 风险偏好（low/medium/high）
- `time_horizon`: 时间周期（short/medium/long）
- `constraints`: 交易约束条件

### 反馈配置

- `storage_path`: 反馈数据存储路径
- `lookback_days`: 反馈分析回溯天数

## 系统集成

该模块设计为与现有的交易API和数据源无缝集成。主要集成点：

1. **与核心API集成**：通过窗口9.1开发的核心API进行集成
2. **与策略模板系统集成**：通过窗口9.2开发的策略模板系统进行集成
3. **与回测系统集成**：支持窗口9.3开发的回测系统
4. **与交易所连接器集成**：支持窗口9.5开发的交易所连接器

## 安全考虑

系统实现了以下安全机制：

- API密钥安全存储
- 错误处理和异常恢复
- 交易操作验证
- 日志和审计跟踪

## 扩展指南

### 添加新的通信组件

1. 继承`AIComponent`抽象类
2. 实现`send_message`和`process_response`方法
3. 在`CommunicationManager`中集成新组件

### 添加新的策略模板

1. 创建新的模板内容
2. 实例化`StrategyTemplate`类
3. 使用`StrategyTemplateManager.add_template`方法添加

### 扩展反馈系统

1. 添加新的性能指标
2. 实现自定义性能评估逻辑
3. 扩展学习反馈生成算法

## 注意事项

1. API密钥应从配置文件或环境变量获取，不应硬编码
2. 确保数据目录有适当的读写权限
3. 注意API请求速率限制
4. 定期备份反馈数据和策略模板
5. 进行充分的测试和验证，特别是在实际交易前

## 开发团队

- 窗口9.6：GPT-Claude通信系统

## 版本历史

- 1.0.0（2025-04-20）：初始版本，实现基本功能