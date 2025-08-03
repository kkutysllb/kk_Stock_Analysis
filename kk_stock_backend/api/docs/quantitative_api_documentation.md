# 量化策略API接口文档

## 概述

本文档详细描述了量化策略模块的API接口设计，包括策略选股、回测分析、信号生成、图表展示等核心功能。API基于FastAPI框架构建，提供RESTful风格的接口服务。

## 技术架构

### 核心组件
- **API Router**: `/api/v1/quantitative/*` - 量化策略核心接口
- **Chart Router**: `/api/v1/quantitative/charts/*` - 图表数据接口
- **Service Layer**: `QuantitativeService` - 业务逻辑处理
- **Chart Generator**: `ChartGenerator` - 图表数据生成

### 支持的策略
1. **太上老君1号策略** (`taishang_1`) - 多趋势共振策略
2. **太上老君2号策略** (`taishang_2`) - 好奇布偶猫BOLL策略
3. **太上老君3号策略** (`taishang_3`) - 小市值动量策略

## API接口详情

### 1. 策略管理接口

#### 1.1 获取可用策略列表
```http
GET /api/v1/quantitative/strategies
```

**响应示例:**
```json
{
  "code": 200,
  "message": "获取策略列表成功",
  "data": [
    {
      "strategy_type": "taishang_1",
      "strategy_name": "太上老君1号策略",
      "description": "多趋势共振策略，基于多时间周期技术指标共振",
      "rebalance_frequency": "每日",
      "max_positions": 8,
      "risk_level": "中等",
      "supported_features": ["选股", "回测", "信号生成", "绩效分析"]
    }
  ],
  "timestamp": "2024-01-17T10:00:00Z"
}
```

### 2. 策略选股接口

#### 2.1 执行策略选股
```http
POST /api/v1/quantitative/selection
```

**请求参数:**
```json
{
  "strategy_type": "taishang_3",
  "max_stocks": 30,
  "market_cap_range": {
    "min_market_cap": 1000000,
    "max_market_cap": 10000000
  },
  "custom_params": {
    "min_score": 0.6,
    "industry_filter": ["金融", "科技"]
  }
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "选股成功",
  "data": {
    "strategy_type": "taishang_3",
    "selection_date": "2024-01-17T10:00:00Z",
    "total_candidates": 50,
    "selected_stocks": [
      {
        "stock_info": {
          "stock_code": "000001.SZ",
          "stock_name": "平安银行",
          "industry": "金融",
          "market_cap": 2000000.0,
          "current_price": 15.20
        },
        "total_score": 0.85,
        "factor_scores": [
          {
            "factor_name": "RSI择时",
            "score": 0.8,
            "weight": 0.3,
            "normalized_score": 0.24
          }
        ],
        "ranking": 1
      }
    ],
    "selection_criteria": {},
    "next_rebalance_date": "2024-01-24"
  },
  "timestamp": "2024-01-17T10:00:00Z"
}
```

### 3. 信号生成接口

#### 3.1 生成明日交易信号
```http
POST /api/v1/quantitative/signals/next-day
```

**请求参数:**
```json
{
  "strategy_type": "taishang_3",
  "stock_pool": ["000001.SZ", "000002.SZ"],
  "current_positions": ["000001.SZ"],
  "signal_date": "2024-01-18"
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "信号生成成功",
  "data": {
    "strategy_type": "taishang_3",
    "signal_date": "2024-01-18",
    "buy_signals": [
      {
        "stock_code": "000002.SZ",
        "stock_name": "万科A",
        "signal_type": "buy",
        "signal_date": "2024-01-18",
        "signal_price": 12.50,
        "target_price": 14.00,
        "stop_loss_price": 11.75,
        "position_size": 8000,
        "confidence": 0.8,
        "reason": "3因子增强小盘策略(得分:0.850): 择时信号x0.6"
      }
    ],
    "sell_signals": [],
    "hold_signals": [
      {
        "stock_code": "000001.SZ",
        "stock_name": "平安银行",
        "signal_type": "hold",
        "signal_date": "2024-01-18",
        "signal_price": 15.20,
        "position_size": 10000,
        "confidence": 0.7,
        "reason": "持仓继续，暂无卖出信号"
      }
    ],
    "market_timing_signal": 1,
    "total_signals": 2
  },
  "timestamp": "2024-01-17T10:00:00Z"
}
```

### 4. 回测接口

#### 4.1 执行策略回测
```http
POST /api/v1/quantitative/backtest
```

**请求参数:**
```json
{
  "strategy_type": "taishang_3",
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "initial_capital": 1000000.0,
  "benchmark_codes": ["000001.SH", "000300.SH", "000905.SH"],
  "custom_params": {
    "position_size": 0.04,
    "stop_loss": 0.06,
    "take_profit": 0.15
  }
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "回测执行成功",
  "data": {
    "backtest_id": "uuid-12345",
    "strategy_type": "taishang_3",
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "initial_capital": 1000000.0,
    "final_capital": 1250000.0,
    "performance_metrics": {
      "period": "2023-01-01 - 2024-01-01",
      "total_return": 0.25,
      "annual_return": 0.25,
      "sharpe_ratio": 1.5,
      "max_drawdown": 0.15,
      "win_rate": 0.65,
      "total_trades": 50,
      "avg_holding_period": 20.0,
      "benchmark_excess_return": {
        "000300.SH": 0.10
      },
      "volatility": 0.18,
      "calmar_ratio": 1.67,
      "sortino_ratio": 2.1
    },
    "positions_over_time": [],
    "trade_records": [],
    "daily_returns": [],
    "cumulative_returns": [],
    "drawdown_series": [],
    "benchmark_comparison": {},
    "created_at": "2024-01-17T10:00:00Z"
  },
  "timestamp": "2024-01-17T10:00:00Z"
}
```

### 5. 图表数据接口

#### 5.1 获取绩效图表
```http
POST /api/v1/quantitative/charts/performance
```

**请求参数:**
```json
{
  "strategy_type": "taishang_3",
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "theme": "light",
  "responsive": true
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "获取绩效图表成功",
  "data": {
    "chart_config": {
      "title": {
        "text": "taishang_3策略绩效分析",
        "left": "center"
      },
      "tooltip": {
        "trigger": "axis",
        "axisPointer": {
          "type": "cross"
        }
      },
      "xAxis": {
        "type": "category",
        "data": ["2023-01-01", "2023-01-02", "..."]
      },
      "yAxis": {
        "type": "value",
        "name": "累计收益率",
        "axisLabel": {
          "formatter": "{value}%"
        }
      },
      "series": [
        {
          "name": "策略收益",
          "type": "line",
          "smooth": true,
          "data": [0, 0.5, 1.2, "..."],
          "itemStyle": {
            "color": "#1f77b4"
          }
        }
      ]
    },
    "chart_type": "performance",
    "data_points": 365,
    "period": "2023-01-01 - 2024-01-01"
  },
  "timestamp": "2024-01-17T10:00:00Z"
}
```

#### 5.2 获取回撤图表
```http
POST /api/v1/quantitative/charts/drawdown
```

#### 5.3 获取持仓分布图表
```http
POST /api/v1/quantitative/charts/positions
```

#### 5.4 获取交易分析图表
```http
POST /api/v1/quantitative/charts/trades
```

#### 5.5 获取风险雷达图
```http
POST /api/v1/quantitative/charts/risk-radar
```

#### 5.6 获取多策略对比图表
```http
POST /api/v1/quantitative/charts/multi-strategy-comparison
```

**请求参数:**
```json
{
  "strategy_types": ["taishang_1", "taishang_2", "taishang_3"],
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "chart_type": "performance",
  "theme": "light"
}
```

### 6. 数据查询接口

#### 6.1 获取策略绩效
```http
GET /api/v1/quantitative/performance/{strategy_type}?start_date=2023-01-01&end_date=2024-01-01
```

#### 6.2 获取当前持仓
```http
GET /api/v1/quantitative/positions/{strategy_type}
```

#### 6.3 获取历史信号
```http
POST /api/v1/quantitative/signals/historical
```

### 7. 高级功能接口

#### 7.1 策略参数优化
```http
POST /api/v1/quantitative/optimize
```

#### 7.2 策略对比分析
```http
GET /api/v1/quantitative/compare?strategy_types=taishang_1,taishang_2&start_date=2023-01-01&end_date=2024-01-01
```

#### 7.3 健康检查
```http
GET /api/v1/quantitative/health
```

## 前端集成指南

### 1. ECharts集成

所有图表接口返回的`chart_config`字段可以直接用于ECharts初始化：

```javascript
// 前端JavaScript示例
async function loadPerformanceChart(strategyType) {
  const response = await fetch('/api/v1/quantitative/charts/performance', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      strategy_type: strategyType,
      theme: 'light',
      responsive: true
    })
  });
  
  const result = await response.json();
  
  if (result.code === 200) {
    const chart = echarts.init(document.getElementById('chart-container'));
    chart.setOption(result.data.chart_config);
  }
}
```

### 2. 响应式支持

所有图表支持响应式配置，会自动适配不同屏幕尺寸：

```javascript
// 响应式图表
const chart = echarts.init(document.getElementById('chart-container'));
chart.setOption(chartConfig);

// 监听窗口大小变化
window.addEventListener('resize', () => {
  chart.resize();
});
```

### 3. 主题切换

支持明亮和暗色两种主题：

```javascript
// 切换主题
function switchTheme(theme) {
  // 重新请求图表数据
  loadChart({ theme: theme });
}
```

## 错误处理

### HTTP状态码
- `200`: 成功
- `400`: 请求参数错误
- `401`: 未授权
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器内部错误

### 错误响应格式
```json
{
  "detail": "错误描述信息"
}
```

### 常见错误
1. **策略类型不支持**: `不支持的策略类型: {strategy_type}`
2. **时间范围无效**: `开始时间不能晚于结束时间`
3. **数据不存在**: `回测结果不存在`
4. **权限不足**: `用户无权限访问该资源`

## 性能优化

### 1. 缓存策略
- 图表数据会在Redis中缓存15分钟
- 策略列表缓存1小时
- 回测结果永久缓存

### 2. 异步处理
- 长时间运行的回测任务使用后台任务处理
- 支持任务状态查询和结果获取

### 3. 分页支持
- 大数据量查询支持分页
- 默认每页20条记录，最大100条

## 安全性

### 1. 认证授权
- 所有接口需要JWT Token认证
- 用户只能访问自己的数据

### 2. 参数验证
- 使用Pydantic进行严格的参数验证
- 防止SQL注入和XSS攻击

### 3. 速率限制
- API接口实施速率限制
- 防止恶意请求和系统过载

## 监控和日志

### 1. 接口监控
- 响应时间监控
- 错误率统计
- 并发量监控

### 2. 业务日志
- 用户操作日志
- 策略执行日志
- 错误异常日志

### 3. 性能指标
- 数据库查询性能
- 缓存命中率
- 内存使用情况

## 版本更新

### v1.0.0 (2024-01-17)
- ✅ 完成核心API接口设计
- ✅ 实现三大策略支持
- ✅ 集成图表数据生成
- ✅ 添加前端响应式支持
- ✅ 完善错误处理和验证

### 未来规划
- 🔄 实时数据推送支持
- 📊 更多图表类型支持
- 🤖 策略AI优化建议
- 📱 移动端API适配

---

**量化策略API** - 专业、可靠、易用的量化交易接口服务! 🚀