import json
from datetime import datetime
from src.data.data_fetcher import DataFetcher
from src.strategies.trading_strategy import HighFrequencyStrategy
from src.backtest.backtest_engine import BacktestEngine
from src.gui.main_window import MainWindow
from src.risk_management.risk_manager import RiskManager
from PyQt5.QtWidgets import QApplication
import sys

def main():
    # 加载配置
    with open("config/config.json", "r") as f:
        config = json.load(f)
    
    # 初始化各个模块
    data_fetcher = DataFetcher(
        config['binance']['api_key'],
        config['binance']['secret_key'],
        config['binance']['test_net']
    )
    
    risk_manager = RiskManager(config['trading'])
    
    # 获取更长时间的历史数据
    data = data_fetcher.fetch_history(
        symbol="BTC/USDT",  # 注意：CCXT使用/分隔符
        interval="1m",
        start_time="2024-01-01",
        end_time="2025-01-31"
    )
    
    # 转换symbol格式并保存到数据库
    data_fetcher.save_to_database(data, "BTCUSDT", "1m")
    
    # 回测使用相同的时间段
    backtest = BacktestEngine()
    start = datetime(2023, 1, 1)
    end = datetime(2024, 4, 12)
    
    result = backtest.run(
        HighFrequencyStrategy,
        {},
        "BTCUSDT",
        start,
        end
    )
    
    print("回测结果：", result)
    
    # 启动GUI
    app = QApplication(sys.argv)
    window = MainWindow()
    window.update_price_chart(data)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()