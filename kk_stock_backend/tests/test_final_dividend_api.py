#!/usr/bin/env python3
"""
测试最终的高股息策略API
"""

import requests
import json

def test_high_dividend_api():
    """测试高股息策略API"""
    print("🧪 测试最终的高股息策略API...")
    print("=" * 60)
    
    try:
        # API端点
        url = "http://localhost:9000/strategy/high-dividend"
        
        # 请求参数
        params = {
            "market_cap": "all",
            "stock_pool": "all", 
            "limit": 10,
            "dividend_yield_min": 2.0,
            "payout_ratio_min": 30.0,
            "dividend_fundraising_ratio_min": 50.0,
            "net_cash_min": 0.0
        }
        
        print(f"📡 请求URL: {url}")
        print(f"📋 请求参数: {json.dumps(params, indent=2, ensure_ascii=False)}")
        
        # 发送POST请求
        response = requests.post(url, params=params)
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 请求成功!")
            print(f"策略名称: {data.get('strategy_name')}")
            print(f"策略类型: {data.get('strategy_type')}")
            print(f"结果数量: {data.get('total_count')}")
            print(f"筛选时间: {data.get('screening_time')}")
            
            results = data.get('results', [])
            if results:
                print("\n📈 筛选结果:")
                print("-" * 60)
                for i, stock in enumerate(results, 1):
                    print(f"{i:2d}. {stock['ts_code']} - {stock['name']}")
                    print(f"    行业: {stock.get('industry', 'N/A')}")
                    print(f"    股价: {stock.get('close', 0):.2f}元")
                    print(f"    总市值: {stock.get('total_mv', 0):.2f}万元")
                    print(f"    股息率: {stock.get('dividend_yield', 0):.2f}%")
                    print(f"    股息支付率: {stock.get('payout_ratio', 0):.2f}%")
                    print(f"    分红募资比: {stock.get('dividend_fundraising_ratio', 0):.2f}%")
                    print(f"    净现金: {stock.get('net_cash', 0):.2f}万元")
                    print(f"    ROE: {stock.get('roe', 0):.2f}%")
                    print(f"    EPS: {stock.get('eps', 0):.2f}元")
                    print(f"    综合评分: {stock.get('score', 0):.2f}")
                    print("-" * 40)
            else:
                print("❌ 没有找到符合条件的股票")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        print("请确保后端服务正在运行 (python -m uvicorn main:app --reload)")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_high_dividend_api()