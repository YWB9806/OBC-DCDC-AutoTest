"""性能监控面板

显示系统性能指标和执行统计信息。
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QProgressBar, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor


class PerformancePanel(QWidget):
    """性能监控面板组件"""
    
    def __init__(self, container, parent=None):
        """初始化性能监控面板
        
        Args:
            container: 依赖注入容器
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.container = container
        self.logger = container.resolve('log_manager').get_logger('ui')
        self.performance_service = container.resolve('performance_monitor_service')
        
        self._init_ui()
        
        # 创建定时器用于更新性能指标
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_metrics)
        self._update_timer.setInterval(2000)  # 每2秒更新一次
        self._update_timer.start()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 系统信息组
        system_group = QGroupBox("系统信息")
        system_layout = QVBoxLayout()
        
        # CPU信息
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU使用率:"))
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_progress.setValue(0)
        cpu_layout.addWidget(self.cpu_progress)
        self.cpu_label = QLabel("0%")
        self.cpu_label.setMinimumWidth(50)
        cpu_layout.addWidget(self.cpu_label)
        system_layout.addLayout(cpu_layout)
        
        # 内存信息
        memory_layout = QHBoxLayout()
        memory_layout.addWidget(QLabel("内存使用率:"))
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        self.memory_progress.setValue(0)
        memory_layout.addWidget(self.memory_progress)
        self.memory_label = QLabel("0%")
        self.memory_label.setMinimumWidth(50)
        memory_layout.addWidget(self.memory_label)
        system_layout.addLayout(memory_layout)
        
        # 磁盘信息
        disk_layout = QHBoxLayout()
        disk_layout.addWidget(QLabel("磁盘使用率:"))
        self.disk_progress = QProgressBar()
        self.disk_progress.setRange(0, 100)
        self.disk_progress.setValue(0)
        disk_layout.addWidget(self.disk_progress)
        self.disk_label = QLabel("0%")
        self.disk_label.setMinimumWidth(50)
        disk_layout.addWidget(self.disk_label)
        system_layout.addLayout(disk_layout)
        
        system_group.setLayout(system_layout)
        layout.addWidget(system_group)
        
        # 进程信息组
        process_group = QGroupBox("进程信息")
        process_layout = QVBoxLayout()
        
        # 进程CPU
        process_cpu_layout = QHBoxLayout()
        process_cpu_layout.addWidget(QLabel("进程CPU:"))
        self.process_cpu_label = QLabel("0%")
        process_cpu_layout.addWidget(self.process_cpu_label)
        process_cpu_layout.addStretch()
        process_layout.addLayout(process_cpu_layout)
        
        # 进程内存
        process_mem_layout = QHBoxLayout()
        process_mem_layout.addWidget(QLabel("进程内存:"))
        self.process_memory_label = QLabel("0 MB")
        process_mem_layout.addWidget(self.process_memory_label)
        process_mem_layout.addStretch()
        process_layout.addLayout(process_mem_layout)
        
        # 线程数
        thread_layout = QHBoxLayout()
        thread_layout.addWidget(QLabel("线程数:"))
        self.thread_label = QLabel("0")
        thread_layout.addWidget(self.thread_label)
        thread_layout.addStretch()
        process_layout.addLayout(thread_layout)
        
        process_group.setLayout(process_layout)
        layout.addWidget(process_group)
        
        # 执行统计组
        stats_group = QGroupBox("执行统计 (最近7天)")
        stats_layout = QVBoxLayout()
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["指标", "值"])
        self.stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.stats_table.setMaximumHeight(200)
        stats_layout.addWidget(self.stats_table)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新统计")
        refresh_btn.clicked.connect(self._refresh_statistics)
        stats_layout.addWidget(refresh_btn)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # 初始加载统计信息
        self._refresh_statistics()
    
    def _update_metrics(self):
        """更新性能指标"""
        try:
            metrics = self.performance_service.get_current_metrics()
            
            if not metrics:
                return
            
            # 更新系统指标
            system = metrics.get('system', {})
            cpu_percent = system.get('cpu_percent', 0)
            memory_percent = system.get('memory_percent', 0)
            disk_percent = system.get('disk_percent', 0)
            
            self.cpu_progress.setValue(int(cpu_percent))
            self.cpu_label.setText(f"{cpu_percent:.1f}%")
            self._set_progress_color(self.cpu_progress, cpu_percent)
            
            self.memory_progress.setValue(int(memory_percent))
            self.memory_label.setText(f"{memory_percent:.1f}%")
            self._set_progress_color(self.memory_progress, memory_percent)
            
            self.disk_progress.setValue(int(disk_percent))
            self.disk_label.setText(f"{disk_percent:.1f}%")
            self._set_progress_color(self.disk_progress, disk_percent)
            
            # 更新进程指标
            process = metrics.get('process', {})
            process_cpu = process.get('cpu_percent', 0)
            process_memory = process.get('memory_mb', 0)
            num_threads = process.get('num_threads', 0)
            
            self.process_cpu_label.setText(f"{process_cpu:.1f}%")
            self.process_memory_label.setText(f"{process_memory:.1f} MB")
            self.thread_label.setText(str(num_threads))
        
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")
    
    def _refresh_statistics(self):
        """刷新统计信息"""
        try:
            stats = self.performance_service.get_execution_statistics(days=7)
            
            # 清空表格
            self.stats_table.setRowCount(0)
            
            # 添加统计数据
            stats_items = [
                ("总执行次数", str(stats.get('total_executions', 0))),
                ("平均CPU使用率", f"{stats.get('avg_cpu_percent', 0):.2f}%"),
                ("平均内存使用", f"{stats.get('avg_memory_mb', 0):.2f} MB"),
                ("峰值CPU使用率", f"{stats.get('peak_cpu_percent', 0):.2f}%"),
                ("峰值内存使用", f"{stats.get('peak_memory_mb', 0):.2f} MB")
            ]
            
            for label, value in stats_items:
                row = self.stats_table.rowCount()
                self.stats_table.insertRow(row)
                self.stats_table.setItem(row, 0, QTableWidgetItem(label))
                self.stats_table.setItem(row, 1, QTableWidgetItem(value))
        
        except Exception as e:
            self.logger.error(f"Error refreshing statistics: {e}")
    
    def _set_progress_color(self, progress_bar: QProgressBar, value: float):
        """设置进度条颜色
        
        Args:
            progress_bar: 进度条控件
            value: 当前值
        """
        if value < 60:
            color = "green"
        elif value < 80:
            color = "orange"
        else:
            color = "red"
        
        progress_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
            }}
        """)
    
    def closeEvent(self, event):
        """关闭事件"""
        self._update_timer.stop()
        super().closeEvent(event)