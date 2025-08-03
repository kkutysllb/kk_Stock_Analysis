#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis缓存管理器
提供统一的缓存接口，支持数据缓存、查询优化和性能提升
"""

import redis
import json
import hashlib
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import logging
from functools import wraps
import asyncio
from concurrent.futures import ThreadPoolExecutor

class CacheManager:
    """
    Redis缓存管理器
    支持字符串、哈希、列表、集合等多种数据类型的缓存
    """
    
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 6379,
                 db: int = 0,
                 password: Optional[str] = None,
                 decode_responses: bool = True,
                 max_connections: int = 20):
        """
        初始化Redis连接
        
        Args:
            host: Redis服务器地址
            port: Redis端口
            db: 数据库编号
            password: 密码
            decode_responses: 是否解码响应
            max_connections: 最大连接数
        """
        try:
            # 创建连接池
            self.pool = redis.ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=decode_responses,
                max_connections=max_connections,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # 创建Redis客户端
            self.redis_client = redis.Redis(connection_pool=self.pool)
            
            # 测试连接
            self.redis_client.ping()
            
            # 线程池用于异步操作
            self.executor = ThreadPoolExecutor(max_workers=10)
            
            # 缓存配置
            self.default_ttl = 3600  # 默认1小时过期
            self.key_prefix = "stock_api:"
            
            logging.info(f"Redis缓存管理器初始化成功: {host}:{port}/{db}")
            
        except Exception as e:
            logging.error(f"Redis连接失败: {e}")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """检查Redis是否可用"""
        try:
            if self.redis_client:
                self.redis_client.ping()
                return True
        except:
            pass
        return False
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            prefix: 键前缀
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            生成的缓存键
        """
        # 将参数转换为字符串并排序
        key_parts = [str(arg) for arg in args]
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend([f"{k}={v}" for k, v in sorted_kwargs])
        
        # 生成哈希值以避免键过长
        key_string = "|".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]
        
        return f"{self.key_prefix}{prefix}:{key_hash}"
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        if not self.is_available():
            return False
            
        try:
            # 统一使用JSON序列化，避免UTF-8解码问题
            serialized_value = json.dumps(value, ensure_ascii=False, default=str)
            
            # 设置缓存
            ttl = ttl or self.default_ttl
            return self.redis_client.setex(key, ttl, serialized_value)
            
        except Exception as e:
            logging.error(f"设置缓存失败 {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值或None
        """
        if not self.is_available():
            return None
            
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # 统一使用JSON反序列化
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError) as e:
                logging.error(f"JSON反序列化失败 {key}: {e}")
                # 删除损坏的缓存
                self.delete(key)
                return None
                    
        except Exception as e:
            logging.error(f"获取缓存失败 {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        if not self.is_available():
            return False
            
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logging.error(f"删除缓存失败 {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        if not self.is_available():
            return False
            
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logging.error(f"检查缓存存在性失败 {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的缓存
        
        Args:
            pattern: 匹配模式
            
        Returns:
            删除的键数量
        """
        if not self.is_available():
            return 0
            
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logging.error(f"清除缓存模式失败 {pattern}: {e}")
            return 0
    
    def clear_all(self) -> bool:
        """
        清空所有缓存
        
        Returns:
            是否清空成功
        """
        if not self.is_available():
            return False
            
        try:
            return self.redis_client.flushdb()
        except Exception as e:
            logging.error(f"清空缓存失败: {e}")
            return False
    
    def clear_corrupted_cache(self) -> int:
        """
        清理损坏的缓存数据（主要是旧的pickle格式数据）
        
        Returns:
            清理的键数量
        """
        if not self.is_available():
            return 0
            
        try:
            cleared_count = 0
            # 获取所有键
            keys = self.redis_client.keys(f"{self.key_prefix}*")
            
            for key in keys:
                try:
                    value = self.redis_client.get(key)
                    if value is not None:
                        # 尝试JSON解析
                        json.loads(value)
                except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
                    # 删除无法解析的键
                    self.redis_client.delete(key)
                    cleared_count += 1
                    logging.info(f"清理损坏缓存: {key}")
                except Exception as e:
                    logging.error(f"检查缓存键失败 {key}: {e}")
            
            logging.info(f"缓存清理完成，共清理 {cleared_count} 个损坏的键")
            return cleared_count
            
        except Exception as e:
            logging.error(f"清理损坏缓存失败: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        if not self.is_available():
            return {"status": "unavailable"}
            
        try:
            info = self.redis_client.info()
            return {
                "status": "available",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
        except Exception as e:
            logging.error(f"获取缓存统计失败: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """
        计算缓存命中率
        
        Args:
            info: Redis信息字典
            
        Returns:
            命中率（0-1之间的浮点数）
        """
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return hits / total
    
    async def async_get(self, key: str) -> Optional[Any]:
        """
        异步获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值或None
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.get, key)
    
    async def async_set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        异步设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.set, key, value, ttl)


# 缓存装饰器
def cache_result(cache_manager: CacheManager, 
                prefix: str, 
                ttl: Optional[int] = None,
                key_generator: Optional[callable] = None):
    """
    缓存结果装饰器
    
    Args:
        cache_manager: 缓存管理器实例
        prefix: 缓存键前缀
        ttl: 过期时间
        key_generator: 自定义键生成函数
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = await cache_manager.async_get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            if result is not None:
                await cache_manager.async_set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 生成缓存键
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            if result is not None:
                cache_manager.set(cache_key, result, ttl)
            
            return result
        
        # 根据函数是否为协程选择包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 全局缓存管理器实例
cache_manager = None

def init_cache_manager(host: str = 'localhost', 
                      port: int = 6379, 
                      db: int = 0, 
                      password: Optional[str] = None) -> CacheManager:
    """
    初始化全局缓存管理器
    
    Args:
        host: Redis服务器地址
        port: Redis端口
        db: 数据库编号
        password: 密码
        
    Returns:
        缓存管理器实例
    """
    global cache_manager
    cache_manager = CacheManager(host=host, port=port, db=db, password=password)
    return cache_manager

def get_cache_manager() -> Optional[CacheManager]:
    """
    获取全局缓存管理器实例
    
    Returns:
        缓存管理器实例或None
    """
    return cache_manager