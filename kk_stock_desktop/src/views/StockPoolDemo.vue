<template>
  <div class="stock-pool-demo-page">
    <div class="page-header">
      <h1 class="page-title">
        <component :is="CubeIcon" class="icon-size" />
        股票池管理系统演示
      </h1>
      <p class="page-subtitle">独立可复用的股票池管理组件，支持完整的CRUD操作和批量股票添加</p>
    </div>

    <div class="demo-container">
      <!-- 功能演示区域 -->
      <div class="demo-section">
        <el-card class="demo-card">
          <template #header>
            <div class="card-header">
              <span>功能演示</span>
              <div class="demo-actions">
                <el-button 
                  type="primary" 
                  @click="openStockPoolManager"
                  :icon="CubeIcon"
                >
                  打开股票池管理器
                </el-button>
                <el-button 
                  type="success" 
                  @click="openStockPoolSelector"
                  :icon="CheckIcon"
                >
                  打开多选对话框
                </el-button>
                <el-button 
                  type="info" 
                  @click="openStockSearchDialog"
                  :icon="MagnifyingGlassIcon"
                >
                  打开股票搜索
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="demo-content">
            <div class="feature-grid">
              <div class="feature-item">
                <div class="feature-icon">
                  <component :is="CubeIcon" />
                </div>
                <h3>股票池管理器</h3>
                <p>完整的股票池CRUD操作，支持管理/选择/查看三种模式</p>
                <ul>
                  <li>创建、编辑、删除股票池</li>
                  <li>查看股票池详情和统计</li>
                  <li>股票池类型管理（默认/自定义/策略）</li>
                  <li>权限控制（默认池不可删除）</li>
                </ul>
              </div>
              
              <div class="feature-item">
                <div class="feature-icon">
                  <component :is="CheckIcon" />
                </div>
                <h3>多选对话框</h3>
                <p>策略选股结果批量添加到多个股票池</p>
                <ul>
                  <li>多股票池选择</li>
                  <li>批量股票添加</li>
                  <li>快速创建新股票池</li>
                  <li>添加结果反馈</li>
                </ul>
              </div>
              
              <div class="feature-item">
                <div class="feature-icon">
                  <component :is="MagnifyingGlassIcon" />
                </div>
                <h3>股票搜索</h3>
                <p>智能股票搜索和批量添加功能</p>
                <ul>
                  <li>实时股票代码/名称搜索</li>
                  <li>多股票选择</li>
                  <li>目标股票池选择</li>
                  <li>批量添加操作</li>
                </ul>
              </div>
            </div>
          </div>
        </el-card>
      </div>
      
      <!-- 组件示例区域 -->
      <div class="example-section">
        <el-card class="example-card">
          <template #header>
            <div class="card-header">
              <span>组件实例演示</span>
              <div class="mode-switcher">
                <el-radio-group v-model="currentMode" @change="handleModeChange">
                  <el-radio-button value="manager">管理模式</el-radio-button>
                  <el-radio-button value="selector">选择模式</el-radio-button>
                  <el-radio-button value="viewer">查看模式</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          
          <!-- 股票池管理器实例 -->
          <StockPoolManager
            :key="currentMode"
            :mode="currentMode"
            :show-actions="currentMode !== 'viewer'"
            :allow-multi-select="currentMode === 'selector'"
            @pools-selected="handlePoolsSelected"
            @pool-created="handlePoolCreated"
            @pool-updated="handlePoolUpdated"
            @pool-deleted="handlePoolDeleted"
            @stock-added="handleStockAdded"
          />
        </el-card>
      </div>
      
      <!-- 事件日志区域 -->
      <div class="log-section">
        <el-card class="log-card">
          <template #header>
            <div class="card-header">
              <span>事件日志</span>
              <el-button size="small" @click="clearLogs">清空日志</el-button>
            </div>
          </template>
          
          <div class="log-content">
            <div v-if="eventLogs.length === 0" class="empty-logs">
              <el-empty description="暂无事件日志" />
            </div>
            <div v-else class="log-list">
              <div 
                v-for="(log, index) in eventLogs" 
                :key="index"
                class="log-item"
                :class="log.type"
              >
                <div class="log-time">{{ formatTime(log.timestamp) }}</div>
                <div class="log-type">{{ log.type.toUpperCase() }}</div>
                <div class="log-message">{{ log.message }}</div>
                <div v-if="log.data" class="log-data">
                  <pre>{{ JSON.stringify(log.data, null, 2) }}</pre>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
    
    <!-- 独立对话框演示 -->
    <StockPoolSelectDialog
      v-model="showSelectDialog"
      :pre-selected-stocks="demoStocks"
      @confirmed="handleSelectConfirmed"
      @canceled="handleSelectCanceled"
    />
    
    <StockSearchDialog
      v-model="showSearchDialog"
      @added="handleSearchAdded"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  CubeIcon, 
  CheckIcon, 
  MagnifyingGlassIcon 
} from '@heroicons/vue/24/outline'

import StockPoolManager from '@/components/StockPool/StockPoolManager.vue'
import StockPoolSelectDialog from '@/components/StockPool/StockPoolSelectDialog.vue'
import StockSearchDialog from '@/components/StockPool/StockSearchDialog.vue'
import { type StockPool, type StockInfo } from '@/services/stockPoolService'

// 响应式数据
const currentMode = ref<'manager' | 'selector' | 'viewer'>('manager')
const showSelectDialog = ref(false)
const showSearchDialog = ref(false)
const eventLogs = ref<Array<{
  timestamp: Date
  type: 'info' | 'success' | 'warning' | 'error'
  message: string
  data?: any
}>>([])

// 演示数据
const demoStocks = ref<StockInfo[]>([
  {
    ts_code: '000001.SZ',
    name: '平安银行',
    industry: '银行',
    market: '深圳',
    add_time: new Date(),
    add_reason: '演示添加',
    tags: ['演示', '银行股']
  },
  {
    ts_code: '600036.SH',
    name: '招商银行',
    industry: '银行',
    market: '上海',
    add_time: new Date(),
    add_reason: '演示添加',
    tags: ['演示', '银行股']
  },
  {
    ts_code: '000858.SZ',
    name: '五粮液',
    industry: '酿酒行业',
    market: '深圳',
    add_time: new Date(),
    add_reason: '演示添加',
    tags: ['演示', '白酒股']
  }
])

// 方法
const addLog = (type: 'info' | 'success' | 'warning' | 'error', message: string, data?: any) => {
  eventLogs.value.unshift({
    timestamp: new Date(),
    type,
    message,
    data
  })
  
  // 限制日志数量
  if (eventLogs.value.length > 50) {
    eventLogs.value = eventLogs.value.slice(0, 50)
  }
}

const clearLogs = () => {
  eventLogs.value = []
  ElMessage.success('日志已清空')
}

const formatTime = (date: Date): string => {
  return date.toLocaleTimeString('zh-CN')
}

const handleModeChange = (mode: string) => {
  addLog('info', `切换到${mode}模式`, { mode })
}

const openStockPoolManager = () => {
  currentMode.value = 'manager'
  addLog('info', '打开股票池管理器')
}

const openStockPoolSelector = () => {
  showSelectDialog.value = true
  addLog('info', '打开股票池多选对话框', { stocksCount: demoStocks.value.length })
}

const openStockSearchDialog = () => {
  showSearchDialog.value = true
  addLog('info', '打开股票搜索对话框')
}

// 事件处理
const handlePoolsSelected = (pools: StockPool[]) => {
  addLog('success', `选择了${pools.length}个股票池`, {
    pools: pools.map(p => ({ id: p.pool_id, name: p.pool_name }))
  })
}

const handlePoolCreated = (pool: StockPool) => {
  addLog('success', `创建了股票池: ${pool.pool_name}`, {
    poolId: pool.pool_id,
    poolType: pool.pool_type
  })
}

const handlePoolUpdated = (pool: StockPool) => {
  addLog('success', `更新了股票池: ${pool.pool_name}`, {
    poolId: pool.pool_id,
    stockCount: pool.stock_count
  })
}

const handlePoolDeleted = (poolId: string) => {
  addLog('warning', `删除了股票池: ${poolId}`, { poolId })
}

const handleStockAdded = (data: { pools: StockPool[], stocks: StockInfo[] }) => {
  addLog('success', `添加了${data.stocks.length}只股票到${data.pools.length}个股票池`, {
    poolsCount: data.pools.length,
    stocksCount: data.stocks.length
  })
}

const handleSelectConfirmed = (data: any) => {
  addLog('success', '股票池选择对话框确认', {
    poolsCount: data.pools.length,
    stocksCount: data.stocks.length,
    totalAdded: data.result.total_added
  })
}

const handleSelectCanceled = () => {
  addLog('info', '股票池选择对话框取消')
}

const handleSearchAdded = (data: { pools: StockPool[], stocks: StockInfo[] }) => {
  addLog('success', `通过搜索添加了${data.stocks.length}只股票到${data.pools.length}个股票池`, {
    poolsCount: data.pools.length,
    stocksCount: data.stocks.length
  })
}

// 初始化日志
addLog('info', '股票池管理系统演示页面已加载')
</script>

<style scoped>
.stock-pool-demo-page {
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

.page-title .icon-size {
  width: 24px;
  height: 24px;
}

.page-subtitle {
  color: var(--text-secondary);
  font-size: 16px;
  margin: 0;
}

.demo-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.demo-card,
.example-card,
.log-card {
  background: var(--gradient-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: var(--text-primary);
}

.demo-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.demo-content {
  padding: var(--spacing-md);
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-lg);
}

.feature-item {
  background: var(--bg-secondary);
  padding: var(--spacing-lg);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-primary);
  text-align: center;
  transition: all var(--transition-base);
}

.feature-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.15);
  border-color: var(--accent-primary);
}

.feature-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 60px;
  height: 60px;
  margin: 0 auto var(--spacing-md);
  background: var(--accent-primary-alpha);
  border-radius: var(--radius-full);
  color: var(--accent-primary);
}

.feature-icon svg {
  width: 30px;
  height: 30px;
}

.feature-item h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.feature-item p {
  color: var(--text-secondary);
  margin-bottom: var(--spacing-md);
  line-height: 1.5;
}

.feature-item ul {
  text-align: left;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.feature-item li {
  margin-bottom: 4px;
}

.mode-switcher {
  display: flex;
  align-items: center;
}

.log-content {
  max-height: 400px;
  overflow-y: auto;
}

.empty-logs {
  padding: var(--spacing-lg);
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.log-item {
  display: grid;
  grid-template-columns: auto auto 1fr;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  border-left: 4px solid transparent;
  font-size: 14px;
  align-items: start;
}

.log-item.info {
  border-left-color: var(--accent-primary);
}

.log-item.success {
  border-left-color: var(--neon-green);
}

.log-item.warning {
  border-left-color: #f39c12;
}

.log-item.error {
  border-left-color: var(--neon-pink);
}

.log-time {
  font-family: monospace;
  color: var(--text-tertiary);
  font-size: 12px;
}

.log-type {
  font-weight: 600;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  color: white;
}

.log-item.info .log-type {
  background: var(--accent-primary);
}

.log-item.success .log-type {
  background: var(--neon-green);
}

.log-item.warning .log-type {
  background: #f39c12;
}

.log-item.error .log-type {
  background: var(--neon-pink);
}

.log-message {
  color: var(--text-primary);
  word-break: break-word;
}

.log-data {
  grid-column: 1 / -1;
  margin-top: var(--spacing-xs);
}

.log-data pre {
  background: var(--bg-primary);
  padding: var(--spacing-xs);
  border-radius: var(--radius-sm);
  font-size: 11px;
  color: var(--text-secondary);
  overflow-x: auto;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stock-pool-demo-page {
    padding: var(--spacing-md);
  }
  
  .card-header {
    flex-direction: column;
    gap: var(--spacing-sm);
    align-items: flex-start;
  }
  
  .demo-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .feature-grid {
    grid-template-columns: 1fr;
  }
  
  .log-item {
    grid-template-columns: 1fr;
    gap: var(--spacing-xs);
  }
  
  .log-data {
    grid-column: 1;
  }
}
</style>