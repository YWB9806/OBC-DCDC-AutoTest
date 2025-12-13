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
        
        # 方案选择器
        suite_layout = QHBoxLayout()
        suite_layout.addWidget(QLabel("测试方案:"))
        
        self.suite_combo = QComboBox()
        self.suite_combo.addItem("-- 未选择方案 --")
        self.suite_combo.currentIndexChanged.connect(self._on_suite_changed)
        suite_layout.addWidget(self.suite_combo)
        
        self.manage_suite_btn = QPushButton("管理方案")
        self.manage_suite_btn.clicked.connect(self._on_manage_suites)
        suite_layout.addWidget(self.manage_suite_btn)
        
        layout.addLayout(suite_layout)
        
        # 过滤器和树形控件选项
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("分类:"))
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("全部")
        self.category_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.category_combo)
        
        filter_layout.addStretch()
        
        # 添加一键折叠/展开按钮
        self.collapse_all_btn = QPushButton("一键折叠")
        self.collapse_all_btn.clicked.connect(self._on_collapse_all)
        filter_layout.addWidget(self.collapse_all_btn)
        
        self.expand_all_btn = QPushButton("一键展开")
        self.expand_all_btn.clicked.connect(self._on_expand_all)
        filter_layout.addWidget(self.expand_all_btn)
        
        # 添加列显示设置按钮
        self.column_settings_btn = QPushButton("列设置")
        self.column_settings_btn.clicked.connect(self._show_column_settings)
        filter_layout.addWidget(self.column_settings_btn)
        
        layout.addLayout(filter_layout)
        
        # 脚本树
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["脚本名称", "路径", "状态"])
        self.tree_widget.setColumnWidth(0, 250)
        self.tree_widget.setColumnWidth(1, 350)
        # 不使用ExtendedSelection，改用复选框模式
        self.tree_widget.itemChanged.connect(self._on_item_checked)
        self.tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.tree_widget)
        
        # 列显示状态（默认只显示脚本名称）
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
        
        self.save_suite_btn = QPushButton("保存为方案")
        self.save_suite_btn.clicked.connect(self._on_save_suite)
        button_layout.addWidget(self.save_suite_btn)
        
        layout.addLayout(button_layout)
    
    def _load_scripts(self):
        """加载脚本列表"""
        try:
            # 从配置获取脚本根目录
            root_path = self.config_manager.get('scripts.root_path', 'TestScripts')
            self._root_path = root_path
            
            if not os.path.exists(root_path):
                self.logger.warning(f"Script root path not found: {root_path}")
                return
            
            # 扫描脚本
            result = self.script_service.scan_and_load_scripts(root_path)
            
            if result['success']:
                self._scripts = result['scripts']
                self._filtered_scripts = self._scripts.copy()
                
                # 更新分类下拉框
                categories = self.script_service.get_categories()
                self.category_combo.clear()
                self.category_combo.addItem("全部")
                self.category_combo.addItems(categories)
                
                # 更新树形控件
                self._update_tree()
                
                # 更新统计信息
                self._update_stats()
                
                # 加载方案列表
                self._load_suites()
                
                self.logger.info(f"Loaded {len(self._scripts)} scripts")
            else:
                error = result.get('error', 'Unknown error')
                self.logger.error(f"Failed to load scripts: {error}")
                QMessageBox.warning(self, "警告", f"加载脚本失败: {error}")
        
        except Exception as e:
            self.logger.error(f"Error loading scripts: {e}")
            QMessageBox.critical(self, "错误", f"加载脚本时出错: {e}")
    
    def _update_tree(self):
        """更新树形控件 - 使用文件夹层级结构"""
        # 暂时断开信号，避免在批量更新时触发
        self.tree_widget.itemChanged.disconnect(self._on_item_checked)
        
        self.tree_widget.clear()
        
        # 获取脚本树形结构
        if self._root_path:
            tree_data = self.script_service.get_script_tree(self._root_path)
            
            # 递归构建树形控件
            self._build_tree_recursive(tree_data, self.tree_widget)
        
        # 重新连接信号
        self.tree_widget.itemChanged.connect(self._on_item_checked)
    
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
    
    def _on_filter_changed(self):
        """过滤器改变"""
        category = self.category_combo.currentText()
        
        if category == "全部":
            self._filtered_scripts = self._scripts.copy()
        else:
            self._filtered_scripts = self.script_service.get_scripts_by_category(category)
        
        # 应用搜索过滤
        keyword = self.search_input.text().strip()
        if keyword:
            self._filtered_scripts = [
                s for s in self._filtered_scripts
                if keyword.lower() in s['name'].lower() or
                   keyword.lower() in s['path'].lower()
            ]
        
        self._update_tree()
        self._update_stats()
    
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
        """全选"""
        self._set_all_check_state(Qt.Checked)
    
    def _on_deselect_all(self):
        """全不选"""
        self._set_all_check_state(Qt.Unchecked)
    
    def _on_invert_selection(self):
        """反选（递归处理）"""
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
            except:
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
    
    def get_current_suite(self):
        """获取当前选择的测试方案
        
        Returns:
            当前方案信息字典，如果未选择则返回None
        """
        return self._current_suite
    
    def _select_scripts_by_paths(self, paths):
        """根据路径选中脚本（递归处理）
        
        Args:
            paths: 脚本路径列表
        """
        path_set = set(paths)
        
        def select_recursive(item):
            for i in range(item.childCount()):
                child = item.child(i)
                script = child.data(0, Qt.UserRole)
                
                # 如果是脚本节点且在路径集合中
                if script and script['path'] in path_set:
                    child.setCheckState(0, Qt.Checked)
                
                # 递归处理子节点
                select_recursive(child)
        
        root = self.tree_widget.invisibleRootItem()
        select_recursive(root)
    
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
        """从对话框加载方案"""
        # 在下拉框中选择该方案（不显示提示消息，因为对话框已经显示过了）
        index = self.suite_combo.findData(suite['id'])
        if index >= 0:
            # 临时断开信号，避免触发_on_suite_changed
            self.suite_combo.currentIndexChanged.disconnect(self._on_suite_changed)
            self.suite_combo.setCurrentIndex(index)
            # 手动调用，但不显示消息
            self._on_suite_changed(index, show_message=False)
            # 重新连接信号
            self.suite_combo.currentIndexChanged.connect(self._on_suite_changed)
    
    def get_current_suite(self):
        """获取当前选择的测试方案
        
        Returns:
            当前方案信息，如果没有选择则返回None
        """
        return self._current_suite