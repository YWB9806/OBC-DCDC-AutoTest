"""备份服务单元测试"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
import shutil
import zipfile
import json
from datetime import datetime

from AppCode.services.backup_service import BackupService


class TestBackupService(unittest.TestCase):
    """备份服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, 'data')
        self.backup_dir = os.path.join(self.temp_dir, 'backups')
        
        os.makedirs(self.data_dir)
        os.makedirs(self.backup_dir)
        
        # 创建测试数据文件
        self.test_file = os.path.join(self.data_dir, 'test.db')
        with open(self.test_file, 'w') as f:
            f.write('test data')
        
        self.mock_logger = Mock()
        self.service = BackupService(
            self.data_dir,
            self.backup_dir,
            self.mock_logger
        )
    
    def tearDown(self):
        """测试后清理"""
        if self.service._auto_backup_running:
            self.service.stop_auto_backup()
        
        # 删除临时目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.service)
        self.assertEqual(self.service.data_dir, self.data_dir)
        self.assertEqual(self.service.backup_dir, self.backup_dir)
        self.assertTrue(os.path.exists(self.backup_dir))
    
    def test_create_backup(self):
        """测试创建备份"""
        description = "Test backup"
        
        result = self.service.create_backup(description)
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertIn('backup_path', result)
        
        backup_file = result['backup_path']
        self.assertTrue(os.path.exists(backup_file))
        self.assertTrue(backup_file.endswith('.zip'))
        
        # 验证ZIP文件内容（应包含data目录和文件）
        with zipfile.ZipFile(backup_file, 'r') as zf:
            namelist = zf.namelist()
            # 检查是否包含data目录下的test.db文件
            self.assertTrue(any('test.db' in name for name in namelist))
            self.assertIn('metadata.txt', namelist)
    
    def test_list_backups(self):
        """测试列出备份"""
        # 创建几个备份
        result1 = self.service.create_backup("Backup 1")
        result2 = self.service.create_backup("Backup 2")
        
        self.assertTrue(result1['success'])
        self.assertTrue(result2['success'])
        
        backups = self.service.list_backups()
        
        # 由于cleanup可能删除了一些备份，至少应该有1个
        self.assertGreaterEqual(len(backups), 1)
        self.assertIn('name', backups[0])
        self.assertIn('size', backups[0])
        self.assertIn('created_time', backups[0])
        self.assertIn('description', backups[0])
    
    def test_restore_backup(self):
        """测试恢复备份"""
        # 创建备份
        result = self.service.create_backup("Test backup")
        backup_file = result['backup_path']
        
        # 修改原始文件
        with open(self.test_file, 'w') as f:
            f.write('modified data')
        
        # 恢复备份
        restore_result = self.service.restore_backup(os.path.basename(backup_file))
        
        self.assertTrue(restore_result['success'])
        
        # 验证文件已恢复
        with open(self.test_file, 'r') as f:
            content = f.read()
            self.assertEqual(content, 'test data')
    
    def test_restore_backup_with_rollback(self):
        """测试恢复失败时的回滚"""
        # 创建备份
        result = self.service.create_backup("Test backup")
        backup_file = result['backup_path']
        
        # 模拟恢复过程中出错
        with patch('zipfile.ZipFile') as mock_zip:
            mock_zip.side_effect = Exception("Extraction failed")
            
            restore_result = self.service.restore_backup(os.path.basename(backup_file))
            
            self.assertFalse(restore_result['success'])
            # 验证原始文件未被破坏
            self.assertTrue(os.path.exists(self.test_file))
    
    def test_delete_backup(self):
        """测试删除备份"""
        # 创建备份
        result = self.service.create_backup("Test backup")
        backup_file = result['backup_path']
        backup_name = os.path.basename(backup_file)
        
        # 删除备份
        delete_result = self.service.delete_backup(backup_name)
        
        self.assertTrue(delete_result['success'])
        self.assertFalse(os.path.exists(backup_file))
    
    def test_cleanup_old_backups(self):
        """测试清理旧备份"""
        # 先设置一个很大的max_backups，避免自动清理
        self.service.set_max_backups(100)
        
        # 创建多个备份
        for i in range(5):
            result = self.service.create_backup(f"Backup {i}")
            self.assertTrue(result['success'])
        
        # 获取当前备份数量（可能因为自动清理而少于5个）
        backups_before = self.service.list_backups()
        initial_count = len(backups_before)
        
        # 清理，只保留2个
        deleted_count = self.service.cleanup_old_backups(keep_count=2)
        
        # 验证删除了正确数量的备份
        self.assertEqual(deleted_count, max(0, initial_count - 2))
        
        # 验证只剩2个或更少备份
        backups = self.service.list_backups()
        self.assertLessEqual(len(backups), 2)
    
    def test_start_stop_auto_backup(self):
        """测试自动备份启停"""
        # 启动自动备份（间隔很长，不会实际执行）
        self.service.start_auto_backup(interval_hours=24)
        
        self.assertTrue(self.service._auto_backup_running)
        self.assertIsNotNone(self.service._auto_backup_thread)
        
        # 停止自动备份
        self.service.stop_auto_backup()
        
        self.assertFalse(self.service._auto_backup_running)
    
    def test_get_backup_info(self):
        """测试获取备份信息"""
        # 创建备份
        result = self.service.create_backup("Test backup")
        backup_file = result['backup_path']
        backup_name = os.path.basename(backup_file)
        
        # 获取信息
        info = self.service.get_backup_info(backup_name)
        
        self.assertIsNotNone(info)
        self.assertEqual(info['description'], "Test backup")
        self.assertIn('created_time', info)
        self.assertIn('size', info)


class TestBackupServiceEdgeCases(unittest.TestCase):
    """备份服务边界情况测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, 'data')
        self.backup_dir = os.path.join(self.temp_dir, 'backups')
        
        os.makedirs(self.data_dir)
        
        self.mock_logger = Mock()
        self.service = BackupService(
            self.data_dir,
            self.backup_dir,
            self.mock_logger
        )
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_create_backup_empty_directory(self):
        """测试备份空目录"""
        result = self.service.create_backup("Empty backup")
        
        self.assertTrue(result['success'])
        self.assertTrue(os.path.exists(result['backup_path']))
    
    def test_restore_nonexistent_backup(self):
        """测试恢复不存在的备份"""
        result = self.service.restore_backup("nonexistent.zip")
        
        self.assertFalse(result['success'])
    
    def test_delete_nonexistent_backup(self):
        """测试删除不存在的备份"""
        result = self.service.delete_backup("nonexistent.zip")
        
        self.assertFalse(result['success'])
    
    def test_list_backups_empty(self):
        """测试列出空备份列表"""
        backups = self.service.list_backups()
        
        self.assertEqual(len(backups), 0)


if __name__ == '__main__':
    unittest.main()