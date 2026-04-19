"""现代化PyQt5登录对话框

美化的用户登录界面。
"""

import sys
import traceback
import hashlib
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QIcon

from AppCode.services.user_service import UserService


class LoginWorker(QThread):
    """后台登录线程

    在线程中只做密码哈希验证（CPU密集型），避免阻塞UI。
    SQLite查询在主线程完成后传入线程，结果返回主线程处理。
    """
    verified = pyqtSignal(bool)  # 密码验证结果

    def __init__(self, password, password_hash):
        super().__init__()
        self.password = password
        self.password_hash = password_hash

    def run(self):
        try:
            if ':' in self.password_hash:
                salt_hex, key_hex = self.password_hash.split(':', 1)
                salt = bytes.fromhex(salt_hex)
                key = hashlib.pbkdf2_hmac('sha256', self.password.encode(), salt, 100000)
                match = key.hex() == key_hex
            else:
                match = hashlib.sha256(self.password.encode()).hexdigest() == self.password_hash
            self.verified.emit(match)
        except Exception:
            self.verified.emit(False)


class LoginDialog(QDialog):
    """现代化登录对话框"""

    def __init__(self, user_service: UserService, parent=None):
        super().__init__(parent)

        self.user_service = user_service
        self.login_result = None
        self._logging_in = False

        from version import get_version_string
        self.setWindowTitle(f"富特科技-测试部-自动化测试软件 v{get_version_string()}")

        # 设置窗口图标
        import os
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'app图标.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setFixedSize(460, 420)
        self.setModal(True)

        self._init_ui()
        self.username_edit.setFocus()

    def _init_ui(self):
        """初始化UI"""
        self.setStyleSheet("QDialog { background-color: #f0f2f5; }")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(0)

        container = QWidget()
        container.setFocusPolicy(Qt.NoFocus)
        container.setStyleSheet("QWidget { background-color: white; border-radius: 12px; }")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(30, 25, 30, 25)
        container_layout.setSpacing(10)

        # 标题
        title_label = QLabel("自动化测试软件")
        title_label.setFocusPolicy(Qt.NoFocus)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; padding: 2px;")
        container_layout.addWidget(title_label)

        subtitle_label = QLabel("富特科技-测试部")
        subtitle_label.setFocusPolicy(Qt.NoFocus)
        subtitle_font = QFont()
        subtitle_font.setPointSize(9)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        subtitle_label.setStyleSheet("color: #7f8c8d; padding-right: 5px;")
        container_layout.addWidget(subtitle_label)

        container_layout.addSpacing(8)

        # 用户名
        username_label = QLabel("用户名")
        username_label.setFocusPolicy(Qt.NoFocus)
        uf = QFont()
        uf.setPointSize(9)
        uf.setBold(True)
        username_label.setFont(uf)
        username_label.setStyleSheet("color: #495057; font-weight: 600;")
        container_layout.addWidget(username_label)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        uef = QFont()
        uef.setPointSize(9)
        self.username_edit.setFont(uef)
        self.username_edit.setFixedHeight(36)
        self.username_edit.setStyleSheet("""
            QLineEdit { padding: 6px 12px; border: 1px solid #d0d0d0; border-radius: 6px; background-color: #f8f9fa; color: #2c3e50; }
            QLineEdit:focus { border: 1px solid #667eea; background-color: white; }
            QLineEdit:hover { border-color: #a0a0a0; }
        """)
        self.username_edit.returnPressed.connect(self._on_login)
        container_layout.addWidget(self.username_edit)

        # 密码
        password_label = QLabel("密码")
        password_label.setFocusPolicy(Qt.NoFocus)
        pf = QFont()
        pf.setPointSize(9)
        pf.setBold(True)
        password_label.setFont(pf)
        password_label.setStyleSheet("color: #495057; font-weight: 600;")
        container_layout.addWidget(password_label)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("请输入密码")
        pef = QFont()
        pef.setPointSize(9)
        self.password_edit.setFont(pef)
        self.password_edit.setFixedHeight(36)
        self.password_edit.setStyleSheet("""
            QLineEdit { padding: 6px 12px; border: 1px solid #d0d0d0; border-radius: 6px; background-color: #f8f9fa; color: #2c3e50; }
            QLineEdit:focus { border: 1px solid #667eea; background-color: white; }
            QLineEdit:hover { border-color: #a0a0a0; }
        """)
        self.password_edit.returnPressed.connect(self._on_login)
        container_layout.addWidget(self.password_edit)

        # 错误提示
        self.error_label = QLabel("")
        self.error_label.setFocusPolicy(Qt.NoFocus)
        ef = QFont()
        ef.setPointSize(9)
        self.error_label.setFont(ef)
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color: #d32f2f; background-color: #ffebee; padding: 8px; border-radius: 4px; border-left: 3px solid #d32f2f;")
        self.error_label.hide()
        container_layout.addWidget(self.error_label)

        container_layout.addSpacing(5)

        # 登录按钮
        self.login_btn = QPushButton("登录")
        lbf = QFont()
        lbf.setPointSize(10)
        lbf.setBold(True)
        self.login_btn.setFont(lbf)
        self.login_btn.setFixedHeight(40)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2); color: white; border: none; border-radius: 6px; font-weight: 600; }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5568d3, stop:1 #6a3f8f); }
            QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4a5bc4, stop:1 #5d3680); }
            QPushButton:disabled { background-color: #cccccc; color: #888888; }
        """)
        self.login_btn.clicked.connect(self._on_login)
        self.login_btn.setDefault(True)
        container_layout.addWidget(self.login_btn)

        # 退出按钮
        self.exit_btn = QPushButton("退出")
        ebf = QFont()
        ebf.setPointSize(10)
        self.exit_btn.setFont(ebf)
        self.exit_btn.setFixedHeight(40)
        self.exit_btn.setCursor(Qt.PointingHandCursor)
        self.exit_btn.setStyleSheet("""
            QPushButton { background-color: white; color: #6c757d; border: 1px solid #d0d0d0; border-radius: 6px; font-weight: 500; }
            QPushButton:hover { background-color: #f8f9fa; border-color: #667eea; color: #667eea; }
            QPushButton:pressed { background-color: #e9ecef; }
        """)
        self.exit_btn.clicked.connect(self._on_exit)
        container_layout.addWidget(self.exit_btn)

        main_layout.addWidget(container)

    def _on_login(self):
        """登录按钮点击事件"""
        if self._logging_in:
            return

        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        # 清空错误提示
        self.error_label.setText("")
        self.error_label.hide()

        if not username:
            self._show_error("请输入用户名")
            self.username_edit.setFocus()
            return

        if not password:
            self._show_error("请输入密码")
            self.password_edit.setFocus()
            return

        # 设置状态
        self._logging_in = True
        self.login_btn.setEnabled(False)
        self.login_btn.setText("登录中...")
        self.exit_btn.setEnabled(False)

        # 保存凭据
        self._pending_username = username
        self._pending_password = password
        self._pending_user_id = None
        self._pending_user_info = None
        self._pending_is_active = True
        self._pending_is_sha256 = False

        # 第一步：在主线程中查数据库获取用户信息（快速，不阻塞UI）
        try:
            user = self.user_service.user_repo.get_by_username(username)
        except Exception:
            user = None

        if not user:
            self._login_failed("用户名或密码错误")
            return

        # 检查账户是否禁用（提前检查，不需要等密码验证）
        if not user.get('is_active', True):
            self._login_failed("账户已被禁用")
            return

        # 保存用户信息供验证通过后使用
        self._pending_user_id = user['id']
        self._pending_user_info = user
        self._pending_is_sha256 = ':' not in user['password_hash']

        # 第二步：在后台线程中验证密码（CPU密集型，不在主线程做）
        self._login_worker = LoginWorker(password, user['password_hash'])
        self._login_worker.verified.connect(self._on_password_verified)
        self._login_worker.start()

    @pyqtSlot(bool)
    def _on_password_verified(self, match):
        """密码验证完成回调（主线程）"""
        if not match:
            self._login_failed("用户名或密码错误")
            return

        # 密码验证通过，完成登录流程
        try:
            user = self._pending_user_info

            # 兼容旧版SHA256哈希：自动升级为PBKDF2
            if self._pending_is_sha256:
                new_hash = self.user_service._hash_password(self._pending_password)
                self.user_service.user_repo.update(user['id'], {'password_hash': new_hash})

            # 生成会话令牌
            session_token = self.user_service._generate_session_token()
            from datetime import datetime
            with self.user_service._lock:
                self.user_service._sessions[session_token] = {
                    'user_id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'login_time': datetime.now().isoformat()
                }
                self.user_service._current_user = user

            # 更新最后登录时间
            self.user_service.user_repo.update(user['id'], {
                'last_login': datetime.now().isoformat()
            })

            if self.user_service.logger:
                self.user_service.logger.info(f"User logged in: {user['username']}")

            self.login_result = {
                'success': True,
                'session_token': session_token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'email': user.get('email')
                }
            }
            self.accept()

        except Exception:
            try:
                import logging
                logging.exception("Login post-verification failed")
            except Exception:
                pass
            self._login_failed(traceback.format_exc())

    def _login_failed(self, error_msg):
        """登录失败处理（主线程）"""
        self._logging_in = False

        if 'Invalid username or password' in error_msg:
            self._show_error("用户名或密码错误")
        elif 'disabled' in error_msg:
            self._show_error("账户已被禁用")
        else:
            self._show_error(error_msg)

        self.password_edit.setFocus()
        self.login_btn.setEnabled(True)
        self.login_btn.setText("登录")
        self.exit_btn.setEnabled(True)

    def _show_error(self, message):
        """显示错误信息"""
        self.error_label.setText(message)
        self.error_label.show()

    def _on_exit(self):
        """退出按钮点击事件"""
        reply = QMessageBox.question(
            self, "确认退出", "确定要退出应用程序吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            sys.exit(0)

    def get_result(self):
        """获取登录结果"""
        return self.login_result
