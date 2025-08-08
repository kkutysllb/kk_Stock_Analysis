"""
量化策略定时调度器

使用APScheduler实现策略的定时自动化执行
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from typing import Dict, Any, List, Optional
import logging
import asyncio
from datetime import datetime, time

from .strategy_adapter import StrategyRunner, strategy_runner
from .database import simulation_db


class StrategyScheduler:
    """策略定时调度器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 配置调度器
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'
        )
        
        self.strategy_runner = strategy_runner
        self._is_running = False
        
    def start(self):
        """启动调度器"""
        try:
            if not self._is_running:
                self.scheduler.start()
                self._is_running = True
                self.logger.info("策略调度器启动成功")
                
                # 启动时加载所有激活的策略
                asyncio.create_task(self._load_active_strategies())
            else:
                self.logger.warning("策略调度器已在运行中")
                
        except Exception as e:
            self.logger.error(f"启动策略调度器失败: {e}")
    
    def stop(self):
        """停止调度器"""
        try:
            if self._is_running:
                self.scheduler.shutdown()
                self._is_running = False
                self.logger.info("策略调度器已停止")
            else:
                self.logger.warning("策略调度器未在运行")
                
        except Exception as e:
            self.logger.error(f"停止策略调度器失败: {e}")
    
    async def start_user_strategy(self, user_id: str, strategy_config: Dict[str, Any]) -> bool:
        """
        启动用户策略自动交易
        
        Args:
            user_id: 用户ID
            strategy_config: 策略配置
                {
                    'strategy_name': str,
                    'allocated_cash': float,
                    'custom_params': dict
                }
        
        Returns:
            启动是否成功
        """
        try:
            strategy_name = strategy_config.get('strategy_name')
            job_id = f"strategy_{user_id}_{strategy_name}"
            
            # 检查任务是否已存在
            if self.scheduler.get_job(job_id):
                self.logger.info(f"策略任务已存在，重新配置: {job_id}")
                # 删除旧任务，重新创建
                self.scheduler.remove_job(job_id)
            
            # 根据策略的内置调仓频率设置定时任务
            if strategy_name == 'taishang_3':
                # 小市值动量策略：每5个交易日（每周一次）
                self.scheduler.add_job(
                    self._execute_strategy_job,
                    'cron',
                    day_of_week='mon',  # 每周一执行
                    hour=9, minute=35,  # 开盘后5分钟
                    args=[user_id, strategy_config],
                    id=job_id,
                    name=f"用户{user_id}的{strategy_name}策略",
                    misfire_grace_time=300  # 5分钟容错时间
                )
            else:
                # 多趋势共振策略、布林带策略：每日检查
                self.scheduler.add_job(
                    self._execute_strategy_job,
                    'cron',
                    day_of_week='mon-fri',  # 工作日执行
                    hour=9, minute=35,      # 开盘后5分钟
                    args=[user_id, strategy_config],
                    id=job_id,
                    name=f"用户{user_id}的{strategy_name}策略",
                    misfire_grace_time=300  # 5分钟容错时间
                )
            
            # 更新数据库中的策略状态
            try:
                success = simulation_db.update_strategy_status(user_id, strategy_name, True)
                if not success:
                    self.logger.warning(f"策略状态更新失败，但任务已创建: {job_id}")
            except Exception as e:
                self.logger.error(f"更新策略状态异常: {e}")
                # 即使状态更新失败，也不删除任务，让策略能够执行
                pass
            
            self.logger.info(f"策略定时任务创建成功: {job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"启动用户策略失败: {e}")
            return False
    
    async def stop_user_strategy(self, user_id: str, strategy_name: str) -> bool:
        """
        停止用户策略自动交易
        
        Args:
            user_id: 用户ID
            strategy_name: 策略名称
        
        Returns:
            停止是否成功
        """
        try:
            job_id = f"strategy_{user_id}_{strategy_name}"
            
            # 删除定时任务
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                self.logger.info(f"策略定时任务删除成功: {job_id}")
            else:
                self.logger.warning(f"策略定时任务不存在: {job_id}")
            
            # 更新数据库中的策略状态
            success = simulation_db.update_strategy_status(user_id, strategy_name, False)
            
            return success
            
        except Exception as e:
            self.logger.error(f"停止用户策略失败: {e}")
            return False
    
    async def _execute_strategy_job(self, user_id: str, strategy_config: Dict[str, Any]):
        """
        执行策略任务（由调度器调用）
        
        Args:
            user_id: 用户ID
            strategy_config: 策略配置
        """
        strategy_name = strategy_config.get('strategy_name', 'unknown')
        
        try:
            self.logger.info(f"开始执行定时策略任务: {user_id} - {strategy_name}")
            
            # 检查是否为交易时间（手动执行时跳过时间检查）
            # if not self._is_trading_time():
            #     self.logger.info(f"非交易时间，跳过策略执行: {strategy_name}")
            #     return
            self.logger.info(f"开始执行策略（跳过交易时间检查）: {strategy_name}")
            
            # 检查策略是否仍然激活
            config = simulation_db.get_user_strategy_config(user_id, strategy_name)
            if not config or not config.get('is_active', False):
                self.logger.warning(f"策略已停用，跳过执行: {user_id} - {strategy_name}")
                return
            
            # 执行策略
            executed_trades = await self.strategy_runner.run_strategy_realtime(user_id, strategy_config)
            
            # 获取当前持仓
            current_positions = await self._get_strategy_positions(user_id, strategy_name)
            
            # 更新执行记录
            simulation_db.update_strategy_execution_record(
                user_id=user_id,
                strategy_name=strategy_name,
                execution_time=datetime.now(),
                total_signals=len(executed_trades),  # 简化处理
                executed_trades=len(executed_trades),
                current_positions=current_positions
            )
            
            self.logger.info(f"策略任务执行完成: {user_id} - {strategy_name}, 交易: {len(executed_trades)}")
            
        except Exception as e:
            self.logger.error(f"执行策略任务失败: {user_id} - {strategy_name}: {e}")
    
    async def _load_active_strategies(self):
        """加载所有激活的策略并创建定时任务"""
        try:
            active_configs = simulation_db.get_active_strategy_configs()
            
            for config in active_configs:
                user_id = config.get('user_id')
                strategy_name = config.get('strategy_name')
                
                if user_id and strategy_name:
                    strategy_config = {
                        'strategy_name': strategy_name,
                        'allocated_cash': config.get('allocated_cash', 300000),
                        'custom_params': config.get('custom_params', {})
                    }
                    
                    await self.start_user_strategy(user_id, strategy_config)
            
            self.logger.info(f"加载激活策略完成，共 {len(active_configs)} 个策略")
            
        except Exception as e:
            self.logger.error(f"加载激活策略失败: {e}")
    
    def _is_trading_time(self) -> bool:
        """
        判断是否为交易时间
        
        Returns:
            是否为交易时间
        """
        # 复用数据库中的交易时间判断逻辑
        return simulation_db.is_trading_time()
    
    async def _get_strategy_positions(self, user_id: str, strategy_name: str) -> List[str]:
        """
        获取策略的当前持仓股票列表
        
        Args:
            user_id: 用户ID
            strategy_name: 策略名称
            
        Returns:
            持仓股票代码列表
        """
        try:
            # 这里应该查询用户的持仓，并过滤出属于该策略的持仓
            # 简化实现，返回空列表
            # 实际实现时需要根据交易记录中的strategy_name字段来匹配
            return []
            
        except Exception as e:
            self.logger.error(f"获取策略持仓失败: {e}")
            return []
    
    def get_job_status(self, user_id: str, strategy_name: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            user_id: 用户ID
            strategy_name: 策略名称
            
        Returns:
            任务状态信息
        """
        try:
            job_id = f"strategy_{user_id}_{strategy_name}"
            job = self.scheduler.get_job(job_id)
            
            if job:
                return {
                    'job_id': job_id,
                    'name': job.name,
                    'next_run_time': job.next_run_time,
                    'trigger': str(job.trigger),
                    'is_active': True
                }
            else:
                return {
                    'job_id': job_id,
                    'is_active': False
                }
                
        except Exception as e:
            self.logger.error(f"获取任务状态失败: {e}")
            return None
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """
        获取所有调度任务
        
        Returns:
            任务列表
        """
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'job_id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time,
                    'trigger': str(job.trigger)
                })
            return jobs
            
        except Exception as e:
            self.logger.error(f"获取所有任务失败: {e}")
            return []


# 创建全局调度器实例
strategy_scheduler = StrategyScheduler()