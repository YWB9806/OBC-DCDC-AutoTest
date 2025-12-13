"""运行所有测试的集成测试脚本"""

import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 发现并添加所有测试
    start_dir = os.path.dirname(__file__)
    suite.addTests(loader.discover(start_dir, pattern='test_*.py'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()


def run_specific_test(test_module):
    """运行特定测试模块
    
    Args:
        test_module: 测试模块名称（不含.py后缀）
    """
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_module)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def print_test_summary():
    """打印测试摘要"""
    print("\n" + "="*70)
    print("测试模块列表:")
    print("="*70)
    
    test_modules = [
        ('test_performance_monitor_service', '性能监控服务测试'),
        ('test_backup_service', '备份服务测试'),
        ('test_user_service', '用户服务测试'),
        ('test_plugin_manager', '插件管理器测试'),
    ]
    
    for module, description in test_modules:
        print(f"  - {module:40s} : {description}")
    
    print("="*70)
    print("\n使用方法:")
    print("  python run_all_tests.py              # 运行所有测试")
    print("  python run_all_tests.py <module>     # 运行特定测试模块")
    print("\n示例:")
    print("  python run_all_tests.py test_user_service")
    print("="*70 + "\n")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # 运行特定测试
        test_module = sys.argv[1]
        if not test_module.startswith('test_'):
            test_module = 'test_' + test_module
        
        print(f"\n运行测试模块: {test_module}\n")
        success = run_specific_test(test_module)
    else:
        # 运行所有测试
        print("\n运行所有测试...\n")
        success = run_all_tests()
    
    # 打印摘要
    print_test_summary()
    
    # 退出码
    sys.exit(0 if success else 1)