"""测试方案服务

提供测试方案管理的业务逻辑。
"""

from typing import List, Dict, Any, Optional
import os


class TestSuiteService:
    """测试方案服务"""
    
    def __init__(self, container):
        """初始化服务
        
        Args:
            container: 依赖注入容器
        """
        self.container = container
        self.logger = container.resolve('log_manager').get_logger('test_suite_service')
        self.suite_repo = container.resolve('test_suite_repository')
    
    def create_suite(
        self,
        name: str,
        script_paths: List[str],
        description: str = "",
        created_by: str = ""
    ) -> Dict[str, Any]:
        """创建测试方案
        
        Args:
            name: 方案名称
            script_paths: 脚本路径列表
            description: 方案描述
            created_by: 创建者
            
        Returns:
            结果字典，包含success和suite_id或error
        """
        try:
            # 验证输入
            if not name or not name.strip():
                return {
                    'success': False,
                    'error': '方案名称不能为空'
                }
            
            if not script_paths:
                return {
                    'success': False,
                    'error': '脚本列表不能为空'
                }
            
            # 验证脚本路径
            invalid_paths = []
            for path in script_paths:
                if not os.path.exists(path):
                    invalid_paths.append(path)
            
            if invalid_paths:
                self.logger.warning(f"Some script paths do not exist: {invalid_paths}")
                # 不阻止创建，只记录警告
            
            # 创建方案
            suite = self.suite_repo.create_suite(
                name=name.strip(),
                script_paths=script_paths,
                description=description.strip() if description else "",
                created_by=created_by
            )
            
            if suite:
                self.logger.info(f"Test suite created: {name} with {len(script_paths)} scripts")
                return {
                    'success': True,
                    'suite_id': suite['id'],
                    'suite': suite
                }
            else:
                return {
                    'success': False,
                    'error': '方案名称已存在'
                }
        
        except Exception as e:
            self.logger.error(f"Error creating test suite: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_suite(
        self,
        suite_id: int,
        name: str = None,
        script_paths: List[str] = None,
        description: str = None
    ) -> Dict[str, Any]:
        """更新测试方案
        
        Args:
            suite_id: 方案ID
            name: 新名称（可选）
            script_paths: 新脚本列表（可选）
            description: 新描述（可选）
            
        Returns:
            结果字典
        """
        try:
            # 验证方案存在
            suite = self.suite_repo.get_by_id(suite_id)
            if not suite:
                return {
                    'success': False,
                    'error': '方案不存在'
                }
            
            # 更新方案
            success = self.suite_repo.update_suite(
                suite_id=suite_id,
                name=name,
                script_paths=script_paths,
                description=description
            )
            
            if success:
                self.logger.info(f"Test suite updated: ID {suite_id}")
                return {
                    'success': True,
                    'suite': self.suite_repo.get_by_id(suite_id)
                }
            else:
                return {
                    'success': False,
                    'error': '更新失败，可能是名称冲突'
                }
        
        except Exception as e:
            self.logger.error(f"Error updating test suite: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_suite(self, suite_id: int) -> Dict[str, Any]:
        """删除测试方案
        
        Args:
            suite_id: 方案ID
            
        Returns:
            结果字典
        """
        try:
            # 验证方案存在
            suite = self.suite_repo.get_by_id(suite_id)
            if not suite:
                return {
                    'success': False,
                    'error': '方案不存在'
                }
            
            # 删除方案
            success = self.suite_repo.delete_suite(suite_id)
            
            if success:
                self.logger.info(f"Test suite deleted: ID {suite_id}")
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': '删除失败'
                }
        
        except Exception as e:
            self.logger.error(f"Error deleting test suite: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_suite(self, suite_id: int) -> Optional[Dict[str, Any]]:
        """获取方案详情
        
        Args:
            suite_id: 方案ID
            
        Returns:
            方案信息
        """
        try:
            return self.suite_repo.export_suite(suite_id)
        except Exception as e:
            self.logger.error(f"Error getting test suite: {e}", exc_info=True)
            return None
    
    def get_suite_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取方案
        
        Args:
            name: 方案名称
            
        Returns:
            方案信息
        """
        try:
            suite = self.suite_repo.get_by_name(name)
            if suite:
                return self.suite_repo.export_suite(suite['id'])
            return None
        except Exception as e:
            self.logger.error(f"Error getting test suite by name: {e}", exc_info=True)
            return None
    
    def list_suites(self) -> List[Dict[str, Any]]:
        """获取所有方案列表
        
        Returns:
            方案列表
        """
        try:
            return self.suite_repo.get_all()
        except Exception as e:
            self.logger.error(f"Error listing test suites: {e}", exc_info=True)
            return []
    
    def get_recent_suites(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近使用的方案
        
        Args:
            limit: 返回数量限制
            
        Returns:
            方案列表
        """
        try:
            return self.suite_repo.get_recent_suites(limit)
        except Exception as e:
            self.logger.error(f"Error getting recent suites: {e}", exc_info=True)
            return []
    
    def get_popular_suites(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最常用的方案
        
        Args:
            limit: 返回数量限制
            
        Returns:
            方案列表
        """
        try:
            return self.suite_repo.get_popular_suites(limit)
        except Exception as e:
            self.logger.error(f"Error getting popular suites: {e}", exc_info=True)
            return []
    
    def search_suites(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索方案
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的方案列表
        """
        try:
            return self.suite_repo.search_suites(keyword)
        except Exception as e:
            self.logger.error(f"Error searching test suites: {e}", exc_info=True)
            return []
    
    def get_suite_scripts(self, suite_id: int) -> List[str]:
        """获取方案的脚本列表
        
        Args:
            suite_id: 方案ID
            
        Returns:
            脚本路径列表
        """
        try:
            return self.suite_repo.get_suite_scripts(suite_id)
        except Exception as e:
            self.logger.error(f"Error getting suite scripts: {e}", exc_info=True)
            return []
    
    def record_execution(self, suite_id: int) -> bool:
        """记录方案执行
        
        Args:
            suite_id: 方案ID
            
        Returns:
            是否成功
        """
        try:
            success = self.suite_repo.increment_execution_count(suite_id)
            if success:
                self.logger.info(f"Recorded execution for suite ID {suite_id}")
            return success
        except Exception as e:
            self.logger.error(f"Error recording suite execution: {e}", exc_info=True)
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取方案统计信息
        
        Returns:
            统计信息
        """
        try:
            return self.suite_repo.get_statistics()
        except Exception as e:
            self.logger.error(f"Error getting suite statistics: {e}", exc_info=True)
            return {
                'total_suites': 0,
                'total_scripts': 0,
                'total_executions': 0,
                'average_scripts_per_suite': 0,
                'average_executions_per_suite': 0
            }
    
    def export_suite_to_file(self, suite_id: int, file_path: str) -> Dict[str, Any]:
        """导出方案到文件
        
        Args:
            suite_id: 方案ID
            file_path: 文件路径
            
        Returns:
            结果字典
        """
        try:
            import json
            
            suite = self.suite_repo.export_suite(suite_id)
            if not suite:
                return {
                    'success': False,
                    'error': '方案不存在'
                }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(suite, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Suite exported to: {file_path}")
            return {'success': True}
        
        except Exception as e:
            self.logger.error(f"Error exporting suite: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def import_suite_from_file(self, file_path: str) -> Dict[str, Any]:
        """从文件导入方案
        
        Args:
            file_path: 文件路径
            
        Returns:
            结果字典
        """
        try:
            import json
            
            with open(file_path, 'r', encoding='utf-8') as f:
                suite_data = json.load(f)
            
            suite_id = self.suite_repo.import_suite(suite_data)
            if suite_id:
                self.logger.info(f"Suite imported from: {file_path}")
                return {
                    'success': True,
                    'suite_id': suite_id
                }
            else:
                return {
                    'success': False,
                    'error': '导入失败'
                }
        
        except Exception as e:
            self.logger.error(f"Error importing suite: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }