"""权限检查装饰器

提供基于角色的访问控制装饰器。
"""

from functools import wraps
from typing import Callable, List, Optional
import tkinter as tk
from tkinter import messagebox


def require_login(func: Callable) -> Callable:
    """要求用户登录的装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # 检查是否有用户服务和当前用户
        if not hasattr(self, 'user_service'):
            messagebox.showerror("错误", "用户服务未初始化")
            return None
        
        if not hasattr(self, 'current_token') or not self.current_token:
            messagebox.showwarning("需要登录", "请先登录")
            return None
        
        # 验证令牌
        user = self.user_service.verify_token(self.current_token)
        if not user:
            messagebox.showwarning("会话过期", "登录会话已过期，请重新登录")
            self.current_token = None
            return None
        
        # 执行原函数
        return func(self, *args, **kwargs)
    
    return wrapper


def require_permission(permission: str) -> Callable:
    """要求特定权限的装饰器
    
    Args:
        permission: 所需权限
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 检查是否有用户服务和当前令牌
            if not hasattr(self, 'user_service'):
                messagebox.showerror("错误", "用户服务未初始化")
                return None
            
            if not hasattr(self, 'current_token') or not self.current_token:
                messagebox.showwarning("需要登录", "请先登录")
                return None
            
            # 检查权限
            if not self.user_service.check_permission(self.current_token, permission):
                messagebox.showerror("权限不足", f"您没有'{permission}'权限")
                return None
            
            # 执行原函数
            return func(self, *args, **kwargs)
        
        return wrapper
    
    return decorator


def require_role(role: str) -> Callable:
    """要求特定角色的装饰器
    
    Args:
        role: 所需角色
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 检查是否有用户服务和当前令牌
            if not hasattr(self, 'user_service'):
                messagebox.showerror("错误", "用户服务未初始化")
                return None
            
            if not hasattr(self, 'current_token') or not self.current_token:
                messagebox.showwarning("需要登录", "请先登录")
                return None
            
            # 验证令牌并检查角色
            user = self.user_service.verify_token(self.current_token)
            if not user:
                messagebox.showwarning("会话过期", "登录会话已过期，请重新登录")
                self.current_token = None
                return None
            
            if user.get('role') != role:
                messagebox.showerror("权限不足", f"需要'{role}'角色")
                return None
            
            # 执行原函数
            return func(self, *args, **kwargs)
        
        return wrapper
    
    return decorator


def require_admin(func: Callable) -> Callable:
    """要求管理员权限的装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    return require_role('admin')(func)


def confirm_action(message: str = "确定要执行此操作吗？", title: str = "确认") -> Callable:
    """需要用户确认的装饰器
    
    Args:
        message: 确认消息
        title: 对话框标题
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 显示确认对话框
            if not messagebox.askyesno(title, message):
                return None
            
            # 执行原函数
            return func(self, *args, **kwargs)
        
        return wrapper
    
    return decorator


def log_action(action_name: str) -> Callable:
    """记录操作日志的装饰器
    
    Args:
        action_name: 操作名称
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 记录操作开始
            if hasattr(self, 'logger'):
                user_info = "Unknown"
                if hasattr(self, 'current_token') and hasattr(self, 'user_service'):
                    user = self.user_service.verify_token(self.current_token)
                    if user:
                        user_info = user.get('username', 'Unknown')
                
                self.logger.info(f"User '{user_info}' started action: {action_name}")
            
            try:
                # 执行原函数
                result = func(self, *args, **kwargs)
                
                # 记录操作成功
                if hasattr(self, 'logger'):
                    self.logger.info(f"Action '{action_name}' completed successfully")
                
                return result
            
            except Exception as e:
                # 记录操作失败
                if hasattr(self, 'logger'):
                    self.logger.error(f"Action '{action_name}' failed: {e}")
                raise
        
        return wrapper
    
    return decorator


def handle_errors(error_message: str = "操作失败", show_dialog: bool = True) -> Callable:
    """错误处理装饰器
    
    Args:
        error_message: 错误消息前缀
        show_dialog: 是否显示错误对话框
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            
            except Exception as e:
                # 记录错误
                if hasattr(self, 'logger'):
                    self.logger.error(f"{error_message}: {e}", exc_info=True)
                
                # 显示错误对话框
                if show_dialog:
                    messagebox.showerror("错误", f"{error_message}: {str(e)}")
                
                return None
        
        return wrapper
    
    return decorator


# 组合装饰器示例
def require_admin_with_confirm(message: str = "此操作需要管理员权限，确定继续吗？") -> Callable:
    """要求管理员权限并需要确认的组合装饰器
    
    Args:
        message: 确认消息
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @require_admin
        @confirm_action(message)
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)
        
        return wrapper
    
    return decorator