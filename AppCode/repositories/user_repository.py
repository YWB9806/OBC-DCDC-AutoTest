"""用户仓储

负责用户数据的持久化操作。
"""

from typing import List, Dict, Any, Optional
from AppCode.data_access.sqlite_data_access import SQLiteDataAccess


class UserRepository:
    """用户仓储"""
    
    def __init__(self, data_access: SQLiteDataAccess):
        """初始化用户仓储
        
        Args:
            data_access: 数据访问对象
        """
        self.db = data_access
        self._ensure_table()
    
    def _ensure_table(self):
        """确保表存在"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT,
            is_active INTEGER DEFAULT 1,
            can_view_results INTEGER DEFAULT 0,
            last_login TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 添加迁移逻辑：如果表已存在但没有can_view_results字段，则添加
        try:
            self.db.execute_non_query("""
                ALTER TABLE users ADD COLUMN can_view_results INTEGER DEFAULT 0
            """)
        except:
            # 字段已存在或表不存在，忽略错误
            pass
        
        create_index_sql_1 = """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_username
        ON users(username)
        """
        
        create_index_sql_2 = """
        CREATE INDEX IF NOT EXISTS idx_role
        ON users(role)
        """
        
        self.db.execute_non_query(create_table_sql)
        self.db.execute_non_query(create_index_sql_1)
        self.db.execute_non_query(create_index_sql_2)
    
    def create(self, user_data: Dict[str, Any]) -> str:
        """创建用户
        
        Args:
            user_data: 用户数据
            
        Returns:
            用户ID
        """
        from datetime import datetime
        
        # 不要手动设置id，让数据库自动生成
        data = {
            'username': user_data.get('username'),
            'password_hash': user_data.get('password_hash'),
            'role': user_data.get('role', 'user'),
            'email': user_data.get('email'),
            'is_active': 1 if user_data.get('is_active', True) else 0,
            'can_view_results': 1 if user_data.get('can_view_results', 0) else 0,
            'created_at': user_data.get('created_at', datetime.now().isoformat())
        }
        
        user_id = self.db.insert('users', data)
        return user_id
    
    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户数据
        """
        result = self.db.get_by_id('users', user_id)
        return result if result else None
    
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            用户数据
        """
        results = self.db.query('users', {'username': username})
        return results[0] if results else None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """获取所有用户
        
        Returns:
            用户列表
        """
        sql = """
        SELECT * FROM users ORDER BY created_at DESC
        """
        return self.db.execute_query(sql)
    
    def get_by_role(self, role: str) -> List[Dict[str, Any]]:
        """根据角色获取用户
        
        Args:
            role: 角色
            
        Returns:
            用户列表
        """
        sql = """
        SELECT * FROM users WHERE role = ? ORDER BY created_at DESC
        """
        return self.db.execute_query(sql, (role,))
    
    def update(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """更新用户
        
        Args:
            user_id: 用户ID
            updates: 更新数据
            
        Returns:
            是否成功
        """
        from datetime import datetime
        
        # 处理is_active字段
        if 'is_active' in updates:
            updates['is_active'] = 1 if updates['is_active'] else 0
        
        # 添加updated_at
        updates['updated_at'] = datetime.now().isoformat()
        
        return self.db.update('users', user_id, updates)
    
    def delete(self, user_id: str) -> bool:
        """删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        return self.db.delete('users', 'id = ?', (user_id,))
    
    def count(self) -> int:
        """获取用户总数
        
        Returns:
            用户总数
        """
        sql = """
        SELECT COUNT(*) as count FROM users
        """
        
        result = self.db.execute_query(sql)
        return result[0]['count'] if result else 0