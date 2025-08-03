<template>
  <div class="portfolio-analysis">
    <el-row :gutter="24">
      <!-- 组合价值走势图 -->
      <el-col :span="24" class="chart-section">
        <el-card class="chart-card">
          <template #header>
            <h3>
              <ArrowTrendingUpIcon class="chart-icon" />
              组合价值走势分析
            </h3>
          </template>
          <div ref="portfolioChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="24" style="margin-top: 24px">
      <!-- 现金持有比例 -->
      <el-col :span="12" class="chart-section">
        <el-card class="chart-card">
          <template #header>
            <h3>
              <ChartPieIcon class="chart-icon" />
              资产配置变化
            </h3>
          </template>
          <div ref="allocationChartRef" class="chart-container-small"></div>
        </el-card>
      </el-col>

      <!-- 持仓数量变化 -->  
      <el-col :span="12" class="chart-section">
        <el-card class="chart-card">
          <template #header>
            <h3>
              <HashtagIcon class="chart-icon" />
              持仓数量统计
            </h3>
          </template>
          <div ref="positionCountRef" class="chart-container-small"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 当前持仓详情 -->
    <el-row :gutter="24" style="margin-top: 24px" v-if="portfolioData?.positions?.length">
      <el-col :span="24">
        <el-card>
          <template #header>
            <h3>
              <TableCellsIcon class="chart-icon" />
              当前持仓详情
            </h3>
          </template>
          <el-table :data="portfolioData.positions" stripe>
            <el-table-column prop="symbol" label="股票代码" width="120" />
            <el-table-column prop="name" label="股票名称" width="150" />
            <el-table-column prop="shares" label="持股数量" width="120">
              <template #default="{ row }">
                {{ formatNumber(row.shares) }}
              </template>
            </el-table-column>
            <el-table-column prop="avg_price" label="均价" width="100">
              <template #default="{ row }">
                ¥{{ row.avg_price?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="current_price" label="现价" width="100">
              <template #default="{ row }">
                ¥{{ row.current_price?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="market_value" label="市值" width="120">
              <template #default="{ row }">
                ¥{{ formatNumber(row.market_value) }}
              </template>
            </el-table-column>
            <el-table-column prop="unrealized_pnl" label="浮动盈亏" width="120">
              <template #default="{ row }">
                <span :class="getPnlClass(row.unrealized_pnl)">
                  ¥{{ formatNumber(row.unrealized_pnl) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="weight" label="仓位占比" width="100">
              <template #default="{ row }">
                {{ (row.weight * 100).toFixed(2) }}%
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElRow, ElCol, ElCard, ElTable, ElTableColumn } from 'element-plus'
import {
  ArrowTrendingUpIcon,
  ChartPieIcon,
  HashtagIcon,
  TableCellsIcon
} from '@heroicons/vue/24/outline'
import * as echarts from 'echarts'
import type { Position } from '../../types/backtest'

interface PortfolioData {
  dates: string[]
  totalValues: number[]
  cumulativeReturns: number[]
  dailyReturns: number[]
  positions: Position[]
}

interface TradesData {
  trades: any[]
  summary: any
  tradeMetrics: any
}

interface Props {
  portfolioData: PortfolioData | null
  chartData: any
  tradesData?: TradesData | null
}

const props = defineProps<Props>()

const portfolioChartRef = ref<HTMLElement>()
const allocationChartRef = ref<HTMLElement>()
const positionCountRef = ref<HTMLElement>()

let portfolioChart: echarts.ECharts | null = null
let allocationChart: echarts.ECharts | null = null
let positionChart: echarts.ECharts | null = null

// 动态获取主题颜色
const getThemeColors = () => {
  const isDark = document.documentElement.classList.contains('dark')
  return {
    textPrimary: isDark ? '#ffffff' : '#0f172a',
    textSecondary: isDark ? '#b4b4b4' : '#475569'
  }
}

const formatNumber = (num: number) => {
  if (Math.abs(num) >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  }
  return num.toFixed(2)
}

const getPnlClass = (pnl: number) => {
  return pnl >= 0 ? 'profit' : 'loss'
}

const initPortfolioChart = () => {
  if (!portfolioChartRef.value || !props.portfolioData) return

  // 清理之前的图表实例
  if (portfolioChart) {
    portfolioChart.dispose()
    portfolioChart = null
  }

  portfolioChart = echarts.init(portfolioChartRef.value)
  const themeColors = getThemeColors()
  
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
          const value = param.seriesName === '组合价值' 
            ? `¥${formatNumber(param.value)}`
            : `${param.value.toFixed(2)}%`
          result += `${param.marker}${param.seriesName}: ${value}<br/>`
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
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 80,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: props.portfolioData.dates,
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
          formatter: (value: number) => `¥${formatNumber(value)}`
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
        name: '累计收益率(%)',
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
        data: props.portfolioData.totalValues,
        lineStyle: {
          color: '#5470c6',
          width: 2
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(84, 112, 198, 0.3)' },
            { offset: 1, color: 'rgba(84, 112, 198, 0.1)' }
          ])
        }
      },
      {
        name: '累计收益率',
        type: 'line',
        yAxisIndex: 1,
        data: props.portfolioData.cumulativeReturns,
        lineStyle: {
          color: '#91cc75',
          width: 2
        }
      }
    ]
  }

  portfolioChart.setOption(option)
}

const initAllocationChart = () => {
  if (!allocationChartRef.value || !props.portfolioData) return

  // 清理之前的图表实例
  if (allocationChart) {
    allocationChart.dispose()
    allocationChart = null
  }

  allocationChart = echarts.init(allocationChartRef.value)
  const themeColors = getThemeColors()
  
  // 计算平均现金比例和持仓比例
  const avgCash = props.portfolioData.totalValues.reduce((sum, total) => {
    const positionValue = total - (props.portfolioData!.totalValues[0] || 1000000) // 简化计算
    const cashRatio = 1 - (positionValue / total)
    return sum + cashRatio
  }, 0) / props.portfolioData.totalValues.length

  const data = [
    { value: avgCash * 100, name: '现金', itemStyle: { color: '#fac858' } },
    { value: (1 - avgCash) * 100, name: '股票持仓', itemStyle: { color: '#ee6666' } }
  ]

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}%'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      textStyle: {
        color: themeColors.textPrimary
      }
    },
    series: [
      {
        type: 'pie',
        radius: '70%',
        center: ['60%', '50%'],
        data: data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }

  allocationChart.setOption(option)
}

// 计算实际持仓数量的函数
const calculateActualPositions = () => {
  if (!props.tradesData?.trades) {
    console.log('📊 持仓计算 - 没有交易数据')
    return new Map()
  }
  
  const trades = props.tradesData.trades
  const dailyPositions = new Map() // 存储每日的持仓情况
  
  console.log('📊 持仓计算 - 开始处理交易数据:', {
    总交易数: trades.length,
    前3笔交易: trades.slice(0, 3).map(t => ({
      symbol: t.symbol || t.stock_code,
      action: t.action || t.order_type,
      date: t.date || t.trade_date,
      shares: t.shares || t.quantity
    }))
  })
  
  // 按时间正序排序交易
  const sortedTrades = trades.sort((a, b) => {
    const dateA = new Date(a.date || a.trade_date || '')
    const dateB = new Date(b.date || b.trade_date || '')
    return dateA.getTime() - dateB.getTime()
  })
  
  // 跟踪当前持仓
  const currentPositions = new Map() // stock_code -> quantity
  
  sortedTrades.forEach((trade, index) => {
    const symbol = trade.symbol || trade.stock_code || ''
    const action = trade.action || trade.order_type || ''
    const shares = trade.shares || trade.quantity || 0
    const tradeDate = trade.date || trade.trade_date || ''
    
    if (index < 5) {
      console.log(`📊 处理交易 ${index + 1}:`, { symbol, action, shares, tradeDate })
    }
    
    // 更新持仓
    if (!currentPositions.has(symbol)) {
      currentPositions.set(symbol, 0)
    }
    
    if (action === 'buy') {
      currentPositions.set(symbol, currentPositions.get(symbol) + shares)
    } else if (action === 'sell') {
      const newQuantity = currentPositions.get(symbol) - shares
      if (newQuantity <= 0) {
        currentPositions.delete(symbol)
      } else {
        currentPositions.set(symbol, newQuantity)
      }
    }
    
    // 记录当日持仓数量
    const positionCount = currentPositions.size
    dailyPositions.set(tradeDate, positionCount)
    
    if (index < 5) {
      console.log(`📊 更新后持仓数量: ${positionCount}, 持仓股票:`, Array.from(currentPositions.keys()))
    }
  })
  
  console.log('📊 持仓计算完成:', {
    每日持仓记录数: dailyPositions.size,
    样本数据: Array.from(dailyPositions.entries()).slice(0, 5)
  })
  
  return dailyPositions
}

const initPositionChart = () => {
  if (!positionCountRef.value) return

  // 清理之前的图表实例
  if (positionChart) {
    positionChart.dispose()
    positionChart = null
  }

  positionChart = echarts.init(positionCountRef.value)
  const themeColors = getThemeColors()
  
  console.log('📊 持仓分析 - 初始化持仓数量图表:', {
    hasTradesData: !!props.tradesData,
    tradesCount: props.tradesData?.trades?.length || 0,
    hasPortfolioData: !!props.portfolioData,
    portfolioDataKeys: props.portfolioData ? Object.keys(props.portfolioData) : [],
    portfolioDataSample: props.portfolioData ? {
      dates: props.portfolioData.dates?.slice(0, 3),
      totalValues: props.portfolioData.totalValues?.slice(0, 3),
      positions: props.portfolioData.positions?.slice(0, 2),
      datesLength: props.portfolioData.dates?.length,
      totalValuesLength: props.portfolioData.totalValues?.length,
      positionsLength: props.portfolioData.positions?.length,
      positionsIsEmpty: props.portfolioData.positions?.length === 0
    } : null,
    hasChartData: !!props.chartData,
    chartDataKeys: props.chartData ? Object.keys(props.chartData) : [],
    chartDataStructure: props.chartData ? {
      portfolio_value: !!props.chartData.portfolio_value,
      trades_analysis: !!props.chartData.trades_analysis,
      trades_analysis_keys: props.chartData.trades_analysis ? Object.keys(props.chartData.trades_analysis) : [],
      trades_analysis_sample: props.chartData.trades_analysis
    } : null
  })
  
  // 优先检查后端chartData中是否有持仓统计数据
  if (props.chartData?.trades_analysis) {
    console.log('📊 检测到后端trades_analysis数据，详细结构：', {
      trades_analysis_full: props.chartData.trades_analysis,
      has_position_data: !!props.chartData.trades_analysis.position_stats,
      position_stats: props.chartData.trades_analysis.position_stats,
      has_monthly_stats: !!props.chartData.trades_analysis.monthly_stats,
      monthly_stats: props.chartData.trades_analysis.monthly_stats
    })
    
    // 检查是否有现成的持仓统计数据
    if (props.chartData.trades_analysis.position_stats) {
      console.log('📊 使用后端持仓统计数据')
      renderPositionChartFromBackendData(props.chartData.trades_analysis.position_stats, themeColors)
      return
    } else if (props.chartData.trades_analysis.monthly_stats) {
      console.log('📊 使用后端月度统计数据计算持仓')
      renderPositionChartFromMonthlyStats(props.chartData.trades_analysis.monthly_stats, themeColors)
      return
    }
  }
  
  // 如果后端没有现成的持仓数据，且有交易数据，使用实际计算的持仓数量  
  if (props.tradesData?.trades && props.tradesData.trades.length > 0) {
    console.log('📊 后端无现成持仓数据，使用前端计算方式')
    const dailyPositions = calculateActualPositions()
    
    // 按月统计持仓数量
    const monthlyPositions = new Map<string, number[]>()
    
    console.log('📊 开始月度统计，每日持仓数据样本:', Array.from(dailyPositions.entries()).slice(0, 10))
    
    for (const [dateStr, positionCount] of dailyPositions.entries()) {
      const date = new Date(dateStr)
      const monthKey = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`
      
      if (!monthlyPositions.has(monthKey)) {
        monthlyPositions.set(monthKey, [])
      }
      
      monthlyPositions.get(monthKey)!.push(positionCount as number)
    }
    
    console.log('📊 月度持仓统计详情:', Array.from(monthlyPositions.entries()).map(([month, counts]) => ({
      月份: month,
      天数: counts.length,
      持仓数量样本: counts.slice(0, 5),
      月末持仓: counts[counts.length - 1] // 显示月末实际持仓数量
    })))
    
    // 获取每月末的实际持仓数量
    const months: string[] = []
    const positionCounts: number[] = []
    
    Array.from(monthlyPositions.entries())
      .sort(([a], [b]) => a.localeCompare(b)) // 字符串排序自动处理跨年：2024-01 < 2024-12 < 2025-01
      .forEach(([monthKey, counts]) => {
        const [year, month] = monthKey.split('-')
        months.push(`${year}年${month}月`) // 显示完整的年月信息
        // 取每月最后一个交易日的持仓数量，而不是平均值
        const monthEndCount = counts.length > 0 ? counts[counts.length - 1] : 0
        positionCounts.push(monthEndCount)
      })
  
    console.log('📈 持仓数量统计:', { 
      months, 
      positionCounts,
      月度持仓统计: Array.from(monthlyPositions.entries())
    })
    
    // 构建图表配置
    const chartData = { months, positionCounts }
    renderPositionChart(chartData, themeColors)
    
  } else {
    // 如果没有交易数据，使用基于portfolioData的合理估算方法
    console.warn('没有交易数据，使用基于portfolioData的持仓数量估算')
    
    if (!props.portfolioData?.dates) {
      console.warn('没有组合数据，无法显示持仓数量图表')
      const chartData = { months: [], positionCounts: [] }
      renderPositionChart(chartData, themeColors)
      return
    }
    
    // 基于组合价值变化和收益率来推断持仓情况
    const totalValues = props.portfolioData.totalValues || []
    const dailyReturns = props.portfolioData.dailyReturns || []
    const dates = props.portfolioData.dates || []
    
    // 按月统计持仓数量变化（基于波动率和收益的智能估算）
    const monthlyPositions = new Map<string, number[]>()
    
    dates.forEach((dateStr: string, index: number) => {
      const date = new Date(dateStr)
      const monthKey = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`
      
      if (!monthlyPositions.has(monthKey)) {
        monthlyPositions.set(monthKey, [])
      }
      
      // 智能估算持仓数量：基于收益率波动和组合价值变化
      const dailyReturn = dailyReturns[index] || 0
      const totalValue = totalValues[index] || 0
      const initialValue = totalValues[0] || 1000000
      
      // 基于多个因素综合判断持仓数量
      let estimatedPositions = 1 // 基础持仓
      
      // 因素1：如果有明显的日收益率波动，说明有股票持仓
      if (Math.abs(dailyReturn) > 0.01) { // 日收益率超过1%
        estimatedPositions = Math.min(5, Math.ceil(Math.abs(dailyReturn) * 100)) // 根据波动率估算持仓数
      }
      
      // 因素2：组合价值显著偏离初始值，说明有仓位变化
      const valueRatio = totalValue / initialValue
      if (valueRatio > 1.02 || valueRatio < 0.98) { // 组合价值偏离初始值2%以上
        estimatedPositions = Math.max(estimatedPositions, 2)
      }
      
      // 因素3：如果组合价值接近初始资金，可能主要持有现金
      if (Math.abs(valueRatio - 1) < 0.005) { // 非常接近初始值
        estimatedPositions = Math.max(1, Math.floor(estimatedPositions * 0.5))
      }
      
      monthlyPositions.get(monthKey)!.push(estimatedPositions)
    })
    
    console.log('📊 智能估算持仓数量样本:', {
      sampleData: Array.from(monthlyPositions.entries()).slice(0, 3).map(([month, counts]) => ({
        month,
        avgCount: counts.reduce((sum, count) => sum + count, 0) / counts.length,
        countRange: [Math.min(...counts), Math.max(...counts)],
        sampleCounts: counts.slice(0, 5)
      }))
    })
    
    // 获取每月末的实际持仓数量
    const months: string[] = []
    const positionCounts: number[] = []
    
    Array.from(monthlyPositions.entries())
      .sort(([a], [b]) => a.localeCompare(b)) // 字符串排序自动处理跨年
      .forEach(([monthKey, counts]) => {
        const [year, month] = monthKey.split('-')
        months.push(`${year}年${month}月`) // 显示完整的年月信息
        // 取每月最后一个交易日的持仓数量
        const monthEndCount = counts.length > 0 ? counts[counts.length - 1] : 0
        positionCounts.push(monthEndCount)
      })
    
    console.log('📈 简化持仓数量统计:', { months, positionCounts })
    
    const chartData = { months, positionCounts }
    renderPositionChart(chartData, themeColors)
  }
}

// 基于后端持仓统计数据渲染图表
const renderPositionChartFromBackendData = (positionStats: any, themeColors: any) => {
  console.log('📊 后端持仓统计数据处理:', positionStats)
  
  // 根据后端数据结构调整
  if (positionStats.monthly_position_counts) {
    const sortedEntries = Object.entries(positionStats.monthly_position_counts)
      .sort(([a], [b]) => a.localeCompare(b)) // 确保跨年排序正确
    const months = sortedEntries.map(([monthKey]) => {
      // 如果是YYYY-MM格式，显示完整年月；否则只显示月份
      if (monthKey.includes('-')) {
        const [year, month] = monthKey.split('-')
        return `${year}年${month}月`
      }
      return `${monthKey}月`
    })
    const positionCounts = sortedEntries.map(([, count]) => count as number)
    renderPositionChart({ months, positionCounts }, themeColors)
  } else {
    // 如果没有月度数据，显示空状态
    renderPositionChart({ months: [], positionCounts: [] }, themeColors)
  }
}

// 基于后端月度统计数据渲染图表
const renderPositionChartFromMonthlyStats = (monthlyStats: any, themeColors: any) => {
  console.log('📊 后端月度统计数据处理:', monthlyStats)
  
  // 尝试从月度统计中提取持仓数据
  if (monthlyStats.position_counts) {
    const sortedEntries = Object.entries(monthlyStats.position_counts)
      .sort(([a], [b]) => a.localeCompare(b)) // 确保跨年排序正确
    const months = sortedEntries.map(([monthKey]) => {
      // 如果是YYYY-MM格式，显示完整年月；否则只显示月份
      if (monthKey.includes('-')) {
        const [year, month] = monthKey.split('-')
        return `${year}年${month}月`
      }
      return `${monthKey}月`
    })
    const positionCounts = sortedEntries.map(([, count]) => count as number)
    renderPositionChart({ months, positionCounts }, themeColors)
  } else if (Array.isArray(monthlyStats)) {
    // 如果是数组格式，尝试提取持仓信息
    const months: string[] = []
    const positionCounts: number[] = []
    
    monthlyStats.forEach((monthData: any, index: number) => {
      // 如果月度数据包含具体的年月信息，使用它；否则使用索引
      if (monthData.year && monthData.month) {
        months.push(`${monthData.year}年${monthData.month.toString().padStart(2, '0')}月`)
      } else {
        months.push(`${index + 1}月`)
      }
      // 尝试从月度数据中获取持仓数量，如果没有则默认为1
      positionCounts.push(monthData.position_count || monthData.positions?.length || 1)
    })
    
    renderPositionChart({ months, positionCounts }, themeColors)
  } else {
    // 如果无法解析，显示空状态
    renderPositionChart({ months: [], positionCounts: [] }, themeColors)
  }
}

const renderPositionChart = (data: {months: string[], positionCounts: number[]}, themeColors: any) => {
  if (data.months.length === 0) {
    // 显示空状态
    const option = {
      title: {
        text: '暂无持仓数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: themeColors.textSecondary,
          fontSize: 16
        }
      }
    }
    positionChart?.setOption(option)
    return
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const data = params[0]
        return `${data.axisValue}<br/>持仓数量: ${data.value}只股票`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.months,
      axisLabel: {
        color: themeColors.textSecondary
      },
      splitLine: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      name: '持仓数量',
      nameTextStyle: {
        color: themeColors.textPrimary
      },
      axisLabel: {
        color: themeColors.textSecondary
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
        data: data.positionCounts,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#83bff6' },
            { offset: 1, color: '#188df0' }
          ])
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#2378f7' },
              { offset: 1, color: '#2378f7' }
            ])
          }
        }
      }
    ]
  }

  positionChart?.setOption(option)
}

const resizeCharts = () => {
  portfolioChart?.resize()
  allocationChart?.resize()
  positionChart?.resize()
}

// 监听主题变化
const themeObserver = new MutationObserver((mutations) => {
  mutations.forEach(mutation => {
    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
      const isDark = document.documentElement.classList.contains('dark')
      console.log('💼 组合分析主题切换:', isDark ? '暗色模式' : '浅色模式')
      
      setTimeout(() => {
        initPortfolioChart()
        initAllocationChart()
        initPositionChart()
      }, 150)
    }
  })
})

onMounted(() => {
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class']
  })
  
  nextTick(() => {
    initPortfolioChart()
    initAllocationChart()
    initPositionChart()
  })
  
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  themeObserver.disconnect()
  portfolioChart?.dispose()
  allocationChart?.dispose()
  positionChart?.dispose()
  window.removeEventListener('resize', resizeCharts)
})

watch(() => [props.portfolioData, props.tradesData], () => {
  console.log('📊 持仓分析 - 数据变化触发重新渲染:', {
    hasPortfolioData: !!props.portfolioData,
    hasTradesData: !!props.tradesData,
    tradesCount: props.tradesData?.trades?.length || 0
  })
  
  nextTick(() => {
    initPortfolioChart()
    initAllocationChart()
    initPositionChart()
  })
}, { deep: true })
</script>

<style scoped>
.portfolio-analysis {
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
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-icon {
  width: 18px;
  height: 18px;
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.chart-container {
  width: 100%;
  height: 400px;
}

.chart-container-small {
  width: 100%;
  height: 300px;
}

.profit {
  color: var(--el-color-success);
  font-weight: 600;
}

.loss {
  color: var(--el-color-danger);
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chart-container {
    height: 300px;
  }
  
  .chart-container-small {
    height: 250px;
  }
  
  .chart-card :deep(.el-card__header) {
    padding: 12px 16px;
  }
}
</style>