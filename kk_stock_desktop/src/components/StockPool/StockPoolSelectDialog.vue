<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    width="70%"
    :before-close="handleClose"
    class="stock-pool-select-dialog"
  >
    <!-- 对话框内容 -->
    <div class="dialog-content">
      <!-- 预选股票信息 -->
      <div v-if="preSelectedStocks.length > 0" class="selected-stocks-info">
        <el-alert
          :title="`将要添加 ${preSelectedStocks.length} 只股票到选中的股票池`"
          type="info"
          :closable="false"
          show-icon
        >
          <div class="stocks-preview">
            <el-tag 
              v-for="stock in preSelectedStocks.slice(0, 5)" 
              :key="stock.ts_code"
              size="small"
              class="stock-tag"
            >
              {{ stock.name }} ({{ stock.ts_code }})
            </el-tag>
            <span v-if="preSelectedStocks.length > 5" class="more-stocks">
              +{{ preSelectedStocks.length - 5 }}只
            </span>
          </div>
        </el-alert>
      </div>

      <!-- 股票池管理器 -->
      <StockPoolManager
        ref="stockPoolManager"
        mode="selector"
        :allow-multi-select="true"
        :show-actions="allowCreate"
        :selector-title="selectorTitle"
        @pools-selected="handlePoolsSelected"
        @pool-created="handlePoolCreated"
      />

      <!-- 创建新股票池选项 -->
      <div v-if="allowCreate" class="create-option">
        <el-divider>或</el-divider>
        <div class="create-new-section">
          <el-button 
            type="primary" 
            plain
            @click="showQuickCreate = !showQuickCreate"
          >
            <component :is="PlusIcon" class="btn-icon" />
            创建新股票池并添加
          </el-button>
          
          <!-- 快速创建表单 -->
          <div v-if="showQuickCreate" class="quick-create-form">
            <el-form :model="quickCreateForm" :rules="quickCreateRules" ref="quickCreateFormRef">
              <el-form-item prop="pool_name">
                <el-input
                  v-model="quickCreateForm.pool_name"
                  placeholder="请输入股票池名称"
                  @keyup.enter="handleQuickCreate"
                />
              </el-form-item>
              <el-form-item>
                <el-input
                  v-model="quickCreateForm.description"
                  placeholder="描述信息（可选）"
                  type="textarea"
                  :rows="2"
                />
              </el-form-item>
              <el-form-item>
                <el-button @click="showQuickCreate = false">取消</el-button>
                <el-button 
                  type="primary" 
                  @click="handleQuickCreate"
                  :loading="creating"
                >
                  {{ creating ? '创建中...' : '创建并添加' }}
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>
    </div>

    <!-- 对话框底部 -->
    <template #footer>
      <div class="dialog-footer">
        <div class="selection-info">
          <span v-if="selectedPools.length > 0">
            已选择 {{ selectedPools.length }} 个股票池
          </span>
          <span v-else class="text-muted">
            请选择至少一个股票池
          </span>
        </div>
        <div class="footer-buttons">
          <el-button @click="handleClose">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleConfirm"
            :disabled="selectedPools.length === 0"
            :loading="processing"
          >
            {{ processing ? '添加中...' : `确认添加到 ${selectedPools.length} 个股票池` }}
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { PlusIcon } from '@heroicons/vue/24/outline'

import { stockPoolService, type StockPool, type StockInfo, type CreatePoolData, type BatchResult } from '@/services/stockPoolService'
import StockPoolManager from './StockPoolManager.vue'

// Props 定义
interface Props {
  modelValue: boolean
  preSelectedStocks?: StockInfo[]
  title?: string
  allowCreate?: boolean
  selectorTitle?: string
}

const props = withDefaults(defineProps<Props>(), {
  preSelectedStocks: () => [],
  title: '选择股票池',
  allowCreate: true,
  selectorTitle: '请选择要加入的股票池（可多选）'
})

// Events 定义
interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirmed', data: { pools: StockPool[], stocks: StockInfo[], result: BatchResult }): void
  (e: 'canceled'): void
}

const emit = defineEmits<Emits>()

// 响应式数据
const stockPoolManager = ref()
const selectedPools = ref<StockPool[]>([])
const processing = ref(false)
const creating = ref(false)
const showQuickCreate = ref(false)
const quickCreateFormRef = ref()

const quickCreateForm = ref({
  pool_name: '',
  description: ''
})

const quickCreateRules = {
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

// 方法
const handlePoolsSelected = (pools: StockPool[]) => {
  selectedPools.value = pools
}

const handlePoolCreated = (pool: StockPool) => {
  // 新创建的股票池自动选中
  selectedPools.value = [pool]
  showQuickCreate.value = false
  ElMessage.success('股票池创建成功')
}

const handleQuickCreate = async () => {
  if (!quickCreateFormRef.value) return

  try {
    await quickCreateFormRef.value.validate()
    creating.value = true

    const createData: CreatePoolData = {
      pool_name: quickCreateForm.value.pool_name,
      description: quickCreateForm.value.description || undefined,
      pool_type: 'custom',
      is_deletable: true,
      tags: ['手动创建']
    }

    const newPool = await stockPoolService.createPool(createData)
    
    // 通知股票池管理器刷新
    if (stockPoolManager.value) {
      stockPoolManager.value.refreshPools()
    }
    
    handlePoolCreated(newPool)
    
    // 重置表单
    quickCreateForm.value = {
      pool_name: '',
      description: ''
    }
    
  } catch (error) {
    console.error('创建股票池失败:', error)
    ElMessage.error('创建股票池失败')
  } finally {
    creating.value = false
  }
}

const handleConfirm = async () => {
  if (selectedPools.value.length === 0) {
    ElMessage.warning('请选择至少一个股票池')
    return
  }

  if (props.preSelectedStocks.length === 0) {
    ElMessage.warning('没有要添加的股票')
    return
  }

  processing.value = true
  
  try {
    // 批量添加股票到选中的股票池
    const result = await stockPoolService.addStocksToPools({
      pool_ids: selectedPools.value.map(pool => pool.pool_id),
      stocks: props.preSelectedStocks
    })

    // 显示结果
    if (result.total_added > 0) {
      ElMessage.success(
        `成功添加 ${result.total_added} 只股票到 ${result.success_pools.length} 个股票池`
      )
    }

    if (result.failed_pools.length > 0) {
      ElMessage.warning(
        `${result.failed_pools.length} 个股票池添加失败`
      )
    }

    // 发送确认事件
    emit('confirmed', {
      pools: selectedPools.value,
      stocks: props.preSelectedStocks,
      result
    })

    // 关闭对话框
    dialogVisible.value = false

  } catch (error) {
    console.error('添加股票失败:', error)
    ElMessage.error('添加股票失败')
  } finally {
    processing.value = false
  }
}

const handleClose = () => {
  emit('canceled')
  dialogVisible.value = false
}

// 重置状态
const resetState = () => {
  selectedPools.value = []
  showQuickCreate.value = false
  quickCreateForm.value = {
    pool_name: '',
    description: ''
  }
  if (stockPoolManager.value) {
    stockPoolManager.value.clearSelection()
  }
}

// 监听对话框显示状态
watch(dialogVisible, (visible) => {
  if (visible) {
    resetState()
  }
})
</script>

<style scoped>
.stock-pool-select-dialog {
  .dialog-content {
    min-height: 400px;
  }

  .selected-stocks-info {
    margin-bottom: 20px;
  }

  .stocks-preview {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
    margin-top: 8px;
  }

  .stock-tag {
    font-size: 12px;
  }

  .more-stocks {
    font-size: 12px;
    color: var(--text-secondary);
    background: var(--bg-secondary);
    padding: 2px 6px;
    border-radius: var(--radius-sm);
  }

  .create-option {
    margin-top: 20px;
  }

  .create-new-section {
    text-align: center;
  }

  .btn-icon {
    width: 14px;
    height: 14px;
    margin-right: 4px;
  }

  .quick-create-form {
    max-width: 400px;
    margin: 16px auto 0;
    padding: 16px;
    background: var(--bg-secondary);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-primary);
  }

  .dialog-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .selection-info {
    font-size: 14px;
    color: var(--text-secondary);
  }

  .text-muted {
    color: var(--text-tertiary);
  }

  .footer-buttons {
    display: flex;
    gap: 8px;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stock-pool-select-dialog {
    .dialog-footer {
      flex-direction: column;
      gap: 12px;
      align-items: stretch;
    }

    .footer-buttons {
      justify-content: center;
    }

    .stocks-preview {
      justify-content: center;
    }
  }
}
</style>