"""脚本管理器接口

定义脚本管理的核心接口。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class IScriptManager(ABC):
    """脚本管理器接口
    
    负责脚本的扫描、加载、分类和管理。
    """
    
    @abstractmethod
    def scan_scripts(self, root_path: str) -> List[Dict[str, Any]]:
        """扫描脚本目录
        
        Args:
            root_path: 根目录路径
            
        Returns:
            脚本信息列表
        """
        pass
    
    @abstractmethod
    def get_script_info(self, script_path: str) -> Dict[str, Any]:
        """获取脚本信息
        
        Args:
            script_path: 脚本路径
            
        Returns:
            脚本信息字典
        """
        pass
    
    @abstractmethod
    def validate_script(self, script_path: str) -> bool:
        """验证脚本
        
        Args:
            script_path: 脚本路径
            
        Returns:
            是否有效
        """
        pass
    
    @abstractmethod
    def get_scripts_by_category(self, category: str) -> List[Dict[str, Any]]:
        """按分类获取脚本
        
        Args:
            category: 分类名称
            
        Returns:
            脚本列表
        """
        pass
    
    @abstractmethod
    def search_scripts(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索脚本
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的脚本列表
        """
        pass
    
    @abstractmethod
    def get_script_tree(self, root_path: str) -> Dict[str, Any]:
        """获取脚本树形结构
        
        Args:
            root_path: 根目录路径
            
        Returns:
            树形结构字典
        """
        pass