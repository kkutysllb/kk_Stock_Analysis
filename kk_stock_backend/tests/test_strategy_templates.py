#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试策略模板配置
验证从配置文件获取模板是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.config.strategy_templates import StrategyTemplateConfig
import json

def test_strategy_templates():
    """测试策略模板配置"""
    print("=" * 60)
    print("策略模板配置测试")
    print("=" * 60)
    
    # 测试获取所有模板
    print("\n1. 获取所有策略模板:")
    all_templates = StrategyTemplateConfig.get_all_templates()
    print(f"总共有 {len(all_templates)} 个模板")
    
    for template in all_templates:
        print(f"  - {template['id']}: {template['name']} ({template['strategy_type']})")
    
    # 测试获取模板ID列表
    print("\n2. 获取模板ID列表:")
    template_ids = StrategyTemplateConfig.get_template_ids()
    print(f"模板ID: {template_ids}")
    
    # 测试根据ID获取模板
    print("\n3. 根据ID获取具体模板:")
    test_ids = ['value', 'growth', 'technical', 'fund_flow']
    
    for template_id in test_ids:
        template = StrategyTemplateConfig.get_template_by_id(template_id)
        if template:
            print(f"\n模板ID: {template_id}")
            print(f"  名称: {template['name']}")
            print(f"  描述: {template['description']}")
            print(f"  策略类型: {template['strategy_type']}")
            print(f"  条件: {json.dumps(template['conditions'], ensure_ascii=False, indent=2)}")
            print(f"  权重: {template.get('weights', {})}")
            print(f"  标签: {template.get('tags', [])}")
        else:
            print(f"模板 {template_id} 不存在")
    
    # 测试根据策略类型获取模板
    print("\n4. 根据策略类型获取模板:")
    strategy_types = ['fundamental', 'technical', 'special']
    
    for strategy_type in strategy_types:
        templates = StrategyTemplateConfig.get_templates_by_type(strategy_type)
        print(f"\n策略类型 '{strategy_type}' 的模板:")
        for template in templates:
            print(f"  - {template['id']}: {template['name']}")
    
    # 测试根据名称获取模板
    print("\n5. 根据名称获取模板:")
    test_names = ['价值投资策略', '技术突破策略', '不存在的策略']
    
    for name in test_names:
        template = StrategyTemplateConfig.get_template_by_name(name)
        if template:
            print(f"找到模板: {name} -> {template['id']}")
        else:
            print(f"未找到模板: {name}")
    
    # 测试模板ID验证
    print("\n6. 模板ID验证:")
    test_validation_ids = ['value', 'invalid_id', 'growth', 'nonexistent']
    
    for template_id in test_validation_ids:
        is_valid = StrategyTemplateConfig.validate_template_id(template_id)
        print(f"  {template_id}: {'有效' if is_valid else '无效'}")
    
    # 测试获取模板概要
    print("\n7. 获取模板概要信息:")
    summary = StrategyTemplateConfig.get_template_summary()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    print("\n=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_strategy_templates()