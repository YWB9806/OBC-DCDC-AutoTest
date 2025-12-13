"""常量定义模块

定义系统中使用的所有常量。
"""

# ============ 应用信息 ============
APP_NAME = "Python脚本批量执行工具"
APP_VERSION = "1.0.0"
APP_AUTHOR = "开发团队"

# ============ 路径常量 ============
DEFAULT_SCRIPT_ROOT = "TestScripts/"
DEFAULT_LOG_DIR = "logs/"
DEFAULT_DATA_DIR = "data/"
DEFAULT_BACKUP_DIR = "backups/"
DEFAULT_CONFIG_DIR = "config/"
DEFAULT_PLUGIN_DIR = "plugins/"

# ============ 数据库常量 ============
DATABASE_NAME = "app.db"
DATABASE_VERSION = "1.0.0"

# ============ 脚本状态 ============
class ScriptStatus:
    """脚本状态常量"""
    IDLE = "idle"              # 空闲
    RUNNING = "running"        # 运行中
    SUCCESS = "success"        # 成功
    FAILED = "failed"          # 失败
    ERROR = "error"            # 错误
    TIMEOUT = "timeout"        # 超时
    CANCELLED = "cancelled"    # 已取消

# ============ 执行状态 ============
class ExecutionStatus:
    """执行状态常量"""
    PENDING = "PENDING"        # 等待中
    RUNNING = "RUNNING"        # 运行中
    PAUSED = "PAUSED"          # 暂停中（新增）
    SUCCESS = "SUCCESS"        # 成功
    FAILED = "FAILED"          # 失败
    ERROR = "ERROR"            # 错误
    TIMEOUT = "TIMEOUT"        # 超时
    CANCELLED = "CANCELLED"    # 已取消
    UNKNOWN = "UNKNOWN"        # 未知状态

# ============ 测试结果 ============
class TestResult:
    """测试结果常量"""
    PASS = "合格"              # 合格/通过
    FAIL = "不合格"            # 不合格/失败
    PENDING = "待判定"         # 待判定（需要人工确认）
    ERROR = "执行错误"         # 执行错误（脚本异常）
    TIMEOUT = "超时"           # 超时（执行超时）
    UNKNOWN = "-"              # 未知/未执行
    
    # 英文别名（兼容性）
    PASS_EN = "PASS"
    FAIL_EN = "FAIL"

# ============ 执行模式 ============
class ExecutionMode:
    """执行模式常量"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"      # 并行执行

# ============ 用户角色 ============
class UserRole:
    """用户角色常量"""
    SUPER_ADMIN = "super_admin"  # 超级管理员（所有权限）
    ADMIN = "admin"              # 管理员（保留用于兼容）
    USER = "user"                # 普通用户（仅执行脚本）

# ============ 权限常量 ============
class Permission:
    """权限常量"""
    # 脚本相关
    VIEW_SCRIPTS = "view_scripts"
    EXECUTE_SCRIPTS = "execute_scripts"
    MANAGE_SCRIPTS = "manage_scripts"
    
    # 结果查看权限（新增）
    VIEW_RESULTS = "view_results"  # 查看执行结果
    
    # 配置相关
    VIEW_CONFIG = "view_config"
    EDIT_CONFIG = "edit_config"
    
    # 用户相关
    VIEW_USERS = "view_users"
    MANAGE_USERS = "manage_users"
    
    # 数据相关
    VIEW_HISTORY = "view_history"
    DELETE_HISTORY = "delete_history"
    BACKUP_DATA = "backup_data"
    RESTORE_DATA = "restore_data"

# ============ 日志级别 ============
class LogLevel:
    """日志级别常量"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# ============ 备份类型 ============
class BackupType:
    """备份类型常量"""
    MANUAL = "MANUAL"          # 手动备份
    AUTO = "AUTO"              # 自动备份
    SCHEDULED = "SCHEDULED"    # 定时备份

# ============ 执行器类型 ============
class ExecutorType:
    """执行器类型常量"""
    PROCESS = "process"        # 进程
    THREAD = "thread"          # 线程

# ============ 配置常量 ============
# 执行配置
DEFAULT_MAX_PARALLEL = 1       # 默认最大并行数（车载ECU测试必须为1）
DEFAULT_TIMEOUT = 300          # 默认超时时间（秒）
DEFAULT_RETRY_COUNT = 0        # 默认重试次数

# 缓存配置
DEFAULT_CACHE_SIZE = 100       # 默认缓存大小
DEFAULT_CACHE_TTL = 3600       # 默认缓存过期时间（秒）

# 日志配置
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_LOG_BACKUP_COUNT = 5

# 监控配置
DEFAULT_MONITORING_INTERVAL = 1  # 监控间隔（秒）
DEFAULT_MAX_MEMORY_MB = 1024     # 最大内存使用（MB）

# 备份配置
DEFAULT_BACKUP_INTERVAL = 86400  # 备份间隔（秒，24小时）
DEFAULT_MAX_BACKUP_COUNT = 7     # 最大备份数量