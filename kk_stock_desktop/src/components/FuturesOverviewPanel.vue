<template>
  <div class="futures-overview-panel card glass-effect">
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="header-left">
        <div class="title-row">
          <h3 class="section-title">
            <ChartBarIcon class="section-icon" />
            股指期货持仓分析
          </h3>
          <div class="title-actions">
            <AskAIComponent :data-context="aiDataContext" />
          </div>
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
        <el-button 
          @click="goToDetailPage" 
          type="default" 
          size="default"
          class="detail-btn"
        >
          <ChartPieIcon class="btn-icon" />
          详细分析
        </el-button>
      </div>
    </div>

    <!-- 期货品种卡片 -->
    <div class="card-body">
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <div class="loading-text">加载期货持仓数据中...</div>
      </div>
      
      <div v-else class="futures-cards-container">
        <div 
          v-for="futures in futuresData" 
          :key="futures.symbol"
          class="futures-card"
          :class="getCardClass(futures.netPosition)"
          @click="goToDetailPage(futures.symbol)"
        >
          <!-- 卡片头部 -->
          <div class="futures-header">
            <div class="futures-info">
              <h4 class="futures-name">{{ futures.name }}</h4>
              <span class="futures-code">{{ futures.symbol }}</span>
            </div>
            <div class="net-position-indicator" :class="getPositionClass(futures.netPosition)">
              <component :is="getPositionIcon(futures.netPosition)" class="position-icon" />
              <span class="position-text">{{ getPositionText(futures.netPosition) }}</span>
            </div>
          </div>

          <!-- 持仓数据 -->
          <div class="futures-metrics">
            <div class="metric-row">
              <div class="metric">
                <span class="label">总多单量</span>
                <span class="value long">{{ formatPosition(futures.totalLong) }}</span>
              </div>
              <div class="metric">
                <span class="label">总空单量</span>
                <span class="value short">{{ formatPosition(futures.totalShort) }}</span>
              </div>
            </div>
            
            <div class="metric-row">
              <div class="metric">
                <span class="label">净持仓量</span>
                <span class="value" :class="getPositionClass(futures.netPosition)">
                  {{ formatPosition(Math.abs(futures.netPosition)) }}
                </span>
              </div>
              <div class="metric">
                <span class="label">持仓变化</span>
                <span class="value change" :class="getChangeClass(futures.netChange)">
                  {{ formatChange(futures.netChange) }}
                </span>
              </div>
            </div>

            <div class="metric-row">
              <div class="metric">
                <span class="label">多单变化</span>
                <span class="value change" :class="getChangeClass(futures.longChange)">
                  {{ formatChange(futures.longChange) }}
                </span>
              </div>
              <div class="metric">
                <span class="label">空单变化</span>
                <span class="value change" :class="getChangeClass(futures.shortChange)">
                  {{ formatChange(futures.shortChange) }}
                </span>
              </div>
            </div>
            
            <!-- 机构分组数据 -->
            <div class="broker-breakdown">
              <div class="breakdown-header">
                <span class="breakdown-title">机构分组持仓</span>
              </div>
              <div class="breakdown-content">
                <div class="broker-group citic">
                  <div class="group-header">
                    <span class="group-name citic-name">中信期货</span>
                    <span class="group-count">({{ futures.brokerBreakdown?.citic?.institutionCount || 0 }}家)</span>
                  </div>
                  <div class="group-metrics">
                    <div class="group-metric">
                      <span class="metric-label">多单变化</span>
                      <span class="metric-value change" :class="getChangeClass(futures.brokerBreakdown?.citic?.totalLongChg || 0)">
                        {{ formatChange(futures.brokerBreakdown?.citic?.totalLongChg || 0) }}
                      </span>
                    </div>
                    <div class="group-metric">
                      <span class="metric-label">空单变化</span>
                      <span class="metric-value change" :class="getChangeClass(futures.brokerBreakdown?.citic?.totalShortChg || 0)">
                        {{ formatChange(futures.brokerBreakdown?.citic?.totalShortChg || 0) }}
                      </span>
                    </div>
                    <div class="group-metric">
                      <span class="metric-label">净持仓变化</span>
                      <span class="metric-value change" :class="getChangeClass(futures.brokerBreakdown?.citic?.netPositionChg || 0)">
                        {{ formatChange(futures.brokerBreakdown?.citic?.netPositionChg || 0) }}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div class="broker-group others">
                  <div class="group-header">
                    <span class="group-name others-name">其他机构</span>
                    <span class="group-count">({{ futures.brokerBreakdown?.others?.institutionCount || 0 }}家)</span>
                  </div>
                  <div class="group-metrics">
                    <div class="group-metric">
                      <span class="metric-label">多单变化</span>
                      <span class="metric-value change" :class="getChangeClass(futures.brokerBreakdown?.others?.totalLongChg || 0)">
                        {{ formatChange(futures.brokerBreakdown?.others?.totalLongChg || 0) }}
                      </span>
                    </div>
                    <div class="group-metric">
                      <span class="metric-label">空单变化</span>
                      <span class="metric-value change" :class="getChangeClass(futures.brokerBreakdown?.others?.totalShortChg || 0)">
                        {{ formatChange(futures.brokerBreakdown?.others?.totalShortChg || 0) }}
                      </span>
                    </div>
                    <div class="group-metric">
                      <span class="metric-label">净持仓变化</span>
                      <span class="metric-value change" :class="getChangeClass(futures.brokerBreakdown?.others?.netPositionChg || 0)">
                        {{ formatChange(futures.brokerBreakdown?.others?.netPositionChg || 0) }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 趋势指示器 -->
          <div class="trend-indicator">
            <div class="trend-bar" :style="getTrendBarStyle(futures.netPosition, futures.netChange)"></div>
          </div>
        </div>
      </div>

      <!-- 数据为空时的提示 -->
      <div v-if="!loading && futuresData.length === 0" class="empty-state">
        <ExclamationTriangleIcon class="empty-icon" />
        <p class="empty-text">暂无期货持仓数据</p>
        <p class="empty-hint">请检查数据源或选择其他日期</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { futuresAPI } from '../api/futures'
import AskAIComponent from './AskAIComponent.vue'
import {
  ChartBarIcon,
  ArrowPathIcon,
  ChartPieIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusIcon,
  ExclamationTriangleIcon
} from '@heroicons/vue/24/outline'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const selectedDate = ref(new Date().toISOString().split('T')[0].replace(/-/g, '')) // 默认设置为今天，YYYYMMDD格式
const futuresData = ref([])
const lastFetchData = ref(null) // 存储上次获取的数据，用于对比

// 期货品种配置
const futuresConfig = {
  'IF': { name: 'IF沪深300', symbol: 'IF' },
  'IC': { name: 'IC中证500', symbol: 'IC' },
  'IH': { name: 'IH上证50', symbol: 'IH' },
  'IM': { name: 'IM中证1000', symbol: 'IM' }
}

// 获取期货持仓数据
const fetchFuturesData = async () => {
  loading.value = true
  try {
    // 使用统一的API客户端
    const tradeDate = selectedDate.value
    const symbols = 'IF,IC,IH,IM'
    
    // console.log(`🔄 [FuturesOverview] 开始获取期货持仓数据 - 日期: ${tradeDate}, 品种: ${symbols}`)
    
    // 调用统一的API方法
    const response = await futuresAPI.getFuturesHoldingSummary(tradeDate, symbols)
    
    
    // console.log(`📊 [FuturesOverview] API响应:`, {
    //   success: response.success,
    //   timestamp: response.timestamp,
    //   tradeDate: response.data?.trade_date,
    //   symbolsCount: response.data?.symbols?.length,
    //   summaryKeys: response.data?.summary ? Object.keys(response.data.summary) : [],
    //   fullResponse: response
    // })
    
    if (response.success && response.data) {
      const summaryData = response.data.summary
      const processedData = []
      
      // 处理返回的数据，转换为组件需要的格式
      Object.keys(futuresConfig).forEach(symbol => {
        const data = summaryData[symbol]
        if (data) {
          processedData.push({
            symbol: data.symbol,
            name: futuresConfig[symbol].name,
            totalLong: data.total_long || 0,
            totalShort: data.total_short || 0,
            netPosition: data.net_position || 0,
            longChange: data.total_long_chg || 0,
            shortChange: data.total_short_chg || 0,
            netChange: data.net_position_chg || 0,
            brokerBreakdown: {
              citic: {
                totalLong: data.broker_breakdown?.citic?.total_long || 0,
                totalShort: data.broker_breakdown?.citic?.total_short || 0,
                netPosition: data.broker_breakdown?.citic?.net_position || 0,
                totalLongChg: data.broker_breakdown?.citic?.total_long_chg || 0,
                totalShortChg: data.broker_breakdown?.citic?.total_short_chg || 0,
                netPositionChg: data.broker_breakdown?.citic?.net_position_chg || 0,
                institutionCount: data.broker_breakdown?.citic?.institution_count || 0
              },
              others: {
                totalLong: data.broker_breakdown?.others?.total_long || 0,
                totalShort: data.broker_breakdown?.others?.total_short || 0,
                netPosition: data.broker_breakdown?.others?.net_position || 0,
                totalLongChg: data.broker_breakdown?.others?.total_long_chg || 0,
                totalShortChg: data.broker_breakdown?.others?.total_short_chg || 0,
                netPositionChg: data.broker_breakdown?.others?.net_position_chg || 0,
                institutionCount: data.broker_breakdown?.others?.institution_count || 0
              }
            }
          })
        } else {
          // 如果没有数据，返回空值
          processedData.push({
            symbol: symbol,
            name: futuresConfig[symbol].name,
            totalLong: 0,
            totalShort: 0,
            netPosition: 0,
            longChange: 0,
            shortChange: 0,
            netChange: 0,
            brokerBreakdown: {
              citic: { totalLong: 0, totalShort: 0, netPosition: 0, totalLongChg: 0, totalShortChg: 0, netPositionChg: 0, institutionCount: 0 },
              others: { totalLong: 0, totalShort: 0, netPosition: 0, totalLongChg: 0, totalShortChg: 0, netPositionChg: 0, institutionCount: 0 }
            }
          })
        }
      })
      
      // console.log(`✅ [FuturesOverview] 数据处理完成:`, {
      //   processedCount: processedData.length,
      //   processedData: processedData.map(item => ({
      //     symbol: item.symbol,
      //     totalLong: item.totalLong,
      //     totalShort: item.totalShort,
      //     netPosition: item.netPosition,
      //     netChange: item.netChange
      //   }))
      // })
      
      // 检查数据一致性
      if (lastFetchData.value && selectedDate.value === lastFetchData.value.date) {
        const currentDataSummary = processedData.map(item => ({
          symbol: item.symbol,
          totalLong: item.totalLong,
          totalShort: item.totalShort,
          netPosition: item.netPosition
        }))
        
        const lastDataSummary = lastFetchData.value.data.map(item => ({
          symbol: item.symbol,
          totalLong: item.totalLong,
          totalShort: item.totalShort,
          netPosition: item.netPosition
        }))
        
        const isDataSame = JSON.stringify(currentDataSummary) === JSON.stringify(lastDataSummary)
        
        if (!isDataSame) {
          console.warn(`⚠️ [FuturesOverview] 同一日期数据不一致！`, {
            date: selectedDate.value,
            currentData: currentDataSummary,
            lastData: lastDataSummary,
            requestTime: new Date().toLocaleString()
          })
          
          // 显示数据不一致警告
          // ElMessage.warning(`检测到同一日期数据不一致，请检查后端数据源是否使用了模拟数据`)
        } else {
          // console.log(`✅ [FuturesOverview] 同一日期数据一致性检查通过`)
        }
      }
      
      // 保存当前数据用于下次对比
      lastFetchData.value = {
        date: selectedDate.value,
        data: processedData,
        fetchTime: new Date().toISOString()
      }
      
      futuresData.value = processedData
    } else {
      throw new Error(response.message || '获取数据失败')
    }
  } catch (error) {
    ElMessage.error(`获取期货数据失败: ${error.message || error}`)
    
    // 如果接口调用失败，使用空数据
    futuresData.value = Object.keys(futuresConfig).map(symbol => ({
      symbol: symbol,
      name: futuresConfig[symbol].name,
      totalLong: 0,
      totalShort: 0,
      netPosition: 0,
      longChange: 0,
      shortChange: 0,
      netChange: 0
    }))
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = () => {
  // console.log(`🔄 [FuturesOverview] 手动刷新数据 - 时间: ${new Date().toLocaleString()}`)
  fetchFuturesData()
}

// 日期变化处理
const onDateChange = (date) => {
  selectedDate.value = date
  fetchFuturesData()
}

// 跳转到详细分析页面
const goToDetailPage = (symbol = null) => {
  const query = symbol ? { symbol } : {}
  router.push({ path: '/analysis/futures', query })
}

// 格式化持仓量（手）
const formatPosition = (value) => {
  if (!value) return '0手'
  return `${value.toLocaleString()}手`
}

// 格式化变化量
const formatChange = (value) => {
  if (!value) return '0'
  const formatted = Math.abs(value).toLocaleString()
  return value > 0 ? `+${formatted}手` : `-${formatted}手`
}

// AI数据上下文
const aiDataContext = computed(() => {
  const dateStr = selectedDate.value ? `${selectedDate.value.slice(0,4)}-${selectedDate.value.slice(4,6)}-${selectedDate.value.slice(6,8)}` : ''
  
  // 计算整体统计
  const getOverallStats = () => {
    const totalLong = futuresData.value.reduce((sum, item) => sum + (item.totalLong || 0), 0)
    const totalShort = futuresData.value.reduce((sum, item) => sum + (item.totalShort || 0), 0)
    const totalNetPosition = futuresData.value.reduce((sum, item) => sum + (item.netPosition || 0), 0)
    const totalLongChange = futuresData.value.reduce((sum, item) => sum + (item.longChange || 0), 0)
    const totalShortChange = futuresData.value.reduce((sum, item) => sum + (item.shortChange || 0), 0)
    const totalNetChange = futuresData.value.reduce((sum, item) => sum + (item.netChange || 0), 0)
    
    const netLongSymbols = futuresData.value.filter(item => item.netPosition > 0).length
    const netShortSymbols = futuresData.value.filter(item => item.netPosition < 0).length
    const neutralSymbols = futuresData.value.length - netLongSymbols - netShortSymbols
    
    return {
      totalLong,
      totalShort,
      totalNetPosition,
      totalLongChange,
      totalShortChange,
      totalNetChange,
      netLongSymbols,
      netShortSymbols,
      neutralSymbols,
      totalSymbols: futuresData.value.length
    }
  }
  
  const overallStats = getOverallStats()
  
  return {
    type: 'futures_holding_analysis',
    title: '股指期货持仓分析',
    period: dateStr,
    data: {
      date: dateStr,
      futuresData: futuresData.value,
      overallStats
    },
    summary: `股指期货持仓分析报告（${dateStr}）：

## 市场整体持仓概况
- 分析日期：${dateStr}
- 总多单量：${formatPosition(overallStats.totalLong)}
- 总空单量：${formatPosition(overallStats.totalShort)}
- 市场净持仓：${formatPosition(overallStats.totalNetPosition)}
- 多单变化：${formatChange(overallStats.totalLongChange)}
- 空单变化：${formatChange(overallStats.totalShortChange)}
- 净持仓变化：${formatChange(overallStats.totalNetChange)}

## 各品种持仓分析
${futuresData.value.map((futures, index) => 
  `${index + 1}. ${futures.name}（${futures.symbol}）：
   - 总多单量：${formatPosition(futures.totalLong)}
   - 总空单量：${formatPosition(futures.totalShort)}
   - 净持仓量：${formatPosition(Math.abs(futures.netPosition))}（${getPositionText(futures.netPosition)}）
   - 多单变化：${formatChange(futures.longChange)}
   - 空单变化：${formatChange(futures.shortChange)}
   - 净持仓变化：${formatChange(futures.netChange)}`
).join('\n\n')}

## 机构持仓结构分析
${futuresData.value.map((futures) => {
  if (!futures.brokerBreakdown) return ''
  return `${futures.name}机构分组：
   - 中信期货系：净持仓变化${formatChange(futures.brokerBreakdown.citic?.netPositionChg || 0)}（${futures.brokerBreakdown.citic?.institutionCount || 0}家机构）
   - 其他机构系：净持仓变化${formatChange(futures.brokerBreakdown.others?.netPositionChg || 0)}（${futures.brokerBreakdown.others?.institutionCount || 0}家机构）`
}).filter(text => text).join('\n\n')}

## 市场持仓分布
- 净多头品种：${overallStats.netLongSymbols}个
- 净空头品种：${overallStats.netShortSymbols}个  
- 中性品种：${overallStats.neutralSymbols}个
- 总分析品种：${overallStats.totalSymbols}个

## 持仓变化趋势分析
- 整体多空偏向：${overallStats.totalNetPosition > 0 ? '偏多头' : overallStats.totalNetPosition < 0 ? '偏空头' : '相对均衡'}
- 资金流向：${overallStats.totalNetChange > 0 ? '增加多头持仓' : overallStats.totalNetChange < 0 ? '增加空头持仓' : '持仓变化平衡'}
- 市场情绪：${overallStats.netLongSymbols > overallStats.netShortSymbols ? '偏向乐观' : overallStats.netLongSymbols < overallStats.netShortSymbols ? '偏向谨慎' : '情绪分化'}

## 技术分析要点
- 持仓集中度：${overallStats.totalSymbols > 0 ? '分散在' + overallStats.totalSymbols + '个主要品种' : '数据不足'}
- 机构参与度：${futuresData.value.some(f => f.brokerBreakdown) ? '机构积极参与，分组持仓明确' : '机构参与度有待提高'}
- 风险提示：建议关注净持仓变化较大的品种，注意市场情绪变化对持仓结构的影响

请基于以上完整的期货持仓数据，提供投资策略建议和风险控制方案。`
  }
})

// 获取卡片样式类
const getCardClass = (netPosition) => {
  if (netPosition > 0) return 'net-long'
  if (netPosition < 0) return 'net-short'
  return 'net-neutral'
}

// 获取持仓方向样式类
const getPositionClass = (netPosition) => {
  if (netPosition > 0) return 'long'
  if (netPosition < 0) return 'short'
  return 'neutral'
}

// 获取变化样式类
const getChangeClass = (change) => {
  if (change > 0) return 'positive'
  if (change < 0) return 'negative'
  return 'neutral'
}

// 获取持仓方向图标
const getPositionIcon = (netPosition) => {
  if (netPosition > 0) return ArrowTrendingUpIcon
  if (netPosition < 0) return ArrowTrendingDownIcon
  return MinusIcon
}

// 获取持仓方向文本
const getPositionText = (netPosition) => {
  if (netPosition > 0) return '净多头'
  if (netPosition < 0) return '净空头'
  return '中性'
}

// 获取趋势条样式
const getTrendBarStyle = (netPosition, netChange) => {
  const intensity = Math.min(Math.abs(netPosition) / 10000, 1) // 归一化强度
  let color = '#6b7280' // 默认灰色
  
  if (netPosition > 0) {
    color = netChange > 0 ? '#ef4444' : '#f87171' // 净多头：深红/浅红
  } else if (netPosition < 0) {
    color = netChange < 0 ? '#10b981' : '#34d399' // 净空头：深绿/浅绿
  }
  
  return {
    background: `linear-gradient(90deg, ${color} ${intensity * 100}%, rgba(107, 114, 128, 0.2) ${intensity * 100}%)`,
    height: '4px',
    borderRadius: '2px'
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchFuturesData()
})
</script>

<style scoped>
.futures-overview-panel {
  margin-bottom: var(--spacing-lg);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-left {
  flex: 1;
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
  gap: var(--spacing-sm);
  margin: 0 0 var(--spacing-xs) 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-icon {
  width: 24px;
  height: 24px;
  color: var(--accent-primary);
}

.section-subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.date-picker {
  width: 160px;
}

.refresh-btn,
.detail-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.btn-icon {
  width: 16px;
  height: 16px;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  gap: var(--spacing-md);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-top: 4px solid var(--accent-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 期货卡片容器 */
.futures-cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--spacing-lg);
}

/* 期货卡片 */
.futures-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.futures-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.2);
}

.futures-card.net-long {
  border-left: 4px solid #ef4444;
}

.futures-card.net-short {
  border-left: 4px solid #10b981;
}

.futures-card.net-neutral {
  border-left: 4px solid #6b7280;
}

/* 卡片头部 */
.futures-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.futures-info h4 {
  margin: 0 0 var(--spacing-xs) 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.futures-code {
  font-size: 12px;
  color: var(--text-tertiary);
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}

.net-position-indicator {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
}

.net-position-indicator.long {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.net-position-indicator.short {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.net-position-indicator.neutral {
  background: rgba(107, 114, 128, 0.2);
  color: #6b7280;
}

.position-icon {
  width: 14px;
  height: 14px;
}

/* 指标数据 */
.futures-metrics {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.metric-row {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.metric {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.metric .label {
  font-size: 12px;
  color: var(--text-secondary);
}

.metric .value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.metric .value.long {
  color: #ef4444;
}

.metric .value.short {
  color: #10b981;
}

.metric .value.change.positive {
  color: #ef4444;
}

.metric .value.change.negative {
  color: #10b981;
}

.metric .value.change.neutral {
  color: var(--text-secondary);
}

/* 趋势指示器 */
.trend-indicator {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-sm);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.trend-bar {
  width: 100%;
  height: 4px;
  border-radius: 2px;
  transition: all 0.3s ease;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  text-align: center;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-md);
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary);
  margin: 0 0 var(--spacing-xs) 0;
}

.empty-hint {
  font-size: 14px;
  color: var(--text-tertiary);
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: space-between;
  }
  
  .futures-cards-container {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }
  
  .metric-row {
    flex-direction: column;
    gap: var(--spacing-sm);
  }
  
  .broker-breakdown {
    margin-top: var(--spacing-sm);
  }
  
  .breakdown-content {
    flex-direction: column;
    gap: var(--spacing-xs);
  }
  
  .broker-group {
    padding: var(--spacing-xs);
  }
  
  .group-metrics {
    flex-direction: column;
    gap: var(--spacing-xs);
  }
}

@media (max-width: 1200px) and (min-width: 769px) {
  .futures-cards-container {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 机构分组样式 */
.broker-breakdown {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.breakdown-header {
  margin-bottom: var(--spacing-sm);
}

.breakdown-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.breakdown-content {
  display: flex;
  gap: var(--spacing-sm);
}

.broker-group {
  flex: 1;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: var(--spacing-sm);
  transition: all 0.2s ease;
}

.broker-group:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
}

.broker-group.citic {
  border-left: 3px solid var(--accent-primary);
}

.broker-group.others {
  border-left: 3px solid var(--accent-secondary);
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-xs);
}

.group-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.group-name.citic-name {
  color: #ff6b35; /* 橙红色，突出中信期货 */
}

.group-name.others-name {
  color: #4a9eff; /* 蓝色，表示其他机构 */
}

.group-count {
  font-size: 11px;
  color: var(--text-tertiary);
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 6px;
  border-radius: 10px;
}

.group-metrics {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.group-metric {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.metric-label {
  font-size: 10px;
  color: var(--text-tertiary);
  text-align: center;
}

.metric-value {
  font-size: 11px;
  font-weight: 600;
  text-align: center;
}

</style>
