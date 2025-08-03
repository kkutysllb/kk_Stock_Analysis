#!/usr/bin/env python3
"""
测试修改后的高股息策略
"""

import sys
sys.path.append('/Users/libing/kk_Projects/kk_StockQuant_Analysis/api')

import requests
import json
from datetime import datetime

def login_and_get_token(base_url, phone, password):
    """登录并获取认证token"""
    login_data = {
        "phone": phone,
        "password": password
    }
    
    try:
        response = requests.post(f"{base_url}/user/login", json=login_data)
        if response.status_code == 200:
            result = response.json()
            return result.get('access_token')
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

def test_high_dividend_strategy():
    """测试高股息策略接口"""
    print("🧪 测试高股息策略接口...")
    print("=" * 50)
    
    # 后端服务地址
    base_url = "http://localhost:9000"
    
    # 测试参数
    test_params = {
        "market_cap": "all",
        "stock_pool": "all",
        "limit": 10,
        "dividend_yield_min": 2.0,  # 降低要求
        "payout_ratio_min": 20.0,   # 降低要求
        "payout_ratio_max": 80.0,   # 放宽要求
        "dividend_coverage_min": 1.0,  # 降低要求
        "roe_min": 5.0,             # 降低要求
        "roic_min": 3.0,            # 降低要求
        "fcf_revenue_ratio_min": 0.0,  # 降低要求
        "debt_ratio_max": 80.0      # 放宽要求
    }
    
    try:
        # 先登录获取token
        print("🔐 正在登录获取认证token...")
        token = login_and_get_token(base_url, "+8618092401097", "Oms@2600a")
        
        if not token:
            print("❌ 无法获取认证token，测试终止")
            return
        
        print("✅ 登录成功，获取到认证token")
        
        # 发送请求
        print(f"📡 发送请求到: {base_url}/strategy/high-dividend")
        print(f"📋 请求参数: {json.dumps(test_params, indent=2, ensure_ascii=False)}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post(
            f"{base_url}/strategy/high-dividend",
            json=test_params,
            headers=headers,
            timeout=30
        )
        
        print(f"\n📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功!")
            print(f"📈 策略名称: {result.get('strategy_name')}")
            print(f"📊 策略类型: {result.get('strategy_type')}")
            print(f"🔢 结果总数: {result.get('total_count')}")
            print(f"⏰ 筛选时间: {result.get('screening_time')}")
            
            results = result.get('results', [])
            if results:
                print(f"\n📋 前5个结果:")
                print("-" * 80)
                for i, stock in enumerate(results[:5]):
                    print(f"{i+1}. {stock.get('name')} ({stock.get('ts_code')})")
                    print(f"   💰 最新价: {stock.get('close', 'N/A')}")
                    print(f"   📊 评分: {stock.get('score', 'N/A')}")
                    print(f"   💎 股息率: {stock.get('dividend_yield', 'N/A')}%")
                    print(f"   📈 ROE: {stock.get('roe', 'N/A')}%")
                    print(f"   💵 EPS: {stock.get('eps', 'N/A')}")
                    print(f"   📉 资产负债率: {stock.get('debt_ratio', 'N/A')}%")
                    print(f"   💰 净利润率: {stock.get('net_profit_margin', 'N/A')}%")
                    print()
            else:
                print("❌ 没有找到符合条件的股票")
                
        elif response.status_code == 422:
            print(f"❌ 参数验证失败: {response.text}")
        elif response.status_code == 401:
            print(f"❌ 认证失败: {response.text}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 请确保后端服务在 http://localhost:9000 运行")
    except requests.exceptions.Timeout:
        print("❌ 请求超时: 服务器响应时间过长")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_with_minimal_conditions():
    """使用最小条件测试"""
    print("\n🧪 使用最小条件测试...")
    print("=" * 50)
    
    base_url = "http://localhost:9000"
    
    # 最小条件参数
    minimal_params = {
        "market_cap": "all",
        "stock_pool": "all",
        "limit": 20,
        "dividend_yield_min": 0.0,
        "payout_ratio_min": 0.0,
        "payout_ratio_max": 100.0,
        "dividend_coverage_min": 0.0,
        "roe_min": 0.0,
        "roic_min": 0.0,
        "fcf_revenue_ratio_min": -100.0,
        "debt_ratio_max": 100.0
    }
    
    try:
        # 先登录获取token
        print("🔐 正在登录获取认证token...")
        token = login_and_get_token(base_url, "+8618092401097", "Oms@2600a")
        
        if not token:
            print("❌ 无法获取认证token，测试终止")
            return
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post(
            f"{base_url}/strategy/high-dividend",
            json=minimal_params,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 最小条件测试成功!")
            print(f"🔢 结果总数: {result.get('total_count')}")
            
            if result.get('total_count', 0) > 0:
                print("✅ 数据库连接和查询逻辑正常")
            else:
                print("⚠️  即使使用最小条件也没有结果，可能存在数据或逻辑问题")
        else:
            print(f"❌ 最小条件测试失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 最小条件测试异常: {e}")

if __name__ == "__main__":
    test_high_dividend_strategy()
    test_with_minimal_conditions()