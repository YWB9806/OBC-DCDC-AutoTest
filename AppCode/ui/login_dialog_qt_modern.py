"""现代化PyQt5登录对话框

美化的用户登录界面。
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from AppCode.services.user_service import UserService


class LoginDialog(QDialog):
    """现代化登录对话框"""
    
    # 登录成功信号
    login_success = pyqtSignal(dict)  # 传递登录结果
    
    def __init__(self, user_service: UserService, parent=None):
        """初始化登录对话框
        
        Args:
            user_service: 用户服务
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.user_service = user_service
        self.login_result = None
        
        self.setWindowTitle("用户登录")
        self.setFixedSize(500, 480)
        self.setModal(True)
        
        # 禁用关闭按钮
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        self._init_ui()
        
        # 设置焦点
        self.username_edit.setFocus()
    
    def _init_ui(self):
        """初始化UI"""
        # 设置背景色
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f2f5;
            }
        """)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(0)
        
        # 创建中心容器
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 16px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(40, 40, 40, 40)
        container_layout.setSpacing(20)
        
        # 标题区域
        title_label = QLabel("Python脚本批量执行工具")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setFixedHeight(50)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: #2c3e50;
            padding: 10px;
        """)
        container_layout.addWidget(title_label)
        
        container_layout.addSpacing(20)
        
        # 用户名
        username_label = QLabel("用户名")
        username_font = QFont()
        username_font.setPointSize(11)
        username_font.setBold(True)
        username_label.setFont(username_font)
        username_label.setFixedHeight(30)
        username_label.setStyleSheet("color: #495057; padding: 5px 0px; font-weight: 600;")
        username_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        container_layout.addWidget(username_label)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        username_edit_font = QFont()
        username_edit_font.setPointSize(11)
        self.username_edit.setFont(username_edit_font)
        self.username_edit.setFixedHeight(45)
        self.username_edit.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: #f8f9fa;
                color: #2c3e50;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
                background-color: white;
            }
            QLineEdit:hover {
                border-color: #b0b0b0;
            }
        """)
        self.username_edit.returnPressed.connect(self._on_login)
        container_layout.addWidget(self.username_edit)
        
        # 密码
        password_label = QLabel("密码")
        password_font = QFont()
        password_font.setPointSize(11)
        password_font.setBold(True)
        password_label.setFont(password_font)
        password_label.setFixedHeight(30)
        password_label.setStyleSheet("color: #495057; padding: 5px 0px; font-weight: 600;")
        password_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        container_layout.addWidget(password_label)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("请输入密码")
        password_edit_font = QFont()
        password_edit_font.setPointSize(11)
        self.password_edit.setFont(password_edit_font)
        self.password_edit.setFixedHeight(45)
        self.password_edit.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: #f8f9fa;
                color: #2c3e50;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
                background-color: white;
            }
            QLineEdit:hover {
                border-color: #b0b0b0;
            }
        """)
        self.password_edit.returnPressed.connect(self._on_login)
        container_layout.addWidget(self.password_edit)
        
        # 错误提示
        self.error_label = QLabel("")
        error_font = QFont()
        error_font.setPointSize(10)
        self.error_label.setFont(error_font)
        self.error_label.setWordWrap(True)
        self.error_label.setFixedHeight(0)
        self.error_label.setStyleSheet("""
            color: #d32f2f;
            background-color: #ffebee;
            padding: 10px;
            border-radius: 4px;
            border-left: 3px solid #d32f2f;
        """)
        self.error_label.hide()
        container_layout.addWidget(self.error_label)
        
        container_layout.addSpacing(10)
        
        # 登录按钮
        self.login_btn = QPushButton("登录")
        login_btn_font = QFont()
        login_btn_font.setPointSize(12)
        login_btn_font.setBold(True)
        self.login_btn.setFont(login_btn_font)
        self.login_btn.setFixedHeight(48)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px;
                font-size: 15px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5568d3, stop:1 #6a3f8f);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a5bc4, stop:1 #5d3680);
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """)
        self.login_btn.clicked.connect(self._on_login)
        self.login_btn.setDefault(True)
        container_layout.addWidget(self.login_btn)
        
        # 退出按钮
        self.exit_btn = QPushButton("退出")
        exit_btn_font = QFont()
        exit_btn_font.setPointSize(12)
        self.exit_btn.setFont(exit_btn_font)
        self.exit_btn.setFixedHeight(48)
        self.exit_btn.setCursor(Qt.PointingHandCursor)
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #6c757d;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 14px;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #667eea;
                color: #667eea;
            }
            QPushButton:pressed {
                background-color: #e9ecef;
            }
        """)
        self.exit_btn.clicked.connect(self._on_exit)
        container_layout.addWidget(self.exit_btn)
        
        main_layout.addWidget(container)
    
    def _on_login(self):
        """登录按钮点击事件"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        # 清空错误提示
        self.error_label.setFixedHeight(0)
        self.error_label.hide()
        self.error_label.setText("")
        
        # 验证输入
        if not username:
            self._show_error("请输入用户名")
            self.username_edit.setFocus()
            return
        
        if not password:
            self._show_error("请输入密码")
            self.password_edit.setFocus()
            return
        
        # 禁用按钮
        self.login_btn.setEnabled(False)
        self.login_btn.setText("登录中...")
        self.exit_btn.setEnabled(False)
        
        try:
            # 尝试登录
            result = self.user_service.login(username, password)
            
            if result['success']:
                self.login_result = result
                self.login_success.emit(result)
                self.accept()
            else:
                error_msg = result.get('error', '登录失败')
                if 'Invalid username or password' in error_msg:
                    self._show_error("用户名或密码错误")
                elif 'disabled' in error_msg:
                    self._show_error("账户已被禁用")
                else:
                    self._show_error(error_msg)
                
                self.password_edit.clear()
                self.password_edit.setFocus()
                
                # 重新启用按钮
                self.login_btn.setEnabled(True)
                self.login_btn.setText("登录")
                self.exit_btn.setEnabled(True)
        
        except Exception as e:
            self._show_error(f"登录错误: {str(e)}")
            self.login_btn.setEnabled(True)
            self.login_btn.setText("登录")
            self.exit_btn.setEnabled(True)
    
    def _show_error(self, message: str):
        """显示错误信息"""
        self.error_label.setText(message)
        self.error_label.setFixedHeight(50)
        self.error_label.show()
    
    def _on_exit(self):
        """退出按钮点击事件"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出应用程序吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.reject()
            import sys
            sys.exit(0)
    
    def get_result(self):
        """获取登录结果"""
        return self.login_result
    
    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() == Qt.Key_Escape:
            event.ignore()
        else:
            super().keyPressEvent(event)