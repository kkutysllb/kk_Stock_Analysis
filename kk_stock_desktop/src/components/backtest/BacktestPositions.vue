<template>
  <div class="positions-container">
    <el-table
      :data="positions"
      style="width: 100%"
      :header-cell-style="{ background: 'var(--el-bg-color-page)' }"
    >
      <el-table-column prop="symbol" label="代码" width="100" />
      <el-table-column prop="name" label="名称" min-width="120" />
      <el-table-column prop="shares" label="持仓股数" width="100" align="right">
        <template #default="{ row }">
          {{ formatNumber(row.shares) }}
        </template>
      </el-table-column>
      <el-table-column prop="avg_price" label="成本价" width="100" align="right">
        <template #default="{ row }">
          ¥{{ row.avg_price.toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column prop="current_price" label="现价" width="100" align="right">
        <template #default="{ row }">
          ¥{{ row.current_price.toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column prop="market_value" label="市值" width="120" align="right">
        <template #default="{ row }">
          {{ formatCurrency(row.market_value) }}
        </template>
      </el-table-column>
      <el-table-column prop="unrealized_pnl" label="浮动盈亏" width="120" align="right">
        <template #default="{ row }">
          <span :class="{ 
            'profit': row.unrealized_pnl > 0, 
            'loss': row.unrealized_pnl < 0 
          }">
            {{ formatCurrency(row.unrealized_pnl) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="weight" label="权重" width="80" align="right">
        <template #default="{ row }">
          {{ (row.weight * 100).toFixed(2) }}%
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 汇总信息 -->
    <div class="summary-row">
      <div class="summary-item">
        <span class="summary-label">总持仓数：</span>
        <span class="summary-value">{{ positions.length }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">总市值：</span>
        <span class="summary-value">{{ formatCurrency(totalMarketValue) }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">总浮盈：</span>
        <span class="summary-value" :class="{ 
          'profit': totalUnrealizedPnl > 0, 
          'loss': totalUnrealizedPnl < 0 
        }">
          {{ formatCurrency(totalUnrealizedPnl) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElTable, ElTableColumn } from 'element-plus'
import type { Position } from '../../types/backtest'

interface Props {
  positions: Position[]
}

const props = defineProps<Props>()

// 计算属性
const totalMarketValue = computed(() => {
  return props.positions.reduce((sum, pos) => sum + pos.market_value, 0)
})

const totalUnrealizedPnl = computed(() => {
  return props.positions.reduce((sum, pos) => sum + pos.unrealized_pnl, 0)
})

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
.positions-container {
  background: var(--el-bg-color);
}

.summary-row {
  display: flex;
  justify-content: flex-end;
  gap: 24px;
  padding: 16px;
  background: var(--el-bg-color-page);
  border-top: 1px solid var(--el-border-color-light);
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.summary-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.summary-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.profit {
  color: var(--el-color-success) !important;
}

.loss {
  color: var(--el-color-danger) !important;
}
</style>