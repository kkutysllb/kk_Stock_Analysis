<template>
  <div class="header-stock-search" ref="searchInputRef">
    <el-input
      v-model="searchKeyword"
      placeholder="输入股票代码或名称搜索..."
      class="search-input"
      @input="onSearchInput"
      @keyup.enter="handleSearch"
      @focus="onInputFocus"
      @blur="onInputBlur"
      clearable
      :loading="searching"
    >
      <template #prefix>
        <MagnifyingGlassIcon class="search-icon" />
      </template>
    </el-input>
    
    <!-- 搜索结果下拉面板 -->
    <Teleport to="body">
      <div 
        v-if="showResults && (searchResults.length > 0 || hasSearched)"
        ref="dropdownRef"
        class="search-results-dropdown"
      >
        <!-- 有结果时显示 -->
        <div v-if="searchResults.length > 0" class="results-content">
          <div class="results-header">
            <span class="results-count">找到 {{ searchResults.length }} 个结果</span>
          </div>
          <div class="results-list">
            <div 
              v-for="stock in searchResults.slice(0, 8)" 
              :key="stock.ts_code"
              class="result-item"
              @click="selectStock(stock)"
            >
              <div class="stock-info">
                <div class="stock-code">{{ stock.ts_code }}</div>
                <div class="stock-name">{{ stock.name }}</div>
              </div>
              <div class="stock-market">
                <el-tag size="small" :type="getMarketType(stock.market)">
                  {{ stock.market }}
                </el-tag>
              </div>
            </div>
          </div>
          <div v-if="searchResults.length > 8" class="more-results">
            还有 {{ searchResults.length - 8 }} 个结果...
          </div>
        </div>
        
        <!-- 无结果时显示 -->
        <div v-else-if="hasSearched && !searching" class="no-results">
          <MagnifyingGlassIcon class="no-results-icon" />
          <p class="no-results-text">未找到相关股票</p>
        </div>
        
        <!-- 搜索中状态 -->
        <div v-else-if="searching" class="searching-state">
          <el-skeleton :rows="3" animated />
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
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

// Emits
const emit = defineEmits<{
  stockSelected: [stock: SelectedStock]
}>()

// 响应式数据
const searchKeyword = ref('')
const searchResults = ref<StockSearchResult[]>([])
const searching = ref(false)
const hasSearched = ref(false)
const showResults = ref(false)

// 搜索框和下拉面板的DOM引用
const searchInputRef = ref<HTMLElement | null>(null)
const dropdownRef = ref<HTMLElement | null>(null)

// 搜索防抖定时器
let searchTimer: number | null = null

// 位置更新函数
const updateDropdownPosition = () => {
  if (!showResults.value || !searchInputRef.value || !dropdownRef.value) return
  
  const searchRect = searchInputRef.value.getBoundingClientRect()
  const dropdown = dropdownRef.value
  
  dropdown.style.left = `${searchRect.left}px`
  dropdown.style.top = `${searchRect.bottom + 4}px`
  dropdown.style.width = `${searchRect.width}px`
}

// 滚动事件监听
const handleScroll = () => {
  updateDropdownPosition()
}

// 窗口大小变化监听
const handleResize = () => {
  updateDropdownPosition()
}

// 方法
const onInputFocus = () => {
  if (searchResults.value.length > 0 || hasSearched.value) {
    showResults.value = true
    nextTick(() => {
      updateDropdownPosition()
    })
  }
}

const onInputBlur = () => {
  // 延迟隐藏，允许点击搜索结果
  setTimeout(() => {
    showResults.value = false
  }, 200)
}

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
    showResults.value = false
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
  showResults.value = true
  
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
    
    // 更新下拉面板位置
    nextTick(() => {
      updateDropdownPosition()
    })
    
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
  showResults.value = false
}

const getMarketType = (market?: string): string => {
  if (!market) return 'info'
  if (market.includes('上海')) return 'primary'
  if (market.includes('深圳')) return 'success'
  return 'info'
}

// 生命周期钩子
onMounted(() => {
  // 添加滚动和窗口大小变化监听
  window.addEventListener('scroll', handleScroll, true)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  // 清理事件监听
  window.removeEventListener('scroll', handleScroll, true)
  window.removeEventListener('resize', handleResize)
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
})
</script>

<style scoped>
.header-stock-search {
  position: relative;
  width: 100%;
}

.search-input {
  width: 100%;
}

.search-icon {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
}

.search-btn {
  border: none;
  background: var(--accent-primary);
  color: white;
  font-size: 12px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.search-btn:hover {
  background: var(--neon-cyan);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
}

/* 搜索结果下拉面板 */
.search-results-dropdown {
  position: fixed;
  z-index: 2000;
  background: var(--dropdown-bg);
  color: var(--dropdown-text);
  border: 1px solid var(--dropdown-border);
  border-radius: 8px;
  backdrop-filter: blur(20px);
  box-shadow: var(--dropdown-shadow);
  margin-top: 4px;
  max-height: 320px;
  min-width: 280px;
  overflow: hidden;
}

/* 浅色主题支持 */
@media (prefers-color-scheme: light) {
  .search-results-dropdown {
    --dropdown-bg: #fff;
    --dropdown-text: #222;
    --dropdown-border: #e0e0e0;
    --dropdown-shadow: 0 8px 32px rgba(0,0,0,0.10);
    --dropdown-hover: #e6f7ff;
    --dropdown-hover-text: #1890ff;
    --dropdown-header-bg: #f7fafd;
    --dropdown-scrollbar-track: #f0f0f0;
    --dropdown-scrollbar-thumb: #d0e7f7;
    --dropdown-tag-bg: #e6f7ff;
    --dropdown-tag-text: #1890ff;
  }
  
  .results-header {
    background: var(--dropdown-header-bg);
    border-bottom: 1px solid var(--dropdown-border);
  }
  
  .more-results {
    background: var(--dropdown-header-bg);
    border-top: 1px solid var(--dropdown-border);
  }
  
  .result-item:hover {
    background: var(--dropdown-hover);
    color: var(--dropdown-hover-text);
  }
  
  .results-list::-webkit-scrollbar-track {
    background: var(--dropdown-scrollbar-track);
  }
  
  .results-list::-webkit-scrollbar-thumb {
    background: var(--dropdown-scrollbar-thumb);
  }
}

/* 深色主题 */
@media (prefers-color-scheme: dark) {
  .search-results-dropdown {
    --dropdown-bg: #23272f;
    --dropdown-text: #f2f2f2;
    --dropdown-border: #444;
    --dropdown-shadow: 0 8px 32px rgba(0,0,0,0.30);
    --dropdown-hover: #003a5e;
    --dropdown-hover-text: #40a9ff;
    --dropdown-header-bg: #23272f;
    --dropdown-scrollbar-track: #222;
    --dropdown-scrollbar-thumb: #444;
    --dropdown-tag-bg: #003a5e;
    --dropdown-tag-text: #40a9ff;
  }
  
  .results-header {
    background: var(--dropdown-header-bg);
    border-bottom: 1px solid var(--dropdown-border);
  }
  
  .more-results {
    background: var(--dropdown-header-bg);
    border-top: 1px solid var(--dropdown-border);
  }
  
  .result-item:hover {
    background: var(--dropdown-hover);
    color: var(--dropdown-hover-text);
  }
  
  .results-list::-webkit-scrollbar-track {
    background: var(--dropdown-scrollbar-track);
  }
  
  .results-list::-webkit-scrollbar-thumb {
    background: var(--dropdown-scrollbar-thumb);
  }
}

.results-content {
  display: flex;
  flex-direction: column;
}

.results-header {
  padding: 8px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
}

.results-count {
  font-size: 11px;
  color: var(--dropdown-tag-text);
  background: var(--dropdown-tag-bg);
  padding: 2px 6px;
  border-radius: 12px;
  font-weight: 500;
}

.results-list {
  max-height: 240px;
  overflow-y: auto;
  padding: 4px;
}

.result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  border: 1px solid transparent;
  color: var(--dropdown-text);
}

.result-item:hover {
  background: var(--dropdown-hover);
  color: var(--dropdown-hover-text);
  transform: translateX(2px);
}

.stock-info {
  flex: 1;
  min-width: 0;
}

.stock-code {
  font-size: 13px;
  font-weight: 600;
  color: var(--dropdown-text);
  margin-bottom: 2px;
}

.stock-name {
  font-size: 11px;
  color: var(--dropdown-text);
  opacity: 0.8;
}

.stock-market {
  flex-shrink: 0;
  margin-left: 8px;
}

.more-results {
  padding: 8px 12px;
  text-align: center;
  font-size: 11px;
  color: var(--dropdown-text);
  border-top: 1px solid var(--dropdown-border);
  background: var(--dropdown-header-bg);
  opacity: 0.8;
}

.no-results,
.searching-state {
  padding: 20px;
  text-align: center;
}

.no-results-icon {
  width: 32px;
  height: 32px;
  color: var(--dropdown-text);
  opacity: 0.6;
  margin-bottom: 8px;
}

.no-results-text {
  font-size: 12px;
  color: var(--dropdown-text);
  margin: 0;
  opacity: 0.8;
}

/* 滚动条样式 */
.results-list::-webkit-scrollbar {
  width: 4px;
}

.results-list::-webkit-scrollbar-track {
  background: var(--dropdown-scrollbar-track);
}

.results-list::-webkit-scrollbar-thumb {
  background: var(--dropdown-scrollbar-thumb);
  border-radius: 2px;
}

.results-list::-webkit-scrollbar-thumb:hover {
  background: var(--dropdown-hover);
}

/* Element Plus 样式覆盖 */
:deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  backdrop-filter: blur(10px);
  transition: all 0.2s ease;
  min-height: 36px;
  padding: 1px 8px 1px 12px;
}

:deep(.el-input__wrapper:hover) {
  border-color: var(--accent-primary);
  background: rgba(255, 255, 255, 0.08);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.15);
  background: rgba(255, 255, 255, 0.08);
}

:deep(.el-input__inner) {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
  height: 34px;
  line-height: 34px;
}

:deep(.el-input__prefix) {
  display: flex;
  align-items: center;
}

:deep(.el-input__suffix) {
  display: flex;
  align-items: center;
}

:deep(.el-tag) {
  font-size: 10px;
  height: 16px;
  line-height: 16px;
  padding: 0 4px;
  background: var(--dropdown-tag-bg);
  color: var(--dropdown-tag-text);
  border: none;
}

:deep(.el-skeleton__item) {
  background: rgba(255, 255, 255, 0.1);
}
</style> 