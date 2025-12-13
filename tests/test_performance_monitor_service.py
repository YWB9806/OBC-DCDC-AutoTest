"""性能监控服务单元测试"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import time
from datetime import datetime

from AppCode.services.performance_monitor_service import PerformanceMonitorService


class TestPerformanceMonitorService(unittest.TestCase):
    """性能监控服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_repo = Mock()
        self.mock_logger = Mock()
        self.service = PerformanceMonitorService(
            self.mock_repo,
            self.mock_logger
        )
    
    def tearDown(self):
        """测试后清理"""
        if self.service._monitoring:
            self.service.stop_monitoring()
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.service)
        self.assertEqual(self.service.metrics_repo, self.mock_repo)
        self.assertEqual(self.service.logger, self.mock_logger)
        self.assertFalse(self.service._monitoring)
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_get_system_metrics(self, mock_disk, mock_memory, mock_cpu):
        """测试获取系统指标"""
        # 模拟psutil返回值
        mock_cpu.return_value = 45.5
        mock_memory.return_value = MagicMock(percent=60.0)
        mock_disk.return_value = MagicMock(percent=70.0)
        
        metrics = self.service.get_system_metrics()
        
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics['cpu_percent'], 45.5)
        self.assertEqual(metrics['memory_percent'], 60.0)
        self.assertEqual(metrics['disk_percent'], 70.0)
        self.assertIn('timestamp', metrics)
    
    @patch('psutil.Process')
    def test_get_process_metrics(self, mock_process_class):
        """测试获取进程指标"""
        # 模拟进程对象
        mock_process = MagicMock()
        mock_process.cpu_percent.return_value = 25.0
        mock_process.memory_info.return_value = MagicMock(rss=100 * 1024 * 1024)
        mock_process.num_threads.return_value = 5
        mock_process_class.return_value = mock_process
        
        metrics = self.service.get_process_metrics()
        
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics['cpu_percent'], 25.0)
        self.assertEqual(metrics['memory_mb'], 100.0)
        self.assertEqual(metrics['thread_count'], 5)
    
    def test_start_stop_monitoring(self):
        """测试启动和停止监控"""
        # 启动监控
        self.service.start_monitoring(interval=1)
        self.assertTrue(self.service._monitoring)
        self.assertIsNotNone(self.service._monitor_thread)
        
        # 等待一小段时间
        time.sleep(0.5)
        
        # 停止监控
        self.service.stop_monitoring()
        self.assertFalse(self.service._monitoring)
    
    def test_record_execution_start(self):
        """测试记录执行开始"""
        execution_id = "test_exec_001"
        
        self.service.record_execution_start(execution_id)
        
        self.assertIn(execution_id, self.service._execution_metrics)
        self.assertIsNotNone(self.service._execution_metrics[execution_id]['start_time'])
    
    def test_record_execution_end(self):
        """测试记录执行结束"""
        execution_id = "test_exec_001"
        
        # 先记录开始
        self.service.record_execution_start(execution_id)
        time.sleep(0.1)
        
        # 记录结束
        self.service.record_execution_end(execution_id)
        
        self.assertIn(execution_id, self.service._execution_metrics)
        metrics = self.service._execution_metrics[execution_id]
        self.assertIsNotNone(metrics['end_time'])
        self.assertGreater(metrics['duration'], 0)
    
    def test_get_execution_stats(self):
        """测试获取执行统计"""
        # 模拟仓储返回数据
        self.mock_repo.get_recent_stats.return_value = {
            'total_executions': 10,
            'avg_duration': 5.5,
            'avg_cpu': 45.0,
            'avg_memory': 60.0
        }
        
        stats = self.service.get_execution_stats(days=7)
        
        self.assertIsNotNone(stats)
        self.assertEqual(stats['total_executions'], 10)
        self.assertEqual(stats['avg_duration'], 5.5)
        self.mock_repo.get_recent_stats.assert_called_once_with(7)
    
    def test_cleanup_old_metrics(self):
        """测试清理旧指标"""
        days = 30
        
        self.service.cleanup_old_metrics(days)
        
        self.mock_repo.delete_old_metrics.assert_called_once_with(days)
    
    def test_get_metrics_by_execution(self):
        """测试按执行ID获取指标"""
        execution_id = "test_exec_001"
        expected_metrics = [
            {'timestamp': '2024-01-01 10:00:00', 'cpu_percent': 45.0},
            {'timestamp': '2024-01-01 10:00:05', 'cpu_percent': 50.0}
        ]
        self.mock_repo.get_by_execution_id.return_value = expected_metrics
        
        metrics = self.service.get_metrics_by_execution(execution_id)
        
        self.assertEqual(metrics, expected_metrics)
        self.mock_repo.get_by_execution_id.assert_called_once_with(execution_id)


class TestPerformanceMonitorServiceIntegration(unittest.TestCase):
    """性能监控服务集成测试"""
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_monitoring_cycle(self, mock_disk, mock_memory, mock_cpu):
        """测试完整监控周期"""
        # 模拟psutil返回值
        mock_cpu.return_value = 45.5
        mock_memory.return_value = MagicMock(percent=60.0)
        mock_disk.return_value = MagicMock(percent=70.0)
        
        mock_repo = Mock()
        mock_logger = Mock()
        service = PerformanceMonitorService(mock_repo, mock_logger)
        
        try:
            # 启动监控
            service.start_monitoring(interval=1)
            
            # 记录执行
            execution_id = "test_exec_001"
            service.record_execution_start(execution_id)
            
            # 等待采集数据
            time.sleep(2)
            
            # 结束执行
            service.record_execution_end(execution_id)
            
            # 验证数据被保存
            self.assertTrue(mock_repo.save.called)
            
        finally:
            service.stop_monitoring()


if __name__ == '__main__':
    unittest.main()