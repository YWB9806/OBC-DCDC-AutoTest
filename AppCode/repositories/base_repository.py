"""仓储基类

提供通用的CRUD操作。
"""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseRepository(ABC):
    """仓储基类"""
    
    def __init__(self, db_manager, logger=None):
        """初始化仓储
        
        Args:
            db_manager: 数据库管理器
            logger: 日志记录器
        """
        self.db = db_manager
        self.logger = logger
        self._table_name = None
    
    @abstractmethod
    def get_table_name(self) -> str:
        """获取表名"""
        pass
    
    def create(self, data: Dict[str, Any]) -> str:
        """创建记录
        
        Args:
            data: 记录数据
            
        Returns:
            记录ID
        """
        table_name = self.get_table_name()
        
        try:
            record_id = self.db.insert(table_name, data)
            
            if self.logger:
                self.logger.info(f"Created record in {table_name}: {record_id}")
            
            return record_id
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create record in {table_name}: {e}")
            raise
    
    def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            记录数据或None
        """
        table_name = self.get_table_name()
        
        try:
            records = self.db.query(table_name, {'id': record_id})
            return records[0] if records else None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get record from {table_name}: {e}")
            return None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """获取所有记录
        
        Returns:
            记录列表
        """
        table_name = self.get_table_name()
        
        try:
            return self.db.query(table_name, {})
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get all records from {table_name}: {e}")
            return []
    
    def query(self, conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """查询记录
        
        Args:
            conditions: 查询条件
            
        Returns:
            记录列表
        """
        table_name = self.get_table_name()
        
        try:
            return self.db.query(table_name, conditions)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to query {table_name}: {e}")
            return []
    
    def update(self, record_id: str, data: Dict[str, Any]) -> bool:
        """更新记录
        
        Args:
            record_id: 记录ID
            data: 更新数据
            
        Returns:
            是否成功
        """
        table_name = self.get_table_name()
        
        try:
            success = self.db.update(table_name, record_id, data)
            
            if self.logger:
                self.logger.info(f"Updated record in {table_name}: {record_id}")
            
            return success
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to update record in {table_name}: {e}")
            return False
    
    def delete(self, record_id: str) -> bool:
        """删除记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            是否成功
        """
        table_name = self.get_table_name()
        
        try:
            success = self.db.delete(table_name, record_id)
            
            if self.logger:
                self.logger.info(f"Deleted record from {table_name}: {record_id}")
            
            return success
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to delete record from {table_name}: {e}")
            return False
    
    def count(self, conditions: Optional[Dict[str, Any]] = None) -> int:
        """统计记录数
        
        Args:
            conditions: 查询条件
            
        Returns:
            记录数
        """
        conditions = conditions or {}
        records = self.query(conditions)
        return len(records)
    
    def exists(self, record_id: str) -> bool:
        """检查记录是否存在
        
        Args:
            record_id: 记录ID
            
        Returns:
            是否存在
        """
        return self.get_by_id(record_id) is not None