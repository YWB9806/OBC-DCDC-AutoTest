"""配置管理器

管理应用程序的配置信息。
"""

import json
import os
from typing import Any, Optional


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = 'config.json'):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self._config = self._load_config()
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        # 默认配置
        default_config = {
            'database': {
                'path': 'data/script_executor.db'
            },
            'execution': {
                'max_workers': 1,  # 车载ECU测试必须顺序执行
                'timeout': 3600,
                'mode': 'sequential'  # 顺序执行模式
            },
            'scripts': {
                'root_path': 'TestScripts'
            },
            'ui': {
                'theme': 'default',
                'language': 'zh_CN'
            }
        }
        
        # 如果配置文件存在，加载并合并
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Failed to load config file: {e}")
        
        return default_config
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键（支持点号分隔的嵌套键）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save config file: {e}")
    
    def get_all(self) -> dict:
        """获取所有配置
        
        Returns:
            配置字典
        """
        return self._config.copy()