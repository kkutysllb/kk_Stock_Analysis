<template>
  <div class="dragon-tiger-panel card glass-effect">
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="header-left">
        <h3 class="section-title">
          <FireIcon class="section-icon" />
          龙虎榜数据
          <AskAIComponent :data-context="aiDataContext" />
        </h3>
        <p class="section-subtitle">实时龙虎榜统计与机构交易分析</p>
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
            <TrendingUpIcon class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value positive">{{ summaryData.statistics.total_buy_amount.toLocaleString() }}</div>
            <div class="stat-label">总买入金额</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon negative">
            <TrendingUpIcon class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value negative">{{ summaryData.statistics.total_sell_amount.toLocaleString() }}</div>
            <div class="stat-label">总卖出金额</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon" :class="summaryData.statistics.total_net_amount >= 0 ? 'positive' : 'negative'">
            <CurrencyDollarIcon class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value" :class="summaryData.statistics.total_net_amount >= 0 ? 'positive' : 'negative'">
              {{ summaryData.statistics.total_net_amount.toLocaleString() }}
            </div>
            <div class="stat-label">净买入金额</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon info">
            <ScaleIcon class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ summaryData.total_count }}</div>
            <div class="stat-label">上榜股票数</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 上部：龙虎榜数据和游资统计分析并排 -->
      <div class="top-panel">
        <div class="top-panel-grid">
          <!-- 左侧：龙虎榜排行 -->
          <div class="panel-section">
            <div class="section-header">
              <h4 class="section-title">
                <ListBulletIcon class="section-icon" />
                龙虎榜排行
              </h4>
              <div class="section-controls">
                <el-select v-model="sortBy" @change="onSortChange" size="small" class="sort-select">
                  <el-option label="按净买入排序" value="net_amount" />
                  <el-option label="按涨跌幅排序" value="pct_change" />
                  <el-option label="按成交额排序" value="amount" />
                </el-select>
              </div>
            </div>
            
            <div class="list-header">
              <h4 class="list-title">龙虎榜详情</h4>
              <div class="list-actions">
                <el-input
                  v-model="searchKeyword"
                  placeholder="搜索股票代码或名称"
                  size="small"
                  class="search-input"
                  clearable
                  @input="onSearchChange"
                >
                  <template #prefix>
                    <MagnifyingGlassIcon class="search-icon" />
                  </template>
                </el-input>
              </div>
            </div>
            
            <div v-loading="loading" class="dragon-tiger-table-container">
              <table class="dragon-tiger-table">
                <thead>
                  <tr>
                    <th class="rank-col">排名</th>
                    <th class="stock-col">股票</th>
                    <th class="change-col">涨跌幅</th>
                    <th class="amount-col">成交额</th>
                    <th class="net-col">净买入</th>
                    <th class="reason-col">上榜原因</th>
                  </tr>
                </thead>
                <tbody>
                  <tr 
                    v-for="(item, index) in sortedDragonTigerList" 
                    :key="item.ts_code"
                    @click="selectStock(item)"
                    :class="{ 'selected': selectedStock?.ts_code === item.ts_code }"
                  >
                    <td class="rank-col">{{ (currentPage - 1) * pageSize + index + 1 }}</td>
                    <td class="stock-col">
                      <div class="stock-info">
                        <div class="stock-name">{{ item.name }}</div>
                        <div class="stock-code">{{ item.ts_code }}</div>
                      </div>
                    </td>
                    <td class="change-col">
                      <span class="value" :class="getChangeClass(item.pct_change)">
                        {{ item.pct_change > 0 ? '+' : '' }}{{ item.pct_change.toFixed(2) }}%
                      </span>
                    </td>
                    <td class="amount-col">
                      <span class="value">{{ formatAmount(item.amount) }}</span>
                    </td>
                    <td class="net-col">
                      <span class="value" :class="getChangeClass(item.net_amount)">
                        {{ formatAmount(item.net_amount) }}
                      </span>
                    </td>
                    <td class="reason-col">
                      <el-tag size="small" type="info">{{ item.reason }}</el-tag>
                    </td>
                  </tr>
                </tbody>
              </table>
              
              <div v-if="!loading && sortedDragonTigerList.length === 0" class="empty-state">
                <ExclamationTriangleIcon class="empty-icon" />
                <p class="empty-text">暂无龙虎榜数据</p>
                <p class="empty-hint">请尝试选择其他日期或稍后刷新</p>
              </div>
              
              <!-- 分页组件 -->
              <div class="pagination-container table-pagination" v-if="totalCount > pageSize">
                <el-pagination
                  v-model:current-page="currentPage"
                  :page-size="pageSize"
                  :total="totalCount"
                  layout="prev, pager, next, jumper, total"
                  size="small"
                  @current-change="handlePageChange"
                />
              </div>
            </div>
          </div>
          
          <!-- 右侧：游资统计分析 -->
          <div class="panel-section">
            <div class="section-header">
              <h4 class="section-title">
                <ChartBarIcon class="section-icon" />
                龙虎榜游资统计分析
              </h4>
            </div>
            
            <!-- 游资统计分析内容区域 -->
            <div class="trader-analysis-container" v-loading="loading">
              <div v-if="hotMoneyData.hm_summary.length > 0" class="hot-money-content">
                <!-- 游资统计概览 -->
                <div class="hot-money-stats">
                  <div class="stat-card">
                    <div class="stat-icon info">
                      <UserGroupIcon class="icon" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ hotMoneyData.overall_stats.total_hm_count }}</div>
                      <div class="stat-label">活跃游资数量</div>
                    </div>
                  </div>
                  
                  <div class="stat-card">
                    <div class="stat-icon positive">
                      <TrendingUpIcon class="icon" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value positive">{{ formatAmount(hotMoneyData.overall_stats.total_buy_amount) }}</div>
                      <div class="stat-label">总买入金额</div>
                    </div>
                  </div>
                  
                  <div class="stat-card">
                    <div class="stat-icon negative">
                      <ArrowTrendingDownIcon class="icon" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value negative">{{ formatAmount(hotMoneyData.overall_stats.total_sell_amount) }}</div>
                      <div class="stat-label">总卖出金额</div>
                    </div>
                  </div>
                </div>
                
                <!-- 游资列表 - 表格形式 -->
                <div class="hot-money-table-container">
                  <div class="table-header">
                    <h5 class="list-title">活跃游资排行</h5>
                    <span class="hot-money-count">共 {{ hotMoneyTotalCount }} 家游资</span>
                  </div>
                  
                  <table class="hot-money-table">
                    <thead>
                      <tr>
                        <th class="name-col">游资名称</th>
                        <th class="trades-col">交易数</th>
                        <th class="stocks-col">股票数</th>
                        <th class="buy-col">买入金额</th>
                        <th class="sell-col">卖出金额</th>
                        <th class="net-col">净买入</th>
                        <th class="recent-col">近期交易</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(hm, index) in paginatedHotMoney" :key="hm.hm_name">
                        <td class="name-col">
                          <div class="hm-name-cell">
                            <div class="hm-name">{{ hm.hm_name }}</div>
                            <el-tooltip :content="hm.desc" placement="top" effect="dark">
                              <InformationCircleIcon class="info-icon" />
                            </el-tooltip>
                          </div>
                        </td>
                        <td class="trades-col">{{ hm.total_trades }}</td>
                        <td class="stocks-col">{{ hm.unique_stocks_count }}</td>
                        <td class="buy-col">
                          <span class="value positive">{{ formatAmount(hm.total_buy_amount) }}</span>
                        </td>
                        <td class="sell-col">
                          <span class="value negative">{{ formatAmount(hm.total_sell_amount) }}</span>
                        </td>
                        <td class="net-col">
                          <span class="value" :class="getChangeClass(hm.total_net_buy)">
                            {{ formatAmount(hm.total_net_buy) }}
                          </span>
                        </td>
                        <td class="recent-col">
                          <div class="recent-trades-list">
                            <div v-for="(trade, i) in hm.recent_trades.slice(0, 3)" :key="`${hm.hm_name}-${i}`" class="recent-trade-item">
                              <span class="trade-code">{{ trade.ts_code }}</span>
                              <span class="trade-amount" :class="getChangeClass(trade.net_buy)">
                                {{ formatAmount(trade.net_buy) }}
                              </span>
                            </div>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  
                  <!-- 游资分页组件 -->
                  <div class="pagination-container table-pagination" v-if="hotMoneyTotalCount > hotMoneyPageSize">
                    <el-pagination
                      v-model:current-page="hotMoneyCurrentPage"
                      :page-size="hotMoneyPageSize"
                      :total="hotMoneyTotalCount"
                      layout="prev, pager, next, total"
                      size="small"
                      @current-change="handleHotMoneyPageChange"
                    />
                  </div>
                </div>
              </div>
              
              <div v-else class="empty-state">
                <InformationCircleIcon class="empty-icon" />
                <p class="empty-text">暂无游资统计数据</p>
                <p class="empty-hint">请尝试选择其他日期或稍后刷新</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 下方：机构交易分析 -->
      <div class="bottom-panel">
        <div class="panel-section">
          <div class="section-header">
            <h4 class="section-title">
              <BuildingOfficeIcon class="section-icon" />
              龙虎榜机构交易分析
            </h4>
          </div>
          
          <!-- 机构交易图表区域 -->
          <div class="charts-section">
            <!-- 上部图表行 -->
            <div class="charts-row">
              <!-- 机构交易饼图 -->
              <div class="chart-card">
                <h6 class="chart-title">机构交易分布</h6>
                <div ref="institutionChartRef" class="chart-container" v-loading="loading"></div>
              </div>
              
              <!-- 交易金额TOP10 -->
              <div class="chart-card">
                <h6 class="chart-title">交易金额TOP10</h6>
                <div ref="amountTop10ChartRef" class="chart-container" v-loading="loading"></div>
              </div>
            </div>
            
            <!-- 下部图表行 -->
            <div class="charts-row">
              <!-- 净买入TOP10 -->
              <div class="chart-card">
                <h6 class="chart-title">净买入TOP10</h6>
                <div ref="buyTop10ChartRef" class="chart-container" v-loading="loading"></div>
              </div>
              
              <!-- 净卖出TOP10 -->
              <div class="chart-card">
                <h6 class="chart-title">净卖出TOP10</h6>
                <div ref="sellTop10ChartRef" class="chart-container" v-loading="loading"></div>
              </div>
            </div>
          </div>
          
          <!-- 活跃机构列表 -->
          <div class="institution-list">
            <div class="institution-header">
              <h5 class="list-title">活跃机构</h5>
              <span class="institution-count">共 {{ institutionTotalCount }} 家机构</span>
            </div>
            
            <div class="institution-table-container">
              <table class="institution-table">
                <thead>
                  <tr>
                    <th class="rank-col">排名</th>
                    <th class="name-col">机构名称</th>
                    <th class="buy-col">买入金额</th>
                    <th class="sell-col">卖出金额</th>
                    <th class="net-col">净买入</th>
                  </tr>
                </thead>
                <tbody>
                  <tr 
                    v-for="(institution, index) in paginatedInstitutions" 
                    :key="institution.name"
                  >
                    <td class="rank-col">{{ (institutionCurrentPage - 1) * institutionPageSize + index + 1 }}</td>
                    <td class="name-col">{{ institution.name }}</td>
                    <td class="buy-col">
                      <span class="value positive">{{ formatAmount(institution.buy) }}</span>
                    </td>
                    <td class="sell-col">
                      <span class="value negative">{{ formatAmount(institution.sell) }}</span>
                    </td>
                    <td class="net-col">
                      <span class="value" :class="getChangeClass(institution.net)">
                        {{ formatAmount(institution.net) }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
              
              <div v-if="paginatedInstitutions.length === 0" class="empty-state">
                <ExclamationTriangleIcon class="empty-icon" />
                <p class="empty-text">暂无机构数据</p>
              </div>
              
              <!-- 机构交易分页组件 -->
              <div class="pagination-container table-pagination" v-if="institutionTotalCount > institutionPageSize">
                <el-pagination
                  v-model:current-page="institutionCurrentPage"
                  :page-size="institutionPageSize"
                  :total="institutionTotalCount"
                  layout="prev, pager, next, total"
                  size="small"
                  @current-change="handleInstitutionPageChange"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { marketAPI, type DragonTigerSummary, type DragonTigerItem } from '../api/market'
import * as echarts from 'echarts'
import AskAIComponent from './AskAIComponent.vue'
import {
  FireIcon,
  ArrowPathIcon,
  ArrowTrendingUpIcon as TrendingUpIcon,
  CurrencyDollarIcon,
  ScaleIcon,
  ListBulletIcon,
  BuildingOffice2Icon as BuildingOfficeIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassIcon,
  ChartBarIcon,
  InformationCircleIcon,
  UserGroupIcon,
  ArrowTrendingDownIcon
} from '@heroicons/vue/24/outline'

// 响应式数据
const loading = ref(false)
const selectedDate = ref('')
const sortBy = ref('net_amount')
const searchKeyword = ref('')
const selectedStock = ref<DragonTigerItem | null>(null)

// 龙虎榜分页相关数据
const currentPage = ref(1)
const pageSize = ref(10) // 每页显示20条数据，确保显示完整的龙虎榜排名

// 机构交易分页相关数据
const institutionCurrentPage = ref(1)
const institutionPageSize = ref(10) // 每页显示8条数据

// 龙虎榜数据
const summaryData = ref<DragonTigerSummary>({
  trade_date: '',
  total_count: 0,
  statistics: {
    total_buy_amount: 0,
    total_sell_amount: 0,
    total_net_amount: 0
  },
  dragon_tiger_list: []
})

// 机构数据
const activeInstitutions = ref<Array<{
  name: string
  buy: number
  sell: number
  net: number
}>>([]
)

// 游资数据
const hotMoneyData = ref<{
  hm_summary: Array<{
    hm_name: string
    desc: string
    orgs: string[]
    total_trades: number
    total_buy_amount: number
    total_sell_amount: number
    total_net_buy: number
    trade_dates: string[]
    stocks_traded: string[]
    avg_buy_rate: number
    avg_sell_rate: number
    recent_trades: Array<{
      trade_date: string
      ts_code: string
      buy: number
      sell: number
      net_buy: number
    }>
    unique_trade_days: number
    unique_stocks_count: number
    activity_score: number
  }>
  overall_stats: {
    total_hm_count: number
    total_trades: number
    total_buy_amount: number
    total_sell_amount: number
    total_net_buy: number
    date_range: {
      start_date: string
      end_date: string | null
    }
  }
  count: number
}>({
  hm_summary: [],
  overall_stats: {
    total_hm_count: 0,
    total_trades: 0,
    total_buy_amount: 0,
    total_sell_amount: 0,
    total_net_buy: 0,
    date_range: {
      start_date: '',
      end_date: null
    }
  },
  count: 0
})

// 游资分页相关数据
const hotMoneyCurrentPage = ref(1)
const hotMoneyPageSize = ref(6) // 修改为每页显示8条数据，以便更好地适应页面高度

// 图表引用
const institutionChartRef = ref<HTMLDivElement>()
const buyTop10ChartRef = ref<HTMLDivElement>()
const sellTop10ChartRef = ref<HTMLDivElement>()
const amountTop10ChartRef = ref<HTMLDivElement>()
let institutionChart: echarts.ECharts | null = null
let buyTop10Chart: echarts.ECharts | null = null
let sellTop10Chart: echarts.ECharts | null = null
let amountTop10Chart: echarts.ECharts | null = null

// 计算属性
// 过滤和排序后的完整列表
const filteredAndSortedList = computed(() => {
  if (!summaryData.value.dragon_tiger_list || !Array.isArray(summaryData.value.dragon_tiger_list)) {
    return []
  }
  
  let list = [...summaryData.value.dragon_tiger_list]
  
  // 搜索过滤
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.trim().toLowerCase()
    list = list.filter(item => 
      item.name.toLowerCase().includes(keyword) || 
      item.ts_code.toLowerCase().includes(keyword)
    )
  }
  
  // 排序
  switch (sortBy.value) {
    case 'net_amount':
      return list.sort((a, b) => b.net_amount - a.net_amount)
    case 'pct_change':
      return list.sort((a, b) => b.pct_change - a.pct_change)
    case 'amount':
      return list.sort((a, b) => b.amount - a.amount)
    default:
      return list
  }
})

// 当前页显示的数据
const sortedDragonTigerList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredAndSortedList.value.slice(start, end)
})

// 龙虎榜总数据数量
const totalCount = computed(() => filteredAndSortedList.value.length)

// 机构交易分页计算属性
// 排序后的机构数据（按净买入金额排序）
const sortedInstitutions = computed(() => {
  return [...activeInstitutions.value].sort((a, b) => Math.abs(b.net) - Math.abs(a.net))
})

// 当前页显示的机构数据
const paginatedInstitutions = computed(() => {
  const start = (institutionCurrentPage.value - 1) * institutionPageSize.value
  const end = start + institutionPageSize.value
  return sortedInstitutions.value.slice(start, end)
})

// 机构总数据数量
const institutionTotalCount = computed(() => sortedInstitutions.value.length)

// 当前页显示的游资数据
const paginatedHotMoney = computed(() => {
  const start = (hotMoneyCurrentPage.value - 1) * hotMoneyPageSize.value
  const end = start + hotMoneyPageSize.value
  return hotMoneyData.value.hm_summary.slice(start, end)
})

// 游资总数据数量
const hotMoneyTotalCount = computed(() => hotMoneyData.value.hm_summary.length)

// AI数据上下文
const aiDataContext = computed(() => {
  const dateToUse = selectedDate.value || getDefaultDate()
  
  const summary = `龙虎榜数据分析 (${dateToUse}):

统计概览:
- 上榜股票总数: ${summaryData.value.total_count}只
- 总买入金额: ${formatAmount(summaryData.value.statistics.total_buy_amount)}
- 总卖出金额: ${formatAmount(summaryData.value.statistics.total_sell_amount)}
- 净买入金额: ${formatAmount(summaryData.value.statistics.total_net_amount)}

龙虎榜排行榜 (前10名):
${sortedDragonTigerList.value.slice(0, 10).map((item, index) => 
  `${index + 1}. ${item.name} (${item.ts_code}) - 净买入: ${formatAmount(item.net_amount)}, 涨跌幅: ${item.pct_change.toFixed(2)}%`
).join('\n')}

活跃机构交易 (前10名):
${sortedInstitutions.value.slice(0, 10).map((item, index) => 
  `${index + 1}. ${item.name} - 买入: ${formatAmount(item.buy)}, 卖出: ${formatAmount(item.sell)}, 净额: ${formatAmount(item.net)}`
).join('\n')}

游资统计概览:
- 活跃游资数量: ${hotMoneyData.value.overall_stats.total_hm_count}个
- 总交易次数: ${hotMoneyData.value.overall_stats.total_trades}次
- 总买入金额: ${formatAmount(hotMoneyData.value.overall_stats.total_buy_amount)}
- 总卖出金额: ${formatAmount(hotMoneyData.value.overall_stats.total_sell_amount)}
- 净买入金额: ${formatAmount(hotMoneyData.value.overall_stats.total_net_buy)}

活跃游资排行 (前5名):
${paginatedHotMoney.value.slice(0, 5).map((item, index) => 
  `${index + 1}. ${item.hm_name} - 交易次数: ${item.total_trades}, 净买入: ${formatAmount(item.total_net_buy)}, 活跃度: ${item.activity_score.toFixed(2)}`
).join('\n')}`

  return {
    type: '龙虎榜数据',
    name: '龙虎榜分析',
    period: dateToUse,
    data: {
      summaryData: summaryData.value,
      dragonTigerList: sortedDragonTigerList.value.slice(0, 10),
      institutions: sortedInstitutions.value.slice(0, 10),
      hotMoneyData: hotMoneyData.value
    },
    summary: summary
  }
})

// 工具函数
const getDefaultDate = () => {
  // 返回有数据的日期（2025-06-27）
  return '2025-06-27'
}

// 方法
const formatAmount = (amount: number): string => {
  if (amount >= 100000000) {
    return (amount / 100000000).toFixed(2) + '亿'
  } else if (amount >= 10000) {
    return (amount / 10000).toFixed(2) + '万'
  }
  return amount.toFixed(2)
}

const getChangeClass = (value: number): string => {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}

const getNetAmountClass = (amount: number): string => {
  if (amount > 0) return 'positive'
  if (amount < 0) return 'negative'
  return 'neutral'
}

const onDateChange = () => {
  // 日期变化时同时更新龙虎榜数据、机构交易数据和游资数据
  loadDragonTigerData()
  loadInstitutionData()
  loadHotMoneyData()
}

const onSortChange = () => {
  // 排序变化时重置到第一页
  currentPage.value = 1
}

// 龙虎榜分页处理
const handlePageChange = (page: number) => {
  currentPage.value = page
}

// 机构交易分页处理
const handleInstitutionPageChange = (page: number) => {
  institutionCurrentPage.value = page
}

// 搜索处理（重置分页）
const onSearchChange = () => {
  currentPage.value = 1
}

const selectStock = (stock: DragonTigerItem) => {
  selectedStock.value = stock
}

const refreshData = () => {
  // 重置分页
  currentPage.value = 1
  institutionCurrentPage.value = 1
  hotMoneyCurrentPage.value = 1
  
  loadDragonTigerData()
  loadInstitutionData()
  loadHotMoneyData()
}

// 加载龙虎榜数据
const loadDragonTigerData = async () => {
  try {
    loading.value = true
    
    // 如果没有选择日期，使用最近的交易日
    const dateToUse = selectedDate.value || getDefaultDate()
    
    // 转换日期格式为API期望的格式（YYYYMMDD）
    const apiDateFormat = dateToUse.replace(/-/g, '')
    
    // 调用龙虎榜数据API - 增加限制数量确保获取足够的数据
    const summaryResponse = await marketAPI.getDragonTigerList(apiDateFormat, 100) // 获取指定日期的龙虎榜数据，增加到100条
    
    if (summaryResponse.success && summaryResponse.data) {
      // 转换API返回的数据格式为前端期望的格式
      const apiData = summaryResponse.data as any
      const dragonTigerStats = apiData.dragon_tiger_stats || []
      
      // 计算统计数据
      const totalBuyAmount = dragonTigerStats.reduce((sum: number, item: any) => sum + (item.l_buy || 0), 0)
      const totalSellAmount = dragonTigerStats.reduce((sum: number, item: any) => sum + (item.l_sell || 0), 0)
      const totalNetAmount = totalBuyAmount - totalSellAmount
      
      summaryData.value = {
        trade_date: dateToUse,
        total_count: (apiData.count as number) || dragonTigerStats.length,
        statistics: {
          total_buy_amount: totalBuyAmount,
          total_sell_amount: totalSellAmount,
          total_net_amount: totalNetAmount
        },
        dragon_tiger_list: dragonTigerStats
      }
    } else {
      // 设置默认数据
      summaryData.value = {
        trade_date: dateToUse,
        total_count: 0,
        statistics: {
          total_buy_amount: 0,
          total_sell_amount: 0,
          total_net_amount: 0
        },
        dragon_tiger_list: []
      }
    }
  } catch (error) {
    // 设置默认数据
    const dateToUse = selectedDate.value || getDefaultDate()
    summaryData.value = {
      trade_date: dateToUse,
      total_count: 0,
      statistics: {
        total_buy_amount: 0,
        total_sell_amount: 0,
        total_net_amount: 0
      },
      dragon_tiger_list: []
    }
  } finally {
    loading.value = false
  }
}

// 加载机构数据
const loadInstitutionData = async () => {
  try {
    // 使用与龙虎榜数据相同的日期逻辑
    const dateToUse = selectedDate.value || getDefaultDate()
    
    // 转换日期格式为API期望的格式（YYYYMMDD）
    const apiDateFormat = dateToUse.replace(/-/g, '')
    
    const response = await marketAPI.getInstitutionTrades(apiDateFormat)
    
    if (response.success && response.data?.institution_trades) {
      // 转换API数据格式为组件需要的格式
      const institutionData = response.data.institution_trades.map((item: any) => ({
        name: item.exalter || '未知机构',
        buy: item.buy || 0,
        sell: item.sell || 0,
        net: (item.buy || 0) - (item.sell || 0)
      }))
      
      activeInstitutions.value = institutionData
    } else {
      // 如果没有数据，使用空数组
      activeInstitutions.value = []
    }
    
    // 更新所有图表
    updateInstitutionChart()
    updateBuyTop10Chart()
    updateSellTop10Chart()
    updateAmountTop10Chart()
  } catch (error) {
    // 出错时使用空数组
    activeInstitutions.value = []
  }
}

// 更新机构交易饼图
const updateInstitutionChart = () => {
  if (!institutionChart || !institutionChartRef.value) return
  
  const buyData = activeInstitutions.value.filter(item => item.net > 0)
  const sellData = activeInstitutions.value.filter(item => item.net < 0)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      textStyle: {
        color: '#666'
      }
    },
    series: [
      {
        name: '机构交易',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        avoidLabelOverlap: false,
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '18',
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          {
            value: buyData.reduce((sum, item) => sum + Math.abs(item.net), 0),
            name: '净买入',
            itemStyle: { color: '#F56C6C' }
          },
          {
            value: sellData.reduce((sum, item) => sum + Math.abs(item.net), 0),
            name: '净卖出',
            itemStyle: { color: '#67C23A' }
          }
        ]
      }
    ]
  }
  
  institutionChart.setOption(option)
}

// 更新净买入TOP10图表
const updateBuyTop10Chart = () => {
  if (!buyTop10Chart || !activeInstitutions.value?.length) return
  
  // 获取净买入排名前10的机构（从高到低排序）
  const buyData = activeInstitutions.value
    .filter((item: any) => item.net > 0)
    .sort((a: any, b: any) => b.net - a.net)
    .slice(0, 10)
    .reverse() // 反转数组，使图表从上到下显示从高到低
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        return `${params.name}<br/>净买入: ${(params.value / 10000).toFixed(2)}万元`
      }
    },
    grid: {
      left: '15%',
      right: '10%',
      top: '10%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLine: { show: true },
      axisTick: { show: true },
      axisLabel: {
        formatter: (value: number) => `${(value / 10000).toFixed(0)}万`
      },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'category',
      data: buyData.map((item: any) => item.name),
      axisLine: { show: true },
      axisTick: { show: true },
      axisLabel: {
        fontSize: 10
      },
      splitLine: { show: false }
    },
    series: [{
      type: 'bar',
      data: buyData.map((item: any) => item.net),
      itemStyle: {
        color: '#F56C6C'
      },
      barWidth: '60%',
      label: {
        show: true,
        position: 'right',
        formatter: (params: any) => `${(params.value / 10000).toFixed(1)}万`,
        fontSize: 10,
        color: '#666'
      }
    }]
  }
  
  buyTop10Chart.setOption(option)
}

// 更新净卖出TOP10图表
const updateSellTop10Chart = () => {
  if (!sellTop10Chart || !activeInstitutions.value?.length) return
  
  // 获取净卖出排名前10的机构（按绝对值从高到低排序）
  const sellData = activeInstitutions.value
    .filter((item: any) => item.net < 0)
    .sort((a: any, b: any) => a.net - b.net) // 负数排序，越小的负数绝对值越大
    .slice(0, 10)
    .reverse() // 反转数组，使图表从上到下显示从高到低
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        return `${params.name}<br/>净卖出: ${(params.value / 10000).toFixed(2)}万元`
      }
    },
    grid: {
      left: '15%',
      right: '10%',
      top: '10%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLine: { show: true },
      axisTick: { show: true },
      axisLabel: {
        formatter: (value: number) => `${(value / 10000).toFixed(0)}万`
      },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'category',
      data: sellData.map((item: any) => item.name),
      axisLine: { show: true },
      axisTick: { show: true },
      axisLabel: {
        fontSize: 10
      },
      splitLine: { show: false }
    },
    series: [{
      type: 'bar',
      data: sellData.map((item: any) => Math.abs(item.net)),
      itemStyle: {
        color: '#67C23A'
      },
      barWidth: '60%',
      label: {
        show: true,
        position: 'right',
        formatter: (params: any) => `${(params.value / 10000).toFixed(1)}万`,
        fontSize: 10,
        color: '#666'
      }
    }]
  }
  
  sellTop10Chart.setOption(option)
}

// 更新交易金额TOP10图表
const updateAmountTop10Chart = () => {
  if (!amountTop10Chart || !activeInstitutions.value?.length) return
  
  // 获取交易金额排名前10的机构（从高到低排序）
  const amountData = activeInstitutions.value
    .sort((a: any, b: any) => (b.buy + b.sell) - (a.buy + a.sell))
    .slice(0, 10)
    .reverse() // 反转数组，使图表从上到下显示从高到低
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        return `${params.name}<br/>交易金额: ${(params.value / 10000).toFixed(2)}万元`
      }
    },
    grid: {
      left: '15%',
      right: '10%',
      top: '10%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLine: { show: true },
      axisTick: { show: true },
      axisLabel: {
        formatter: (value: number) => `${(value / 10000).toFixed(0)}万`
      },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'category',
      data: amountData.map((item: any) => item.name),
      axisLine: { show: true },
      axisTick: { show: true },
      axisLabel: {
        fontSize: 10
      },
      splitLine: { show: false }
    },
    series: [{
      type: 'bar',
      data: amountData.map((item: any) => item.buy + item.sell),
      itemStyle: {
        color: '#409EFF'
      },
      barWidth: '60%',
      label: {
        show: true,
        position: 'right',
        formatter: (params: any) => `${(params.value / 10000).toFixed(1)}万`,
        fontSize: 10,
        color: '#666'
      }
    }]
  }
  
  amountTop10Chart.setOption(option)
}

// 初始化所有图表
const initAllCharts = () => {
  initInstitutionChart()
  initBuyTop10Chart()
  initSellTop10Chart()
  initAmountTop10Chart()
}

// 初始化机构交易图表
const initInstitutionChart = () => {
  if (!institutionChartRef.value) return
  
  institutionChart = echarts.init(institutionChartRef.value)
  updateInstitutionChart()
  
  // 响应式调整
  window.addEventListener('resize', () => {
    institutionChart?.resize()
  })
}

// 初始化净买入TOP10图表
const initBuyTop10Chart = () => {
  if (!buyTop10ChartRef.value) return
  
  buyTop10Chart = echarts.init(buyTop10ChartRef.value)
  updateBuyTop10Chart()
  
  window.addEventListener('resize', () => {
    buyTop10Chart?.resize()
  })
}

// 初始化净卖出TOP10图表
const initSellTop10Chart = () => {
  if (!sellTop10ChartRef.value) return
  
  sellTop10Chart = echarts.init(sellTop10ChartRef.value)
  updateSellTop10Chart()
  
  window.addEventListener('resize', () => {
    sellTop10Chart?.resize()
  })
}

// 初始化交易金额TOP10图表
const initAmountTop10Chart = () => {
  if (!amountTop10ChartRef.value) return
  
  amountTop10Chart = echarts.init(amountTop10ChartRef.value)
  updateAmountTop10Chart()
  
  window.addEventListener('resize', () => {
    amountTop10Chart?.resize()
  })
}

// 加载游资统计数据
const loadHotMoneyData = async () => {
  try {
    loading.value = true
    
    // 如果没有选择日期，使用最近的交易日
    const dateToUse = selectedDate.value || getDefaultDate()
    
    // 转换日期格式为API期望的格式（YYYYMMDD）
    const apiDateFormat = dateToUse.replace(/-/g, '')
    
    // 调用游资统计数据API
    const hmResponse = await marketAPI.getHotMoneyTrades(apiDateFormat, 20)
    
    if (hmResponse.success && hmResponse.data) {
      hotMoneyData.value = hmResponse.data
    } else {
      // 设置默认数据
      hotMoneyData.value = {
        hm_summary: [],
        overall_stats: {
          total_hm_count: 0,
          total_trades: 0,
          total_buy_amount: 0,
          total_sell_amount: 0,
          total_net_buy: 0,
          date_range: {
            start_date: apiDateFormat,
            end_date: null
          }
        },
        count: 0
      }
    }
  } catch (error) {
    hotMoneyData.value = {
      hm_summary: [],
      overall_stats: {
        total_hm_count: 0,
        total_trades: 0,
        total_buy_amount: 0,
        total_sell_amount: 0,
        total_net_buy: 0,
        date_range: {
          start_date: '',
          end_date: null
        }
      },
      count: 0
    }
  } finally {
    loading.value = false
  }
}

// 游资分页处理
const handleHotMoneyPageChange = (page: number) => {
  hotMoneyCurrentPage.value = page
}

// 组件挂载
onMounted(async () => { 
  // 设置默认日期为当前系统时间
  const today = new Date()
  selectedDate.value = today.toISOString().split('T')[0]
  
  // 加载数据
  await loadDragonTigerData()
  await loadInstitutionData()
  await loadHotMoneyData()
  
  // 初始化所有图表
  nextTick(() => {
    initAllCharts()
  })
})
</script>

<style scoped>
.dragon-tiger-panel {
  width: 100%;
  padding: 0;
}

.dragon-tiger-panel:hover {
  transform: none;
  box-shadow: var(--shadow-sm);
  border-color: var(--border-primary);
}

/* 卡片头部样式 */
/* 使用全局card-header样式，无需重复定义 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.section-title {
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
  font-weight: 500;
}

.date-picker {
  width: 160px;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
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

/* 统计概览 */
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
  background: var(--surface-bg);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon.positive {
  background: rgba(103, 194, 58, 0.1);
  color: var(--success-color);
}

.stat-icon.negative {
  background: rgba(245, 108, 108, 0.1);
  color: var(--error-color);
}

.stat-icon.warning {
  background: rgba(230, 162, 60, 0.1);
  color: var(--warning-color);
}

.stat-icon.info {
  background: rgba(64, 158, 255, 0.1);
  color: var(--primary-color);
}

/* 深色主题下的统计图标增强效果 */
.dark .stat-icon.positive {
  background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
  color: #ffffff;
  box-shadow: 0 0 15px rgba(0, 255, 136, 0.4);
}

.dark .stat-icon.negative {
  background: linear-gradient(135deg, #ff006e 0%, #cc0055 100%);
  color: #ffffff;
  box-shadow: 0 0 15px rgba(255, 0, 110, 0.4);
}

.dark .stat-icon.warning {
  background: linear-gradient(135deg, #ffa500 0%, #cc8400 100%);
  color: #ffffff;
  box-shadow: 0 0 15px rgba(255, 165, 0, 0.4);
}

.dark .stat-icon.info {
  background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
  color: #ffffff;
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.4);
}

.stat-icon.neutral {
  background: rgba(144, 147, 153, 0.1);
  color: var(--text-secondary);
}

.stat-icon-size {
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
  margin-bottom: 2px;
}

.stat-value.positive {
  color: var(--success-color);
}

.stat-value.negative {
  color: var(--error-color);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

/* 主要内容区域 */
.main-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.top-panel {
  min-height: 500px;
  height: auto;
  flex-shrink: 0;
  overflow: visible;
}

.bottom-panel {
  height: auto;
  min-height: 650px;
  flex-shrink: 0;
}

.panel-section {
  background: var(--surface-bg);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
  overflow: visible;
  display: flex;
  flex-direction: column;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background: var(--surface-hover);
  border-bottom: 1px solid var(--border-light);
}

/* 移除重复的.section-title定义，使用上面统一的定义 */

.list-section-icon {
  width: 16px;
  height: 16px;
}

.section-controls {
  display: flex;
  gap: var(--spacing-sm);
}

.sort-select {
  width: 140px;
}

/* 列表头部 */
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background: var(--surface-hover);
  border-bottom: 1px solid var(--border-light);
}

.list-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.list-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.search-input {
  width: 200px;
}

.search-icon {
  width: 14px;
  height: 14px;
  color: var(--text-tertiary);
}

/* 龙虎榜列表容器 */
.dragon-tiger-table-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: visible;
  min-height: 350px;
}

.dragon-tiger-table {
  width: 100%;
  border-collapse: collapse;
  border: none;
  background: var(--bg-secondary);
  font-size: 12px;
}

.dragon-tiger-table thead {
  background-color: var(--bg-tertiary);
}

.dragon-tiger-table th {
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  font-size: 12px;
  color: var(--text-primary);
  border: none;
  white-space: nowrap;
}

.dragon-tiger-table td {
  padding: 8px 12px;
  text-align: left;
  font-size: 12px;
  color: var(--text-primary);
  border: none;
  white-space: nowrap;
}

.dragon-tiger-table tbody tr:nth-child(even) {
  background-color: var(--bg-tertiary);
}

.dragon-tiger-table tbody tr:hover {
  background-color: var(--bg-elevated);
}

.rank-col {
  width: 60px;
  text-align: center;
}

.stock-col {
  width: 180px;
  text-align: left;
}

.change-col {
  width: 120px;
  text-align: right;
}

.amount-col {
  width: 120px;
  text-align: right;
}

.net-col {
  width: 120px;
  text-align: right;
}

.reason-col {
  width: 240px;
  text-align: left;
}

.stock-info {
  display: flex;
  flex-direction: column;
}

.stock-name {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 13px;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stock-code {
  font-size: 12px;
  color: var(--text-secondary);
}

.value {
  font-weight: 500;
}

.value.positive {
  color: var(--success-color);
}

.value.negative {
  color: var(--error-color);
}

.info-icon {
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
  margin-left: 4px;
  cursor: pointer;
}

.info-icon:hover {
  color: var(--primary-color);
}

.table-pagination {
  margin-top: var(--spacing-md);
  border-top: 1px solid var(--border-primary);
  padding: var(--spacing-sm) 0;
  display: flex;
  justify-content: center;
  background: var(--bg-tertiary);
  flex-shrink: 0;
  position: relative;
  z-index: 1500;
}

/* 机构交易分析 */
.charts-section {
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.charts-row {
  display: flex;
  gap: var(--spacing-md);
}

.chart-card {
  flex: 1;
  background: var(--card-bg);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
  padding: var(--spacing-sm);
}

.chart-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-sm) 0;
  text-align: center;
}

.chart-container {
  width: 100%;
  height: 250px;
}

.institution-list {
  padding: var(--spacing-md);
  margin-top: var(--spacing-lg);
  border-top: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 300px;
}

/* 机构列表头部 */
.institution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.list-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.institution-count {
  font-size: 12px;
  color: var(--text-secondary);
}

/* 机构列表容器 */
.institution-table-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: visible;
  min-height: 250px;
}

.institution-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  overflow: auto;
  flex: 1;
}

.institution-table thead {
  background-color: var(--surface-hover);
}

.institution-table th {
  padding: 10px;
  text-align: left;
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-light);
}

.institution-table td {
  padding: 8px 10px;
  text-align: left;
  font-size: 13px;
  border-bottom: 1px solid var(--border-light);
}

.institution-table tr:nth-child(even) {
  background-color: var(--surface-hover);
}

.institution-table tr:hover {
  background-color: rgba(64, 158, 255, 0.05);
}

.rank-col {
  width: 60px;
  text-align: center;
}

.name-col {
  width: 180px;
  text-align: left;
}

.buy-col, .sell-col, .net-col {
  width: 120px;
  text-align: right;
}

.value {
  font-weight: 500;
}

.value.positive {
  color: var(--success-color);
}

.value.negative {
  color: var(--error-color);
}

.info-icon {
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
  margin-left: 4px;
  cursor: pointer;
}

.info-icon:hover {
  color: var(--primary-color);
}

.table-pagination {
  margin-top: var(--spacing-md);
  border-top: 1px solid var(--border-light);
  padding: var(--spacing-sm) 0;
  display: flex;
  justify-content: center;
  background: var(--surface-hover);
  flex-shrink: 0;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  text-align: center;
  flex: 1;
}

.empty-icon {
  width: 40px;
  height: 40px;
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-md);
}

.empty-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.empty-hint {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .charts-row {
    flex-direction: column;
  }
  
  .stats-overview {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }
  
  .bottom-panel {
    height: auto;
  }
}

@media (max-width: 768px) {
  .panel-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: stretch;
  }
  
  .header-controls {
    justify-content: flex-end;
  }
  
  .stats-overview {
    grid-template-columns: 1fr;
  }
  
  .list-item {
    flex-wrap: wrap;
    gap: var(--spacing-sm);
  }
  
  .item-reason {
    width: 100%;
    margin-top: var(--spacing-xs);
  }
}

/* 新增样式 */
.top-panel-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  min-height: 100%;
  height: auto;
}

.trader-analysis-container {
  display: flex;
  min-height: 100%;
  height: auto;
  width: 100%;
  overflow: visible;
}

.hot-money-content {
  width: 100%;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.hot-money-stats {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  flex-shrink: 0;
}

.hot-money-list {
  margin-top: var(--spacing-lg);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.hot-money-count {
  font-size: 12px;
  color: var(--text-secondary);
}

.hot-money-items {
  max-height: 300px;
  overflow-y: auto;
}

.hot-money-item {
  display: flex;
  flex-direction: column;
  padding: var(--spacing-md);
  background: var(--surface-bg);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-md);
}

.hm-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.hm-rank {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.hm-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.hm-metrics {
  display: flex;
  gap: var(--spacing-sm);
  margin-left: auto;
}

.metric-badge {
  background: var(--surface-hover);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  color: var(--text-secondary);
}

.hm-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.hm-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: var(--spacing-sm);
}

.hm-trades {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--surface-hover);
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
}

.hm-trade-metric {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hm-recent-trades {
  margin-top: var(--spacing-sm);
}

.recent-trades-header {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.recent-trades-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.recent-trade-item {
  display: flex;
  align-items: center;
  gap: 4px;
  background: var(--surface-hover);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.trade-code {
  font-size: 11px;
  color: var(--text-secondary);
}

.trade-amount {
  font-size: 11px;
  font-weight: 500;
}

.trade-amount.positive {
  color: var(--success-color);
}

.trade-amount.negative {
  color: var(--error-color);
}

.hot-money-table-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: visible;
  min-height: 350px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
  flex-shrink: 0;
}

.hot-money-table {
  width: 100%;
  border-collapse: collapse;
  border: none;
  background: var(--bg-secondary);
  font-size: 12px;
}

.hot-money-table thead {
  background-color: var(--bg-tertiary);
}

.hot-money-table th {
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  font-size: 12px;
  color: var(--text-primary);
  border: none;
  white-space: nowrap;
}

.hot-money-table td {
  padding: 8px 12px;
  text-align: left;
  font-size: 12px;
  color: var(--text-primary);
  border: none;
  white-space: nowrap;
}

.hot-money-table tbody tr:nth-child(even) {
  background-color: var(--bg-tertiary);
}

.hot-money-table tbody tr:hover {
  background-color: var(--bg-elevated);
}

.hm-name-cell {
  display: flex;
  align-items: center;
}

.rank-col {
  width: 60px;
  text-align: center;
}

.name-col {
  width: 180px;
}

.trades-col, .stocks-col {
  width: 80px;
  text-align: center;
}

.buy-col, .sell-col, .net-col {
  width: 120px;
  text-align: right;
}

.value {
  font-weight: 500;
}

.value.positive {
  color: var(--success-color);
}

.value.negative {
  color: var(--error-color);
}

.info-icon {
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
  margin-left: 4px;
  cursor: pointer;
}

.info-icon:hover {
  color: var(--primary-color);
}

.table-pagination {
  margin-top: var(--spacing-md);
  border-top: 1px solid var(--border-light);
  padding: var(--spacing-sm) 0;
  display: flex;
  justify-content: center;
  background: var(--surface-hover);
  flex-shrink: 0;
}

.recent-col {
  width: 240px;
  text-align: left;
}

.dragon-tiger-table tr.selected {
  background-color: rgba(64, 158, 255, 0.1);
  border-left: 3px solid var(--primary-color);
}

/* 分页组件 */
.pagination-container {
  padding: var(--spacing-sm);
  border-top: 1px solid var(--border-primary);
  background: var(--bg-tertiary);
  display: flex;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
  z-index: 1500;
}

/* 确保分页组件内的Element Plus组件也有正确的层级 */
.pagination-container .el-pagination {
  position: relative;
  z-index: 1501;
}

/* 修复可能的容器层级问题 */
.dragon-tiger-table-container,
.hot-money-table-container,
.institution-table-container {
  position: relative;
  z-index: 1;
}

/* 确保表格不会覆盖分页组件 */
.dragon-tiger-table,
.hot-money-table,
.institution-table {
  position: relative;
  z-index: 2;
}
</style>