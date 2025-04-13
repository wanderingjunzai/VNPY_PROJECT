from typing import Dict
import numpy as np

class RiskManager:
    def __init__(self, config: Dict):
        self.risk_limit = config['risk_limit']
        self.max_positions = config['max_positions']
        self.positions = {}
        
    def check_order(self, symbol: str, price: float, 
                    volume: float, direction: str) -> bool:
        """检查订单是否符合风险控制要求"""
        # 检查持仓数量限制
        if len(self.positions) >= self.max_positions:
            return False
            
        # 检查单个交易品种的资金使用比例
        position_value = price * volume
        total_value = sum(p['value'] for p in self.positions.values())
        
        if position_value / (total_value + position_value) > self.risk_limit:
            return False
            
        return True
        
    def update_position(self, symbol: str, price: float, 
                       volume: float, direction: str):
        """更新持仓信息"""
        if direction == "buy":
            self.positions[symbol] = {
                "volume": volume,
                "value": price * volume
            }
        else:
            if symbol in self.positions:
                del self.positions[symbol]
                
    def calculate_var(self, returns: np.array, 
                     confidence_level: float = 0.95) -> float:
        """计算VaR风险价值"""
        return np.percentile(returns, (1 - confidence_level) * 100)