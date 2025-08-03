#!/usr/bin/env python3
"""
测试高股息策略API调用
"""

import requests
import json

# API基础URL
API_BASE = "http://localhost:8000"

# 测试参数
test_params = {
    "market_cap": "all",
    "stock_pool": "all", 
    "limit": 20,
    "dividend_yield_min": 2.0,
    "payout_ratio_min": 20.0,
    "dividend_fundraising_ratio_min": 30.0,
    "net_cash_min": -1000000.0
}

def test_dividend_api():
    """测试高股息策略API"""
    print("🧪 测试高股息策略API...")
    print("=" * 60)
    
    url = f"{API_BASE}/strategy/high-dividend"
    print(f"📍 请求URL: {url}")
    print(f"📊 请求参数: {json.dumps(test_params, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=test_params, timeout=30)
        print(f"📈 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 请求成功")
            print(f"📊 找到股票数量: {data.get('total_count', 0)}")
            print(f"🏷️ 策略名称: {data.get('strategy_name', 'N/A')}")
            print(f"🔍 策略类型: {data.get('strategy_type', 'N/A')}")
            print(f"⏰ 筛选时间: {data.get('screening_time', 'N/A')}")
            
            results = data.get('results', [])
            if results:
                print("\n前5只股票:")
                for i, stock in enumerate(results[:5], 1):
                    print(f"{i}. {stock.get('ts_code')} - {stock.get('name')}")
                    print(f"   股价: {stock.get('close', 0):.2f}元")
                    print(f"   股息率: {stock.get('dividend_yield', 0):.2f}%")
                    if 'dividend_fundraising_ratio' in stock:
                        print(f"   分红募资比: {stock.get('dividend_fundraising_ratio', 0):.2f}%")
                    if 'net_cash' in stock:
                        print(f"   净现金: {stock.get('net_cash', 0):.2f}万元")
            else:
                print("\n❌ 没有找到符合条件的股票")
                
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    test_dividend_api()