<template>
  <div class="simulation-trading">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">模拟交易</h1>
        <p class="page-subtitle">KK量化模拟交易系统 - 无风险练习交易策略</p>
      </div>
      <div class="header-right">
        <el-button @click="refreshData" :loading="loading" type="primary" size="small">
          <ArrowPathIcon class="icon" />
          刷新数据
        </el-button>
      </div>
    </div>

    <!-- 账户概览卡片 -->
    <div class="account-overview">
      <el-card class="overview-card">
        <template #header>
          <div class="card-header">
            <span>账户概览</span>
            <el-tag :class="accountData.daily_return >= 0 ? 'profit-tag-cn' : 'loss-tag-cn'">
              {{ accountData.daily_return >= 0 ? '盈利' : '亏损' }}
            </el-tag>
          </div>
        </template>
        
        <div class="account-stats">
          <div class="stat-item">
            <div class="stat-label">总资产</div>
            <div class="stat-value primary">{{ formatCurrency(accountData.total_assets) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">可用资金</div>
            <div class="stat-value">{{ formatCurrency(accountData.available_cash) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">持仓市值</div>
            <div class="stat-value">{{ formatCurrency(accountData.total_market_value) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">总收益</div>
            <div class="stat-value" :class="accountData.total_return >= 0 ? 'profit-cn' : 'loss-cn'">
              {{ formatCurrency(accountData.total_return) }}
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-label">收益率</div>
            <div class="stat-value" :class="accountData.total_return_rate >= 0 ? 'profit-cn' : 'loss-cn'">
              {{ formatPercentage(accountData.total_return_rate) }}
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-label">日收益</div>
            <div class="stat-value" :class="accountData.daily_return >= 0 ? 'profit-cn' : 'loss-cn'">
              {{ formatCurrency(accountData.daily_return) }}
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 主要功能区域 -->
    <div class="main-content">
      <div class="left-panel">
        <!-- Tab切换 -->
        <el-tabs v-model="activeTab" class="trading-tabs">
          <el-tab-pane label="我的持仓" name="positions">
            <!-- 持仓列表 -->
            <el-card class="positions-card">
              <template #header>
                <div class="card-header">
                  <span>我的持仓</span>
                  <el-tag>{{ positions.length }} 只股票</el-tag>
                </div>
              </template>
          
          <el-table :data="positions" v-loading="positionsLoading" empty-text="暂无持仓" style="width: 100%">
            <el-table-column prop="stock_code" label="股票代码" min-width="100">
              <template #default="{ row }">
                <span class="stock-code">{{ row.stock_code }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="stock_name" label="股票名称" min-width="120">
              <template #default="{ row }">
                <span class="stock-name">{{ row.stock_name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="total_quantity" label="持仓数量" min-width="100" align="right">
              <template #default="{ row }">
                {{ row.total_quantity?.toLocaleString() }}
              </template>
            </el-table-column>
            <el-table-column prop="avg_cost" label="成本价" min-width="80" align="right">
              <template #default="{ row }">
                ¥{{ row.avg_cost?.toFixed(2) || '--' }}
              </template>
            </el-table-column>
            <el-table-column prop="current_price" label="现价" min-width="80" align="right">
              <template #default="{ row }">
                ¥{{ row.current_price?.toFixed(2) || '--' }}
              </template>
            </el-table-column>
            <el-table-column prop="market_value" label="市值" min-width="120" align="right">
              <template #default="{ row }">
                {{ formatCurrency(row.market_value) }}
              </template>
            </el-table-column>
            <el-table-column prop="unrealized_pnl" label="浮动盈亏" min-width="140" align="right">
              <template #default="{ row }">
                <span :class="row.unrealized_pnl >= 0 ? 'profit-cn' : 'loss-cn'">
                  {{ formatCurrency(row.unrealized_pnl) }}
                  ({{ formatPercentage(row.unrealized_pnl_rate) }})
                </span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" fixed="right">
              <template #default="{ row }">
                <el-button 
                  @click="openSellDialog(row)" 
                  class="sell-button-cn"
                  size="small"
                  :disabled="row.available_quantity <= 0"
                >
                  卖出
                </el-button>
              </template>
            </el-table-column>
          </el-table>
            </el-card>
          </el-tab-pane>
          
          <el-tab-pane label="交易记录" name="trades">
            <!-- 交易记录列表 -->
            <el-card class="trades-card">
              <template #header>
                <div class="card-header">
                  <span>交易记录</span>
                  <el-tag>{{ trades.length }} 笔交易</el-tag>
                </div>
              </template>
              
              <div class="trades-filter">
                <el-form :inline="true" class="filter-form">
                  <el-form-item label="股票代码">
                    <el-input 
                      v-model="tradeQuery.stock_code" 
                      placeholder="输入股票代码"
                      clearable
                      style="width: 120px"
                    />
                  </el-form-item>
                  <el-form-item label="开始日期">
                    <el-date-picker
                      v-model="tradeQuery.start_date"
                      type="date"
                      placeholder="开始日期"
                      style="width: 140px"
                    />
                  </el-form-item>
                  <el-form-item label="结束日期">
                    <el-date-picker
                      v-model="tradeQuery.end_date"
                      type="date"
                      placeholder="结束日期"
                      style="width: 140px"
                    />
                  </el-form-item>
                  <el-form-item>
                    <el-button @click="loadTrades" type="primary" size="small">查询</el-button>
                    <el-button @click="resetTradeQuery" size="small">重置</el-button>
                  </el-form-item>
                </el-form>
              </div>
              
              <el-table :data="trades" v-loading="tradesLoading" empty-text="暂无交易记录">
                <el-table-column prop="trade_time" label="交易时间" width="160">
                  <template #default="{ row }">
                    {{ formatDateTime(row.trade_time) }}
                  </template>
                </el-table-column>
                <el-table-column prop="stock_code" label="股票代码" width="100">
                  <template #default="{ row }">
                    <span class="stock-code">{{ row.stock_code }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="stock_name" label="股票名称" width="120">
                  <template #default="{ row }">
                    <span class="stock-name">{{ row.stock_name }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="trade_type" label="交易类型" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag :class="row.trade_type === 'BUY' ? 'buy-tag-cn' : 'sell-tag-cn'" size="small">
                      {{ row.trade_type === 'BUY' ? '买入' : '卖出' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="quantity" label="数量" width="100" align="right">
                  <template #default="{ row }">
                    {{ row.quantity.toLocaleString() }}
                  </template>
                </el-table-column>
                <el-table-column prop="price" label="价格" width="80" align="right">
                  <template #default="{ row }">
                    ¥{{ row.price.toFixed(2) }}
                  </template>
                </el-table-column>
                <el-table-column prop="amount" label="金额" width="120" align="right">
                  <template #default="{ row }">
                    {{ formatCurrency(row.amount) }}
                  </template>
                </el-table-column>
                <el-table-column prop="total_cost" label="手续费" width="100" align="right">
                  <template #default="{ row }">
                    {{ formatCurrency(row.total_cost) }}
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag :type="getStatusType(row.status)" size="small">
                      {{ getStatusText(row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
              
              <!-- 分页 -->
              <div class="pagination-wrapper">
                <el-pagination
                  v-model:current-page="tradeQuery.page"
                  v-model:page-size="tradeQuery.page_size"
                  :page-sizes="[10, 20, 50, 100]"
                  :total="tradeTotal"
                  layout="total, sizes, prev, pager, next, jumper"
                  @size-change="loadTrades"
                  @current-change="loadTrades"
                />
              </div>
            </el-card>
          </el-tab-pane>

          <el-tab-pane label="策略自动化" name="strategy">
            <!-- 策略自动化面板 -->
            <el-card class="strategy-automation-card">
              <template #header>
                <div class="card-header">
                  <span>量化策略自动交易</span>
                  <el-tag type="info">第三阶段功能</el-tag>
                </div>
              </template>

              <!-- 策略选择卡片 -->
              <div class="strategy-cards">
                <div 
                  v-for="strategy in strategies" 
                  :key="strategy.name"
                  class="strategy-card"
                  :class="{ 'active': strategy.is_active }"
                >
                  <div class="strategy-header">
                    <div class="strategy-info">
                      <h3>{{ strategy.display_name }}</h3>
                      <p class="strategy-desc">{{ strategy.description }}</p>
                    </div>
                    <el-switch
                      v-model="strategy.is_active"
                      @change="toggleStrategy(strategy)"
                      :loading="strategy.switching"
                      active-text="运行中"
                      inactive-text="已停止"
                    />
                  </div>

                  <div class="strategy-details">
                    <div class="detail-row">
                      <span class="label">调仓频率：</span>
                      <span class="value">{{ strategy.frequency }}</span>
                    </div>
                    <div class="detail-row">
                      <span class="label">风险控制：</span>
                      <span class="value">{{ strategy.risk_control }}</span>
                    </div>
                    <div class="detail-row">
                      <span class="label">适合资金：</span>
                      <span class="value">{{ strategy.suitable_funds }}</span>
                    </div>
                  </div>

                  <div class="strategy-config" v-if="!strategy.is_active">
                    <div class="config-item">
                      <label>分配资金</label>
                      <el-input-number
                        v-model="strategy.allocated_cash"
                        :min="50000"
                        :max="1000000"
                        :step="10000"
                        :precision="0"
                        controls-position="right"
                        style="width: 100%"
                      />
                      <span class="unit">元</span>
                    </div>
                  </div>

                  <div class="strategy-performance" v-if="strategy.is_active">
                    <h4>运行状态</h4>
                    <div class="performance-stats">
                      <div class="stat-item">
                        <span class="stat-label">持仓数量</span>
                        <span class="stat-value">{{ strategy.current_positions }}只</span>
                      </div>
                      <div class="stat-item">
                        <span class="stat-label">累计收益</span>
                        <span 
                          class="stat-value" 
                          :class="strategy.total_return >= 0 ? 'profit-cn' : 'loss-cn'"
                        >
                          {{ formatPercentage(strategy.total_return_rate) }}
                        </span>
                      </div>
                      <div class="stat-item">
                        <span class="stat-label">最后执行</span>
                        <span class="stat-value">{{ formatTime(strategy.last_execution) }}</span>
                      </div>
                      <div class="stat-item">
                        <span class="stat-label">下次执行</span>
                        <span class="stat-value">{{ formatTime(strategy.next_run_time) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 策略持仓概览 -->
              <div class="strategy-positions-section" v-if="strategyPositions.length > 0">
                <h3>策略持仓概览</h3>
                <el-table :data="strategyPositions" stripe style="width: 100%">
                  <el-table-column prop="strategy_display_name" label="策略" width="120" />
                  <el-table-column prop="stock_code" label="股票代码" width="100" />
                  <el-table-column prop="stock_name" label="股票名称" width="120" />
                  <el-table-column prop="total_quantity" label="持仓数量" width="100" align="right">
                    <template #default="{ row }">
                      {{ row.total_quantity?.toLocaleString() }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="current_price" label="现价" width="80" align="right">
                    <template #default="{ row }">
                      ¥{{ row.current_price?.toFixed(2) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="market_value" label="市值" width="100" align="right">
                    <template #default="{ row }">
                      {{ formatCurrency(row.market_value) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="unrealized_pnl_rate" label="浮动盈亏" width="100" align="right">
                    <template #default="{ row }">
                      <span :class="row.unrealized_pnl_rate >= 0 ? 'profit-cn' : 'loss-cn'">
                        {{ formatPercentage(row.unrealized_pnl_rate) }}
                      </span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <!-- 策略交易记录 -->
              <div class="strategy-trades-section" v-if="strategyTrades.length > 0">
                <h3>策略交易记录</h3>
                <el-table :data="strategyTrades" stripe style="width: 100%">
                  <el-table-column prop="trade_time" label="交易时间" width="150">
                    <template #default="{ row }">
                      {{ formatDateTime(row.trade_time) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="strategy_name" label="策略" width="120">
                    <template #default="{ row }">
                      {{ getStrategyDisplayName(row.strategy_name) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="stock_code" label="股票" width="100" />
                  <el-table-column prop="trade_type" label="类型" width="80">
                    <template #default="{ row }">
                      <el-tag :type="row.trade_type === 'BUY' ? 'success' : 'danger'" size="small">
                        {{ row.trade_type === 'BUY' ? '买入' : '卖出' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="quantity" label="数量" width="80" align="right" />
                  <el-table-column prop="price" label="价格" width="80" align="right">
                    <template #default="{ row }">
                      ¥{{ row.price?.toFixed(2) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="amount" label="金额" width="100" align="right">
                    <template #default="{ row }">
                      {{ formatCurrency(row.amount) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="status" label="状态" width="80">
                    <template #default="{ row }">
                      <el-tag :type="row.status === 'FILLED' ? 'success' : 'info'" size="small">
                        {{ row.status === 'FILLED' ? '已成交' : '处理中' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </el-card>
          </el-tab-pane>
        </el-tabs>
      </div>

      <div class="right-panel">
        <!-- 交易面板 -->
        <el-card class="trading-card">
          <template #header>
            <div class="card-header">
              <span>股票交易</span>
            </div>
          </template>
          
          <div class="trading-form">
            <!-- 股票搜索 -->
            <div class="form-item">
              <label>选择股票</label>
              <div class="stock-selection-container">
                <StockSearchComponent 
                  :compact="true"
                  @stock-selected="onStockSelected"
                  class="stock-search"
                />
                <el-button 
                  @click="showStockPoolDialog"
                  type="primary"
                  size="small"
                  class="pool-select-btn"
                >
                  从股票池选择
                </el-button>
              </div>
            </div>

            <!-- 选中的股票信息 -->
            <div v-if="selectedStock" class="selected-stock">
              <div class="stock-info">
                <span class="stock-code">{{ selectedStock.ts_code }}</span>
                <span class="stock-name">{{ selectedStock.name }}</span>
              </div>
              <div class="stock-price">
                <span class="current-price">¥{{ currentPrice?.toFixed(2) || '--' }}</span>
              </div>
            </div>

            <!-- 交易类型 -->
            <div class="form-item">
              <label>交易类型</label>
              <el-radio-group v-model="tradeType" @change="onTradeTypeChange">
                <el-radio-button value="buy">买入</el-radio-button>
                <el-radio-button value="sell" :disabled="!canSell">卖出</el-radio-button>
              </el-radio-group>
            </div>

            <!-- 订单类型 -->
            <div class="form-item">
              <label>订单类型</label>
              <el-radio-group v-model="orderType">
                <el-radio-button value="MARKET">市价单</el-radio-button>
                <el-radio-button value="LIMIT">限价单</el-radio-button>
              </el-radio-group>
            </div>

            <!-- 价格输入 -->
            <div v-if="orderType === 'LIMIT'" class="form-item">
              <label>委托价格</label>
              <el-input-number
                v-model="orderPrice"
                :precision="2"
                :step="0.01"
                :min="0"
                placeholder="输入委托价格"
                style="width: 100%"
              />
            </div>

            <!-- 数量输入 -->
            <div class="form-item">
              <label>交易数量</label>
              <el-input-number
                v-model="orderQuantity"
                :precision="0"
                :step="100"
                :min="100"
                placeholder="输入交易数量（股）"
                style="width: 100%"
              />
              <div class="quantity-tips">
                <span v-if="selectedStock">
                  最小交易单位：{{ getTradingUnit() }} 股
                </span>
                <span v-if="tradeType === 'sell' && selectedPosition">
                  可卖：{{ selectedPosition.available_quantity }} 股
                </span>
              </div>
            </div>

            <!-- 费用计算 -->
            <div v-if="tradingCost" class="trading-cost">
              <h4>费用预估</h4>
              <div class="cost-item">
                <span>手续费：</span>
                <span>¥{{ tradingCost.commission }}</span>
              </div>
              <div class="cost-item">
                <span>印花税：</span>
                <span>¥{{ tradingCost.stamp_tax }}</span>
              </div>
              <div class="cost-item">
                <span>过户费：</span>
                <span>¥{{ tradingCost.transfer_fee }}</span>
              </div>
              <div class="cost-item">
                <span>滑点费：</span>
                <span>¥{{ tradingCost.slippage }}</span>
              </div>
              <div class="cost-item total">
                <span>总费用：</span>
                <span>¥{{ tradingCost.total_cost }}</span>
              </div>
            </div>

            <!-- 交易按钮 -->
            <div class="form-actions">
              <el-button 
                @click="submitOrder" 
                :class="tradeType === 'buy' ? 'buy-button-cn' : 'sell-button-cn'"
                :loading="submitting"
                :disabled="!canSubmitOrder"
                size="large"
                style="width: 100%"
              >
                {{ tradeType === 'buy' ? '买入' : '卖出' }}
              </el-button>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 股票池选择对话框 -->
    <StockPoolStockSelect
      v-model="stockPoolDialogVisible"
      @stock-selected="onStockFromPoolSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowPathIcon } from '@heroicons/vue/24/outline'
import { simulationApi } from '@/api/simulation'
import { eventBus } from '@/utils/eventBus'
import StockSearchComponent from '@/components/analysis/StockSearchComponent.vue'
import StockPoolStockSelect from '@/components/StockPool/StockPoolStockSelect.vue'

// 响应式数据
const loading = ref(false)
const positionsLoading = ref(false)
const submitting = ref(false)
const tradesLoading = ref(false)
const activeTab = ref('positions')

// 股票池相关
const stockPoolDialogVisible = ref(false)

// 账户数据
const accountData = reactive({
  total_assets: 0,
  available_cash: 0,
  total_market_value: 0,
  total_return: 0,
  total_return_rate: 0,
  daily_return: 0,
  daily_return_rate: 0
})

// 持仓数据
const positions = ref<any[]>([])

// 交易记录数据
const trades = ref<any[]>([])
const tradeTotal = ref(0)
const tradeQuery = reactive({
  page: 1,
  page_size: 20,
  stock_code: '',
  start_date: null as Date | null,
  end_date: null as Date | null
})

// 交易表单数据
const selectedStock = ref<any>(null)
const currentPrice = ref<number>(0)
const tradeType = ref<'buy' | 'sell'>('buy')
const orderType = ref<'MARKET' | 'LIMIT'>('MARKET')
const orderPrice = ref<number>(0)
const orderQuantity = ref<number>(100)
const tradingCost = ref<any>(null)

// 策略自动化数据 - 改为动态获取
const strategies = ref<any[]>([])

const strategyPositions = ref<any[]>([])
const strategyTrades = ref<any[]>([])
const strategyLoading = ref(false)

// 计算属性
const selectedPosition = computed(() => {
  if (!selectedStock.value) return null
  return positions.value.find(p => p.stock_code === selectedStock.value.code || p.stock_code === selectedStock.value.ts_code)
})

const canSell = computed(() => {
  return selectedPosition.value && selectedPosition.value.available_quantity > 0
})

const canSubmitOrder = computed(() => {
  if (!selectedStock.value || !orderQuantity.value) return false
  if (orderType.value === 'LIMIT' && !orderPrice.value) return false
  if (tradeType.value === 'sell' && (!selectedPosition.value || orderQuantity.value > selectedPosition.value.available_quantity)) {
    return false
  }
  return true
})

// 方法
const formatCurrency = (value: number): string => {
  if (value === undefined || value === null) return '¥0.00'
  return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const formatPercentage = (value: number): string => {
  if (value === undefined || value === null) return '0.00%'
  return `${(value * 100).toFixed(2)}%`
}

const formatDateTime = (dateStr: string): string => {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getStatusType = (status: string): string => {
  switch (status) {
    case 'FILLED': return 'success'
    case 'PENDING': return 'warning' 
    case 'CANCELLED': return 'info'
    case 'FAILED': return 'danger'
    default: return 'info'
  }
}

const getStatusText = (status: string): string => {
  switch (status) {
    case 'FILLED': return '已成交'
    case 'PENDING': return '待成交'
    case 'CANCELLED': return '已撤销'
    case 'FAILED': return '失败'
    default: return status
  }
}

const getTradingUnit = (): number => {
  if (!selectedStock.value) return 100
  // 科创板200股为一手，其他100股为一手
  const stockCode = selectedStock.value.code || selectedStock.value.ts_code
  return stockCode?.startsWith('688') ? 200 : 100
}

// 刷新数据
const refreshData = async () => {
  loading.value = true
  try {
    const promises = [
      loadAccountData(),
      loadPositions()
    ]
    
    // 如果当前在交易记录tab，也刷新交易记录
    if (activeTab.value === 'trades') {
      promises.push(loadTrades())
    }
    
    await Promise.all(promises)
    ElMessage.success('数据刷新成功')
  } catch (error) {
    console.error('刷新数据失败:', error)
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

// 加载账户数据
const loadAccountData = async () => {
  try {
    const response = await simulationApi.getAccount()
    if (response.success && response.data) {
      Object.assign(accountData, response.data)
    }
  } catch (error) {
    console.error('加载账户数据失败:', error)
    ElMessage.error('加载账户数据失败')
  }
}

// 加载持仓数据
const loadPositions = async () => {
  positionsLoading.value = true
  try {
    const response = await simulationApi.getPositions()
    // console.log('持仓API响应:', response)
    // console.log('响应数据结构:', response.data)
    
    // 兼容处理：由于API响应结构不同，需要灵活处理
    if (response && (response.success !== false)) {
      // API直接返回 {total: 3, data: [...]} 或者标准格式
      let positionsData: any[] = []
      
      if (response.data && response.data.data) {
        // 标准格式: {success: true, data: {total: 3, data: [...]}}
        positionsData = response.data.data || []
      } else if (response.data && Array.isArray(response.data)) {
        // 直接数组格式: {success: true, data: [...]}
        positionsData = response.data
      } else if (response.data && response.data.total !== undefined) {
        // 模拟交易格式: {total: 3, data: [...]}
        positionsData = response.data.data || []
      }
      
      // console.log('解析后持仓数据:', positionsData)
      // console.log('持仓数量:', positionsData.length)
      
      // 强制清空再重新赋值，确保Vue响应式系统正确更新
      positions.value = []
      await nextTick()
      positions.value = [...positionsData]
      
      // console.log('Vue响应式数组更新完成:', positions.value.length)
    }
  } catch (error) {
    console.error('加载持仓数据失败:', error)
    ElMessage.error('加载持仓数据失败')
  } finally {
    positionsLoading.value = false
  }
}

// 加载交易记录
const loadTrades = async () => {
  tradesLoading.value = true
  try {
    const query: any = {
      page: tradeQuery.page,
      page_size: tradeQuery.page_size
    }
    
    if (tradeQuery.stock_code) {
      query.stock_code = tradeQuery.stock_code
    }
    
    if (tradeQuery.start_date) {
      query.start_date = tradeQuery.start_date.toISOString().split('T')[0]
    }
    
    if (tradeQuery.end_date) {
      query.end_date = tradeQuery.end_date.toISOString().split('T')[0]
    }
    
    const response = await simulationApi.getTrades(query)
    // console.log('交易记录API响应:', response)
    
    if (response && (response.success !== false)) {
      // 处理不同的响应格式
      let tradesData: any[] = []
      let total: number = 0
      
      if (response.data && response.data.data) {
        // 标准格式: {success: true, data: {total: x, data: [...], page: x, ...}}
        tradesData = response.data.data || []
        total = response.data.total || 0
      } else if (response.data && Array.isArray(response.data)) {
        // 直接数组格式
        tradesData = response.data
        total = tradesData.length
      } else if (response.data && response.data.total !== undefined) {
        // 模拟交易格式: {total: x, data: [...]}
        tradesData = response.data.data || []
        total = response.data.total || 0
      }
      
      trades.value = tradesData
      tradeTotal.value = total
      
      // console.log('交易记录加载完成:', tradesData.length, '/', total)
    }
  } catch (error) {
    console.error('加载交易记录失败:', error)
    ElMessage.error('加载交易记录失败')
  } finally {
    tradesLoading.value = false
  }
}

// 重置交易记录查询条件
const resetTradeQuery = () => {
  tradeQuery.page = 1
  tradeQuery.stock_code = ''
  tradeQuery.start_date = null
  tradeQuery.end_date = null
  loadTrades()
}

// 股票选择处理
const onStockSelected = async (stock: any) => {
  selectedStock.value = stock
  // console.log('选中股票:', stock)
  
  // 获取当前价格
  try {
    const stockCode = stock.code || stock.ts_code
    const response = await simulationApi.getStockQuote(stockCode)
    if (response.success && response.data) {
      currentPrice.value = response.data.current_price
      if (orderType.value === 'LIMIT') {
        orderPrice.value = response.data.current_price
      }
    }
  } catch (error) {
    console.error('获取股价失败:', error)
    ElMessage.warning('获取股价失败，请稍后重试')
  }
}

// 交易类型改变
const onTradeTypeChange = () => {
  if (tradeType.value === 'sell' && !canSell.value) {
    ElMessage.warning('当前股票无可卖持仓')
    tradeType.value = 'buy'
  }
}

// 打开卖出对话框
const openSellDialog = (position: any) => {
  selectedStock.value = {
    ts_code: position.stock_code,
    name: position.stock_name
  }
  currentPrice.value = position.current_price
  tradeType.value = 'sell'
  orderQuantity.value = Math.min(position.available_quantity, 100)
  
  if (orderType.value === 'LIMIT') {
    orderPrice.value = position.current_price
  }
}

// 计算交易费用
const calculateTradingCost = async () => {
  if (!selectedStock.value || !orderQuantity.value) {
    tradingCost.value = null
    return
  }
  
  const price = orderType.value === 'MARKET' ? currentPrice.value : orderPrice.value
  if (!price) return
  
  const amount = orderQuantity.value * price
  const market = selectedStock.value.ts_code.endsWith('.SH') ? 'SH' : 'SZ'
  
  try {
    const response = await simulationApi.calculateTradingCost(amount, tradeType.value.toUpperCase() as 'BUY' | 'SELL', market)
    if (response.success && response.data) {
      tradingCost.value = response.data
    }
  } catch (error) {
    console.error('计算交易费用失败:', error)
  }
}

// 提交订单
const submitOrder = async () => {
  if (!canSubmitOrder.value) return
  
  try {
    await ElMessageBox.confirm(
      `确认${tradeType.value === 'buy' ? '买入' : '卖出'} ${selectedStock.value.name} ${orderQuantity.value}股？`,
      '确认交易',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    submitting.value = true
    
    const orderData = {
      stock_code: selectedStock.value.ts_code,
      stock_name: selectedStock.value.name,
      quantity: orderQuantity.value,
      order_type: orderType.value,
      price: orderType.value === 'LIMIT' ? orderPrice.value : undefined
    }
    
    let response
    if (tradeType.value === 'buy') {
      response = await simulationApi.buyStock(orderData)
    } else {
      response = await simulationApi.sellStock(orderData)
    }
    
    if (response.success) {
      ElMessage.success(`${tradeType.value === 'buy' ? '买入' : '卖出'}订单提交成功`)
      // 重置表单
      resetForm()
      // 刷新数据
      await refreshData()
    } else {
      ElMessage.error(response.message || '订单提交失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('提交订单失败:', error)
      ElMessage.error(error?.response?.data?.detail || '订单提交失败')
    }
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  selectedStock.value = null
  currentPrice.value = 0
  orderPrice.value = 0
  orderQuantity.value = 100
  tradingCost.value = null
}

// 股票池相关方法
const showStockPoolDialog = () => {
  stockPoolDialogVisible.value = true
}

const onStockFromPoolSelected = (stock: any) => {
  // console.log('从股票池选择的股票:', stock)
  if (stock) {
    // 转换为股票搜索组件期望的格式
    const stockForTrading = {
      ts_code: stock.ts_code,
      name: stock.stock_name || stock.name,
      code: stock.ts_code
    }
    
    // 调用股票选择处理函数
    onStockSelected(stockForTrading)
    
    ElMessage.success(`已选择股票：${stockForTrading.name}`)
  }
}

// 监听数据变化，重新计算费用
watch([orderQuantity, orderPrice, orderType, tradeType, selectedStock], () => {
  calculateTradingCost()
}, { deep: true })

// 监听tab切换，加载对应数据
watch(activeTab, async (newTab) => {
  if (newTab === 'trades' && trades.value.length === 0) {
    loadTrades()
  } else if (newTab === 'strategy') {
    // 策略自动化tab：先加载配置，再加载状态
    if (strategies.value.length === 0) {
      await loadStrategyConfigs()
    }
    await loadStrategyStatus()
  }
})

// 策略自动化相关方法
const toggleStrategy = async (strategy: any) => {
  if (strategy.switching) return
  
  strategy.switching = true
  
  // 记录切换前的状态，因为v-model已经改变了strategy.is_active
  const isActivating = strategy.is_active
  const targetAction = isActivating ? '启动' : '停止'
  
  try {
    const response = isActivating 
      ? await simulationApi.activateStrategy({
          strategy_name: strategy.name,
          allocated_cash: strategy.allocated_cash
        })
      : await simulationApi.deactivateStrategy(strategy.name)
    
    if (response.success) {
      ElMessage.success(`策略${strategy.display_name}${targetAction}成功`)
      // 刷新策略状态
      await loadStrategyStatus()
    } else {
      // API调用失败，恢复开关状态
      strategy.is_active = !strategy.is_active
      ElMessage.error(response.message || '操作失败')
    }
  } catch (error: any) {
    console.error('策略切换失败:', error)
    // API调用失败，恢复开关状态
    strategy.is_active = !strategy.is_active
    ElMessage.error(error?.response?.data?.detail || '操作失败')
  } finally {
    strategy.switching = false
  }
}

const formatTime = (timeStr: string | null): string => {
  if (!timeStr) return '--'
  return new Date(timeStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getStrategyDisplayName = (strategyName: string): string => {
  const strategyMap: Record<string, string> = {
    'taishang_1': '太上老君1号',
    'taishang_2': '太上老君2号',
    'taishang_3': '太上老君3号'
  }
  return strategyMap[strategyName] || strategyName
}

const loadStrategyConfigs = async () => {
  try {
    // 首先加载策略配置信息
    const configResponse = await simulationApi.getStrategyConfigs()
    if (configResponse.success && configResponse.data && configResponse.data.strategies) {
      const configData = configResponse.data.strategies
      
      // 转换为前端需要的格式
      strategies.value = Object.keys(configData).map(strategyName => ({
        name: strategyName,
        display_name: configData[strategyName].display_name,
        description: configData[strategyName].description,
        frequency: configData[strategyName].rebalance_frequency,
        risk_control: configData[strategyName].risk_control,
        suitable_funds: configData[strategyName].suitable_funds,
        allocated_cash: parseFloat(configData[strategyName].default_allocated_cash.replace(/[^\d]/g, '')) || 300000,
        is_active: false,
        switching: false,
        current_positions: 0,
        total_return: 0,
        total_return_rate: 0,
        last_execution: null as string | null,
        next_run_time: null as string | null
      }))
      
      // console.log('策略配置加载成功:', strategies.value)
    }
  } catch (error: any) {
    console.error('加载策略配置失败:', error)
    ElMessage.error('加载策略配置失败')
    
    // 如果加载失败，使用默认配置作为兜底
    strategies.value = [
      {
        name: 'taishang_1',
        display_name: '太上老君1号',
        description: '多趋势共振策略，适合稳健投资',
        frequency: '每日检查',
        risk_control: '6%止损/12%止盈',
        suitable_funds: '30万-300万',
        allocated_cash: 300000,
        is_active: false,
        switching: false,
        current_positions: 0,
        total_return: 0,
        total_return_rate: 0,
        last_execution: null as string | null,
        next_run_time: null as string | null
      },
      {
        name: 'taishang_2',
        display_name: '太上老君2号',
        description: '好奇布偶猫BOLL策略，波段交易',
        frequency: '每日检查',
        risk_control: '10%止损/15%止盈',
        suitable_funds: '40万-500万',
        allocated_cash: 400000,
        is_active: false,
        switching: false,
        current_positions: 0,
        total_return: 0,
        total_return_rate: 0,
        last_execution: null as string | null,
        next_run_time: null as string | null
      },
      {
        name: 'taishang_3',
        display_name: '太上老君3号',
        description: '小市值动量策略，高收益潜力',
        frequency: '每5日调仓',
        risk_control: '6%止损/15%止盈',
        suitable_funds: '50万-1000万',
        allocated_cash: 500000,
        is_active: false,
        switching: false,
        current_positions: 0,
        total_return: 0,
        total_return_rate: 0,
        last_execution: null as string | null,
        next_run_time: null as string | null
      }
    ]
  }
}

const loadStrategyStatus = async () => {
  try {
    strategyLoading.value = true
    
    // 加载每个策略的状态
    for (const strategy of strategies.value) {
      const response = await simulationApi.getStrategyStatus(strategy.name)
      if (response.success && response.data) {
        const data = response.data
        strategy.is_active = data.is_active
        strategy.last_execution = data.last_execution || null
        strategy.next_run_time = data.next_run_time || null
        strategy.current_positions = data.current_positions || 0
        
        // 加载策略绩效
        const perfResponse = await simulationApi.getStrategyPerformance(strategy.name)
        if (perfResponse.success && perfResponse.data) {
          const perfData = perfResponse.data
          strategy.total_return = perfData.total_return || 0
          strategy.total_return_rate = perfData.total_return_rate || 0
        }
      }
    }
  } catch (error: any) {
    console.error('加载策略状态失败:', error)
    ElMessage.error('加载策略状态失败')
  } finally {
    strategyLoading.value = false
  }
}


// 监听页面刷新事件
eventBus.on('refresh-simulation-trading', refreshData)

// 组件挂载
onMounted(async () => {
  refreshData()
  // 如果当前在策略自动化tab，加载策略配置和状态
  if (activeTab.value === 'strategy') {
    await loadStrategyConfigs()
    await loadStrategyStatus()
  }
})
</script>

<style scoped>
.simulation-trading {
  padding: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-primary);
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.header-right {
  display: flex;
  gap: 12px;
}

.icon {
  width: 16px;
  height: 16px;
  margin-right: 8px;
}

/* 账户概览 */
.account-overview {
  margin-bottom: 20px;
}

.overview-card {
  border-radius: 12px;
  border: 1px solid var(--border-primary);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.account-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.stat-value.primary {
  font-size: 24px;
  color: var(--accent-primary);
}

.stat-value.profit {
  color: var(--success-primary);
}

.stat-value.loss {
  color: var(--danger-primary);
}

/* 主要内容区域 */
.main-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 20px;
  min-height: 0;
}

.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
}

/* Tab组件 */
.trading-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.trading-tabs .el-tabs__content {
  flex: 1;
  padding: 0;
}

.trading-tabs .el-tab-pane {
  height: 100%;
}

/* 持仓卡片 */
.positions-card,
.trades-card {
  flex: 1;
  height: 100%;
  border-radius: 12px;
  border: 1px solid var(--border-primary);
}

.positions-card .el-card__body,
.trades-card .el-card__body {
  height: calc(100% - 60px);
  display: flex;
  flex-direction: column;
}

.positions-card .el-table,
.trades-card .el-table {
  flex: 1;
}

.stock-code {
  font-family: monospace;
  font-weight: 600;
  color: var(--accent-primary);
}

.stock-name {
  color: var(--text-primary);
}

/* 中国股市红涨绿跌样式 */
.profit-cn {
  color: #ff4757 !important; /* 红色表示盈利/上涨 */
  font-weight: 600;
}

.loss-cn {
  color: #2ed573 !important; /* 绿色表示亏损/下跌 */
  font-weight: 600;
}

/* 盈利/亏损标签样式 */
.profit-tag-cn {
  background-color: #ff4757 !important;
  color: white !important;
  border-color: #ff4757 !important;
}

.loss-tag-cn {
  background-color: #2ed573 !important;
  color: white !important;
  border-color: #2ed573 !important;
}

/* 买入/卖出标签样式 */
.buy-tag-cn {
  background-color: #ff4757 !important; /* 买入用红色 */
  color: white !important;
  border-color: #ff4757 !important;
}

.sell-tag-cn {
  background-color: #2ed573 !important; /* 卖出用绿色 */
  color: white !important;
  border-color: #2ed573 !important;
}

/* 买入/卖出按钮样式 */
.buy-button-cn {
  background-color: #ff4757 !important;
  border-color: #ff4757 !important;
  color: white !important;
}

.buy-button-cn:hover {
  background-color: #ff3742 !important;
  border-color: #ff3742 !important;
}

.sell-button-cn {
  background-color: #2ed573 !important;
  border-color: #2ed573 !important;
  color: white !important;
}

.sell-button-cn:hover {
  background-color: #26d062 !important;
  border-color: #26d062 !important;
}

/* 原来的样式保持向后兼容 */
.profit {
  color: #ff4757 !important;
}

.loss {
  color: #2ed573 !important;
}

/* 交易卡片 */
.trading-card {
  border-radius: 12px;
  border: 1px solid var(--border-primary);
}

.trading-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-item {
  position: relative;
}

.form-item label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.search-icon {
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
}

/* 搜索结果 */
.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-height: 200px;
  overflow-y: auto;
}

.search-result-item {
  padding: 12px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-secondary);
}

.search-result-item:hover {
  background: var(--bg-secondary);
}

.search-result-item:last-child {
  border-bottom: none;
}

/* 选中股票信息 */
.selected-stock {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stock-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stock-info .stock-code {
  font-size: 14px;
}

.stock-info .stock-name {
  font-size: 12px;
  color: var(--text-secondary);
}

.current-price {
  font-size: 18px;
  font-weight: 600;
  color: var(--accent-primary);
}

/* 股票选择容器 */
.stock-selection-container {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.stock-search {
  flex: 1;
}

.pool-select-btn {
  flex-shrink: 0;
  white-space: nowrap;
}

/* 数量提示 */
.quantity-tips {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-tertiary);
  display: flex;
  justify-content: space-between;
}

/* 费用计算 */
.trading-cost {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.trading-cost h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: var(--text-primary);
}

.cost-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 4px;
}

.cost-item.total {
  font-weight: 600;
  font-size: 14px;
  border-top: 1px solid var(--border-primary);
  padding-top: 4px;
  margin-top: 4px;
}

/* 表单操作 */
.form-actions {
  margin-top: 8px;
}

/* 交易记录样式 */
.trades-filter {
  margin-bottom: 16px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.filter-form {
  margin: 0;
}

.filter-form .el-form-item {
  margin-bottom: 0;
  margin-right: 16px;
}

.filter-form .el-form-item:last-child {
  margin-right: 0;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

/* 策略自动化样式 */
.strategy-automation {
  padding: 20px;
}

.strategy-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.strategy-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s ease;
}

.strategy-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.strategy-title {
  flex: 1;
}

.strategy-title h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.strategy-title p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.strategy-toggle {
  flex-shrink: 0;
  margin-left: 16px;
}

.strategy-info {
  margin-bottom: 16px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.info-item .label {
  color: var(--text-secondary);
}

.info-item .value {
  color: var(--text-primary);
  font-weight: 500;
}

.strategy-status {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
  font-size: 13px;
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-item .label {
  color: var(--text-secondary);
}

.status-item .value {
  color: var(--text-primary);
  font-weight: 500;
}

.strategy-performance {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-primary);
}

.performance-item {
  text-align: center;
}

.performance-item .label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.performance-item .value {
  font-size: 16px;
  font-weight: 600;
}

.strategy-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
  color: var(--text-secondary);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr auto;
  }
  
  .right-panel {
    order: -1;
  }
  
  .strategy-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .account-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .page-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .strategy-automation {
    padding: 16px;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .strategy-status {
    grid-template-columns: 1fr;
  }
}
</style>