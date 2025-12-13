"""用户管理面板

提供用户管理和权限控制的UI界面。
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QInputDialog, QDialog,
    QLabel, QLineEdit, QComboBox, QFormLayout, QDialogButtonBox
)
from PyQt5.QtCore import Qt

from AppCode.utils.constants import UserRole


class UserDialog(QDialog):
    """用户编辑对话框"""
    
    def __init__(self, user_data=None, parent=None):
        """初始化对话框
        
        Args:
            user_data: 用户数据（编辑模式）
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.user_data = user_data
        self.is_edit_mode = user_data is not None
        
        self.setWindowTitle("编辑用户" if self.is_edit_mode else "创建用户")
        self.setMinimumWidth(400)
        
        self._init_ui()
        
        if self.is_edit_mode:
            self._load_user_data()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 表单
        form_layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        if self.is_edit_mode:
            self.username_edit.setReadOnly(True)
        form_layout.addRow("用户名:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        if self.is_edit_mode:
            self.password_edit.setPlaceholderText("留空表示不修改密码")
        form_layout.addRow("密码:", self.password_edit)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems([UserRole.SUPER_ADMIN, UserRole.USER])
        self.role_combo.currentTextChanged.connect(self._on_role_changed)
        form_layout.addRow("角色:", self.role_combo)
        
        self.email_edit = QLineEdit()
        form_layout.addRow("邮箱:", self.email_edit)
        
        # 新增：查看结果权限复选框
        from PyQt5.QtWidgets import QCheckBox
        self.can_view_results_checkbox = QCheckBox("允许查看执行结果")
        form_layout.addRow("权限:", self.can_view_results_checkbox)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _load_user_data(self):
        """加载用户数据"""
        if self.user_data:
            self.username_edit.setText(self.user_data.get('username', ''))
            self.email_edit.setText(self.user_data.get('email', ''))
            
            role = self.user_data.get('role', UserRole.USER)
            index = self.role_combo.findText(role)
            if index >= 0:
                self.role_combo.setCurrentIndex(index)
            
            # 加载权限设置
            can_view_results = bool(self.user_data.get('can_view_results', 0))
            self.can_view_results_checkbox.setChecked(can_view_results)
            
            # 根据角色设置权限复选框状态
            self._on_role_changed(role)
    
    def _on_role_changed(self, role: str):
        """角色变化事件"""
        # 超级管理员自动拥有所有权限，不可修改
        if role == UserRole.SUPER_ADMIN:
            self.can_view_results_checkbox.setChecked(True)
            self.can_view_results_checkbox.setEnabled(False)
        else:
            self.can_view_results_checkbox.setEnabled(True)
    
    def get_data(self):
        """获取表单数据"""
        data = {
            'username': self.username_edit.text().strip(),
            'role': self.role_combo.currentText(),
            'email': self.email_edit.text().strip(),
            'can_view_results': 1 if self.can_view_results_checkbox.isChecked() else 0
        }
        
        password = self.password_edit.text()
        if password:
            data['password'] = password
        
        return data


class UserPanel(QWidget):
    """用户管理面板组件"""
    
    def __init__(self, container, parent=None):
        """初始化用户管理面板
        
        Args:
            container: 依赖注入容器
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.container = container
        self.logger = container.resolve('log_manager').get_logger('ui')
        self.user_service = container.resolve('user_service')
        
        self._init_ui()
        self._refresh_user_list()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 控制按钮组
        control_group = QGroupBox("用户操作")
        control_layout = QHBoxLayout()
        
        self.create_user_btn = QPushButton("创建用户")
        self.create_user_btn.clicked.connect(self._on_create_user)
        control_layout.addWidget(self.create_user_btn)
        
        self.edit_user_btn = QPushButton("编辑用户")
        self.edit_user_btn.clicked.connect(self._on_edit_user)
        self.edit_user_btn.setEnabled(False)
        control_layout.addWidget(self.edit_user_btn)
        
        self.delete_user_btn = QPushButton("删除用户")
        self.delete_user_btn.clicked.connect(self._on_delete_user)
        self.delete_user_btn.setEnabled(False)
        control_layout.addWidget(self.delete_user_btn)
        
        self.change_password_btn = QPushButton("修改密码")
        self.change_password_btn.clicked.connect(self._on_change_password)
        self.change_password_btn.setEnabled(False)
        control_layout.addWidget(self.change_password_btn)
        
        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.clicked.connect(self._refresh_user_list)
        control_layout.addWidget(self.refresh_btn)
        
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 用户列表
        list_group = QGroupBox("用户列表")
        list_layout = QVBoxLayout()
        
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(6)
        self.user_table.setHorizontalHeaderLabels(["用户名", "角色", "邮箱", "查看结果", "最后登录", "创建时间"])
        self.user_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.user_table.itemSelectionChanged.connect(self._on_selection_changed)
        list_layout.addWidget(self.user_table)
        
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
    
    def _refresh_user_list(self):
        """刷新用户列表"""
        try:
            users = self.user_service.list_users()
            
            self.user_table.setRowCount(0)
            
            for user in users:
                row = self.user_table.rowCount()
                self.user_table.insertRow(row)
                
                # 用户名
                self.user_table.setItem(row, 0, QTableWidgetItem(user['username']))
                
                # 角色
                self.user_table.setItem(row, 1, QTableWidgetItem(user['role']))
                
                # 邮箱
                self.user_table.setItem(row, 2, QTableWidgetItem(user.get('email', '')))
                
                # 查看结果权限
                can_view = "是" if user.get('can_view_results', 0) else "否"
                self.user_table.setItem(row, 3, QTableWidgetItem(can_view))
                
                # 最后登录
                last_login = user.get('last_login', '')
                if last_login:
                    last_login = last_login.replace('T', ' ')[:19]
                self.user_table.setItem(row, 4, QTableWidgetItem(last_login))
                
                # 创建时间
                created_at = user.get('created_at', '')
                if created_at:
                    created_at = created_at.replace('T', ' ')[:19]
                self.user_table.setItem(row, 5, QTableWidgetItem(created_at))
                
                # 存储用户ID
                self.user_table.item(row, 0).setData(Qt.UserRole, user['id'])
            
            self.logger.info(f"User list refreshed: {len(users)} users")
        
        except Exception as e:
            self.logger.error(f"Error refreshing user list: {e}")
            QMessageBox.critical(self, "错误", f"刷新用户列表失败: {e}")
    
    def _on_create_user(self):
        """创建用户按钮点击"""
        try:
            dialog = UserDialog(parent=self)
            
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()
                
                # 验证数据
                if not data['username']:
                    QMessageBox.warning(self, "警告", "用户名不能为空!")
                    return
                
                if not data.get('password'):
                    QMessageBox.warning(self, "警告", "密码不能为空!")
                    return
                
                # 创建用户
                result = self.user_service.create_user(
                    username=data['username'],
                    password=data['password'],
                    role=data['role'],
                    email=data.get('email')
                )
                
                if result['success']:
                    QMessageBox.information(self, "成功", "用户创建成功!")
                    self._refresh_user_list()
                else:
                    QMessageBox.critical(self, "错误", f"用户创建失败: {result.get('error')}")
        
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            QMessageBox.critical(self, "错误", f"创建用户时出错: {e}")
    
    def _on_edit_user(self):
        """编辑用户按钮点击"""
        try:
            selected_rows = self.user_table.selectedItems()
            if not selected_rows:
                return
            
            row = selected_rows[0].row()
            user_id = self.user_table.item(row, 0).data(Qt.UserRole)
            
            # 获取用户数据
            users = self.user_service.list_users()
            user_data = next((u for u in users if u['id'] == user_id), None)
            
            if not user_data:
                QMessageBox.warning(self, "警告", "用户不存在!")
                return
            
            dialog = UserDialog(user_data=user_data, parent=self)
            
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()
                
                # 更新用户
                updates = {
                    'role': data['role'],
                    'email': data.get('email'),
                    'can_view_results': data.get('can_view_results', 0)
                }
                
                if data.get('password'):
                    updates['password'] = data['password']
                
                result = self.user_service.update_user(user_id, updates)
                
                if result['success']:
                    QMessageBox.information(self, "成功", "用户更新成功!")
                    self._refresh_user_list()
                else:
                    QMessageBox.critical(self, "错误", f"用户更新失败: {result.get('error')}")
        
        except Exception as e:
            self.logger.error(f"Error editing user: {e}")
            QMessageBox.critical(self, "错误", f"编辑用户时出错: {e}")
    
    def _on_delete_user(self):
        """删除用户按钮点击"""
        try:
            selected_rows = self.user_table.selectedItems()
            if not selected_rows:
                return
            
            row = selected_rows[0].row()
            username = self.user_table.item(row, 0).text()
            user_id = self.user_table.item(row, 0).data(Qt.UserRole)
            
            # 确认删除
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除用户 '{username}' 吗?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # 删除用户
            result = self.user_service.delete_user(user_id)
            
            if result['success']:
                QMessageBox.information(self, "成功", "用户删除成功!")
                self._refresh_user_list()
            else:
                QMessageBox.critical(self, "错误", f"用户删除失败: {result.get('error')}")
        
        except Exception as e:
            self.logger.error(f"Error deleting user: {e}")
            QMessageBox.critical(self, "错误", f"删除用户时出错: {e}")
    
    def _on_change_password(self):
        """修改密码按钮点击"""
        try:
            selected_rows = self.user_table.selectedItems()
            if not selected_rows:
                return
            
            row = selected_rows[0].row()
            user_id = self.user_table.item(row, 0).data(Qt.UserRole)
            username = self.user_table.item(row, 0).text()
            
            # 询问旧密码
            old_password, ok = QInputDialog.getText(
                self,
                "修改密码",
                f"请输入 '{username}' 的旧密码:",
                QLineEdit.Password
            )
            
            if not ok or not old_password:
                return
            
            # 询问新密码
            new_password, ok = QInputDialog.getText(
                self,
                "修改密码",
                "请输入新密码:",
                QLineEdit.Password
            )
            
            if not ok or not new_password:
                return
            
            # 修改密码
            result = self.user_service.change_password(user_id, old_password, new_password)
            
            if result['success']:
                QMessageBox.information(self, "成功", "密码修改成功!")
            else:
                QMessageBox.critical(self, "错误", f"密码修改失败: {result.get('error')}")
        
        except Exception as e:
            self.logger.error(f"Error changing password: {e}")
            QMessageBox.critical(self, "错误", f"修改密码时出错: {e}")
    
    def _on_selection_changed(self):
        """选择变化事件"""
        has_selection = len(self.user_table.selectedItems()) > 0
        self.edit_user_btn.setEnabled(has_selection)
        self.delete_user_btn.setEnabled(has_selection)
        self.change_password_btn.setEnabled(has_selection)