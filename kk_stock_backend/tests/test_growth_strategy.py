#!/usr/bin/env python3
"""
测试成长股策略API
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

def test_growth_strategy(token):
    """测试成长股策略"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试成长股策略模板应用
    print(f"\n🔍 测试成长股策略模板应用")
    
    try:
        # 使用策略模板接口
        template_data = {
            "template_id": "成长股策略",  # 这是模板ID
            "custom_parameters": {},
            "custom_weights": {}
        }
        
        response = requests.post(
            f"{API_URL}/strategy/templates/成长股策略/apply",
            headers=headers,
            json=template_data
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
                    print(f"   价格: {stock.get('close'):.2f}" if stock.get('close') else "   价格: --")
                    print(f"   PE: {stock.get('pe'):.2f}" if stock.get('pe') else "   PE: --")
                    print(f"   PB: {stock.get('pb'):.2f}" if stock.get('pb') else "   PB: --")
                    print(f"   涨跌幅: {stock.get('pct_chg'):.2f}%" if stock.get('pct_chg') else "   涨跌幅: --")
                    print(f"   总市值: {stock.get('total_mv', 0)/10000:.0f}亿" if stock.get('total_mv') else "   总市值: --")
                    print(f"   综合评分: {stock.get('score'):.2f}" if stock.get('score') else "   综合评分: --")
                    
                    # 显示成长股专用字段
                    print(f"   📈 成长股指标:")
                    avg_eps_growth = stock.get('avg_eps_growth')
                    avg_revenue_growth = stock.get('avg_revenue_growth')
                    avg_roic = stock.get('avg_roic')
                    peg_ratio = stock.get('peg_ratio')
                    avg_gross_margin = stock.get('avg_gross_margin')
                    avg_net_margin = stock.get('avg_net_margin')
                    latest_rd_rate = stock.get('latest_rd_rate')
                    
                    print(f"      EPS增长率: {avg_eps_growth:.2f}%" if avg_eps_growth is not None else "      EPS增长率: N/A")
                    print(f"      营收增长率: {avg_revenue_growth:.2f}%" if avg_revenue_growth is not None else "      营收增长率: N/A")
                    print(f"      ROIC: {avg_roic:.2f}%" if avg_roic is not None else "      ROIC: N/A")
                    print(f"      PEG: {peg_ratio:.2f}" if peg_ratio is not None else "      PEG: N/A")
                    print(f"      毛利率: {avg_gross_margin:.2f}%" if avg_gross_margin is not None else "      毛利率: N/A")
                    print(f"      净利率: {avg_net_margin:.2f}%" if avg_net_margin is not None else "      净利率: N/A")
                    print(f"      研发费用率: {latest_rd_rate:.2f}%" if latest_rd_rate is not None else "      研发费用率: N/A")
                    print()
            else:
                print("❌ 没有找到符合条件的股票")
                
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")

def main():
    print("🚀 开始测试成长股策略")
    print("=" * 60)
    
    # 登录获取token
    token = login_and_get_token()
    if not token:
        print("❌ 无法获取访问令牌，测试终止")
        return
    
    # 测试成长股策略
    test_growth_strategy(token)
    
    print("\n" + "=" * 60)
    print("🎯 测试完成")

if __name__ == "__main__":
    main()