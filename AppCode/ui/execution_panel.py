"""执行控制面板

用于控制脚本执行和显示执行进度。
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QProgressBar, QLabel, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QTextCursor
from datetime import datetime
import threading


class ExecutionPanel(QWidget):
    """执行控制面板组件"""

    # 信号定义
    execution_started = pyqtSignal(str)  # 执行开始
    execution_finished = pyqtSignal(str, bool)  # 执行完成(execution_id, success)

    # 控制按钮信号
    refresh_requested = pyqtSignal()  # 请求刷新
    start_requested = pyqtSignal()  # 请求开始执行
    stop_requested = pyqtSignal()  # 请求停止执行
    
    def __init__(self, container, parent=None):
        """初始化执行控制面板
        
        Args:
            container: 依赖注入容器
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.container = container
        self.logger = container.resolve('log_manager').get_logger('ui')
        self.execution_service = container.resolve('execution_service')
        
        self._current_execution_id = None
        self._current_batch_id = None
        self._is_executing = False
        self._displayed_lines = {}  # 记录每个执行ID已显示的行数
        self._start_time = None  # 记录开始时间
        self._is_stopping = False  # 标记是否正在停止
        self.current_suite = None  # 当前测试方案
        
        self._init_ui()
        
        # 创建定时器用于更新执行状态
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_execution_status)
        self._update_timer.setInterval(1000)  # 1秒更新一次
        self._last_update_time = {}  # 记录每个脚本的最后更新时间，避免频繁更新
        
        # 创建定时器用于更新时间显示
        self._time_timer = QTimer()
        self._time_timer.timeout.connect(self._update_time_display)
        self._time_timer.setInterval(1000)  # 每秒更新一次
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # ========== 控制按钮区域（最上方）==========
        control_group = QGroupBox("执行控制")
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setToolTip("刷新脚本列表 (F5)")
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        control_layout.addWidget(self.refresh_btn)

        control_layout.addWidget(QLabel("|"))  # 分隔符

        # 开始执行按钮
        self.start_btn = QPushButton("▶ 开始执行")
        self.start_btn.setToolTip("开始执行选中的脚本 (F9)")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_btn.clicked.connect(self._on_start_clicked)
        control_layout.addWidget(self.start_btn)

        # 停止执行按钮
        self.stop_btn = QPushButton("停止执行")
        self.stop_btn.setToolTip("停止当前执行 (Shift+F9)")
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        control_layout.addWidget(self.stop_btn)


        control_layout.addWidget(QLabel("|"))  # 分隔符

        # 跳过当前按钮
        self.skip_btn = QPushButton("跳过当前")
        self.skip_btn.setToolTip("跳过当前正在执行的脚本 (Ctrl+K)")
        self.skip_btn.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold;")
        self.skip_btn.setEnabled(False)
        self.skip_btn.clicked.connect(self._on_skip_clicked)
        control_layout.addWidget(self.skip_btn)

        control_layout.addStretch()  # 弹性空间

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # ========== 执行进度组 ==========
        progress_group = QGroupBox("执行进度")
        progress_layout = QVBoxLayout()

        # 总体进度
        progress_info_layout = QHBoxLayout()
        progress_info_layout.addWidget(QLabel("总体进度:"))

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_info_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("0/0")
        progress_info_layout.addWidget(self.progress_label)

        progress_layout.addLayout(progress_info_layout)

        # 状态信息
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("状态:"))
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        status_layout.addWidget(QLabel("已用时间:"))
        self.time_label = QLabel("00:00:00")
        status_layout.addWidget(self.time_label)

        progress_layout.addLayout(status_layout)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # ========== 数据统计模块（移到进度下方）==========
        stats_group = QGroupBox("数据统计")
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)  # 设置间距

        # 当前状态
        stats_layout.addWidget(QLabel("当前状态:"))
        self.status_label_main = QLabel("空闲中")
        self.status_label_main.setStyleSheet("font-weight: bold; color: green;")
        stats_layout.addWidget(self.status_label_main)

        # 分隔符
        stats_layout.addWidget(QLabel("|"))

        # 已选脚本
        stats_layout.addWidget(QLabel("已选脚本:"))
        self.selected_count_label = QLabel("0 个")
        stats_layout.addWidget(self.selected_count_label)

        # 分隔符
        stats_layout.addWidget(QLabel("|"))

        # 成功
        stats_layout.addWidget(QLabel("成功:"))
        self.success_count_label = QLabel("0 个")
        self.success_count_label.setStyleSheet("color: green;")
        stats_layout.addWidget(self.success_count_label)

        # 失败
        stats_layout.addWidget(QLabel("失败:"))
        self.failed_count_label = QLabel("0 个")
        self.failed_count_label.setStyleSheet("color: red;")
        stats_layout.addWidget(self.failed_count_label)

        # 待判定
        stats_layout.addWidget(QLabel("待判定:"))
        self.pending_count_label = QLabel("0 个")
        self.pending_count_label.setStyleSheet("color: orange;")
        stats_layout.addWidget(self.pending_count_label)

        # 分隔符
        stats_layout.addWidget(QLabel("|"))

        # 通过率
        stats_layout.addWidget(QLabel("本轮通过率:"))
        self.pass_rate_label = QLabel("0.0%")
        self.pass_rate_label.setStyleSheet("font-weight: bold;")
        stats_layout.addWidget(self.pass_rate_label)

        # 分隔符
        stats_layout.addWidget(QLabel("|"))

        # 预估时间
        stats_layout.addWidget(QLabel("预估剩余时间:"))
        self.eta_label = QLabel("--:--")
        stats_layout.addWidget(self.eta_label)

        # 弹性空间
        stats_layout.addStretch()

        # 清空按钮
        self.clear_btn = QPushButton("清空输出")
        self.clear_btn.clicked.connect(self._on_clear_output)
        stats_layout.addWidget(self.clear_btn)

        # 保留这些标签用于兼容性（隐藏不显示）
        self.suite_label = QLabel("未选择")
        self.suite_label.setVisible(False)
        self.concurrency_label = QLabel("1")
        self.concurrency_label.setVisible(False)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # ========== 执行列表 ==========
        list_group = QGroupBox("执行列表")
        list_layout = QVBoxLayout()

        self.execution_table = QTableWidget()
        self.execution_table.setColumnCount(5)
        self.execution_table.setHorizontalHeaderLabels(["脚本名称", "状态", "进度", "耗时", "结果"])
        self.execution_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.execution_table.setSelectionBehavior(QTableWidget.SelectRows)
        list_layout.addWidget(self.execution_table)

        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # ========== 输出日志 ==========
        output_group = QGroupBox("执行输出")
        output_layout = QVBoxLayout()

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
    
    def start_execution(self, script_paths: list):
        """开始执行脚本
        
        Args:
            script_paths: 脚本路径列表
        """
        if self._is_executing:
            QMessageBox.warning(self, "警告", "已有执行任务正在进行中")
            return
        
        if not script_paths:
            QMessageBox.warning(self, "警告", "没有选择要执行的脚本")
            return
        
        # 去重并记录日志
        unique_paths = list(dict.fromkeys(script_paths))  # 保持顺序的去重
        if len(unique_paths) != len(script_paths):
            self.logger.warning(f"Removed {len(script_paths) - len(unique_paths)} duplicate scripts")
            script_paths = unique_paths
        
        self.logger.info(f"Starting execution for {len(script_paths)} scripts")
        for i, path in enumerate(script_paths, 1):
            self.logger.debug(f"  {i}. {path}")
        
        try:
            # 清空之前的输出
            self.output_text.clear()
            self.execution_table.setRowCount(0)
            self._displayed_lines = {}  # 重置已显示行数记录
            self._start_time = datetime.now()  # 记录开始时间
            self._is_stopping = False  # 重置停止标记
            self._last_update_time = {}  # 重置更新时间记录
            
            # 优化：禁用UI更新，批量添加完成后再刷新
            self.execution_table.setUpdatesEnabled(False)
            
            try:
                # 初始化执行列表
                for script_path in script_paths:
                    row = self.execution_table.rowCount()
                    self.execution_table.insertRow(row)
                    
                    import os
                    script_name = os.path.basename(script_path)
                    
                    self.execution_table.setItem(row, 0, QTableWidgetItem(script_name))
                    self.execution_table.setItem(row, 1, QTableWidgetItem("等待中"))
                    self.execution_table.setItem(row, 2, QTableWidgetItem("0%"))
                    self.execution_table.setItem(row, 3, QTableWidgetItem("-"))
                    self.execution_table.setItem(row, 4, QTableWidgetItem("-"))
            finally:
                # 恢复UI更新
                self.execution_table.setUpdatesEnabled(True)
            
            # 获取当前方案信息
            suite_id = None
            suite_name = None
            if self.current_suite:
                suite_id = self.current_suite.get('id')
                suite_name = self.current_suite.get('name')
            
            # 开始批量执行
            if len(script_paths) == 1:
                result = self.execution_service.execute_single_script(
                    script_paths[0],
                    suite_id=suite_id,
                    suite_name=suite_name
                )
                self._current_execution_id = result.get('execution_id')
            else:
                result = self.execution_service.execute_batch_scripts(
                    script_paths,
                    suite_id=suite_id,
                    suite_name=suite_name
                )
                self._current_batch_id = result.get('batch_id')
            
            if result['success']:
                self._is_executing = True
                self.status_label.setText("执行中...")
                self.status_label_main.setText("执行中...")
                self.status_label_main.setStyleSheet("font-weight: bold; color: blue;")
                
                # 更新统计
                self.selected_count_label.setText(f"{len(script_paths)} 个")
                self._update_statistics()
                
                # 启动更新定时器
                self._update_timer.start()
                self._time_timer.start()
                
                # 发送信号
                exec_id = self._current_execution_id or self._current_batch_id
                self.execution_started.emit(exec_id)
                
                self._append_output(f"开始执行 {len(script_paths)} 个脚本...")
                self.logger.info(f"Execution started: {exec_id}")
                self.logger.info(f"Execution started for {len(script_paths)} scripts")
            else:
                error = result.get('error', 'Unknown error')
                QMessageBox.critical(self, "错误", f"启动执行失败: {error}")
                self.logger.error(f"Failed to start execution: {error}")
        
        except Exception as e:
            self.logger.error(f"Error starting execution: {e}")
            QMessageBox.critical(self, "错误", f"启动执行时出错: {e}")
    
    def stop_execution(self):
        """停止执行（改进版 - 完全异步）"""
        if not self._is_executing or self._is_stopping:
            return
        
        try:
            self._is_stopping = True
            
            exec_id = self._current_execution_id or self._current_batch_id
            if exec_id:
                self._append_output("正在停止执行...", QColor(255, 165, 0))
                self.logger.info(f"Stopping execution: {exec_id}")
                
                # 禁用停止按钮，防止重复点击
                if hasattr(self, 'parent') and callable(self.parent):
                    parent = self.parent()
                    if parent and hasattr(parent, 'stop_action'):
                        parent.stop_action.setEnabled(False)
                
                # 使用完全异步的方式执行取消
                import threading
                cancel_thread = threading.Thread(
                    target=self._do_cancel_execution_async,
                    args=(exec_id,),
                    daemon=True,
                    name="CancelExecutionThread"
                )
                cancel_thread.start()
                
                # 不等待线程完成，立即返回
                # 取消结果会通过回调更新UI
        
        except Exception as e:
            self.logger.error(f"Error stopping execution: {e}", exc_info=True)
            self._append_output(f"停止执行时出错: {e}", QColor(255, 0, 0))
            self._is_stopping = False
            self._enable_stop_button()
    
    def _do_cancel_execution_async(self, exec_id: str):
        """异步执行取消操作（在独立线程中运行）"""
        try:
            self.logger.info(f"Cancel thread started for: {exec_id}")
            
            # 直接调用取消服务，不设置超时
            result = self.execution_service.cancel_execution(exec_id)
            
            # 使用PyQt5信号槽机制更新UI（线程安全）
            if result['success']:
                # 使用QTimer在主线程中执行
                QTimer.singleShot(0, self._on_cancel_success)
            else:
                error_msg = result.get('error', 'Unknown error')
                # 使用lambda传递参数
                QTimer.singleShot(0, lambda: self._on_cancel_failed(error_msg))
        
        except Exception as e:
            self.logger.error(f"Error in cancel execution: {e}", exc_info=True)
            # 使用lambda传递参数
            QTimer.singleShot(0, lambda: self._on_cancel_failed(str(e)))
    
    def _on_cancel_success(self):
        """取消成功回调（在UI线程中执行）"""
        self._append_output("执行已停止", QColor(0, 128, 0))
        self.logger.info("Execution stopped successfully")
        self._enable_stop_button()

    def _on_cancel_failed(self, error_msg: str):
        """取消失败回调（在UI线程中执行）"""
        self._append_output(f"停止执行失败: {error_msg}", QColor(255, 0, 0))
        self.logger.warning(f"Failed to stop execution: {error_msg}")
        self._is_stopping = False
        self._enable_stop_button()

    def _enable_stop_button(self):
        """重新启用停止按钮"""
        if hasattr(self, 'parent') and callable(self.parent):
            parent = self.parent()
            if parent and hasattr(parent, 'stop_action'):
                parent.stop_action.setEnabled(True)
    
    def _update_execution_status(self):
        """更新执行状态（优化版 - 增量更新）"""
        # 如果不在执行中，或者正在停止，跳过更新
        if not self._is_executing or self._is_stopping:
            return

        try:
            exec_id = self._current_execution_id or self._current_batch_id
            if not exec_id:
                return

            # 获取执行状态
            if self._current_batch_id:
                status = self.execution_service.get_batch_status(self._current_batch_id)
                # 更新批次中每个脚本的状态
                executions = status.get('executions', [])

                # 优化：改进状态更新逻辑（修复状态不更新问题）
                current_time = datetime.now()
                for i, execution in enumerate(executions):
                    if i < self.execution_table.rowCount():
                        exec_status = execution.get('status')
                        exec_id_item = execution.get('id')

                        # 获取上次更新时间和上次状态
                        last_update = self._last_update_time.get(exec_id_item, None)
                        last_status_key = f"{exec_id_item}_last_status"
                        last_status = self._last_update_time.get(last_status_key, None)

                        # 判断是否需要更新
                        status_changed = last_status != exec_status
                        is_running = exec_status == 'RUNNING'
                        is_pending = exec_status == 'PENDING'
                        is_completed = exec_status in ['SUCCESS', 'FAILED', 'ERROR', 'TIMEOUT', 'CANCELLED']

                        # 完成状态立即更新，状态变化立即更新，运行中每秒更新，等待中每2秒更新
                        should_update = (
                            is_completed or  # 完成状态立即更新
                            status_changed or  # 状态变化立即更新
                            (is_running and (last_update is None or (current_time - last_update).total_seconds() >= 1.0)) or  # 运行中每秒更新
                            (is_pending and (last_update is None or (current_time - last_update).total_seconds() >= 2.0))  # 等待中每2秒更新
                        )

                        if should_update:
                            self._update_table_row(i, execution)
                            self._last_update_time[exec_id_item] = current_time
                            self._last_update_time[last_status_key] = exec_status  # 记录上次状态

                            # 只更新正在运行或刚完成的脚本的输出
                            if exec_status in ['RUNNING', 'SUCCESS', 'FAILED', 'ERROR', 'TIMEOUT']:
                                if exec_id_item:
                                    script_name = execution.get('script_path', '').split('/')[-1].split('\\')[-1]
                                    self._update_output(exec_id_item, script_name)
                
                # 更新统计信息（降低频率）
                self._update_statistics()
                
                # 计算总体进度
                total = len(executions)
                completed = sum(1 for e in executions if e.get('status') in ['SUCCESS', 'FAILED', 'CANCELLED'])
                if total > 0:
                    progress = int((completed / total) * 100)
                    self.progress_bar.setValue(progress)
                    self.progress_label.setText(f"{completed}/{total}")
                
                # 检查批次是否完成
                batch_status = status.get('status', 'RUNNING')
            else:
                # 单个脚本执行
                status = self.execution_service.get_execution_status(self._current_execution_id)
                if self.execution_table.rowCount() > 0:
                    self._update_table_row(0, status)
                
                progress = status.get('progress', 0)
                self.progress_bar.setValue(int(progress))
                self.progress_label.setText(f"{progress}%")
                
                # 获取并显示输出
                script_name = status.get('script_path', '').split('/')[-1].split('\\')[-1]
                self._update_output(self._current_execution_id, script_name)
                
                # 更新统计信息
                self._update_statistics()
                
                batch_status = status.get('status', 'RUNNING')
            
            # 更新状态标签
            status_text_map = {
                'PENDING': '等待中',
                'RUNNING': '执行中',
                'SUCCESS': '成功',
                'FAILED': '失败',
                'CANCELLED': '已取消',
                'PAUSED': '已暂停',
                'UNKNOWN': '未知'
            }
            self.status_label.setText(status_text_map.get(batch_status, batch_status))
            
            # 检查是否完成
            if batch_status in ['SUCCESS', 'FAILED', 'CANCELLED']:
                self._finish_execution(batch_status == 'SUCCESS')
        
        except Exception as e:
            self.logger.error(f"Error updating execution status: {e}", exc_info=True)
    
    def _update_table_row(self, row: int, execution_info: dict):
        """更新表格行
        
        Args:
            row: 行号
            execution_info: 执行信息
        """
        try:
            status = execution_info.get('status', 'UNKNOWN')
            progress = execution_info.get('progress', 0)
            
            # 状态映射
            status_text_map = {
                'PENDING': '等待中',
                'RUNNING': '执行中',
                'SUCCESS': '成功',
                'FAILED': '失败',
                'CANCELLED': '已取消',
                'PAUSED': '已暂停',
                'UNKNOWN': '未知'
            }
            
            # 更新状态
            status_item = QTableWidgetItem(status_text_map.get(status, status))
            if status == 'SUCCESS':
                status_item.setForeground(QColor(0, 128, 0))
            elif status == 'FAILED':
                status_item.setForeground(QColor(255, 0, 0))
            elif status == 'RUNNING':
                status_item.setForeground(QColor(0, 0, 255))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.execution_table.setItem(row, 1, status_item)
            
            # 更新进度
            progress_item = QTableWidgetItem(f"{progress}%")
            progress_item.setTextAlignment(Qt.AlignCenter)
            self.execution_table.setItem(row, 2, progress_item)
            
            # 更新耗时 - 修复 fromisoformat 错误
            start_time = execution_info.get('start_time')
            end_time = execution_info.get('end_time')
            
            if start_time and end_time:
                # 处理可能是字符串或datetime对象的情况
                if isinstance(start_time, str):
                    start = datetime.fromisoformat(start_time)
                elif isinstance(start_time, datetime):
                    start = start_time
                else:
                    return  # 无效的时间格式
                
                if isinstance(end_time, str):
                    end = datetime.fromisoformat(end_time)
                elif isinstance(end_time, datetime):
                    end = end_time
                else:
                    return  # 无效的时间格式
                
                duration = (end - start).total_seconds()
                duration_item = QTableWidgetItem(f"{duration:.1f}s")
                duration_item.setTextAlignment(Qt.AlignCenter)
                self.execution_table.setItem(row, 3, duration_item)
            elif start_time and status == 'RUNNING':
                # 正在运行，显示已用时间
                if isinstance(start_time, str):
                    start = datetime.fromisoformat(start_time)
                elif isinstance(start_time, datetime):
                    start = start_time
                else:
                    return
                
                duration = (datetime.now() - start).total_seconds()
                duration_item = QTableWidgetItem(f"{duration:.1f}s")
                duration_item.setTextAlignment(Qt.AlignCenter)
                self.execution_table.setItem(row, 3, duration_item)
            
            # ⭐ 修复关键点：放宽结果更新条件，包含RUNNING状态
            # 对于高进度的RUNNING状态也提取并显示结果
            if status in ['RUNNING', 'SUCCESS', 'FAILED', 'CANCELLED', 'TIMEOUT', 'ERROR']:
                from AppCode.utils.constants import TestResult
                test_result = self._extract_test_result(execution_info)
                
                # 只有当结果不是UNKNOWN时才更新，避免覆盖已有的有效结果
                if test_result != TestResult.UNKNOWN:
                    result_item = QTableWidgetItem(test_result)
                    
                    # 根据结果设置颜色
                    if test_result == TestResult.PASS:
                        result_item.setForeground(QColor(0, 128, 0))  # 绿色
                    elif test_result == TestResult.FAIL:
                        result_item.setForeground(QColor(255, 0, 0))  # 红色
                    elif test_result == TestResult.PENDING:
                        result_item.setForeground(QColor(255, 165, 0))  # 橙色
                    elif test_result == TestResult.ERROR:
                        result_item.setForeground(QColor(139, 0, 0))  # 深红色
                    elif test_result == TestResult.TIMEOUT:
                        result_item.setForeground(QColor(128, 0, 128))  # 紫色
                    
                    result_item.setTextAlignment(Qt.AlignCenter)
                    self.execution_table.setItem(row, 4, result_item)
        
        except Exception as e:
            self.logger.error(f"Error updating table row: {e}", exc_info=True)
    
    def _update_output(self, exec_id: str, script_name: str = ""):
        """更新输出显示
        
        Args:
            exec_id: 执行ID
            script_name: 脚本名称
        """
        try:
            # 获取输出
            output_lines = self.execution_service.get_execution_output(exec_id)
            
            if output_lines:
                displayed_count = self._displayed_lines.get(exec_id, 0)
                
                # 只添加新的输出行
                new_lines = output_lines[displayed_count:]
                for line in new_lines:
                    # 添加时间戳和脚本名称前缀
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    prefix = f"[{timestamp}]"
                    if script_name:
                        prefix += f" [{script_name}]"
                    formatted_line = f"{prefix} {line}"
                    
                    # 检查是否包含测试结果
                    if '合格' in line or 'PASS' in line.upper():
                        self._append_output(formatted_line, QColor(0, 128, 0))
                    elif '不合格' in line or 'FAIL' in line.upper():
                        self._append_output(formatted_line, QColor(255, 0, 0))
                    elif 'ERROR' in line.upper() or ('错误' in line and '误差' not in line):
                        self._append_output(formatted_line, QColor(255, 0, 0))
                    elif 'WARNING' in line.upper() or '警告' in line:
                        self._append_output(formatted_line, QColor(255, 165, 0))
                    else:
                        self._append_output(formatted_line)
                
                # 更新已显示行数
                self._displayed_lines[exec_id] = len(output_lines)
        
        except Exception as e:
            self.logger.error(f"Error updating output: {e}", exc_info=True)
    
    def _extract_test_result(self, execution_info: dict) -> str:
        """从执行信息中提取测试结果 — 仅认定"合格"/"不合格"为最终结果"""
        try:
            from AppCode.utils.constants import TestResult

            status = execution_info.get('status')
            exec_id = execution_info.get('id')

            if status == 'TIMEOUT':
                return TestResult.TIMEOUT
            elif status == 'ERROR':
                return TestResult.ERROR
            elif status == 'CANCELLED':
                return TestResult.PENDING

            output_lines = []
            if exec_id:
                try:
                    output_lines = self.execution_service.get_execution_output(exec_id)
                except Exception:
                    output_lines = execution_info.get('output', [])
            else:
                output_lines = execution_info.get('output', [])

            # 只从输出中查找中文最终结果（从后往前）
            for line in reversed(output_lines):
                stripped = line.strip()
                if not stripped:
                    continue

                if '不合格' in stripped:
                    return TestResult.FAIL
                if '合格' in stripped:
                    return TestResult.PASS

            if status == 'RUNNING':
                return TestResult.UNKNOWN

            # 完成但没有明确的中文结果 → 待判定
            if status == 'SUCCESS':
                return TestResult.PENDING
            elif status == 'FAILED':
                return TestResult.FAIL

            return TestResult.UNKNOWN

        except Exception as e:
            self.logger.error(f"Error extracting test result: {e}")
            return TestResult.UNKNOWN
    
    def _finish_execution(self, success: bool):
        """完成执行
        
        Args:
            success: 是否成功
        """
        self._is_executing = False
        self._is_stopping = False
        
        # 停止更新定时器
        self._update_timer.stop()
        self._time_timer.stop()
        
        # 更新状态
        if success:
            self.status_label.setText("执行完成")
            self.status_label_main.setText("执行完成")
            self.status_label_main.setStyleSheet("font-weight: bold; color: green;")
            self._append_output("所有脚本执行完成", QColor(0, 128, 0))
        else:
            self.status_label.setText("执行失败")
            self.status_label_main.setText("执行失败")
            self.status_label_main.setStyleSheet("font-weight: bold; color: red;")
            self._append_output("执行失败或被取消", QColor(255, 0, 0))
        
        # 最终统计更新
        self._update_statistics()
        
        # 发送信号
        exec_id = self._current_execution_id or self._current_batch_id
        if exec_id:
            self.execution_finished.emit(exec_id, success)
        
        # 清空当前执行ID
        self._current_execution_id = None
        self._current_batch_id = None
        
        self.logger.info(f"Execution finished: success={success}")
    
    def _append_output(self, text: str, color: QColor = None):
        """追加输出文本
        
        Args:
            text: 文本内容
            color: 文本颜色
        """
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        if color:
            self.output_text.setTextColor(color)
        
        cursor.insertText(text + "\n")
        
        if color:
            self.output_text.setTextColor(QColor(0, 0, 0))
        
        self.output_text.setTextCursor(cursor)
        self.output_text.ensureCursorVisible()
    
    
    def _on_clear_output(self):
        """清空输出"""
        self.output_text.clear()
    
    def _update_time_display(self):
        """更新时间显示"""
        if self._start_time and self._is_executing:
            elapsed = datetime.now() - self._start_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            seconds = int(elapsed.total_seconds() % 60)
            self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def _update_statistics(self):
        """更新统计信息"""
        if not self._is_executing:
            return
        
        try:
            # 统计各种状态的脚本数
            success_count = 0
            failed_count = 0
            pending_count = 0
            error_count = 0
            timeout_count = 0
            
            for row in range(self.execution_table.rowCount()):
                result_item = self.execution_table.item(row, 4)
                if result_item:
                    result = result_item.text()
                    from AppCode.utils.constants import TestResult
                    if result == TestResult.PASS:
                        success_count += 1
                    elif result == TestResult.FAIL:
                        failed_count += 1
                    elif result == TestResult.PENDING:
                        pending_count += 1
                    elif result == TestResult.ERROR:
                        error_count += 1
                    elif result == TestResult.TIMEOUT:
                        timeout_count += 1
            
            # 更新标签
            self.success_count_label.setText(f"{success_count} 个")
            self.failed_count_label.setText(f"{failed_count} 个")
            self.pending_count_label.setText(f"{pending_count} 个")
            
            # 计算通过率
            total_completed = success_count + failed_count + error_count + timeout_count
            if total_completed > 0:
                pass_rate = (success_count / total_completed) * 100
                self.pass_rate_label.setText(f"{pass_rate:.1f}%")
                
                # 根据通过率设置颜色
                if pass_rate >= 90:
                    self.pass_rate_label.setStyleSheet("font-weight: bold; color: green;")
                elif pass_rate >= 70:
                    self.pass_rate_label.setStyleSheet("font-weight: bold; color: orange;")
                else:
                    self.pass_rate_label.setStyleSheet("font-weight: bold; color: red;")
            else:
                self.pass_rate_label.setText("0.0%")
            
            # 预估剩余时间
            total_scripts = self.execution_table.rowCount()
            if total_completed > 0 and total_completed < total_scripts:
                if self._start_time:
                    elapsed = (datetime.now() - self._start_time).total_seconds()
                    avg_time_per_script = elapsed / total_completed
                    remaining_scripts = total_scripts - total_completed
                    eta_seconds = int(avg_time_per_script * remaining_scripts)
                    
                    eta_minutes = eta_seconds // 60
                    eta_seconds = eta_seconds % 60
                    self.eta_label.setText(f"{eta_minutes:02d}:{eta_seconds:02d}")
            else:
                self.eta_label.setText("--:--")
        
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")

    # ========== 控制按钮回调方法 ==========
    def _on_refresh_clicked(self):
        """刷新按钮点击"""
        self.refresh_requested.emit()
        self.logger.info("Refresh requested from execution panel")

    def _on_start_clicked(self):
        """开始执行按钮点击"""
        self.start_requested.emit()
        self.logger.info("Start execution requested from execution panel")

    def _on_stop_clicked(self):
        """停止执行按钮点击"""
        self.stop_requested.emit()
        self.logger.info("Stop execution requested from execution panel")

    def _on_skip_clicked(self):
        """跳过当前脚本按钮点击"""
        if not self._is_executing:
            return

        try:
            exec_id = self._current_execution_id or self._current_batch_id
            if exec_id:
                self._append_output("正在跳过当前脚本...", QColor(255, 165, 0))
                self.logger.info(f"Skipping current script in execution: {exec_id}")

                # 如果是单个执行，直接取消
                if self._current_execution_id:
                    self.stop_execution()
                else:
                    # 批量执行：调用执行服务跳过当前脚本
                    result = self.execution_service.skip_current_script(exec_id)
                    if result.get('success'):
                        self._append_output("已跳过当前脚本", QColor(0, 128, 0))
                    else:
                        error = result.get('error', 'Unknown error')
                        self._append_output(f"跳过失败: {error}", QColor(255, 0, 0))

        except Exception as e:
            self.logger.error(f"Error skipping script: {e}", exc_info=True)
            self._append_output(f"跳过脚本时出错: {e}", QColor(255, 0, 0))

    def set_button_states(self, is_executing: bool):
        """设置按钮状态

        Args:
            is_executing: 是否正在执行
        """
        self.start_btn.setEnabled(not is_executing)
        self.stop_btn.setEnabled(is_executing)

    def set_suite_name(self, suite_name: str):
        """设置当前方案名称
        
        Args:
            suite_name: 方案名称
        """
        self.suite_label.setText(suite_name if suite_name else "未选择")
    
    def set_current_suite(self, suite: dict):
        """设置当前测试方案
        
        Args:
            suite: 方案信息字典，包含id和name
        """
        self.current_suite = suite
        if suite:
            self.set_suite_name(suite.get('name', '未知方案'))
        else:
            self.set_suite_name(None)