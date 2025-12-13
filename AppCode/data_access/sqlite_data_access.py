"""SQLite数据访问实现

提供基于SQLite的数据访问功能。
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
import json


class SQLiteDataAccess:
    """SQLite数据访问类"""
    
    def __init__(self, db_path: str):
        """初始化数据访问
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 创建执行历史表（添加suite_id、suite_name和test_result字段）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS execution_history (
                id TEXT PRIMARY KEY,
                script_path TEXT NOT NULL,
                params TEXT,
                user_id TEXT,
                status TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                output TEXT,
                error TEXT,
                batch_id TEXT,
                suite_id INTEGER,
                suite_name VARCHAR(100),
                test_result VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建批次执行表（添加suite_id和suite_name字段）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS batch_executions (
                id TEXT PRIMARY KEY,
                name TEXT,
                total_scripts INTEGER,
                completed_scripts INTEGER DEFAULT 0,
                successful_scripts INTEGER DEFAULT 0,
                failed_scripts INTEGER DEFAULT 0,
                pending_scripts INTEGER DEFAULT 0,
                error_scripts INTEGER DEFAULT 0,
                timeout_scripts INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                user_id TEXT,
                suite_id INTEGER,
                suite_name VARCHAR(100),
                params TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建测试方案表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_suites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                script_paths TEXT NOT NULL,
                script_count INTEGER DEFAULT 0,
                created_by VARCHAR(50),
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_executed_time DATETIME,
                execution_count INTEGER DEFAULT 0
            )
        ''')
        
        # 创建性能指标表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_percent REAL,
                memory_percent REAL,
                disk_io_read REAL,
                disk_io_write REAL,
                network_sent REAL,
                network_recv REAL
            )
        ''')
        
        # 创建用户表
        cursor.execute('''
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
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_history_batch_id ON execution_history(batch_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_history_suite_id ON execution_history(suite_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_batch_executions_suite_id ON batch_executions(suite_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_batch_executions_status ON batch_executions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_test_suites_name ON test_suites(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_perf_execution ON performance_metrics(execution_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_perf_timestamp ON performance_metrics(timestamp)')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_role ON users(role)')
        
        conn.commit()
        conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        
        conn.close()
        return results
    
    def execute_non_query(self, query: str, params: tuple = ()) -> int:
        """执行非查询语句
        
        Args:
            query: SQL语句
            params: 参数
            
        Returns:
            影响的行数
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        
        affected_rows = cursor.rowcount
        conn.close()
        
        return affected_rows
    
    def insert(self, table: str, data: Dict[str, Any]) -> str:
        """插入数据
        
        Args:
            table: 表名
            data: 数据字典
            
        Returns:
            插入的记录ID
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, tuple(data.values()))
            conn.commit()
            
            # 如果data中有id，返回它；否则返回lastrowid
            record_id = data.get('id', str(cursor.lastrowid))
            conn.close()
            
            return record_id
        except Exception as e:
            print(f"Insert error: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def update(self, table: str, record_id: str, data: Dict[str, Any]) -> bool:
        """更新数据
        
        Args:
            table: 表名
            record_id: 记录ID
            data: 更新的数据
            
        Returns:
            是否成功
        """
        set_clause = ', '.join([f'{k} = ?' for k in data.keys()])
        query = f'UPDATE {table} SET {set_clause} WHERE id = ?'
        
        try:
            params = tuple(data.values()) + (record_id,)
            self.execute_non_query(query, params)
            return True
        except Exception as e:
            print(f"Update error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def delete(self, table: str, record_id: str) -> bool:
        """删除数据
        
        Args:
            table: 表名
            record_id: 记录ID
            
        Returns:
            是否成功
        """
        query = f'DELETE FROM {table} WHERE id = ?'
        
        try:
            self.execute_non_query(query, (record_id,))
            return True
        except Exception as e:
            print(f"Delete error: {e}")
            return False
    
    def get_by_id(self, table: str, id_value: str) -> Optional[Dict[str, Any]]:
        """根据ID获取记录
        
        Args:
            table: 表名
            id_value: ID值
            
        Returns:
            记录字典
        """
        query = f'SELECT * FROM {table} WHERE id = ?'
        results = self.execute_query(query, (id_value,))
        
        return results[0] if results else None
    
    def query(self, table: str, conditions: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """查询数据
        
        Args:
            table: 表名
            conditions: 查询条件字典
            
        Returns:
            结果列表
        """
        query = f'SELECT * FROM {table}'
        params = []
        
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                if key.endswith('>='):
                    where_clauses.append(f"{key[:-2]} >= ?")
                elif key.endswith('<='):
                    where_clauses.append(f"{key[:-2]} <= ?")
                else:
                    where_clauses.append(f"{key} = ?")
                params.append(value)
            
            query += ' WHERE ' + ' AND '.join(where_clauses)
        
        return self.execute_query(query, tuple(params))