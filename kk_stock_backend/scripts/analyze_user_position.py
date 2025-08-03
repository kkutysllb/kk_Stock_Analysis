#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析用户持仓收益更新问题的脚本
"""

import sys
import os
from datetime import datetime, timedelta
import uuid
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from api.db_handler import get_db_handler

def is_trading_day(date: datetime) -> bool:
    """判断是否为交易日（周一到周五）"""
    return date.weekday() < 5  # 0-4 代表周一到周五

def format_datetime(dt) -> str:
    """格式化日期时间显示"""
    if dt is None:
        return "无"
    if isinstance(dt, str):
        return dt
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_currency(amount) -> str:
    """格式化货币显示"""
    if amount is None:
        return "0.00"
    return f"{amount:,.2f}"

def analyze_user_position_issue(phone: str = "+8613609247807"):
    """分析指定用户的持仓收益更新问题"""
    print("=" * 80)
    print(f"📱 分析用户 {phone} 的持仓收益更新问题")
    print("=" * 80)
    
    try:
        # 初始化数据库连接
        db_handler = get_db_handler()
        
        # 步骤1: 查找用户记录
        print("\n🔍 步骤1: 查找用户记录")
        users_collection = db_handler.get_collection('users')
        user = users_collection.find_one({'phone': phone})
        
        if not user:
            print(f"❌ 未找到手机号为 {phone} 的用户")
            return
        
        user_id = user.get('user_id')
        print(f"✅ 找到用户:")
        print(f"   用户ID: {user_id}")
        print(f"   用户名: {user.get('username', '未设置')}")
        print(f"   注册时间: {format_datetime(user.get('created_at'))}")
        print(f"   最后登录: {format_datetime(user.get('last_login'))}")
        
        # 步骤2: 查询账户信息
        print("\n🏦 步骤2: 查询模拟账户信息")
        accounts_collection = db_handler.get_collection('simulation_accounts')
        account = accounts_collection.find_one({'user_id': user_id})
        
        if not account:
            print(f"❌ 未找到用户 {user_id} 的模拟账户")
            return
        
        print(f"✅ 账户信息:")
        print(f"   账户ID: {account.get('account_id')}")
        print(f"   账户状态: {account.get('status', '未知')}")
        print(f"   总资产: ¥{format_currency(account.get('total_assets'))}")
        print(f"   现金余额: ¥{format_currency(account.get('cash_balance'))}")
        print(f"   持仓市值: ¥{format_currency(account.get('total_market_value'))}")
        print(f"   日收益: ¥{format_currency(account.get('daily_return'))}")
        print(f"   日收益率: {account.get('daily_return_rate', 0):.4f}%")
        print(f"   总收益: ¥{format_currency(account.get('total_return'))}")
        print(f"   总收益率: {account.get('total_return_rate', 0):.4f}%")
        print(f"   最后更新时间: {format_datetime(account.get('last_update_time'))}")
        
        account_id = account.get('account_id')
        
        # 步骤3: 查询持仓数据
        print("\n📊 步骤3: 查询持仓数据")
        positions_collection = db_handler.get_collection('simulation_positions')
        positions = list(positions_collection.find({'account_id': account_id}))
        
        if not positions:
            print("❌ 未找到任何持仓数据")
        else:
            print(f"✅ 找到 {len(positions)} 个持仓:")
            
            total_market_value = 0
            total_unrealized_pnl = 0
            
            for i, position in enumerate(positions, 1):
                stock_code = position.get('stock_code', '未知')
                quantity = position.get('quantity', 0)
                cost_price = position.get('cost_price', 0)
                current_price = position.get('current_price', 0)
                market_value = position.get('market_value', 0)
                unrealized_pnl = position.get('unrealized_pnl', 0)
                last_price_update = position.get('last_price_update')
                
                total_market_value += market_value
                total_unrealized_pnl += unrealized_pnl
                
                print(f"\n   持仓 {i}: {stock_code}")
                print(f"      数量: {quantity:,} 股")
                print(f"      成本价: ¥{cost_price:.3f}")
                print(f"      当前价: ¥{current_price:.3f}")
                print(f"      市值: ¥{format_currency(market_value)}")
                print(f"      未实现盈亏: ¥{format_currency(unrealized_pnl)}")
                print(f"      价格更新时间: {format_datetime(last_price_update)}")
                
                # 检查价格更新是否及时
                if last_price_update:
                    now = datetime.now()
                    if isinstance(last_price_update, str):
                        try:
                            last_price_update = datetime.fromisoformat(last_price_update.replace('Z', '+00:00'))
                        except:
                            pass
                    
                    if isinstance(last_price_update, datetime):
                        time_diff = now - last_price_update
                        if time_diff.total_seconds() > 3600:  # 超过1小时
                            print(f"      ⚠️  价格更新滞后: {time_diff}")
            
            print(f"\n📈 持仓汇总:")
            print(f"   计算总市值: ¥{format_currency(total_market_value)}")
            print(f"   计算总盈亏: ¥{format_currency(total_unrealized_pnl)}")
            print(f"   账户记录市值: ¥{format_currency(account.get('total_market_value'))}")
            
            # 检查数据一致性
            account_market_value = account.get('total_market_value', 0)
            if abs(total_market_value - account_market_value) > 0.01:
                print(f"   ❌ 市值不一致! 差异: ¥{format_currency(abs(total_market_value - account_market_value))}")
            else:
                print(f"   ✅ 市值数据一致")
        
        # 步骤4: 查询账户快照
        print("\n📸 步骤4: 查询最近7天的账户快照")
        snapshots_collection = db_handler.get_collection('account_snapshots')
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        snapshots = list(snapshots_collection.find({
            'account_id': account_id,
            'snapshot_date': {
                '$gte': start_date.strftime('%Y-%m-%d'),
                '$lte': end_date.strftime('%Y-%m-%d')
            }
        }).sort('snapshot_date', -1))
        
        if not snapshots:
            print("❌ 最近7天内没有账户快照数据")
        else:
            print(f"✅ 找到 {len(snapshots)} 个快照:")
            for snapshot in snapshots:
                snapshot_date = snapshot.get('snapshot_date')
                total_assets = snapshot.get('total_assets', 0)
                daily_return = snapshot.get('daily_return', 0)
                daily_return_rate = snapshot.get('daily_return_rate', 0)
                created_at = snapshot.get('created_at')
                
                print(f"   📅 {snapshot_date}: 总资产¥{format_currency(total_assets)}, "
                      f"日收益¥{format_currency(daily_return)} ({daily_return_rate:.4f}%), "
                      f"创建时间: {format_datetime(created_at)}")
        
        # 步骤5: 检查今天是否为交易日
        print("\n📅 步骤5: 检查交易日状态")
        now = datetime.now()
        today_is_trading_day = is_trading_day(now)
        
        print(f"   今天日期: {now.strftime('%Y-%m-%d %A')}")
        print(f"   是否交易日: {'是' if today_is_trading_day else '否'}")
        
        if today_is_trading_day:
            print("   ✅ 今天是交易日，定时任务应该执行")
        else:
            print("   ℹ️  今天不是交易日，定时任务可能不会执行")
        
        # 步骤6: 分析问题并给出建议
        print("\n🔍 步骤6: 问题分析与建议")
        print("-" * 50)
        
        issues_found = []
        
        # 检查账户最后更新时间
        last_update = account.get('last_update_time')
        if last_update:
            if isinstance(last_update, str):
                try:
                    last_update = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                except:
                    pass
            
            if isinstance(last_update, datetime):
                time_since_update = now - last_update
                if time_since_update.total_seconds() > 24 * 3600:  # 超过24小时
                    issues_found.append(f"账户数据超过24小时未更新 (上次更新: {format_datetime(last_update)})")
        
        # 检查持仓价格更新
        for position in positions:
            last_price_update = position.get('last_price_update')
            stock_code = position.get('stock_code')
            if last_price_update:
                if isinstance(last_price_update, str):
                    try:
                        last_price_update = datetime.fromisoformat(last_price_update.replace('Z', '+00:00'))
                    except:
                        continue
                
                if isinstance(last_price_update, datetime):
                    time_diff = now - last_price_update
                    if time_diff.total_seconds() > 6 * 3600:  # 超过6小时
                        issues_found.append(f"股票 {stock_code} 价格超过6小时未更新")
        
        # 检查快照创建
        today_str = now.strftime('%Y-%m-%d')
        today_snapshot = None
        for snapshot in snapshots:
            if snapshot.get('snapshot_date') == today_str:
                today_snapshot = snapshot
                break
        
        if today_is_trading_day and not today_snapshot:
            issues_found.append("今天是交易日但没有创建账户快照")
        
        # 数据一致性检查
        if positions:
            if abs(total_market_value - account.get('total_market_value', 0)) > 0.01:
                issues_found.append("持仓市值与账户记录不一致")
        
        # 输出问题和建议
        if issues_found:
            print("❌ 发现的问题:")
            for i, issue in enumerate(issues_found, 1):
                print(f"   {i}. {issue}")
            
            print("\n💡 建议的解决方案:")
            print("   1. 检查定时任务是否正常运行 (scheduler.py)")
            print("   2. 检查股价数据源是否正常更新")
            print("   3. 手动执行一次持仓更新任务")
            print("   4. 检查数据库连接和权限")
            print("   5. 查看应用程序日志了解具体错误信息")
        else:
            print("✅ 未发现明显问题，数据看起来正常")
        
        # 检查模拟交易调度器状态
        print("\n🤖 步骤7: 检查定时任务相关配置")
        try:
            from api.simulation.scheduler import scheduler
            if scheduler.running:
                print("   ✅ 定时任务调度器正在运行")
                jobs = scheduler.get_jobs()
                print(f"   📋 当前活跃任务数: {len(jobs)}")
                for job in jobs:
                    print(f"      - {job.id}: 下次执行 {job.next_run_time}")
            else:
                print("   ❌ 定时任务调度器未运行")
                issues_found.append("定时任务调度器未运行")
        except Exception as e:
            print(f"   ⚠️  无法检查定时任务状态: {e}")
        
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_user_position_issue()