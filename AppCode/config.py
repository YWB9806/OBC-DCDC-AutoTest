"""全局配置模块

管理应用程序的全局配置。
"""

import os
import json
from typing import Dict, Any
from dataclasses import dataclass, asdict

from AppCode.utils.constants import *
from AppCode.utils.exceptions import ConfigurationError


@dataclass
class AppConfig:
    """应用配置类"""
    
    # 路径配置
    script_root_path: str = DEFAULT_SCRIPT_ROOT
    log_directory: str = DEFAULT_LOG_DIR
    data_directory: str = DEFAULT_DATA_DIR
    backup_directory: str = DEFAULT_BACKUP_DIR
    config_directory: str = DEFAULT_CONFIG_DIR
    plugin_directory: str = DEFAULT_PLUGIN_DIR
    
    # Python解释器
    python_interpreter: str = "python"
    
    # 执行配置
    max_parallel: int = DEFAULT_MAX_PARALLEL
    max_concurrent_executions: int = DEFAULT_MAX_PARALLEL
    timeout: int = DEFAULT_TIMEOUT
    retry_on_error: bool = False
    retry_count: int = DEFAULT_RETRY_COUNT
    use_process_pool: bool = True
    
    # 性能配置
    enable_monitoring: bool = True
    monitoring_interval: int = DEFAULT_MONITORING_INTERVAL
    max_memory_usage: int = DEFAULT_MAX_MEMORY_MB
    
    # 缓存配置
    enable_cache: bool = True
    cache_size: int = DEFAULT_CACHE_SIZE
    cache_ttl: int = DEFAULT_CACHE_TTL
    
    # 安全配置
    enable_sandbox: bool = False
    allowed_modules: list = None
    
    # 备份配置
    auto_backup: bool = True
    backup_interval: int = DEFAULT_BACKUP_INTERVAL
    max_backup_count: int = DEFAULT_MAX_BACKUP_COUNT
    
    # UI配置
    theme: str = "light"
    font_size: int = 10
    auto_scroll: bool = True
    show_line_numbers: bool = True
    
    # 日志配置
    log_level: str = DEFAULT_LOG_LEVEL
    max_file_size: int = DEFAULT_LOG_MAX_SIZE
    backup_count: int = DEFAULT_LOG_BACKUP_COUNT
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """从字典创建配置"""
        return cls(**data)
    
    def save_to_file(self, file_path: str):
        """保存配置到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise ConfigurationError(f"Failed to save config: {e}")
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'AppConfig':
        """从文件加载配置"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return cls.from_dict(data)
            else:
                # 返回默认配置
                return cls()
        except Exception as e:
            raise ConfigurationError(f"Failed to load config: {e}")