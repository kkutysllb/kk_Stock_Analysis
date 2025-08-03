<template>
  <div class="trend-analysis-page page-component">
    <!-- 页面标题 -->
    <div class="page-header glass-effect">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title text-gradient">
            <ArrowTrendingUpIcon class="title-icon" />
            估值&趋势分析
          </h1>
          <p class="page-subtitle">智能估值&趋势分析系统 - 支持相对估值分析、融资融券分析&道氏理论分析</p>
        </div>
        <div class="header-right">
          <!-- 股票搜索组件 -->
          <div class="header-search">
            <HeaderStockSearch 
              @stock-selected="onStockSelectedFromSearch"
            />
          </div>
          <el-button 
            v-if="selectedStock" 
            type="success" 
            @click="triggerAllAnalysis" 
            :loading="analyzing"
            :disabled="!selectedStock"
          >
            <ArrowPathIcon class="btn-icon" />
            {{ analyzing ? '分析中...' : '联动分析' }}
          </el-button>
          <el-button type="primary" @click="refreshAllData" :loading="refreshing">
            <ArrowPathIcon class="btn-icon" />
            刷新数据
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="page-content">
      <div class="content-grid">
        <!-- 分析面板 -->
        <div class="content-main">
          <!-- 估值分析组件区域 -->
          <div class="valuation-analysis-section">
            <!-- 相对估值分析面板 - 全宽布局 -->
            <RelativeValuationPanel 
              ref="valuationAnalysisRef"
              :selectedStock="selectedStock"
              @analysis-completed="onAnalysisCompleted"
              @stock-selected="onStockSelected"
            />
          </div>


          <!-- 融资融券分析面板 -->
          <div class="margin-trading-section">
            <MarginTradingPanel 
              ref="marginAnalysisRef"
              :selectedStock="selectedStock"
              @analysis-completed="onAnalysisCompleted"
              @stock-selected="onStockSelected"
            />
          </div>

          <!-- 道氏理论分析面板 -->
          <DowTheoryAnalysisPanel 
            ref="dowAnalysisRef"
            :selectedStock="selectedStock"
            @analysis-completed="onAnalysisCompleted"
            @stock-selected="onStockSelected"
          />

        </div>
      </div>

    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  ArrowTrendingUpIcon, 
  ArrowPathIcon
} from '@heroicons/vue/24/outline'

// 导入组件
import DowTheoryAnalysisPanel from '@/components/analysis/DowTheoryAnalysisPanel.vue'
import RelativeValuationPanel from '@/components/analysis/RelativeValuationPanel.vue'
import MarginTradingPanel from '@/components/analysis/MarginTradingPanel.vue'
import HeaderStockSearch from '@/components/analysis/HeaderStockSearch.vue'

// 导入API
import { apiClient } from '@/api/base'

// 路由 (预留)

// 类型定义
interface SelectedStock {
  code: string
  name: string
  poolId?: string
}

interface AnalysisResult {
  id: string
  stockCode: string
  stockName: string
  analysisType?: string
  overallTrend: string
  overallPhase: string
  confidence: number
  recommendation: string
  analysisDate: string
  detailed: any
}


// 响应式数据
const dowAnalysisRef = ref()
const valuationAnalysisRef = ref()
const marginAnalysisRef = ref()
const refreshing = ref(false)
const analyzing = ref(false)

// 选中的股票
const selectedStock = ref<SelectedStock | null>(null)

// 分析结果
const analysisResults = ref<AnalysisResult[]>([])

// 计算属性（已移除未使用的hasSelectedStock）

// 方法
const triggerAllAnalysis = async () => {
  if (!selectedStock.value) {
    ElMessage.warning('请先选择股票')
    return
  }

  analyzing.value = true
  // console.log('开始联动分析:', selectedStock.value)
  
  // 显示分析开始的提示
  ElMessage({
    message: `正在分析 ${selectedStock.value.name} (${selectedStock.value.code})...`,
    type: 'info',
    duration: 2000
  })
  
  try {
    const analysisPromises: Promise<any>[] = []
    let analysisResults: { component: string; success: boolean; error?: any }[] = []
    
    // 辅助函数：安全调用组件分析方法
    const safeCallAnalysis = async (
      componentName: string, 
      analysisMethod: () => any
    ): Promise<{ component: string; success: boolean; error?: any }> => {
      try {
        // console.log(`开始${componentName}...`)
        const result = analysisMethod()
        
        // 如果返回Promise，等待完成
        if (result && typeof result.then === 'function') {
          await result
          // console.log(`${componentName}完成`)
          return { component: componentName, success: true }
        } else {
          // 如果不是Promise，认为同步完成
          // console.log(`${componentName}同步完成`)
          return { component: componentName, success: true }
        }
      } catch (error) {
        // console.error(`${componentName}失败:`, error)
        return { component: componentName, success: false, error }
      }
    }
    
    // 触发相对估值分析
    if (valuationAnalysisRef.value?.triggerAnalysis) {
      analysisPromises.push(
        safeCallAnalysis('相对估值分析', () => valuationAnalysisRef.value.triggerAnalysis())
      )
    }
    
    // 触发融资融券分析
    if (marginAnalysisRef.value?.triggerAnalysis) {
      analysisPromises.push(
        safeCallAnalysis('融资融券分析', () => marginAnalysisRef.value.triggerAnalysis())
      )
    }
    
    // 触发道氏理论分析
    if (dowAnalysisRef.value?.startAnalysis) {
      analysisPromises.push(
        safeCallAnalysis('道氏理论分析', () => dowAnalysisRef.value.startAnalysis())
      )
    }
    
    // 等待所有分析完成
    if (analysisPromises.length > 0) {
      analysisResults = await Promise.all(analysisPromises)
      // console.log('所有分析完成:', analysisResults)
    }
    
    // 统计结果
    const successCount = analysisResults.filter(r => r.success).length
    const failedCount = analysisResults.filter(r => !r.success).length
    
    // 显示完成消息
    if (successCount > 0) {
      if (failedCount > 0) {
        ElMessage({
          type: 'warning',
          message: `联动分析完成！成功 ${successCount} 个，失败 ${failedCount} 个组件`
        })
      } else {
        ElMessage.success(`联动分析完成！已成功触发 ${successCount} 个组件分析`)
      }
    } else if (analysisResults.length > 0) {
      ElMessage.error('所有组件分析都失败了，请检查网络连接和数据')
    } else {
      ElMessage.warning('未找到可用的分析组件')
    }
    
  } catch (error) {
    console.error('联动分析系统错误:', error)
    ElMessage.error(`联动分析失败: ${error instanceof Error ? error.message : '未知错误'}`)
  } finally {
    analyzing.value = false
  }
}

const refreshAllData = async () => {
  refreshing.value = true
  try {
    if (selectedStock.value) {
      await triggerAllAnalysis()
      ElMessage.success('数据刷新成功')
    } else {
      ElMessage.warning('请先选择股票')
    }
  } catch (error) {
    console.error('刷新数据失败:', error)
    ElMessage.error('刷新数据失败')
  } finally {
    refreshing.value = false
  }
}

const onStockSelected = (stock: SelectedStock) => {
  selectedStock.value = stock
  // console.log('选中股票:', stock)
}

const onStockSelectedFromSearch = async (stock: SelectedStock) => {
  selectedStock.value = stock
  // console.log('从搜索选中股票:', stock)
  ElMessage.success(`已选择股票: ${stock.name} (${stock.code})`)
  
  // 自动开始联动分析
  await triggerAllAnalysis()
}


const onAnalysisCompleted = async (result: AnalysisResult) => {
  try {
    // 根据分析类型决定是否保存到后端数据库
    if (result.analysisType !== 'margin_trading') {
      await saveAnalysisResultToBackend(result)
    }
    
    // 检查是否有同一股票同一分析类型在短时间内的重复分析
    const now = new Date(result.analysisDate)
    const recentThreshold = 5 * 60 * 1000 // 5分钟内认为是重复分析
    
    const existingIndex = analysisResults.value.findIndex(r => {
      if (r.stockCode !== result.stockCode) {
        return false
      }
      
      // 检查分析类型和时间差
      if (r.analysisType && result.analysisType && r.analysisType !== result.analysisType) {
        return false
      }
      
      const existingTime = new Date(r.analysisDate)
      const timeDiff = Math.abs(now.getTime() - existingTime.getTime())
      return timeDiff < recentThreshold
    })
    
    if (existingIndex >= 0) {
      // 如果是短时间内的重复分析，替换旧结果
      // console.log('替换近期分析结果:', result)
      analysisResults.value[existingIndex] = result
    } else {
      // 否则添加新结果到开头（不同日期的分析结果会保留）
      // console.log('添加新分析结果:', result)
      analysisResults.value.unshift(result)
    }
    
    // 保持最多显示50个结果（增加容量以容纳历史分析）
    if (analysisResults.value.length > 50) {
      analysisResults.value = analysisResults.value.slice(0, 50)
    }
    
    // 根据分析类型显示成功消息
    const analysisTypeNames: Record<string, string> = {
      'dow_theory': '道氏理论分析',
      'relative_valuation': '相对估值分析',
      'margin_trading': '融资融券分析'
    }
    const typeName = analysisTypeNames[result.analysisType || 'dow_theory'] || '分析'
    
    if (result.analysisType === 'margin_trading') {
      ElMessage.success(`${typeName}完成`)
    } else {
      ElMessage.success(`${typeName}结果已保存到后端数据库`)
    }
  } catch (error) {
    console.error('保存分析结果失败:', error)
    ElMessage.warning('分析完成，但保存到数据库失败')
    
    // 即使保存失败，也要更新前端显示
    const now = new Date(result.analysisDate)
    const recentThreshold = 5 * 60 * 1000
    
    const existingIndex = analysisResults.value.findIndex(r => {
      if (r.stockCode !== result.stockCode) {
        return false
      }
      if (r.analysisType && result.analysisType && r.analysisType !== result.analysisType) {
        return false
      }
      const existingTime = new Date(r.analysisDate)
      const timeDiff = Math.abs(now.getTime() - existingTime.getTime())
      return timeDiff < recentThreshold
    })
    
    if (existingIndex >= 0) {
      analysisResults.value[existingIndex] = result
    } else {
      analysisResults.value.unshift(result)
    }
    
    if (analysisResults.value.length > 50) {
      analysisResults.value = analysisResults.value.slice(0, 50)
    }
  }
}


// 保存分析结果到后端数据库
const saveAnalysisResultToBackend = async (result: AnalysisResult) => {
  try {
    const analysisData = {
      stock_code: result.stockCode,
      stock_name: result.stockName,
      analysis_type: 'dow_theory',
      overall_trend: result.overallTrend,
      overall_phase: result.overallPhase || 'unknown',
      confidence: result.confidence,
      recommendation: result.recommendation,
      detailed_analysis: result.detailed,
      tags: [],
      notes: null
    }
    
    const response = await apiClient.post('/user/analysis-results/', analysisData)
    
    if (response.success) {
      // console.log('分析结果保存成功:', response.data)
      return response.data
    } else {
      throw new Error(response.message || '保存失败')
    }
  } catch (error: any) {
    console.error('保存分析结果到后端失败:', error)
    throw error
  }
}

// 加载历史分析结果
const loadHistoryAnalysisResults = async () => {
  try {
    // console.log('开始加载历史分析结果...')
    const response = await apiClient.get('/user/analysis-results/', {
      params: {
        page: 1,
        page_size: 50,
        include_archived: false
      }
    })
    
    if (response.success && response.data) {
      // 转换后端数据格式为前端格式
      const historyResults = response.data.map((item: any) => ({
        id: item.result_id,
        stockCode: item.stock_code,
        stockName: item.stock_name,
        overallTrend: item.overall_trend,
        overallPhase: item.overall_phase || 'unknown',
        confidence: item.confidence,
        recommendation: item.recommendation,
        analysisDate: item.create_time,
        detailed: {} // 简化版本，详情通过点击获取
      }))
      
      analysisResults.value = historyResults
      // console.log('加载历史分析结果成功:', analysisResults.value.length, '条')
      
      if (historyResults.length > 0) {
        ElMessage.success(`已加载 ${historyResults.length} 条历史分析记录`)
      }
    } else {
      // console.log('没有找到历史分析结果')
    }
  } catch (error: any) {
    console.error('加载历史分析结果失败:', error)
    ElMessage.error(`加载历史记录失败: ${error?.message || '未知错误'}`)
  }
}

// 生命周期
onMounted(async () => {
  // console.log('趋势分析页面已加载')
  // 加载历史分析结果
  await loadHistoryAnalysisResults()
})
</script>

<style scoped>
.trend-analysis-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: var(--spacing-lg);
}

/* ========== 页面标题区域 ========== */
.page-header {
  padding: var(--spacing-lg);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  background: var(--bg-secondary);
}

.header-content {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-lg);
  min-height: 60px;
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 var(--spacing-sm) 0;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.title-icon {
  width: 32px;
  height: 32px;
  color: var(--accent-primary);
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex: 1;
  justify-content: flex-end;
}

.header-search {
  width: 280px;
  margin-right: var(--spacing-lg);
  flex-shrink: 0;
}

.btn-icon {
  width: 16px;
  height: 16px;
  margin-right: var(--spacing-xs);
}

/* ========== 页面内容区域 ========== */
.page-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  min-height: 0;
}

.content-grid {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  min-height: 600px; /* 移除固定高度限制，允许内容自然展开 */
}

.content-main {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  width: 100%;
}

/* ========== 估值分析组件区域 ========== */
.valuation-analysis-section {
  width: 100%;
  margin-bottom: var(--spacing-2xl);
  height: auto;
  min-height: 800px;
  position: relative;
}

/* 为估值分析添加底部视觉分隔 */
.valuation-analysis-section::after {
  content: '';
  position: absolute;
  bottom: -24px;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
  border-radius: 1px;
}

/* ========== 融资融券分析组件区域 ========== */
.margin-trading-section {
  width: 100%;
  margin: var(--spacing-2xl) 0;
  height: auto;
  min-height: 600px;
  position: relative;
}

/* 添加视觉分隔线 */
.margin-trading-section::before {
  content: '';
  position: absolute;
  top: -24px;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
  border-radius: 1px;
}

.valuation-panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
  width: 100%;
  height: 100%;
}

.valuation-panel-wrapper {
  height: 100%; /* 恢复固定高度，占满父容器 */
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 恢复隐藏溢出 */
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  background: var(--bg-secondary);
}



/* ========== 响应式设计 ========== */
@media (max-width: 1200px) {
  .valuation-analysis-section {
    height: 1200px; /* 垂直布局时增加高度 */
  }
  
  .valuation-panels {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-md);
  }
  
  .header-right {
    justify-content: center;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .content-grid {
    gap: var(--spacing-md);
  }
  
  .valuation-analysis-section {
    height: 800px; /* 移动端设置固定高度 */
    margin-bottom: var(--spacing-xl);
  }
  
  .margin-trading-section {
    margin: var(--spacing-xl) 0;
    min-height: 500px;
  }
  
  .valuation-panels {
    gap: var(--spacing-sm);
  }
  
  /* 移动端分隔线样式调整 */
  .valuation-analysis-section::after,
  .margin-trading-section::before {
    width: 40px;
    height: 1px;
  }
}

/* ========== Element Plus 样式覆盖 ========== */
:deep(.el-button) {
  border-radius: var(--radius-md);
  font-weight: 500;
  transition: all var(--transition-base);
}

:deep(.el-button--primary) {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
}

:deep(.el-button--primary:hover) {
  background: var(--neon-cyan);
  border-color: var(--neon-cyan);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
}

:deep(.el-button:not(.el-button--primary)) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  backdrop-filter: blur(10px);
  font-weight: 500;
  font-size: 12px;
}

:deep(.el-button:not(.el-button--primary):hover) {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* ========== Element Plus Select 样式 ========== */
:deep(.el-select) {
  --el-select-border-color-hover: var(--accent-primary);
  --el-select-input-focus-border-color: var(--accent-primary);
}

:deep(.el-select .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  backdrop-filter: blur(10px);
  transition: all 0.2s ease;
  min-height: 24px;
  padding: 0 6px;
}

:deep(.el-select .el-input__wrapper:hover) {
  border-color: var(--accent-primary);
  background: rgba(255, 255, 255, 0.05);
}

:deep(.el-select .el-input__wrapper.is-focus) {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 1px rgba(0, 212, 255, 0.15);
  background: rgba(255, 255, 255, 0.05);
}

:deep(.el-select .el-input__inner) {
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 500;
  height: 22px;
  line-height: 22px;
}

:deep(.el-select-dropdown) {
  background: rgba(30, 30, 30, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  backdrop-filter: blur(20px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

:deep(.el-select-dropdown__item) {
  color: var(--text-primary);
  font-size: 11px;
  line-height: 24px;
  padding: 2px 8px;
  transition: all 0.2s ease;
}

:deep(.el-select-dropdown__item:hover) {
  background: rgba(0, 212, 255, 0.1);
  color: var(--accent-primary);
}

:deep(.el-select-dropdown__item.selected) {
  background: rgba(0, 212, 255, 0.2);
  color: var(--accent-primary);
  font-weight: 600;
}

/* ========== 分析类型选择器 ========== */
.analysis-type-selector {
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  background: var(--bg-secondary);
  display: flex;
  justify-content: center;
  align-items: center;
}

:deep(.el-radio-group) {
  display: flex;
  gap: 0;
}

:deep(.el-radio-button) {
  margin: 0;
}

:deep(.el-radio-button__inner) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  font-weight: 500;
  font-size: 14px;
  padding: 8px 16px;
  transition: all var(--transition-base);
}

:deep(.el-radio-button__inner:hover) {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

:deep(.el-radio-button.is-active .el-radio-button__inner) {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: #000;
  font-weight: 600;
}

:deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-top-left-radius: var(--radius-md);
  border-bottom-left-radius: var(--radius-md);
}

:deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-top-right-radius: var(--radius-md);
  border-bottom-right-radius: var(--radius-md);
}
</style>