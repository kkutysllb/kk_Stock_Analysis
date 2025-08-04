<template>
  <el-dialog
    v-model="visible"
    title="添加股票"
    width="600px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <div class="add-stock-content">
      <!-- 股票搜索 -->
      <div class="search-section">
        <el-input
          v-model="searchKeyword"
          placeholder="输入股票代码或名称搜索（至少2个字符）"
          @input="handleSearch"
          clearable
          :loading="searching"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- 搜索结果 -->
      <div v-if="searchResults.length > 0" class="search-results">
        <div class="results-header">
          <span>搜索结果</span>
          <el-button size="small" @click="clearSearch">清空</el-button>
        </div>
        <div class="results-list">
          <div 
            v-for="stock in searchResults"
            :key="stock.ts_code"
            class="result-item"
            @click="addStock(stock)"
          >
            <div class="stock-info">
              <span class="stock-code">{{ stock.ts_code }}</span>
              <span class="stock-name">{{ stock.name }}</span>
            </div>
            <el-button size="small" type="primary">添加</el-button>
          </div>
        </div>
      </div>

      <!-- 已选股票 -->
      <div v-if="selectedStocks.length > 0" class="selected-section">
        <div class="selected-header">
          <span>已选股票 ({{ selectedStocks.length }})</span>
          <el-button size="small" @click="clearSelected">清空</el-button>
        </div>
        <div class="selected-list">
          <el-tag
            v-for="stock in selectedStocks"
            :key="stock.ts_code"
            closable
            @close="removeStock(stock.ts_code)"
          >
            {{ stock.ts_code }} {{ stock.name }}
          </el-tag>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleSubmit"
          :loading="submitting"
          :disabled="selectedStocks.length === 0"
        >
          添加 {{ selectedStocks.length }} 只股票
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

// 股票接口定义
interface Stock {
  ts_code: string
  name: string
  market?: string
  industry?: string
}

// Props and Emits
const props = defineProps<{
  modelValue: boolean
  poolId: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'stocks-added': [poolId: string, stocks: Stock[]]
}>()

// Data
const visible = ref(false)
const submitting = ref(false)
const searchKeyword = ref('')
const searchResults = ref<Stock[]>([])
const selectedStocks = ref<Stock[]>([])
const searching = ref(false)
let searchTimer: number | null = null


// Watch
watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
  if (!val) {
    resetForm()
  }
})

// Methods
const resetForm = () => {
  searchKeyword.value = ''
  searchResults.value = []
  selectedStocks.value = []
}

const handleSearch = () => {
  // 清除之前的定时器
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  
  if (!searchKeyword.value) {
    searchResults.value = []
    return
  }
  
  if (searchKeyword.value.length < 2) {
    searchResults.value = []
    return // 至少输入2个字符才开始搜索
  }
  
  // 防抖处理，500ms后执行搜索
  searchTimer = setTimeout(() => {
    performSearch()
  }, 500)
}

const performSearch = async () => {
  try {
    searching.value = true
    
    // 调用后端API搜索股票
    const response = await axios.get('/user/stock-pools/search-stocks', {
      params: {
        keyword: searchKeyword.value,
        limit: 10
      }
    })
    
    if (response.data.success) {
      searchResults.value = response.data.data || []
    } else {
      searchResults.value = []
      ElMessage.warning(response.data.message || '搜索失败')
    }
  } catch (error: any) {
    console.error('股票搜索失败:', error)
    searchResults.value = []
    ElMessage.error('搜索股票时发生错误，请稍后重试')
  } finally {
    searching.value = false
  }
}

const addStock = (stock: Stock) => {
  const exists = selectedStocks.value.find((s: Stock) => s.ts_code === stock.ts_code)
  if (!exists) {
    selectedStocks.value.push(stock)
  }
}

const removeStock = (stockCode: string) => {
  const index = selectedStocks.value.findIndex((s: Stock) => s.ts_code === stockCode)
  if (index >= 0) {
    selectedStocks.value.splice(index, 1)
  }
}

const clearSearch = () => {
  searchKeyword.value = ''
  searchResults.value = []
}

const clearSelected = () => {
  selectedStocks.value = []
}

const handleCancel = () => {
  visible.value = false
}

const handleSubmit = async () => {
  if (!props.poolId || selectedStocks.value.length === 0) return
  
  try {
    submitting.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    emit('stocks-added', props.poolId, selectedStocks.value)
    visible.value = false
  } catch (error) {
    console.error('添加股票失败:', error)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.add-stock-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  max-height: 500px;
}

.search-section {
  margin-bottom: var(--spacing-md);
}

.search-results,
.selected-section {
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.results-header,
.selected-header {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border-primary);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  color: var(--text-primary);
}

.results-list {
  max-height: 200px;
  overflow-y: auto;
}

.result-item {
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--border-secondary);
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.result-item:hover {
  background: var(--bg-elevated);
}

.result-item:last-child {
  border-bottom: none;
}

.stock-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stock-code {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 13px;
}

.stock-name {
  color: var(--text-secondary);
  font-size: 12px;
}

.selected-list {
  padding: var(--spacing-md);
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  max-height: 150px;
  overflow-y: auto;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

/* 滚动条样式 */
.results-list::-webkit-scrollbar,
.selected-list::-webkit-scrollbar {
  width: 4px;
}

.results-list::-webkit-scrollbar-track,
.selected-list::-webkit-scrollbar-track {
  background: var(--bg-elevated);
}

.results-list::-webkit-scrollbar-thumb,
.selected-list::-webkit-scrollbar-thumb {
  background: var(--border-primary);
  border-radius: 2px;
}
</style>