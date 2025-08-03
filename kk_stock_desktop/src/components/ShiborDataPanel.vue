<template>
  <div class="shibor-data-panel">
    <div class="panel-header">
      <div class="panel-title-section">
        <h3 class="panel-title">
          <BanknotesIcon class="title-icon" />
          SHIBOR利率数据
        </h3>
        <AskAIComponent :data-context="aiDataContext" />
      </div>
      
      <div class="panel-controls">
        <el-radio-group v-model="activeTab" @change="onTabChange" size="default">
          <el-radio-button value="overview">概览</el-radio-button>
          <el-radio-button value="trend">趋势</el-radio-button>
          <el-radio-button value="analysis">分析</el-radio-button>
        </el-radio-group>
        
        <div class="date-control" v-if="activeTab === 'trend' || activeTab === 'overview'">
          <el-date-picker
            v-if="activeTab === 'overview'"
            v-model="overviewSelectedDate"
            type="date"
            placeholder="选择日期"
            size="default"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            class="date-picker"
            clearable
            @change="onOverviewDateChange"
          />
          <el-date-picker
            v-else-if="activeTab === 'trend'"
            v-model="selectedDate"
            type="date"
            placeholder="选择日期"
            size="default"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            class="date-picker"
            clearable
            @change="onDateChange"
          />
        </div>
      </div>
    </div>
    
    <div class="panel-body">
      <div v-if="loading" class="loading-container">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span class="loading-text">加载中...</span>
      </div>
      
      <div v-else-if="error" class="error-container">
        <el-icon class="error-icon"><Warning /></el-icon>
        <span class="error-text">{{ error }}</span>
        <el-button @click="loadData" type="primary" size="small" class="retry-button">
          重试
        </el-button>
      </div>
      
      <div v-else class="panel-content">
        <!-- 概览面板 -->
        <div v-if="activeTab === 'overview'" class="overview-panel">
          <div class="latest-data-section">
            <div class="section-title">最新利率</div>
            <div class="latest-data-grid">
              <div 
                v-for="item in latestData" 
                :key="item.period"
                class="rate-card"
                :class="{ 'rate-up': item.change > 0, 'rate-down': item.change < 0 }"
              >
                <div class="rate-period">{{ item.period }}</div>
                <div class="rate-value">{{ item.rate }}%</div>
                <div class="rate-change">
                  <span class="change-icon">
                    {{ item.change > 0 ? '↑' : item.change < 0 ? '↓' : '=' }}
                  </span>
                  <span class="change-value">{{ Math.abs(item.change) }}bp</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="curve-section">
            <div class="section-title">利率曲线</div>
            <div class="curve-chart" ref="curveChartContainer"></div>
          </div>
        </div>
        
        <!-- 趋势面板 -->
        <div v-if="activeTab === 'trend'" class="trend-panel">
          <div class="trend-controls">
            <el-radio-group v-model="selectedPeriod" @change="onPeriodChange" size="small">
              <el-radio-button v-for="period in availablePeriods" :key="period" :value="period">
                {{ period }}
              </el-radio-button>
            </el-radio-group>
          </div>
          
          <div class="trend-chart" ref="trendChartContainer"></div>
        </div>
        
        <!-- 分析面板 -->
        <div v-if="activeTab === 'analysis'" class="analysis-panel">
          <div class="analysis-content">
            <div class="analysis-section">
              <h4 class="analysis-title">利率分析报告</h4>
              <div class="analysis-text" v-html="analysisReport"></div>
            </div>
            
            <div class="statistics-section">
              <h4 class="statistics-title">统计数据</h4>
              <div class="statistics-grid">
                <div class="stat-item">
                  <div class="stat-label">平均利率</div>
                  <div class="stat-value">{{ statistics.averageRate }}%</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">最高利率</div>
                  <div class="stat-value">{{ statistics.maxRate }}%</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">最低利率</div>
                  <div class="stat-value">{{ statistics.minRate }}%</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">波动率</div>
                  <div class="stat-value">{{ statistics.volatility }}%</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { useAppStore } from '../stores/app'
import { shiborAPI } from '../api/shibor'
import { 
  ElRadioGroup, 
  ElRadioButton,
  ElDatePicker,
  ElButton,
  ElIcon
} from 'element-plus'
import { Loading, Warning } from '@element-plus/icons-vue'
import { BanknotesIcon } from '@heroicons/vue/24/outline'
import AskAIComponent from './AskAIComponent.vue'

// 获取应用状态
const appStore = useAppStore()

// 响应式状态
const loading = ref(false)
const error = ref('')
const activeTab = ref<'overview' | 'trend' | 'analysis'>('overview')
const selectedPeriod = ref('ON')
const selectedDate = ref<string>(new Date().toISOString().split('T')[0])

// 概览面板的选择日期（默认为当前日期）
const overviewSelectedDate = ref<string>(new Date().toISOString().split('T')[0])

// 计算日期范围的辅助函数
const getDateRange = (endDate: string): [string, string] => {
  const end = new Date(endDate)
  const start = new Date(end.getTime() - 30 * 24 * 60 * 60 * 1000)
  return [
    start.toISOString().split('T')[0],
    endDate
  ]
}

// 获取概览面板的日期范围
const overviewDateRange = computed(() => getDateRange(overviewSelectedDate.value))
const dateRange = computed(() => getDateRange(selectedDate.value))

// 数据状态
const latestData = ref<any[]>([])
const trendData = ref<any[]>([])
const analysisReport = ref('')
const statistics = ref({
  averageRate: 0,
  maxRate: 0,
  minRate: 0,
  volatility: 0
})

// 图表实例
const curveChartContainer = ref<HTMLElement | null>(null)
const trendChartContainer = ref<HTMLElement | null>(null)
const curveChart = ref<echarts.ECharts | null>(null)
const trendChart = ref<echarts.ECharts | null>(null)

// 可用期限
const availablePeriods = ['ON', '1W', '2W', '1M', '3M', '6M', '9M', '1Y']

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

// AI数据上下文
const aiDataContext = computed(() => {
  const summary = `SHIBOR利率数据分析：

## 当前数据状态
- 活跃面板：${activeTab.value === 'overview' ? '概览' : activeTab.value === 'trend' ? '趋势' : '分析'}
- 选中期限：${selectedPeriod.value}
- 概览数据范围：${overviewDateRange.value[0]} 至 ${overviewDateRange.value[1]}
- 趋势数据范围：${dateRange.value[0]} 至 ${dateRange.value[1]}

## 最新利率数据
${latestData.value.map(item => 
  `- ${item.period}: ${item.rate}% (${item.change > 0 ? '+' : ''}${item.change}bp)`
).join('\n')}

## 统计摘要
- 平均利率：${statistics.value.averageRate}%
- 最高利率：${statistics.value.maxRate}%
- 最低利率：${statistics.value.minRate}%
- 波动率：${statistics.value.volatility}%

## 趋势数据（最近${trendData.value.length}个数据点）
${trendData.value.slice(-10).map(item => 
  `${item.date}: ${item.rate}%`
).join('\n')}

## 分析要点
- SHIBOR（上海银行间同业拆放利率）是中国货币市场基准利率
- 反映银行间流动性状况和货币政策传导效果
- 各期限利率变化体现市场对流动性预期
- 利率曲线形态反映市场对未来利率走势的预期

请基于以上SHIBOR利率数据进行深入分析，提供市场流动性判断、货币政策影响分析和投资建议。`
  
  return {
    type: 'shibor_data',
    name: `SHIBOR利率数据(${activeTab.value})`,
    title: 'SHIBOR利率数据分析',
    activeTab: activeTab.value,
    selectedPeriod: selectedPeriod.value,
    dateRange: dateRange.value,
    overviewDateRange: overviewDateRange.value,
    latestData: latestData.value,
    trendData: trendData.value,
    statistics: statistics.value,
    summary: summary,
    data: {
      activeTab: activeTab.value,
      selectedPeriod: selectedPeriod.value,
      overviewDateRange: overviewDateRange.value,
      trendDateRange: dateRange.value,
      dataCount: trendData.value.length
    }
  }
})

// 加载数据
const loadData = async () => {
  loading.value = true
  error.value = ''
  
  try {
    await Promise.all([
      loadLatestData(),
      loadTrendData(),
      loadAnalysisData()
    ])
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载数据失败'
  } finally {
    loading.value = false
  }
}

// 加载最新数据（支持日期范围查询）
const loadLatestData = async () => {
  try {
    // 将日期格式从YYYY-MM-DD转换为YYYYMMDD
    const startDate = overviewDateRange.value[0].replace(/-/g, '')
    const endDate = overviewDateRange.value[1].replace(/-/g, '')
    
    // 调用后端API获取指定日期范围的SHIBOR数据
    const response = await shiborAPI.getShiborData({
      start_date: startDate,
      end_date: endDate,
      limit: 50, // 获取足够的数据用于分析
    })
    
    if (response.success && response.data) {
      const shiborRates = response.data.shibor_rates
      
      if (Array.isArray(shiborRates) && shiborRates.length > 0) {
        // 获取最新一天的数据（数组第一个元素是最新的）
        const latestRecord = shiborRates[0]
        
        // 计算变化（与前一天比较）
        const previousRecord = shiborRates.length > 1 ? shiborRates[1] : null
        
        // 构建利率曲线数据
        const periods = ['on', '1w', '2w', '1m', '3m', '6m', '9m', '1y']
        const periodLabels = ['ON', '1W', '2W', '1M', '3M', '6M', '9M', '1Y']
        
        latestData.value = periods.map((period, index) => {
          const currentRate = (latestRecord as any)[period] || 0
          const previousRate = previousRecord ? ((previousRecord as any)[period] || 0) : 0
          const change = previousRate ? ((currentRate - previousRate) * 100) : 0 // 转换为基点
          
          return {
            period: periodLabels[index],
            rate: currentRate,
            change: Math.round(change * 100) / 100 // 保留两位小数
          }
        }).filter(item => item.rate > 0) // 过滤掉无效数据
        
        // 计算统计信息
        if (latestData.value.length > 0) {
          const rates = latestData.value.map(item => item.rate)
          statistics.value = {
            averageRate: Math.round((rates.reduce((sum, rate) => sum + rate, 0) / rates.length) * 10000) / 10000,
            maxRate: Math.max(...rates),
            minRate: Math.min(...rates),
            volatility: 0 // 可以后续计算波动率
          }
        }
      }
      
      // 只在概览tab激活时初始化曲线图表
      await nextTick()
      if (activeTab.value === 'overview') {
        initCurveChart()
      }
    }
  } catch (err) {
    console.error('加载最新SHIBOR数据失败:', err)
  }
}

// 加载趋势数据
const loadTrendData = async () => {
  try {
    const response = await shiborAPI.getTrend(
      selectedPeriod.value.toLowerCase(), // 转换为小写
      dateRange.value[0], 
      dateRange.value[1]
    )
    
    if (response.success && response.data) {
      // 根据API实际返回的数据结构处理
      if (Array.isArray(response.data)) {
        // 如果直接返回数组
        trendData.value = response.data
      } else if ('trend_data' in response.data) {
        // 如果返回的是对象格式
        trendData.value = (response.data as { trend_data?: any[] }).trend_data || []
      } else {
        trendData.value = []
      }
      // 只在趋势tab激活时初始化趋势图表
      await nextTick()
      if (activeTab.value === 'trend') {
        initTrendChart()
      }
    }
  } catch (err) {
    console.error('加载SHIBOR趋势数据失败:', err)
  }
}

// 加载分析数据
const loadAnalysisData = async () => {
  try {
    const response = await shiborAPI.getAnalysis()
    if (response.success && response.data) {
      // 根据API实际返回的数据结构处理
      if (response.data.report) {
        // 如果有分析报告
        analysisReport.value = response.data.report
      } else {
        analysisReport.value = '基于SHIBOR利率数据的分析报告'
      }
      
      if (response.data.statistics) {
        // 如果有统计数据
        statistics.value = {
          averageRate: response.data.statistics.averageRate || 0,
          maxRate: response.data.statistics.maxRate || 0,
          minRate: response.data.statistics.minRate || 0,
          volatility: response.data.statistics.volatility || 0
        }
      } else if ('trend_analysis' in response.data) {
        // 如果返回的是trend_analysis格式
        const analysisData = (response.data as any).trend_analysis
        const onData = analysisData?.on || {}
        statistics.value = {
          averageRate: onData.average || 0,
          maxRate: onData.max || 0,
          minRate: onData.min || 0,
          volatility: onData.volatility || 0
        }
      }
    }
  } catch (err) {
    console.error('加载SHIBOR分析数据失败:', err)
  }
}

// 防抖定时器
let curveChartTimer: number | null = null
let trendChartTimer: number | null = null

// 初始化利率曲线图表
const initCurveChart = () => {
  if (!curveChartContainer.value || latestData.value.length === 0) {
    return
  }
  
  // 清除之前的定时器
  if (curveChartTimer) {
    clearTimeout(curveChartTimer)
  }
  
  // 使用防抖避免频繁重绘
  curveChartTimer = setTimeout(() => {
    // 销毁现有图表
    if (curveChart.value) {
      curveChart.value.dispose()
    }
    
    // 创建新图表
    const chart = echarts.init(curveChartContainer.value!)
    curveChart.value = chart
    const periods = latestData.value.map(item => item.period)
    const rates = latestData.value.map(item => item.rate)
    
    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        formatter: '{b}: {c}%'
      },
      xAxis: {
        type: 'category',
        data: periods,
        axisLabel: {
          color: appStore.isDarkMode ? '#ffffff' : '#333333'
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: '{value}%',
          color: appStore.isDarkMode ? '#ffffff' : '#333333'
        }
      },
      series: [{
        data: rates,
        type: 'line',
        smooth: true,
        lineStyle: {
          color: '#3b82f6'
        },
        itemStyle: {
          color: '#3b82f6'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.1)' }
          ])
        }
      }]
    }
    
    chart.setOption(option)
  }, 100) // 100ms防抖延迟
}

// 初始化趋势图表
const initTrendChart = () => {
  if (!trendChartContainer.value || trendData.value.length === 0) return
  
  // 清除之前的定时器
  if (trendChartTimer) {
    clearTimeout(trendChartTimer)
  }
  
  // 使用防抖避免频繁重绘
  trendChartTimer = setTimeout(() => {
    // 销毁现有图表
    if (trendChart.value) {
      trendChart.value.dispose()
    }
    
    // 创建新图表
    const chart = echarts.init(trendChartContainer.value!)
    trendChart.value = chart
    
    const dates = trendData.value.map(item => item.date)
    const rates = trendData.value.map(item => item.rate)
    
    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        formatter: '{b}: {c}%'
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: {
          color: appStore.isDarkMode ? '#ffffff' : '#333333'
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: '{value}%',
          color: appStore.isDarkMode ? '#ffffff' : '#333333'
        }
      },
      series: [{
        data: rates,
        type: 'line',
        smooth: true,
        lineStyle: {
          color: '#10b981'
        },
        itemStyle: {
          color: '#10b981'
        }
      }]
    }
    
    chart.setOption(option)
  }, 100) // 100ms防抖延迟
}

// 处理标签页切换
const onTabChange = (tab: string | number | boolean | undefined) => {
  if (typeof tab === 'string') {
    activeTab.value = tab as 'overview' | 'trend' | 'analysis'
    nextTick(() => {
      if (tab === 'overview') {
        initCurveChart()
      } else if (tab === 'trend') {
        initTrendChart()
      }
    })
  }
}

// 处理期限切换
const onPeriodChange = (period: string | number | boolean | undefined) => {
  if (typeof period === 'string') {
    selectedPeriod.value = period
    loadTrendData()
  }
}



// 处理概览面板日期变化
const onOverviewDateChange = () => {
 
  // watch监听器会自动处理数据加载，这里不需要重复调用
}

// 处理趋势面板日期变化
const onDateChange = () => {
  // v-model会自动更新selectedDate的值
  // watch监听器会自动处理数据加载，这里不需要重复调用
}

// 处理窗口大小变化
const handleResize = () => {
  if (curveChart.value) {
    curveChart.value.resize()
  }
  if (trendChart.value) {
    trendChart.value.resize()
  }
}

// 监听activeTab变化，确保图表在正确的时机初始化
watch(() => activeTab.value, (newTab) => {
  nextTick(() => {
    // 使用setTimeout确保DOM完全渲染后再初始化图表
    setTimeout(() => {
      if (newTab === 'overview' && latestData.value.length > 0) {
        initCurveChart()
      } else if (newTab === 'trend' && trendData.value.length > 0) {
        initTrendChart()
      }
    }, 50)
  })
})

// 监听主题变化
watch(() => appStore.isDarkMode, () => {
  nextTick(() => {
    if (activeTab.value === 'overview') {
      initCurveChart()
    } else if (activeTab.value === 'trend') {
      initTrendChart()
    }
  })
})

// 监听概览面板日期范围变化
watch(() => overviewDateRange.value, () => {
  if (activeTab.value === 'overview') {
    nextTick(() => {
      setTimeout(() => {
        if (latestData.value.length > 0) {
          initCurveChart()
        }
      }, 50)
    })
  }
}, { deep: true })

// 监听概览面板日期变化
watch(() => overviewSelectedDate.value, (newDate, oldDate) => {
  if (activeTab.value === 'overview' && newDate !== oldDate) {
    loadLatestData()
  }
})

// 监听趋势面板日期变化
watch(() => selectedDate.value, (newDate, oldDate) => {
  if (activeTab.value === 'trend' && newDate !== oldDate) {
    loadTrendData()
  }
})

// 组件挂载
onMounted(async () => {
  await loadData()
  // 确保数据加载完成后，根据当前激活的tab初始化对应的图表
  await nextTick()
  
  // 使用setTimeout确保DOM完全渲染后再初始化图表
  setTimeout(() => {
    if (activeTab.value === 'overview' && latestData.value.length > 0) {
      initCurveChart()
    } else if (activeTab.value === 'trend' && trendData.value.length > 0) {
      initTrendChart()
    }
  }, 100)
  
  window.addEventListener('resize', handleResize)
})

// 组件卸载
onUnmounted(() => {
  // 清理定时器
  if (curveChartTimer) {
    clearTimeout(curveChartTimer)
  }
  if (trendChartTimer) {
    clearTimeout(trendChartTimer)
  }
  
  // 销毁图表实例
  if (curveChart.value) {
    curveChart.value.dispose()
  }
  if (trendChart.value) {
    trendChart.value.dispose()
  }
  
  // 移除事件监听器
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.shibor-data-panel {
  display: flex;
  flex-direction: column;
  background-color: var(--bg-content);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md);
  box-shadow: var(--shadow-sm);
  height: 100%;
  min-height: 600px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  gap: var(--spacing-md);
}

.panel-title-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.title-icon {
  width: 20px;
  height: 20px;
  color: var(--accent-primary);
}

.panel-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.date-control {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.date-picker {
  width: 260px;
}

.panel-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: var(--spacing-md);
}

.loading-icon {
  font-size: 24px;
  animation: spin 1s linear infinite;
  color: var(--accent-primary);
}

.error-icon {
  font-size: 24px;
  color: var(--error-color);
}

.loading-text,
.error-text {
  color: var(--text-secondary);
}

.retry-button {
  margin-top: var(--spacing-sm);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.panel-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* 概览面板样式 */
.overview-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  height: 100%;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
}

.latest-data-section {
  flex-shrink: 0;
}

.latest-data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--spacing-md);
}

.rate-card {
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  text-align: center;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.rate-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.rate-card.rate-up {
  border-color: var(--success-color);
}

.rate-card.rate-down {
  border-color: var(--error-color);
}

.rate-period {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.rate-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.rate-change {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 12px;
}

.rate-up .rate-change {
  color: var(--success-color);
}

.rate-down .rate-change {
  color: var(--error-color);
}

.change-icon {
  font-weight: bold;
}

.curve-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.curve-chart {
  flex: 1;
  min-height: 300px;
  width: 100%;
  height: 300px;
}

/* 趋势面板样式 */
.trend-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  height: 100%;
}

.trend-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.trend-chart {
  flex: 1;
  min-height: 400px;
  width: 100%;
  height: 400px;
}

/* 分析面板样式 */
.analysis-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  height: 100%;
}

.analysis-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.analysis-section {
  flex: 1;
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.analysis-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-md) 0;
}

.analysis-text {
  color: var(--text-secondary);
  line-height: 1.6;
}

.statistics-section {
  flex-shrink: 0;
}

.statistics-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-md) 0;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--spacing-md);
}

.stat-item {
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  text-align: center;
  border: 1px solid var(--border-color);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .shibor-data-panel {
    padding: var(--spacing-sm);
  }
  
  .panel-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .panel-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .date-picker {
    width: 100%;
  }
  
  .latest-data-grid {
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  }
  
  .statistics-grid {
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  }
}
</style>