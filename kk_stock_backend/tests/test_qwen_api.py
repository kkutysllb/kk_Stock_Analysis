#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen API测试脚本
用于诊断API调用问题
"""

import requests
import json
import sys
import os

# 添加项目根目录到 sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# content_generator模块已删除，使用硬编码配置
def get_llm_config():
    """获取LLM配置（硬编码版本）"""
    return {
        "api_base_url": "http://172.16.20.20:8008",
        "full_api_url": "http://172.16.20.20:8008/v1/chat/completions",
        "model_name": "QwQ"
    }


def test_basic_connection():
    """测试基本连接"""
    print("🔗 测试基本连接...")
    
    llm_config = get_llm_config()
    api_url = llm_config.get("full_api_url", "http://172.16.20.20:8008/v1/chat/completions")
    
    try:
        # 测试根路径
        base_url = api_url.replace('/v1/chat/completions', '')
        response = requests.get(base_url, timeout=5)
        print(f"✅ 基本连接测试: HTTP {response.status_code}")
        if response.status_code != 200:
            print(f"   响应内容: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ 基本连接失败: {e}")


def test_openai_format():
    """测试OpenAI格式的API调用"""
    print("\n🤖 测试OpenAI格式API调用...")
    
    llm_config = get_llm_config()
    api_url = llm_config.get("full_api_url", "http://172.16.20.20:8008/v1/chat/completions")
    model_name = llm_config.get("model_name", "QwQ")
    
    # 标准OpenAI格式
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "你好，请简单回复"}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer EMPTY"  # 本地服务通常不需要真实token
    }
    
    try:
        print(f"📡 发送请求到: {api_url}")
        print(f"📝 请求体: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"📊 响应状态: HTTP {response.status_code}")
        print(f"📊 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API调用成功!")
            print(f"📜 响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ API调用失败: HTTP {response.status_code}")
            print(f"📜 错误内容: {response.text}")
            
    except Exception as e:
        print(f"💥 请求异常: {e}")


def test_simple_format():
    """测试简化格式的API调用"""
    print("\n🔧 测试简化格式API调用...")
    
    llm_config = get_llm_config()
    api_url = llm_config.get("full_api_url", "http://172.16.20.20:8008/v1/chat/completions")
    model_name = llm_config.get("model_name", "QwQ")
    
    # 最简格式
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    }
    
    try:
        print(f"📡 发送简化请求到: {api_url}")
        print(f"📝 请求体: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        response = requests.post(
            api_url,
            json=payload,
            timeout=30
        )
        
        print(f"📊 响应状态: HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 简化API调用成功!")
            print(f"📜 响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 简化API调用失败: HTTP {response.status_code}")
            print(f"📜 错误内容: {response.text}")
            
    except Exception as e:
        print(f"💥 请求异常: {e}")


def test_different_models():
    """测试不同的模型名称"""
    print("\n🎯 测试不同模型名称...")
    
    llm_config = get_llm_config()
    api_url = llm_config.get("full_api_url", "http://172.16.20.20:8008/v1/chat/completions")
    
    # 尝试不同的模型名称
    model_names = ["QwQ", "qwq", "Qwen", "default", ""]
    
    for model_name in model_names:
        print(f"\n🧪 测试模型名称: '{model_name}'")
        
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 10
        }
        
        try:
            response = requests.post(api_url, json=payload, timeout=10)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ 模型名称 '{model_name}' 有效")
                return model_name
            else:
                print(f"   ❌ 模型名称 '{model_name}' 无效: {response.text[:100]}")
                
        except Exception as e:
            print(f"   💥 请求失败: {e}")
    
    return None


def test_model_list():
    """测试获取模型列表"""
    print("\n📋 测试获取模型列表...")
    
    llm_config = get_llm_config()
    base_url = llm_config.get("api_base_url", "http://172.16.20.20:8008")
    models_url = f"{base_url}/v1/models"
    
    try:
        response = requests.get(models_url, timeout=10)
        print(f"📊 模型列表响应: HTTP {response.status_code}")
        
        if response.status_code == 200:
            models = response.json()
            print(f"✅ 可用模型: {json.dumps(models, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 获取模型列表失败: {response.text}")
            
    except Exception as e:
        print(f"💥 请求异常: {e}")


def run_comprehensive_test():
    """运行综合测试"""
    print("🚀 Qwen API 综合测试")
    print("=" * 60)
    
    # 显示配置信息
    try:
        llm_config = get_llm_config()
        print("\n⚙️ 当前配置:")
        print(f"  API地址: {llm_config.get('api_base_url', 'N/A')}")
        print(f"  完整URL: {llm_config.get('full_api_url', 'N/A')}")
        print(f"  模型名称: {llm_config.get('model_name', 'N/A')}")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return
    
    # 运行各项测试
    test_basic_connection()
    test_model_list()
    test_different_models()
    test_simple_format()
    test_openai_format()
    
    print("\n" + "=" * 60)
    print("🎯 测试建议:")
    print("1. 检查服务是否正常运行")
    print("2. 确认模型名称是否正确")
    print("3. 验证API端点路径")
    print("4. 检查请求格式是否符合服务要求")


if __name__ == "__main__":
    run_comprehensive_test()