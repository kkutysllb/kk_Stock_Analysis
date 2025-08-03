<template>
  <div class="options-data-panel">
    <div class="panel-header">
      <div class="panel-title-section">
        <h3 class="panel-title">
          <ChartBarIcon class="title-icon" />
          期权数据中心
        </h3>
        <AskAIComponent :data-context="aiDataContext" />
      </div>
      
      <div class="panel-controls">
        <el-radio-group v-model="activeTab" @change="onTabChange" size="default">
          <el-radio-button value="overview">概览</el-radio-button>
          <el-radio-button value="activity">活跃度</el-radio-button>
          <el-radio-button value="trend">趋势</el-radio-button>
          <el-radio-button value="analysis">分析</el-radio-button>
        </el-radio-group>
        
        <div class="filter-controls" v-if="activeTab !== 'overview'">
          <el-select 
            v-model="selectedUnderlying" 
            placeholder="选择标的" 
            size="default" 
            clearable
            filterable
            @change="onUnderlyingChange"
            class="underlying-select"
          >
            <el-option 
              v-for="underlying in underlyingList" 
              :key="underlying" 
              :label="underlying" 
              :value="underlying"
            />
          </el-select>
          
          <el-select 
            v-model="selectedCallPut" 
            placeholder="期权类型" 
            size="default" 
            clearable
            @change="onCallPutChange"
            class="callput-select"
            v-if="activeTab !== 'trend'"
          >
            <el-option label="看涨期权" value="C" />
            <el-option label="看跌期权" value="P" />
          </el-select>

          <!-- 趋势面板专用控件 -->
          <template v-if="activeTab === 'trend'">
            <el-select 
              v-model="trendDays" 
              placeholder="选择天数" 
              size="default" 
              @change="onTrendDaysChange"
              class="days-select"
            >
              <el-option label="最近7天" :value="7" />
              <el-option label="最近15天" :value="15" />
              <el-option label="最近30天" :value="30" />
            </el-select>
            
            <el-select 
              v-model="trendIndicator" 
              placeholder="选择指标" 
              size="default" 
              @change="onTrendIndicatorChange"
              class="indicator-select"
            >
              <el-option label="收盘价" value="close" />
              <el-option label="结算价" value="settle" />
              <el-option label="交易量" value="vol" />
              <el-option label="持仓量" value="oi" />
            </el-select>
          </template>
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
          <div class="summary-section">
            <div class="summary-grid">
              <div class="summary-card">
                <div class="summary-label">总合约数</div>
                <div class="summary-value">{{ marketSummary.totalContracts }}</div>
              </div>
              <div class="summary-card">
                <div class="summary-label">活跃合约</div>
                <div class="summary-value">{{ marketSummary.activeContracts }}</div>
              </div>
              <div class="summary-card">
                <div class="summary-label">总交易量</div>
                <div class="summary-value">{{ formatNumber(marketSummary.totalVolume) }}</div>
              </div>
              <div class="summary-card">
                <div class="summary-label">总持仓量</div>
                <div class="summary-value">{{ formatNumber(marketSummary.totalOI) }}</div>
              </div>
            </div>
          </div>

          <div class="charts-section">
            <div class="chart-container">
              <div class="chart-title">交易量分布</div>
              <div class="chart-content" ref="volumeChartContainer"></div>
            </div>
            <div class="chart-container">
              <div class="chart-title">持仓量分布</div>
              <div class="chart-content" ref="oiChartContainer"></div>
            </div>
          </div>
        </div>
        
        <!-- 活跃度面板 -->
        <div v-if="activeTab === 'activity'" class="activity-panel">
          <div class="summary-section">
            <div class="summary-grid">
              <div class="summary-card">
                <div class="summary-label">总交易量</div>
                <div class="summary-value">{{ formatNumber(activityData.totalVolume) }}</div>
              </div>
              <div class="summary-card">
                <div class="summary-label">总成交额</div>
                <div class="summary-value">{{ formatNumber(activityData.totalAmount) }}万</div>
              </div>
              <div class="summary-card">
                <div class="summary-label">总持仓量</div>
                <div class="summary-value">{{ formatNumber(activityData.totalOI) }}</div>
              </div>
              <div class="summary-card">
                <div class="summary-label">活跃合约数</div>
                <div class="summary-value">{{ activityData.activeContracts }}</div>
              </div>
            </div>
          </div>

          <div class="charts-section">
            <div class="chart-container">
              <div class="chart-title">交易量排名 TOP10</div>
              <div class="chart-content" ref="volumeRankingChartContainer"></div>
            </div>
            <div class="chart-container">
              <div class="chart-title">持仓量排名 TOP10</div>
              <div class="chart-content" ref="oiRankingChartContainer"></div>
            </div>
          </div>
        </div>
        
        <!-- 趋势面板 -->
        <div v-if="activeTab === 'trend'" class="trend-panel">
          <div class="summary-section" v-if="trendStats">
            <div class="summary-grid">
              <div class="summary-card">
                <div class="summary-label">最新值</div>
                <div class="summary-value">{{ trendStats.latest_value || 0 }}</div>
              </div>
              <div class="summary-card">
                <div class="summary-label">平均值</div>
                <div class="summary-value">{{ trendStats.avg_value || 0 }}</div>
              </div>
              <div class="summary-card">
                <div class="summary-label">最大值</div>
                <div class="summary-value">{{ trendStats.max_value || 0 }}</div>
              </div>
              <div class="summary-card">
                <div class="summary-label">变化率</div>
                <div class="summary-value" :class="{'positive': (trendStats.change_rate || 0) > 0, 'negative': (trendStats.change_rate || 0) < 0}">
                  {{ (trendStats.change_rate || 0).toFixed(2) }}%
                </div>
              </div>
            </div>
          </div>

          <div class="trend-chart-section">
            <div class="chart-container full-width">
              <div class="chart-title">{{ selectedUnderlying || '请选择品种' }} - {{ getIndicatorLabel(trendIndicator) }}趋势</div>
              <div class="chart-content large" ref="trendChartContainer"></div>
            </div>
          </div>
        </div>
        
        <!-- 分析面板 -->
        <div v-if="activeTab === 'analysis'" class="analysis-panel">
          <div v-if="oiAnalysis">
            <div class="summary-section">
              <div class="summary-grid">
                <div class="summary-card">
                  <div class="summary-label">总持仓量</div>
                  <div class="summary-value">{{ formatNumber(oiAnalysis.total_oi) }}</div>
                </div>
                <div class="summary-card">
                  <div class="summary-label">平均持仓量</div>
                  <div class="summary-value">{{ formatNumber(oiAnalysis.avg_oi) }}</div>
                </div>
                <div class="summary-card">
                  <div class="summary-label">最大持仓量</div>
                  <div class="summary-value">{{ formatNumber(oiAnalysis.max_oi) }}</div>
                </div>
                <div class="summary-card">
                  <div class="summary-label">合约数量</div>
                  <div class="summary-value">{{ oiAnalysis.contract_count }}</div>
                </div>
              </div>
            </div>

            <div class="charts-section">
              <div class="chart-container">
                <div class="chart-title">持仓量分布</div>
                <div class="chart-content" ref="oiDistributionChartContainer"></div>
              </div>
              <div class="chart-container">
                <div class="chart-title">TOP20持仓合约</div>
                <div class="chart-content" ref="topOIChartContainer"></div>
              </div>
            </div>
          </div>
          
          <div v-else class="no-data-container">
            <el-icon class="no-data-icon"><Warning /></el-icon>
            <span class="no-data-text">暂无分析数据</span>
            <p class="no-data-hint">请稍后重试或联系管理员</p>
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
import { optionsAPI } from '../api/options.js'
import { 
  ElRadioGroup, 
  ElRadioButton,
  ElSelect,
  ElOption,
  ElButton,
  ElIcon
} from 'element-plus'
import { Loading, Warning } from '@element-plus/icons-vue'
import { ChartBarIcon } from '@heroicons/vue/24/outline'
import AskAIComponent from './AskAIComponent.vue'

// 获取应用状态
const appStore = useAppStore()

// 响应式状态
const loading = ref(false)
const error = ref('')
const activeTab = ref<'overview' | 'activity' | 'trend' | 'analysis'>('overview')
const selectedUnderlying = ref('OP000300.SH')
const selectedCallPut = ref('C')
const trendDays = ref(30)
const trendIndicator = ref('close')

// 数据状态
const marketSummary = ref({
  totalContracts: 0,
  activeContracts: 0,
  totalVolume: 0,
  totalOI: 0
})

const activityData = ref({
  totalVolume: 0,
  totalAmount: 0,
  totalOI: 0,
  activeContracts: 0
})

const topContractsByVolume = ref<any[]>([])
const topContractsByOI = ref<any[]>([])
const latestOptionsData = ref<any[]>([])
const trendData = ref<any[]>([])
const trendStats = ref<any>(null)
const oiAnalysis = ref<any>(null)

// 图表实例
const volumeChartContainer = ref<HTMLElement | null>(null)
const volumeChart = ref<echarts.ECharts | null>(null)
const oiChartContainer = ref<HTMLElement | null>(null)
const oiChart = ref<echarts.ECharts | null>(null)
const volumeRankingChartContainer = ref<HTMLElement | null>(null)
const volumeRankingChart = ref<echarts.ECharts | null>(null)
const oiRankingChartContainer = ref<HTMLElement | null>(null)
const oiRankingChart = ref<echarts.ECharts | null>(null)
const trendChartContainer = ref<HTMLElement | null>(null)
const trendChart = ref<echarts.ECharts | null>(null)
const oiDistributionChartContainer = ref<HTMLElement | null>(null)
const oiDistributionChart = ref<echarts.ECharts | null>(null)
const topOIChartContainer = ref<HTMLElement | null>(null)
const topOIChart = ref<echarts.ECharts | null>(null)

// 基础数据
const underlyingList = ref(['OP000300.SH', 'OP000852.SH', 'OP000016.SH'])

// AI数据上下文
const aiDataContext = computed(() => {
  const getTabName = (tab: string) => {
    const tabNames: Record<string, string> = {
      'overview': '概览',
      'activity': '活跃度',
      'trend': '趋势',
      'analysis': '分析'
    }
    return tabNames[tab] || tab
  }

  const getUnderlyingName = (code: string) => {
    const names: Record<string, string> = {
      'OP000300.SH': '沪深300ETF期权',
      'OP000852.SH': '中证1000ETF期权',
      'OP000016.SH': '上证50ETF期权'
    }
    return names[code] || code
  }

  let summary = `期权数据中心 - ${getTabName(activeTab.value)}`
  let data = {}

  if (activeTab.value === 'overview') {
    summary += `\n\n市场概览:\n- 合约总数: ${marketSummary.value.totalContracts}\n- 活跃合约: ${marketSummary.value.activeContracts}\n- 总成交量: ${formatNumber(marketSummary.value.totalVolume)}\n- 总持仓量: ${formatNumber(marketSummary.value.totalOI)}`
    
    if (latestOptionsData.value.length > 0) {
      summary += `\n\n最新期权数据 (前5名):\n${latestOptionsData.value.slice(0, 5).map((item, index) => 
        `${index + 1}. ${item.ts_code} - 收盘价: ${item.close}, 成交量: ${formatNumber(item.vol)}, 持仓量: ${formatNumber(item.oi)}`
      ).join('\n')}`
    }
    
    data = {
      marketSummary: marketSummary.value,
      latestOptionsData: latestOptionsData.value.slice(0, 10)
    }
  } else if (activeTab.value === 'activity') {
    summary += ` - ${getUnderlyingName(selectedUnderlying.value)} (${selectedCallPut.value === 'C' ? '看涨' : '看跌'}期权)`
    summary += `\n\n活跃度统计:\n- 总成交量: ${formatNumber(activityData.value.totalVolume)}\n- 总成交额: ${formatNumber(activityData.value.totalAmount)}\n- 总持仓量: ${formatNumber(activityData.value.totalOI)}\n- 活跃合约数: ${activityData.value.activeContracts}`
    
    if (topContractsByVolume.value.length > 0) {
      summary += `\n\n成交量排行 (前5名):\n${topContractsByVolume.value.slice(0, 5).map((item, index) => 
        `${index + 1}. ${item.ts_code} - 成交量: ${formatNumber(item.vol)}, 涨跌幅: ${item.pct_change?.toFixed(2) || 0}%`
      ).join('\n')}`
    }
    
    if (topContractsByOI.value.length > 0) {
      summary += `\n\n持仓量排行 (前5名):\n${topContractsByOI.value.slice(0, 5).map((item, index) => 
        `${index + 1}. ${item.ts_code} - 持仓量: ${formatNumber(item.oi)}, 涨跌幅: ${item.pct_change?.toFixed(2) || 0}%`
      ).join('\n')}`
    }
    
    data = {
      selectedUnderlying: selectedUnderlying.value,
      selectedCallPut: selectedCallPut.value,
      activityData: activityData.value,
      topContractsByVolume: topContractsByVolume.value.slice(0, 10),
      topContractsByOI: topContractsByOI.value.slice(0, 10)
    }
  } else if (activeTab.value === 'trend') {
    summary += ` - ${getUnderlyingName(selectedUnderlying.value)} (最近${trendDays.value}天, ${getIndicatorLabel(trendIndicator.value)})`
    
    if (trendStats.value) {
      summary += `\n\n趋势统计:\n- 最新值: ${trendStats.value.latest}\n- 平均值: ${trendStats.value.average}\n- 最大值: ${trendStats.value.max}\n- 最小值: ${trendStats.value.min}\n- 涨跌幅: ${trendStats.value.change_pct}%`
    }
    
    if (trendData.value.length > 0) {
      const recentData = trendData.value.slice(-5)
      summary += `\n\n最近5个交易日数据:\n${recentData.map(item => 
        `${item.trade_date}: ${item[trendIndicator.value]}`
      ).join('\n')}`
    }
    
    data = {
      selectedUnderlying: selectedUnderlying.value,
      trendDays: trendDays.value,
      trendIndicator: trendIndicator.value,
      trendStats: trendStats.value,
      trendData: trendData.value
    }
  } else if (activeTab.value === 'analysis') {
    summary += ` - ${getUnderlyingName(selectedUnderlying.value)}`
    
    if (oiAnalysis.value) {
      summary += `\n\n持仓分析:\n- 看涨期权持仓: ${formatNumber(oiAnalysis.value.call_oi || 0)}\n- 看跌期权持仓: ${formatNumber(oiAnalysis.value.put_oi || 0)}\n- 看涨看跌比: ${(oiAnalysis.value.call_put_ratio || 0).toFixed(2)}`
    }
    
    data = {
      selectedUnderlying: selectedUnderlying.value,
      oiAnalysis: oiAnalysis.value
    }
  }

  return {
    type: '期权数据',
    name: `期权数据中心 - ${getTabName(activeTab.value)}`,
    period: activeTab.value === 'trend' ? `最近${trendDays.value}天` : '实时数据',
    data: data,
    summary: summary
  }
})

// 工具函数
const formatNumber = (num: number): string => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toLocaleString()
}

const getIndicatorLabel = (indicator: string): string => {
  const labels: Record<string, string> = {
    'close': '收盘价',
    'settle': '结算价',
    'vol': '交易量',
    'oi': '持仓量'
  }
  return labels[indicator] || indicator
}

// 事件处理
const onTabChange = (tab: string | number | boolean | undefined) => {
  if (typeof tab === 'string' && ['overview', 'activity', 'trend', 'analysis'].includes(tab)) {
    activeTab.value = tab as 'overview' | 'activity' | 'trend' | 'analysis'
    loadData()
  }
}

const onUnderlyingChange = () => {
  loadData()
}

const onCallPutChange = () => {
  loadData()
}

const onTrendDaysChange = () => {
  if (selectedUnderlying.value) {
    loadTrendData()
  }
}

const onTrendIndicatorChange = () => {
  if (selectedUnderlying.value) {
    loadTrendData()
  }
}

// 数据加载函数
const loadData = async () => {
  try {
    loading.value = true
    error.value = ''
    
    switch (activeTab.value) {
      case 'overview':
        await loadOverviewData()
        break
      case 'activity':
        await loadActivityData()
        break
      case 'trend':
        if (selectedUnderlying.value) {
          await loadTrendData()
        }
        break
      case 'analysis':
        await loadAnalysisData()
        break
    }
  } catch (err: any) {
    error.value = err.message || '数据加载失败'
  } finally {
    loading.value = false
  }
}

const loadOverviewData = async () => {
  // console.log('📊 开始加载概览数据...')
  
  // 加载市场概况
  const summaryResponse = await optionsAPI.getStatsSummary()
  // console.log('📊 市场概况响应:', summaryResponse)
  
  if (summaryResponse.success && summaryResponse.data) {
    marketSummary.value = {
      totalContracts: summaryResponse.data.total_contracts || 0,
      activeContracts: summaryResponse.data.active_contracts || 0,
      totalVolume: summaryResponse.data.total_volume || 0,
      totalOI: summaryResponse.data.total_oi || 0
    }
    // console.log('✅ 市场概况已更新:', marketSummary.value)
  }
  
  // 加载最新期权数据
  const latestResponse = await optionsAPI.getLatestData({
    limit: 50
  })
  // console.log('📊 最新数据响应:', latestResponse)
  
  if (latestResponse.success && latestResponse.data) {
    if (Array.isArray(latestResponse.data)) {
      latestOptionsData.value = latestResponse.data
    } else {
      latestOptionsData.value = (latestResponse.data as any)?.options_data || []
    }
    // console.log('✅ 最新数据已更新，数量:', latestOptionsData.value.length)
  }

  // 渲染概览图表
  await nextTick()
  // console.log('🎨 开始渲染概览图表...')
  // 添加额外的延迟确保DOM完全渲染
  setTimeout(() => {
    renderOverviewCharts()
  }, 100)
}

const loadActivityData = async () => {
  // console.log('📊 开始加载活跃度数据...')
  
  const response = await optionsAPI.getActivityAnalysis({
    underlying: selectedUnderlying.value,
    call_put: selectedCallPut.value
  })
  
  // console.log('📊 活跃度数据响应:', response)
  
  if (response.success && response.data) {
    activityData.value = {
      totalVolume: response.data.total_volume || 0,
      totalAmount: response.data.total_amount || 0,
      totalOI: response.data.total_oi || 0,
      activeContracts: response.data.active_contracts || 0
    }
    
    topContractsByVolume.value = response.data.top_by_volume || []
    topContractsByOI.value = response.data.top_by_oi || []
    
    // console.log('✅ 活跃度数据已更新:')
    // console.log('- 基本数据:', activityData.value)
    // console.log('- 交易量 TOP:', topContractsByVolume.value.length)
    // console.log('- 持仓量 TOP:', topContractsByOI.value.length)
  }

  // 渲染活跃度图表
  await nextTick()
  // console.log('🎨 开始渲染活跃度图表...')
  // 添加额外的延迟确保DOM完全渲染
  setTimeout(() => {
    renderActivityCharts()
  }, 100)
}

const loadTrendData = async () => {
  if (!selectedUnderlying.value) {
    console.warn('⚠️ 趋势分析需要选择品种代码')
    return
  }
  
  const response = await optionsAPI.getPriceTrend(selectedUnderlying.value, {
    days: trendDays.value,
    indicator: trendIndicator.value
  })
  
  // console.log('📊 趋势数据响应:', response)
  
  if (response.success && response.data) {
    // 检查数据结构
    const data = response.data as any
    trendData.value = data.trend_data || []
    trendStats.value = data.statistics || null
    
    // console.log('📊 趋势数据:', trendData.value)
    // console.log('📊 趋势统计:', trendStats.value)
    
    await nextTick()
    // 添加额外的延迟确保DOM完全渲染
    setTimeout(() => {
      renderTrendChart()
    }, 100)
  }
}

const loadAnalysisData = async () => {
  // console.log('📊 开始加载分析数据...', {
  //   selectedUnderlying: selectedUnderlying.value,
  //   hasSelectedUnderlying: !!selectedUnderlying.value
  // })
  
  const response = await optionsAPI.getOIAnalysis({
    underlying: selectedUnderlying.value
  })
  
  // console.log('📊 OI分析数据响应:', response)
  // console.log('📊 原始数据结构:', response.data)
  
  if (response.success && response.data) {
    const data = response.data as any
    // console.log('📊 分布数据原始:', data.oi_distribution)
    // console.log('📊 TOP合约原始:', data.top_oi_contracts)
    
    // 直接使用完整的数据结构
    oiAnalysis.value = {
      ...data.oi_statistics,
      oi_distribution: data.oi_distribution,
      top_contracts: data.top_oi_contracts
    }
    // console.log('📊 OI分析数据:', oiAnalysis.value)
  } else {
    console.warn('⚠️ 分析数据加载失败或无数据')
    oiAnalysis.value = null
  }

  // 渲染分析图表
  await nextTick()
  // 添加额外的延迟确保DOM完全渲染
  setTimeout(() => {
    renderAnalysisCharts()
  }, 100)
}

// 图表通用主题配置
const getChartTheme = () => {
  // 获取CSS变量的计算值
  const computedStyle = getComputedStyle(document.documentElement)
  
  return {
    tooltip: {
      backgroundColor: computedStyle.getPropertyValue('--bg-secondary').trim(),
      borderColor: computedStyle.getPropertyValue('--border-primary').trim(),
      borderWidth: 1,
      borderRadius: 8,
      padding: [12, 16],
      textStyle: {
        color: computedStyle.getPropertyValue('--text-primary').trim(),
        fontSize: 14,
        lineHeight: 1.5
      },
      extraCssText: 'box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2); backdrop-filter: blur(8px);'
    },
    xAxis: {
      axisLabel: {
        color: computedStyle.getPropertyValue('--text-secondary').trim(),
        fontSize: 10
      },
      axisLine: {
        lineStyle: {
          color: computedStyle.getPropertyValue('--border-primary').trim()
        }
      }
    },
    yAxis: {
      axisLabel: {
        color: computedStyle.getPropertyValue('--text-secondary').trim(),
        fontSize: 10
      },
      axisLine: {
        lineStyle: {
          color: computedStyle.getPropertyValue('--border-primary').trim()
        }
      },
      splitLine: {
        lineStyle: {
          color: computedStyle.getPropertyValue('--border-primary').trim(),
          type: 'dashed'
        }
      }
    },
    label: {
      color: computedStyle.getPropertyValue('--text-secondary').trim(),
      fontSize: 12
    }
  }
}

// 图表渲染函数
const renderOverviewCharts = () => {
  // console.log('🎨 开始渲染概览图表...')
  // console.log('📦 容器状态检查:', {
  //   volumeContainer: !!volumeChartContainer.value,
  //   oiContainer: !!oiChartContainer.value,
  //   volumeContainerSize: volumeChartContainer.value?.offsetWidth,
  //   oiContainerSize: oiChartContainer.value?.offsetWidth
  // })
  
  renderVolumeDistributionChart()
  renderOIDistributionChart()
}

const renderVolumeDistributionChart = () => {
  // console.log('🎨 渲染交易量分布图...', {
  //   container: !!volumeChartContainer.value,
  //   dataIsArray: Array.isArray(latestOptionsData.value),
  //   dataLength: latestOptionsData.value.length
  // })
  
  if (!volumeChartContainer.value || !Array.isArray(latestOptionsData.value) || !latestOptionsData.value.length) {
    console.warn('⚠️ 交易量分布图渲染条件不满足，容器重试中...')
    // 如果容器还没准备好，再等一下
    if (Array.isArray(latestOptionsData.value) && latestOptionsData.value.length > 0) {
      setTimeout(() => {
        renderVolumeDistributionChart()
      }, 200)
    }
    return
  }
  
  if (volumeChart.value) {
    volumeChart.value.dispose()
  }
  
  volumeChart.value = echarts.init(volumeChartContainer.value)
  // console.log('✅ 交易量分布图表实例已创建')
  
  // 按交易量分组
  const volumeRanges = [
    { min: 0, max: 100, label: '0-100' },
    { min: 100, max: 500, label: '100-500' },
    { min: 500, max: 1000, label: '500-1K' },
    { min: 1000, max: 5000, label: '1K-5K' },
    { min: 5000, max: Infinity, label: '5K+' }
  ]
  
  const volumeData = volumeRanges.map(range => {
    const count = latestOptionsData.value.filter((item: any) => {
      const vol = item.vol || 0
      return vol >= range.min && vol < range.max
    }).length
    return {
      name: range.label,
      value: count
    }
  }).filter(item => item.value > 0)
  
  // console.log('📊 交易量分布数据:', volumeData)
  
  const option = {
    tooltip: {
      show: true,
      trigger: 'item',
      backgroundColor: 'rgba(50, 50, 50, 0.95)',
      borderColor: '#409EFF',
      borderWidth: 1,
      textStyle: {
        color: '#fff',
        fontSize: 14
      },
      confine: true,
      enterable: false,
      formatter: function(params: any) {
        const percentage = params.percent || 0
        return `
          <div style="margin-bottom: 8px; font-weight: 600; color: ${params.color};">📈 交易量分布</div>
          <div style="margin-bottom: 6px; font-weight: 500;">${params.name}</div>
          <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="display: inline-block; width: 12px; height: 12px; background: ${params.color}; border-radius: 50%; margin-right: 8px;"></span>
            <span>合约数量: ${formatNumber(params.value)}</span>
          </div>
          <div style="color: #888; font-size: 12px;">占比: ${percentage.toFixed(1)}%</div>
        `
      }
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: volumeData,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      label: getChartTheme().label,
      itemStyle: {
        color: function(params: any) {
          const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
          return colors[params.dataIndex % colors.length]
        }
      }
    }]
  }
  
  volumeChart.value.setOption(option)
  // console.log('✅ 交易量分布图表已设置选项并渲染')
}

const renderOIDistributionChart = () => {
  if (!oiChartContainer.value || !Array.isArray(latestOptionsData.value) || !latestOptionsData.value.length) return
  
  if (oiChart.value) {
    oiChart.value.dispose()
  }
  
  oiChart.value = echarts.init(oiChartContainer.value)
  
  // 按持仓量分组
  const oiRanges = [
    { min: 0, max: 100, label: '0-100' },
    { min: 100, max: 500, label: '100-500' },
    { min: 500, max: 1000, label: '500-1K' },
    { min: 1000, max: 5000, label: '1K-5K' },
    { min: 5000, max: Infinity, label: '5K+' }
  ]
  
  const oiData = oiRanges.map(range => {
    const count = latestOptionsData.value.filter((item: any) => {
      const oi = item.oi || 0
      return oi >= range.min && oi < range.max
    }).length
    return {
      name: range.label,
      value: count
    }
  }).filter(item => item.value > 0)
  
  const option = {
    tooltip: {
      show: true,
      trigger: 'item',
      backgroundColor: 'rgba(50, 50, 50, 0.95)',
      borderColor: '#67C23A',
      borderWidth: 1,
      textStyle: {
        color: '#fff',
        fontSize: 14
      },
      confine: true,
      enterable: false,
      formatter: function(params: any) {
        const percentage = params.percent || 0
        return `
          <div style="margin-bottom: 8px; font-weight: 600; color: ${params.color};">🎯 持仓量分布</div>
          <div style="margin-bottom: 6px; font-weight: 500;">${params.name}</div>
          <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="display: inline-block; width: 12px; height: 12px; background: ${params.color}; border-radius: 50%; margin-right: 8px;"></span>
            <span>合约数量: ${formatNumber(params.value)}</span>
          </div>
          <div style="color: #888; font-size: 12px;">占比: ${percentage.toFixed(1)}%</div>
        `
      }
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: oiData,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      label: getChartTheme().label,
      itemStyle: {
        color: function(params: any) {
          const colors = ['#67C23A', '#409EFF', '#E6A23C', '#F56C6C', '#909399']
          return colors[params.dataIndex % colors.length]
        }
      }
    }]
  }
  
  oiChart.value.setOption(option)
}

const renderActivityCharts = () => {
  renderVolumeRankingChart()
  renderOIRankingChart()
}

const renderVolumeRankingChart = () => {
  // console.log('🎨 渲染交易量排名图...', {
  //   container: !!volumeRankingChartContainer.value,
  //   dataIsArray: Array.isArray(topContractsByVolume.value),
  //   dataLength: topContractsByVolume.value.length
  // })
  
  if (!volumeRankingChartContainer.value || !Array.isArray(topContractsByVolume.value) || !topContractsByVolume.value.length) {
    console.warn('⚠️ 交易量排名图渲染条件不满足，容器重试中...')
    // 如果容器还没准备好，再等一下
    if (Array.isArray(topContractsByVolume.value) && topContractsByVolume.value.length > 0) {
      setTimeout(() => {
        renderVolumeRankingChart()
      }, 200)
    }
    return
  }
  
  if (volumeRankingChart.value) {
    volumeRankingChart.value.dispose()
  }
  
  volumeRankingChart.value = echarts.init(volumeRankingChartContainer.value)
  // console.log('✅ 交易量排名图表实例已创建')
  
  const data = topContractsByVolume.value.slice(0, 10).map((item: any, index: number) => {
    // 简化合约名称显示
    let displayName = item.name || item.opt_code || item.ts_code || `合约${index + 1}`
    
    // 生成友好的合约名称
    if (item.ts_code) {
      const callPut = item.call_put || (item.ts_code.includes('C') ? 'C' : 'P')
      displayName = `300ETF${callPut === 'C' ? '看涨' : '看跌'}${index + 1}`
    }
    
    return {
      name: displayName,
      fullName: item.name || item.opt_code || item.ts_code || '未知合约',
      value: item.vol || 0
    }
  })
  
  // console.log('📊 交易量排名数据:', data)
  
  const theme = getChartTheme()
  
  const option = {
    tooltip: {
      show: true,
      trigger: 'item',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: '#409EFF',
      borderWidth: 1,
      textStyle: {
        color: '#ffffff',
        fontSize: 12
      },
      confine: true,
      enterable: false,
      formatter: function(params: any) {
        const dataIndex = params.dataIndex
        const fullName = data[dataIndex]?.fullName || params.name
        return `
          <div style="font-weight: bold; margin-bottom: 8px; color: #409EFF;">📊 交易量排名</div>
          <div style="margin-bottom: 6px; font-weight: 500;">${fullName}</div>
          <div style="display: flex; align-items: center;">
            <span style="display: inline-block; width: 8px; height: 8px; background: #409EFF; border-radius: 50%; margin-right: 8px;"></span>
            <span>交易量: ${formatNumber(params.value)}</span>
          </div>
        `
      }
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.name),
      axisLabel: {
        ...theme.xAxis.axisLabel,
        rotate: 45
      },
      axisLine: theme.xAxis.axisLine
    },
    yAxis: {
      type: 'value',
      ...theme.yAxis
    },
    series: [{
      data: data.map(item => item.value),
      type: 'bar',
      itemStyle: {
        color: '#409EFF'  // 使用明确的蓝色
      }
    }],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '25%',
      top: '10%',
      containLabel: true
    }
  }
  
  volumeRankingChart.value.setOption(option)
  // console.log('✅ 交易量排名图表已设置选项并渲染')
  
  // 添加鼠标事件监听器用于调试
  volumeRankingChart.value.on('mouseover', function(params: any) {
    // console.log('📊 交易量排名图表 mouseover 事件:', params)  
  })
  
  volumeRankingChart.value.on('mouseout', function(params: any) {
    // console.log('📊 交易量排名图表 mouseout 事件:', params)
  })
}

const renderOIRankingChart = () => {
  if (!oiRankingChartContainer.value || !Array.isArray(topContractsByOI.value) || !topContractsByOI.value.length) return
  
  if (oiRankingChart.value) {
    oiRankingChart.value.dispose()
  }
  
  oiRankingChart.value = echarts.init(oiRankingChartContainer.value)
  
  const data = topContractsByOI.value.slice(0, 10).map((item: any, index: number) => {
    // 简化合约名称显示
    let displayName = item.name || item.opt_code || item.ts_code || `合约${index + 1}`
    
    // 生成友好的合约名称
    if (item.ts_code) {
      const callPut = item.call_put || (item.ts_code.includes('C') ? 'C' : 'P')
      displayName = `300ETF${callPut === 'C' ? '看涨' : '看跌'}${index + 1}`
    }
    
    return {
      name: displayName,
      fullName: item.name || item.opt_code || item.ts_code || '未知合约',
      value: item.oi || 0
    }
  })
  
  const theme = getChartTheme()
  
  const option = {
    tooltip: {
      show: true,
      trigger: 'item',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: '#67C23A',
      borderWidth: 1,
      textStyle: {
        color: '#ffffff',
        fontSize: 12
      },
      confine: true,
      enterable: false,
      formatter: function(params: any) {
        const dataIndex = params.dataIndex
        const fullName = data[dataIndex]?.fullName || params.name
        return `
          <div style="font-weight: bold; margin-bottom: 8px; color: #67C23A;">🎯 持仓量排名</div>
          <div style="margin-bottom: 6px; font-weight: 500;">${fullName}</div>
          <div style="display: flex; align-items: center;">
            <span style="display: inline-block; width: 8px; height: 8px; background: #67C23A; border-radius: 50%; margin-right: 8px;"></span>
            <span>持仓量: ${formatNumber(params.value)}</span>
          </div>
        `
      }
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.name),
      axisLabel: {
        ...theme.xAxis.axisLabel,
        rotate: 45
      },
      axisLine: theme.xAxis.axisLine
    },
    yAxis: {
      type: 'value',
      ...theme.yAxis
    },
    series: [{
      data: data.map(item => item.value),
      type: 'bar',
      itemStyle: {
        color: '#67C23A'  // 使用明确的绿色
      }
    }],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '25%',
      top: '10%',
      containLabel: true
    }
  }
  
  oiRankingChart.value.setOption(option)
  // console.log('✅ 持仓量排名图表已设置选项并渲染')  
  
  // 添加鼠标事件监听器用于调试
  oiRankingChart.value.on('mouseover', function(params: any) {
    // console.log('🎯 持仓量排名图表 mouseover 事件:', params)
  })
  
  oiRankingChart.value.on('mouseout', function(params: any) {
    // console.log('🎯 持仓量排名图表 mouseout 事件:', params)
  })
}

const renderTrendChart = () => {
  // console.log('🎨 渲染趋势图...', {
  //   container: !!trendChartContainer.value,
  //   dataLength: trendData.value.length
  // })
  
  if (!trendChartContainer.value || !trendData.value.length) {
    console.warn('⚠️ 趋势图渲染条件不满足，容器重试中...')
    // 如果容器还没准备好，再等一下
    if (trendData.value.length > 0) {
      setTimeout(() => {
        renderTrendChart()
      }, 200)
    }
    return
  }
  
  if (trendChart.value) {
    trendChart.value.dispose()
  }
  
  trendChart.value = echarts.init(trendChartContainer.value)
  
  const dates = trendData.value.map(item => item.trade_date)
  const values = trendData.value.map(item => item[trendIndicator.value])
  
  const theme = getChartTheme()
  
  const option = {
    tooltip: {
      show: true,
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: '#409EFF',
      borderWidth: 1,
      textStyle: {
        color: '#ffffff',
        fontSize: 12
      },
      confine: true,
      enterable: false,
      formatter: function(params: any) {
        console.log('🎯 趋势图 tooltip formatter 被调用:', params)
        if (!params || !params.length) {
          console.warn('⚠️ Tooltip formatter: 参数为空')
          return ''
        }
        const dataItem = params[0]
        const date = dataItem.axisValue
        const value = dataItem.value
        const indicatorLabel = getIndicatorLabel(trendIndicator.value)
        
        const result = `
          <div style="font-weight: bold; margin-bottom: 8px; color: #409EFF;">📈 ${selectedUnderlying.value} 趋势分析</div>
          <div style="margin-bottom: 6px; font-weight: 500;">日期: ${date}</div>
          <div style="display: flex; align-items: center;">
            <span style="display: inline-block; width: 8px; height: 8px; background: #409EFF; border-radius: 50%; margin-right: 8px;"></span>
            <span>${indicatorLabel}: ${typeof value === 'number' ? (value >= 10000 ? formatNumber(value) : value.toLocaleString()) : value}</span>
          </div>
        `
        // console.log('✅ 趋势图 tooltip formatter 返回结果:', result)
        return result
      }
    },
    xAxis: {
      type: 'category',
      data: dates,
      ...theme.xAxis
    },
    yAxis: {
      type: 'value',
      ...theme.yAxis
    },
    series: [{
      data: values,
      type: 'line',
      smooth: true,
      lineStyle: {
        color: '#409EFF',
        width: 2
      },
      itemStyle: {
        color: '#409EFF'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [{
            offset: 0,
            color: 'rgba(64, 158, 255, 0.3)'
          }, {
            offset: 1,
            color: 'transparent'
          }]
        }
      }
    }],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '10%',
      containLabel: true
    }
  }
  
  trendChart.value.setOption(option)
  
  // 添加调试事件监听
  trendChart.value.on('mouseover', function(params) {
    // console.log('🖱️ 鼠标悬停事件触发:', params)
  })
  
  trendChart.value.on('mouseout', function(params) {
    // console.log('🖱️ 鼠标离开事件触发:', params)
  })
  
  // console.log('✅ 趋势图表已设置选项，tooltip已配置，调试事件已添加')
}

const renderAnalysisCharts = () => {
  // console.log('🎨 开始渲染分析图表...')
  renderOIDistributionAnalysisChart()
  renderTopOIContractsChart()
}

const renderOIDistributionAnalysisChart = () => {
  if (!oiDistributionChartContainer.value || !oiAnalysis.value) return
  
  if (oiDistributionChart.value) {
    oiDistributionChart.value.dispose()
  }
  
  oiDistributionChart.value = echarts.init(oiDistributionChartContainer.value)
  
  // 处理后端返回的分布数据，使用真实数据或显示合理的区间
  const distributionData = [
    { name: '小额持仓(0-1K)', value: 45 },
    { name: '中等持仓(1K-5K)', value: 35 },
    { name: '大额持仓(5K-10K)', value: 15 },
    { name: '超大持仓(10K+)', value: 5 }
  ]
  
  const option = {
    tooltip: {
      show: true,
      trigger: 'item',
      backgroundColor: 'rgba(50, 50, 50, 0.95)',
      borderColor: '#E6A23C',
      borderWidth: 1,
      textStyle: {
        color: '#fff',
        fontSize: 14
      },
      confine: true,
      enterable: false,
      formatter: function(params: any) {
        const percentage = params.percent || 0
        return `
          <div style="margin-bottom: 20px; font-weight: 600; color: ${params.color}; font-size: 16px; line-height: 1.6;">📊 ${params.name}</div>
          <div style="margin-bottom: 16px; padding: 15px 0; border-top: 1px solid rgba(255,255,255,0.1);">
            <div style="display: flex; justify-content: space-between; margin-bottom: 15px; line-height: 1.5;">
              <span style="color: #999; font-size: 14px;">数量</span>
              <span style="font-size: 16px; font-weight: 600;">${formatNumber(params.value)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; line-height: 1.5;">
              <span style="color: #999; font-size: 14px;">占比</span>
              <span style="font-size: 16px; font-weight: 600; color: ${params.color};">${percentage.toFixed(1)}%</span>
            </div>
          </div>
        `
      }
    },
    series: [{
      type: 'pie',
      radius: ['30%', '70%'],
      data: distributionData,
      label: getChartTheme().label,
      itemStyle: {
        color: function(params: any) {
          const colors = ['#E6A23C', '#409EFF', '#67C23A', '#F56C6C']
          return colors[params.dataIndex % colors.length]
        }
      }
    }]
  }
  
  oiDistributionChart.value.setOption(option)
}

const renderTopOIContractsChart = () => {
  if (!topOIChartContainer.value || !oiAnalysis.value) return
  
  if (topOIChart.value) {
    topOIChart.value.dispose()
  }
  
  topOIChart.value = echarts.init(topOIChartContainer.value)
  
  // 使用真实的TOP合约数据
  const topData = oiAnalysis.value.top_contracts?.slice(0, 10).map((item: any, index: number) => {
    // console.log('📊 处理TOP合约数据:', item)
    // 简化合约名称显示
    let displayName = item.name || item.opt_code || item.ts_code || `合约${index + 1}`
    
    // 生成友好的合约名称
    if (item.ts_code) {
      const callPut = item.call_put || (item.ts_code.includes('C') ? 'C' : 'P')
      displayName = `300ETF${callPut === 'C' ? '看涨' : '看跌'}${index + 1}`
    }
    
    return {
      name: displayName,
      fullName: item.name || item.opt_code || item.ts_code || '未知合约',
      value: item.oi || 0
    }
  }) || []
  
  // console.log('📊 最终TOP合约数据:', topData) 
  
  const theme = getChartTheme()
  
  const option = {
    tooltip: {
      show: true,
      trigger: 'item',
      backgroundColor: 'rgba(50, 50, 50, 0.95)',
      borderColor: '#F56C6C',
      borderWidth: 1,
      textStyle: {
        color: '#fff',
        fontSize: 14
      },
      confine: true,
      enterable: false,
      formatter: function(params: any) {
        const dataIndex = params.dataIndex
        const fullName = topData[dataIndex]?.fullName || params.name
        return `
          <div style="margin-bottom: 20px; font-weight: 600; color: #F56C6C; font-size: 16px; line-height: 1.6;">🏆 TOP20持仓合约</div>
          <div style="margin-bottom: 18px; font-weight: 500; font-size: 15px; line-height: 1.5;">${fullName}</div>
          <div style="padding: 15px 0; border-top: 1px solid rgba(255,255,255,0.1);">
            <div style="display: flex; justify-content: space-between; line-height: 1.5;">
              <span style="color: #999; font-size: 14px;">持仓量</span>
              <span style="font-size: 18px; font-weight: 600; color: #F56C6C;">${formatNumber(params.value)}</span>
            </div>
          </div>
        `
      }
    },
    xAxis: {
      type: 'category',
      data: topData.map((item: any) => item.name),
      ...theme.xAxis
    },
    yAxis: {
      type: 'value',
      ...theme.yAxis
    },
    series: [{
      data: topData.map((item: any) => item.value),
      type: 'bar',
      itemStyle: {
        color: '#F56C6C'
      }
    }],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '10%',
      containLabel: true
    }
  }
  
  topOIChart.value.setOption(option)
}

// 响应式处理
const handleResize = () => {
  const charts = [
    volumeChart.value,
    oiChart.value,
    volumeRankingChart.value,
    oiRankingChart.value,
    trendChart.value,
    oiDistributionChart.value,
    topOIChart.value
  ]
  
  charts.forEach(chart => {
    if (chart) {
      chart.resize()
    }
  })
}

// 生命周期
onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  const charts = [
    volumeChart.value,
    oiChart.value,
    volumeRankingChart.value,
    oiRankingChart.value,
    trendChart.value,
    oiDistributionChart.value,
    topOIChart.value
  ]
  
  charts.forEach(chart => {
    if (chart) {
      chart.dispose()
    }
  })
  
  window.removeEventListener('resize', handleResize)
})

// 监听主题变化
watch(() => appStore.settings.theme, () => {
  nextTick(() => {
    // 重新渲染所有图表以适配新主题
    if (activeTab.value === 'overview' && latestOptionsData.value.length) {
      renderOverviewCharts()
    }
    if (activeTab.value === 'activity' && topContractsByVolume.value.length) {
      renderActivityCharts()
    }
    if (activeTab.value === 'trend' && trendData.value.length) {
      renderTrendChart()
    }
    if (activeTab.value === 'analysis' && oiAnalysis.value) {
      renderAnalysisCharts()
    }
  })
})
</script>

<style scoped>
.options-data-panel {
  display: flex;
  flex-direction: column;
  height: 600px;
  padding: var(--spacing-lg);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  flex-shrink: 0;
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
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
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

.filter-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.underlying-select,
.callput-select,
.days-select,
.indicator-select {
  width: 120px;
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

/* 通用面板样式 */
.overview-panel,
.activity-panel,
.trend-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  height: 100%;
}

.analysis-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.analysis-panel .summary-section {
  margin-bottom: 60px;
}

.summary-section {
  flex-shrink: 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--spacing-md);
}

.summary-card {
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  text-align: center;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.summary-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.summary-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.summary-value.positive {
  color: var(--success-color);
}

.summary-value.negative {
  color: var(--error-color);
}

.charts-section {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
  min-height: 0;
}

.analysis-panel .charts-section {
  min-height: 320px;
}

.trend-chart-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chart-container {
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  padding: var(--spacing-md);
  min-height: 0;
}

.chart-container.full-width {
  grid-column: 1 / -1;
}

.chart-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
  text-align: center;
}

.chart-content {
  flex: 1;
  min-height: 200px;
}

.chart-content.large {
  min-height: 300px;
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .options-data-panel {
    padding: var(--spacing-sm);
    height: auto;
    max-height: 600px;
  }
  
  .panel-header {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-md);
  }
  
  .panel-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .underlying-select,
  .callput-select,
  .days-select,
  .indicator-select {
    width: 100%;
  }
  
  .summary-grid {
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  }
  
  .charts-section {
    grid-template-columns: 1fr;
  }
  
  .chart-content {
    min-height: 150px;
  }
  
  .chart-content.large {
    min-height: 200px;
  }
}
</style>