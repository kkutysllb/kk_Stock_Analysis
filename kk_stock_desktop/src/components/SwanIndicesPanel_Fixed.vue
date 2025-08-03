<template>
  <div class="swan-indices-panel-fixed">
    <!-- 指数选择器 -->
    <div class="panel-header">
      <!-- 面板标题和AI按钮 -->
      <div class="panel-title-section">
        <h3 class="panel-title">申万行业指数</h3>
        <AskAIComponent :data-context="aiDataContext" />
      </div>
      
      <div class="index-selector">
        <el-select
          v-model="selectedIndex"
          @change="onIndexChange"
          size="default"
          placeholder="请选择申万行业指数"
          filterable
          class="index-select"
          :loading="loadingIndices"
        >
          <el-option
            v-for="index in swanIndices"
            :key="index.code"
            :label="index.name"
            :value="index.code"
          >
            <span class="index-name">{{ index.name }}</span>
            <span class="index-code">{{ index.code }}</span>
          </el-option>
        </el-select>
      </div>
      
      <div class="period-selector">
        <el-radio-group v-model="activePeriod" @change="onPeriodChange" size="default">
          <el-radio-button value="daily">日线</el-radio-button>
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
        <div v-show="loading" class="loading-overlay">
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
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
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
import AskAIComponent from './AskAIComponent.vue'

// 使用组合式API，但避免过多的响应式数据
const appStore = useAppStore()

// 基础状态（最小化响应式数据）
const selectedIndex = ref('801010.SI')
const activePeriod = ref<'daily' | 'custom'>('daily')
const dateRange = ref<[string, string] | null>(null)
const dataPoints = ref('60')
const loading = ref(false)
const loadingIndices = ref(false)
const chartContainer = ref<HTMLElement | null>(null)

// 申万行业指数配置（动态从API获取）
const swanIndices = ref<Array<{ code: string, name: string, color: string, stock_count?: number }>>([])

// 加载申万行业列表
const loadSwanIndices = async () => {
  if (loadingIndices.value) return
  
  loadingIndices.value = true
  try {
    // console.log('开始加载申万行业列表...')  
    const response = await marketAPI.getSwIndustries()
    
    if (response.success && response.data?.industries) {
      swanIndices.value = response.data.industries.map(industry => ({
        code: industry.code,
        name: industry.name,
        color: industry.color,
        stock_count: industry.stock_count
      }))
      
      // console.log(`成功加载${swanIndices.value.length}个申万行业`)
      
      // 如果当前selectedIndex不在新加载的列表中，设置为第一个
      if (swanIndices.value.length > 0 && !swanIndices.value.find(item => item.code === selectedIndex.value)) {
        selectedIndex.value = swanIndices.value[0].code
        // console.log(`设置默认选中行业: ${selectedIndex.value}`)
      }
    } else {
      console.error('获取申万行业列表失败:', response.message)
      // 如果API失败，使用默认的固定列表作为降级
      swanIndices.value = [
        { code: '801010.SI', name: '农林牧渔', color: '#3b82f6' },
        { code: '801020.SI', name: '采掘', color: '#10b981' },
        { code: '801030.SI', name: '化工', color: '#f59e0b' },
        { code: '801040.SI', name: '钢铁', color: '#ef4444' },
        { code: '801050.SI', name: '有色金属', color: '#8b5cf6' },
        { code: '801080.SI', name: '电子', color: '#ec4899' },
        { code: '801110.SI', name: '家用电器', color: '#14b8a6' },
        { code: '801120.SI', name: '食品饮料', color: '#6366f1' },
        { code: '801130.SI', name: '纺织服装', color: '#d946ef' },
        { code: '801140.SI', name: '轻工制造', color: '#f97316' },
        { code: '801150.SI', name: '医药生物', color: '#22c55e' },
        { code: '801160.SI', name: '公用事业', color: '#64748b' },
        { code: '801170.SI', name: '交通运输', color: '#0ea5e9' },
        { code: '801180.SI', name: '房地产', color: '#eab308' },
        { code: '801200.SI', name: '商业贸易', color: '#a855f7' },
        { code: '801210.SI', name: '休闲服务', color: '#06b6d4' },
        { code: '801230.SI', name: '综合', color: '#94a3b8' },
        { code: '801710.SI', name: '建筑材料', color: '#f43f5e' },
        { code: '801720.SI', name: '建筑装饰', color: '#10b981' },
        { code: '801730.SI', name: '电气设备', color: '#6366f1' },
        { code: '801740.SI', name: '国防军工', color: '#d946ef' },
        { code: '801750.SI', name: '计算机', color: '#f97316' },
        { code: '801760.SI', name: '传媒', color: '#22c55e' },
        { code: '801770.SI', name: '通信', color: '#64748b' },
        { code: '801780.SI', name: '银行', color: '#0ea5e9' },
        { code: '801790.SI', name: '非银金融', color: '#eab308' },
        { code: '801880.SI', name: '汽车', color: '#a855f7' },
        { code: '801890.SI', name: '机械设备', color: '#06b6d4' }
      ]
    }
  } catch (error) {
    console.error('加载申万行业列表出错:', error)
    // 降级使用默认配置
    swanIndices.value = [
      { code: '801010.SI', name: '农林牧渔', color: '#3b82f6' },
      { code: '801020.SI', name: '采掘', color: '#10b981' },
      { code: '801030.SI', name: '化工', color: '#f59e0b' },
      { code: '801040.SI', name: '钢铁', color: '#ef4444' },
      { code: '801050.SI', name: '有色金属', color: '#8b5cf6' },
      { code: '801080.SI', name: '电子', color: '#ec4899' },
      { code: '801110.SI', name: '家用电器', color: '#14b8a6' },
      { code: '801120.SI', name: '食品饮料', color: '#6366f1' },
      { code: '801130.SI', name: '纺织服装', color: '#d946ef' },
      { code: '801140.SI', name: '轻工制造', color: '#f97316' },
      { code: '801150.SI', name: '医药生物', color: '#22c55e' },
      { code: '801160.SI', name: '公用事业', color: '#64748b' },
      { code: '801170.SI', name: '交通运输', color: '#0ea5e9' },
      { code: '801180.SI', name: '房地产', color: '#eab308' },
      { code: '801200.SI', name: '商业贸易', color: '#a855f7' },
      { code: '801210.SI', name: '休闲服务', color: '#06b6d4' },
      { code: '801230.SI', name: '综合', color: '#94a3b8' },
      { code: '801710.SI', name: '建筑材料', color: '#f43f5e' },
      { code: '801720.SI', name: '建筑装饰', color: '#10b981' },
      { code: '801730.SI', name: '电气设备', color: '#6366f1' },
      { code: '801740.SI', name: '国防军工', color: '#d946ef' },
      { code: '801750.SI', name: '计算机', color: '#f97316' },
      { code: '801760.SI', name: '传媒', color: '#22c55e' },
      { code: '801770.SI', name: '通信', color: '#64748b' },
      { code: '801780.SI', name: '银行', color: '#0ea5e9' },
      { code: '801790.SI', name: '非银金融', color: '#eab308' },
      { code: '801880.SI', name: '汽车', color: '#a855f7' },
      { code: '801890.SI', name: '机械设备', color: '#06b6d4' }
    ]
  } finally {
    loadingIndices.value = false
  }
}

// 非响应式数据存储
let chartInstance: echarts.ECharts | null = null
let chartData: any[] = []
let latestData: any = null
let isDestroyed = false

// AI数据上下文
const aiDataContext = computed(() => {
  const currentIndex = swanIndices.value.find(i => i.code === selectedIndex.value)
  
  // 数据一致性检查：确保chartData确实是当前选中指数的数据
  let validLatestData = null
  let validChartData = []
  
  if (chartData.length > 0) {
    // 检查chartData中的数据是否匹配当前选中的指数
    const firstDataPoint = chartData[0]
    const lastDataPoint = chartData[chartData.length - 1]
    
    // 检查数据是否为当前选中指数的数据
    const hasValidTsCode = firstDataPoint.ts_code || lastDataPoint.ts_code
    const isDataMatching = !hasValidTsCode || 
                          firstDataPoint.ts_code === selectedIndex.value || 
                          lastDataPoint.ts_code === selectedIndex.value ||
                          chartData.some(item => item.ts_code === selectedIndex.value)
    
    if (isDataMatching) {
      // 数据匹配，使用chartData中的数据
      validChartData = chartData
      const latest = chartData[chartData.length - 1]
      validLatestData = {
        close: latest.close,
        pct_change: latest.pct_change || 0,
        vol: latest.vol,
        amount: latest.amount,
        trade_date: latest.trade_date
      }
    } else {
      // 数据不匹配，使用latestData并清空chartData
      console.warn(`chartData数据与当前选中指数(${selectedIndex.value})不匹配，使用latestData数据`)
      validChartData = []
      validLatestData = latestData
    }
  } else {
    // 如果chartData为空，则使用latestData
    validChartData = []
    validLatestData = latestData
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
  const recentChartData = validChartData.slice(-dataPointsNum) // 根据用户设置的数据点数量
  
  let summary = ''
  if (validLatestData) {
    const pctChg = validLatestData.pct_change || 0
    const trend = pctChg > 0 ? '上涨' : pctChg < 0 ? '下跌' : '平盘'
    summary = `申万行业指数分析完整数据：

【重要提示：当前分析对象是 ${currentIndex?.name}（${selectedIndex.value}），请确保所有分析都基于此指数数据】

## 当前指数信息
- 指数名称：${currentIndex?.name || '未知'}
- 指数代码：${selectedIndex.value}
- 当前收盘价：${validLatestData.close?.toFixed(2)}
- 涨跌幅：${trend}${Math.abs(pctChg).toFixed(2)}%
- 成交量：${(validLatestData.vol || 0).toLocaleString()}万手
- 成交额：${(validLatestData.amount || 0).toLocaleString()}万元

## 历史数据统计
${stats ? `- 数据点数：${stats.count}个
- 最高价：${stats.max.toFixed(2)}
- 最低价：${stats.min.toFixed(2)}
- 平均价：${stats.avg.toFixed(2)}
- 中位数：${stats.median.toFixed(2)}
- 整体趋势：${stats.trend > 0 ? '上升' : stats.trend < 0 ? '下降' : '平稳'}（${stats.trend.toFixed(2)}%）
- 价格波动率：${stats.volatility.toFixed(2)}` : '- 暂无历史统计数据'}

## 最近交易数据（${currentIndex?.name}）
${recentChartData.map(item => 
  `${item.trade_date}: 收盘${item.close?.toFixed(2)}, 涨跌幅${(item.pct_change || 0).toFixed(2)}%, 成交量${(item.vol || 0).toLocaleString()}万手`
).join('\n')}

## 分析要点
- 分析对象：${currentIndex?.name}（${selectedIndex.value}）
- 周期类型：${activePeriod.value === 'daily' ? '日线' : '自定义周期'}
- 数据范围：${activePeriod.value === 'custom' && dateRange.value ? `${dateRange.value[0]} 至 ${dateRange.value[1]}` : `最近${dataPoints.value}个交易日`}
- 行业特征：${currentIndex?.name}作为申万行业指数，反映该行业整体表现
- 技术指标：请结合价格走势、成交量变化、涨跌幅分布等进行综合分析

请基于以上完整的${currentIndex?.name}数据进行深入分析，提供投资建议、风险提示和市场前景判断。

【再次提醒：本次分析的重点对象是 ${currentIndex?.name}，代码 ${selectedIndex.value}，请勿混淆其他指数】`
  } else {
    summary = `申万行业指数分析：

## 当前指数信息
- 指数名称：${currentIndex?.name || '未知'}
- 指数代码：${selectedIndex.value}
- 数据状态：正在加载中...

## 分析设置
- 周期类型：${activePeriod.value === 'daily' ? '日线' : '自定义周期'}
- 数据范围：${activePeriod.value === 'custom' && dateRange.value ? `${dateRange.value[0]} 至 ${dateRange.value[1]}` : `最近${dataPoints.value}个交易日`}

请等待数据加载完成后进行分析。`
  }
  
  return {
    type: 'sw_industry_index',
    name: `${currentIndex?.name || '申万行业指数'}(${selectedIndex.value})`, // 这个name字段用于AI组件检测数据变化
    title: '申万行业指数分析',
    selectedIndex: selectedIndex.value,
    indexName: currentIndex?.name || '',
    period: activePeriod.value,
    dataPoints: dataPoints.value,
    latestData: validLatestData,
    recentData: recentChartData,
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

// 事件处理函数
const onIndexChange = (value: string) => {
  if (isDestroyed) return
  loadIndexData()
}

const onPeriodChange = () => {
  if (isDestroyed) return
  loadIndexData()
}

const onDateRangeChange = () => {
  if (isDestroyed) return
  loadIndexData()
}

const onDataPointsChange = () => {
  if (isDestroyed) return
  loadIndexData()
}

// 加载指数数据
const loadIndexData = async () => {
  // 检查组件状态
  if (!selectedIndex.value || isDestroyed) {
    console.warn('组件未就绪或已卸载，跳过数据加载')
    return
  }
  
  // 检查DOM容器是否存在
  if (!chartContainer.value) {
    console.warn('图表容器不存在，延迟加载数据')
    await nextTick()
    if (!chartContainer.value || isDestroyed) {
      return
    }
  }
  
  loading.value = true
  
  try {
    // 使用完整的申万行业指数代码（保留.SI后缀）
    let indexCode = selectedIndex.value
    // console.log(`加载申万行业指数数据: ${indexCode}, 周期: ${activePeriod.value}`)
    
    let response
    
    // 根据不同的周期类型和参数加载数据
    if (activePeriod.value === 'custom' && dateRange.value) {
      // 自定义日期范围
      const [startDate, endDate] = dateRange.value as [string, string]
      // console.log(`自定义日期范围: ${startDate} 至 ${endDate}`)  
      
      response = await marketAPI.getSwIndustryDaily(
        indexCode, // 使用修改后的代码
        startDate,
        endDate,
        30
      )
    } else {
      // 使用预设的数据点数量，从当前日期开始向前获取数据
      const limit = parseInt(dataPoints.value)
      // console.log(`使用预设数据点数: ${limit}`)
      
      // 获取当前日期作为结束日期，确保从当前日期开始向前获取数据
      const currentDate = new Date()
      // 添加一天以确保包含最新数据
      currentDate.setDate(currentDate.getDate() + 1)
      const endDate = currentDate.toISOString().slice(0, 10).replace(/-/g, '') // 格式化为YYYYMMDD
      
      // console.log(`设置结束日期为: ${endDate} (当前日期+1天以确保包含最新数据)`)
      
      response = await marketAPI.getSwIndustryDaily(
        indexCode, // 使用修改后的代码
        undefined, // 不设置开始日期，让后端基于limit和结束日期计算
        endDate,   // 设置结束日期为当前日期
        limit
      )
    }
    
    if (response.success && response.data) {
      // console.log('获取到申万行业指数数据:', response.data)
      
      // 处理申万行业指数数据
      if (response.data.sw_industry_data && Array.isArray(response.data.sw_industry_data)) {
        chartData = response.data.sw_industry_data
          .sort((a: any, b: any) => {
            // 确保数据按日期升序排序 (trade_date格式: YYYYMMDD)
            const dateA = parseInt(a.trade_date.toString())
            const dateB = parseInt(b.trade_date.toString())
            return dateA - dateB
          })
          .map((item: any, index: number, array: any[]) => {
            // 计算环比变化
            const periodChange = calculatePeriodChange(array, index)
            
            // 返回处理后的数据项，统一字段名称
            return {
              ...item,
              pct_change: item.pct_chg || item.pct_change || 0, // 统一字段名称：API返回pct_chg，组件使用pct_change
              periodChange
            }
          })
        
        // console.log(`处理后的数据项数: ${chartData.length}`)
        
        // 检查组件是否已卸载
        if (isDestroyed) return
        
        // 获取最新的指数数据
        if (chartData.length > 0) {
          latestData = chartData[chartData.length - 1]
        }
        
        // 初始化图表
        await nextTick()
        // 验证DOM元素是否仍然有效且组件未卸载
        if (chartContainer.value && 
            chartContainer.value.parentNode && 
            !isDestroyed &&
            document.contains(chartContainer.value)) {
          try {
            initChart()
          } catch (error) {
            console.error('初始化图表时出错:', error)
          }
        }
      } else {
        console.error('申万行业指数数据格式不正确:', response.data)
      }
    } else {
      console.error('获取申万行业指数数据失败:', response.message)
    }
  } catch (error) {
    console.error('加载申万行业指数数据出错:', error)
  } finally {
    // 使用try-catch包装所有响应式更新
    try {
      if (!isDestroyed) {
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
  // 组件已卸载，直接返回
  if (isDestroyed) {
    return
  }
  
  // DOM容器检查
  if (!chartContainer.value || 
      !chartContainer.value.parentNode ||
      !document.contains(chartContainer.value)) {
    console.warn('申万行业指数图表容器无效，跳过初始化')
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
    if (chartInstance) {
      chartInstance.dispose()
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
    chartInstance = chart
    
    // 获取主题颜色
    const colors = getThemeColors()
    
    // 准备数据
    const dates = chartData.map(item => {
      const dateStr = item.trade_date.toString()
      if (dateStr.length === 8) {
        return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`
      }
      return item.trade_date
    })
    
    // 准备价格数据
    const priceData = chartData.map(item => item.close)
    
    // 准备成交量数据
    const volumeData = chartData.map((item, index) => {
      const isUp = index === 0 ? true : item.close >= chartData[index - 1].close
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
          const data = chartData[dataIndex]
          const date = params[0].axisValue
          
          if (!data) return ''
          
          const pctChange = data.pct_change || 0
          const changeColor = pctChange >= 0 ? colors.upColor : colors.downColor
          const changeSign = pctChange >= 0 ? '+' : ''
          
          // 计算成交量变化幅度
          let volumeChangeInfo = ''
          if (dataIndex > 0) {
            const prevData = chartData[dataIndex - 1]
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
      if (chartInstance) {
        chartInstance.resize()
      }
    }
    
    // 添加窗口大小变化监听
    window.addEventListener('resize', resizeChart)
    
  } catch (error) {
    console.error('初始化申万行业指数图表出错:', error)
  }
}

// 组件挂载时加载数据
onMounted(async () => {
  isDestroyed = false
  
  try {
    // 首先加载申万行业列表
    await loadSwanIndices()
    
    // 确保组件仍然处于挂载状态
    if (!isDestroyed) {
      // 确保在下一个tick中加载数据，以保证DOM已经渲染完成
      await nextTick()
      if (!isDestroyed) {
        loadIndexData()
      }
    }
  } catch (error) {
    console.error('组件挂载时出错:', error)
  }
})

// 组件销毁
onBeforeUnmount(() => {
  isDestroyed = true
  
  if (chartInstance) {
    try {
      chartInstance.dispose()
    } catch (error) {
      // 忽略销毁错误
    }
    chartInstance = null
  }
  
  // 清理数据
  chartData = []
  latestData = null
})
</script>

<style scoped>
.swan-indices-panel-fixed {
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

@media (min-width: 768px) {
  .panel-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

.panel-title-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-lg);
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.index-selector {
  display: flex;
  gap: var(--spacing-sm);
}

.index-select {
  width: 300px;
  min-width: 250px;
}

.index-name {
  font-weight: 500;
}

.index-code {
  color: #888;
  font-size: 0.85em;
  float: right;
}

.period-selector {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  align-items: center;
}

.date-picker {
  width: 260px;
}

.data-points-select {
  width: 120px;
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
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.legend-section {
  display: flex;
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
</style>