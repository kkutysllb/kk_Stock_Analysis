<template>
  <div class="margin-trading-panel glass-effect">
    <!-- 面板标题 -->
    <div class="panel-header">
      <div class="panel-title">
        <PresentationChartLineIcon class="title-icon" />
        <span>融资融券分析</span>
        <el-tag v-if="selectedStock" size="small" type="info">
          {{ selectedStock.code }} {{ selectedStock.name }}
        </el-tag>
      </div>
      <div class="panel-actions">
        <el-select 
          v-model="analysisDays" 
          size="small" 
          style="width: 80px; margin-right: 8px;"
          @change="onDaysChange"
        >
          <el-option label="7天" :value="7" />
          <el-option label="15天" :value="15" />
          <el-option label="30天" :value="30" />
          <el-option label="60天" :value="60" />
        </el-select>
        <el-button 
          size="small" 
          type="primary"
          :loading="analyzing"
          :disabled="!hasValidStock"
          @click="triggerAnalysis"
        >
          <AdjustmentsHorizontalIcon class="action-icon" v-if="!analyzing" />
          {{ analyzing ? '分析中...' : '开始分析' }}
        </el-button>
      </div>
    </div>

    <!-- 面板内容 -->
    <div class="panel-content scrollable-content">
      <!-- 分析结果 -->
      <div class="analysis-result">
        <!-- 综合评分卡片 -->
        <div class="result-section">
          <h4 class="section-title">
            <StarIcon class="title-icon" />
            融资融券综合评估
          </h4>
          <div class="score-overview">
            <div class="score-card">
              <div class="score-main">
                <div class="score-value">{{ analysisResult?.overall_score?.toFixed(1) || 'N/A' }}</div>
                <div class="score-label">综合评分</div>
                <div class="score-max">/100</div>
              </div>
              <div class="score-details">
                <div class="score-item">
                  <span class="label">投资建议</span>
                  <el-tag 
                    size="small" 
                    :type="getRecommendationType(analysisResult?.recommendation)"
                  >
                    {{ getRecommendationText(analysisResult?.recommendation) }}
                  </el-tag>
                </div>
                <div class="score-item">
                  <span class="label">风险等级</span>
                  <el-tag 
                    size="small" 
                    :type="getRiskType(analysisResult?.risk_level)"
                  >
                    {{ getRiskText(analysisResult?.risk_level) }}
                  </el-tag>
                </div>
                <div class="score-item">
                  <span class="label">分析周期</span>
                  <span class="value">{{ analysisResult?.analysis_period || 'N/A' }}</span>
                </div>
                <div class="score-item">
                  <span class="label">数据条数</span>
                  <span class="value">{{ analysisResult?.data_count || 0 }}条</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 趋势分析 -->
        <div class="result-section">
          <h4 class="section-title">
            <ArrowTrendingUpIcon class="title-icon" />
            融资融券趋势
          </h4>
          <div class="trend-grid">
            <div class="trend-card">
              <div class="trend-header">
                <ArrowTrendingUpIcon class="trend-icon financing" />
                <span class="trend-title">融资趋势</span>
              </div>
              <div class="trend-content">
                <div class="trend-direction">
                  <el-tag 
                    size="large" 
                    :type="getTrendType(analysisResult?.financing_trend)"
                  >
                    {{ getTrendText(analysisResult?.financing_trend) }}
                  </el-tag>
                </div>
                <div class="trend-metrics">
                  <div class="metric-row">
                    <span class="metric-label">平均余额</span>
                    <span class="metric-value">
                      {{ formatAmount(analysisResult?.avg_financing_balance) }}
                    </span>
                  </div>
                  <div class="metric-row">
                    <span class="metric-label">平均买入</span>
                    <span class="metric-value">
                      {{ formatAmount(analysisResult?.avg_financing_buy) }}
                    </span>
                  </div>
                  <div class="metric-row">
                    <span class="metric-label">净流入</span>
                    <span class="metric-value" :class="{ 'positive': analysisResult?.net_financing_flow > 0, 'negative': analysisResult?.net_financing_flow < 0 }">
                      {{ formatAmount(analysisResult?.net_financing_flow, true) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div class="trend-card">
              <div class="trend-header">
                <ArrowTrendingDownIcon class="trend-icon securities" />
                <span class="trend-title">融券趋势</span>
              </div>
              <div class="trend-content">
                <div class="trend-direction">
                  <el-tag 
                    size="large" 
                    :type="getTrendType(analysisResult?.securities_trend)"
                  >
                    {{ getTrendText(analysisResult?.securities_trend) }}
                  </el-tag>
                </div>
                <div class="trend-metrics">
                  <div class="metric-row">
                    <span class="metric-label">平均余额</span>
                    <span class="metric-value">
                      {{ formatAmount(analysisResult?.avg_securities_balance) }}
                    </span>
                  </div>
                  <div class="metric-row">
                    <span class="metric-label">平均卖出</span>
                    <span class="metric-value">
                      {{ formatAmount(analysisResult?.avg_securities_sell) }}
                    </span>
                  </div>
                  <div class="metric-row">
                    <span class="metric-label">净流入</span>
                    <span class="metric-value" :class="{ 'positive': analysisResult?.net_securities_flow > 0, 'negative': analysisResult?.net_securities_flow < 0 }">
                      {{ formatAmount(analysisResult?.net_securities_flow, true) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 图表展示 -->
        <div class="result-section">
          <h4 class="section-title">
            <ChartBarIcon class="title-icon" />
            余额趋势图表
          </h4>
          <div class="chart-container">
            <div ref="chartContainer" class="chart-element"></div>
          </div>
        </div>

        <!-- 详细数据表格 -->
        <div class="result-section">
          <h4 class="section-title">
            <TableCellsIcon class="title-icon" />
            详细数据
          </h4>
          <div class="table-container">
            <el-table 
              :data="marginData" 
              stripe 
              size="small"
              :loading="loadingData"
              style="width: 100%"
              :show-overflow-tooltip="true"
            >
              <el-table-column prop="trade_date" label="日期" min-width="80">
                <template #default="{ row }">
                  <span class="date-text">{{ formatDate(row.trade_date) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="融资余额" min-width="100">
                <template #default="{ row }">
                  <span class="amount-text financing">{{ formatAmount(row.rzye) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="融资买入" min-width="90">
                <template #default="{ row }">
                  <span class="amount-text buy">{{ formatAmount(row.rzmre) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="融资偿还" min-width="90">
                <template #default="{ row }">
                  <span class="amount-text repay">{{ formatAmount(row.rzche) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="融券余额" min-width="100">
                <template #default="{ row }">
                  <span class="amount-text securities">{{ formatAmount(row.rqye) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="融券卖出" min-width="80" class-name="mobile-hide">
                <template #default="{ row }">
                  <span class="amount-text sell">{{ formatAmount(row.rqmcl) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="融券偿还" min-width="80" class-name="mobile-hide">
                <template #default="{ row }">
                  <span class="amount-text repay">{{ formatAmount(row.rqchl) }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- 风险提示 -->
        <div v-if="analysisResult?.risk_factors?.length > 0" class="result-section">
          <h4 class="section-title">
            <ExclamationTriangleIcon class="title-icon" />
            风险提示
          </h4>
          <div class="risk-factors">
            <el-alert
              v-for="(factor, index) in analysisResult.risk_factors"
              :key="index"
              :title="factor"
              type="warning"
              :closable="false"
              show-icon
            />
          </div>
        </div>

      </div>

      <!-- 无数据状态 -->
      <div v-if="!hasAnalysisResult && !analyzing" class="empty-state">
        <div class="empty-content">
          <PresentationChartLineIcon class="empty-icon" />
          <h3>融资融券分析</h3>
          <p>选择股票并点击"开始分析"查看详细的融资融券数据分析</p>
          <div class="empty-features">
            <div class="feature-item">
              <CheckCircleIcon class="feature-icon" />
              <span>融资融券趋势分析</span>
            </div>
            <div class="feature-item">
              <CheckCircleIcon class="feature-icon" />
              <span>资金流向监控</span>
            </div>
            <div class="feature-item">
              <CheckCircleIcon class="feature-icon" />
              <span>风险评估与建议</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import {
  PresentationChartLineIcon,
  AdjustmentsHorizontalIcon,
  StarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChartBarIcon,
  TableCellsIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/vue/24/outline'

import { apiClient } from '@/api/base'

// Props
interface Props {
  selectedStock?: {
    code: string
    name: string
    poolId?: string
  } | null
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'analysis-completed': [result: any]
  'stock-selected': [stock: any]
}>()

// 响应式数据
const analyzing = ref(false)
const loadingData = ref(false)
const analysisDays = ref(30)
const analysisResult = ref<any>(null)
const marginData = ref<any[]>([])
const chartContainer = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

// 计算属性
const hasValidStock = computed(() => {
  return props.selectedStock && props.selectedStock.code
})

const hasAnalysisResult = computed(() => {
  return analysisResult.value !== null
})

// 方法
const triggerAnalysis = async () => {
  if (!hasValidStock.value) {
    ElMessage.warning('请先选择股票')
    return
  }

  analyzing.value = true
  
  try {
    // 调用融资融券分析接口
    const response = await apiClient.get(`/api/margin-trading/analysis/${props.selectedStock!.code}`, {
      params: { days: analysisDays.value }
    })

    // 兼容不同的API响应格式
    let analysisData: any = null
    if (response.success && response.data) {
      analysisData = response.data
    } else if (response.data && (response.data as any).stock_code) {
      analysisData = response.data
    } else if ((response as any).stock_code) {
      analysisData = response
    }
    
    if (analysisData && analysisData.stock_code) {
      analysisResult.value = analysisData
      console.log('分析结果:', analysisData)
      
      // 获取详细数据
      await loadMarginData()
      
      // 创建图表
      await nextTick()
      createChart()
      
      ElMessage.success('融资融券分析完成')
      
      // 发送分析完成事件
      emit('analysis-completed', {
        id: `margin_${Date.now()}`,
        stockCode: props.selectedStock!.code,
        stockName: props.selectedStock!.name,
        analysisType: 'margin_trading',
        analysisDate: new Date().toISOString(),
        detailed: analysisData
      })
    } else {
      throw new Error(response.message || '分析数据格式错误')
    }
  } catch (error: any) {
    console.error('融资融券分析失败:', error)
    ElMessage.error(`分析失败: ${error?.message || '未知错误'}`)
  } finally {
    analyzing.value = false
  }
}

const loadMarginData = async () => {
  if (!hasValidStock.value) return

  loadingData.value = true
  
  try {
    const response = await apiClient.get(`/api/margin-trading/data/${props.selectedStock!.code}`, {
      params: { days: analysisDays.value }
    })

    // 兼容不同的API响应格式
    let rawData = null
    if (response.success && response.data?.data) {
      rawData = response.data.data
    } else if (response.data?.data) {
      rawData = response.data.data
    } else if (Array.isArray(response.data)) {
      rawData = response.data
    } else if (response.data) {
      rawData = response.data
    }
    
    if (rawData && Array.isArray(rawData)) {
      marginData.value = [...rawData].reverse() // 最新数据在前，避免修改原数组
      console.log('加载融资融券数据成功:', marginData.value.length, '条')
    } else {
      console.warn('未找到有效的数据数组:', response)
    }
  } catch (error: any) {
    console.error('加载融资融券数据失败:', error)
  } finally {
    loadingData.value = false
  }
}

const createChart = () => {
  console.log('创建图表 - 数据检查:', {
    hasContainer: !!chartContainer.value,
    dataLength: marginData.value.length,
    sampleData: marginData.value[0]
  })
  
  if (!chartContainer.value || !marginData.value.length) {
    console.warn('图表创建失败: 容器或数据缺失')
    return
  }

  // 销毁已存在的图表
  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartContainer.value)

  const dates = marginData.value.map(item => item.trade_date.substring(4, 6) + '/' + item.trade_date.substring(6, 8))
  const financingBalance = marginData.value.map(item => item.rzye)
  const securitiesBalance = marginData.value.map(item => item.rqye)
  
  console.log('图表数据准备:', {
    dates: dates.length,
    financingBalance: financingBalance.length,
    securitiesBalance: securitiesBalance.length
  })

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: '#00d4ff',
      textStyle: { color: '#fff' }
    },
    legend: {
      data: ['融资余额', '融券余额'],
      textStyle: { color: '#fff' }
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#333' } },
      axisLabel: { color: '#999' }
    },
    yAxis: [
      {
        type: 'value',
        name: '融资余额(元)',
        position: 'left',
        axisLine: { lineStyle: { color: '#00d4ff' } },
        axisLabel: { 
          color: '#00d4ff',
          formatter: (value: number) => formatAmount(value)
        }
      },
      {
        type: 'value',
        name: '融券余额(元)',
        position: 'right',
        axisLine: { lineStyle: { color: '#ff6b6b' } },
        axisLabel: { 
          color: '#ff6b6b',
          formatter: (value: number) => formatAmount(value)
        }
      }
    ],
    series: [
      {
        name: '融资余额',
        type: 'line',
        yAxisIndex: 0,
        data: financingBalance,
        smooth: true,
        lineStyle: { color: '#00d4ff', width: 2 },
        itemStyle: { color: '#00d4ff' },
        areaStyle: { 
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 212, 255, 0.3)' },
            { offset: 1, color: 'rgba(0, 212, 255, 0.05)' }
          ])
        }
      },
      {
        name: '融券余额',
        type: 'line',
        yAxisIndex: 1,
        data: securitiesBalance,
        smooth: true,
        lineStyle: { color: '#ff6b6b', width: 2 },
        itemStyle: { color: '#ff6b6b' },
        areaStyle: { 
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255, 107, 107, 0.3)' },
            { offset: 1, color: 'rgba(255, 107, 107, 0.05)' }
          ])
        }
      }
    ],
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      top: '15%'
    }
  }

  chartInstance.setOption(option)
  console.log('图表设置完成')
}

const onDaysChange = () => {
  if (hasAnalysisResult.value) {
    triggerAnalysis()
  }
}

// 格式化工具函数
const formatAmount = (amount: number | null | undefined, showSign = false): string => {
  if (amount == null) return 'N/A'
  
  const absAmount = Math.abs(amount)
  let result = ''
  
  if (absAmount >= 100000000) {
    result = (absAmount / 100000000).toFixed(2) + '亿'
  } else if (absAmount >= 10000) {
    result = (absAmount / 10000).toFixed(2) + '万'
  } else {
    result = absAmount.toFixed(2)
  }
  
  if (showSign && amount !== 0) {
    result = (amount > 0 ? '+' : '-') + result
  }
  
  return result
}

const formatDate = (dateStr: string): string => {
  if (!dateStr || dateStr.length !== 8) return dateStr
  return dateStr.substring(4, 6) + '/' + dateStr.substring(6, 8)
}

const getRecommendationType = (recommendation: string) => {
  switch (recommendation) {
    case 'bullish': return 'success'
    case 'bearish': return 'danger'
    default: return 'info'
  }
}

const getRecommendationText = (recommendation: string) => {
  switch (recommendation) {
    case 'bullish': return '看多'
    case 'bearish': return '看空'
    default: return '中性'
  }
}

const getRiskType = (risk: string) => {
  switch (risk) {
    case 'low': return 'success'
    case 'high': return 'danger'
    default: return 'warning'
  }
}

const getRiskText = (risk: string) => {
  switch (risk) {
    case 'low': return '低风险'
    case 'high': return '高风险'
    default: return '中等风险'
  }
}

const getTrendType = (trend: string) => {
  switch (trend) {
    case 'increasing': return 'success'
    case 'decreasing': return 'danger'
    default: return 'info'
  }
}

const getTrendText = (trend: string) => {
  switch (trend) {
    case 'increasing': return '上升'
    case 'decreasing': return '下降'
    default: return '稳定'
  }
}

// 监听股票变化
watch(
  () => props.selectedStock,
  (newStock) => {
    if (newStock && newStock.code) {
      // 重置之前的分析结果
      analysisResult.value = null
      marginData.value = []
      if (chartInstance) {
        chartInstance.dispose()
        chartInstance = null
      }
    }
  }
)

// 组件销毁时清理图表
onMounted(() => {
  return () => {
    if (chartInstance) {
      chartInstance.dispose()
    }
  }
})
</script>

<style scoped>
.margin-trading-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  background: var(--bg-secondary);
  overflow: hidden;
}

/* ========== 面板标题 ========== */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-primary);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.01));
  backdrop-filter: blur(10px);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.title-icon {
  width: 20px;
  height: 20px;
  color: var(--accent-primary);
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.action-icon {
  width: 14px;
  height: 14px;
}

/* ========== 面板内容 ========== */
.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
}

.scrollable-content {
  max-height: calc(100vh - 200px);
}

/* ========== 分析结果区域 ========== */
.result-section {
  margin-bottom: var(--spacing-lg);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-md) 0;
}

/* ========== 综合评分卡片 ========== */
.score-overview {
  margin-bottom: var(--spacing-lg);
}

.score-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.05), rgba(0, 255, 157, 0.05));
}

.score-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-right: var(--spacing-lg);
  border-right: 1px solid var(--border-primary);
  min-width: 120px;
}

.score-value {
  font-size: 48px;
  font-weight: 700;
  color: var(--accent-primary);
  line-height: 1;
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
}

.score-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: var(--spacing-xs);
}

.score-max {
  font-size: 14px;
  color: var(--text-tertiary);
}

.score-details {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

.score-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.score-item .label {
  font-size: 12px;
  color: var(--text-secondary);
}

.score-item .value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

/* ========== 趋势分析 ========== */
.trend-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

.trend-card {
  padding: var(--spacing-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.02);
}

.trend-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.trend-icon {
  width: 18px;
  height: 18px;
}

.trend-icon.financing {
  color: #00d4ff;
}

.trend-icon.securities {
  color: #ff6b6b;
}

.trend-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.trend-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.trend-direction {
  margin-bottom: var(--spacing-sm);
}

.trend-metrics {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  padding: 2px 0;
}

.metric-label {
  color: var(--text-secondary);
}

.metric-value {
  font-weight: 500;
  color: var(--text-primary);
}

.metric-value.positive {
  color: #67c23a;
}

.metric-value.negative {
  color: #f56c6c;
}

/* ========== 图表容器 ========== */
.chart-container {
  margin: var(--spacing-md) 0;
}

.chart-element {
  width: 100%;
  height: 300px;
  border-radius: var(--radius-md);
  background: rgba(0, 0, 0, 0.2);
}

/* ========== 表格容器 ========== */
.table-container {
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--border-primary);
  overflow-x: auto;
}

.date-text {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
}

.amount-text {
  font-size: 11px;
  font-weight: 500;
  display: block;
  text-align: right;
}

.amount-text.financing {
  color: #00d4ff;
}

.amount-text.securities {
  color: #ff6b6b;
}

.amount-text.buy {
  color: #67c23a;
}

.amount-text.sell {
  color: #f56c6c;
}

.amount-text.repay {
  color: var(--text-secondary);
}

/* ========== 风险提示 ========== */
.risk-factors {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

/* ========== 空状态 ========== */
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.empty-content {
  text-align: center;
  max-width: 400px;
}

.empty-icon {
  width: 80px;
  height: 80px;
  color: var(--text-tertiary);
  margin: 0 auto var(--spacing-lg);
}

.empty-content h3 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-md) 0;
}

.empty-content p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 var(--spacing-lg) 0;
  line-height: 1.6;
}

.empty-features {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  align-items: flex-start;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 14px;
  color: var(--text-secondary);
}

.feature-icon {
  width: 16px;
  height: 16px;
  color: var(--accent-primary);
}

/* ========== Element Plus 组件样式覆盖 ========== */
:deep(.el-table) {
  background: transparent;
  color: var(--text-primary);
  width: 100%;
  table-layout: fixed;
}

:deep(.el-table th) {
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid var(--border-primary);
  color: var(--text-primary);
  font-size: 11px;
  font-weight: 600;
  padding: 8px 4px;
  text-align: center;
}

:deep(.el-table td) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
  padding: 8px 4px;
  font-size: 11px;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: rgba(255, 255, 255, 0.02);
}

:deep(.el-table__empty-text) {
  color: var(--text-tertiary);
}

:deep(.el-table .cell) {
  padding: 0 4px;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}

:deep(.el-table--small .el-table__cell) {
  padding: 6px 2px;
}

/* 表格加载状态优化 */
:deep(.el-loading-mask) {
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
}

:deep(.el-loading-spinner .el-icon) {
  color: var(--accent-primary);
}

/* 滚动条优化 */
.table-container::-webkit-scrollbar {
  height: 6px;
}

.table-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.table-container::-webkit-scrollbar-thumb {
  background: rgba(0, 212, 255, 0.3);
  border-radius: 3px;
}

.table-container::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 212, 255, 0.5);
}

:deep(.el-alert) {
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.2);
  border-radius: var(--radius-md);
}

:deep(.el-alert__icon) {
  color: #ffc107;
}

:deep(.el-alert__title) {
  color: var(--text-primary);
  font-size: 12px;
}

/* ========== 响应式设计 ========== */
@media (max-width: 768px) {
  .trend-grid {
    grid-template-columns: 1fr;
  }
  
  .score-card {
    flex-direction: column;
    text-align: center;
  }
  
  .score-main {
    border-right: none;
    border-bottom: 1px solid var(--border-primary);
    padding-right: 0;
    padding-bottom: var(--spacing-md);
  }
  
  .score-details {
    grid-template-columns: 1fr;
    text-align: left;
  }
  
  /* 移动端隐藏部分表格列 */
  :deep(.mobile-hide) {
    display: none !important;
  }
  
  .table-container {
    font-size: 10px;
  }
  
  .amount-text {
    font-size: 10px;
  }
  
  .date-text {
    font-size: 10px;
  }
}

@media (max-width: 1024px) {
  /* 平板端隐藏最后一列 */
  :deep(.el-table__body .mobile-hide:last-child) {
    display: none !important;
  }
}

/* ========== 表格优化 ========== */
@media (max-width: 480px) {
  .table-container {
    border-radius: var(--radius-sm);
  }
  
  :deep(.el-table) {
    font-size: 10px;
  }
  
  :deep(.el-table th) {
    padding: 6px 4px;
    font-size: 9px;
  }
  
  :deep(.el-table td) {
    padding: 6px 4px;
  }
  
  .amount-text {
    font-size: 9px;
    line-height: 1.2;
  }
  
  .date-text {
    font-size: 9px;
  }
}
</style>