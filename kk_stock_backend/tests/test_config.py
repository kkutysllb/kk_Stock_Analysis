#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置系统测试脚本
验证全局配置管理的各项功能
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 智能收评模块已删除，配置测试不再可用
def test_config_loading():
    """测试配置加载"""
    print("🔧 测试配置加载...")
    
    config = get_config()
    print(f"✅ 配置实例创建成功: {config}")
    
    # 测试基本配置获取
    model_name = config.get("llm", "model_name")
    print(f"✅ 模型名称: {model_name}")
    
    api_url = config.get("llm", "api_base_url")
    print(f"✅ API地址: {api_url}")
    
    # 测试嵌套配置
    db_uri = config.get("database", "mongodb", "cloud_uri")
    print(f"✅ 数据库URI: {db_uri}")


def test_llm_config():
    """测试LLM配置"""
    print("\n🤖 测试LLM配置...")
    
    llm_config = get_llm_config()
    print(f"✅ LLM配置: {json.dumps(llm_config, indent=2, ensure_ascii=False)}")
    
    # 验证关键配置项
    required_keys = ["provider", "model_name", "api_base_url", "full_api_url"]
    for key in required_keys:
        if key in llm_config:
            print(f"✅ {key}: {llm_config[key]}")
        else:
            print(f"❌ 缺少配置项: {key}")


def test_database_config():
    """测试数据库配置"""
    print("\n💾 测试数据库配置...")
    
    db_config = get_database_config()
    print(f"✅ 数据库配置: {json.dumps(db_config, indent=2, ensure_ascii=False)}")


def test_environment_variables():
    """测试环境变量覆盖"""
    print("\n🌍 测试环境变量覆盖...")
    
    # 设置测试环境变量
    test_vars = {
        "AGENT_LLM_MODEL": "TestModel",
        "AGENT_LLM_API_URL": "http://test.example.com:8008",
        "AGENT_DEBUG": "true"
    }
    
    print("设置测试环境变量...")
    for key, value in test_vars.items():
        os.environ[key] = value
        print(f"  {key} = {value}")
    
    # 重新加载配置
    config = get_config()
    config.reload()
    
    # 验证环境变量覆盖
    model_name = config.get("llm", "model_name")
    api_url = config.get("llm", "api_base_url")
    debug_mode = config.get("system", "debug")
    
    print(f"✅ 环境变量覆盖后的模型名称: {model_name}")
    print(f"✅ 环境变量覆盖后的API地址: {api_url}")
    print(f"✅ 环境变量覆盖后的调试模式: {debug_mode}")
    
    # 清理测试环境变量
    for key in test_vars.keys():
        os.environ.pop(key, None)


def test_config_persistence():
    """测试配置持久化"""
    print("\n💾 测试配置持久化...")
    
    config = get_config()
    
    # 修改配置
    original_timeout = config.get("llm", "timeout")
    test_timeout = 999
    
    print(f"原始超时设置: {original_timeout}")
    config.set("llm", "timeout", value=test_timeout)
    print(f"修改后超时设置: {config.get('llm', 'timeout')}")
    
    # 保存配置
    config.save_config()
    print("✅ 配置已保存到文件")
    
    # 恢复原始配置
    config.set("llm", "timeout", value=original_timeout)
    config.save_config()
    print(f"✅ 恢复原始配置: {config.get('llm', 'timeout')}")


def test_utility_methods():
    """测试实用方法"""
    print("\n🛠️ 测试实用方法...")
    
    config = get_config()
    
    # 测试环境检测
    is_debug = config.is_debug()
    is_production = config.is_production()
    
    print(f"✅ 调试模式: {is_debug}")
    print(f"✅ 生产环境: {is_production}")
    
    # 测试配置信息字符串
    config_str = str(config)
    print(f"✅ 配置信息: {config_str}")


def test_agent_integration():
    """智能收评模块已删除"""
    print("\n🤖 智能收评模块已删除，跳过测试...")


def test_system_integration():
    """智能收评模块已删除"""
    print("\n🏢 智能收评模块已删除，跳过测试...")


def run_all_tests():
    """运行所有测试"""
    print("🚀 开始配置系统测试")
    print("=" * 60)
    
    tests = [
        test_config_loading,
        test_llm_config,
        test_database_config,
        test_environment_variables,
        test_config_persistence,
        test_utility_methods,
        test_agent_integration,
        test_system_integration
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
            print("✅ 测试通过\n")
        except Exception as e:
            failed += 1
            print(f"❌ 测试失败: {e}\n")
    
    print("=" * 60)
    print(f"📊 测试结果: 通过 {passed} 个，失败 {failed} 个")
    
    if failed == 0:
        print("🎉 所有配置测试通过！")
    else:
        print(f"⚠️ 有 {failed} 个测试失败，请检查配置")


if __name__ == "__main__":
    run_all_tests()