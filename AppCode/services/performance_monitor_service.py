"""性能监控服务

提供系统性能监控和统计功能。
"""

import psutil
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from threading import Thread, Lock

from AppCode.repositories.performance_metrics_repository import PerformanceMetricsRepository


class PerformanceMonitorService:
    """性能监控服务"""
    
    def __init__(
        self,
        metrics_repo: PerformanceMetricsRepository,
        logger=None
    ):
        """初始化性能监控服务
        
        Args:
            metrics_repo: 性能指标仓储
            logger: 日志记录器
        """
        self.metrics_repo = metrics_repo
        self.logger = logger
        
        self._monitoring = False
        self._monitor_thread = None
        self._lock = Lock()
        self._current_metrics = {}
        self._interval = 5  # 监控间隔（秒）
    
    def start_monitoring(self, interval: int = 5):
        """开始监控
        
        Args:
            interval: 监控间隔（秒）
        """
        if self._monitoring:
            if self.logger:
                self.logger.warning("Performance monitoring already started")
            return
        
        self._interval = interval
        self._monitoring = True
        
        self._monitor_thread = Thread(
            target=self._monitor_loop,
            daemon=True,
            name="PerformanceMonitor"
        )
        self._monitor_thread.start()
        
        if self.logger:
            self.logger.info(f"Performance monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self):
        """停止监控"""
        self._monitoring = False
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        if self.logger:
            self.logger.info("Performance monitoring stopped")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前性能指标
        
        Returns:
            性能指标字典
        """
        with self._lock:
            return self._current_metrics.copy()
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息
        
        Returns:
            系统信息字典
        """
        try:
            cpu_count = psutil.cpu_count(logical=False)
            cpu_count_logical = psutil.cpu_count(logical=True)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_count': cpu_count,
                'cpu_count_logical': cpu_count_logical,
                'total_memory': memory.total,
                'total_disk': disk.total,
                'platform': psutil.WINDOWS if hasattr(psutil, 'WINDOWS') else 'Unknown'
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get system info: {e}")
            return {}
    
    def get_process_metrics(self, pid: Optional[int] = None) -> Dict[str, Any]:
        """获取进程性能指标
        
        Args:
            pid: 进程ID，None表示当前进程
            
        Returns:
            进程性能指标
        """
        try:
            process = psutil.Process(pid)
            
            with process.oneshot():
                cpu_percent = process.cpu_percent(interval=0.1)
                memory_info = process.memory_info()
                num_threads = process.num_threads()
                
                return {
                    'pid': process.pid,
                    'name': process.name(),
                    'cpu_percent': cpu_percent,
                    'memory_rss': memory_info.rss,
                    'memory_vms': memory_info.vms,
                    'num_threads': num_threads,
                    'status': process.status()
                }
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get process metrics: {e}")
            return {}
    
    def get_metrics_history(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取历史性能指标
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            
        Returns:
            性能指标列表
        """
        if start_time and end_time:
            return self.metrics_repo.get_by_time_range(start_time, end_time)
        else:
            return self.metrics_repo.get_recent(limit)
    
    def get_execution_statistics(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """获取执行统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        metrics = self.metrics_repo.get_by_time_range(
            start_time.isoformat(),
            end_time.isoformat()
        )
        
        if not metrics:
            return {
                'total_executions': 0,
                'avg_cpu_percent': 0,
                'avg_memory_mb': 0,
                'peak_cpu_percent': 0,
                'peak_memory_mb': 0
            }
        
        total = len(metrics)
        avg_cpu = sum(m.get('cpu_percent', 0) for m in metrics) / total
        avg_memory = sum(m.get('memory_mb', 0) for m in metrics) / total
        peak_cpu = max(m.get('cpu_percent', 0) for m in metrics)
        peak_memory = max(m.get('memory_mb', 0) for m in metrics)
        
        return {
            'total_executions': total,
            'avg_cpu_percent': round(avg_cpu, 2),
            'avg_memory_mb': round(avg_memory, 2),
            'peak_cpu_percent': round(peak_cpu, 2),
            'peak_memory_mb': round(peak_memory, 2),
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
    
    def record_execution_metrics(
        self,
        execution_id: str,
        script_path: str,
        duration: float,
        cpu_percent: float,
        memory_mb: float
    ):
        """记录执行性能指标
        
        Args:
            execution_id: 执行ID
            script_path: 脚本路径
            duration: 执行时长（秒）
            cpu_percent: CPU使用率
            memory_mb: 内存使用量（MB）
        """
        try:
            record = {
                'execution_id': execution_id,
                'script_path': script_path,
                'timestamp': datetime.now().isoformat(),
                'duration': duration,
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb
            }
            
            self.metrics_repo.create(record)
            
            if self.logger:
                self.logger.debug(f"Performance metrics recorded for {execution_id}")
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to record metrics: {e}")
    
    def cleanup_old_metrics(self, days: int = 30):
        """清理旧的性能指标
        
        Args:
            days: 保留天数
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            deleted = self.metrics_repo.delete_before(cutoff_time.isoformat())
            
            if self.logger:
                self.logger.info(f"Cleaned up {deleted} old performance metrics")
            
            return deleted
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to cleanup metrics: {e}")
            return 0
    
    def _monitor_loop(self):
        """监控循环"""
        while self._monitoring:
            try:
                # 收集系统指标
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # 收集进程指标
                process = psutil.Process()
                process_cpu = process.cpu_percent(interval=0.1)
                process_memory = process.memory_info()
                
                # 更新当前指标
                metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'system': {
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory.percent,
                        'memory_used_mb': memory.used / (1024 * 1024),
                        'memory_available_mb': memory.available / (1024 * 1024),
                        'disk_percent': disk.percent,
                        'disk_used_gb': disk.used / (1024 * 1024 * 1024),
                        'disk_free_gb': disk.free / (1024 * 1024 * 1024)
                    },
                    'process': {
                        'cpu_percent': process_cpu,
                        'memory_mb': process_memory.rss / (1024 * 1024),
                        'num_threads': process.num_threads()
                    }
                }
                
                with self._lock:
                    self._current_metrics = metrics
                
                # 休眠到下一个监控周期
                time.sleep(self._interval)
            
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in monitor loop: {e}")
                time.sleep(self._interval)