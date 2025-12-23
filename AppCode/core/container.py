"""依赖注入容器

管理应用程序的依赖关系和对象生命周期。
"""

from typing import Dict, Any, Callable, Optional
import logging


class Container:
    """依赖注入容器"""
    
    _instance = None  # 单例实例
    
    @classmethod
    def get_instance(cls):
        """获取容器单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """初始化容器"""
        self._services = {}
        self._singletons = {}
        self._factories = {}
        
        # 注册核心服务
        self._register_core_services()
    
    def _register_core_services(self):
        """注册核心服务"""
        # 日志管理器
        self.register_singleton('log_manager', self._create_log_manager)
        
        # 配置管理器
        self.register_singleton('config_manager', self._create_config_manager)
        
        # 缓存管理器
        self.register_singleton('cache_manager', self._create_cache_manager)
        
        # 数据访问层
        self.register_singleton('data_access', self._create_data_access)
        
        # 仓储层
        self.register_singleton('execution_history_repo', self._create_execution_history_repo)
        self.register_singleton('batch_execution_repo', self._create_batch_execution_repo)
        self.register_singleton('performance_metrics_repo', self._create_performance_metrics_repo)
        self.register_singleton('user_repo', self._create_user_repo)
        self.register_singleton('test_suite_repository', self._create_test_suite_repo)
        
        # 核心层
        self.register_singleton('script_manager', self._create_script_manager)
        self.register_singleton('execution_engine', self._create_execution_engine)
        self.register_singleton('result_analyzer', self._create_result_analyzer)
        self.register_singleton('plugin_manager', self._create_plugin_manager)
        
        # 服务层
        self.register_singleton('script_service', self._create_script_service)
        self.register_singleton('execution_service', self._create_execution_service)
        self.register_singleton('analysis_service', self._create_analysis_service)
        self.register_singleton('performance_monitor_service', self._create_performance_monitor_service)
        self.register_singleton('backup_service', self._create_backup_service)
        self.register_singleton('user_service', self._create_user_service)
        self.register_singleton('test_suite_service', self._create_test_suite_service)
    
    def register_singleton(self, name: str, factory: Callable):
        """注册单例服务
        
        Args:
            name: 服务名称
            factory: 工厂函数
        """
        self._factories[name] = factory
    
    def register_transient(self, name: str, factory: Callable):
        """注册瞬态服务（每次都创建新实例）
        
        Args:
            name: 服务名称
            factory: 工厂函数
        """
        self._services[name] = factory
    
    def register_instance(self, name: str, instance: Any):
        """注册实例
        
        Args:
            name: 服务名称
            instance: 实例对象
        """
        self._singletons[name] = instance
    
    def resolve(self, name: str) -> Any:
        """解析服务
        
        Args:
            name: 服务名称
            
        Returns:
            服务实例
        """
        # 检查是否已有单例实例
        if name in self._singletons:
            return self._singletons[name]
        
        # 检查是否有工厂函数
        if name in self._factories:
            instance = self._factories[name]()
            self._singletons[name] = instance
            return instance
        
        # 检查是否有瞬态服务
        if name in self._services:
            return self._services[name]()
        
        raise KeyError(f"Service not found: {name}")
    
    def _create_log_manager(self):
        """创建日志管理器"""
        from AppCode.infrastructure.log_manager import LogManager
        return LogManager()
    
    def _create_config_manager(self):
        """创建配置管理器"""
        from AppCode.infrastructure.config_manager import ConfigManager
        return ConfigManager()
    
    def _create_cache_manager(self):
        """创建缓存管理器"""
        from AppCode.infrastructure.cache_manager import CacheManager
        return CacheManager()
    
    def _create_data_access(self):
        """创建数据访问层"""
        from AppCode.data_access.sqlite_data_access import SQLiteDataAccess
        config = self.resolve('config_manager')
        db_path = config.get('database.path', 'data/script_executor.db')
        return SQLiteDataAccess(db_path)
    
    def _create_execution_history_repo(self):
        """创建执行历史仓储"""
        from AppCode.repositories.execution_history_repository import ExecutionHistoryRepository
        data_access = self.resolve('data_access')
        return ExecutionHistoryRepository(data_access)
    
    def _create_batch_execution_repo(self):
        """创建批次执行仓储"""
        from AppCode.repositories.batch_execution_repository import BatchExecutionRepository
        data_access = self.resolve('data_access')
        return BatchExecutionRepository(data_access)
    
    def _create_script_manager(self):
        """创建脚本管理器"""
        from AppCode.core.script_manager import ScriptManager
        logger = self.resolve('log_manager').get_logger('script_manager')
        cache_manager = self.resolve('cache_manager')
        return ScriptManager(logger, cache_manager)
    
    def _create_execution_engine(self):
        """创建执行引擎"""
        from AppCode.core.execution_engine import ExecutionEngine
        logger = self.resolve('log_manager').get_logger('execution_engine')
        config_manager = self.resolve('config_manager')
        # 车载ECU测试必须顺序执行，硬件资源独占
        return ExecutionEngine(logger, max_workers=1, config_manager=config_manager)
    
    def _create_result_analyzer(self):
        """创建结果分析器"""
        from AppCode.core.result_analyzer import ResultAnalyzer
        logger = self.resolve('log_manager').get_logger('result_analyzer')
        data_access = self.resolve('data_access')
        return ResultAnalyzer(logger, data_access)
    
    def _create_script_service(self):
        """创建脚本服务"""
        from AppCode.services.script_service import ScriptService
        script_manager = self.resolve('script_manager')
        execution_repo = self.resolve('execution_history_repo')
        logger = self.resolve('log_manager').get_logger('script_service')
        cache_manager = self.resolve('cache_manager')
        return ScriptService(script_manager, execution_repo, logger, cache_manager)
    
    def _create_execution_service(self):
        """创建执行服务"""
        from AppCode.services.execution_service import ExecutionService
        execution_engine = self.resolve('execution_engine')
        execution_repo = self.resolve('execution_history_repo')
        batch_repo = self.resolve('batch_execution_repo')
        logger = self.resolve('log_manager').get_logger('execution_service')
        return ExecutionService(execution_engine, execution_repo, batch_repo, logger)
    
    def _create_analysis_service(self):
        """创建分析服务"""
        from AppCode.services.analysis_service import AnalysisService
        result_analyzer = self.resolve('result_analyzer')
        execution_repo = self.resolve('execution_history_repo')
        batch_repo = self.resolve('batch_execution_repo')
        logger = self.resolve('log_manager').get_logger('analysis_service')
        return AnalysisService(result_analyzer, execution_repo, batch_repo, logger)
    
    def _create_performance_metrics_repo(self):
        """创建性能指标仓储"""
        from AppCode.repositories.performance_metrics_repository import PerformanceMetricsRepository
        data_access = self.resolve('data_access')
        return PerformanceMetricsRepository(data_access)
    
    def _create_user_repo(self):
        """创建用户仓储"""
        from AppCode.repositories.user_repository import UserRepository
        data_access = self.resolve('data_access')
        return UserRepository(data_access)
    
    def _create_plugin_manager(self):
        """创建插件管理器"""
        from AppCode.core.plugin_manager import PluginManager
        import os
        logger = self.resolve('log_manager').get_logger('plugin_manager')
        plugin_dir = os.path.join(os.getcwd(), 'plugins')
        return PluginManager(plugin_dir, logger)
    
    def _create_performance_monitor_service(self):
        """创建性能监控服务"""
        from AppCode.services.performance_monitor_service import PerformanceMonitorService
        metrics_repo = self.resolve('performance_metrics_repo')
        logger = self.resolve('log_manager').get_logger('performance_monitor')
        return PerformanceMonitorService(metrics_repo, logger)
    
    def _create_backup_service(self):
        """创建备份服务"""
        from AppCode.services.backup_service import BackupService
        import os
        logger = self.resolve('log_manager').get_logger('backup_service')
        data_dir = 'data'
        backup_dir = os.path.join(data_dir, 'backups')
        return BackupService(data_dir, backup_dir, logger)
    
    def _create_user_service(self):
        """创建用户服务"""
        from AppCode.services.user_service import UserService
        user_repo = self.resolve('user_repo')
        logger = self.resolve('log_manager').get_logger('user_service')
        return UserService(user_repo, logger)
    
    def _create_test_suite_repo(self):
        """创建测试方案仓储"""
        from AppCode.repositories.test_suite_repository import TestSuiteRepository
        data_access = self.resolve('data_access')
        return TestSuiteRepository(data_access)
    
    def _create_test_suite_service(self):
        """创建测试方案服务"""
        from AppCode.services.test_suite_service import TestSuiteService
        return TestSuiteService(self)