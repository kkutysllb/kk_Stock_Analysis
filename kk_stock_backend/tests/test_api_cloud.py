#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API接口云端数据库测试脚本
验证API接口是否正确使用云端数据库
"""

import requests
import json
import time

def test_api_endpoints():
    """测试API接口"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("API接口云端数据库测试")
    print("=" * 60)
    
    # 测试接口列表
    test_endpoints = [
        {
            "name": "系统健康检查",
            "url": f"{base_url}/system/health",
            "method": "GET"
        },
        {
            "name": "交易日历查询",
            "url": f"{base_url}/trading-calendar/is-trading-day?date=20241201",
            "method": "GET"
        },
        {
            "name": "股票基本信息搜索",
            "url": f"{base_url}/stock/basic/search?keyword=平安&limit=5",
            "method": "GET"
        },
        {
            "name": "指数基本信息搜索",
            "url": f"{base_url}/index/basic/search?keyword=上证&limit=5",
            "method": "GET"
        }
    ]
    
    success_count = 0
    total_count = len(test_endpoints)
    
    for i, endpoint in enumerate(test_endpoints, 1):
        print(f"\n{i}. 测试 {endpoint['name']}...")
        print(f"   URL: {endpoint['url']}")
        
        try:
            response = requests.get(endpoint['url'], timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    print(f"   ✅ 成功 - 状态码: {response.status_code}")
                    
                    # 显示部分响应数据
                    if 'data' in data:
                        if isinstance(data['data'], dict):
                            if 'count' in data['data']:
                                print(f"   📊 数据量: {data['data']['count']}")
                            elif 'total_count' in data['data']:
                                print(f"   📊 数据量: {data['data']['total_count']}")
                            elif 'is_trading_day' in data['data']:
                                print(f"   📅 交易日: {data['data']['is_trading_day']}")
                    
                    success_count += 1
                else:
                    print(f"   ⚠️  API返回失败 - {data.get('message', '未知错误')}")
            else:
                print(f"   ❌ HTTP错误 - 状态码: {response.status_code}")
                print(f"   响应: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ 连接失败 - API服务可能未启动")
            print(f"   💡 请先启动API服务: cd api && python -m uvicorn main:app --host 0.0.0.0 --port 8000")
        except requests.exceptions.Timeout:
            print(f"   ❌ 请求超时")
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")
        
        # 避免请求过快
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print(f"测试完成: {success_count}/{total_count} 个接口成功")
    
    if success_count == total_count:
        print("🎉 所有API接口测试通过！")
        print("✅ API接口已成功切换到云端数据库")
    elif success_count > 0:
        print("⚠️  部分API接口测试通过")
        print("💡 请检查失败的接口")
    else:
        print("❌ 所有API接口测试失败")
        print("💡 请检查API服务是否正常启动")
    
    print("=" * 60)
    return success_count == total_count

if __name__ == "__main__":
    test_api_endpoints()