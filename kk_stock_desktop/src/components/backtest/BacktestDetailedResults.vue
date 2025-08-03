<template>
  <div class="detailed-results-container">
    <!-- 标签页导航 -->
    <el-tabs v-model="activeTab" class="detailed-tabs">
      <el-tab-pane name="portfolio">
        <template #label>
          <span class="tab-label">
            <BriefcaseIcon class="tab-icon" />
            持仓分析
          </span>
        </template>
        <PortfolioAnalysis 
          v-if="backtestResult"
          :portfolio-data="portfolioData"
          :chart-data="backtestResult.chart_data"
          :trades-data="tradesData"
        />
      </el-tab-pane>
      
      <el-tab-pane name="trades">
        <template #label>
          <span class="tab-label">
            <ArrowsRightLeftIcon class="tab-icon" />
            交易分析
          </span>
        </template>
        <TradesAnalysis 
          v-if="backtestResult"
          :trades-data="tradesData"
          :chart-data="backtestResult.chart_data"
        />
      </el-tab-pane>
      
      <el-tab-pane name="monthly">
        <template #label>
          <span class="tab-label">
            <CalendarDaysIcon class="tab-icon" />
            月度收益
          </span>
        </template>
        <MonthlyReturns 
          v-if="backtestResult"
          :monthly-data="backtestResult.chart_data?.monthly_heatmap"
        />
      </el-tab-pane>
      
      <el-tab-pane name="risk">
        <template #label>
          <span class="tab-label">
            <ExclamationTriangleIcon class="tab-icon" />
            风险分析
          </span>
        </template>
        <RiskAnalysis 
          v-if="backtestResult"
          :drawdown-data="backtestResult.chart_data?.drawdown"
          :performance-data="backtestResult.performance_report"
          :trades-data="tradesData"
        />
      </el-tab-pane>
      
      <el-tab-pane name="report">
        <template #label>
          <span class="tab-label">
            <DocumentTextIcon class="tab-icon" />
            分析报告
          </span>
        </template>
        <AnalysisReport 
          :report-content="markdownReport || ''"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElTabs, ElTabPane } from 'element-plus'
import {
  BriefcaseIcon,
  ArrowsRightLeftIcon,
  CalendarDaysIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon
} from '@heroicons/vue/24/outline'
import type { BacktestResult, Position, Trade } from '../../types/backtest'
import PortfolioAnalysis from './PortfolioAnalysis.vue'
import TradesAnalysis from './TradesAnalysis.vue'
import MonthlyReturns from './MonthlyReturns.vue'
import RiskAnalysis from './RiskAnalysis.vue'
import AnalysisReport from './AnalysisReport.vue'

interface Props {
  backtestResult: BacktestResult | null
  positions: Position[]
  trades: Trade[]
  markdownReport: string
}

const props = defineProps<Props>()

const activeTab = ref('portfolio')

// 计算属性：处理持仓数据
const portfolioData = computed(() => {
  if (!props.backtestResult?.chart_data?.portfolio_value) return null
  
  const chartData = props.backtestResult.chart_data.portfolio_value.data
  return {
    dates: chartData.dates,
    totalValues: chartData.portfolio_values,
    cumulativeReturns: chartData.cumulative_returns,
    dailyReturns: chartData.daily_returns || [],
    positions: props.positions
  }
})

// 计算属性：处理交易数据
const tradesData = computed(() => {
  console.log('📊 BacktestDetailedResults: 交易数据检查', {
    hasTrades: !!props.trades,
    tradesLength: props.trades?.length || 0,
    sampleTrade: props.trades?.[0]
  })
  
  if (!props.trades || props.trades.length === 0) {
    console.log('📊 BacktestDetailedResults: 没有交易数据')
    return null
  }
  
  return {
    trades: props.trades,
    summary: props.backtestResult?.trading_summary,
    tradeMetrics: props.backtestResult?.performance_report?.trade_metrics
  }
})
</script>

<style scoped>
.detailed-results-container {
  width: 100%;
  padding: 0;
}

.detailed-tabs {
  --el-tabs-header-height: 60px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border-radius: 16px;
  overflow: hidden;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  position: relative;
}

.detailed-tabs :deep(.el-tabs__header) {
  background: linear-gradient(135deg, 
    var(--el-bg-color) 0%, 
    var(--el-fill-color-extra-light) 100%);
  border-radius: 16px 16px 0 0;
  padding: 16px 32px 0 32px;
  border-bottom: 1px solid var(--el-border-color-light);
  margin: 0;
  position: relative;
  backdrop-filter: blur(10px);
}

.detailed-tabs :deep(.el-tabs__header::before) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, 
    #00d4aa 0%, 
    #409eff 25%, 
    #9c27b0 50%, 
    #ff6b6b 75%, 
    #ffd93d 100%);
  border-radius: 16px 16px 0 0;
  animation: gradientShift 3s ease-in-out infinite;
}

@keyframes gradientShift {
  0%, 100% { 
    background: linear-gradient(90deg, 
      #00d4aa 0%, 
      #409eff 25%, 
      #9c27b0 50%, 
      #ff6b6b 75%, 
      #ffd93d 100%);
  }
  50% { 
    background: linear-gradient(90deg, 
      #ffd93d 0%, 
      #00d4aa 25%, 
      #409eff 50%, 
      #9c27b0 75%, 
      #ff6b6b 100%);
  }
}

/* 标签图标样式 */
.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
  letter-spacing: 0.5px;
}

.tab-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.detailed-tabs :deep(.el-tabs__nav-wrap) {
  padding: 0;
  overflow: visible;
}

.detailed-tabs :deep(.el-tabs__nav-scroll) {
  overflow: visible;
}

.detailed-tabs :deep(.el-tabs__nav) {
  border: none;
  display: flex;
  gap: 8px;
  justify-content: center;
}

.detailed-tabs :deep(.el-tabs__item) {
  height: 44px;
  line-height: 44px;
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-regular);
  border: 2px solid transparent;
  padding: 0 20px;
  margin: 0;
  border-radius: 12px;
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  position: relative;
  background: var(--el-bg-color);
  white-space: nowrap;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 120px;
  overflow: hidden;
}

.detailed-tabs :deep(.el-tabs__item::before) {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(255, 255, 255, 0.4), 
    transparent);
  transition: left 0.6s ease;
}

.detailed-tabs :deep(.el-tabs__item:hover) {
  color: var(--el-color-primary);
  background: linear-gradient(135deg, 
    var(--el-color-primary-light-9), 
    var(--el-color-primary-light-8));
  border-color: var(--el-color-primary-light-5);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(var(--el-color-primary-rgb), 0.25);
}

.detailed-tabs :deep(.el-tabs__item:hover::before) {
  left: 100%;
}

.detailed-tabs :deep(.el-tabs__item:hover .tab-icon) {
  transform: scale(1.1) rotate(5deg);
}

.detailed-tabs :deep(.el-tabs__item.is-active) {
  background: linear-gradient(135deg, 
    var(--el-color-primary), 
    var(--el-color-primary-light-3));
  color: white;
  font-weight: 700;
  border-color: var(--el-color-primary);
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 8px 32px rgba(var(--el-color-primary-rgb), 0.4);
  z-index: 10;
  position: relative;
}

.detailed-tabs :deep(.el-tabs__item.is-active .tab-icon) {
  transform: scale(1.15);
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.detailed-tabs :deep(.el-tabs__item.is-active::after) {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, 
    transparent, 
    rgba(255, 255, 255, 0.3), 
    transparent);
  border-radius: 14px;
  z-index: -1;
  animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
  from {
    opacity: 0.5;
    transform: scale(1);
  }
  to {
    opacity: 1;
    transform: scale(1.02);
  }
}

.detailed-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.detailed-tabs :deep(.el-tabs__content) {
  padding: 32px 0 0 0;
  background: var(--el-bg-color);
  border-radius: 0 0 16px 16px;
  position: relative;
}

.detailed-tabs :deep(.el-tabs__content::before) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent, 
    var(--el-border-color-light), 
    transparent);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .detailed-results-container {
    padding: 16px;
  }
  
  .detailed-tabs :deep(.el-tabs__header) {
    padding: 12px 24px 0 24px;
  }
  
  .detailed-tabs :deep(.el-tabs__item) {
    font-size: 13px;
    padding: 0 18px;
    min-width: 110px;
    height: 42px;
    line-height: 42px;
  }
  
  .tab-label {
    font-size: 13px;
    gap: 6px;
  }
  
  .tab-icon {
    width: 15px;
    height: 15px;
  }
}

@media (max-width: 768px) {
  .detailed-results-container {
    padding: 12px;
  }
  
  .detailed-tabs {
    --el-tabs-header-height: 56px;
    border-radius: 12px;
  }
  
  .detailed-tabs :deep(.el-tabs__header) {
    padding: 8px 16px 0 16px;
    border-radius: 12px 12px 0 0;
  }
  
  .detailed-tabs :deep(.el-tabs__header::before) {
    border-radius: 12px 12px 0 0;
  }
  
  .detailed-tabs :deep(.el-tabs__nav) {
    gap: 6px;
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
    padding-bottom: 4px;
    justify-content: flex-start;
  }
  
  .detailed-tabs :deep(.el-tabs__nav)::-webkit-scrollbar {
    display: none;
  }
  
  .detailed-tabs :deep(.el-tabs__item) {
    font-size: 12px;
    padding: 0 16px;
    height: 40px;
    line-height: 40px;
    min-width: 100px;
    flex-shrink: 0;
    border-radius: 10px;
  }
  
  .tab-label {
    font-size: 12px;
    gap: 5px;
  }
  
  .tab-icon {
    width: 14px;
    height: 14px;
  }
  
  .detailed-tabs :deep(.el-tabs__content) {
    padding: 24px 0 0 0;
    border-radius: 0 0 12px 12px;
  }
}

@media (max-width: 480px) {
  .detailed-results-container {
    padding: 8px;
  }
  
  .detailed-tabs {
    border-radius: 10px;
  }
  
  .detailed-tabs :deep(.el-tabs__header) {
    border-radius: 10px 10px 0 0;
    padding: 6px 12px 0 12px;
  }
  
  .detailed-tabs :deep(.el-tabs__header::before) {
    border-radius: 10px 10px 0 0;
    height: 3px;
  }
  
  .detailed-tabs :deep(.el-tabs__item) {
    font-size: 11px;
    padding: 0 14px;
    height: 38px;
    line-height: 38px;
    min-width: 85px;
    border-radius: 8px;
  }
  
  .tab-label {
    font-size: 11px;
    gap: 4px;
  }
  
  .tab-icon {
    width: 13px;
    height: 13px;
  }
  
  .detailed-tabs :deep(.el-tabs__content) {
    padding: 20px 0 0 0;
    border-radius: 0 0 10px 10px;
  }
  
  .detailed-tabs :deep(.el-tabs__item:hover),
  .detailed-tabs :deep(.el-tabs__item.is-active) {
    transform: translateY(-1px) scale(1.02);
  }
}

/* 暗色模式优化 */
@media (prefers-color-scheme: dark) {
  .detailed-tabs :deep(.el-tabs__header) {
    background: linear-gradient(135deg, 
      var(--el-bg-color) 0%, 
      rgba(255, 255, 255, 0.05) 100%);
  }
  
  .detailed-tabs :deep(.el-tabs__item) {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .detailed-tabs :deep(.el-tabs__item:hover) {
    background: linear-gradient(135deg, 
      rgba(var(--el-color-primary-rgb), 0.2), 
      rgba(var(--el-color-primary-rgb), 0.1));
    border-color: rgba(var(--el-color-primary-rgb), 0.3);
  }
}
</style>