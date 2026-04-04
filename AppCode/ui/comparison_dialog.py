"""结果对比对话框

对比两次执行结果的差异。
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QHeaderView
)
from PyQt5.QtCore import Qt


class ComparisonDialog(QDialog):
    """执行结果对比对话框"""

    def __init__(self, result1: dict, result2: dict, parent=None):
        """初始化对比对话框

        Args:
            result1: 第一条执行结果
            result2: 第二条执行结果
            parent: 父窗口
        """
        super().__init__(parent)
        self.result1 = result1
        self.result2 = result2
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("执行结果对比")
        self.setMinimumSize(700, 550)

        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("两次执行结果对比")
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title)

        # 对比表格
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(3)
        self.comparison_table.setHorizontalHeaderLabels(["对比项", "执行 1", "执行 2"])
        self.comparison_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.comparison_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.comparison_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.comparison_table.setColumnWidth(0, 150)
        layout.addWidget(self.comparison_table)

        self._populate_table()

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _populate_table(self):
        """填充对比数据"""
        r1, r2 = self.result1, self.result2

        # 长文本字段：截断显示，tooltip 显示完整内容
        long_text_fields = {'output', 'error', 'execution_params'}
        truncate_len = 200

        fields = [
            ("脚本路径", 'script_path'),
            ("测试方案", 'suite_name'),
            ("状态", 'status'),
            ("测试结果", 'test_result'),
            ("开始时间", 'start_time'),
            ("结束时间", 'end_time'),
            ("耗时(秒)", 'duration'),
            ("执行参数", 'execution_params'),
            ("标准输出", 'output'),
            ("错误输出", 'error'),
            ("错误信息", 'error_message'),
        ]

        self.comparison_table.setRowCount(len(fields))

        for row, (label, key) in enumerate(fields):
            # 标签
            label_item = QTableWidgetItem(label)
            label_item.setFlags(label_item.flags() & ~Qt.ItemIsEditable)
            label_item.setBackground(Qt.lightGray)
            self.comparison_table.setItem(row, 0, label_item)

            # 值
            val1 = str(r1.get(key, ''))
            val2 = str(r2.get(key, ''))

            # 长文本截断显示
            if key in long_text_fields:
                display1 = val1[:truncate_len] + ('...' if len(val1) > truncate_len else '')
                display2 = val2[:truncate_len] + ('...' if len(val2) > truncate_len else '')
            else:
                display1, display2 = val1, val2

            item1 = QTableWidgetItem(display1)
            item2 = QTableWidgetItem(display2)
            item1.setFlags(item1.flags() & ~Qt.ItemIsEditable)
            item2.setFlags(item2.flags() & ~Qt.ItemIsEditable)

            # 长文本设置 tooltip
            if key in long_text_fields:
                item1.setToolTip(val1)
                item2.setToolTip(val2)

            # 差异高亮
            if val1 != val2:
                item1.setBackground(Qt.yellow)
                item2.setBackground(Qt.yellow)

            self.comparison_table.setItem(row, 1, item1)
            self.comparison_table.setItem(row, 2, item2)
