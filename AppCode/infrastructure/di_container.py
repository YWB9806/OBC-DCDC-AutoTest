"""依赖注入容器

提供依赖注入和服务定位功能。
"""

from typing import Dict, Any, Callable, Type, Optional
from AppCode.utils.decorators import singleton


@singleton
class DIContainer:
    """依赖注入容器
    
    管理应用程序中的依赖关系和服务实例。
    采用单例模式确保全局统一的容器。
    """
    
    def __init__(self):
        """初始化容器"""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register(self, name: str, service: Any):
        """注册服务实例
        
        Args:
            name: 服务名称
            service: 服务实例
        """
        self._services[name] = service
    
    def register_factory(self, name: str, factory: Callable):
        """注册服务工厂
        
        Args:
            name: 服务名称
            factory: 工厂函数
        """
        self._factories[name] = factory
    
    def register_singleton(self, name: str, service_class: Type, *args, **kwargs):
        """注册单例服务
        
        Args:
            name: 服务名称
            service_class: 服务类
            *args: 构造参数
            **kwargs: 构造参数
        """
        if name not in self._singletons:
            self._singletons[name] = service_class(*args, **kwargs)
    
    def resolve(self, name: str) -> Any:
        """解析服务
        
        Args:
            name: 服务名称
            
        Returns:
            服务实例
            
        Raises:
            KeyError: 服务未注册时抛出
        """
        # 检查单例
        if name in self._singletons:
            return self._singletons[name]
        
        # 检查已注册的实例
        if name in self._services:
            return self._services[name]
        
        # 检查工厂
        if name in self._factories:
            return self._factories[name]()
        
        raise KeyError(f"Service not registered: {name}")
    
    def has(self, name: str) -> bool:
        """检查服务是否已注册
        
        Args:
            name: 服务名称
            
        Returns:
            是否已注册
        """
        return (name in self._services or 
                name in self._factories or 
                name in self._singletons)
    
    def remove(self, name: str):
        """移除服务
        
        Args:
            name: 服务名称
        """
        self._services.pop(name, None)
        self._factories.pop(name, None)
        self._singletons.pop(name, None)
    
    def clear(self):
        """清空所有服务"""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
    
    def get_all_services(self) -> Dict[str, str]:
        """获取所有已注册的服务
        
        Returns:
            服务名称到类型的映射
        """
        services = {}
        
        for name in self._services:
            services[name] = type(self._services[name]).__name__
        
        for name in self._factories:
            services[name] = "Factory"
        
        for name in self._singletons:
            services[name] = f"Singleton<{type(self._singletons[name]).__name__}>"
        
        return services


class ServiceLocator:
    """服务定位器
    
    提供便捷的服务访问方式。
    """
    
    _container: Optional[DIContainer] = None
    
    @classmethod
    def set_container(cls, container: DIContainer):
        """设置容器
        
        Args:
            container: DI容器实例
        """
        cls._container = container
    
    @classmethod
    def get(cls, name: str) -> Any:
        """获取服务
        
        Args:
            name: 服务名称
            
        Returns:
            服务实例
        """
        if cls._container is None:
            raise RuntimeError("Container not initialized")
        return cls._container.resolve(name)
    
    @classmethod
    def has(cls, name: str) -> bool:
        """检查服务是否存在
        
        Args:
            name: 服务名称
            
        Returns:
            是否存在
        """
        if cls._container is None:
            return False
        return cls._container.has(name)