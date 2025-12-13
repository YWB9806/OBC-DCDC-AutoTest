"""插件管理器单元测试"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
import shutil

from AppCode.core.plugin_manager import PluginManager
from AppCode.interfaces.i_plugin import IPlugin, IReportPlugin


class MockPlugin(IPlugin):
    """模拟插件类"""
    
    def __init__(self):
        self._initialized = False
    
    def get_name(self) -> str:
        return "MockPlugin"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_description(self) -> str:
        return "A mock plugin for testing"
    
    def get_author(self) -> str:
        return "Test Author"
    
    def initialize(self, context: dict) -> bool:
        self._initialized = True
        return True
    
    def execute(self, *args, **kwargs):
        return "Mock execution result"
    
    def cleanup(self):
        self._initialized = False
    
    def get_config_schema(self) -> dict:
        return {'param1': 'string', 'param2': 'int'}
    
    def update_config(self, config: dict):
        pass


class TestPluginManager(unittest.TestCase):
    """插件管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时插件目录
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_dir = os.path.join(self.temp_dir, 'plugins')
        os.makedirs(self.plugin_dir)
        
        self.mock_logger = Mock()
        self.manager = PluginManager(self.plugin_dir, self.mock_logger)
    
    def tearDown(self):
        """测试后清理"""
        self.manager.cleanup()
        
        # 删除临时目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.manager)
        self.assertEqual(self.manager.plugin_dir, self.plugin_dir)
        self.assertTrue(os.path.exists(self.plugin_dir))
    
    def test_set_context(self):
        """测试设置上下文"""
        context = {'app': 'test', 'version': '1.0'}
        
        self.manager.set_context(context)
        
        self.assertEqual(self.manager._context, context)
    
    def _create_test_plugin_file(self, filename: str, plugin_class_name: str = "TestPlugin"):
        """创建测试插件文件"""
        plugin_code = f'''
from AppCode.interfaces.i_plugin import IPlugin

class {plugin_class_name}(IPlugin):
    def get_name(self) -> str:
        return "{plugin_class_name}"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_description(self) -> str:
        return "Test plugin"
    
    def get_author(self) -> str:
        return "Test"
    
    def initialize(self, context: dict) -> bool:
        return True
    
    def execute(self, *args, **kwargs):
        return "test result"
    
    def cleanup(self):
        pass
    
    def get_config_schema(self) -> dict:
        return {{}}
    
    def update_config(self, config: dict):
        pass
'''
        plugin_path = os.path.join(self.plugin_dir, filename)
        with open(plugin_path, 'w') as f:
            f.write(plugin_code)
        
        return plugin_path
    
    def test_load_plugin(self):
        """测试加载插件"""
        plugin_path = self._create_test_plugin_file('test_plugin.py')
        
        success = self.manager.load_plugin(plugin_path)
        
        self.assertTrue(success)
        self.assertIn('TestPlugin', self.manager._plugins)
    
    def test_load_plugins(self):
        """测试批量加载插件"""
        # 创建多个插件文件
        self._create_test_plugin_file('plugin1.py', 'Plugin1')
        self._create_test_plugin_file('plugin2.py', 'Plugin2')
        
        count = self.manager.load_plugins()
        
        self.assertEqual(count, 2)
        self.assertIn('Plugin1', self.manager._plugins)
        self.assertIn('Plugin2', self.manager._plugins)
    
    def test_unload_plugin(self):
        """测试卸载插件"""
        plugin_path = self._create_test_plugin_file('test_plugin.py')
        self.manager.load_plugin(plugin_path)
        
        success = self.manager.unload_plugin('TestPlugin')
        
        self.assertTrue(success)
        self.assertNotIn('TestPlugin', self.manager._plugins)
    
    def test_get_plugin(self):
        """测试获取插件"""
        plugin_path = self._create_test_plugin_file('test_plugin.py')
        self.manager.load_plugin(plugin_path)
        
        plugin = self.manager.get_plugin('TestPlugin')
        
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.get_name(), 'TestPlugin')
    
    def test_list_plugins(self):
        """测试列出插件"""
        self._create_test_plugin_file('plugin1.py', 'Plugin1')
        self._create_test_plugin_file('plugin2.py', 'Plugin2')
        self.manager.load_plugins()
        
        plugins = self.manager.list_plugins()
        
        self.assertEqual(len(plugins), 2)
        self.assertIn('name', plugins[0])
        self.assertIn('version', plugins[0])
        self.assertIn('description', plugins[0])
    
    def test_execute_plugin(self):
        """测试执行插件"""
        plugin_path = self._create_test_plugin_file('test_plugin.py')
        self.manager.load_plugin(plugin_path)
        
        result = self.manager.execute_plugin('TestPlugin')
        
        self.assertEqual(result, 'test result')
    
    def test_execute_nonexistent_plugin(self):
        """测试执行不存在的插件"""
        with self.assertRaises(ValueError):
            self.manager.execute_plugin('NonexistentPlugin')
    
    def test_reload_plugin(self):
        """测试重新加载插件"""
        plugin_path = self._create_test_plugin_file('test_plugin.py')
        self.manager.load_plugin(plugin_path)
        
        # 修改插件文件
        with open(plugin_path, 'a') as f:
            f.write('\n# Modified\n')
        
        success = self.manager.reload_plugin('TestPlugin')
        
        self.assertTrue(success)
        self.assertIn('TestPlugin', self.manager._plugins)
    
    def test_get_plugins_by_type(self):
        """测试按类型获取插件"""
        # 创建报告插件
        report_plugin_code = '''
from AppCode.interfaces.i_plugin import IReportPlugin

class ReportPlugin(IReportPlugin):
    def get_name(self) -> str:
        return "ReportPlugin"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_description(self) -> str:
        return "Report plugin"
    
    def get_author(self) -> str:
        return "Test"
    
    def initialize(self, context: dict) -> bool:
        return True
    
    def execute(self, *args, **kwargs):
        return "report"
    
    def cleanup(self):
        pass
    
    def get_config_schema(self) -> dict:
        return {}
    
    def update_config(self, config: dict):
        pass
    
    def generate_report(self, data: dict) -> str:
        return "test report"
    
    def get_supported_formats(self) -> list:
        return ['html']
    
    def save_report(self, report: str, file_path: str) -> bool:
        return True
'''
        plugin_path = os.path.join(self.plugin_dir, 'report_plugin.py')
        with open(plugin_path, 'w') as f:
            f.write(report_plugin_code)
        
        self.manager.load_plugin(plugin_path)
        
        # 获取报告插件
        report_plugins = self.manager.get_plugins_by_type(IReportPlugin)
        
        self.assertEqual(len(report_plugins), 1)
        self.assertEqual(report_plugins[0].get_name(), 'ReportPlugin')
    
    def test_cleanup(self):
        """测试清理所有插件"""
        self._create_test_plugin_file('plugin1.py', 'Plugin1')
        self._create_test_plugin_file('plugin2.py', 'Plugin2')
        self.manager.load_plugins()
        
        self.manager.cleanup()
        
        self.assertEqual(len(self.manager._plugins), 0)


class TestPluginManagerEdgeCases(unittest.TestCase):
    """插件管理器边界情况测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_dir = os.path.join(self.temp_dir, 'plugins')
        os.makedirs(self.plugin_dir)
        
        self.mock_logger = Mock()
        self.manager = PluginManager(self.plugin_dir, self.mock_logger)
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_load_invalid_plugin_file(self):
        """测试加载无效插件文件"""
        # 创建无效的Python文件
        invalid_path = os.path.join(self.plugin_dir, 'invalid.py')
        with open(invalid_path, 'w') as f:
            f.write('invalid python code {{{')
        
        success = self.manager.load_plugin(invalid_path)
        
        self.assertFalse(success)
    
    def test_load_plugin_no_plugin_class(self):
        """测试加载没有插件类的文件"""
        # 创建没有插件类的文件
        no_plugin_path = os.path.join(self.plugin_dir, 'no_plugin.py')
        with open(no_plugin_path, 'w') as f:
            f.write('# Just a comment\nprint("hello")')
        
        success = self.manager.load_plugin(no_plugin_path)
        
        self.assertFalse(success)
    
    def test_unload_nonexistent_plugin(self):
        """测试卸载不存在的插件"""
        success = self.manager.unload_plugin('NonexistentPlugin')
        
        self.assertFalse(success)
    
    def test_get_nonexistent_plugin(self):
        """测试获取不存在的插件"""
        plugin = self.manager.get_plugin('NonexistentPlugin')
        
        self.assertIsNone(plugin)
    
    def test_reload_nonexistent_plugin(self):
        """测试重新加载不存在的插件"""
        success = self.manager.reload_plugin('NonexistentPlugin')
        
        self.assertFalse(success)


if __name__ == '__main__':
    unittest.main()