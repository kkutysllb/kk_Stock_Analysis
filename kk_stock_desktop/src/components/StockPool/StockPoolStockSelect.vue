<template>
  <el-dialog
    v-model="dialogVisible"
    title="从股票池选择股票"
    width="80%"
    :before-close="handleClose"
    class="stock-pool-stock-select-dialog"
  >
    <div class="dialog-content">
      <!-- 股票池选择 -->
      <div class="pool-selection">
        <label class="selection-label">选择股票池：</label>
        <el-select
          v-model="selectedPoolId"
          placeholder="请选择股票池"
          @change="onPoolChange"
          style="width: 300px"
        >
          <el-option
            v-for="pool in stockPools"
            :key="pool.pool_id"
            :label="`${pool.pool_name} (${pool.stock_count}只股票)`"
            :value="pool.pool_id"
          />
        </el-select>
        <el-button 
          @click="loadStockPools" 
          size="small"
          :loading="poolsLoading"
        >
          刷新
        </el-button>
      </div>

      <!-- 股票列表 -->
      <div v-if="selectedPoolId" class="stocks-section">
        <div class="section-header">
          <h4>股票列表</h4>
          <span class="stock-count">{{ stocks.length }} 只股票</span>
        </div>
        
        <div v-if="stocksLoading" class="loading-container" v-loading="stocksLoading">
          <div style="height: 200px;"></div>
        </div>
        
        <div v-else-if="stocks.length === 0" class="empty-container">
          <el-empty description="该股票池暂无股票" />
        </div>
        
        <el-table
          v-else
          :data="stocks"
          @row-click="onStockSelect"
          highlight-current-row
          style="width: 100%"
          class="stocks-table"
        >
          <el-table-column prop="name" label="股票名称" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">
              <div class="stock-info">
                <span class="stock-name">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="ts_code" label="股票代码" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="stock-code">{{ row.ts_code }}</span>
            </template>
          </el-table-column>
          
          <el-table-column prop="market" label="市场" width="60" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="row.ts_code.endsWith('.SH') ? 'danger' : 'success'">
                {{ row.ts_code.endsWith('.SH') ? 'SH' : 'SZ' }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="industry" label="行业" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="industry-text">{{ row.industry || '--' }}</span>
            </template>
          </el-table-column>
          
          <el-table-column prop="add_time" label="添加时间" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">
              {{ formatDateTime(row.add_time) }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="70" align="center" fixed="right">
            <template #default="{ row }">
              <el-button 
                @click.stop="onStockSelect(row)"
                type="primary"
                size="small"
              >
                选择
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 导入股票池服务
import { stockPoolService } from '@/services/stockPoolService'

// Props 定义
interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()

// Events 定义
interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'stock-selected', stock: any): void
}

const emit = defineEmits<Emits>()

// 响应式数据
const poolsLoading = ref(false)
const stocksLoading = ref(false)
const stockPools = ref<any[]>([])
const selectedPoolId = ref<string>('')
const stocks = ref<any[]>([])

// 计算属性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value)
})

// 方法
const handleClose = () => {
  emit('update:modelValue', false)
}

const formatDateTime = (dateStr: string): string => {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadStockPools = async () => {
  poolsLoading.value = true
  try {
    const pools = await stockPoolService.getUserPools()
    stockPools.value = pools
    console.log('加载股票池列表:', stockPools.value)
  } catch (error) {
    console.error('加载股票池失败:', error)
    ElMessage.error('加载股票池失败')
  } finally {
    poolsLoading.value = false
  }
}

const onPoolChange = async () => {
  if (selectedPoolId.value) {
    await loadStocks()
  } else {
    stocks.value = []
  }
}

const loadStocks = async () => {
  if (!selectedPoolId.value) return
  
  stocksLoading.value = true
  try {
    const poolDetail = await stockPoolService.getPoolDetail(selectedPoolId.value)
    stocks.value = poolDetail.stocks || []
    console.log('加载股票池股票:', stocks.value)
  } catch (error) {
    console.error('加载股票列表失败:', error)
    ElMessage.error('加载股票列表失败')
  } finally {
    stocksLoading.value = false
  }
}

const onStockSelect = (stock: any) => {
  console.log('选择股票:', stock)
  emit('stock-selected', stock)
  handleClose()
}

// 监听对话框显示状态
watch(() => props.modelValue, (visible) => {
  if (visible) {
    loadStockPools()
  }
})

// 组件挂载时加载数据
onMounted(() => {
  if (props.modelValue) {
    loadStockPools()
  }
})
</script>

<style scoped>
.dialog-content {
  padding: 0;
}

.pool-selection {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding: 16px;
  background: var(--bg-secondary, #f8f9fa);
  border-radius: 8px;
}

.selection-label {
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
}

.stocks-section {
  border: 1px solid var(--border-primary, #e0e0e0);
  border-radius: 8px;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--bg-primary, #ffffff);
  border-bottom: 1px solid var(--border-primary, #e0e0e0);
}

.section-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.stock-count {
  font-size: 14px;
  color: var(--text-secondary);
}

.loading-container, .empty-container {
  padding: 20px;
}

.stocks-table {
  border: none;
  width: 100%;
}

.stocks-table .el-table__row {
  cursor: pointer;
}

.stocks-table .el-table__row:hover {
  background-color: var(--bg-secondary, #f8f9fa);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stocks-table .el-table__header th,
  .stocks-table .el-table__body td {
    padding: 8px 4px;
    font-size: 12px;
  }
  
  .stocks-table .stock-name {
    font-size: 12px;
  }
  
  .stocks-table .stock-code {
    font-size: 11px;
  }
  
  .stocks-table .industry-text {
    font-size: 11px;
  }
}

.stock-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stock-name {
  font-weight: 500;
  color: var(--text-primary);
}

.stock-code {
  font-family: monospace;
  font-weight: 600;
  color: var(--accent-primary, #1976d2);
}

.industry-text {
  font-size: 13px;
  color: var(--text-secondary);
}
</style>