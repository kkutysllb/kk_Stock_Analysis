#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis缓存配置
定义缓存策略、TTL设置和键命名规范
"""

from typing import Dict, Any
from datetime import timedelta

# Redis连接配置
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'password': None,
    'decode_responses': True,
    'max_connections': 20,
    'socket_connect_timeout': 5,
    'socket_timeout': 5,
    'retry_on_timeout': True
}

# 缓存TTL配置（秒）
CACHE_TTL = {
    # 基础数据 - 较长缓存时间
    'stock_basic': 24 * 3600,      # 股票基本信息 - 24小时
    'stock_company': 24 * 3600,    # 公司信息 - 24小时
    'trading_calendar': 7 * 24 * 3600,  # 交易日历 - 7天
    
    # 行情数据 - 中等缓存时间
    'stock_daily': 4 * 3600,       # 日线数据 - 4小时
    'stock_weekly': 6 * 3600,      # 周线数据 - 6小时
    'stock_monthly': 12 * 3600,    # 月线数据 - 12小时
    'index_daily': 2 * 3600,       # 指数日线 - 2小时
    'index_weekly': 4 * 3600,      # 指数周线 - 4小时
    'index_monthly': 8 * 3600,     # 指数月线 - 8小时
    
    # 财务数据 - 长缓存时间
    'fina_indicator': 12 * 3600,   # 财务指标 - 12小时
    'income': 12 * 3600,           # 利润表 - 12小时
    'balancesheet': 12 * 3600,     # 资产负债表 - 12小时
    'cashflow': 12 * 3600,         # 现金流量表 - 12小时
    
    # 实时数据 - 短缓存时间
    'realtime_quote': 60,          # 实时行情 - 1分钟
    'market_summary': 5 * 60,      # 市场概况 - 5分钟
    'top_list': 10 * 60,           # 龙虎榜 - 10分钟
    'limit_list': 5 * 60,          # 涨跌停 - 5分钟
    
    # 分析数据 - 中等缓存时间
    'technical_analysis': 30 * 60, # 技术分析 - 30分钟
    'market_flow': 15 * 60,        # 资金流向 - 15分钟
    'margin_detail': 2 * 3600,     # 融资融券 - 2小时
    
    # 缠论分析数据 - 较长缓存时间（计算耗时）
    'chan_analysis': 3600,         # 缠论综合分析 - 1小时
    'chan_structure': 1800,        # 缠论结构数据 - 30分钟
    'chan_signals': 900,           # 缠论交易信号 - 15分钟
    'dow_analysis': 3600,          # 道氏理论分析 - 1小时
    
    # 搜索和列表 - 短缓存时间
    'search_results': 10 * 60,     # 搜索结果 - 10分钟
    'stock_list': 30 * 60,         # 股票列表 - 30分钟
    'industry_list': 2 * 3600,     # 行业列表 - 2小时
    
    # 统计数据 - 中等缓存时间
    'market_stats': 15 * 60,       # 市场统计 - 15分钟
    'sector_stats': 30 * 60,       # 板块统计 - 30分钟
    'performance_stats': 1 * 3600, # 性能统计 - 1小时
    
    # 默认TTL
    'default': 1 * 3600            # 默认 - 1小时
}

# 缓存键前缀配置
CACHE_KEYS = {
    'stock_basic': 'stock:basic',
    'stock_company': 'stock:company',
    'stock_daily': 'stock:daily',
    'stock_weekly': 'stock:weekly',
    'stock_monthly': 'stock:monthly',
    'stock_search': 'stock:search',
    'stock_list': 'stock:list',
    
    'index_daily': 'index:daily',
    'index_weekly': 'index:weekly',
    'index_monthly': 'index:monthly',
    'index_list': 'index:list',
    
    'financial_indicator': 'finance:indicator',
    'financial_income': 'finance:income',
    'financial_balance': 'finance:balance',
    'financial_cashflow': 'finance:cashflow',
    
    'market_summary': 'market:summary',
    'market_indices': 'market:indices',
    'market_flow': 'market:flow',
    'market_stats': 'market:stats',
    
    'dragon_tiger': 'dragon:tiger',
    'limit_list': 'limit:list',
    'margin_detail': 'margin:detail',
    
    'trading_calendar': 'calendar:trading',
    'concept_data': 'concept:data',
    'etf_data': 'etf:data',
    'futures_data': 'futures:data',
    
    'analytics': 'analytics',
    'performance': 'performance',
    'system': 'system',
    
    # 缠论分析键前缀
    'chan_analysis': 'chan:analysis',
    'chan_structure': 'chan:structure', 
    'chan_signals': 'chan:signals',
    'dow_analysis': 'dow:analysis'
}

# 缓存策略配置
CACHE_STRATEGIES = {
    # 高频查询数据 - 积极缓存
    'high_frequency': {
        'ttl': 5 * 60,              # 5分钟
        'preload': True,            # 预加载
        'refresh_threshold': 0.8,   # 80%时间后刷新
        'max_size': 10000          # 最大缓存条目
    },
    
    # 中频查询数据 - 标准缓存
    'medium_frequency': {
        'ttl': 30 * 60,             # 30分钟
        'preload': False,
        'refresh_threshold': 0.9,   # 90%时间后刷新
        'max_size': 5000
    },
    
    # 低频查询数据 - 长期缓存
    'low_frequency': {
        'ttl': 4 * 3600,            # 4小时
        'preload': False,
        'refresh_threshold': 0.95,  # 95%时间后刷新
        'max_size': 2000
    },
    
    # 静态数据 - 超长缓存
    'static_data': {
        'ttl': 24 * 3600,           # 24小时
        'preload': True,
        'refresh_threshold': 0.99,  # 99%时间后刷新
        'max_size': 1000
    }
}

# 数据类型与缓存策略映射
DATA_TYPE_STRATEGY = {
    # 高频数据
    'realtime_quote': 'high_frequency',
    'market_summary': 'high_frequency',
    'limit_list': 'high_frequency',
    'top_list': 'high_frequency',
    
    # 中频数据
    'stock_daily': 'medium_frequency',
    'index_daily': 'medium_frequency',
    'market_flow': 'medium_frequency',
    'search_results': 'medium_frequency',
    
    # 低频数据
    'stock_weekly': 'low_frequency',
    'stock_monthly': 'low_frequency',
    'financial_data': 'low_frequency',
    'margin_detail': 'low_frequency',
    
    # 分析数据（计算密集型，适合较长缓存）
    'chan_analysis': 'low_frequency',
    'chan_structure': 'medium_frequency',
    'chan_signals': 'medium_frequency',
    'dow_analysis': 'low_frequency',
    
    # 静态数据
    'stock_basic': 'static_data',
    'stock_company': 'static_data',
    'trading_calendar': 'static_data',
    'industry_list': 'static_data'
}

# 缓存预热配置
CACHE_WARMUP = {
    'enabled': True,
    'warmup_on_startup': True,
    'warmup_data_types': [
        'stock_basic',
        'trading_calendar',
        'market_indices',
        'industry_list'
    ],
    'warmup_batch_size': 100,
    'warmup_delay': 1  # 秒
}

# 缓存监控配置
CACHE_MONITORING = {
    'enabled': True,
    'log_cache_hits': False,     # 是否记录缓存命中日志
    'log_cache_misses': True,    # 是否记录缓存未命中日志
    'stats_interval': 300,       # 统计信息更新间隔（秒）
    'alert_thresholds': {
        'hit_rate_min': 0.7,     # 最低命中率阈值
        'memory_usage_max': 0.8,  # 最大内存使用率
        'connection_usage_max': 0.9  # 最大连接使用率
    }
}

# 缓存清理配置
CACHE_CLEANUP = {
    'enabled': True,
    'cleanup_interval': 3600,    # 清理间隔（秒）
    'max_memory_usage': 0.85,    # 最大内存使用率
    'cleanup_strategies': [
        'expired_keys',          # 清理过期键
        'lru_eviction',         # LRU淘汰
        'pattern_cleanup'       # 模式清理
    ],
    'cleanup_patterns': [
        'stock:search:*',       # 清理搜索缓存
        'market:summary:*',     # 清理市场概况缓存
        'analytics:temp:*'      # 清理临时分析缓存
    ]
}

# 环境配置
ENVIRONMENT_CONFIG = {
    'development': {
        'redis_db': 0,
        'default_ttl': 300,      # 5分钟
        'enable_debug': True,
        'log_level': 'DEBUG'
    },
    'testing': {
        'redis_db': 1,
        'default_ttl': 60,       # 1分钟
        'enable_debug': True,
        'log_level': 'INFO'
    },
    'production': {
        'redis_db': 0,
        'default_ttl': 3600,     # 1小时
        'enable_debug': False,
        'log_level': 'WARNING'
    }
}

def get_cache_config(environment: str = 'development') -> Dict[str, Any]:
    """
    获取指定环境的缓存配置
    
    Args:
        environment: 环境名称 (development/testing/production)
        
    Returns:
        缓存配置字典
    """
    base_config = {
        'redis': REDIS_CONFIG,
        'ttl': CACHE_TTL,
        'keys': CACHE_KEYS,
        'strategies': CACHE_STRATEGIES,
        'data_type_strategy': DATA_TYPE_STRATEGY,
        'warmup': CACHE_WARMUP,
        'monitoring': CACHE_MONITORING,
        'cleanup': CACHE_CLEANUP
    }
    
    # 合并环境特定配置
    env_config = ENVIRONMENT_CONFIG.get(environment, ENVIRONMENT_CONFIG['development'])
    base_config['environment'] = env_config
    
    # 更新Redis配置
    base_config['redis']['db'] = env_config['redis_db']
    
    # 更新默认TTL
    base_config['ttl']['default'] = env_config['default_ttl']
    
    return base_config

def get_ttl_for_data_type(data_type: str) -> int:
    """
    获取指定数据类型的TTL
    
    Args:
        data_type: 数据类型
        
    Returns:
        TTL值（秒）
    """
    return CACHE_TTL.get(data_type, CACHE_TTL['default'])

def get_cache_key_prefix(data_type: str) -> str:
    """
    获取指定数据类型的缓存键前缀
    
    Args:
        data_type: 数据类型
        
    Returns:
        缓存键前缀
    """
    return CACHE_KEYS.get(data_type, 'api')

def get_strategy_for_data_type(data_type: str) -> Dict[str, Any]:
    """
    获取指定数据类型的缓存策略
    
    Args:
        data_type: 数据类型
        
    Returns:
        缓存策略配置
    """
    strategy_name = DATA_TYPE_STRATEGY.get(data_type, 'medium_frequency')
    return CACHE_STRATEGIES.get(strategy_name, CACHE_STRATEGIES['medium_frequency'])