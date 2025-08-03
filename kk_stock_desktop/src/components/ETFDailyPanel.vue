<template>
  <div class="etf-daily-panel" v-if="isMounted">
    <div class="panel-header">
      <!-- 面板标题和AI按钮 -->
      <div class="panel-title-section">
        <h3 class="panel-title">ETF数据</h3>
        <AskAIComponent :data-context="aiDataContext" />
      </div>
      
      <!-- ETF选择器 -->
      <div class="etf-selector">
        <el-select
          v-model="selectedETF"
          @change="onETFChange"
          size="default"
          :placeholder="loadingETFList ? '加载ETF列表中...' : '请选择ETF'"
          filterable
          :loading="loadingETFList"
          class="etf-select"
        >
          <el-option
            v-for="etf in etfList"
            :key="etf.code"
            :label="etf.name"
            :value="etf.code"
          >
            <div class="etf-option">
              <span>{{ etf.name }}</span>
              <span class="etf-code">{{ etf.code }}</span>
            </div>
          </el-option>
        </el-select>
      </div>
      
      <div class="period-selector">
        <el-radio-group v-model="activePeriod" @change="(val: string | number | boolean | undefined) => onPeriodChange(val as PeriodType)" size="default">
          <el-radio-button value="daily">日线</el-radio-button>
          <el-radio-button value="custom">自定义</el-radio-button>
        </el-radio-group>
        
        <el-date-picker
          v-if="activePeriod === 'custom'"
          v-model="dateRange as any"
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
          <span>价格走势</span>
        </div>
        <div class="legend-item">
          <span class="legend-line line-secondary"></span>
          <span>成交量（红涨绿跌）</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeMount, onMounted, onUnmounted, nextTick, watch, withDefaults, shallowRef } from 'vue'
import * as echarts from 'echarts'
import { useAppStore } from '../stores/app'
import { etfAPI } from '../api/etf'
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
  initialETF?: string
  initialPeriod?: 'daily' | 'custom'
}

// 定义emit
const emit = defineEmits<{
  'update:selected-etf': [code: string]
  'update:active-period': [period: string]
}>()

// 获取应用状态
const appStore = useAppStore()

// ETF配置 - 动态从后端获取
const etfList = ref<Array<{code: string, name: string, color: string}>>([])
const loadingETFList = ref(false)

const props = withDefaults(defineProps<Props>(), {
  initialETF: '',  // 空字符串，等ETF列表加载后自动选择
  initialPeriod: 'daily'
})

// 定义类型
type PeriodType = 'daily' | 'custom'

// 响应式数据
const selectedETF = ref(props.initialETF || '')
const activePeriod = ref<PeriodType>(props.initialPeriod || 'daily')
const dateRange = ref<[string, string] | null>(null)
const dataPoints = ref('60')
const loading = ref(false)
const chartContainer = ref<HTMLElement | null>(null)
const chartInstance = ref<echarts.ECharts | null>(null)
const resizeObserver = ref<ResizeObserver | null>(null)
const windowResizeHandler = ref<(() => void) | null>(null)
const chartData = shallowRef<any[]>([])
const etfLatestData = shallowRef<any>(null)
const componentUnmounted = ref(false)
const isMounted = ref(false)

// 初始化时立即设置状态
onBeforeMount(() => {
  componentUnmounted.value = false
})

// 计算属性：获取当前选中ETF的名称
const selectedETFName = computed(() => {
  const etf = etfList.value.find((item: {code: string, name: string, color: string}) => item.code === selectedETF.value)
  return etf ? etf.name : '请选择ETF'
})

// AI数据上下文
const aiDataContext = computed(() => {
  const currentETF = etfList.value.find(etf => etf.code === selectedETF.value)
  
  // 数据一致性检查：确保chartData确实是当前选中ETF的数据
  let latestData = null
  let validChartData = []
  
  if (chartData.value.length > 0) {
    // 检查chartData中的数据是否匹配当前选中的ETF
    // 由于chartData是通过selectedETF.value加载的，理论上应该匹配
    // 但为了确保数据一致性，我们进行额外检查
    const firstDataPoint = chartData.value[0]
    const lastDataPoint = chartData.value[chartData.value.length - 1]
    
    // 检查数据是否为当前选中ETF的数据
    // 注意：有些数据可能没有ts_code字段，这种情况下认为数据是匹配的
    const hasValidTsCode = firstDataPoint.ts_code || lastDataPoint.ts_code
    const isDataMatching = !hasValidTsCode || 
                          firstDataPoint.ts_code === selectedETF.value || 
                          lastDataPoint.ts_code === selectedETF.value ||
                          chartData.value.some((item: any) => item.ts_code === selectedETF.value)
    
    if (isDataMatching) {
      // 数据匹配，使用chartData中的数据
      validChartData = chartData.value
      const latest = chartData.value[chartData.value.length - 1]
      latestData = {
        close: latest.close,
        pct_chg: latest.pct_chg,
        vol: latest.volume,
        amount: latest.amount,
        trade_date: latest.date
      }
    } else {
      // 数据不匹配，使用etfLatestData并清空chartData
      console.warn(`chartData数据与当前选中ETF(${selectedETF.value})不匹配，使用etfLatestData数据`)
      validChartData = []
      latestData = etfLatestData.value
    }
  } else {
    // 如果chartData为空，则使用etfLatestData
    validChartData = []
    latestData = etfLatestData.value
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
  
  const stats = getHistoricalStats(validChartData)
  // 根据用户设置的数据点数量传递给AI，确保AI分析的数据量与用户查看的一致
  const dataPointsNum = parseInt(dataPoints.value) || 60
  const recentData = validChartData.slice(-dataPointsNum) // 根据用户设置的数据点数量
  
  let summary = ''
  if (latestData) {
    const pctChg = latestData.pct_chg || 0
    const trend = pctChg > 0 ? '上涨' : pctChg < 0 ? '下跌' : '平盘'
    summary = `ETF日线分析完整数据：

【重要提示：当前分析对象是 ${currentETF?.name}（${selectedETF.value}），请确保所有分析都基于此ETF数据】

## 当前ETF信息
- ETF名称：${currentETF?.name || '未知'}
- ETF代码：${selectedETF.value}
- 当前收盘价：${latestData.close?.toFixed(2)}
- 涨跌幅：${trend}${Math.abs(pctChg).toFixed(2)}%
- 成交量：${(latestData.vol || 0).toLocaleString()}万手
- 成交额：${(latestData.amount || 0).toLocaleString()}万元

## 历史数据统计
${stats ? `- 数据点数：${stats.count}个
- 最高价：${stats.max.toFixed(2)}
- 最低价：${stats.min.toFixed(2)}
- 平均价：${stats.avg.toFixed(2)}
- 中位数：${stats.median.toFixed(2)}
- 整体趋势：${stats.trend > 0 ? '上升' : stats.trend < 0 ? '下降' : '平稳'}（${stats.trend.toFixed(2)}%）
- 价格波动率：${stats.volatility.toFixed(2)}` : '- 暂无历史统计数据'}

## 最近交易数据（${currentETF?.name}）
${recentData.map((item: any) => 
  `${item.date}: 收盘${item.close?.toFixed(2)}, 涨跌幅${(item.pct_chg || 0).toFixed(2)}%, 成交量${(item.volume || 0).toLocaleString()}万手`
).join('\n')}

## 分析要点
- 分析对象：${currentETF?.name}（${selectedETF.value}）
- 周期类型：${activePeriod.value === 'daily' ? '日线' : '自定义周期'}
- 数据范围：${activePeriod.value === 'custom' && dateRange.value ? `${dateRange.value[0]} 至 ${dateRange.value[1]}` : `最近${dataPoints.value}个交易日`}
- ETF特征：${currentETF?.name}作为交易型开放式指数基金，跟踪相关指数表现
- 技术指标：请结合价格走势、成交量变化、涨跌幅分布等进行综合分析

请基于以上完整的${currentETF?.name}数据进行深入分析，提供投资建议、风险提示和市场前景判断。

【再次提醒：本次分析的重点对象是 ${currentETF?.name}，代码 ${selectedETF.value}，请勿混淆其他ETF】`
  } else {
    summary = `ETF日线分析：

## 当前ETF信息
- ETF名称：${currentETF?.name || '未知'}
- ETF代码：${selectedETF.value}
- 数据状态：正在加载中...

## 分析设置
- 周期类型：${activePeriod.value === 'daily' ? '日线' : '自定义周期'}
- 数据范围：${activePeriod.value === 'custom' && dateRange.value ? `${dateRange.value[0]} 至 ${dateRange.value[1]}` : `最近${dataPoints.value}个交易日`}

请等待数据加载完成后进行分析。`
  }
  
  return {
    type: 'etf_daily',
    name: `${currentETF?.name || 'ETF'}(${selectedETF.value})`, // 这个name字段用于AI组件检测数据变化
    title: 'ETF日线分析',
    selectedETF: selectedETF.value,
    etfName: currentETF?.name || '',
    period: activePeriod.value,
    dataPoints: dataPoints.value,
    latestData: latestData,
    recentData: recentData,
    statistics: stats,
    summary: summary,
    data: {
      selectedETF: selectedETF.value,
      selectedETFName: currentETF?.name || '',
      period: activePeriod.value,
      dataPoints: dataPoints.value
    }
  }
})

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

// 监听属性变化
watch(() => props.initialETF, (newVal: string | undefined, oldVal: string | undefined) => {
  if (componentUnmounted.value || !isMounted.value) return
  selectedETF.value = newVal || ''
  if (!componentUnmounted.value && isMounted.value) {
    loadETFData()
  }
})

watch(() => props.initialPeriod, (newVal: 'daily' | 'custom' | undefined, oldVal: 'daily' | 'custom' | undefined) => {
  if (componentUnmounted.value || !isMounted.value) return
  activePeriod.value = (newVal as PeriodType) || 'daily'
  if (!componentUnmounted.value && isMounted.value) {
    loadETFData()
  }
})

// 事件处理函数
const onETFChange = (value: string) => {
  emit('update:selected-etf', value)
  loadETFData()
}

const onPeriodChange = (value: PeriodType) => {
  emit('update:active-period', value)
  loadETFData()
}

const onDateRangeChange = () => {
  loadETFData()
}

const onDataPointsChange = () => {
  loadETFData()
}

// 加载ETF列表
const loadETFList = async () => {
  if (loadingETFList.value) return
  
  loadingETFList.value = true
  
  try {
    // console.log('开始加载ETF列表...')
    
    // 从后端API获取ETF列表
    const response = await etfAPI.getETFList({
      limit: 200  // 获取足够多的ETF
    })
    
    if (response.success && response.data && response.data.etf_list) {
      // console.log('获取到ETF列表:', response.data.etf_list)
      
      // 预定义颜色数组
      const colors = [
        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', 
        '#ec4899', '#14b8a6', '#6366f1', '#d946ef', '#f97316',
        '#22c55e', '#64748b', '#0ea5e9', '#eab308', '#a855f7',
        '#06b6d4', '#94a3b8', '#f43f5e', '#10b981', '#6366f1'
      ]
      
      // 转换数据格式
      etfList.value = response.data.etf_list.map((etf: any, index: number) => ({
        code: etf.ts_code,
        name: etf.name || etf.cname || etf.csname || `ETF-${etf.ts_code}`,
        color: colors[index % colors.length]
      }))
      
      // console.log(`成功加载 ${etfList.value.length} 个ETF`)
      
      // 如果当前选中的ETF不在列表中或为空，选择第一个
      if (etfList.value.length > 0) {
        const currentETFExists = selectedETF.value && etfList.value.some(etf => etf.code === selectedETF.value)
        if (!currentETFExists) {
          selectedETF.value = etfList.value[0].code
          // console.log(`当前ETF不存在或为空，切换到: ${selectedETF.value}`)
        }
      }
    } else {
      console.error('获取ETF列表失败:', response.message || '未知错误')
      // 使用默认的ETF列表作为备选
      etfList.value = [
        { code: '510300.SH', name: '沪深300ETF', color: '#3b82f6' },
        { code: '510500.SH', name: '中证500ETF', color: '#10b981' },
        { code: '159919.SZ', name: '沪深300ETF', color: '#f59e0b' },
        { code: '159995.SZ', name: '芯片ETF', color: '#ef4444' }
      ]
      // 自动选择第一个ETF
      if (etfList.value.length > 0 && !selectedETF.value) {
        selectedETF.value = etfList.value[0].code
      }
      // console.log('使用默认ETF列表')
    }
  } catch (error) {
    console.error('加载ETF列表出错:', error)
    // 使用默认的ETF列表作为备选
    etfList.value = [
      { code: '510300.SH', name: '沪深300ETF', color: '#3b82f6' },
      { code: '510500.SH', name: '中证500ETF', color: '#10b981' },
      { code: '159919.SZ', name: '沪深300ETF', color: '#f59e0b' },
      { code: '159995.SZ', name: '芯片ETF', color: '#ef4444' }
    ]
    // 自动选择第一个ETF
    if (etfList.value.length > 0 && !selectedETF.value) {
      selectedETF.value = etfList.value[0].code
    }
    // console.log('出错后使用默认ETF列表')
  } finally {
    loadingETFList.value = false
  }
}

// 加载ETF数据
const loadETFData = async () => {
  // 检查组件状态
  if (!selectedETF.value || componentUnmounted.value || !isMounted.value) {
    console.warn('组件未就绪或已卸载，跳过ETF数据加载')
    return
  }
  
  // 检查DOM容器是否存在
  if (!chartContainer.value) {
    console.warn('图表容器不存在，延迟加载数据')
    await nextTick()
    if (!chartContainer.value || componentUnmounted.value || !isMounted.value) {
      return
    }
  }
  
  loading.value = true
  
  try {
    // console.log(`加载ETF数据: ${selectedETF.value}, 周期: ${activePeriod.value}`)
    
    let response
    
    // 根据不同的周期类型和参数加载数据
    if (activePeriod.value === 'custom' && dateRange.value) {
      // 自定义日期范围
      const [startDate, endDate] = dateRange.value as [string, string]
      // console.log(`自定义日期范围: ${startDate} 至 ${endDate}`)
      
      response = await etfAPI.getETFDaily(selectedETF.value, {
        start_date: startDate,
        end_date: endDate,
        limit: 30
      })
    } else {
      // 使用预设的数据点数量
      const limit = parseInt(dataPoints.value)
      // console.log(`使用预设数据点数: ${limit}`)
      
      response = await etfAPI.getETFDaily(selectedETF.value, {
        limit: limit
      })
    }
    
    if (response.success && response.data) {
      // console.log('获取到ETF数据:', response.data)
      
      // 处理ETF数据
      if (response.data.daily_data && Array.isArray(response.data.daily_data)) {
        chartData.value = response.data.daily_data
          .sort((a: any, b: any) => {
            // 确保数据按日期升序排序 (trade_date格式: YYYYMMDD)
            const dateA = parseInt(a.trade_date.toString())
            const dateB = parseInt(b.trade_date.toString())
            return dateA - dateB
          })
          .map((item: any, index: number, array: any[]) => {
            // 计算环比变化
            const periodChange = calculatePeriodChange(array, index)
            
            // 返回处理后的数据项
            return {
              ...item,
              periodChange
            }
          })
        
        // console.log(`处理后的数据项数: ${chartData.value.length}`)
        
        // 检查组件是否已卸载
        if (componentUnmounted.value || !isMounted.value) return
        
        // 获取最新的ETF数据
        if (chartData.value.length > 0) {
          etfLatestData.value = chartData.value[chartData.value.length - 1]
        }
        
        // 初始化图表
        await nextTick()
        // 验证DOM元素是否仍然有效
        if (chartContainer.value && 
            chartContainer.value.parentNode && 
            !componentUnmounted.value &&
            isMounted.value &&
            document.contains(chartContainer.value)) {
          try {
            initChart()
          } catch (error) {
            console.error('初始化ETF图表时出错:', error)
          }
        }
      } else {
        console.error('ETF数据格式不正确:', response.data)
      }
    } else {
      console.error('获取ETF数据失败:', response.message)
    }
  } catch (error) {
    console.error('加载ETF数据出错:', error)
  } finally {
    // 使用try-catch包装所有响应式更新
    try {
      if (!componentUnmounted.value && isMounted.value) {
        loading.value = false
      }
    } catch (error) {
      // 忽略组件已卸载时的响应式更新错误
      console.warn('组件已卸载，忽略loading状态更新')
    }
  }
}

// 计算环比涨跌幅
const calculatePeriodChange = (data: any[], index: number) => {
  if (index === 0) return 0
  
  const current = data[index].vol
  const previous = data[index - 1].vol
  
  if (previous === 0) return 0
  
  return ((current - previous) / previous) * 100
}

// 移除未使用的calculateMA函数

// 获取主题相关的颜色配置
const getThemeColors = () => {
  const isDark = appStore.isDarkMode
  return {
    // 涨跌颜色
    upColor: '#f56565', // 红色
    downColor: '#48bb78', // 绿色
    // 文字颜色
    textColor: isDark ? '#e2e8f0' : '#2d3748',
    // 背景色
    backgroundColor: 'transparent',
    // 网格线颜色
    gridColor: isDark ? '#4a5568' : '#e2e8f0',
    // 边框颜色
    borderColor: isDark ? '#4a5568' : '#cbd5e0'
  }
}

// 初始化图表
const initChart = () => {
  // 组件已卸载或未挂载，直接返回
  if (componentUnmounted.value || !isMounted.value) {
    return
  }
  
  // DOM容器检查
  if (!chartContainer.value || 
      !chartContainer.value.parentNode ||
      !document.contains(chartContainer.value)) {
    console.warn('ETF图表容器无效，跳过初始化')
    return
  }
  
  // 检查容器尺寸
  const containerHeight = chartContainer.value.offsetHeight
  
  // 如果容器高度为0，延迟初始化
  if (containerHeight === 0) {
    console.warn('图表容器高度为0，延迟初始化...')
    setTimeout(() => {
      initChart()
    }, 500)
    return
  }
  
  try {
    // 销毁现有图表实例
    if (chartInstance.value) {
      chartInstance.value.dispose()
    }
    
    // 创建新的图表实例
    const existingInstance = echarts.getInstanceByDom(chartContainer.value)
    if (existingInstance) {
      existingInstance.dispose()
    }
    const chart = echarts.init(chartContainer.value, null, {
      renderer: 'canvas',
      useDirtyRect: false
    })
    chartInstance.value = chart
    
    // 获取主题颜色
    const colors = getThemeColors()
    
    // 准备数据
    const dates = chartData.value.map((item: any) => {
      const dateStr = item.trade_date.toString()
      if (dateStr.length === 8) {
        return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`
      }
      return item.trade_date
    })
    
    // 准备价格数据
    const priceData = chartData.value.map((item: any) => item.close)
    
    // 准备成交量数据
    const volumeData = chartData.value.map((item: any, index: number) => {
      const isUp = index === 0 ? true : item.close >= chartData.value[index - 1].close
      return {
        value: item.vol,
        itemStyle: {
          color: isUp ? colors.upColor : colors.downColor
        }
      }
    })
    
    // 设置图表选项
    const option = {
      backgroundColor: colors.backgroundColor,
      animation: true,
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          lineStyle: {
            color: colors.borderColor,
            type: 'dashed'
          }
        },
        backgroundColor: appStore.isDarkMode ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.95)',
        borderColor: colors.borderColor,
        borderWidth: 1,
        textStyle: {
          color: colors.textColor,
          fontSize: 13
        },
        padding: [12, 16],
        formatter: (params: any[]) => {
          const dataIndex = params[0].dataIndex
          const data = chartData.value[dataIndex]
          const date = params[0].axisValue
          
          if (!data) return ''
          
          const pctChange = data.pct_change || 0
          const changeColor = pctChange >= 0 ? colors.upColor : colors.downColor
          const changeSign = pctChange >= 0 ? '+' : ''
          
          // 计算成交量变化幅度
          let volumeChangeInfo = ''
          if (dataIndex > 0) {
            const prevData = chartData.value[dataIndex - 1]
            if (prevData && prevData.vol) {
              const volumeChange = ((data.vol - prevData.vol) / prevData.vol) * 100
              const volumeChangeColor = volumeChange >= 0 ? colors.upColor : colors.downColor
              const volumeChangeSign = volumeChange >= 0 ? '+' : ''
              volumeChangeInfo = `
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                  <span>量变幅度：</span>
                  <span style="color: ${volumeChangeColor}; font-weight: 600;">${volumeChangeSign}${volumeChange.toFixed(2)}%</span>
                </div>
              `
            }
          }
          
          return `
            <div style="font-weight: 600; margin-bottom: 8px; color: ${colors.textColor}">${date}</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
              <span>收盘价：</span>
              <span style="font-weight: 600;">${data.close?.toFixed(2)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
              <span>涨跌幅：</span>
              <span style="color: ${changeColor}; font-weight: 600;">${changeSign}${pctChange.toFixed(2)}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
              <span>成交量：</span>
              <span>${(data.vol / 10000).toFixed(2)}万手</span>
            </div>
            ${volumeChangeInfo}
            <div style="display: flex; justify-content: space-between;">
              <span>成交额：</span>
              <span>${(data.amount / 100000000).toFixed(2)}亿元</span>
            </div>
          `
        }
      },
      grid: [
        {
          left: '3%',
          right: '3%',
          top: '5%',
          height: '65%',
          containLabel: true
        },
        {
          left: '3%',
          right: '3%',
          top: '75%',
          height: '20%',
          containLabel: true
        }
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          axisLine: {
            lineStyle: { color: colors.gridColor }
          },
          axisTick: {
            lineStyle: { color: colors.gridColor }
          },
          axisLabel: {
            color: colors.textColor,
            fontSize: 11
          },
          splitLine: { show: false }
        },
        {
          type: 'category',
          gridIndex: 1,
          data: dates,
          axisLine: {
            lineStyle: { color: colors.gridColor }
          },
          axisTick: {
            lineStyle: { color: colors.gridColor }
          },
          axisLabel: {
            color: colors.textColor,
            fontSize: 11
          },
          splitLine: { show: false }
        }
      ],
      yAxis: [
        {
          type: 'value',
          scale: true,
          axisLine: {
            lineStyle: { color: colors.gridColor }
          },
          axisTick: {
            lineStyle: { color: colors.gridColor }
          },
          axisLabel: {
            color: colors.textColor,
            fontSize: 11
          },
          splitLine: {
            lineStyle: {
              color: colors.gridColor,
              type: 'dashed'
            }
          }
        },
        {
          type: 'value',
          gridIndex: 1,
          axisLine: {
            lineStyle: { color: colors.gridColor }
          },
          axisTick: {
            lineStyle: { color: colors.gridColor }
          },
          axisLabel: {
            color: colors.textColor,
            fontSize: 11,
            formatter: (value: number) => {
              return (value / 10000).toFixed(0) + '万'
            }
          },
          splitLine: {
            lineStyle: {
              color: colors.gridColor,
              type: 'dashed'
            }
          }
        }
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 0,
          end: 100
        }
      ],
      series: [
        {
          name: '价格走势',
          type: 'line',
          data: priceData,
          smooth: true,
          symbol: 'none',
          lineStyle: {
            width: 2,
            color: colors.upColor
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              {
                offset: 0,
                color: `${colors.upColor}40`
              },
              {
                offset: 1,
                color: `${colors.upColor}10`
              }
            ])
          }
        },
        {
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: volumeData,
          barWidth: '60%'
        }
      ]
    }
    
    // 应用图表选项
    chart.setOption(option, true)
    
    // 处理图表大小调整
    const resizeChart = () => {
      if (chartInstance.value) {
        chartInstance.value.resize()
      }
    }
    
    // 清理之前的监听器
    if (windowResizeHandler.value) {
      window.removeEventListener('resize', windowResizeHandler.value)
    }
    if (resizeObserver.value) {
      resizeObserver.value.disconnect()
    }
    
    // 保存resize处理函数引用
    windowResizeHandler.value = resizeChart
    
    // 添加窗口大小变化监听
    window.addEventListener('resize', windowResizeHandler.value)
    
    // 添加ResizeObserver监听容器大小变化
    resizeObserver.value = new ResizeObserver(() => {
      resizeChart()
    })
    
    if (chartContainer.value && resizeObserver.value) {
      resizeObserver.value.observe(chartContainer.value)
    }
  } catch (error) {
    console.error('初始化ETF图表出错:', error)
  }
}

// 窗口大小改变时调整图表
const handleResize = () => {
  if (chartInstance.value) {
    chartInstance.value.resize()
  }
}

// 组件挂载
onMounted(async () => {
  // 标记组件已挂载
  isMounted.value = true
  
  try {
    // 先加载ETF列表，再加载数据
    await loadETFList()
    
    // 确保组件仍然处于挂载状态
    if (!componentUnmounted.value && isMounted.value) {
      // 确保在下一个tick中加载数据，以保证DOM已经渲染完成
      await nextTick()
      if (!componentUnmounted.value && isMounted.value && etfList.value.length > 0) {
        loadETFData()
      }
    }
    
    // 监听窗口大小变化
    if (!componentUnmounted.value && isMounted.value) {
      window.addEventListener('resize', handleResize)
    }
  } catch (error) {
    console.error('ETF组件挂载时出错:', error)
  }
})

// 组件卸载
onUnmounted(() => {
  // 立即标记组件状态 - 必须首先执行
  componentUnmounted.value = true
  isMounted.value = false
  
  // 使用try-catch包装所有可能的响应式操作
  try {
    // 强制停止所有响应式更新
    loading.value = false
    
    // 清理图表实例
    if (chartInstance.value) {
      try {
        chartInstance.value.dispose()
      } catch (error) {
        console.warn('清理图表实例时出错:', error)
      }
      chartInstance.value = null
    }
    
    // 清理事件监听器
    if (windowResizeHandler.value) {
      window.removeEventListener('resize', windowResizeHandler.value)
      windowResizeHandler.value = null
    }
    if (resizeObserver.value) {
      resizeObserver.value.disconnect()
      resizeObserver.value = null
    }
    window.removeEventListener('resize', handleResize)
    
    // 清理DOM引用和数据
    chartContainer.value = null
    chartData.value = []
    etfLatestData.value = null
  } catch (error) {
    // 完全忽略卸载时的任何错误
    console.warn('ETF组件卸载时出现错误，已忽略:', error)
  }
})
</script>

<style scoped>
.etf-daily-panel {
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

.etf-selector {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.etf-select {
  width: 220px;
}

.etf-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.etf-code {
  color: #888;
  font-size: 0.9em;
}

.period-selector {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  align-items: center;
  
  :deep(.el-radio-group) {
    background: var(--el-fill-color-dark);
    border-radius: 4px;
    padding: 2px;
    
    .el-radio-button__inner {
      border: none;
      background: transparent;
      box-shadow: none;
      border-radius: 3px;
      transition: all 0.2s;
      
      &:hover {
        background: var(--el-fill-color);
      }
    }
    
    .el-radio-button.is-active .el-radio-button__inner {
      background: var(--el-color-primary);
      color: white;
      box-shadow: none;
    }
  }
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
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(4px);
  z-index: 10;
  gap: var(--spacing-sm);
}

.loading-icon {
  font-size: 24px;
  color: var(--accent-primary);
  animation: spin 1s linear infinite;
}

.loading-text {
  color: var(--text-secondary);
  font-size: 14px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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
  background-color: #f56565;
}

.line-secondary {
  background: linear-gradient(to right, #f56565 50%, #48bb78 50%);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .panel-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .period-selector {
    justify-content: center;
  }
  
  .date-picker,
  .data-points-select {
    min-width: 100px;
    max-width: 120px;
  }
  
  .chart-container {
    height: 300px;
  }
  
  .legend-section {
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-sm);
  }
}
</style>