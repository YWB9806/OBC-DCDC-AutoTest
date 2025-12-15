"""结果查看器

用于查看和分析执行结果。
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QTextEdit,
    QSplitter, QLabel, QComboBox, QDateEdit, QGroupBox,
    QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QColor
import csv
import json
from datetime import datetime


class ResultViewer(QWidget):
    """结果查看器组件"""
    
    # 信号定义
    result_selected = pyqtSignal(str)  # 结果被选中
    
    def __init__(self, container, parent=None):
        """初始化结果查看器
        
        Args:
            container: 依赖注入容器
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.container = container
        self.logger = container.resolve('log_manager').get_logger('ui')
        self.execution_service = container.resolve('execution_service')
        self.analysis_service = container.resolve('analysis_service')
        self.suite_service = container.resolve('test_suite_service')
        
        self._all_results = []  # 存储所有结果
        
        self._init_ui()
        self._load_suites()
        self._load_results()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 过滤器组
        filter_group = QGroupBox("筛选条件")
        filter_layout = QVBoxLayout()
        
        # 第一行：日期和状态
        row1_layout = QHBoxLayout()
        
        row1_layout.addWidget(QLabel("开始日期:"))
        self.start_date = QDateEdit()
        # 修复：默认显示今天的数据，而不是30天前
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        # 移除自动触发
        # self.start_date.dateChanged.connect(self._on_filter_changed)
        row1_layout.addWidget(self.start_date)
        
        row1_layout.addWidget(QLabel("结束日期:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        # 移除自动触发
        # self.end_date.dateChanged.connect(self._on_filter_changed)
        row1_layout.addWidget(self.end_date)
        
        row1_layout.addWidget(QLabel("状态:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["全部", "成功", "失败", "取消", "错误", "超时"])
        # 移除自动触发
        # self.status_combo.currentTextChanged.connect(self._on_filter_changed)
        row1_layout.addWidget(self.status_combo)
        
        row1_layout.addStretch()
        filter_layout.addLayout(row1_layout)
        
        # 第二行：测试方案和批次时间筛选
        row2_layout = QHBoxLayout()
        
        row2_layout.addWidget(QLabel("测试方案:"))
        self.suite_combo = QComboBox()
        self.suite_combo.addItem("-- 全部方案 --")
        self.suite_combo.currentIndexChanged.connect(self._on_suite_changed)
        row2_layout.addWidget(self.suite_combo)
        
        row2_layout.addWidget(QLabel("批次时间:"))
        self.batch_combo = QComboBox()
        self.batch_combo.addItem("-- 全部批次 --")
        row2_layout.addWidget(self.batch_combo)
        
        row2_layout.addStretch()
        
        # 添加应用筛选按钮
        self.apply_filter_btn = QPushButton("应用筛选")
        self.apply_filter_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.apply_filter_btn.clicked.connect(self._load_results)
        row2_layout.addWidget(self.apply_filter_btn)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh)
        row2_layout.addWidget(self.refresh_btn)
        
        self.export_csv_btn = QPushButton("导出CSV")
        self.export_csv_btn.clicked.connect(self._export_to_csv)
        row2_layout.addWidget(self.export_csv_btn)
        
        self.export_json_btn = QPushButton("导出JSON")
        self.export_json_btn.clicked.connect(self._export_to_json)
        row2_layout.addWidget(self.export_json_btn)
        
        filter_layout.addLayout(row2_layout)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # 分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 结果列表
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(8)
        self.result_table.setHorizontalHeaderLabels([
            "脚本名称", "测试方案", "批次时间", "测试结果", "状态", "开始时间", "耗时(秒)", "错误信息"
        ])
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.result_table.verticalHeader().setVisible(True)  # 显示行号
        splitter.addWidget(self.result_table)
        
        # 详细信息
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        
        detail_layout.addWidget(QLabel("执行详情:"))
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        detail_layout.addWidget(self.detail_text)
        
        splitter.addWidget(detail_widget)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # 统计信息
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("总计: 0 | 成功: 0 | 失败: 0")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
    
    def _load_suites(self):
        """加载测试方案列表"""
        try:
            suites = self.suite_service.list_suites()
            
            # 更新下拉框
            self.suite_combo.clear()
            self.suite_combo.addItem("-- 全部方案 --")
            
            for suite in suites:
                self.suite_combo.addItem(suite['name'], suite['id'])
            
            self.logger.info(f"Loaded {len(suites)} test suites for filtering")
        
        except Exception as e:
            self.logger.error(f"Error loading suites: {e}")
    
    def _load_results(self):
        """加载执行结果"""
        try:
            # 获取日期范围（确保包含完整的一天）
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            
            self.logger.info(f"Loading results with date range: {start_date} to {end_date}")
            
            # 获取状态过滤
            status_filter = self.status_combo.currentText()
            status_map = {
                "全部": None,
                "成功": "SUCCESS",
                "失败": "FAILED",
                "取消": "CANCELLED",
                "错误": "ERROR",
                "超时": "TIMEOUT"
            }
            status = status_map.get(status_filter)
            
            # 获取方案过滤
            suite_id = None
            if self.suite_combo.currentIndex() > 0:
                suite_id = self.suite_combo.currentData()
            
            # 获取执行历史
            results = self.execution_service.get_execution_history(
                status=status,
                start_date=start_date,
                end_date=end_date,
                suite_id=suite_id
            )
            
            self.logger.info(f"Found {len(results)} results matching criteria")
            
            # 先收集所有批次时间（在应用批次时间筛选之前）
            all_batch_times = set()
            for result in results:
                batch_id = result.get('batch_id', '')
                if batch_id and batch_id.startswith('batch_'):
                    try:
                        parts = batch_id.split('_')
                        if len(parts) >= 2:
                            timestamp_us = int(parts[1])
                            timestamp_s = timestamp_us / 1000000
                            dt = datetime.fromtimestamp(timestamp_s)
                            batch_time = dt.strftime('%H:%M:%S')
                            all_batch_times.add(batch_time)
                    except:
                        pass
                elif not batch_id:
                    # 如果没有batch_id，使用start_time
                    start_time = result.get('start_time', '')
                    if start_time:
                        try:
                            dt = datetime.fromisoformat(start_time.replace('T', ' ').split('.')[0])
                            batch_time = dt.strftime('%H:%M:%S')
                            all_batch_times.add(batch_time)
                        except:
                            pass
            
            # 更新批次时间下拉框（使用所有批次时间）
            self._update_batch_combo(all_batch_times)
            
            # 获取批次时间过滤
            batch_time_filter = None
            if self.batch_combo.currentIndex() > 0:
                batch_time_filter = self.batch_combo.currentText()
            
            # 应用批次时间过滤
            if batch_time_filter:
                filtered_results = []
                for result in results:
                    batch_id = result.get('batch_id', '')
                    if batch_id and batch_id.startswith('batch_'):
                        try:
                            parts = batch_id.split('_')
                            if len(parts) >= 2:
                                timestamp_us = int(parts[1])
                                timestamp_s = timestamp_us / 1000000
                                dt = datetime.fromtimestamp(timestamp_s)
                                batch_time = dt.strftime('%H:%M:%S')
                                if batch_time == batch_time_filter:
                                    filtered_results.append(result)
                        except:
                            pass
                results = filtered_results
            
            # 保存所有结果用于导出
            self._all_results = results
            
            # 更新表格
            self.result_table.setRowCount(0)
            
            success_count = 0
            failed_count = 0
            pass_count = 0
            fail_count = 0
            pending_count = 0
            
            # 收集显示结果的批次时间（用于验证）
            batch_times = set()
            
            for result in results:
                row = self.result_table.rowCount()
                self.result_table.insertRow(row)
                
                # 脚本名称
                import os
                script_path = result.get('script_path', '')
                script_name = os.path.basename(script_path) if script_path else ''
                name_item = QTableWidgetItem(script_name)
                name_item.setData(Qt.UserRole, result)  # 存储完整数据
                self.result_table.setItem(row, 0, name_item)
                
                # 测试方案
                suite_name = result.get('suite_name', '-')
                suite_item = QTableWidgetItem(suite_name)
                suite_item.setTextAlignment(Qt.AlignCenter)
                self.result_table.setItem(row, 1, suite_item)
                
                # 批次时间（从batch_id提取或使用start_time）
                batch_id = result.get('batch_id', '')
                batch_time = '-'
                if batch_id and batch_id.startswith('batch_'):
                    # batch_id格式：batch_1765560702018331_59635
                    # 提取时间戳部分（微秒）
                    try:
                        parts = batch_id.split('_')
                        if len(parts) >= 2:
                            timestamp_us = int(parts[1])
                            timestamp_s = timestamp_us / 1000000
                            dt = datetime.fromtimestamp(timestamp_s)
                            batch_time = dt.strftime('%H:%M:%S')
                    except:
                        pass
                
                if batch_time == '-':
                    # 如果无法从batch_id提取，使用start_time
                    start_time = result.get('start_time', '')
                    if start_time:
                        try:
                            dt = datetime.fromisoformat(start_time.replace('T', ' ').split('.')[0])
                            batch_time = dt.strftime('%H:%M:%S')
                        except:
                            pass
                
                batch_time_item = QTableWidgetItem(batch_time)
                batch_time_item.setTextAlignment(Qt.AlignCenter)
                self.result_table.setItem(row, 2, batch_time_item)
                
                # 测试结果 - 转换为中文显示（兼容中英文格式）
                test_result = result.get('test_result', '-')
                test_result_display = self._translate_test_result(test_result)
                test_result_item = QTableWidgetItem(test_result_display)
                
                # 统一判断逻辑，支持中英文格式
                if test_result in ['pass', '合格']:
                    test_result_item.setForeground(QColor(0, 200, 0))
                    pass_count += 1
                elif test_result in ['fail', '不合格']:
                    test_result_item.setForeground(QColor(255, 0, 0))
                    fail_count += 1
                elif test_result in ['pending', '待判定']:
                    test_result_item.setForeground(QColor(255, 165, 0))
                    pending_count += 1
                elif test_result in ['error', '错误', '执行错误']:
                    test_result_item.setForeground(QColor(139, 0, 0))
                elif test_result in ['timeout', '超时']:
                    test_result_item.setForeground(QColor(128, 0, 128))
                test_result_item.setTextAlignment(Qt.AlignCenter)
                self.result_table.setItem(row, 3, test_result_item)
                
                # 执行状态
                status = result.get('status', '')
                status_item = QTableWidgetItem(status)
                if status == 'SUCCESS':
                    status_item.setForeground(QColor(0, 128, 0))
                    success_count += 1
                elif status == 'FAILED':
                    status_item.setForeground(QColor(255, 0, 0))
                    failed_count += 1
                status_item.setTextAlignment(Qt.AlignCenter)
                self.result_table.setItem(row, 4, status_item)
                
                # 开始时间
                start_time = result.get('start_time', '')
                if start_time:
                    try:
                        dt = datetime.fromisoformat(start_time.replace('T', ' ').split('.')[0])
                        start_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                start_time_item = QTableWidgetItem(start_time)
                start_time_item.setTextAlignment(Qt.AlignCenter)
                self.result_table.setItem(row, 5, start_time_item)
                
                # 耗时
                duration = self._calculate_duration(result)
                duration_item = QTableWidgetItem(f"{duration:.2f}")
                duration_item.setTextAlignment(Qt.AlignCenter)
                self.result_table.setItem(row, 6, duration_item)
                
                # 错误信息
                error = result.get('error', '')
                self.result_table.setItem(row, 7, QTableWidgetItem(error[:50] if error else ''))
            
            # 更新统计信息
            total = len(results)
            pass_rate = (pass_count / total * 100) if total > 0 else 0
            self.stats_label.setText(
                f"总计: {total} | 成功: {success_count} | 失败: {failed_count} | "
                f"合格: {pass_count} | 不合格: {fail_count} | 待判定: {pending_count} | 合格率: {pass_rate:.1f}%"
            )
            
            self.logger.info(f"Loaded {total} execution results")
        
        except Exception as e:
            self.logger.error(f"Error loading results: {e}")
            QMessageBox.critical(self, "错误", f"加载结果失败: {e}")
    
    def _calculate_duration(self, result: dict) -> float:
        """计算执行时长
        
        Args:
            result: 执行结果
            
        Returns:
            时长（秒）
        """
        try:
            from datetime import datetime
            
            start_time = result.get('start_time')
            end_time = result.get('end_time')
            
            if start_time and end_time:
                start = datetime.fromisoformat(start_time)
                end = datetime.fromisoformat(end_time)
                return (end - start).total_seconds()
        except Exception:
            pass
        
        return 0.0
    
    def _translate_test_result(self, test_result: str) -> str:
        """将测试结果转换为中文显示（兼容中英文格式）
        
        Args:
            test_result: 测试结果（支持中文或英文）
            
        Returns:
            中文测试结果
        """
        # 如果已经是中文，直接返回
        if test_result in ['合格', '不合格', '待判定', '错误', '超时', '执行错误']:
            return test_result
        
        # 英文到中文的映射
        translation = {
            'pass': '合格',
            'fail': '不合格',
            'pending': '待判定',
            'error': '错误',
            'timeout': '超时',
            '-': '-'
        }
        return translation.get(test_result, test_result)
    
    def _update_batch_combo(self, batch_times: set):
        """更新批次时间下拉框
        
        Args:
            batch_times: 批次时间集合
        """
        current_batch = self.batch_combo.currentText()
        self.batch_combo.clear()
        self.batch_combo.addItem("-- 全部批次 --")
        
        # 按时间排序
        for batch_time in sorted(batch_times, reverse=True):
            self.batch_combo.addItem(batch_time)
        
        # 恢复之前的选择
        index = self.batch_combo.findText(current_batch)
        if index >= 0:
            self.batch_combo.setCurrentIndex(index)
    
    def _on_suite_changed(self):
        """测试方案改变时，重新加载批次列表"""
        # 先加载结果以获取批次信息
        self._load_results()
    
    def _on_selection_changed(self):
        """选择改变"""
        selected_items = self.result_table.selectedItems()
        
        if not selected_items:
            self.detail_text.clear()
            return
        
        # 获取选中行的脚本名称单元格（第1列，索引0）
        row = selected_items[0].row()
        result = self.result_table.item(row, 0).data(Qt.UserRole)
        
        if result:
            # 显示详细信息
            self._show_detail(result)
            
            # 发送信号
            self.result_selected.emit(result.get('id', ''))
    
    def _show_detail(self, result: dict):
        """显示详细信息
        
        Args:
            result: 执行结果
        """
        detail_lines = []
        
        detail_lines.append(f"执行ID: {result.get('id', '')}")
        detail_lines.append(f"脚本路径: {result.get('script_path', '')}")
        detail_lines.append(f"状态: {result.get('status', '')}")
        detail_lines.append(f"开始时间: {result.get('start_time', '')}")
        detail_lines.append(f"结束时间: {result.get('end_time', '')}")
        detail_lines.append(f"耗时: {self._calculate_duration(result):.2f} 秒")
        
        if result.get('params'):
            detail_lines.append(f"\n参数: {result.get('params')}")
        
        if result.get('output'):
            detail_lines.append(f"\n输出:\n{result.get('output')}")
        
        if result.get('error'):
            detail_lines.append(f"\n错误:\n{result.get('error')}")
        
        self.detail_text.setPlainText("\n".join(detail_lines))
    
    def _on_filter_changed(self):
        """过滤器改变"""
        self._load_results()
    
    def refresh(self):
        """刷新结果列表"""
        self._load_suites()
        self._load_results()
    
    def _export_to_csv(self):
        """导出为CSV"""
        if not self._all_results:
            QMessageBox.warning(self, "警告", "没有可导出的数据")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出CSV",
            f"execution_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # 写入表头
                writer.writerow([
                    '序号', '脚本路径', '测试方案', '批次时间', '测试结果', '执行状态',
                    '开始时间', '结束时间', '耗时(秒)', '错误信息'
                ])
                
                # 写入数据
                for idx, result in enumerate(self._all_results, 1):
                    duration = self._calculate_duration(result)
                    
                    # 提取批次时间
                    batch_id = result.get('batch_id', '')
                    batch_time = '-'
                    if batch_id and batch_id.startswith('batch_'):
                        try:
                            parts = batch_id.split('_')
                            if len(parts) >= 2:
                                timestamp_us = int(parts[1])
                                timestamp_s = timestamp_us / 1000000
                                dt = datetime.fromtimestamp(timestamp_s)
                                batch_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            batch_time = batch_id
                    
                    # 转换测试结果为中文
                    test_result = self._translate_test_result(result.get('test_result', '-'))
                    
                    writer.writerow([
                        idx,
                        result.get('script_path', ''),
                        result.get('suite_name', '-'),
                        batch_time,
                        test_result,
                        result.get('status', ''),
                        result.get('start_time', ''),
                        result.get('end_time', ''),
                        f"{duration:.2f}",
                        result.get('error', '')
                    ])
            
            QMessageBox.information(
                self, "成功",
                f"已导出 {len(self._all_results)} 条记录到:\n{file_path}"
            )
            self.logger.info(f"Exported {len(self._all_results)} results to CSV: {file_path}")
        
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            QMessageBox.critical(self, "错误", f"导出失败: {e}")
    
    def _export_to_json(self):
        """导出为JSON"""
        if not self._all_results:
            QMessageBox.warning(self, "警告", "没有可导出的数据")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出JSON",
            f"execution_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # 添加导出时间和统计信息
            export_data = {
                'export_time': datetime.now().isoformat(),
                'total_count': len(self._all_results),
                'filter_criteria': {
                    'start_date': self.start_date.date().toString("yyyy-MM-dd"),
                    'end_date': self.end_date.date().toString("yyyy-MM-dd"),
                    'status': self.status_combo.currentText(),
                    'suite': self.suite_combo.currentText()
                },
                'results': self._all_results
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(
                self, "成功",
                f"已导出 {len(self._all_results)} 条记录到:\n{file_path}"
            )
            self.logger.info(f"Exported {len(self._all_results)} results to JSON: {file_path}")
        
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {e}")
            QMessageBox.critical(self, "错误", f"导出失败: {e}")