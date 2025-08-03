<template>
  <div class="index-board-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <ChartBarIcon class="icon-size"></ChartBarIcon>
        指数看板
      </h1>
      <div class="header-actions">
        <el-button @click="refreshData">
          <ArrowPathIcon class="icon-size"></ArrowPathIcon>
          刷新数据
        </el-button>
      </div>
    </div>

    <!-- 主要指数分析面板 -->
    <div class="main-indices-section">
      <h2 class="section-title">
        <PresentationChartLineIcon class="title-icon" />
        主要指数分析
      </h2>
      <MainIndicesPanel
        :initial-index="selectedIndexCode || '000001.SH'"
        :initial-period="'daily'"
        @update:selected-index="handleIndexSelect"
      ></MainIndicesPanel>
    </div>

    <!-- 成份指数分析面板 -->
    <div class="component-indices-section">
      <h2 class="section-title">
        <BuildingLibraryIcon class="title-icon" />
        成份指数分析
      </h2>
      <ComponentIndicesPanel
        :initial-index="'000016.SH'"
        :initial-period="'daily'"
        @update:selected-index="handleComponentIndexSelect"
      ></ComponentIndicesPanel>
    </div>

    <!-- 中小板块指数分析面板 -->
    <div class="small-mid-cap-section">
      <h2 class="section-title">
        <CubeIcon class="title-icon" />
        中小板块指数分析
      </h2>
      <SmallMidCapPanel
        :initial-index="selectedSmallMidCapIndexCode"
        :initial-period="'daily'"
        @update:selected-index="handleSmallMidCapIndexSelect"
      ></SmallMidCapPanel>
    </div>
    
    <!-- 申万行业指数分析面板 -->
    <div class="swan-indices-section">
      <h2 class="section-title">
        <CubeTransparentIcon class="title-icon" />
        申万行业指数分析
      </h2>
      <SwanIndicesPanel
        :initial-index="selectedSwanIndexCode"
        @update:selected-index="handleSwanIndexSelect"
      ></SwanIndicesPanel>
    </div>
    
    <!-- ETF日线分析面板 -->
    <div class="etf-daily-section">
      <h2 class="section-title">
        <CurrencyDollarIcon class="title-icon" />
        ETF日线分析
      </h2>
      <ETFDailyPanel
        :initial-etf="selectedETFCode"
        @update:selected-etf="handleETFSelect"
      ></ETFDailyPanel>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { 
  ChartBarIcon, 
  ArrowPathIcon, 
  PresentationChartLineIcon,
  BuildingLibraryIcon,
  CubeIcon,
  CubeTransparentIcon,
  CurrencyDollarIcon
} from '@heroicons/vue/24/outline'
import { useRoute } from 'vue-router'
import MainIndicesPanel from '../../components/MainIndicesPanel.vue'
import ComponentIndicesPanel from '../../components/ComponentIndicesPanel.vue'
import SmallMidCapPanel from '../../components/SmallMidCapPanel.vue'
import SwanIndicesPanel from '../../components/SwanIndicesPanel.vue'
import ETFDailyPanel from '../../components/ETFDailyPanel.vue'

// 响应式数据
const loading = ref(false)
const selectedIndexCode = ref<string | null>(null)
const selectedComponentIndexCode = ref<string>('000016.SH')
const selectedSmallMidCapIndexCode = ref<string>('000510.CSI')
const selectedSwanIndexCode = ref<string>('801010.SI')
const selectedETFCode = ref<string>('510300.SH')

// 获取路由对象，用于读取URL参数
const route = useRoute()

// 刷新数据
const refreshData = async () => {
  loading.value = true
  try {
    // console.log('刷新数据')
    
    // 刷新所有面板的数据
    // 通过触发一个时间戳更新来通知子组件刷新
    const timestamp = Date.now()
    
    // 这里可以发出事件或使用其他方式通知子组件刷新
    // 避免直接重新赋值相同的值导致频繁重渲染
    // console.log('刷新时间戳:', timestamp)
    
    // 延迟一会儿模拟加载
    await new Promise(resolve => setTimeout(resolve, 500))
  } catch (error) {
    console.error('刷新数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 处理指数选择
const handleIndexSelect = (indexCode: string) => {
  selectedIndexCode.value = indexCode
  // console.log('选中指数:', indexCode)
}

// 处理成份指数选择
const handleComponentIndexSelect = (indexCode: string) => {
  selectedComponentIndexCode.value = indexCode
  // console.log('选中成份指数:', indexCode)
}

// 处理申万行业指数选择
const handleSwanIndexSelect = (indexCode: string) => {
  selectedSwanIndexCode.value = indexCode
  // console.log('选中申万行业指数:', indexCode)
}

// 处理中小板块指数选择
const handleSmallMidCapIndexSelect = (indexCode: string) => {
  selectedSmallMidCapIndexCode.value = indexCode
  // console.log('选中中小板块指数:', indexCode) 
}


// 处理ETF选择
const handleETFSelect = (etfCode: string) => {
  selectedETFCode.value = etfCode
  // console.log('选中ETF:', etfCode)    
}

// 这里可以添加任何需要的辅助函数

// 组件挂载时，检查URL参数并设置相应的状态
onMounted(async () => {
  // 检查URL参数中是否有指数代码
  const codeParam = route.query.code as string
  
  // 如果有指数代码，保存起来
  if (codeParam) {
    selectedIndexCode.value = codeParam
  }
})
</script>

<style scoped>
.index-board-container {
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.icon-size {
  width: 24px;
  height: 24px;
}

.main-indices-section,
.component-indices-section,
.small-mid-cap-section,
.swan-indices-section,
.etf-daily-section {
  margin-bottom: var(--spacing-xl);
  height: 600px; /* 添加明确的高度 */
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
}

.title-icon {
  width: 20px;
  height: 20px;
  color: var(--accent-primary);
}

.indices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.placeholder-message {
  padding: var(--spacing-lg);
  text-align: center;
  color: var(--text-secondary);
  background: var(--bg-content);
  border-radius: var(--radius-lg);
  border: 1px dashed var(--border-color);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  padding: var(--spacing-xl);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>