<template>
  <div class="futures-analysis">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">股指期货专题分析</h1>
        <div class="header-controls">
                  <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYYMMDD"
          :disabled-date="disabledDate"
          @change="handleDateChange"
          :clearable="false"
        />
          <el-select
            v-model="selectedSymbols"
            multiple
            placeholder="选择品种"
            style="width: 300px; margin-left: 10px;"
            @change="handleSymbolChange"
          >
            <el-option
              v-for="item in symbolOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <el-button
            type="primary"
            :icon="Refresh"
            :loading="isLoading"
            @click="refreshData"
            style="margin-left: 10px;"
          >
            刷新数据
          </el-button>
        </div>
      </div>
    </div>

    <!-- 活跃期货合约汇总卡片 -->
    <div class="overview-section">
      <SummaryCards 
        :summary-data="summaryData"
        :is-loading="isLoading"
        :selected-date="selectedDate"
        :selected-symbols="selectedSymbols"
        @refresh="refreshData"
      />
    </div>

    <!-- 价格走势分析 -->
    <div class="analysis-section">
      <PriceAnalysisChart
        chart-type="kline"
        :symbols="selectedSymbols"
        :date="selectedDate"
        :loading="isLoading"
      />
    </div>

    <!-- 成交量与持仓分析 -->
    <div class="analysis-section">
      <VolumePositionChart
        chart-type="volume"
        :symbols="selectedSymbols"
        :date="selectedDate"
        :loading="isLoading"
      />
    </div>

    <!-- 期货公司持仓分析 -->
    <div class="analysis-section">
      <HoldingAnalysisChart
        chart-type="ranking"
        :symbols="selectedSymbols"
        :date="selectedDate"
        :loading="isLoading"
      />
    </div>

    <!-- 正反向市场分析 -->
    <div class="analysis-section">
      <ContangoAnalysisPanel />
    </div>


  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import SummaryCards from '@/components/analysis/SummaryCards.vue'
import PriceAnalysisChart from '@/components/analysis/PriceAnalysisChart.vue'
import VolumePositionChart from '@/components/analysis/VolumePositionChart.vue'
import HoldingAnalysisChart from '@/components/analysis/HoldingAnalysisChart.vue'

import ContangoAnalysisPanel from '@/components/ContangoAnalysisPanel.vue'
import { futuresAPI } from '@/api'

// 数据状态
const isLoading = ref(false)
const selectedDate = ref('')
const selectedSymbols = ref(['IF', 'IC', 'IH', 'IM'])
const summaryData = ref({})

// 品种选项
const symbolOptions = [
  { label: 'IF-沪深300', value: 'IF' },
  { label: 'IC-中证500', value: 'IC' },
  { label: 'IH-上证50', value: 'IH' },
  { label: 'IM-中证1000', value: 'IM' }
]

// 计算开始日期（30天前）
const startDate = computed(() => {
  if (!selectedDate.value) return ''
  const date = new Date(
    parseInt(selectedDate.value.substring(0, 4)),
    parseInt(selectedDate.value.substring(4, 6)) - 1,
    parseInt(selectedDate.value.substring(6, 8))
  )
  date.setDate(date.getDate() - 30)
  return date.getFullYear().toString() + 
         (date.getMonth() + 1).toString().padStart(2, '0') + 
         date.getDate().toString().padStart(2, '0')
})

// 禁用未来日期
const disabledDate = (time: Date) => {
  return time.getTime() > Date.now()
}

// 处理日期变化
const handleDateChange = async (value: string) => {
  selectedDate.value = value
  if (value) {
    await nextTick()
    await refreshData()
  }
}

// 处理品种变化
const handleSymbolChange = async () => {
  if (selectedSymbols.value.length > 0) {
    await nextTick()
    await refreshData()
  }
}

// 刷新数据
const refreshData = async () => {
  if (!selectedDate.value || selectedSymbols.value.length === 0) {
    return
  }

  isLoading.value = true
  try {
    // 获取活跃期货合约汇总数据
    const response = await futuresAPI.getActiveFuturesSummary(
      selectedDate.value,
      selectedSymbols.value.join(',')
    )
    
    if (response.success && response.data) {
      summaryData.value = response.data
      ElMessage.success('数据刷新成功')
    } else {
      ElMessage.warning('未获取到汇总数据')
    }
  } catch (error) {
    console.error('刷新数据失败:', error)
    ElMessage.error('数据刷新失败，请稍后重试')
  } finally {
    isLoading.value = false
  }
}

// 初始化数据
onMounted(async () => {
  // 只有当没有选择日期时，才设置默认日期为今天
  if (!selectedDate.value) {
    const today = new Date()
    const todayStr = today.getFullYear().toString() + 
                     (today.getMonth() + 1).toString().padStart(2, '0') + 
                     today.getDate().toString().padStart(2, '0')
    selectedDate.value = todayStr
    
    await nextTick()
    await refreshData()
  }
})
</script>

<style scoped>
.futures-analysis {
  padding: 20px;
  background-color: var(--el-bg-color-page);
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 20px;
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: var(--el-box-shadow-light);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.header-controls {
  display: flex;
  align-items: center;
}

.overview-section,
.analysis-section {
  margin-bottom: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .futures-analysis {
    padding: 10px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .header-controls {
    flex-direction: column;
    gap: 10px;
  }
  
  .header-controls .el-select,
  .header-controls .el-date-picker {
    width: 100% !important;
  }
}
</style>