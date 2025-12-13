"""统计仪表板

显示执行统计和分析数据。
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QTextEdit, QComboBox,
    QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from datetime import datetime


class Dashboard(QWidget):
    """统计仪表板组件"""
    
    def __init__(self, container, parent=None):
        """初始化统计仪表板
        
        Args:
            container: 依赖注入容器
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.container = container
        self.logger = container.resolve('log_manager').get_logger('ui')
        self.analysis_service = container.resolve('analysis_service')
        
        self._init_ui()
        self._load_statistics()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 控制栏
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("报告类型:"))
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems(["摘要报告", "详细报告", "趋势报告"])
        control_layout.addWidget(self.report_type_combo)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh)
        control_layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("导出报告")
        self.export_btn.clicked.connect(self.export_report)
        control_layout.addWidget(self.export_btn)
        
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # 统计卡片区域
        cards_layout = QHBoxLayout()
        
        # 总执行次数卡片
        self.total_card = self._create_stat_card("总执行次数", "0")
        cards_layout.addWidget(self.total_card)
        
        # 成功率卡片
        self.success_rate_card = self._create_stat_card("成功率", "0%")
        cards_layout.addWidget(self.success_rate_card)
        
        # 平均耗时卡片
        self.avg_time_card = self._create_stat_card("平均耗时", "0s")
        cards_layout.addWidget(self.avg_time_card)
        
        # 今日执行卡片
        self.today_card = self._create_stat_card("今日执行", "0")
        cards_layout.addWidget(self.today_card)
        
        layout.addLayout(cards_layout)
        
        # 详细统计组
        detail_group = QGroupBox("详细统计")
        detail_layout = QVBoxLayout()
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        detail_layout.addWidget(self.detail_text)
        
        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)
        
        # 报告预览组
        report_group = QGroupBox("报告预览")
        report_layout = QVBoxLayout()
        
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QFont("Courier New", 9))
        report_layout.addWidget(self.report_text)
        
        report_group.setLayout(report_layout)
        layout.addWidget(report_group)
    
    def _create_stat_card(self, title: str, value: str) -> QGroupBox:
        """创建统计卡片
        
        Args:
            title: 标题
            value: 值
            
        Returns:
            卡片组件
        """
        card = QGroupBox(title)
        layout = QVBoxLayout()
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setFont(QFont("Arial", 24, QFont.Bold))
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        card.value_label = value_label  # 保存引用以便更新
        
        return card
    
    def _load_statistics(self):
        """加载统计信息"""
        try:
            # 获取总体统计
            result = self.analysis_service.get_overall_statistics()
            
            if result['success']:
                stats = result['statistics']
                
                # 更新卡片
                self.total_card.value_label.setText(str(stats.get('total_executions', 0)))
                
                success_rate = stats.get('success_rate', 0)
                self.success_rate_card.value_label.setText(f"{success_rate:.1f}%")
                
                avg_duration = stats.get('average_duration', 0)
                self.avg_time_card.value_label.setText(f"{avg_duration:.1f}s")
                
                # 计算今日执行次数
                today_count = self._get_today_count(stats)
                self.today_card.value_label.setText(str(today_count))
                
                # 更新详细统计
                self._update_detail_stats(stats)
                
                # 生成报告
                self._generate_report()
                
                self.logger.info("Statistics loaded successfully")
            else:
                error = result.get('error', 'Unknown error')
                self.logger.error(f"Failed to load statistics: {error}")
        
        except Exception as e:
            self.logger.error(f"Error loading statistics: {e}")
    
    def _get_today_count(self, stats: dict) -> int:
        """获取今日执行次数
        
        Args:
            stats: 统计数据
            
        Returns:
            今日执行次数
        """
        today = datetime.now().strftime('%Y-%m-%d')
        daily_executions = stats.get('daily_executions', {})
        return daily_executions.get(today, 0)
    
    def _update_detail_stats(self, stats: dict):
        """更新详细统计
        
        Args:
            stats: 统计数据
        """
        lines = []
        
        lines.append("=== 执行统计 ===")
        lines.append(f"总执行次数: {stats.get('total_executions', 0)}")
        lines.append(f"成功: {stats.get('successful', 0)}")
        lines.append(f"失败: {stats.get('failed', 0)}")
        lines.append(f"取消: {stats.get('cancelled', 0)}")
        lines.append(f"成功率: {stats.get('success_rate', 0):.2f}%")
        lines.append("")
        
        lines.append("=== 性能指标 ===")
        lines.append(f"总耗时: {stats.get('total_duration', 0):.2f} 秒")
        lines.append(f"平均耗时: {stats.get('average_duration', 0):.2f} 秒")
        lines.append("")
        
        lines.append("=== 按状态分布 ===")
        scripts_by_status = stats.get('scripts_by_status', {})
        for status, count in scripts_by_status.items():
            lines.append(f"{status}: {count}")
        lines.append("")
        
        lines.append("=== 最常执行的脚本 (Top 10) ===")
        top_scripts = stats.get('top_scripts', [])
        for i, (script, count) in enumerate(top_scripts[:10], 1):
            import os
            script_name = os.path.basename(script)
            lines.append(f"{i}. {script_name}: {count} 次")
        
        self.detail_text.setPlainText("\n".join(lines))
    
    def _generate_report(self):
        """生成报告"""
        try:
            report_type_map = {
                "摘要报告": "summary",
                "详细报告": "detailed",
                "趋势报告": "trend"
            }
            
            report_type = report_type_map.get(
                self.report_type_combo.currentText(),
                "summary"
            )
            
            result = self.analysis_service.generate_report(report_type)
            
            if result['success']:
                self.report_text.setPlainText(result['content'])
            else:
                error = result.get('error', 'Unknown error')
                self.report_text.setPlainText(f"生成报告失败: {error}")
        
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            self.report_text.setPlainText(f"生成报告时出错: {e}")
    
    def refresh(self):
        """刷新统计数据"""
        self._load_statistics()
    
    def export_report(self):
        """导出报告"""
        try:
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出报告",
                f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "文本文件 (*.txt);;所有文件 (*.*)"
            )
            
            if not file_path:
                return
            
            # 获取报告内容
            report_content = self.report_text.toPlainText()
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            QMessageBox.information(self, "成功", f"报告已导出到: {file_path}")
            self.logger.info(f"Report exported to: {file_path}")
        
        except Exception as e:
            self.logger.error(f"Error exporting report: {e}")
            QMessageBox.critical(self, "错误", f"导出报告失败: {e}")