<template>
  <div class="sentiment-indicator">
    <el-card class="indicator-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <h3>
              <el-icon class="panel-icon"><TrendCharts /></el-icon>
              市场情绪指标
            </h3>
            <AskAIComponent :data-context="aiDataContext" />
          </div>
          <div class="header-controls">
            <el-select v-model="timeRange" placeholder="时间范围" size="small" style="width: 120px;">
              <el-option label="近7天" value="7d" />
              <el-option label="近30天" value="30d" />
              <el-option label="近90天" value="90d" />
            </el-select>
            <el-button @click="fetchSentimentData" :loading="loading" size="small" type="primary">
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <div class="indicator-content" v-loading="loading">
        <!-- 情绪指标网格 -->
        <div class="indicators-grid">
          <div class="indicator-item" v-for="indicator in sentimentData" :key="indicator.name">
            <div class="indicator-header">
              <span class="indicator-name">
                <el-icon class="indicator-icon"><TrendCharts /></el-icon>
                {{ indicator.name }}
              </span>
              <el-tooltip :content="indicator.description" placement="top">
                <el-icon class="info-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
            <div class="indicator-value">
              <span class="current-value" :class="getValueClass(indicator.level)">
                {{ indicator.value }}{{ indicator.unit }}
              </span>
              <span class="change-value" :class="indicator.change >= 0 ? 'positive' : 'negative'">
                {{ indicator.change >= 0 ? '+' : '' }}{{ indicator.change }}{{ indicator.unit }}
              </span>
            </div>
            <div class="indicator-level">
              <el-tag :type="getLevelType(indicator.level)" size="small">
                {{ getLevelText(indicator.level) }}
              </el-tag>
            </div>
            <div class="indicator-chart">
              <div :ref="(el: HTMLElement | null) => setChartRef(indicator.name, el)" :data-chart="indicator.name" class="mini-chart"></div>
            </div>
          </div>
        </div>

        <!-- 综合情绪指数 -->
        <div class="sentiment-summary">
          <div class="summary-gauge">
            <h4>
              <el-icon class="gauge-icon"><TrendCharts /></el-icon>
              综合情绪指数
            </h4>
            <div ref="gaugeChart" class="gauge-chart"></div>
          </div>
          <div class="summary-info">
            <div class="summary-card">
              <div class="summary-title">综合情绪指数</div>
              <div class="summary-value" :class="getIndexClass(overallSentiment.index)">
                {{ overallSentiment.index }}
              </div>
              <div class="summary-level">{{ overallSentiment.level }}</div>
            </div>
            <div class="summary-factors">
              <div class="factors-header">
                <h5>主要因素</h5>
              </div>
              <div class="factors-list">
                <div 
                  v-for="(factor, index) in overallSentiment.factors" 
                  :key="factor"
                  class="factor-item"
                  :class="`factor-${index % 3}`"
                >
                  <div class="factor-dot"></div>
                  <span class="factor-text">{{ factor }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { InfoFilled, TrendCharts } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useAppStore } from '../stores/app'
import { apiClient } from '../api/base'
import { ElMessage } from 'element-plus'
import AskAIComponent from './AskAIComponent.vue'

// Props
interface Props {
  symbols?: string[]
  date?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  symbols: () => ['IF', 'IC', 'IH', 'IM'],
  date: '',
  loading: false
})

// 应用状态
const appStore = useAppStore()

// 主题相关颜色
const isDarkMode = computed(() => appStore.isDarkMode)
const textColor = computed(() => isDarkMode.value ? '#E5EAF3' : '#606266')
const borderColor = computed(() => isDarkMode.value ? 'rgba(255, 255, 255, 0.1)' : 'rgba(15, 23, 42, 0.1)')
const backgroundColor = computed(() => isDarkMode.value ? '#1d1e1f' : '#ffffff')

// 响应式数据
const timeRange = ref('30d')
const loading = ref(false)

// 图表引用
const gaugeChart = ref<HTMLElement | null>(null)
let gaugeChartInstance: echarts.ECharts | null = null
const miniChartInstances: Record<string, echarts.ECharts> = {}

// 设置图表引用
const setChartRef = (name: string, el: HTMLElement | null) => {
  if (el && !miniChartInstances[name]) {
    nextTick(() => {
      initMiniChart(name, el as HTMLElement)
    })
  }
}

// 情绪数据 - 使用真实API数据
const sentimentData = ref([
  {
    name: '多空比',
    value: 0,
    unit: '',
    change: 0,
    level: 'neutral',
    description: '多头持仓与空头持仓的比值，反映市场多空力量对比',
    data: [] as Array<[string, number]>
  },
  {
    name: '恐慌指数',
    value: 50,
    unit: '',
    change: 0,
    level: 'neutral',
    description: '基于期权波动率计算的恐慌指数，数值越高表示市场恐慌程度越高',
    data: [] as Array<[string, number]>
  },
  {
    name: '资金流向',
    value: 0,
    unit: '亿',
    change: 0,
    level: 'neutral',
    description: '主力资金净流入流出情况，正值表示净流入',
    data: [] as Array<[string, number]>
  },
  {
    name: '基差水平',
    value: 0,
    unit: '点',
    change: 0,
    level: 'neutral',
    description: '期货价格与现货价格的差值，反映市场预期',
    data: [] as Array<[string, number]>
  }
])

// 综合情绪指数
const overallSentiment = ref({
  index: 50,
  level: '中性',
  factors: [
    '暂无数据'
  ]
})

// AI数据上下文
const aiDataContext = computed(() => {
  // console.log('AI数据上下文计算中，当前数据:', {
  //   sentimentData: sentimentData.value,
  //   overallSentiment: overallSentiment.value,
  //   timeRange: timeRange.value
  // })
  
  // 计算历史数据统计信息
  const getHistoricalStats = (data: Array<[string, number]>) => {
    if (!data || data.length === 0) return null
    
    const values = data.map((item: [string, number]) => item[1])
    const sorted = [...values].sort((a, b) => a - b)
    
    return {
      count: values.length,
      min: Math.min(...values),
      max: Math.max(...values),
      avg: values.reduce((sum, val) => sum + val, 0) / values.length,
      median: sorted[Math.floor(sorted.length / 2)],
      trend: values.length > 1 ? (values[values.length - 1] - values[0]) / values[0] * 100 : 0,
      volatility: Math.sqrt(values.reduce((sum, val) => sum + Math.pow(val - values.reduce((s, v) => s + v, 0) / values.length, 2), 0) / values.length)
    }
  }

  return {
    type: 'market_sentiment',
    title: '市场情绪分析',
    data: {
      timeRange: timeRange.value,
      overallSentiment: overallSentiment.value,
      indicators: sentimentData.value.map((indicator: any) => {
        const stats = getHistoricalStats(indicator.data)
        return {
          name: indicator.name,
          value: indicator.value,
          unit: indicator.unit,
          change: indicator.change,
          level: indicator.level,
          description: indicator.description,
          historicalData: indicator.data || [],
          statistics: stats,
          dataPoints: indicator.data?.length || 0
        }
      }),
      summary: {
        bullishCount: sentimentData.value.filter((item: any) => item.level === 'bullish').length,
        bearishCount: sentimentData.value.filter((item: any) => item.level === 'bearish').length,
        neutralCount: sentimentData.value.filter((item: any) => item.level === 'neutral').length,
        totalDataPoints: sentimentData.value.reduce((sum: number, item: any) => sum + (item.data?.length || 0), 0)
      }
    },
    summary: `市场情绪分析完整数据（${timeRange.value}）：

## 综合情绪指数
- 当前指数：${overallSentiment.value.index}（${overallSentiment.value.level}）
- 主要因素：${overallSentiment.value.factors.join('，')}

## 各项指标详情
${sentimentData.value.map((indicator: any) => {
  const stats = getHistoricalStats(indicator.data)
  const trendText = stats ? (stats.trend > 0 ? '上升' : stats.trend < 0 ? '下降' : '平稳') : '无数据'
  const levelText = indicator.level === 'bullish' ? '看涨' : indicator.level === 'bearish' ? '看跌' : '中性'
  
  return `### ${indicator.name}
- 当前值：${indicator.value}${indicator.unit}
- 变化量：${indicator.change >= 0 ? '+' : ''}${indicator.change}${indicator.unit}
- 趋势判断：${levelText}
- 历史数据点：${indicator.data?.length || 0}个
${stats ? `- 历史统计：
  * 最高值：${stats.max.toFixed(2)}${indicator.unit}
  * 最低值：${stats.min.toFixed(2)}${indicator.unit}
  * 平均值：${stats.avg.toFixed(2)}${indicator.unit}
  * 整体趋势：${trendText}（${stats.trend.toFixed(2)}%）
  * 波动率：${stats.volatility.toFixed(2)}` : '- 暂无历史统计数据'}
- 指标说明：${indicator.description}`
}).join('\n\n')}

## 历史数据时间序列
${sentimentData.value.map((indicator: any) => {
  if (!indicator.data || indicator.data.length === 0) return `${indicator.name}：无历史数据`
  
  const recentData = indicator.data.slice(-10) // 最近10个数据点
  return `${indicator.name}（最近${recentData.length}个数据点）：
${recentData.map(([date, value]: [string, number]) => `  ${date}: ${value}${indicator.unit}`).join('\n')}`
}).join('\n\n')}

## 市场情绪汇总
- 看涨指标：${sentimentData.value.filter((item: any) => item.level === 'bullish').length}个
- 看跌指标：${sentimentData.value.filter((item: any) => item.level === 'bearish').length}个  
- 中性指标：${sentimentData.value.filter((item: any) => item.level === 'neutral').length}个
- 总数据点：${sentimentData.value.reduce((sum: number, item: any) => sum + (item.data?.length || 0), 0)}个

请基于以上完整的市场情绪数据（包括历史数据和统计信息）进行深入分析，提供投资建议和风险提示。`
  }
})

// 获取市场情绪数据
const fetchSentimentData = async () => {
  loading.value = true
  try {
    const days = timeRange.value === '7d' ? 7 : timeRange.value === '30d' ? 30 : 90
    
    // 调用新的市场情绪汇总API
    const sentimentResponse = await apiClient.get('/sentiment/dashboard-summary', {
      params: { days: days }
    })
    
    if (sentimentResponse.success && sentimentResponse.data) {
      const data = sentimentResponse.data
      // console.log('市场情绪数据获取成功:', data)
      
      // 更新综合情绪指数
      if (data.overall_sentiment) {
        overallSentiment.value = {
          index: data.overall_sentiment.index,
          level: data.overall_sentiment.level,
          factors: data.overall_sentiment.factors
        }
      }
      
      // 更新情绪指标数据
      if (data.sentiment_indicators && data.sentiment_indicators.length > 0) {
        data.sentiment_indicators.forEach((indicator: any, index: number) => {
          if (index < sentimentData.value.length) {
            const oldDataLength = sentimentData.value[index].data?.length || 0
            const oldValue = sentimentData.value[index].value
            
            sentimentData.value[index].value = indicator.value
            sentimentData.value[index].change = indicator.change
            sentimentData.value[index].level = indicator.level
            sentimentData.value[index].unit = indicator.unit
            sentimentData.value[index].description = indicator.description
            
            // 更新历史数据
            if (indicator.data && indicator.data.length > 0) {
              sentimentData.value[index].data = [...indicator.data] // 创建新数组引用
            }
          }
        })
      }
      
      // 等待DOM更新
      await nextTick()
      
      // 重新初始化或更新仪表盘图表
      initGaugeChart()
      
      // 销毁并重新创建所有迷你图表，确保数据更新
      Object.keys(miniChartInstances).forEach(name => {
        if (miniChartInstances[name]) {
          miniChartInstances[name].dispose()
          delete miniChartInstances[name]
        }
      })
      
      // 重新初始化所有迷你图表
      sentimentData.value.forEach((indicator: any, index: number) => {
        if (indicator.data && indicator.data.length > 0) {
          const chartElement = document.querySelector(`[data-chart="${indicator.name}"]`) as HTMLElement
          if (chartElement) {
            initMiniChart(indicator.name, chartElement)
          } 
        }
      })
    }
    
  } catch (error) {
    ElMessage.error('获取市场情绪数据失败')
  } finally {
    loading.value = false
  }
}

// 获取情绪等级
const getMoodLevel = (score: number): string => {
  if (score >= 80) return '极度乐观'
  if (score >= 60) return '乐观'
  if (score >= 40) return '中性'
  if (score >= 20) return '悲观'
  return '极度悲观'
}

// 工具函数
const getValueClass = (level: string) => {
  switch (level) {
    case 'bullish': return 'bullish'
    case 'bearish': return 'bearish'
    default: return 'neutral'
  }
}

const getLevelType = (level: string) => {
  switch (level) {
    case 'bullish': return 'danger'    // 看涨用红色(danger类型)
    case 'bearish': return 'success'   // 看跌用绿色(success类型)
    default: return 'info'
  }
}

const getLevelText = (level: string) => {
  switch (level) {
    case 'bullish': return '看涨'
    case 'bearish': return '看跌'
    default: return '中性'
  }
}

const getIndexClass = (index: number) => {
  if (index >= 70) return 'bullish'
  if (index <= 30) return 'bearish'
  return 'neutral'
}

// 初始化仪表盘图表
const initGaugeChart = () => {
  if (!gaugeChart.value) return

  // 如果已经存在实例，先销毁
  if (gaugeChartInstance) {
    gaugeChartInstance.dispose()
    gaugeChartInstance = null
  }

  // 先检查是否已有实例，避免重复初始化
  const existingInstance = echarts.getInstanceByDom(gaugeChart.value)
  if (existingInstance) {
    existingInstance.dispose()
  }
  gaugeChartInstance = echarts.init(gaugeChart.value)
  
  const option = {
    series: [
      {
        name: '情绪指数',
        type: 'gauge',
        startAngle: 180,
        endAngle: 0,
        center: ['50%', '75%'],
        radius: '90%',
        min: 0,
        max: 100,
        splitNumber: 10,
        axisLine: {
          lineStyle: {
            width: 6,
            color: [
              [0.3, '#27ae60'], // 绿色表示恐慌/悲观
              [0.7, '#f39c12'], // 橙色表示中性
              [1, '#e74c3c']    // 红色表示乐观
            ]
          }
        },
        pointer: {
          icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
          length: '12%',
          width: 20,
          offsetCenter: [0, '-60%'],
          itemStyle: {
            color: 'inherit'
          }
        },
        axisTick: {
          length: 12,
          lineStyle: {
            color: 'inherit',
            width: 2
          }
        },
        splitLine: {
          length: 20,
          lineStyle: {
            color: 'inherit',
            width: 5
          }
        },
        axisLabel: {
          color: textColor.value,
          fontSize: 12,
          distance: -60,
          formatter: (value: number) => {
            if (value === 0) return '极度恐慌'
            if (value === 30) return '恐慌'
            if (value === 50) return '中性'
            if (value === 70) return '乐观'
            if (value === 100) return '极度乐观'
            return ''
          }
        },
        title: {
          offsetCenter: [0, '-10%'],
          fontSize: 16,
          color: textColor.value
        },
        detail: {
          fontSize: 30,
          offsetCenter: [0, '-35%'],
          valueAnimation: true,
          formatter: (value: number) => {
            return value.toFixed(0)
          },
          color: 'inherit'
        },
        data: [
          {
            value: overallSentiment.value.index,
            name: '情绪指数'
          }
        ]
      }
    ]
  }
  
  gaugeChartInstance?.setOption(option)
}

// 初始化迷你图表
const initMiniChart = (name: string, element: HTMLElement) => {
  // 如果已经存在实例，先销毁
  if (miniChartInstances[name]) {
    miniChartInstances[name].dispose()
    delete miniChartInstances[name]
  }

      // 先检查是否已有实例，避免重复初始化
    const existingInstance = echarts.getInstanceByDom(element)
    if (existingInstance) {
      existingInstance.dispose()
    }
    const chartInstance = echarts.init(element)
  const indicator = sentimentData.value.find((item: any) => item.name === name)
  const data = indicator?.data || []
  
  if (data.length === 0) return
  
  // 计算数据范围
  const values = data.map((item: [string, number]) => item[1])
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)
  const range = maxValue - minValue
  
  // 如果range很小，使用固定的padding
  let padding = range > 0 ? range * 0.2 : Math.abs(minValue) * 0.1 || 1
  
  // 确保有最小的显示范围
  if (range < 0.01) {
    padding = Math.max(padding, 0.5)
  }
  
  const yAxisMin = minValue - padding
  const yAxisMax = maxValue + padding
  
  const chartColor = getChartColor(indicator?.level || 'neutral')
  
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDarkMode.value ? 'rgba(0,0,0,0.8)' : 'rgba(255,255,255,0.9)',
      borderColor: chartColor,
      borderWidth: 1,
      textStyle: {
        color: isDarkMode.value ? '#fff' : '#333',
        fontSize: 12
      },
      formatter: (params: any) => {
        const point = params[0]
        return `${point.name}<br/>${indicator?.name}: ${point.value}${indicator?.unit || ''}`
      },
      position: function (pos: number[], _params: any, _dom: HTMLElement, _rect: any, size: any) {
        // Ensure tooltip is positioned within visible area
        const obj: any = { top: pos[1] }
        obj[['left', 'right'][+(pos[0] < size.viewSize[0] / 2)]] = 5
        return obj
      },
      confine: true
    },
    grid: {
      left: 0,
      right: 0,
      top: 2,
      bottom: 2
    },
    xAxis: {
      type: 'category',
      show: false,
      data: data.map((item: [string, number]) => item[0])
    },
    yAxis: {
      type: 'value',
      show: false,
      min: yAxisMin,
      max: yAxisMax
    },
    series: [
      {
        data: data.map((item: [string, number]) => item[1]),
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color: chartColor,
          width: 2,
          shadowColor: chartColor,
          shadowBlur: 4,
          shadowOffsetY: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              {
                offset: 0,
                color: chartColor + '60' // 38% opacity at top
              },
              {
                offset: 0.6,
                color: chartColor + '20' // 12% opacity at middle
              },
              {
                offset: 1,
                color: chartColor + '05' // 2% opacity at bottom
              }
            ]
          }
        },
        emphasis: {
          lineStyle: {
            width: 3
          }
        }
      }
    ],
    animation: true,
    animationDuration: 300
  }
  
  chartInstance.setOption(option)
  miniChartInstances[name] = chartInstance
}

// 更新迷你图表
const updateMiniChart = (name: string, data: any[]) => {
  const chartInstance = miniChartInstances[name]
  if (chartInstance && data && data.length > 0) {
    const indicator = sentimentData.value.find((item: any) => item.name === name)
    
    // 计算数据范围
    const values = data.map((item: [string, number]) => item[1])
    const minValue = Math.min(...values)
    const maxValue = Math.max(...values)
    const range = maxValue - minValue
    
    // 如果range很小，使用固定的padding
    let padding = range > 0 ? range * 0.2 : Math.abs(minValue) * 0.1 || 1
    
    // 确保有最小的显示范围
    if (range < 0.01) {
      padding = Math.max(padding, 0.5)
    }
    
    const yAxisMin = minValue - padding
    const yAxisMax = maxValue + padding
    
    const chartColor = getChartColor(indicator?.level || 'neutral')
    
    const option = {
      tooltip: {
        trigger: 'axis',
        backgroundColor: isDarkMode.value ? 'rgba(0,0,0,0.8)' : 'rgba(255,255,255,0.9)',
        borderColor: chartColor,
        borderWidth: 1,
        textStyle: {
          color: isDarkMode.value ? '#fff' : '#333',
          fontSize: 12
        },
        formatter: (params: any) => {
          const point = params[0]
          return `${point.name}<br/>${indicator?.name}: ${point.value}${indicator?.unit || ''}`
        },
        position: function (pos: number[], _params: any, _dom: HTMLElement, _rect: any, size: any) {
          // Ensure tooltip is positioned within visible area
          const obj: any = { top: pos[1] }
          obj[['left', 'right'][+(pos[0] < size.viewSize[0] / 2)]] = 5
          return obj
        },
        confine: true
      },
      xAxis: {
        type: 'category',
        show: false,
        data: data.map((item: [string, number]) => item[0])
      },
      yAxis: {
        type: 'value',
        show: false,
        min: yAxisMin,
        max: yAxisMax
      },
      series: [{
        data: data.map((item: [string, number]) => item[1]),
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color: chartColor,
          width: 2,
          shadowColor: chartColor,
          shadowBlur: 4,
          shadowOffsetY: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              {
                offset: 0,
                color: chartColor + '60' // 38% opacity at top
              },
              {
                offset: 0.6,
                color: chartColor + '20' // 12% opacity at middle
              },
              {
                offset: 1,
                color: chartColor + '05' // 2% opacity at bottom
              }
            ]
          }
        }
      }]
    }
    
    // 使用notMerge=true和lazyUpdate=false强制完全重绘
    chartInstance.setOption(option, true)
    chartInstance.resize()
  }
}

// 获取图表颜色
const getChartColor = (level: string) => {
  if (level === 'bullish') {
    return isDarkMode.value ? '#ff4757' : '#e74c3c'  // 红色表示看涨
  } else if (level === 'bearish') {
    return isDarkMode.value ? '#2ed573' : '#27ae60'  // 绿色表示看跌
  }
  return isDarkMode.value ? '#3742fa' : '#2f3542'  // 中性用蓝灰色
}

// 监听时间范围变化
watch(timeRange, () => {
  fetchSentimentData()
})

// 监听情绪数据变化
watch(() => sentimentData.value, (newData: any[], _oldData: any[]) => {
  nextTick(() => {
    newData.forEach((indicator: any, _index: number) => {
      if (indicator.data && indicator.data.length > 0) {
        const chartElement = document.querySelector(`[data-chart="${indicator.name}"]`) as HTMLElement
        if (chartElement) {
          // 如果图表实例已存在，更新数据
          if (miniChartInstances[indicator.name]) {
            updateMiniChart(indicator.name, indicator.data)
          } else {
            // 否则初始化新图表
            initMiniChart(indicator.name, chartElement)
          }
        }
      }
    })
  })
}, { deep: true })

// 监听主题变化
watch(() => appStore.isDarkMode, () => {
  nextTick(() => {
    initGaugeChart()
    
    // 更新所有迷你图表
    Object.keys(miniChartInstances).forEach((name: string) => {
      const indicator = sentimentData.value.find((item: any) => item.name === name)
      if (indicator && indicator.data) {
        updateMiniChart(name, indicator.data)
      }
    })
  })
})

// 防抖处理的窗口大小调整
let resizeTimer: number | null = null
const handleResize = () => {
  if (resizeTimer) {
    clearTimeout(resizeTimer)
  }
  
  resizeTimer = setTimeout(() => {
    // 调整仪表盘图表大小
    if (gaugeChartInstance) {
      gaugeChartInstance.resize()
    }
    
    // 调整所有迷你图表大小
    Object.values(miniChartInstances).forEach((chart: echarts.ECharts) => {
      if (chart) {
        chart.resize()
      }
    })
  }, 150) // 150ms延迟防抖
}

// 组件挂载和卸载
onMounted(() => {
  fetchSentimentData()
  
  // 添加窗口大小调整监听器
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  gaugeChartInstance?.dispose()
  Object.values(miniChartInstances).forEach((chart: echarts.ECharts) => chart.dispose())
  
  // 清理防抖定时器
  if (resizeTimer) {
    clearTimeout(resizeTimer)
  }
  
  // 移除窗口大小调整监听器
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.sentiment-indicator {
  width: 100%;
  margin-bottom: var(--spacing-xl);
}

.indicator-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-icon {
  font-size: 18px;
  color: var(--primary-color);
}

.indicator-content {
  padding: 0;
}

.indicators-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.indicator-item {
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  background: var(--bg-tertiary);
  transition: all 0.3s ease;
  position: relative;
}

.indicator-item:hover {
  box-shadow: var(--shadow-sm);
}

.indicator-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.indicator-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.indicator-icon {
  font-size: 14px;
  color: var(--primary-color);
}

.info-icon {
  color: var(--text-secondary);
  cursor: pointer;
}

.indicator-value {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: var(--spacing-xs);
}

.current-value {
  font-size: 20px;
  font-weight: bold;
}

.current-value.bullish {
  color: #e74c3c; /* 红色表示看涨 */
}

.current-value.bearish {
  color: #27ae60; /* 绿色表示看跌 */
}

.current-value.neutral {
  color: #3742fa; /* 蓝色表示中性 */
}

.change-value {
  font-size: 12px;
}

.change-value.positive {
  color: #e74c3c; /* 红色表示上涨 */
}

.change-value.negative {
  color: #27ae60; /* 绿色表示下跌 */
}

.indicator-level {
  margin-bottom: var(--spacing-sm);
}

.indicator-chart {
  height: 60px;
  margin-top: var(--spacing-xs);
  border-radius: var(--radius-sm);
  overflow: visible;
  background: var(--bg-quaternary);
  min-height: 50px;
}

.mini-chart {
  width: 100%;
  height: 100%;
}

.sentiment-summary {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
  align-items: start;
}

.summary-gauge {
  height: 180px;
}

.summary-gauge h4 {
  font-size: 16px;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.gauge-icon {
  font-size: 16px;
  color: var(--primary-color);
}

.gauge-chart {
  width: 100%;
  height: 100%;
}

.summary-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.summary-card {
  text-align: center;
  padding: var(--spacing-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
}

.summary-title {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: var(--spacing-xs);
}

.summary-value {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: var(--spacing-xs);
}

.summary-value.bullish {
  color: #e74c3c; /* 红色表示乐观 */
}

.summary-value.bearish {
  color: #27ae60; /* 绿色表示悲观 */
}

.summary-value.neutral {
  color: #3742fa; /* 蓝色表示中性 */
}

.summary-level {
  color: var(--text-secondary);
  font-size: 14px;
}

.summary-factors {
  margin-top: var(--spacing-md);
}

.factors-header h5 {
  margin: 0 0 var(--spacing-md) 0;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.factors-header h5::before {
  content: '';
  width: 3px;
  height: 16px;
  background: var(--accent-primary);
  border-radius: 2px;
}

.factors-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.factor-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: rgba(255, 255, 255, 0.03);
  border-radius: var(--radius-sm);
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.factor-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, var(--factor-color) 0%, transparent 100%);
}

.factor-item:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateX(2px);
}

.factor-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--factor-color);
  flex-shrink: 0;
  box-shadow: 0 0 8px var(--factor-color);
}

.factor-text {
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
}

/* 不同因素的颜色主题 */
.factor-0 {
  --factor-color: #3b82f6;
}

.factor-1 {
  --factor-color: #10b981;
}

.factor-2 {
  --factor-color: #f59e0b;
}

@media (max-width: 768px) {
  .indicators-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-sm);
  }
  
  .sentiment-summary {
    grid-template-columns: 1fr;
  }
  
  .summary-gauge {
    height: 150px;
  }
  
  .indicator-chart {
    height: 50px;
    min-height: 40px;
  }
  
  .indicator-item {
    padding: var(--spacing-sm);
  }
}

@media (max-width: 480px) {
  .indicators-grid {
    gap: var(--spacing-xs);
  }
  
  .summary-gauge {
    height: 120px;
  }
  
  .indicator-chart {
    height: 45px;
    min-height: 35px;
  }
  
  .indicator-item {
    padding: var(--spacing-xs);
  }
  
  .current-value {
    font-size: 16px;
  }
  
  .factor-item {
    padding: var(--spacing-xs);
  }
  
  .factor-text {
    font-size: 11px;
  }
}

@media (min-width: 1200px) {
  .indicator-chart {
    height: 70px;
    min-height: 60px;
  }
}

@media (min-width: 1600px) {
  .indicator-chart {
    height: 80px;
    min-height: 70px;
  }
}
</style>
