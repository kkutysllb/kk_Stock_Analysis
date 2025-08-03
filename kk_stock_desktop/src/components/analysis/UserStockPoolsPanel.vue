<template>
  <div class="stock-pools-panel glass-effect">
    <!-- 面板标题 -->
    <div class="panel-header">
      <div class="panel-title">
        <FolderIcon class="title-icon" />
        <span>我的股票池</span>
        <el-badge :value="totalStocks" :max="999" class="stock-count-badge" />
      </div>
      <div class="panel-actions">
        <el-tooltip content="创建新股票池" placement="top">
          <el-button type="primary" size="small" @click="showCreateModal">
            <PlusIcon class="action-icon" />
          </el-button>
        </el-tooltip>
        <el-tooltip content="刷新数据" placement="top">
          <el-button size="small" @click="refreshData" :loading="loading">
            <ArrowPathIcon class="action-icon" />
          </el-button>
        </el-tooltip>
      </div>
    </div>

    <!-- 股票池列表 -->
    <div class="panel-content">
      <div v-if="loading && stockPools.length === 0" class="loading-state">
        <el-skeleton :rows="3" animated />
      </div>
      
      <div v-else-if="stockPools.length === 0" class="empty-state">
        <FolderIcon class="empty-icon" />
        <p class="empty-text">暂无股票池</p>
        <el-button type="primary" @click="showCreateModal">
          <PlusIcon class="btn-icon" />
          创建第一个股票池
        </el-button>
      </div>

      <div v-else class="pools-list">
        <div 
          v-for="pool in stockPools"
          :key="pool.pool_id"
          class="pool-card"
          :class="{ active: selectedPoolId === pool.pool_id }"
          @click="selectPool(pool)"
        >
          <div class="pool-header">
            <div class="pool-info">
              <h4 class="pool-name">{{ pool.pool_name }}</h4>
              <p class="pool-description">{{ pool.description || '暂无描述' }}</p>
            </div>
            <div class="pool-meta">
              <el-badge :value="pool.stocks?.length || 0" :max="99" class="stock-badge" />
              <el-dropdown trigger="click" @command="handlePoolAction">
                <el-button size="small" type="link">
                  <EllipsisVerticalIcon class="action-icon" />
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="{ action: 'edit', poolId: pool.pool_id }">
                      <PencilIcon class="menu-icon" />
                      编辑
                    </el-dropdown-item>
                    <el-dropdown-item :command="{ action: 'delete', poolId: pool.pool_id }">
                      <TrashIcon class="menu-icon danger" />
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>

          <!-- 股票列表 -->
          <div v-if="pool.stocks && pool.stocks.length > 0" class="stocks-list">
            <div 
              v-for="stock in pool.stocks.slice(0, showAllStocks[pool.pool_id] ? undefined : 5)"
              :key="stock.ts_code"
              class="stock-item"
              :class="{ selected: selectedStock?.code === stock.ts_code }"
              @click.stop="selectStock(stock, pool.pool_id)"
            >
              <div class="stock-info">
                <span class="stock-code">{{ stock.ts_code }}</span>
                <span class="stock-name">{{ stock.name }}</span>
              </div>
              <div class="stock-meta">
                <span v-if="stock.industry" class="stock-industry">{{ stock.industry }}</span>
                <span class="stock-market">{{ stock.market || 'N/A' }}</span>
              </div>
            </div>
            
            <!-- 展开/收起按钮 -->
            <div v-if="pool.stocks.length > 5" class="expand-button">
              <el-button 
                size="small" 
                type="link" 
                @click.stop="toggleShowAllStocks(pool.pool_id)"
              >
                {{ showAllStocks[pool.pool_id] ? '收起' : `展开更多 (${pool.stocks.length - 5})` }}
                <ChevronDownIcon 
                  class="expand-icon" 
                  :class="{ rotated: showAllStocks[pool.pool_id] }" 
                />
              </el-button>
            </div>
          </div>

          <div v-else class="empty-pool">
            <p class="empty-pool-text">该股票池暂无股票</p>
            <el-button size="small" @click.stop="showAddStockModal(pool.pool_id)">
              <PlusIcon class="btn-icon" />
              添加股票
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建股票池弹窗 -->
    <CreatePoolModal 
      v-model="createModalVisible"
      @pool-created="onPoolCreated"
    />

    <!-- 编辑股票池弹窗 -->
    <EditPoolModal 
      v-model="editModalVisible"
      :poolData="editingPool"
      @pool-updated="onPoolUpdated"
    />

    <!-- 添加股票弹窗 -->
    <AddStockModal 
      v-model="addStockModalVisible"
      :poolId="targetPoolId"
      @stocks-added="onStocksAdded"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, defineEmits, defineExpose } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  FolderIcon, 
  PlusIcon, 
  ArrowPathIcon,
  EllipsisVerticalIcon,
  PencilIcon,
  TrashIcon,
  ChevronDownIcon
} from '@heroicons/vue/24/outline'

// 导入组件
import CreatePoolModal from './CreatePoolModal.vue'
import EditPoolModal from './EditPoolModal.vue'
import AddStockModal from './AddStockModal.vue'

// 导入API
import { useUserStockPoolsStore } from '@/stores/userStockPools'
import type { StockPool as ApiStockPool, StockInfo } from '@/api/userStockPools'

// 类型定义 - 使用API的类型定义
type StockPool = ApiStockPool

interface SelectedStock {
  code: string
  name: string
  poolId?: string
}

// Emits
const emit = defineEmits<{
  stockSelected: [stock: SelectedStock]
  poolsUpdated: [pools: StockPool[]]
}>()

// Store
const stockPoolsStore = useUserStockPoolsStore()

// 响应式数据
const loading = computed(() => stockPoolsStore.loading)
const stockPools = computed(() => stockPoolsStore.stockPools)
const selectedPoolId = ref<string | null>(null)
const selectedStock = ref<SelectedStock | null>(null)
const showAllStocks = reactive<Record<string, boolean>>({})

// 弹窗状态
const createModalVisible = ref(false)
const editModalVisible = ref(false)
const addStockModalVisible = ref(false)
const editingPool = ref<StockPool | null>(null)
const targetPoolId = ref<string | null>(null)

// 计算属性
const totalStocks = computed(() => {
  return stockPools.value.reduce((total, pool) => total + (pool.stocks?.length || 0), 0)
})

// 方法
const refreshData = async () => {
  try {
    await stockPoolsStore.fetchStockPools()
    emit('poolsUpdated', stockPools.value)
    console.log('股票池数据刷新成功:', stockPools.value)
  } catch (error) {
    console.error('刷新股票池数据失败:', error)
    ElMessage.error('刷新数据失败')
  }
}

const selectPool = (pool: StockPool) => {
  selectedPoolId.value = pool.pool_id
  console.log('选中股票池:', pool)
}

const selectStock = (stock: StockInfo, poolId: string) => {
  const selectedStockData: SelectedStock = {
    code: stock.ts_code,
    name: stock.name,
    poolId
  }
  selectedStock.value = selectedStockData
  emit('stockSelected', selectedStockData)
  console.log('选中股票:', selectedStockData)
}

const toggleShowAllStocks = (poolId: string) => {
  showAllStocks[poolId] = !showAllStocks[poolId]
}

const showCreateModal = () => {
  createModalVisible.value = true
}

const showAddStockModal = (poolId: string) => {
  targetPoolId.value = poolId
  addStockModalVisible.value = true
}

const handlePoolAction = async (command: { action: string; poolId: string }) => {
  const { action, poolId } = command
  const pool = stockPools.value.find(p => p.pool_id === poolId)
  
  if (!pool) return
  
  switch (action) {
    case 'edit':
      editingPool.value = pool
      editModalVisible.value = true
      break
      
    case 'delete':
      try {
        await ElMessageBox.confirm(
          `确定要删除股票池 "${pool.pool_name}" 吗？此操作不可撤销。`,
          '确认删除',
          {
            confirmButtonText: '删除',
            cancelButtonText: '取消',
            type: 'warning',
            confirmButtonClass: 'el-button--danger'
          }
        )
        
        await stockPoolsStore.deleteStockPool(poolId)
        await refreshData()
        
        // 如果删除的是当前选中的股票池，清空选中状态
        if (selectedPoolId.value === poolId) {
          selectedPoolId.value = null
          selectedStock.value = null
        }
        
        ElMessage.success('股票池删除成功')
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除股票池失败:', error)
          ElMessage.error('删除失败')
        }
      }
      break
  }
}

const onPoolCreated = (_pool: StockPool) => {
  createModalVisible.value = false
  refreshData()
  ElMessage.success('股票池创建成功')
}

const onPoolUpdated = (_pool: StockPool) => {
  editModalVisible.value = false
  editingPool.value = null
  refreshData()
  ElMessage.success('股票池更新成功')
}

const onStocksAdded = (_poolId: string, stocks: StockInfo[]) => {
  addStockModalVisible.value = false
  targetPoolId.value = null
  refreshData()
  ElMessage.success(`成功添加 ${stocks.length} 只股票`)
}

// 暴露给父组件的方法
defineExpose({
  refreshData
})

// 生命周期
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.stock-pools-panel {
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
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-elevated);
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

.stock-count-badge {
  margin-left: var(--spacing-xs);
}

.panel-actions {
  display: flex;
  gap: var(--spacing-xs);
}

.action-icon {
  width: 14px;
  height: 14px;
}

/* ========== 面板内容 ========== */
.panel-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.loading-state,
.empty-state {
  padding: var(--spacing-xl);
  text-align: center;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: var(--text-tertiary);
  margin: 0 auto var(--spacing-md);
}

.empty-text {
  color: var(--text-secondary);
  margin-bottom: var(--spacing-lg);
}

.btn-icon {
  width: 14px;
  height: 14px;
  margin-right: var(--spacing-xs);
}

/* ========== 股票池列表 ========== */
.pools-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.pool-card {
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  transition: all var(--transition-base);
  cursor: pointer;
  overflow: hidden;
}

.pool-card:hover {
  border-color: var(--accent-primary);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.15);
}

.pool-card.active {
  border-color: var(--accent-primary);
  background: rgba(0, 212, 255, 0.05);
  box-shadow: 0 0 0 1px rgba(0, 212, 255, 0.2);
}

.pool-header {
  padding: var(--spacing-md);
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-sm);
  background: var(--bg-elevated);
}

.pool-info {
  flex: 1;
  min-width: 0;
}

.pool-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-xs) 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pool-description {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pool-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.stock-badge {
  margin-right: var(--spacing-xs);
}

/* ========== 股票列表 ========== */
.stocks-list {
  border-top: 1px solid var(--border-secondary);
}

.stock-item {
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--border-secondary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all var(--transition-fast);
  cursor: pointer;
}

.stock-item:last-child {
  border-bottom: none;
}

.stock-item:hover {
  background: var(--bg-elevated);
}

.stock-item.selected {
  background: rgba(0, 212, 255, 0.1);
  color: var(--accent-primary);
}

.stock-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.stock-code {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.stock-name {
  font-size: 11px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stock-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.stock-industry {
  font-size: 11px;
  color: var(--text-secondary);
  background: var(--bg-elevated);
  padding: 2px 6px;
  border-radius: 4px;
}

.stock-market {
  font-size: 10px;
  color: var(--text-tertiary);
  font-weight: 500;
}

.expand-button {
  padding: var(--spacing-xs) var(--spacing-md);
  text-align: center;
  border-top: 1px solid var(--border-secondary);
  background: var(--bg-elevated);
}

.expand-icon {
  width: 12px;
  height: 12px;
  margin-left: var(--spacing-xs);
  transition: transform var(--transition-base);
}

.expand-icon.rotated {
  transform: rotate(180deg);
}

/* ========== 空股票池状态 ========== */
.empty-pool {
  padding: var(--spacing-lg);
  text-align: center;
  border-top: 1px solid var(--border-secondary);
  background: var(--bg-elevated);
}

.empty-pool-text {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0 0 var(--spacing-md) 0;
}

/* ========== 下拉菜单样式 ========== */
.menu-icon {
  width: 14px;
  height: 14px;
  margin-right: var(--spacing-xs);
}

.menu-icon.danger {
  color: var(--danger-primary);
}

/* ========== Element Plus 样式覆盖 ========== */
:deep(.el-badge__content) {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  font-size: 10px;
  height: 16px;
  line-height: 16px;
  min-width: 16px;
}

:deep(.el-button--small) {
  height: 24px;
  padding: 0 8px;
  font-size: 12px;
}

:deep(.el-skeleton__item) {
  background: var(--bg-elevated);
}

:deep(.el-dropdown-menu__item) {
  font-size: 13px;
  padding: 6px 12px;
}

:deep(.el-dropdown-menu__item:hover) {
  background: var(--bg-elevated);
  color: var(--accent-primary);
}

/* ========== 滚动条样式 ========== */
.pools-list::-webkit-scrollbar {
  width: 4px;
}

.pools-list::-webkit-scrollbar-track {
  background: var(--bg-elevated);
}

.pools-list::-webkit-scrollbar-thumb {
  background: var(--border-primary);
  border-radius: 2px;
}

.pools-list::-webkit-scrollbar-thumb:hover {
  background: var(--accent-primary);
}
</style>