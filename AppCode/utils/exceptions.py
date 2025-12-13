"""自定义异常模块

定义系统中使用的所有自定义异常类。
"""


class AppBaseException(Exception):
    """应用基础异常类
    
    所有自定义异常的基类。
    """
    
    def __init__(self, message: str, code: str = None):
        """初始化异常
        
        Args:
            message: 错误消息
            code: 错误代码
        """
        self.message = message
        self.code = code
        super().__init__(self.message)


# ============ 验证相关异常 ============

class ValidationError(AppBaseException):
    """验证错误
    
    当数据验证失败时抛出。
    """
    
    def __init__(self, message: str, field: str = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field


# ============ 脚本相关异常 ============

class ScriptError(AppBaseException):
    """脚本错误基类"""
    pass


class ScriptNotFoundError(ScriptError):
    """脚本未找到错误"""
    
    def __init__(self, script_path: str):
        message = f"Script not found: {script_path}"
        super().__init__(message, "SCRIPT_NOT_FOUND")
        self.script_path = script_path


class ScriptExecutionError(ScriptError):
    """脚本执行错误"""
    
    def __init__(self, script_path: str, reason: str):
        message = f"Failed to execute script {script_path}: {reason}"
        super().__init__(message, "SCRIPT_EXECUTION_ERROR")
        self.script_path = script_path
        self.reason = reason


class ScriptTimeoutError(ScriptError):
    """脚本执行超时错误"""
    
    def __init__(self, script_path: str, timeout: int):
        message = f"Script execution timeout after {timeout} seconds: {script_path}"
        super().__init__(message, "SCRIPT_TIMEOUT")
        self.script_path = script_path
        self.timeout = timeout


# ============ 执行相关异常 ============

class ExecutionError(AppBaseException):
    """执行错误基类"""
    pass


class ExecutionCancelledError(ExecutionError):
    """执行被取消错误"""
    
    def __init__(self, execution_id: str):
        message = f"Execution cancelled: {execution_id}"
        super().__init__(message, "EXECUTION_CANCELLED")
        self.execution_id = execution_id


class ExecutionFailedError(ExecutionError):
    """执行失败错误"""
    
    def __init__(self, execution_id: str, reason: str):
        message = f"Execution failed {execution_id}: {reason}"
        super().__init__(message, "EXECUTION_FAILED")
        self.execution_id = execution_id
        self.reason = reason


# ============ 数据库相关异常 ============

class DatabaseError(AppBaseException):
    """数据库错误基类"""
    pass


class DatabaseConnectionError(DatabaseError):
    """数据库连接错误"""
    
    def __init__(self, reason: str):
        message = f"Database connection failed: {reason}"
        super().__init__(message, "DATABASE_CONNECTION_ERROR")


class DatabaseMigrationError(DatabaseError):
    """数据库迁移错误"""
    
    def __init__(self, version: str, reason: str):
        message = f"Database migration to version {version} failed: {reason}"
        super().__init__(message, "DATABASE_MIGRATION_ERROR")
        self.version = version


# ============ 配置相关异常 ============

class ConfigurationError(AppBaseException):
    """配置错误"""
    
    def __init__(self, message: str):
        super().__init__(message, "CONFIGURATION_ERROR")


# ============ 权限相关异常 ============

class PermissionError(AppBaseException):
    """权限错误"""
    
    def __init__(self, user_id: str, permission: str):
        message = f"User {user_id} does not have permission: {permission}"
        super().__init__(message, "PERMISSION_DENIED")
        self.user_id = user_id
        self.permission = permission


class AuthenticationError(AppBaseException):
    """认证错误"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


# ============ 资源相关异常 ============

class ResourceError(AppBaseException):
    """资源错误基类"""
    pass


class ResourceNotFoundError(ResourceError):
    """资源未找到错误"""
    
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} not found: {resource_id}"
        super().__init__(message, "RESOURCE_NOT_FOUND")
        self.resource_type = resource_type
        self.resource_id = resource_id


class ResourceExhaustedError(ResourceError):
    """资源耗尽错误"""
    
    def __init__(self, resource_type: str):
        message = f"Resource exhausted: {resource_type}"
        super().__init__(message, "RESOURCE_EXHAUSTED")
        self.resource_type = resource_type


# ============ 插件相关异常 ============

class PluginError(AppBaseException):
    """插件错误基类"""
    pass


class PluginLoadError(PluginError):
    """插件加载错误"""
    
    def __init__(self, plugin_name: str, reason: str):
        message = f"Failed to load plugin {plugin_name}: {reason}"
        super().__init__(message, "PLUGIN_LOAD_ERROR")
        self.plugin_name = plugin_name


class PluginExecutionError(PluginError):
    """插件执行错误"""
    
    def __init__(self, plugin_name: str, reason: str):
        message = f"Plugin {plugin_name} execution failed: {reason}"
        super().__init__(message, "PLUGIN_EXECUTION_ERROR")
        self.plugin_name = plugin_name