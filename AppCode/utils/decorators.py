"""装饰器模块

提供各种装饰器功能。
"""

import time
import functools
from typing import Callable, Any
from datetime import datetime

from .exceptions import PermissionError, ValidationError


def timer(func: Callable) -> Callable:
    """计时装饰器
    
    记录函数执行时间。
    
    Example:
        @timer
        def slow_function():
            time.sleep(1)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        print(f"[TIMER] {func.__name__} took {duration:.4f} seconds")
        return result
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0, 
         exceptions: tuple = (Exception,)) -> Callable:
    """重试装饰器
    
    在函数失败时自动重试。
    
    Args:
        max_attempts: 最大尝试次数
        delay: 重试延迟（秒）
        exceptions: 需要重试的异常类型
    
    Example:
        @retry(max_attempts=3, delay=1.0)
        def unstable_function():
            # 可能失败的操作
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        print(f"[RETRY] Attempt {attempt + 1} failed, retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        print(f"[RETRY] All {max_attempts} attempts failed")
            raise last_exception
        return wrapper
    return decorator


def validate_args(**validators) -> Callable:
    """参数验证装饰器
    
    验证函数参数。
    
    Args:
        **validators: 参数名到验证函数的映射
    
    Example:
        @validate_args(
            name=lambda x: len(x) > 0,
            age=lambda x: x > 0
        )
        def create_user(name: str, age: int):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数参数名
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # 验证参数
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise ValidationError(
                            f"Validation failed for parameter: {param_name}",
                            param_name
                        )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(permission: str) -> Callable:
    """权限检查装饰器
    
    检查用户是否有指定权限。
    
    Args:
        permission: 需要的权限
    
    Example:
        @require_permission("execute_scripts")
        def execute_script(self, user_id: str, script_id: str):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, user_id: str, *args, **kwargs):
            # 假设self有permission_manager属性
            if hasattr(self, 'permission_manager'):
                if not self.permission_manager.check_permission(user_id, permission):
                    raise PermissionError(user_id, permission)
            return func(self, user_id, *args, **kwargs)
        return wrapper
    return decorator


def cache_result(ttl: int = 3600) -> Callable:
    """结果缓存装饰器
    
    缓存函数返回结果。
    
    Args:
        ttl: 缓存过期时间（秒）
    
    Example:
        @cache_result(ttl=300)
        def expensive_computation(x: int) -> int:
            return x ** 2
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 创建缓存键
            key = str(args) + str(kwargs)
            
            # 检查缓存
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl:
                    return result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache[key] = (result, time.time())
            return result
        
        # 添加清除缓存的方法
        wrapper.clear_cache = lambda: cache.clear()
        return wrapper
    return decorator


def log_execution(logger=None) -> Callable:
    """执行日志装饰器
    
    记录函数执行日志。
    
    Args:
        logger: 日志记录器
    
    Example:
        @log_execution(logger)
        def important_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            if logger:
                logger.info(f"Executing {func_name}")
            
            try:
                result = func(*args, **kwargs)
                if logger:
                    logger.info(f"{func_name} completed successfully")
                return result
            except Exception as e:
                if logger:
                    logger.error(f"{func_name} failed: {e}")
                raise
        return wrapper
    return decorator


def singleton(cls):
    """单例装饰器
    
    确保类只有一个实例。
    
    Example:
        @singleton
        class ConfigManager:
            pass
    """
    instances = {}
    
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


def deprecated(message: str = None) -> Callable:
    """废弃警告装饰器
    
    标记函数为废弃状态。
    
    Args:
        message: 警告消息
    
    Example:
        @deprecated("Use new_function instead")
        def old_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warning_msg = f"Function {func.__name__} is deprecated"
            if message:
                warning_msg += f": {message}"
            print(f"[WARNING] {warning_msg}")
            return func(*args, **kwargs)
        return wrapper
    return decorator