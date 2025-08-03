#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存工具 - 简化版
"""

from functools import wraps
from typing import Callable


def cache_response(ttl_seconds: int = 300, key_prefix: str = "api", cache_type: str = "response") -> Callable:
    """缓存响应装饰器 - 简化版"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator