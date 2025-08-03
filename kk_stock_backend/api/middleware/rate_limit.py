"""
请求限流中间件
防止API被过度调用，提高系统稳定性
"""

import time
from typing import Dict, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """请求限流中间件"""
    
    def __init__(
        self,
        app,
        calls: int = 100,  # 允许的请求次数
        period: int = 60,  # 时间窗口(秒)
        per_ip: bool = True,  # 是否按IP限制
        exclude_paths: Optional[list] = None  # 排除的路径
    ):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.per_ip = per_ip
        self.exclude_paths = exclude_paths or ['/health', '/docs', '/redoc', '/openapi.json']
        
        # 存储请求记录 {key: [timestamp1, timestamp2, ...]}
        self.requests: Dict[str, list] = {}
    
    def _get_client_key(self, request: Request) -> str:
        """获取客户端标识键"""
        if self.per_ip:
            # 获取真实IP（考虑代理情况）
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()
            return request.client.host if request.client else "unknown"
        else:
            # 全局限流
            return "global"
    
    def _is_rate_limited(self, key: str) -> bool:
        """检查是否超过限流阈值"""
        now = time.time()
        
        # 获取该键的请求记录
        if key not in self.requests:
            self.requests[key] = []
        
        request_times = self.requests[key]
        
        # 清理过期的请求记录
        cutoff_time = now - self.period
        request_times[:] = [t for t in request_times if t > cutoff_time]
        
        # 检查是否超过限制
        if len(request_times) >= self.calls:
            return True
        
        # 添加当前请求时间
        request_times.append(now)
        return False
    
    def _should_exclude(self, path: str) -> bool:
        """检查路径是否应该被排除在限流之外"""
        return any(excluded in path for excluded in self.exclude_paths)
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 检查是否需要排除此路径
        if self._should_exclude(request.url.path):
            return await call_next(request)
        
        # 获取客户端标识
        client_key = self._get_client_key(request)
        
        # 检查是否被限流
        if self._is_rate_limited(client_key):
            logger.warning(f"Rate limit exceeded for {client_key}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "请求频率过高",
                    "message": f"请求频率超过限制，每{self.period}秒最多{self.calls}次请求",
                    "retry_after": self.period
                },
                headers={"Retry-After": str(self.period)}
            )
        
        # 处理请求
        response = await call_next(request)
        
        # 添加限流信息到响应头
        remaining = max(0, self.calls - len(self.requests.get(client_key, [])))
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.period))
        
        return response


class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """高级限流中间件 - 支持不同API不同限制"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # 不同API的限流配置
        self.rate_limits = {
            # 高频查询API - 更严格限制
            "heavy": {
                "paths": ["/stock/", "/market/", "/money_flow/", "/analytics/"],
                "calls": 30,  # 每分钟30次
                "period": 60
            },
            # 中等频率API
            "medium": {
                "paths": ["/user/", "/strategy/", "/backtest/"],
                "calls": 60,  # 每分钟60次
                "period": 60
            },
            # 轻量API - 较宽松限制
            "light": {
                "paths": ["/health", "/system/", "/admin/"],
                "calls": 120,  # 每分钟120次
                "period": 60
            }
        }
        
        # 存储请求记录
        self.requests: Dict[str, Dict[str, list]] = {}
    
    def _get_rate_limit_type(self, path: str) -> str:
        """根据路径确定限流类型"""
        for limit_type, config in self.rate_limits.items():
            for pattern in config["paths"]:
                if pattern in path:
                    return limit_type
        return "medium"  # 默认中等限制
    
    def _get_client_key(self, request: Request) -> str:
        """获取客户端标识"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_key: str, limit_type: str) -> bool:
        """检查特定类型的限流"""
        now = time.time()
        config = self.rate_limits[limit_type]
        
        # 初始化客户端记录
        if client_key not in self.requests:
            self.requests[client_key] = {}
        if limit_type not in self.requests[client_key]:
            self.requests[client_key][limit_type] = []
        
        request_times = self.requests[client_key][limit_type]
        
        # 清理过期记录
        cutoff_time = now - config["period"]
        request_times[:] = [t for t in request_times if t > cutoff_time]
        
        # 检查限制
        if len(request_times) >= config["calls"]:
            return True
        
        # 添加当前请求
        request_times.append(now)
        return False
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 排除静态资源和文档
        if any(path in request.url.path for path in ['/docs', '/redoc', '/openapi.json', '/static']):
            return await call_next(request)
        
        client_key = self._get_client_key(request)
        limit_type = self._get_rate_limit_type(request.url.path)
        
        if self._is_rate_limited(client_key, limit_type):
            config = self.rate_limits[limit_type]
            logger.warning(f"Rate limit exceeded for {client_key} on {limit_type} API")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "请求频率过高",
                    "message": f"{limit_type.upper()}类API每{config['period']}秒最多{config['calls']}次请求",
                    "retry_after": config["period"],
                    "limit_type": limit_type
                },
                headers={"Retry-After": str(config["period"])}
            )
        
        response = await call_next(request)
        
        # 添加限流信息
        config = self.rate_limits[limit_type]
        remaining = max(0, config["calls"] - len(self.requests.get(client_key, {}).get(limit_type, [])))
        response.headers["X-RateLimit-Type"] = limit_type
        response.headers["X-RateLimit-Limit"] = str(config["calls"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response