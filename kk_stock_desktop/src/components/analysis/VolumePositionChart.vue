<template>
  <div class="volume-position-chart">
    <!-- 面板标题和AI按钮 -->
    <div class="panel-title-section">
      <h3 class="panel-title">
        <ChartBarIcon class="title-icon" />
        成交量与持仓分析
      </h3>
      <AskAIComponent :data-context="aiDataContext" />
    </div>
    
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>
    <div v-else class="chart-container">
      <!-- 成交量分析 -->
      <div v-if="chartType === 'volume'" class="volume-analysis">
        <div class="chart-grid">
          <div class="chart-item">
            <div class="chart-header">
              <h3 class="chart-title">成交量趋势</h3>
            </div>
            <div id="volume-trend-chart" class="chart-canvas"></div>
          </div>
          <div class="chart-item">
            <div class="chart-header">
              <h3 class="chart-title">量价关系</h3>
            </div>
            <div id="volume-price-chart" class="chart-canvas"></div>
          </div>
        </div>
        <div class="stats-panel">
          <div class="stat-card" v-for="symbol in symbols" :key="symbol">
            <div class="stat-header">
              <span class="stat-symbol">{{ getSymbolName(symbol) }}</span>
            </div>
            <div class="stat-metrics">
              <div class="stat-item today-volume">
                <div class="stat-icon">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                    <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>
                  </svg>
                </div>
                <div class="stat-content">
                  <span class="stat-label">今日成交量</span>
                  <span class="stat-value">{{ formatVolume(getVolumeStats(symbol).today) }}</span>
                </div>
              </div>
              <div class="stat-item avg-volume">
                <div class="stat-icon">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                    <path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z"/>
                  </svg>
                </div>
                <div class="stat-content">
                  <span class="stat-label">近30天日均成交量</span>
                  <span class="stat-value">{{ formatVolume(getVolumeStats(symbol).average) }}</span>
                </div>
              </div>
              <div class="stat-item amount">
                <div class="stat-icon">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                  </svg>
                </div>
                <div class="stat-content">
                  <span class="stat-label">近30天日均成交额</span>
                  <span class="stat-value">{{ formatAmount(getVolumeStats(symbol).amount) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 持仓量分析 -->
      <div v-else-if="chartType === 'position'" class="position-analysis">
        <div class="chart-grid">
          <div class="chart-item">
            <div class="chart-header">
              <h3 class="chart-title">持仓量变化趋势</h3>
            </div>
            <div id="position-trend-chart" class="chart-canvas"></div>
          </div>
          <div class="chart-item">
            <div class="chart-header">
              <h3 class="chart-title">持仓结构分布</h3>
            </div>
            <div id="position-structure-chart" class="chart-canvas"></div>
          </div>
        </div>
        <div class="position-summary">
          <div class="summary-card" v-for="symbol in symbols" :key="symbol">
            <div class="summary-header">
              <span class="summary-symbol">{{ getSymbolName(symbol) }}</span>
              <span class="summary-change" :class="getChangeClass(getPositionStats(symbol).change)">
                {{ formatChange(getPositionStats(symbol).change) }}
              </span>
            </div>
            <div class="summary-metrics">
              <div class="summary-item">
                <span class="summary-label">总持仓量</span>
                <span class="summary-value">{{ formatPosition(getPositionStats(symbol).total) }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">多头持仓</span>
                <span class="summary-value">{{ formatPosition(getPositionStats(symbol).long) }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">空头持仓</span>
                <span class="summary-value">{{ formatPosition(getPositionStats(symbol).short) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 资金流向分析 -->
      <div v-else-if="chartType === 'flow'" class="flow-analysis">
        <div class="chart-grid">
          <div class="chart-item">
            <div class="chart-header">
              <h3 class="chart-title">资金流向趋势</h3>
            </div>
            <div id="flow-trend-chart" class="chart-canvas"></div>
          </div>
          <div class="chart-item">
            <div class="chart-header">
              <h3 class="chart-title">资金流入流出饼图</h3>
            </div>
            <div id="flow-distribution-chart" class="chart-canvas"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, nextTick, onUnmounted, computed } from 'vue'
import * as echarts from 'echarts'
import { useAppStore } from '@/stores/app'
import { futuresAPI } from '@/api/futures'
import { marketAPI } from '@/api/market'
import { ChartBarIcon } from '@heroicons/vue/24/outline'
import AskAIComponent from '../AskAIComponent.vue'

interface Props {
  chartType: 'volume' | 'position' | 'flow'
  symbols: string[]
  date: string
  loading: boolean
}

const props = defineProps<Props>()

const appStore = useAppStore()

// ECharts实例存储
const chartInstances = ref<Map<string, echarts.ECharts>>(new Map())

// 获取主题相关颜色
const isDarkMode = computed(() => appStore.isDarkMode)
const textColor = computed(() => isDarkMode.value ? '#ffffff' : '#0f172a')
const borderColor = computed(() => isDarkMode.value ? 'rgba(255, 255, 255, 0.1)' : 'rgba(15, 23, 42, 0.1)')
const backgroundColor = computed(() => isDarkMode.value ? 'rgba(42, 42, 42, 0.7)' : 'rgba(255, 255, 255, 0.7)')

// 品种名称映射
const symbolNames = {
  'IF': 'IF-沪深300',
  'IC': 'IC-中证500', 
  'IH': 'IH-上证50',
  'IM': 'IM-中证1000'
}

// 模拟数据
const volumeData = ref<any>({})
const positionData = ref<any>({})

// 获取品种名称
const getSymbolName = (symbol: string): string => {
  return symbolNames[symbol as keyof typeof symbolNames] || symbol
}

// AI数据上下文
const aiDataContext = computed(() => {
  const dateStr = props.date || ''
  const symbols = props.symbols.join(', ')
  
  return {
    type: 'futures_volume_position_analysis',
    title: '成交量与持仓分析',
    period: dateStr,
    data: {
      date: dateStr,
      symbols: props.symbols,
      chartType: props.chartType,
      volumeData: volumeData.value,
      positionData: positionData.value
    },
    summary: `成交量与持仓分析（${dateStr}）：

## 分析概况
- 分析日期：${dateStr}
- 分析品种：${symbols}
- 分析类型：${props.chartType === 'volume' ? '成交量分析' : props.chartType === 'position' ? '持仓分析' : '资金流向分析'}

## 各品种成交量分析
${props.symbols.map(symbol => {
  const volumeStats = volumeData.value[symbol] || { today: 0, average: 0, amount: 0 }
  return `### ${getSymbolName(symbol)}（${symbol}）
- 今日成交量：${formatVolume(volumeStats.today)}
- 近30天日均成交量：${formatVolume(volumeStats.average)}
- 近30天日均成交额：${formatAmount(volumeStats.amount)}
- 成交活跃度：${volumeStats.today > volumeStats.average ? '高于平均' : volumeStats.today < volumeStats.average ? '低于平均' : '持平'}`
}).join('\n\n')}

## 各品种持仓分析
${props.symbols.map(symbol => {
  const positionStats = positionData.value[symbol] || { total: 0, long: 0, short: 0, change: 0 }
  const netPosition = positionStats.long - positionStats.short
  return `### ${getSymbolName(symbol)}（${symbol}）
- 总持仓量：${formatPosition(positionStats.total)}手
- 多头持仓：${formatPosition(positionStats.long)}手
- 空头持仓：${formatPosition(positionStats.short)}手
- 净持仓：${formatPosition(Math.abs(netPosition))}手（${netPosition > 0 ? '净多头' : netPosition < 0 ? '净空头' : '平衡'}）
- 持仓变化：${formatChange(positionStats.change)}手`
}).join('\n\n')}

## 市场活跃度评估
${props.symbols.map(symbol => {
  const volumeStats = volumeData.value[symbol] || { today: 0, average: 0, amount: 0 }
  const positionStats = positionData.value[symbol] || { total: 0, long: 0, short: 0, change: 0 }
  const volumeRatio = volumeStats.average > 0 ? (volumeStats.today / volumeStats.average) : 1
  const activityLevel = volumeRatio > 1.5 ? '高活跃' : volumeRatio > 0.8 ? '正常' : '低活跃'
  return `- ${getSymbolName(symbol)}：成交量比例${(volumeRatio * 100).toFixed(1)}%，活跃度${activityLevel}`
}).join('\n')}

${props.chartType === 'volume' ? `## 成交量分析要点
- 成交量趋势：反映市场参与度和关注度变化
- 量价关系：成交量与价格变化的配合关系
- 活跃度对比：各品种相对活跃程度比较
- 成交额分析：资金规模和市场容量评估` : ''}

${props.chartType === 'position' ? `## 持仓分析要点
- 持仓量变化：反映市场参与者的建仓和平仓行为
- 多空结构：市场多空力量对比和偏向性
- 持仓集中度：主要机构的持仓分布情况
- 持仓变化趋势：资金流向和市场情绪变化` : ''}

${props.chartType === 'flow' ? `## 资金流向分析要点
- 资金流入流出：主动资金的进出方向
- 流向强度：资金流动的规模和速度
- 品种轮动：不同品种间的资金转移
- 市场偏好：资金对不同品种的偏好变化` : ''}

## 分析建议
- 关注成交量与价格的背离现象
- 分析持仓量变化对价格走势的影响
- 识别异常成交量和持仓变化的信号
- 结合多空持仓结构判断市场情绪
- 利用资金流向信息把握市场热点
`
  }
})

// 监听props变化
watch([() => props.chartType, () => props.symbols, () => props.date], () => {
  if (!props.loading) {
    nextTick(() => {
      initCharts()
    })
  }
}, { immediate: true })

// 监听loading状态
watch(() => props.loading, (newLoading) => {
  if (!newLoading) {
    nextTick(() => {
      initCharts()
    })
  }
})

// 监听主题变化
watch(() => appStore.isDarkMode, () => {
  nextTick(() => {
    initCharts()
  })
})

// 初始化图表
const initCharts = async () => {
  // 清理现有图表
  chartInstances.value.forEach(chart => {
    chart.dispose()
  })
  chartInstances.value.clear()

  // 获取真实数据
  await fetchRealData()

  if (props.chartType === 'volume') {
    await initVolumeCharts()
  } else if (props.chartType === 'position') {
    await initPositionCharts()
  } else if (props.chartType === 'flow') {
    await initFlowCharts()
  }
}

// 获取真实数据
const fetchRealData = async () => {
  try {
    // 将日期格式从YYYY-MM-DD转换为YYYYMMDD
    const tradeDate = props.date.replace(/-/g, '')
    console.log(`正在获取成交量和持仓数据: 日期=${tradeDate}, 品种=${props.symbols.join(',')}`)
    
    // 获取活跃期货合约汇总数据
    const activeSummaryResponse = await futuresAPI.getActiveFuturesSummary(tradeDate, props.symbols.join(','))
    
    if (!activeSummaryResponse.success || !activeSummaryResponse.data || !activeSummaryResponse.data.summary_by_symbol) {
      throw new Error('获取活跃期货合约汇总数据失败')
    }
    
    const summaryBySymbol = activeSummaryResponse.data.summary_by_symbol
    
    // 处理成交量数据
    props.symbols.forEach(symbol => {
      const symbolData = summaryBySymbol[symbol]
      
      if (symbolData) {
        // 获取成交量数据
        const mainContractVolume = symbolData.main_contract?.volume || 0
        const mainContractAmount = 0 // API中没有直接提供amount，设为0
        
        volumeData.value[symbol] = {
          today: symbolData.total_vol || 0,
          average: 0, // 将通过历史数据计算
          amount: mainContractAmount
        }
        
        positionData.value[symbol] = {
          total: (symbolData.total_long || 0) + (symbolData.total_short || 0),
          long: symbolData.total_long || 0,
          short: symbolData.total_short || 0,
          change: symbolData.net_position_chg || 0
        }
      } else {
        // 如果没有数据，设置为0
        volumeData.value[symbol] = { today: 0, average: 0, amount: 0 }
        positionData.value[symbol] = { total: 0, long: 0, short: 0, change: 0 }
      }
    })
    
    // 计算日均成交量（获取过去30天的数据）
    await calculateAverageVolume(tradeDate)
    
    console.log('成功获取成交量和持仓数据:', { volumeData: volumeData.value, positionData: positionData.value })
  } catch (error) {
    console.error('获取成交量和持仓数据失败:', error)
    // 出错时设置为空数据
    props.symbols.forEach(symbol => {
      volumeData.value[symbol] = { today: 0, average: 0, amount: 0 }
      positionData.value[symbol] = { total: 0, long: 0, short: 0, change: 0 }
    })
  }
}

// 计算日均成交量
const calculateAverageVolume = async (endDate: string) => {
  try {
    // 计算30天前的日期
    const year = parseInt(endDate.substring(0, 4))
    const month = parseInt(endDate.substring(4, 6)) - 1
    const day = parseInt(endDate.substring(6, 8))
    const startDate = new Date(year, month, day)
    startDate.setDate(startDate.getDate() - 30)
    const startDateStr = startDate.toISOString().split('T')[0].replace(/-/g, '')
    
    // 获取交易日列表，排除非交易日
    const tradingDaysResponse = await marketAPI.getTradingDays(startDateStr, endDate)
    if (!tradingDaysResponse.success || !tradingDaysResponse.data) {
      console.warn('无法获取交易日历信息，使用原有计算方式')
    }
    
    console.log('交易日历API响应:', {
      success: tradingDaysResponse.success,
      dataLength: tradingDaysResponse.data?.length,
      sampleData: tradingDaysResponse.data?.slice(0, 3)
    })
    
    const tradingDays = (tradingDaysResponse.success && tradingDaysResponse.data) ? 
      new Set(tradingDaysResponse.data.map((item: any) => item.date)) : 
      new Set()
      
    console.log('交易日集合:', {
      size: tradingDays.size,
      sample: Array.from(tradingDays).slice(0, 5)
    })
    
    // 获取每个品种的主力合约历史数据
    const activeSummaryResponse = await futuresAPI.getActiveFuturesSummary(endDate, props.symbols.join(','))
    if (!activeSummaryResponse.success || !activeSummaryResponse.data?.summary_by_symbol) {
      console.warn('无法获取主力合约信息，跳过日均成交量计算')
      return
    }
    
    const summaryBySymbol = activeSummaryResponse.data.summary_by_symbol
    
    for (const symbol of props.symbols) {
      const symbolData = summaryBySymbol[symbol]
      if (!symbolData?.main_contract?.symbol) continue
      
      let mainContract = symbolData.main_contract.symbol
      
      // 确保合约代码包含.CFX后缀
      if (!mainContract.endsWith('.CFX')) {
        mainContract = `${mainContract}.CFX`
      }
      
      // 获取主力合约的历史K线数据
      const klineResponse = await futuresAPI.getFuturesDaily(
        mainContract,
        startDateStr,
        endDate,
        30
      )
      
      if (klineResponse.success && klineResponse.data && klineResponse.data.daily_data && klineResponse.data.daily_data.length > 0) {
        console.log(`${symbol} K线数据样本:`, {
          总数据条数: klineResponse.data.daily_data.length,
          样本数据: klineResponse.data.daily_data.slice(0, 3).map(item => ({
            trade_date: item.trade_date,
            vol: item.vol,
            amount: item.amount
          }))
        })
        
        // 过滤出交易日的数据
        const tradingDayData = klineResponse.data.daily_data.filter((item: any) => {
          // 如果没有获取到交易日历，则不过滤
          if (tradingDays.size === 0) return true
          const isTradeDay = tradingDays.has(item.trade_date)
          if (!isTradeDay) {
            console.log(`${symbol} 非交易日被过滤:`, item.trade_date)
          }
          return isTradeDay
        })
        
        console.log(`${symbol} 过滤后数据:`, {
          原始数据: klineResponse.data.daily_data.length,
          过滤后: tradingDayData.length,
          交易日集合大小: tradingDays.size
        })
        
        // 计算平均成交量和成交额（仅基于交易日）
        const volumes = tradingDayData.map((item: any) => item.vol || 0)
        const amounts = tradingDayData.map((item: any) => item.amount || 0)
        const validVolumes = volumes.filter((vol: number) => vol > 0)
        const validAmounts = amounts.filter((amount: number) => amount > 0)
        
        console.log(`${symbol} 成交量统计:`, {
          总数据: volumes.length,
          有效数据: validVolumes.length,
          平均成交量: validVolumes.length > 0 ? validVolumes.reduce((sum, vol) => sum + vol, 0) / validVolumes.length : 0
        })
        
        if (validVolumes.length > 0) {
          const averageVolume = validVolumes.reduce((sum: number, vol: number) => sum + vol, 0) / validVolumes.length
          
          // 更新日均成交量
          if (volumeData.value[symbol]) {
            volumeData.value[symbol].average = Math.round(averageVolume)
          }
        }
        
        if (validAmounts.length > 0) {
           const averageAmount = validAmounts.reduce((sum: number, amount: number) => sum + amount, 0) / validAmounts.length
           
           // 更新日均成交额
           if (volumeData.value[symbol]) {
             volumeData.value[symbol].amount = Math.round(averageAmount)
           }
         }
      }
    }
    
    console.log('日均成交量计算完成:', volumeData.value)
  } catch (error) {
    console.error('计算日均成交量失败:', error)
  }
}

const initVolumeCharts = async () => {
  // 成交量趋势图
  const trendContainer = document.getElementById('volume-trend-chart')
  if (trendContainer) {
    try {
      // 先检查并清理现有图表实例
      if (chartInstances.value.has('volume-trend')) {
        const existingChart = chartInstances.value.get('volume-trend')
        if (existingChart && !existingChart.isDisposed()) {
          existingChart.dispose()
        }
        chartInstances.value.delete('volume-trend')
      }
      
      // 检查DOM元素是否已有ECharts实例
      const existingInstance = echarts.getInstanceByDom(trendContainer)
      if (existingInstance && !existingInstance.isDisposed()) {
        existingInstance.dispose()
      }
      
      const chart = echarts.init(trendContainer)
      chartInstances.value.set('volume-trend', chart)
      
      // 获取历史成交量数据
      const endDate = props.date.replace(/-/g, '')
      // 正确解析YYYYMMDD格式的日期字符串
      const dateStr = props.date.replace(/-/g, '')
      const year = parseInt(dateStr.substring(0, 4))
      const month = parseInt(dateStr.substring(4, 6)) - 1 // 月份从0开始
      const day = parseInt(dateStr.substring(6, 8))
      const startDate = new Date(year, month, day)
      startDate.setDate(startDate.getDate() - 30) // 获取30天数据
      const startDateStr = startDate.toISOString().split('T')[0].replace(/-/g, '')
      
      // 获取所有品种的主力合约代码
      const activeSummaryResponse = await futuresAPI.getActiveFuturesSummary(endDate, props.symbols.join(','))
      
      if (!activeSummaryResponse.success || !activeSummaryResponse.data || !activeSummaryResponse.data.summary_by_symbol) {
        throw new Error('获取主力合约失败')
      }
      
      const summaryBySymbol = activeSummaryResponse.data.summary_by_symbol
      
      // 获取所有主力合约的K线数据
      const tsCodes: string[] = []
      for (const symbol of props.symbols) {
        let mainContract = summaryBySymbol[symbol]?.main_contract?.symbol
        if (mainContract) {
          // 确保合约代码包含.CFX后缀
          if (!mainContract.endsWith('.CFX')) {
            mainContract = `${mainContract}.CFX`
          }
          tsCodes.push(mainContract)
        }
      }
      
      if (tsCodes.length === 0) {
        throw new Error('未找到有效的主力合约')
      }
      
      // 批量获取K线数据
      console.log('调用批量K线数据API:', {
        ts_codes: tsCodes,
        start_date: startDateStr,
        end_date: endDate,
        limit: 30
      })
      
      const response = await futuresAPI.getBatchFuturesDaily({
        ts_codes: tsCodes,
        start_date: startDateStr,
        end_date: endDate,
        limit: 30
      })
      
      if (!response.success || !response.data) {
        throw new Error('批量获取K线数据失败')
      }
      
      const responseData = response.data
      
      if (!responseData.results) {
        throw new Error('批量获取K线数据返回格式错误')
      }
      
      // 处理数据
      const allDates = new Set<string>()
      
      // 收集所有日期
      responseData.results.forEach(result => {
        if (result.success && result.data) {
          result.data.forEach(item => {
            allDates.add(item.trade_date)
          })
        }
      })
      
      // 按日期正向排序（从早到晚）
      const dates = Array.from(allDates).sort((a, b) => a.localeCompare(b))
      
      // 生成系列数据
      const series = props.symbols.map((symbol, index) => {
        const symbolData = responseData.results.find(r => 
          r.success && r.data && r.ts_code.includes(symbol)
        )
        
        const data = dates.map(date => {
          const item = symbolData?.data?.find(d => d.trade_date === date)
          return item?.vol || null
        })
        
        return {
          name: getSymbolName(symbol),
          type: 'line',
          data: data,
          smooth: true,
          lineStyle: { color: getColor(index) }
        }
      })

      // 从系列数据生成图例，确保一致性
      const legendData = series.map(s => s.name)

      const option = {
        title: {
          text: '成交量趋势对比',
          textStyle: { color: textColor.value }
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: backgroundColor.value,
          textStyle: { color: textColor.value },
          formatter: function(params: any[]) {
            if (!params || params.length === 0) return ''
            
            const date = params[0].axisValue
            let result = `<div style="margin-bottom: 5px;"><strong>${date}</strong></div>`
            
            params.forEach(param => {
              const value = param.value ? Number(param.value).toLocaleString() : 'N/A'
              result += `<div style="margin: 2px 0;">
                <span style="display: inline-block; width: 12px; height: 12px; background-color: ${param.color}; border-radius: 50%; margin-right: 8px;"></span>
                ${param.seriesName}: ${value}
              </div>`
            })
            
            return result
          }
        },
        legend: {
          data: legendData,
          textStyle: { color: textColor.value }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: dates,
          axisLine: { lineStyle: { color: borderColor.value } },
          axisLabel: { color: textColor.value }
        },
        yAxis: {
          type: 'value',
          axisLine: { lineStyle: { color: borderColor.value } },
          axisLabel: { color: textColor.value },
          splitLine: { lineStyle: { color: borderColor.value } }
        },
        series: series
      }

      chart.setOption(option)
    } catch (error) {
      console.error('初始化成交量趋势图表失败:', error)
      // 出错时使用已有的图表实例显示空图表
      if (chartInstances.value.has('volume-trend')) {
        const chart = chartInstances.value.get('volume-trend')
        if (chart && !chart.isDisposed()) {
          const option = {
            title: {
              text: '成交量趋势对比 - 暂无数据',
              textStyle: { color: textColor.value }
            },
            tooltip: {
              trigger: 'axis',
              backgroundColor: backgroundColor.value,
              textStyle: { color: textColor.value }
            },
            legend: {
              data: [],
              textStyle: { color: textColor.value }
            },
            grid: {
              left: '3%',
              right: '4%',
              bottom: '3%',
              containLabel: true
            },
            xAxis: {
              type: 'category',
              data: [],
              axisLine: { lineStyle: { color: borderColor.value } },
              axisLabel: { color: textColor.value }
            },
            yAxis: {
              type: 'value',
              axisLine: { lineStyle: { color: borderColor.value } },
              axisLabel: { color: textColor.value },
              splitLine: { lineStyle: { color: borderColor.value } }
            },
            series: []
          }
          chart.setOption(option)
        }
      }
    }
  }

  // 量价关系图
  const priceContainer = document.getElementById('volume-price-chart')
  if (priceContainer) {
    try {
      // 先检查并清理现有图表实例
      if (chartInstances.value.has('volume-price')) {
        const existingChart = chartInstances.value.get('volume-price')
        if (existingChart && !existingChart.isDisposed()) {
          existingChart.dispose()
        }
        chartInstances.value.delete('volume-price')
      }
      
      // 检查DOM元素是否已有ECharts实例
      const existingInstance = echarts.getInstanceByDom(priceContainer)
      if (existingInstance && !existingInstance.isDisposed()) {
        existingInstance.dispose()
      }
      
      const chart = echarts.init(priceContainer)
      chartInstances.value.set('volume-price', chart)
      
      // 获取历史量价数据
      const endDate = props.date.replace(/-/g, '')
      // 正确解析YYYYMMDD格式的日期字符串
      const dateStr = props.date.replace(/-/g, '')
      const year = parseInt(dateStr.substring(0, 4))
      const month = parseInt(dateStr.substring(4, 6)) - 1 // 月份从0开始
      const day = parseInt(dateStr.substring(6, 8))
      const startDate = new Date(year, month, day)
      startDate.setDate(startDate.getDate() - 30) // 获取30天数据
      const startDateStr = startDate.toISOString().split('T')[0].replace(/-/g, '')
      
      // 获取所有品种的主力合约代码
      const activeSummaryResponse = await futuresAPI.getActiveFuturesSummary(endDate, props.symbols.join(','))
      
      if (!activeSummaryResponse.success || !activeSummaryResponse.data || !activeSummaryResponse.data.summary_by_symbol) {
        throw new Error('获取主力合约失败')
      }
      
      const summaryBySymbol = activeSummaryResponse.data.summary_by_symbol
      
      // 获取所有主力合约的K线数据
      const tsCodes: string[] = []
      for (const symbol of props.symbols) {
        let mainContract = summaryBySymbol[symbol]?.main_contract?.symbol
        if (mainContract) {
          // 确保合约代码包含.CFX后缀
          if (!mainContract.endsWith('.CFX')) {
            mainContract = `${mainContract}.CFX`
          }
          tsCodes.push(mainContract)
        }
      }
      
      if (tsCodes.length === 0) {
        throw new Error('未找到有效的主力合约')
      }
      
      // 批量获取K线数据
      console.log('调用批量K线数据API:', {
        ts_codes: tsCodes,
        start_date: startDateStr,
        end_date: endDate,
        limit: 30
      })
      
      const response = await futuresAPI.getBatchFuturesDaily({
        ts_codes: tsCodes,
        start_date: startDateStr,
        end_date: endDate,
        limit: 30
      })
      
      if (!response.success || !response.data) {
        throw new Error('批量获取K线数据失败')
      }
      
      const responseData = response.data
      
      if (!responseData.results) {
        throw new Error('批量获取K线数据返回格式错误')
      }
      
      // 生成散点数据
      const scatterData = props.symbols.map((symbol, index) => {
        const symbolData = responseData.results.find(r => 
          r.success && r.data && r.ts_code.includes(symbol)
        )
        
        const data = []
        if (symbolData && symbolData.data) {
          for (let i = 1; i < symbolData.data.length; i++) {
            const prev = symbolData.data[i-1]
            const curr = symbolData.data[i]
            if (prev && curr && prev.close && curr.close) {
              // 计算价格变化百分比和成交量
              const pctChange = ((curr.close - prev.close) / prev.close) * 100
              data.push([curr.vol, pctChange])
            }
          }
        }
        
        return {
          name: getSymbolName(symbol),
          type: 'scatter',
          data: data,
          itemStyle: { color: getColor(index) }
        }
      })

      // 确保图例数据与系列名称完全一致
      const legendData = scatterData.map(s => s.name)

      const option = {
        title: {
          text: '量价关系散点图',
          textStyle: { color: textColor.value }
        },
        tooltip: {
          trigger: 'item',
          backgroundColor: backgroundColor.value,
          textStyle: { color: textColor.value }
        },
        legend: {
          data: legendData,
          textStyle: { color: textColor.value }
        },
        xAxis: {
          type: 'value',
          name: '成交量',
          axisLine: { lineStyle: { color: borderColor.value } },
          axisLabel: { color: textColor.value },
          nameTextStyle: { color: textColor.value }
        },
        yAxis: {
          type: 'value',
          name: '价格变化%',
          axisLine: { lineStyle: { color: borderColor.value } },
          axisLabel: { color: textColor.value },
          nameTextStyle: { color: textColor.value },
          splitLine: { lineStyle: { color: borderColor.value } }
        },
        series: scatterData
      }

      chart.setOption(option)
    } catch (error) {
      console.error('初始化量价关系图表失败:', error)
      // 出错时使用已有的图表实例显示空图表
      if (chartInstances.value.has('volume-price')) {
        const chart = chartInstances.value.get('volume-price')
        if (chart && !chart.isDisposed()) {
          const option = {
            title: {
              text: '量价关系散点图 - 暂无数据',
              textStyle: { color: textColor.value }
            },
            tooltip: {
              trigger: 'item',
              backgroundColor: backgroundColor.value,
              textStyle: { color: textColor.value }
            },
            legend: {
              data: [],
              textStyle: { color: textColor.value }
            },
            xAxis: {
              type: 'value',
              name: '成交量',
              axisLine: { lineStyle: { color: borderColor.value } },
              axisLabel: { color: textColor.value },
              nameTextStyle: { color: textColor.value }
            },
            yAxis: {
              type: 'value',
              name: '价格变化%',
              axisLine: { lineStyle: { color: borderColor.value } },
              axisLabel: { color: textColor.value },
              nameTextStyle: { color: textColor.value },
              splitLine: { lineStyle: { color: borderColor.value } }
            },
            series: []
          }
          chart.setOption(option)
        }
      }
    }
  }
}

// 初始化持仓图表
const initPositionCharts = async () => {
  // 持仓量趋势图
  const trendContainer = document.getElementById('position-trend-chart')
  if (trendContainer) {
    const chart = echarts.init(trendContainer)
    chartInstances.value.set('position-trend', chart)

    if (positionData.value && positionData.value.length > 0) {
      // 获取日期数据（使用第一个品种的日期作为X轴）
      const dates = positionData.value[0]?.data.map((item: any) => 
        item.trade_date.substring(4, 6) + '/' + item.trade_date.substring(6, 8)
      ) || []

      const series = positionData.value.map((data: any, index: number) => ({
        name: getSymbolName(data.symbol),
        type: 'line',
        data: data.data.map((item: any) => item.oi),
        smooth: true,
        lineStyle: { width: 2 },
        symbol: 'circle',
        symbolSize: 4
      }))

      // 从系列数据生成图例，确保一致性
      const legendData = series.map((s: any) => s.name)

      const option = {
        title: {
          text: '持仓量趋势对比',
          textStyle: { color: textColor.value }
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: backgroundColor.value,
          textStyle: { color: textColor.value },
          formatter: function(params: any[]) {
            if (!params || params.length === 0) return ''
            
            const date = params[0].axisValue
            let result = `<div style="margin-bottom: 5px;"><strong>${date}</strong></div>`
            
            params.forEach(param => {
              const value = param.value ? Number(param.value).toLocaleString() : 'N/A'
              result += `<div style="margin: 2px 0;">
                <span style="display: inline-block; width: 12px; height: 12px; background-color: ${param.color}; border-radius: 50%; margin-right: 8px;"></span>
                ${param.seriesName}: ${value}
              </div>`
            })
            
            return result
          }
        },
        legend: {
          data: legendData,
          textStyle: { color: textColor.value }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: dates,
          axisLine: { lineStyle: { color: borderColor.value } },
          axisLabel: { color: textColor.value }
        },
        yAxis: {
          type: 'value',
          axisLine: { lineStyle: { color: borderColor.value } },
          axisLabel: { color: textColor.value },
          splitLine: { lineStyle: { color: borderColor.value } }
        },
        series: series
      }

      chart.setOption(option)
    } else {
      // 错误状态的图表选项
      const option = {
        title: {
          text: '持仓量趋势对比 - 暂无数据',
          textStyle: { color: textColor.value }
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: backgroundColor.value,
          textStyle: { color: textColor.value }
        },
        legend: {
          data: [],
          textStyle: { color: textColor.value }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: [],
          axisLine: { lineStyle: { color: borderColor.value } },
          axisLabel: { color: textColor.value }
        },
        yAxis: {
          type: 'value',
          axisLine: { lineStyle: { color: borderColor.value } },
          axisLabel: { color: textColor.value },
          splitLine: { lineStyle: { color: borderColor.value } }
        },
        series: []
      }

      chart.setOption(option)
    }
  }

  // 持仓结构饼图
  const structureContainer = document.getElementById('position-structure-chart')
  if (structureContainer) {
    const chart = echarts.init(structureContainer)
    chartInstances.value.set('position-structure', chart)

    const pieData = props.symbols.map((symbol, index) => ({
      name: getSymbolName(symbol),
      value: positionData.value[symbol]?.total || 0,
      itemStyle: { color: getColor(index) }
    }))

    const option = {
      title: {
        text: '持仓结构分布',
        textStyle: { color: textColor.value }
      },
      tooltip: {
        trigger: 'item',
        backgroundColor: backgroundColor.value,
        textStyle: { color: textColor.value }
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        textStyle: { color: textColor.value }
      },
      series: [{
        name: '持仓量',
        type: 'pie',
        radius: '50%',
        data: pieData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    }

    chart.setOption(option)
  }
}

// 初始化资金流向图表
const initFlowCharts = async () => {
  // 资金流向趋势图
  const flowContainer = document.getElementById('flow-trend-chart')
  if (flowContainer) {
    const chart = echarts.init(flowContainer)
    chartInstances.value.set('flow-trend', chart)

    const dates = generateDates(30)
    const series = props.symbols.map((symbol, index) => ({
      name: getSymbolName(symbol),
      type: 'line',
      data: generateFlowData(30),
      smooth: true,
      lineStyle: { color: getColor(index) }
    }))

    const option = {
      title: {
        text: '资金流向趋势',
        textStyle: { color: textColor.value }
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: backgroundColor.value,
        textStyle: { color: textColor.value }
      },
      legend: {
        data: props.symbols.map(s => getSymbolName(s)),
        textStyle: { color: textColor.value }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: borderColor.value } },
        axisLabel: { color: textColor.value }
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: borderColor.value } },
        axisLabel: { color: textColor.value },
        splitLine: { lineStyle: { color: borderColor.value } }
      },
      series: series
    }

    chart.setOption(option)
  }

  // 资金流入流出饼图
  const distributionContainer = document.getElementById('flow-distribution-chart')
  if (distributionContainer) {
    const chart = echarts.init(distributionContainer)
    chartInstances.value.set('flow-distribution', chart)

    const option = {
      title: {
        text: '资金流向分布',
        textStyle: { color: textColor.value }
      },
      tooltip: {
        trigger: 'item',
        backgroundColor: backgroundColor.value,
        textStyle: { color: textColor.value }
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        textStyle: { color: textColor.value }
      },
      series: [
        {
          name: '资金流向',
          type: 'pie',
          radius: '50%',
          data: [
            { 
              value: 60, 
              name: '资金流入', 
              itemStyle: { color: isDarkMode.value ? '#22c55e' : '#4ade80' } 
            },
            { 
              value: 40, 
              name: '资金流出', 
              itemStyle: { color: isDarkMode.value ? '#ef4444' : '#f87171' } 
            }
          ],
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

    chart.setOption(option)
  }
}

// 工具函数
const generateDates = (days: number): string[] => {
  const dates = []
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(date.toISOString().split('T')[0])
  }
  return dates
}

const generateVolumeData = (days: number): number[] => {
  const data = []
  for (let i = 0; i < days; i++) {
    data.push(Math.floor(Math.random() * 50000) + 30000)
  }
  return data
}

const generatePositionData = (days: number): number[] => {
  const data = []
  let base = 100000
  for (let i = 0; i < days; i++) {
    base += (Math.random() - 0.5) * 5000
    data.push(Math.floor(base))
  }
  return data
}

const generateScatterData = () => {
  return props.symbols.map((symbol, index) => ({
    name: getSymbolName(symbol),
    type: 'scatter',
    data: Array.from({ length: 20 }, () => [
      Math.random() * 100000,
      (Math.random() - 0.5) * 10
    ]),
    itemStyle: { color: getColor(index) }
  }))
}

const generateFlowData = (days: number): number[] => {
  const data = []
  for (let i = 0; i < days; i++) {
    data.push(Math.random() * 1000000)
  }
  return data
}

const getColor = (index: number): string => {
  const darkColors = ['#ef4444', '#22c55e', '#3b82f6', '#f59e0b']
  const lightColors = ['#f87171', '#4ade80', '#60a5fa', '#fbbf24']
  const colors = isDarkMode.value ? darkColors : lightColors
  return colors[index % colors.length]
}

// 数据格式化函数
const formatVolume = (value: number): string => {
  if (value >= 10000) {
    return (value / 10000).toFixed(1) + '万手'
  }
  return value.toString() + '手'
}

const formatAmount = (value: number): string => {
  if (value >= 100000000) {
    return (value / 100000000).toFixed(1) + '亿元'
  } else if (value >= 10000) {
    return (value / 10000).toFixed(1) + '万元'
  }
  return value.toString() + '元'
}

const formatPosition = (value: number): string => {
  if (value >= 10000) {
    return (value / 10000).toFixed(1) + '万手'
  }
  return value.toString() + '手'
}

const formatChange = (value: number): string => {
  const sign = value >= 0 ? '+' : ''
  return sign + formatPosition(Math.abs(value))
}

const getChangeClass = (value: number): string => {
  return value >= 0 ? 'positive' : 'negative'
}

// 获取统计数据
const getVolumeStats = (symbol: string) => {
  return volumeData.value[symbol] || { today: 0, average: 0, amount: 0 }
}

const getPositionStats = (symbol: string) => {
  return positionData.value[symbol] || { total: 0, long: 0, short: 0, change: 0 }
}

// 修改组件卸载时清理图表
onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  // 清理所有图表实例
  chartInstances.value.forEach((chart, key) => {
    if (chart && !chart.isDisposed()) {
      chart.dispose()
    }
  })
  chartInstances.value.clear()
})

const handleResize = () => {
  chartInstances.value.forEach((chart, key) => {
    if (chart && !chart.isDisposed()) {
      chart.resize()
    }
  })
}
</script>

<style scoped>
.volume-position-chart {
  width: 100%;
  min-height: 400px;
}

.panel-title-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  gap: var(--spacing-lg);
}

.panel-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.title-icon {
  width: 20px;
  height: 20px;
}

.loading-container {
  padding: var(--spacing-lg);
}

.chart-container {
  width: 100%;
}

.chart-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.chart-item {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-primary);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.chart-canvas {
  width: 100%;
  height: 350px;
}

.stats-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-md);
}

.stat-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-primary);
}

.stat-header {
  margin-bottom: var(--spacing-sm);
}

.stat-symbol {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.stat-metrics {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
}

.stat-content {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 2px;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
}

/* 今日成交量样式 - 蓝色主题 */
.stat-item.today-volume {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(147, 197, 253, 0.05));
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.stat-item.today-volume .stat-icon {
  background: linear-gradient(135deg, #3b82f6, #60a5fa);
  color: white;
}

.stat-item.today-volume .stat-value {
  color: #1d4ed8;
}

/* 日均成交量样式 - 绿色主题 */
.stat-item.avg-volume {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(134, 239, 172, 0.05));
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.stat-item.avg-volume .stat-icon {
  background: linear-gradient(135deg, #22c55e, #4ade80);
  color: white;
}

.stat-item.avg-volume .stat-value {
  color: #15803d;
}

/* 成交额样式 - 紫色主题 */
.stat-item.amount {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(196, 181, 253, 0.05));
  border: 1px solid rgba(168, 85, 247, 0.2);
}

.stat-item.amount .stat-icon {
  background: linear-gradient(135deg, #a855f7, #c084fc);
  color: white;
}

.stat-item.amount .stat-value {
  color: #7c3aed;
}

/* 暗色主题适配 */
.dark .stat-item.today-volume .stat-value {
  color: #60a5fa;
}

.dark .stat-item.avg-volume .stat-value {
  color: #4ade80;
}

.dark .stat-item.amount .stat-value {
  color: #c084fc;
}

.position-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-md);
}

.summary-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-primary);
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.summary-symbol {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.summary-change {
  font-size: 12px;
  font-weight: 600;
}

.summary-change.positive {
  color: var(--color-success);
}

.summary-change.negative {
  color: var(--color-danger);
}

.summary-metrics {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.summary-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.flow-analysis .chart-grid {
  margin-bottom: var(--spacing-lg);
}

.flow-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-md);
}

.flow-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-primary);
}

.flow-header {
  margin-bottom: var(--spacing-sm);
}

.flow-symbol {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.flow-metrics {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.flow-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.flow-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.flow-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chart-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-header {
    flex-direction: column;
    gap: var(--spacing-sm);
    align-items: flex-start;
  }
}
</style>
