#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis缓存中间件
为FastAPI路由提供自动缓存功能
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from cache_manager import get_cache_manager
from cache_config import get_ttl_for_data_type, get_cache_key_prefix

logger = logging.getLogger(__name__)

class CacheMiddleware(BaseHTTPMiddleware):
    """
    缓存中间件
    自动缓存GET请求的响应结果
    """
    
    def __init__(self, app, 
                 cache_enabled: bool = True,
                 cache_methods: list = None,
                 exclude_paths: list = None,
                 include_paths: list = None):
        """
        初始化缓存中间件
        
        Args:
            app: FastAPI应用实例
            cache_enabled: 是否启用缓存
            cache_methods: 需要缓存的HTTP方法列表
            exclude_paths: 排除缓存的路径列表
            include_paths: 包含缓存的路径列表（如果指定，只缓存这些路径）
        """
        super().__init__(app)
        self.cache_enabled = cache_enabled
        self.cache_methods = cache_methods or ['GET']
        self.exclude_paths = exclude_paths or [
            '/docs', '/redoc', '/openapi.json', 
            '/health', '/metrics', '/admin'
        ]
        self.include_paths = include_paths
        
        # 路径缓存配置映射
        self.path_cache_config = {
            '/stock/basic/search': {'data_type': 'search_results', 'ttl': 600},
            '/stock/basic/list': {'data_type': 'stock_list', 'ttl': 1800},
            '/stock/basic/detail': {'data_type': 'stock_basic', 'ttl': 3600},
            '/market/indices': {'data_type': 'index_daily', 'ttl': 1800},
            '/market/dragon-tiger': {'data_type': 'top_list', 'ttl': 600},
            '/financial': {'data_type': 'financial_data', 'ttl': 3600},
            '/index': {'data_type': 'index_daily', 'ttl': 1800},
            '/calendar': {'data_type': 'trading_calendar', 'ttl': 86400}
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求和响应
        
        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            响应对象
        """
        # 检查是否需要缓存
        if not self._should_cache(request):
            return await call_next(request)
        
        # 获取缓存管理器
        cache_manager = get_cache_manager()
        if not cache_manager or not cache_manager.is_available():
            return await call_next(request)
        
        # 生成缓存键
        cache_key = self._generate_cache_key(request)
        
        try:
            # 尝试从缓存获取响应
            cached_response = await cache_manager.async_get(cache_key)
            if cached_response:
                logger.debug(f"缓存命中: {cache_key}")
                return JSONResponse(
                    content=cached_response['content'],
                    status_code=cached_response['status_code'],
                    headers=cached_response.get('headers', {})
                )
            
            # 缓存未命中，执行原始请求
            response = await call_next(request)
            
            # 缓存响应（仅缓存成功的JSON响应）
            if self._should_cache_response(response):
                await self._cache_response(cache_manager, cache_key, request, response)
            
            return response
            
        except Exception as e:
            logger.error(f"缓存中间件错误: {e}")
            # 出错时直接返回原始响应
            return await call_next(request)
    
    def _should_cache(self, request: Request) -> bool:
        """
        判断是否应该缓存请求
        
        Args:
            request: 请求对象
            
        Returns:
            是否应该缓存
        """
        # 检查缓存是否启用
        if not self.cache_enabled:
            return False
        
        # 检查HTTP方法
        if request.method not in self.cache_methods:
            return False
        
        # 检查路径
        path = request.url.path
        
        # 如果指定了包含路径，只缓存这些路径
        if self.include_paths:
            return any(path.startswith(include_path) for include_path in self.include_paths)
        
        # 检查排除路径
        if any(path.startswith(exclude_path) for exclude_path in self.exclude_paths):
            return False
        
        return True
    
    def _should_cache_response(self, response: Response) -> bool:
        """
        判断是否应该缓存响应
        
        Args:
            response: 响应对象
            
        Returns:
            是否应该缓存响应
        """
        # 只缓存成功的响应
        if response.status_code != 200:
            return False
        
        # 只缓存JSON响应
        content_type = response.headers.get('content-type', '')
        if 'application/json' not in content_type:
            return False
        
        return True
    
    def _generate_cache_key(self, request: Request) -> str:
        """
        生成缓存键
        
        Args:
            request: 请求对象
            
        Returns:
            缓存键
        """
        # 基础信息
        method = request.method
        path = request.url.path
        query_params = str(request.query_params)
        
        # 生成唯一标识
        key_string = f"{method}:{path}:{query_params}"
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]
        
        # 获取路径对应的缓存前缀
        cache_prefix = self._get_cache_prefix_for_path(path)
        
        return f"api:{cache_prefix}:{key_hash}"
    
    def _get_cache_prefix_for_path(self, path: str) -> str:
        """
        根据路径获取缓存前缀
        
        Args:
            path: 请求路径
            
        Returns:
            缓存前缀
        """
        # 查找匹配的路径配置
        for config_path in self.path_cache_config:
            if path.startswith(config_path):
                data_type = self.path_cache_config[config_path]['data_type']
                return get_cache_key_prefix(data_type)
        
        # 默认前缀
        return 'general'
    
    def _get_ttl_for_path(self, path: str) -> int:
        """
        根据路径获取TTL
        
        Args:
            path: 请求路径
            
        Returns:
            TTL值（秒）
        """
        # 查找匹配的路径配置
        for config_path in self.path_cache_config:
            if path.startswith(config_path):
                config = self.path_cache_config[config_path]
                if 'ttl' in config:
                    return config['ttl']
                data_type = config['data_type']
                return get_ttl_for_data_type(data_type)
        
        # 默认TTL
        return 3600  # 1小时
    
    async def _cache_response(self, cache_manager, cache_key: str, 
                            request: Request, response: Response):
        """
        缓存响应
        
        Args:
            cache_manager: 缓存管理器
            cache_key: 缓存键
            request: 请求对象
            response: 响应对象
        """
        try:
            # 读取响应内容
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # 解析JSON内容
            content = json.loads(response_body.decode())
            
            # 构建缓存数据
            cache_data = {
                'content': content,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'cached_at': json.dumps(datetime.now().isoformat())
            }
            
            # 获取TTL
            ttl = self._get_ttl_for_path(request.url.path)
            
            # 存储到缓存
            await cache_manager.async_set(cache_key, cache_data, ttl)
            
            logger.debug(f"响应已缓存: {cache_key}, TTL: {ttl}s")
            
            # 重新创建响应对象
            response.body_iterator = self._create_body_iterator(response_body)
            
        except Exception as e:
            logger.error(f"缓存响应失败: {e}")
            # 重新创建响应对象以确保正常返回
            response.body_iterator = self._create_body_iterator(response_body)
    
    def _create_body_iterator(self, body: bytes):
        """
        创建响应体迭代器
        
        Args:
            body: 响应体字节
            
        Yields:
            响应体块
        """
        yield body


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    缓存控制中间件
    添加缓存控制头
    """
    
    def __init__(self, app, default_max_age: int = 3600):
        """
        初始化缓存控制中间件
        
        Args:
            app: FastAPI应用实例
            default_max_age: 默认最大缓存时间（秒）
        """
        super().__init__(app)
        self.default_max_age = default_max_age
        
        # 路径特定的缓存控制配置
        self.cache_control_config = {
            '/stock/basic': 'public, max-age=3600',
            '/market/indices': 'public, max-age=1800',
            '/financial': 'public, max-age=3600',
            '/calendar': 'public, max-age=86400',
            '/health': 'no-cache',
            '/metrics': 'no-cache',
            '/admin': 'no-cache, no-store'
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求和响应，添加缓存控制头
        
        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            响应对象
        """
        response = await call_next(request)
        
        # 添加缓存控制头
        if response.status_code == 200:
            cache_control = self._get_cache_control_for_path(request.url.path)
            response.headers['Cache-Control'] = cache_control
            response.headers['X-Cache-Status'] = 'MISS'  # 默认为未命中
        
        return response
    
    def _get_cache_control_for_path(self, path: str) -> str:
        """
        根据路径获取缓存控制头
        
        Args:
            path: 请求路径
            
        Returns:
            缓存控制头值
        """
        # 查找匹配的路径配置
        for config_path, cache_control in self.cache_control_config.items():
            if path.startswith(config_path):
                return cache_control
        
        # 默认缓存控制
        return f'public, max-age={self.default_max_age}'


# 缓存装饰器函数
def cache_endpoint(data_type: str = None, ttl: int = None, key_prefix: str = None):
    """
    端点缓存装饰器
    
    Args:
        data_type: 数据类型
        ttl: 缓存时间（秒）
        key_prefix: 缓存键前缀
    """
    def decorator(func):
        import inspect
        from functools import wraps
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取缓存管理器
            cache_manager = get_cache_manager()
            if not cache_manager or not cache_manager.is_available():
                return await func(*args, **kwargs)
            
            # 获取函数签名，提取实际参数值
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # 生成缓存键（使用函数名和实际参数值）
            prefix = key_prefix or (get_cache_key_prefix(data_type) if data_type else 'endpoint')
            # 将函数名包含在缓存键中，确保不同函数有不同的缓存键
            cache_key = cache_manager._generate_key(f"{prefix}_{func.__name__}", **bound_args.arguments)
            
            # 尝试从缓存获取
            cached_result = await cache_manager.async_get(cache_key)
            if cached_result is not None:
                # 如果缓存的是字典，需要重建为Pydantic模型
                if isinstance(cached_result, dict) and hasattr(func, '__annotations__'):
                    # 获取函数返回类型
                    return_annotation = func.__annotations__.get('return')
                    if return_annotation and hasattr(return_annotation, 'model_validate'):
                        try:
                            return return_annotation.model_validate(cached_result)
                        except Exception:
                            pass
                return cached_result
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            if result is not None:
                cache_ttl = ttl or (get_ttl_for_data_type(data_type) if data_type else 3600)
                
                # 如果结果是Pydantic模型，转换为字典后缓存
                if hasattr(result, 'model_dump'):
                    cache_data = result.model_dump()
                elif hasattr(result, 'dict'):
                    cache_data = result.dict()
                else:
                    cache_data = result
                
                await cache_manager.async_set(cache_key, cache_data, cache_ttl)
            
            return result
        
        return wrapper
    return decorator