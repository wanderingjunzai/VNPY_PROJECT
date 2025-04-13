from datetime import datetime
import sys
import logging
from pathlib import Path
from typing import List, Dict
from vnpy.trader.object import BarData, OrderData, TradeData
from vnpy.trader.constant import Exchange, Interval, Status, Direction
from vnpy_ctastrategy.backtesting import BacktestingEngine, CtaTemplate, BacktestingMode
from pymongo import MongoClient
import pandas as pd
import numpy as np

class BacktestEngine:
    def __init__(self):
        """初始化回测引擎"""
        self.engine = BacktestingEngine()
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.crypto_trading
        self.collection = self.db.market_data
        
        # 设置引擎基础参数
        self.init_capital = 1_000_000  # 初始资金100万
        self.contract_multiplier = 1    # 合约乘数
        self.commission_rate = 0.001    # 手续费率 0.1%
        self.price_tick = 0.01         # 价格精度

        self.setup_logging()

    def setup_logging(self):
        """配置日志系统"""
        # 创建logs目录
        log_dir = Path("d:/MFE5210/logs")
        log_dir.mkdir(exist_ok=True)
        
        # 生成日志文件名
        log_filename = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file = log_dir / log_filename
        
        # 配置根日志记录器
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(
            filename=log_file,
            mode='a',
            encoding='utf-8'
        )
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        print(f"日志文件保存在: {log_file}")

    def load_bar_data(self, symbol: str, start: datetime, end: datetime) -> List[BarData]:
        query = {
            "symbol": symbol,
            "datetime": {
                "$gte": start,
                "$lt": end
            }
        }
        
        cursor = self.collection.find(query).sort("datetime", 1)
        bars = []
        
        print(f"开始加载{symbol}的历史数据...")
        
        for doc in cursor:
            # 打印第一条数据用于调试
            if len(bars) == 0:
                print("首条数据样例:")
                print(doc)
                
            bar = BarData(
                symbol=doc["symbol"],
                exchange=Exchange.LOCAL,
                datetime=doc["datetime"],
                interval=Interval.MINUTE,
                volume=float(doc["volume"]),
                open_price=float(doc["open"]),
                high_price=float(doc["high"]),
                low_price=float(doc["low"]),
                close_price=float(doc["close"]),
                gateway_name="BACKTEST"
            )
            bars.append(bar)
        
        print(f"数据加载完成，共{len(bars)}条K线")
        
        # 打印首尾数据时间用于验证
        if bars:
            print(f"数据时间范围: {bars[0].datetime} 到 {bars[-1].datetime}")
        
        return bars

    def run_backtest(self, strategy_class, setting: Dict, symbol: str, start: datetime, end: datetime):
        """运行回测"""
        print("\n正在初始化回测引擎...")
        
        # 设置初始资金
        initial_capital = 1_000_000
        
        # 设置回测参数
        self.engine.set_parameters(
            vt_symbol=f"{symbol}.LOCAL",
            interval=Interval.MINUTE,
            start=start,
            end=end,
            rate=0.001,
            slippage=0,
            size=1,
            pricetick=0.01,
            capital=initial_capital  # 使用变量确保一致性
        )
        
        print(f"初始资金设置为: {initial_capital:,}")
        
        # 添加策略
        self.strategy = self.engine.add_strategy(strategy_class, setting)
        
        # 启用交易
        self.engine.strategy.trading = True
        
        # 检查引擎状态
        print("\n检查回测引擎状态:")
        print(f"交易对: {symbol}")
        print(f"初始资金: {self.engine.capital:,.2f}")
        print(f"手续费率: {self.engine.rate}")
        
        # 加载数据
        bars = self.load_bar_data(symbol, start, end)
        if not bars:
            return None
            
        print("\n开始回测运行...")
        
        # 运行K线回放
        for bar in bars:
            self.engine.new_bar(bar)
        
        # 完成回测
        self.engine.run_backtesting()
        df = self.engine.calculate_result()
        
        if df is not None and not df.empty:
            # 添加账户余额列
            df['balance'] = initial_capital  # 初始化余额列
            
            # 获取所有交易记录
            trades = self.engine.get_all_trades()
            if trades:
                print(f"\n=== 交易统计 ===")
                print(f"总成交笔数: {len(trades)}")
                print(f"初始资金: {initial_capital:,.2f}")
                
                # 计算每笔交易后的余额
                current_balance = initial_capital
                for trade in trades:
                    trade_value = trade.price * trade.volume
                    commission = trade_value * self.engine.rate
                    
                    if trade.direction == Direction.LONG:
                        current_balance -= (trade_value + commission)
                    else:
                        current_balance += (trade_value - commission)
                        
                print(f"最终资金: {current_balance:,.2f}")
                print(f"总收益率: {((current_balance - initial_capital) / initial_capital * 100):.2f}%")
                
                return df

        return None

    def calculate_statistics(self, df) -> Dict[str, float]:
        """计算回测统计指标"""
        # 获取所有交易
        trades = self.engine.get_all_trades()
        if not trades:
            return None
            
        # 初始化变量
        initial_capital = self.engine.capital
        final_capital = self.engine.capital
        open_price = 0  # 用于记录开仓价格
        win_count = 0   # 记录盈利笔数
        
        # 计算每笔交易的收益
        for trade in trades:
            trade_value = trade.price * trade.volume
            commission = trade_value * self.engine.rate
            
            if trade.direction == Direction.LONG:
                open_price = trade.price  # 记录开仓价格
                final_capital -= (trade_value + commission)
            else:  # SHORT - 平仓
                if open_price > 0:  # 确保有开仓价格
                    # 如果平仓价格高于开仓价格，则为盈利交易
                    if trade.price > open_price:
                        win_count += 1
                final_capital += (trade_value - commission)
        
        # 计算各项指标
        total_days = (trades[-1].datetime - trades[0].datetime).days
        total_return = (final_capital - initial_capital) / initial_capital * 100
        annual_return = total_return * 365 / total_days if total_days > 0 else 0
        win_rate = (win_count / (len(trades) // 2)) * 100 if trades else 0  # 除以2因为每对交易包含开仓和平仓
        
        # 计算最大回撤
        max_drawdown = 0
        peak = initial_capital
        current_capital = initial_capital
        
        for trade in trades:
            trade_value = trade.price * trade.volume
            commission = trade_value * self.engine.rate
            
            if trade.direction == Direction.LONG:
                current_capital -= (trade_value + commission)
            else:
                current_capital += (trade_value - commission)
                
            drawdown = (peak - current_capital) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
            peak = max(peak, current_capital)
        
        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "sharpe_ratio": 0.0,  # 需要日收益率数据才能计算
            "max_drawdown": max_drawdown,
            "win_rate": win_rate
        }

    def get_strategy(self):
        """获取当前正在运行的策略实例"""
        return getattr(self, 'strategy', None)