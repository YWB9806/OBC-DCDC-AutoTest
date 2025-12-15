"""主窗口

应用程序的主界面窗口。
"""

import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QStatusBar, QMenuBar,
    QMenu, QAction, QToolBar, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

from .script_browser import ScriptBrowser
from .execution_panel import ExecutionPanel
from .execution_queue_panel import ExecutionQueuePanel
from .result_viewer import ResultViewer
from .dashboard import Dashboard
from .performance_panel import PerformancePanel
from .backup_panel import BackupPanel
from .user_panel import UserPanel
from .plugin_panel import PluginPanel
from AppCode.ui.update_dialog import show_update_dialog
from PyQt5.QtCore import QTimer

class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 信号定义
    script_selected = pyqtSignal(str)  # 脚本被选中
    execution_started = pyqtSignal(list)  # 执行开始
    execution_stopped = pyqtSignal()  # 执行停止
    
    def __init__(self, container, parent=None):
        """初始化主窗口
        
        Args:
            container: 依赖注入容器
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.container = container
        self.logger = container.resolve('log_manager').get_logger('ui')
        
        # 获取服务
        self.script_service = container.resolve('script_service')
        self.execution_service = container.resolve('execution_service')
        self.analysis_service = container.resolve('analysis_service')
        self.performance_monitor_service = container.resolve('performance_monitor_service')
        self.backup_service = container.resolve('backup_service')
        self.user_service = container.resolve('user_service')
        self.plugin_manager = container.resolve('plugin_manager')
        
        # 当前登录用户信息
        self.current_user = None
        self.is_super_admin = False
        self.can_view_results = False
        
        # 保存分割器引用
        self.main_splitter = None
        
        self._init_ui()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._connect_signals()
        
        # 初始状态：禁用所有功能，等待登录
        self._disable_all_functions()
        
        self.logger.info("Main window initialized")
        # 移除自动更新检查，改为手动检查
        # QTimer.singleShot(3000, lambda: show_update_dialog(self, force_check=False))
    
    def _init_ui(self):
        """初始化UI"""
        from version import get_version_string
        self.setWindowTitle(f"Python脚本批量执行工具 v{get_version_string()}")
        # 调整窗口大小：宽度改为800，适应小屏幕显示器
        self.setGeometry(100, 100, 800, 700)
        
        # 设置窗口图标
        icon_path = os.path.join('resources', 'app图标.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            self.logger.info(f"Window icon loaded from: {icon_path}")
        else:
            self.logger.warning(f"Window icon not found: {icon_path}")
        
        # 创建两栏分割器（可拖动）
        self.main_splitter = QSplitter(Qt.Horizontal, self)
        
        # 关键设置：防止子控件被完全折叠
        self.main_splitter.setChildrenCollapsible(False)
        
        # 设置分割器手柄宽度，使其更容易抓取
        self.main_splitter.setHandleWidth(6)
        
        # 设置分割器样式，使手柄更明显
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #d0d0d0;
                border: 1px solid #a0a0a0;
            }
            QSplitter::handle:hover {
                background-color: #b0b0b0;
            }
            QSplitter::handle:pressed {
                background-color: #909090;
            }
        """)
        
        # 左侧：脚本浏览器（临时脚本池）
        self.script_browser = ScriptBrowser(self.container)
        self.main_splitter.addWidget(self.script_browser)
        
        # 右侧：标签页
        self.tab_widget = QTabWidget()
        
        # 执行队列面板（作为第一个标签页）
        self.execution_queue = ExecutionQueuePanel()
        self.queue_tab_index = self.tab_widget.addTab(self.execution_queue, "执行队列")
        
        # 执行控制面板（所有用户可见）
        self.execution_panel = ExecutionPanel(self.container)
        self.execution_tab_index = self.tab_widget.addTab(self.execution_panel, "执行控制")
        
        # 结果查看器（需要权限）
        self.result_viewer = ResultViewer(self.container)
        self.result_tab_index = self.tab_widget.addTab(self.result_viewer, "执行结果")
        
        # 统计仪表板（开发版本隐藏）
        # self.dashboard = Dashboard(self.container)
        # self.tab_widget.addTab(self.dashboard, "统计分析")
        
        # 性能监控面板（开发版本隐藏）
        # self.performance_panel = PerformancePanel(self.container, self)
        # self.tab_widget.addTab(self.performance_panel, "性能监控")
        
        # 备份管理面板（开发版本隐藏）
        # self.backup_panel = BackupPanel(self.container, self)
        # self.tab_widget.addTab(self.backup_panel, "数据备份")
        
        # 用户管理面板（仅超级管理员可见）
        self.user_panel = UserPanel(self.container, self)
        self.user_tab_index = self.tab_widget.addTab(self.user_panel, "用户管理")
        
        # 插件管理面板 - 注意：PluginPanel使用tkinter，暂时跳过
        # self.plugin_panel = PluginPanel(self, self.plugin_manager)
        # self.tab_widget.addTab(self.plugin_panel, "插件管理")
        
        self.main_splitter.addWidget(self.tab_widget)
        
        # 设置分割器初始大小（像素）- 两栏布局
        # 总宽度800，按比例分配：左250 + 右550 = 800
        self.main_splitter.setSizes([250, 550])
        
        # 设置拉伸因子，使右侧面板在窗口调整大小时获得更多空间
        self.main_splitter.setStretchFactor(0, 1)  # 左侧：适度拉伸
        self.main_splitter.setStretchFactor(1, 3)  # 右侧：主要拉伸区域
        
        # 直接将分割器设为中央部件
        self.setCentralWidget(self.main_splitter)
        
        self.logger.info("UI initialized with two-column layout (execution queue moved to tab)")
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        refresh_action = QAction("刷新脚本(&R)", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._on_refresh_scripts)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 执行菜单
        exec_menu = menubar.addMenu("执行(&E)")
        
        start_action = QAction("开始执行(&S)", self)
        start_action.setShortcut("F9")
        start_action.triggered.connect(self._on_start_execution)
        exec_menu.addAction(start_action)
        
        stop_action = QAction("停止执行(&T)", self)
        stop_action.setShortcut("Shift+F9")
        stop_action.triggered.connect(self._on_stop_execution)
        exec_menu.addAction(stop_action)
        
        exec_menu.addSeparator()
        
        # 新增：暂停执行
        pause_action = QAction("暂停执行(&P)", self)
        pause_action.setShortcut("F10")
        pause_action.triggered.connect(self._on_pause_execution)
        exec_menu.addAction(pause_action)
        
        # 新增：继续执行
        resume_action = QAction("继续执行(&C)", self)
        resume_action.setShortcut("F11")
        resume_action.triggered.connect(self._on_resume_execution)
        exec_menu.addAction(resume_action)
        
        exec_menu.addSeparator()
        
        # 新增：重新执行失败的脚本
        retry_failed_action = QAction("重试失败脚本(&R)", self)
        retry_failed_action.triggered.connect(self._on_retry_failed)
        exec_menu.addAction(retry_failed_action)
        
        # 新增：跳过当前脚本
        skip_current_action = QAction("跳过当前脚本(&K)", self)
        skip_current_action.setShortcut("Ctrl+K")
        skip_current_action.triggered.connect(self._on_skip_current)
        exec_menu.addAction(skip_current_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        dashboard_action = QAction("统计仪表板(&D)", self)
        dashboard_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        view_menu.addAction(dashboard_action)
        
        performance_action = QAction("性能监控(&P)", self)
        performance_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))
        view_menu.addAction(performance_action)
        
        backup_action = QAction("数据备份(&B)", self)
        backup_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(4))
        view_menu.addAction(backup_action)
        
        user_action = QAction("用户管理(&U)", self)
        user_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(5))
        view_menu.addAction(user_action)
        
        plugin_action = QAction("插件管理(&L)", self)
        plugin_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(6))
        view_menu.addAction(plugin_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        settings_action = QAction("设置(&S)", self)
        settings_action.triggered.connect(self._on_settings)
        tools_menu.addAction(settings_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        check_update_action = QAction("检查更新(&U)", self)
        check_update_action.setShortcut("F12")
        check_update_action.triggered.connect(self._on_check_update)
        help_menu.addAction(check_update_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _create_tool_bar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # 刷新按钮
        refresh_action = QAction("刷新", self)
        refresh_action.setToolTip("刷新脚本列表 (F5)")
        refresh_action.triggered.connect(self._on_refresh_scripts)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # 执行按钮
        self.start_action = QAction("开始执行", self)
        self.start_action.setToolTip("开始执行选中的脚本 (F9)")
        self.start_action.triggered.connect(self._on_start_execution)
        toolbar.addAction(self.start_action)
        
        self.stop_action = QAction("停止执行", self)
        self.stop_action.setToolTip("停止当前执行 (Shift+F9)")
        self.stop_action.setEnabled(False)
        self.stop_action.triggered.connect(self._on_stop_execution)
        toolbar.addAction(self.stop_action)
        
        self.pause_action = QAction("暂停", self)
        self.pause_action.setToolTip("暂停执行 (F10)")
        self.pause_action.setEnabled(False)
        self.pause_action.triggered.connect(self._on_pause_execution)
        toolbar.addAction(self.pause_action)
        
        self.resume_action = QAction("继续", self)
        self.resume_action.setToolTip("继续执行 (F11)")
        self.resume_action.setEnabled(False)
        self.resume_action.triggered.connect(self._on_resume_execution)
        toolbar.addAction(self.resume_action)
        
        toolbar.addSeparator()
        
        # 重试和跳过按钮
        self.retry_action = QAction("重试失败", self)
        self.retry_action.setToolTip("重新执行失败的脚本")
        self.retry_action.triggered.connect(self._on_retry_failed)
        toolbar.addAction(self.retry_action)
        
        self.skip_action = QAction("跳过当前", self)
        self.skip_action.setToolTip("跳过当前正在执行的脚本 (Ctrl+K)")
        self.skip_action.setEnabled(False)
        self.skip_action.triggered.connect(self._on_skip_current)
        toolbar.addAction(self.skip_action)
        
        toolbar.addSeparator()
        
        # 导出按钮
        export_action = QAction("导出报告", self)
        export_action.setToolTip("导出执行报告")
        export_action.triggered.connect(self._on_export_report)
        toolbar.addAction(export_action)
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 脚本浏览器信号
        self.script_browser.script_selected.connect(self._on_script_selected)
        self.script_browser.scripts_selected.connect(self._on_scripts_selected)
        self.script_browser.add_to_queue_requested.connect(self._on_add_to_queue)
        
        # 执行队列信号
        self.execution_queue.execute_requested.connect(self._on_execute_queue)
        self.execution_queue.queue_changed.connect(self._on_queue_changed)
        
        # 执行面板信号
        self.execution_panel.execution_started.connect(self._on_execution_started)
        self.execution_panel.execution_finished.connect(self._on_execution_finished)
        self.execution_panel.execution_paused.connect(self._on_execution_paused)
        self.execution_panel.execution_resumed.connect(self._on_execution_resumed)
        
        # 结果查看器信号
        self.result_viewer.result_selected.connect(self._on_result_selected)
    
    def _on_refresh_scripts(self):
        """刷新脚本列表"""
        try:
            self.status_bar.showMessage("正在刷新脚本列表...")
            self.script_browser.refresh()
            self.status_bar.showMessage("脚本列表已刷新", 3000)
            self.logger.info("Scripts refreshed")
        except Exception as e:
            self.logger.error(f"Failed to refresh scripts: {e}")
            QMessageBox.critical(self, "错误", f"刷新脚本失败: {e}")
    
    def _on_add_to_queue(self, script_paths, script_info_list):
        """将脚本添加到执行队列
        
        Args:
            script_paths: 脚本路径列表
            script_info_list: 脚本信息列表
        """
        self.execution_queue.add_scripts(script_paths, script_info_list)
        
        # 【Bug修复】获取当前方案并传递给执行面板
        current_suite = self.script_browser.get_current_suite()
        if current_suite:
            self.execution_panel.set_current_suite(current_suite)
            self.logger.info(f"Set current suite for execution: {current_suite.get('name')}")
        else:
            # 如果没有选择方案，清空执行面板的方案信息
            self.execution_panel.set_current_suite(None)
            self.logger.info("No suite selected, cleared execution panel suite info")
        
        self.logger.info(f"Added {len(script_paths)} scripts to execution queue")
    
    def _on_queue_changed(self, queue):
        """执行队列改变
        
        Args:
            queue: 新的队列（脚本路径列表）
        """
        self.logger.info(f"Execution queue changed, now has {len(queue)} scripts")
    
    def _on_execute_queue(self, script_paths):
        """执行队列中的脚本
        
        Args:
            script_paths: 要执行的脚本路径列表
        """
        if not script_paths:
            return
        
        self.logger.info(f"Executing {len(script_paths)} scripts from queue")
        
        # 【Bug修复】在执行前再次确认当前方案（防止用户在添加到队列后切换了方案）
        current_suite = self.script_browser.get_current_suite()
        if current_suite:
            self.execution_panel.set_current_suite(current_suite)
            self.logger.info(f"Confirmed current suite before execution: {current_suite.get('name')}")
        
        # 切换到执行控制面板（现在是第二个标签页，索引为1）
        self.tab_widget.setCurrentIndex(1)
        
        # 开始执行
        self.execution_panel.start_execution(script_paths)
    
    def _on_start_execution(self):
        """开始执行 - 从执行队列执行"""
        queue = self.execution_queue.get_queue()
        
        if not queue:
            QMessageBox.warning(self, "警告", "执行队列为空，请先添加脚本到执行列表")
            return
        
        # 执行队列中的脚本
        self._on_execute_queue(queue)
    
    def _on_stop_execution(self):
        """停止执行"""
        self.execution_panel.stop_execution()
        self.logger.info("Execution stopped")
    
    def _on_pause_execution(self):
        """暂停执行"""
        try:
            self.execution_panel.pause_execution()
            self.logger.info("Pause execution requested")
        except Exception as e:
            self.logger.error(f"Error pausing execution: {e}")
            QMessageBox.critical(self, "错误", f"暂停执行时出错: {e}")
    
    def _on_resume_execution(self):
        """继续执行"""
        try:
            self.execution_panel.resume_execution()
            self.logger.info("Resume execution requested")
        except Exception as e:
            self.logger.error(f"Error resuming execution: {e}")
            QMessageBox.critical(self, "错误", f"恢复执行时出错: {e}")
    
    def _on_retry_failed(self):
        """重试失败的脚本"""
        try:
            # 从执行面板获取失败的脚本
            failed_scripts = []
            execution_table = self.execution_panel.execution_table
            
            for row in range(execution_table.rowCount()):
                result_item = execution_table.item(row, 4)  # 结果列
                if result_item and result_item.text() in ['不合格', '执行错误', '超时']:
                    script_name_item = execution_table.item(row, 0)
                    if script_name_item:
                        # 需要从脚本名称找到完整路径
                        script_name = script_name_item.text()
                        # 从脚本浏览器中查找对应的完整路径
                        for script in self.script_browser._scripts:
                            if script['name'] == script_name:
                                failed_scripts.append(script['path'])
                                break
            
            if not failed_scripts:
                QMessageBox.information(self, "提示", "没有需要重试的失败脚本")
                return
            
            reply = QMessageBox.question(
                self,
                "确认重试",
                f"找到 {len(failed_scripts)} 个失败的脚本，是否重新执行？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.logger.info(f"Retrying {len(failed_scripts)} failed scripts")
                self.execution_panel.start_execution(failed_scripts)
        except Exception as e:
            self.logger.error(f"Error retrying failed scripts: {e}")
            QMessageBox.critical(self, "错误", f"重试失败脚本时出错: {e}")
    
    def _on_skip_current(self):
        """跳过当前脚本"""
        try:
            QMessageBox.information(self, "提示", "跳过当前脚本功能开发中...\n当前版本暂不支持跳过单个脚本")
            self.logger.info("Skip current script requested (not implemented)")
        except Exception as e:
            self.logger.error(f"Error in skip current: {e}")
    
    def _on_settings(self):
        """打开设置对话框"""
        QMessageBox.information(self, "设置", "设置功能开发中...")
    
    def _on_check_update(self):
        """手动检查更新"""
        try:
            self.logger.info("Manual update check requested")
            show_update_dialog(self, force_check=True)
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            QMessageBox.critical(self, "错误", f"检查更新时出错: {e}")
    
    def _on_about(self):
        """显示关于对话框"""
        from version import get_version_string
        about_text = f"""
        <h2>Python脚本批量执行工具</h2>
        <p>版本: {get_version_string()}</p>
        <p>一款用于批量管理和执行Python测试脚本的桌面应用程序。</p>
        <p>Copyright © 2024-2025</p>
        <br>
        <p><b>功能特性：</b></p>
        <ul>
        <li>支持批量执行Python脚本</li>
        <li>支持添加任意位置的脚本文件或文件夹</li>
        <li>实时监控执行过程和结果</li>
        <li>测试方案管理</li>
        <li>用户权限管理</li>
        </ul>
        """
        QMessageBox.about(self, "关于", about_text)
    
    def _on_export_report(self):
        """导出报告"""
        try:
            # 切换到统计仪表板
            self.tab_widget.setCurrentIndex(2)
            self.dashboard.export_report()
        except Exception as e:
            self.logger.error(f"Failed to export report: {e}")
            QMessageBox.critical(self, "错误", f"导出报告失败: {e}")
    
    def _on_script_selected(self, script_path: str):
        """脚本被选中"""
        self.status_bar.showMessage(f"已选择: {script_path}")
        self.script_selected.emit(script_path)
    
    def _on_scripts_selected(self, script_paths: list):
        """多个脚本被选中"""
        count = len(script_paths)
        self.status_bar.showMessage(f"已选择 {count} 个脚本")
    
    def _on_execution_started(self, execution_id: str):
        """执行开始"""
        self.status_bar.showMessage(f"执行已开始: {execution_id}")
        
        # 更新工具栏按钮状态
        self.start_action.setEnabled(False)   # 禁用开始按钮
        self.stop_action.setEnabled(True)     # 启用停止按钮
        self.pause_action.setEnabled(True)    # 启用暂停按钮
        self.resume_action.setEnabled(False)  # 禁用继续按钮（执行开始时）
        self.skip_action.setEnabled(True)     # 启用跳过按钮
    
    def _on_execution_finished(self, execution_id: str, success: bool):
        """执行完成"""
        status = "成功" if success else "失败"
        self.status_bar.showMessage(f"执行{status}: {execution_id}", 5000)
        
        # 更新工具栏按钮状态
        self.start_action.setEnabled(True)    # 启用开始按钮
        self.stop_action.setEnabled(False)    # 禁用停止按钮
        self.pause_action.setEnabled(False)   # 禁用暂停按钮
        self.resume_action.setEnabled(False)  # 禁用继续按钮
        self.skip_action.setEnabled(False)    # 禁用跳过按钮
        
        # 刷新结果查看器（如果有权限）
        if self.can_view_results:
            self.result_viewer.refresh()
        
        # 刷新统计仪表板（开发版本已隐藏）
        # self.dashboard.refresh()
    
    def _on_execution_paused(self, execution_id: str):
        """执行暂停"""
        self.status_bar.showMessage(f"执行已暂停: {execution_id}", 3000)
        
        # 更新工具栏按钮状态
        self.pause_action.setEnabled(False)   # 禁用暂停按钮
        self.resume_action.setEnabled(True)   # 启用继续按钮
        self.stop_action.setEnabled(True)     # 保持停止按钮启用
        
        self.logger.info(f"Execution paused: {execution_id}, resume button enabled")
    
    def _on_execution_resumed(self, execution_id: str):
        """执行恢复"""
        self.status_bar.showMessage(f"执行已恢复: {execution_id}", 3000)
        
        # 更新工具栏按钮状态
        self.pause_action.setEnabled(True)    # 启用暂停按钮
        self.resume_action.setEnabled(False)  # 禁用继续按钮
        self.stop_action.setEnabled(True)     # 保持停止按钮启用
        
        self.logger.info(f"Execution resumed: {execution_id}, pause button enabled")
    
    def _on_result_selected(self, execution_id: str):
        """结果被选中"""
        self.status_bar.showMessage(f"查看执行结果: {execution_id}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出应用程序吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.logger.info("Application closing")
            event.accept()
        else:
            event.ignore()
    
    def set_current_user(self, user_info: dict):
        """设置当前登录用户并应用权限
        
        Args:
            user_info: 用户信息字典
        """
        self.current_user = user_info
        
        # 获取用户权限
        user_data = user_info.get('user', {})
        role = user_data.get('role', '')
        
        from AppCode.utils.constants import UserRole
        self.is_super_admin = (role == UserRole.SUPER_ADMIN)
        
        # 检查查看结果权限
        self.can_view_results = self.user_service.can_view_results()
        
        # 应用权限设置
        self._apply_permissions()
        
        # 更新状态栏
        username = user_data.get('username', 'Unknown')
        role_text = "超级管理员" if self.is_super_admin else "普通用户"
        self.status_bar.showMessage(f"当前用户: {username} ({role_text})")
        
        self.logger.info(f"User logged in: {username}, role: {role}, can_view_results: {self.can_view_results}")
    
    def _disable_all_functions(self):
        """禁用所有功能（登录前状态）"""
        # 禁用工具栏按钮
        if hasattr(self, 'start_action'):
            self.start_action.setEnabled(False)
        if hasattr(self, 'stop_action'):
            self.stop_action.setEnabled(False)
        if hasattr(self, 'pause_action'):
            self.pause_action.setEnabled(False)
        if hasattr(self, 'resume_action'):
            self.resume_action.setEnabled(False)
        if hasattr(self, 'retry_action'):
            self.retry_action.setEnabled(False)
        if hasattr(self, 'skip_action'):
            self.skip_action.setEnabled(False)
        
        # 禁用脚本浏览器
        if hasattr(self, 'script_browser'):
            self.script_browser.setEnabled(False)
        
        # 禁用所有标签页
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setEnabled(False)
    
    def _apply_permissions(self):
        """根据用户权限应用功能访问控制"""
        # 启用基本功能
        if hasattr(self, 'start_action'):
            self.start_action.setEnabled(True)
        if hasattr(self, 'retry_action'):
            self.retry_action.setEnabled(True)
        
        # 启用脚本浏览器
        if hasattr(self, 'script_browser'):
            self.script_browser.setEnabled(True)
        
        # 启用执行控制面板
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setEnabled(True)
        
        # 根据权限控制标签页可见性
        if hasattr(self, 'tab_widget'):
            # 执行结果标签页：根据权限显示/隐藏
            if not self.can_view_results:
                # 隐藏执行结果标签页
                self.tab_widget.removeTab(self.result_tab_index)
                self.logger.info("Result viewer tab hidden (no permission)")
            else:
                self.logger.info("Result viewer tab visible (has permission)")
            
            # 用户管理标签页：仅超级管理员可见
            if not self.is_super_admin:
                # 找到用户管理标签页的当前索引并移除
                for i in range(self.tab_widget.count()):
                    if self.tab_widget.tabText(i) == "用户管理":
                        self.tab_widget.removeTab(i)
                        self.logger.info("User management tab hidden (not super admin)")
                        break
            else:
                self.logger.info("User management tab visible (super admin)")