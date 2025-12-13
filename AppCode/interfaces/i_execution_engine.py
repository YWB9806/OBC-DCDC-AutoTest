"""执行引擎接口

定义脚本执行的核心接口。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, Optional


class IExecutionEngine(ABC):
    """执行引擎接口
    
    负责脚本的执行、监控和控制。
    """
    
    @abstractmethod
    def execute_script(self, script_path: str, **kwargs) -> Dict[str, Any]:
        """执行单个脚本
        
        Args:
            script_path: 脚本路径
            **kwargs: 执行参数
            
        Returns:
            执行结果字典
        """
        pass
    
    @abstractmethod
    def execute_batch(self, script_paths: List[str], 
                     mode: str = 'sequential', **kwargs) -> Dict[str, Any]:
        """批量执行脚本
        
        Args:
            script_paths: 脚本路径列表
            mode: 执行模式（sequential/parallel）
            **kwargs: 执行参数
            
        Returns:
            批量执行结果
        """
        pass
    
    @abstractmethod
    def cancel_execution(self, execution_id: str):
        """取消执行
        
        Args:
            execution_id: 执行ID
        """
        pass
    
    @abstractmethod
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """获取执行状态
        
        Args:
            execution_id: 执行ID
            
        Returns:
            状态信息字典
        """
        pass
    
    @abstractmethod
    def register_callback(self, event: str, callback: Callable):
        """注册回调函数
        
        Args:
            event: 事件名称
            callback: 回调函数
        """
        pass
    
    @abstractmethod
    def set_timeout(self, timeout: int):
        """设置超时时间
        
        Args:
            timeout: 超时时间（秒）
        """
        pass
    
    @abstractmethod
    def set_max_parallel(self, max_parallel: int):
        """设置最大并行数
        
        Args:
            max_parallel: 最大并行数
        """
        pass