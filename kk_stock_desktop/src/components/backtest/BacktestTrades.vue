<template>
  <div class="trades-container">
    <!-- 筛选器 -->
    <div class="filters">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-select v-model="filterAction" placeholder="交易方向" clearable>
            <el-option label="全部" value="" />
            <el-option label="买入" value="buy" />
            <el-option label="卖出" value="sell" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-input
            v-model="filterSymbol"
            placeholder="搜索股票代码或名称"
            clearable
          />
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="filterDate"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            clearable
          />
        </el-col>
      </el-row>
    </div>
    
    <!-- 交易记录表格 -->
    <el-table
      :data="paginatedTrades"
      style="width: 100%"
      :header-cell-style="{ background: 'var(--el-bg-color-page)' }"
      :default-sort="{ prop: 'date', order: 'descending' }"
    >
      <el-table-column prop="date" label="日期" width="110" sortable />
      <el-table-column prop="symbol" label="代码" width="100" />
      <el-table-column prop="name" label="名称" min-width="120" />
      <el-table-column prop="action" label="方向" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.action === 'buy' ? 'danger' : 'success'" size="small">
            {{ row.action === 'buy' ? '买入' : '卖出' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="shares" label="数量" width="100" align="right">
        <template #default="{ row }">
          {{ formatNumber(row.shares) }}
        </template>
      </el-table-column>
      <el-table-column prop="price" label="价格" width="100" align="right">
        <template #default="{ row }">
          ¥{{ row.price.toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column prop="amount" label="金额" width="120" align="right">
        <template #default="{ row }">
          {{ formatCurrency(row.amount) }}
        </template>
      </el-table-column>
      <el-table-column prop="commission" label="佣金" width="100" align="right">
        <template #default="{ row }">
          {{ formatCurrency(row.commission) }}
        </template>
      </el-table-column>
      <el-table-column prop="stamp_tax" label="印花税" width="100" align="right">
        <template #default="{ row }">
          {{ formatCurrency(row.stamp_tax) }}
        </template>
      </el-table-column>
      <el-table-column prop="total_cost" label="总成本" width="120" align="right">
        <template #default="{ row }">
          <span :class="{ 
            'buy-cost': row.action === 'buy',
            'sell-proceed': row.action === 'sell'
          }">
            {{ formatCurrency(row.total_cost) }}
          </span>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100]"
        :total="filteredTrades.length"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
    
    <!-- 统计信息 -->
    <div class="statistics">
      <div class="stat-grid">
        <div class="stat-item">
          <div class="stat-label">总交易次数</div>
          <div class="stat-value">{{ filteredTrades.length }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">买入次数</div>
          <div class="stat-value buy">{{ buyTrades.length }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">卖出次数</div>
          <div class="stat-value sell">{{ sellTrades.length }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">总交易金额</div>
          <div class="stat-value">{{ formatCurrency(totalAmount) }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">总手续费</div>
          <div class="stat-value">{{ formatCurrency(totalFees) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElTable, ElTableColumn, ElRow, ElCol, ElSelect, ElOption, ElInput, ElDatePicker, ElTag, ElPagination } from 'element-plus'
import type { Trade } from '../../types/backtest'

interface Props {
  trades: Trade[]
}

const props = defineProps<Props>()

// 筛选条件
const filterAction = ref('')
const filterSymbol = ref('')
const filterDate = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 计算属性
const filteredTrades = computed(() => {
  let filtered = props.trades

  if (filterAction.value) {
    filtered = filtered.filter(trade => trade.action === filterAction.value)
  }

  if (filterSymbol.value) {
    const searchTerm = filterSymbol.value.toLowerCase()
    filtered = filtered.filter(trade => 
      trade.symbol.toLowerCase().includes(searchTerm) ||
      trade.name.toLowerCase().includes(searchTerm)
    )
  }

  if (filterDate.value) {
    filtered = filtered.filter(trade => trade.date === filterDate.value)
  }

  return filtered
})

const paginatedTrades = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredTrades.value.slice(start, end)
})

const buyTrades = computed(() => {
  return filteredTrades.value.filter(trade => trade.action === 'buy')
})

const sellTrades = computed(() => {
  return filteredTrades.value.filter(trade => trade.action === 'sell')
})

const totalAmount = computed(() => {
  return filteredTrades.value.reduce((sum, trade) => sum + trade.amount, 0)
})

const totalFees = computed(() => {
  return filteredTrades.value.reduce((sum, trade) => 
    sum + trade.commission + trade.stamp_tax, 0)
})

// 方法
const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
}

// 工具函数
const formatNumber = (value: number) => {
  return new Intl.NumberFormat('zh-CN').format(value)
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2
  }).format(value)
}
</script>

<style scoped>
.trades-container {
  background: var(--el-bg-color);
}

.filters {
  padding: 16px;
  background: var(--el-bg-color-page);
  border-bottom: 1px solid var(--el-border-color-light);
  margin-bottom: 0;
}

.pagination {
  display: flex;
  justify-content: center;
  padding: 20px;
  background: var(--el-bg-color-page);
  border-top: 1px solid var(--el-border-color-light);
}

.statistics {
  padding: 20px;
  background: var(--el-bg-color-page);
  border-top: 1px solid var(--el-border-color-light);
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: var(--el-bg-color);
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-bottom: 8px;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.stat-value.buy {
  color: var(--el-color-danger);
}

.stat-value.sell {
  color: var(--el-color-success);
}

.buy-cost {
  color: var(--el-color-danger);
}

.sell-proceed {
  color: var(--el-color-success);
}
</style>