<template>
  <div class="stock-search-component" :class="{ 'compact': compact }">
    <div class="search-header">
      <h4 class="search-title">
        <MagnifyingGlassIcon class="title-icon" />
        股票搜索
      </h4>
    </div>
    
    <div class="search-content">
      <!-- 搜索输入框 -->
      <div class="search-input-container">
        <el-input
          v-model="searchKeyword"
          placeholder="输入股票代码或名称搜索..."
          class="search-input"
          @input="onSearchInput"
          @keyup.enter="handleSearch"
          clearable
          :loading="searching"
        >
          <template #prefix>
            <MagnifyingGlassIcon class="search-icon" />
          </template>
          <template #suffix>
            <el-button 
              type="primary" 
              size="small" 
              @click="handleSearch"
              :loading="searching"
              :disabled="!searchKeyword.trim()"
            >
              搜索
            </el-button>
          </template>
        </el-input>
      </div>
      
      <!-- 搜索结果 -->
      <div class="search-results" v-if="searchResults.length > 0">
        <div class="results-header">
          <span class="results-count">找到 {{ searchResults.length }} 个结果</span>
        </div>
        <div class="results-list">
          <div 
            v-for="stock in searchResults" 
            :key="stock.ts_code"
            class="result-item"
            @click="selectStock(stock)"
          >
            <div class="stock-info">
              <div class="stock-code">{{ stock.ts_code }}</div>
              <div class="stock-name">{{ stock.name }}</div>
              <div class="stock-industry" v-if="stock.industry">{{ stock.industry }}</div>
            </div>
            <div class="stock-market">
              <el-tag size="small" :type="getMarketType(stock.market)">
                {{ stock.market }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div class="empty-state" v-else-if="hasSearched && !searching">
        <MagnifyingGlassIcon class="empty-icon" />
        <p class="empty-text">未找到相关股票</p>
        <p class="empty-hint">请尝试输入其他关键词</p>
      </div>
      
      <!-- 初始状态 -->
      <div class="initial-state" v-else-if="!searching">
        <MagnifyingGlassIcon class="initial-icon" />
        <p class="initial-text">输入股票代码或名称开始搜索</p>
        <p class="initial-hint">支持模糊搜索，如：宁德时代、300750</p>
      </div>
      
      <!-- 搜索中状态 -->
      <div class="loading-state" v-else>
        <el-skeleton :rows="3" animated />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'
import { MagnifyingGlassIcon } from '@heroicons/vue/24/outline'
import { apiClient } from '@/api/base'

// 接口定义
interface StockSearchResult {
  ts_code: string
  name: string
  industry?: string
  market?: string
  list_date?: string
}

interface SelectedStock {
  code: string
  name: string
  industry?: string
  market?: string
}

// Props
const props = defineProps<{
  compact?: boolean
}>()

// Emits
const emit = defineEmits<{
  stockSelected: [stock: SelectedStock]
}>()

// 响应式数据
const searchKeyword = ref('')
const searchResults = ref<StockSearchResult[]>([])
const searching = ref(false)
const hasSearched = ref(false)

// 搜索防抖定时器
let searchTimer: number | null = null

// 方法
const onSearchInput = () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  
  if (searchKeyword.value.trim()) {
    searchTimer = setTimeout(() => {
      handleSearch()
    }, 300) // 300ms 防抖
  } else {
    searchResults.value = []
    hasSearched.value = false
  }
}

const handleSearch = async () => {
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  
  searching.value = true
  hasSearched.value = false
  
  try {
    const response = await apiClient.get('/user/stock-pools/search-stocks', {
      keyword,
      limit: 20
    })
    
    // 处理响应数据
    const responseData = response.data || response
    let stocks = []
    
    if (Array.isArray(responseData)) {
      stocks = responseData
    } else if (responseData && Array.isArray(responseData.data)) {
      stocks = responseData.data
    }
    
    searchResults.value = stocks
    hasSearched.value = true
    
    console.log('搜索结果:', stocks)
    
  } catch (error) {
    console.error('搜索股票失败:', error)
    ElMessage.error('搜索失败，请稍后重试')
    searchResults.value = []
    hasSearched.value = true
  } finally {
    searching.value = false
  }
}

const selectStock = (stock: StockSearchResult) => {
  const selectedStock: SelectedStock = {
    code: stock.ts_code,
    name: stock.name,
    industry: stock.industry,
    market: stock.market
  }
  
  emit('stockSelected', selectedStock)
  console.log('选中股票:', selectedStock)
  
  // 清空搜索结果
  searchKeyword.value = ''
  searchResults.value = []
  hasSearched.value = false
}

const getMarketType = (market?: string): string => {
  if (!market) return 'info'
  if (market.includes('上海')) return 'primary'
  if (market.includes('深圳')) return 'success'
  return 'info'
}
</script>

<style scoped>
.stock-search-component {
  height: auto;
  max-height: 400px;
  display: flex;
  flex-direction: column;
  border: none;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.stock-search-component.compact {
  max-height: 200px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  z-index: 100;
}

/* ========== 搜索头部 ========== */
.search-header {
  padding: 16px 16px 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: transparent;
}

.compact .search-header {
  padding: 12px 12px 6px;
}

.search-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.compact .search-title {
  font-size: 14px;
}

.title-icon {
  width: 20px;
  height: 20px;
  color: var(--accent-primary);
}

/* ========== 搜索内容 ========== */
.search-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.search-input-container {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.compact .search-input-container {
  padding: 8px 12px;
}

.search-icon {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
}

/* ========== 搜索结果 ========== */
.search-results {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.results-header {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: transparent;
}

.results-count {
  font-size: 11px;
  color: var(--accent-primary);
  background: rgba(0, 212, 255, 0.1);
  padding: 3px 8px;
  border-radius: 20px;
  font-weight: 500;
}

.results-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px 16px;
}

.compact .results-list {
  max-height: 120px;
  padding: 8px 12px 12px;
}

.result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 6px;
  position: relative;
}

.compact .result-item {
  padding: 8px 12px;
  margin-bottom: 4px;
}

.result-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.result-item:hover::before {
  opacity: 1;
}

.result-item:hover {
  transform: translateX(2px);
}

.stock-info {
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.stock-code {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.stock-name {
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 2px;
  opacity: 0.8;
}

.stock-industry {
  font-size: 10px;
  color: var(--text-tertiary);
  opacity: 0.8;
}

.stock-market {
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

/* ========== 状态样式 ========== */
.empty-state,
.initial-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  text-align: center;
}

.empty-icon,
.initial-icon {
  width: 40px;
  height: 40px;
  color: var(--text-tertiary);
  opacity: 0.6;
  margin-bottom: 12px;
}

.empty-text,
.initial-text {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 8px 0;
  font-weight: 500;
}

.empty-hint,
.initial-hint {
  font-size: 11px;
  color: var(--text-tertiary);
  margin: 0;
  opacity: 0.8;
}

.loading-state {
  padding: 16px;
}

/* ========== Element Plus 样式覆盖 ========== */
:deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  backdrop-filter: blur(10px);
  transition: all 0.2s ease;
  min-height: 32px;
}

:deep(.el-input__wrapper:hover) {
  border-color: var(--accent-primary);
  background: rgba(255, 255, 255, 0.05);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.15);
  background: rgba(255, 255, 255, 0.05);
}

:deep(.el-input__inner) {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
  height: 30px;
  line-height: 30px;
}

:deep(.el-button) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  backdrop-filter: blur(10px);
  font-weight: 500;
  font-size: 12px;
  min-height: 30px;
}

:deep(.el-button:hover) {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

:deep(.el-tag) {
  font-size: 10px;
  height: 18px;
  line-height: 18px;
  padding: 0 6px;
}

:deep(.el-skeleton__item) {
  background: var(--bg-elevated);
}

/* ========== 滚动条样式 ========== */
.results-list::-webkit-scrollbar {
  width: 4px;
}

.results-list::-webkit-scrollbar-track {
  background: var(--bg-elevated);
}

.results-list::-webkit-scrollbar-thumb {
  background: var(--border-primary);
  border-radius: 2px;
}

.results-list::-webkit-scrollbar-thumb:hover {
  background: var(--accent-primary);
}

/* ========== 响应式设计 ========== */
@media (max-width: 768px) {
  .search-input-container {
    padding: var(--spacing-md);
  }
  
  .result-item {
    padding: var(--spacing-sm);
  }
  
  .stock-code {
    font-size: 13px;
  }
  
  .stock-name {
    font-size: 11px;
  }
  
  .stock-industry {
    font-size: 10px;
  }
}
</style>