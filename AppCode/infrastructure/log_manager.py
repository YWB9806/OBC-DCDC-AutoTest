"""日志管理器

统一管理应用程序的日志记录。
"""

import logging
import os
from datetime import datetime
from typing import Optional


class LogManager:
    """日志管理器"""
    
    def __init__(self, log_dir: str = 'logs'):
        """初始化日志管理器
        
        Args:
            log_dir: 日志目录
        """
        self.log_dir = log_dir
        self._loggers = {}
        
        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 配置根日志记录器
        self._configure_root_logger()
    
    def _configure_root_logger(self):
        """配置根日志记录器"""
        # 创建日志文件名
        log_file = os.path.join(
            self.log_dir,
            f"app_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        # 配置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # 配置根记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取日志记录器
        
        Args:
            name: 记录器名称
            
        Returns:
            日志记录器
        """
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        
        return self._loggers[name]