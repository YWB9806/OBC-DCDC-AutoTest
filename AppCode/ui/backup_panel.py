"""备份管理面板

提供数据库备份和恢复的UI界面。
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QInputDialog, QLabel
)
from PyQt5.QtCore import Qt, QTimer


class BackupPanel(QWidget):
    """备份管理面板组件"""
    
    def __init__(self, container, parent=None):
        """初始化备份管理面板
        
        Args:
            container: 依赖注入容器
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.container = container
        self.logger = container.resolve('log_manager').get_logger('ui')
        self.backup_service = container.resolve('backup_service')
        
        self._init_ui()
        self._refresh_backup_list()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 控制按钮组
        control_group = QGroupBox("备份操作")
        control_layout = QHBoxLayout()
        
        self.create_backup_btn = QPushButton("创建备份")
        self.create_backup_btn.clicked.connect(self._on_create_backup)
        control_layout.addWidget(self.create_backup_btn)
        
        self.restore_backup_btn = QPushButton("恢复备份")
        self.restore_backup_btn.clicked.connect(self._on_restore_backup)
        self.restore_backup_btn.setEnabled(False)
        control_layout.addWidget(self.restore_backup_btn)
        
        self.delete_backup_btn = QPushButton("删除备份")
        self.delete_backup_btn.clicked.connect(self._on_delete_backup)
        self.delete_backup_btn.setEnabled(False)
        control_layout.addWidget(self.delete_backup_btn)
        
        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.clicked.connect(self._refresh_backup_list)
        control_layout.addWidget(self.refresh_btn)
        
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 自动备份设置组
        auto_backup_group = QGroupBox("自动备份设置")
        auto_backup_layout = QHBoxLayout()
        
        self.auto_backup_status_label = QLabel("状态: 未启用")
        auto_backup_layout.addWidget(self.auto_backup_status_label)
        
        self.start_auto_backup_btn = QPushButton("启动自动备份")
        self.start_auto_backup_btn.clicked.connect(self._on_start_auto_backup)
        auto_backup_layout.addWidget(self.start_auto_backup_btn)
        
        self.stop_auto_backup_btn = QPushButton("停止自动备份")
        self.stop_auto_backup_btn.clicked.connect(self._on_stop_auto_backup)
        self.stop_auto_backup_btn.setEnabled(False)
        auto_backup_layout.addWidget(self.stop_auto_backup_btn)
        
        auto_backup_layout.addStretch()
        
        auto_backup_group.setLayout(auto_backup_layout)
        layout.addWidget(auto_backup_group)
        
        # 备份列表
        list_group = QGroupBox("备份列表")
        list_layout = QVBoxLayout()
        
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(4)
        self.backup_table.setHorizontalHeaderLabels(["备份名称", "大小", "创建时间", "描述"])
        self.backup_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.backup_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.backup_table.itemSelectionChanged.connect(self._on_selection_changed)
        list_layout.addWidget(self.backup_table)
        
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
    
    def _refresh_backup_list(self):
        """刷新备份列表"""
        try:
            backups = self.backup_service.list_backups()
            
            self.backup_table.setRowCount(0)
            
            for backup in backups:
                row = self.backup_table.rowCount()
                self.backup_table.insertRow(row)
                
                # 备份名称
                self.backup_table.setItem(row, 0, QTableWidgetItem(backup['name']))
                
                # 大小（转换为MB）
                size_mb = backup['size'] / (1024 * 1024)
                self.backup_table.setItem(row, 1, QTableWidgetItem(f"{size_mb:.2f} MB"))
                
                # 创建时间
                created_time = backup['created_time'].replace('T', ' ')[:19]
                self.backup_table.setItem(row, 2, QTableWidgetItem(created_time))
                
                # 描述
                self.backup_table.setItem(row, 3, QTableWidgetItem(backup.get('description', '')))
            
            self.logger.info(f"Backup list refreshed: {len(backups)} backups")
        
        except Exception as e:
            self.logger.error(f"Error refreshing backup list: {e}")
            QMessageBox.critical(self, "错误", f"刷新备份列表失败: {e}")
    
    def _on_create_backup(self):
        """创建备份按钮点击"""
        try:
            # 询问备份描述
            description, ok = QInputDialog.getText(
                self,
                "创建备份",
                "请输入备份描述（可选）:"
            )
            
            if not ok:
                return
            
            # 创建备份
            result = self.backup_service.create_backup(description=description)
            
            if result['success']:
                QMessageBox.information(
                    self,
                    "成功",
                    f"备份创建成功!\n\n"
                    f"备份名称: {result['backup_name']}\n"
                    f"备份大小: {result['backup_size'] / (1024 * 1024):.2f} MB"
                )
                self._refresh_backup_list()
            else:
                QMessageBox.critical(
                    self,
                    "错误",
                    f"备份创建失败: {result.get('error')}"
                )
        
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            QMessageBox.critical(self, "错误", f"创建备份时出错: {e}")
    
    def _on_restore_backup(self):
        """恢复备份按钮点击"""
        try:
            selected_rows = self.backup_table.selectedItems()
            if not selected_rows:
                return
            
            row = selected_rows[0].row()
            backup_name = self.backup_table.item(row, 0).text()
            
            # 确认恢复
            reply = QMessageBox.question(
                self,
                "确认恢复",
                f"确定要恢复备份 '{backup_name}' 吗?\n\n"
                "警告: 当前数据库将被覆盖!",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # 恢复备份
            result = self.backup_service.restore_backup(backup_name)
            
            if result['success']:
                QMessageBox.information(
                    self,
                    "成功",
                    "备份恢复成功!\n\n请重启应用程序以使更改生效。"
                )
            else:
                QMessageBox.critical(
                    self,
                    "错误",
                    f"备份恢复失败: {result.get('error')}"
                )
        
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            QMessageBox.critical(self, "错误", f"恢复备份时出错: {e}")
    
    def _on_delete_backup(self):
        """删除备份按钮点击"""
        try:
            selected_rows = self.backup_table.selectedItems()
            if not selected_rows:
                return
            
            row = selected_rows[0].row()
            backup_name = self.backup_table.item(row, 0).text()
            
            # 确认删除
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除备份 '{backup_name}' 吗?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # 删除备份
            result = self.backup_service.delete_backup(backup_name)
            
            if result['success']:
                QMessageBox.information(self, "成功", "备份删除成功!")
                self._refresh_backup_list()
            else:
                QMessageBox.critical(
                    self,
                    "错误",
                    f"备份删除失败: {result.get('error')}"
                )
        
        except Exception as e:
            self.logger.error(f"Error deleting backup: {e}")
            QMessageBox.critical(self, "错误", f"删除备份时出错: {e}")
    
    def _on_start_auto_backup(self):
        """启动自动备份按钮点击"""
        try:
            # 询问备份间隔
            interval, ok = QInputDialog.getInt(
                self,
                "自动备份设置",
                "请输入备份间隔（小时）:",
                24,  # 默认值
                1,   # 最小值
                168  # 最大值（7天）
            )
            
            if not ok:
                return
            
            # 启动自动备份
            self.backup_service.start_auto_backup(interval_hours=interval)
            
            self.auto_backup_status_label.setText(f"状态: 已启用 (间隔: {interval}小时)")
            self.start_auto_backup_btn.setEnabled(False)
            self.stop_auto_backup_btn.setEnabled(True)
            
            QMessageBox.information(
                self,
                "成功",
                f"自动备份已启动!\n\n备份间隔: {interval}小时"
            )
        
        except Exception as e:
            self.logger.error(f"Error starting auto backup: {e}")
            QMessageBox.critical(self, "错误", f"启动自动备份时出错: {e}")
    
    def _on_stop_auto_backup(self):
        """停止自动备份按钮点击"""
        try:
            self.backup_service.stop_auto_backup()
            
            self.auto_backup_status_label.setText("状态: 未启用")
            self.start_auto_backup_btn.setEnabled(True)
            self.stop_auto_backup_btn.setEnabled(False)
            
            QMessageBox.information(self, "成功", "自动备份已停止!")
        
        except Exception as e:
            self.logger.error(f"Error stopping auto backup: {e}")
            QMessageBox.critical(self, "错误", f"停止自动备份时出错: {e}")
    
    def _on_selection_changed(self):
        """选择变化事件"""
        has_selection = len(self.backup_table.selectedItems()) > 0
        self.restore_backup_btn.setEnabled(has_selection)
        self.delete_backup_btn.setEnabled(has_selection)