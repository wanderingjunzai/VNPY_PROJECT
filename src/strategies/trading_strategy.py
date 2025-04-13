import logging
from datetime import datetime
from vnpy.trader.utility import ArrayManager
from vnpy.trader.object import (
    TickData, 
    BarData,
    OrderData,
    TradeData
)
from vnpy.trader.constant import (
    Direction,
    Offset,
    Status,
    Exchange,
    Interval,
    OrderType
)
from vnpy_ctastrategy import (
    CtaTemplate,
    StopOrder
)
from typing import List, Dict, Set

class HighFrequencyStrategy(CtaTemplate):
    author = "策略作者"
    
    # 策略参数
    fast_window = 5
    slow_window = 10
    rsi_window = 6
    rsi_entry = 40
    
    # 策略变量
    fast_ma0 = 0.0
    slow_ma0 = 0.0
    rsi_value = 0.0
    pos_price = 0.0
    
    parameters = ["fast_window", "slow_window", "rsi_window", "rsi_entry"]
    variables = ["fast_ma0", "slow_ma0", "rsi_value", "pos_price"]
    
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """策略初始化"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        # 设置日志
        self.logger = logging.getLogger(strategy_name)
        self.logger.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(console_handler)
        
        # 参数设置
        self.fast_window = setting.get('fast_window', 5)
        self.slow_window = setting.get('slow_window', 10)
        self.rsi_window = setting.get('rsi_window', 6)
        self.rsi_entry = setting.get('rsi_entry', 40)
        
        # 变量初始化
        self.fast_ma0 = 0.0
        self.slow_ma0 = 0.0
        self.rsi_value = 0.0
        
        # 指标初始化
        self.am = ArrayManager(100)
        self.active_orders = set()
        
        self.logger.info("策略初始化完成")
        self.write_log("策略初始化完成")

    def write_log(self, msg: str):
        """重写日志方法"""
        print(msg)  # 直接打印到控制台
        self.logger.info(msg)  # 同时通过logger记录

    def write_debug(self, msg: str):
        """写入调试信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        bar_time = getattr(self, 'current_bar_time', None)
        if bar_time:
            self.log_file.write(f"[{timestamp}][Bar时间:{bar_time}] {msg}\n")
        else:
            self.log_file.write(f"[{timestamp}] {msg}\n")
        self.log_file.flush()  # 确保立即写入
        print(msg)  # 同时打印到控制台
    
    def on_init(self):
        """策略初始化完成"""
        self.write_log("策略初始化完成")
        self.load_bar(10)

    def on_start(self):
        """策略启动"""
        self.write_log("策略启动")

    def on_stop(self):
        """策略停止"""
        self.write_log("策略停止")
        #self.log_file.close()  # 关闭日志文件

    def on_tick(self, tick: TickData):
        """Tick数据更新"""
        self.bg.update_tick(tick)
    
    def on_bar(self, bar: BarData):
        """K线更新"""
        self.am.update_bar(bar)
        if not self.am.inited:
            return

        fast_ma = self.am.sma(self.fast_window)
        slow_ma = self.am.sma(self.slow_window)
        rsi_value = self.am.rsi(self.rsi_window)
        
        # 记录指标数据
        self.fast_ma0 = fast_ma
        self.slow_ma0 = slow_ma
        self.rsi_value = rsi_value

        # 记录当前状态
        self.write_log(f"\n=== 当前状态 ===")
        self.write_log(f"K线时间: {bar.datetime}")
        self.write_log(f"当前仓位: {self.pos}")
        self.write_log(f"持仓成本: {self.pos_price}")

        # 有多头持仓时的平仓逻辑
        if self.pos > 0 and not self.active_orders:
            if rsi_value > 50 or fast_ma < slow_ma:
                self.write_log("\n=== 平仓信号触发 ===")
                try:
                    orderids = self.sell(bar.close_price, abs(self.pos))
                    if orderids:
                        self.active_orders.update(orderids)
                        self.write_log(f"平仓订单发送成功: {orderids}")
                except Exception as e:
                    self.write_log(f"平仓订单发送异常: {str(e)}")

        # 无持仓时的开仓逻辑
        elif self.pos == 0 and not self.active_orders:
            if rsi_value < 50 and fast_ma > slow_ma:
                self.write_log("\n=== 开仓信号触发 ===")
                try:
                    orderids = self.buy(bar.close_price, 1)
                    if orderids:
                        self.active_orders.update(orderids)
                        self.write_log(f"开仓订单发送成功: {orderids}")
                except Exception as e:
                    self.write_log(f"开仓订单发送异常: {str(e)}")

    def on_order(self, order: OrderData):
        """订单状态更新"""
        self.write_log(f"\n订单状态变化:")
        self.write_log(f"订单ID: {order.vt_orderid}")
        self.write_log(f"订单状态: {order.status}")
        self.write_log(f"委托价格: {order.price}")
        self.write_log(f"委托数量: {order.volume}")
        self.write_log(f"已成交: {order.traded}")
        self.write_log(f"剩余: {order.volume - order.traded}")
        
        if order.vt_orderid in self.active_orders:
            if order.status in [Status.ALLTRADED, Status.CANCELLED, Status.REJECTED]:
                self.active_orders.remove(order.vt_orderid)
                self.write_log(f"订单完成，从活动订单中移除: {order.vt_orderid}")
                self.write_log(f"剩余活动订单: {self.active_orders}")

    def on_trade(self, trade: TradeData):
        """成交更新"""
        self.write_log(f"\n=== 成交信息 ===")
        self.write_log(f"成交时间: {trade.datetime}")
        self.write_log(f"成交方向: {trade.direction}")
        self.write_log(f"成交价格: {trade.price}")
        self.write_log(f"成交数量: {trade.volume}")
        
        # 计算交易金额
        trade_value = trade.price * trade.volume
        
        # 更新持仓价格
        if trade.direction == Direction.LONG:
            self.pos_price = trade.price
        
        # 计算手续费
        commission = trade_value * self.cta_engine.rate
        
        # 记录交易信息
        self.write_log(f"\n=== 账户更新 ===")
        self.write_log(f"交易前仓位: {self.pos}")
        self.write_log(f"交易金额: {trade_value:.2f}")
        self.write_log(f"手续费: {commission:.2f}")
        
        # 更新后
        self.write_log(f"当前仓位: {self.pos}")
        self.write_log(f"持仓成本: {self.pos_price}")
        
        # 添加资金更新计算
        if trade.direction == Direction.LONG:
            net_value = -trade_value - commission
        else:  # SHORT
            profit = (trade.price - self.pos_price) * trade.volume
            net_value = trade_value - commission
            self.write_log(f"平仓盈亏: {profit:.2f}")
        
        # 更新账户余额
        self.cta_engine.capital += net_value
        
        self.write_log(f"\n=== 账户更新 ===")
        self.write_log(f"交易金额: {trade_value:.2f}")
        self.write_log(f"手续费: {commission:.2f}")
        self.write_log(f"净值变化: {net_value:.2f}")
        self.write_log(f"当前余额: {self.cta_engine.capital:.2f}")