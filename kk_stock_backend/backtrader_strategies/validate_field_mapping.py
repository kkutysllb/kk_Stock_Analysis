#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字段映射验证脚本
验证配置文件中的字段映射与数据库实际字段的匹配情况
"""

import sys
import os
import json
from typing import Dict, List, Set
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.global_db import get_global_db_handler
from backtrader_strategies.config import DatabaseConfig


class FieldMappingValidator:
    """字段映射验证器"""
    
    def __init__(self):
        """初始化验证器"""
        self.db_handler = get_global_db_handler()
        self.db_config = DatabaseConfig()
        
    def get_actual_database_fields(self) -> Dict[str, Set[str]]:
        """获取数据库中实际存在的字段"""
        collections_info = {}
        
        # 检查主要集合的字段
        collections_to_check = {
            'stock_factor_pro': '技术因子表',
            'stock_fina_indicator': '财务指标表',
            'stock_income': '利润表',
            'stock_balance_sheet': '资产负债表',
            'stock_cash_flow': '现金流量表'
        }
        
        for collection_name, description in collections_to_check.items():
            try:
                print(f"📊 检查 {description} ({collection_name})...")
                collection = self.db_handler.get_collection(collection_name)
                
                # 获取一个样本文档来分析字段
                sample = collection.find_one()
                if sample:
                    fields = set(sample.keys())
                    collections_info[collection_name] = fields
                    print(f"   ✅ 发现 {len(fields)} 个字段")
                else:
                    print(f"   ❌ 集合为空")
                    collections_info[collection_name] = set()
                    
            except Exception as e:
                print(f"   ❌ 检查失败: {e}")
                collections_info[collection_name] = set()
        
        return collections_info
    
    def validate_technical_indicators(self, actual_fields: Set[str]) -> Dict[str, any]:
        """验证技术指标字段映射"""
        print("\n🔍 验证技术指标字段映射...")
        
        # 从配置中获取技术指标映射
        field_mapping = self.db_config.field_mapping
        
        # 定义财务指标字段名称（这些不应该在stock_factor_pro中查找）
        financial_fields = {
            'eps', 'diluted2_eps', 'dt_eps', 'bvps', 'cfps', 'ocfps', 'revenue_ps',
            'total_revenue_ps', 'capital_rese_ps', 'surplus_rese_ps', 'undist_profit_ps',
            'retainedps', 'roe', 'roe_waa', 'roe_dt', 'roe_avg', 'roe_yearly',
            'roa_dp', 'roa_yearly', 'netprofit_margin',
            'profit_to_gr', 'profit_to_op', 'assets_turn', 'total_fa_trun',
            'debt_to_assets', 'debt_to_eqt', 'eqt_to_debt', 'assets_to_eqt',
            'ocf_to_debt', 'op_to_debt',
            'ocf_to_profit', 'ocf_to_opincome', 'ocf_to_or', 'revenue_yoy',
            'profit_yoy', 'dt_netprofit_yoy', 'eps_yoy', 'dt_eps_yoy',
            'bps_yoy', 'cfps_yoy', 'roe_yoy', 'assets_yoy', 'equity_yoy',
            'ebt_yoy', 'op_yoy', 'ocf_yoy', 'q_eps', 'q_roe', 'q_dt_roe',
            'q_netprofit_margin', 'q_netprofit_yoy', 'q_netprofit_qoq',
            'q_profit_yoy', 'q_profit_qoq', 'q_profit_to_gr', 'q_dtprofit',
            'q_dtprofit_to_profit', 'q_opincome', 'q_investincome',
            'q_investincome_to_ebt', 'q_opincome_to_ebt', 'op_income',
            'profit_dedt', 'retained_earnings', 'fixed_assets', 'non_op_profit',
            'valuechange_income', 'investincome_of_ebt', 'opincome_of_ebt',
            'n_op_profit_of_ebt', 'dtprofit_to_profit', 'nop_to_ebt',
            'op_of_gr', 'op_to_ebt', 'extra_item',
            'npta', 'dp_assets_to_eqt'
        }
        
        # 过滤出真正的技术指标字段（排除财务指标）
        technical_field_keys = [k for k in field_mapping.keys() if k not in financial_fields]
        
        # 分类统计技术指标
        categories = {
            'basic_market': [k for k in ['open', 'high', 'low', 'close', 'volume', 'amount', 'pre_close', 'change', 'pct_chg'] if k in technical_field_keys],
            'ma_indicators': [k for k in technical_field_keys if k.startswith('ma') and ('_' in k or k in ['ma5', 'ma10', 'ma20', 'ma30', 'ma60', 'ma90', 'ma120', 'ma250'])],
            'ema_indicators': [k for k in technical_field_keys if k.startswith('ema')],
            'macd_indicators': [k for k in technical_field_keys if 'macd' in k],
            'rsi_indicators': [k for k in technical_field_keys if k.startswith('rsi')],
            'kdj_indicators': [k for k in technical_field_keys if 'kdj' in k],
            'boll_indicators': [k for k in technical_field_keys if 'boll' in k],
            'dmi_indicators': [k for k in technical_field_keys if 'dmi' in k],
        }
        
        # 计算其他指标（排除已分类的）
        categorized_fields = set()
        for fields in categories.values():
            categorized_fields.update(fields)
        categories['other_indicators'] = [k for k in technical_field_keys if k not in categorized_fields]
        
        validation_result = {
            'total_mapped': 0,
            'total_found': 0,
            'total_missing': 0,
            'categories': {},
            'missing_fields': [],
            'coverage_percentage': 0.0
        }
        
        for category, fields in categories.items():
            category_result = {
                'mapped_count': len(fields),
                'found_count': 0,
                'missing_fields': []
            }
            
            for field in fields:
                if field in field_mapping:
                    db_field = field_mapping[field]
                    validation_result['total_mapped'] += 1
                    
                    if db_field in actual_fields:
                        category_result['found_count'] += 1
                        validation_result['total_found'] += 1
                    else:
                        category_result['missing_fields'].append(f"{field} -> {db_field}")
                        validation_result['missing_fields'].append(f"{field} -> {db_field}")
                        validation_result['total_missing'] += 1
            
            category_result['coverage'] = (category_result['found_count'] / 
                                         category_result['mapped_count'] * 100) if category_result['mapped_count'] > 0 else 0
            validation_result['categories'][category] = category_result
            
            print(f"   📈 {category}: {category_result['found_count']}/{category_result['mapped_count']} "
                  f"({category_result['coverage']:.1f}% 覆盖率)")
        
        validation_result['coverage_percentage'] = (validation_result['total_found'] / 
                                                  validation_result['total_mapped'] * 100) if validation_result['total_mapped'] > 0 else 0
        
        return validation_result
    
    def validate_financial_indicators(self, actual_fields: Set[str]) -> Dict[str, any]:
        """验证财务指标字段映射"""
        print("\n💰 验证财务指标字段映射...")
        
        field_mapping = self.db_config.field_mapping
        
        # 财务指标分类 (移除不存在的字段)
        financial_categories = {
            'per_share': ['eps', 'bvps', 'cfps', 'ocfps', 'revenue_ps'],
            'profitability': ['roe', 'roa_dp', 'netprofit_margin'],  # 移除grossprofit_margin
            'solvency': ['debt_to_assets', 'debt_to_eqt'],            # 移除current_ratio, quick_ratio
            'growth': ['revenue_yoy', 'profit_yoy', 'eps_yoy', 'roe_yoy'],
            'efficiency': ['assets_turn', 'total_fa_trun'],
            'cashflow': ['ocf_to_profit', 'ocf_to_debt', 'ocf_to_opincome']
        }
        
        validation_result = {
            'total_mapped': 0,
            'total_found': 0,
            'total_missing': 0,
            'categories': {},
            'missing_fields': [],
            'coverage_percentage': 0.0
        }
        
        for category, fields in financial_categories.items():
            category_result = {
                'mapped_count': 0,
                'found_count': 0,
                'missing_fields': []
            }
            
            for field in fields:
                if field in field_mapping:
                    category_result['mapped_count'] += 1
                    validation_result['total_mapped'] += 1
                    
                    db_field = field_mapping[field]
                    if db_field in actual_fields:
                        category_result['found_count'] += 1
                        validation_result['total_found'] += 1
                    else:
                        category_result['missing_fields'].append(f"{field} -> {db_field}")
                        validation_result['missing_fields'].append(f"{field} -> {db_field}")
                        validation_result['total_missing'] += 1
            
            if category_result['mapped_count'] > 0:
                category_result['coverage'] = (category_result['found_count'] / 
                                             category_result['mapped_count'] * 100)
                validation_result['categories'][category] = category_result
                
                print(f"   💼 {category}: {category_result['found_count']}/{category_result['mapped_count']} "
                      f"({category_result['coverage']:.1f}% 覆盖率)")
        
        validation_result['coverage_percentage'] = (validation_result['total_found'] / 
                                                  validation_result['total_mapped'] * 100) if validation_result['total_mapped'] > 0 else 0
        
        return validation_result
    
    def generate_validation_report(self) -> Dict[str, any]:
        """生成完整的验证报告"""
        print("🚀 开始验证字段映射...")
        print("="*80)
        
        # 获取数据库实际字段
        actual_fields_by_collection = self.get_actual_database_fields()
        
        # 验证技术指标 (来自stock_factor_pro)
        technical_validation = {}
        if 'stock_factor_pro' in actual_fields_by_collection:
            technical_validation = self.validate_technical_indicators(
                actual_fields_by_collection['stock_factor_pro']
            )
        
        # 验证财务指标 (来自stock_fina_indicator)
        financial_validation = {}
        if 'stock_fina_indicator' in actual_fields_by_collection:
            financial_validation = self.validate_financial_indicators(
                actual_fields_by_collection['stock_fina_indicator']
            )
        
        # 生成综合报告
        total_mapped = (technical_validation.get('total_mapped', 0) + 
                       financial_validation.get('total_mapped', 0))
        total_found = (technical_validation.get('total_found', 0) + 
                      financial_validation.get('total_found', 0))
        
        report = {
            'validation_time': datetime.now().isoformat(),
            'database_collections': {
                collection: len(fields) 
                for collection, fields in actual_fields_by_collection.items()
            },
            'technical_indicators': technical_validation,
            'financial_indicators': financial_validation,
            'overall_summary': {
                'total_mapped_fields': total_mapped,
                'total_found_fields': total_found,
                'total_missing_fields': total_mapped - total_found,
                'overall_coverage_percentage': (total_found / total_mapped * 100) if total_mapped > 0 else 0
            }
        }
        
        return report
    
    def print_summary(self, report: Dict[str, any]):
        """打印验证摘要"""
        print("\n" + "="*80)
        print("📋 字段映射验证摘要")
        print("="*80)
        
        overall = report['overall_summary']
        
        print(f"📊 总体覆盖情况:")
        print(f"   🎯 映射字段总数: {overall['total_mapped_fields']}")
        print(f"   ✅ 找到字段数量: {overall['total_found_fields']}")
        print(f"   ❌ 缺失字段数量: {overall['total_missing_fields']}")
        print(f"   📈 总体覆盖率: {overall['overall_coverage_percentage']:.1f}%")
        
        # 技术指标摘要
        if 'technical_indicators' in report:
            tech = report['technical_indicators']
            print(f"\n🔧 技术指标覆盖率: {tech.get('coverage_percentage', 0):.1f}%")
            if tech.get('missing_fields'):
                print(f"   ❌ 缺失技术指标字段数: {len(tech['missing_fields'])}")
        
        # 财务指标摘要
        if 'financial_indicators' in report:
            fin = report['financial_indicators']
            print(f"💰 财务指标覆盖率: {fin.get('coverage_percentage', 0):.1f}%")
            if fin.get('missing_fields'):
                print(f"   ❌ 缺失财务指标字段数: {len(fin['missing_fields'])}")
        
        # 数据库集合信息
        print(f"\n📚 数据库集合字段统计:")
        for collection, field_count in report['database_collections'].items():
            print(f"   📊 {collection}: {field_count} 个字段")
        
        # 覆盖率评级
        coverage = overall['overall_coverage_percentage']
        if coverage >= 90:
            grade = "A+ (优秀)"
        elif coverage >= 80:
            grade = "A (良好)"
        elif coverage >= 70:
            grade = "B+ (及格)"
        elif coverage >= 60:
            grade = "B (需改进)"
        else:
            grade = "C (严重不足)"
        
        print(f"\n🏆 字段映射质量评级: {grade}")
        
        if overall['total_missing_fields'] > 0:
            print(f"\n⚠️  建议优先补充缺失的 {overall['total_missing_fields']} 个字段映射")


def main():
    """主函数"""
    print("🔍 字段映射验证工具")
    print("基于数据库因子综合报告验证配置文件中的字段映射")
    print("="*80)
    
    try:
        # 创建验证器
        validator = FieldMappingValidator()
        
        # 生成验证报告
        report = validator.generate_validation_report()
        
        # 打印摘要
        validator.print_summary(report)
        
        # 保存详细报告
        report_file = f"field_mapping_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join(os.path.dirname(__file__), 'results', report_file)
        
        # 确保results目录存在
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 详细报告已保存至: {report_path}")
        
        print("\n✅ 字段映射验证完成")
        
    except Exception as e:
        print(f"❌ 验证过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()