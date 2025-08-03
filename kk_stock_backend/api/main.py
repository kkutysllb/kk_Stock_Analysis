import os
import asyncio
import logging
import os
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

# 导入路由模块
from api.routers import user, market, strategy, user_stock_pools, analysis_results, backtest_unified, simulation
from api.routers import (
    stock_data, index_data, financial_data,
    market_flow, margin_data, dragon_tiger,
    analytics, admin, system, trading_calendar,
    concept_data, hm_data, futures_data, etf_data,
    sentiment_analytics, database_config, cache_demo,
    dow_theory_analysis, macro_data, options_data,
    limit_data, relative_valuation, margin_trading,
    market_margin_analysis
)

# 导入缓存管理器
from cache_manager import init_cache_manager, get_cache_manager
from cache_config import get_cache_config

# 导入模拟交易调度器
from api.simulation.scheduler import start_simulation_scheduler, stop_simulation_scheduler

# 导入中间件
from api.middleware import AdvancedRateLimitMiddleware

# 加载环境变量
load_dotenv()

# 配置
API_PORT = int(os.getenv("API_PORT", 9001))
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_RELOAD = os.getenv("API_RELOAD", "false").lower() == "true"

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时的初始化
    logger.info("🚀 正在启动量化分析API服务...")
    
    try:
        # 初始化Redis缓存管理器
        logger.info("📦 正在初始化Redis缓存...")
        environment = os.getenv("ENVIRONMENT", "development")
        cache_config = get_cache_config(environment)
        
        redis_config = cache_config['redis']
        redis_host = os.getenv("REDIS_HOST", redis_config['host'])
        redis_port = int(os.getenv("REDIS_PORT", redis_config['port']))
        redis_db = int(os.getenv("REDIS_DB", redis_config['db']))
        redis_password = os.getenv("REDIS_PASSWORD", redis_config['password'])
        
        cache_manager = init_cache_manager(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password
        )
        
        if cache_manager and cache_manager.is_available():
            logger.info(f"✅ Redis缓存连接成功: {redis_host}:{redis_port}/{redis_db}")
            
            # 清理损坏的缓存数据
            try:
                cleared_count = cache_manager.clear_corrupted_cache()
                if cleared_count > 0:
                    logger.info(f"🧹 清理了 {cleared_count} 个损坏的缓存键")
                else:
                    logger.info("✨ 缓存数据完整，无需清理")
            except Exception as e:
                logger.warning(f"⚠️ 缓存清理失败: {e}")
            
            # 获取缓存统计信息
            stats = cache_manager.get_stats()
            logger.info(f"📊 Redis状态: {stats.get('status', 'unknown')}")
            
            # 存储缓存管理器到应用状态
            app.state.cache_manager = cache_manager
            app.state.cache_config = cache_config
        else:
            logger.warning("⚠️ Redis缓存不可用，将使用无缓存模式")
            app.state.cache_manager = None
            app.state.cache_config = cache_config
        
        # 启动模拟交易定时任务调度器
        logger.info("📅 正在启动模拟交易定时任务调度器...")
        try:
            start_simulation_scheduler()
            logger.info("✅ 模拟交易定时任务调度器启动成功")
        except Exception as e:
            logger.error(f"❌ 模拟交易调度器启动失败: {e}")
        
        # 启动策略自动化调度器
        logger.info("🤖 正在启动策略自动化调度器...")
        try:
            from api.simulation.strategy_scheduler import strategy_scheduler
            strategy_scheduler.start()
            logger.info("✅ 策略自动化调度器启动成功")
        except Exception as e:
            logger.error(f"❌ 策略自动化调度器启动失败: {e}")
        
        logger.info("🎉 API服务启动完成！")
        
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        # 即使Redis失败也继续启动服务
        app.state.cache_manager = None
        logger.warning("⚠️ 将在无缓存模式下启动服务")
    
    yield
    
    # 关闭时的清理
    logger.info("🛑 正在关闭API服务...")
    
    try:
        # 停止模拟交易定时任务调度器
        logger.info("🛑 正在停止模拟交易定时任务调度器...")
        try:
            stop_simulation_scheduler()
            logger.info("✅ 模拟交易定时任务调度器已停止")
        except Exception as e:
            logger.error(f"❌ 停止模拟交易调度器失败: {e}")
        
        # 停止策略自动化调度器
        logger.info("🛑 正在停止策略自动化调度器...")
        try:
            from api.simulation.strategy_scheduler import strategy_scheduler
            strategy_scheduler.stop()
            logger.info("✅ 策略自动化调度器已停止")
        except Exception as e:
            logger.error(f"❌ 停止策略自动化调度器失败: {e}")
        
        # 清理缓存连接
        cache_manager = getattr(app.state, 'cache_manager', None)
        if cache_manager:
            logger.info("🧹 正在清理Redis连接...")
            # Redis连接池会自动清理，这里只是记录日志
            logger.info("✅ Redis连接已清理")
        
        logger.info("👋 API服务已安全关闭")
        
    except Exception as e:
        logger.error(f"❌ 服务关闭时出错: {e}")

# 创建FastAPI应用
app = FastAPI(
    title="量化分析API",
    description="""
    🚀 跨平台量化分析与策略建议系统API
    
    ## 主要特性
    - 📊 66个数据集合，涵盖股票、指数、期货、ETF等
    - 💾 双数据库架构（云端+本地）
    - 📈 实时性能监控
    - 🔍 多维度数据查询和分析
    
    ## 数据覆盖
    - 基础设施数据：交易日历、股票信息、公司信息
    - 行情数据：日线、周线、月线K线数据
    - 财务数据：三大报表、财务指标、业绩预告
    - 资金流向：个股、行业、大盘资金流向
    - 融资融券：融资融券汇总和明细
    - 龙虎榜：龙虎榜统计和机构交易
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 中间件配置
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000  # 启用gzip压缩
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启用高级限流中间件
app.add_middleware(AdvancedRateLimitMiddleware)



# 全局异常处理器
@app.exception_handler(429)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={
            "error": "请求频率过高",
            "message": "请稍后再试或升级账户以获得更高的请求限额",
            "retry_after": 60
        },
        headers={"Retry-After": "60"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"内部服务器错误: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "内部服务器错误",
            "message": "服务暂时不可用，请稍后重试"
        }
    )

# 健康检查和系统状态
@app.get("/")
async def read_root():
    return {
        "message": "🚀 量化分析API服务",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "多维度数据查询",
            "股票技术分析",
            "市场数据统计",
            "双数据库架构"
        ]
    }

@app.get("/health")
async def health_check():
    """系统健康检查"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "message": "API服务运行正常",
            "version": "2.0.0"
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

@app.get("/metrics")
async def get_metrics():
    """获取系统性能指标"""
    try:
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "api_version": "2.0.0",
            "status": "running"
        }
        
        # 获取缓存统计信息
        cache_manager = getattr(app.state, 'cache_manager', None)
        if cache_manager:
            cache_stats = cache_manager.get_stats()
            metrics["cache"] = cache_stats
        else:
            metrics["cache"] = {"status": "disabled"}
        
        return metrics
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# 挂载所有路由模块
# 用户认证和管理
app.include_router(user.router, prefix="/user", tags=["用户管理"])
app.include_router(user_stock_pools.router, prefix="/user", tags=["用户股票池"])
app.include_router(analysis_results.router, prefix="/user", tags=["分析结果管理"])

# 核心数据接口
app.include_router(market.router, prefix="/market", tags=["市场数据"])
app.include_router(stock_data.router, prefix="/stock", tags=["股票数据"])
app.include_router(index_data.router, prefix="/index", tags=["指数数据"])
app.include_router(financial_data.router, prefix="/financial", tags=["财务数据"])
app.include_router(futures_data.router, prefix="/futures", tags=["期货数据"])
app.include_router(etf_data.router, prefix="/etf", tags=["ETF数据"])
app.include_router(options_data.router, prefix="/options", tags=["期权数据"])
app.include_router(trading_calendar.router, prefix="/calendar", tags=["交易日历"])
app.include_router(concept_data.router)
app.include_router(hm_data.router, prefix="/hm", tags=["HM自定义数据"])
app.include_router(macro_data.router, prefix="/macro", tags=["宏观数据"])
app.include_router(limit_data.router, prefix="/limit_data", tags=["涨跌停数据"])

# 资金和交易数据
app.include_router(market_flow.router, prefix="/money_flow", tags=["资金流向"])
app.include_router(margin_data.router, prefix="/margin", tags=["融资融券"])
app.include_router(margin_trading.router, tags=["融资融券分析"])
app.include_router(market_margin_analysis.router, tags=["两市融资融券分析"])
app.include_router(dragon_tiger.router, prefix="/dragon-tiger", tags=["龙虎榜"])

# 分析和策略
app.include_router(analytics.router, prefix="/analytics", tags=["数据分析"])
app.include_router(sentiment_analytics.router, prefix="/sentiment", tags=["市场情绪分析"])
app.include_router(strategy.router, prefix="/strategy", tags=["投资策略"])
app.include_router(backtest_unified.router, prefix="/backtest", tags=["统一回测接口"])
app.include_router(dow_theory_analysis.router, tags=["道氏理论分析"])
app.include_router(relative_valuation.router, tags=["相对估值分析"])

# 模拟交易
app.include_router(simulation.router, tags=["模拟交易"])

# 智能内容生成模块已删除

# 系统管理
app.include_router(admin.router, prefix="/admin", tags=["系统管理"])
app.include_router(system.router, prefix="/system", tags=["系统监控"])
app.include_router(database_config.router, prefix="/admin", tags=["数据库配置"])

# 缓存演示和管理
app.include_router(cache_demo.router, prefix="/cache", tags=["缓存演示"])

if __name__ == "__main__":
    # 先使用单worker确保服务正常启动，后续可以通过环境变量控制
    worker_count = int(os.getenv("UVICORN_WORKERS", 1))
    logger.info(f"启动API服务 - 地址: {API_HOST}:{API_PORT}, Workers: {worker_count}")
    uvicorn.run(
        "api.main:app" if worker_count > 1 else app, 
        host=API_HOST, 
        port=API_PORT, 
        reload=False,  # 禁用自动重载避免权限问题
        workers=worker_count if worker_count > 1 else None,
        log_level="info",
        access_log=True
    )