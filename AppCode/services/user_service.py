"""用户管理服务

提供用户认证和权限管理功能。
"""

import hashlib
import os
import secrets
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from AppCode.repositories.user_repository import UserRepository
from AppCode.utils.constants import UserRole


class UserService:
    """用户管理服务"""
    
    def __init__(
        self,
        user_repo: UserRepository,
        logger=None
    ):
        """初始化用户管理服务
        
        Args:
            user_repo: 用户仓储
            logger: 日志记录器
        """
        self.user_repo = user_repo
        self.logger = logger

        self._current_user = None
        self._sessions = {}  # session_token -> user_info
        self._lock = threading.Lock()
        
        # 确保默认管理员账户存在
        self._ensure_default_admin()
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            登录结果
        """
        try:
            # 获取用户
            user = self.user_repo.get_by_username(username)
            
            if not user:
                return {
                    'success': False,
                    'error': 'Invalid username or password'
                }
            
            # 验证密码
            if not self._verify_password(password, user['password_hash']):
                return {
                    'success': False,
                    'error': 'Invalid username or password'
                }

            # 兼容旧版SHA256哈希：验证通过后自动升级为PBKDF2格式
            if ':' not in user['password_hash']:
                new_hash = self._hash_password(password)
                self.user_repo.update(user['id'], {'password_hash': new_hash})
                if self.logger:
                    self.logger.info(f"Upgraded password hash for user: {username}")
            
            # 检查用户是否被禁用
            if not user.get('is_active', True):
                return {
                    'success': False,
                    'error': 'User account is disabled'
                }
            
            # 生成会话令牌
            session_token = self._generate_session_token()

            # 保存会话（线程安全）
            with self._lock:
                self._sessions[session_token] = {
                    'user_id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'login_time': datetime.now().isoformat()
                }
                # 设置当前用户
                self._current_user = user

            # 更新最后登录时间
            self.user_repo.update(user['id'], {
                'last_login': datetime.now().isoformat()
            })
            
            if self.logger:
                self.logger.info(f"User logged in: {username}")
            
            return {
                'success': True,
                'session_token': session_token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'email': user.get('email')
                }
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Login error: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def logout(self, session_token: str) -> Dict[str, Any]:
        """用户登出
        
        Args:
            session_token: 会话令牌
            
        Returns:
            登出结果
        """
        try:
            with self._lock:
                if session_token in self._sessions:
                    username = self._sessions[session_token]['username']
                    del self._sessions[session_token]

                    if self.logger:
                        self.logger.info(f"User logged out: {username}")

                self._current_user = None
            
            return {
                'success': True,
                'message': 'Logged out successfully'
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Logout error: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """验证会话
        
        Args:
            session_token: 会话令牌
            
        Returns:
            用户信息，如果会话无效则返回None
        """
        with self._lock:
            return self._sessions.get(session_token)
    
    def verify_token(self, session_token: str) -> Optional[Dict[str, Any]]:
        """验证令牌（别名方法，用于测试兼容）
        
        Args:
            session_token: 会话令牌
            
        Returns:
            用户信息，如果令牌无效则返回None
        """
        return self.verify_session(session_token)
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """获取当前用户
        
        Returns:
            当前用户信息
        """
        with self._lock:
            return self._current_user
    
    def create_user(
        self,
        username: str,
        password: str,
        role: str = UserRole.USER,
        email: Optional[str] = None,
        can_view_results: int = 0
    ) -> Dict[str, Any]:
        """创建用户
        
        Args:
            username: 用户名
            password: 密码
            role: 角色
            email: 邮箱
            can_view_results: 是否允许查看执行结果 (0或1)
            
        Returns:
            创建结果
        """
        try:
            # 检查用户名是否已存在
            existing_user = self.user_repo.get_by_username(username)
            if existing_user:
                return {
                    'success': False,
                    'error': 'Username already exists'
                }
            
            # 超级管理员自动拥有查看结果权限
            if role == UserRole.SUPER_ADMIN:
                can_view_results = 1
            
            # 创建用户
            user_data = {
                'username': username,
                'password_hash': self._hash_password(password),
                'role': role,
                'email': email,
                'is_active': True,
                'can_view_results': can_view_results,
                'created_at': datetime.now().isoformat()
            }
            
            user_id = self.user_repo.create(user_data)
            
            if self.logger:
                self.logger.info(f"User created: {username} (role: {role}, can_view_results: {can_view_results})")
            
            return {
                'success': True,
                'user_id': user_id,
                'message': 'User created successfully'
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating user: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新用户信息
        
        Args:
            user_id: 用户ID
            updates: 更新数据
            
        Returns:
            更新结果
        """
        try:
            # 如果更新密码，需要哈希
            if 'password' in updates:
                updates['password_hash'] = self._hash_password(updates.pop('password'))
            
            self.user_repo.update(user_id, updates)
            
            if self.logger:
                self.logger.info(f"User updated: {user_id}")
            
            return {
                'success': True,
                'message': 'User updated successfully'
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating user: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            删除结果
        """
        try:
            self.user_repo.delete(user_id)
            
            if self.logger:
                self.logger.info(f"User deleted: {user_id}")
            
            return {
                'success': True,
                'message': 'User deleted successfully'
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error deleting user: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_users(self) -> List[Dict[str, Any]]:
        """列出所有用户
        
        Returns:
            用户列表
        """
        try:
            users = self.user_repo.get_all()
            
            # 移除敏感信息
            for user in users:
                user.pop('password_hash', None)
            
            return users
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error listing users: {e}")
            return []
    
    def check_permission(
        self,
        session_token: str,
        required_role: str = UserRole.USER
    ) -> bool:
        """检查权限
        
        Args:
            session_token: 会话令牌
            required_role: 所需角色
            
        Returns:
            是否有权限
        """
        session = self.verify_session(session_token)
        
        if not session:
            return False
        
        user_role = session.get('role')
        
        # 管理员拥有所有权限
        if user_role == UserRole.ADMIN:
            return True
        
        # 检查角色匹配
        return user_role == required_role
    
    def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> Dict[str, Any]:
        """修改密码
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            修改结果
        """
        try:
            user = self.user_repo.get_by_id(user_id)
            
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # 验证旧密码
            if not self._verify_password(old_password, user['password_hash']):
                return {
                    'success': False,
                    'error': 'Invalid old password'
                }
            
            # 更新密码
            self.user_repo.update(user_id, {
                'password_hash': self._hash_password(new_password)
            })
            
            if self.logger:
                self.logger.info(f"Password changed for user: {user_id}")
            
            return {
                'success': True,
                'message': 'Password changed successfully'
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error changing password: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def _hash_password(self, password: str) -> str:
        """哈希密码（PBKDF2 + 随机盐）

        Args:
            password: 明文密码

        Returns:
            哈希后的密码（格式：salt_hex:key_hex）
        """
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return salt.hex() + ':' + key.hex()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码（兼容旧版SHA256哈希和新版PBKDF2哈希）

        Args:
            password: 明文密码
            password_hash: 哈希密码

        Returns:
            是否匹配
        """
        try:
            # 新格式: salt_hex:key_hex (PBKDF2)
            if ':' in password_hash:
                salt_hex, key_hex = password_hash.split(':', 1)
                salt = bytes.fromhex(salt_hex)
                key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
                return key.hex() == key_hex
            # 旧格式: 纯SHA256哈希（64字符十六进制）
            else:
                return hashlib.sha256(password.encode()).hexdigest() == password_hash
        except (ValueError, AttributeError):
            return False
    
    def _generate_session_token(self) -> str:
        """生成会话令牌
        
        Returns:
            会话令牌
        """
        return secrets.token_urlsafe(32)
    
    def _generate_token(self) -> str:
        """生成令牌（别名方法，用于测试兼容）
        
        Returns:
            令牌
        """
        return self._generate_session_token()
    
    def _ensure_default_admin(self):
        """确保默认超级管理员账户存在"""
        try:
            import os
            admin = self.user_repo.get_by_username('admin')
            
            if not admin:
                # 从环境变量读取密码，如果没有则随机生成
                admin_password = os.environ.get('ADMIN_PASSWORD')
                if not admin_password:
                    admin_password = os.urandom(8).hex()
                    if self.logger:
                        self.logger.info("Generated default admin password (see console output)")
                    print(f"[SETUP] Default admin password: {admin_password}")
                
                # 创建默认超级管理员账户
                user_data = {
                    'username': 'admin',
                    'password_hash': self._hash_password(admin_password),
                    'role': UserRole.SUPER_ADMIN,
                    'email': 'admin@example.com',
                    'is_active': True,
                    'can_view_results': 1,  # 超级管理员可以查看结果
                    'created_at': datetime.now().isoformat()
                }
                
                self.user_repo.create(user_data)
                
                if self.logger:
                    self.logger.info("Default super admin account created (username: admin)")
            else:
                # 如果admin账户存在但不是超级管理员，升级为超级管理员
                if admin.get('role') != UserRole.SUPER_ADMIN:
                    self.user_repo.update(admin['id'], {
                        'role': UserRole.SUPER_ADMIN,
                        'can_view_results': 1
                    })
                    if self.logger:
                        self.logger.info("Upgraded admin account to super admin")
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error ensuring default admin: {e}")
    
    def can_view_results(self, user_id: str = None) -> bool:
        """检查用户是否有查看结果的权限
        
        Args:
            user_id: 用户ID，如果为None则检查当前用户
            
        Returns:
            是否有权限
        """
        try:
            if user_id is None:
                with self._lock:
                    user = self._current_user
            else:
                user = self.user_repo.get_by_id(user_id)

            if not user:
                return False

            # 超级管理员始终有权限
            if user.get('role') == UserRole.SUPER_ADMIN:
                return True

            # 检查can_view_results字段
            return bool(user.get('can_view_results', 0))
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error checking view results permission: {e}")
            return False
    
    def is_super_admin(self, user_id: str = None) -> bool:
        """检查用户是否是超级管理员
        
        Args:
            user_id: 用户ID，如果为None则检查当前用户
            
        Returns:
            是否是超级管理员
        """
        try:
            if user_id is None:
                with self._lock:
                    user = self._current_user
            else:
                user = self.user_repo.get_by_id(user_id)

            if not user:
                return False

            return user.get('role') == UserRole.SUPER_ADMIN
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error checking super admin status: {e}")
            return False