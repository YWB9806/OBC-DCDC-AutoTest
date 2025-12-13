"""测试方案仓储

管理测试方案数据。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from .base_repository import BaseRepository


class TestSuiteRepository(BaseRepository):
    """测试方案仓储"""
    
    def get_table_name(self) -> str:
        """获取表名"""
        return 'test_suites'
    
    def create_suite(
        self,
        name: str,
        script_paths: List[str],
        description: str = "",
        created_by: str = ""
    ) -> Optional[Dict[str, Any]]:
        """创建测试方案
        
        Args:
            name: 方案名称
            script_paths: 脚本路径列表
            description: 方案描述
            created_by: 创建者
            
        Returns:
            创建的方案信息，失败返回None
        """
        # 检查名称是否已存在
        existing = self.get_by_name(name)
        if existing:
            if self.logger:
                self.logger.warning(f"Test suite already exists: {name}")
            return None
        
        suite_data = {
            'name': name,
            'description': description,
            'script_paths': json.dumps(script_paths, ensure_ascii=False),
            'script_count': len(script_paths),
            'created_by': created_by,
            'created_time': datetime.now().isoformat(),
            'updated_time': datetime.now().isoformat(),
            'execution_count': 0
        }
        
        suite_id = self.create(suite_data)
        if suite_id:
            if self.logger:
                self.logger.info(f"Test suite created: {name} (ID: {suite_id})")
            return self.get_by_id(suite_id)
        
        return None
    
    def update_suite(
        self,
        suite_id: int,
        name: str = None,
        script_paths: List[str] = None,
        description: str = None
    ) -> bool:
        """更新测试方案
        
        Args:
            suite_id: 方案ID
            name: 新名称（可选）
            script_paths: 新脚本列表（可选）
            description: 新描述（可选）
            
        Returns:
            是否成功
        """
        update_data = {
            'updated_time': datetime.now().isoformat()
        }
        
        if name is not None:
            # 检查新名称是否与其他方案冲突
            existing = self.get_by_name(name)
            if existing and existing['id'] != suite_id:
                if self.logger:
                    self.logger.warning(f"Suite name already exists: {name}")
                return False
            update_data['name'] = name
        
        if script_paths is not None:
            update_data['script_paths'] = json.dumps(script_paths, ensure_ascii=False)
            update_data['script_count'] = len(script_paths)
        
        if description is not None:
            update_data['description'] = description
        
        success = self.update(suite_id, update_data)
        if success and self.logger:
            self.logger.info(f"Test suite updated: ID {suite_id}")
        
        return success
    
    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取方案
        
        Args:
            name: 方案名称
            
        Returns:
            方案信息
        """
        # 去除首尾空格后查询
        results = self.query({'name': name.strip() if name else ''})
        return results[0] if results else None
    
    def get_suite_scripts(self, suite_id: int) -> List[str]:
        """获取方案的脚本列表
        
        Args:
            suite_id: 方案ID
            
        Returns:
            脚本路径列表
        """
        suite = self.get_by_id(suite_id)
        if suite and suite.get('script_paths'):
            try:
                return json.loads(suite['script_paths'])
            except json.JSONDecodeError:
                if self.logger:
                    self.logger.error(f"Failed to parse script_paths for suite {suite_id}")
                return []
        return []
    
    def increment_execution_count(self, suite_id: int) -> bool:
        """增加执行次数
        
        Args:
            suite_id: 方案ID
            
        Returns:
            是否成功
        """
        suite = self.get_by_id(suite_id)
        if not suite:
            return False
        
        current_count = suite.get('execution_count', 0)
        return self.update(suite_id, {
            'execution_count': current_count + 1,
            'last_executed_time': datetime.now().isoformat()
        })
    
    def get_recent_suites(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近使用的方案
        
        Args:
            limit: 返回数量限制
            
        Returns:
            方案列表
        """
        all_suites = self.get_all()
        
        # 按最后执行时间排序
        sorted_suites = sorted(
            all_suites,
            key=lambda x: x.get('last_executed_time', ''),
            reverse=True
        )
        
        return sorted_suites[:limit]
    
    def get_popular_suites(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最常用的方案
        
        Args:
            limit: 返回数量限制
            
        Returns:
            方案列表
        """
        all_suites = self.get_all()
        
        # 按执行次数排序
        sorted_suites = sorted(
            all_suites,
            key=lambda x: x.get('execution_count', 0),
            reverse=True
        )
        
        return sorted_suites[:limit]
    
    def search_suites(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索方案
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的方案列表
        """
        all_suites = self.get_all()
        keyword_lower = keyword.lower()
        
        results = []
        for suite in all_suites:
            name = suite.get('name', '').lower()
            description = suite.get('description', '').lower()
            
            if keyword_lower in name or keyword_lower in description:
                results.append(suite)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取方案统计信息
        
        Returns:
            统计信息
        """
        all_suites = self.get_all()
        
        total_scripts = 0
        total_executions = 0
        
        for suite in all_suites:
            total_scripts += suite.get('script_count', 0)
            total_executions += suite.get('execution_count', 0)
        
        stats = {
            'total_suites': len(all_suites),
            'total_scripts': total_scripts,
            'total_executions': total_executions,
            'average_scripts_per_suite': total_scripts / len(all_suites) if all_suites else 0,
            'average_executions_per_suite': total_executions / len(all_suites) if all_suites else 0
        }
        
        return stats
    
    def delete_suite(self, suite_id: int) -> bool:
        """删除测试方案
        
        Args:
            suite_id: 方案ID
            
        Returns:
            是否成功
        """
        success = self.delete(suite_id)
        if success and self.logger:
            self.logger.info(f"Test suite deleted: ID {suite_id}")
        return success
    
    def export_suite(self, suite_id: int) -> Optional[Dict[str, Any]]:
        """导出方案（包含完整信息）
        
        Args:
            suite_id: 方案ID
            
        Returns:
            方案完整信息
        """
        suite = self.get_by_id(suite_id)
        if not suite:
            return None
        
        # 解析脚本路径
        if suite.get('script_paths'):
            try:
                suite['script_paths'] = json.loads(suite['script_paths'])
            except json.JSONDecodeError:
                pass
        
        return suite
    
    def import_suite(self, suite_data: Dict[str, Any]) -> Optional[int]:
        """导入方案
        
        Args:
            suite_data: 方案数据
            
        Returns:
            新方案ID，失败返回None
        """
        # 确保必要字段存在
        if 'name' not in suite_data or 'script_paths' not in suite_data:
            if self.logger:
                self.logger.error("Invalid suite data for import")
            return None
        
        # 检查名称冲突
        name = suite_data['name']
        existing = self.get_by_name(name)
        if existing:
            # 自动重命名
            counter = 1
            while existing:
                new_name = f"{name} ({counter})"
                existing = self.get_by_name(new_name)
                counter += 1
            name = new_name
        
        # 创建新方案
        script_paths = suite_data['script_paths']
        if isinstance(script_paths, str):
            try:
                script_paths = json.loads(script_paths)
            except json.JSONDecodeError:
                script_paths = []
        
        # create_suite返回方案对象，需要提取ID
        suite = self.create_suite(
            name=name,
            script_paths=script_paths,
            description=suite_data.get('description', ''),
            created_by=suite_data.get('created_by', '')
        )
        
        return suite['id'] if suite else None