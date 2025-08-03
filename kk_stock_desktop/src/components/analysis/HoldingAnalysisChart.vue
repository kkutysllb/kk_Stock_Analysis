<template>
  <div class="holding-analysis-chart">
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="header-left">
        <div class="panel-title-section">
          <h3 class="section-title">
            <ChartBarIcon class="section-icon" />
            股指期货持仓分析
          </h3>
          <AskAIComponent :data-context="aiDataContext" />
        </div>
        <p class="section-subtitle">前20大机构持仓数据概览</p>
      </div>
      <div class="header-actions">
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYYMMDD"
          @change="onDateChange"
          size="default"
          class="date-picker"
          :clearable="false"
        />
        <el-button 
          @click="refreshData" 
          :loading="loading" 
          type="primary" 
          size="default"
          class="refresh-btn"
        >
          <ArrowPathIcon class="btn-icon" />
          刷新
        </el-button>
      </div>
    </div>
    
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>
    <div v-else-if="symbols.length > 0 && Object.keys(holdingDataBySymbol).length > 0" class="chart-container">
      <!-- 品种卡片网格 -->
      <div 
        v-for="symbol in symbols" 
        :key="symbol" 
        class="symbol-card"
      >
        <div class="card-header">
          <h3 class="symbol-name" :class="getSymbolClass(symbol)">
            <component :is="getSymbolIcon(symbol)" class="symbol-icon" />
            {{ getSymbolName(symbol) }}
          </h3>
          <div class="header-controls">
            <el-radio-group v-model="chartTypeBySymbol[symbol]" size="small">
              <el-radio-button value="ranking">机构排名</el-radio-button>
              <el-radio-button value="comparison">多空对比</el-radio-button>
              <el-radio-button value="trend">变化趋势</el-radio-button>
            </el-radio-group>
          </div>
        </div>
        
        <!-- 图表容器 -->
        <div class="chart-section">
          <div :id="`chart-${symbol}`" class="main-chart"></div>
        </div>
        
        <!-- 统计摘要 -->
        <div class="stats-summary">
          <div class="summary-grid">
            <div class="stat-item">
              <span class="stat-label">总多单</span>
              <span class="stat-value positive">{{ formatPosition(getSymbolSummary(symbol)?.total_long) }}</span>
              <span class="stat-change" :class="getChangeClass(getSymbolSummary(symbol)?.total_long_chg)">
                {{ formatChange(getSymbolSummary(symbol)?.total_long_chg) }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">总空单</span>
              <span class="stat-value negative">{{ formatPosition(getSymbolSummary(symbol)?.total_short) }}</span>
              <span class="stat-change" :class="getChangeClass(getSymbolSummary(symbol)?.total_short_chg)">
                {{ formatChange(getSymbolSummary(symbol)?.total_short_chg) }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">净持仓</span>
              <span class="stat-value" :class="getPositionClass(getSymbolSummary(symbol)?.net_position)">
                {{ formatPosition(getSymbolSummary(symbol)?.net_position) }}
              </span>
              <span class="stat-change" :class="getChangeClass(getSymbolSummary(symbol)?.net_position_chg)">
                {{ formatChange(getSymbolSummary(symbol)?.net_position_chg) }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">机构数量</span>
              <span class="stat-value">{{ getSymbolSummary(symbol)?.institution_count || 0 }}家</span>
            </div>
          </div>
        </div>

        <!-- 前5机构明细表格 -->
        <div class="top-institutions-table">
          <h4 class="table-title">前5大机构持仓明细</h4>
          <el-table 
            :data="getTop5Institutions(symbol)" 
            size="small"
            :show-header="true"
            style="width: 100%"
          >
            <el-table-column prop="rank" label="排名" width="50" align="center">
              <template #default="{ row }">
                <el-tag :type="getRankTagType(row.rank)" size="small">{{ row.rank }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="broker" label="机构名称" min-width="120" show-overflow-tooltip />
            <el-table-column prop="long_hld" label="多单" width="80" align="right">
              <template #default="{ row }">
                <span class="positive">{{ formatMiniPosition(row.long_hld) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="short_hld" label="空单" width="80" align="right">
              <template #default="{ row }">
                <span class="negative">{{ formatMiniPosition(row.short_hld) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="net_position" label="净额" width="80" align="right">
              <template #default="{ row }">
                <span :class="getPositionClass(row.net_position)">{{ formatMiniPosition(row.net_position) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="long_chg" label="多单变化" width="90" align="right">
              <template #default="{ row }">
                <span :class="getChangeClass(row.long_chg)">{{ formatChange(row.long_chg) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="short_chg" label="空单变化" width="90" align="right">
              <template #default="{ row }">
                <span :class="getChangeClass(row.short_chg)">{{ formatChange(row.short_chg) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>
    <div v-else class="no-data">
      <el-empty description="暂无持仓数据">
        <template #description>
          <p>请检查：</p>
          <ul style="text-align: left; margin: 10px 0;">
            <li>是否选择了正确的日期</li>
            <li>是否选择了有效的品种</li>
            <li>该日期是否有持仓数据</li>
          </ul>
        </template>
      </el-empty>
    </div>
    
    <!-- 期指分组持仓统计面板 -->
    <div class="group-holding-section">
      <FuturesOverviewPanel />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { futuresAPI } from '@/api/futures'
import { useAppStore } from '@/stores/app'
import { 
  ChartBarIcon, 
  ArrowTrendingUpIcon, 
  CurrencyDollarIcon, 
  BuildingOfficeIcon,
  ArrowPathIcon 
} from '@heroicons/vue/24/outline'
import FuturesOverviewPanel from '@/components/FuturesOverviewPanel.vue'
import AskAIComponent from '../AskAIComponent.vue'

interface Props {
  symbols: string[]
  date: string
  chartType: 'ranking' | 'structure' | 'changes'
  loading: boolean
}

interface InstitutionHolding {
  rank: number
  broker: string
  long_hld: number
  short_hld: number
  net_position: number
  long_chg: number
  short_chg: number
  net_chg: number
  vol: number
  vol_chg: number
}

interface SymbolHoldingData {
  symbol: string
  trade_date: string
  top20_institutions: InstitutionHolding[]
  daily_trends: Array<{
    trade_date: string
    total_long: number
    total_short: number
    net_position: number
    total_long_chg: number
    total_short_chg: number
    net_position_chg: number
    institution_count: number
  }>
}

const props = defineProps<Props>()
const appStore = useAppStore()

// 响应式数据
const holdingDataBySymbol = ref<Record<string, SymbolHoldingData>>({})
const chartInstances = ref<Map<string, echarts.ECharts>>(new Map())
const chartTypeBySymbol = ref<Record<string, 'ranking' | 'comparison' | 'trend'>>({})
const selectedDate = ref(new Date().toISOString().split('T')[0].replace(/-/g, ''))

// 初始化每个品种的图表类型
const initChartTypes = () => {
  props.symbols.forEach(symbol => {
    if (!chartTypeBySymbol.value[symbol]) {
      chartTypeBySymbol.value[symbol] = 'ranking'
    }
  })
}

// 获取主题相关颜色
const isDarkMode = computed(() => appStore.isDarkMode)
const textColor = computed(() => isDarkMode.value ? '#ffffff' : '#0f172a')
const borderColor = computed(() => isDarkMode.value ? 'rgba(255, 255, 255, 0.1)' : 'rgba(15, 23, 42, 0.1)')
const backgroundColor = computed(() => isDarkMode.value ? 'rgba(42, 42, 42, 0.7)' : 'rgba(255, 255, 255, 0.7)')
const positiveColor = computed(() => isDarkMode.value ? '#ef4444' : '#f87171')
const negativeColor = computed(() => isDarkMode.value ? '#22c55e' : '#4ade80')

// 获取品种名称
const getSymbolName = (symbol: string): string => {
  const symbolNames: Record<string, string> = {
    'IF': 'IF-沪深300',
    'IC': 'IC-中证500',
    'IH': 'IH-上证50',
    'IM': 'IM-中证1000'
  }
  return symbolNames[symbol] || symbol
}

// AI数据上下文
const aiDataContext = computed(() => {
  const dateStr = selectedDate.value ? `${selectedDate.value.slice(0,4)}-${selectedDate.value.slice(4,6)}-${selectedDate.value.slice(6,8)}` : ''
  const symbols = props.symbols.join(', ')
  
  // 计算整体统计
  const getOverallStats = () => {
    let totalLong = 0
    let totalShort = 0
    let totalNetPosition = 0
    let totalLongChg = 0
    let totalShortChg = 0
    let totalNetChg = 0
    let totalInstitutions = 0
    
    props.symbols.forEach(symbol => {
      const summary = getSymbolSummary(symbol)
      if (summary) {
        totalLong += summary.total_long
        totalShort += summary.total_short
        totalNetPosition += summary.net_position
        totalLongChg += summary.total_long_chg
        totalShortChg += summary.total_short_chg
        totalNetChg += summary.net_position_chg
        totalInstitutions += summary.institution_count
      }
    })
    
    return {
      totalLong,
      totalShort,
      totalNetPosition,
      totalLongChg,
      totalShortChg,
      totalNetChg,
      totalInstitutions
    }
  }
  
  const overallStats = getOverallStats()
  
  return {
    type: 'futures_holding_analysis',
    title: '股指期货持仓分析',
    period: dateStr,
    data: {
      date: dateStr,
      symbols: props.symbols,
      holdingDataBySymbol: holdingDataBySymbol.value,
      overallStats
    },
    summary: `股指期货持仓分析（${dateStr}）：

## 分析概况
- 分析日期：${dateStr}
- 分析品种：${symbols}
- 数据来源：前20大机构持仓数据
- 分析维度：多空持仓、机构排名、持仓变化

## 各品种持仓分析
${props.symbols.map(symbol => {
  const summary = getSymbolSummary(symbol)
  const top5 = getTop5Institutions(symbol)
  if (!summary) return `### ${getSymbolName(symbol)}（${symbol}）\n- 暂无持仓数据`
  
  return `### ${getSymbolName(symbol)}（${symbol}）
- 总多单：${formatPosition(summary.total_long)}手
- 总空单：${formatPosition(summary.total_short)}手
- 净持仓：${formatPosition(summary.net_position)}手（${summary.net_position > 0 ? '净多头' : summary.net_position < 0 ? '净空头' : '平衡'}）
- 多单变化：${formatChange(summary.total_long_chg)}手
- 空单变化：${formatChange(summary.total_short_chg)}手
- 净持仓变化：${formatChange(summary.net_position_chg)}手
- 参与机构：${summary.institution_count}家

#### 前5大机构明细
${top5.map((inst, idx) => 
  `${idx + 1}. ${inst.broker}：多单${formatMiniPosition(inst.long_hld)}，空单${formatMiniPosition(inst.short_hld)}，净额${formatMiniPosition(inst.net_position)}`
).join('\n')}`
}).join('\n\n')}

## 市场整体统计
- 总多单量：${formatPosition(overallStats.totalLong)}手
- 总空单量：${formatPosition(overallStats.totalShort)}手
- 市场净持仓：${formatPosition(overallStats.totalNetPosition)}手
- 多单总变化：${formatChange(overallStats.totalLongChg)}手
- 空单总变化：${formatChange(overallStats.totalShortChg)}手
- 净持仓总变化：${formatChange(overallStats.totalNetChg)}手
- 总参与机构：${overallStats.totalInstitutions}家

## 市场结构分析
- 市场偏向：${overallStats.totalNetPosition > 0 ? '整体偏多头' : overallStats.totalNetPosition < 0 ? '整体偏空头' : '多空相对平衡'}
- 资金流向：${overallStats.totalNetChg > 0 ? '增加多头持仓' : overallStats.totalNetChg < 0 ? '增加空头持仓' : '持仓变化平衡'}
- 活跃程度：根据机构参与数量和持仓变化幅度评估

## 重点机构分析
${props.symbols.map(symbol => {
  const top3 = getTop5Institutions(symbol).slice(0, 3)
  if (top3.length === 0) return ''
  return `### ${getSymbolName(symbol)}前3大机构
${top3.map(inst => 
  `- ${inst.broker}：排名第${inst.rank}，净持仓${formatMiniPosition(inst.net_position)}手`
).join('\n')}`
}).filter(text => text).join('\n\n')}

## 分析要点
- 机构持仓排名反映市场参与者的实力和偏好
- 多空对比显示市场情绪和预期方向
- 持仓变化趋势揭示资金流向和操作策略
- 前20大机构数据具有较强的市场代表性
- 结合价格走势分析持仓数据的有效性
`
  }
})

// 获取品种样式类
const getSymbolClass = (symbol: string): string => {
  const symbolClasses: Record<string, string> = {
    'IF': 'symbol-if',
    'IC': 'symbol-ic', 
    'IH': 'symbol-ih',
    'IM': 'symbol-im'
  }
  return symbolClasses[symbol] || ''
}

// 获取品种图标
const getSymbolIcon = (symbol: string) => {
  const symbolIcons: Record<string, any> = {
    'IF': ChartBarIcon,
    'IC': ArrowTrendingUpIcon,
    'IH': CurrencyDollarIcon,
    'IM': BuildingOfficeIcon
  }
  return symbolIcons[symbol] || ChartBarIcon
}

// 获取品种汇总数据
const getSymbolSummary = (symbol: string) => {
  const symbolData = holdingDataBySymbol.value[symbol]
  if (!symbolData || !symbolData.top20_institutions.length) return null
  
  const institutions = symbolData.top20_institutions
  return {
    total_long: institutions.reduce((sum, inst) => sum + inst.long_hld, 0),
    total_short: institutions.reduce((sum, inst) => sum + inst.short_hld, 0),
    net_position: institutions.reduce((sum, inst) => sum + inst.net_position, 0),
    total_long_chg: institutions.reduce((sum, inst) => sum + inst.long_chg, 0),
    total_short_chg: institutions.reduce((sum, inst) => sum + inst.short_chg, 0),
    net_position_chg: institutions.reduce((sum, inst) => sum + inst.net_chg, 0),
    institution_count: institutions.length
  }
}

// 获取前5机构数据
const getTop5Institutions = (symbol: string): InstitutionHolding[] => {
  const symbolData = holdingDataBySymbol.value[symbol]
  return symbolData?.top20_institutions.slice(0, 5) || []
}

// 获取排名标签类型
const getRankTagType = (rank: number): string => {
  if (rank === 1) return 'danger'
  if (rank <= 3) return 'warning'
  if (rank <= 5) return 'success'
  return 'info'
}

// 初始化图表的统一函数
const initCharts = async () => {
  initChartTypes()
  await fetchTop20HoldingData()
  await initAllCharts()
}

// 监听props变化
watch(() => props.symbols, () => {
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
    initAllCharts()
  })
})

// 移除watch监听器，只使用@change事件处理器避免重复触发
// 日期变化现在完全由onDateChange处理

// 监听图表类型变化
watch(() => chartTypeBySymbol.value, () => {
  nextTick(() => {
    initAllCharts()
  })
}, { deep: true })

// 获取前20机构持仓数据
const fetchTop20HoldingData = async () => {
  if (!selectedDate.value || props.symbols.length === 0) {
    return
  }
  
  try {
    const response = await futuresAPI.getFuturesTop20Holdings(
      props.symbols.join(','),
      selectedDate.value,
      7 // 获取最近7天的趋势数据
    )
    
    if (response.success && response.data) {
      holdingDataBySymbol.value = response.data.holdings_by_symbol || {}
      // 数据更新后重新渲染图表
      await nextTick()
      await initAllCharts()
    } else {
      console.error('获取前20机构持仓数据失败:', response)
      // 如果新接口失败，回退到原有逻辑
      await fetchFallbackData()
    }
  } catch (error) {
    console.error('获取前20机构持仓数据异常:', error)
    // 如果新接口失败，回退到原有逻辑  
    await fetchFallbackData()
  }
}

// 回退数据获取逻辑
const fetchFallbackData = async () => {
  try {
    // 使用原有的getFuturesHolding接口为每个品种获取数据
    for (const symbol of props.symbols) {
      const response = await futuresAPI.getFuturesHolding(
        symbol,
        selectedDate.value,
        selectedDate.value,
        20 // 获取前20名
      )
      
             if (response.success && response.data && response.data.holding_data && response.data.holding_data.length > 0) {
         const holdingData = response.data.holding_data
        
        // 按多头持仓量排序并添加排名
        const sortedData = holdingData
          .sort((a, b) => b.long_hld - a.long_hld)
          .map((item, index) => ({
            rank: index + 1,
            broker: item.broker,
            long_hld: item.long_hld,
            short_hld: item.short_hld,
            net_position: item.long_hld - item.short_hld,
            long_chg: item.long_chg,
            short_chg: item.short_chg,
            net_chg: item.long_chg - item.short_chg,
            vol: item.vol,
            vol_chg: item.vol_chg
          }))
        
        holdingDataBySymbol.value[symbol] = {
          symbol,
          trade_date: selectedDate.value,
          top20_institutions: sortedData,
          daily_trends: [] // 回退模式下没有趋势数据
        }
      }
    }
    
    // 回退数据更新后重新渲染图表
    await nextTick()
    await initAllCharts()
  } catch (error) {
    console.error('回退数据获取失败:', error)
  }
}

// 初始化所有图表
const initAllCharts = async () => {
  await nextTick()
  
  for (const symbol of props.symbols) {
    const chartId = `chart-${symbol}`
    const chartElement = document.getElementById(chartId)
    
    if (chartElement && holdingDataBySymbol.value[symbol]) {
      // 销毁已存在的图表实例
      const existingChart = chartInstances.value.get(chartId)
      if (existingChart) {
        existingChart.dispose()
      }
      
      // 创建新的图表实例
      const chart = echarts.init(chartElement)
      const chartType = chartTypeBySymbol.value[symbol] || 'ranking'
      const option = createChartOption(symbol, chartType)
      chart.setOption(option)
      
      // 存储图表实例
      chartInstances.value.set(chartId, chart)
    }
  }
}

// 创建图表配置
const createChartOption = (symbol: string, chartType: 'ranking' | 'comparison' | 'trend') => {
  const symbolData = holdingDataBySymbol.value[symbol]
  if (!symbolData) return {}
  
  switch (chartType) {
    case 'ranking':
      return createRankingChartOption(symbolData)
    case 'comparison':
      return createComparisonChartOption(symbolData)
    case 'trend':
      return createTrendChartOption(symbolData)
    default:
      return createRankingChartOption(symbolData)
  }
}

// 创建机构排名图表配置
const createRankingChartOption = (symbolData: SymbolHoldingData) => {
  const top20 = symbolData.top20_institutions.slice(0, 20)
  
  return {
    title: {
      text: '前20大机构持仓排名',
      textStyle: { 
        fontSize: 14,
        color: textColor.value
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: backgroundColor.value,
      textStyle: { color: textColor.value },
      formatter: (params: any) => {
        const data = params[0]
        const institution = top20[data.dataIndex]
        return `
          <div>
            <strong>${institution.broker}</strong><br/>
            排名: ${institution.rank}<br/>
            多单: ${formatPosition(institution.long_hld)}<br/>
            空单: ${formatPosition(institution.short_hld)}<br/>
            净额: ${formatPosition(institution.net_position)}
          </div>
        `
      }
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '25%',
      top: '15%'
    },
    xAxis: {
      type: 'category',
      data: top20.map(item => item.broker),
      axisLabel: {
        rotate: 45,
        color: textColor.value,
        fontSize: 9,
        interval: 0, // 显示所有标签
        overflow: 'none'
      },
      axisLine: {
        lineStyle: { color: borderColor.value }
      }
    },
    yAxis: {
      type: 'value',
      name: '持仓量(手)',
      axisLabel: {
        color: textColor.value,
        formatter: (value: number) => formatMiniPosition(value)
      },
      axisLine: {
        lineStyle: { color: borderColor.value }
      },
      splitLine: {
        lineStyle: { color: borderColor.value }
      }
    },
    series: [{
      name: '净持仓',
      type: 'bar',
      data: top20.map(item => item.net_position),
      itemStyle: {
        color: (params: any) => {
          const value = params.value
          return value >= 0 ? positiveColor.value : negativeColor.value
        }
      }
    }]
  }
}

// 创建多空对比图表配置
const createComparisonChartOption = (symbolData: SymbolHoldingData) => {
  const top20 = symbolData.top20_institutions.slice(0, 20)
  
  return {
    title: {
      text: '前20大机构多空持仓对比',
      textStyle: { 
        fontSize: 14,
        color: textColor.value
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: backgroundColor.value,
      textStyle: { color: textColor.value }
    },
    legend: {
      data: ['多单', '空单'],
      textStyle: { color: textColor.value }
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '25%',
      top: '15%'
    },
    xAxis: {
      type: 'category',
      data: top20.map(item => item.broker),
      axisLabel: {
        rotate: 45,
        color: textColor.value,
        fontSize: 9,
        interval: 0, // 显示所有标签
        overflow: 'none'
      },
      axisLine: {
        lineStyle: { color: borderColor.value }
      }
    },
    yAxis: {
      type: 'value',
      name: '持仓量(手)',
      axisLabel: {
        color: textColor.value,
        formatter: (value: number) => formatMiniPosition(value)
      },
      axisLine: {
        lineStyle: { color: borderColor.value }
      },
      splitLine: {
        lineStyle: { color: borderColor.value }
      }
    },
    series: [{
      name: '多单',
      type: 'bar',
      data: top20.map(item => item.long_hld),
      itemStyle: { color: positiveColor.value }
    }, {
      name: '空单',
      type: 'bar',
      data: top20.map(item => item.short_hld),
      itemStyle: { color: negativeColor.value }
    }]
  }
}

// 创建变化趋势图表配置
const createTrendChartOption = (symbolData: SymbolHoldingData) => {
  const trends = symbolData.daily_trends || []
  
  if (trends.length === 0) {
    return {
      title: {
        text: '暂无趋势数据',
        textStyle: { 
          fontSize: 14,
          color: textColor.value
        }
      }
    }
  }
  
  return {
    title: {
      text: '持仓变化趋势（最近7天）',
      textStyle: { 
        fontSize: 14,
        color: textColor.value
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: backgroundColor.value,
      textStyle: { color: textColor.value }
    },
    legend: {
      data: ['多单', '空单', '净持仓'],
      textStyle: { color: textColor.value }
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      top: '15%'
    },
    xAxis: {
      type: 'category',
      data: trends.map(item => item.trade_date.substring(4, 8)),
      axisLabel: {
        color: textColor.value
      },
      axisLine: {
        lineStyle: { color: borderColor.value }
      }
    },
    yAxis: {
      type: 'value',
      name: '持仓量(手)',
      axisLabel: {
        color: textColor.value,
        formatter: (value: number) => formatMiniPosition(value)
      },
      axisLine: {
        lineStyle: { color: borderColor.value }
      },
      splitLine: {
        lineStyle: { color: borderColor.value }
      }
    },
    series: [{
      name: '多单',
      type: 'line',
      data: trends.map(item => item.total_long),
      lineStyle: { color: positiveColor.value },
      smooth: true
    }, {
      name: '空单',
      type: 'line',
      data: trends.map(item => item.total_short),
      lineStyle: { color: negativeColor.value },
      smooth: true
    }, {
      name: '净持仓',
      type: 'line',
      data: trends.map(item => item.net_position),
      lineStyle: { color: '#3b82f6' },
      smooth: true
    }]
  }
}

// 格式化函数
const formatPosition = (value: number | undefined | null): string => {
  if (value === undefined || value === null || isNaN(value)) {
    return '0手'
  }
  if (Math.abs(value) >= 10000) {
    return (value / 10000).toFixed(1) + '万手'
  }
  return value.toString() + '手'
}

const formatMiniPosition = (value: number | undefined): string => {
  if (value === undefined || value === null) return '--'
  if (Math.abs(value) >= 10000) {
    return `${(value / 10000).toFixed(1)}万`
  }
  return value.toString()
}

const formatChange = (value: number | undefined | null): string => {
  if (value === undefined || value === null || isNaN(value)) {
    return '0'
  }
  const sign = value >= 0 ? '+' : ''
  return sign + formatMiniPosition(value)
}

const getPositionClass = (value: number | undefined | null): string => {
  if (value === undefined || value === null || isNaN(value)) {
    return 'neutral'
  }
  return value >= 0 ? 'positive' : 'negative'
}

const getChangeClass = (value: number | undefined | null): string => {
  if (value === undefined || value === null || isNaN(value)) {
    return 'neutral'
  }
  return value >= 0 ? 'positive' : 'negative'
}

// 组件挂载和卸载
onMounted(async () => {
  console.log('组件挂载，初始日期:', selectedDate.value, 'props日期:', props.date)
  // 不强制同步外部日期，保持组件内部日期选择的独立性
  
  await nextTick()
  await initCharts()
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  // 清理事件监听器
  window.removeEventListener('resize', handleResize)
  // 清理图表实例
  chartInstances.value.forEach(chart => {
    chart.dispose()
  })
})

const handleResize = () => {
  chartInstances.value.forEach(chart => {
    chart.resize()
  })
}

// 日期变化处理
const onDateChange = (date: string) => {
  if (date) {
    selectedDate.value = date
    fetchTop20HoldingData()
  }
}

// 刷新数据
const refreshData = () => {
  holdingDataBySymbol.value = {}
  fetchTop20HoldingData()
}
</script>

<style scoped>
.holding-analysis-chart {
  padding: 0;
}

/* 卡片头部样式 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 16px;
  box-shadow: var(--el-box-shadow-light);
  border: 1px solid var(--el-border-color-light);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}

.section-icon {
  width: 20px;
  height: 20px;
  color: var(--el-color-primary);
}

.section-subtitle {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.date-picker {
  width: 180px;
}

.refresh-btn {
  min-width: 80px;
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.chart-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  height: 100%;
}

.symbol-card {
  background: var(--el-bg-color);
  border-radius: 16px;
  padding: 20px;
  box-shadow: var(--el-box-shadow-light);
  transition: all 0.3s ease;
  border: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
}

.symbol-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--el-box-shadow-dark);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.panel-title-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-lg);
}

.symbol-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.symbol-icon {
  width: 20px;
  height: 20px;
}

/* 品种特定颜色 */
.symbol-if {
  color: #ff6b35; /* 橙红色 - IF沪深300 */
}

.symbol-ic {
  color: #4a9eff; /* 蓝色 - IC中证500 */
}

.symbol-ih {
  color: #06d6a0; /* 青色 - IH上证50 */
}

.symbol-im {
  color: #ffd93d; /* 金色 - IM中证1000 */
}

.header-controls .el-radio-group {
  --el-radio-button-font-size: 11px;
}

.chart-section {
  margin-bottom: 16px;
}

.main-chart {
  width: 100%;
  height: 450px;
}

.stats-summary {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 2px;
}

.stat-change {
  font-size: 11px;
  font-weight: 500;
}

.top-institutions-table {
  flex: 1;
}

.table-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 12px 0;
}

.positive {
  color: var(--el-color-success);
}

.negative {
  color: var(--el-color-danger);
}

.neutral {
  color: var(--el-text-color-primary);
}

.no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: var(--el-text-color-placeholder);
  padding: 40px 20px;
}

.loading-container {
  padding: 40px;
  grid-column: 1 / -1;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .chart-container {
    grid-template-columns: 1fr;
  }
  
  .main-chart {
    height: 400px;
  }
}

@media (max-width: 768px) {
  .symbol-card {
    padding: 16px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
    padding: 16px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .date-picker {
    width: 140px;
  }
  
  .summary-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .main-chart {
    height: 350px;
  }
}

/* 分组持仓统计面板样式 */
.group-holding-section {
  margin-top: 32px;
  padding-top: 32px;
  border-top: 1px solid var(--el-border-color-light);
}
</style>
