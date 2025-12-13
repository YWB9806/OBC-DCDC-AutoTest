"""批次执行仓储

管理批次执行记录。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_repository import BaseRepository


class BatchExecutionRepository(BaseRepository):
    """批次执行仓储"""
    
    def get_table_name(self) -> str:
        """获取表名"""
        return 'batch_executions'
    
    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """获取指定状态的批次
        
        Args:
            status: 批次状态
            
        Returns:
            批次列表
        """
        return self.query({'status': status})
    
    def get_active_batches(self) -> List[Dict[str, Any]]:
        """获取活动中的批次
        
        Returns:
            批次列表
        """
        all_batches = self.get_all()
        
        active_statuses = ['pending', 'running']
        return [
            batch for batch in all_batches
            if batch.get('status') in active_statuses
        ]
    
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的批次
        
        Args:
            limit: 返回数量限制
            
        Returns:
            批次列表
        """
        all_batches = self.get_all()
        
        # 按开始时间排序
        sorted_batches = sorted(
            all_batches,
            key=lambda x: x.get('start_time', ''),
            reverse=True
        )
        
        return sorted_batches[:limit]
    
    def get_by_date_range(
        self,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """获取日期范围内的批次
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            批次列表
        """
        all_batches = self.get_all()
        
        filtered = []
        for batch in all_batches:
            start_time = batch.get('start_time', '')
            if start_date <= start_time <= end_date:
                filtered.append(batch)
        
        return filtered
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取批次统计信息
        
        Returns:
            统计信息
        """
        all_batches = self.get_all()
        
        stats = {
            'total': len(all_batches),
            'by_status': {},
            'total_scripts': 0,
            'total_duration': 0,
            'average_duration': 0,
            'average_scripts_per_batch': 0
        }
        
        durations = []
        script_counts = []
        
        for batch in all_batches:
            # 统计状态
            status = batch.get('status', 'unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # 统计脚本数
            script_count = batch.get('total_scripts', 0)
            stats['total_scripts'] += script_count
            script_counts.append(script_count)
            
            # 统计时长
            if batch.get('start_time') and batch.get('end_time'):
                try:
                    start = datetime.fromisoformat(batch['start_time'])
                    end = datetime.fromisoformat(batch['end_time'])
                    duration = (end - start).total_seconds()
                    durations.append(duration)
                    stats['total_duration'] += duration
                except Exception:
                    pass
        
        if durations:
            stats['average_duration'] = sum(durations) / len(durations)
        
        if script_counts:
            stats['average_scripts_per_batch'] = sum(script_counts) / len(script_counts)
        
        return stats
    
    def update_progress(
        self,
        batch_id: str,
        completed: int,
        total: int
    ) -> bool:
        """更新批次进度
        
        Args:
            batch_id: 批次ID
            completed: 已完成数
            total: 总数
            
        Returns:
            是否成功
        """
        progress = (completed / total * 100) if total > 0 else 0
        
        return self.update(batch_id, {
            'completed_scripts': completed,
            'progress': progress
        })
    
    def complete_batch(
        self,
        batch_id: str,
        status: str,
        summary: Optional[Dict[str, Any]] = None
    ) -> bool:
        """完成批次
        
        Args:
            batch_id: 批次ID
            status: 最终状态
            summary: 执行摘要
            
        Returns:
            是否成功
        """
        data = {
            'status': status,
            'end_time': datetime.now().isoformat(),
            'progress': 100
        }
        
        if summary:
            data['summary'] = str(summary)
        
        return self.update(batch_id, data)