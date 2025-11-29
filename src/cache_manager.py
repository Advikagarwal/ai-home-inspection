"""
Caching Layer for AI-Assisted Home Inspection Workspace
Implements intelligent caching for frequently accessed property data and query results
"""

import time
import json
import hashlib
import logging
import threading
from typing import Any, Optional, Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from config import get_config
from performance_monitor import get_performance_monitor


@dataclass
class CacheEntry:
    """Represents a cached item with metadata"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: int = 300
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)
    
    def access(self) -> Any:
        """Access the cached value and update metadata"""
        self.last_accessed = datetime.now()
        self.access_count += 1
        return self.value


class CacheManager:
    """
    Intelligent cache manager with TTL, LRU eviction, and performance tracking
    """
    
    def __init__(self, max_size: int = 1000):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = get_performance_monitor()
        
        # Cache storage
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Default TTL from config
        self.default_ttl = self.config.performance.cache_ttl_seconds
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a cache key from function arguments
        
        Args:
            prefix: Key prefix (usually function name)
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Create a deterministic string from arguments
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self.cache:
                self.performance_monitor.record_cache_miss()
                return None
            
            entry = self.cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self.cache[key]
                self.performance_monitor.record_cache_miss()
                self.logger.debug(f"Cache entry expired: {key}")
                return None
            
            # Record hit and return value
            self.performance_monitor.record_cache_hit()
            value = entry.access()
            self.logger.debug(f"Cache hit: {key}")
            return value
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (uses default if None)
        """
        if ttl_seconds is None:
            ttl_seconds = self.default_ttl
        
        with self._lock:
            # Evict if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                ttl_seconds=ttl_seconds
            )
            
            self.cache[key] = entry
            self.logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")
    
    def delete(self, key: str) -> bool:
        """
        Delete entry from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key was found and deleted
        """
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                self.logger.debug(f"Cache delete: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self.cache.clear()
            self.logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_entries = len(self.cache)
            expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())
            
            if total_entries > 0:
                avg_access_count = sum(entry.access_count for entry in self.cache.values()) / total_entries
                oldest_entry = min(self.cache.values(), key=lambda e: e.created_at)
                newest_entry = max(self.cache.values(), key=lambda e: e.created_at)
                age_range = (newest_entry.created_at - oldest_entry.created_at).total_seconds()
            else:
                avg_access_count = 0
                age_range = 0
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_entries,
                'max_size': self.max_size,
                'utilization': total_entries / self.max_size,
                'avg_access_count': avg_access_count,
                'age_range_seconds': age_range,
                'hit_rate': self.performance_monitor.get_cache_hit_rate()
            }
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.cache:
            return
        
        # Find LRU entry
        lru_key = min(self.cache.keys(), key=lambda k: self.cache[k].last_accessed)
        del self.cache[lru_key]
        self.logger.debug(f"Evicted LRU entry: {lru_key}")
    
    def _cleanup_expired(self) -> int:
        """
        Remove expired entries from cache
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def _start_cleanup_thread(self) -> None:
        """Start background thread for cache cleanup"""
        def cleanup_worker():
            while True:
                try:
                    self._cleanup_expired()
                    time.sleep(60)  # Cleanup every minute
                except Exception as e:
                    self.logger.error(f"Error in cache cleanup: {e}")
                    time.sleep(60)
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        self.logger.info("Cache cleanup thread started")


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(ttl_seconds: Optional[int] = None, key_prefix: Optional[str] = None):
    """
    Decorator to cache function results
    
    Args:
        ttl_seconds: Time to live for cached result
        key_prefix: Custom key prefix (uses function name if None)
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator


def cache_property_data(property_id: str, data: Any, ttl_seconds: int = 600) -> None:
    """
    Cache property data with specific TTL
    
    Args:
        property_id: Property identifier
        data: Property data to cache
        ttl_seconds: Time to live in seconds
    """
    cache_manager = get_cache_manager()
    cache_key = f"property_data:{property_id}"
    cache_manager.set(cache_key, data, ttl_seconds)


def get_cached_property_data(property_id: str) -> Optional[Any]:
    """
    Get cached property data
    
    Args:
        property_id: Property identifier
        
    Returns:
        Cached property data or None
    """
    cache_manager = get_cache_manager()
    cache_key = f"property_data:{property_id}"
    return cache_manager.get(cache_key)


def invalidate_property_cache(property_id: str) -> None:
    """
    Invalidate cached data for a specific property
    
    Args:
        property_id: Property identifier
    """
    cache_manager = get_cache_manager()
    cache_key = f"property_data:{property_id}"
    cache_manager.delete(cache_key)