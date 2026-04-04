"""执行历史仓储

管理脚本执行历史记录。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_repository import BaseRepository


class ExecutionHistoryRepository(BaseRepository):
    """执行历史仓储"""
    
    def get_table_name(self) -> str:
        """获取表名"""
        return 'execution_history'
    
    def get_by_script(self, script_path: str) -> List[Dict[str, Any]]:
        """获取指定脚本的执行历史
        
        Args:
            script_path: 脚本路径
            
        Returns:
            执行历史列表
        """
        return self.query({'script_path': script_path})
    
    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """获取指定状态的执行记录
        
        Args:
            status: 执行状态
            
        Returns:
            执行记录列表
        """
        return self.query({'status': status})
    
    def get_by_batch(self, batch_id: str) -> List[Dict[str, Any]]:
        """获取批次的所有执行记录
        
        Args:
            batch_id: 批次ID
            
        Returns:
            执行记录列表
        """
        return self.query({'batch_id': batch_id})
    
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的执行记录
        
        Args:
            limit: 返回数量限制
            
        Returns:
            执行记录列表
        """
        try:
            sql = "SELECT * FROM execution_history ORDER BY start_time DESC LIMIT ?"
            return self.db.execute_query(sql, (limit,))
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get recent records: {e}")
            return []
    
    def get_by_date_range(
        self,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """获取日期范围内的执行记录
        
        Args:
            start_date: 开始日期（格式：yyyy-MM-dd）
            end_date: 结束日期（格式：yyyy-MM-dd）
            
        Returns:
            执行记录列表
        """
        try:
            # 使用 T 前缀格式以匹配 isoformat() 存储的格式（如 2026-04-04T10:30:00）
            start_datetime = f"{start_date}T00:00:00"
            end_datetime = f"{end_date}T23:59:59"
            sql = "SELECT * FROM execution_history WHERE start_time >= ? AND start_time <= ?"
            return self.db.execute_query(sql, (start_datetime, end_datetime))
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get records by date range: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取执行统计信息
        
        Returns:
            统计信息
        """
        all_records = self.get_all()
        
        stats = {
            'total': len(all_records),
            'by_status': {},
            'by_script': {},
            'total_duration': 0,
            'average_duration': 0
        }
        
        durations = []
        
        for record in all_records:
            # 统计状态
            status = record.get('status', 'unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # 统计脚本
            script = record.get('script_path', 'unknown')
            stats['by_script'][script] = stats['by_script'].get(script, 0) + 1
            
            # 统计时长
            if record.get('start_time') and record.get('end_time'):
                try:
                    start = datetime.fromisoformat(record['start_time'])
                    end = datetime.fromisoformat(record['end_time'])
                    duration = (end - start).total_seconds()
                    durations.append(duration)
                    stats['total_duration'] += duration
                except Exception:
                    pass
        
        if durations:
            stats['average_duration'] = sum(durations) / len(durations)
        
        return stats
    
    def delete_old_records(self, days: int = 30) -> int:
        """删除旧记录
        
        Args:
            days: 保留天数
            
        Returns:
            删除的记录数
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()
        
        all_records = self.get_all()
        deleted_count = 0
        
        for record in all_records:
            start_time = record.get('start_time', '')
            if start_time and start_time < cutoff_str:
                if self.delete(record['id']):
                    deleted_count += 1
        
        if self.logger:
            self.logger.info(f"Deleted {deleted_count} old execution records")
        
        return deleted_count