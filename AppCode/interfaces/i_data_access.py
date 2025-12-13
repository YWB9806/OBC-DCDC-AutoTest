"""数据访问接口

定义数据访问层的核心接口（仓储模式）。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class IDataAccess(ABC):
    """数据访问接口基类
    
    定义通用的CRUD操作。
    """
    
    @abstractmethod
    def create(self, data: Dict[str, Any]) -> int:
        """创建记录
        
        Args:
            data: 数据字典
            
        Returns:
            新记录的ID
        """
        pass
    
    @abstractmethod
    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            记录字典，不存在则返回None
        """
        pass
    
    @abstractmethod
    def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """更新记录
        
        Args:
            record_id: 记录ID
            data: 更新数据
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def delete(self, record_id: int) -> bool:
        """删除记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def get_all(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """获取所有记录
        
        Args:
            filters: 过滤条件
            
        Returns:
            记录列表
        """
        pass
    
    @abstractmethod
    def count(self, filters: Dict[str, Any] = None) -> int:
        """统计记录数
        
        Args:
            filters: 过滤条件
            
        Returns:
            记录数量
        """
        pass


class IExecutionHistoryRepository(IDataAccess):
    """执行历史仓储接口"""
    
    @abstractmethod
    def get_by_batch_id(self, batch_id: int) -> List[Dict[str, Any]]:
        """根据批次ID获取执行历史
        
        Args:
            batch_id: 批次ID
            
        Returns:
            执行历史列表
        """
        pass
    
    @abstractmethod
    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """根据状态获取执行历史
        
        Args:
            status: 状态
            
        Returns:
            执行历史列表
        """
        pass
    
    @abstractmethod
    def get_statistics(self, start_date: str = None, 
                      end_date: str = None) -> Dict[str, Any]:
        """获取统计信息
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            统计信息字典
        """
        pass


class IBatchExecutionRepository(IDataAccess):
    """批次执行仓储接口"""
    
    @abstractmethod
    def get_recent_batches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的批次
        
        Args:
            limit: 数量限制
            
        Returns:
            批次列表
        """
        pass
    
    @abstractmethod
    def get_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """根据用户获取批次
        
        Args:
            user_id: 用户ID
            
        Returns:
            批次列表
        """
        pass


class IUserRepository(IDataAccess):
    """用户仓储接口"""
    
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            用户信息字典
        """
        pass
    
    @abstractmethod
    def verify_password(self, username: str, password: str) -> bool:
        """验证密码
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            是否验证通过
        """
        pass
    
    @abstractmethod
    def update_last_login(self, user_id: int):
        """更新最后登录时间
        
        Args:
            user_id: 用户ID
        """
        pass