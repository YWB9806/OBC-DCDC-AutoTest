"""脚本服务

提供脚本管理相关的业务逻辑。
"""

from typing import List, Dict, Any, Optional

from AppCode.core.script_manager import ScriptManager
from AppCode.repositories.execution_history_repository import ExecutionHistoryRepository


class ScriptService:
    """脚本服务"""
    
    def __init__(
        self,
        script_manager: ScriptManager,
        execution_repo: ExecutionHistoryRepository,
        logger=None,
        cache_manager=None
    ):
        """初始化脚本服务
        
        Args:
            script_manager: 脚本管理器
            execution_repo: 执行历史仓储
            logger: 日志记录器
            cache_manager: 缓存管理器
        """
        self.script_manager = script_manager
        self.execution_repo = execution_repo
        self.logger = logger
        self.cache_manager = cache_manager
    
    def scan_and_load_scripts(self, root_path: str) -> Dict[str, Any]:
        """扫描并加载脚本
        
        Args:
            root_path: 根目录路径
            
        Returns:
            扫描结果
        """
        if self.logger:
            self.logger.info(f"Scanning scripts from: {root_path}")
        
        try:
            scripts = self.script_manager.scan_scripts(root_path)
            
            result = {
                'success': True,
                'total': len(scripts),
                'scripts': scripts,
                'categories': self._group_by_category(scripts)
            }
            
            if self.logger:
                self.logger.info(f"Successfully scanned {len(scripts)} scripts")
            
            return result
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to scan scripts: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'total': 0,
                'scripts': []
            }
    
    def get_script_details(self, script_path: str) -> Dict[str, Any]:
        """获取脚本详细信息
        
        Args:
            script_path: 脚本路径
            
        Returns:
            脚本详细信息
        """
        try:
            # 获取基本信息
            script_info = self.script_manager.get_script_info(script_path)
            
            # 获取执行历史
            execution_history = self.execution_repo.get_by_script(script_path)
            
            # 统计执行信息
            total_executions = len(execution_history)
            successful = sum(1 for e in execution_history if e.get('status') == 'success')
            failed = sum(1 for e in execution_history if e.get('status') == 'failed')
            
            script_info['execution_stats'] = {
                'total': total_executions,
                'successful': successful,
                'failed': failed,
                'success_rate': (successful / total_executions * 100) if total_executions > 0 else 0
            }
            
            script_info['recent_executions'] = execution_history[:5]  # 最近5次
            
            return script_info
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get script details: {e}")
            
            return {'error': str(e)}
    
    def validate_scripts(self, script_paths: List[str]) -> Dict[str, Any]:
        """批量验证脚本
        
        Args:
            script_paths: 脚本路径列表
            
        Returns:
            验证结果
        """
        results = {
            'total': len(script_paths),
            'valid': 0,
            'invalid': 0,
            'details': []
        }
        
        for script_path in script_paths:
            is_valid = self.script_manager.validate_script(script_path)
            
            if is_valid:
                results['valid'] += 1
            else:
                results['invalid'] += 1
            
            results['details'].append({
                'path': script_path,
                'valid': is_valid
            })
        
        return results
    
    def search_scripts(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """搜索脚本
        
        Args:
            keyword: 搜索关键词
            category: 分类
            status: 状态
            
        Returns:
            匹配的脚本列表
        """
        # 先按关键词搜索
        if keyword:
            scripts = self.script_manager.search_scripts(keyword)
        else:
            # 获取所有脚本（从缓存）
            scripts = list(self.script_manager._scripts_cache.values())
        
        # 按分类过滤
        if category:
            scripts = [s for s in scripts if s.get('category') == category]
        
        # 按状态过滤
        if status:
            scripts = [s for s in scripts if s.get('status') == status]
        
        return scripts
    
    def get_script_tree(self, root_path: str) -> Dict[str, Any]:
        """获取脚本树形结构
        
        Args:
            root_path: 根目录路径
            
        Returns:
            树形结构
        """
        try:
            return self.script_manager.get_script_tree(root_path)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get script tree: {e}")
            return {'error': str(e)}
    
    def get_categories(self) -> List[str]:
        """获取所有分类
        
        Returns:
            分类列表
        """
        scripts = list(self.script_manager._scripts_cache.values())
        categories = set(s.get('category', '未分类') for s in scripts)
        return sorted(list(categories))
    
    def get_scripts_by_category(self, category: str) -> List[Dict[str, Any]]:
        """获取指定分类的脚本
        
        Args:
            category: 分类名称
            
        Returns:
            脚本列表
        """
        return self.script_manager.get_scripts_by_category(category)
    
    def refresh_cache(self):
        """刷新脚本缓存"""
        self.script_manager.clear_cache()
        
        if self.logger:
            self.logger.info("Script cache cleared")
    
    def _group_by_category(self, scripts: List[Dict[str, Any]]) -> Dict[str, int]:
        """按分类分组统计
        
        Args:
            scripts: 脚本列表
            
        Returns:
            分类统计
        """
        categories = {}
        for script in scripts:
            category = script.get('category', '未分类')
            categories[category] = categories.get(category, 0) + 1
        
        return categories
    
    def get_popular_scripts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最常执行的脚本
        
        Args:
            limit: 返回数量限制
            
        Returns:
            脚本列表
        """
        # 统计每个脚本的执行次数
        all_executions = self.execution_repo.get_all()
        
        script_counts = {}
        for execution in all_executions:
            script_path = execution.get('script_path')
            if script_path:
                script_counts[script_path] = script_counts.get(script_path, 0) + 1
        
        # 排序并获取前N个
        sorted_scripts = sorted(
            script_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        # 获取脚本详细信息
        popular_scripts = []
        for script_path, count in sorted_scripts:
            try:
                script_info = self.script_manager.get_script_info(script_path)
                script_info['execution_count'] = count
                popular_scripts.append(script_info)
            except Exception:
                pass
        
        return popular_scripts