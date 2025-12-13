"""数据库管理模块

提供数据库连接、初始化、迁移等功能。
"""

import sqlite3
import os
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime

from AppCode.utils.constants import DATABASE_NAME, DATABASE_VERSION
from AppCode.utils.exceptions import DatabaseConnectionError, DatabaseMigrationError
from AppCode.utils.decorators import singleton


@singleton
class DatabaseManager:
    """数据库管理器
    
    负责数据库的连接、初始化、迁移和查询。
    采用单例模式确保全局只有一个数据库连接管理器。
    """
    
    def __init__(self, db_path: str = None):
        """初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，默认为data/app.db
        """
        if db_path is None:
            db_path = os.path.join("data", DATABASE_NAME)
        
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """确保数据目录存在"""
        data_dir = os.path.dirname(self.db_path)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
    
    def connect(self) -> sqlite3.Connection:
        """建立数据库连接
        
        Returns:
            数据库连接对象
            
        Raises:
            DatabaseConnectionError: 连接失败时抛出
        """
        try:
            if self._connection is None:
                self._connection = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    timeout=30.0
                )
                self._connection.row_factory = sqlite3.Row
                # 启用外键约束
                self._connection.execute("PRAGMA foreign_keys = ON")
                # 设置日志模式为WAL以提高并发性能
                self._connection.execute("PRAGMA journal_mode = WAL")
            return self._connection
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")
    
    def disconnect(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器
        
        Yields:
            数据库连接对象
        """
        conn = self.connect()
        try:
            yield conn
        finally:
            # 不关闭连接，保持连接池
            pass
    
    @contextmanager
    def transaction(self):
        """事务上下文管理器
        
        Yields:
            数据库连接对象
        """
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
    
    def initialize_database(self):
        """初始化数据库
        
        创建所有必要的表结构。
        """
        with self.transaction() as conn:
            cursor = conn.cursor()
            
            # 创建版本管理表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version VARCHAR(20) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """)
            
            # 创建用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(100),
                    role VARCHAR(20) DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # 创建执行历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id INTEGER,
                    script_path TEXT NOT NULL,
                    script_name VARCHAR(255) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    result VARCHAR(20),
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration REAL,
                    output TEXT,
                    error_message TEXT,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (batch_id) REFERENCES batch_execution(id)
                )
            """)
            
            # 创建批次执行表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS batch_execution (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_name VARCHAR(255),
                    execution_mode VARCHAR(20) NOT NULL,
                    total_scripts INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration REAL,
                    user_id INTEGER,
                    config_snapshot TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # 创建性能监控表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_io REAL,
                    FOREIGN KEY (execution_id) REFERENCES execution_history(id)
                )
            """)
            
            # 创建配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configurations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key VARCHAR(100) UNIQUE NOT NULL,
                    value TEXT,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建备份记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backup_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_type VARCHAR(20) NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    description TEXT,
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            """)
            
            # 创建索引
            self._create_indexes(cursor)
            
            # 记录初始版本
            cursor.execute(
                "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                (DATABASE_VERSION, "Initial database schema")
            )
    
    def _create_indexes(self, cursor):
        """创建数据库索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_execution_history_status ON execution_history(status)",
            "CREATE INDEX IF NOT EXISTS idx_execution_history_start_time ON execution_history(start_time)",
            "CREATE INDEX IF NOT EXISTS idx_execution_history_batch_id ON execution_history(batch_id)",
            "CREATE INDEX IF NOT EXISTS idx_batch_execution_start_time ON batch_execution(start_time)",
            "CREATE INDEX IF NOT EXISTS idx_performance_metrics_execution_id ON performance_metrics(execution_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    def get_current_version(self) -> Optional[str]:
        """获取当前数据库版本
        
        Returns:
            当前版本号，如果没有版本记录则返回None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT version FROM schema_version ORDER BY id DESC LIMIT 1"
                )
                row = cursor.fetchone()
                return row[0] if row else None
        except sqlite3.OperationalError:
            # 表不存在
            return None
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """执行查询语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # 转换为字典列表
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """执行更新语句
        
        Args:
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            受影响的行数
        """
        with self.transaction() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """批量执行语句
        
        Args:
            query: SQL语句
            params_list: 参数列表
            
        Returns:
            受影响的行数
        """
        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def backup_database(self, backup_path: str):
        """备份数据库
        
        Args:
            backup_path: 备份文件路径
        """
        import shutil
        
        # 确保备份目录存在
        backup_dir = os.path.dirname(backup_path)
        if backup_dir and not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        
        # 复制数据库文件
        shutil.copy2(self.db_path, backup_path)
    
    def restore_database(self, backup_path: str):
        """恢复数据库
        
        Args:
            backup_path: 备份文件路径
        """
        import shutil
        
        if not os.path.exists(backup_path):
            raise DatabaseConnectionError(f"Backup file not found: {backup_path}")
        
        # 关闭当前连接
        self.disconnect()
        
        # 恢复数据库文件
        shutil.copy2(backup_path, self.db_path)
        
        # 重新连接
        self.connect()