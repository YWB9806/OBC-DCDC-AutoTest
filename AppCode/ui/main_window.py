"""主窗口

应用程序的主界面窗口。
"""

import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QStatusBar, QMenuBar,
    QMenu, QAction, QToolBar, QMessageBox, QFileDialog,
    QSystemTrayIcon
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

from .script_browser import ScriptBrowser
from .execution_panel import ExecutionPanel
from .execution_queue_panel import ExecutionQueuePanel
from .result_viewer import ResultViewer
from .backup_panel import BackupPanel
from .report_panel import ReportPanel
from .user_panel import UserPanel
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
        self.setWindowTitle(f"富特科技-测试部-自动化测试软件 v{get_version_string()}")
        # 调整窗口大小：宽度改为800，适应小屏幕显示器
        self.setGeometry(100, 100, 800, 700)
        
        # 设置窗口图标
        icon_path = os.path.join('resources', 'app_icon.png')
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

        # 报告面板
        self.report_panel = ReportPanel(self.container, self)
        self.tab_widget.addTab(self.report_panel, "测试报告")

        # 用户管理面板（仅超级管理员可见）
        self.user_panel = UserPanel(self.container, self)
        self.user_tab_index = self.tab_widget.addTab(self.user_panel, "用户管理")

        # 备份管理面板（放在最右侧）
        self.backup_panel = BackupPanel(self.container, self)
        self.tab_widget.addTab(self.backup_panel, "数据备份")

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

        # 添加脚本（原"添加路径"中的单个文件功能）
        add_script_action = QAction("添加脚本(&S)", self)
        add_script_action.triggered.connect(self._on_menu_add_script)
        file_menu.addAction(add_script_action)

        # 添加目录（原"添加路径"中的文件夹功能）
        add_dir_action = QAction("添加目录(&D)", self)
        add_dir_action.triggered.connect(self._on_menu_add_directory)
        file_menu.addAction(add_dir_action)

        file_menu.addSeparator()

        refresh_action = QAction("刷新脚本(&R)", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._on_refresh_scripts)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 方案菜单
        suite_menu = menubar.addMenu("方案(&P)")

        save_suite_action = QAction("保存方案(&S)", self)
        save_suite_action.triggered.connect(self.script_browser._on_save_suite)
        suite_menu.addAction(save_suite_action)

        manage_suite_action = QAction("管理方案(&M)", self)
        manage_suite_action.triggered.connect(self.script_browser._on_manage_suites)
        suite_menu.addAction(manage_suite_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")

        settings_action = QAction("设置(&S)", self)
        settings_action.triggered.connect(self._on_settings)
        tools_menu.addAction(settings_action)

        # 插件菜单
        self.plugin_menu = menubar.addMenu("插件(&L)")
        self._refresh_plugin_menu()

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
        """创建工具栏（精简版 - 所有执行控制按钮已移到执行面板）"""
        # 不再创建工具栏，所有控制按钮都在执行面板中
        # 保留这些 action 的引用（用于状态更新）
        self.start_action = QAction("开始执行", self)
        self.stop_action = QAction("停止执行", self)
        self.pause_action = QAction("暂停", self)
        self.resume_action = QAction("继续", self)
        self.skip_action = QAction("跳过当前", self)
        self.retry_action = QAction("重试失败", self)

        # 设置初始状态
        self.start_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        self.pause_action.setEnabled(False)
        self.resume_action.setEnabled(False)
        self.skip_action.setEnabled(False)

    def _refresh_plugin_menu(self):
        """刷新插件菜单"""
        self.plugin_menu.clear()
        config_manager = self.container.resolve('config_manager')
        plugins = config_manager.get('plugins.items', [])

        if not plugins:
            empty_action = QAction("（无）", self)
            empty_action.setEnabled(False)
            self.plugin_menu.addAction(empty_action)
            return

        for plugin in plugins:
            name = plugin.get('name', '未知')
            path = plugin.get('path', '')
            if name and path:
                action = QAction(name, self)
                action.setToolTip(path)
                action.triggered.connect(lambda checked, p=path: self._on_launch_plugin(p))
                self.plugin_menu.addAction(action)

    def _on_launch_plugin(self, path):
        """启动外部插件"""
        import subprocess
        import os
        try:
            if os.path.exists(path):
                subprocess.Popen([path], shell=False)
                self.logger.info(f"Launched plugin: {path}")
                self.status_bar.showMessage(f"已启动: {os.path.basename(path)}", 3000)
            else:
                QMessageBox.warning(self, "警告", f"插件路径不存在:\n{path}")
        except Exception as e:
            self.logger.error(f"Failed to launch plugin {path}: {e}")
            QMessageBox.critical(self, "错误", f"启动插件失败: {e}")

    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 系统托盘图标（用于桌面通知）
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._tray_icon = QSystemTrayIcon(self)
            self._tray_icon.setIcon(self.windowIcon())
            self._tray_icon.show()
        else:
            self._tray_icon = None
    
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

        # 执行面板控制按钮信号
        self.execution_panel.refresh_requested.connect(self._on_refresh_scripts)
        self.execution_panel.start_requested.connect(self._on_execute_queue)
        self.execution_panel.stop_requested.connect(self._on_stop_execution)
        self.execution_panel.pause_requested.connect(self._on_pause_execution)
        self.execution_panel.resume_requested.connect(self._on_resume_execution)

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
            exec_id = self.execution_panel._current_execution_id or self.execution_panel._current_batch_id
            if not exec_id:
                QMessageBox.warning(self, "提示", "当前没有正在执行的脚本")
                return
            
            reply = QMessageBox.question(
                self,
                "确认跳过",
                "确定要跳过当前正在执行的脚本吗？\n跳过后将立即执行下一条脚本。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                result = self.execution_service.skip_current_script(exec_id)
                if result['success']:
                    self.logger.info(f"Skipped current script: {exec_id}")
                    self.status_bar.showMessage("已跳过当前脚本", 3000)
                else:
                    error_msg = result.get('error', '未知错误')
                    QMessageBox.warning(self, "警告", f"跳过失败: {error_msg}")
                    self.logger.warning(f"Failed to skip current script: {error_msg}")
        except Exception as e:
            self.logger.error(f"Error in skip current: {e}")
            QMessageBox.critical(self, "错误", f"跳过当前脚本时出错: {e}")
    
    def _on_settings(self):
        """打开设置对话框"""
        try:
            from .settings_dialog import SettingsDialog
            config_manager = self.container.resolve('config_manager')
            dialog = SettingsDialog(self, config_manager)
            if dialog.exec_():
                # 将新的超时设置动态应用到执行引擎
                engine = self.container.resolve('execution_engine')
                if engine:
                    engine.set_timeout(config_manager.get('execution.script_timeout', 3600))
                    engine.set_result_idle_timeout(config_manager.get('execution.result_idle_timeout', 5))
                self.logger.info("Settings saved and applied to engine")
                self.status_bar.showMessage("设置已保存", 3000)
                # 刷新插件菜单
                self._refresh_plugin_menu()
        except Exception as e:
            self.logger.error(f"Error opening settings: {e}")
            QMessageBox.critical(self, "错误", f"打开设置时出错: {e}")
    
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
        <h2>富特科技-测试部-自动化测试软件</h2>
        <p>版本: {get_version_string()}</p>
        <p>开发者: Yangwenbo</p>
        <p>联系方式: ywb9806@163.com</p>
        """
        QMessageBox.about(self, "关于", about_text)

    def _on_menu_add_script(self):
        """菜单栏 - 添加脚本文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Python脚本文件", "", "Python Files (*.py);;All Files (*)"
        )
        if file_path:
            self.script_browser._add_custom_script(file_path)

    def _on_menu_add_directory(self):
        """菜单栏 - 添加目录"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择脚本文件夹", "")
        if folder_path:
            self.script_browser._add_custom_folder_with_selection(folder_path)
    
    def _on_export_report(self):
        """导出报告"""
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "导出报告", "execution_report",
            "HTML Files (*.html);;CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            if selected_filter.startswith("HTML"):
                self._export_report_html(file_path)
            else:
                self._export_report_csv(file_path)

            QMessageBox.information(self, "成功", f"报告已导出到:\n{file_path}")
        except Exception as e:
            self.logger.error(f"Failed to export report: {e}")
            QMessageBox.critical(self, "错误", f"导出报告失败:\n{e}")

    def _export_report_html(self, file_path: str):
        """导出HTML格式报告"""
        import html as html_mod
        history_repo = self.container.resolve('execution_history_repository')
        records = history_repo.get_recent(100)

        rows_html = ""
        for r in records:
            status = r.get('status', '')
            color = "#4CAF50" if status == "SUCCESS" else "#F44336" if status == "FAILED" else "#FF9800"
            rows_html += f"""<tr>
                <td>{html_mod.escape(r.get('script_path', ''))}</td>
                <td style="color:{color};font-weight:bold">{html_mod.escape(status)}</td>
                <td>{html_mod.escape(r.get('start_time', ''))}</td>
                <td>{html_mod.escape(str(r.get('duration', '')))}</td>
                <td>{html_mod.escape(r.get('executed_by', ''))}</td>
            </tr>"""

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>执行报告</title>
<style>
body {{ font-family: "Microsoft YaHei", sans-serif; margin: 20px; }}
h1 {{ color: #333; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 15px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background-color: #2196F3; color: white; }}
tr:nth-child(even) {{ background-color: #f2f2f2; }}
.info {{ color: #666; margin-bottom: 10px; }}
</style>
</head>
<body>
<h1>Python脚本执行报告</h1>
<p class="info">生成时间: {html_mod.escape(str(__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')))}
&nbsp;&nbsp;共 {len(records)} 条记录</p>
<table>
<thead><tr><th>脚本路径</th><th>状态</th><th>执行时间</th><th>耗时(秒)</th><th>执行者</th></tr></thead>
<tbody>
{rows_html}
</tbody>
</table>
</body>
</html>"""

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _export_report_csv(self, file_path: str):
        """导出CSV格式报告"""
        import csv
        history_repo = self.container.resolve('execution_history_repository')
        records = history_repo.get_recent(500)

        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['脚本路径', '状态', '开始时间', '结束时间', '耗时(秒)', '执行者'])
            for r in records:
                writer.writerow([
                    r.get('script_path', ''),
                    r.get('status', ''),
                    r.get('start_time', ''),
                    r.get('end_time', ''),
                    r.get('duration', ''),
                    r.get('executed_by', '')
                ])
    
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

        # 更新执行面板按钮状态
        self.execution_panel.set_button_states(is_executing=True, is_paused=False)

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

        # 更新执行面板按钮状态
        self.execution_panel.set_button_states(is_executing=False, is_paused=False)

        # 窗口非活动时发送系统通知
        if self._tray_icon and not self.isActiveWindow():
            icon_type = QSystemTrayIcon.Information if success else QSystemTrayIcon.Critical
            self._tray_icon.showMessage(
                "脚本执行完成",
                f"执行{status}: {execution_id}",
                icon_type,
                5000
            )

        # 刷新结果查看器（如果有权限）
        if self.can_view_results:
            self.result_viewer.refresh()

    def _on_execution_paused(self, execution_id: str):
        """执行暂停"""
        self.status_bar.showMessage(f"执行已暂停: {execution_id}", 3000)

        # 更新工具栏按钮状态
        self.pause_action.setEnabled(False)   # 禁用暂停按钮
        self.resume_action.setEnabled(True)   # 启用继续按钮
        self.stop_action.setEnabled(True)     # 保持停止按钮启用

        # 更新执行面板按钮状态
        self.execution_panel.set_button_states(is_executing=True, is_paused=True)

        self.logger.info(f"Execution paused: {execution_id}, resume button enabled")

    def _on_execution_resumed(self, execution_id: str):
        """执行恢复"""
        self.status_bar.showMessage(f"执行已恢复: {execution_id}", 3000)

        # 更新工具栏按钮状态
        self.pause_action.setEnabled(True)    # 启用暂停按钮
        self.resume_action.setEnabled(False)  # 禁用继续按钮
        self.stop_action.setEnabled(True)     # 保持停止按钮启用

        # 更新执行面板按钮状态
        self.execution_panel.set_button_states(is_executing=True, is_paused=False)
        
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
            tabs_to_remove = []
            if not self.can_view_results:
                tabs_to_remove.append("执行结果")
            if not self.is_super_admin:
                tabs_to_remove.append("用户管理")

            # 从后往前移除，避免索引偏移
            for i in range(self.tab_widget.count() - 1, -1, -1):
                if self.tab_widget.tabText(i) in tabs_to_remove:
                    self.tab_widget.removeTab(i)