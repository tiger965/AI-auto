"""
Cache Module for AI System Automation Project.

This module implements a versatile caching system for the AI automation framework,
providing optimized data storage and retrieval mechanisms for frequently accessed
data to improve system performance and reduce redundant computations.

Classes:
    CacheManager: Centralized manager for various cache stores.
    MemoryCache: In-memory cache implementation.
    DiskCache: Persistent disk-based cache implementation.
    LRUCache: Least Recently Used cache implementation.
    CacheItem: Container for cached items with metadata.

Functions:
    get(key): Retrieve an item from the cache.
    set(key, value, ttl): Store an item in the cache with optional TTL.
    delete(key): Remove an item from the cache.
    clear(): Clear all items from the cache.
    get_stats(): Get cache performance statistics.
"""

import logging
import time
import threading
import json
import os
import pickle
import hashlib
import inspect
from typing import Dict, List, Tuple, Any, Optional, Union, Callable
import shutil
from collections import OrderedDict

# Configure logging
logger = logging.getLogger(__name__)


class CacheItem:
    """
    Container for cached items with metadata.
    
    Attributes:
        key (str): The cache key.
        value (Any): The cached value.
        created_at (float): Timestamp when the item was created.
        expires_at (Optional[float]): Timestamp when the item expires.
        access_count (int): Number of times the item has been accessed.
        last_accessed (float): Timestamp when the item was last accessed.
        size (int): Approximate size of the item in bytes.
    """
    
    def __init__(self, key: str, value: Any, ttl: Optional[float] = None):
        """
        Initialize a new CacheItem.
        
        Args:
            key (str): The cache key.
            value (Any): The value to cache.
            ttl (Optional[float]): Time-to-live in seconds.
        """
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl if ttl is not None else None
        self.access_count = 0
        self.last_accessed = self.created_at
        
        # Estimate size in bytes
        try:
            # For simple types
            if isinstance(value, (int, float, bool, str)):
                self.size = len(str(value).encode('utf-8'))
            # For more complex objects, use pickle
            else:
                self.size = len(pickle.dumps(value))
        except Exception:
            # Default if we can't estimate size
            self.size = 1024
    
    def is_expired(self) -> bool:
        """
        Check if the item has expired.
        
        Returns:
            bool: True if the item has expired, False otherwise.
        """
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def access(self) -> Any:
        """
        Access the item and update access metadata.
        
        Returns:
            Any: The cached value.
        """
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value
    
    def to_dict(self) -> Dict:
        """
        Convert the cache item to a dictionary for serialization.
        
        Returns:
            Dict: Dictionary representation of the cache item.
        """
        return {
            "key": self.key,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "size": self.size
        }


class LRUCache:
    """
    Least Recently Used (LRU) cache implementation.
    
    This cache evicts the least recently used items when it reaches capacity.
    
    Attributes:
        name (str): Name of the cache.
        capacity (int): Maximum number of items the cache can hold.
        items (OrderedDict): Cache items ordered by access time.
    """
    
    def __init__(self, name: str, capacity: int = 1000):
        """
        Initialize a new LRUCache.
        
        Args:
            name (str): Name of the cache.
            capacity (int): Maximum number of items the cache can hold.
        """
        self.name = name
        self.capacity = capacity
        self.items = OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve an item from the cache.
        
        Args:
            key (str): Cache key.
            
        Returns:
            Optional[Any]: Cached value if found, None otherwise.
        """
        with self.lock:
            if key not in self.items:
                self.misses += 1
                return None
            
            # Get the item
            item = self.items[key]
            
            # Check if expired
            if item.is_expired():
                # Remove expired item
                del self.items[key]
                self.misses += 1
                return None
            
            # Move to end (most recently used)
            self.items.move_to_end(key)
            
            # Update access stats
            self.hits += 1
            return item.access()
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Store an item in the cache.
        
        Args:
            key (str): Cache key.
            value (Any): Value to cache.
            ttl (Optional[float]): Time-to-live in seconds.
        """
        with self.lock:
            # Create cache item
            item = CacheItem(key, value, ttl)
            
            # Remove existing item with same key
            if key in self.items:
                del self.items[key]
            
            # Check if we need to evict items
            while len(self.items) >= self.capacity:
                # Evict least recently used item
                self.items.popitem(last=False)
                self.evictions += 1
            
            # Add the new item
            self.items[key] = item
    
    def delete(self, key: str) -> bool:
        """
        Remove an item from the cache.
        
        Args:
            key (str): Cache key.
            
        Returns:
            bool: True if the item was removed, False otherwise.
        """
        with self.lock:
            if key in self.items:
                del self.items[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items from the cache."""
        with self.lock:
            self.items.clear()
    
    def get_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dict: Cache statistics.
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests) * 100 if total_requests > 0 else 0
            
            return {
                "name": self.name,
                "type": "LRU",
                "capacity": self.capacity,
                "size": len(self.items),
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "evictions": self.evictions
            }


class MemoryCache:
    """
    In-memory cache implementation.
    
    Attributes:
        name (str): Name of the cache.
        items (Dict[str, CacheItem]): Cached items.
        max_size (Optional[int]): Maximum cache size in bytes.
        current_size (int): Current cache size in bytes.
    """
    
    def __init__(self, name: str, max_size: Optional[int] = None):
        """
        Initialize a new MemoryCache.
        
        Args:
            name (str): Name of the cache.
            max_size (Optional[int]): Maximum cache size in bytes.
        """
        self.name = name
        self.items = {}
        self.max_size = max_size
        self.current_size = 0
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        
        # Start a periodic cleanup thread
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start a thread to periodically clean up expired items."""
        def cleanup_task():
            while True:
                try:
                    time.sleep(60)  # Run every minute
                    self._cleanup_expired()
                except Exception as e:
                    logger.error(f"Error in cache cleanup: {str(e)}")
        
        threading.Thread(target=cleanup_task, daemon=True).start()
    
    def _cleanup_expired(self):
        """Remove expired items from the cache."""
        with self.lock:
            # Find expired keys
            expired_keys = [key for key, item in self.items.items() if item.is_expired()]
            
            # Remove expired items
            for key in expired_keys:
                self._remove_item(key)
            
            if expired_keys:
                logger.debug(f"Removed {len(expired_keys)} expired items from {self.name} cache")
    
    def _remove_item(self, key: str):
        """
        Remove an item from the cache and update size.
        
        Args:
            key (str): Cache key.
        """
        if key in self.items:
            self.current_size -= self.items[key].size
            del self.items[key]
    
    def _make_space(self, needed_space: int):
        """
        Make space in the cache by removing least recently used items.
        
        Args:
            needed_space (int): Space needed in bytes.
        """
        if self.max_size is None:
            return
        
        # Check if we need to make space
        if self.current_size + needed_space <= self.max_size:
            return
        
        # Sort items by last accessed time
        sorted_items = sorted(
            self.items.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # Remove items until we have enough space
        for key, item in sorted_items:
            self._remove_item(key)
            
            # Check if we have enough space now
            if self.current_size + needed_space <= self.max_size:
                break
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve an item from the cache.
        
        Args:
            key (str): Cache key.
            
        Returns:
            Optional[Any]: Cached value if found, None otherwise.
        """
        with self.lock:
            if key not in self.items:
                self.misses += 1
                return None
            
            item = self.items[key]
            
            # Check if expired
            if item.is_expired():
                self._remove_item(key)
                self.misses += 1
                return None
            
            # Update stats
            self.hits += 1
            return item.access()
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Store an item in the cache.
        
        Args:
            key (str): Cache key.
            value (Any): Value to cache.
            ttl (Optional[float]): Time-to-live in seconds.
        """
        with self.lock:
            # Create cache item
            item = CacheItem(key, value, ttl)
            
            # Make space if needed
            self._make_space(item.size)
            
            # Check if we still don't have enough space
            if self.max_size is not None and item.size > self.max_size:
                logger.warning(f"Item size ({item.size} bytes) exceeds cache max size ({self.max_size} bytes)")
                return
            
            # Remove existing item with same key
            if key in self.items:
                self._remove_item(key)
            
            # Add the new item
            self.items[key] = item
            self.current_size += item.size
    
    def delete(self, key: str) -> bool:
        """
        Remove an item from the cache.
        
        Args:
            key (str): Cache key.
            
        Returns:
            bool: True if the item was removed, False otherwise.
        """
        with self.lock:
            if key in self.items:
                self._remove_item(key)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items from the cache."""
        with self.lock:
            self.items.clear()
            self.current_size = 0
    
    def get_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dict: Cache statistics.
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests) * 100 if total_requests > 0 else 0
            
            # Calculate additional stats
            item_count = len(self.items)
            avg_item_size = self.current_size / item_count if item_count > 0 else 0
            
            return {
                "name": self.name,
                "type": "memory",
                "item_count": item_count,
                "current_size": self.current_size,
                "max_size": self.max_size,
                "usage_percent": (self.current_size / self.max_size) * 100 if self.max_size else None,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "avg_item_size": avg_item_size
            }


class DiskCache:
    """
    Disk-based persistent cache implementation.
    
    Attributes:
        name (str): Name of the cache.
        cache_dir (str): Directory where cache files are stored.
        max_size (Optional[int]): Maximum cache size in bytes.
        current_size (int): Current cache size in bytes.
        index (Dict[str, Dict]): Index of cached items.
    """
    
    def __init__(self, name: str, cache_dir: str = None, max_size: Optional[int] = None):
        """
        Initialize a new DiskCache.
        
        Args:
            name (str): Name of the cache.
            cache_dir (str, optional): Directory for cache files.
            max_size (Optional[int]): Maximum cache size in bytes.
        """
        self.name = name
        self.cache_dir = cache_dir or os.path.join(os.path.expanduser("~"), ".cache", "ai_system", name)
        self.max_size = max_size
        self.current_size = 0
        self.index = {}
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load the index
        self._load_index()
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def _key_to_path(self, key: str) -> str:
        """
        Convert a cache key to a file path.
        
        Args:
            key (str): Cache key.
            
        Returns:
            str: File path for the cache item.
        """
        # Create a hash of the key for the filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, key_hash)
    
    def _load_index(self):
        """Load the cache index from disk."""
        index_path = os.path.join(self.cache_dir, "index.json")
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r') as f:
                    self.index = json.load(f)
                    
                # Calculate current size
                self.current_size = sum(item.get("size", 0) for item in self.index.values())
                
                logger.debug(f"Loaded disk cache index: {len(self.index)} items, {self.current_size} bytes")
            except Exception as e:
                logger.error(f"Error loading cache index: {str(e)}")
                self.index = {}
                self.current_size = 0
    
    def _save_index(self):
        """Save the cache index to disk."""
        index_path = os.path.join(self.cache_dir, "index.json")
        try:
            with open(index_path, 'w') as f:
                json.dump(self.index, f)
        except Exception as e:
            logger.error(f"Error saving cache index: {str(e)}")
    
    def _start_cleanup_thread(self):
        """Start a thread to periodically clean up expired items."""
        def cleanup_task():
            while True:
                try:
                    time.sleep(300)  # Run every 5 minutes
                    self._cleanup_expired()
                except Exception as e:
                    logger.error(f"Error in disk cache cleanup: {str(e)}")
        
        threading.Thread(target=cleanup_task, daemon=True).start()
    
    def _cleanup_expired(self):
        """Remove expired items from the cache."""
        with self.lock:
            now = time.time()
            expired_keys = []
            
            # Find expired keys
            for key, metadata in self.index.items():
                expires_at = metadata.get("expires_at")
                if expires_at is not None and now > expires_at:
                    expired_keys.append(key)
            
            # Remove expired items
            for key in expired_keys:
                self._remove_item(key)
            
            if expired_keys:
                # Save the updated index
                self._save_index()
                logger.debug(f"Removed {len(expired_keys)} expired items from {self.name} disk cache")
    
    def _remove_item(self, key: str):
        """
        Remove an item from the cache.
        
        Args:
            key (str): Cache key.
        """
        if key in self.index:
            # Update current size
            self.current_size -= self.index[key].get("size", 0)
            
            # Delete the file
            file_path = self._key_to_path(key)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error removing cache file: {str(e)}")
            
            # Remove from index
            del self.index[key]
    
    def _make_space(self, needed_space: int):
        """
        Make space in the cache by removing least recently used items.
        
        Args:
            needed_space (int): Space needed in bytes.
        """
        if self.max_size is None:
            return
        
        # Check if we need to make space
        if self.current_size + needed_space <= self.max_size:
            return
        
        # Sort items by last accessed time
        sorted_items = sorted(
            self.index.items(),
            key=lambda x: x[1].get("last_accessed", 0)
        )
        
        # Remove items until we have enough space
        for key, _ in sorted_items:
            self._remove_item(key)
            
            # Check if we have enough space now
            if self.current_size + needed_space <= self.max_size:
                break
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve an item from the cache.
        
        Args:
            key (str): Cache key.
            
        Returns:
            Optional[Any]: Cached value if found, None otherwise.
        """
        with self.lock:
            if key not in self.index:
                self.misses += 1
                return None
            
            metadata = self.index[key]
            
            # Check if expired
            expires_at = metadata.get("expires_at")
            if expires_at is not None and time.time() > expires_at:
                self._remove_item(key)
                self._save_index()
                self.misses += 1
                return None
            
            # Try to load the item
            file_path = self._key_to_path(key)
            if not os.path.exists(file_path):
                # File doesn't exist, remove from index
                self._remove_item(key)
                self._save_index()
                self.misses += 1
                return None
            
            try:
                with open(file_path, 'rb') as f:
                    value = pickle.load(f)
                    
                # Update access stats
                metadata["access_count"] = metadata.get("access_count", 0) + 1
                metadata["last_accessed"] = time.time()
                self._save_index()
                
                self.hits += 1
                return value
            except Exception as e:
                logger.error(f"Error loading cache item: {str(e)}")
                self._remove_item(key)
                self._save_index()
                self.misses += 1
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Store an item in the cache.
        
        Args:
            key (str): Cache key.
            value (Any): Value to cache.
            ttl (Optional[float]): Time-to-live in seconds.
        """
        with self.lock:
            # Serialize the value to estimate size
            try:
                serialized = pickle.dumps(value)
                item_size = len(serialized)
            except Exception as e:
                logger.error(f"Error serializing cache item: {str(e)}")
                return
            
            # Make space if needed
            self._make_space(item_size)
            
            # Check if we still don't have enough space
            if self.max_size is not None and item_size > self.max_size:
                logger.warning(f"Item size ({item_size} bytes) exceeds cache max size ({self.max_size} bytes)")
                return
            
            # Remove existing item with same key
            if key in self.index:
                self._remove_item(key)
            
            # Write to disk
            file_path = self._key_to_path(key)
            try:
                with open(file_path, 'wb') as f:
                    pickle.dump(value, f)
            except Exception as e:
                logger.error(f"Error writing cache item: {str(e)}")
                return
            
            # Update index
            now = time.time()
            self.index[key] = {
                "created_at": now,
                "expires_at": now + ttl if ttl is not None else None,
                "access_count": 0,
                "last_accessed": now,
                "size": item_size
            }
            
            # Update current size
            self.current_size += item_size
            
            # Save the index
            self._save_index()
    
    def delete(self, key: str) -> bool:
        """
        Remove an item from the cache.
        
        Args:
            key (str): Cache key.
            
        Returns:
            bool: True if the item was removed, False otherwise.
        """
        with self.lock:
            if key in self.index:
                self._remove_item(key)
                self._save_index()
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items from the cache."""
        with self.lock:
            # Remove all files
            for key in list(self.index.keys()):
                self._remove_item(key)
            
            # Reset index
            self.index = {}
            self.current_size = 0
            
            # Save the index
            self._save_index()
    
    def get_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dict: Cache statistics.
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests) * 100 if total_requests > 0 else 0
            
            return {
                "name": self.name,
                "type": "disk",
                "item_count": len(self.index),
                "current_size": self.current_size,
                "max_size": self.max_size,
                "usage_percent": (self.current_size / self.max_size) * 100 if self.max_size else None,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "cache_dir": self.cache_dir
            }


class CacheManager:
    """
    Central manager for various cache stores.
    
    This class coordinates different cache implementations and provides
    a unified interface for caching operations.
    
    Attributes:
        caches (Dict[str, Any]): Registered cache instances.
        default_cache (str): Name of the default cache.
    """
    
    def __init__(self):
        """Initialize a new CacheManager."""
        self.caches = {}
        self.default_cache = None
        self.lock = threading.RLock()
        self.initialized = False
    
    def register_cache(self, cache, default: bool = False):
        """
        Register a cache with the manager.
        
        Args:
            cache: Cache implementation to register.
            default (bool, optional): Whether this is the default cache.
        """
        with self.lock:
            self.caches[cache.name] = cache
            if default or self.default_cache is None:
                self.default_cache = cache.name
            logger.info(f"Registered cache: {cache.name}" + (" (default)" if default else ""))
    
    def get_cache(self, name: Optional[str] = None):
        """
        Get a registered cache by name.
        
        Args:
            name (Optional[str]): Cache name, or None for the default cache.
            
        Returns:
            The requested cache implementation.
            
        Raises:
            ValueError: If the cache is not found.
        """
        with self.lock:
            cache_name = name or self.default_cache
            if cache_name not in self.caches:
                raise ValueError(f"Cache not found: {cache_name}")
            return self.caches[cache_name]
    
    def get(self, key: str, cache_name: Optional[str] = None) -> Optional[Any]:
        """
        Retrieve an item from a cache.
        
        Args:
            key (str): Cache key.
            cache_name (Optional[str]): Cache to use, or None for the default.
            
        Returns:
            Optional[Any]: Cached value if found, None otherwise.
        """
        try:
            cache = self.get_cache(cache_name)
            return cache.get(key)
        except ValueError:
            logger.error(f"Cache not found: {cache_name}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None, cache_name: Optional[str] = None) -> None:
        """
        Store an item in a cache.
        
        Args:
            key (str): Cache key.
            value (Any): Value to cache.
            ttl (Optional[float]): Time-to-live in seconds.
            cache_name (Optional[str]): Cache to use, or None for the default.
        """
        try:
            cache = self.get_cache(cache_name)
            cache.set(key, value, ttl)
        except ValueError:
            logger.error(f"Cache not found: {cache_name}")
    
    def delete(self, key: str, cache_name: Optional[str] = None) -> bool:
        """
        Remove an item from a cache.
        
        Args:
            key (str): Cache key.
            cache_name (Optional[str]): Cache to use, or None for the default.
            
        Returns:
            bool: True if the item was removed, False otherwise.
        """
        try:
            cache = self.get_cache(cache_name)
            return cache.delete(key)
        except ValueError:
            logger.error(f"Cache not found: {cache_name}")
            return False
    
    def clear(self, cache_name: Optional[str] = None) -> None:
        """
        Clear all items from a cache.
        
        Args:
            cache_name (Optional[str]): Cache to clear, or None for the default.
        """
        if cache_name is None:
            # Clear all caches
            for cache in self.caches.values():
                cache.clear()
        else:
            try:
                cache = self.get_cache(cache_name)
                cache.clear()
            except ValueError:
                logger.error(f"Cache not found: {cache_name}")
    
    def get_stats(self, cache_name: Optional[str] = None) -> Dict:
        """
        Get cache statistics.
        
        Args:
            cache_name (Optional[str]): Cache to get stats for, or None for all.
            
        Returns:
            Dict: Cache statistics.
        """
        with self.lock:
            if cache_name is not None:
                try:
                    cache = self.get_cache(cache_name)
                    return cache.get_stats()
                except ValueError:
                    logger.error(f"Cache not found: {cache_name}")
                    return {}
                    
            # Aggregate stats for all caches
            stats = {
                "caches": [],
                "total_hits": 0,
                "total_misses": 0,
                "total_items": 0,
                "total_size": 0
            }
            
            for cache in self.caches.values():
                cache_stats = cache.get_stats()
                stats["caches"].append(cache_stats)
                stats["total_hits"] += cache_stats.get("hits", 0)
                stats["total_misses"] += cache_stats.get("misses", 0)
                stats["total_items"] += cache_stats.get("item_count", 0)
                stats["total_size"] += cache_stats.get("current_size", 0)
            
            total_requests = stats["total_hits"] + stats["total_misses"]
            stats["overall_hit_rate"] = (stats["total_hits"] / total_requests) * 100 if total_requests > 0 else 0
            
            return stats


# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """
    Get the global cache manager instance.
    
    Returns:
        CacheManager: The global cache manager.
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

def get(key: str, cache_name: Optional[str] = None) -> Optional[Any]:
    """
    Retrieve an item from the cache.
    
    Args:
        key (str): Cache key.
        cache_name (Optional[str]): Cache to use, or None for the default.
        
    Returns:
        Optional[Any]: Cached value if found, None otherwise.
    """
    return get_cache_manager().get(key, cache_name)

def set(key: str, value: Any, ttl: Optional[float] = None, cache_name: Optional[str] = None) -> None:
    """
    Store an item in the cache.
    
    Args:
        key (str): Cache key.
        value (Any): Value to cache.
        ttl (Optional[float]): Time-to-live in seconds.
        cache_name (Optional[str]): Cache to use, or None for the default.
    """
    get_cache_manager().set(key, value, ttl, cache_name)

def delete(key: str, cache_name: Optional[str] = None) -> bool:
    """
    Remove an item from the cache.
    
    Args:
        key (str): Cache key.
        cache_name (Optional[str]): Cache to use, or None for the default.
        
    Returns:
        bool: True if the item was removed, False otherwise.
    """
    return get_cache_manager().delete(key, cache_name)

def clear(cache_name: Optional[str] = None) -> None:
    """
    Clear all items from the cache.
    
    Args:
        cache_name (Optional[str]): Cache to clear, or None for all.
    """
    get_cache_manager().clear(cache_name)

def get_stats(cache_name: Optional[str] = None) -> Dict:
    """
    Get cache statistics.
    
    Args:
        cache_name (Optional[str]): Cache to get stats for, or None for all.
        
    Returns:
        Dict: Cache statistics.
    """
    return get_cache_manager().get_stats(cache_name)

def initialize_cache():
    """Initialize the caching system with default caches."""
    manager = get_cache_manager()
    if manager.initialized:
        return
    
    # Register memory cache (default)
    memory_cache = MemoryCache("memory")
    manager.register_cache(memory_cache, default=True)
    
    # Register LRU cache
    lru_cache = LRUCache("lru", capacity=1000)
    manager.register_cache(lru_cache)
    
    # Register disk cache
    disk_cache = DiskCache("disk")
    manager.register_cache(disk_cache)
    
    manager.initialized = True
    logger.info("Cache system initialized")

# Initialize the cache system
initialize_cache()