"""缓存管理器

管理应用程序的缓存数据。
"""

from typing import Any, Optional
import time


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, default_ttl: int = 3600):
        """初始化缓存管理器
        
        Args:
            default_ttl: 默认过期时间（秒）
        """
        self.default_ttl = default_ttl
        self._cache = {}
        self._expiry = {}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在或已过期返回None
        """
        # 检查是否存在
        if key not in self._cache:
            return None
        
        # 检查是否过期
        if key in self._expiry:
            if time.time() > self._expiry[key]:
                # 已过期，删除
                del self._cache[key]
                del self._expiry[key]
                return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示使用默认值
        """
        self._cache[key] = value
        
        # 设置过期时间
        if ttl is None:
            ttl = self.default_ttl
        
        if ttl > 0:
            self._expiry[key] = time.time() + ttl
    
    def delete(self, key: str):
        """删除缓存
        
        Args:
            key: 缓存键
        """
        if key in self._cache:
            del self._cache[key]
        
        if key in self._expiry:
            del self._expiry[key]
    
    def clear(self):
        """清空所有缓存"""
        self._cache.clear()
        self._expiry.clear()
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        return self.get(key) is not None
    
    def cleanup_expired(self):
        """清理过期的缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, expiry_time in self._expiry.items()
            if current_time > expiry_time
        ]
        
        for key in expired_keys:
            self.delete(key)