<template>
  <el-dialog
    v-model="dialogVisible"
    title="股票搜索"
    width="800px"
    :before-close="handleClose"
    class="stock-search-dialog"
  >
    <div class="search-content">
      <!-- 搜索区域 -->
      <div class="search-section">
        <el-input
          v-model="searchKeyword"
          placeholder="输入股票代码或名称进行搜索"
          clearable
          @input="handleSearch"
          @clear="handleClear"
          class="search-input"
        >
          <template #prefix>
            <component :is="MagnifyingGlassIcon" class="search-icon" />
          </template>
        </el-input>
        
        <div class="search-tip">
          支持股票代码、股票名称和拼音首字母搜索
        </div>
      </div>
      
      <!-- 搜索结果 -->
      <div class="results-section">
        <div v-if="searching" class="loading-container" v-loading="searching">
          <div style="height: 100px;"></div>
        </div>
        
        <div v-else-if="searchResults.length === 0 && hasSearched" class="empty-container">
          <el-empty description="未找到相关股票">
            <el-button type="primary" @click="handleClear">重新搜索</el-button>
          </el-empty>
        </div>
        
        <div v-else-if="searchResults.length > 0" class="results-list">
          <div class="results-header">
            <span class="results-count">找到 {{ searchResults.length }} 只股票</span>
            <div v-if="mode === 'select'" class="header-actions">
              <el-button
                size="small"
                @click="selectAll"
                :disabled="selectedStocks.length === searchResults.length"
              >
                全选
              </el-button>
              <el-button
                size="small"
                @click="clearSelection"
                :disabled="selectedStocks.length === 0"
              >
                清空
              </el-button>
            </div>
          </div>
          
          <el-table 
            :data="searchResults" 
            height="350"
            @selection-change="handleSelectionChange"
          >
            <el-table-column 
              v-if="mode === 'select'"
              type="selection" 
              width="50" 
            />
            
            <el-table-column prop="ts_code" label="股票代码" width="120">
              <template #default="{ row }">
                <span class="stock-code">{{ row.ts_code }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="name" label="股票名称" width="150">
              <template #default="{ row }">
                <span class="stock-name">{{ row.name }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="industry" label="行业" width="120" />
            
            <el-table-column prop="market" label="市场" width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="row.market === '上海' ? 'success' : 'primary'">
                  {{ row.market }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="list_date" label="上市日期" width="100" />
            
            <el-table-column 
              v-if="mode === 'add'"
              label="操作" 
              width="120"
              fixed="right"
            >
              <template #default="{ row }">
                <el-button
                  type="primary"
                  size="small"
                  @click="handleAddStock(row)"
                >
                  添加到股票池
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <div v-else class="welcome-container">
          <el-empty description="输入关键词开始搜索股票" />
        </div>
      </div>
      
      <!-- 已选择的股票 -->
      <div v-if="mode === 'select' && selectedStocks.length > 0" class="selected-section">
        <div class="selected-header">
          <span class="selected-title">已选择股票 ({{ selectedStocks.length }})</span>
          <el-button size="small" type="link" @click="clearSelection">清空选择</el-button>
        </div>
        
        <div class="selected-list">
          <el-tag
            v-for="stock in selectedStocks"
            :key="stock.ts_code"
            closable
            @close="removeSelected(stock)"
            class="selected-stock"
          >
            {{ stock.ts_code }} {{ stock.name }}
          </el-tag>
        </div>
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          v-if="mode === 'select'"
          type="primary"
          @click="handleConfirm"
          :disabled="selectedStocks.length === 0"
        >
          确认选择 ({{ selectedStocks.length }})
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { MagnifyingGlassIcon } from '@heroicons/vue/24/outline'

import { stockPoolService, type StockSearchResult, type StockInfo } from '@/services/stockPoolService'

// Props 定义
interface Props {
  modelValue: boolean
  mode?: 'select' | 'add'
  targetPools?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'select',
  targetPools: () => []
})

// Events 定义
interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'selected', stocks: StockInfo[]): void
  (e: 'added', data: { pools: any[], stocks: StockInfo[] }): void
}

const emit = defineEmits<Emits>()

// 响应式数据
const searching = ref(false)
const searchKeyword = ref('')
const searchResults = ref<StockSearchResult[]>([])
const selectedStocks = ref<StockInfo[]>([])
const hasSearched = ref(false)

let searchTimer: number | null = null

// 计算属性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

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
      return
    }
    
    searching.value = true
    hasSearched.value = true
    
    try {
      const results = await stockPoolService.searchStocks(keyword, 50)
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
  selectedStocks.value = []
}

const handleSelectionChange = (selection: StockSearchResult[]) => {
  selectedStocks.value = selection.map(item => ({
    ts_code: item.ts_code,
    name: item.name,
    industry: item.industry || '',
    market: item.market || '',
    add_time: new Date(),
    add_reason: '手动添加',
    tags: []
  }))
}

const selectAll = () => {
  selectedStocks.value = searchResults.value.map(item => ({
    ts_code: item.ts_code,
    name: item.name,
    industry: item.industry || '',
    market: item.market || '',
    add_time: new Date(),
    add_reason: '手动添加',
    tags: []
  }))
}

const clearSelection = () => {
  selectedStocks.value = []
}

const removeSelected = (stock: StockInfo) => {
  const index = selectedStocks.value.findIndex(s => s.ts_code === stock.ts_code)
  if (index > -1) {
    selectedStocks.value.splice(index, 1)
  }
}

const handleAddStock = async (stock: StockSearchResult) => {
  if (!props.targetPools || props.targetPools.length === 0) {
    ElMessage.warning('请先选择目标股票池')
    return
  }
  
  try {
    const stockInfo: StockInfo = {
      ts_code: stock.ts_code,
      name: stock.name,
      industry: stock.industry || '',
      market: stock.market || '',
      add_time: new Date(),
      add_reason: '手动添加',
      tags: []
    }
    
    const result = await stockPoolService.addStocksToPools({
      pool_ids: props.targetPools,
      stocks: [stockInfo]
    })
    
    ElMessage.success('股票添加成功')
    emit('added', { pools: result.success_pools, stocks: [stockInfo] })
    
  } catch (error) {
    console.error('添加股票失败:', error)
    ElMessage.error('添加股票失败')
  }
}

const handleConfirm = () => {
  if (selectedStocks.value.length === 0) {
    ElMessage.warning('请先选择股票')
    return
  }
  
  emit('selected', selectedStocks.value)
  handleClose()
}

const handleClose = () => {
  searchKeyword.value = ''
  searchResults.value = []
  selectedStocks.value = []
  hasSearched.value = false
  dialogVisible.value = false
}

// 监听对话框显示状态
watch(dialogVisible, (visible) => {
  if (visible) {
    nextTick(() => {
      // 聚焦搜索框
      const searchInput = document.querySelector('.search-input input') as HTMLInputElement
      if (searchInput) {
        searchInput.focus()
      }
    })
  } else {
    // 清理搜索定时器
    if (searchTimer) {
      clearTimeout(searchTimer)
      searchTimer = null
    }
  }
})
</script>

<style scoped>
.stock-search-dialog {
  .search-content {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  .search-section {
    .search-input {
      margin-bottom: 8px;
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
    }
  }
  
  .results-section {
    min-height: 300px;
    
    .loading-container,
    .empty-container,
    .welcome-container {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 200px;
    }
    
    .results-list {
      .results-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        padding: 8px 0;
        border-bottom: 1px solid var(--border-primary);
      }
      
      .results-count {
        font-size: 14px;
        color: var(--text-secondary);
      }
      
      .header-actions {
        display: flex;
        gap: 8px;
      }
      
      .stock-code {
        font-weight: 600;
        color: var(--accent-primary);
      }
      
      .stock-name {
        font-weight: 500;
        color: var(--text-primary);
      }
    }
  }
  
  .selected-section {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: 16px;
    
    .selected-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }
    
    .selected-title {
      font-weight: 600;
      color: var(--text-primary);
    }
    
    .selected-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    
    .selected-stock {
      font-size: 12px;
    }
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stock-search-dialog {
    width: 95% !important;
    
    .results-section {
      .results-list {
        .results-header {
          flex-direction: column;
          gap: 8px;
          align-items: flex-start;
        }
      }
    }
    
    .selected-section {
      .selected-header {
        flex-direction: column;
        gap: 8px;
        align-items: flex-start;
      }
    }
  }
}
</style>