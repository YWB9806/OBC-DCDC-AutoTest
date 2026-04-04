"""脚本选择对话框

用户添加文件夹时，弹出对话框让用户勾选要添加的脚本
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QPushButton, QLabel, QLineEdit,
    QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
import os


class ScriptSelectionDialog(QDialog):
    """脚本选择对话框"""
    
    def __init__(self, scripts, source_path, parent=None):
        """初始化对话框
        
        Args:
            scripts: 脚本列表（字典列表）
            source_path: 源路径（文件夹路径）
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.scripts = scripts
        self.source_path = source_path
        self.selected_scripts = []
        
        self._init_ui()
        self._load_scripts()
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("选择要添加的脚本")
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(f"从以下路径找到 {len(self.scripts)} 个脚本:")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title_label)
        
        path_label = QLabel(self.source_path)
        path_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(path_label)
        
        # 搜索栏
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词过滤脚本...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        
        # 脚本树
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["脚本名称", "相对路径", "大小"])
        self.tree_widget.setColumnWidth(0, 300)
        self.tree_widget.setColumnWidth(1, 250)
        self.tree_widget.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.tree_widget)
        
        # 统计信息
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)
        
        # 快捷按钮
        quick_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self._on_select_all)
        quick_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("全不选")
        self.deselect_all_btn.clicked.connect(self._on_deselect_all)
        quick_layout.addWidget(self.deselect_all_btn)
        
        self.invert_btn = QPushButton("反选")
        self.invert_btn.clicked.connect(self._on_invert)
        quick_layout.addWidget(self.invert_btn)
        
        quick_layout.addStretch()
        layout.addLayout(quick_layout)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("确定添加")
        self.ok_btn.clicked.connect(self._on_ok)
        self.ok_btn.setDefault(True)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
    
    def _load_scripts(self):
        """加载脚本到树形控件（优化版）"""
        # 暂时断开信号，避免在批量添加时触发多次更新
        self.tree_widget.itemChanged.disconnect(self._on_item_changed)
        self.tree_widget.setUpdatesEnabled(False)
        
        try:
            self.tree_widget.clear()
            
            # 按文件夹分组
            folder_items = {}
            
            for script in self.scripts:
                script_path = script['path']
                script_name = script['name']
                
                # 计算相对路径
                try:
                    rel_path = os.path.relpath(script_path, self.source_path)
                    folder = os.path.dirname(rel_path)
                except Exception:
                    rel_path = script_path
                    folder = ""

                # 获取文件大小
                try:
                    size = os.path.getsize(script_path)
                    size_str = self._format_size(size)
                except Exception:
                    size_str = "N/A"
                
                # 创建或获取文件夹节点
                if folder and folder != ".":
                    if folder not in folder_items:
                        folder_item = QTreeWidgetItem(self.tree_widget)
                        folder_item.setText(0, f"📁 {folder}")
                        folder_item.setFlags(folder_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsTristate)
                        folder_item.setCheckState(0, Qt.Unchecked)
                        folder_item.setExpanded(False)  # 默认折叠，提高性能
                        folder_items[folder] = folder_item
                    
                    parent_item = folder_items[folder]
                else:
                    parent_item = self.tree_widget
                
                # 创建脚本节点
                script_item = QTreeWidgetItem(parent_item)
                script_item.setText(0, f"📄 {script_name}")
                script_item.setText(1, rel_path)
                script_item.setText(2, size_str)
                script_item.setData(0, Qt.UserRole, script)
                script_item.setFlags(script_item.flags() | Qt.ItemIsUserCheckable)
                script_item.setCheckState(0, Qt.Checked)  # 默认全选
            
            self._update_stats()
        
        finally:
            # 恢复UI更新和信号连接
            self.tree_widget.setUpdatesEnabled(True)
            self.tree_widget.itemChanged.connect(self._on_item_changed)
    
    def _format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def _on_search(self):
        """搜索过滤"""
        keyword = self.search_input.text().strip().lower()
        
        def filter_recursive(item):
            """递归过滤"""
            visible = False
            
            for i in range(item.childCount()):
                child = item.child(i)
                script = child.data(0, Qt.UserRole)
                
                if script:
                    # 脚本节点
                    name = script['name'].lower()
                    path = script['path'].lower()
                    match = not keyword or keyword in name or keyword in path
                    child.setHidden(not match)
                    if match:
                        visible = True
                else:
                    # 文件夹节点
                    child_visible = filter_recursive(child)
                    child.setHidden(not child_visible)
                    if child_visible:
                        visible = True
            
            return visible
        
        # 从根节点开始过滤
        root = self.tree_widget.invisibleRootItem()
        filter_recursive(root)
        
        self._update_stats()
    
    def _on_item_changed(self, item, column):
        """复选框状态改变"""
        if column == 0:
            self._update_stats()
    
    def _update_stats(self):
        """更新统计信息"""
        total = 0
        selected = 0
        
        def count_recursive(item):
            nonlocal total, selected
            for i in range(item.childCount()):
                child = item.child(i)
                script = child.data(0, Qt.UserRole)
                
                if script and not child.isHidden():
                    total += 1
                    if child.checkState(0) == Qt.Checked:
                        selected += 1
                
                count_recursive(child)
        
        root = self.tree_widget.invisibleRootItem()
        count_recursive(root)
        
        self.stats_label.setText(f"已选择: {selected} / {total} 个脚本")
    
    def _on_select_all(self):
        """全选（优化版）"""
        # 暂时断开信号，避免每次状态改变都触发更新
        self.tree_widget.itemChanged.disconnect(self._on_item_changed)
        self.tree_widget.setUpdatesEnabled(False)
        
        try:
            self._set_all_check_state(Qt.Checked)
        finally:
            self.tree_widget.setUpdatesEnabled(True)
            self.tree_widget.itemChanged.connect(self._on_item_changed)
            self._update_stats()
    
    def _on_deselect_all(self):
        """全不选（优化版）"""
        # 暂时断开信号，避免每次状态改变都触发更新
        self.tree_widget.itemChanged.disconnect(self._on_item_changed)
        self.tree_widget.setUpdatesEnabled(False)
        
        try:
            self._set_all_check_state(Qt.Unchecked)
        finally:
            self.tree_widget.setUpdatesEnabled(True)
            self.tree_widget.itemChanged.connect(self._on_item_changed)
            self._update_stats()
    
    def _on_invert(self):
        """反选（优化版）"""
        # 暂时断开信号，避免每次状态改变都触发更新
        self.tree_widget.itemChanged.disconnect(self._on_item_changed)
        self.tree_widget.setUpdatesEnabled(False)
        
        try:
            def invert_recursive(item):
                for i in range(item.childCount()):
                    child = item.child(i)
                    script = child.data(0, Qt.UserRole)
                    
                    if script and not child.isHidden():
                        current = child.checkState(0)
                        new_state = Qt.Unchecked if current == Qt.Checked else Qt.Checked
                        child.setCheckState(0, new_state)
                    
                    invert_recursive(child)
            
            root = self.tree_widget.invisibleRootItem()
            invert_recursive(root)
        
        finally:
            self.tree_widget.setUpdatesEnabled(True)
            self.tree_widget.itemChanged.connect(self._on_item_changed)
            self._update_stats()
    
    def _set_all_check_state(self, state):
        """设置所有可见脚本的复选框状态"""
        def set_recursive(item):
            for i in range(item.childCount()):
                child = item.child(i)
                script = child.data(0, Qt.UserRole)
                
                if script and not child.isHidden():
                    child.setCheckState(0, state)
                
                set_recursive(child)
        
        root = self.tree_widget.invisibleRootItem()
        set_recursive(root)
    
    def _on_ok(self):
        """确定按钮"""
        # 收集选中的脚本
        self.selected_scripts = []
        
        def collect_recursive(item):
            for i in range(item.childCount()):
                child = item.child(i)
                script = child.data(0, Qt.UserRole)
                
                if script and child.checkState(0) == Qt.Checked:
                    self.selected_scripts.append(script)
                
                collect_recursive(child)
        
        root = self.tree_widget.invisibleRootItem()
        collect_recursive(root)
        
        if not self.selected_scripts:
            QMessageBox.warning(self, "警告", "请至少选择一个脚本")
            return
        
        self.accept()
    
    def get_selected_scripts(self):
        """获取选中的脚本列表
        
        Returns:
            选中的脚本信息列表
        """
        return self.selected_scripts