"""备份服务

提供数据库备份和恢复功能。
"""

import os
import shutil
import zipfile
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time


class BackupService:
    """备份服务"""
    
    def __init__(
        self,
        db_path: str,
        backup_dir: str,
        logger=None
    ):
        """初始化备份服务
        
        Args:
            db_path: 数据库文件路径或数据目录
            backup_dir: 备份目录
            logger: 日志记录器
        """
        # 如果传入的是目录，则作为data_dir
        if os.path.isdir(db_path):
            self.data_dir = db_path
            self.db_path = os.path.join(db_path, 'test.db')  # 默认数据库文件
        else:
            self.db_path = db_path
            self.data_dir = os.path.dirname(db_path)
        
        self.backup_dir = backup_dir
        self.logger = logger
        
        # 确保备份目录存在
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        
        # 自动备份配置
        self._auto_backup_enabled = False
        self._auto_backup_interval = 24  # 小时
        self._auto_backup_thread = None
        self._auto_backup_running = False
        self._max_backups = 30  # 保留最多30个备份
    
    def create_backup(self, description: str = "") -> Dict[str, Any]:
        """创建备份
        
        Args:
            description: 备份描述
            
        Returns:
            备份结果
        """
        try:
            # 检查数据目录是否存在
            if not os.path.exists(self.data_dir):
                return {
                    'success': False,
                    'error': 'Data directory not found'
                }
            
            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}.zip"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # 创建备份（压缩整个data目录）
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 遍历data目录中的所有文件
                for root, dirs, files in os.walk(self.data_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 计算相对路径
                        arcname = os.path.relpath(file_path, os.path.dirname(self.data_dir))
                        zipf.write(file_path, arcname)
                
                # 如果目录为空，至少添加目录本身
                if not os.listdir(self.data_dir):
                    zipf.writestr('data/', '')
                
                # 添加元数据
                total_size = sum(
                    os.path.getsize(os.path.join(root, file))
                    for root, dirs, files in os.walk(self.data_dir)
                    for file in files
                )
                metadata = {
                    'timestamp': timestamp,
                    'description': description,
                    'data_size': total_size
                }
                zipf.writestr('metadata.txt', str(metadata))
            
            backup_size = os.path.getsize(backup_path)
            
            if self.logger:
                self.logger.info(f"Backup created: {backup_name} ({backup_size} bytes)")
            
            # 清理旧备份
            self._cleanup_old_backups()
            
            return {
                'success': True,
                'backup_name': backup_name,
                'backup_path': backup_path,  # 返回完整路径
                'backup_size': backup_size,
                'timestamp': timestamp,
                'description': description
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create backup: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """恢复备份
        
        Args:
            backup_name: 备份文件名
            
        Returns:
            恢复结果
        """
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # 检查备份文件是否存在
            if not os.path.exists(backup_path):
                return {
                    'success': False,
                    'error': 'Backup file not found'
                }
            
            # 备份当前数据库（以防恢复失败）
            if os.path.exists(self.db_path):
                temp_backup = f"{self.db_path}.temp_backup"
                shutil.copy2(self.db_path, temp_backup)
            else:
                temp_backup = None
            
            try:
                # 解压备份文件到临时目录
                temp_restore_dir = f"{self.data_dir}_restore_temp"
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    # 提取所有文件（除了metadata.txt）
                    for member in zipf.namelist():
                        if member != 'metadata.txt':
                            zipf.extract(member, os.path.dirname(self.data_dir))
                
                # 删除临时备份
                if temp_backup and os.path.exists(temp_backup):
                    os.remove(temp_backup)
                
                if self.logger:
                    self.logger.info(f"Backup restored: {backup_name}")
                
                return {
                    'success': True,
                    'backup_name': backup_name,
                    'message': 'Backup restored successfully'
                }
            
            except Exception as e:
                # 恢复失败，还原原数据库
                if temp_backup and os.path.exists(temp_backup):
                    shutil.copy2(temp_backup, self.db_path)
                    os.remove(temp_backup)
                
                raise e
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to restore backup: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份
        
        Returns:
            备份列表
        """
        try:
            backups = []
            
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('backup_') and filename.endswith('.zip'):
                    filepath = os.path.join(self.backup_dir, filename)
                    
                    # 获取文件信息
                    stat = os.stat(filepath)
                    
                    # 尝试读取元数据
                    description = ""
                    try:
                        with zipfile.ZipFile(filepath, 'r') as zipf:
                            if 'metadata.txt' in zipf.namelist():
                                metadata_str = zipf.read('metadata.txt').decode('utf-8')
                                metadata = eval(metadata_str)
                                description = metadata.get('description', '')
                    except Exception:
                        pass
                    
                    backups.append({
                        'name': filename,
                        'path': filepath,
                        'size': stat.st_size,
                        'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'description': description
                    })
            
            # 按创建时间倒序排序
            backups.sort(key=lambda x: x['created_time'], reverse=True)
            
            return backups
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to list backups: {e}")
            return []
    
    def delete_backup(self, backup_name: str) -> Dict[str, Any]:
        """删除备份
        
        Args:
            backup_name: 备份文件名
            
        Returns:
            删除结果
        """
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            if not os.path.exists(backup_path):
                return {
                    'success': False,
                    'error': 'Backup file not found'
                }
            
            os.remove(backup_path)
            
            if self.logger:
                self.logger.info(f"Backup deleted: {backup_name}")
            
            return {
                'success': True,
                'message': 'Backup deleted successfully'
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to delete backup: {e}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_backup_info(self, backup_name: str) -> Optional[Dict[str, Any]]:
        """获取备份信息
        
        Args:
            backup_name: 备份文件名
            
        Returns:
            备份信息，如果不存在则返回None
        """
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            if not os.path.exists(backup_path):
                return None
            
            stat = os.stat(backup_path)
            
            # 读取元数据
            description = ""
            db_size = 0
            try:
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    if 'metadata.txt' in zipf.namelist():
                        metadata_str = zipf.read('metadata.txt').decode('utf-8')
                        metadata = eval(metadata_str)
                        description = metadata.get('description', '')
                        db_size = metadata.get('db_size', 0)
            except Exception:
                pass
            
            return {
                'name': backup_name,
                'path': backup_path,
                'size': stat.st_size,
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'description': description,
                'db_size': db_size
            }
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get backup info: {e}")
            return None
    
    def cleanup_old_backups(self, keep_count: int = None) -> int:
        """清理旧备份（公共方法）
        
        Args:
            keep_count: 保留的备份数量，如果为None则使用默认值
            
        Returns:
            删除的备份数量
        """
        try:
            if keep_count is None:
                keep_count = self._max_backups
            
            backups = self.list_backups()
            
            # 如果备份数量超过限制，删除最旧的
            if len(backups) > keep_count:
                backups_to_delete = backups[keep_count:]
                
                for backup in backups_to_delete:
                    self.delete_backup(backup['name'])
                
                deleted_count = len(backups_to_delete)
                
                if self.logger:
                    self.logger.info(f"Cleaned up {deleted_count} old backups")
                
                return deleted_count
            
            return 0
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to cleanup old backups: {e}")
            return 0
    
    def start_auto_backup(self, interval_hours: int = 24):
        """启动自动备份
        
        Args:
            interval_hours: 备份间隔（小时）
        """
        if self._auto_backup_enabled:
            if self.logger:
                self.logger.warning("Auto backup already enabled")
            return
        
        self._auto_backup_interval = interval_hours
        self._auto_backup_enabled = True
        self._auto_backup_running = True
        
        self._auto_backup_thread = threading.Thread(
            target=self._auto_backup_loop,
            daemon=True,
            name="AutoBackup"
        )
        self._auto_backup_thread.start()
        
        if self.logger:
            self.logger.info(f"Auto backup started (interval: {interval_hours}h)")
    
    def stop_auto_backup(self):
        """停止自动备份"""
        self._auto_backup_enabled = False
        self._auto_backup_running = False
        
        if self._auto_backup_thread:
            self._auto_backup_thread.join(timeout=5)
        
        if self.logger:
            self.logger.info("Auto backup stopped")
    
    def set_max_backups(self, max_backups: int):
        """设置最大备份数量
        
        Args:
            max_backups: 最大备份数量
        """
        self._max_backups = max_backups
        if self.logger:
            self.logger.info(f"Max backups set to: {max_backups}")
    
    def _auto_backup_loop(self):
        """自动备份循环"""
        while self._auto_backup_running:
            try:
                # 创建自动备份
                result = self.create_backup(description="Auto backup")
                
                if result['success']:
                    if self.logger:
                        self.logger.info("Auto backup completed")
                else:
                    if self.logger:
                        self.logger.error(f"Auto backup failed: {result.get('error')}")
                
                # 等待下一个备份周期
                time.sleep(self._auto_backup_interval * 3600)
            
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in auto backup loop: {e}")
                time.sleep(3600)  # 出错后等待1小时再试
    
    def _cleanup_old_backups(self):
        """清理旧备份（内部方法）"""
        self.cleanup_old_backups()