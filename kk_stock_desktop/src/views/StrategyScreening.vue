<template>
  <div class="strategy-screening-page">
    <div class="page-header">
      <h1 class="page-title">
        <component :is="ChartBarIcon" class="icon-size" />
        策略选股
      </h1>
      <p class="page-subtitle">基于技术面、基本面和特色指标进行智能选股</p>
    </div>

    <div class="screening-container">
      <!-- 用户股票池面板 -->
      <div class="stock-pool-section" v-if="authStore.isAuthenticated">
        <el-card class="stock-pool-card">
          <template #header>
            <div class="card-header-content">
              <div class="header-left">
                <component :is="CubeIcon" class="header-icon" />
                <span>我的股票池</span>
              </div>
            </div>
          </template>
          <StockPoolManager
            ref="stockPoolManagerRef"
            mode="manager"
            :show-actions="true"
            @pool-created="handlePoolCreated"
            @pool-updated="handlePoolUpdated"
            @pool-deleted="handlePoolDeleted"
            @stock-added="handleStockAdded"
          />
        </el-card>
      </div>

      <!-- 筛选条件区域 -->
      <div class="screening-form">
        <el-card class="form-card">
          <template #header>
            <div class="card-header-content">
              <span>筛选条件</span>
              <div class="header-actions">
                <el-button type="primary" size="small" @click="resetFilters">
                  重置
                </el-button>
                <el-button type="success" size="small" @click="startScreening" :loading="isScreening">
                  {{ isScreening ? '筛选中...' : '开始筛选' }}
                </el-button>
              </div>
            </div>
          </template>

          <!-- 策略模板选择区域 -->
          <div class="template-section">
            <h3 class="section-title">
              <component :is="ChartBarIcon" class="section-icon" />
              选择策略模板
              <span class="template-count">({{ strategyTemplates.length }}个策略)</span>
            </h3>
            <el-row :gutter="20" class="template-grid">
              <el-col 
                :xs="12" 
                :sm="12" 
                :md="8" 
                :lg="6" 
                :xl="6" 
                v-for="template in strategyTemplates" 
                :key="template.id"
                class="template-col"
              >
                <el-card class="template-card" :class="{ active: selectedTemplate === template.id }">
                  <div class="template-content" @click="selectTemplate(template)">
                    <!-- 选择状态圆圈 -->
                    <div class="selection-indicator">
                      <div class="selection-circle" :class="{ selected: selectedTemplate === template.id }">
                        <div class="selection-dot" v-if="selectedTemplate === template.id"></div>
                      </div>
                    </div>
                    <div class="template-icon">
                      <component :is="templateIcons[template.strategy_type] || ChartBarIcon" />
                    </div>
                    <h3 class="template-name">{{ template.name }}</h3>
                    <p class="template-description">{{ template.description }}</p>
                    
                    <!-- 策略简介 -->
                    <div class="strategy-brief">
                      <div class="brief-text">{{ getStrategyBrief(template.strategy_type) }}</div>
                    </div>
                  </div>
                  
                  <!-- 卡片操作区域 -->
                  <div class="card-actions">
                    <el-button 
                      size="small" 
                      type="primary" 
                      plain 
                      @click.stop="showStrategyDetail(template)"
                      class="detail-btn"
                    >
                      <component :is="InformationCircleIcon" class="btn-icon" />
                      策略详情
                    </el-button>
                    <el-button 
                      size="small" 
                      :type="selectedTemplate === template.id ? 'success' : 'default'"
                      @click.stop="selectTemplate(template)"
                      class="select-btn"
                    >
                      {{ selectedTemplate === template.id ? '已选择' : '选择策略' }}
                    </el-button>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </div>

      <!-- 结果展示区域 -->
      <div class="results-section">
        <el-card class="results-card">
          <template #header>
            <div class="card-header-content">
              <span>筛选结果 ({{ screeningResults.length }})</span>
              <div class="header-actions">
                <el-button size="small" @click="exportResults" :disabled="screeningResults.length === 0">
                  导出结果
                </el-button>
                <el-button size="small" @click="addAllToPool" :disabled="screeningResults.length === 0">
                  批量加入股票池
                </el-button>
              </div>
            </div>
          </template>

          <div v-if="isScreening" class="loading-container" v-loading="isScreening" element-loading-text="正在筛选股票...">
            <div style="height: 200px;"></div>
          </div>

          <div v-else-if="screeningResults.length === 0" class="empty-container">
            <el-empty description="暂无筛选结果" />
          </div>

          <div v-else class="results-table-container">
            <!-- 动态响应式表格 -->
            <div class="table-wrapper">
                          <el-table 
              :key="`table-${selectedTemplate}-${screeningResults.length}`"
              :data="paginatedResults" 
              stripe 
              class="modern-table"
              :default-sort="{ prop: 'score', order: 'descending' }"
              @sort-change="handleSortChange"
              v-loading="isScreening"
              table-layout="auto"
              size="default"
            >
                <!-- 动态列 - 根据策略类型显示不同指标 -->
                <el-table-column 
                  v-for="column in currentColumns" 
                  :key="`${selectedTemplate}-${column.prop}`"
                  :prop="column.prop" 
                  :label="column.label" 
                  :min-width="column.minWidth || 80"
                  :sortable="column.sortable"
                  :show-overflow-tooltip="column.prop === 'name'"
                >
                  <template #default="{ row }">
                    <!-- 股票名称特殊处理 - 包含股票代码 -->
                    <div v-if="column.prop === 'name'" class="name-cell">
                      <div class="stock-main-info">
                        <div class="stock-title">
                          <span class="stock-name">{{ row.name }}</span>
                          <span class="stock-code">({{ row.ts_code }})</span>
                        </div>
                        <span class="industry-tag" v-if="row.industry">{{ row.industry }}</span>
                      </div>
                    </div>
                    <!-- 评分列特殊处理 -->
                    <div v-else-if="column.prop === 'score'" class="score-cell">
                      <div class="score-display">
                        <span class="score-number">{{ formatCellValue(row[column.prop], row, column.type || '', column.prop) }}</span>
                        <div class="score-bar">
                          <div 
                            class="score-fill" 
                            :style="{ width: getScorePercentage(row.score) + '%' }"
                          ></div>
                        </div>
                      </div>
                    </div>
                    <!-- 普通列处理 -->
                    <span v-else :class="getCellClass(row[column.prop], column.type || '')">
                      {{ formatCellValue(row[column.prop], row, column.type || '', column.prop) }}
                    </span>
                  </template>
                </el-table-column>
                
                <!-- 操作列 - 使用新的股票池选择对话框 -->
                <el-table-column label="操作" min-width="120" fixed="right">
                  <template #default="{ row }">
                    <div class="action-cell">
                      <el-button size="small" type="success" @click="addSingleStockToPool(row)">
                        加入股票池
                      </el-button>
                    </div>
                  </template>
                </el-table-column>
                </el-table>
            </div>
            
            <!-- 分页组件 -->
            <div class="pagination-container">
              <el-pagination
                v-model:current-page="currentPage"
                v-model:page-size="pageSize"
                :page-sizes="[5, 10, 20, 50]"
                :total="sortedResults.length"
                layout="total, sizes, prev, pager, next, jumper"
                background
                @size-change="handleSizeChange"
                @current-change="handleCurrentChange"
              />
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 策略详情弹窗 -->
    <StrategyDetailModal
      v-model="showDetailModal"
      :strategy-template="currentDetailTemplate"
      @save-settings="saveStrategySettings"
    />
    
    <!-- 股票池选择对话框 -->
    <StockPoolSelectDialog
      v-model="showStockPoolDialog"
      :pre-selected-stocks="selectedStocksForPool"
      @confirmed="handleStockPoolConfirmed"
      @canceled="handleStockPoolCanceled"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { 
  ChartBarIcon, 
  ArrowTrendingUpIcon, 
  ScaleIcon, 
  BoltIcon, 
  CurrencyDollarIcon,
  ArrowPathIcon,
  FireIcon,
  InformationCircleIcon,
  EyeIcon,
  CubeIcon
} from '@heroicons/vue/24/outline'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  applyStrategyTemplate,
  exportScreeningResults,
  type ScreeningResult
} from '@/api/strategy'
import { useAuthStore } from '@/stores/auth'
import StrategyDetailModal from '@/components/StrategyDetailModal.vue'
import { usePageRefresh, PAGE_REFRESH_CONFIG } from '@/utils/usePageRefresh'
import StockPoolManager from '@/components/StockPool/StockPoolManager.vue'
import StockPoolSelectDialog from '@/components/StockPool/StockPoolSelectDialog.vue'
import { type StockInfo, type StockPool } from '@/services/stockPoolService'

// Store
const authStore = useAuthStore()

// 统一刷新函数
const refreshStrategy = async () => {
  // console.log('开始刷新策略选股数据...')
  try {
    // 如果有当前筛选结果，重新执行筛选
    if (selectedTemplate.value && screeningResults.value.length > 0) {
      await startScreening()
    }
    
    // console.log('策略选股数据刷新完成')
  } catch (error) {
    console.error('策略选股数据刷新失败:', error)
  }
}

// 使用页面刷新组合函数
const { refresh } = usePageRefresh(
  refreshStrategy,
  PAGE_REFRESH_CONFIG.STRATEGY.path,
  PAGE_REFRESH_CONFIG.STRATEGY.event
)

// 响应式数据
const isScreening = ref(false)
const selectedTemplate = ref<string | null>(null)
const screeningResults = ref<ScreeningResult[]>([])

// 策略详情弹窗相关
const showDetailModal = ref(false)
const currentDetailTemplate = ref<any>(null)
const strategySettings = ref<Record<string, any>>({})

// 分页相关
const currentPage = ref(1)
const pageSize = ref(5)  // 默认每页5条
const sortConfig = ref({ prop: 'score', order: 'descending' })

// 引用股票池管理器
const stockPoolManagerRef = ref<InstanceType<typeof StockPoolManager> | null>(null)

// 股票池选择对话框相关
const showStockPoolDialog = ref(false)
const selectedStocksForPool = ref<StockInfo[]>([])

// 计算属性
const sortedResults = computed(() => {
  const results = [...screeningResults.value]
  if (sortConfig.value.prop) {
    results.sort((a, b) => {
      const aVal = a[sortConfig.value.prop as keyof ScreeningResult] || 0
      const bVal = b[sortConfig.value.prop as keyof ScreeningResult] || 0
      
      if (sortConfig.value.order === 'ascending') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })
  }
  return results
})

const paginatedResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return sortedResults.value.slice(start, end)
})

// 8个固定的策略模板
const strategyTemplates = ref([
  {
    id: '686a347c09e24f7707f7b4d8',
    name: '价值投资策略',
    strategy_type: 'value',
    description: '基于PE、PB、ROE等指标筛选低估值优质股票'
  },
  {
    id: '686a347c09e24f7707f7b4d9',
    name: '高质量成长股策略',
    strategy_type: 'growth',
    description: '严格筛选EPS增长>25%、ROIC>10%、PEG<1的优质成长股'
  },
  {
    id: '686a78a59faddf493bb01c60',
    name: '动量突破策略',
    strategy_type: 'momentum',
    description: '基于技术指标识别突破趋势的强势股票'
  },
  {
    id: '686a71f4c51f290dcebb0742',
    name: '高股息策略',
    strategy_type: 'dividend',
    description: '筛选股息率高、分红稳定的价值股票'
  },
  {
    id: '686a347c09e24f7707f7b4da',
    name: '技术突破策略',
    strategy_type: 'technical',
    description: '基于RSI、MACD等技术指标的突破信号'
  },
  {
    id: '686a347c09e24f7707f7b4db',
    name: '超跌反弹策略',
    strategy_type: 'oversold',
    description: '筛选超跌后具备反弹潜力的股票'
  },
  {
    id: '686a347c09e24f7707f7b4dc',
    name: '连板龙头策略',
    strategy_type: 'limit_up',
    description: '识别连续涨停的龙头股票'
  },
  {
    id: '686a347c09e24f7707f7b4dd',
    name: '资金追踪策略',
    strategy_type: 'fund_flow',
    description: '基于资金流向筛选受到资金关注的股票'
  }
])

// 策略模板图标映射 - 统一使用策略类型ID
const templateIcons: Record<string, any> = {
  // 策略类型ID映射（与前后端保持一致）
  'value': ScaleIcon,               // 价值投资策略
  'growth': ArrowTrendingUpIcon,    // 成长股策略
  'momentum': BoltIcon,             // 动量突破策略
  'dividend': CurrencyDollarIcon,   // 高股息策略
  'technical': ChartBarIcon,        // 技术突破策略
  'oversold': ArrowPathIcon,        // 超跌反弹策略
  'limit_up': FireIcon,             // 连板龙头策略
  'fund_flow': EyeIcon, // 资金追踪策略
  // 兼容中文名称映射（向后兼容）
  '价值投资策略': ScaleIcon,
  '成长股策略': ArrowTrendingUpIcon,
  '动量突破策略': BoltIcon,
  '高股息策略': CurrencyDollarIcon,
  '技术突破策略': ChartBarIcon,
  '超跌反弹策略': ArrowPathIcon,
  '连板龙头策略': FireIcon,
  '资金追踪策略': EyeIcon
  }

// 策略列配置 - 简化版本，只定义列信息
const strategyColumnConfig: Record<string, Array<{
  prop: string
  label: string
  minWidth?: number
  sortable?: boolean
  type?: string
}>> = {
  'value': [
    { prop: 'name', label: '股票名称', minWidth: 120 },
    { prop: 'close', label: '最新价', minWidth: 80, sortable: true, type: 'price' },
    { prop: 'pct_chg', label: '涨跌幅', minWidth: 80, sortable: true, type: 'change' },
    { prop: 'pe', label: 'PE', minWidth: 70, sortable: true, type: 'pe' },
    { prop: 'pb', label: 'PB', minWidth: 70, sortable: true, type: 'pb' },
    { prop: 'technical.roe', label: 'ROE%', minWidth: 80, sortable: true, type: 'roe' },
    { prop: 'technical.current_ratio', label: '流动比率', minWidth: 90, sortable: true, type: 'ratio' },
    { prop: 'technical.debt_ratio', label: '负债率%', minWidth: 90, sortable: true, type: 'debt' },
    { prop: 'total_mv', label: '总市值', minWidth: 100, sortable: true, type: 'market_cap' },
    { prop: 'score', label: '价值评分', minWidth: 120, sortable: true, type: 'score' }
  ],
  'growth': [
    { prop: 'name', label: '股票名称', minWidth: 120 },
    { prop: 'close', label: '最新价', minWidth: 80, sortable: true, type: 'price' },
    { prop: 'pct_chg', label: '涨跌幅', minWidth: 80, sortable: true, type: 'change' },
    { prop: 'avg_eps_growth', label: 'EPS增长%', minWidth: 100, sortable: true, type: 'growth_rate' },
    { prop: 'avg_revenue_growth', label: '营收增长%', minWidth: 100, sortable: true, type: 'growth_rate' },
    { prop: 'avg_roic', label: 'ROIC%', minWidth: 80, sortable: true, type: 'percentage' },
    { prop: 'peg_ratio', label: 'PEG', minWidth: 70, sortable: true, type: 'peg' },
    { prop: 'avg_gross_margin', label: '毛利率%', minWidth: 90, sortable: true, type: 'percentage' },
    { prop: 'avg_net_margin', label: '净利率%', minWidth: 90, sortable: true, type: 'percentage' },
    { prop: 'latest_rd_rate', label: '研发费用率%', minWidth: 110, sortable: true, type: 'percentage' },
    { prop: 'total_mv', label: '总市值', minWidth: 100, sortable: true, type: 'market_cap' },
    { prop: 'score', label: '成长评分', minWidth: 120, sortable: true, type: 'score' }
  ],
  'momentum': [
    { prop: 'name', label: '股票名称', minWidth: 120 },
    { prop: 'close', label: '最新价', minWidth: 80, sortable: true, type: 'price' },
    { prop: 'pct_chg', label: '涨跌幅', minWidth: 80, sortable: true, type: 'change' },
    { prop: 'period_return', label: '60日收益', minWidth: 100, sortable: true, type: 'period_return' },
    { prop: 'rps_score', label: 'RPS', minWidth: 80, sortable: true, type: 'rps' },
    { prop: 'rsi', label: 'RSI', minWidth: 70, sortable: true, type: 'rsi' },
    { prop: 'macd', label: 'MACD', minWidth: 80, sortable: true, type: 'macd' },
    { prop: 'ema_20', label: 'EMA20', minWidth: 80, sortable: true, type: 'ema' },
    { prop: 'score', label: '动量评分', minWidth: 120, sortable: true, type: 'score' }
  ],
  'dividend': [
    { prop: 'name', label: '股票名称', minWidth: 140 },
    { prop: 'close', label: '最新价', minWidth: 80, sortable: true, type: 'price' },
    { prop: 'pct_chg', label: '涨跌幅', minWidth: 80, sortable: true, type: 'change' },
    { prop: 'dividend_yield', label: '股息率%', minWidth: 100, sortable: true, type: 'dividend_yield' },
    { prop: 'payout_ratio', label: '股息支付率%', minWidth: 110, sortable: true, type: 'percentage' },
    { prop: 'dividend_fundraising_ratio', label: '分红募资比%', minWidth: 120, sortable: true, type: 'percentage' },
    { prop: 'net_cash', label: '净现金(万元)', minWidth: 110, sortable: true, type: 'net_cash' },
    { prop: 'roe', label: 'ROE%', minWidth: 80, sortable: true, type: 'roe' },
    { prop: 'roic', label: 'ROIC%', minWidth: 80, sortable: true, type: 'percentage' },
    { prop: 'eps', label: 'EPS', minWidth: 80, sortable: true, type: 'eps' },
    { prop: 'net_profit_margin', label: '净利润率%', minWidth: 100, sortable: true, type: 'percentage' },
    { prop: 'debt_ratio', label: '资产负债率%', minWidth: 110, sortable: true, type: 'percentage' },
    { prop: 'score', label: '综合评分', minWidth: 120, sortable: true, type: 'score' }
  ],
  'technical': [
    { prop: 'name', label: '股票名称', minWidth: 140 },
    { prop: 'close', label: '最新价', minWidth: 80, sortable: true, type: 'price' },
    { prop: 'pct_chg', label: '涨跌幅', minWidth: 80, sortable: true, type: 'change' },
    { prop: 'rsi', label: 'RSI', minWidth: 70, sortable: true, type: 'rsi' },
    { prop: 'macd', label: 'MACD', minWidth: 80, sortable: true, type: 'macd' },
    { prop: 'volume_ratio', label: '量比', minWidth: 70, sortable: true, type: 'volume_ratio' },
    { prop: 'ema_20', label: '20日均线', minWidth: 90, sortable: true, type: 'ema' },
    { prop: 'breakthrough_signal', label: '突破信号', minWidth: 90, sortable: true, type: 'breakthrough' },
    { prop: 'total_mv', label: '总市值', minWidth: 100, sortable: true, type: 'market_cap' },
    { prop: 'score', label: '突破评分', minWidth: 100, sortable: true, type: 'score' }
  ],
  'oversold': [
    { prop: 'name', label: '股票名称', minWidth: 120 },
    { prop: 'close', label: '最新价', minWidth: 80, sortable: true, type: 'price' },
    { prop: 'pct_chg', label: '涨跌幅', minWidth: 80, sortable: true, type: 'change' },
    { prop: 'rsi', label: 'RSI', minWidth: 70, sortable: true, type: 'rsi' },
    { prop: 'pe', label: 'PE', minWidth: 70, sortable: true, type: 'pe' },
    { prop: 'pb', label: 'PB', minWidth: 70, sortable: true, type: 'pb' },
    { prop: 'total_mv', label: '总市值', minWidth: 100, sortable: true, type: 'market_cap' },
    { prop: 'score', label: '反弹评分', minWidth: 120, sortable: true, type: 'score' }
  ],
  'limit_up': [
    { prop: 'name', label: '股票名称', minWidth: 120 },
    { prop: 'close', label: '最新价', minWidth: 80, sortable: true, type: 'price' },
    { prop: 'pct_chg', label: '涨跌幅', minWidth: 80, sortable: true, type: 'change' },
    { prop: 'limit_times', label: '连板天数', minWidth: 90, sortable: true, type: 'limit_times' },
    { prop: 'open_times', label: '开板次数', minWidth: 90, sortable: true, type: 'open_times' },
    { prop: 'turnover_rate', label: '换手率%', minWidth: 90, sortable: true, type: 'limit_turnover' },
    { prop: 'total_mv', label: '总市值', minWidth: 100, sortable: true, type: 'market_cap' },
    { prop: 'score', label: '龙头评分', minWidth: 120, sortable: true, type: 'score' }
  ],
  'fund_flow': [
    { prop: 'name', label: '股票名称', minWidth: 120 },
    { prop: 'close', label: '最新价', minWidth: 80, sortable: true, type: 'price' },
    { prop: 'pct_chg', label: '涨跌幅', minWidth: 80, sortable: true, type: 'change' },
    { prop: 'margin_buy_trend', label: '融资买入趋势%', minWidth: 120, sortable: true, type: 'percentage' },
    { prop: 'margin_balance_growth', label: '融资余额增长%', minWidth: 120, sortable: true, type: 'percentage' },
    { prop: 'fund_tracking_score', label: '追踪评分', minWidth: 100, sortable: true, type: 'score' },
    { prop: 'total_mv', label: '总市值', minWidth: 100, sortable: true, type: 'market_cap' }
  ]
}

// 获取当前策略的列配置
const currentColumns = computed(() => {
  if (selectedTemplate.value) {
    const template = strategyTemplates.value.find(t => t.id === selectedTemplate.value)
    if (template && template.strategy_type) {
      const columns = strategyColumnConfig[template.strategy_type] || strategyColumnConfig['value']
      // console.log(`[策略选股] 切换到策略: ${template.strategy_type}, 列配置:`, columns)
      return columns
    }
  }
  // 默认显示价值投资的列配置
  // console.log('[策略选股] 使用默认价值投资列配置')
  return strategyColumnConfig['value']
})

// 获取嵌套属性值的辅助函数
const getNestedValue = (obj: any, path: string): any => {
  return path.split('.').reduce((current, key) => current?.[key], obj)
}

// 格式化函数 - 根据类型格式化数据
const formatCellValue = (value: any, row: any, type: string, prop: string): string => {
  // 如果是嵌套属性，重新获取值
  if (prop.includes('.')) {
    value = getNestedValue(row, prop)
  }
  
  switch (type) {
    case 'price':
      return value ? `¥${value.toFixed(2)}` : '--'
    case 'change':
      return formatChange(value)
    case 'pe':
      return formatPE(value)
    case 'pb':
      return formatPB(value)
    case 'roe':
      return value ? `${value}%` : '--'
    case 'roe_simple':
      return value ? `${value}%` : '--'
    case 'ratio':
      return value ? value.toFixed(2) : '--'
    case 'debt':
      return value ? `${value}%` : '--'
    case 'rsi':
      // 优先使用顶层字段，如果没有则尝试从technical对象获取
      const rsi = value !== null && value !== undefined ? value : row?.technical?.rsi_qfq_12
      return rsi ? rsi.toFixed(1) : '--'
    case 'volume_ratio':
      // 优先使用顶层字段，如果没有则尝试从technical对象获取
      const vr = value !== null && value !== undefined ? value : row?.technical?.volume_ratio
      return vr ? vr.toFixed(2) : '--'
    case 'macd':
      // 优先使用顶层字段，如果没有则尝试从technical对象获取
      const macd = value !== null && value !== undefined ? value : row?.technical?.macd_qfq
      return macd ? (macd > 0 ? `+${macd.toFixed(3)}` : macd.toFixed(3)) : '--'
    case 'dividend':
      const dy = row?.technical?.dividend_yield
      return dy ? `${dy}%` : '--'
    case 'dividend_yield':
      return value !== null && value !== undefined ? `${value.toFixed(2)}%` : '--'
    case 'dividend_coverage_ratio':
      return value !== null && value !== undefined ? `${value.toFixed(2)}倍` : '--'
    case 'eps':
      return value !== null && value !== undefined ? `¥${value.toFixed(2)}` : '--'
    case 'net_profit_margin':
      return value !== null && value !== undefined ? `${value.toFixed(2)}%` : '--'
    case 'net_cash':
      return value !== null && value !== undefined ? `${value.toFixed(2)}万元` : '--'
    case 'limit_days':
      const days = row?.special?.limit_days
      return days ? `${days}天` : '--'
    case 'turnover':
      const tr = row?.technical?.turnover_rate
      return tr ? `${tr}%` : '--'
    case 'limit_turnover':
      const limitTr = row?.turnover_rate || row?.special?.turnover_rate
      return limitTr ? `${limitTr}%` : '--'
    case 'net_inflow':
      const inflow = row?.special?.net_inflow
      return inflow ? `${(inflow / 10000).toFixed(2)}万` : '--'
    case 'growth_rate':
      return value !== null && value !== undefined ? `${value.toFixed(2)}%` : '--'
    case 'percentage':
      return value !== null && value !== undefined ? `${value.toFixed(2)}%` : '--'
    case 'peg':
      return value !== null && value !== undefined ? value.toFixed(2) : '--'
    case 'period_return':
      return value !== null && value !== undefined ? `${(value * 100).toFixed(2)}%` : '--'
    case 'rps':
      return value !== null && value !== undefined ? value.toFixed(1) : '--'
    case 'ema':
      return value !== null && value !== undefined ? `¥${value.toFixed(2)}` : '--'
    case 'breakthrough':
      return value ? '✅ 是' : '❌ 否'
    case 'limit_times':
      const times = row?.special?.limit_times || value
      return times ? `${times}连板` : '--'
    case 'open_times':
      const openTimes = row?.special?.open_times || value
      return openTimes !== null && openTimes !== undefined ? `${openTimes}次` : '--'
    case 'leader_signal':
      const signal = row?.special?.leader_signal || value
      return signal ? '🔥 强龙头' : '⚠️ 观察'
    case 'sector_up_nums':
      const sectorNums = row?.special?.sector_up_nums || value
      return sectorNums ? `${sectorNums}只` : '--'
    case 'fund_amount':
      return value !== null && value !== undefined ? `${value.toFixed(2)}万` : '--'
    case 'rank':
      return value !== null && value !== undefined ? `第${value}名` : '--'
    case 'market_cap':
      return formatMarketCap(value)
    case 'score':
      return formatScore(value)
    default:
      return value || '--'
  }
}

// 获取单元格样式类
const getCellClass = (value: any, type: string): string => {
  if (type === 'change') {
    return getChangeClass(value)
  }
  return ''
}

// 获取评分百分比（用于进度条显示）
const getScorePercentage = (score: number | undefined): number => {
  if (score === undefined || score === null) return 0
  // 假设最高分为200分，转换为百分比
  return Math.min((score / 200) * 100, 100)
}

// 方法
const resetFilters = () => {
  selectedTemplate.value = null
  screeningResults.value = []
  ElMessage.success('已重置选择')
}

const startScreening = async () => {
  if (!authStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    return
  }

  if (!selectedTemplate.value) {
    ElMessage.warning('请先选择策略模板')
    return
  }

  isScreening.value = true
  try {
    let results: ScreeningResult[] = []
    
    // 获取当前选择策略的自定义参数
    const customSettings = strategySettings.value[selectedTemplate.value]
    const selectedStrategy = strategyTemplates.value.find(t => t.id === selectedTemplate.value)
    
    // 对于高股息策略，使用直接API调用
    if (selectedStrategy?.strategy_type === 'dividend') {
      // console.log('使用高股息策略直接API调用')
      const { highDividendScreening } = await import('@/api/strategy')
      
      // 构建高股息策略参数
      const dividendParams = {
        market_cap: 'all',
        stock_pool: 'all',
        limit: 20,
        dividend_yield_min: customSettings?.parameters?.dividend_yield_min || 2.0,
        payout_ratio_min: customSettings?.parameters?.payout_ratio_min || 20.0,
        dividend_fundraising_ratio_min: customSettings?.parameters?.dividend_fundraising_ratio_min || 30.0,
        net_cash_min: customSettings?.parameters?.net_cash_min || -1000000.0
      }
      
      // console.log('高股息策略参数:', dividendParams)
      const response = await highDividendScreening(dividendParams)
      
      if (response.data) {
        const screeningResponse = response.data
        results = screeningResponse.results || []
      }
    } else if (selectedStrategy?.strategy_type === 'technical') {
      // console.log('使用技术突破策略直接API调用')
      const { technicalBreakthroughScreening } = await import('@/api/strategy')
      
      // 构建技术突破策略参数
      const technicalParams = {
        market_cap: 'all',
        stock_pool: 'all',
        limit: 20,
        rsi_min: customSettings?.parameters?.rsi_min || 45.0,
        rsi_max: customSettings?.parameters?.rsi_max || 85.0,
        volume_ratio_min: customSettings?.parameters?.volume_ratio_min || 1.2,
        macd_requirement: customSettings?.parameters?.macd_requirement !== undefined ? customSettings.parameters.macd_requirement : false,
        ma_alignment: customSettings?.parameters?.ma_alignment !== undefined ? customSettings.parameters.ma_alignment : false,
        bollinger_position: customSettings?.parameters?.bollinger_position || 'upper'
      }
      
      // console.log('技术突破策略参数:', technicalParams)
      const response = await technicalBreakthroughScreening(technicalParams)
      
      if (response.data) {
        const screeningResponse = response.data
        results = screeningResponse.results || []
      }
    } else if (selectedStrategy?.strategy_type === 'oversold') {
      // console.log('使用超跌反弹策略直接API调用')  
      const { oversoldReboundScreening } = await import('@/api/strategy')
      
      // 构建超跌反弹策略参数
      const oversoldParams = {
        market_cap: 'all',
        stock_pool: 'all',
        limit: 20,
        rsi_min: customSettings?.parameters?.rsi_min || 15.0,
        rsi_max: customSettings?.parameters?.rsi_max || 35.0,
        volume_ratio_min: customSettings?.parameters?.volume_ratio_min || 1.3,
        pe_max: customSettings?.parameters?.pe_max || 50.0,
        pb_max: customSettings?.parameters?.pb_max || 8.0,
        decline_days: customSettings?.parameters?.decline_days || 3
      }
      
      // console.log('超跌反弹策略参数:', oversoldParams)
      const response = await oversoldReboundScreening(oversoldParams)
      
      if (response.data) {
        const screeningResponse = response.data
        results = screeningResponse.results || []
      }
    } else if (selectedStrategy?.strategy_type === 'limit_up') {
      // console.log('使用连板龙头策略直接API调用')
      const { limitUpLeaderScreening } = await import('@/api/strategy')
      
      // 构建连板龙头策略参数
      const limitUpParams = {
        market_cap: 'all',
        stock_pool: 'all',
        limit: 20,
        min_limit_times: customSettings?.parameters?.min_limit_times || 2,
        max_limit_times: customSettings?.parameters?.max_limit_times || 10,
        max_open_times: customSettings?.parameters?.max_open_times || 3,
        min_turnover: customSettings?.parameters?.min_turnover || 5.0,
        max_turnover: customSettings?.parameters?.max_turnover || 30.0
      }
      
      // console.log('连板龙头策略参数:', limitUpParams)    
      const response = await limitUpLeaderScreening(limitUpParams)
      
      if (response.data) {
        const screeningResponse = response.data
        results = screeningResponse.results || []
      }
    } else if (selectedStrategy?.strategy_type === 'fund_flow') {
      // console.log('使用资金追踪策略直接API调用')
      const { fundFlowTrackingScreening } = await import('@/api/strategy')
      
      // 构建资金追踪策略参数（简化版）
      const fundFlowParams = {
        market_cap: 'all',
        stock_pool: 'all', 
        limit: 20,
        margin_buy_trend_min: customSettings?.parameters?.margin_buy_trend_min || 50,
        margin_balance_growth_min: customSettings?.parameters?.margin_balance_growth_min || 50
      }
      
      // console.log('资金追踪策略参数:', fundFlowParams)
      const response = await fundFlowTrackingScreening(fundFlowParams)
      
      if (response.data) {
        const screeningResponse = response.data
        results = screeningResponse.results || []
      }
    } else {
      // 其他策略使用模板方式
      const requestData = {
        template_id: selectedTemplate.value,
        custom_parameters: customSettings?.parameters || {},
        custom_weights: customSettings?.weights || {}
      }
      
      // console.log('开始筛选，参数:', requestData)
      
      // 模板筛选 - 传递自定义参数
      const response = await applyStrategyTemplate(selectedTemplate.value, requestData)
      
      // 后端返回ScreeningResponse对象，包装在ApiResponse.data中
      if (response.data) {
        const screeningResponse = response.data
        results = screeningResponse.results || []
      } else {
        results = []
      }
    }
    
    screeningResults.value = results
    ElMessage.success(`筛选完成，找到 ${results.length} 只股票`)
  } catch (error: any) {
    console.error('筛选失败:', error)
    ElMessage.error(error.message || '筛选失败，请重试')
  } finally {
    isScreening.value = false
  }
}

// 获取策略简介
const getStrategyBrief = (strategyType: string): string => {
  const briefMap: Record<string, string> = {
    'value': '基于巴菲特价值投资理念，寻找低估值高ROE的优质股票',
    'growth': '严格量化筛选高质量成长股：EPS增长>25%，ROIC>10%，PEG<1',
    'momentum': '捕捉技术突破信号，追踪市场动量趋势',
    'dividend': '筛选高股息率股票，支持分红募资比、净现金等多维度指标',
    'technical': '基于技术指标分析，识别买卖时机',
    'oversold': '基于多维度超跌识别和反弹确认，寻找深度调整后的反弹机会',
    'limit_up': '基于真实涨跌停数据的连板龙头选股，识别强势板块龙头机会',
    'fund_flow': '基于融资融券核心数据追踪主力资金动向，聚焦融资买入趋势和余额增长双核心指标'
  }
  return briefMap[strategyType] || '智能选股策略'
}

// 显示策略详情
const showStrategyDetail = (template: any) => {
  currentDetailTemplate.value = template
  showDetailModal.value = true
}

// 保存策略设置
const saveStrategySettings = (templateId: string, settings: any) => {
  strategySettings.value[templateId] = settings
  // 可以选择将设置保存到 localStorage 或发送到后端
  localStorage.setItem('strategySettings', JSON.stringify(strategySettings.value))
  // console.log('策略设置已保存:', templateId, settings)
}

const selectTemplate = (template: any) => {
  selectedTemplate.value = template.id
  // 清空之前的筛选结果，避免数据结构不匹配
  screeningResults.value = []
  // 重置分页
  currentPage.value = 1
  // console.log(`[策略选股] 选择策略模板: ${template.name} (${template.strategy_type})`)
  ElMessage.success(`已选择 ${template.name} 模板`)
}

const exportResults = async () => {
  if (screeningResults.value.length === 0) {
    ElMessage.warning('没有可导出的数据')
    return
  }
  
  try {
    const response = await exportScreeningResults(screeningResults.value, 'excel')
    const blob = response.data
    if (blob) {
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `策略筛选结果_${new Date().toISOString().split('T')[0]}.xlsx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      ElMessage.success('导出成功')
    } else {
      ElMessage.error('导出数据为空')
    }
  } catch (error: any) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败，请重试')
  }
}

// 转换筛选结果为股票信息格式
const convertToStockInfo = (result: ScreeningResult): StockInfo => {
  return {
    ts_code: result.ts_code,
    name: result.name,
    industry: result.industry || '',
    market: result.ts_code.endsWith('.SH') ? '上海' : (result.ts_code.endsWith('.SZ') ? '深圳' : ''),
    add_time: new Date(),
    add_reason: '策略选股添加',
    tags: ['策略选股']
  }
}

// 批量加入股票池
const addAllToPool = () => {
  if (!authStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    return
  }
  
  if (screeningResults.value.length === 0) {
    ElMessage.warning('没有可添加的股票')
    return
  }
  
  // 转换所有筛选结果为股票信息格式
  selectedStocksForPool.value = screeningResults.value.map(convertToStockInfo)
  showStockPoolDialog.value = true
}

// 单个股票加入股票池
const addSingleStockToPool = (row: ScreeningResult) => {
  if (!authStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    return
  }
  
  // 转换单个筛选结果为股票信息格式
  selectedStocksForPool.value = [convertToStockInfo(row)]
  showStockPoolDialog.value = true
}

// 股票池对话框确认回调
const handleStockPoolConfirmed = (data: any) => {
  ElMessage.success(`成功添加 ${data.stocks.length} 只股票到 ${data.pools.length} 个股票池`)
  
  // 刷新股票池管理器
  if (stockPoolManagerRef.value) {
    stockPoolManagerRef.value.refreshPools()
  }
}

// 股票池管理器事件处理
const handlePoolCreated = (pool: StockPool) => {
  // console.log('股票池已创建:', pool.pool_name)
}

const handlePoolUpdated = (pool: StockPool) => {
  // console.log('股票池已更新:', pool.pool_name)
}

const handlePoolDeleted = (poolId: string) => {
  // console.log('股票池已删除:', poolId)
}

const handleStockAdded = (data: { pools: StockPool[], stocks: StockInfo[] }) => {
  // console.log('股票已添加:', data.pools.length, '个股票池,', data.stocks.length, '只股票')
}

// 股票池对话框取消回调
const handleStockPoolCanceled = () => {
  selectedStocksForPool.value = []
}

// 格式化方法
const formatChange = (pctChg: number | undefined): string => {
  if (pctChg === undefined || pctChg === null) return '--'
  const sign = pctChg > 0 ? '+' : ''
  return `${sign}${pctChg.toFixed(2)}%`
}

const getChangeClass = (pctChg: number | undefined): string => {
  if (pctChg === undefined || pctChg === null) return ''
  if (pctChg > 0) return 'text-red'
  if (pctChg < 0) return 'text-green'
  return ''
}

const formatPE = (pe: number | undefined): string => {
  if (pe === undefined || pe === null || pe <= 0) return '--'
  if (pe > 1000) return '1000+'
  return pe.toFixed(1)
}

const formatPB = (pb: number | undefined): string => {
  if (pb === undefined || pb === null || pb <= 0) return '--'
  return pb.toFixed(2)
}

const formatMarketCap = (totalMv: number | undefined): string => {
  if (totalMv === undefined || totalMv === null || totalMv <= 0) return '--'
  const billion = totalMv / 10000
  if (billion >= 1000) {
    return `${(billion / 1000).toFixed(1)}万亿`
  } else if (billion >= 1) {
    return `${billion.toFixed(0)}亿`
  } else {
    return `${totalMv.toFixed(0)}万`
  }
}

const formatScore = (score: number | undefined): string => {
  if (score === undefined || score === null) return '--'
  return score.toFixed(1)
}

// 分页和排序事件处理
const handleSortChange = (sortInfo: { prop: string; order: string | null }) => {
  sortConfig.value = {
    prop: sortInfo.prop || 'score',
    order: sortInfo.order || 'descending'
  }
  currentPage.value = 1 // 排序后回到第一页
}

const handleSizeChange = (newSize: number) => {
  pageSize.value = newSize
  currentPage.value = 1 // 改变页面大小后回到第一页
}

const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
}


onMounted(async () => {
  // 初始化认证状态
  authStore.initAuth()
  
  // 加载已保存的策略设置
  const savedSettings = localStorage.getItem('strategySettings')
  if (savedSettings) {
    try {
      strategySettings.value = JSON.parse(savedSettings)
    } catch (error) {
      console.error('加载策略设置失败:', error)
    }
  }
  
  // 初始化高股息策略默认参数（如果没有保存的设置）
  const dividendTemplateId = '686a71f4c51f290dcebb0742'
  if (!strategySettings.value[dividendTemplateId]) {
    strategySettings.value[dividendTemplateId] = {
      parameters: {
        dividend_yield_min: 2.0,
        payout_ratio_min: 20.0,
        dividend_fundraising_ratio_min: 30.0,
        net_cash_min: -1000000.0,
        roe_min: 0,
        debt_ratio_max: 80,
        net_profit_margin_min: 0,
        market_cap_min: 10
      },
      weights: {}
    }
  }
  
  // 初始化技术突破策略默认参数（如果没有保存的设置）
  const technicalTemplateId = '686a347c09e24f7707f7b4da'
  if (!strategySettings.value[technicalTemplateId]) {
    strategySettings.value[technicalTemplateId] = {
      parameters: {
        rsi_min: 45.0,
        rsi_max: 85.0,
        volume_ratio_min: 1.2,
        macd_requirement: false,
        ma_alignment: false,
        bollinger_position: 'upper'
      },
      weights: {}
    }
  }
  
})
</script>

<style scoped>
.strategy-screening-page {
  padding: var(--spacing-lg);
  min-height: 100%;
  background: var(--bg-primary);
}

.page-header {
  margin-bottom: var(--spacing-lg);
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.page-title svg {
  width: 24px !important;
  height: 24px !important;
  flex-shrink: 0;
}

.page-title .icon-size {
  width: 24px !important;
  height: 24px !important;
  font-size: 24px !important;
}

.page-subtitle {
  color: var(--text-secondary);
  font-size: 16px;
  margin: 0;
}

.screening-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  width: 100%;
}

.stock-pool-section {
  width: 100%;
}

.stock-pool-card {
  background: var(--gradient-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.header-icon {
  width: 18px;
  height: 18px;
  color: var(--accent-primary);
}

.results-section {
  width: 100%;
  flex: 1;
}

.form-card,
.results-card {
  background: var(--gradient-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.card-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}



.template-section {
  padding: var(--spacing-md);
}

.template-grid {
  width: 100%;
  margin: 0;
}

.template-col {
  margin-bottom: var(--spacing-md);
  display: flex;
  height: 100%;
}

.template-col .el-card {
  width: 100%;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--spacing-lg);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding-bottom: var(--spacing-sm);
  border-bottom: 2px solid var(--border-primary);
  position: relative;
}

.section-title svg {
  width: 18px !important;
  height: 18px !important;
  flex-shrink: 0;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, var(--accent-primary), var(--neon-blue));
  border-radius: 1px;
}

.section-icon {
  color: var(--accent-primary);
  width: 18px !important;
  height: 18px !important;
  font-size: 18px !important;
  filter: drop-shadow(0 0 4px rgba(0, 255, 255, 0.4));
}

.template-count {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 4px 12px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-primary);
  margin-left: auto;
}

.template-card {
  transition: all var(--transition-base);
  border: 2px solid transparent;
  position: relative;
  background: var(--gradient-secondary);
  border-radius: var(--radius-lg);
  height: 380px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.template-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 255, 255, 0.15);
  border-color: rgba(0, 255, 255, 0.3);
}

.template-card.active {
  border-color: var(--accent-primary);
  box-shadow: 0 8px 30px rgba(0, 255, 255, 0.25);
  background: linear-gradient(135deg, rgba(0, 255, 255, 0.05), rgba(255, 0, 255, 0.05));
}

.template-content {
  text-align: center;
  padding: var(--spacing-lg);
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  flex: 1;
  cursor: pointer;
  transition: all var(--transition-base);
}

/* 选择状态圆圈样式 */
.selection-indicator {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 10;
}

.selection-circle {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-primary);
  border-radius: 50%;
  background: var(--bg-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-base);
  cursor: pointer;
}

.selection-circle.selected {
  border-color: var(--accent-primary);
  background: var(--accent-primary);
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}

.selection-dot {
  width: 8px;
  height: 8px;
  background: white;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.template-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: var(--spacing-md);
  color: var(--accent-primary);
  transition: all var(--transition-base);
  flex-shrink: 0;
  height: 40px;
}

.template-icon svg {
  width: 20px !important;
  height: 20px !important;
}

.template-card:hover .template-icon {
  transform: scale(1.05);
  color: var(--neon-blue);
}

.template-card:hover .template-icon svg {
  transform: scale(1.1);
}

.template-card.active .template-icon {
  color: var(--accent-primary);
  filter: drop-shadow(0 0 8px rgba(0, 255, 255, 0.6));
}

.template-card.active .template-icon svg {
  filter: drop-shadow(0 0 4px rgba(0, 255, 255, 0.4));
}

.template-name {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: var(--spacing-sm);
  color: var(--text-primary);
  transition: color var(--transition-base);
  flex-shrink: 0;
  line-height: 1.3;
}

.template-card:hover .template-name {
  color: var(--accent-primary);
}

.template-card.active .template-name {
  color: var(--accent-primary);
  text-shadow: 0 0 8px rgba(0, 255, 255, 0.3);
}

.template-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
  transition: color var(--transition-base);
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
}

.template-card:hover .template-description {
  color: var(--text-primary);
}

.template-card.active .template-description {
  color: var(--text-primary);
}

/* 策略简介样式 */
.strategy-brief {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--border-primary);
  height: 50px;
  overflow: hidden;
}

.brief-text {
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.4;
  font-style: italic;
  opacity: 0.8;
  height: 100%;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 卡片操作区域样式 */
.card-actions {
  padding: var(--spacing-md);
  background: var(--bg-primary);
  border-top: 1px solid var(--border-primary);
  display: flex;
  gap: var(--spacing-sm);
  justify-content: space-between;
  height: 64px;
  align-items: center;
  flex-shrink: 0;
  margin-top: auto;
}

.detail-btn,
.select-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-height: 32px;
}

.btn-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.detail-btn {
  background: transparent;
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.detail-btn:hover {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: white;
}

.select-btn.el-button--success {
  background: var(--neon-green);
  border-color: var(--neon-green);
  color: white;
}

.loading-container,
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.results-table-container {
  overflow-x: auto;
  width: 100%;
}

/* 新增的表格样式 */
.table-wrapper {
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  width: 100%;
}

.modern-table {
  width: 100%;
  font-size: 14px;
  table-layout: auto;
}

/* 表格单元格样式 */
.code-cell {
  display: flex;
  align-items: center;
}


.name-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stock-main-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stock-title {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stock-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.stock-code {
  font-family: 'Consolas', 'Monaco', monospace;
  font-weight: 500;
  color: var(--text-secondary);
  font-size: 12px;
}

.industry-tag {
  font-size: 11px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 2px 6px;
  border-radius: 4px;
  max-width: fit-content;
  display: inline-block;
}

.price-cell {
  display: flex;
  align-items: center;
}

.price {
  font-weight: 600;
  font-family: 'Consolas', 'Monaco', monospace;
}

.change-cell {
  display: flex;
  align-items: center;
}

.pe-value,
.pb-value {
  font-family: 'Consolas', 'Monaco', monospace;
  font-weight: 500;
}

.market-cap-cell {
  display: flex;
  align-items: center;
}

.market-cap {
  font-weight: 500;
  font-size: 13px;
}

.score-cell {
  display: flex;
  align-items: center;
}

.score-display {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}

.score-number {
  font-weight: 700;
  color: var(--accent-primary);
  font-size: 14px;
  text-align: center;
}

.score-bar {
  width: 100%;
  height: 6px;
  background: var(--bg-secondary);
  border-radius: 3px;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--neon-green), var(--neon-blue), var(--accent-primary));
  border-radius: 3px;
  transition: width var(--transition-base);
}

.action-cell {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 分页样式 */
.pagination-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--spacing-lg) 0;
  background: var(--bg-primary);
  border-top: 1px solid var(--border-primary);
}

/* 涨跌幅颜色 */
.text-red {
  color: var(--neon-pink);
  font-weight: 600;
}

.text-green {
  color: var(--neon-green);
  font-weight: 600;
}

/* 确保所有SVG图标都有合适的尺寸 */
svg {
  flex-shrink: 0;
}

/* Element Plus 表格深度样式 */
:deep(.el-table) {
  background: transparent;
  border: none;
  width: 100%;
  table-layout: auto;
}

:deep(.el-table th) {
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-weight: 600;
  border: none;
  padding: 12px 8px;
  white-space: nowrap;
}

:deep(.el-table td) {
  border: none;
  padding: 12px 8px;
  overflow: hidden;
  text-overflow: ellipsis;
}

:deep(.el-table tr) {
  background: transparent;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: var(--bg-secondary);
}

:deep(.el-table__body tr:hover td) {
  background: var(--bg-hover) !important;
}

:deep(.el-table th.is-sortable) {
  cursor: pointer;
}

:deep(.el-table th.is-sortable:hover) {
  background: var(--bg-hover);
}

/* 分页组件样式 */
:deep(.el-pagination) {
  --el-pagination-bg-color: var(--bg-primary);
  --el-pagination-text-color: var(--text-primary);
  --el-pagination-border-radius: var(--radius-md);
}

:deep(.el-pagination .el-pager li) {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-primary);
  margin: 0 2px;
  border-radius: var(--radius-sm);
}

:deep(.el-pagination .el-pager li.is-active) {
  background: var(--accent-primary);
  color: white;
  border-color: var(--accent-primary);
}

:deep(.el-pagination .el-pager li:hover) {
  background: var(--bg-hover);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .results-table-container {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  
  .modern-table {
    min-width: 900px;
  }
  
  .action-cell {
    flex-direction: column;
    gap: 4px;
  }
  
  .action-cell .el-button {
    font-size: 12px;
    padding: 4px 8px;
  }
}

@media (max-width: 768px) {
  .strategy-screening-page {
    padding: var(--spacing-md);
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .template-col {
    margin-bottom: var(--spacing-md);
  }
  
  .template-card {
    height: 340px;
  }
  
  .template-content {
    padding: var(--spacing-md);
  }
  
  .template-icon {
    height: 35px;
  }
  
  .template-icon svg {
    width: 18px !important;
    height: 18px !important;
  }
  
  .template-name {
    font-size: 16px;
  }
  
  .template-description {
    font-size: 13px;
    height: 50px;
  }
  
  .strategy-brief {
    height: 40px;
  }
  
  .results-table-container {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    width: 100%;
  }
  
  .modern-table {
    min-width: 700px;
  }
  
  .pagination-container {
    padding: var(--spacing-md) 0;
  }
  
  :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  :deep(.el-pagination .el-pagination__sizes) {
    margin-bottom: var(--spacing-sm);
  }
}

@media (max-width: 480px) {
  .card-header-content {
    flex-direction: column;
    gap: var(--spacing-sm);
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .template-section {
    padding: var(--spacing-sm);
  }
  
  .template-grid .el-row {
    margin: 0 -10px;
  }
  
  .template-col {
    padding: 0 10px;
    margin-bottom: var(--spacing-sm);
  }
  
  .template-card {
    height: 300px;
  }
  
  .template-content {
    padding: var(--spacing-sm);
  }
  
  .template-icon {
    height: 30px;
    margin-bottom: var(--spacing-sm);
  }
  
  .template-icon svg {
    width: 16px !important;
    height: 16px !important;
  }
  
  .template-name {
    font-size: 15px;
    margin-bottom: 6px;
  }
  
  .template-description {
    font-size: 12px;
    height: 45px;
    line-height: 1.4;
  }
  
  .strategy-brief {
    height: 35px;
  }
  
  .action-cell .el-button {
    font-size: 11px;
    padding: 3px 6px;
  }
  
  .score-display {
    gap: 2px;
  }
  
  .score-bar {
    height: 4px;
  }
}

/* 中等屏幕优化 */
@media (min-width: 992px) and (max-width: 1199px) {
  .template-card {
    height: 360px;
  }
  
  .template-content {
    padding: var(--spacing-lg);
  }
  
  .template-name {
    font-size: 17px;
  }
  
  .template-description {
    font-size: 14px;
    height: 65px;
  }
  
  .strategy-brief {
    height: 45px;
  }
}

/* 更大屏幕的自适应 */
@media (min-width: 1400px) {
  .template-card {
    height: 400px;
  }
  
  .template-content {
    padding: calc(var(--spacing-lg) + 4px);
  }
  
  .template-icon {
    height: 45px;
  }
  
  .template-icon svg {
    width: 24px !important;
    height: 24px !important;
  }
  
  .template-name {
    font-size: 19px;
  }
  
  .template-description {
    font-size: 15px;
    height: 70px;
  }
  
  .strategy-brief {
    height: 55px;
  }
  
  .modern-table {
    font-size: 15px;
  }
  
  :deep(.el-table th) {
    padding: 14px 12px;
  }
  
  :deep(.el-table td) {
    padding: 14px 12px;
  }
}

/* 表格列宽度优化 */
:deep(.el-table__header-wrapper) {
  width: 100%;
}

:deep(.el-table__body-wrapper) {
  width: 100%;
}

/* 确保表格能够完全利用可用空间 */
:deep(.el-table-column) {
  flex: 1;
  min-width: 0;
}

/* 固定列的特殊处理 */
:deep(.el-table__fixed-right) {
  right: 0;
}

:deep(.el-table__fixed) {
  left: 0;
}
</style>