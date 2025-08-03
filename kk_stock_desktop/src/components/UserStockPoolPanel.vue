<template>
  <div class="user-stock-pool-panel">
    <el-card class="pool-card">
      <template #header>
        <div class="card-header-content">
          <div class="header-left">
            <component :is="FolderIcon" class="header-icon" />
            <span>我的股票池</span>
            <span class="pool-count">({{ stockPools.length }}个股票池)</span>
          </div>
          <div class="header-actions">
            <el-button type="primary" size="small" @click="showCreateModal">
              <component :is="PlusIcon" class="btn-icon" />
              新建股票池
            </el-button>
            <el-button size="small" @click="loadStockPools">
              <component :is="ArrowPathIcon" class="btn-icon" />
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <div v-if="loading" class="loading-container">
        <el-skeleton :loading="loading" animated>
          <template #template>
            <div style="height: 100px; display: flex; align-items: center; justify-content: center;">
              <el-skeleton-item variant="text" style="width: 200px" />
            </div>
          </template>
        </el-skeleton>
      </div>

      <div v-else-if="!authStore.isAuthenticated" class="auth-required">
        <el-empty description="请先登录查看股票池" />
        <el-button type="primary" @click="showLogin">登录</el-button>
      </div>

      <div v-else-if="stockPools.length === 0" class="empty-container">
        <el-empty description="暂无股票池">
          <el-button type="primary" @click="showCreateModal">创建第一个股票池</el-button>
        </el-empty>
      </div>

      <div v-else class="pools-grid">
        <div
          v-for="pool in stockPools"
          :key="pool.id"
          class="pool-item"
          @click="viewPoolDetail(pool)"
        >
          <div class="pool-header">
            <div class="pool-name">{{ pool.name }}</div>
            <el-dropdown trigger="click" @command="handlePoolAction($event, pool)">
              <el-button type="link" size="small" class="more-btn">
                <EllipsisVerticalIcon class="icon" />
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="view">查看详情</el-dropdown-item>
                  <el-dropdown-item command="edit">编辑</el-dropdown-item>
                  <el-dropdown-item command="export">导出</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div class="pool-stats">
            <div class="stat-item">
              <span class="stat-label">股票数量</span>
              <span class="stat-value">{{ pool.stock_count || 0 }}只</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">创建时间</span>
              <span class="stat-value">{{ formatDate(pool.created_at) }}</span>
            </div>
          </div>
          <div class="pool-description">
            {{ pool.description || '暂无描述' }}
          </div>
        </div>
      </div>
    </el-card>

    <!-- 创建股票池弹窗 -->
    <el-dialog
      v-model="createModalVisible"
      title="创建股票池"
      width="500px"
      :before-close="handleCreateModalClose"
    >
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="80px">
        <el-form-item label="股票池名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入股票池名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入股票池描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createModalVisible = false">取消</el-button>
          <el-button type="primary" @click="createStockPool" :loading="creating">
            {{ creating ? '创建中...' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 股票池详情弹窗 -->
    <el-dialog
      v-model="detailModalVisible"
      :title="currentPool?.name || '股票池详情'"
      width="80%"
      :before-close="handleDetailModalClose"
    >
      <div v-if="currentPool" class="pool-detail">
        <div class="detail-header">
          <div class="pool-info">
            <h3>{{ currentPool.name }}</h3>
            <p>{{ currentPool.description || '暂无描述' }}</p>
            <div class="pool-meta">
              <span>创建时间：{{ formatDate(currentPool.created_at) }}</span>
              <span>股票数量：{{ poolStocks.length }}只</span>
            </div>
          </div>
        </div>
        
        <div class="stocks-table" v-loading="loadingStocks" element-loading-text="加载股票列表...">
          <el-table :data="poolStocks" stripe>
            <el-table-column prop="ts_code" label="股票代码" width="120" />
            <el-table-column prop="name" label="股票名称" width="150" />
            <el-table-column prop="industry" label="行业" width="120" />
            <el-table-column prop="added_at" label="添加时间" width="150">
              <template #default="{ row }">
                {{ formatDate(row.added_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button
                  type="danger"
                  size="small"
                  @click="removeFromPool(row)"
                >
                  移除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  FolderIcon,
  PlusIcon,
  ArrowPathIcon,
  EllipsisVerticalIcon
} from '@heroicons/vue/24/outline'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { eventBus } from '@/utils/eventBus'
import {
  getStockPools,
  createStockPool as apiCreateStockPool,
  deleteStockPool,
  getStockPoolDetail,
  removeStockFromPool,
  type StockPool,
  type StockPoolStock
} from '@/api/stockPool'

// Store
const authStore = useAuthStore()

// 响应式数据
const loading = ref(false)
const stockPools = ref<StockPool[]>([])
const createModalVisible = ref(false)
const detailModalVisible = ref(false)
const creating = ref(false)
const loadingStocks = ref(false)
const currentPool = ref<StockPool | null>(null)
const poolStocks = ref<StockPoolStock[]>([])

// 创建表单
const createForm = ref({
  name: '',
  description: ''
})

const createFormRef = ref()

const createRules = {
  name: [
    { required: true, message: '请输入股票池名称', trigger: 'blur' },
    { min: 1, max: 50, message: '名称长度应在1-50个字符', trigger: 'blur' }
  ]
}

// 方法
const loadStockPools = async () => {
  if (!authStore.isAuthenticated) {
    return
  }

  loading.value = true
  try {
    const response = await getStockPools()
    stockPools.value = response.data || []
  } catch (error: any) {
    console.error('加载股票池失败:', error)
    ElMessage.error('加载股票池失败')
  } finally {
    loading.value = false
  }
}

const showCreateModal = () => {
  if (!authStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    showLogin()
    return
  }
  createModalVisible.value = true
}

const showLogin = () => {
  eventBus.emit('show-login-modal')
}

const handleCreateModalClose = () => {
  createModalVisible.value = false
  createForm.value.name = ''
  createForm.value.description = ''
  createFormRef.value?.clearValidate()
}

const createStockPool = async () => {
  if (!createFormRef.value) return

  try {
    await createFormRef.value.validate()
    creating.value = true
    
    const response = await apiCreateStockPool(createForm.value)
    if (response.success) {
      ElMessage.success('创建成功')
      createModalVisible.value = false
      handleCreateModalClose()
      await loadStockPools()
    } else {
      ElMessage.error(response.message || '创建失败')
    }
  } catch (error: any) {
    console.error('创建股票池失败:', error)
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

const viewPoolDetail = async (pool: StockPool) => {
  currentPool.value = pool
  detailModalVisible.value = true
  await loadPoolStocks(pool.id)
}

const loadPoolStocks = async (poolId: string) => {
  loadingStocks.value = true
  try {
    const response = await getStockPoolDetail(poolId)
    poolStocks.value = response.data?.stocks || []
  } catch (error: any) {
    console.error('加载股票列表失败:', error)
    ElMessage.error('加载股票列表失败')
  } finally {
    loadingStocks.value = false
  }
}

const handleDetailModalClose = () => {
  detailModalVisible.value = false
  currentPool.value = null
  poolStocks.value = []
}

const handlePoolAction = async (command: string, pool: StockPool) => {
  switch (command) {
    case 'view':
      await viewPoolDetail(pool)
      break
    case 'edit':
      ElMessage.info('编辑功能开发中...')
      break
    case 'export':
      ElMessage.info('导出功能开发中...')
      break
    case 'delete':
      await deletePool(pool)
      break
  }
}

const deletePool = async (pool: StockPool) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除股票池"${pool.name}"吗？此操作不可撤销。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await deleteStockPool(pool.id)
    if (response.success) {
      ElMessage.success('删除成功')
      await loadStockPools()
    } else {
      ElMessage.error(response.message || '删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除股票池失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const removeFromPool = async (stock: StockPoolStock) => {
  if (!currentPool.value) return

  try {
    await ElMessageBox.confirm(
      `确定要将"${stock.name}"从股票池中移除吗？`,
      '确认移除',
      {
        confirmButtonText: '移除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await removeStockFromPool(currentPool.value.id, stock.ts_code)
    if (response.success) {
      ElMessage.success('移除成功')
      await loadPoolStocks(currentPool.value.id)
    } else {
      ElMessage.error(response.message || '移除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('移除股票失败:', error)
      ElMessage.error('移除失败')
    }
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '--'
  const date = new Date(dateStr)
  return date.toLocaleDateString()
}

// 生命周期
onMounted(() => {
  if (authStore.isAuthenticated) {
    loadStockPools()
  }
})

// 暴露方法给父组件
defineExpose({
  loadStockPools
})
</script>

<style scoped>
.user-stock-pool-panel {
  width: 100%;
}

.pool-card {
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

.pool-count {
  font-size: 14px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.btn-icon {
  width: 14px;
  height: 14px;
  margin-right: 4px;
}

.loading-container,
.auth-required,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  gap: var(--spacing-md);
}

.pools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-md);
  padding: var(--spacing-md);
}

.pool-item {
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  cursor: pointer;
  transition: all var(--transition-base);
  position: relative;
}

.pool-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.15);
  border-color: var(--accent-primary);
}

.pool-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-sm);
}

.pool-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
  flex: 1;
}

.more-btn {
  color: var(--text-secondary);
  padding: 4px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.more-btn:hover {
  color: var(--accent-primary);
}

.pool-stats {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.stat-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.pool-description {
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.pool-detail {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.detail-header {
  border-bottom: 1px solid var(--border-primary);
  padding-bottom: var(--spacing-md);
}

.pool-info h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.pool-info p {
  color: var(--text-secondary);
  margin-bottom: var(--spacing-sm);
}

.pool-meta {
  display: flex;
  gap: var(--spacing-lg);
  font-size: 14px;
  color: var(--text-tertiary);
}

.stocks-table {
  min-height: 200px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .card-header-content {
    flex-direction: column;
    gap: var(--spacing-sm);
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .pools-grid {
    grid-template-columns: 1fr;
    padding: var(--spacing-sm);
  }

  .pool-meta {
    flex-direction: column;
    gap: var(--spacing-xs);
  }
}
</style>