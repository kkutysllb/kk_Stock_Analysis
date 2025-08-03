<template>
  <div class="component-indices-panel">
    <!-- 指数选择器 -->
    <div class="panel-header">
      <div class="panel-title-section">
        <h3 class="panel-title">成份指数分析</h3>
        <AskAIComponent :data-context="aiDataContext" />
      </div>
      <div class="index-selector">
        <el-radio-group v-model="selectedIndex" @change="onIndexChange" size="default">
          <el-radio-button v-for="index in indexConfig" :key="index.code" :value="index.code">
            <span class="index-content">
              <span class="index-name">{{ index.name }}</span>
              <span 
                v-if="indexDataMap[index.code]?.latest_data" 
                class="index-price"
                :class="{ 
                  'price-up': (indexDataMap[index.code]?.latest_data?.pct_chg || 0) > 0,
                  'price-down': (indexDataMap[index.code]?.latest_data?.pct_chg || 0) < 0 
                }"
              >
                {{ indexDataMap[index.code]?.latest_data?.close?.toFixed(2) }}
                <span class="price-change">
                  {{ (indexDataMap[index.code]?.latest_data?.pct_chg || 0) > 0 ? '+' : '' }}
                  {{ indexDataMap[index.code]?.latest_data?.pct_chg?.toFixed(2) }}%
                </span>
              </span>
            </span>
          </el-radio-button>
        </el-radio-group>
      </div>
      
      <div class="time-control">
        <el-radio-group v-model="activePeriod" @change="onPeriodChange" size="default">
          <el-radio-button value="daily">日线</el-radio-button>
          <el-radio-button value="weekly">周线</el-radio-button>
          <el-radio-button value="monthly">月线</el-radio-button>
          <el-radio-button value="custom">自定义</el-radio-button>
        </el-radio-group>
        
        <el-date-picker
          v-if="activePeriod === 'custom'"
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
        
        <el-select 
          v-else
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
    
    <div class="panel-body">
      <div class="chart-container" ref="chartContainer">
        <div v-if="loading" class="loading-overlay">
          <el-icon class="loading-icon"><Loading /></el-icon>
          <span class="loading-text">加载中...</span>
        </div>
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
import AskAIComponent from './AskAIComponent.vue'
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

// 定义props
interface Props {
  initialIndex?: string
  initialPeriod?: 'daily' | 'weekly' | 'monthly' | 'custom'
}

const props = withDefaults(defineProps<Props>(), {
  initialIndex: '000016.SH',  // 默认为上证50
  initialPeriod: 'daily'
})

// 定义emit
const emit = defineEmits<{
  'update:selected-index': [code: string]
  'update:active-period': [period: string]
}>()

// 获取应用状态
const appStore = useAppStore()

// 成份指数配置
const indexConfig = [
  { code: '000016.SH', name: '上证50', color: '#3b82f6' },
  { code: '000300.SH', name: '沪深300', color: '#10b981' },
  { code: '000905.SH', name: '中证500', color: '#f59e0b' },
  { code: '000852.SH', name: '中证1000', color: '#ef4444' },
  { code: '399303.SZ', name: '国证2000', color: '#8b5cf6' }
]

// 定义类型
type PeriodType = 'daily' | 'weekly' | 'monthly' | 'custom'

// 响应式数据
const selectedIndex = ref(props.initialIndex)
const activePeriod = ref<PeriodType>(props.initialPeriod)
const dateRange = ref<[DateModelType, DateModelType] | undefined>()
const dataPoints = ref('60')
const loading = ref(false)
const chartContainer = ref<HTMLElement | null>(null)
const chartInstance = ref<echarts.ECharts | null>(null)
const chartData = ref<any[]>([])
const indexLatestData = ref<any>(null)
const indexDataMap = ref<Record<string, any>>({})
const componentUnmounted = ref(false)

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
    text: '最近一个月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 1)
      return [start, end]
    }
  },
  {
    text: '最近三个月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 3)
      return [start, end]
    }
  }
]

// 加载所有指数的最新数据
const loadAllIndexData = async () => {
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
  }
}

// 获取指定指数的最新数据
const getIndexLatestData = (code: string) => {
  return indexDataMap.value[code]?.latest_data
}

// AI数据上下文
const aiDataContext = computed(() => {
  const currentIndexConfig = indexConfig.find(idx => idx.code === selectedIndex.value)
  
  // 数据一致性检查：确保chartData确实是当前选中指数的数据
  let currentIndexData = null
  let validChartData = []
  
  if (chartData.value.length > 0) {
    // 检查chartData中的数据是否匹配当前选中的指数
    // 由于chartData是通过selectedIndex.value加载的，理论上应该匹配
    // 但为了确保数据一致性，我们进行额外检查
    const firstDataPoint = chartData.value[0]
    const lastDataPoint = chartData.value[chartData.value.length - 1]
    
    // 检查数据是否为当前选中指数的数据
    // 注意：有些数据可能没有ts_code字段，这种情况下认为数据是匹配的
    const hasValidTsCode = firstDataPoint.ts_code || lastDataPoint.ts_code
    const isDataMatching = !hasValidTsCode || 
                          firstDataPoint.ts_code === selectedIndex.value || 
                          lastDataPoint.ts_code === selectedIndex.value ||
                          chartData.value.some(item => item.ts_code === selectedIndex.value)
    
    if (isDataMatching) {
      // 数据匹配，使用chartData中的数据
      validChartData = chartData.value
      const latest = chartData.value[chartData.value.length - 1]
      currentIndexData = {
        close: latest.close,
        pct_chg: latest.pct_chg,
        vol: latest.vol,
        amount: latest.amount,
        trade_date: latest.trade_date
      }
    } else {
      // 数据不匹配，使用indexDataMap中的数据并清空chartData
      console.warn(`chartData数据与当前选中指数(${selectedIndex.value})不匹配，使用indexDataMap数据`)
      validChartData = []
      currentIndexData = getIndexLatestData(selectedIndex.value)
    }
  } else {
    // 如果chartData为空，则从indexDataMap获取
    validChartData = []
    currentIndexData = getIndexLatestData(selectedIndex.value)
  }
  // 根据用户设置的数据点数量传递给AI，确保AI分析的数据量与用户查看的一致
  const dataPointsNum = parseInt(dataPoints.value) || 60
  const recentChartData = validChartData.slice(-dataPointsNum) // 根据用户设置的数据点数量
  
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
  
  const stats = getHistoricalStats(validChartData)
  
  let summary = ''
  if (currentIndexData) {
    const pctChg = currentIndexData.pct_chg || 0
    const trend = pctChg > 0 ? '上涨' : pctChg < 0 ? '下跌' : '平盘'
    summary = `成份指数分析完整数据：

【重要提示：当前分析对象是 ${currentIndexConfig?.name}（${selectedIndex.value}），请确保所有分析都基于此指数数据】

## 当前指数信息
- 指数名称：${currentIndexConfig?.name || '未知'}
- 指数代码：${selectedIndex.value}
- 当前收盘价：${currentIndexData.close?.toFixed(2)}
- 涨跌幅：${trend}${Math.abs(pctChg).toFixed(2)}%
- 成交量：${(currentIndexData.vol || 0).toLocaleString()}万手
- 成交额：${(currentIndexData.amount || 0).toLocaleString()}万元

## 历史数据统计
${stats ? `- 数据点数：${stats.count}个
- 最高价：${stats.max.toFixed(2)}
- 最低价：${stats.min.toFixed(2)}
- 平均价：${stats.avg.toFixed(2)}
- 中位数：${stats.median.toFixed(2)}
- 整体趋势：${stats.trend > 0 ? '上升' : stats.trend < 0 ? '下降' : '平稳'}（${stats.trend.toFixed(2)}%）
- 价格波动率：${stats.volatility.toFixed(2)}` : '- 暂无历史统计数据'}

## 最近交易数据（${currentIndexConfig?.name}）
${recentChartData.map(item => 
  `${item.trade_date}: 收盘${item.close?.toFixed(2)}, 涨跌幅${(item.pct_chg || 0).toFixed(2)}%, 成交量${(item.vol || 0).toLocaleString()}万手`
).join('\n')}

## 其他指数对比
${Object.entries(indexDataMap.value).map(([code, data]) => {
  const latestData = data.latest_data
  if (!latestData || code === selectedIndex.value) return null
  const pctChg = latestData.pct_chg || 0
  const trend = pctChg > 0 ? '上涨' : pctChg < 0 ? '下跌' : '平盘'
  return `- ${data.name}(${code}): ${latestData.close?.toFixed(2)}, ${trend}${Math.abs(pctChg).toFixed(2)}%`
}).filter(Boolean).join('\n')}

## 分析要点
- 分析对象：${currentIndexConfig?.name}（${selectedIndex.value}）
- 周期类型：${activePeriod.value === 'daily' ? '日线' : activePeriod.value === 'weekly' ? '周线' : activePeriod.value === 'monthly' ? '月线' : '自定义周期'}
- 数据范围：${activePeriod.value === 'custom' && dateRange.value ? `${dateRange.value[0]} 至 ${dateRange.value[1]}` : `最近${dataPoints.value}个交易日`}
- 指数特征：${currentIndexConfig?.name}作为成份指数，反映相关成份股的整体表现
- 技术指标：请结合价格走势、成交量变化、涨跌幅分布等进行综合分析

请基于以上完整的${currentIndexConfig?.name}（${selectedIndex.value}）数据进行深入分析，提供投资建议、风险提示和市场前景判断。

【再次提醒：本次分析的重点对象是 ${currentIndexConfig?.name}，代码 ${selectedIndex.value}，请勿混淆其他指数】`
  } else {
    summary = `成份指数分析：

## 当前指数信息
- 指数名称：${currentIndexConfig?.name || '未知'}
- 指数代码：${selectedIndex.value}
- 数据状态：正在加载中...

## 分析设置
- 周期类型：${activePeriod.value === 'daily' ? '日线' : activePeriod.value === 'weekly' ? '周线' : activePeriod.value === 'monthly' ? '月线' : '自定义周期'}
- 数据范围：${activePeriod.value === 'custom' && dateRange.value ? `${dateRange.value[0]} 至 ${dateRange.value[1]}` : `最近${dataPoints.value}个交易日`}

请等待数据加载完成后进行分析。`
  }
  
  return {
    type: 'component_index',
    name: `${currentIndexConfig?.name || '成份指数'}(${selectedIndex.value})`, // 这个name字段用于AI组件检测数据变化
    title: '成份指数分析',
    selectedIndex: selectedIndex.value,
    indexName: currentIndexConfig?.name || '',
    period: activePeriod.value,
    dataPoints: dataPoints.value,
    latestData: currentIndexData,
    recentData: recentChartData,
    allIndicesData: Object.entries(indexDataMap.value).map(([code, data]) => ({
      code,
      name: data.name,
      latestData: data.latest_data
    })),
    statistics: stats,
    summary: summary,
    data: {
      selectedIndex: selectedIndex.value,
      selectedIndexName: currentIndexConfig?.name || '',
      period: activePeriod.value,
      dataPoints: dataPoints.value
    }
  }
})

// 监听属性变化
watch(() => props.initialIndex, async (newVal) => {
  if (componentUnmounted.value) return
  selectedIndex.value = newVal
  await nextTick()
  if (!componentUnmounted.value) {
    loadIndexData()
  }
})

watch(() => props.initialPeriod, async (newVal) => {
  if (componentUnmounted.value) return
  activePeriod.value = newVal as PeriodType
  await nextTick()
  if (!componentUnmounted.value) {
    loadIndexData()
  }
})

// 监听周期变化时重新加载所有数据
watch([activePeriod, dataPoints], async () => {
  if (componentUnmounted.value) return
  try {
    await loadAllIndexData()
  } catch (error) {
    console.error('重新加载指数数据失败:', error)
  }
})

// 事件处理函数
const onIndexChange = async (value: string | number | boolean | undefined) => {
  const stringValue = String(value)
  emit('update:selected-index', stringValue)
  try {
    await loadIndexData()
  } catch (error) {
    console.error('切换指数时加载数据失败:', error)
  }
}

const onPeriodChange = async (value: string | number | boolean | undefined) => {
  const periodValue = String(value) as PeriodType
  emit('update:active-period', periodValue)
  
  // 使用nextTick确保DOM更新完成，并添加安全检查
  await nextTick()
  
  // 验证组件是否仍然挂载且DOM元素有效
  if (!chartContainer.value || !chartContainer.value.parentNode) {
    return
  }
  
  try {
    await loadIndexData()
  } catch (error) {
    console.error('周期改变时加载数据失败:', error)
  }
}

const onDateRangeChange = async () => {
  try {
    await loadIndexData()
  } catch (error) {
    console.error('日期范围改变时加载数据失败:', error)
  }
}

const onDataPointsChange = async () => {
  try {
    await loadIndexData()
  } catch (error) {
    console.error('数据点数改变时加载数据失败:', error)
  }
}

// 加载指数数据
const loadIndexData = async () => {
  if (!selectedIndex.value || componentUnmounted.value) return
  
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
      
      response = await marketAPI.getIndexKline(
        selectedIndex.value,
        period,
        parseInt(dataPoints.value)
      )
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
      if (isDataEmpty) {
        // console.log(`${selectedIndex.value}数据为空`)
      }
      
      // 计算环比涨跌幅
      const calculatePeriodChange = (data: any[], index: number) => {
        if (index <= 0 || !data[index - 1]) return 0
        const currentClose = parseFloat(String(data[index].close)) || 0
        const prevClose = parseFloat(String(data[index - 1].close)) || 0
        if (prevClose === 0) return 0
        return ((currentClose - prevClose) / prevClose) * 100
      }
      
      // 检查组件是否已卸载
      if (componentUnmounted.value) return
      
      // 处理数据，确保所有必要的字段都存在
      chartData.value = sortedData.map((item, index) => {
        // 确保数值字段是数字类型
        const open = parseFloat(String(item.open)) || 0
        const close = parseFloat(String(item.close)) || 0
        const high = parseFloat(String(item.high)) || 0
        const low = parseFloat(String(item.low)) || 0
        const vol = parseFloat(String(item.vol)) || 0
        const amount = parseFloat(String(item.amount)) || 0
        
        // 计算涨跌幅，如果API没有提供，则自行计算
        let pct_chg = parseFloat(String(item.pct_chg))
        if (isNaN(pct_chg)) {
          // 如果是第一条数据或者前一条的收盘价为0，则涨跌幅为0
          if (index === 0 || parseFloat(String(sortedData[index - 1].close)) === 0) {
            pct_chg = 0
          } else {
            // 否则计算涨跌幅
            const prevClose = parseFloat(String(sortedData[index - 1].close))
            pct_chg = ((close - prevClose) / prevClose) * 100
          }
        }
        
        // 计算当前周期相对上一周期的涨跌幅
        const periodChange = calculatePeriodChange(sortedData, index)
        
        return {
          ...item,
          open,
          close,
          high,
          low,
          vol,
          amount,
          pct_chg,
          period_change: periodChange
        }
      })
      
      // 获取最新数据用于显示
      if (chartData.value.length > 0 && !componentUnmounted.value) {
        const latest = chartData.value[chartData.value.length - 1]
        indexLatestData.value = {
          trade_date: latest.trade_date,
          close: latest.close,
          pct_chg: latest.pct_chg,
          period_change: latest.period_change
        }
      }
      
      // 初始化图表
      await nextTick()
      // 验证DOM元素是否仍然有效且组件未卸载
      if (chartContainer.value && chartContainer.value.parentNode && !componentUnmounted.value) {
        initChart()
      }
    } else {
      console.error('获取指数数据失败:', response.message)
    }
  } catch (error) {
    console.error('加载指数数据出错:', error)
  } finally {
    if (!componentUnmounted.value) {
      loading.value = false
    }
  }
}

// 计算移动平均线
const calculateMA = (dayCount: number, data: any[]) => {
  const result: (number | string)[] = []
  for (let i = 0; i < data.length; i++) {
    if (i < dayCount - 1) {
      result.push('-')
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
    
    // 准备日期数据
    const dates = chartData.value.map(item => {
      // 格式化日期
      const dateStr = item.trade_date
      if (dateStr.length === 8) {
        // 如果是YYYYMMDD格式，转换为YYYY-MM-DD
        return `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`
      }
      return dateStr
    })
    
    // 准备成交量数据和颜色
    const volumeData = chartData.value.map((item, index) => {
      return [index, item.vol, item.close > item.open ? 1 : -1]
    })
    
    const volumeColor = (params: any) => {
      return params.data[2] > 0 ? '#ef4444' : '#10b981'
    }
    
    // 准备涨跌幅数据
    const changeData = chartData.value.map((item, index) => {
      return item.pct_chg
    })
    
    // 准备量比变化数据
    const volChangeData = chartData.value.map((item, index) => {
      if (index === 0 || !chartData.value[index - 1] || chartData.value[index - 1].vol === 0) {
        return 0
      }
      return ((item.vol - chartData.value[index - 1].vol) / chartData.value[index - 1].vol) * 100
    })
    
    // 颜色配置
    const maColors = ['#5470c6', '#91cc75', '#fac858']
  
    // 图表配置
    const option = {
    backgroundColor: 'transparent',
    animation: false,
    legend: {
      data: getMAConfig().map(ma => ma.name),
      textStyle: {
        color: appStore.isDarkMode ? '#ffffff' : '#333333'
      },
      left: 'center',
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
      backgroundColor: appStore.isDarkMode ? 'rgba(0,0,0,0.8)' : 'rgba(255,255,255,0.9)',
      borderColor: appStore.isDarkMode ? '#555555' : '#cccccc',
      borderWidth: 1,
      textStyle: {
        color: appStore.isDarkMode ? '#ffffff' : '#333333'
      },
      formatter: (params: any[]) => {
        const date = params[0].axisValue
        const dataIndex = params[0].dataIndex
        const candleItem = params.find(item => item.seriesName === 'K线')
        
        // 动态获取当前时间粒度下的移动平均线项
        const maItems = getMAConfig().map(ma => ({
          config: ma,
          item: params.find(item => item.seriesName === ma.name)
        }))
        const volumeItem = params.find(item => item.seriesName === '成交量')
        const pctChgItem = params.find(item => item.seriesName === '涨跌幅')
        
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
              <div>成交量：${(originalData.vol / 10000).toFixed(2)}万手</div>
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
        
        return result
      }
    },
    axisPointer: {
      link: { xAxisIndex: 'all' },
      label: { backgroundColor: '#777' }
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
    xAxis: [
      {
        type: 'category',
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      },
      {
        type: 'category',
        gridIndex: 1,
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      },
      {
        type: 'category',
        gridIndex: 2,
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      }
    ],
    yAxis: [
      {
        scale: true,
        splitArea: {
          show: true,
          areaStyle: {
            color: ['transparent', 'transparent']
          }
        }
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false }
      },
      {
        scale: true,
        gridIndex: 2,
        splitNumber: 2,
        axisLabel: { show: true },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1, 2],
        start: 0,
        end: 100
      },
      {
        show: true,
        xAxisIndex: [0, 1, 2],
        type: 'slider',
        bottom: '0%',
        start: 0,
        end: 100
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        showSymbol: false,
        showInLegend: false,
        data: chartData.value.map(item => [item.open, item.close, item.low, item.high]),
        itemStyle: { color: '#ff4d4f', color0: '#52c41a', borderColor: '#ff4d4f', borderColor0: '#52c41a' }
      },
      ...getMAConfig().map(ma => ({
        name: ma.name,
        type: 'line',
        data: calculateMA(ma.days, chartData.value),
        smooth: true,
        lineStyle: { opacity: 0.5 }
      })),
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumeData,
        itemStyle: { color: volumeColor }
      },
      {
        name: '涨跌幅',
        type: 'line',
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: changeData,
        showSymbol: false,
        lineStyle: { width: 1 },
        itemStyle: {
          color: (params: any) => {
            const value = params.data
            return value >= 0 ? '#ff4d4f' : '#52c41a'
          }
        },
        areaStyle: {
          color: (params: any) => {
            const value = params.data
            return value >= 0 ? 'rgba(255, 77, 79, 0.2)' : 'rgba(82, 196, 26, 0.2)'
          }
        }
      }
    ]
  }
  
    // 设置图表选项
    chart.setOption(option, true) // 使用true参数强制清除之前的实例配置

  } catch (error) {
    console.error('设置图表选项失败:', error)
  }
  
  // 监听窗口大小变化，调整图表大小
  window.removeEventListener('resize', handleResize) // 先移除可能存在的事件监听
  window.addEventListener('resize', handleResize)
}

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

// 组件挂载时加载数据
onMounted(async () => {
  try {
    await loadAllIndexData()
    await loadIndexData()
  } catch (error) {
    console.error('组件挂载时加载数据失败:', error)
  }
  
  // 添加窗口resize事件监听
  window.addEventListener('resize', handleResize)
  
  // 延迟一点时间确保DOM已渲染
  setTimeout(() => {
    observeChartContainer()
  }, 200)
})

// 组件卸载时清理资源
onUnmounted(() => {
  componentUnmounted.value = true
  safeDisposeChart()
  
  // 移除事件监听
  window.removeEventListener('resize', handleResize)
  
  // 停止观察
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
})
</script>

<style scoped>
.component-indices-panel {
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
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
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
}

.price-change {
  font-size: 12px;
}

.time-control {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  align-items: center;
}

.date-picker {
  width: 260px;
  margin-left: var(--spacing-sm);
  
  :deep(.el-input__wrapper) {
    background: var(--el-bg-color);
    border-radius: 4px;
  }
}

.data-points-select {
  width: 120px;
  margin-left: var(--spacing-sm);
  
  :deep(.el-input__wrapper) {
    background: var(--el-bg-color);
    border-radius: 4px;
  }
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

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .component-indices-panel {
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
