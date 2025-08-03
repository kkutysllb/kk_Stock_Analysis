<template>
  <div class="stock-selector">
    <!-- 搜索区域 -->
    <div class="search-section">
      <el-input
        v-model="searchKeyword"
        :placeholder="placeholder"
        clearable
        @input="handleSearch"
        @clear="handleClear"
        class="search-input"
        :size="size"
      >
        <template #prefix>
          <component :is="MagnifyingGlassIcon" class="search-icon" />
        </template>
      </el-input>
      
      <div v-if="showTip" class="search-tip">
        支持股票代码、股票名称和拼音首字母搜索
      </div>
    </div>
    
    <!-- 搜索结果 -->
    <div v-if="showResults" class="results-section">
      <div v-if="searching" class="loading-container" v-loading="searching">
        <div style="height: 80px;"></div>
      </div>
      
      <div v-else-if="searchResults.length === 0 && hasSearched" class="empty-container">
        <el-empty description="未找到相关股票" :image-size="60">
          <el-button size="small" @click="handleClear">重新搜索</el-button>
        </el-empty>
      </div>
      
      <div v-else-if="searchResults.length > 0" class="results-list">
        <div class="results-header">
          <span class="results-count">找到 {{ searchResults.length }} 只股票</span>
        </div>
        
        <div class="stock-list">
          <div 
            v-for="stock in searchResults" 
            :key="stock.ts_code"
            class="stock-item"
            @click="handleSelectStock(stock)"
          >
            <div class="stock-info">
              <div class="stock-code">{{ stock.ts_code }}</div>
              <div class="stock-name">{{ stock.name }}</div>
              <div class="stock-industry">{{ stock.industry }}</div>
            </div>
            <div class="stock-market">
              <el-tag size="small" :type="stock.market === '上海' ? 'success' : 'primary'">
                {{ stock.market }}
              </el-tag>
            </div>
            <div class="stock-action">
              <el-button type="primary" size="small">
                {{ actionText }}
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { MagnifyingGlassIcon } from '@heroicons/vue/24/outline'

import { stockPoolService, type StockSearchResult } from '@/services/stockPoolService'

// Props 定义
interface Props {
  placeholder?: string
  showTip?: boolean
  showResults?: boolean
  actionText?: string
  size?: 'large' | 'default' | 'small'
  maxResults?: number
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '输入股票代码或名称进行搜索',
  showTip: true,
  showResults: true,
  actionText: '选择',
  size: 'default',
  maxResults: 20
})

// Events 定义
interface Emits {
  (e: 'select', stock: StockSearchResult): void
  (e: 'search', keyword: string): void
  (e: 'clear'): void
}

const emit = defineEmits<Emits>()

// 响应式数据
const searching = ref(false)
const searchKeyword = ref('')
const searchResults = ref<StockSearchResult[]>([])
const hasSearched = ref(false)

let searchTimer: number | null = null

// 方法
const handleSearch = async () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  
  searchTimer = setTimeout(async () => {
    const keyword = searchKeyword.value.trim()
    if (!keyword) {
      searchResults.value = []
      hasSearched.value = false
      emit('clear')
      return
    }
    
    searching.value = true
    hasSearched.value = true
    emit('search', keyword)
    
    try {
      const results = await stockPoolService.searchStocks(keyword, props.maxResults)
      searchResults.value = results
    } catch (error) {
      console.error('搜索股票失败:', error)
      ElMessage.error('搜索股票失败')
      searchResults.value = []
    } finally {
      searching.value = false
    }
  }, 300)
}

const handleClear = () => {
  searchKeyword.value = ''
  searchResults.value = []
  hasSearched.value = false
  emit('clear')
}

const handleSelectStock = (stock: StockSearchResult) => {
  emit('select', stock)
  ElMessage.success(`已选择股票: ${stock.name}(${stock.ts_code})`)
  
  // 清空搜索结果
  handleClear()
}

// 暴露方法给父组件
defineExpose({
  clearSearch: handleClear,
  setKeyword: (keyword: string) => {
    searchKeyword.value = keyword
    handleSearch()
  }
})
</script>

<style scoped>
.stock-selector {
  width: 100%;
}

/* ========== 搜索区域 ========== */
.search-section {
  margin-bottom: var(--spacing-md);
}

.search-input {
  width: 100%;
}

.search-icon {
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
}

.search-tip {
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.4;
  margin-top: var(--spacing-xs);
}

/* ========== 结果区域 ========== */
.results-section {
  min-height: 200px;
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
}

.loading-container,
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 150px;
}

.results-list {
  padding: var(--spacing-sm);
}

.results-header {
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--border-secondary);
  margin-bottom: var(--spacing-sm);
}

.results-count {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.stock-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.stock-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm);
  background: var(--bg-primary);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-base);
}

.stock-item:hover {
  background: var(--bg-elevated);
  border-color: var(--accent-primary);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 212, 255, 0.15);
}

.stock-info {
  flex: 1;
  text-align: left;
}

.stock-code {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent-primary);
  margin-bottom: 2px;
}

.stock-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 1px;
}

.stock-industry {
  font-size: 11px;
  color: var(--text-tertiary);
}

.stock-market {
  margin: 0 var(--spacing-sm);
}

.stock-action {
  flex-shrink: 0;
}

/* ========== 响应式设计 ========== */
@media (max-width: 768px) {
  .stock-item {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-xs);
  }
  
  .stock-market {
    margin: 0;
    align-self: flex-start;
  }
  
  .stock-action {
    align-self: flex-end;
  }
}

/* ========== 滚动条样式 ========== */
.results-section::-webkit-scrollbar {
  width: 4px;
}

.results-section::-webkit-scrollbar-track {
  background: var(--bg-elevated);
}

.results-section::-webkit-scrollbar-thumb {
  background: var(--border-primary);
  border-radius: 2px;
}

.results-section::-webkit-scrollbar-thumb:hover {
  background: var(--accent-primary);
}
</style>