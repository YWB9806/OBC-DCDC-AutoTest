"""缓存管理模块

提供LRU缓存和内存缓存功能。
"""

import time
from typing import Any, Optional, Dict, Callable
from collections import OrderedDict
from threading import Lock

from AppCode.utils.constants import DEFAULT_CACHE_SIZE, DEFAULT_CACHE_TTL
from AppCode.utils.decorators import singleton


class LRUCache:
    """LRU缓存实现
    
    最近最少使用缓存，线程安全。
    """
    
    def __init__(self, capacity: int = DEFAULT_CACHE_SIZE):
        """初始化LRU缓存
        
        Args:
            capacity: 缓存容量
        """
        self.capacity = capacity
        self.cache: OrderedDict = OrderedDict()
        self.lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在则返回None
        """
        with self.lock:
            if key not in self.cache:
                return None
            
            # 移到末尾（最近使用）
            self.cache.move_to_end(key)
            return self.cache[key]
    
    def put(self, key: str, value: Any):
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        with self.lock:
            if key in self.cache:
                # 更新并移到末尾
                self.cache.move_to_end(key)
            else:
                # 检查容量
                if len(self.cache) >= self.capacity:
                    # 删除最旧的项
                    self.cache.popitem(last=False)
            
            self.cache[key] = value
    
    def remove(self, key: str):
        """删除缓存项
        
        Args:
            key: 缓存键
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
    
    def size(self) -> int:
        """获取缓存大小
        
        Returns:
            缓存项数量
        """
        with self.lock:
            return len(self.cache)


class TTLCache:
    """带过期时间的缓存
    
    支持设置缓存项的过期时间。
    """
    
    def __init__(self, default_ttl: int = DEFAULT_CACHE_TTL):
        """初始化TTL缓存
        
        Args:
            default_ttl: 默认过期时间（秒）
        """
        self.default_ttl = default_ttl
        self.cache: Dict[str, tuple] = {}  # key -> (value, expire_time)
        self.lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在或已过期则返回None
        """
        with self.lock:
            if key not in self.cache:
                return None
            
            value, expire_time = self.cache[key]
            
            # 检查是否过期
            if time.time() > expire_time:
                del self.cache[key]
                return None
            
            return value
    
    def put(self, key: str, value: Any, ttl: int = None):
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None则使用默认值
        """
        with self.lock:
            expire_time = time.time() + (ttl or self.default_ttl)
            self.cache[key] = (value, expire_time)
    
    def remove(self, key: str):
        """删除缓存项
        
        Args:
            key: 缓存键
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
    
    def cleanup_expired(self):
        """清理过期缓存项"""
        with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expire_time) in self.cache.items()
                if current_time > expire_time
            ]
            for key in expired_keys:
                del self.cache[key]
    
    def size(self) -> int:
        """获取缓存大小
        
        Returns:
            缓存项数量
        """
        with self.lock:
            return len(self.cache)


@singleton
class CacheManager:
    """缓存管理器
    
    统一管理应用程序的各种缓存。
    采用单例模式确保全局统一的缓存管理。
    """
    
    def __init__(self):
        """初始化缓存管理器"""
        self.lru_cache = LRUCache()
        self.ttl_cache = TTLCache()
        self._caches: Dict[str, Any] = {}
    
    def get_lru_cache(self) -> LRUCache:
        """获取LRU缓存
        
        Returns:
            LRU缓存实例
        """
        return self.lru_cache
    
    def get_ttl_cache(self) -> TTLCache:
        """获取TTL缓存
        
        Returns:
            TTL缓存实例
        """
        return self.ttl_cache
    
    def create_cache(self, name: str, cache_type: str = 'lru', 
                    **kwargs) -> Any:
        """创建命名缓存
        
        Args:
            name: 缓存名称
            cache_type: 缓存类型（'lru' 或 'ttl'）
            **kwargs: 缓存参数
            
        Returns:
            缓存实例
        """
        if name in self._caches:
            return self._caches[name]
        
        if cache_type == 'lru':
            cache = LRUCache(**kwargs)
        elif cache_type == 'ttl':
            cache = TTLCache(**kwargs)
        else:
            raise ValueError(f"Unknown cache type: {cache_type}")
        
        self._caches[name] = cache
        return cache
    
    def get_cache(self, name: str) -> Optional[Any]:
        """获取命名缓存
        
        Args:
            name: 缓存名称
            
        Returns:
            缓存实例，不存在则返回None
        """
        return self._caches.get(name)
    
    def clear_all(self):
        """清空所有缓存"""
        self.lru_cache.clear()
        self.ttl_cache.clear()
        for cache in self._caches.values():
            if hasattr(cache, 'clear'):
                cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            'lru_cache_size': self.lru_cache.size(),
            'ttl_cache_size': self.ttl_cache.size(),
            'named_caches': {}
        }
        
        for name, cache in self._caches.items():
            if hasattr(cache, 'size'):
                stats['named_caches'][name] = cache.size()
        
        return stats