"""日志管理模块

提供统一的日志配置和管理功能。
"""

import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional
from datetime import datetime

from AppCode.utils.constants import DEFAULT_LOG_DIR, DEFAULT_LOG_LEVEL, DEFAULT_LOG_MAX_SIZE, DEFAULT_LOG_BACKUP_COUNT
from AppCode.utils.decorators import singleton


@singleton
class LoggingManager:
    """日志管理器
    
    负责配置和管理应用程序的日志系统。
    采用单例模式确保全局统一的日志配置。
    """
    
    def __init__(self, log_dir: str = None, log_level: str = None):
        """初始化日志管理器
        
        Args:
            log_dir: 日志目录
            log_level: 日志级别
        """
        self.log_dir = log_dir or DEFAULT_LOG_DIR
        self.log_level = log_level or DEFAULT_LOG_LEVEL
        self._loggers = {}
        self._ensure_log_directory()
    
    def _ensure_log_directory(self):
        """确保日志目录存在"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
    
    def setup_logger(self, name: str, log_file: str = None,
                    level: str = None, console: bool = True,
                    use_time_rotation: bool = False) -> logging.Logger:
        """设置日志记录器
        
        Args:
            name: 日志记录器名称
            log_file: 日志文件名（不含路径）
            level: 日志级别
            console: 是否输出到控制台
            use_time_rotation: 是否使用按时间滚动（True=按天，False=按大小）
            
        Returns:
            配置好的日志记录器
        """
        # 如果已存在，直接返回
        if name in self._loggers:
            return self._loggers[name]
        
        # 创建日志记录器
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level or self.log_level))
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件处理器
        if log_file:
            file_path = os.path.join(self.log_dir, log_file)
            
            if use_time_rotation:
                # 按天滚动的日志文件
                file_handler = TimedRotatingFileHandler(
                    file_path,
                    when='midnight',
                    interval=1,
                    backupCount=DEFAULT_LOG_BACKUP_COUNT,
                    encoding='utf-8'
                )
                file_handler.suffix = "%Y%m%d"
            else:
                # 按大小滚动的日志文件
                file_handler = RotatingFileHandler(
                    file_path,
                    maxBytes=DEFAULT_LOG_MAX_SIZE,
                    backupCount=DEFAULT_LOG_BACKUP_COUNT,
                    encoding='utf-8'
                )
            
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # 控制台处理器
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        self._loggers[name] = logger
        return logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            日志记录器
        """
        if name not in self._loggers:
            return self.setup_logger(name, f"{name}.log")
        return self._loggers[name]
    
    def setup_application_loggers(self):
        """设置应用程序的所有日志记录器"""
        # 主应用日志 - 按天滚动
        self.setup_logger('app', 'app.log', console=True, use_time_rotation=True)
        
        # 脚本执行日志 - 按天滚动
        self.setup_logger('execution', 'execution.log', console=False, use_time_rotation=True)
        
        # 数据库日志 - 按大小滚动
        self.setup_logger('database', 'database.log', console=False, use_time_rotation=False)
        
        # 性能监控日志 - 按天滚动
        self.setup_logger('performance', 'performance.log', console=False, use_time_rotation=True)
        
        # 错误日志 - 按天滚动
        self.setup_logger('error', 'error.log', level='ERROR', console=True, use_time_rotation=True)
        
        # API日志 - 按天滚动
        self.setup_logger('api', 'api.log', console=False, use_time_rotation=True)
        
        # UI日志 - 按天滚动
        self.setup_logger('ui', 'ui.log', console=False, use_time_rotation=True)
    
    def log_exception(self, logger_name: str, exception: Exception, 
                     context: str = None):
        """记录异常信息
        
        Args:
            logger_name: 日志记录器名称
            exception: 异常对象
            context: 上下文信息
        """
        logger = self.get_logger(logger_name)
        message = f"Exception occurred"
        if context:
            message += f" in {context}"
        message += f": {type(exception).__name__}: {str(exception)}"
        logger.exception(message)
    
    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志文件
        
        Args:
            days: 保留天数
        """
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (days * 86400)
        
        for filename in os.listdir(self.log_dir):
            file_path = os.path.join(self.log_dir, filename)
            if os.path.isfile(file_path):
                file_time = os.path.getmtime(file_path)
                if file_time < cutoff_time:
                    try:
                        os.remove(file_path)
                        print(f"Removed old log file: {filename}")
                    except Exception as e:
                        print(f"Failed to remove log file {filename}: {e}")
    
    def flush_all_loggers(self):
        """刷新所有日志记录器，确保日志写入磁盘"""
        for logger in self._loggers.values():
            for handler in logger.handlers:
                handler.flush()