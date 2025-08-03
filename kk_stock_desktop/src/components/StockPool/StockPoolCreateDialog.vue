<template>
  <el-dialog
    v-model="dialogVisible"
    title="创建股票池"
    width="500px"
    :before-close="handleClose"
    class="stock-pool-create-dialog"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="股票池名称" prop="pool_name">
        <el-input
          v-model="form.pool_name"
          placeholder="请输入股票池名称"
          maxlength="50"
          show-word-limit
        />
      </el-form-item>
      
      <el-form-item label="描述信息">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入股票池描述（可选）"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>
      
      <el-form-item label="公开分享">
        <el-switch
          v-model="form.is_public"
          active-text="公开"
          inactive-text="私有"
        />
        <div class="form-tip">
          公开后其他用户可以查看和复制此股票池
        </div>
      </el-form-item>
      
      <el-form-item label="标签">
        <el-select
          v-model="form.tags"
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
      
      <el-form-item label="初始股票" class="stocks-section">
        <div class="stocks-container">
          <div class="stocks-header">
            <span class="stocks-count">已添加 {{ form.stocks?.length || 0 }} 只股票</span>
            <el-button
              type="primary"
              size="small"
              @click="showStockSearch = true"
            >
              <component :is="PlusIcon" class="btn-icon" />
              添加股票
            </el-button>
          </div>
          
          <div v-if="form.stocks && form.stocks.length > 0" class="stocks-list">
            <div
              v-for="(stock, index) in form.stocks"
              :key="stock.ts_code"
              class="stock-item"
            >
              <div class="stock-info">
                <span class="stock-code">{{ stock.ts_code }}</span>
                <span class="stock-name">{{ stock.name }}</span>
                <span class="stock-industry">{{ stock.industry }}</span>
              </div>
              <el-button
                link
                size="small"
                @click="removeStock(index)"
                class="remove-btn"
              >
                <component :is="XMarkIcon" class="btn-icon" />
              </el-button>
            </div>
          </div>
          
          <div v-else class="stocks-empty">
            <el-empty description="暂无股票，可稍后添加" />
          </div>
        </div>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          @click="handleSubmit"
          :loading="submitting"
        >
          {{ submitting ? '创建中...' : '创建股票池' }}
        </el-button>
      </div>
    </template>
    
    <!-- 股票搜索对话框 -->
    <StockSearchDialog
      v-model="showStockSearch"
      mode="select"
      @selected="handleStockSelected"
    />
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { PlusIcon, XMarkIcon } from '@heroicons/vue/24/outline'

import { stockPoolService, type StockPool, type StockInfo, type CreatePoolData } from '@/services/stockPoolService'
import StockSearchDialog from './StockSearchDialog.vue'

// Props 定义
interface Props {
  modelValue: boolean
  preSelectedStocks?: StockInfo[]
}

const props = withDefaults(defineProps<Props>(), {
  preSelectedStocks: () => []
})

// Events 定义
interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'created', pool: StockPool): void
}

const emit = defineEmits<Emits>()

// 响应式数据
const submitting = ref(false)
const showStockSearch = ref(false)
const formRef = ref<FormInstance>()

const form = ref<CreatePoolData>({
  pool_name: '',
  description: '',
  is_public: false,
  tags: [],
  stocks: []
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

const rules = {
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
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    const createdPool = await stockPoolService.createPool(form.value)
    
    ElMessage.success('股票池创建成功')
    emit('created', createdPool)
    handleClose()
    
  } catch (error) {
    console.error('创建股票池失败:', error)
    ElMessage.error('创建股票池失败')
  } finally {
    submitting.value = false
  }
}

const handleStockSelected = (stocks: StockInfo[]) => {
  // 确保stocks数组存在
  if (!form.value.stocks) {
    form.value.stocks = []
  }
  
  // 过滤掉已存在的股票
  const existingCodes = new Set(form.value.stocks.map(s => s.ts_code))
  const newStocks = stocks.filter(stock => !existingCodes.has(stock.ts_code))
  
  form.value.stocks.push(...newStocks)
  
  if (newStocks.length > 0) {
    ElMessage.success(`成功添加 ${newStocks.length} 只股票`)
  } else {
    ElMessage.warning('所选股票已存在')
  }
}

const removeStock = (index: number) => {
  if (form.value.stocks) {
    form.value.stocks.splice(index, 1)
  }
}

const resetForm = () => {
  form.value = {
    pool_name: '',
    description: '',
    is_public: false,
    tags: [],
    stocks: []
  }
  formRef.value?.clearValidate()
}

const handleClose = () => {
  resetForm()
  dialogVisible.value = false
}

// 监听预选股票
watch(() => props.preSelectedStocks, (newStocks) => {
  if (newStocks && newStocks.length > 0) {
    if (!form.value.stocks) {
      form.value.stocks = []
    }
    form.value.stocks = [...newStocks]
  }
}, { immediate: true })

// 监听对话框显示状态
watch(dialogVisible, (visible) => {
  if (visible && props.preSelectedStocks?.length) {
    if (!form.value.stocks) {
      form.value.stocks = []
    }
    form.value.stocks = [...props.preSelectedStocks]
  }
})
</script>

<style scoped>
.stock-pool-create-dialog {
  .form-tip {
    font-size: 12px;
    color: var(--text-tertiary);
    margin-top: 4px;
  }
  
  .stocks-section {
    .stocks-container {
      border: 1px solid var(--border-primary);
      border-radius: var(--radius-md);
      padding: 16px;
      background: var(--bg-secondary);
    }
    
    .stocks-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }
    
    .stocks-count {
      font-size: 14px;
      color: var(--text-secondary);
    }
    
    .btn-icon {
      width: 14px;
      height: 14px;
      margin-right: 4px;
    }
    
    .stocks-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      max-height: 200px;
      overflow-y: auto;
    }
    
    .stock-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      background: var(--bg-primary);
      border: 1px solid var(--border-primary);
      border-radius: var(--radius-sm);
    }
    
    .stock-info {
      display: flex;
      gap: 12px;
      align-items: center;
      flex: 1;
    }
    
    .stock-code {
      font-weight: 600;
      color: var(--text-primary);
      min-width: 80px;
    }
    
    .stock-name {
      font-weight: 500;
      color: var(--text-primary);
      min-width: 80px;
    }
    
    .stock-industry {
      font-size: 12px;
      color: var(--text-secondary);
      background: var(--bg-secondary);
      padding: 2px 6px;
      border-radius: var(--radius-xs);
    }
    
    .remove-btn {
      color: var(--danger-color);
      padding: 4px;
      
      &:hover {
        color: var(--danger-color-dark);
      }
    }
    
    .stocks-empty {
      text-align: center;
      padding: 20px;
    }
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stock-pool-create-dialog {
    width: 95% !important;
    
    .stocks-section {
      .stocks-header {
        flex-direction: column;
        gap: 8px;
        align-items: flex-start;
      }
      
      .stock-item {
        flex-direction: column;
        gap: 8px;
        align-items: flex-start;
      }
      
      .stock-info {
        flex-direction: column;
        gap: 4px;
        align-items: flex-start;
      }
    }
  }
}
</style>