#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库测试数据清理脚本
保留管理员账户，清除所有其他用户及相关数据
用于测试删除用户功能的准确性
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from api.cloud_db_handler import CloudDBHandler


class DatabaseCleaner:
    """数据库清理器"""
    
    def __init__(self):
        """初始化清理器"""
        self.db_handler = CloudDBHandler()
        
        # 管理员账户信息（从检查结果确认）
        self.admin_user_id = "946c1533-e852-45ca-abe2-54b9864b63b8"
        self.admin_email = "admin@kkquant.com"
        
        # 需要清理的用户相关集合
        self.user_related_collections = [
            "user_stock_pools",
            "user_pool_operations", 
            "strategy_screening_results",
            "user_analysis_operations",
            "user_analysis_results",
            "test_user_watchlist"
        ]
    
    def confirm_admin_user(self) -> bool:
        """确认管理员用户存在"""
        try:
            users_collection = self.db_handler.get_collection("users")
            admin_user = users_collection.find_one({
                "user_id": self.admin_user_id,
                "email": self.admin_email
            })
            
            if admin_user:
                print(f"✅ 确认管理员用户存在: {admin_user['nickname']} ({admin_user['email']})")
                print(f"   用户ID: {admin_user['user_id']}")
                print(f"   角色: {admin_user.get('roles', [])}")
                return True
            else:
                print(f"❌ 未找到管理员用户: {self.admin_user_id}")
                return False
                
        except Exception as e:
            print(f"❌ 检查管理员用户失败: {str(e)}")
            return False
    
    def get_non_admin_users(self) -> List[Dict[str, Any]]:
        """获取所有非管理员用户"""
        try:
            users_collection = self.db_handler.get_collection("users")
            non_admin_users = list(users_collection.find({
                "user_id": {"$ne": self.admin_user_id}
            }))
            
            print(f"\n📋 发现 {len(non_admin_users)} 个非管理员用户:")
            for i, user in enumerate(non_admin_users, 1):
                print(f"   {i}. {user.get('nickname', 'N/A')} ({user.get('email', 'N/A')})")
                print(f"      用户ID: {user['user_id']}")
                print(f"      角色: {user.get('roles', [])}")
                print()
            
            return non_admin_users
            
        except Exception as e:
            print(f"❌ 获取非管理员用户失败: {str(e)}")
            return []
    
    def clean_user_related_data(self, user_ids: List[str]) -> Dict[str, int]:
        """清理用户相关数据（包括孤立数据）"""
        cleanup_stats = {}
        
        print(f"\n🧹 开始清理所有非管理员用户的相关数据...")
        
        for collection_name in self.user_related_collections:
            try:
                collection = self.db_handler.get_collection(collection_name)
                
                # 删除所有非管理员的数据（包括已删除用户的孤立数据）
                result = collection.delete_many({
                    "user_id": {"$ne": self.admin_user_id}
                })
                cleanup_stats[collection_name] = result.deleted_count
                
                print(f"   ✅ {collection_name}: 删除 {result.deleted_count} 条记录")
                
            except Exception as e:
                print(f"   ❌ {collection_name}: 清理失败 - {str(e)}")
                cleanup_stats[collection_name] = 0
        
        return cleanup_stats
    
    def clean_non_admin_users(self, user_ids: List[str]) -> int:
        """删除非管理员用户"""
        try:
            users_collection = self.db_handler.get_collection("users")
            
            result = users_collection.delete_many({
                "user_id": {"$in": user_ids}
            })
            
            print(f"\n👤 删除用户记录: {result.deleted_count} 个")
            return result.deleted_count
            
        except Exception as e:
            print(f"❌ 删除用户记录失败: {str(e)}")
            return 0
    
    def verify_cleanup(self) -> bool:
        """验证清理结果"""
        try:
            users_collection = self.db_handler.get_collection("users")
            
            # 检查只剩管理员用户
            remaining_users = list(users_collection.find())
            
            print(f"\n🔍 验证清理结果:")
            print(f"   剩余用户数量: {len(remaining_users)}")
            
            if len(remaining_users) == 1:
                admin_user = remaining_users[0]
                if admin_user["user_id"] == self.admin_user_id:
                    print(f"   ✅ 仅保留管理员用户: {admin_user['nickname']} ({admin_user['email']})")
                    
                    # 检查用户相关集合是否已清空
                    print(f"\n📊 检查相关集合清理情况:")
                    all_clean = True
                    
                    for collection_name in self.user_related_collections:
                        try:
                            collection = self.db_handler.get_collection(collection_name)
                            count = collection.count_documents({})
                            print(f"   {collection_name}: {count} 条记录")
                            if count > 0:
                                # 检查是否还有非管理员数据
                                non_admin_count = collection.count_documents({
                                    "user_id": {"$ne": self.admin_user_id}
                                })
                                if non_admin_count > 0:
                                    print(f"     ⚠️  仍有 {non_admin_count} 条非管理员数据")
                                    all_clean = False
                        except Exception as e:
                            print(f"   ❌ 检查 {collection_name} 失败: {str(e)}")
                    
                    return all_clean
                else:
                    print(f"   ❌ 剩余用户不是管理员: {admin_user['user_id']}")
                    return False
            else:
                print(f"   ❌ 剩余用户数量不正确，应该只有1个管理员")
                for user in remaining_users:
                    print(f"     - {user['nickname']} ({user['user_id']})")
                return False
                
        except Exception as e:
            print(f"❌ 验证清理结果失败: {str(e)}")
            return False
    
    def run_cleanup(self, confirm: bool = False) -> bool:
        """执行完整的清理流程"""
        print("=" * 80)
        print("🧹 数据库测试数据清理工具")
        print("=" * 80)
        print("⚠️  警告: 此操作将删除除管理员外的所有用户及相关数据！")
        print(f"📋 保留管理员: {self.admin_email} ({self.admin_user_id})")
        print("=" * 80)
        
        # 1. 确认管理员用户存在
        if not self.confirm_admin_user():
            print("❌ 清理终止: 管理员用户不存在")
            return False
        
        # 2. 获取非管理员用户
        non_admin_users = self.get_non_admin_users()
        if not non_admin_users:
            print("✅ 数据库中只有管理员用户，无需清理")
            return True
        
        # 3. 二次确认
        if not confirm:
            user_input = input(f"\n❓ 确认删除 {len(non_admin_users)} 个用户及其所有相关数据? (输入 'YES' 确认): ")
            if user_input != "YES":
                print("❌ 清理已取消")
                return False
        
        # 4. 执行清理
        user_ids = [user["user_id"] for user in non_admin_users]
        
        print(f"\n🚀 开始执行清理...")
        start_time = datetime.now()
        
        # 清理用户相关数据
        cleanup_stats = self.clean_user_related_data(user_ids)
        
        # 删除用户记录
        deleted_users = self.clean_non_admin_users(user_ids)
        
        # 5. 验证清理结果
        success = self.verify_cleanup()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 6. 输出总结
        print(f"\n" + "=" * 80)
        print(f"📊 清理完成总结")
        print(f"=" * 80)
        print(f"⏱️  耗时: {duration:.2f} 秒")
        print(f"👤 删除用户: {deleted_users} 个")
        print(f"📄 清理数据详情:")
        
        total_deleted = 0
        for collection_name, count in cleanup_stats.items():
            print(f"   {collection_name}: {count} 条")
            total_deleted += count
        
        print(f"📊 总计删除记录: {total_deleted} 条")
        print(f"✅ 清理状态: {'成功' if success else '失败'}")
        
        if success:
            print(f"\n🎉 数据库已准备就绪，可以进行删除用户功能测试！")
        else:
            print(f"\n⚠️  清理过程中出现问题，请检查上述日志")
        
        return success


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库测试数据清理工具')
    parser.add_argument('--confirm', '-y', action='store_true', help='自动确认清理，跳过交互确认')
    parser.add_argument('--dry-run', '-d', action='store_true', help='只检查不执行清理')
    
    args = parser.parse_args()
    
    cleaner = DatabaseCleaner()
    
    if args.dry_run:
        print("🔍 干运行模式 - 只检查不执行清理")
        cleaner.confirm_admin_user()
        cleaner.get_non_admin_users()
        return
    
    success = cleaner.run_cleanup(confirm=args.confirm)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()