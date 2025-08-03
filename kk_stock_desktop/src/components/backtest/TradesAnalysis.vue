<template>
  <div class="trades-analysis">
    <el-row :gutter="24">
      <!-- 交易频率分析 -->
      <el-col :span="12" class="chart-section">
        <el-card class="chart-card">
          <template #header>
            <h3>月度交易频率</h3>
          </template>
          <div ref="tradeFrequencyRef" class="chart-container-small"></div>
        </el-card>
      </el-col>

      <!-- 盈亏分布 -->
      <el-col :span="12" class="chart-section">
        <el-card class="chart-card">
          <template #header>
            <h3>交易盈亏分布</h3>
          </template>
          <div ref="pnlDistributionRef" class="chart-container-small"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="24" style="margin-top: 24px">
      <!-- 股票交易频次 -->
      <el-col :span="12" class="chart-section">
        <el-card class="chart-card">
          <template #header>
            <h3>股票交易频次TOP10</h3>
          </template>
          <div ref="stockFrequencyRef" class="chart-container-small"></div>
        </el-card>
      </el-col>

      <!-- 交易成本分析 -->
      <el-col :span="12" class="chart-section">
        <el-card class="chart-card">
          <template #header>
            <h3>交易成本构成</h3>
          </template>
          <div ref="tradeCostRef" class="chart-container-small"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 交易记录详情 -->
    <el-row :gutter="24" style="margin-top: 24px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="trade-header">
              <h3>交易记录详情</h3>
              <div class="trade-controls">
                <el-select v-model="filterType" size="small" style="width: 120px">
                  <el-option label="全部" value="all" />
                  <el-option label="买入" value="buy" />
                  <el-option label="卖出" value="sell" />
                </el-select>
                <el-input 
                  v-model="searchKeyword" 
                  placeholder="搜索股票代码"
                  size="small"
                  style="width: 150px; margin-left: 12px"
                  clearable
                />
              </div>
            </div>
          </template>
          
          <el-table :data="filteredTrades" stripe max-height="400" style="width: 100%" class="trades-table">
            <el-table-column prop="date" label="交易日期" width="130" />
            <el-table-column prop="symbol" label="股票代码" width="120" />
            <el-table-column prop="action" label="类型" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.action === 'buy' ? 'success' : 'danger'" size="small">
                  {{ row.action === 'buy' ? '买入' : '卖出' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="shares" label="数量" width="110" align="right">
              <template #default="{ row }">
                {{ formatNumber(row.shares) }}
              </template>
            </el-table-column>
            <el-table-column prop="price" label="价格" width="100" align="right">
              <template #default="{ row }">
                ¥{{ row.price?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="成交金额" width="130" align="right">
              <template #default="{ row }">
                <span :class="getAmountClass(row.amount, row.action)">
                  ¥{{ formatNumber(Math.abs(row.amount)) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="commission" label="手续费" width="100" align="right">
              <template #default="{ row }">
                ¥{{ row.commission?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="stamp_tax" label="印花税" width="100" align="right">
              <template #default="{ row }">
                ¥{{ row.stamp_tax?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column label="盈亏" min-width="120" align="right">
              <template #default="{ row }">
                <span v-if="row.pnl !== undefined" :class="getPnlClass(row.pnl)">
                  {{ row.pnl > 0 ? '+' : '' }}¥{{ formatNumber(row.pnl) }}
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElRow, ElCol, ElCard, ElTable, ElTableColumn, ElTag, ElSelect, ElOption, ElInput } from 'element-plus'
import * as echarts from 'echarts'
import type { Trade } from '../../types/backtest'

interface TradesData {
  trades: Trade[]
  summary: any
  tradeMetrics: any
}

interface Props {
  tradesData: TradesData | null
  chartData: any
}

const props = defineProps<Props>()

const tradeFrequencyRef = ref<HTMLElement>()
const pnlDistributionRef = ref<HTMLElement>()
const stockFrequencyRef = ref<HTMLElement>()
const tradeCostRef = ref<HTMLElement>()

const filterType = ref('all')
const searchKeyword = ref('')

let tradeFrequencyChart: echarts.ECharts | null = null
let pnlDistributionChart: echarts.ECharts | null = null
let stockFrequencyChart: echarts.ECharts | null = null
let tradeCostChart: echarts.ECharts | null = null

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

const getAmountClass = (amount: number, type: string) => {
  return type === 'buy' ? 'buy-amount' : 'sell-amount'
}

// 计算交易盈亏的函数
const calculateTradePnL = () => {
  if (!props.tradesData?.trades) return new Map()
  
  const trades = props.tradesData.trades
  const stockPositions = new Map()
  const tradePnLMap = new Map() // 存储每笔交易的盈亏
  
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
    const tradeId = trade.trade_id || `${symbol}_${action}_${price}`
    
    if (!stockPositions.has(symbol)) {
      stockPositions.set(symbol, { totalShares: 0, totalCost: 0 })
    }
    
    const position = stockPositions.get(symbol)
    
    if (action === 'buy') {
      // 买入：累加成本，盈亏为0
      const totalCost = shares * price + commission
      position.totalShares += shares
      position.totalCost += totalCost
      tradePnLMap.set(tradeId, 0) // 买入交易盈亏为0
    } else if (action === 'sell' && position.totalShares > 0) {
      // 卖出：计算盈亏
      const avgCost = position.totalCost / position.totalShares
      const sellRevenue = shares * price - commission - stampTax
      const sellCost = shares * avgCost
      const pnl = sellRevenue - sellCost
      
      tradePnLMap.set(tradeId, pnl)
      
      // 更新持仓
      position.totalShares -= shares
      position.totalCost -= sellCost
      
      // 如果全部卖出，重置成本
      if (position.totalShares <= 0) {
        position.totalShares = 0
        position.totalCost = 0
      }
    } else {
      tradePnLMap.set(tradeId, 0) // 其他情况盈亏为0
    }
  })
  
  return tradePnLMap
}

// 过滤交易记录
const filteredTrades = computed(() => {
  if (!props.tradesData?.trades) {
    console.log('📊 TradesAnalysis: 没有交易数据', props.tradesData)
    return []
  }
  
  let trades = props.tradesData.trades
  console.log('📊 TradesAnalysis: 原始交易数据', trades.length, trades[0])
  
  // 计算所有交易的盈亏
  const tradePnLMap = calculateTradePnL()
  
  // 按类型过滤
  if (filterType.value !== 'all') {
    trades = trades.filter(trade => 
      (trade.action === filterType.value) || (trade.order_type === filterType.value)
    )
  }
  
  // 按关键词搜索
  if (searchKeyword.value) {
    trades = trades.filter(trade => {
      const symbol = trade.symbol || trade.stock_code || ''
      return symbol.toLowerCase().includes(searchKeyword.value.toLowerCase())
    })
  }
  
  // 统一日期字段并添加盈亏信息
  const processedTrades = trades.map(trade => {
    const tradeId = trade.trade_id || `${trade.symbol || trade.stock_code}_${trade.action || trade.order_type}_${trade.price}`
    return {
      ...trade,
      date: trade.date || trade.trade_date || '',
      symbol: trade.symbol || trade.stock_code || '',
      action: trade.action || trade.order_type || '',
      shares: trade.shares || trade.quantity || 0,
      amount: trade.amount || trade.net_amount || 0,
      pnl: tradePnLMap.get(tradeId) || 0 // 添加计算的盈亏
    }
  })
  
  // 按时间倒序排序（最新的在前面）
  const sortedTrades = processedTrades.sort((a, b) => {
    const dateA = new Date(a.date).getTime()
    const dateB = new Date(b.date).getTime()
    return dateB - dateA // 倒序：较新的日期在前
  })
  
  console.log('📊 交易记录排序详情:', {
    总数: sortedTrades.length,
    前3条日期: sortedTrades.slice(0, 3).map(t => ({ date: t.date, symbol: t.symbol, action: t.action, pnl: t.pnl })),
    后3条日期: sortedTrades.slice(-3).map(t => ({ date: t.date, symbol: t.symbol, action: t.action, pnl: t.pnl }))
  })
  
  return sortedTrades
})

const initTradeFrequencyChart = () => {
  if (!tradeFrequencyRef.value || !props.tradesData?.trades) {
    console.log('📊 initTradeFrequencyChart: 缺少数据或DOM元素')
    return
  }

  // 检查DOM尺寸
  const rect = tradeFrequencyRef.value.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    console.log('📊 initTradeFrequencyChart: DOM尺寸为0，延迟初始化')
    setTimeout(() => initTradeFrequencyChart(), 100)
    return
  }

  tradeFrequencyChart = echarts.init(tradeFrequencyRef.value)
  
  const themeColors = getThemeColors()
  
  // 计算月度交易频率
  const monthlyTrades: { [key: string]: number } = {}
  props.tradesData.trades.forEach(trade => {
    const tradeDate = trade.date || trade.trade_date || ''
    if (tradeDate) {
      const month = tradeDate.substring(0, 7) // YYYY-MM
      monthlyTrades[month] = (monthlyTrades[month] || 0) + 1
    }
  })
  
  console.log('📊 月度交易统计:', monthlyTrades)
  
  const months = Object.keys(monthlyTrades).sort()
  const counts = months.map(month => monthlyTrades[month])

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}: {c}笔'
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: months.map(m => m.substring(5)), // 只显示月份
      axisLabel: {
        color: themeColors.textSecondary
      },
      splitLine: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      name: '交易笔数',
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
        type: 'line',
        data: counts,
        smooth: true,
        lineStyle: {
          color: '#5470c6',
          width: 3
        },
        itemStyle: {
          color: '#5470c6'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(84, 112, 198, 0.3)' },
            { offset: 1, color: 'rgba(84, 112, 198, 0.1)' }
          ])
        }
      }
    ]
  }

  tradeFrequencyChart.setOption(option)
}

const initPnlDistributionChart = () => {
  if (!pnlDistributionRef.value || !props.tradesData?.trades) return

  // 检查DOM尺寸
  const rect = pnlDistributionRef.value.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    setTimeout(() => initPnlDistributionChart(), 100)
    return
  }

  pnlDistributionChart = echarts.init(pnlDistributionRef.value)
  const themeColors = getThemeColors()
  
  // 从实际交易数据计算盈亏分布
  const trades = props.tradesData.trades
  
  console.log('📊 交易数据分析:', {
    总交易数: trades.length,
    前5笔交易: trades.slice(0, 5).map(t => ({
      symbol: t.symbol || t.stock_code,
      action: t.action || t.order_type,
      shares: t.shares,
      price: t.price,
      amount: t.amount,
      net_amount: t.net_amount,
      commission: t.commission,
      stamp_tax: t.stamp_tax,
      pnl: t.pnl,
      profit: t.profit,
      // 打印所有字段名用于调试
      all_fields: Object.keys(t)
    }))
  })
  
  // 计算每笔交易的盈亏 - 需要配对买入卖出交易
  const stockPositions = new Map() // 跟踪每只股票的持仓成本
  const pnlData: number[] = []
  
  // 按日期排序交易记录
  const sortedTrades = trades.sort((a, b) => {
    const dateA = new Date(a.date || a.trade_date || '')
    const dateB = new Date(b.date || b.trade_date || '')
    return dateA.getTime() - dateB.getTime()
  })
  
  console.log('📊 盈亏字段调试:', {
    交易数据字段示例: trades[0] ? Object.keys(trades[0]) : [],
    前3笔交易字段: trades.slice(0, 3).map(t => ({
      symbol: t.symbol || t.stock_code,
      action: t.action || t.order_type,
      shares: t.shares || t.quantity,
      price: t.price,
      amount: t.amount || t.net_amount,
      commission: t.commission,
      stamp_tax: t.stamp_tax
    }))
  })
  
  // 使用已计算的盈亏数据
  const tradePnLMap = calculateTradePnL()
  
  // 提取所有卖出交易的盈亏数据
  sortedTrades.forEach(trade => {
    const action = trade.action || trade.order_type || ''
    const tradeId = trade.trade_id || `${trade.symbol || trade.stock_code}_${action}_${trade.price}`
    
    if (action === 'sell') {
      const pnl = tradePnLMap.get(tradeId) || 0
      if (pnl !== 0) {
        pnlData.push(pnl)
      }
    }
  })
  
  console.log('📊 盈亏数据:', {
    有效交易数: pnlData.length,
    盈亏数据样本: pnlData.slice(0, 10),
    总盈亏: pnlData.reduce((sum, pnl) => sum + pnl, 0)
  })
  
  // 统计盈亏分布
  let profitCount = 0  // 盈利交易数
  let lossCount = 0    // 亏损交易数
  let breakEvenCount = 0 // 保本交易数
  let totalProfit = 0  // 总盈利
  let totalLoss = 0    // 总亏损
  
  pnlData.forEach(pnl => {
    if (pnl > 0) {
      profitCount++
      totalProfit += pnl
    } else if (pnl < 0) {
      lossCount++
      totalLoss += Math.abs(pnl)
    } else {
      breakEvenCount++
    }
  })
  
  const netPnl = totalProfit - totalLoss
  const winRate = pnlData.length > 0 ? (profitCount / pnlData.length * 100).toFixed(1) : '0.0'
  
  console.log('📊 盈亏统计:', {
    盈利交易: profitCount,
    亏损交易: lossCount,
    保本交易: breakEvenCount,
    胜率: `${winRate}%`,
    总盈利: `¥${(totalProfit / 10000).toFixed(2)}万`,
    总亏损: `¥${(totalLoss / 10000).toFixed(2)}万`,
    净盈亏: `¥${(netPnl / 10000).toFixed(2)}万`
  })
  
  // 如果没有有效的盈亏数据，显示提示
  if (pnlData.length === 0) {
    // 显示空状态
    const option = {
      title: {
        text: '暂无交易盈亏数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: themeColors.textSecondary,
          fontSize: 16
        }
      }
    }
    pnlDistributionChart.setOption(option)
    return
  }
  
  // 构建饼图数据
  const pieData: Array<{name: string, value: number, detail: string, itemStyle: {color: string}}> = []
  
  if (profitCount > 0) {
    const avgProfit = totalProfit / profitCount
    pieData.push({
      name: `盈利交易`,
      value: profitCount,
      detail: `${profitCount}笔 | 总盈利: ¥${(totalProfit / 10000).toFixed(2)}万 | 平均: ¥${(avgProfit / 10000).toFixed(2)}万`,
      itemStyle: { color: '#f56c6c' }
    })
  }
  if (lossCount > 0) {
    const avgLoss = totalLoss / lossCount
    pieData.push({
      name: `亏损交易`,
      value: lossCount,
      detail: `${lossCount}笔 | 总亏损: ¥${(totalLoss / 10000).toFixed(2)}万 | 平均: ¥${(avgLoss / 10000).toFixed(2)}万`,
      itemStyle: { color: '#67c23a' }
    })
  }
  if (breakEvenCount > 0) {
    pieData.push({
      name: `保本交易`,
      value: breakEvenCount,
      detail: `${breakEvenCount}笔 | 无盈亏`,
      itemStyle: { color: '#e6a23c' }
    })
  }

  const option = {
    title: {
      text: `胜率: ${winRate}%`,
      subtext: `净盈亏: ¥${(netPnl / 10000).toFixed(2)}万`,
      left: 'center',
      top: '10%',
      textStyle: {
        color: themeColors.textPrimary,
        fontSize: 16,
        fontWeight: 'bold'
      },
      subtextStyle: {
        color: netPnl >= 0 ? '#f56c6c' : '#67c23a',
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const percentage = ((params.value / pnlData.length) * 100).toFixed(1)
        return `${params.name}<br/>${params.data.detail}<br/>占比: ${percentage}%`
      }
    },
    legend: {
      orient: 'vertical',
      left: '10%',
      top: '55%',
      textStyle: {
        color: themeColors.textPrimary,
        fontSize: 12
      },
      formatter: (name: string) => {
        const data = pieData.find(item => item.name === name)
        if (data) {
          const percentage = ((data.value / pnlData.length) * 100).toFixed(1)
          return `${name} (${percentage}%)`
        }
        return name
      }
    },
    series: [
      {
        type: 'pie',
        radius: ['35%', '65%'],
        center: ['70%', '60%'],
        avoidLabelOverlap: false,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        label: {
          show: false
        },
        labelLine: {
          show: false
        },
        data: pieData
      }
    ]
  }

  pnlDistributionChart.setOption(option)
}

const initStockFrequencyChart = () => {
  if (!stockFrequencyRef.value || !props.tradesData?.trades) return

  // 检查DOM尺寸
  const rect = stockFrequencyRef.value.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    setTimeout(() => initStockFrequencyChart(), 100)
    return
  }

  stockFrequencyChart = echarts.init(stockFrequencyRef.value)
  const themeColors = getThemeColors()
  
  // 计算股票交易频次
  const stockCounts: { [key: string]: number } = {}
  props.tradesData.trades.forEach(trade => {
    const symbol = trade.symbol || trade.stock_code || 'Unknown'
    stockCounts[symbol] = (stockCounts[symbol] || 0) + 1
  })
  
  const sortedStocks = Object.entries(stockCounts)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 10)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '25%',
      right: '5%',
      bottom: '10%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
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
    yAxis: {
      type: 'category',
      data: sortedStocks.map(([stock]) => stock),
      axisLabel: {
        color: themeColors.textSecondary
      },
      splitLine: {
        show: false
      }
    },
    series: [
      {
        type: 'bar',
        data: sortedStocks.map(([, count]) => count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#83bff6' },
            { offset: 1, color: '#188df0' }
          ])
        }
      }
    ]
  }

  stockFrequencyChart.setOption(option)
}

const initTradeCostChart = () => {
  if (!tradeCostRef.value || !props.tradesData?.tradeMetrics) return

  // 检查DOM尺寸
  const rect = tradeCostRef.value.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    setTimeout(() => initTradeCostChart(), 100)
    return
  }

  tradeCostChart = echarts.init(tradeCostRef.value)
  const themeColors = getThemeColors()
  
  const metrics = props.tradesData.tradeMetrics
  const data = [
    { value: metrics.total_commission || 0, name: '手续费' },
    { value: metrics.total_stamp_tax || 0, name: '印花税' }
  ]

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: ¥{c}'
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
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
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

  tradeCostChart.setOption(option)
}

const resizeCharts = () => {
  tradeFrequencyChart?.resize()
  pnlDistributionChart?.resize()
  stockFrequencyChart?.resize()
  tradeCostChart?.resize()
}

onMounted(() => {
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class']
  })
  
  // 使用更长的延迟确保DOM完全渲染
  setTimeout(() => {
    nextTick(() => {
      initTradeFrequencyChart()
      initPnlDistributionChart() 
      initStockFrequencyChart()
      initTradeCostChart()
    })
  }, 300)
  
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  themeObserver.disconnect()
  tradeFrequencyChart?.dispose()
  pnlDistributionChart?.dispose()
  stockFrequencyChart?.dispose()
  tradeCostChart?.dispose()
  window.removeEventListener('resize', resizeCharts)
})

watch(() => props.tradesData, () => {
  if (props.tradesData?.trades && props.tradesData.trades.length > 0) {
    setTimeout(() => {
      nextTick(() => {
        initTradeFrequencyChart()
        initPnlDistributionChart()
        initStockFrequencyChart()
        initTradeCostChart()
      })
    }, 100)
  }
}, { deep: true })

// 监听主题变化
const themeObserver = new MutationObserver(() => {
  setTimeout(() => {
    tradeFrequencyChart?.setOption(tradeFrequencyChart.getOption(), true)
    pnlDistributionChart?.setOption(pnlDistributionChart.getOption(), true)
    stockFrequencyChart?.setOption(stockFrequencyChart.getOption(), true)
    tradeCostChart?.setOption(tradeCostChart.getOption(), true)
  }, 100)
})

onMounted(() => {
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class']
  })
  // 原有的挂载逻辑...
})

onUnmounted(() => {
  themeObserver.disconnect()
  // 原有的销毁逻辑...
})
</script>

<style scoped>
.trades-analysis {
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
  color: var(--text-primary);
}

.chart-container-small {
  width: 100%;
  height: 350px;
  min-height: 280px;
  padding: 10px;
}

.trade-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.trade-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.trade-controls {
  display: flex;
  align-items: center;
}

.trades-table {
  width: 100% !important;
}

.trades-table :deep(.el-table__body-wrapper) {
  overflow-x: auto;
}

.trades-table :deep(.el-table) {
  width: 100% !important;
  min-width: 1000px;
}

.profit {
  color: #f56c6c;
  font-weight: 600;
}

.loss {  
  color: #67c23a;
  font-weight: 600;
}

.buy-amount {
  color: var(--el-color-danger);
}

.sell-amount {
  color: var(--el-color-success);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .chart-container-small {
    height: 320px;
    padding: 8px;
  }
}

@media (max-width: 768px) {
  .chart-container-small {
    height: 280px;
    padding: 5px;
  }
  
  .trade-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .trade-controls {
    width: 100%;
    justify-content: flex-end;
  }
}

@media (max-width: 480px) {
  .chart-container-small {
    height: 250px;
    padding: 5px;
  }
}
</style>