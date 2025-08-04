#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略选股模板配置文件
将原本存储在数据库中的8个系统模板迁移到文件中进行预设
每个用户可以基于这些模板调整参数进行选股
"""

from typing import Dict, List, Any
from datetime import datetime


class StrategyTemplateConfig:
    """策略模板配置类"""
    
    # 预设的8个策略模板
    TEMPLATES = {
        "value": {
            "id": "value",
            "name": "价值投资策略",
            "strategy_type": "fundamental",
            "description": "寻找低估值、高ROE、稳定增长的优质股票",
            "conditions": {
                "fundamental": {
                    "total_score_min": 70,
                    "roe_min": 10,
                    "pe_max": 25,
                    "pb_max": 3,
                    "growth_score_min": 60,
                    "profitability_score_min": 70
                }
            },
            "weights": {
                "technical": 0.1,
                "fundamental": 0.8,
                "special": 0.1
            },
            "tags": ["价值投资", "长线持有", "稳健"],
            "is_system": True
        },
        
        "growth": {
            "id": "growth",
            "name": "成长股策略",
            "strategy_type": "growth",
            "description": "寻找高成长性、高盈利能力的成长股",
            "conditions": {
                "fundamental": {
                    "growth_score_min": 80,
                    "profitability_score_min": 70,
                    "roe_min": 15
                }
            },
            "weights": {
                "technical": 0.2,
                "fundamental": 0.7,
                "special": 0.1
            },
            "tags": ["成长股", "高增长", "中长线"],
            "is_system": True
        },
        
        "momentum": {
            "id": "momentum",
            "name": "动量突破策略",
            "strategy_type": "momentum",
            "description": "寻找技术面突破、量价配合的强势股",
            "conditions": {
                "technical": {
                    "rsi_min": 50,
                    "rsi_max": 80,
                    "macd_positive": True,
                    "above_ma20": True,
                    "volume_ratio_min": 1.5
                }
            },
            "weights": {
                "technical": 0.8,
                "fundamental": 0.1,
                "special": 0.1
            },
            "tags": ["技术突破", "动量", "短中线"],
            "is_system": True
        },
        
        "dividend": {
            "id": "dividend",
            "name": "高股息策略",
            "strategy_type": "dividend",
            "description": "寻找高股息率、稳定分红的价值股票",
            "conditions": {
                "fundamental": {
                    "dividend_yield_min": 4.0,
                    "dividend_payout_ratio_min": 30.0,
                    "dividend_payout_ratio_max": 70.0,
                    "dividend_coverage_ratio_min": 1.5,
                    "roe_min": 10.0,
                    "roic_min": 8.0,
                    "fcf_revenue_ratio_min": 5.0,
                    "debt_ratio_max": 60.0,
                    "total_score_min": 70
                }
            },
            "weights": {
                "technical": 0.1,
                "fundamental": 0.8,
                "special": 0.1
            },
            "tags": ["高股息", "分红", "价值投资"],
            "is_system": True
        },
        
        "technical": {
            "id": "technical",
            "name": "技术突破策略",
            "strategy_type": "technical",
            "description": "基于技术指标的短线突破策略",
            "conditions": {
                "technical": {
                    "macd_positive": True,
                    "rsi_min": 40,
                    "rsi_max": 80,
                    "above_ma20": True,
                    "volume_ratio_min": 1.5,
                    "kdj_k_min": 50
                }
            },
            "weights": {
                "technical": 1.0,
                "fundamental": 0.0,
                "special": 0.0
            },
            "tags": ["技术分析", "短线", "突破"],
            "is_system": True
        },
        
        "oversold": {
            "id": "oversold",
            "name": "超跌反弹策略",
            "strategy_type": "oversold",
            "description": "寻找超跌后技术面修复的反弹机会",
            "conditions": {
                "technical": {
                    "rsi_min": 20,
                    "rsi_max": 40,
                    "volume_ratio_min": 1.2
                },
                "fundamental": {
                    "pe_max": 30,
                    "pb_max": 5
                }
            },
            "weights": {
                "technical": 0.6,
                "fundamental": 0.3,
                "special": 0.1
            },
            "tags": ["超跌反弹", "短线", "技术修复"],
            "is_system": True
        },
        
        "limit_up": {
            "id": "limit_up",
            "name": "连板龙头策略",
            "strategy_type": "limit_up",
            "description": "寻找连续涨停的市场热点龙头股",
            "conditions": {
                "special": {
                    "limit_days_min": 2,
                    "net_inflow_positive": True,
                    "hot_money_score_min": 60
                },
                "technical": {
                    "volume_ratio_min": 2.0
                }
            },
            "weights": {
                "technical": 0.2,
                "fundamental": 0.0,
                "special": 0.8
            },
            "tags": ["连板", "游资", "短线"],
            "is_system": True
        },
        
        "fund_flow": {
            "id": "fund_flow",
            "name": "资金追踪策略",
            "strategy_type": "fund_flow",
            "description": "基于融资融券数据追踪主力资金动向，筛选具有融资买入趋势和余额增长的优质股票",
            "conditions": {
                "special": {
                    "margin_buy_trend_min": 50,
                    "margin_balance_growth_min": 50,
                    "fund_tracking_score_min": 60
                }
            },
            "weights": {
                "technical": 0.3,
                "fundamental": 0.2,
                "special": 0.5
            },
            "tags": ["资金追踪", "融资融券", "主力资金"],
            "is_system": True
        }
    }
    
    @classmethod
    def get_all_templates(cls) -> List[Dict[str, Any]]:
        """获取所有策略模板"""
        return list(cls.TEMPLATES.values())
    
    @classmethod
    def get_template_by_id(cls, template_id: str) -> Dict[str, Any]:
        """根据ID获取策略模板"""
        return cls.TEMPLATES.get(template_id)
    
    @classmethod
    def get_template_ids(cls) -> List[str]:
        """获取所有模板ID"""
        return list(cls.TEMPLATES.keys())
    
    @classmethod
    def get_templates_by_type(cls, strategy_type: str) -> List[Dict[str, Any]]:
        """根据策略类型获取模板"""
        return [template for template in cls.TEMPLATES.values() 
                if template['strategy_type'] == strategy_type]
    
    @classmethod
    def get_template_by_name(cls, template_name: str) -> Dict[str, Any]:
        """根据名称获取策略模板"""
        for template in cls.TEMPLATES.values():
            if template['name'] == template_name:
                return template
        return None
    
    @classmethod
    def validate_template_id(cls, template_id: str) -> bool:
        """验证模板ID是否有效"""
        return template_id in cls.TEMPLATES
    
    @classmethod
    def get_template_summary(cls) -> Dict[str, Any]:
        """获取模板概要信息"""
        templates = cls.get_all_templates()
        
        # 按策略类型分组统计
        type_counts = {}
        for template in templates:
            strategy_type = template['strategy_type']
            type_counts[strategy_type] = type_counts.get(strategy_type, 0) + 1
        
        return {
            'total_templates': len(templates),
            'template_types': type_counts,
            'template_ids': cls.get_template_ids(),
            'last_updated': datetime.now().isoformat()
        }