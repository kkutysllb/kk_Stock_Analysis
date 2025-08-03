"""
模拟交易系统定时任务

处理T+1交割、每日快照、价格更新等定时任务
"""

import asyncio
import logging
from datetime import datetime, date, time, timedelta
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .service import simulation_service
from .database import simulation_db
from api.db_handler import get_db_handler


logger = logging.getLogger(__name__)


class SimulationScheduler:
    """模拟交易定时任务调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')
        self.db_handler = get_db_handler()
        self.is_running = False
    
    def start(self):
        """启动定时任务调度器"""
        if self.is_running:
            logger.info("模拟交易定时任务调度器已经在运行中")
            return
        
        try:
            # 添加定时任务
            self._add_jobs()
            
            # 启动调度器
            self.scheduler.start()
            self.is_running = True
            
            logger.info("模拟交易定时任务调度器已启动")
            
        except RuntimeError as e:
            if "running event loop" in str(e):
                logger.warning("AsyncIOScheduler需要在异步环境中运行，将使用阻塞模式启动")
                # 在主应用中，AsyncIOScheduler会自动在事件循环中运行
                try:
                    self._add_jobs()
                    self.scheduler.start()
                    self.is_running = True
                    logger.info("模拟交易定时任务调度器已启动（阻塞模式）")
                except Exception as inner_e:
                    logger.error(f"阻塞模式启动失败: {inner_e}")
            else:
                logger.error(f"启动定时任务调度器失败: {e}")
        except Exception as e:
            logger.error(f"启动定时任务调度器失败: {e}")
    
    def stop(self):
        """停止定时任务调度器"""
        if not self.is_running:
            logger.info("模拟交易定时任务调度器未在运行")
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("模拟交易定时任务调度器已停止")
        except Exception as e:
            logger.error(f"停止定时任务调度器失败: {e}")
    
    def _add_jobs(self):
        """添加定时任务"""
        
        # 每日凌晨0:30处理T+1交割
        self.scheduler.add_job(
            self.process_daily_settlement,
            CronTrigger(hour=0, minute=30),
            id='daily_settlement',
            name='每日T+1交割处理',
            max_instances=1,
            coalesce=True
        )
        
        # 每日收盘后19:00创建当日账户快照
        self.scheduler.add_job(
            self.create_daily_snapshots,
            CronTrigger(
                day_of_week='mon-fri', 
                hour=19, 
                minute=0
            ),
            id='daily_snapshots',
            name='每日账户快照创建',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600  # 1小时内的错过执行仍然会执行
        )
        
        # 交易时间内每5分钟更新持仓价格
        self.scheduler.add_job(
            self.update_position_prices,
            CronTrigger(
                day_of_week='mon-fri',
                hour='9-11,13-15',
                minute='*/5'
            ),
            id='update_prices',
            name='更新持仓价格',
            max_instances=1,
            coalesce=True
        )
        
        # 每日收盘后19:30更新账户收益（确保数据采集完成）
        self.scheduler.add_job(
            self.update_daily_returns,
            CronTrigger(
                day_of_week='mon-fri',
                hour=19,
                minute=30
            ),
            id='daily_returns',
            name='更新每日收益',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600  # 1小时内的错过执行仍然会执行
        )
        
        logger.info("定时任务已添加完成")
    
    async def process_daily_settlement(self):
        """处理每日T+1交割"""
        try:
            logger.info("开始处理T+1交割...")
            
            # 处理前一日的买入交易，释放可卖数量
            await simulation_service.process_t_plus_one_settlement()
            
            logger.info("T+1交割处理完成")
            
        except Exception as e:
            logger.error(f"T+1交割处理失败: {e}")
    
    async def create_daily_snapshots(self):
        """创建每日账户快照"""
        try:
            logger.info("开始创建每日账户快照...")
            
            # 获取所有活跃用户
            users_col = self.db_handler.get_collection("users")
            users = list(users_col.find({"status": 1}, {"user_id": 1}))
            
            success_count = 0
            for user in users:
                try:
                    user_id = user["user_id"]
                    await simulation_service.create_daily_snapshot(user_id)
                    success_count += 1
                except Exception as e:
                    logger.warning(f"用户 {user['user_id']} 快照创建失败: {e}")
            
            logger.info(f"每日快照创建完成，成功: {success_count}/{len(users)}")
            
        except Exception as e:
            logger.error(f"创建每日快照失败: {e}")
    
    async def update_position_prices(self):
        """更新持仓价格"""
        try:
            logger.info("开始更新持仓价格...")
            
            # 获取所有持仓
            positions_col = self.db_handler.get_collection(simulation_db.POSITIONS_COLLECTION)
            positions = list(positions_col.find({}))
            
            # 按股票代码分组，减少重复查询
            stock_codes = list(set(pos["stock_code"] for pos in positions))
            
            # 批量获取股价
            stock_prices = {}
            for stock_code in stock_codes:
                try:
                    price = await simulation_service._get_current_stock_price(stock_code)
                    if price:
                        stock_prices[stock_code] = price
                except Exception as e:
                    logger.warning(f"获取股票 {stock_code} 价格失败: {e}")
            
            # 更新持仓价格
            update_count = 0
            for position in positions:
                stock_code = position["stock_code"]
                if stock_code in stock_prices:
                    current_price = stock_prices[stock_code]
                    market_value = position["total_quantity"] * current_price
                    unrealized_pnl = market_value - position["cost_value"]
                    unrealized_pnl_rate = unrealized_pnl / position["cost_value"] if position["cost_value"] > 0 else 0
                    
                    # 更新持仓数据
                    simulation_db.create_or_update_position({
                        **position,
                        "current_price": current_price,
                        "market_value": market_value,
                        "unrealized_pnl": unrealized_pnl,
                        "unrealized_pnl_rate": unrealized_pnl_rate,
                        "last_price_update": datetime.now()
                    })
                    update_count += 1
            
            logger.info(f"持仓价格更新完成，更新: {update_count} 个持仓")
            
        except Exception as e:
            logger.error(f"更新持仓价格失败: {e}")
    
    def get_latest_trading_date_and_previous(self, current_date: date) -> tuple[date, date]:
        """获取最近的交易日和它的上一个交易日（用于计算每日收益）"""
        try:
            trading_calendar_col = self.db_handler.get_collection("infrastructure_trading_calendar")
            current_date_str = current_date.strftime("%Y%m%d")
            
            # 查找当前日期或之前最近的交易日
            latest_trading_record = trading_calendar_col.find_one({
                "cal_date": {"$lte": current_date_str},
                "exchange": "SSE",
                "is_open": 1
            }, sort=[("cal_date", -1)])
            
            if latest_trading_record and "pretrade_date" in latest_trading_record:
                # 最近的交易日
                latest_date_str = latest_trading_record["cal_date"]
                latest_year = int(latest_date_str[:4])
                latest_month = int(latest_date_str[4:6])
                latest_day = int(latest_date_str[6:8])
                latest_trading_date = date(latest_year, latest_month, latest_day)
                
                # 上一个交易日
                pretrade_date_str = latest_trading_record["pretrade_date"]
                prev_year = int(pretrade_date_str[:4])
                prev_month = int(pretrade_date_str[4:6])
                prev_day = int(pretrade_date_str[6:8])
                previous_trading_date = date(prev_year, prev_month, prev_day)
                
                return latest_trading_date, previous_trading_date
            else:
                # 如果没有找到，回退到自然日计算
                logger.warning(f"未找到 {current_date} 的交易日信息，使用自然日计算")
                fallback_latest = current_date - timedelta(days=1)
                fallback_previous = current_date - timedelta(days=2)
                return fallback_latest, fallback_previous
                
        except Exception as e:
            logger.error(f"获取交易日失败: {e}")
            # 出错时回退到自然日计算
            fallback_latest = current_date - timedelta(days=1)
            fallback_previous = current_date - timedelta(days=2)
            return fallback_latest, fallback_previous

    async def update_daily_returns(self):
        """更新每日收益 - 基于持仓股价变化计算"""
        try:
            logger.info("开始更新每日收益...")
            
            # 获取所有模拟账户
            accounts_col = self.db_handler.get_collection(simulation_db.ACCOUNTS_COLLECTION)
            accounts = list(accounts_col.find({"status": 1}))
            
            today = date.today()
            # 获取最近的交易日和它的上一个交易日
            latest_trading_date, previous_trading_date = self.get_latest_trading_date_and_previous(today)
            
            # 转换为YYYYMMDD格式（数据库中trade_date的格式）
            latest_date_str = latest_trading_date.strftime("%Y%m%d")
            previous_date_str = previous_trading_date.strftime("%Y%m%d")
            
            logger.info(f"当前日期: {today}, 最近交易日: {latest_trading_date} ({latest_date_str}), 上一交易日: {previous_trading_date} ({previous_date_str})")
            
            update_count = 0
            for account in accounts:
                try:
                    user_id = account["user_id"]
                    
                    # 获取用户持仓
                    positions = simulation_db.get_user_positions(user_id)
                    if not positions:
                        logger.debug(f"用户 {user_id} 无持仓，跳过")
                        continue
                    
                    # 计算持仓日收益
                    total_daily_return = 0.0
                    total_previous_value = 0.0
                    valid_positions = 0
                    
                    for position in positions:
                        stock_code = position["stock_code"]
                        quantity = position["total_quantity"]
                        
                        # 获取今日和昨日价格
                        today_price = await simulation_service._get_stock_price_by_date(stock_code, latest_date_str)
                        yesterday_price = await simulation_service._get_stock_price_by_date(stock_code, previous_date_str)
                        
                        if today_price is not None and yesterday_price is not None:
                            # 计算这只股票的收益贡献
                            today_value = quantity * today_price
                            yesterday_value = quantity * yesterday_price
                            stock_return = today_value - yesterday_value
                            
                            total_daily_return += stock_return
                            total_previous_value += yesterday_value
                            valid_positions += 1
                            
                            logger.debug(f"  {stock_code}: {quantity}股, 昨价{yesterday_price:.4f}, 今价{today_price:.4f}, 收益{stock_return:,.2f}")
                        else:
                            logger.warning(f"  {stock_code}: 价格数据缺失 (今日:{today_price}, 昨日:{yesterday_price})")
                    
                    if valid_positions > 0:
                        # 计算收益率
                        daily_return_rate = total_daily_return / total_previous_value if total_previous_value > 0 else 0
                        
                        # 更新账户日收益
                        simulation_db.update_simulation_account(user_id, {
                            "daily_return": total_daily_return,
                            "daily_return_rate": daily_return_rate
                        })
                        
                        # 更新总资产和总收益
                        await simulation_service._update_account_assets(user_id)
                        
                        update_count += 1
                        logger.info(f"用户 {user_id}: 持仓收益 {total_daily_return:,.2f}元 ({daily_return_rate:.4f}), 有效持仓 {valid_positions}/{len(positions)}")
                    else:
                        logger.warning(f"用户 {user_id}: 无有效价格数据，无法计算收益")
                    
                except Exception as e:
                    logger.warning(f"用户 {account['user_id']} 收益更新失败: {e}")
                    import traceback
                    traceback.print_exc()
            
            logger.info(f"每日收益更新完成，更新: {update_count} 个账户")
            
        except Exception as e:
            logger.error(f"更新每日收益失败: {e}")
            import traceback
            traceback.print_exc()
    
    async def manual_run_settlement(self):
        """手动运行T+1交割（用于测试）"""
        await self.process_daily_settlement()
    
    async def manual_run_snapshots(self):
        """手动运行快照创建（用于测试）"""
        await self.create_daily_snapshots()
    
    async def manual_run_price_update(self):
        """手动运行价格更新（用于测试）"""
        await self.update_position_prices()
    
    async def manual_run_returns_update(self):
        """手动运行收益更新（用于测试）"""
        await self.update_daily_returns()


# 创建全局调度器实例
simulation_scheduler = SimulationScheduler()


def start_simulation_scheduler():
    """启动模拟交易定时任务调度器"""
    simulation_scheduler.start()


def stop_simulation_scheduler():
    """停止模拟交易定时任务调度器"""
    simulation_scheduler.stop()


# 在应用启动时自动启动调度器
import atexit
atexit.register(stop_simulation_scheduler)