#!/usr/bin/env python3
"""
测试策略状态更新修复效果

验证启动日志中的策略状态更新警告问题是否已解决
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from api.simulation.database import simulation_db
from api.simulation.strategy_scheduler import strategy_scheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_strategy_status_fix():
    """测试策略状态更新修复效果"""
    
    print("=" * 60)
    print("测试策略状态更新修复效果")
    print("=" * 60)
    
    # 测试用户和策略
    test_user_id = 'user_1753547944_1101'
    test_strategies = ['taishang_1', 'taishang_2', 'taishang_3']
    
    print(f"\n1. 测试用户: {test_user_id}")
    print(f"   测试策略: {', '.join(test_strategies)}")
    
    # 测试策略状态更新功能
    print(f"\n2. 测试策略状态更新功能...")
    update_results = {}
    
    for strategy in test_strategies:
        try:
            print(f"   更新策略 {strategy} 状态...")
            result = simulation_db.update_strategy_status(test_user_id, strategy, True)
            update_results[strategy] = result
            status = "✅ 成功" if result else "❌ 失败"
            print(f"   - {strategy}: {status}")
        except Exception as e:
            update_results[strategy] = False
            print(f"   - {strategy}: ❌ 异常 - {e}")
    
    # 验证数据库记录
    print(f"\n3. 验证数据库策略配置记录...")
    config_results = {}
    
    for strategy in test_strategies:
        try:
            config = simulation_db.get_user_strategy_config(test_user_id, strategy)
            if config:
                config_results[strategy] = {
                    'exists': True,
                    'is_active': config.get('is_active'),
                    'allocated_cash': config.get('allocated_cash'),
                    'created_time': config.get('created_time')
                }
                print(f"   - {strategy}: ✅ 存在")
                print(f"     激活状态: {config.get('is_active')}")
                print(f"     分配资金: {config.get('allocated_cash'):,}元")
            else:
                config_results[strategy] = {'exists': False}
                print(f"   - {strategy}: ❌ 不存在")
        except Exception as e:
            config_results[strategy] = {'exists': False, 'error': str(e)}
            print(f"   - {strategy}: ❌ 查询异常 - {e}")
    
    # 测试调度器任务创建
    print(f"\n4. 测试调度器任务创建...")
    
    try:
        # 启动调度器
        if not strategy_scheduler._is_running:
            strategy_scheduler.start()
            print("   调度器启动成功")
        else:
            print("   调度器已在运行")
        
        # 创建测试任务
        task_results = {}
        for strategy in test_strategies:
            try:
                strategy_config = {
                    'strategy_name': strategy,
                    'allocated_cash': config_results[strategy].get('allocated_cash', 300000),
                    'custom_params': {}
                }
                
                success = await strategy_scheduler.start_user_strategy(test_user_id, strategy_config)
                task_results[strategy] = success
                status = "✅ 成功" if success else "❌ 失败"
                print(f"   - {strategy}: {status}")
                
            except Exception as e:
                task_results[strategy] = False
                print(f"   - {strategy}: ❌ 异常 - {e}")
        
        # 检查任务状态
        print(f"\n5. 检查调度任务状态...")
        jobs = strategy_scheduler.get_all_jobs()
        print(f"   当前任务数量: {len(jobs)}")
        
        for job in jobs:
            print(f"   - ID: {job['job_id']}")
            print(f"     名称: {job['name']}")
            print(f"     下次执行: {job['next_run_time']}")
            print(f"     触发器: {job['trigger']}")
            print()
        
    except Exception as e:
        print(f"   调度器测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 总结测试结果
    print("=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    all_updates_success = all(update_results.values())
    all_configs_exist = all(result.get('exists', False) for result in config_results.values())
    
    print(f"策略状态更新: {'✅ 全部成功' if all_updates_success else '❌ 存在失败'}")
    print(f"数据库配置记录: {'✅ 全部存在' if all_configs_exist else '❌ 存在缺失'}")
    
    if all_updates_success and all_configs_exist:
        print("\n🎉 修复验证成功！启动日志中的策略状态更新警告问题已解决")
        print("   - upsert操作确保了策略配置记录的正确创建")
        print("   - 策略调度器现在能够正常更新和创建策略状态")
    else:
        print("\n⚠️  仍存在问题，需要进一步检查")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_strategy_status_fix())