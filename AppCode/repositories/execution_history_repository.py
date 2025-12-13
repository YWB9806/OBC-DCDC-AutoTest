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
        all_records = self.get_all()
        
        # 按开始时间排序
        sorted_records = sorted(
            all_records,
            key=lambda x: x.get('start_time', ''),
            reverse=True
        )
        
        return sorted_records[:limit]
    
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
        all_records = self.get_all()
        
        # 添加时间部分以确保完整的日期范围
        start_datetime = f"{start_date} 00:00:00"
        end_datetime = f"{end_date} 23:59:59"
        
        filtered = []
        for record in all_records:
            start_time = record.get('start_time', '')
            if not start_time:
                continue
            
            try:
                # 提取日期时间部分进行比较（处理ISO格式）
                # ISO格式：2025-12-13T01:32:04 或 2025-12-13 01:32:04 或 2025-12-13T01:32:04.123456
                record_datetime = start_time.replace('T', ' ').split('.')[0]  # 移除毫秒部分
                
                # 确保格式一致性：如果record_datetime只有日期没有时间，添加时间
                if len(record_datetime) == 10:  # 只有日期 yyyy-MM-dd
                    record_datetime = f"{record_datetime} 00:00:00"
                
                # 字符串比较（确保格式一致）
                if start_datetime <= record_datetime <= end_datetime:
                    filtered.append(record)
            except Exception as e:
                # 如果解析失败，记录日志但继续处理其他记录
                if self.logger:
                    self.logger.warning(f"Failed to parse start_time '{start_time}': {e}")
                continue
        
        return filtered
    
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