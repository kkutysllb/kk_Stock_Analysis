#!/usr/bin/env python3
"""
测试新的价值投资策略（基于历史财报均值）
"""

import requests
import json
from datetime import datetime

# API配置
BASE_URL = "http://localhost:9000"
API_URL = f"{BASE_URL}"

def login_and_get_token():
    """登录并获取token"""
    login_data = {
        "phone": "+8613609247807",
        "password": "Imscfg_2252"
    }
    
    try:
        response = requests.post(f"{API_URL}/user/login", json=login_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 登录成功: {result.get('message', '')}")
            return result.get('access_token')
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录请求失败: {str(e)}")
        return None

def test_value_investment_strategy(token):
    """测试价值投资策略"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试参数
    test_cases = [
        {
            "name": "全市场价值投资",
            "params": {
                "market_cap": "all",
                "stock_pool": "all",
                "limit": 10
            }
        },
        {
            "name": "大盘股价值投资", 
            "params": {
                "market_cap": "large",
                "stock_pool": "main",
                "limit": 10
            }
        },
        {
            "name": "中盘股价值投资",
            "params": {
                "market_cap": "mid", 
                "stock_pool": "all",
                "limit": 10
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 测试: {test_case['name']}")
        print(f"参数: {test_case['params']}")
        
        try:
            response = requests.post(
                f"{API_URL}/strategy/value-investment",
                headers=headers,
                params=test_case['params']
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 请求成功")
                print(f"策略名称: {result.get('strategy_name')}")
                print(f"总数量: {result.get('total_count')}")
                print(f"筛选时间: {result.get('screening_time')}")
                
                results = result.get('results', [])
                if results:
                    print(f"\n📊 前3个结果:")
                    for i, stock in enumerate(results[:3]):
                        print(f"{i+1}. {stock.get('name')} ({stock.get('ts_code')})")
                        print(f"   行业: {stock.get('industry')}")
                        print(f"   价格: {stock.get('close'):.2f}")
                        print(f"   PE: {stock.get('pe'):.2f}")
                        print(f"   PB: {stock.get('pb'):.2f}")
                        print(f"   涨跌幅: {stock.get('pct_chg'):.2f}%")
                        print(f"   总市值: {stock.get('total_mv', 0)/10000:.0f}亿")
                        print(f"   综合评分: {stock.get('score'):.2f}")
                        
                        # 显示财务指标
                        technical = stock.get('technical', {})
                        if technical:
                            print(f"   📈 财务指标 (基于{technical.get('financial_count', 0)}个财报期):")
                            
                            roe = technical.get('roe')
                            current_ratio = technical.get('current_ratio')
                            debt_ratio = technical.get('debt_ratio')
                            profit_growth = technical.get('profit_growth')
                            
                            print(f"      ROE: {roe:.2f}%" if roe is not None else "      ROE: N/A")
                            print(f"      流动比率: {current_ratio:.2f}" if current_ratio is not None else "      流动比率: N/A")
                            print(f"      资产负债率: {debt_ratio:.2f}%" if debt_ratio is not None else "      资产负债率: N/A")
                            print(f"      净利润增长: {profit_growth:.2f}%" if profit_growth is not None else "      净利润增长: N/A")
                        print()
                else:
                    print("❌ 没有找到符合条件的股票")
                    
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")

def main():
    print("🚀 开始测试价值投资策略（基于历史财报均值）")
    print("=" * 60)
    
    # 登录获取token
    token = login_and_get_token()
    if not token:
        print("❌ 无法获取访问令牌，测试终止")
        return
    
    # 测试价值投资策略
    test_value_investment_strategy(token)
    
    print("\n" + "=" * 60)
    print("🎯 测试完成")

if __name__ == "__main__":
    main() 