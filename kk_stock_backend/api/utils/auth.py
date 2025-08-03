#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证工具 - 简化版，使用现有的认证系统
"""

from typing import Dict, Any


async def get_current_user() -> Dict[str, Any]:
    """获取当前用户信息 - 简化版本用于测试"""
    return {
        "user_id": "test_user",
        "username": "test_user", 
        "email": "test@example.com"
    }