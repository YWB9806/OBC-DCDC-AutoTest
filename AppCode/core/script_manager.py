"""脚本管理器实现

负责脚本的扫描、加载、分类和管理。
"""

import os
import ast
from typing import List, Dict, Any, Optional
from pathlib import Path

from AppCode.interfaces.i_script_manager import IScriptManager
from AppCode.utils.validators import PathValidator
from AppCode.utils.exceptions import ScriptNotFoundError, ValidationError
from AppCode.utils.constants import ScriptStatus


class ScriptManager(IScriptManager):
    """脚本管理器实现"""
    
    def __init__(self, logger=None, cache_manager=None):
        """初始化脚本管理器
        
        Args:
            logger: 日志记录器
            cache_manager: 缓存管理器
        """
        self.logger = logger
        self.cache_manager = cache_manager
        self._scripts_cache = {}
    
    def scan_scripts(self, root_path: str) -> List[Dict[str, Any]]:
        """扫描脚本目录
        
        Args:
            root_path: 根目录路径
            
        Returns:
            脚本信息列表
        """
        if self.logger:
            self.logger.info(f"Scanning scripts in: {root_path}")
        
        PathValidator.validate_directory_path(root_path, must_exist=True)
        
        scripts = []
        for root, dirs, files in os.walk(root_path):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    script_path = os.path.join(root, file)
                    try:
                        script_info = self.get_script_info(script_path)
                        scripts.append(script_info)
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"Failed to process {script_path}: {e}")
        
        if self.logger:
            self.logger.info(f"Found {len(scripts)} scripts")
        
        return scripts
    
    def get_script_info(self, script_path: str) -> Dict[str, Any]:
        """获取脚本信息
        
        Args:
            script_path: 脚本路径
            
        Returns:
            脚本信息字典
        """
        # 检查缓存
        if script_path in self._scripts_cache:
            return self._scripts_cache[script_path]
        
        PathValidator.validate_script_path(script_path)
        
        if not os.path.exists(script_path):
            raise ScriptNotFoundError(script_path)
        
        # 提取脚本信息
        script_info = {
            'path': script_path,
            'name': os.path.basename(script_path),
            'directory': os.path.dirname(script_path),
            'size': os.path.getsize(script_path),
            'modified_time': os.path.getmtime(script_path),
            'category': self._extract_category(script_path),
            'description': self._extract_description(script_path),
            'status': ScriptStatus.IDLE
        }
        
        # 缓存结果
        self._scripts_cache[script_path] = script_info
        
        return script_info
    
    def validate_script(self, script_path: str) -> bool:
        """验证脚本
        
        Args:
            script_path: 脚本路径
            
        Returns:
            是否有效
        """
        try:
            PathValidator.validate_script_path(script_path)
            
            if not os.path.exists(script_path):
                return False
            
            # 尝试解析Python语法
            with open(script_path, 'r', encoding='utf-8') as f:
                code = f.read()
                ast.parse(code)
            
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Script validation failed for {script_path}: {e}")
            return False
    
    def get_scripts_by_category(self, category: str) -> List[Dict[str, Any]]:
        """按分类获取脚本
        
        Args:
            category: 分类名称
            
        Returns:
            脚本列表
        """
        return [
            script for script in self._scripts_cache.values()
            if script.get('category') == category
        ]
    
    def search_scripts(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索脚本
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的脚本列表
        """
        keyword_lower = keyword.lower()
        results = []
        
        for script in self._scripts_cache.values():
            if (keyword_lower in script['name'].lower() or
                keyword_lower in script.get('description', '').lower() or
                keyword_lower in script['path'].lower()):
                results.append(script)
        
        return results
    
    def get_script_tree(self, root_path: str) -> Dict[str, Any]:
        """获取脚本树形结构
        
        Args:
            root_path: 根目录路径
            
        Returns:
            树形结构字典
        """
        tree = {
            'name': os.path.basename(root_path),
            'path': root_path,
            'type': 'directory',
            'children': []
        }
        
        try:
            for item in os.listdir(root_path):
                item_path = os.path.join(root_path, item)
                
                if os.path.isdir(item_path):
                    # 递归处理子目录
                    subtree = self.get_script_tree(item_path)
                    tree['children'].append(subtree)
                elif item.endswith('.py') and not item.startswith('__'):
                    # 添加脚本文件
                    tree['children'].append({
                        'name': item,
                        'path': item_path,
                        'type': 'file'
                    })
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to build tree for {root_path}: {e}")
        
        return tree
    
    def _extract_category(self, script_path: str) -> str:
        """从路径提取分类"""
        # 从路径中提取分类信息
        parts = Path(script_path).parts
        if len(parts) > 2:
            return parts[-2]  # 返回父目录名作为分类
        return "未分类"
    
    def _extract_description(self, script_path: str) -> str:
        """提取脚本描述"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                # 读取前几行查找文档字符串
                lines = f.readlines()[:10]
                for line in lines:
                    line = line.strip()
                    if line.startswith('"""') or line.startswith("'''"):
                        # 提取文档字符串
                        return line.strip('"""').strip("'''").strip()
        except Exception:
            pass
        return ""
    
    def clear_cache(self):
        """清空缓存"""
        self._scripts_cache.clear()