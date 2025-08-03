<template>
  <div class="risk-analysis">
    <el-row :gutter="24">
      <!-- 回撤分析图 -->
      <el-col :span="24" class="chart-section">
        <el-card class="chart-card">
          <template #header>
            <h3>回撤分析</h3>
          </template>
          <div ref="drawdownChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="24" style="margin-top: 24px">
      <!-- 风险指标雷达图 -->
      <el-col :span="12" class="chart-section">
        <el-card class="chart-card">
          <template #header>
            <h3>风险指标雷达图</h3>
          </template>
          <div ref="riskRadarRef" class="chart-container-small"></div>
        </el-card>
      </el-col>

      <!-- VaR分析 -->
      <el-col :span="12" class="chart-section">
        <el-card class="chart-card">
          <template #header>
            <h3>风险价值(VaR)分析</h3>
          </template>
          <div ref="varAnalysisRef" class="chart-container-small"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 风险指标详情表格 -->
    <el-row :gutter="24" style="margin-top: 24px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <h3>风险指标详情</h3>
          </template>
          
          <el-row :gutter="24">
            <el-col :span="8">
              <div class="risk-metric-card">
                <h4>收益风险指标</h4>
                <div class="metric-list">
                  <div class="metric-item">
                    <span class="metric-label">夏普比率</span>
                    <span class="metric-value" :class="getSharpeClass(performanceData?.basic_metrics?.sharpe_ratio)">
                      {{ performanceData?.basic_metrics?.sharpe_ratio?.toFixed(3) || '-' }}
                    </span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">索提诺比率</span>
                    <span class="metric-value" :class="getSortinoClass(performanceData?.advanced_metrics?.sortino_ratio)">
                      {{ performanceData?.advanced_metrics?.sortino_ratio?.toFixed(3) || '-' }}
                    </span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">卡尔玛比率</span>
                    <span class="metric-value" :class="getCalmarClass(performanceData?.basic_metrics?.calmar_ratio)">
                      {{ performanceData?.basic_metrics?.calmar_ratio?.toFixed(3) || '-' }}
                    </span>
                  </div>
                </div>
              </div>
            </el-col>
            
            <el-col :span="8">
              <div class="risk-metric-card">
                <h4>回撤风险指标</h4>
                <div class="metric-list">
                  <div class="metric-item">
                    <span class="metric-label">最大回撤</span>
                    <span class="metric-value loss">
                      {{ (Math.abs(performanceData?.basic_metrics?.max_drawdown || 0) * 100).toFixed(2) }}%
                    </span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">最大连续亏损</span>
                    <span class="metric-value">
                      {{ performanceData?.advanced_metrics?.max_consecutive_losses || '-' }}次
                    </span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">年化波动率</span>
                    <span class="metric-value">
                      {{ (performanceData?.basic_metrics?.volatility * 100)?.toFixed(2) || '-' }}%
                    </span>
                  </div>
                </div>
              </div>
            </el-col>
            
            <el-col :span="8">
              <div class="risk-metric-card">
                <h4>极值风险指标</h4>
                <div class="metric-list">
                  <div class="metric-item">
                    <span class="metric-label">VaR(5%)</span>
                    <span class="metric-value loss">
                      {{ (Math.abs(performanceData?.advanced_metrics?.var_5 || 0) * 100).toFixed(3) }}%
                    </span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">CVaR(5%)</span>
                    <span class="metric-value loss">
                      {{ (Math.abs(performanceData?.advanced_metrics?.cvar_5 || 0) * 100).toFixed(3) }}%
                    </span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">胜率</span>
                    <span class="metric-value" :class="getWinRateClass(calculateTradeWinRate())">
                      {{ (calculateTradeWinRate() * 100).toFixed(1) }}%
                    </span>
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElRow, ElCol, ElCard } from 'element-plus'
import * as echarts from 'echarts'

interface DrawdownData {
  title: string
  type: string
  data: {
    dates: string[]
    portfolio_values: number[]
    peak_values: number[]
    drawdown: number[]
  }
}

interface PerformanceData {
  basic_metrics: {
    sharpe_ratio: number
    max_drawdown: number
    calmar_ratio: number
    volatility: number
  }
  advanced_metrics: {
    sortino_ratio: number
    var_5: number
    cvar_5: number
    max_consecutive_losses: number
    winning_days_ratio: number
  }
}

interface TradesData {
  trades: any[]
  summary: any
  tradeMetrics: any
}

interface Props {
  drawdownData: DrawdownData | null
  performanceData: PerformanceData | null
  tradesData: TradesData | null
}

const props = defineProps<Props>()

const drawdownChartRef = ref<HTMLElement>()
const riskRadarRef = ref<HTMLElement>()
const varAnalysisRef = ref<HTMLElement>()

let drawdownChart: echarts.ECharts | null = null
let riskRadarChart: echarts.ECharts | null = null
let varAnalysisChart: echarts.ECharts | null = null

// 动态获取主题颜色
const getThemeColors = () => {
  const isDark = document.documentElement.classList.contains('dark')
  return {
    textPrimary: isDark ? '#ffffff' : '#0f172a',
    textSecondary: isDark ? '#b4b4b4' : '#475569'
  }
}

const getSharpeClass = (value?: number) => {
  if (!value) return ''
  if (value > 1.5) return 'excellent'
  if (value > 1.0) return 'good'
  if (value > 0.5) return 'fair'
  return 'poor'
}

const getSortinoClass = (value?: number) => {
  if (!value) return ''
  if (value > 2.0) return 'excellent'
  if (value > 1.5) return 'good'
  if (value > 1.0) return 'fair'
  return 'poor'
}

const getCalmarClass = (value?: number) => {
  if (!value) return ''
  if (value > 3.0) return 'excellent'
  if (value > 2.0) return 'good'
  if (value > 1.0) return 'fair'
  return 'poor'
}

const getWinRateClass = (value?: number) => {
  if (!value) return ''
  const rate = value * 100
  if (rate > 60) return 'excellent'
  if (rate > 50) return 'good'
  if (rate > 40) return 'fair'
  return 'poor'
}

// 计算交易胜率的函数
const calculateTradeWinRate = () => {
  if (!props.tradesData?.trades) return props.performanceData?.advanced_metrics?.winning_days_ratio || 0
  
  const trades = props.tradesData.trades
  const stockPositions = new Map()
  let profitTrades = 0
  let totalSellTrades = 0
  
  // 按时间正序排序进行计算
  const sortedTrades = trades.sort((a, b) => {
    const dateA = new Date(a.date || a.trade_date || '')
    const dateB = new Date(b.date || b.trade_date || '')
    return dateA.getTime() - dateB.getTime()
  })
  
  sortedTrades.forEach(trade => {
    const symbol = trade.symbol || trade.stock_code || ''
    const action = trade.action || trade.order_type || ''
    const shares = trade.shares || trade.quantity || 0
    const price = trade.price || 0
    const commission = trade.commission || 0
    const stampTax = trade.stamp_tax || 0
    
    if (!stockPositions.has(symbol)) {
      stockPositions.set(symbol, { totalShares: 0, totalCost: 0 })
    }
    
    const position = stockPositions.get(symbol)
    
    if (action === 'buy') {
      // 买入：累加成本
      const totalCost = shares * price + commission
      position.totalShares += shares
      position.totalCost += totalCost
    } else if (action === 'sell' && position.totalShares > 0) {
      // 卖出：计算盈亏
      const avgCost = position.totalCost / position.totalShares
      const sellRevenue = shares * price - commission - stampTax
      const sellCost = shares * avgCost
      const pnl = sellRevenue - sellCost
      
      totalSellTrades++
      if (pnl > 0) {
        profitTrades++
      }
      
      // 更新持仓
      position.totalShares -= shares
      position.totalCost -= sellCost
      
      // 如果全部卖出，重置成本
      if (position.totalShares <= 0) {
        position.totalShares = 0
        position.totalCost = 0
      }
    }
  })
  
  return totalSellTrades > 0 ? profitTrades / totalSellTrades : 0
}

const initDrawdownChart = () => {
  if (!drawdownChartRef.value || !props.drawdownData?.data) return

  // 检查DOM尺寸
  const rect = drawdownChartRef.value.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    setTimeout(() => initDrawdownChart(), 100)
    return
  }

  drawdownChart = echarts.init(drawdownChartRef.value)
  const themeColors = getThemeColors()
  
  const data = props.drawdownData.data

  const option = {
    title: {
      left: 'center',
      textStyle: {
        color: themeColors.textPrimary,
        fontSize: 16
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any) => {
        const date = params[0].axisValue
        let result = `日期: ${date}<br/>`
        params.forEach((param: any) => {
          if (param.seriesName === '回撤') {
            result += `${param.marker}${param.seriesName}: ${param.value.toFixed(2)}%<br/>`
          } else {
            result += `${param.marker}${param.seriesName}: ¥${(param.value / 10000).toFixed(2)}万<br/>`
          }
        })
        return result
      }
    },
    legend: {
      top: 30,
      textStyle: {
        color: themeColors.textPrimary
      }
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '10%',
      top: 80,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.dates,
      axisLabel: {
        color: themeColors.textSecondary
      },
      splitLine: {
        show: false
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '组合价值',
        position: 'left',
        nameTextStyle: {
          color: themeColors.textPrimary
        },
        axisLabel: {
          color: themeColors.textSecondary,
          formatter: (value: number) => `¥${(value / 10000).toFixed(0)}万`
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: themeColors.textSecondary,
            opacity: 0.1,
            type: 'dashed'
          }
        }
      },
      {
        type: 'value',
        name: '回撤(%)',
        position: 'right',
        nameTextStyle: {
          color: themeColors.textPrimary
        },
        axisLabel: {
          color: themeColors.textSecondary,
          formatter: '{value}%'
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: [
      {
        name: '组合价值',
        type: 'line',
        yAxisIndex: 0,
        data: data.portfolio_values,
        lineStyle: {
          color: '#5470c6',
          width: 2
        }
      },
      {
        name: '历史最高',
        type: 'line',
        yAxisIndex: 0,
        data: data.peak_values,
        lineStyle: {
          color: '#91cc75',
          width: 1,
          type: 'dashed'
        }
      },
      {
        name: '回撤',
        type: 'line',
        yAxisIndex: 1,
        data: data.drawdown,
        lineStyle: {
          color: '#ee6666',
          width: 2
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(238, 102, 102, 0.3)' },
            { offset: 1, color: 'rgba(238, 102, 102, 0.1)' }
          ])
        }
      }
    ]
  }

  drawdownChart.setOption(option)
}

const initRiskRadarChart = () => {
  if (!riskRadarRef.value || !props.performanceData) return

  // 检查DOM尺寸
  const rect = riskRadarRef.value.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    setTimeout(() => initRiskRadarChart(), 100)
    return
  }

  riskRadarChart = echarts.init(riskRadarRef.value)
  const themeColors = getThemeColors()
  
  const metrics = props.performanceData
  
  // 标准化指标值（0-100分）
  const normalizeScore = (value: number, type: 'ratio' | 'percent' | 'inverse' | 'volatility' | 'drawdown') => {
    switch (type) {
      case 'ratio':
        return Math.min(100, Math.max(0, value * 50)) // 比率类指标
      case 'percent':
        return Math.min(100, Math.max(0, value * 100)) // 百分比类指标
      case 'volatility':
        // 波动率：将0-50%映射到100-0分（波动率越低越好）
        const volPercent = Math.abs(value) * 100 // 转换为百分比
        return Math.min(100, Math.max(0, 100 - volPercent * 2)) 
      case 'drawdown':
        // 回撤：将0-50%映射到100-0分（回撤越小越好）
        const ddPercent = Math.abs(value) * 100 // 转换为百分比
        return Math.min(100, Math.max(0, 100 - ddPercent * 2))
      case 'inverse':
        return Math.min(100, Math.max(0, 100 - Math.abs(value) * 1000)) // 负面指标反转
      default:
        return 0
    }
  }

  // 计算实际交易胜率
  const tradeWinRate = calculateTradeWinRate()
  
  const radarData = [
    { name: '夏普比率', value: normalizeScore(metrics.basic_metrics.sharpe_ratio, 'ratio') },
    { name: '索提诺比率', value: normalizeScore(metrics.advanced_metrics.sortino_ratio, 'ratio') },
    { name: '卡尔玛比率', value: normalizeScore(metrics.basic_metrics.calmar_ratio, 'ratio') },
    { name: '最大回撤', value: normalizeScore(metrics.basic_metrics.max_drawdown, 'drawdown') },
    { name: '波动率', value: normalizeScore(metrics.basic_metrics.volatility, 'volatility') },
    { name: '胜率', value: normalizeScore(tradeWinRate, 'percent') }
  ]

  const option = {
    radar: {
      indicator: radarData.map(item => ({
        name: item.name,
        max: 100
      })),
      center: ['50%', '55%'],
      radius: '70%',
      axisNameGap: 8,
      axisName: {
        color: themeColors.textPrimary
      }
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: radarData.map(item => item.value),
            name: '风险指标',
            itemStyle: {
              color: '#5470c6'
            },
            areaStyle: {
              color: new echarts.graphic.RadialGradient(0.1, 0.6, 1, [
                { color: 'rgba(84, 112, 198, 0.3)', offset: 0 },
                { color: 'rgba(84, 112, 198, 0.1)', offset: 1 }
              ])
            }
          }
        ]
      }
    ]
  }

  riskRadarChart.setOption(option)
}

const initVarAnalysisChart = () => {
  if (!varAnalysisRef.value || !props.performanceData) return

  // 检查DOM尺寸
  const rect = varAnalysisRef.value.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    setTimeout(() => initVarAnalysisChart(), 100)
    return
  }

  varAnalysisChart = echarts.init(varAnalysisRef.value)
  const themeColors = getThemeColors()
  
  const metrics = props.performanceData.advanced_metrics
  
  // 模拟不同置信水平的VaR数据
  const confidenceLevels = ['99%', '95%', '90%', '85%', '80%']
  const varValues = [
    Math.abs(metrics.var_5) * 2.5,
    Math.abs(metrics.var_5),
    Math.abs(metrics.var_5) * 0.8,
    Math.abs(metrics.var_5) * 0.6,
    Math.abs(metrics.var_5) * 0.4
  ]

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const value = params[0].value
        return `${params[0].axisValue}置信水平<br/>VaR: ${(value * 100).toFixed(3)}%`
      }
    },
    grid: {
      left: '15%',
      right: '5%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: confidenceLevels,
      axisLabel: {
        color: themeColors.textSecondary
      },
      splitLine: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      name: 'VaR值',
      nameTextStyle: {
        color: themeColors.textPrimary
      },
      axisLabel: {
        color: themeColors.textSecondary,
        formatter: (value: number) => `${(value * 100).toFixed(2)}%`
      },
      splitLine: {
        show: true,
        lineStyle: {
          color: themeColors.textSecondary,
          opacity: 0.1,
          type: 'dashed'
        }
      }
    },
    series: [
      {
        type: 'bar',
        data: varValues.map(value => ({
          value: value,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#ff7875' },
              { offset: 1, color: '#f56c6c' }
            ])
          }
        })),
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#ff4d4f' },
              { offset: 1, color: '#cf1322' }
            ])
          }
        }
      }
    ]
  }

  varAnalysisChart.setOption(option)
}

const resizeCharts = () => {
  drawdownChart?.resize()
  riskRadarChart?.resize()
  varAnalysisChart?.resize()
}

onMounted(() => {
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class']
  })
  
  nextTick(() => {
    initDrawdownChart()
    initRiskRadarChart()
    initVarAnalysisChart()
  })
  
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  themeObserver.disconnect()
  drawdownChart?.dispose()
  riskRadarChart?.dispose()
  varAnalysisChart?.dispose()
  window.removeEventListener('resize', resizeCharts)
})

watch(() => [props.drawdownData, props.performanceData], () => {
  nextTick(() => {
    initDrawdownChart()
    initRiskRadarChart()
    initVarAnalysisChart()
  })
}, { deep: true })

// 监听主题变化
const themeObserver = new MutationObserver((mutations) => {
  mutations.forEach(mutation => {
    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
      const isDark = document.documentElement.classList.contains('dark')
      console.log('⚠️ 风险分析主题切换:', isDark ? '暗色模式' : '浅色模式')
      
      setTimeout(() => {
        initDrawdownChart()
        initRiskRadarChart()
        initVarAnalysisChart()
      }, 150)
    }
  })
})
</script>

<style scoped>
.risk-analysis {
  width: 100%;
}

.chart-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-card :deep(.el-card__header) {
  background: var(--el-bg-color-page);
  border-bottom: 1px solid var(--el-border-color-lighter);
  padding: 16px 20px;
}

.chart-card h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.chart-container {
  width: 100%;
  height: 450px;
  padding: 10px;
}

.chart-container-small {
  width: 100%;
  height: 350px;
  padding: 10px;
}

.risk-metric-card {
  background: var(--el-bg-color-page);
  border-radius: 8px;
  padding: 20px;
  height: 100%;
  border: 1px solid var(--el-border-color-lighter);
}

.risk-metric-card h4 {
  margin: 0 0 16px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  border-bottom: 2px solid var(--el-color-primary);
  padding-bottom: 8px;
}

.metric-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.metric-value.excellent {
  color: var(--el-color-success);
}

.metric-value.good {
  color: #67c23a;
}

.metric-value.fair {
  color: var(--el-color-warning);
}

.metric-value.poor {
  color: var(--el-color-danger);
}

.metric-value.loss {
  color: var(--el-color-danger);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chart-container {
    height: 300px;
  }
  
  .chart-container-small {
    height: 250px;
  }
  
  .risk-metric-card {
    padding: 16px;
  }
  
  .metric-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>