import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
import pyqtgraph as pg

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("量化交易系统")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中心窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建图表
        self.price_plot = pg.PlotWidget()
        self.price_plot.setTitle("价格走势")
        layout.addWidget(self.price_plot)
        
        self.pnl_plot = pg.PlotWidget()
        self.pnl_plot.setTitle("盈亏曲线")
        layout.addWidget(self.pnl_plot)
        
    def update_price_chart(self, data):
        self.price_plot.clear()
        self.price_plot.plot(data['close'].values)
        
    def update_pnl_chart(self, data):
        self.pnl_plot.clear()
        self.pnl_plot.plot(data['cumulative_pnl'].values)