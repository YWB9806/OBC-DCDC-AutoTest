"""执行队列面板

显示待执行的脚本列表，支持排序、删除等操作
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QMessageBox,
    QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon


class ExecutionQueuePanel(QWidget):
    """执行队列面板"""
    
    # 信号定义
    queue_changed = pyqtSignal(list)  # 队列改变时发出
    execute_requested = pyqtSignal(list)  # 请求执行
    
    def __init__(self, parent=None):
        """初始化执行队列面板"""
        super().__init__(parent)
        
        self._queue = []  # 执行队列（脚本路径列表）
        self._script_info_map = {}  # 脚本路径 -> 脚本信息映射
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_layout = QHBoxLayout()
        title_label = QLabel("执行队列")
        title_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        title_layout.addWidget(title_label)
        
        self.count_label = QLabel("(0)")
        self.count_label.setStyleSheet("color: #666;")
        title_layout.addWidget(self.count_label)
        
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 列表控件
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget)
        
        # 按钮栏
        button_layout = QHBoxLayout()
        
        self.move_up_btn = QPushButton("↑ 上移")
        self.move_up_btn.clicked.connect(self._on_move_up)
        button_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("↓ 下移")
        self.move_down_btn.clicked.connect(self._on_move_down)
        button_layout.addWidget(self.move_down_btn)
        
        self.remove_btn = QPushButton("移除")
        self.remove_btn.clicked.connect(self._on_remove)
        button_layout.addWidget(self.remove_btn)
        
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self._on_clear)
        button_layout.addWidget(self.clear_btn)
        
        layout.addLayout(button_layout)
        
        # 执行按钮
        execute_layout = QHBoxLayout()
        execute_layout.addStretch()
        
        self.execute_btn = QPushButton("开始执行")
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.execute_btn.clicked.connect(self._on_execute)
        self.execute_btn.setEnabled(False)
        execute_layout.addWidget(self.execute_btn)
        
        execute_layout.addStretch()
        layout.addLayout(execute_layout)
    
    def add_scripts(self, script_paths, script_info_list):
        """添加脚本到队列（优化版 - 批量操作）
        
        Args:
            script_paths: 脚本路径列表
            script_info_list: 脚本信息列表
        """
        added_count = 0
        
        # 批量添加，减少中间状态更新
        for path, info in zip(script_paths, script_info_list):
            if path not in self._queue:
                self._queue.append(path)
                self._script_info_map[path] = info
                added_count += 1
        
        if added_count > 0:
            # 只在最后更新一次UI
            self._update_list()
            self.queue_changed.emit(self._queue)
            
            # 只在添加数量较少时弹出消息框，避免频繁打断用户
            if added_count <= 10:
                QMessageBox.information(
                    self, "成功",
                    f"已添加 {added_count} 个脚本到执行队列"
                )
            else:
                # 大量脚本时使用状态栏提示（需要主窗口支持）
                from PyQt5.QtWidgets import QApplication
                main_window = QApplication.activeWindow()
                if main_window and hasattr(main_window, 'statusBar'):
                    main_window.statusBar().showMessage(
                        f"已添加 {added_count} 个脚本到执行队列", 3000
                    )
    
    def remove_scripts(self, script_paths):
        """从队列中移除脚本
        
        Args:
            script_paths: 要移除的脚本路径列表
        """
        removed_count = 0
        
        for path in script_paths:
            if path in self._queue:
                self._queue.remove(path)
                if path in self._script_info_map:
                    del self._script_info_map[path]
                removed_count += 1
        
        if removed_count > 0:
            self._update_list()
            self.queue_changed.emit(self._queue)
    
    def clear_queue(self):
        """清空队列"""
        self._queue.clear()
        self._script_info_map.clear()
        self._update_list()
        self.queue_changed.emit(self._queue)
    
    def get_queue(self):
        """获取当前队列
        
        Returns:
            脚本路径列表
        """
        return self._queue.copy()
    
    def _update_list(self):
        """更新列表显示（优化版 - 减少重绘）"""
        # 暂停UI更新，批量操作完成后再刷新
        self.list_widget.setUpdatesEnabled(False)
        
        try:
            self.list_widget.clear()
            
            # 批量添加项目
            for i, path in enumerate(self._queue):
                info = self._script_info_map.get(path, {})
                name = info.get('name', path)
                
                item = QListWidgetItem(f"{i+1}. {name}")
                item.setData(Qt.UserRole, path)
                item.setToolTip(path)
                self.list_widget.addItem(item)
            
            # 更新计数
            self.count_label.setText(f"({len(self._queue)})")
            
            # 更新执行按钮状态
            self.execute_btn.setEnabled(len(self._queue) > 0)
        
        finally:
            # 恢复UI更新
            self.list_widget.setUpdatesEnabled(True)
    
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        
        menu = QMenu(self)
        
        move_up_action = QAction("上移", self)
        move_up_action.triggered.connect(self._on_move_up)
        menu.addAction(move_up_action)
        
        move_down_action = QAction("下移", self)
        move_down_action.triggered.connect(self._on_move_down)
        menu.addAction(move_down_action)
        
        menu.addSeparator()
        
        remove_action = QAction("移除", self)
        remove_action.triggered.connect(self._on_remove)
        menu.addAction(remove_action)
        
        menu.exec_(self.list_widget.mapToGlobal(pos))
    
    def _on_item_double_clicked(self, item):
        """双击项目 - 显示详情"""
        path = item.data(Qt.UserRole)
        info = self._script_info_map.get(path, {})
        
        details = f"脚本名称: {info.get('name', 'N/A')}\n"
        details += f"路径: {path}\n"
        details += f"分类: {info.get('category', 'N/A')}\n"
        
        QMessageBox.information(self, "脚本详情", details)
    
    def _on_move_up(self):
        """上移选中项"""
        current_row = self.list_widget.currentRow()
        if current_row <= 0:
            return
        
        # 交换队列中的位置
        self._queue[current_row], self._queue[current_row - 1] = \
            self._queue[current_row - 1], self._queue[current_row]
        
        self._update_list()
        self.list_widget.setCurrentRow(current_row - 1)
        self.queue_changed.emit(self._queue)
    
    def _on_move_down(self):
        """下移选中项"""
        current_row = self.list_widget.currentRow()
        if current_row < 0 or current_row >= len(self._queue) - 1:
            return
        
        # 交换队列中的位置
        self._queue[current_row], self._queue[current_row + 1] = \
            self._queue[current_row + 1], self._queue[current_row]
        
        self._update_list()
        self.list_widget.setCurrentRow(current_row + 1)
        self.queue_changed.emit(self._queue)
    
    def _on_remove(self):
        """移除选中项"""
        current_row = self.list_widget.currentRow()
        if current_row < 0:
            return
        
        path = self._queue[current_row]
        self._queue.pop(current_row)
        
        if path in self._script_info_map:
            del self._script_info_map[path]
        
        self._update_list()
        self.queue_changed.emit(self._queue)
    
    def _on_clear(self):
        """清空队列"""
        if not self._queue:
            return
        
        reply = QMessageBox.question(
            self, "确认",
            f"确定要清空执行队列吗？\n当前有 {len(self._queue)} 个脚本",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.clear_queue()
    
    def _on_execute(self):
        """执行队列中的脚本"""
        if not self._queue:
            return
        
        self.execute_requested.emit(self._queue.copy())