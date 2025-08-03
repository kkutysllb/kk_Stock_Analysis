<template>
  <div class="main-indices-panel">
    <div class="panel-header">
      <!-- 面板标题和AI按钮 -->
      <div class="panel-title-section">
        <h3 class="panel-title">主要指数</h3>
        <AskAIComponent :data-context="aiDataContext" />
      </div>
      
      <!-- 指数选择器 -->
      <div class="index-selector">
        <el-radio-group 
          v-model="selectedIndex" 
          @change="onIndexChange" 
          size="default"
        >
          <el-radio-button 
            v-for="index in indexConfig" 
            :key="index.code"
            :value="index.code"
          >
            <span class="index-content">
              <span class="index-name">{{ index.name }}</span>
              <span 
                class="index-price"
                :class="{ 
                  'price-up': (getIndexLatestData(index.code)?.pct_chg || 0) > 0,
                  'price-down': (getIndexLatestData(index.code)?.pct_chg || 0) < 0,
                  'price-hidden': !getIndexLatestData(index.code)
                }"
              >
                {{ getIndexLatestData(index.code)?.close?.toFixed(2) || '--' }}
                <span class="price-change">
                  {{ (getIndexLatestData(index.code)?.pct_chg || 0) > 0 ? '+' : '' }}
                  {{ getIndexLatestData(index.code)?.pct_chg?.toFixed(2) || '0.00' }}%
                </span>
              </span>
            </span>
          </el-radio-button>
        </el-radio-group>
      </div>

      <!-- 时间控制区 -->
      <div class="time-control">
        <el-radio-group 
          v-model="activePeriod" 
          @change="onPeriodChange"
          size="default"
        >
          <el-radio-button value="daily">日线</el-radio-button>
          <el-radio-button value="weekly">周线</el-radio-button>
          <el-radio-button value="monthly">月线</el-radio-button>
          <el-radio-button value="custom">自定义</el-radio-button>
        </el-radio-group>

        <div v-show="activePeriod === 'custom'" class="date-picker-wrapper">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="default"
            format="YYYY-MM-DD"
            value-format="YYYYMMDD"
            :shortcuts="dateShortcuts"
            @change="onDateRangeChange"
            class="date-picker"
          />
        </div>

        <div v-show="activePeriod !== 'custom'" class="data-points-wrapper">
          <el-select 
            v-model="dataPoints" 
            size="default"
            @change="onDataPointsChange"
            class="data-points-select"
          >
            <el-option label="最近60个" value="60" />
            <el-option label="最近120个" value="120" />
            <el-option label="最近250个" value="250" />
          </el-select>
        </div>
      </div>
    </div>
    
    <div class="panel-body">
      <div class="chart-container" ref="chartContainer"></div>
      <div v-show="loading" class="loading-overlay">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span class="loading-text">加载中...</span>
      </div>
      
      <div class="legend-section">
        <div class="legend-item">
          <span class="legend-line line-primary"></span>
          <span>涨跌幅（红涨绿跌）</span>
        </div>
        <div class="legend-item">
          <span class="legend-line line-secondary"></span>
          <span>成交量变化幅度</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch, withDefaults, type Ref } from 'vue'
import * as echarts from 'echarts'
import { useAppStore } from '../stores/app'
import { marketAPI } from '../api/market'
import { 
  ElRadioGroup, 
  ElRadioButton,
  ElDatePicker,
  ElSelect,
  ElOption,
  ElIcon
} from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import type { DateModelType } from 'element-plus'
import 'element-plus/es/components/radio/style/css'
import 'element-plus/es/components/radio-button/style/css'
import 'element-plus/es/components/date-picker/style/css'
import 'element-plus/es/components/select/style/css'
import AskAIComponent from './AskAIComponent.vue'

// 定义props
interface Props {
  initialIndex?: string
  initialPeriod?: 'daily' | 'weekly' | 'monthly' | 'custom'
}

const props = withDefaults(defineProps<Props>(), {
  initialIndex: '000001.SH',
  initialPeriod: 'daily'
})

// 定义emit
const emit = defineEmits<{
  'update:selected-index': [code: string]
  'update:active-period': [period: string]
}>()

// 获取应用状态
const appStore = useAppStore()

// 指数配置
const indexConfig = [
  { code: '000001.SH', name: '上证指数', color: '#3b82f6' },
  { code: '399001.SZ', name: '深证成指', color: '#10b981' },
  { code: '399006.SZ', name: '创业板指', color: '#f59e0b' },
  { code: '000688.SH', name: '科创50', color: '#ef4444' },
  { code: '899050.BJ', name: '北证50', color: '#8b5cf6' }
]

// 定义类型
interface IndexLatestData {
  open?: number
  close?: number
  high?: number
  low?: number
  vol?: number
  amount?: number
  pct_chg?: number
}

interface IndexData {
  ts_code: string
  name: string
  latest_data?: IndexLatestData
}

interface ChartDataItem {
  date: string
  open: number
  close: number
  high: number
  low: number
  volume: number
  amount: number
  pct_chg: number
}

// 响应式状态
const selectedIndex = ref<string>(props.initialIndex)
const activePeriod = ref<'daily' | 'weekly' | 'monthly' | 'custom'>(props.initialPeriod)
const loading = ref(false)
const chartContainer = ref<HTMLElement | null>(null)
const chartInstance = ref<echarts.ECharts | null>(null)
const chartKey = ref(0)
const indexData = ref<IndexData | null>(null)
const chartData = ref<ChartDataItem[]>([])
const componentUnmounted = ref(false)

// 新增状态和类型定义
type DateRangeValue = [DateModelType, DateModelType] | undefined
const dateRange = ref<DateRangeValue>()
const dataPoints = ref<string>('60')

// 日期快捷选项
const dateShortcuts = [
  {
    text: '最近一周',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start, end]
    }
  },
  {
    text: '最近一月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 1)
      return [start, end]
    }
  },
  {
    text: '最近三月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 3)
      return [start, end]
    }
  }
]

// 计算属性
const selectedIndexColor = computed(() => {
  const index = indexConfig.find(i => i.code === selectedIndex.value)
  return index?.color || '#3b82f6'
})

const selectedIndexName = computed(() => {
  const index = indexConfig.find(i => i.code === selectedIndex.value)
  return index?.name || '指数'
})

// AI数据上下文
const aiDataContext = computed(() => {
  const currentIndex = indexConfig.find(i => i.code === selectedIndex.value)
  
  // 优先使用chartData中的最新数据，如果没有则使用indexDataMap中的数据
  let latestData = null
  if (chartData.value.length > 0) {
    // 从chartData获取最新数据（这是当前选中指数的实际数据）
    const latest = chartData.value[chartData.value.length - 1]
    latestData = {
      close: latest.close,
      pct_chg: latest.pct_chg,
      vol: latest.volume,
      amount: latest.amount,
      trade_date: latest.date
    }
  } else {
    // 如果chartData为空，则从indexDataMap获取
    latestData = getIndexLatestData(selectedIndex.value)
  }
  
  // 计算历史数据统计
  const getHistoricalStats = (data: any[]) => {
    if (!data || data.length === 0) return null
    
    const values = data.map(item => item.close).filter(val => val != null)
    if (values.length === 0) return null
    
    const sorted = [...values].sort((a, b) => a - b)
    const sum = values.reduce((acc, val) => acc + val, 0)
    const avg = sum / values.length
    
    return {
      count: values.length,
      min: Math.min(...values),
      max: Math.max(...values),
      avg: avg,
      median: sorted[Math.floor(sorted.length / 2)],
      trend: values.length > 1 ? (values[values.length - 1] - values[0]) / values[0] * 100 : 0,
      volatility: Math.sqrt(values.reduce((sum, val) => sum + Math.pow(val - avg, 2), 0) / values.length)
    }
  }
  
  const stats = getHistoricalStats(chartData.value)
  // 根据用户设置的数据点数量传递给AI，确保AI分析的数据量与用户查看的一致
  const dataPointsNum = parseInt(dataPoints.value) || 60
  const recentData = chartData.value.slice(-dataPointsNum) // 根据用户设置的数据点数量
  
  let summary = ''
  if (latestData) {
    const pctChg = latestData.pct_chg || 0
    const trend = pctChg > 0 ? '上涨' : pctChg < 0 ? '下跌' : '平盘'
    summary = `主要指数分析完整数据：

## 当前指数信息
- 指数名称：${currentIndex?.name || '未知'}
- 指数代码：${selectedIndex.value}
- 当前收盘价：${latestData.close?.toFixed(2)}
- 涨跌幅：${trend}${Math.abs(pctChg).toFixed(2)}%
- 成交量：${(latestData.vol || 0).toLocaleString()}万手
- 成交额：${(latestData.amount || 0).toLocaleString()}万元

## 历史数据统计（基于${recentData.length}个数据点）
${stats ? `- 数据点数：${stats.count}个
- 最高价：${stats.max.toFixed(2)}
- 最低价：${stats.min.toFixed(2)}
- 平均价：${stats.avg.toFixed(2)}
- 中位数：${stats.median.toFixed(2)}
- 整体趋势：${stats.trend > 0 ? '上升' : stats.trend < 0 ? '下降' : '平稳'}（${stats.trend.toFixed(2)}%）
- 价格波动率：${stats.volatility.toFixed(2)}` : '- 暂无历史统计数据'}

## 最近交易数据（${currentIndex?.name}）
${recentData.map(item => 
  `${item.date}: 收盘${item.close?.toFixed(2)}, 涨跌幅${(item.pct_chg || 0).toFixed(2)}%, 成交量${(item.volume || 0).toLocaleString()}万手`
).join('\n')}

## 其他主要指数对比
${Object.entries(indexDataMap.value).map(([code, data]) => {
  const indexLatestData = data.latest_data
  if (!indexLatestData || code === selectedIndex.value) return null
  const pctChg = indexLatestData.pct_chg || 0
  const trend = pctChg > 0 ? '上涨' : pctChg < 0 ? '下跌' : '平盘'
  return `- ${data.name}(${code}): ${indexLatestData.close?.toFixed(2)}, ${trend}${Math.abs(pctChg).toFixed(2)}%`
}).filter(Boolean).join('\n')}

## 分析要点
- 分析对象：${currentIndex?.name}（${selectedIndex.value}）
- 周期类型：${activePeriod.value === 'daily' ? '日线' : activePeriod.value === 'weekly' ? '周线' : activePeriod.value === 'monthly' ? '月线' : '自定义周期'}
- 数据范围：${activePeriod.value === 'custom' && dateRange.value ? `${dateRange.value[0]} 至 ${dateRange.value[1]}` : `最近${dataPoints.value}个交易日`}
- 指数特征：${currentIndex?.name}作为主要市场指数，反映整体市场走势和投资者情绪
- 技术指标：请结合价格走势、成交量变化、涨跌幅分布等进行综合分析

请基于以上完整的${currentIndex?.name}数据进行深入分析，提供投资建议、风险提示和市场前景判断。`
  } else {
    summary = `主要指数分析：

## 当前指数信息
- 指数名称：${currentIndex?.name || '未知'}
- 指数代码：${selectedIndex.value}
- 数据状态：正在加载中...

## 分析设置
- 周期类型：${activePeriod.value === 'daily' ? '日线' : activePeriod.value === 'weekly' ? '周线' : activePeriod.value === 'monthly' ? '月线' : '自定义周期'}
- 数据范围：${activePeriod.value === 'custom' && dateRange.value ? `${dateRange.value[0]} 至 ${dateRange.value[1]}` : `最近${dataPoints.value}个交易日`}

请等待数据加载完成后进行分析。`
  }
  
  return {
    type: 'main_index',
    name: `${currentIndex?.name || '主要指数'}(${selectedIndex.value})`, // 这个name字段用于AI组件检测数据变化
    title: '主要指数分析',
    selectedIndex: selectedIndex.value,
    indexName: currentIndex?.name || '',
    period: activePeriod.value,
    dataPoints: dataPoints.value,
    latestData: latestData,
    recentData: recentData,
    statistics: stats,
    summary: summary,
    data: {
      selectedIndex: selectedIndex.value,
      selectedIndexName: currentIndex?.name || '',
      period: activePeriod.value,
      dataPoints: dataPoints.value
    }
  }
})

// 处理日期范围变化
const onDateRangeChange = async (dates: DateRangeValue) => {
  try {
    if (dates) {
      dateRange.value = dates
      activePeriod.value = 'custom'
      await loadIndexData()
    } else {
      dateRange.value = undefined
      if (activePeriod.value === 'custom') {
        activePeriod.value = 'daily'
      }
    }
  } catch (error) {
    console.error('处理日期范围变化失败:', error)
  }
}

// 处理数据点数量变化
const onDataPointsChange = async (value: string) => {
  try {
    dataPoints.value = value
    if (activePeriod.value !== 'custom') {
      await loadIndexData()
    }
  } catch (error) {
    console.error('处理数据点数量变化失败:', error)
  }
}

// 修改周期切换处理
const onPeriodChange = async (period: string | number | boolean | undefined) => {
  if (isLoading.value) return
  
  try {
    if (typeof period === 'string' && 
        (period === 'daily' || period === 'weekly' || period === 'monthly' || period === 'custom')) {
      
      // 先设置loading状态，阻止进一步操作
      isLoading.value = true
      
      // 使用nextTick确保DOM更新完成
      await nextTick()
      
      // 批量更新状态
      activePeriod.value = period
      
      // 如果切换到非自定义周期，清空日期范围
      if (period !== 'custom') {
        dateRange.value = undefined
      }
      
      emit('update:active-period', period)
      
      // 等待一个tick确保状态同步
      await nextTick()
      
      await loadIndexData()
    }
  } catch (error) {
    console.error('处理周期变化失败:', error)
  } finally {
    isLoading.value = false
  }
}

// 定义状态
const indexDataMap = ref<Record<string, any>>({})

// 加载所有指数的最新数据
const loadAllIndexData = async () => {
  loading.value = true
  try {
    // 获取指数数据
    const response = await marketAPI.getIndices(
      activePeriod.value === 'custom' ? 'daily' : activePeriod.value, 
      parseInt(dataPoints.value)
    )
    
    if (response.success && response.data && response.data.indices) {
      // 遍历所有指数数据
      response.data.indices.forEach(index => {
        if (index && index.latest_data) {
          // 确保数值类型正确
          const latestData = {
            trade_date: index.latest_data.trade_date,
            open: Number(index.latest_data.open) || 0,
            high: Number(index.latest_data.high) || 0,
            low: Number(index.latest_data.low) || 0,
            close: Number(index.latest_data.close) || 0,
            pre_close: Number(index.latest_data.pre_close) || 0,
            change: Number(index.latest_data.change) || 0,
            pct_chg: Number(index.latest_data.pct_chg) || 0,
            vol: Number(index.latest_data.vol) || 0,
            amount: Number(index.latest_data.amount) || 0
          }
          
          // 如果是周或月粒度，且pct_chg为NaN或0，尝试计算环比涨跌幅
          if ((activePeriod.value === 'weekly' || activePeriod.value === 'monthly') && 
              (!latestData.pct_chg || isNaN(latestData.pct_chg))) {
            if (latestData.close && latestData.pre_close && latestData.pre_close !== 0) {
              latestData.pct_chg = ((latestData.close - latestData.pre_close) / latestData.pre_close) * 100
            }
          }
          
          // 存储处理后的数据
          indexDataMap.value[index.ts_code] = {
            name: index.name,
            latest_data: latestData
          }
        }
      })
    }
  } catch (error) {
    console.error('加载指数数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 监听周期变化时重新加载所有数据
watch([activePeriod, dataPoints], async () => {
  try {
    await loadAllIndexData()
  } catch (error) {
    console.error('重新加载指数数据失败:', error)
  }
})

// 组件挂载时加载数据
onMounted(async () => {
  try {
    await loadAllIndexData()
  } catch (error) {
    console.error('初始化加载指数数据失败:', error)
  }
})

// 获取指定指数的最新数据
const getIndexLatestData = (code: string) => {
  if (!code || !indexDataMap.value || !indexDataMap.value[code]) {
    return null
  }
  return indexDataMap.value[code]?.latest_data || null
}

// 数据加载函数
const loadIndexData = async () => {
  // 先清理图表避免DOM冲突
  safeDisposeChart()
  
  loading.value = true
  try {
    let response
    if (activePeriod.value === 'custom' && dateRange.value) {
      const [startDate, endDate] = dateRange.value
      response = await marketAPI.getIndexKline(
        selectedIndex.value,
        'daily',
        undefined,
        startDate?.toString() || '',
        endDate?.toString() || ''
      )
    } else {
      // 确定周期
      const period = activePeriod.value === 'custom' ? 'daily' : activePeriod.value
      
      // 北证50特殊处理：确保使用正确的API和参数
      if (selectedIndex.value === '899050.BJ') {
        // 确保使用正确的周期参数
        response = await marketAPI.getIndexKline(
          selectedIndex.value,
          period,  // 使用对应的周期
          parseInt(dataPoints.value)
        )
      } else {
        // 其他指数正常处理
        response = await marketAPI.getIndexKline(
          selectedIndex.value,
          period,
          parseInt(dataPoints.value)
        )
      }
    }

    // 根据后端实际返回的数据结构获取K线数据
    // API可能直接返回数组，或者嵌套在data或kline_data字段中
    if (response.success) {
      // 获取K线数据
      const rawData = Array.isArray(response.data) 
        ? response.data 
        : (response.data?.kline_data || response.data?.data || [])
      
      // 获取ts_code和name
      const ts_code = Array.isArray(response.data) 
        ? (rawData[0]?.ts_code || selectedIndex.value) 
        : (response.data?.ts_code || selectedIndex.value)
      
      const name = Array.isArray(response.data) 
        ? '' 
        : (response.data?.name || '')
      

      // 确保数据按时间正序排列
      let sortedData = [...rawData].sort((a, b) => 
        a.trade_date.localeCompare(b.trade_date)
      )
      
      // 记录数据是否为空
      const isDataEmpty = sortedData.length === 0
     
      // 计算环比涨跌幅
      const calculatePeriodChange = (data: any[], index: number) => {
        if (index <= 0 || !data[index - 1]) return 0
        const currentClose = parseFloat(String(data[index].close)) || 0
        const prevClose = parseFloat(String(data[index - 1].close)) || 0
        if (prevClose === 0) return 0
        return ((currentClose - prevClose) / prevClose) * 100
      }
      
      chartData.value = sortedData.map((item: any, index) => ({
        date: item.trade_date,
        open: parseFloat(String(item.open)) || 0,
        close: parseFloat(String(item.close)) || 0,
        high: parseFloat(String(item.high)) || 0,
        low: parseFloat(String(item.low)) || 0,
        volume: parseFloat(String(item.vol)) || 0,
        amount: parseFloat(String(item.amount)) || 0,
        // 根据时间粒度选择涨跌幅计算方法
        pct_chg: activePeriod.value === 'daily' 
          ? parseFloat(String(item.pct_chg)) || 0 
          : calculatePeriodChange(sortedData, index),
        change: parseFloat(String(item.change)) || 0,
        pre_close: parseFloat(String(item.pre_close)) || 0
      }))


      // 等待DOM更新完成后再初始化图表
      await nextTick()
    } else {
      console.error('API返回数据格式不正确:', response)
    }
  } catch (error) {
    console.error('加载指数数据失败:', error)
  } finally {
    loading.value = false
    // 在loading完成后初始化图表
    await nextTick()
    initChart()
  }
}

// 计算移动平均线
const calculateMA = (dayCount: number, data: ChartDataItem[]) => {
  const result = []
  for (let i = 0; i < data.length; i++) {
    if (i < dayCount - 1) {
      result.push(null)
      continue
    }
    let sum = 0
    for (let j = 0; j < dayCount; j++) {
      sum += data[i - j].close
    }
    result.push(+(sum / dayCount).toFixed(2))
  }
  return result
}

// 根据时间粒度获取移动平均线配置
const getMAConfig = () => {
  if (activePeriod.value === 'daily') {
    // 日粒度：MA5, MA21, MA55
    return [
      { name: 'MA5', days: 5 },
      { name: 'MA21', days: 21 },
      { name: 'MA55', days: 55 }
    ]
  } else {
    // 周粒度和月粒度：MA5, MA20, MA60
    return [
      { name: 'MA5', days: 5 },
      { name: 'MA20', days: 20 },
      { name: 'MA60', days: 60 }
    ]
  }
}

// 安全清理图表实例
const safeDisposeChart = () => {
  try {
    if (chartInstance.value) {
      chartInstance.value.dispose()
      chartInstance.value = null
    }
    
    // 清理可能残留的实例
    if (chartContainer.value) {
      const existingInstance = echarts.getInstanceByDom(chartContainer.value)
      if (existingInstance) {
        existingInstance.dispose()
      }
    }
  } catch (error) {
    console.warn('清理图表实例时出错:', error)
    chartInstance.value = null
  }
}

// 初始化图表
const initChart = () => {
  if (!chartContainer.value || !chartContainer.value.parentNode) {
    return
  }

  // 先安全清理现有实例
  safeDisposeChart()

  if (chartData.value.length === 0) {
    // 显示无数据提示
    try {
      const chart = echarts.init(chartContainer.value)
      chartInstance.value = chart
      
      chart.setOption({
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: {
            color: '#999',
            fontSize: 16
          }
        }
      })
    } catch (error) {
      console.error('初始化空数据图表失败:', error)
    }
    return
  }
  
  try {
    // 创建新的图表实例
    const chart = echarts.init(chartContainer.value, null, {
      renderer: 'canvas',
      useDirtyRect: false
    })
    chartInstance.value = chart
    
    // 设置图表自适应选项
    chart.setOption({
      backgroundColor: 'transparent',
      animation: false
    })
    
    // 准备数据
    const dates = chartData.value.map(item => {
      const dateStr = item.date
      if (typeof dateStr === 'string' && dateStr.length === 8) {
        const date = new Date(
          parseInt(dateStr.substring(0, 4)),
          parseInt(dateStr.substring(4, 6)) - 1,
          parseInt(dateStr.substring(6, 8))
        )
        
        if (activePeriod.value === 'monthly') {
          return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
        } else if (activePeriod.value === 'weekly') {
          const weekNum = Math.ceil(date.getDate() / 7)
          return `${date.getMonth() + 1}月第${weekNum}周`
        } else {
          return `${date.getMonth() + 1}-${String(date.getDate()).padStart(2, '0')}`
        }
      }
      return dateStr
    })

    // 提取数据
    const volumeData = chartData.value.map(item => (item.volume || 0) / 1e8) // 转换为亿手
    const pctChgData = chartData.value.map(item => item.pct_chg || 0)
    
    // 计算成交量变化幅度
    const volumeChangeData = chartData.value.map((item, index) => {
      if (index === 0) return 0
      const prevVolume = chartData.value[index - 1].volume || 0
      return prevVolume > 0 ? ((item.volume - prevVolume) / prevVolume) * 100 : 0
    })

    // 根据主题设置样式
    const textColor = appStore.isDarkMode ? '#ffffff' : '#333333'
    const tooltipBgColor = appStore.isDarkMode ? 'rgba(0,0,0,0.8)' : 'rgba(255,255,255,0.9)'
    const axisLineColor = appStore.isDarkMode ? '#555555' : '#cccccc'
    const gridLineColor = appStore.isDarkMode ? '#333333' : '#f0f0f0'
    
    // 设置图表选项
    const option = {
      backgroundColor: 'transparent',
      animation: false,
      legend: {
        data: getMAConfig().map(ma => ma.name),
        textStyle: {
          color: textColor
        },
        selected: Object.fromEntries(getMAConfig().map(ma => [ma.name, true]))
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          animation: false,
          label: {
            backgroundColor: '#505765'
          }
        },
        backgroundColor: tooltipBgColor,
        borderColor: appStore.isDarkMode ? '#555555' : '#cccccc',
        borderWidth: 1,
        textStyle: {
          color: textColor
        },
        formatter: (params: any[]) => {
          const date = params[0].axisValue
          const dataIndex = params[0].dataIndex // 使用dataIndex直接访问数据
          const candleItem = params.find(item => item.seriesName === 'K线')
          
          // 动态获取当前时间粒度下的移动平均线项
          const maItems = getMAConfig().map(ma => ({
            config: ma,
            item: params.find(item => item.seriesName === ma.name)
          }))
          const volumeItem = params.find(item => item.seriesName === '成交量')
          const pctChgItem = params.find(item => item.seriesName === '涨跌幅')
          const volumeChangeItem = params.find(item => item.seriesName === '量比变化')
          
          let result = `<div style="font-weight: bold">${date}</div>`
          
          if (dataIndex >= 0 && dataIndex < chartData.value.length) {
            // 直接使用dataIndex访问原始数据
            const originalData = chartData.value[dataIndex]
            
            if (originalData) {
              result += `
                <div>开盘：${originalData.open.toFixed(2)}</div>
                <div>收盘：${originalData.close.toFixed(2)}</div>
                <div>最高：${originalData.high.toFixed(2)}</div>
                <div>最低：${originalData.low.toFixed(2)}</div>
                <div>涨跌幅：${originalData.pct_chg >= 0 ? '+' : ''}${originalData.pct_chg.toFixed(2)}%</div>
              `
              
              // 添加移动平均线数据
              const maColors = ['#5470c6', '#91cc75', '#fac858']
              maItems.forEach((ma, index) => {
                if (ma.item && ma.item.value !== undefined && ma.item.value !== null && typeof ma.item.value === 'number') {
                  result += `<div style="color: ${maColors[index % maColors.length]}">${ma.config.name}：${ma.item.value.toFixed(2)}</div>`
                }
              })
            }
          } else if (candleItem) {
            // 回退到使用K线图数据点
            const data = candleItem.data
            result += `
              <div>开盘：${data[0]}</div>
              <div>收盘：${data[1]}</div>
              <div>最高：${data[2]}</div>
              <div>最低：${data[3]}</div>
            `
          }
          
          if (volumeItem) {
            result += `<div>成交量：${volumeItem.value.toFixed(2)}亿手</div>`
          }
          
          if (pctChgItem) {
            const value = pctChgItem.value
            const color = value >= 0 ? '#ff4d4f' : '#52c41a'
            const sign = value >= 0 ? '+' : ''
            result += `<div style="color: ${color}">涨跌幅：${sign}${value.toFixed(2)}%</div>`
          }
          
          if (volumeChangeItem) {
            const value = volumeChangeItem.value
            const color = value >= 0 ? '#ff4d4f' : '#52c41a'
            const sign = value >= 0 ? '+' : ''
            result += `<div style="color: ${color}">量比变化：${sign}${value.toFixed(2)}%</div>`
          }
          
          return result
        }
      },
      axisPointer: {
        link: { xAxisIndex: 'all' },
        label: {
          backgroundColor: '#777'
        }
      },
      grid: [
        {
          left: '3%',
          right: '3%',
          top: '8%',
          height: '50%'
        },
        {
          left: '3%',
          right: '3%',
          top: '65%',
          height: '15%'
        },
        {
          left: '3%',
          right: '3%',
          top: '85%',
          height: '10%'
        }
      ],
      xAxis: [{
        type: 'category',
        data: dates,
        scale: true,
        boundaryGap: true,
        axisLine: { onZero: false },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax',
        axisLabel: {
          color: textColor
        }
      }, {
        type: 'category',
        gridIndex: 1,
        data: dates,
        scale: true,
        boundaryGap: true,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      }, {
        type: 'category',
        gridIndex: 2,
        data: dates,
        scale: true,
        boundaryGap: true,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      }],
      yAxis: [{
        scale: true,
        splitArea: {
          show: true,
          areaStyle: {
            color: ['transparent', 'transparent']
          }
        },
        axisLabel: {
          color: textColor
        }
      }, {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false }
      }, {
        scale: true,
        gridIndex: 2,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false }
      }],
      dataZoom: [{
        type: 'inside',
        xAxisIndex: [0, 1, 2],
        start: 0,
        end: 100
      }, {
        show: true,
        xAxisIndex: [0, 1, 2],
        type: 'slider',
        top: '95%',
        start: 0,
        end: 100
      }],
      series: [{
        name: 'K线',
        type: 'candlestick',
        showSymbol: false,
        showInLegend: false,  // 不在图例中显示
        data: chartData.value.map(item => [
          item.open,
          item.close,
          item.low,
          item.high
        ]),
        itemStyle: {
          // 涨为红色，跌为绿色
          color: '#ff4d4f',  // 阳线（收盘价 > 开盘价）填充色
          color0: '#52c41a', // 阴线（收盘价 < 开盘价）填充色
          borderColor: '#ff4d4f',  // 阳线边框色
          borderColor0: '#52c41a'  // 阴线边框色
        }
      },
      // 动态生成移动平均线系列
      ...getMAConfig().map(ma => ({
        name: ma.name,
        type: 'line',
        data: calculateMA(ma.days, chartData.value),
        smooth: true,
        lineStyle: {
          opacity: 0.5
        }
      })), {
        
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumeData,
        itemStyle: {
          color: (params: any) => {
            const item = chartData.value[params.dataIndex]
            // 涨为红色，跌为绿色
            return item.close >= item.open ? '#ff4d4f' : '#52c41a'
          }
        }
      }, {
        name: '涨跌幅',
        type: 'line',
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: pctChgData,
        lineStyle: {
          color: '#5470c6',
          width: 1
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
            offset: 0,
            color: 'rgba(84,112,198,0.3)'
          }, {
            offset: 1,
            color: 'rgba(84,112,198,0.1)'
          }])
        }
      }, {
        name: '量比变化',
        type: 'line',
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: volumeChangeData,
        lineStyle: {
          color: '#91cc75',
          width: 1
        }
      }]
    }
    
    chart.setOption(option)
  } catch (error) {
  }
}

// 初始化组件
onMounted(async () => {
  try {
    await loadIndexData()
  } catch (error) {
    console.error('初始化组件时加载数据失败:', error)
  }
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
  
  // 延迟一点时间确保DOM已渲染
  setTimeout(() => {
    observeChartContainer()
  }, 200)
})

// 清理
onUnmounted(() => {
  componentUnmounted.value = true
  safeDisposeChart()
  window.removeEventListener('resize', handleResize)
  
  // 停止观察
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
})

// 处理窗口大小变化
const handleResize = () => {
  if (chartInstance.value) {
    chartInstance.value.resize()
  }
}

// 容器大小变化观察器
let resizeObserver: ResizeObserver | null = null

// 监听容器大小变化
const observeChartContainer = () => {
  if (!chartContainer.value) return
  
  // 创建ResizeObserver实例
  resizeObserver = new ResizeObserver(entries => {
    if (chartInstance.value) {
      chartInstance.value.resize()
    }
  })
  
  // 开始观察
  resizeObserver.observe(chartContainer.value)
}

// 监听主题变化，重新渲染图表
watch(() => appStore.isDarkMode, async () => {
  await nextTick()
  if (chartContainer.value && chartData.value.length > 0) {
    initChart()
  }
})

// 防止并发加载
const isLoading = ref(false)

// 处理指数切换
const onIndexChange = async (code: string | number | boolean | undefined) => {
  if (typeof code === 'string' && !isLoading.value) {
    isLoading.value = true
    try {
      selectedIndex.value = code
      emit('update:selected-index', code)
      await loadIndexData()
    } finally {
      isLoading.value = false
    }
  }
}
</script>

<style scoped>
.main-indices-panel {
  display: flex;
  flex-direction: column;
  background-color: var(--bg-content);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md);
  box-shadow: var(--shadow-sm);
  height: 100%;
  min-height: 500px;
}

.panel-header {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.panel-title-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
  gap: var(--spacing-lg);
}

.panel-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

@media (min-width: 768px) {
  .panel-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

.index-selector {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.index-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.index-name {
  font-size: 14px;
  font-weight: 500;
}

.index-price {
  font-size: 13px;
  
  &.price-up {
    color: var(--el-color-danger);
  }
  
  &.price-down {
    color: var(--el-color-success);
  }
  
  &.price-hidden {
    display: none;
  }
}

.time-control {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  align-items: center;
}

.date-picker-wrapper,
.data-points-wrapper {
  display: contents;
}

.date-picker {
  width: 260px;
  margin-left: var(--spacing-sm);
}

.data-points-select {
  width: 120px;
  margin-left: var(--spacing-sm);
}

.panel-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chart-container {
  flex: 1;
  min-height: 450px;
  position: relative;
  width: 100%;
  background: transparent;
  overflow: hidden;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.7);
  z-index: 10;
}

:deep(.dark) .loading-overlay {
  background-color: rgba(0, 0, 0, 0.7);
}

.loading-icon {
  font-size: 24px;
  animation: spin 1s linear infinite;
}

.loading-text {
  margin-top: var(--spacing-sm);
  color: var(--text-secondary);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.legend-section {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm);
  border-top: 1px solid var(--border-color);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 12px;
  color: var(--text-secondary);
}

.legend-line {
  display: inline-block;
  width: 16px;
  height: 2px;
}

.line-primary {
  background-color: var(--accent-primary);
}

.line-secondary {
  background-color: var(--accent-secondary);
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .main-indices-panel {
    padding: var(--spacing-sm);
  }

  .panel-header {
    flex-direction: column;
    align-items: stretch;
  }

  .index-selector,
  .time-control {
    width: 100%;
    justify-content: center;
  }

  .legend-section {
    flex-direction: column;
    align-items: center;
  }
}
</style>