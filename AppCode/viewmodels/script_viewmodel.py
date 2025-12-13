"""脚本视图模型

管理脚本相关的UI数据和操作。
"""

from typing import List, Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal


class ScriptViewModel(QObject):
    """脚本视图模型"""
    
    # 信号定义
    scripts_loaded = pyqtSignal(list)  # 脚本加载完成
    script_updated = pyqtSignal(dict)  # 脚本更新
    error_occurred = pyqtSignal(str)   # 错误发生
    
    def __init__(self, container):
        """初始化脚本视图模型
        
        Args:
            container: 依赖注入容器
        """
        super().__init__()
        
        self.container = container
        self.logger = container.resolve('log_manager').get_logger('viewmodel')
        self.script_service = container.resolve('script_service')
        
        self._scripts = []
        self._categories = {}
    
    def load_scripts(self, directory: str = None):
        """加载脚本
        
        Args:
            directory: 脚本目录，None表示使用默认目录
        """
        try:
            result = self.script_service.scan_scripts(directory)
            
            if result['success']:
                self._scripts = result['scripts']
                self._organize_by_category()
                self.scripts_loaded.emit(self._scripts)
                self.logger.info(f"Loaded {len(self._scripts)} scripts")
            else:
                error = result.get('error', 'Unknown error')
                self.error_occurred.emit(f"加载脚本失败: {error}")
                self.logger.error(f"Failed to load scripts: {error}")
        
        except Exception as e:
            self.logger.error(f"Error loading scripts: {e}")
            self.error_occurred.emit(f"加载脚本时出错: {e}")
    
    def _organize_by_category(self):
        """按分类组织脚本"""
        self._categories = {}
        
        for script in self._scripts:
            category = script.get('category', 'Uncategorized')
            if category not in self._categories:
                self._categories[category] = []
            self._categories[category].append(script)
    
    def get_scripts(self) -> List[Dict]:
        """获取所有脚本
        
        Returns:
            脚本列表
        """
        return self._scripts
    
    def get_categories(self) -> Dict[str, List[Dict]]:
        """获取分类脚本
        
        Returns:
            分类字典
        """
        return self._categories
    
    def get_script_by_path(self, path: str) -> Optional[Dict]:
        """根据路径获取脚本
        
        Args:
            path: 脚本路径
            
        Returns:
            脚本信息，未找到返回None
        """
        for script in self._scripts:
            if script.get('path') == path:
                return script
        return None
    
    def search_scripts(self, keyword: str) -> List[Dict]:
        """搜索脚本
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的脚本列表
        """
        if not keyword:
            return self._scripts
        
        keyword = keyword.lower()
        results = []
        
        for script in self._scripts:
            name = script.get('name', '').lower()
            path = script.get('path', '').lower()
            description = script.get('description', '').lower()
            
            if (keyword in name or 
                keyword in path or 
                keyword in description):
                results.append(script)
        
        return results
    
    def filter_by_category(self, category: str) -> List[Dict]:
        """按分类过滤脚本
        
        Args:
            category: 分类名称
            
        Returns:
            该分类的脚本列表
        """
        return self._categories.get(category, [])
    
    def validate_script(self, path: str) -> Dict:
        """验证脚本
        
        Args:
            path: 脚本路径
            
        Returns:
            验证结果
        """
        try:
            result = self.script_service.validate_script(path)
            
            if result['success']:
                # 更新脚本状态
                script = self.get_script_by_path(path)
                if script:
                    script['is_valid'] = result['is_valid']
                    script['validation_errors'] = result.get('errors', [])
                    self.script_updated.emit(script)
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error validating script: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_script_info(self, path: str) -> Dict:
        """获取脚本详细信息
        
        Args:
            path: 脚本路径
            
        Returns:
            脚本详细信息
        """
        try:
            result = self.script_service.get_script_info(path)
            return result
        
        except Exception as e:
            self.logger.error(f"Error getting script info: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_statistics(self) -> Dict:
        """获取脚本统计信息
        
        Returns:
            统计信息
        """
        total = len(self._scripts)
        by_category = {cat: len(scripts) for cat, scripts in self._categories.items()}
        
        return {
            'total': total,
            'by_category': by_category,
            'categories': list(self._categories.keys())
        }