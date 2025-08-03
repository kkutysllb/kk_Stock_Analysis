<template>
  <div class="stock-pool-manager">
    <!-- 操作模式提示 -->
    <div v-if="mode === 'selector'" class="mode-indicator">
      <el-alert
        :title="selectorTitle"
        type="info"
        :closable="false"
        show-icon
      />
    </div>

    <!-- 股票池列表 -->
    <div class="pools-container">
      <div class="pools-header">
        <div class="header-left">
          <h3>{{ headerTitle }}</h3>
          <span class="pools-count">({{ displayPools.length }}个股票池)</span>
        </div>
        <div class="header-actions" v-if="showActions">
          <el-button 
            type="primary" 
            size="small" 
            @click="showCreateDialog"
            v-if="mode !== 'viewer'"
          >
            <component :is="PlusIcon" class="btn-icon" />
            新建股票池
          </el-button>
          <el-button 
            size="small" 
            @click="refreshPools"
          >
            <component :is="ArrowPathIcon" class="btn-icon" />
            刷新
          </el-button>
        </div>
      </div>

      <!-- 股票池网格 -->
      <div v-if="loading" class="loading-container" v-loading="loading">
        <div style="height: 200px;"></div>
      </div>
      
      <div v-else-if="displayPools.length === 0" class="empty-container">
        <el-empty description="暂无股票池">
          <el-button 
            type="primary" 
            @click="showCreateDialog"
            v-if="mode !== 'viewer'"
          >
            创建第一个股票池
          </el-button>
        </el-empty>
      </div>

      <div v-else class="pools-grid">
        <div
          v-for="pool in displayPools"
          :key="pool.pool_id"
          class="pool-card"
          :class="{ 
            'selected': isPoolSelected(pool.pool_id),
            'selectable': mode === 'selector',
            'default-pool': pool.is_default
          }"
          @click="handlePoolClick(pool)"
        >
          <!-- 选择标识 -->
          <div v-if="mode === 'selector'" class="selection-indicator">
            <el-checkbox 
              :model-value="isPoolSelected(pool.pool_id)"
              @change="togglePoolSelection(pool.pool_id)"
              @click.stop
            />
          </div>

          <!-- 股票池信息 -->
          <div class="pool-info">
            <div class="pool-header">
              <div class="pool-name">
                {{ pool.pool_name }}
                <el-tag v-if="pool.is_default" type="success" size="small">默认</el-tag>
                <el-tag v-if="pool.is_public" type="info" size="small">公开</el-tag>
              </div>
              
              <!-- 操作菜单 -->
              <el-dropdown 
                v-if="mode === 'manager'"
                trigger="click" 
                @command="(cmd: string) => handlePoolAction(cmd, pool)"
                @click.stop
              >
                <el-button link size="small" class="action-btn">
                  <EllipsisVerticalIcon class="icon" />
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="view">查看详情</el-dropdown-item>
                    <el-dropdown-item command="edit">编辑信息</el-dropdown-item>
                    <el-dropdown-item command="addStock">添加股票</el-dropdown-item>
                    <el-dropdown-item 
                      command="delete" 
                      :disabled="!stockPoolService.canDeletePool(pool)"
                      divided
                    >
                      删除股票池
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>

            <div class="pool-description">
              {{ pool.description || '暂无描述' }}
            </div>

            <div class="pool-stats">
              <div class="stat-item">
                <span class="stat-label">股票数量</span>
                <span class="stat-value">{{ pool.stock_count }}只</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">类型</span>
                <span class="stat-value">{{ getPoolTypeText(pool.pool_type) }}</span>
              </div>
            </div>

            <div class="pool-tags" v-if="pool.tags.length > 0">
              <el-tag 
                v-for="tag in pool.tags.slice(0, 3)" 
                :key="tag" 
                size="small"
                class="pool-tag"
              >
                {{ tag }}
              </el-tag>
              <span v-if="pool.tags.length > 3" class="more-tags">+{{ pool.tags.length - 3 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div v-if="mode === 'selector' && selectedPools.length > 0" class="bottom-actions">
      <div class="selected-info">
        已选择 {{ selectedPools.length }} 个股票池
      </div>
      <div class="action-buttons">
        <el-button @click="clearSelection">清空选择</el-button>
        <el-button 
          type="primary" 
          @click="confirmSelection"
          :disabled="selectedPools.length === 0"
        >
          确认选择
        </el-button>
      </div>
    </div>

    <!-- 子组件对话框 -->
    <StockPoolCreateDialog 
      v-model="createDialogVisible" 
      @created="handlePoolCreated" 
    />
    
    <StockPoolDetailDialog 
      v-model="detailDialogVisible" 
      :pool-id="currentPoolId"
      @updated="handlePoolUpdated"
      @deleted="handlePoolDeleted"
    />
    
    <StockSearchDialog 
      v-model="searchDialogVisible"
      :target-pools="searchTargetPools"
      @added="handleStockAdded"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  PlusIcon, 
  ArrowPathIcon, 
  EllipsisVerticalIcon 
} from '@heroicons/vue/24/outline'

import { stockPoolService, type StockPool, type StockInfo } from '@/services/stockPoolService'
import StockPoolCreateDialog from './StockPoolCreateDialog.vue'
import StockPoolDetailDialog from './StockPoolDetailDialog.vue'
import StockSearchDialog from './StockSearchDialog.vue'

// Props 定义
interface Props {
  mode?: 'manager' | 'selector' | 'viewer'  // 管理模式/选择模式/查看模式
  showActions?: boolean                       // 是否显示操作按钮
  allowMultiSelect?: boolean                  // 是否允许多选
  preSelectedStocks?: StockInfo[]            // 预选股票（策略选股结果）
  filterPools?: (pools: StockPool[]) => StockPool[]  // 股票池过滤器
  selectorTitle?: string                      // 选择器标题
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'manager',
  showActions: true,
  allowMultiSelect: true,
  preSelectedStocks: () => [],
  selectorTitle: '请选择要加入的股票池（可多选）'
})

// Events 定义
interface Emits {
  (e: 'poolsSelected', pools: StockPool[]): void
  (e: 'stockAdded', data: { pools: StockPool[], stocks: StockInfo[] }): void
  (e: 'poolCreated', pool: StockPool): void
  (e: 'poolUpdated', pool: StockPool): void
  (e: 'poolDeleted', poolId: string): void
}

const emit = defineEmits<Emits>()

// 响应式数据
const loading = ref(false)
const pools = ref<StockPool[]>([])
const selectedPools = ref<string[]>([])
const createDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const searchDialogVisible = ref(false)
const currentPoolId = ref('')
const searchTargetPools = ref<string[]>([])

// 计算属性
const headerTitle = computed(() => {
  switch (props.mode) {
    case 'selector': return '选择股票池'
    case 'viewer': return '股票池列表'
    default: return '我的股票池'
  }
})

const displayPools = computed(() => {
  let filteredPools = pools.value
  if (props.filterPools) {
    filteredPools = props.filterPools(filteredPools)
  }
  return filteredPools
})

// 方法
const refreshPools = async () => {
  loading.value = true
  try {
    pools.value = await stockPoolService.getUserPools()
  } catch (error) {
    console.error('加载股票池失败:', error)
    ElMessage.error('加载股票池失败')
  } finally {
    loading.value = false
  }
}

const isPoolSelected = (poolId: string): boolean => {
  return selectedPools.value.includes(poolId)
}

const togglePoolSelection = (poolId: string) => {
  if (props.mode !== 'selector') return
  
  const index = selectedPools.value.indexOf(poolId)
  if (index > -1) {
    selectedPools.value.splice(index, 1)
  } else {
    if (props.allowMultiSelect) {
      selectedPools.value.push(poolId)
    } else {
      selectedPools.value = [poolId]
    }
  }
}

const handlePoolClick = (pool: StockPool) => {
  if (props.mode === 'selector') {
    togglePoolSelection(pool.pool_id)
  } else if (props.mode === 'manager') {
    viewPoolDetail(pool)
  }
}

const handlePoolAction = async (command: string, pool: StockPool) => {
  switch (command) {
    case 'view':
      viewPoolDetail(pool)
      break
    case 'edit':
      editPool(pool)
      break
    case 'addStock':
      addStockToPool(pool)
      break
    case 'delete':
      await deletePool(pool)
      break
  }
}

const viewPoolDetail = (pool: StockPool) => {
  currentPoolId.value = pool.pool_id
  detailDialogVisible.value = true
}

const editPool = (pool: StockPool) => {
  // TODO: 实现编辑功能
  ElMessage.info('编辑功能开发中...')
}

const addStockToPool = (pool: StockPool) => {
  searchTargetPools.value = [pool.pool_id]
  searchDialogVisible.value = true
}

const deletePool = async (pool: StockPool) => {
  if (!stockPoolService.canDeletePool(pool)) {
    ElMessage.warning('该股票池不允许删除')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除股票池"${pool.pool_name}"吗？此操作不可撤销。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await stockPoolService.deletePool(pool.pool_id)
    ElMessage.success('删除成功')
    await refreshPools()
    emit('poolDeleted', pool.pool_id)
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const showCreateDialog = () => {
  createDialogVisible.value = true
}

const clearSelection = () => {
  selectedPools.value = []
}

const confirmSelection = () => {
  const selected = pools.value.filter(pool => selectedPools.value.includes(pool.pool_id))
  emit('poolsSelected', selected)
}

const getPoolTypeText = (type: string): string => {
  switch (type) {
    case 'default': return '默认'
    case 'custom': return '自定义'
    case 'strategy': return '策略'
    default: return '未知'
  }
}

// 事件处理
const handlePoolCreated = (pool: StockPool) => {
  pools.value.unshift(pool)
  emit('poolCreated', pool)
}

const handlePoolUpdated = (pool: StockPool) => {
  const index = pools.value.findIndex(p => p.pool_id === pool.pool_id)
  if (index > -1) {
    pools.value[index] = pool
  }
  emit('poolUpdated', pool)
}

const handlePoolDeleted = (poolId: string) => {
  pools.value = pools.value.filter(p => p.pool_id !== poolId)
  emit('poolDeleted', poolId)
}

const handleStockAdded = (data: { pools: StockPool[], stocks: StockInfo[] }) => {
  // 更新相关股票池的股票数量
  data.pools.forEach(updatedPool => {
    const index = pools.value.findIndex(p => p.pool_id === updatedPool.pool_id)
    if (index > -1) {
      pools.value[index] = updatedPool
    }
  })
  emit('stockAdded', data)
}

// 暴露的方法
const openSelectDialog = (stocks?: StockInfo[]) => {
  if (props.mode === 'selector') {
    // 如果有预选股票，可以在这里处理
    return
  }
}

const openAddStockDialog = (targetPools?: string[]) => {
  searchTargetPools.value = targetPools || []
  searchDialogVisible.value = true
}

const getSelectedPools = (): StockPool[] => {
  return pools.value.filter(pool => selectedPools.value.includes(pool.pool_id))
}

// 生命周期
onMounted(() => {
  refreshPools()
})

// 暴露方法给父组件
defineExpose({
  openSelectDialog,
  openAddStockDialog,
  refreshPools,
  getSelectedPools,
  clearSelection
})
</script>

<style scoped>
.stock-pool-manager {
  width: 100%;
  min-height: 300px;
}

.mode-indicator {
  margin-bottom: 16px;
}

.pools-container {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.pools-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-primary);
  background: var(--bg-secondary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.pools-count {
  font-size: 14px;
  color: var(--text-secondary);
  background: var(--bg-primary);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.btn-icon {
  width: 14px;
  height: 14px;
  margin-right: 4px;
}

.loading-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.pools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  padding: 20px;
}

.pool-card {
  background: var(--bg-secondary);
  border: 2px solid var(--border-primary);
  border-radius: var(--radius-md);
  padding: 16px;
  transition: all var(--transition-base);
  cursor: pointer;
  position: relative;
}

.pool-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.15);
  border-color: var(--accent-primary);
}

.pool-card.selected {
  border-color: var(--accent-primary);
  background: var(--accent-primary-alpha);
}

.pool-card.selectable {
  cursor: pointer;
}

.pool-card.default-pool {
  border-left: 4px solid var(--success-color);
}

.selection-indicator {
  position: absolute;
  top: 12px;
  right: 12px;
}

.pool-info {
  margin-top: 8px;
}

.pool-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.pool-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.action-btn {
  color: var(--text-secondary);
  padding: 4px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  color: var(--accent-primary);
}

.pool-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.pool-stats {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.stat-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.pool-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.pool-tag {
  font-size: 11px;
}

.more-tags {
  font-size: 12px;
  color: var(--text-tertiary);
}

.bottom-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-primary);
  margin-top: 16px;
  border-radius: var(--radius-md);
}

.selected-info {
  font-size: 14px;
  color: var(--text-secondary);
}

.action-buttons {
  display: flex;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .pools-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .pools-grid {
    grid-template-columns: 1fr;
    padding: 16px;
  }

  .bottom-actions {
    flex-direction: column;
    gap: 12px;
  }

  .action-buttons {
    width: 100%;
    justify-content: center;
  }
}
</style>