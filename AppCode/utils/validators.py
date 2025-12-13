"""验证器模块

提供各种数据验证功能。
"""

import os
import re
from typing import Any, List, Optional
from pathlib import Path

from .exceptions import ValidationError


class Validator:
    """验证器基类"""
    
    @staticmethod
    def validate_not_empty(value: Any, field_name: str = "Value") -> Any:
        """验证值不为空
        
        Args:
            value: 要验证的值
            field_name: 字段名称
            
        Returns:
            验证通过的值
            
        Raises:
            ValidationError: 值为空时抛出
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{field_name} cannot be empty", field_name)
        return value
    
    @staticmethod
    def validate_type(value: Any, expected_type: type, field_name: str = "Value") -> Any:
        """验证值的类型
        
        Args:
            value: 要验证的值
            expected_type: 期望的类型
            field_name: 字段名称
            
        Returns:
            验证通过的值
            
        Raises:
            ValidationError: 类型不匹配时抛出
        """
        if not isinstance(value, expected_type):
            raise ValidationError(
                f"{field_name} must be {expected_type.__name__}, got {type(value).__name__}",
                field_name
            )
        return value
    
    @staticmethod
    def validate_range(value: int, min_val: int = None, max_val: int = None,
                      field_name: str = "Value") -> int:
        """验证数值范围
        
        Args:
            value: 要验证的值
            min_val: 最小值
            max_val: 最大值
            field_name: 字段名称
            
        Returns:
            验证通过的值
            
        Raises:
            ValidationError: 超出范围时抛出
        """
        if min_val is not None and value < min_val:
            raise ValidationError(
                f"{field_name} must be >= {min_val}, got {value}",
                field_name
            )
        if max_val is not None and value > max_val:
            raise ValidationError(
                f"{field_name} must be <= {max_val}, got {value}",
                field_name
            )
        return value
    
    @staticmethod
    def validate_in_list(value: Any, valid_values: List[Any],
                        field_name: str = "Value") -> Any:
        """验证值在列表中
        
        Args:
            value: 要验证的值
            valid_values: 有效值列表
            field_name: 字段名称
            
        Returns:
            验证通过的值
            
        Raises:
            ValidationError: 值不在列表中时抛出
        """
        if value not in valid_values:
            raise ValidationError(
                f"{field_name} must be one of {valid_values}, got {value}",
                field_name
            )
        return value


class PathValidator:
    """路径验证器"""
    
    @staticmethod
    def validate_file_path(path: str, must_exist: bool = False) -> str:
        """验证文件路径
        
        Args:
            path: 文件路径
            must_exist: 是否必须存在
            
        Returns:
            验证通过的路径
            
        Raises:
            ValidationError: 路径无效时抛出
        """
        if not path:
            raise ValidationError("File path cannot be empty", "path")
        
        # 检查路径遍历攻击
        if '..' in path:
            raise ValidationError("Path traversal detected", "path")
        
        # 检查是否存在
        if must_exist and not os.path.exists(path):
            raise ValidationError(f"File not found: {path}", "path")
        
        return path
    
    @staticmethod
    def validate_directory_path(path: str, must_exist: bool = False,
                               create_if_not_exist: bool = False) -> str:
        """验证目录路径
        
        Args:
            path: 目录路径
            must_exist: 是否必须存在
            create_if_not_exist: 不存在时是否创建
            
        Returns:
            验证通过的路径
            
        Raises:
            ValidationError: 路径无效时抛出
        """
        if not path:
            raise ValidationError("Directory path cannot be empty", "path")
        
        # 检查路径遍历攻击
        if '..' in path:
            raise ValidationError("Path traversal detected", "path")
        
        # 检查是否存在
        if not os.path.exists(path):
            if must_exist:
                raise ValidationError(f"Directory not found: {path}", "path")
            elif create_if_not_exist:
                os.makedirs(path, exist_ok=True)
        
        return path
    
    @staticmethod
    def validate_script_path(path: str) -> str:
        """验证脚本路径
        
        Args:
            path: 脚本路径
            
        Returns:
            验证通过的路径
            
        Raises:
            ValidationError: 路径无效时抛出
        """
        PathValidator.validate_file_path(path)
        
        # 检查文件扩展名
        if not path.endswith('.py'):
            raise ValidationError("Script must be a Python file (.py)", "path")
        
        # 排除特殊文件
        filename = os.path.basename(path)
        if filename.startswith('__'):
            raise ValidationError("Cannot execute special Python files", "path")
        
        return path


class StringValidator:
    """字符串验证器"""
    
    @staticmethod
    def validate_email(email: str) -> str:
        """验证邮箱地址
        
        Args:
            email: 邮箱地址
            
        Returns:
            验证通过的邮箱
            
        Raises:
            ValidationError: 邮箱格式无效时抛出
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError("Invalid email format", "email")
        return email
    
    @staticmethod
    def validate_username(username: str) -> str:
        """验证用户名
        
        Args:
            username: 用户名
            
        Returns:
            验证通过的用户名
            
        Raises:
            ValidationError: 用户名格式无效时抛出
        """
        if not username or len(username) < 3:
            raise ValidationError("Username must be at least 3 characters", "username")
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError(
                "Username can only contain letters, numbers and underscores",
                "username"
            )
        
        return username