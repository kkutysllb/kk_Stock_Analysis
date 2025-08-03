<template>
  <div class="contango-overview-panel card glass-effect">
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="header-left">
        <div class="title-row">
          <h3 class="section-title">
            <ArrowTrendingUpIcon class="section-icon" />
            股指期货正反向市场分析
          </h3>
          <div class="title-actions">
            <AskAIComponent :data-context="aiDataContext" />
          </div>
        </div>
        <p class="section-subtitle">期货合约基差与期限结构概览</p>
      </div>
      <div class="header-actions">
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          :disabled-date="disabledDate"
          @change="onDateChange"
          class="date-picker"
          size="default"
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
        <el-button 
          @click="goToDetailPage" 
          type="default" 
          size="default"
          class="detail-btn"
        >
          <PresentationChartLineIcon class="btn-icon" />
          详细分析
        </el-button>
      </div>
    </div>

    <!-- 概览内容 -->
    <div class="card-body">
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <div class="loading-text">加载正反向市场数据中...</div>
      </div>
      
      <div v-else class="overview-content">
        <!-- 市场概览统计 -->
        <div class="market-summary">
          <div class="summary-card contango">
            <div class="summary-icon">
              <ArrowTrendingUpIcon class="icon" />
            </div>
            <div class="summary-content">
              <div class="summary-value">{{ marketOverview.contangoCount }}</div>
              <div class="summary-label">正向市场</div>
            </div>
          </div>
          
          <div class="summary-card backwardation">
            <div class="summary-icon">
              <ArrowTrendingDownIcon class="icon" />
            </div>
            <div class="summary-content">
              <div class="summary-value">{{ marketOverview.backwardationCount }}</div>
              <div class="summary-label">反向市场</div>
            </div>
          </div>
          
          <div class="summary-card basis-rate">
            <div class="summary-icon">
              <ScaleIcon class="icon" />
            </div>
            <div class="summary-content">
              <div class="summary-value">{{ formatPercentage(marketOverview.avgBasisRate) }}</div>
              <div class="summary-label">平均基差率</div>
            </div>
          </div>
        </div>

        <!-- 各品种概览 -->
        <div class="symbols-overview">
          <div 
            v-for="symbol in symbolsData" 
            :key="symbol.symbol"
            class="symbol-card"
            :class="getMarketStatusClass(symbol.marketStatus)"
            @click="goToDetailPage(symbol.symbol)"
          >
            <div class="symbol-header">
              <div class="symbol-info">
                <h4 class="symbol-name">{{ symbol.name }}</h4>
                <span class="symbol-code">{{ symbol.symbol }}</span>
              </div>
              <div class="market-status" :class="getMarketStatusClass(symbol.marketStatus)">
                <component :is="getMarketStatusIcon(symbol.marketStatus)" class="status-icon" />
                <span class="status-text">{{ getMarketStatusText(symbol.marketStatus) }}</span>
              </div>
            </div>

            <div class="symbol-metrics">
              <div class="metric-row">
                <div class="metric">
                  <span class="label">现货指数</span>
                  <span class="value">{{ formatNumber(symbol.spotIndex) }}</span>
                </div>
                <div class="metric">
                  <span class="label">主力合约</span>
                  <span class="value">{{ symbol.mainContract }}</span>
                </div>
              </div>
              
              <div class="metric-row">
                <div class="metric">
                  <span class="label">基差</span>
                  <span class="value" :class="getBasisClass(symbol.basis)">{{ formatNumber(symbol.basis) }}</span>
                </div>
                <div class="metric">
                  <span class="label">基差率</span>
                  <span class="value" :class="getBasisClass(symbol.basis)">{{ formatPercentage(symbol.basisRate) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 数据为空时的提示 -->
      <div v-if="!loading && symbolsData.length === 0" class="empty-state">
        <ExclamationTriangleIcon class="empty-icon" />
        <p class="empty-text">暂无正反向市场数据</p>
        <p class="empty-hint">请检查数据源或稍后重试</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { futuresAPI } from '../api/futures'
import { useAppStore } from '../stores/app'
import AskAIComponent from './AskAIComponent.vue'
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ArrowPathIcon,
  PresentationChartLineIcon,
  ScaleIcon,
  ExclamationTriangleIcon,
  MinusIcon
} from '@heroicons/vue/24/outline'

const router = useRouter()
const appStore = useAppStore()

// 响应式数据
const loading = ref(false)
const contangoData = ref(null)
const selectedDate = ref(null)

// 初始化当前日期
const initializeDate = () => {
  const today = new Date()
  selectedDate.value = today.toISOString().split('T')[0]
}

// 计算市场概览数据
  const marketOverview = computed(() => {
    if (!contangoData.value || !contangoData.value.analysis_results) {
      return {
        contangoCount: 0,
        backwardationCount: 0,
        avgBasisRate: 0
      }
    }
    
    let totalContango = 0
    let totalBackwardation = 0
    let totalBasisRate = 0
    let totalContracts = 0
    
    contangoData.value.analysis_results.forEach(result => {
      const contracts = result.contracts || []
      contracts.forEach(contract => {
        if (contract.is_contango) {
          totalContango++
        } else {
          totalBackwardation++
        }
        totalBasisRate += contract.basis_rate || 0
        totalContracts++
      })
    })
    
    return {
      contangoCount: totalContango,
      backwardationCount: totalBackwardation,
      avgBasisRate: totalContracts > 0 ? totalBasisRate / totalContracts : 0
    }
  })

// 各品种数据
const symbolsData = computed(() => {
  if (!contangoData.value || !contangoData.value.analysis_results) {
    return []
  }
  
  return contangoData.value.analysis_results.map(result => {
    const contracts = result.contracts || []
    const contangoCount = contracts.filter(c => c.is_contango).length
    const backwardationCount = contracts.length - contangoCount
    
    // 计算平均基差率
    const avgBasisRate = contracts.length > 0 
      ? contracts.reduce((sum, c) => sum + (c.basis_rate || 0), 0) / contracts.length 
      : 0
    
    // 确定市场状态
    let marketStatus = 'neutral'
    if (avgBasisRate > 0.01) {
      marketStatus = 'contango'
    } else if (avgBasisRate < -0.01) {
      marketStatus = 'backwardation'
    }
    
    // 获取主力合约（通常是第一个合约）
    const mainContract = contracts.length > 0 ? contracts[0] : null
    
    return {
      symbol: result.symbol,
      name: getSymbolName(result.symbol),
      contangoCount,
      backwardationCount,
      avgBasisRate,
      marketStatus,
      totalContracts: contracts.length,
      spotIndex: result.spot_price || 0,
      mainContract: mainContract ? mainContract.contract_name || mainContract.ts_code : '--',
      basis: mainContract ? mainContract.basis : 0,
      basisRate: avgBasisRate
    }
  })
})

// 日期相关方法
const disabledDate = (time) => {
  // 禁用未来日期
  return time.getTime() > Date.now()
}

const onDateChange = (date) => {
  if (date) {
    fetchData(date)
  }
}

// 日期格式转换函数
const formatDateForAPI = (date) => {
  if (!date) return null
  // 将 YYYY-MM-DD 格式转换为 YYYYMMDD 格式
  if (typeof date === 'string') {
    return date.replace(/-/g, '')
  }
  // 如果是 Date 对象，转换为 YYYYMMDD 格式
  if (date instanceof Date) {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}${month}${day}`
  }
  return date
}

// 获取数据
const fetchData = async (tradeDate = null) => {
  try {
    loading.value = true
    
    // 转换日期格式
    const formattedDate = formatDateForAPI(tradeDate)
    // console.log('请求日期:', tradeDate, '转换后:', formattedDate)
    
    const response = await futuresAPI.getContangoAnalysis(formattedDate)
    
    if (response.success && response.data) {
      contangoData.value = response.data
    } else {
      throw new Error(response.error || '获取数据失败')
    }
  } catch (error) {
    console.error('获取正反向市场数据失败:', error)
    ElMessage.error('获取正反向市场数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = async () => {
  await fetchData(selectedDate.value)
  ElMessage.success('数据已刷新')
}

// 跳转到详细分析页面
const goToDetailPage = (symbol = null) => {
  if (symbol) {
    router.push({ name: 'FuturesAnalysis', query: { symbol } })
  } else {
    router.push({ name: 'FuturesAnalysis' })
  }
}

// 格式化函数
const formatNumber = (value) => {
  if (value === null || value === undefined) return '--'
  return value.toFixed(2)
}

const formatPercentage = (value) => {
  if (value === null || value === undefined) return '--'
  return `${(value * 100).toFixed(2)}%`
}

// AI数据上下文
const aiDataContext = computed(() => {
  const dateStr = selectedDate.value || ''
  
  if (!contangoData.value || !contangoData.value.analysis_results) {
    return {
      type: 'contango_overview_analysis',
      title: '股指期货正反向市场分析',
      period: dateStr,
      data: { date: dateStr },
      summary: `股指期货正反向市场分析 (${dateStr}):\n\n暂无数据`
    }
  }
  
  const overview = marketOverview.value
  const symbolsInfo = symbolsData.value
  
  return {
    type: 'contango_overview_analysis',
    title: '股指期货正反向市场分析',
    period: dateStr,
    data: {
      date: dateStr,
      marketOverview: overview,
      symbolsData: symbolsInfo,
      analysisResults: contangoData.value.analysis_results
    },
    summary: `股指期货正反向市场分析概览（${dateStr}）：

## 市场整体概况
- 分析日期：${dateStr}
- 正向市场合约：${overview.contangoCount}个
- 反向市场合约：${overview.backwardationCount}个
- 平均基差率：${formatPercentage(overview.avgBasisRate)}
- 市场总体状态：${overview.contangoCount > overview.backwardationCount ? '以正向市场为主' : overview.backwardationCount > overview.contangoCount ? '以反向市场为主' : '正反向市场相当'}

## 各品种概览分析
${symbolsInfo.map((symbol, index) => 
  `${index + 1}. ${symbol.name}（${symbol.symbol}）：
   - 现货指数：${formatNumber(symbol.spotIndex)}
   - 主力合约：${symbol.mainContract}
   - 基差：${formatNumber(symbol.basis)}点
   - 基差率：${formatPercentage(symbol.basisRate)}
   - 市场状态：${getMarketStatusText(symbol.marketStatus)}`
).join('\n\n')}

## 详细合约分析
${contangoData.value.analysis_results.map((result) => {
  const symbolName = getSymbolName(result.symbol)
  const contracts = result.contracts || []
  const contangoContracts = contracts.filter(c => c.is_contango)
  const backwardationContracts = contracts.filter(c => !c.is_contango)
  
  return `${symbolName}期限结构：
   - 现货价格：${formatNumber(result.spot_price)}
   - 活跃合约数：${contracts.length}个
   - 正向合约：${contangoContracts.length}个
   - 反向合约：${backwardationContracts.length}个
   - 合约详情：
${contracts.map(contract => 
     `     * ${contract.ts_code}：期货价${formatNumber(contract.futures_price)}，基差${formatNumber(contract.basis)}（${formatPercentage(contract.basis_rate)}），${contract.days_to_expiry}天到期，${contract.is_contango ? '正向' : '反向'}`
   ).join('\n')}`
}).join('\n\n')}

## 期限结构分析
- 市场结构偏向：${overview.contangoCount > overview.backwardationCount ? '正向市场占主导，期货价格普遍高于现货' : overview.backwardationCount > overview.contangoCount ? '反向市场占主导，期货价格普遍低于现货' : '正反向市场均衡，期限结构分化'}
- 基差水平：${Math.abs(overview.avgBasisRate) > 0.02 ? '基差较大，市场预期明确' : '基差适中，市场预期相对温和'}
- 套利机会：${overview.contangoCount > 0 && overview.backwardationCount > 0 ? '不同品种间存在跨品种套利机会' : '品种间期限结构相似，套利机会有限'}

## 投资策略建议
- 正向市场策略：${overview.contangoCount > 0 ? '可考虑卖出远月合约，买入近月合约的期限套利' : '当前无明显正向市场机会'}
- 反向市场策略：${overview.backwardationCount > 0 ? '可考虑买入远月合约，卖出近月合约的期限套利' : '当前无明显反向市场机会'}
- 风险控制：注意到期日临近时基差收敛风险，建议设置合理止损位

请基于以上正反向市场分析，制定相应的期货投资和套利策略。`
  }
})

// 样式类函数
const getMarketStatusClass = (status) => {
  switch (status) {
    case 'contango': return 'contango'
    case 'backwardation': return 'backwardation'
    default: return 'neutral'
  }
}

const getMarketStatusIcon = (status) => {
  switch (status) {
    case 'contango': return ArrowTrendingUpIcon
    case 'backwardation': return ArrowTrendingDownIcon
    default: return MinusIcon
  }
}

const getMarketStatusText = (status) => {
  switch (status) {
    case 'contango': return '正向市场'
    case 'backwardation': return '反向市场'
    default: return '中性'
  }
}

const getBasisClass = (basis) => {
  if (basis > 0) return 'positive'
  if (basis < 0) return 'negative'
  return 'neutral'
}

// 获取品种名称
const getSymbolName = (symbol) => {
  const symbolNames = {
    'IF': 'IF沪深300',
    'IC': 'IC中证500', 
    'IH': 'IH上证50',
    'IM': 'IM中证1000'
  }
  return symbolNames[symbol] || symbol
}

// 组件挂载时获取数据
onMounted(() => {
  initializeDate()
  fetchData(selectedDate.value)
})
</script>

<style scoped>
.contango-overview-panel {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.title-actions {
  display: flex;
  align-items: center;
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
  color: var(--el-text-color-regular);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.date-picker {
  width: 160px;
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.card-body {
  padding: 24px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 16px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--el-border-color-light);
  border-top: 3px solid var(--el-color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.overview-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.market-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  transition: all 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.summary-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
}

.summary-card.contango .summary-icon {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.summary-card.backwardation .summary-icon {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.summary-card.basis-rate .summary-icon {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.summary-icon .icon {
  width: 20px;
  height: 20px;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.summary-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.summary-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.symbols-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.symbol-card {
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  cursor: pointer;
  transition: all 0.3s ease;
}

.symbol-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.symbol-card.contango {
  border-left: 4px solid #ef4444;
}

.symbol-card.backwardation {
  border-left: 4px solid #22c55e;
}

.symbol-card.neutral {
  border-left: 4px solid #6b7280;
}

.symbol-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.symbol-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.symbol-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}

.symbol-code {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.market-status {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.market-status.contango {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.market-status.backwardation {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.market-status.neutral {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
}

.status-icon {
  width: 12px;
  height: 12px;
}

.symbol-metrics {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric .label {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.metric .value {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.metric .value.positive {
  color: #ef4444;
}

.metric .value.negative {
  color: #22c55e;
}

.metric .value.neutral {
  color: var(--el-text-color-regular);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 12px;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: var(--el-text-color-placeholder);
}

.empty-text {
  font-size: 16px;
  color: var(--el-text-color-regular);
  margin: 0;
}

.empty-hint {
  font-size: 14px;
  color: var(--el-text-color-placeholder);
  margin: 0;
}

@media (max-width: 768px) {
  .market-summary {
    grid-template-columns: 1fr;
  }
  
  .symbols-overview {
    grid-template-columns: 1fr;
  }
  
  .card-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>