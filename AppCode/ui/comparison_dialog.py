"""结果对比对话框

对比两次执行结果的差异。
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QHeaderView,
    QTextEdit, QSplitter, QWidget
)
from PyQt5.QtCore import Qt


class ComparisonDialog(QDialog):
    """执行结果对比对话框"""

    def __init__(self, result1: dict, result2: dict, parent=None):
        super().__init__(parent)
        self.result1 = result1
        self.result2 = result2
        self._field_keys = {}
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("执行结果对比")
        self.setMinimumSize(900, 650)

        layout = QVBoxLayout(self)

        title = QLabel("两次执行结果对比 — 点击表格行查看完整内容")
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title)

        splitter = QSplitter(Qt.Vertical)

        # 上半部分：对比表格
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(3)
        self.comparison_table.setHorizontalHeaderLabels(["对比项", "执行 1", "执行 2"])
        self.comparison_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.comparison_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.comparison_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.comparison_table.setColumnWidth(0, 150)
        self.comparison_table.cellClicked.connect(self._on_cell_clicked)
        splitter.addWidget(self.comparison_table)

        self._populate_table()

        # 下半部分：详情展示（左右分栏）
        bottom_splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.addWidget(QLabel("执行 1 完整内容:"))
        self.detail1_text = QTextEdit()
        self.detail1_text.setReadOnly(True)
        self.detail1_text.setPlaceholderText("点击上方表格行查看完整内容")
        left_layout.addWidget(self.detail1_text)
        bottom_splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.addWidget(QLabel("执行 2 完整内容:"))
        self.detail2_text = QTextEdit()
        self.detail2_text.setReadOnly(True)
        self.detail2_text.setPlaceholderText("点击上方表格行查看完整内容")
        right_layout.addWidget(self.detail2_text)
        bottom_splitter.addWidget(right_widget)

        splitter.addWidget(bottom_splitter)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _populate_table(self):
        r1, r2 = self.result1, self.result2

        fields = [
            ("脚本路径", 'script_path'),
            ("测试方案", 'suite_name'),
            ("状态", 'status'),
            ("测试结果", 'test_result'),
            ("开始时间", 'start_time'),
            ("结束时间", 'end_time'),
            ("耗时(秒)", 'duration'),
            ("标准输出", 'output'),
            ("错误输出", 'error'),
        ]

        self.comparison_table.setRowCount(len(fields))

        for row, (label, key) in enumerate(fields):
            self._field_keys[row] = key

            label_item = QTableWidgetItem(label)
            label_item.setFlags(label_item.flags() & ~Qt.ItemIsEditable)
            label_item.setBackground(Qt.lightGray)
            self.comparison_table.setItem(row, 0, label_item)

            val1 = str(r1.get(key, ''))
            val2 = str(r2.get(key, ''))

            display1 = val1 if len(val1) <= 60 else val1[:60] + '... (点击查看完整)'
            display2 = val2 if len(val2) <= 60 else val2[:60] + '... (点击查看完整)'

            item1 = QTableWidgetItem(display1)
            item2 = QTableWidgetItem(display2)
            item1.setFlags(item1.flags() & ~Qt.ItemIsEditable)
            item2.setFlags(item2.flags() & ~Qt.ItemIsEditable)

            item1.setToolTip(val1[:500] + ('...' if len(val1) > 500 else ''))
            item2.setToolTip(val2[:500] + ('...' if len(val2) > 500 else ''))

            if val1 != val2:
                item1.setBackground(Qt.yellow)
                item2.setBackground(Qt.yellow)

            self.comparison_table.setItem(row, 1, item1)
            self.comparison_table.setItem(row, 2, item2)

    def _on_cell_clicked(self, row, col):
        key = self._field_keys.get(row)
        if key is None:
            return

        val1 = str(self.result1.get(key, ''))
        val2 = str(self.result2.get(key, ''))

        self.detail1_text.setPlainText(val1)
        self.detail2_text.setPlainText(val2)
