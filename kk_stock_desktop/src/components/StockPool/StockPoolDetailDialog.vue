<template>
  <el-dialog
    v-model="dialogVisible"
    :title="pool ? `股票池详情 - ${pool.pool_name}` : '加载中...'"
    width="80%"
    :before-close="handleClose"
    class="stock-pool-detail-dialog"
  >
    <div v-if="loading" class="loading-container" v-loading="loading">
      <div style="height: 300px;"></div>
    </div>
    
    <div v-else-if="pool" class="detail-content">
      <!-- 股票池基本信息 -->
      <div class="pool-info-section">
        <div class="section-header">
          <h3>基本信息</h3>
          <div class="header-actions">
            <el-button 
              size="small" 
              @click="showEditMode = !showEditMode"
              v-if="canEdit"
            >
              <component :is="PencilIcon" class="btn-icon" />
              {{ showEditMode ? '取消编辑' : '编辑信息' }}
            </el-button>
            <el-button 
              size="small" 
              type="primary"
              @click="showAddStockDialog = true"
            >
              <component :is="PlusIcon" class="btn-icon" />
              添加股票
            </el-button>
            <el-button 
              size="small" 
              type="danger"
              @click="handleDeletePool"
              v-if="canDelete"
            >
              <component :is="TrashIcon" class="btn-icon" />
              删除股票池
            </el-button>
          </div>
        </div>
        
        <!-- 编辑模式 -->
        <div v-if="showEditMode" class="edit-form">
          <el-form
            ref="editFormRef"
            :model="editForm"
            :rules="editRules"
            label-width="100px"
          >
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="股票池名称" prop="pool_name">
                  <el-input v-model="editForm.pool_name" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="公开分享">
                  <el-switch
                    v-model="editForm.is_public"
                    active-text="公开"
                    inactive-text="私有"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="描述信息">
              <el-input
                v-model="editForm.description"
                type="textarea"
                :rows="3"
              />
            </el-form-item>
            
            <el-form-item label="标签">
              <el-select
                v-model="editForm.tags"
                multiple
                filterable
                allow-create
                placeholder="选择或输入标签"
                style="width: 100%"
              >
                <el-option
                  v-for="tag in commonTags"
                  :key="tag"
                  :label="tag"
                  :value="tag"
                />
              </el-select>
            </el-form-item>
            
            <el-form-item>
              <el-button @click="showEditMode = false">取消</el-button>
              <el-button 
                type="primary" 
                @click="handleUpdatePool"
                :loading="updating"
              >
                {{ updating ? '保存中...' : '保存修改' }}
              </el-button>
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 显示模式 -->
        <div v-else class="info-display">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="股票池名称">
              {{ pool.pool_name }}
              <el-tag v-if="pool.is_default" type="success" size="small" style="margin-left: 8px;">默认</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="股票数量">
              {{ pool.stock_count }}只
            </el-descriptions-item>
            <el-descriptions-item label="公开分享">
              <el-tag :type="pool.is_public ? 'success' : 'info'" size="small">
                {{ pool.is_public ? '公开' : '私有' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDate(pool.create_time) }}
            </el-descriptions-item>
            <el-descriptions-item label="描述信息" :span="2">
              {{ pool.description || '暂无描述' }}
            </el-descriptions-item>
            <el-descriptions-item label="标签" :span="2">
              <div class="tags-container">
                <el-tag 
                  v-for="tag in pool.tags" 
                  :key="tag" 
                  size="small"
                  class="tag-item"
                >
                  {{ tag }}
                </el-tag>
                <span v-if="pool.tags.length === 0" class="text-muted">暂无标签</span>
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
      
      <!-- 股票列表 -->
      <div class="stocks-section">
        <div class="section-header">
          <h3>股票列表 ({{ pool.stocks.length }}只)</h3>
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索股票代码或名称"
              style="width: 200px;"
              clearable
            >
              <template #prefix>
                <component :is="MagnifyingGlassIcon" />
              </template>
            </el-input>
          </div>
        </div>
        
        <!-- 股票表格 -->
        <el-table 
          :data="filteredStocks" 
          height="400"
          stripe
          v-loading="stocksLoading"
        >
          <el-table-column prop="ts_code" label="股票代码" width="120" />
          <el-table-column prop="name" label="股票名称" width="150" />
          <el-table-column prop="industry" label="行业" width="120" />
          <el-table-column prop="market" label="市场" width="80" />
          <el-table-column prop="add_time" label="添加时间" width="150">
            <template #default="{ row }">
              {{ formatDate(row.add_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="add_reason" label="添加原因" />
          <el-table-column label="标签" width="150">
            <template #default="{ row }">
              <div class="stock-tags">
                <el-tag 
                  v-for="tag in row.tags?.slice(0, 2)" 
                  :key="tag" 
                  size="small"
                  class="stock-tag"
                >
                  {{ tag }}
                </el-tag>
                <span v-if="(row.tags?.length || 0) > 2" class="more-tags">
                  +{{ (row.tags?.length || 0) - 2 }}
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button 
                type="link" 
                size="small" 
                @click="handleRemoveStock(row.ts_code)"
                class="danger-text"
              >
                移除
              </el-button>
            </template>
          </el-table-column>
          
          <template #empty>
            <el-empty description="暂无股票数据">
              <el-button type="primary" @click="showAddStockDialog = true">
                添加第一只股票
              </el-button>
            </el-empty>
          </template>
        </el-table>
      </div>
    </div>
    
    <!-- 股票搜索对话框 -->
    <StockSearchDialog
      v-model="showAddStockDialog"
      :target-pools="[poolId]"
      @added="handleStockAdded"
      @selected="handleStockSelected"
    />
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { 
  PencilIcon, 
  PlusIcon, 
  TrashIcon,
  MagnifyingGlassIcon 
} from '@heroicons/vue/24/outline'

import { stockPoolService, type StockPool, type StockInfo, type UpdatePoolData } from '@/services/stockPoolService'
import StockSearchDialog from './StockSearchDialog.vue'

// Props 定义
interface Props {
  modelValue: boolean
  poolId: string
}

const props = defineProps<Props>()

// Events 定义
interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'updated', pool: StockPool): void
  (e: 'deleted', poolId: string): void
}

const emit = defineEmits<Emits>()

// 响应式数据
const loading = ref(false)
const stocksLoading = ref(false)
const updating = ref(false)
const showEditMode = ref(false)
const showAddStockDialog = ref(false)
const searchKeyword = ref('')
const editFormRef = ref<FormInstance>()
const pool = ref<StockPool | null>(null)

const editForm = ref({
  pool_name: '',
  description: '',
  is_public: false,
  tags: [] as string[]
})

const commonTags = [
  '热门股票',
  '科技股',
  '蓝筹股',
  '成长股',
  '价值股',
  '新能源',
  '消费',
  '医疗',
  '金融',
  '地产',
  '自选股',
  '关注列表'
]

const editRules = {
  pool_name: [
    { required: true, message: '请输入股票池名称', trigger: 'blur' },
    { min: 1, max: 50, message: '名称长度应在1-50个字符', trigger: 'blur' }
  ]
}

// 计算属性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const canEdit = computed(() => {
  return pool.value && !pool.value.is_default
})

const canDelete = computed(() => {
  return pool.value && stockPoolService.canDeletePool(pool.value)
})

const filteredStocks = computed(() => {
  if (!pool.value || !searchKeyword.value) {
    return pool.value?.stocks || []
  }
  
  const keyword = searchKeyword.value.toLowerCase()
  return pool.value.stocks.filter(stock => 
    stock.ts_code.toLowerCase().includes(keyword) ||
    stock.name.toLowerCase().includes(keyword)
  )
})

// 方法
const loadPoolDetail = async () => {
  if (!props.poolId) return
  
  loading.value = true
  try {
    pool.value = await stockPoolService.getPoolDetail(props.poolId)
    
    // 初始化编辑表单
    editForm.value = {
      pool_name: pool.value.pool_name,
      description: pool.value.description || '',
      is_public: pool.value.is_public,
      tags: [...pool.value.tags]
    }
  } catch (error) {
    console.error('加载股票池详情失败:', error)
    ElMessage.error('加载股票池详情失败')
  } finally {
    loading.value = false
  }
}

const handleUpdatePool = async () => {
  if (!editFormRef.value || !pool.value) return
  
  try {
    await editFormRef.value.validate()
    updating.value = true
    
    const updateData: UpdatePoolData = {
      pool_name: editForm.value.pool_name,
      description: editForm.value.description || undefined,
      is_public: editForm.value.is_public,
      tags: editForm.value.tags
    }
    
    const updatedPool = await stockPoolService.updatePool(pool.value.pool_id, updateData)
    
    pool.value = updatedPool
    showEditMode.value = false
    
    ElMessage.success('股票池信息更新成功')
    emit('updated', updatedPool)
    
  } catch (error) {
    console.error('更新股票池失败:', error)
    ElMessage.error('更新股票池失败')
  } finally {
    updating.value = false
  }
}

const handleDeletePool = async () => {
  if (!pool.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除股票池“${pool.value.pool_name}”吗？此操作不可撤销。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await stockPoolService.deletePool(pool.value.pool_id)
    
    ElMessage.success('股票池删除成功')
    emit('deleted', pool.value.pool_id)
    handleClose()
    
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除股票池失败:', error)
      ElMessage.error('删除股票池失败')
    }
  }
}

const handleRemoveStock = async (stockCode: string) => {
  if (!pool.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要从股票池中移除股票 ${stockCode} 吗？`,
      '确认移除',
      {
        confirmButtonText: '移除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await stockPoolService.removeStockFromPool(pool.value.pool_id, stockCode)
    
    // 更新本地数据
    pool.value.stocks = pool.value.stocks.filter(stock => stock.ts_code !== stockCode)
    pool.value.stock_count = pool.value.stocks.length
    
    ElMessage.success('股票移除成功')
    emit('updated', pool.value)
    
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('移除股票失败:', error)
      ElMessage.error('移除股票失败')
    }
  }
}

const handleStockAdded = (data: { pools: StockPool[], stocks: StockInfo[] }) => {
  // 更新当前股票池数据
  const updatedPool = data.pools.find(p => p.pool_id === props.poolId)
  if (updatedPool && pool.value) {
    pool.value.stocks = updatedPool.stocks
    pool.value.stock_count = updatedPool.stock_count
    emit('updated', pool.value)
  }
}

const handleStockSelected = async (stocks: StockInfo[]) => {
  try {
    if (!props.poolId || stocks.length === 0) {
      return
    }
    
    // 将选中的股票添加到当前股票池
    await stockPoolService.addStocksToPool(props.poolId, stocks)
    
    // 重新加载股票池数据
    await loadPoolDetail()
    
    ElMessage.success(`成功添加 ${stocks.length} 只股票到股票池`)
    
    // 确保pool.value不为null再emit
    if (pool.value) {
      emit('updated', pool.value)
    }
    
    // 关闭添加股票对话框
    showAddStockDialog.value = false
    
  } catch (error) {
    console.error('添加股票失败:', error)
    ElMessage.error('添加股票失败')
  }
}

const handleClose = () => {
  showEditMode.value = false
  searchKeyword.value = ''
  dialogVisible.value = false
}


const formatDate = (date: Date | string): string => {
  if (!date) return '-'
  const d = new Date(date)
  return d.toLocaleString('zh-CN')
}

// 监听
watch(() => props.poolId, (newId) => {
  if (newId && dialogVisible.value) {
    loadPoolDetail()
  }
})

watch(dialogVisible, (visible) => {
  if (visible && props.poolId) {
    loadPoolDetail()
  } else if (!visible) {
    pool.value = null
    showEditMode.value = false
  }
})

onMounted(() => {
  if (props.poolId && dialogVisible.value) {
    loadPoolDetail()
  }
})
</script>

<style scoped>
.stock-pool-detail-dialog {
  .detail-content {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }
  
  .loading-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 300px;
  }
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
    }
  }
  
  .header-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  
  .btn-icon {
    width: 14px;
    height: 14px;
    margin-right: 4px;
  }
  
  .edit-form {
    background: var(--bg-secondary);
    padding: 20px;
    border-radius: var(--radius-md);
    border: 1px solid var(--border-primary);
  }
  
  .info-display {
    .tags-container {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
    }
    
    .tag-item {
      font-size: 12px;
    }
  }
  
  .stocks-section {
    .stock-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      align-items: center;
    }
    
    .stock-tag {
      font-size: 11px;
    }
    
    .more-tags {
      font-size: 11px;
      color: var(--text-tertiary);
    }
    
    .danger-text {
      color: var(--danger-color);
    }
    
    .danger-text:hover {
      color: var(--danger-color-dark);
    }
  }
  
  .text-muted {
    color: var(--text-tertiary);
    font-size: 14px;
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stock-pool-detail-dialog {
    width: 95% !important;
  }
}

@media (max-width: 768px) {
  .stock-pool-detail-dialog {
    .section-header {
      flex-direction: column;
      gap: 12px;
      align-items: flex-start;
    }
    
    .header-actions {
      width: 100%;
      justify-content: flex-end;
    }
    
    .edit-form {
      padding: 16px;
    }
  }
}
</style>