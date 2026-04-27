"""
更新提示对话框
显示更新信息并提供下载选项
"""

import webbrowser
from typing import Optional, Dict, Any

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QCheckBox, QGroupBox,
    QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QIcon

from AppCode.services.update_service import get_update_service


class UpdateDialog(QDialog):
    """更新提示对话框"""
    
    def __init__(self, update_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("发现新版本")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # 主布局
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 标题区域
        title_layout = self._create_title_section()
        layout.addLayout(title_layout)
        
        # 版本信息区域
        version_group = self._create_version_section()
        layout.addWidget(version_group)
        
        # 更新说明区域
        notes_group = self._create_notes_section()
        layout.addWidget(notes_group)
        
        # 选项区域
        options_layout = self._create_options_section()
        layout.addLayout(options_layout)
        
        # 按钮区域
        button_layout = self._create_button_section()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def _create_title_section(self) -> QHBoxLayout:
        """创建标题区域"""
        layout = QHBoxLayout()
        
        # 图标（可选）
        # icon_label = QLabel()
        # icon_label.setPixmap(QIcon(":/icons/update.png").pixmap(48, 48))
        # layout.addWidget(icon_label)
        
        # 标题文本
        title_label = QLabel("🎉 发现新版本！")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        return layout
    
    def _create_version_section(self) -> QGroupBox:
        """创建版本信息区域"""
        group = QGroupBox("版本信息")
        layout = QVBoxLayout()
        
        # 当前版本
        current_version = self.update_info.get('current_version', 'Unknown')
        current_label = QLabel(f"当前版本: <b>{current_version}</b>")
        layout.addWidget(current_label)
        
        # 最新版本
        latest_version = self.update_info.get('latest_version', 'Unknown')
        is_prerelease = self.update_info.get('is_prerelease', False)
        prerelease_tag = " (预发布版本)" if is_prerelease else ""
        latest_label = QLabel(f"最新版本: <b style='color: #2196F3;'>{latest_version}</b>{prerelease_tag}")
        layout.addWidget(latest_label)
        
        # 发布日期
        release_date = self.update_info.get('release_date', 'Unknown')
        if release_date and release_date != 'Unknown':
            # 格式化日期
            try:
                from datetime import datetime
                date_obj = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
                date_label = QLabel(f"发布日期: {formatted_date}")
                layout.addWidget(date_label)
            except Exception:
                pass
        
        group.setLayout(layout)
        return group
    
    def _create_notes_section(self) -> QGroupBox:
        """创建更新说明区域"""
        group = QGroupBox("更新说明")
        layout = QVBoxLayout()
        
        # 更新说明文本框
        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        self.notes_text.setMinimumHeight(200)
        
        # 设置更新说明内容
        release_notes = self.update_info.get('release_notes', '暂无更新说明')
        # PyQt5使用setPlainText或setHtml，不支持setMarkdown
        self.notes_text.setPlainText(release_notes)
        
        layout.addWidget(self.notes_text)
        
        group.setLayout(layout)
        return group
    
    def _create_options_section(self) -> QHBoxLayout:
        """创建选项区域"""
        layout = QHBoxLayout()
        
        # 不再提示复选框
        self.dont_show_checkbox = QCheckBox("不再提示此版本")
        self.dont_show_checkbox.setToolTip("勾选后将不再提示此版本的更新")
        layout.addWidget(self.dont_show_checkbox)
        
        layout.addStretch()
        
        return layout
    
    def _create_button_section(self) -> QHBoxLayout:
        """创建按钮区域"""
        layout = QHBoxLayout()
        
        layout.addStretch()
        
        # 稍后提醒按钮
        self.later_button = QPushButton("稍后提醒")
        self.later_button.clicked.connect(self.on_later_clicked)
        layout.addWidget(self.later_button)
        
        # 查看详情按钮
        self.details_button = QPushButton("查看详情")
        self.details_button.clicked.connect(self.on_details_clicked)
        layout.addWidget(self.details_button)
        
        # 立即下载按钮
        self.download_button = QPushButton("立即下载")
        self.download_button.setDefault(True)
        self.download_button.clicked.connect(self.on_download_clicked)
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        layout.addWidget(self.download_button)
        
        return layout
    
    def on_later_clicked(self):
        """稍后提醒按钮点击"""
        if self.dont_show_checkbox.isChecked():
            # 保存不再提示的设置
            self._save_skip_version()
        self.reject()
    
    def on_details_clicked(self):
        """查看详情按钮点击"""
        html_url = self.update_info.get('html_url', '')
        if html_url:
            webbrowser.open(html_url)
        else:
            QMessageBox.warning(self, "提示", "无法获取详情页面地址")
    
    def on_download_clicked(self):
        """立即下载按钮点击"""
        download_url = self.update_info.get('download_url', '')
        
        if not download_url:
            QMessageBox.warning(self, "提示", "无法获取下载地址")
            return
        
        # 打开下载页面
        try:
            webbrowser.open(download_url)
            
            # 提示用户
            QMessageBox.information(
                self,
                "下载提示",
                "已在浏览器中打开下载页面。\n\n"
                "下载完成后，请关闭当前程序并运行新版本的安装程序。"
            )
            
            if self.dont_show_checkbox.isChecked():
                self._save_skip_version()
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"打开下载页面失败: {str(e)}"
            )
    
    def _save_skip_version(self):
        """保存跳过的版本号"""
        try:
            import json
            from pathlib import Path
            
            config_file = Path("config/update_config.json")
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 读取现有配置
            config = {}
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 保存跳过的版本
            config['skip_version'] = self.update_info.get('latest_version')
            
            # 写入配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"保存跳过版本配置失败: {e}")


def show_update_dialog(parent=None, force_check: bool = False) -> Optional[QDialog]:
    """
    显示更新对话框
    
    Args:
        parent: 父窗口
        force_check: 是否强制检查更新
    
    Returns:
        对话框实例，如果没有更新则返回None
    """
    try:
        # 检查更新
        service = get_update_service()
        update_info = service.check_for_updates(force=force_check)

        if update_info is None:
            if force_check:
                QMessageBox.warning(
                    parent,
                    "检查更新",
                    "无法获取更新信息，请检查网络连接后重试。"
                )
            return None

        # 检查是否出错
        if update_info.get('error'):
            if force_check:
                error_msg = update_info.get('error_message', '无法连接到GitHub服务器')
                QMessageBox.warning(
                    parent,
                    "检查更新失败",
                    f"{error_msg}\n\n请检查网络连接或稍后重试。"
                )
            return None

        # 没有更新
        if not update_info.get('has_update'):
            if force_check:
                current = update_info.get('current_version', '')
                QMessageBox.information(
                    parent,
                    "检查更新",
                    f"当前已是最新版本！\n版本: v{current}"
                )
            return None

        # 检查是否跳过此版本
        if not force_check and _should_skip_version(update_info.get('latest_version')):
            return None

        # 显示更新对话框
        dialog = UpdateDialog(update_info, parent)
        dialog.exec_()
        return dialog

    except Exception as e:
        if force_check:
            QMessageBox.critical(
                parent,
                "错误",
                f"检查更新时发生错误: {str(e)}"
            )
        return None


def _should_skip_version(version: str) -> bool:
    """检查是否应该跳过此版本"""
    try:
        import json
        from pathlib import Path
        
        config_file = Path("config/update_config.json")
        if not config_file.exists():
            return False
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        skip_version = config.get('skip_version')
        return skip_version == version
        
    except Exception:
        return False