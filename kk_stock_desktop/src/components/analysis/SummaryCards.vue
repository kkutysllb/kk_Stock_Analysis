<template>
  <div class="summary-cards">
    <!-- 面板标题和AI按钮 -->
    <div class="panel-title-section">
      <h3 class="panel-title">
        <DocumentIcon class="title-icon" />
        活跃期货合约汇总
      </h3>
      <AskAIComponent :data-context="aiDataContext" />
    </div>
    
    <div v-if="isLoading" class="loading-container">
      <el-skeleton :rows="3" animated />
    </div>
    <div v-else-if="Object.keys(displayData).length === 0" class="no-data-container">
      <el-empty description="暂无活跃期货合约数据">
        <template #image>
          <el-icon size="64"><DocumentIcon /></el-icon>
        </template>
        <el-button type="primary" @click="$emit('refresh')">刷新数据</el-button>
      </el-empty>
    </div>
    <div v-else class="cards-grid">
      <el-card v-for="(data, symbol) in displayData" :key="String(symbol)" class="summary-card">
        <template #header>
          <div class="card-header">
            <h3 class="symbol-name">{{ getSymbolName(String(symbol)) }}</h3>
            <el-tag :type="getContractTagType(data)" size="small">
              {{ data.active_contracts_count || 0 }}个活跃合约
            </el-tag>
          </div>
        </template>
        
        <div class="card-content">
          <!-- 主力合约信息 -->
          <div class="main-contract-info" v-if="data.main_contract">
            <div class="info-item">
              <span class="label">主力合约:</span>
              <span class="value main-contract">{{ data.main_contract.symbol }}</span>
            </div>
            <div class="info-item" v-if="data.main_contract.total_volume">
              <span class="label">总持仓:</span>
              <span class="value">{{ formatNumber(data.main_contract.total_volume) }}</span>
            </div>
          </div>

          <!-- 活跃合约列表 -->
          <div class="active-contracts-info" v-if="data.active_contracts && data.active_contracts.length > 0">
            <div class="contracts-title">活跃合约列表:</div>
            <div class="contracts-list">
              <el-tag 
                v-for="contract in data.active_contracts" 
                :key="contract"
                size="small"
                :type="contract === data.main_contract?.symbol ? 'success' : 'info'"
                class="contract-tag"
              >
                {{ contract }}
                <span v-if="contract === data.main_contract?.symbol" class="main-badge">主力</span>
              </el-tag>
            </div>
          </div>

          <!-- 持仓统计 -->
          <div class="position-stats">
            <div class="stat-row">
              <div class="stat-item">
                <span class="stat-label">总多头:</span>
                <span class="stat-value positive">{{ formatNumber(data.total_long || 0) }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">总空头:</span>
                <span class="stat-value negative">{{ formatNumber(data.total_short || 0) }}</span>
              </div>
            </div>
            <div class="stat-row">
              <div class="stat-item">
                <span class="stat-label">净持仓:</span>
                <span class="stat-value" :class="getNetPositionClass(data.net_position || 0)">
                  {{ formatNumber(data.net_position || 0) }}
                </span>
              </div>
              <div class="stat-item">
                <span class="stat-label">参与机构:</span>
                <span class="stat-value">{{ data.institution_count || 0 }}</span>
              </div>
            </div>
          </div>

          <!-- 变化情况 -->
          <div class="change-stats" v-if="hasChangeData(data)">
            <div class="change-title">日变化</div>
            <div class="change-row">
              <div class="change-item">
                <span class="change-label">多头变化:</span>
                <span class="change-value" :class="getChangeClass(data.total_long_chg || 0)">
                  {{ formatChange(data.total_long_chg || 0) }}
                </span>
              </div>
              <div class="change-item">
                <span class="change-label">空头变化:</span>
                <span class="change-value" :class="getChangeClass(data.total_short_chg || 0)">
                  {{ formatChange(data.total_short_chg || 0) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 总体统计卡片 -->
    <el-card v-if="!isLoading && overallStats && Object.keys(displayData).length > 0" class="overall-stats-card">
      <template #header>
        <div class="overall-header">
          <h3 class="card-title">整体统计</h3>
          <el-tag size="small" type="info">{{ formatDate(selectedDate) }}</el-tag>
        </div>
      </template>
      <div class="overall-content">
        <div class="overall-item">
          <span class="overall-label">总活跃合约:</span>
          <span class="overall-value">{{ overallStats.total_active_contracts || 0 }}</span>
        </div>
        <div class="overall-item">
          <span class="overall-label">总净持仓:</span>
          <span class="overall-value" :class="getNetPositionClass(overallStats.total_net_position || 0)">
            {{ formatNumber(overallStats.total_net_position || 0) }}
          </span>
        </div>
        <div class="overall-item">
          <span class="overall-label">总成交量:</span>
          <span class="overall-value">{{ formatNumber(overallStats.total_vol || 0) }}</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { DocumentIcon } from '@heroicons/vue/24/outline'
import AskAIComponent from '../AskAIComponent.vue'

interface Props {
  summaryData?: any
  isLoading?: boolean
  selectedDate?: string
  selectedSymbols?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  summaryData: () => ({}),
  isLoading: false,
  selectedDate: '',
  selectedSymbols: () => []
})

// 定义emit事件
const emit = defineEmits<{
  refresh: []
}>()

// 品种名称映射
const symbolNames = {
  'IF': 'IF-沪深300',
  'IC': 'IC-中证500', 
  'IH': 'IH-上证50',
  'IM': 'IM-中证1000'
}

// 计算显示数据
const displayData = computed(() => {
  console.log('SummaryCards - 原始数据:', props.summaryData)
  
  if (!props.summaryData) {
    console.log('SummaryCards - 无数据')
    return {}
  }
  
  // 尝试从不同的数据结构中获取品种详情
  let symbolDetails = null
  
  if (props.summaryData.symbol_details) {
    symbolDetails = props.summaryData.symbol_details
  } else if (props.summaryData.summary_by_symbol) {
    symbolDetails = props.summaryData.summary_by_symbol
  } else if (props.summaryData.data && props.summaryData.data.symbol_details) {
    symbolDetails = props.summaryData.data.symbol_details
  } else if (props.summaryData.data && props.summaryData.data.summary_by_symbol) {
    symbolDetails = props.summaryData.data.summary_by_symbol
  }
  
  console.log('SummaryCards - 品种详情:', symbolDetails)
  
  // 如果没有找到数据，返回空对象，不显示任何卡片
  if (!symbolDetails || Object.keys(symbolDetails).length === 0) {
    console.log('SummaryCards - 无有效的品种数据')
    return {}
  }
  
  return symbolDetails
})

// 计算整体统计
const overallStats = computed(() => {
  if (!props.summaryData || !props.summaryData.total_stats) {
    return null
  }
  return props.summaryData.total_stats
})

// AI数据上下文
const aiDataContext = computed(() => {
  const dateStr = props.selectedDate ? `${props.selectedDate.slice(0,4)}-${props.selectedDate.slice(4,6)}-${props.selectedDate.slice(6,8)}` : ''
  const symbols = props.selectedSymbols?.join(', ') || ''
  
  // 计算汇总统计
  const getSummaryStats = () => {
    const data = displayData.value
    const overall = overallStats.value
    
    let totalActiveContracts = 0
    let totalNetPosition = 0
    let totalVolume = 0
    let totalInstitutions = 0
    
    Object.values(data).forEach((symbolData: any) => {
      totalActiveContracts += symbolData.active_contracts_count || 0
      totalNetPosition += symbolData.net_position || 0
      totalVolume += symbolData.total_vol || 0
      totalInstitutions += symbolData.institution_count || 0
    })
    
    return {
      totalActiveContracts,
      totalNetPosition,
      totalVolume,
      totalInstitutions,
      symbolCount: Object.keys(data).length
    }
  }
  
  const summaryStats = getSummaryStats()
  
  return {
    type: 'futures_summary_analysis',
    title: '活跃期货合约汇总分析',
    period: dateStr,
    data: {
      date: dateStr,
      symbols: symbols,
      displayData: displayData.value,
      overallStats: overallStats.value,
      summaryStats
    },
    summary: `活跃期货合约汇总分析（${dateStr}）：

## 分析概况
- 分析日期：${dateStr}
- 分析品种：${symbols}
- 活跃品种数：${summaryStats.symbolCount}个
- 总活跃合约：${summaryStats.totalActiveContracts}个

## 各品种详细分析
${Object.entries(displayData.value).map(([symbol, data]: [string, any]) => 
  `### ${getSymbolName(symbol)}（${symbol}）
- 活跃合约数：${data.active_contracts_count || 0}个
- 主力合约：${data.main_contract?.symbol || '未知'}
- 总多头持仓：${formatNumber(data.total_long || 0)}手
- 总空头持仓：${formatNumber(data.total_short || 0)}手
- 净持仓：${formatNumber(data.net_position || 0)}手
- 参与机构数：${data.institution_count || 0}家
- 活跃合约列表：${data.active_contracts?.join(', ') || '无'}
${hasChangeData(data) ? `- 多头变化：${formatChange(data.total_long_chg || 0)}手
- 空头变化：${formatChange(data.total_short_chg || 0)}手` : ''}`
).join('\n\n')}

## 市场整体分析
- 总净持仓：${formatNumber(summaryStats.totalNetPosition)}手
- 总成交量：${formatNumber(summaryStats.totalVolume)}手
- 总参与机构：${summaryStats.totalInstitutions}家
- 市场偏向：${summaryStats.totalNetPosition > 0 ? '偏多头' : summaryStats.totalNetPosition < 0 ? '偏空头' : '相对均衡'}

## 活跃度分析
${Object.entries(displayData.value).map(([symbol, data]: [string, any]) => {
  const contractCount = data.active_contracts_count || 0
  const activityLevel = contractCount >= 5 ? '高活跃' : contractCount >= 3 ? '中等活跃' : '低活跃'
  return `- ${getSymbolName(symbol)}：${contractCount}个合约（${activityLevel}）`
}).join('\n')}

## 主力合约分析
${Object.entries(displayData.value).map(([symbol, data]: [string, any]) => 
  `- ${getSymbolName(symbol)}主力合约：${data.main_contract?.symbol || '未确定'}${data.main_contract?.total_volume ? `，持仓量${formatNumber(data.main_contract.total_volume)}手` : ''}`
).join('\n')}
`
  }
})

// 工具函数
const getSymbolName = (symbol: string): string => {
  return symbolNames[symbol as keyof typeof symbolNames] || symbol
}

const formatNumber = (num: number): string => {
  if (Math.abs(num) >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toLocaleString()
}

const formatChange = (num: number): string => {
  const prefix = num > 0 ? '+' : ''
  return prefix + formatNumber(num)
}

const getNetPositionClass = (value: number): string => {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}

const getChangeClass = (value: number): string => {
  if (value > 0) return 'increase'
  if (value < 0) return 'decrease'
  return 'neutral'
}

const getContractTagType = (data: any): string => {
  const count = data.active_contracts_count || 0
  if (count >= 5) return 'success'
  if (count >= 3) return 'warning'
  return 'info'
}

const hasChangeData = (data: any): boolean => {
  return data.total_long_chg !== undefined || data.total_short_chg !== undefined
}

// 格式化日期显示
const formatDate = (dateStr: string): string => {
  if (!dateStr || dateStr.length !== 8) return dateStr
  
  const year = dateStr.substring(0, 4)
  const month = dateStr.substring(4, 6)
  const day = dateStr.substring(6, 8)
  
  return `${year}-${month}-${day}`
}
</script>

<style scoped>
.summary-cards {
  padding: 0px;
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
  padding: 40px;
}

.no-data-container {
  padding: 60px 20px;
  text-align: center;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.summary-card {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--el-box-shadow-dark);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.symbol-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.card-content {
  space-y: 15px;
}

.main-contract-info {
  padding: 10px;
  background: var(--el-bg-color-page);
  border-radius: 6px;
  margin-bottom: 15px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.label {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.value {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.main-contract {
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.position-stats,
.change-stats {
  margin-bottom: 15px;
}

.stat-row,
.change-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.stat-item,
.change-item {
  display: flex;
  flex-direction: column;
  flex: 1;
  text-align: center;
}

.stat-label,
.change-label {
  font-size: 11px;
  color: var(--el-text-color-regular);
  margin-bottom: 2px;
}

.stat-value,
.change-value {
  font-size: 13px;
  font-weight: 500;
}

.change-title {
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-bottom: 8px;
  text-align: center;
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

.increase {
  color: var(--el-color-success);
}

.decrease {
  color: var(--el-color-danger);
}

.overall-stats-card {
  margin-top: 20px;
}

.card-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.overall-content {
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.overall-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.overall-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-bottom: 5px;
}

.overall-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .cards-grid {
    grid-template-columns: 1fr;
  }
  
  .overall-content {
    flex-direction: column;
    gap: 15px;
  }
  
  .overall-item {
    width: 100%;
  }
}

/* 活跃合约信息样式 */
.active-contracts-info {
  margin: 12px 0;
  padding: 8px 0;
  border-top: 1px solid var(--el-border-color-light);
  border-bottom: 1px solid var(--el-border-color-light);
}

.contracts-title {
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-bottom: 6px;
}

.contracts-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.contract-tag {
  position: relative;
  font-size: 11px;
}

.main-badge {
  font-size: 10px;
  margin-left: 2px;
  color: var(--el-color-success);
  font-weight: bold;
}

/* 整体统计头部样式 */
.overall-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.overall-header .card-title {
  margin: 0;
}
</style> 