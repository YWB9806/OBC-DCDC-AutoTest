"""
设置对话框
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSpinBox, QCheckBox, QPushButton, QGroupBox,
                             QFormLayout, QMessageBox, QTabWidget, QWidget)
from PyQt5.QtCore import Qt
from AppCode.infrastructure.config_manager import ConfigManager


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("设置")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # 执行设置选项卡
        execution_tab = self.create_execution_tab()
        tab_widget.addTab(execution_tab, "执行设置")
        
        # 备份设置选项卡
        backup_tab = self.create_backup_tab()
        tab_widget.addTab(backup_tab, "备份设置")
        
        # 更新设置选项卡
        update_tab = self.create_update_tab()
        tab_widget.addTab(update_tab, "更新设置")
        
        layout.addWidget(tab_widget)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def create_execution_tab(self):
        """创建执行设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 执行设置组
        execution_group = QGroupBox("执行设置")
        execution_layout = QFormLayout()
        
        # 单脚本最大运行时间
        self.script_timeout_spinbox = QSpinBox()
        self.script_timeout_spinbox.setMinimum(60)  # 最小1分钟
        self.script_timeout_spinbox.setMaximum(86400)  # 最大24小时
        self.script_timeout_spinbox.setSuffix(" 秒")
        self.script_timeout_spinbox.setValue(3600)  # 默认1小时
        self.script_timeout_spinbox.setSingleStep(60)  # 步进60秒
        
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(self.script_timeout_spinbox)
        timeout_label = QLabel("(默认: 3600秒 = 1小时)")
        timeout_label.setStyleSheet("color: gray; font-size: 10px;")
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addStretch()
        
        execution_layout.addRow("单脚本最大运行时间:", timeout_layout)
        
        # 添加说明
        info_label = QLabel(
            "说明：当单个脚本运行时间超过设定值时，将自动停止该脚本并标记为超时。\n"
            "建议根据实际测试场景设置合理的超时时间。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 10px; padding: 10px;")
        execution_layout.addRow("", info_label)
        
        execution_group.setLayout(execution_layout)
        layout.addWidget(execution_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def create_backup_tab(self):
        """创建备份设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 备份设置组
        backup_group = QGroupBox("备份设置")
        backup_layout = QFormLayout()
        
        # 自动备份
        self.auto_backup_checkbox = QCheckBox("启用自动备份")
        backup_layout.addRow("", self.auto_backup_checkbox)
        
        # 备份间隔
        self.backup_interval_spinbox = QSpinBox()
        self.backup_interval_spinbox.setMinimum(3600)  # 最小1小时
        self.backup_interval_spinbox.setMaximum(604800)  # 最大7天
        self.backup_interval_spinbox.setSuffix(" 秒")
        self.backup_interval_spinbox.setValue(86400)  # 默认1天
        self.backup_interval_spinbox.setSingleStep(3600)  # 步进1小时
        backup_layout.addRow("备份间隔:", self.backup_interval_spinbox)
        
        # 最大备份数
        self.max_backups_spinbox = QSpinBox()
        self.max_backups_spinbox.setMinimum(1)
        self.max_backups_spinbox.setMaximum(100)
        self.max_backups_spinbox.setValue(10)
        backup_layout.addRow("最大备份数:", self.max_backups_spinbox)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def create_update_tab(self):
        """创建更新设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 更新设置组
        update_group = QGroupBox("更新设置")
        update_layout = QFormLayout()
        
        # 启动时检查更新
        self.check_update_checkbox = QCheckBox("启动时自动检查更新")
        update_layout.addRow("", self.check_update_checkbox)
        
        update_group.setLayout(update_layout)
        layout.addWidget(update_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def load_settings(self):
        """加载设置"""
        try:
            # 执行设置
            script_timeout = self.config_manager.get('execution.script_timeout', 3600)
            self.script_timeout_spinbox.setValue(script_timeout)
            
            # 备份设置
            auto_backup = self.config_manager.get('backup.auto_backup', True)
            self.auto_backup_checkbox.setChecked(auto_backup)
            
            backup_interval = self.config_manager.get('backup.backup_interval', 86400)
            self.backup_interval_spinbox.setValue(backup_interval)
            
            max_backups = self.config_manager.get('backup.max_backups', 10)
            self.max_backups_spinbox.setValue(max_backups)
            
            # 更新设置
            check_update = self.config_manager.get('update.check_on_startup', True)
            self.check_update_checkbox.setChecked(check_update)
            
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载设置失败: {e}")
            
    def save_settings(self):
        """保存设置"""
        try:
            # 执行设置
            script_timeout = self.script_timeout_spinbox.value()
            self.config_manager.set('execution.script_timeout', script_timeout)
            self.config_manager.set('execution.timeout', script_timeout)  # 保持兼容性
            
            # 备份设置
            self.config_manager.set('backup.auto_backup', self.auto_backup_checkbox.isChecked())
            self.config_manager.set('backup.backup_interval', self.backup_interval_spinbox.value())
            self.config_manager.set('backup.max_backups', self.max_backups_spinbox.value())
            
            # 更新设置
            self.config_manager.set('update.check_on_startup', self.check_update_checkbox.isChecked())
            
            # 保存到文件
            self.config_manager.save()
            
            QMessageBox.information(self, "成功", "设置已保存，部分设置将在重启后生效。")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败: {e}")