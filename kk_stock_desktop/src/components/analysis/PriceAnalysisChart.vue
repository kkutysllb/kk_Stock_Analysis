<template>
  <div class="price-analysis-chart">
    <!-- 面板标题和AI按钮 -->
    <div class="panel-title-section">
      <h3 class="panel-title">
        <ChartBarIcon class="title-icon" />
        价格走势分析
      </h3>
      <AskAIComponent :data-context="aiDataContext" />
    </div>
    
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>
    <div v-else class="chart-container">
      <!-- K线图模式 -->
      <div v-if="chartType === 'kline'" class="kline-charts">
        <div 
          v-for="symbol in symbols" 
          :key="symbol" 
          class="chart-item"
        >
          <div class="chart-header">
            <h3 class="chart-title">{{ getSymbolName(symbol) }} K线图</h3>
            <div class="contract-info" v-if="mainContracts[symbol]">
              <span class="contract-label">主力合约:</span>
              <span class="contract-code">{{ mainContracts[symbol] }}</span>
            </div>
            <div class="chart-controls">
              <el-radio-group v-model="timeframe" size="small" @change="handleTimeframeChange">
                <el-radio-button value="1d">日线</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <div :id="`kline-${symbol}`" class="chart-canvas"></div>
        </div>
      </div>

      <!-- 对比分析模式 -->
      <div v-else-if="chartType === 'compare'" class="compare-chart">
        <div class="chart-header">
          <h3 class="chart-title">价格走势对比</h3>
          <div class="chart-controls">
            <el-select v-model="compareMetric" size="small" @change="handleMetricChange">
              <el-option label="收盘价" value="close" />
              <el-option label="涨跌幅" value="change_pct" />
              <el-option label="振幅" value="amplitude" />
            </el-select>
          </div>
        </div>
        <div id="compare-chart" class="chart-canvas"></div>
      </div>

      <!-- 相关性分析模式 -->
      <div v-else-if="chartType === 'correlation'" class="correlation-chart">
        <div class="chart-header">
          <h3 class="chart-title">品种相关性热力图</h3>
          <div class="chart-controls">
            <el-select v-model="correlationPeriod" size="small" @change="handlePeriodChange">
              <el-option label="近30天" value="30" />
              <el-option label="近60天" value="60" />
              <el-option label="近90天" value="90" />
            </el-select>
          </div>
        </div>
        <div id="correlation-chart" class="chart-canvas"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { futuresAPI, type FuturesKlineData } from '@/api/futures'
import { useAppStore } from '@/stores/app'
import { ChartBarIcon } from '@heroicons/vue/24/outline'
import AskAIComponent from '../AskAIComponent.vue'

interface Props {
  chartType: 'kline' | 'compare' | 'correlation'
  symbols: string[]
  date: string
  loading: boolean
}

const props = defineProps<Props>()
const appStore = useAppStore()

// 响应式数据
const timeframe = ref('1d')
const compareMetric = ref('close')
const correlationPeriod = ref('30')

// 主力合约信息存储
const mainContracts = ref<Record<string, string>>({})

// ECharts实例存储
const chartInstances = ref<Map<string, echarts.ECharts>>(new Map())

// 品种名称映射
const symbolNames = {
  'IF': 'IF-沪深300',
  'IC': 'IC-中证500', 
  'IH': 'IH-上证50',
  'IM': 'IM-中证1000'
}

// 获取主题相关颜色
const isDarkMode = computed(() => appStore.isDarkMode)
const textColor = computed(() => isDarkMode.value ? '#ffffff' : '#0f172a')
const borderColor = computed(() => isDarkMode.value ? 'rgba(255, 255, 255, 0.1)' : 'rgba(15, 23, 42, 0.1)')
const backgroundColor = computed(() => isDarkMode.value ? 'rgba(42, 42, 42, 0.7)' : 'rgba(255, 255, 255, 0.7)')

// 获取品种名称
const getSymbolName = (symbol: string): string => {
  return symbolNames[symbol as keyof typeof symbolNames] || symbol
}

// AI数据上下文
const aiDataContext = computed(() => {
  const dateStr = props.date ? `${props.date.slice(0,4)}-${props.date.slice(4,6)}-${props.date.slice(6,8)}` : ''
  const symbols = props.symbols.join(', ')
  
  return {
    type: 'futures_price_analysis',
    title: '期货价格走势分析',
    period: dateStr,
    data: {
      date: dateStr,
      symbols: props.symbols,
      chartType: props.chartType,
      timeframe: timeframe.value,
      compareMetric: compareMetric.value,
      correlationPeriod: correlationPeriod.value,
      mainContracts: mainContracts.value
    },
    summary: `期货价格走势分析（${dateStr}）：

## 分析概况
- 分析日期：${dateStr}
- 分析品种：${symbols}
- 图表类型：${props.chartType === 'kline' ? 'K线图' : props.chartType === 'compare' ? '对比分析' : '相关性分析'}
- 时间周期：${timeframe.value === '1d' ? '日线' : timeframe.value}

## 各品种分析
${props.symbols.map(symbol => 
  `### ${getSymbolName(symbol)}（${symbol}）
- 主力合约：${mainContracts.value[symbol] || '加载中...'}
- 分析维度：价格走势、技术指标、成交量
- 图表展示：K线图、均线系统（MA5、MA10、MA20）`
).join('\n\n')}

## 技术分析要点
- K线形态：反映价格开盘、收盘、最高、最低价
- 均线系统：MA5（短期趋势）、MA10（中期趋势）、MA20（长期趋势）
- 成交量：反映市场活跃度和资金关注度
- 价格区间：支撑位和阻力位识别

${props.chartType === 'compare' ? `## 对比分析设置
- 对比指标：${compareMetric.value === 'close' ? '收盘价' : compareMetric.value === 'change_pct' ? '涨跌幅' : '振幅'}
- 分析维度：多品种横向对比，识别强弱关系` : ''}

${props.chartType === 'correlation' ? `## 相关性分析设置
- 分析周期：近${correlationPeriod.value}天
- 分析方法：皮尔逊相关系数热力图
- 应用价值：套利机会识别、风险分散` : ''}

## 分析建议
- 结合K线形态判断价格趋势
- 关注均线系统的排列和交叉信号
- 分析成交量与价格的配合关系
- 识别关键支撑位和阻力位
- 多品种对比寻找相对强弱
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
}, { immediate: false })

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
  
  // 清空主力合约信息
  mainContracts.value = {}

  if (props.chartType === 'kline') {
    await initKlineCharts()
  } else if (props.chartType === 'compare') {
    await initCompareChart()
  } else if (props.chartType === 'correlation') {
    await initCorrelationChart()
  }
}

// 初始化K线图
const initKlineCharts = async () => {
  for (const symbol of props.symbols) {
    const container = document.getElementById(`kline-${symbol}`)
    if (!container) continue

    // 先检查并清理现有图表实例
    const chartId = `kline-${symbol}`
    if (chartInstances.value.has(chartId)) {
      const existingChart = chartInstances.value.get(chartId)
      if (existingChart && !existingChart.isDisposed()) {
        existingChart.dispose()
      }
      chartInstances.value.delete(chartId)
    }
    
    // 检查DOM元素是否已有ECharts实例
    const existingInstance = echarts.getInstanceByDom(container)
    if (existingInstance && !existingInstance.isDisposed()) {
      existingInstance.dispose()
    }

    const chart = echarts.init(container)
    chartInstances.value.set(chartId, chart)

    try {
      // 获取K线数据
      const klineData = await fetchKlineData(symbol)
      
      if (!klineData.dates.length || !klineData.kline.length) {
        // 如果没有数据，显示无数据提示
        chart.setOption({
          title: {
            text: '暂无数据',
            left: 'center',
            top: 'center',
            textStyle: { 
              color: textColor.value,
              fontSize: 20,
              fontWeight: 'bold'
            }
          }
        })
        console.warn(`${symbol}没有K线数据`)
        continue
      }
      
      const option = {
        title: {
          text: '',
          textStyle: { color: textColor.value }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          },
          backgroundColor: backgroundColor.value,
          textStyle: { color: textColor.value }
        },
        legend: {
          data: ['K线', 'MA5', 'MA10', 'MA20'],
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
          data: klineData.dates,
          axisLine: { lineStyle: { color: borderColor.value } },
          axisLabel: { color: textColor.value }
        },
        yAxis: {
          type: 'value',
          scale: true,
          axisLine: { lineStyle: { color: borderColor.value } },
          axisLabel: { color: textColor.value },
          splitLine: { lineStyle: { color: borderColor.value } }
        },
        series: [
          {
            name: 'K线',
            type: 'candlestick',
            data: klineData.kline,
            itemStyle: {
              color: isDarkMode.value ? '#ef4444' : '#f87171',
              color0: isDarkMode.value ? '#22c55e' : '#4ade80',
              borderColor: isDarkMode.value ? '#ef4444' : '#f87171',
              borderColor0: isDarkMode.value ? '#22c55e' : '#4ade80'
            }
          },
          {
            name: 'MA5',
            type: 'line',
            data: klineData.ma5,
            smooth: true,
            lineStyle: { color: isDarkMode.value ? '#fbbf24' : '#fcd34d' }
          },
          {
            name: 'MA10',
            type: 'line',
            data: klineData.ma10,
            smooth: true,
            lineStyle: { color: isDarkMode.value ? '#a855f7' : '#c084fc' }
          },
          {
            name: 'MA20',
            type: 'line',
            data: klineData.ma20,
            smooth: true,
            lineStyle: { color: isDarkMode.value ? '#06b6d4' : '#22d3ee' }
          }
        ]
      }

      chart.setOption(option)
    } catch (error) {
      console.error(`获取${symbol}K线数据失败:`, error)
      // 显示错误提示
      chart.setOption({
        title: {
          text: '数据加载失败',
          left: 'center',
          top: 'center',
          textStyle: { 
            color: textColor.value,
            fontSize: 20,
            fontWeight: 'bold'
          }
        }
      })
    }
  }
}

// 初始化对比图表
const initCompareChart = async () => {
  const container = document.getElementById('compare-chart')
  if (!container) return

  // 先检查并清理现有图表实例
  if (chartInstances.value.has('compare-chart')) {
    const existingChart = chartInstances.value.get('compare-chart')
    if (existingChart && !existingChart.isDisposed()) {
      existingChart.dispose()
    }
    chartInstances.value.delete('compare-chart')
  }
  
  // 检查DOM元素是否已有ECharts实例
  const existingInstance = echarts.getInstanceByDom(container)
  if (existingInstance && !existingInstance.isDisposed()) {
    existingInstance.dispose()
  }

  const chart = echarts.init(container)
  chartInstances.value.set('compare-chart', chart)

  try {
    const compareData = await fetchCompareData()
    
    const option = {
      title: {
        text: '价格走势对比',
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
        data: compareData.dates,
        axisLine: { lineStyle: { color: borderColor.value } },
        axisLabel: { color: textColor.value }
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: borderColor.value } },
        axisLabel: { color: textColor.value },
        splitLine: { lineStyle: { color: borderColor.value } }
      },
      series: compareData.series
    }

    chart.setOption(option)
  } catch (error) {
    console.error('获取对比数据失败:', error)
  }
}

// 初始化相关性图表
const initCorrelationChart = async () => {
  const container = document.getElementById('correlation-chart')
  if (!container) return

  // 先检查并清理现有图表实例
  if (chartInstances.value.has('correlation-chart')) {
    const existingChart = chartInstances.value.get('correlation-chart')
    if (existingChart && !existingChart.isDisposed()) {
      existingChart.dispose()
    }
    chartInstances.value.delete('correlation-chart')
  }
  
  // 检查DOM元素是否已有ECharts实例
  const existingInstance = echarts.getInstanceByDom(container)
  if (existingInstance && !existingInstance.isDisposed()) {
    existingInstance.dispose()
  }

  const chart = echarts.init(container)
  chartInstances.value.set('correlation-chart', chart)

  try {
    const correlationData = await fetchCorrelationData()
    
    const option = {
      title: {
        text: '品种相关性热力图',
        textStyle: { color: textColor.value }
      },
      tooltip: {
        position: 'top',
        backgroundColor: backgroundColor.value,
        textStyle: { color: textColor.value }
      },
      grid: {
        height: '50%',
        top: '10%'
      },
      xAxis: {
        type: 'category',
        data: props.symbols,
        splitArea: { show: true },
        axisLabel: { color: textColor.value }
      },
      yAxis: {
        type: 'category',
        data: props.symbols,
        splitArea: { show: true },
        axisLabel: { color: textColor.value }
      },
      visualMap: {
        min: -1,
        max: 1,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '15%',
        textStyle: { color: textColor.value }
      },
      series: [{
        name: '相关性',
        type: 'heatmap',
        data: correlationData,
        label: {
          show: true,
          color: textColor.value
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    }

    chart.setOption(option)
  } catch (error) {
    console.error('获取相关性数据失败:', error)
  }
}

// 获取K线数据
const fetchKlineData = async (symbol: string) => {
  try {
    // 直接使用传入的日期格式
    const endDate = props.date
    // 正确解析YYYYMMDD格式的日期字符串
    const year = parseInt(props.date.substring(0, 4))
    const month = parseInt(props.date.substring(4, 6)) - 1 // 月份从0开始
    const day = parseInt(props.date.substring(6, 8))
    const startDate = new Date(year, month, day)
    startDate.setDate(startDate.getDate() - 30) // 获取30天数据
    const startDateStr = startDate.toISOString().split('T')[0].replace(/-/g, '')
    
    console.log(`正在获取K线数据: 品种=${symbol}, 开始日期=${startDateStr}, 结束日期=${endDate}, 原始日期=${props.date}`)
    
    // 获取主力合约代码
    const activeSummaryResponse = await futuresAPI.getActiveFuturesSummary(endDate, symbol)
    
    if (!activeSummaryResponse.success || !activeSummaryResponse.data || !activeSummaryResponse.data.summary_by_symbol) {
      console.warn('获取主力合约失败')
      return { dates: [], kline: [], ma5: [], ma10: [], ma20: [] }
    }
    
    let mainContract = activeSummaryResponse.data.summary_by_symbol[symbol]?.main_contract?.symbol
    
    if (!mainContract) {
      console.warn(`未找到${symbol}的主力合约`)
      return { dates: [], kline: [], ma5: [], ma10: [], ma20: [] }
    }
    
    // 确保合约代码包含.CFX后缀
    if (!mainContract.endsWith('.CFX')) {
      mainContract = `${mainContract}.CFX`
    }
    
    // 保存主力合约信息用于显示
    mainContracts.value[symbol] = mainContract
    
    console.log(`使用主力合约: ${mainContract}`)
    
    // 获取K线数据
    const response = await futuresAPI.getFuturesDaily(mainContract, startDateStr, endDate, 30)
    
    if (!response.success || !response.data || !response.data.daily_data) {
      console.warn('获取K线数据失败')
      return { dates: [], kline: [], ma5: [], ma10: [], ma20: [] }
    }
    
    const klineData = response.data.daily_data
    
    // 按日期正向排序（从早到晚）
    const sortedKlineData = klineData.sort((a, b) => a.trade_date.localeCompare(b.trade_date))
    
    // 转换数据格式
    const dates = sortedKlineData.map(item => item.trade_date)
    const kline = sortedKlineData.map(item => [item.open, item.close, item.low, item.high])
    
    // 计算移动平均线
    const ma5 = calculateMA(5, sortedKlineData)
    const ma10 = calculateMA(10, sortedKlineData)
    const ma20 = calculateMA(20, sortedKlineData)
    
    return { dates, kline, ma5, ma10, ma20 }
  } catch (error) {
    console.error(`获取${symbol}K线数据失败:`, error)
    // 出错时返回空数据
    return { dates: [], kline: [], ma5: [], ma10: [], ma20: [] }
  }
}

// 计算移动平均线
const calculateMA = (days: number, data: FuturesKlineData[]) => {
  const result = []
  for (let i = 0; i < data.length; i++) {
    if (i < days - 1) {
      result.push('-')
      continue
    }
    let sum = 0
    for (let j = 0; j < days; j++) {
      sum += data[i - j].close
    }
    result.push((sum / days).toFixed(2))
  }
  return result
}

// 获取对比数据
const fetchCompareData = async () => {
  try {
    // 直接使用传入的日期格式
    const endDate = props.date
    // 正确解析YYYYMMDD格式的日期字符串
    const year = parseInt(props.date.substring(0, 4))
    const month = parseInt(props.date.substring(4, 6)) - 1 // 月份从0开始
    const day = parseInt(props.date.substring(6, 8))
    const startDate = new Date(year, month, day)
    startDate.setDate(startDate.getDate() - 30) // 获取30天数据
    const startDateStr = startDate.toISOString().split('T')[0].replace(/-/g, '')
    
    console.log(`正在获取对比数据: 开始日期=${startDateStr}, 结束日期=${endDate}, 原始日期=${props.date}`)
    
    // 获取所有品种的主力合约代码
    const activeSummaryResponse = await futuresAPI.getActiveFuturesSummary(endDate, props.symbols.join(','))
    
    if (!activeSummaryResponse.success || !activeSummaryResponse.data || !activeSummaryResponse.data.summary_by_symbol) {
      console.warn('获取主力合约失败')
      return { dates: [], series: [] }
    }
    
    // 获取所有主力合约的K线数据
    const tsCodes: string[] = []
    const symbolToContract: Record<string, string> = {}
    
    for (const symbol of props.symbols) {
      let mainContract = activeSummaryResponse.data.summary_by_symbol[symbol]?.main_contract?.symbol
      if (mainContract) {
        // 确保合约代码包含.CFX后缀
        if (!mainContract.endsWith('.CFX')) {
          mainContract = `${mainContract}.CFX`
        }
        console.log(`${symbol}使用主力合约: ${mainContract}`)
        tsCodes.push(mainContract)
        symbolToContract[symbol] = mainContract
      }
    }
    
    if (tsCodes.length === 0) {
      console.warn('未找到有效的主力合约')
      return { dates: [], series: [] }
    }
    
    // 批量获取K线数据
    const response = await futuresAPI.getBatchFuturesDaily({
      ts_codes: tsCodes,
      start_date: startDateStr,
      end_date: endDate,
      limit: 30
    })
    
    if (!response.success || !response.data || !response.data.results) {
      throw new Error('批量获取K线数据失败')
    }
    
    // 处理数据
    const allDates = new Set<string>()
    const dataBySymbol: Record<string, Record<string, number>> = {}
    
    // 收集所有日期
    response.data.results.forEach(result => {
      if (result.success && result.data) {
        result.data.forEach(item => {
          allDates.add(item.trade_date)
        })
      }
    })
    
    // 按日期正向排序（从早到晚）
    const dates = Array.from(allDates).sort((a, b) => a.localeCompare(b))
    
    // 按照品种整理数据
    response.data.results.forEach((result, index) => {
      if (result.success && result.data && index < props.symbols.length) {
        const symbol = props.symbols[index]
        if (symbol) {
          dataBySymbol[symbol] = {}
        }
        
        // 初始化基准值为100
        let baseValue = 100
        let firstClose = null
        
        // 按日期排序后找到第一个收盘价作为基准
        const sortedData = result.data.sort((a, b) => a.trade_date.localeCompare(b.trade_date))
        for (const item of sortedData) {
          if (item.close) {
            firstClose = item.close
            break
          }
        }
        
        // 计算相对变化
        sortedData.forEach(item => {
          if (firstClose && item.close) {
            // 计算相对于基准的百分比变化
            dataBySymbol[symbol][item.trade_date] = baseValue * (item.close / firstClose)
          }
        })
      }
    })
    
    // 生成系列数据
    const colors = ['#ef4444', '#22c55e', '#3b82f6', '#f59e0b']
    const series = props.symbols.map((symbol, index) => {
      const data = dates.map(date => {
        return dataBySymbol[symbol]?.[date]?.toFixed(2) || null
      })
      
      return {
        name: getSymbolName(symbol),
        type: 'line',
        data: data,
        smooth: true,
        lineStyle: { color: colors[index] }
      }
    })
    
    return { dates, series }
  } catch (error) {
    console.error('获取对比数据失败:', error)
    // 出错时返回空数据
    return { dates: [], series: [] }
  }
}

// 获取相关性数据
const fetchCorrelationData = async () => {
  try {
    // 直接使用传入的日期格式
    const endDate = props.date
    // 正确解析YYYYMMDD格式的日期字符串
    const year = parseInt(props.date.substring(0, 4))
    const month = parseInt(props.date.substring(4, 6)) - 1 // 月份从0开始
    const day = parseInt(props.date.substring(6, 8))
    const startDate = new Date(year, month, day)
    startDate.setDate(startDate.getDate() - parseInt(correlationPeriod.value)) // 根据所选周期获取数据
    const startDateStr = startDate.toISOString().split('T')[0].replace(/-/g, '')
    
    console.log(`正在获取相关性数据: 开始日期=${startDateStr}, 结束日期=${endDate}, 周期=${correlationPeriod.value}天, 原始日期=${props.date}`)
    
    // 获取所有品种的主力合约代码
    const activeSummaryResponse = await futuresAPI.getActiveFuturesSummary(endDate, props.symbols.join(','))
    
    if (!activeSummaryResponse.success || !activeSummaryResponse.data || !activeSummaryResponse.data.summary_by_symbol) {
      console.warn('获取主力合约失败')
      return []
    }
    
    // 获取所有主力合约的K线数据
    const tsCodes: string[] = []
    const symbolToContract: Record<string, string> = {}
    for (const symbol of props.symbols) {
      let mainContract = activeSummaryResponse.data.summary_by_symbol[symbol]?.main_contract?.symbol
      if (mainContract) {
        // 确保合约代码包含.CFX后缀
        if (!mainContract.endsWith('.CFX')) {
          mainContract = `${mainContract}.CFX`
        }
        console.log(`${symbol}使用主力合约: ${mainContract}`)
        tsCodes.push(mainContract)
        symbolToContract[symbol] = mainContract
      }
    }
    
    if (tsCodes.length === 0) {
      console.warn('未找到有效的主力合约')
      return []
    }
    
    // 批量获取K线数据
    const response = await futuresAPI.getBatchFuturesDaily({
      ts_codes: tsCodes,
      start_date: startDateStr,
      end_date: endDate,
      limit: parseInt(correlationPeriod.value)
    })
    
    if (!response.success || !response.data || !response.data.results) {
      throw new Error('批量获取K线数据失败')
    }
    
    // 处理数据，计算相关性
    const returns: Record<string, number[]> = {}
    
    // 计算每个品种的收益率序列
    response.data.results.forEach((result, index) => {
      if (result.success && result.data && result.data.length > 1) {
        const symbol = props.symbols[index]
        returns[symbol] = []
        
        // 计算日收益率
        for (let i = 1; i < result.data.length; i++) {
          const prevClose = result.data[i-1].close
          const currClose = result.data[i].close
          if (prevClose && currClose) {
            const dailyReturn = (currClose - prevClose) / prevClose
            returns[symbol].push(dailyReturn)
          }
        }
      }
    })
    
    // 计算相关性矩阵
    const correlationData = []
    
    for (let i = 0; i < props.symbols.length; i++) {
      for (let j = 0; j < props.symbols.length; j++) {
        const symbol1 = props.symbols[i]
        const symbol2 = props.symbols[j]
        
        if (i === j) {
          // 自相关为1
          correlationData.push([i, j, 1])
        } else if (returns[symbol1] && returns[symbol2] && 
                  returns[symbol1].length > 0 && returns[symbol2].length > 0) {
          // 计算相关系数
          const correlation = calculateCorrelation(returns[symbol1], returns[symbol2])
          correlationData.push([i, j, parseFloat(correlation.toFixed(2))])
        } else {
          // 无法计算相关性
          correlationData.push([i, j, null])
        }
      }
    }
    
    return correlationData
  } catch (error) {
    console.error('获取相关性数据失败:', error)
    // 出错时返回空数据
    return []
  }
}

// 计算相关系数
const calculateCorrelation = (x: number[], y: number[]): number => {
  const n = Math.min(x.length, y.length)
  if (n === 0) return 0
  
  // 计算均值
  const xMean = x.slice(0, n).reduce((a, b) => a + b, 0) / n
  const yMean = y.slice(0, n).reduce((a, b) => a + b, 0) / n
  
  // 计算协方差和标准差
  let numerator = 0
  let xVar = 0
  let yVar = 0
  
  for (let i = 0; i < n; i++) {
    const xDiff = x[i] - xMean
    const yDiff = y[i] - yMean
    numerator += xDiff * yDiff
    xVar += xDiff * xDiff
    yVar += yDiff * yDiff
  }
  
  if (xVar === 0 || yVar === 0) return 0
  
  return numerator / (Math.sqrt(xVar) * Math.sqrt(yVar))
}

// 事件处理
const handleTimeframeChange = () => {
  // 只有日线数据，不需要处理切换
  return
}

const handleMetricChange = () => {
  if (props.chartType === 'compare') {
    initCompareChart()
  }
}

const handlePeriodChange = () => {
  if (props.chartType === 'correlation') {
    initCorrelationChart()
  }
}

// 组件挂载和卸载
onMounted(() => {
  // 初始化图表
  nextTick(() => {
    initCharts()
  })
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  // 清理事件监听器
  window.removeEventListener('resize', handleResize)
  // 清理图表实例
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
.price-analysis-chart {
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

.kline-charts {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: var(--spacing-lg);
  min-height: 800px;
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
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.contract-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  background: var(--bg-accent);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-secondary);
}

.contract-label {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 500;
}

.contract-code {
  font-size: 11px;
  color: var(--primary-color);
  font-weight: 600;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.chart-canvas {
  width: 100%;
  height: 400px;
}

.compare-chart,
.correlation-chart {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-primary);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .kline-charts {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(4, 1fr);
    min-height: 1600px;
  }
}

@media (max-width: 768px) {
  .kline-charts {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(4, 1fr);
    min-height: 1200px;
  }
  
  .chart-header {
    flex-direction: column;
    gap: var(--spacing-sm);
    align-items: flex-start;
  }
  
  .chart-canvas {
    height: 300px;
  }
}
</style>
