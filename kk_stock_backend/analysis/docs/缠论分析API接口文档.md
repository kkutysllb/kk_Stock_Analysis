# 缠论分析API接口文档

基于道氏理论API设计模式，提供完整的缠论分析服务，支持多时间级别分析、前端渲染数据生成。

## 📋 接口概览

| 接口路径 | 方法 | 功能描述 | 分析级别 |
|---------|------|----------|----------|
| `/chan_theory/analyze` | POST | 缠论综合分析 | basic/standard/advanced/premium |
| `/chan_theory/analyze/{symbol}` | GET | 快速缠论分析 | standard |
| `/chan_theory/batch_analyze` | POST | 批量缠论分析 | basic |
| `/chan_theory/structure/{symbol}` | GET | 获取结构数据 | basic |
| `/chan_theory/signals/{symbol}` | GET | 获取交易信号 | advanced |
| `/chan_theory/quality_assessment/{symbol}` | GET | 获取质量评估 | premium |
| `/chan_theory/charts/{analysis_id}/{chart_name}` | GET | 获取分析图表 | - |
| `/chan_theory/config/default` | GET | 获取默认配置 | - |

## 🎯 核心接口详解

### 1. 缠论综合分析 `POST /chan_theory/analyze`

**功能描述**：提供完整的缠论分析功能，支持多时间级别分析、结构识别、信号生成等。

#### 请求参数

```json
{
  "symbol": "000001.SZ",                    // 股票代码（必填）
  "start_date": "2025-06-01",              // 开始日期（必填）
  "end_date": "2025-07-11",                // 结束日期（必填）
  "analysis_level": "standard",            // 分析级别
  "timeframes": ["5min", "30min", "daily"], // 分析时间级别
  "primary_timeframe": "daily",            // 主要分析级别
  
  // 结构识别参数
  "fenxing_window": 3,                     // 分型识别窗口
  "fenxing_strength": 0.001,               // 分型强度阈值
  "min_fenxing_gap": 2,                    // 分型间最小间隔
  
  // 笔段参数
  "min_bi_length": 3,                      // 笔的最小长度
  "bi_strength_threshold": 0.005,          // 笔的强度阈值
  "min_xd_bi_count": 3,                    // 线段最少包含笔数
  
  // 中枢参数
  "min_zhongshu_overlap": 0.001,           // 中枢最小重叠比例
  "zhongshu_extend_ratio": 0.05,           // 中枢扩展比例
  
  // 技术指标参数
  "bollinger_period": 20,                  // 布林带周期
  "bollinger_std": 2.0,                    // 布林带标准差
  "minute_fenxing_strength": 0.0005,       // 分钟级分型强度
  
  // 输出控制
  "include_visualization": true,            // 是否生成可视化图表
  "include_detailed_data": true,           // 是否包含详细数据
  "return_charts": false                   // 是否返回图表文件
}
```

#### 分析级别说明

| 级别 | 描述 | 包含功能 |
|------|------|----------|
| `basic` | 基础分析 | 仅结构识别（分型、笔、线段、中枢） |
| `standard` | 标准分析 | 结构识别 + 趋势分析 |
| `advanced` | 高级分析 | 结构识别 + 趋势分析 + 映射关系 |
| `premium` | 完整分析 | 全部功能 + 可视化图表 + 质量评估 |

#### 响应数据结构

```json
{
  "code": 200,
  "message": "分析完成",
  "data": {
    "analysis_id": "000001.SZ_20250713_092611",
    "symbol": "000001.SZ",
    "analysis_time": "2025-07-13T09:26:11",
    "analysis_level": "standard",
    "timeframes": ["5min", "30min", "daily"],
    "time_range": {
      "start": "2025-06-01",
      "end": "2025-07-11"
    },
    
    // 元数据信息
    "meta": {
      "symbol": "000001.SZ",
      "analysis_time": "20250713_092611",
      "version": "2.0.0",
      "data_source": "kk_stock_backend_enhanced",
      "analysis_level": "standard",
      "timeframes": ["5min", "30min", "daily"]
    },
    
    // 数据概览
    "data_summary": {
      "levels": ["5min", "30min", "daily"],
      "data_counts": {
        "5min": 1421,
        "30min": 261,
        "daily": 29
      },
      "time_range": {
        "start": "2025-06-03T00:00:00",
        "end": "2025-07-11T15:00:00"
      }
    },
    
    // 结构分析（核心数据）
    "structure_analysis": {
      "5min": {
        "level": "5min",
        "data_quality": {
          "original_count": "1421",
          "processed_count": "599",
          "has_bollinger": "True"
        },
        "fenxing_count": "94",
        "fenxing_tops": [
          {
            "index": "26",
            "timestamp": "2025-06-05T09:30:00",
            "price": 11.91,
            "fenxing_type": "top",
            "strength": 0.013521670892188834,
            "level": "5min",
            "confirmed": "True"
          }
          // ... 更多分型数据
        ],
        "fenxing_bottoms": [
          // 底分型数据结构类似
        ],
        "bi_count": "53",
        "bi_list": [
          {
            "start_time": "2025-06-05T09:30:00",
            "end_time": "2025-06-05T11:15:00",
            "start_price": 11.91,
            "end_price": 11.78,
            "direction": "down",
            "amplitude": 0.0109,
            "strength": 0.0119
          }
          // ... 更多笔数据
        ],
        "xianduan_count": "76",
        "xianduan_list": [
          // 线段数据
        ],
        "zhongshu_count": "5",
        "zhongshu_list": [
          {
            "start_time": "2025-06-05T09:30:00",
            "end_time": "2025-06-10T15:00:00",
            "high": 11.95,
            "low": 11.65,
            "center": 11.80,
            "range_ratio": 0.0254,
            "forming_xd": [
              // 构成中枢的线段
            ]
          }
          // ... 更多中枢数据
        ],
        "current_zhongshu": {
          // 当前中枢信息
        },
        "trend_analysis": {
          "current_trend": "up",
          "trend_strength": 0.65,
          "trend_duration": 15
        }
      },
      "30min": {
        // 30分钟级别结构数据
      },
      "daily": {
        // 日线级别结构数据
      }
    },
    
    // 质量评估
    "quality_assessment": {
      "overall_score": 0.69,
      "grade": "及格",
      "data_quality": 0.6,
      "structure_quality": 0.7,
      "mapping_quality": 0.15,
      "signal_quality": 0.4,
      "strengths": [
        "缠论结构完整，分型笔段识别准确"
      ],
      "weaknesses": [
        "映射关系不够清晰，需要提升分析深度"
      ],
      "recommendations": [
        "分析结果质量一般，建议谨慎对待",
        "可继续观察，等待更好的机会"
      ]
    },
    
    // 操作建议
    "operation_advice": {
      "action": "观望",
      "direction": "谨慎",
      "confidence_level": 0.5,
      "risk_level": "中等",
      "position_suggestion": "轻仓观察",
      "key_levels": {
        "support_levels": [11.65, 11.55],
        "resistance_levels": [11.95, 12.05]
      },
      "notes": ["基于缠论结构分析生成的建议，仅供参考"]
    },
    
    // 可视化配置
    "visualization_config": {
      "chart_types": ["kline", "structure", "indicators"],
      "timeframes": ["5min", "30min", "daily"],
      "indicators": ["bollinger", "ma"],
      "structure_overlays": ["fenxing", "bi", "zhongshu"],
      "color_scheme": "default"
    },
    
    // 图表链接（仅当include_visualization=true时）
    "chart_urls": [
      "/chan_theory/charts/000001.SZ_20250713_092611/multi_level_structure.png",
      "/chan_theory/charts/000001.SZ_20250713_092611/mapping_analysis.png",
      "/chan_theory/charts/000001.SZ_20250713_092611/comprehensive_assessment.png"
    ]
  },
  
  "meta": {
    "processing_time": 15.67,
    "data_points": 1711,
    "cache_key": "chan_analysis:000001.SZ:2025-06-01:2025-07-11",
    "result_file": "/path/to/result/file.json"
  }
}
```

### 2. 快速缠论分析 `GET /chan_theory/analyze/{symbol}`

**功能描述**：提供简化的缠论分析，适用于快速查看。

#### 请求示例

```
GET /chan_theory/analyze/000001.SZ?days=30&level=standard&timeframes=5min,30min,daily
```

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `symbol` | string | 是 | - | 股票代码 |
| `days` | integer | 否 | 30 | 分析天数 |
| `level` | string | 否 | standard | 分析级别 |
| `timeframes` | string | 否 | 5min,30min,daily | 时间级别，逗号分隔 |

#### 响应数据

与综合分析接口相同的数据结构，但默认不包含可视化图表。

### 3. 批量缠论分析 `POST /chan_theory/batch_analyze`

**功能描述**：支持同时分析多只股票。

#### 请求参数

```json
{
  "symbols": ["000001.SZ", "000002.SZ", "600000.SH"],
  "start_date": "2025-06-01",
  "end_date": "2025-07-11",
  "analysis_level": "basic",
  "max_concurrent": 5
}
```

#### 响应数据

```json
{
  "code": 200,
  "message": "批量分析完成，成功: 2, 失败: 1",
  "data": {
    "successful_results": [
      {
        "symbol": "000001.SZ",
        "analysis_level": "basic",
        "data_summary": {...},
        "structure_summary": {...},
        "quality_score": 0.69
      }
    ],
    "failed_symbols": [
      {
        "symbol": "000002.SZ",
        "error": "数据不足"
      }
    ],
    "summary": {
      "total_symbols": 3,
      "successful_count": 2,
      "failed_count": 1
    }
  }
}
```

### 4. 获取结构数据 `GET /chan_theory/structure/{symbol}`

**功能描述**：获取特定时间级别的缠论结构数据。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `start_date` | string | 是 | - | 开始日期 YYYY-MM-DD |
| `end_date` | string | 是 | - | 结束日期 YYYY-MM-DD |
| `timeframe` | string | 否 | daily | 时间级别：5min\|30min\|daily |
| `structure_type` | string | 否 | all | 结构类型：fenxing\|bi\|xianduan\|zhongshu\|all |

#### 请求示例

```
GET /chan_theory/structure/000001.SZ?start_date=2025-06-01&end_date=2025-07-11&timeframe=5min&structure_type=fenxing
```

#### 响应数据

```json
{
  "code": 200,
  "message": "结构数据获取成功",
  "data": {
    "fenxing_tops": [
      {
        "index": "26",
        "timestamp": "2025-06-05T09:30:00",
        "price": 11.91,
        "fenxing_type": "top",
        "strength": 0.0135,
        "level": "5min",
        "confirmed": "True"
      }
    ],
    "fenxing_bottoms": [
      // 底分型数据
    ],
    "count": 94
  }
}
```

### 5. 获取交易信号 `GET /chan_theory/signals/{symbol}`

**功能描述**：获取缠论交易信号，包括买卖点信号、背离信号等。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `start_date` | string | 是 | - | 开始日期 |
| `end_date` | string | 是 | - | 结束日期 |
| `signal_type` | string | 否 | all | 信号类型：buy\|sell\|all |
| `min_strength` | float | 否 | 0.3 | 最小信号强度 |

#### 响应数据

```json
{
  "code": 200,
  "message": "交易信号获取成功",
  "data": {
    "signals": [
      {
        "type": "buy_1",
        "timeframe": "daily",
        "timestamp": "2025-06-15T09:30:00",
        "price": 11.85,
        "strength": 0.75,
        "confidence": 0.68,
        "description": "日线级别一类买点",
        "supporting_levels": ["5min", "30min"]
      }
    ],
    "summary": {
      "total_signals": 3,
      "buy_signals": 2,
      "sell_signals": 1,
      "avg_strength": 0.65
    }
  }
}
```

### 6. 获取质量评估 `GET /chan_theory/quality_assessment/{symbol}`

**功能描述**：获取缠论分析的质量评估，包括各维度评分。

#### 响应数据

```json
{
  "code": 200,
  "message": "质量评估获取成功",
  "data": {
    "overall_score": 0.69,
    "grade": "及格",
    "data_quality": {
      "score": 0.6,
      "description": "数据覆盖较好，质量可接受"
    },
    "structure_quality": {
      "score": 0.7,
      "fenxing_score": 0.8,
      "bi_score": 0.7,
      "zhongshu_score": 0.6,
      "description": "结构识别准确，完整性良好"
    },
    "mapping_quality": {
      "score": 0.15,
      "adjusted_score": 0.4,
      "description": "映射关系识别有待提高"
    },
    "signal_quality": {
      "score": 0.4,
      "description": "信号生成基础有效，强度中等"
    },
    "strengths": [
      "缠论结构完整，分型笔段识别准确"
    ],
    "weaknesses": [
      "映射关系不够清晰，需要提升分析深度"
    ],
    "recommendations": [
      "分析结果质量一般，建议谨慎对待",
      "可继续观察，等待更好的机会"
    ]
  }
}
```

## 🛠️ 前端集成指南

### JavaScript/TypeScript 示例

```javascript
// 1. 缠论综合分析
async function analyzeChanTheory(symbol, startDate, endDate, options = {}) {
  const requestBody = {
    symbol,
    start_date: startDate,
    end_date: endDate,
    analysis_level: options.level || 'standard',
    timeframes: options.timeframes || ['5min', '30min', 'daily'],
    include_visualization: options.includeCharts || false,
    ...options.params
  };
  
  try {
    const response = await fetch('/chan_theory/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(requestBody)
    });
    
    const result = await response.json();
    
    if (result.code === 200) {
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('缠论分析失败:', error);
    throw error;
  }
}

// 2. 快速分析
async function quickAnalyze(symbol, days = 30) {
  const response = await fetch(
    `/chan_theory/analyze/${symbol}?days=${days}&level=standard`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  
  return await response.json();
}

// 3. 获取结构数据
async function getStructureData(symbol, startDate, endDate, timeframe = '5min') {
  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
    timeframe,
    structure_type: 'all'
  });
  
  const response = await fetch(
    `/chan_theory/structure/${symbol}?${params}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  
  return await response.json();
}

// 4. 使用示例
async function example() {
  try {
    // 综合分析
    const analysis = await analyzeChanTheory(
      '000001.SZ',
      '2025-06-01',
      '2025-07-11',
      {
        level: 'premium',
        includeCharts: true,
        params: {
          fenxing_strength: 0.001,
          min_bi_length: 3
        }
      }
    );
    
    console.log('分析结果:', analysis);
    console.log('综合评分:', analysis.quality_assessment.overall_score);
    console.log('操作建议:', analysis.operation_advice.action);
    
    // 渲染K线图和结构
    renderKlineChart(analysis.structure_analysis);
    
    // 显示买卖点
    if (analysis.signal_analysis) {
      displayTradingSignals(analysis.signal_analysis.buy_signals);
    }
    
  } catch (error) {
    console.error('分析失败:', error);
  }
}
```

### React组件示例

```jsx
import React, { useState, useEffect } from 'react';

const ChanTheoryAnalysis = ({ symbol }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState({
    start: '2025-06-01',
    end: '2025-07-11'
  });

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const result = await analyzeChanTheory(
        symbol,
        dateRange.start,
        dateRange.end,
        {
          level: 'standard',
          timeframes: ['5min', '30min', 'daily']
        }
      );
      setAnalysis(result);
    } catch (error) {
      console.error('分析失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chan-theory-analysis">
      <div className="controls">
        <input
          type="date"
          value={dateRange.start}
          onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
        />
        <input
          type="date"
          value={dateRange.end}
          onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
        />
        <button onClick={handleAnalyze} disabled={loading}>
          {loading ? '分析中...' : '开始分析'}
        </button>
      </div>

      {analysis && (
        <div className="analysis-results">
          {/* 质量评估 */}
          <div className="quality-assessment">
            <h3>质量评估</h3>
            <div className="score">
              综合评分: {(analysis.quality_assessment.overall_score * 100).toFixed(1)}%
            </div>
            <div className="grade">
              等级: {analysis.quality_assessment.grade}
            </div>
          </div>

          {/* 结构统计 */}
          <div className="structure-summary">
            <h3>结构统计</h3>
            {Object.entries(analysis.structure_analysis).map(([level, data]) => (
              <div key={level} className="level-summary">
                <h4>{level}级别</h4>
                <p>分型: {data.fenxing_count}个</p>
                <p>笔: {data.bi_count}条</p>
                <p>中枢: {data.zhongshu_count}个</p>
              </div>
            ))}
          </div>

          {/* 操作建议 */}
          <div className="operation-advice">
            <h3>操作建议</h3>
            <p>建议操作: {analysis.operation_advice.action}</p>
            <p>风险等级: {analysis.operation_advice.risk_level}</p>
            <p>仓位建议: {analysis.operation_advice.position_suggestion}</p>
          </div>

          {/* 可视化图表 */}
          {analysis.chart_urls && (
            <div className="charts">
              <h3>分析图表</h3>
              {analysis.chart_urls.map((url, index) => (
                <img key={index} src={url} alt={`分析图表${index + 1}`} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ChanTheoryAnalysis;
```

## 🔧 配置说明

### 获取默认配置

```javascript
// 获取默认配置
const config = await fetch('/chan_theory/config/default');
const defaultConfig = await config.json();

console.log('默认参数:', defaultConfig.data.default_params);
console.log('支持的分析级别:', defaultConfig.data.analysis_levels);
console.log('支持的时间级别:', defaultConfig.data.timeframes);
```

### 参数调优建议

| 参数 | 用途 | 建议值范围 | 说明 |
|------|------|------------|------|
| `fenxing_strength` | 分型强度阈值 | 0.0005-0.005 | 值越小识别越多分型 |
| `min_bi_length` | 笔最小长度 | 3-8 | 值越大笔越少但质量越高 |
| `min_zhongshu_overlap` | 中枢重叠比例 | 0.001-0.01 | 值越小识别越多中枢 |
| `bollinger_period` | 布林带周期 | 10-30 | 标准设置为20 |

## ⚠️ 注意事项

1. **时间范围限制**：单次分析期间不能超过1年，不能少于7天
2. **并发限制**：批量分析最大并发数不超过10
3. **缓存机制**：分析结果会缓存30分钟-1小时
4. **数据延迟**：分钟级数据可能有5-15分钟延迟
5. **风险提示**：分析结果仅供参考，投资需谨慎

## 🚀 性能优化

1. **使用缓存**：相同参数的重复请求会使用缓存结果
2. **分级分析**：根据需求选择合适的分析级别
3. **时间级别选择**：只选择必要的时间级别进行分析
4. **批量处理**：多股票分析使用批量接口
5. **异步处理**：前端使用异步方式调用API

## 📞 技术支持

如有问题请联系技术支持或查看相关文档：
- API文档：`/docs`
- 系统状态：`/health`
- 性能指标：`/metrics`