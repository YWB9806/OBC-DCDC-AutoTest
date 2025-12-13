"""性能指标仓储

负责性能指标数据的持久化操作。
"""

from typing import List, Dict, Any, Optional
from AppCode.data_access.sqlite_data_access import SQLiteDataAccess


class PerformanceMetricsRepository:
    """性能指标仓储"""
    
    def __init__(self, data_access: SQLiteDataAccess):
        """初始化性能指标仓储
        
        Args:
            data_access: 数据访问对象
        """
        self.db = data_access
        self._ensure_table()
    
    def _ensure_table(self):
        """确保表存在"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT,
            script_path TEXT,
            timestamp TEXT NOT NULL,
            duration REAL,
            cpu_percent REAL,
            memory_mb REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        create_index_sql_1 = """
        CREATE INDEX IF NOT EXISTS idx_perf_timestamp
        ON performance_metrics(timestamp)
        """
        
        create_index_sql_2 = """
        CREATE INDEX IF NOT EXISTS idx_perf_execution
        ON performance_metrics(execution_id)
        """
        
        self.db.execute_non_query(create_table_sql)
        self.db.execute_non_query(create_index_sql_1)
        self.db.execute_non_query(create_index_sql_2)
    
    def create(self, metrics: Dict[str, Any]) -> str:
        """创建性能指标记录
        
        Args:
            metrics: 性能指标数据
            
        Returns:
            记录ID
        """
        sql = """
        INSERT INTO performance_metrics 
        (execution_id, script_path, timestamp, duration, cpu_percent, memory_mb)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        params = (
            metrics.get('execution_id'),
            metrics.get('script_path'),
            metrics.get('timestamp'),
            metrics.get('duration'),
            metrics.get('cpu_percent'),
            metrics.get('memory_mb')
        )
        
        cursor = self.db.execute(sql, params)
        return str(cursor.lastrowid)
    
    def get_by_id(self, metrics_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取性能指标
        
        Args:
            metrics_id: 指标ID
            
        Returns:
            性能指标数据
        """
        sql = """
        SELECT * FROM performance_metrics WHERE id = ?
        """
        
        result = self.db.fetch_one(sql, (metrics_id,))
        return self._row_to_dict(result) if result else None
    
    def get_by_execution(self, execution_id: str) -> List[Dict[str, Any]]:
        """根据执行ID获取性能指标
        
        Args:
            execution_id: 执行ID
            
        Returns:
            性能指标列表
        """
        sql = """
        SELECT * FROM performance_metrics 
        WHERE execution_id = ?
        ORDER BY timestamp DESC
        """
        
        results = self.db.fetch_all(sql, (execution_id,))
        return [self._row_to_dict(row) for row in results]
    
    def get_by_time_range(
        self,
        start_time: str,
        end_time: str
    ) -> List[Dict[str, Any]]:
        """根据时间范围获取性能指标
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            性能指标列表
        """
        sql = """
        SELECT * FROM performance_metrics 
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp DESC
        """
        
        results = self.db.fetch_all(sql, (start_time, end_time))
        return [self._row_to_dict(row) for row in results]
    
    def get_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近的性能指标
        
        Args:
            limit: 返回数量限制
            
        Returns:
            性能指标列表
        """
        sql = """
        SELECT * FROM performance_metrics 
        ORDER BY timestamp DESC
        LIMIT ?
        """
        
        results = self.db.fetch_all(sql, (limit,))
        return [self._row_to_dict(row) for row in results]
    
    def get_statistics(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取统计信息
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            统计信息
        """
        if start_time and end_time:
            sql = """
            SELECT 
                COUNT(*) as total_count,
                AVG(duration) as avg_duration,
                AVG(cpu_percent) as avg_cpu,
                AVG(memory_mb) as avg_memory,
                MAX(cpu_percent) as max_cpu,
                MAX(memory_mb) as max_memory
            FROM performance_metrics
            WHERE timestamp BETWEEN ? AND ?
            """
            params = (start_time, end_time)
        else:
            sql = """
            SELECT 
                COUNT(*) as total_count,
                AVG(duration) as avg_duration,
                AVG(cpu_percent) as avg_cpu,
                AVG(memory_mb) as avg_memory,
                MAX(cpu_percent) as max_cpu,
                MAX(memory_mb) as max_memory
            FROM performance_metrics
            """
            params = ()
        
        result = self.db.fetch_one(sql, params)
        
        if result:
            return {
                'total_count': result[0] or 0,
                'avg_duration': round(result[1] or 0, 2),
                'avg_cpu': round(result[2] or 0, 2),
                'avg_memory': round(result[3] or 0, 2),
                'max_cpu': round(result[4] or 0, 2),
                'max_memory': round(result[5] or 0, 2)
            }
        
        return {
            'total_count': 0,
            'avg_duration': 0,
            'avg_cpu': 0,
            'avg_memory': 0,
            'max_cpu': 0,
            'max_memory': 0
        }
    
    def delete_before(self, timestamp: str) -> int:
        """删除指定时间之前的记录
        
        Args:
            timestamp: 时间戳
            
        Returns:
            删除的记录数
        """
        sql = """
        DELETE FROM performance_metrics WHERE timestamp < ?
        """
        
        cursor = self.db.execute(sql, (timestamp,))
        return cursor.rowcount
    
    def delete_by_execution(self, execution_id: str) -> int:
        """删除指定执行的性能指标
        
        Args:
            execution_id: 执行ID
            
        Returns:
            删除的记录数
        """
        sql = """
        DELETE FROM performance_metrics WHERE execution_id = ?
        """
        
        cursor = self.db.execute(sql, (execution_id,))
        return cursor.rowcount
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """将数据库行转换为字典
        
        Args:
            row: 数据库行
            
        Returns:
            字典数据
        """
        if not row:
            return {}
        
        return {
            'id': row[0],
            'execution_id': row[1],
            'script_path': row[2],
            'timestamp': row[3],
            'duration': row[4],
            'cpu_percent': row[5],
            'memory_mb': row[6],
            'created_at': row[7]
        }