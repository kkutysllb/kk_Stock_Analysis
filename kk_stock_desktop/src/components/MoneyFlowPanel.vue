<template>
  <div class="money-flow-panel card glass-effect">
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="header-left">
        <h3 class="section-title">
          <CurrencyDollarIcon class="section-icon" />
          每日资金流分析
          <AskAIComponent :data-context="aiDataContext" />
        </h3>
        <p class="section-subtitle">实时资金流向统计与市场情绪分析</p>
      </div>
      <div class="header-actions">
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="onDateChange"
          size="default"
          class="date-picker"
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

    <!-- 统计概览 -->
    <div class="card-body">
      <div class="stats-overview">
        <div class="stat-card">
          <div class="stat-icon positive">
            <ArrowTrendingUpIcon class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value positive">{{ formatAmount(marketSummary?.total_net_inflow || 0) }}</div>
            <div class="stat-label">市场流入</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon negative">
            <ArrowTrendingDownIcon class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value negative">{{ formatAmount(marketSummary?.total_net_outflow || 0) }}</div>
            <div class="stat-label">市场流出</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon" :class="getNetInflowClass()">
            <ScaleIcon class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value" :class="getNetInflowClass()">{{ formatAmount(getNetInflowValue()) }}</div>
            <div class="stat-label">市场净流入</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon info">
            <ChartBarIcon class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ marketSummary?.inflow_stocks || 0 }}</div>
            <div class="stat-label">净流入股票数</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon warning">
            <ChartBarIcon class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ marketSummary?.outflow_stocks || 0 }}</div>
            <div class="stat-label">净流出股票数</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon" :class="getSentimentClass(marketSummary?.market_sentiment || '中性')">
            <HeartIcon class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value" :class="getSentimentClass(marketSummary?.market_sentiment || '中性')">
              {{ marketSummary?.market_sentiment || '中性' }}
            </div>
            <div class="stat-label">市场情绪</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 上部：资金流图表和排行榜并排 -->
      <div class="top-panel">
        <div class="top-panel-grid">
          <!-- 左侧：资金流趋势图表 -->
          <div class="panel-section chart-section">
            <div class="section-header">
              <h4 class="section-title">
                <ChartBarIcon class="section-icon" />
                资金流向趋势
              </h4>
              <div class="section-controls">
                <el-radio-group v-model="chartType" @change="updateChart" size="small" class="chart-type-radio-group">
                  <el-radio-button value="net_flow">净流入趋势</el-radio-button>
                  <el-radio-button value="buy_sell">买卖对比</el-radio-button>
                  <el-radio-button value="distribution">资金分布</el-radio-button>
                </el-radio-group>
              </div>
            </div>
            
            <div class="chart-container" v-loading="loading">
              <div ref="chartRef" class="money-flow-chart"></div>
            </div>
          </div>
          
          <!-- 右侧：资金流排行榜 -->
          <div class="panel-section ranking-section">
            <div class="section-header">
              <h4 class="section-title">
                <ListBulletIcon class="section-icon" />
                资金流排行榜
              </h4>
              <div class="section-controls">
                <el-radio-group v-model="rankingType" @change="onRankingTypeChange" size="small" class="ranking-radio-group">
                  <el-radio-button value="inflow">净流入排行</el-radio-button>
                  <el-radio-button value="outflow">净流出排行</el-radio-button>
                </el-radio-group>
              </div>
            </div>
            
            <div v-loading="loading" class="ranking-table-container">
              <table class="ranking-table">
                <thead>
                  <tr>
                    <th class="rank-col">排名</th>
                    <th class="stock-col">股票</th>
                    <th class="industry-col">行业</th>
                    <th class="change-col">涨跌幅</th>
                    <th class="flow-col">资金流向</th>
                  </tr>
                </thead>
                <tbody>
                  <tr 
                    v-for="(item, index) in currentRankingData" 
                    :key="item.ts_code"
                    @click="selectStock(item)"
                    :class="{ 'selected': selectedStock?.ts_code === item.ts_code }"
                  >
                    <td class="rank-col">{{ index + 1 }}</td>
                    <td class="stock-col">
                      <div class="stock-info">
                        <div class="stock-name">{{ item.name }}</div>
                        <div class="stock-code">{{ item.ts_code }}</div>
                      </div>
                    </td>
                    <td class="industry-col">
                      <el-tag size="small" type="info">{{ item.industry }}</el-tag>
                    </td>
                    <td class="change-col">
                      <span class="value" :class="getChangeClass(item.pct_change)">
                        {{ item.pct_change > 0 ? '+' : '' }}{{ item.pct_change?.toFixed(2) }}%
                      </span>
                    </td>
                    <td class="flow-col">
                      <span class="value" :class="getChangeClass(item.net_amount)">
                        {{ formatAmount(item.net_amount) }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
              
              <div v-if="!loading && currentRankingData.length === 0" class="empty-state">
                <ExclamationTriangleIcon class="empty-icon" />
                <p class="empty-text">暂无资金流数据</p>
                <p class="empty-hint">请尝试选择其他日期或稍后刷新</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 下部：行业资金流分析 -->
      <div class="bottom-panel">
        <div class="section-header">
          <div class="section-title-row">
            <h4 class="section-title">
              <BuildingOfficeIcon class="section-icon" />
              行业资金流分析
            </h4>
            <div class="section-title-actions">
              <AskAIComponent :data-context="industryAiDataContext" />
            </div>
          </div>
          <div class="section-controls">
            <el-input
              v-model="industrySearchKeyword"
              placeholder="搜索行业"
              size="small"
              class="search-input"
              clearable
              @input="onIndustrySearchChange"
            >
              <template #prefix>
                <MagnifyingGlassIcon class="search-icon" />
              </template>
            </el-input>
          </div>
        </div>
        
        <!-- 行业资金流图表 -->
        <div class="industry-chart-container" v-if="industryData.length > 0">
          <div ref="industryChartRef" class="industry-chart"></div>
        </div>
        
        <!-- 行业资金流表格切换 -->
        <div class="industry-tabs">
          <el-radio-group v-model="industryTableType" size="small" @change="onIndustryTableTypeChange">
            <el-radio-button value="inflow">净流入行业</el-radio-button>
            <el-radio-button value="outflow">净流出行业</el-radio-button>
          </el-radio-group>
        </div>
        
        <div v-loading="loading" class="industry-table-container">
          <table class="industry-table">
            <thead>
              <tr>
                <th class="rank-col">排名</th>
                <th class="industry-col">行业名称</th>
                <th class="change-col">涨跌幅</th>
                <th class="close-col">收盘价</th>
                <th class="net-amount-col">{{ industryTableType === 'inflow' ? '净流入金额' : '净流出金额' }}</th>
                <th class="trend-col">趋势</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="(item, index) in filteredIndustryData" 
                :key="item.ts_code"
                @click="selectIndustry(item)"
                :class="{ 'selected': selectedIndustry?.ts_code === item.ts_code }"
              >
                <td class="rank-col">{{ index + 1 }}</td>
                <td class="industry-col">
                  <div class="industry-info">
                    <div class="industry-name">{{ item.name }}</div>
                    <div class="industry-code">{{ item.ts_code }}</div>
                  </div>
                </td>
                <td class="change-col">
                  <span class="value" :class="getChangeClass(item.pct_change)">
                    {{ item.pct_change > 0 ? '+' : '' }}{{ item.pct_change?.toFixed(2) }}%
                  </span>
                </td>
                <td class="close-col">
                  <span class="value">{{ item.close?.toFixed(2) }}</span>
                </td>
                <td class="net-amount-col">
                  <span class="value" :class="industryTableType === 'inflow' ? getChangeClass(item.net_amount) : 'negative'">
                    {{ industryTableType === 'inflow' ? formatAmount(item.net_amount) : formatAmount(item.net_outflow || 0) }}
                  </span>
                </td>
                <td class="trend-col">
                  <div class="trend-indicator" :class="industryTableType === 'inflow' ? getTrendClass(item.net_amount) : 'negative'">
                    <component :is="industryTableType === 'inflow' ? getTrendIcon(item.net_amount) : ArrowDownIcon" class="trend-icon" />
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          
          <div v-if="!loading && filteredIndustryData.length === 0" class="empty-state">
            <ExclamationTriangleIcon class="empty-icon" />
            <p class="empty-text">暂无行业资金流数据</p>
            <p class="empty-hint">请尝试选择其他日期或调整搜索条件</p>
          </div>
          
          <!-- 分页组件 -->
          <div class="pagination-container table-pagination" v-if="industryData.length > industryPageSize">
            <el-pagination
              v-model:current-page="industryCurrentPage"
              :page-size="industryPageSize"
              :total="industryData.length"
              layout="prev, pager, next, jumper, total"
              size="small"
              @current-change="handleIndustryPageChange"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { marketAPI } from '../api/market'
import AskAIComponent from './AskAIComponent.vue'
import {
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ScaleIcon,
  HeartIcon,
  ChartBarIcon,
  ListBulletIcon,
  BuildingOffice2Icon as BuildingOfficeIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  MinusIcon
} from '@heroicons/vue/24/outline'

// 响应式数据
const loading = ref(false)
const selectedDate = ref(new Date().toISOString().split('T')[0])
const chartType = ref('net_flow')
const rankingType = ref('inflow')
const industrySearchKeyword = ref('')
const chartRef = ref<HTMLElement>()
const chart = ref<echarts.ECharts>()
const industryChartRef = ref<HTMLElement>()
const industryChart = ref<echarts.ECharts>()

// 数据状态
const marketSummary = ref({
  total_net_inflow: 0,
  total_net_outflow: 0,
  inflow_stocks: 0,
  outflow_stocks: 0,
  market_sentiment: '中性'
})

const inflowRankingData = ref<any[]>([])
const outflowRankingData = ref<any[]>([])
const industryData = ref<any[]>([])
const inflowIndustryData = ref<any[]>([])
const outflowIndustryData = ref<any[]>([])
const marketFlowData = ref<any[]>([])
const selectedStock = ref<any>(null)
const selectedIndustry = ref<any>(null)

// 行业表格类型
const industryTableType = ref('inflow')

// 分页相关
const industryCurrentPage = ref(1)
const industryPageSize = ref(15)

// ResizeObserver引用
const resizeObserverRef = ref<ResizeObserver | null>(null)

// 计算属性
const currentRankingData = computed(() => {
  return rankingType.value === 'inflow' ? inflowRankingData.value : outflowRankingData.value
})

const filteredIndustryData = computed(() => {
  const currentData = industryTableType.value === 'inflow' ? inflowIndustryData.value : outflowIndustryData.value
  
  let filtered = currentData
  
  if (industrySearchKeyword.value) {
    const keyword = industrySearchKeyword.value.toLowerCase()
    filtered = filtered.filter((item: any) => 
      item.name?.toLowerCase().includes(keyword) ||
      item.ts_code?.toLowerCase().includes(keyword)
    )
  }
  
  const start = (industryCurrentPage.value - 1) * industryPageSize.value
  const end = start + industryPageSize.value
  return filtered.slice(start, end)
})

// AI数据上下文
const aiDataContext = computed(() => {
  const summary = marketSummary.value
  const topInflowStocks = inflowRankingData.value.slice(0, 10)
  const topOutflowStocks = outflowRankingData.value.slice(0, 10)
  const topInflowIndustries = inflowIndustryData.value.slice(0, 10)
  const topOutflowIndustries = outflowIndustryData.value.slice(0, 10)
  
  // 计算历史数据统计
  const getHistoricalStats = () => {
    if (!marketFlowData.value || marketFlowData.value.length === 0) return null
    
    const netFlows = marketFlowData.value.map(item => item.net_amount || 0)
    const totalInflows = marketFlowData.value.map(item => item.total_inflow || 0)
    const totalOutflows = marketFlowData.value.map(item => item.total_outflow || 0)
    
    return {
      dataPoints: marketFlowData.value.length,
      netFlowStats: {
        min: Math.min(...netFlows),
        max: Math.max(...netFlows),
        avg: netFlows.reduce((sum, val) => sum + val, 0) / netFlows.length,
        total: netFlows.reduce((sum, val) => sum + val, 0),
        positiveCount: netFlows.filter(val => val > 0).length,
        negativeCount: netFlows.filter(val => val < 0).length
      },
      inflowStats: {
        min: Math.min(...totalInflows),
        max: Math.max(...totalInflows),
        avg: totalInflows.reduce((sum, val) => sum + val, 0) / totalInflows.length,
        total: totalInflows.reduce((sum, val) => sum + val, 0)
      },
      outflowStats: {
        min: Math.min(...totalOutflows),
        max: Math.max(...totalOutflows),
        avg: totalOutflows.reduce((sum, val) => sum + val, 0) / totalOutflows.length,
        total: totalOutflows.reduce((sum, val) => sum + val, 0)
      }
    }
  }
  
  const historicalStats = getHistoricalStats()
  
  // 计算行业资金流统计
  const industryStats = {
    totalInflowIndustries: inflowIndustryData.value.length,
    totalOutflowIndustries: outflowIndustryData.value.length,
    totalIndustries: inflowIndustryData.value.length + outflowIndustryData.value.length,
    topInflowAmount: inflowIndustryData.value[0]?.net_amount || 0,
    topOutflowAmount: Math.abs(outflowIndustryData.value[0]?.net_amount || 0),
    totalInflowAmount: inflowIndustryData.value.reduce((sum, item) => sum + (item.net_amount || 0), 0),
    totalOutflowAmount: Math.abs(outflowIndustryData.value.reduce((sum, item) => sum + (item.net_amount || 0), 0))
  }
  
  // 计算个股资金流统计
  const stockStats = {
    totalInflowStocks: inflowRankingData.value.length,
    totalOutflowStocks: outflowRankingData.value.length,
    topInflowAmount: inflowRankingData.value[0]?.net_amount || 0,
    topOutflowAmount: Math.abs(outflowRankingData.value[0]?.net_amount || 0),
    totalStockInflowAmount: inflowRankingData.value.reduce((sum, item) => sum + (item.net_amount || 0), 0),
    totalStockOutflowAmount: Math.abs(outflowRankingData.value.reduce((sum, item) => sum + (item.net_amount || 0), 0))
  }
  
  return {
    type: 'money_flow_analysis',
    title: '每日资金流分析',
    period: selectedDate.value,
    data: {
      date: selectedDate.value,
      marketSummary: {
        totalNetInflow: summary.total_net_inflow,
        totalNetOutflow: summary.total_net_outflow,
        inflowStocks: summary.inflow_stocks,
        outflowStocks: summary.outflow_stocks,
        marketSentiment: summary.market_sentiment,
        netValue: getNetInflowValue()
      },
      topInflowStocks,
      topOutflowStocks,
      topInflowIndustries,
      topOutflowIndustries,
      historicalData: marketFlowData.value,
      statistics: {
        historical: historicalStats,
        industry: industryStats,
        stock: stockStats
      }
    },
    summary: `每日资金流分析完整报告（${selectedDate.value}）：

## 市场整体资金流向
- 分析日期：${selectedDate.value}
- 市场情绪：${summary.market_sentiment}
- 总净流入：${formatAmount(summary.total_net_inflow || 0)}
- 总净流出：${formatAmount(Math.abs(summary.total_net_outflow || 0))}
- 净流入金额：${formatAmount(getNetInflowValue())}
- 净流入股票数：${summary.inflow_stocks || 0}只
- 净流出股票数：${summary.outflow_stocks || 0}只

## 个股资金流排行榜

### 资金净流入TOP10
${topInflowStocks.map((stock, index) => 
  `${index + 1}. ${stock.name}（${stock.ts_code}）：净流入${formatAmount(stock.net_amount)}，涨跌幅${stock.pct_chg > 0 ? '+' : ''}${stock.pct_chg?.toFixed(2) || 0}%`
).join('\n')}

### 资金净流出TOP10
${topOutflowStocks.map((stock, index) => 
  `${index + 1}. ${stock.name}（${stock.ts_code}）：净流出${formatAmount(Math.abs(stock.net_amount))}，涨跌幅${stock.pct_chg > 0 ? '+' : ''}${stock.pct_chg?.toFixed(2) || 0}%`
).join('\n')}

## 行业资金流分析

### 资金净流入行业TOP10
${topInflowIndustries.map((industry, index) => 
  `${index + 1}. ${industry.industry_name}：净流入${formatAmount(industry.net_amount)}，涨跌幅${industry.pct_chg > 0 ? '+' : ''}${industry.pct_chg?.toFixed(2) || 0}%`
).join('\n')}

### 资金净流出行业TOP10
${topOutflowIndustries.map((industry, index) => 
  `${index + 1}. ${industry.industry_name}：净流出${formatAmount(Math.abs(industry.net_amount))}，涨跌幅${industry.pct_chg > 0 ? '+' : ''}${industry.pct_chg?.toFixed(2) || 0}%`
).join('\n')}

## 历史数据分析
${historicalStats ? `
- 历史数据点：${historicalStats.dataPoints}个交易日
- 净流入统计：
  * 最大净流入：${formatAmount(historicalStats.netFlowStats.max)}
  * 最大净流出：${formatAmount(Math.abs(historicalStats.netFlowStats.min))}
  * 平均净流入：${formatAmount(historicalStats.netFlowStats.avg)}
  * 累计净流入：${formatAmount(historicalStats.netFlowStats.total)}
  * 净流入天数：${historicalStats.netFlowStats.positiveCount}天
  * 净流出天数：${historicalStats.netFlowStats.negativeCount}天
- 资金流入统计：
  * 最大单日流入：${formatAmount(historicalStats.inflowStats.max)}
  * 最小单日流入：${formatAmount(historicalStats.inflowStats.min)}
  * 平均日流入：${formatAmount(historicalStats.inflowStats.avg)}
  * 累计流入：${formatAmount(historicalStats.inflowStats.total)}
- 资金流出统计：
  * 最大单日流出：${formatAmount(historicalStats.outflowStats.max)}
  * 最小单日流出：${formatAmount(historicalStats.outflowStats.min)}
  * 平均日流出：${formatAmount(historicalStats.outflowStats.avg)}
  * 累计流出：${formatAmount(historicalStats.outflowStats.total)}
` : '- 暂无历史数据'}

## 行业资金流统计汇总
- 净流入行业数：${industryStats.totalInflowIndustries}个
- 净流出行业数：${industryStats.totalOutflowIndustries}个
- 总行业数：${industryStats.totalIndustries}个
- 最大行业净流入：${formatAmount(industryStats.topInflowAmount)}
- 最大行业净流出：${formatAmount(industryStats.topOutflowAmount)}
- 行业总净流入：${formatAmount(industryStats.totalInflowAmount)}
- 行业总净流出：${formatAmount(industryStats.totalOutflowAmount)}

## 个股资金流统计汇总
- 净流入个股数：${stockStats.totalInflowStocks}只
- 净流出个股数：${stockStats.totalOutflowStocks}只
- 最大个股净流入：${formatAmount(stockStats.topInflowAmount)}
- 最大个股净流出：${formatAmount(stockStats.topOutflowAmount)}
- 个股总净流入：${formatAmount(stockStats.totalStockInflowAmount)}
- 个股总净流出：${formatAmount(stockStats.totalStockOutflowAmount)}

## 技术分析要点
- 市场资金流向：${getNetInflowValue() > 0 ? '净流入' : getNetInflowValue() < 0 ? '净流出' : '平衡'}
- 市场活跃度：${summary.inflow_stocks + summary.outflow_stocks > 3000 ? '高' : summary.inflow_stocks + summary.outflow_stocks > 2000 ? '中' : '低'}
- 资金集中度：${stockStats.topInflowAmount > 10000000000 ? '高度集中' : stockStats.topInflowAmount > 5000000000 ? '相对集中' : '分散'}
- 行业轮动：${industryStats.totalInflowIndustries > industryStats.totalOutflowIndustries ? '积极' : '谨慎'}

请基于以上完整的资金流数据分析（包括历史数据、行业分析、个股分析），提供投资建议和风险提示。`
  }
})

// 行业资金流AI数据上下文
const industryAiDataContext = computed(() => {
  const currentInflowIndustries = inflowIndustryData.value.slice(0, 20)
  const currentOutflowIndustries = outflowIndustryData.value.slice(0, 20)
  
  // 计算行业资金流统计
  const getIndustryStats = () => {
    const allIndustries = [...currentInflowIndustries, ...currentOutflowIndustries]
    const totalInflowAmount = currentInflowIndustries.reduce((sum, item) => sum + (item.net_amount || 0), 0)
    const totalOutflowAmount = Math.abs(currentOutflowIndustries.reduce((sum, item) => sum + (item.net_amount || 0), 0))
    const netAmount = totalInflowAmount - totalOutflowAmount
    
    return {
      totalIndustries: allIndustries.length,
      inflowIndustries: currentInflowIndustries.length,
      outflowIndustries: currentOutflowIndustries.length,
      totalInflowAmount,
      totalOutflowAmount,
      netAmount,
      avgInflowAmount: currentInflowIndustries.length > 0 ? totalInflowAmount / currentInflowIndustries.length : 0,
      avgOutflowAmount: currentOutflowIndustries.length > 0 ? totalOutflowAmount / currentOutflowIndustries.length : 0,
      topInflowAmount: currentInflowIndustries[0]?.net_amount || 0,
      topOutflowAmount: Math.abs(currentOutflowIndustries[0]?.net_amount || 0)
    }
  }
  
  const industryStats = getIndustryStats()
  
  return {
    type: 'industry_money_flow_analysis',
    title: '行业资金流分析',
    period: selectedDate.value,
    data: {
      date: selectedDate.value,
      inflowIndustries: currentInflowIndustries,
      outflowIndustries: currentOutflowIndustries,
      statistics: industryStats,
      searchKeyword: industrySearchKeyword.value,
      tableType: industryTableType.value
    },
    summary: `行业资金流分析专项报告（${selectedDate.value}）：

## 行业资金流概览
- 分析日期：${selectedDate.value}
- 总分析行业数：${industryStats.totalIndustries}个
- 净流入行业数：${industryStats.inflowIndustries}个
- 净流出行业数：${industryStats.outflowIndustries}个
- 行业总净流入：${formatAmount(industryStats.totalInflowAmount)}
- 行业总净流出：${formatAmount(industryStats.totalOutflowAmount)}
- 行业净资金流向：${formatAmount(industryStats.netAmount)}

## 资金净流入行业TOP20
${currentInflowIndustries.map((industry, index) => 
  `${index + 1}. ${industry.name}（${industry.ts_code}）：净流入${formatAmount(industry.net_amount)}，涨跌幅${industry.pct_chg > 0 ? '+' : ''}${industry.pct_chg?.toFixed(2) || 0}%，收盘价${industry.close?.toFixed(2) || 0}`
).join('\n')}

## 资金净流出行业TOP20
${currentOutflowIndustries.map((industry, index) => 
  `${index + 1}. ${industry.name}（${industry.ts_code}）：净流出${formatAmount(Math.abs(industry.net_amount))}，涨跌幅${industry.pct_chg > 0 ? '+' : ''}${industry.pct_chg?.toFixed(2) || 0}%，收盘价${industry.close?.toFixed(2) || 0}`
).join('\n')}

## 行业资金流统计分析
- 最大净流入行业：${currentInflowIndustries[0]?.name || '无'}，金额${formatAmount(industryStats.topInflowAmount)}
- 最大净流出行业：${currentOutflowIndustries[0]?.name || '无'}，金额${formatAmount(industryStats.topOutflowAmount)}
- 平均净流入金额：${formatAmount(industryStats.avgInflowAmount)}
- 平均净流出金额：${formatAmount(industryStats.avgOutflowAmount)}
- 资金流向偏好：${industryStats.netAmount > 0 ? '整体偏向流入' : industryStats.netAmount < 0 ? '整体偏向流出' : '流入流出基本平衡'}

## 行业轮动分析
- 强势行业占比：${((industryStats.inflowIndustries / industryStats.totalIndustries) * 100).toFixed(1)}%
- 弱势行业占比：${((industryStats.outflowIndustries / industryStats.totalIndustries) * 100).toFixed(1)}%
- 市场行业分化程度：${industryStats.inflowIndustries > industryStats.outflowIndustries ? '多数行业获得资金青睐' : industryStats.inflowIndustries < industryStats.outflowIndustries ? '多数行业遭遇资金流出' : '行业间资金流向分化明显'}

## 技术分析要点
- 资金集中度：${industryStats.topInflowAmount > industryStats.avgInflowAmount * 3 ? '高度集中' : industryStats.topInflowAmount > industryStats.avgInflowAmount * 2 ? '相对集中' : '相对分散'}
- 行业轮动状态：${industryStats.inflowIndustries > industryStats.totalIndustries * 0.6 ? '普涨轮动' : industryStats.outflowIndustries > industryStats.totalIndustries * 0.6 ? '普跌调整' : '结构性轮动'}
- 投资建议：基于行业资金流向，建议关注净流入前5名行业，规避净流出前5名行业

请基于以上完整的行业资金流数据，提供详细的行业投资策略和风险提示。`
  }
})

// 方法
const formatAmount = (amount: number) => {
  if (!amount) return '0'
  const absAmount = Math.abs(amount)
  if (absAmount >= 100000000) {
    return `${(amount / 100000000).toFixed(2)}亿`
  } else if (absAmount >= 10000) {
    return `${(amount / 10000).toFixed(2)}万`
  }
  return amount.toLocaleString()
}

const getChangeClass = (value: number) => {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}

const getSentimentClass = (sentiment: string) => {
  if (sentiment === '乐观' || sentiment === '积极') return 'positive'
  if (sentiment === '悲观' || sentiment === '消极') return 'negative'
  return 'info'
}

// 计算市场净流入值
const getNetInflowValue = () => {
  const inflow = marketSummary.value?.total_net_inflow || 0
  const outflow = marketSummary.value?.total_net_outflow || 0
  return inflow - outflow
}

// 获取净流入样式类
const getNetInflowClass = () => {
  const netValue = getNetInflowValue()
  if (netValue > 0) return 'positive'
  if (netValue < 0) return 'negative'
  return 'info'
}

const getTrendClass = (value: number) => {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}

const getTrendIcon = (value: number) => {
  if (value > 0) return ArrowUpIcon
  if (value < 0) return ArrowDownIcon
  return MinusIcon
}

const selectStock = (stock: any) => {
  selectedStock.value = stock
}

const selectIndustry = (industry: any) => {
  selectedIndustry.value = industry
}

const onIndustryTableTypeChange = () => {
  // 重置分页
  industryCurrentPage.value = 1
  // 重置选中行业
  selectedIndustry.value = null
  // 更新图表
  nextTick(() => {
    updateIndustryChart()
  })
}

const onDateChange = () => {
  loadData()
}

const onRankingTypeChange = () => {
  // 排行榜类型切换时不需要重新加载数据
}

const onIndustrySearchChange = () => {
  industryCurrentPage.value = 1
}

const handleIndustryPageChange = (page: number) => {
  industryCurrentPage.value = page
}

const refreshData = () => {
  loadData()
}

// 图表相关方法
const initChart = () => {
  if (!chartRef.value) return
  
  // 销毁旧的实例
  if (chart.value) {
    chart.value.dispose()
  }
  
  // 创建新实例
  // 先检查是否已有实例，避免重复初始化
  const existingInstance = echarts.getInstanceByDom(chartRef.value)
  if (existingInstance) {
    existingInstance.dispose()
  }
  chart.value = echarts.init(chartRef.value, null, {
    renderer: 'canvas'  // 显式指定渲染器为canvas
  })
  
  // 绑定鼠标事件，用于调试
  chart.value.on('mouseover', function(params) {})
  
  // 监听窗口大小变化，自动调整图表大小
  window.addEventListener('resize', resizeChart)
  
  // 更新图表
  nextTick(() => {
    updateChart()
  })
}

const updateChart = () => {
  if (!chart.value || !marketFlowData.value.length) {
    return
  }
  
  // 清除之前的图表配置
  chart.value.clear()
  
  // 按日期排序数据（从早到晚）
  const sortedData = [...marketFlowData.value].sort((a, b) => a.trade_date.localeCompare(b.trade_date))
  
  // 基础配置，适用于所有图表
  const baseOption = {
    tooltip: {
      show: true,
      backgroundColor: 'rgba(50, 50, 50, 0.9)',
      borderWidth: 0,
      textStyle: {
        color: '#fff',
        fontSize: 13
      },
      padding: [10, 15],
      extraCssText: 'box-shadow: 0 0 10px rgba(0, 0, 0, 0.3); border-radius: 6px;',
      confine: true,
      enterable: true,
      transitionDuration: 0.2
    }
  }
  
  let option: any = {}
  
  if (chartType.value === 'net_flow') {
    // 净流入趋势图
    option = {
      title: {
        textStyle: { fontSize: 14, color: '#333' }
      },
      tooltip: {
        ...baseOption.tooltip,
        trigger: 'item',
        axisPointer: {
          type: 'line',
          animation: false,
          lineStyle: {
            color: '#409EFF',
            width: 1,
            type: 'solid'
          }
        },
        formatter: function(params: any) {
          if (!params) return '';
          
          const dataIndex = params.dataIndex;
          if (dataIndex === undefined || dataIndex < 0 || dataIndex >= sortedData.length) {
            return '';
          }
          
          const originalData = sortedData[dataIndex];
          if (!originalData) return '';
          
          const date = `${originalData.trade_date.slice(0,4)}-${originalData.trade_date.slice(4,6)}-${originalData.trade_date.slice(6,8)}`;
          const changeClass = originalData.net_amount > 0 ? 'color: #F56C6C' : 'color: #67C23A';
          const changeIcon = originalData.net_amount > 0 ? '↑' : '↓';
          
          return `
            <div style="font-weight: bold; margin-bottom: 5px; font-size: 14px;">${date}</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
              <span>净流入:</span>
              <span style="${changeClass}">${formatAmount(originalData.net_amount)} ${changeIcon}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
              <span>流入金额:</span>
              <span style="color: #F56C6C">${formatAmount(originalData.net_inflow)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
              <span>流出金额:</span>
              <span style="color: #67C23A">${formatAmount(Math.abs(originalData.net_outflow))}</span>
            </div>
          `;
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: sortedData.map((item: any) => {
          const date = item.trade_date
          return `${date.slice(4,6)}-${date.slice(6,8)}`
        }),
        axisLabel: {
          fontSize: 12
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (value: number) => formatAmount(value)
        }
      },
      series: [{
        name: '净流入',
        type: 'line',
        data: sortedData.map((item: any) => {
          return {
            value: item.net_amount,
            itemStyle: {
              color: '#409EFF'
            }
          };
        }),
        smooth: true,
        lineStyle: { color: '#409EFF', width: 2 },
        areaStyle: { 
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
          ])
        },
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: {
          color: '#409EFF',
          borderColor: '#fff',
          borderWidth: 2
        },
        emphasis: {
          itemStyle: {
            color: '#409EFF',
            borderColor: '#fff',
            borderWidth: 3,
            shadowBlur: 10,
            shadowColor: 'rgba(64, 158, 255, 0.5)'
          },
          symbolSize: 12
        }
      }]
    }
  } else if (chartType.value === 'buy_sell') {
    // 买卖对比图
    option = {
      title: {
        textStyle: { fontSize: 14, color: '#333' }
      },
      tooltip: {
        ...baseOption.tooltip,
        trigger: 'item',
        formatter: function(params: any) {
          if (!params) return '';
          
          const dataIndex = params.dataIndex;
          if (dataIndex === undefined || dataIndex < 0 || dataIndex >= sortedData.length) {
            return '';
          }
          
          const originalData = sortedData[dataIndex];
          if (!originalData) return '';
          
          const date = `${originalData.trade_date.slice(0,4)}-${originalData.trade_date.slice(4,6)}-${originalData.trade_date.slice(6,8)}`;
          
          // 计算买入卖出比例
          const totalVolume = originalData.net_inflow + Math.abs(originalData.net_outflow);
          const inRatio = totalVolume ? (originalData.net_inflow / totalVolume * 100).toFixed(2) : '0.00';
          const outRatio = totalVolume ? (Math.abs(originalData.net_outflow) / totalVolume * 100).toFixed(2) : '0.00';
          
          return `
            <div style="font-weight: bold; margin-bottom: 5px; font-size: 14px;">${date}</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
              <span>买入金额:</span>
              <span style="color: #F56C6C">${formatAmount(originalData.net_inflow)} (${inRatio}%)</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
              <span>卖出金额:</span>
              <span style="color: #67C23A">${formatAmount(Math.abs(originalData.net_outflow))} (${outRatio}%)</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
              <span>净流入金额:</span>
              <span style="${originalData.net_amount > 0 ? 'color: #F56C6C' : 'color: #67C23A'}">
                ${formatAmount(originalData.net_amount)}
              </span>
            </div>
          `;
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      legend: {
        data: ['买入', '卖出'],
        top: 30,
        textStyle: {
          color: 'var(--el-text-color-primary)'
        },
        inactiveColor: 'rgba(128, 128, 128, 0.5)'
      },
      color: ['#F56C6C', '#67C23A'],
      xAxis: {
        type: 'category',
        data: sortedData.map((item: any) => {
          const date = item.trade_date
          return `${date.slice(4,6)}-${date.slice(6,8)}`
        }),
        axisLabel: {
          fontSize: 12
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (value: number) => formatAmount(value)
        }
      },
      series: [
        {
          name: '买入',
          type: 'bar',
          data: sortedData.map((item: any) => ({
            value: item.net_inflow,
            itemStyle: { color: '#F56C6C' }
          })),
          barWidth: '35%'
        },
        {
          name: '卖出',
          type: 'bar',
          data: sortedData.map((item: any) => ({
            value: Math.abs(item.net_outflow),
            itemStyle: { color: '#67C23A' }
          })),
          barWidth: '35%'
        }
      ]
    }
  } else if (chartType.value === 'distribution') {
    // 资金分布饼图 - 保留原有配置，因为它的tooltip正常工作
    const totalInflow = marketSummary.value?.total_net_inflow || 0
    const distributionData = [
      { name: '超大单净流入', value: Math.abs(totalInflow * 0.4) },
      { name: '大单净流入', value: Math.abs(totalInflow * 0.3) },
      { name: '中单净流入', value: Math.abs(totalInflow * 0.2) },
      { name: '小单净流入', value: Math.abs(totalInflow * 0.1) }
    ]
    
    // 定义颜色映射类型
    interface ColorMap {
      [key: string]: string;
    }
    
    option = {
      title: {
        textStyle: { fontSize: 14, color: '#333' }
      },
      tooltip: {
        show: true,
        trigger: 'item',
        backgroundColor: 'rgba(50, 50, 50, 0.9)',
        borderWidth: 0,
        textStyle: {
          color: '#fff',
          fontSize: 13
        },
        padding: [10, 15],
        extraCssText: 'box-shadow: 0 0 10px rgba(0, 0, 0, 0.3); border-radius: 6px;',
        confine: true,
        enterable: true,
        transitionDuration: 0.2,
        formatter: function(params: any) {
          // 为每种类型分配不同颜色
          const colorMap: ColorMap = {
            '超大单净流入': '#F56C6C',
            '大单净流入': '#E6A23C',
            '中单净流入': '#409EFF',
            '小单净流入': '#67C23A'
          }
          
          const name = params.name as string;
          
          return `
            <div style="font-weight: bold; margin-bottom: 5px; font-size: 14px;">${name}</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
              <span>金额:</span>
              <span style="color: ${colorMap[name] || '#fff'}">${formatAmount(params.value)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
              <span>占比:</span>
              <span style="color: ${colorMap[name] || '#fff'}">${params.percent}%</span>
            </div>
            <div style="margin-top: 5px; padding-top: 5px; border-top: 1px dashed rgba(255,255,255,0.2);">
              <span style="font-size: 12px; color: #ccc;">点击查看详情</span>
            </div>
          `
        }
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        textStyle: {
          color: 'var(--el-text-color-primary)'
        }
      },
      series: [{
        name: '资金分布',
        type: 'pie',
        radius: '60%',
        data: distributionData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        label: {
          show: true,
          formatter: '{b}: {d}%'
        }
      }]
    }
  }
  
  // 设置图表选项
  chart.value.setOption(option, true)
}

// 添加图表重绘方法
const resizeChart = () => {
  if (chart.value) {
    chart.value.resize()
  }
}

// 行业图表相关方法
const initIndustryChart = () => { 
  if (!industryChartRef.value) {
    return
  }
  
  // 销毁旧的实例
  if (industryChart.value) {
    industryChart.value.dispose()
  }
  
  // 创建新实例
  industryChart.value = echarts.init(industryChartRef.value, null, {
    renderer: 'canvas'
  })
  
  
  // 监听窗口大小变化
  window.addEventListener('resize', resizeIndustryChart)
  
  // 更新图表
  nextTick(() => {
    updateIndustryChart()
  })
}

const updateIndustryChart = () => {
  
  // 如果数据为空，跳过更新
  if (!inflowIndustryData.value.length && !outflowIndustryData.value.length) {
    return
  }
  
  // 如果图表实例不存在，先创建它
  if (!industryChart.value) {
    if (!industryChartRef.value) {
      return
    }
    
    // 先检查是否已有实例，避免重复初始化
    const existingInstance = echarts.getInstanceByDom(industryChartRef.value)
    if (existingInstance) {
      existingInstance.dispose()
    }
    industryChart.value = echarts.init(industryChartRef.value, null, {
      renderer: 'canvas'
    })
  }
  
  // 清除之前的图表配置
  industryChart.value.clear()
  
  // 显示各自top50的数值
  const topInflowIndustries = inflowIndustryData.value.slice(0, 50)
  const topOutflowIndustries = outflowIndustryData.value.slice(0, 50)
  
  
  // 使用全部top50数据用于图表显示
  const chartInflowIndustries = topInflowIndustries
  const chartOutflowIndustries = topOutflowIndustries
  
  // 合并行业名称，去重
  const allIndustryNames = [...new Set([
    ...chartInflowIndustries.map(item => item.name),
    ...chartOutflowIndustries.map(item => item.name)
  ])]
  
  
  // 准备图表数据
  const categories = allIndustryNames
  const inflowData = categories.map(name => {
    const industry = chartInflowIndustries.find(item => item.name === name)
    return industry ? industry.net_amount : 0
  })
  const outflowData = categories.map(name => {
    const industry = chartOutflowIndustries.find(item => item.name === name)
    return industry ? Math.abs(industry.net_amount) : 0 // 修复：使用net_amount的绝对值
  })
  
  // 保存行业数据用于tooltip
  const industryMap = new Map()
  chartInflowIndustries.forEach(item => {
    industryMap.set(item.name, item)
  })
  chartOutflowIndustries.forEach(item => {
    if (!industryMap.has(item.name)) {
      industryMap.set(item.name, item)
    }
  })
  
  const option = {
    title: {
      text: '行业资金流向对比',
      left: 'center',
      textStyle: {
        color: 'var(--el-text-color-primary)',
        fontSize: 16
      }
    },
    tooltip: {
      show: true,
      trigger: 'item',
      axisPointer: {
        type: 'shadow'
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
        // 如果是数组，取第一个元素
        if (Array.isArray(params)) {
          params = params[0];
        }
        
        const categoryName = params.name
        const industry = industryMap.get(categoryName)
        
        let result = `<div style="font-weight: bold; margin-bottom: 8px;">${categoryName}</div>`
        
        // 添加行业信息
        if (industry) {
          result += `
            <div style="margin-bottom: 5px; border-bottom: 1px dashed rgba(255,255,255,0.2); padding-bottom: 5px;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                <span>收盘价:</span>
                <span>${industry.close?.toFixed(2) || '-'}</span>
              </div>
              <div style="display: flex; justify-content: space-between;">
                <span>涨跌幅:</span>
                <span style="color: ${industry.pct_change > 0 ? '#F56C6C' : '#67C23A'}">
                  ${industry.pct_change > 0 ? '+' : ''}${industry.pct_change?.toFixed(2) || 0}%
                </span>
              </div>
            </div>
          `
        }
        
        // 添加资金流向数据
        const color = params.color || (params.value >= 0 ? '#F56C6C' : '#67C23A')
        const seriesName = params.seriesName || (params.value >= 0 ? '净流入' : '净流出')
        const value = params.value
        const absValue = Math.abs(value)
        const formattedValue = (absValue / 100000000).toFixed(2) + '亿元'
        
        result += `
          <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
            <span style="display: flex; align-items: center;">
              <span style="display:inline-block;margin-right:5px;border-radius:50%;width:6px;height:6px;background-color:${color};"></span>
              ${seriesName}
            </span>
            <span style="color: ${color};">${value >= 0 ? '+' : ''}${formattedValue}</span>
          </div>
        `
        
        return result
      }
    },
    legend: {
      data: ['净流入', '净流出'],
      top: 30,
      textStyle: {
        color: 'var(--el-text-color-primary)'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        rotate: 45,
        color: 'var(--el-text-color-regular)'
      }
    },
    yAxis: {
      type: 'value',
      name: '资金流向(亿元)',
      position: 'left',
      axisLabel: {
        show: false  // 隐藏刻度标签
      },
      splitLine: {
        show: false  // 隐藏网格线
      },
      axisLine: {
        show: false  // 隐藏Y轴线
      },
      axisTick: {
        show: false  // 隐藏刻度线
      }
    },
    series: [
      {
        name: '净流入',
        type: 'bar',
        data: inflowData,
        itemStyle: {
          color: '#F56C6C'
        },
        barWidth: '35%',
        tooltip: {
          show: true
        },
        emphasis: {
          focus: 'series',
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      },
      {
        name: '净流出',
        type: 'bar',
        data: outflowData.map(val => -val), // 显示为负值，在水平轴下方
        itemStyle: {
          color: '#67C23A'
        },
        barWidth: '35%',
        tooltip: {
          show: true
        },
        emphasis: {
          focus: 'series',
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }
  
  industryChart.value.setOption(option)
  
  // 添加点击事件，选择行业
  industryChart.value.off('click')
  industryChart.value.on('click', function(params: any) {
    if (params.componentType === 'series') {
      const industryName = params.name
      const industry = chartInflowIndustries.find(item => item.name === industryName) || 
                       chartOutflowIndustries.find(item => item.name === industryName)
      
      if (industry) {
        selectIndustry(industry)
      }
    }
  })
}

const resizeIndustryChart = () => {
  if (industryChart.value) {
    industryChart.value.resize()
  }
}

// 确保所有图表自适应
const setupChartResize = () => {
  // 监听窗口大小变化
  window.addEventListener('resize', resizeChart)
  window.addEventListener('resize', resizeIndustryChart)
  
  // 监听容器大小变化
  if (typeof ResizeObserver !== 'undefined') {
    const resizeObserver = new ResizeObserver(() => {
      if (chart.value) chart.value.resize()
      if (industryChart.value) industryChart.value.resize()
    })
    
    if (chartRef.value) resizeObserver.observe(chartRef.value)
    if (industryChartRef.value) resizeObserver.observe(industryChartRef.value)
    
    // 保存resizeObserver实例以便在组件卸载时移除
    return resizeObserver
  }
  
  return null
}

// 在组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('resize', resizeChart)
  window.removeEventListener('resize', resizeIndustryChart)
  
  if (chart.value) {
    chart.value.dispose()
  }
  if (industryChart.value) {
    industryChart.value.dispose()
  }
})

// 监听图表类型变化
watch(chartType, () => {
  nextTick(() => {
    updateChart()
  })
})

// 监听数据变化
watch(marketFlowData, () => {
  nextTick(() => {
    updateChart()
  })
}, { deep: true })

// 数据加载
const loadData = async () => {
  loading.value = true
  
  try {
    const dateStr = selectedDate.value
    // 将日期格式从 YYYY-MM-DD 转换为 YYYYMMDD
    const apiDateFormat = dateStr.replace(/-/g, '')
    
    // 并行加载所有数据
    const [analysisRes, inflowRes, outflowRes, industryRes, marketRes] = await Promise.all([
      marketAPI.getMoneyFlowAnalysis(apiDateFormat),
      marketAPI.getMoneyFlowInflowRanking(apiDateFormat, 20),
      marketAPI.getMoneyFlowOutflowRanking(apiDateFormat, 20),
      marketAPI.getMoneyFlowIndustry(apiDateFormat, 1000), // 增加数量以获取更多行业数据，包括净流出
      marketAPI.getMoneyFlowMarket(apiDateFormat, apiDateFormat, 10)
    ])
    
    // 处理分析数据
    if (analysisRes.success) {
      marketSummary.value = analysisRes.data.market_analysis
      // 使用历史数据更新图表
      if (analysisRes.data.historical_data && analysisRes.data.historical_data.length > 0) {
        marketFlowData.value = analysisRes.data.historical_data
      }
    }
    
    // 处理流入排行数据
    if (inflowRes.success) {
      inflowRankingData.value = inflowRes.data.rankings
    }
    
    // 处理流出排行数据
    if (outflowRes.success) {
      outflowRankingData.value = outflowRes.data.rankings
    }
    
    // 处理行业数据
    if (industryRes.success) {
      const allIndustryData = industryRes.data.industry_flows
      
      // 分别处理净流入和净流出行业，只保留前50个
      inflowIndustryData.value = allIndustryData
        .filter((item: any) => item.net_amount > 0)
        .sort((a: any, b: any) => b.net_amount - a.net_amount)
        .slice(0, 50) // 只保留前50个净流入行业
        .map((item: any) => ({
          ...item,
          net_outflow: 0
        }))
      
      outflowIndustryData.value = allIndustryData
        .filter((item: any) => item.net_amount < 0)
        .sort((a: any, b: any) => a.net_amount - b.net_amount) // 按净流出量从大到小排序
        .slice(0, 50) // 只保留前50个净流出行业
        .map((item: any) => ({
          ...item,
          net_outflow: Math.abs(item.net_amount)
        }))
      
      // 保留原有的industryData以兼容其他功能
      industryData.value = allIndustryData.map((item: any) => ({
        ...item,
        net_outflow: item.net_amount < 0 ? Math.abs(item.net_amount) : 0
      }))
    }
    
    // 注释掉市场数据覆盖历史数据的问题
    // if (marketRes.success) {
    //   marketFlowData.value = marketRes.data.market_flows
    // }
    
    // 更新图表
    nextTick(() => {
      updateChart()
      updateIndustryChart()
    })
    
  } catch (error) {
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  // console.log('组件已挂载，开始初始化')
  
  // 先初始化图表容器
  nextTick(() => {
    // console.log('开始初始化图表容器')
    initChart()
    initIndustryChart()
    
    // 设置图表自适应
    const resizeObserver = setupChartResize()
    
    // 然后加载数据
    loadData()
    
    // 存储resizeObserver以便在组件卸载时清理
    if (resizeObserver) {
      // 将清理逻辑移到组件外部
      resizeObserverRef.value = resizeObserver
    }
  })
})

// 组件卸载时清理资源
onUnmounted(() => {
  // 清理ResizeObserver
  if (resizeObserverRef.value) {
    if (chartRef.value) resizeObserverRef.value.unobserve(chartRef.value)
    if (industryChartRef.value) resizeObserverRef.value.unobserve(industryChartRef.value)
    resizeObserverRef.value.disconnect()
  }
  
  // 清理ECharts实例
  if (chart.value) {
    chart.value.dispose()
  }
  if (industryChart.value) {
    industryChart.value.dispose()
  }
})
</script>

<style scoped>
/* 资金流面板样式 - 继承全局卡片样式 */
.money-flow-panel {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  background: linear-gradient(135deg, var(--surface-bg) 0%, var(--surface-hover) 100%);
  border-bottom: 1px solid var(--border-light);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

/* 标题行布局 - 包含标题和问AI按钮 */
.header-left .section-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.section-icon {
  width: 20px;
  height: 20px;
  color: var(--primary-color);
}

/* 深色主题下的彩色图标背景 */
.dark .section-icon {
  background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
  color: #ffffff;
  border-radius: 6px;
  padding: 4px;
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
}

.section-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.date-picker {
  width: 160px;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.card-body {
  padding: 0;
  margin-bottom: var(--spacing-lg);
}

.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--surface-hover);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  flex-shrink: 0;
}

.stat-icon.positive {
  background: rgba(245, 108, 108, 0.1); /* 红色背景表示积极/上涨 */
  color: #F56C6C;
}

.stat-icon.negative {
  background: rgba(103, 194, 58, 0.1); /* 绿色背景表示消极/下跌 */
  color: #67C23A;
}

.stat-icon.info {
  background: rgba(64, 158, 255, 0.1);
  color: var(--primary-color);
}

.stat-icon.warning {
  background: rgba(230, 162, 60, 0.1);
  color: #E6A23C;
}

/* 深色主题下的统计图标增强效果 */
.dark .stat-icon.positive {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); /* 红色渐变表示上涨 */
  color: #ffffff;
  box-shadow: 0 0 15px rgba(255, 107, 107, 0.4);
}

.dark .stat-icon.negative {
  background: linear-gradient(135deg, #51cf66 0%, #40c057 100%); /* 绿色渐变表示下跌 */
  color: #ffffff;
  box-shadow: 0 0 15px rgba(81, 207, 102, 0.4);
}

.dark .stat-icon.info {
  background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
  color: #ffffff;
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.4);
}

.dark .stat-icon.warning {
  background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
  color: #ffffff;
  box-shadow: 0 0 15px rgba(243, 156, 18, 0.4);
}

.stat-icon .icon {
  width: 20px;
  height: 20px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.stat-value.positive {
  color: #F56C6C; /* 红色表示积极/上涨 */
}

.stat-value.negative {
  color: #67C23A; /* 绿色表示消极/下跌 */
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.main-content {
  padding: 0 var(--spacing-lg) var(--spacing-lg);
}

.top-panel {
  margin-bottom: var(--spacing-xl);
}

.top-panel-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--spacing-xl);
  height: 500px;
}

.panel-section {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(10px);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-secondary);
  background: rgba(255, 255, 255, 0.02);
  flex-shrink: 0;
}

.section-header .section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.section-title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.section-title-actions {
  display: flex;
  align-items: center;
}

.section-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

/* 现代单选按钮组样式 */
.chart-type-radio-group {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 2px;
  border: 1px solid var(--border-secondary);
}

.chart-type-radio-group .el-radio-button {
  margin: 0;
}

.chart-type-radio-group .el-radio-button__inner {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 6px;
  transition: all 0.3s ease;
  font-weight: 500;
}

.chart-type-radio-group .el-radio-button__inner:hover {
  background: rgba(64, 158, 255, 0.1);
  color: var(--primary-color);
}

.chart-type-radio-group .el-radio-button.is-active .el-radio-button__inner {
  background: var(--primary-color);
  color: #ffffff;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.3);
}

.chart-type-radio-group .el-radio-button:first-child .el-radio-button__inner {
  border-radius: 6px;
}

.chart-type-radio-group .el-radio-button:last-child .el-radio-button__inner {
  border-radius: 6px;
}

/* 排行榜单选按钮组样式 */
.ranking-radio-group {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 2px;
  border: 1px solid var(--border-secondary);
}

.ranking-radio-group .el-radio-button {
  margin: 0;
}

.ranking-radio-group .el-radio-button__inner {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 6px;
  transition: all 0.3s ease;
  font-weight: 500;
}

.ranking-radio-group .el-radio-button__inner:hover {
  background: rgba(64, 158, 255, 0.1);
  color: var(--primary-color);
}

.ranking-radio-group .el-radio-button.is-active .el-radio-button__inner {
  background: var(--primary-color);
  color: #ffffff;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.3);
}

.ranking-radio-group .el-radio-button:first-child .el-radio-button__inner {
  border-radius: 6px;
}

.ranking-radio-group .el-radio-button:last-child .el-radio-button__inner {
  border-radius: 6px;
}

.chart-section {
  min-height: 500px;
}

.chart-container {
  flex: 1;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
}

.money-flow-chart {
  flex: 1;
  min-height: 400px;
}

.ranking-section {
  display: flex;
  flex-direction: column;
}

.ranking-table-container {
  flex: 1;
  overflow: auto;
}

.ranking-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  background: var(--bg-secondary);
}

.ranking-table thead {
  background-color: var(--bg-tertiary);
  position: sticky;
  top: 0;
  z-index: 10;
}

.ranking-table th {
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  font-size: 12px;
  color: var(--text-primary);
  border: none;
  white-space: nowrap;
}

.ranking-table td {
  padding: 8px 12px;
  text-align: left;
  font-size: 12px;
  color: var(--text-primary);
  border: none;
  white-space: nowrap;
}

.ranking-table tbody tr:nth-child(even) {
  background-color: var(--bg-tertiary);
}

.ranking-table tbody tr:hover {
  background-color: var(--bg-elevated);
  cursor: pointer;
}

.ranking-table tr.selected {
  background-color: rgba(64, 158, 255, 0.1);
  border-left: 3px solid var(--primary-color);
}

.rank-col {
  width: 60px;
  text-align: center;
}

.stock-col {
  width: 120px;
}

.industry-col {
  width: 100px;
}

.change-col {
  width: 80px;
  text-align: right;
}

.flow-col {
  width: 100px;
  text-align: right;
}

.stock-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stock-name {
  font-weight: 500;
  color: var(--text-primary);
}

.stock-code {
  font-size: 11px;
  color: var(--text-tertiary);
}

.value {
  font-weight: 500;
}

.value.positive {
  color: #F56C6C; /* 红色表示上涨/净流入 */
}

.value.negative {
  color: #67C23A; /* 绿色表示下跌/净流出 */
}

.value.neutral {
  color: var(--text-secondary);
}

.bottom-panel {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
  backdrop-filter: blur(10px);
}

.industry-chart-container {
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-primary);
}

.industry-chart {
  width: 100%;
  height: 400px;
}

.industry-tabs {
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border-primary);
  background: var(--bg-tertiary);
}

.industry-table-container {
  max-height: 400px;
  overflow: auto;
}

.industry-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  background: var(--bg-secondary);
}

.industry-table thead {
  background-color: var(--bg-tertiary);
  position: sticky;
  top: 0;
  z-index: 10;
}

.industry-table th {
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  font-size: 12px;
  color: var(--text-primary);
  border: none;
  white-space: nowrap;
}

.industry-table td {
  padding: 8px 12px;
  text-align: left;
  font-size: 12px;
  color: var(--text-primary);
  border: none;
  white-space: nowrap;
}

.industry-table tbody tr:nth-child(even) {
  background-color: var(--bg-tertiary);
}

.industry-table tbody tr:hover {
  background-color: var(--bg-elevated);
  cursor: pointer;
}

.industry-table tr.selected {
  background-color: rgba(64, 158, 255, 0.1);
  border-left: 3px solid var(--primary-color);
}

.industry-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.industry-name {
  font-weight: 500;
  color: var(--text-primary);
}

.industry-code {
  font-size: 11px;
  color: var(--text-tertiary);
}

.close-col {
  width: 80px;
  text-align: right;
}

.net-amount-col {
  width: 120px;
  text-align: right;
}

.net-outflow-col {
  width: 120px;
  text-align: right;
}

.trend-col {
  width: 60px;
  text-align: center;
}

.trend-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  margin: 0 auto;
}

.trend-indicator.positive {
  background: rgba(245, 108, 108, 0.1); /* 红色背景表示上涨 */
  color: #F56C6C;
}

.trend-indicator.negative {
  background: rgba(103, 194, 58, 0.1); /* 绿色背景表示下跌 */
  color: #67C23A;
}

.trend-indicator.neutral {
  background: rgba(144, 147, 153, 0.1);
  color: var(--text-secondary);
}

.trend-icon {
  width: 12px;
  height: 12px;
}

.search-input {
  width: 200px;
}

.search-icon {
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  color: var(--text-secondary);
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
  margin-bottom: var(--spacing-xs);
}

.empty-hint {
  font-size: 14px;
  color: var(--text-tertiary);
}

.pagination-container {
  padding: var(--spacing-sm);
  border-top: 1px solid var(--border-primary);
  background: var(--bg-tertiary);
  display: flex;
  justify-content: center;
}

/* CSS变量定义 */
:root {
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --surface-bg: #ffffff;
  --surface-hover: #f8f9fa;
  --border-light: #e1e4e8;
  --text-primary: #24292f;
  --text-secondary: #656d76;
  --text-tertiary: #8b949e;
  --primary-color: #409eff;
  --success-color: #67c23a;
  --error-color: #f56c6c;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>