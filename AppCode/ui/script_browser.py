"""脚本浏览器

用于浏览和选择脚本的树形控件。
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QLineEdit, QPushButton, QLabel,
    QCheckBox, QComboBox, QMessageBox, QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
import os

from .test_suite_dialog import SaveSuiteDialog, ManageSuitesDialog


class ScriptBrowser(QWidget):
    """脚本浏览器组件"""
    
    # 信号定义
    script_selected = pyqtSignal(str)  # 单个脚本被选中
    scripts_selected = pyqtSignal(list)  # 多个脚本被选中
    add_to_queue_requested = pyqtSignal(list, list)  # 请求添加到执行队列 (paths, info_list)
    
    def __init__(self, container, parent=None):
        """初始化脚本浏览器
        
        Args:
            container: 依赖注入容器
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.container = container
        self.logger = container.resolve('log_manager').get_logger('ui')
        self.script_service = container.resolve('script_service')
        self.config_manager = container.resolve('config_manager')
        self.suite_service = container.resolve('test_suite_service')
        
        self._scripts = []
        self._filtered_scripts = []
        self._current_suite = None  # 当前加载的方案
        self._root_path = None  # 脚本根目录
        
        # 保持线程引用，防止被垃圾回收导致崩溃
        self._scan_thread = None
        
        self._init_ui()
        self._load_scripts()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 搜索栏
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索脚本...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        
        self.search_btn = QPushButton("搜索")
        self.search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(self.search_btn)
        
        layout.addLayout(search_layout)
        
        # 方案操作栏（一行显示：测试方案 + 选择方案 + 一键折叠 + 一键展开）
        suite_layout = QHBoxLayout()
        suite_layout.addWidget(QLabel("测试方案:"))

        self.suite_combo = QComboBox()
        self.suite_combo.addItem("-- 未选择方案 --")
        self.suite_combo.currentIndexChanged.connect(self._on_suite_changed)
        suite_layout.addWidget(self.suite_combo)

        suite_layout.addStretch()

        self.collapse_all_btn = QPushButton("一键折叠")
        self.collapse_all_btn.clicked.connect(self._on_collapse_all)
        suite_layout.addWidget(self.collapse_all_btn)

        self.expand_all_btn = QPushButton("一键展开")
        self.expand_all_btn.clicked.connect(self._on_expand_all)
        suite_layout.addWidget(self.expand_all_btn)

        layout.addLayout(suite_layout)
        
        # 脚本树
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["脚本名称", "路径", "状态"])
        self.tree_widget.setColumnWidth(0, 250)
        self.tree_widget.setColumnWidth(1, 350)
        # 不使用ExtendedSelection，改用复选框模式
        self.tree_widget.itemChanged.connect(self._on_item_checked)
        self.tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.tree_widget)

        # 列显示状态（默认隐藏路径和状态列）
        self._column_visibility = {
            0: True,   # 脚本名称 - 始终显示
            1: False,  # 路径 - 默认隐藏
            2: False   # 状态 - 默认隐藏
        }
        self._apply_column_visibility()
        
        # 统计信息
        self.stats_label = QLabel("总计: 0 个脚本")
        layout.addWidget(self.stats_label)
        
        # 按钮栏
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh)
        button_layout.addWidget(self.refresh_btn)
        
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self._on_select_all)
        button_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("全不选")
        self.deselect_all_btn.clicked.connect(self._on_deselect_all)
        button_layout.addWidget(self.deselect_all_btn)
        
        self.invert_selection_btn = QPushButton("反选")
        self.invert_selection_btn.clicked.connect(self._on_invert_selection)
        button_layout.addWidget(self.invert_selection_btn)
        
        button_layout.addStretch()
        
        # "添加路径"按钮已移到上方过滤器布局中
        
        self.add_to_queue_btn = QPushButton("添加到执行列表 →")
        self.add_to_queue_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.add_to_queue_btn.clicked.connect(self._on_add_to_queue)
        button_layout.addWidget(self.add_to_queue_btn)

        layout.addLayout(button_layout)
        
        # 自定义路径列表
        self._custom_paths = []  # 存储用户添加的自定义路径
    
    def _load_scripts(self):
        """加载脚本列表"""
        try:
            # 不再自动加载TestScripts目录
            # 用户需要手动添加路径
            self._root_path = None
            
            all_scripts = []
            
            # 只加载自定义路径的脚本
            for custom_path in self._custom_paths:
                if os.path.isfile(custom_path):
                    # 单个文件
                    try:
                        script_info = self.script_service.script_manager.get_script_info(custom_path)
                        all_scripts.append(script_info)
                    except Exception as e:
                        self.logger.warning(f"Failed to load custom script {custom_path}: {e}")
                elif os.path.isdir(custom_path):
                    # 文件夹
                    result = self.script_service.scan_and_load_scripts(custom_path)
                    if result['success']:
                        all_scripts.extend(result['scripts'])
            
            self._scripts = all_scripts
            self._filtered_scripts = self._scripts.copy()

            # 批量更新UI（禁用更新直到完成）
            self.tree_widget.setUpdatesEnabled(False)
            try:
                # 更新树形控件
                self._update_tree()
                
                # 更新统计信息
                self._update_stats()
            finally:
                self.tree_widget.setUpdatesEnabled(True)
            
            # 加载方案列表
            self._load_suites()
            
            self.logger.info(f"Loaded {len(self._scripts)} scripts (including {len(self._custom_paths)} custom paths)")
        
        except Exception as e:
            self.logger.error(f"Error loading scripts: {e}")
            QMessageBox.critical(self, "错误", f"加载脚本时出错: {e}")
    
    def _update_tree(self):
        """更新树形控件 - 构建完整的层级目录结构（优化版）"""
        # 暂时断开信号，避免在批量更新时触发
        self.tree_widget.itemChanged.disconnect(self._on_item_checked)
        
        # 禁用UI更新，批量操作完成后再刷新
        self.tree_widget.setUpdatesEnabled(False)
        
        try:
            self.tree_widget.clear()
            
            # 如果没有脚本，直接返回
            if not self._filtered_scripts:
                return
            
            # 找到所有自定义路径的公共根目录
            base_paths = {}  # {base_path: scripts}
            for custom_path in self._custom_paths:
                if os.path.isdir(custom_path):
                    base_paths[custom_path] = []
            
            # 将脚本分配到对应的基础路径
            for script in self._filtered_scripts:
                script_path = script['path']
                # 找到脚本所属的基础路径
                for base_path in base_paths:
                    if script_path.startswith(base_path):
                        base_paths[base_path].append(script)
                        break
            
            # 为每个基础路径构建目录树
            for base_path, scripts in base_paths.items():
                if not scripts:
                    continue
                
                # 构建该基础路径下的目录树
                root_nodes = {}  # 存储所有目录节点 {relative_path: tree_item}
                
                for script in scripts:
                    script_path = script['path']
                    
                    # 获取相对于基础路径的相对路径
                    try:
                        rel_path = os.path.relpath(script_path, base_path)
                    except ValueError:
                        # 如果无法计算相对路径，使用绝对路径
                        rel_path = script_path
                    
                    # 获取脚本的目录部分
                    dir_path = os.path.dirname(rel_path)
                    
                    # 如果脚本就在基础路径下（没有子目录）
                    if not dir_path or dir_path == '.':
                        # 直接在根节点下创建脚本
                        base_name = os.path.basename(base_path)
                        if base_path not in root_nodes:
                            base_item = QTreeWidgetItem(self.tree_widget)
                            base_item.setText(0, f"📁 {base_name}")
                            base_item.setText(1, base_path)
                            base_item.setExpanded(False)  # 默认折叠，提高性能
                            base_item.setFlags(base_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsTristate)
                            base_item.setCheckState(0, Qt.Unchecked)
                            root_nodes[base_path] = base_item
                        
                        parent_item = root_nodes[base_path]
                    else:
                        # 分割相对路径为各级目录
                        path_parts = dir_path.split(os.sep)
                        
                        # 递归创建目录节点
                        parent_item = None
                        current_rel_path = ""
                        
                        # 首先创建基础路径节点
                        base_name = os.path.basename(base_path)
                        if base_path not in root_nodes:
                            base_item = QTreeWidgetItem(self.tree_widget)
                            base_item.setText(0, f"📁 {base_name}")
                            base_item.setText(1, base_path)
                            base_item.setExpanded(False)  # 默认折叠，提高性能
                            base_item.setFlags(base_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsTristate)
                            base_item.setCheckState(0, Qt.Unchecked)
                            root_nodes[base_path] = base_item
                        
                        parent_item = root_nodes[base_path]
                        
                        # 然后创建子目录节点
                        for dir_name in path_parts:
                            if not dir_name or dir_name == '.':
                                continue
                            
                            if current_rel_path:
                                current_rel_path = os.path.join(current_rel_path, dir_name)
                            else:
                                current_rel_path = dir_name
                            
                            full_path = os.path.join(base_path, current_rel_path)
                            
                            # 检查该路径的节点是否已创建
                            if full_path in root_nodes:
                                parent_item = root_nodes[full_path]
                            else:
                                # 创建新的目录节点
                                folder_item = QTreeWidgetItem(parent_item)
                                folder_item.setText(0, f"📁 {dir_name}")
                                folder_item.setText(1, full_path)
                                folder_item.setExpanded(False)  # 默认折叠，提高性能
                                
                                # 文件夹节点添加复选框（三态）
                                folder_item.setFlags(folder_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsTristate)
                                folder_item.setCheckState(0, Qt.Unchecked)
                                
                                # 缓存节点
                                root_nodes[full_path] = folder_item
                                parent_item = folder_item
                    
                    # 在最后一级目录下添加脚本节点
                    if parent_item is not None:
                        script_item = QTreeWidgetItem(parent_item)
                        script_item.setText(0, f"📄 {script['name']}")
                        script_item.setText(1, script['path'])
                        script_item.setText(2, script.get('status', 'idle'))
                        script_item.setData(0, Qt.UserRole, script)
                        
                        # 脚本节点添加复选框
                        script_item.setFlags(script_item.flags() | Qt.ItemIsUserCheckable)
                        script_item.setCheckState(0, Qt.Unchecked)
            
            # 更新所有文件夹节点的脚本计数
            self._update_folder_counts(self.tree_widget.invisibleRootItem())
        
        finally:
            # 恢复UI更新
            self.tree_widget.setUpdatesEnabled(True)
            
            # 重新连接信号
            self.tree_widget.itemChanged.connect(self._on_item_checked)
    
    def _update_folder_counts(self, parent_item):
        """递归更新文件夹节点的脚本计数
        
        Args:
            parent_item: 父节点
        """
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            
            # 如果是文件夹节点（有子节点）
            if child.childCount() > 0:
                # 递归更新子文件夹
                self._update_folder_counts(child)
                
                # 统计该文件夹下的脚本数量
                script_count = self._count_scripts_in_item(child)
                
                # 更新文件夹显示名称
                folder_name = child.text(0)
                if "📁" in folder_name:
                    # 移除旧的计数
                    base_name = folder_name.split("(")[0].strip()
                    child.setText(0, f"{base_name} ({script_count})")
    
    def _count_scripts_in_item(self, item):
        """递归统计节点下的脚本数量
        
        Args:
            item: 树节点
            
        Returns:
            脚本数量
        """
        count = 0
        for i in range(item.childCount()):
            child = item.child(i)
            script = child.data(0, Qt.UserRole)
            
            if script:
                # 是脚本节点
                count += 1
            else:
                # 是文件夹节点，递归统计
                count += self._count_scripts_in_item(child)
        
        return count
    
    def _build_tree_recursive(self, node_data, parent_item):
        """递归构建树形结构
        
        Args:
            node_data: 节点数据（字典）
            parent_item: 父节点（QTreeWidget或QTreeWidgetItem）
        """
        if node_data.get('type') == 'directory':
            # 创建文件夹节点
            if isinstance(parent_item, QTreeWidget):
                folder_item = QTreeWidgetItem(parent_item)
            else:
                folder_item = QTreeWidgetItem(parent_item)
            
            folder_name = node_data.get('name', '')
            children = node_data.get('children', [])
            
            # 统计子节点中的脚本数量
            script_count = self._count_scripts_in_node(node_data)
            
            folder_item.setText(0, f"📁 {folder_name} ({script_count})")
            folder_item.setText(1, node_data.get('path', ''))
            folder_item.setExpanded(True)
            
            # 文件夹节点添加复选框（三态）
            folder_item.setFlags(folder_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsTristate)
            folder_item.setCheckState(0, Qt.Unchecked)
            
            # 递归处理子节点
            for child in children:
                self._build_tree_recursive(child, folder_item)
        
        elif node_data.get('type') == 'file':
            # 创建脚本文件节点
            script_item = QTreeWidgetItem(parent_item)
            script_path = node_data.get('path', '')
            script_name = node_data.get('name', '')
            
            # 从缓存中获取脚本详细信息
            script_info = self._get_script_info_by_path(script_path)
            
            script_item.setText(0, f"📄 {script_name}")
            script_item.setText(1, script_path)
            script_item.setText(2, script_info.get('status', 'idle') if script_info else 'idle')
            script_item.setData(0, Qt.UserRole, script_info)
            
            # 脚本节点添加复选框
            script_item.setFlags(script_item.flags() | Qt.ItemIsUserCheckable)
            script_item.setCheckState(0, Qt.Unchecked)
    
    def _count_scripts_in_node(self, node_data):
        """统计节点中的脚本数量
        
        Args:
            node_data: 节点数据
            
        Returns:
            脚本数量
        """
        count = 0
        if node_data.get('type') == 'file':
            return 1
        
        for child in node_data.get('children', []):
            count += self._count_scripts_in_node(child)
        
        return count
    
    def _get_script_info_by_path(self, script_path):
        """根据路径获取脚本信息
        
        Args:
            script_path: 脚本路径
            
        Returns:
            脚本信息字典或None
        """
        for script in self._scripts:
            if script.get('path') == script_path:
                return script
        return None
    
    def _update_stats(self):
        """更新统计信息"""
        total = len(self._filtered_scripts)
        self.stats_label.setText(f"总计: {total} 个脚本")
    
    def _on_search(self):
        """搜索脚本"""
        keyword = self.search_input.text().strip()
        
        if not keyword:
            self._filtered_scripts = self._scripts.copy()
        else:
            self._filtered_scripts = self.script_service.search_scripts(keyword)
        
        self._update_tree()
        self._update_stats()
    
    def _on_collapse_all(self):
        """一键折叠所有节点"""
        self.tree_widget.collapseAll()
    
    def _on_expand_all(self):
        """一键展开所有节点"""
        self.tree_widget.expandAll()
    
    def _show_column_settings(self):
        """显示列设置菜单"""
        menu = QMenu(self)
        
        # 路径列选项
        path_action = QAction("显示路径", self, checkable=True)
        path_action.setChecked(self._column_visibility[1])
        path_action.triggered.connect(lambda: self._toggle_column(1))
        menu.addAction(path_action)
        
        # 状态列选项
        status_action = QAction("显示状态", self, checkable=True)
        status_action.setChecked(self._column_visibility[2])
        status_action.triggered.connect(lambda: self._toggle_column(2))
        menu.addAction(status_action)
        
        # 在按钮下方显示菜单
        menu.exec_(self.column_settings_btn.mapToGlobal(
            self.column_settings_btn.rect().bottomLeft()
        ))
    
    def _toggle_column(self, column_index):
        """切换列的显示状态"""
        self._column_visibility[column_index] = not self._column_visibility[column_index]
        self._apply_column_visibility()
    
    def _apply_column_visibility(self):
        """应用列显示设置"""
        for col_index, visible in self._column_visibility.items():
            if col_index == 0:  # 脚本名称列始终显示
                continue
            if visible:
                self.tree_widget.showColumn(col_index)
            else:
                self.tree_widget.hideColumn(col_index)
    

    def _on_item_checked(self, item, column):
        """复选框状态改变"""
        if column != 0:
            return
        
        # 获取所有选中的脚本
        checked_scripts = self._get_checked_scripts()
        
        if len(checked_scripts) == 1:
            self.script_selected.emit(checked_scripts[0])
        elif len(checked_scripts) > 1:
            self.scripts_selected.emit(checked_scripts)
    
    def _get_checked_scripts(self):
        """获取所有选中的脚本路径（递归遍历树形结构）"""
        checked_paths = []
        seen_paths = set()  # 用于去重
        
        def collect_checked(item):
            """递归收集选中的脚本"""
            for i in range(item.childCount()):
                child = item.child(i)
                script = child.data(0, Qt.UserRole)
                
                # 如果是脚本节点且被选中
                if script and child.checkState(0) == Qt.Checked:
                    if script['path'] not in seen_paths:
                        checked_paths.append(script['path'])
                        seen_paths.add(script['path'])
                
                # 递归处理子节点
                collect_checked(child)
        
        # 从根节点开始收集
        root = self.tree_widget.invisibleRootItem()
        collect_checked(root)
        
        # 添加日志记录
        if self.logger:
            self.logger.info(f"Selected {len(checked_paths)} unique scripts")
        
        return checked_paths
    
    def _on_item_double_clicked(self, item, column):
        """项目双击"""
        script = item.data(0, Qt.UserRole)
        if script:
            # 可以在这里添加查看脚本详情的功能
            self.logger.info(f"Double clicked: {script['path']}")
    
    def _on_select_all(self):
        """全选（优化版）"""
        # 暂时断开信号，避免每次状态改变都触发
        self.tree_widget.itemChanged.disconnect(self._on_item_checked)
        self.tree_widget.setUpdatesEnabled(False)
        
        try:
            self._set_all_check_state(Qt.Checked)
        finally:
            self.tree_widget.setUpdatesEnabled(True)
            self.tree_widget.itemChanged.connect(self._on_item_checked)
    
    def _on_deselect_all(self):
        """全不选（优化版）"""
        # 暂时断开信号，避免每次状态改变都触发
        self.tree_widget.itemChanged.disconnect(self._on_item_checked)
        self.tree_widget.setUpdatesEnabled(False)
        
        try:
            self._set_all_check_state(Qt.Unchecked)
        finally:
            self.tree_widget.setUpdatesEnabled(True)
            self.tree_widget.itemChanged.connect(self._on_item_checked)
    
    def _on_invert_selection(self):
        """反选（递归处理 - 优化版）"""
        # 暂时断开信号，避免每次状态改变都触发
        self.tree_widget.itemChanged.disconnect(self._on_item_checked)
        self.tree_widget.setUpdatesEnabled(False)
        
        try:
            def invert_recursive(item):
                for i in range(item.childCount()):
                    child = item.child(i)
                    script = child.data(0, Qt.UserRole)
                    
                    # 只反转脚本节点
                    if script:
                        current_state = child.checkState(0)
                        new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
                        child.setCheckState(0, new_state)
                    
                    # 递归处理子节点
                    invert_recursive(child)
            
            root = self.tree_widget.invisibleRootItem()
            invert_recursive(root)
        
        finally:
            self.tree_widget.setUpdatesEnabled(True)
            self.tree_widget.itemChanged.connect(self._on_item_checked)
    
    def _set_all_check_state(self, state):
        """设置所有脚本的复选框状态（递归处理）"""
        def set_recursive(item):
            for i in range(item.childCount()):
                child = item.child(i)
                script = child.data(0, Qt.UserRole)
                
                # 只设置脚本节点
                if script:
                    child.setCheckState(0, state)
                
                # 递归处理子节点
                set_recursive(child)
        
        root = self.tree_widget.invisibleRootItem()
        set_recursive(root)
    
    def refresh(self):
        """刷新脚本列表"""
        self._load_scripts()
    
    def get_selected_scripts(self):
        """获取选中的脚本
        
        Returns:
            选中的脚本路径列表
        """
        return self._get_checked_scripts()
    
    def _load_suites(self):
        """加载方案列表"""
        try:
            suites = self.suite_service.list_suites()
            
            # 保存当前选择
            current_text = self.suite_combo.currentText()
            
            # 临时断开信号，避免在刷新时触发提示
            self.suite_combo.currentIndexChanged.disconnect(self._on_suite_changed)
            
            # 更新下拉框
            self.suite_combo.clear()
            self.suite_combo.addItem("-- 未选择方案 --")
            
            for suite in suites:
                self.suite_combo.addItem(suite['name'], suite['id'])
            
            # 恢复选择
            index = self.suite_combo.findText(current_text)
            if index >= 0:
                self.suite_combo.setCurrentIndex(index)
            
            # 重新连接信号
            self.suite_combo.currentIndexChanged.connect(self._on_suite_changed)
            
            self.logger.info(f"Loaded {len(suites)} test suites")
        
        except Exception as e:
            self.logger.error(f"Error loading suites: {e}")
            # 确保信号重新连接
            try:
                self.suite_combo.currentIndexChanged.disconnect(self._on_suite_changed)
            except Exception:
                pass
            self.suite_combo.currentIndexChanged.connect(self._on_suite_changed)
    
    def _on_suite_changed(self, index, show_message=True):
        """方案选择改变
        
        Args:
            index: 下拉框索引
            show_message: 是否显示提示消息
        """
        if index <= 0:
            self._current_suite = None
            return
        
        suite_id = self.suite_combo.currentData()
        if not suite_id:
            return
        
        try:
            # 加载方案
            suite = self.suite_service.get_suite(suite_id)
            if not suite:
                QMessageBox.warning(self, "警告", "方案不存在")
                return
            
            self._current_suite = suite
            
            # 获取方案中的脚本路径
            script_paths = suite.get('script_paths', [])
            if isinstance(script_paths, str):
                import json
                script_paths = json.loads(script_paths)
            
            # 【Bug修复】检查并自动加载缺失的脚本路径
            # 规范化路径以进行比较（统一使用小写和正斜杠）
            def normalize_path(p):
                """规范化路径用于比较"""
                return os.path.normpath(p).lower().replace('\\', '/')
            
            missing_scripts = []
            loaded_paths = {normalize_path(s['path']) for s in self._scripts}
            
            for path in script_paths:
                normalized_path = normalize_path(path)
                if normalized_path not in loaded_paths and os.path.exists(path):
                    missing_scripts.append(path)
            
            if missing_scripts:
                self.logger.info(f"Found {len(missing_scripts)} missing scripts, auto-loading their directories...")
                self._auto_load_missing_scripts(missing_scripts)
            
            # 取消所有选择
            self._set_all_check_state(Qt.Unchecked)
            
            # 选中方案中的脚本
            self._select_scripts_by_paths(script_paths)
            
            self.logger.info(f"Loaded suite: {suite['name']} with {len(script_paths)} scripts")
            
            # 只在需要时显示提示消息
            if show_message:
                QMessageBox.information(
                    self, "成功",
                    f"已加载方案 '{suite['name']}'\n包含 {len(script_paths)} 个脚本"
                )
        
        except Exception as e:
            self.logger.error(f"Error loading suite: {e}")
            QMessageBox.critical(self, "错误", f"加载方案失败: {e}")
    
    def _auto_load_missing_scripts(self, script_paths):
        """自动加载缺失的脚本（通过扫描其父目录）
        
        Args:
            script_paths: 缺失的脚本路径列表
        """
        try:
            # 收集需要扫描的目录（去重）
            dirs_to_scan = set()
            
            for path in script_paths:
                if not os.path.isfile(path):
                    continue
                
                # 获取脚本的直接父目录
                parent_dir = os.path.dirname(path)
                if not parent_dir or len(parent_dir) <= 3:  # 避免扫描根目录（如 C:/ 或 C:\）
                    self.logger.warning(f"Skipping root or invalid directory for: {path}")
                    continue
                
                # 尝试找到一个合理的项目根目录
                # 策略：向上查找，但最多3层，且不超过盘符根目录
                current_dir = parent_dir
                project_root = parent_dir
                max_levels = 3
                level = 0
                
                while level < max_levels and current_dir:
                    parent = os.path.dirname(current_dir)
                    
                    # 停止条件：
                    # 1. 到达根目录（如 C:\ 或 /）
                    # 2. 父目录为空或与当前目录相同
                    # 3. 父目录长度 <= 3（盘符）
                    if not parent or parent == current_dir or len(parent) <= 3:
                        break
                    
                    # 检查是否已经在custom_paths中
                    if parent in self._custom_paths:
                        project_root = parent
                        break
                    
                    # 检查是否是常见的项目根目录标志
                    # （包含 .git, .vscode, requirements.txt 等）
                    if any(os.path.exists(os.path.join(parent, marker))
                           for marker in ['.git', '.vscode', 'requirements.txt', 'setup.py']):
                        project_root = parent
                        break
                    
                    current_dir = parent
                    level += 1
                
                # 确保不是根目录
                if project_root and len(project_root) > 3 and project_root not in self._custom_paths:
                    dirs_to_scan.add(project_root)
            
            if not dirs_to_scan:
                self.logger.info("No valid directories to scan for missing scripts")
                return
            
            self.logger.info(f"Auto-loading {len(dirs_to_scan)} directories for missing scripts: {dirs_to_scan}")
            
            # 扫描并加载这些目录
            total_added = 0
            for dir_path in dirs_to_scan:
                try:
                    if dir_path not in self._custom_paths:
                        self._custom_paths.append(dir_path)
                        
                        # 扫描目录
                        self.logger.info(f"Scanning directory: {dir_path}")
                        result = self.script_service.scan_and_load_scripts(dir_path)
                        
                        if result['success']:
                            # 添加脚本到列表
                            existing_paths = {s['path'] for s in self._scripts}
                            added_count = 0
                            
                            for script in result['scripts']:
                                if script['path'] not in existing_paths:
                                    self._scripts.append(script)
                                    self._filtered_scripts.append(script)
                                    existing_paths.add(script['path'])
                                    added_count += 1
                            
                            total_added += added_count
                            self.logger.info(f"Added {added_count} scripts from {dir_path}")
                        else:
                            self.logger.warning(f"Failed to scan {dir_path}: {result.get('error')}")
                
                except Exception as e:
                    self.logger.error(f"Error scanning directory {dir_path}: {e}")
                    continue
            
            # 只在有新脚本添加时才更新UI（批量更新）
            if total_added > 0:
                self.tree_widget.setUpdatesEnabled(False)
                try:
                    self._update_tree()
                    self._update_stats()
                finally:
                    self.tree_widget.setUpdatesEnabled(True)
            
            self.logger.info(f"Auto-load complete. Total scripts: {len(self._scripts)}")
        
        except Exception as e:
            self.logger.error(f"Error auto-loading missing scripts: {e}", exc_info=True)
    
    def _select_scripts_by_paths(self, paths):
        """根据路径选中脚本（递归处理 - 优化版）
        
        Args:
            paths: 脚本路径列表
        """
        # 暂时断开信号，避免每次状态改变都触发
        self.tree_widget.itemChanged.disconnect(self._on_item_checked)
        self.tree_widget.setUpdatesEnabled(False)
        
        try:
            # 规范化路径用于比较
            def normalize_path(p):
                """规范化路径用于比较"""
                return os.path.normpath(p).lower().replace('\\', '/')
            
            # 创建规范化路径集合
            normalized_path_set = {normalize_path(p) for p in paths}
            
            def select_recursive(item):
                for i in range(item.childCount()):
                    child = item.child(i)
                    script = child.data(0, Qt.UserRole)
                    
                    # 如果是脚本节点且在路径集合中（使用规范化路径比较）
                    if script:
                        normalized_script_path = normalize_path(script['path'])
                        if normalized_script_path in normalized_path_set:
                            child.setCheckState(0, Qt.Checked)
                    
                    # 递归处理子节点
                    select_recursive(child)
            
            root = self.tree_widget.invisibleRootItem()
            select_recursive(root)
        
        finally:
            self.tree_widget.setUpdatesEnabled(True)
            self.tree_widget.itemChanged.connect(self._on_item_checked)
    
    def _on_save_suite(self):
        """保存为方案"""
        selected_scripts = self.get_selected_scripts()
        
        if not selected_scripts:
            QMessageBox.warning(self, "警告", "请先选择要保存的脚本")
            return
        
        # 显示保存对话框
        dialog = SaveSuiteDialog(selected_scripts, self)
        if dialog.exec_() == dialog.Accepted:
            suite_info = dialog.get_suite_info()
            
            try:
                result = self.suite_service.create_suite(
                    name=suite_info['name'],
                    script_paths=suite_info['script_paths'],
                    description=suite_info['description']
                )
                
                if result['success']:
                    QMessageBox.information(
                        self, "成功",
                        f"方案 '{suite_info['name']}' 保存成功"
                    )
                    # 刷新方案列表
                    self._load_suites()
                    # 选择新创建的方案
                    index = self.suite_combo.findText(suite_info['name'])
                    if index >= 0:
                        self.suite_combo.setCurrentIndex(index)
                else:
                    QMessageBox.warning(
                        self, "失败",
                        f"保存失败: {result.get('error', '')}"
                    )
            
            except Exception as e:
                self.logger.error(f"Error saving suite: {e}")
                QMessageBox.critical(self, "错误", f"保存方案时出错: {e}")
    
    def _on_manage_suites(self):
        """管理方案"""
        dialog = ManageSuitesDialog(self.container, self)
        dialog.suite_selected.connect(self._on_suite_loaded_from_dialog)
        dialog.exec_()
        
        # 刷新方案列表
        self._load_suites()
    
    def _on_suite_loaded_from_dialog(self, suite):
        """从对话框加载方案（优化版 - 异步加载）"""
        from PyQt5.QtWidgets import QProgressDialog
        from PyQt5.QtCore import QThread, pyqtSignal, Qt
        
        # 在下拉框中选择该方案（不显示提示消息，因为对话框已经显示过了）
        index = self.suite_combo.findData(suite['id'])
        if index < 0:
            return
        
        # 创建进度对话框
        progress = QProgressDialog("正在加载方案...", None, 0, 0, self)
        progress.setWindowTitle("加载中")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)  # 立即显示
        progress.setCancelButton(None)  # 不允许取消
        progress.setValue(0)
        progress.show()
        
        # 使用线程异步加载方案
        class LoadSuiteThread(QThread):
            finished = pyqtSignal(list, list)  # selected_scripts, script_info_list
            error = pyqtSignal(str)
            
            def __init__(self, parent_widget, suite_data, suite_index):
                super().__init__()
                self.parent_widget = parent_widget
                self.suite_data = suite_data
                self.suite_index = suite_index
            
            def run(self):
                try:
                    # 临时断开信号，避免触发_on_suite_changed
                    self.parent_widget.suite_combo.currentIndexChanged.disconnect(
                        self.parent_widget._on_suite_changed
                    )
                    self.parent_widget.suite_combo.setCurrentIndex(self.suite_index)
                    
                    # 手动调用加载方案（不显示消息）
                    self.parent_widget._on_suite_changed(self.suite_index, show_message=False)
                    
                    # 重新连接信号
                    self.parent_widget.suite_combo.currentIndexChanged.connect(
                        self.parent_widget._on_suite_changed
                    )
                    
                    # 获取选中的脚本
                    selected_scripts = self.parent_widget.get_selected_scripts()
                    script_info_list = []
                    
                    if selected_scripts:
                        # 获取脚本信息
                        for path in selected_scripts:
                            info = self.parent_widget._get_script_info_by_path(path)
                            if info:
                                script_info_list.append(info)
                    
                    self.finished.emit(selected_scripts, script_info_list)
                
                except Exception as e:
                    self.error.emit(str(e))
        
        # 保持线程引用
        self._load_suite_thread = LoadSuiteThread(self, suite, index)
        
        def on_load_finished(selected_scripts, script_info_list):
            try:
                progress.close()
                
                if selected_scripts:
                    # 触发添加到队列的信号
                    self.add_to_queue_requested.emit(selected_scripts, script_info_list)
                    self.logger.info(f"Auto-added {len(selected_scripts)} scripts from suite '{suite['name']}' to execution queue")
            
            except Exception as e:
                self.logger.error(f"Error in on_load_finished: {e}")
            finally:
                self._load_suite_thread = None
        
        def on_load_error(error_msg):
            try:
                progress.close()
                QMessageBox.critical(self, "错误", f"加载方案失败: {error_msg}")
            except Exception as e:
                self.logger.error(f"Error in on_load_error: {e}")
            finally:
                self._load_suite_thread = None
        
        # 连接信号
        self._load_suite_thread.finished.connect(on_load_finished)
        self._load_suite_thread.error.connect(on_load_error)
        
        # 启动线程
        self._load_suite_thread.start()
    
    def get_current_suite(self):
        """获取当前选择的测试方案
        
        Returns:
            当前方案信息，如果没有选择则返回None
        """
        return self._current_suite
    
    def _on_add_custom_path(self):
        """添加自定义脚本路径"""
        from PyQt5.QtWidgets import QFileDialog, QInputDialog
        from .script_selection_dialog import ScriptSelectionDialog
        
        # 询问用户要添加文件还是文件夹
        items = ["添加单个脚本文件", "添加整个文件夹"]
        item, ok = QInputDialog.getItem(
            self, "选择添加类型",
            "请选择要添加的类型:",
            items, 0, False
        )
        
        if not ok:
            return
        
        if item == "添加单个脚本文件":
            # 选择单个Python文件
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择Python脚本文件",
                "",
                "Python Files (*.py);;All Files (*)"
            )
            
            if file_path:
                self._add_custom_script(file_path)
        
        else:
            # 选择文件夹
            folder_path = QFileDialog.getExistingDirectory(
                self,
                "选择脚本文件夹",
                ""
            )
            
            if folder_path:
                self._add_custom_folder_with_selection(folder_path)
    
    def _add_custom_script(self, script_path):
        """添加单个自定义脚本
        
        Args:
            script_path: 脚本文件路径
        """
        try:
            # 检查是否已添加
            if script_path in self._custom_paths:
                QMessageBox.information(self, "提示", "该脚本已经添加过了")
                return
            
            # 验证脚本
            if not self.script_service.script_manager.validate_script(script_path):
                QMessageBox.warning(self, "警告", "无效的Python脚本文件")
                return
            
            # 添加到自定义路径列表
            self._custom_paths.append(script_path)
            
            # 获取脚本信息并添加到缓存
            script_info = self.script_service.script_manager.get_script_info(script_path)
            self._scripts.append(script_info)
            self._filtered_scripts.append(script_info)
            
            # 更新树形控件
            self._update_tree()
            self._update_stats()
            
            self.logger.info(f"Added custom script: {script_path}")
            QMessageBox.information(
                self, "成功",
                f"已添加脚本:\n{os.path.basename(script_path)}"
            )
        
        except Exception as e:
            self.logger.error(f"Error adding custom script: {e}")
            QMessageBox.critical(self, "错误", f"添加脚本失败: {e}")
    
    def _add_custom_folder_with_selection(self, folder_path):
        """添加自定义文件夹 - 弹出对话框让用户选择脚本（异步优化版）
        
        Args:
            folder_path: 文件夹路径
        """
        try:
            from .script_selection_dialog import ScriptSelectionDialog
            from PyQt5.QtWidgets import QProgressDialog
            from PyQt5.QtCore import QThread, pyqtSignal
            
            # 检查是否已添加
            if folder_path in self._custom_paths:
                QMessageBox.information(self, "提示", "该文件夹已经添加过了")
                return
            
            # 创建进度对话框
            progress = QProgressDialog("正在扫描文件夹...", "取消", 0, 0, self)
            progress.setWindowTitle("扫描中")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(500)  # 500ms后才显示
            progress.setValue(0)
            
            # 使用线程扫描文件夹（避免UI卡顿）
            class ScanThread(QThread):
                finished = pyqtSignal(dict)
                error = pyqtSignal(str)
                
                def __init__(self, service, path):
                    super().__init__()
                    self.service = service
                    self.path = path
                
                def run(self):
                    try:
                        result = self.service.scan_and_load_scripts(self.path)
                        self.finished.emit(result)
                    except Exception as e:
                        self.error.emit(str(e))
            
            # 保持线程引用，防止被垃圾回收
            self._scan_thread = ScanThread(self.script_service, folder_path)
            
            # 扫描完成后的处理
            def on_scan_finished(result):
                try:
                    progress.close()
                    
                    if not result['success']:
                        QMessageBox.warning(self, "警告", f"扫描文件夹失败: {result.get('error', '')}")
                        return
                    
                    all_scripts = result['scripts']
                    if not all_scripts:
                        QMessageBox.information(self, "提示", "该文件夹中没有找到Python脚本")
                        return
                    
                    # 显示脚本选择对话框
                    dialog = ScriptSelectionDialog(all_scripts, folder_path, self)
                    if dialog.exec_() != dialog.Accepted:
                        return
                    
                    # 获取用户选择的脚本
                    selected_scripts = dialog.get_selected_scripts()
                    if not selected_scripts:
                        return
                    
                    # 添加到自定义路径列表
                    self._custom_paths.append(folder_path)
                    
                    # 使用集合优化查找性能
                    existing_paths = {s['path'] for s in self._scripts}
                    
                    # 批量添加选中的脚本到列表（避免逐个添加触发多次更新）
                    added_count = 0
                    for script in selected_scripts:
                        if script['path'] not in existing_paths:
                            self._scripts.append(script)
                            self._filtered_scripts.append(script)
                            existing_paths.add(script['path'])
                            added_count += 1
                    
                    # 只在有新脚本添加时才更新UI
                    if added_count > 0:
                        # 使用优化的更新方法：禁用UI更新直到完成
                        self.tree_widget.setUpdatesEnabled(False)
                        try:
                            self._update_tree()
                            self._update_stats()
                        finally:
                            self.tree_widget.setUpdatesEnabled(True)
                    
                    self.logger.info(f"Added {added_count} scripts from folder: {folder_path}")
                    QMessageBox.information(
                        self, "成功",
                        f"已从文件夹添加 {added_count} 个脚本:\n{os.path.basename(folder_path)}"
                    )
                except Exception as e:
                    self.logger.error(f"Error in on_scan_finished: {e}")
                    QMessageBox.critical(self, "错误", f"处理扫描结果时出错: {e}")
                finally:
                    # 清理线程引用
                    self._scan_thread = None
            
            def on_scan_error(error_msg):
                try:
                    progress.close()
                    QMessageBox.critical(self, "错误", f"扫描文件夹时出错: {error_msg}")
                except Exception as e:
                    self.logger.error(f"Error in on_scan_error: {e}")
                finally:
                    # 清理线程引用
                    self._scan_thread = None
            
            # 连接信号
            self._scan_thread.finished.connect(on_scan_finished)
            self._scan_thread.error.connect(on_scan_error)
            
            # 启动线程
            self._scan_thread.start()
        
        except Exception as e:
            self.logger.error(f"Error adding custom folder: {e}")
            QMessageBox.critical(self, "错误", f"添加文件夹失败: {e}")
    
    def _on_add_to_queue(self):
        """添加选中的脚本到执行队列"""
        selected_scripts = self.get_selected_scripts()
        
        if not selected_scripts:
            QMessageBox.warning(self, "警告", "请先选择要添加的脚本")
            return
        
        # 发出信号，由主窗口处理
        # 获取脚本信息
        script_info_list = []
        for path in selected_scripts:
            info = self._get_script_info_by_path(path)
            if info:
                script_info_list.append(info)
        
        # 触发信号
        if hasattr(self, 'add_to_queue_requested'):
            self.add_to_queue_requested.emit(selected_scripts, script_info_list)