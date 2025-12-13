"""插件管理器

负责插件的加载、管理和执行。
"""

import os
import importlib.util
import inspect
from typing import Dict, Any, List, Optional, Type
from pathlib import Path

from AppCode.interfaces.i_plugin import IPlugin, IReportPlugin, IAnalyzerPlugin, INotificationPlugin


class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugin_dir: str, logger=None):
        """初始化插件管理器
        
        Args:
            plugin_dir: 插件目录
            logger: 日志记录器
        """
        self.plugin_dir = plugin_dir
        self.logger = logger
        
        self._plugins = {}  # plugin_name -> plugin_instance
        self._plugin_classes = {}  # plugin_name -> plugin_class
        self._context = {}
        
        # 确保插件目录存在
        Path(plugin_dir).mkdir(parents=True, exist_ok=True)
    
    def set_context(self, context: Dict[str, Any]):
        """设置应用上下文
        
        Args:
            context: 应用上下文
        """
        self._context = context
    
    def load_plugins(self) -> int:
        """加载所有插件
        
        Returns:
            加载的插件数量
        """
        loaded_count = 0
        
        try:
            # 遍历插件目录
            for filename in os.listdir(self.plugin_dir):
                if filename.endswith('.py') and not filename.startswith('_'):
                    plugin_path = os.path.join(self.plugin_dir, filename)
                    
                    if self._load_plugin_from_file(plugin_path):
                        loaded_count += 1
            
            if self.logger:
                self.logger.info(f"Loaded {loaded_count} plugins")
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading plugins: {e}")
        
        return loaded_count
    
    def load_plugin(self, plugin_path: str) -> bool:
        """加载单个插件
        
        Args:
            plugin_path: 插件文件路径
            
        Returns:
            是否加载成功
        """
        return self._load_plugin_from_file(plugin_path)
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否卸载成功
        """
        try:
            if plugin_name in self._plugins:
                plugin = self._plugins[plugin_name]
                plugin.cleanup()
                
                del self._plugins[plugin_name]
                del self._plugin_classes[plugin_name]
                
                if self.logger:
                    self.logger.info(f"Plugin unloaded: {plugin_name}")
                
                return True
            
            return False
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """获取插件实例
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件实例
        """
        return self._plugins.get(plugin_name)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件
        
        Returns:
            插件信息列表
        """
        plugins_info = []
        
        for name, plugin in self._plugins.items():
            try:
                info = {
                    'name': plugin.get_name(),
                    'version': plugin.get_version(),
                    'description': plugin.get_description(),
                    'author': plugin.get_author(),
                    'type': self._get_plugin_type(plugin)
                }
                plugins_info.append(info)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error getting plugin info for {name}: {e}")
        
        return plugins_info
    
    def get_plugins_by_type(self, plugin_type: Type[IPlugin]) -> List[IPlugin]:
        """根据类型获取插件
        
        Args:
            plugin_type: 插件类型
            
        Returns:
            插件列表
        """
        return [
            plugin for plugin in self._plugins.values()
            if isinstance(plugin, plugin_type)
        ]
    
    def execute_plugin(
        self,
        plugin_name: str,
        *args,
        **kwargs
    ) -> Any:
        """执行插件
        
        Args:
            plugin_name: 插件名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            执行结果
        """
        plugin = self.get_plugin(plugin_name)
        
        if not plugin:
            raise ValueError(f"Plugin not found: {plugin_name}")
        
        try:
            return plugin.execute(*args, **kwargs)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error executing plugin {plugin_name}: {e}")
            raise
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """重新加载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否成功
        """
        try:
            # 获取插件文件路径
            if plugin_name not in self._plugin_classes:
                return False
            
            plugin_class = self._plugin_classes[plugin_name]
            module = inspect.getmodule(plugin_class)
            
            if not module or not hasattr(module, '__file__'):
                return False
            
            plugin_path = module.__file__
            
            # 卸载插件
            self.unload_plugin(plugin_name)
            
            # 重新加载模块（清除缓存）
            import sys
            if module.__name__ in sys.modules:
                importlib.reload(sys.modules[module.__name__])
            
            # 重新加载插件
            success = self._load_plugin_from_file(plugin_path)
            
            if success and self.logger:
                self.logger.info(f"Plugin reloaded: {plugin_name}")
            
            return success
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error reloading plugin {plugin_name}: {e}")
            return False
    
    def _load_plugin_from_file(self, plugin_path: str) -> bool:
        """从文件加载插件
        
        Args:
            plugin_path: 插件文件路径
            
        Returns:
            是否加载成功
        """
        try:
            # 加载模块
            module_name = Path(plugin_path).stem
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            
            if not spec or not spec.loader:
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找插件类
            plugin_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, IPlugin) and 
                    obj is not IPlugin and
                    obj is not IReportPlugin and
                    obj is not IAnalyzerPlugin and
                    obj is not INotificationPlugin):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                if self.logger:
                    self.logger.warning(f"No plugin class found in {plugin_path}")
                return False
            
            # 实例化插件
            plugin = plugin_class()
            
            # 初始化插件
            if not plugin.initialize(self._context):
                if self.logger:
                    self.logger.error(f"Plugin initialization failed: {plugin.get_name()}")
                return False
            
            # 注册插件
            plugin_name = plugin.get_name()
            self._plugins[plugin_name] = plugin
            self._plugin_classes[plugin_name] = plugin_class
            
            if self.logger:
                self.logger.info(f"Plugin loaded: {plugin_name} v{plugin.get_version()}")
            
            return True
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading plugin from {plugin_path}: {e}")
            return False
    
    def _get_plugin_type(self, plugin: IPlugin) -> str:
        """获取插件类型
        
        Args:
            plugin: 插件实例
            
        Returns:
            插件类型
        """
        if isinstance(plugin, IReportPlugin):
            return "Report"
        elif isinstance(plugin, IAnalyzerPlugin):
            return "Analyzer"
        elif isinstance(plugin, INotificationPlugin):
            return "Notification"
        else:
            return "Generic"
    
    def cleanup(self):
        """清理所有插件"""
        for plugin_name in list(self._plugins.keys()):
            self.unload_plugin(plugin_name)
        
        if self.logger:
            self.logger.info("All plugins cleaned up")