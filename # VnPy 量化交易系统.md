# VnPy 量化交易系统

基于 VnPy 3.9.4 开发的高频量化交易系统，支持加密货币交易，具备完整的策略回测、实盘交易和风险管理功能。

## 系统架构

- 数据获取：使用 vnpy-binance 接口获取历史数据和实时行情
- 数据存储：MongoDB 数据库
- 回测引擎：自主开发的回测系统，支持多品种回测
- 交易执行：对接币安模拟交易接口
- 风险控制：实时监控持仓风险、资金风险等
- 可视化界面：基于 PyQt5 的监控界面

## 主要功能

1. 数据模块
   - 历史数据获取与存储
   - 实时行情订阅
   - 数据清洗与预处理

2. 策略模块
   - 日内高频交易策略
   - 信号生成与过滤
   - 仓位管理

3. 回测模块
   - 历史数据回测
   - 性能评估指标(Sharpe比率、最大回撤等)
   - 交易成本分析(TCA)

4. 风控模块
   - 资金风险控制
   - 持仓限制
   - 订单审核
   - 风险预警

5. GUI界面
   - 策略监控
   - 持仓查看
   - 资金曲线
   - 风险指标展示

## 环境配置

```bash
# 运行环境要求
Python 3.9
VnPy 3.9.4
MongoDB

# 安装依赖
pip install -r requirements.txt
```

## 快速开始

1. 配置币安API
```python
# config/config.json 中填入API信息
{
    "api_key": "your_api_key",
    "secret_key": "your_secret_key"
}
```

2. 启动系统
```python
python main.py
```

## 项目结构

- src/
  - strategies/: 交易策略实现
  - backtest/: 回测引擎
  - execution/: 交易执行模块
  - gui/: 图形界面
  - database/: 数据库操作
  - risk_management/: 风险管理模块
  - data/: 数据获取与处理

## 使用说明

1. 数据获取
```python
from src.data.data_fetcher import BinanceDataFetcher
fetcher = BinanceDataFetcher()
data = fetcher.fetch_history("BTCUSDT", "1m", "2024-01-01")
```

2. 回测运行
```python
from src.backtest.backtest_engine import BacktestEngine
engine = BacktestEngine()
engine.run(strategy, start_date, end_date)
```

## 注意事项

- 请确保已正确配置币安API密钥
- 建议先使用模拟盘测试策略
- 实盘交易前请充分回测验证策略有效性

## 开发计划

- [ ] 增加更多交易策略
- [ ] 优化回测性能
- [ ] 添加更多风控指标
- [ ] 完善GUI界面

## 作者

MFE5210
