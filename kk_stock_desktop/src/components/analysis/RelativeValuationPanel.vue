<template>
  <div class="relative-valuation-panel glass-effect">
    <!-- 面板标题 -->
    <div class="panel-header">
      <div class="panel-title">
        <ScaleIcon class="title-icon" />
        <span>相对估值分析</span>
        <el-tag v-if="selectedStock" size="small" type="info">
          {{ selectedStock.code }} {{ selectedStock.name }}
        </el-tag>
      </div>
      <div class="panel-actions">
        <el-button 
          size="small" 
          type="primary"
          :loading="analyzing"
          :disabled="!hasValidStock"
          @click="triggerAnalysis"
        >
          <AdjustmentsHorizontalIcon class="action-icon" v-if="!analyzing" />
          {{ analyzing ? '分析中...' : '开始分析' }}
        </el-button>
      </div>
    </div>

    <!-- 面板内容 -->
    <div class="panel-content scrollable-content">
      <!-- 分析结果 - 直接显示，无条件渲染 -->
      <div class="analysis-result">
        <!-- 估值指标概览 -->
        <div class="result-section">
          <h4 class="section-title">
            <ScaleIcon class="title-icon" />
            估值指标概览
          </h4>
          <div class="valuation-overview">
            <div class="valuation-grid">
              <!-- PE指标 -->
              <div class="metric-mini-card">
                <div class="metric-header-mini">
                  <ChartBarIcon class="metric-icon-mini" />
                  <span class="metric-name">市盈率 (PE)</span>
                </div>
                <div class="metric-value-large">{{ analysisResult?.current_metrics?.pe_ratio?.toFixed(2) || 'N/A' }}</div>
                <div class="metric-comparison-mini">
                  <div class="comparison-item-mini">
                    <span class="label-mini">行业中位数</span>
                    <span class="value-mini">{{ analysisResult?.industry_comparison?.pe_median?.toFixed(2) || 'N/A' }}</span>
                  </div>
                  <div class="comparison-item-mini">
                    <span class="label-mini">相对位置</span>
                    <el-tag size="small" :type="getPEComparisonType(analysisResult?.current_metrics?.pe_ratio, analysisResult?.industry_comparison?.pe_median)">
                      {{ analysisResult?.industry_comparison?.pe_rating || 'N/A' }}
                    </el-tag>
                  </div>
                </div>
              </div>

              <!-- PB指标 -->
              <div class="metric-mini-card">
                <div class="metric-header-mini">
                  <BookOpenIcon class="metric-icon-mini" />
                  <span class="metric-name">市净率 (PB)</span>
                </div>
                <div class="metric-value-large">{{ analysisResult?.current_metrics?.pb_ratio?.toFixed(2) || 'N/A' }}</div>
                <div class="metric-comparison-mini">
                  <div class="comparison-item-mini">
                    <span class="label-mini">行业中位数</span>
                    <span class="value-mini">{{ analysisResult?.industry_comparison?.pb_median?.toFixed(2) || 'N/A' }}</span>
                  </div>
                  <div class="comparison-item-mini">
                    <span class="label-mini">相对位置</span>
                    <el-tag size="small" :type="getPBComparisonType(analysisResult?.current_metrics?.pb_ratio, analysisResult?.industry_comparison?.pb_median)">
                      {{ analysisResult?.industry_comparison?.pb_rating || 'N/A' }}
                    </el-tag>
                  </div>
                </div>
              </div>

              <!-- PS指标 -->
              <div class="metric-mini-card">
                <div class="metric-header-mini">
                  <CurrencyDollarIcon class="metric-icon-mini" />
                  <span class="metric-name">市销率 (PS)</span>
                </div>
                <div class="metric-value-large">{{ analysisResult?.current_metrics?.ps_ratio?.toFixed(2) || 'N/A' }}</div>
                <div class="metric-comparison-mini">
                  <div class="comparison-item-mini">
                    <span class="label-mini">行业中位数</span>
                    <span class="value-mini">{{ analysisResult?.industry_comparison?.ps_median?.toFixed(2) || 'N/A' }}</span>
                  </div>
                  <div class="comparison-item-mini">
                    <span class="label-mini">相对位置</span>
                    <el-tag size="small" :type="getPSComparisonType(analysisResult?.current_metrics?.ps_ratio, analysisResult?.industry_comparison?.ps_median)">
                      {{ analysisResult?.industry_comparison?.ps_rating || 'N/A' }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>




        <!-- 动态估值分析 -->
        <div v-if="analysisResult?.dynamic_valuation" class="result-section dynamic-analysis-section">
          <h4 class="section-title">动态估值分析</h4>
          <div class="dynamic-valuation">
            <!-- PEG比率分析 -->
            <div class="dynamic-metric-group">
              <h5 class="metric-group-title">PEG比率分析</h5>
              <div class="peg-analysis-grid">
                <div class="peg-item">
                  <div class="peg-label">1年PEG</div>
                  <div class="peg-value">{{ analysisResult?.dynamic_valuation?.dynamic_metrics?.peg_1y?.toFixed(2) || 'N/A' }}</div>
                  <div class="peg-desc">基于1年增长率</div>
                </div>
                <div class="peg-item">
                  <div class="peg-label">3年PEG</div>
                  <div class="peg-value">{{ analysisResult?.dynamic_valuation?.dynamic_metrics?.peg_3y?.toFixed(2) || 'N/A' }}</div>
                  <div class="peg-desc">基于3年增长率</div>
                </div>
                <div class="peg-item">
                  <div class="peg-label">PEG评级</div>
                  <el-tag size="small" :type="getPEGRatingType(analysisResult?.dynamic_valuation?.dynamic_metrics?.peg_rating)">
                    {{ analysisResult?.dynamic_valuation?.dynamic_metrics?.peg_rating || 'N/A' }}
                  </el-tag>
                  <div class="peg-desc">综合PEG评级</div>
                </div>
                <div class="peg-item">
                  <div class="peg-label">前瞻PE</div>
                  <div class="peg-value">{{ analysisResult?.dynamic_valuation?.dynamic_metrics?.forward_pe?.toFixed(1) || 'N/A' }}</div>
                  <div class="peg-desc">基于预测增长</div>
                </div>
              </div>
            </div>

            <!-- 成长性分析 -->
            <div class="dynamic-metric-group">
              <h5 class="metric-group-title">成长性分析</h5>
              <div class="growth-analysis-grid">
                <div class="growth-item">
                  <div class="metric-header-mini">
                    <ArrowTrendingUpIcon class="metric-icon-mini" />
                    <span class="metric-name">成长可持续性</span>
                  </div>
                  <div class="metric-value-large">{{ Math.round(analysisResult?.dynamic_valuation?.growth_metrics?.growth_sustainability_score || 0) }}</div>
                  <div class="metric-comparison-mini">
                    <div class="comparison-item-mini">
                      <span class="label-mini">趋势评价</span>
                      <span class="value-mini">{{ analysisResult?.dynamic_valuation?.growth_metrics?.growth_trend || 'N/A' }}</span>
                    </div>
                  </div>
                </div>
                <div class="growth-item">
                  <div class="metric-header-mini">
                    <ChartBarIcon class="metric-icon-mini" />
                    <span class="metric-name">营收增长(1年)</span>
                  </div>
                  <div class="metric-value-large">{{ (analysisResult?.dynamic_valuation?.growth_metrics?.revenue_growth_1y || 0).toFixed(1) }}%</div>
                  <div class="metric-comparison-mini">
                    <div class="comparison-item-mini">
                      <span class="label-mini">稳定性</span>
                      <span class="value-mini">{{ analysisResult?.dynamic_valuation?.growth_metrics?.revenue_growth_stability || 'N/A' }}</span>
                    </div>
                  </div>
                </div>
                <div class="growth-item">
                  <div class="metric-header-mini">
                    <CurrencyDollarIcon class="metric-icon-mini" />
                    <span class="metric-name">利润增长(1年)</span>
                  </div>
                  <div class="metric-value-large">{{ (analysisResult?.dynamic_valuation?.growth_metrics?.profit_growth_1y || 0).toFixed(1) }}%</div>
                  <div class="metric-comparison-mini">
                    <div class="comparison-item-mini">
                      <span class="label-mini">稳定性</span>
                      <span class="value-mini">{{ analysisResult?.dynamic_valuation?.growth_metrics?.profit_growth_stability || 'N/A' }}</span>
                    </div>
                  </div>
                </div>
                <div class="growth-item">
                  <div class="metric-header-mini">
                    <ArrowTrendingUpIcon class="metric-icon-mini" />
                    <span class="metric-name">营收增长(3年)</span>
                  </div>
                  <div class="metric-value-large">{{ (analysisResult?.dynamic_valuation?.growth_metrics?.revenue_growth_3y || 0).toFixed(1) }}%</div>
                  <div class="metric-comparison-mini">
                    <div class="comparison-item-mini">
                      <span class="label-mini">复合增长</span>
                      <span class="value-mini">CAGR</span>
                    </div>
                  </div>
                </div>
                <div class="growth-item">
                  <div class="metric-header-mini">
                    <CurrencyDollarIcon class="metric-icon-mini" />
                    <span class="metric-name">利润增长(3年)</span>
                  </div>
                  <div class="metric-value-large">{{ (analysisResult?.dynamic_valuation?.growth_metrics?.profit_growth_3y || 0).toFixed(1) }}%</div>
                  <div class="metric-comparison-mini">
                    <div class="comparison-item-mini">
                      <span class="label-mini">复合增长</span>
                      <span class="value-mini">CAGR</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 盈利质量分析 -->
            <div class="dynamic-metric-group">
              <h5 class="metric-group-title">盈利质量分析</h5>
              <div class="profitability-analysis-grid">
                <div class="profitability-item">
                  <div class="metric-header-mini">
                    <TrophyIcon class="metric-icon-mini" />
                    <span class="metric-name">盈利质量</span>
                  </div>
                  <div class="metric-value-large">{{ Math.round(analysisResult?.dynamic_valuation?.profitability_metrics?.quality_score || 0) }}</div>
                  <div class="metric-comparison-mini">
                    <div class="comparison-item-mini">
                      <span class="label-mini">ROE趋势</span>
                      <span class="value-mini">{{ analysisResult?.dynamic_valuation?.profitability_metrics?.roe_trend || 'N/A' }}</span>
                    </div>
                  </div>
                </div>
                <div class="profitability-item">
                  <div class="metric-header-mini">
                    <BanknotesIcon class="metric-icon-mini" />
                    <span class="metric-name">ROE</span>
                  </div>
                  <div class="metric-value-large">{{ (analysisResult?.dynamic_valuation?.profitability_metrics?.roe || 0).toFixed(2) }}%</div>
                  <div class="metric-comparison-mini">
                    <div class="comparison-item-mini">
                      <span class="label-mini">股东回报</span>
                      <span class="value-mini">净资产收益率</span>
                    </div>
                  </div>
                </div>
                <div class="profitability-item">
                  <div class="metric-header-mini">
                    <ShieldCheckIcon class="metric-icon-mini" />
                    <span class="metric-name">ROA</span>
                  </div>
                  <div class="metric-value-large">{{ (analysisResult?.dynamic_valuation?.profitability_metrics?.roa || 0).toFixed(2) }}%</div>
                  <div class="metric-comparison-mini">
                    <div class="comparison-item-mini">
                      <span class="label-mini">资产效率</span>
                      <span class="value-mini">总资产收益率</span>
                    </div>
                  </div>
                </div>
                <div class="profitability-item">
                  <div class="metric-header-mini">
                    <PresentationChartLineIcon class="metric-icon-mini" />
                    <span class="metric-name">毛利率</span>
                  </div>
                  <div class="metric-value-large">{{ (analysisResult?.dynamic_valuation?.profitability_metrics?.gross_margin || 0).toFixed(2) }}%</div>
                  <div class="metric-comparison-mini">
                    <div class="comparison-item-mini">
                      <span class="label-mini">盈利能力</span>
                      <span class="value-mini">营业利润率</span>
                    </div>
                  </div>
                </div>
                <div class="profitability-item">
                  <div class="metric-header-mini">
                    <ArrowTrendingUpIcon class="metric-icon-mini" />
                    <span class="metric-name">现金转换率</span>
                  </div>
                  <div class="metric-value-large">{{ (analysisResult?.dynamic_valuation?.profitability_metrics?.cash_conversion_ratio || 0).toFixed(1) }}%</div>
                  <div class="metric-comparison-mini">
                    <div class="comparison-item-mini">
                      <span class="label-mini">现金质量</span>
                      <span class="value-mini">经营现金流</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 综合评级 -->
            <div class="dynamic-metric-group">
              <h5 class="metric-group-title">综合动态评级</h5>
              <div class="rating-cards-grid">
                <!-- 主要评级卡片 -->
                <div class="rating-main-card">
                  <div class="rating-card-header">
                    <TrophyIcon class="rating-icon" />
                    <span class="rating-card-title">综合评级</span>
                  </div>
                  <div class="rating-display">
                    <el-progress 
                      type="circle" 
                      :percentage="Math.round(analysisResult?.dynamic_valuation?.comprehensive_rating?.comprehensive_score || 0)" 
                      :width="80"
                      :stroke-width="6"
                      :color="getComprehensiveScoreColor(analysisResult?.dynamic_valuation?.comprehensive_rating?.comprehensive_score)"
                    >
                      <template #default="{ percentage }">
                        <div class="rating-score-display">
                          <div class="score-number">{{ percentage }}</div>
                          <div class="score-label">分</div>
                        </div>
                      </template>
                    </el-progress>
                    <div class="rating-level-text">{{ analysisResult?.dynamic_valuation?.comprehensive_rating?.comprehensive_rating || 'N/A' }}</div>
                  </div>
                </div>
                
                <!-- 静态评级卡片 -->
                <div class="rating-sub-card">
                  <div class="rating-card-header">
                    <ScaleIcon class="rating-icon" />
                    <span class="rating-card-title">静态评级</span>
                  </div>
                  <div class="rating-content">
                    <div class="rating-score-large">{{ (analysisResult?.dynamic_valuation?.comprehensive_rating?.static_score || 0).toFixed(0) }}</div>
                    <div class="rating-label">分</div>
                    <el-tag size="small" :type="getComprehensiveRatingType(analysisResult?.dynamic_valuation?.comprehensive_rating?.static_rating)">
                      {{ analysisResult?.dynamic_valuation?.comprehensive_rating?.static_rating || 'N/A' }}
                    </el-tag>
                  </div>
                </div>
                
                <!-- 成长评分卡片 -->
                <div class="rating-sub-card">
                  <div class="rating-card-header">
                    <ArrowTrendingUpIcon class="rating-icon" />
                    <span class="rating-card-title">成长评分</span>
                  </div>
                  <div class="rating-content">
                    <div class="rating-score-large growth-score">{{ (analysisResult?.dynamic_valuation?.comprehensive_rating?.growth_score || 0).toFixed(0) }}</div>
                    <div class="rating-label">分</div>
                    <div class="rating-desc">成长潜力</div>
                  </div>
                </div>
                
                <!-- 质量评分卡片 -->
                <div class="rating-sub-card">
                  <div class="rating-card-header">
                    <ShieldCheckIcon class="rating-icon" />
                    <span class="rating-card-title">质量评分</span>
                  </div>
                  <div class="rating-content">
                    <div class="rating-score-large quality-score">{{ (analysisResult?.dynamic_valuation?.comprehensive_rating?.quality_score || 0).toFixed(0) }}</div>
                    <div class="rating-label">分</div>
                    <div class="rating-desc">盈利质量</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 投资建议 -->
        <div class="result-section">
          <h4 class="section-title">投资建议</h4>
          <div class="investment-advice">
            <div class="advice-grid">
              <!-- 动态投资建议卡片 -->
              <div v-if="analysisResult?.dynamic_valuation?.investment_recommendation" class="advice-card dynamic-advice-card">
                <div class="advice-card-header">
                  <TrophyIcon class="advice-icon" />
                  <span class="advice-title">动态估值建议</span>
                </div>
                <div class="advice-rating-display">
                  <div class="rating-circle" :class="getInvestmentActionClass(analysisResult?.dynamic_valuation?.investment_recommendation?.investment_action)">
                    <span class="rating-text">{{ analysisResult?.dynamic_valuation?.investment_recommendation?.investment_action || 'N/A' }}</span>
                  </div>
                  <div class="rating-info">
                    <div class="confidence-level">信心度: {{ analysisResult?.dynamic_valuation?.investment_recommendation?.confidence_level || 'N/A' }}</div>
                    <div class="time-horizon">期限: {{ analysisResult?.dynamic_valuation?.investment_recommendation?.time_horizon || 'N/A' }}</div>
                  </div>
                </div>
                <div class="advice-description">{{ analysisResult?.dynamic_valuation?.investment_recommendation?.recommendation_rationale || '暂无说明' }}</div>
                
                <!-- 风险和催化因素 -->
                <div class="risk-catalyst-grid">
                  <div v-if="analysisResult?.dynamic_valuation?.investment_recommendation?.key_risks?.length > 0" class="risk-section">
                    <h6 class="section-subtitle">主要风险</h6>
                    <div class="tag-list">
                      <el-tag 
                        v-for="risk in analysisResult.dynamic_valuation.investment_recommendation.key_risks" 
                        :key="risk" 
                        size="small" 
                        type="danger"
                      >
                        {{ risk }}
                      </el-tag>
                    </div>
                  </div>
                  <div v-if="analysisResult?.dynamic_valuation?.investment_recommendation?.catalysts?.length > 0" class="catalyst-section">
                    <h6 class="section-subtitle">催化因素</h6>
                    <div class="tag-list">
                      <el-tag 
                        v-for="catalyst in analysisResult.dynamic_valuation.investment_recommendation.catalysts" 
                        :key="catalyst" 
                        size="small" 
                        type="success"
                      >
                        {{ catalyst }}
                      </el-tag>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 静态投资建议卡片 -->
              <div class="advice-card static-advice-card">
                <div class="advice-card-header">
                  <ChartBarIcon class="advice-icon" />
                  <span class="advice-title">静态估值建议</span>
                </div>
                <div class="advice-rating-display">
                  <div class="rating-circle" :class="getRatingClass(analysisResult?.investment_advice)">
                    <span class="rating-text">{{ getAdviceRatingText(analysisResult?.investment_advice) }}</span>
                  </div>
                  <div class="rating-info">
                    <div class="advice-level">{{ getAdviceTitle(analysisResult?.investment_advice) }}</div>
                  </div>
                </div>
                <div class="advice-description">{{ analysisResult?.investment_advice || '暂无建议' }}</div>
                
                <div class="advice-metrics-grid">
                  <div class="metric-item">
                    <div class="metric-label">目标PE</div>
                    <div class="metric-value price-value">{{ analysisResult?.dynamic_valuation?.valuation_forecast?.target_pe?.toFixed(1) || 'N/A' }}</div>
                  </div>
                  <div class="metric-item">
                    <div class="metric-label">预测增长(营收)</div>
                    <div class="metric-value neutral">{{ (analysisResult?.dynamic_valuation?.valuation_forecast?.revenue_forecast_1y || 0).toFixed(1) }}%</div>
                  </div>
                  <div class="metric-item">
                    <div class="metric-label">预测增长(利润)</div>
                    <div class="metric-value">{{ (analysisResult?.dynamic_valuation?.valuation_forecast?.profit_forecast_1y || 0).toFixed(1) }}%</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="result-actions">
          <el-button size="small" @click="exportReport" :loading="exporting" :disabled="!analysisResult">
            <DocumentArrowDownIcon class="btn-icon" v-if="!exporting" />
            {{ exporting ? '导出中...' : '导出报告' }}
          </el-button>
          <el-button size="small" @click="saveToPool" :loading="savingToPool" :disabled="!analysisResult">
            <BookmarkIcon class="btn-icon" v-if="!savingToPool" />
            {{ savingToPool ? '获取中...' : '保存到股票池' }}
          </el-button>
        </div>

        <!-- 股票池选择对话框 -->
        <StockPoolSelectDialog
          v-model="showStockPoolDialog"
          :pre-selected-stocks="currentStockForPool"
          :title="`将 ${props.selectedStock?.name} 添加到股票池`"
          :selector-title="'请选择要添加股票的股票池'"
          :allow-create="true"
          @confirmed="handleStockPoolConfirmed"
          @canceled="handleStockPoolCanceled"
          class="custom-stock-pool-dialog"
        />
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ScaleIcon,
  ChartBarIcon,
  BookOpenIcon,
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  BanknotesIcon,
  ShieldCheckIcon,
  TrophyIcon,
  PresentationChartLineIcon,
  DocumentArrowDownIcon,
  BookmarkIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/vue/24/outline'



// 导入API
import { relativeValuationAPI } from '@/api/valuation'
import html2canvas from 'html2canvas'
// 导入股票池选择器组件
import StockPoolSelectDialog from '@/components/StockPool/StockPoolSelectDialog.vue'

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
  analysisType: string
  overallTrend: string
  overallPhase: string
  confidence: number
  recommendation: string
  analysisDate: string
  detailed: any
}

// Props
interface Props {
  selectedStock?: SelectedStock | null
}

const props = withDefaults(defineProps<Props>(), {
  selectedStock: null
})

// Emits
const emit = defineEmits<{
  'analysis-completed': [result: AnalysisResult]
  'stock-selected': [stock: SelectedStock]
}>()

// 响应式数据
const analyzing = ref(false)
const analysisProgress = ref(0)
const analysisResult = ref<any>(null)
const analysisError = ref<string | null>(null)
const chartDataLoaded = ref(false)
const trendChartLoaded = ref(false)

// 功能按钮相关状态
const exporting = ref(false)
const savingToPool = ref(false)
const showStockPoolDialog = ref(false)


// 图表引用
const comparisonChart = ref<HTMLElement | null>(null)
const trendChart = ref<HTMLElement | null>(null)

// 分析设置
const analysisSettings = ref({
  includeIndustryComparison: true,
  includePeerComparison: true,
  includeHistoricalTrend: true,
  timeHorizon: '3y',
  benchmarkIndex: 'auto'
})

// 日期范围
const dateRange = ref<[string, string]>([
  new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  new Date().toISOString().split('T')[0]
])

// 图表控制
const trendPeriod = ref('3y')
const trendMetric = ref('pe')

// 计算属性
const hasValidStock = computed(() => {
  return props.selectedStock && props.selectedStock.code
})

// 格式化当前股票为股票池组件需要的格式
const currentStockForPool = computed(() => {
  if (!props.selectedStock) return []
  
  return [{
    ts_code: props.selectedStock.code,
    name: props.selectedStock.name,
    industry: analysisResult.value?.industry || '',
    current_price: 0, // 可以从分析结果中获取，如果有的话
    change_pct: 0
  }]
})

// 监听股票变化，自动分析
watch(() => props.selectedStock, (newStock) => {
  if (newStock && newStock.code) {
    startAnalysis()
  } else {
    // 清空分析结果
    analysisResult.value = null
    analysisError.value = null
  }
}, { immediate: true })

// 方法
const startAnalysis = async () => {
  if (!hasValidStock.value) {
    return
  }

  analyzing.value = true
  analysisProgress.value = 0
  analysisError.value = null
  analysisResult.value = null

  try {
    // 模拟分析进度
    const progressInterval = setInterval(() => {
      if (analysisProgress.value < 90) {
        analysisProgress.value += Math.random() * 20
      }
    }, 500)

    // 调用相对估值分析API
    const response = await relativeValuationAPI.analyzeStock(
      props.selectedStock!.code,
      dateRange.value[1]?.replace(/-/g, '')
    )

    clearInterval(progressInterval)
    analysisProgress.value = 100

    if (response.success && response.data) {
      analysisResult.value = response.data
      
      // 加载图表
      await nextTick()
      await loadCharts()
      
      // 发送分析完成事件
      const result: AnalysisResult = {
        id: `relative_${Date.now()}`,
        stockCode: props.selectedStock!.code,
        stockName: props.selectedStock!.name,
        analysisType: 'relative_valuation',
        overallTrend: response.data.overall_rating || 'unknown',
        overallPhase: 'analysis',
        confidence: response.data.rating_score || 0,
        recommendation: getRecommendationFromAdvice(response.data.investment_advice),
        analysisDate: new Date().toISOString(),
        detailed: response.data
      }
      
      emit('analysis-completed', result)
    } else {
      throw new Error(response.message || '分析失败')
    }
  } catch (error: any) {
    console.error('相对估值分析失败:', error)
    analysisError.value = error.message || '分析过程中发生错误'
  } finally {
    analyzing.value = false
  }
}

const loadCharts = async () => {
  try {
    // 这里应该使用真实的图表库（如ECharts）来渲染图表
    // 暂时模拟图表加载
    setTimeout(() => {
      chartDataLoaded.value = true
      trendChartLoaded.value = true
    }, 1000)
  } catch (error) {
    console.error('图表加载失败:', error)
  }
}

const switchTrendPeriod = () => {
  // 切换趋势周期时重新加载图表
  loadCharts()
}

const switchTrendMetric = () => {
  // 切换趋势指标时重新加载图表
  loadCharts()
}

const retryAnalysis = () => {
  analysisError.value = null
  startAnalysis()
}

// 手动触发分析
const triggerAnalysis = () => {
  if (!hasValidStock.value) {
    ElMessage.warning('请先选择股票')
    return
  }
  
  // 清空之前的结果
  analysisResult.value = null
  analysisError.value = null
  
  // 开始新的分析
  startAnalysis()
}

const exportReport = async () => {
  if (!analysisResult.value || !props.selectedStock) {
    ElMessage.warning('暂无分析数据可导出')
    return
  }

  exporting.value = true
  try {
    const markdown = generateMarkdownReport()
    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${props.selectedStock.name}(${props.selectedStock.code})_相对估值分析报告_${new Date().toISOString().split('T')[0]}.md`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    ElMessage.success('报告导出成功')
  } catch (error) {
    console.error('导出报告失败:', error)
    ElMessage.error('导出报告失败')
  } finally {
    exporting.value = false
  }
}


const saveToPool = () => {
  if (!props.selectedStock) {
    ElMessage.warning('请先选择股票')
    return
  }

  if (currentStockForPool.value.length === 0) {
    ElMessage.warning('没有可添加的股票数据')
    return
  }

  // 显示股票池选择对话框
  showStockPoolDialog.value = true
}

// 处理股票池选择确认
const handleStockPoolConfirmed = (data: any) => {
  console.log('股票添加结果:', data)
  ElMessage.success(`成功将 ${props.selectedStock?.name} 添加到 ${data.pools.length} 个股票池`)
  showStockPoolDialog.value = false
}

// 处理股票池选择取消
const handleStockPoolCanceled = () => {
  showStockPoolDialog.value = false
}

// 生成Markdown报告
const generateMarkdownReport = (): string => {
  const stock = props.selectedStock!
  const result = analysisResult.value
  const currentDate = new Date().toLocaleDateString('zh-CN')

  return `# 相对估值分析报告

## 基本信息
- **股票代码**: ${stock.code}
- **股票名称**: ${stock.name}
- **所属行业**: ${result?.industry || 'N/A'}
- **分析日期**: ${currentDate}

## 估值指标概览

### 市盈率 (PE)
- **当前PE**: ${result?.current_metrics?.pe_ratio?.toFixed(2) || 'N/A'}
- **行业中位数**: ${result?.industry_comparison?.pe_median?.toFixed(2) || 'N/A'}
- **相对位置**: ${result?.industry_comparison?.pe_rating || 'N/A'}

### 市净率 (PB)
- **当前PB**: ${result?.current_metrics?.pb_ratio?.toFixed(2) || 'N/A'}
- **行业中位数**: ${result?.industry_comparison?.pb_median?.toFixed(2) || 'N/A'}
- **相对位置**: ${result?.industry_comparison?.pb_rating || 'N/A'}

### 市销率 (PS)
- **当前PS**: ${result?.current_metrics?.ps_ratio?.toFixed(2) || 'N/A'}
- **行业中位数**: ${result?.industry_comparison?.ps_median?.toFixed(2) || 'N/A'}
- **相对位置**: ${result?.industry_comparison?.ps_rating || 'N/A'}

## 动态估值分析

### PEG比率分析
- **1年PEG**: ${result?.dynamic_valuation?.dynamic_metrics?.peg_1y?.toFixed(2) || 'N/A'}
- **3年PEG**: ${result?.dynamic_valuation?.dynamic_metrics?.peg_3y?.toFixed(2) || 'N/A'}
- **PEG评级**: ${result?.dynamic_valuation?.dynamic_metrics?.peg_rating || 'N/A'}
- **前瞻PE**: ${result?.dynamic_valuation?.dynamic_metrics?.forward_pe?.toFixed(1) || 'N/A'}

### 成长性分析
- **成长可持续性**: ${Math.round(result?.dynamic_valuation?.growth_metrics?.growth_sustainability_score || 0)}分
- **营收增长(1年)**: ${(result?.dynamic_valuation?.growth_metrics?.revenue_growth_1y || 0).toFixed(1)}%
- **利润增长(1年)**: ${(result?.dynamic_valuation?.growth_metrics?.profit_growth_1y || 0).toFixed(1)}%
- **营收增长(3年)**: ${(result?.dynamic_valuation?.growth_metrics?.revenue_growth_3y || 0).toFixed(1)}%
- **利润增长(3年)**: ${(result?.dynamic_valuation?.growth_metrics?.profit_growth_3y || 0).toFixed(1)}%

### 盈利质量分析
- **盈利质量**: ${Math.round(result?.dynamic_valuation?.profitability_metrics?.quality_score || 0)}分
- **ROE**: ${(result?.dynamic_valuation?.profitability_metrics?.roe || 0).toFixed(2)}%
- **ROA**: ${(result?.dynamic_valuation?.profitability_metrics?.roa || 0).toFixed(2)}%
- **毛利率**: ${(result?.dynamic_valuation?.profitability_metrics?.gross_margin || 0).toFixed(2)}%
- **现金转换率**: ${(result?.dynamic_valuation?.profitability_metrics?.cash_conversion_ratio || 0).toFixed(1)}%

### 综合动态评级
- **综合评分**: ${Math.round(result?.dynamic_valuation?.comprehensive_rating?.comprehensive_score || 0)}分
- **综合评级**: ${result?.dynamic_valuation?.comprehensive_rating?.comprehensive_rating || 'N/A'}
- **静态评级**: ${result?.dynamic_valuation?.comprehensive_rating?.static_rating || 'N/A'} (${(result?.dynamic_valuation?.comprehensive_rating?.static_score || 0).toFixed(0)}分)
- **成长评分**: ${(result?.dynamic_valuation?.comprehensive_rating?.growth_score || 0).toFixed(0)}分
- **质量评分**: ${(result?.dynamic_valuation?.comprehensive_rating?.quality_score || 0).toFixed(0)}分

## 投资建议

### 动态估值建议
- **投资动作**: ${result?.dynamic_valuation?.investment_recommendation?.investment_action || 'N/A'}
- **信心度**: ${result?.dynamic_valuation?.investment_recommendation?.confidence_level || 'N/A'}
- **时间期限**: ${result?.dynamic_valuation?.investment_recommendation?.time_horizon || 'N/A'}
- **建议理由**: ${result?.dynamic_valuation?.investment_recommendation?.recommendation_rationale || '暂无说明'}

${result?.dynamic_valuation?.investment_recommendation?.key_risks?.length > 0 ? `
#### 主要风险
${result.dynamic_valuation.investment_recommendation.key_risks.map((risk: string) => `- ${risk}`).join('\n')}
` : ''}

${result?.dynamic_valuation?.investment_recommendation?.catalysts?.length > 0 ? `
#### 催化因素
${result.dynamic_valuation.investment_recommendation.catalysts.map((catalyst: string) => `- ${catalyst}`).join('\n')}
` : ''}

### 静态估值建议
- **投资建议**: ${getAdviceTitle(result?.investment_advice)}
- **详细说明**: ${result?.investment_advice || '暂无建议'}
- **目标PE**: ${result?.dynamic_valuation?.valuation_forecast?.target_pe?.toFixed(1) || 'N/A'}
- **预测增长(营收)**: ${(result?.dynamic_valuation?.valuation_forecast?.revenue_forecast_1y || 0).toFixed(1)}%
- **预测增长(利润)**: ${(result?.dynamic_valuation?.valuation_forecast?.profit_forecast_1y || 0).toFixed(1)}%

## 总结
- **整体评级**: ${result?.overall_rating || 'N/A'}
- **评级分数**: ${result?.rating_score || 0}分
- **分析摘要**: ${result?.analysis_summary || '暂无摘要'}

---
*本报告由KK量化分析系统生成，仅供参考，不构成投资建议。投资有风险，入市需谨慎。*
`
}

// 辅助方法
const getPEComparisonType = (pe: number, avgPe: number) => {
  if (!pe || !avgPe) return 'info'
  const ratio = pe / avgPe
  if (ratio < 0.8) return 'success'
  if (ratio > 1.2) return 'danger'
  return 'warning'
}

const getPEComparisonText = (pe: number, avgPe: number) => {
  if (!pe || !avgPe) return '无数据'
  const ratio = pe / avgPe
  if (ratio < 0.8) return '低估'
  if (ratio > 1.2) return '高估'
  return '合理'
}

const getPBComparisonType = (pb: number, avgPb: number) => {
  if (!pb || !avgPb) return 'info'
  const ratio = pb / avgPb
  if (ratio < 0.8) return 'success'
  if (ratio > 1.2) return 'danger'
  return 'warning'
}

const getPBComparisonText = (pb: number, avgPb: number) => {
  if (!pb || !avgPb) return '无数据'
  const ratio = pb / avgPb
  if (ratio < 0.8) return '低估'
  if (ratio > 1.2) return '高估'
  return '合理'
}

const getPSComparisonType = (ps: number, avgPs: number) => {
  if (!ps || !avgPs) return 'info'
  const ratio = ps / avgPs
  if (ratio < 0.8) return 'success'
  if (ratio > 1.2) return 'danger'
  return 'warning'
}

const getPSComparisonText = (ps: number, avgPs: number) => {
  if (!ps || !avgPs) return '无数据'
  const ratio = ps / avgPs
  if (ratio < 0.8) return '低估'
  if (ratio > 1.2) return '高估'
  return '合理'
}

const getValuationColor = (score: number) => {
  if (!score) return 'var(--el-color-info)'
  if (score >= 0.8) return 'var(--el-color-success)'
  if (score >= 0.6) return 'var(--el-color-warning)'
  return 'var(--el-color-danger)'
}

const getGrowthClass = (score: number) => {
  if (!score) return 'unknown'
  if (score >= 0.8) return 'excellent'
  if (score >= 0.6) return 'good'
  if (score >= 0.4) return 'average'
  return 'poor'
}

const getGrowthText = (score: number) => {
  if (!score) return '未知'
  if (score >= 0.8) return '优秀'
  if (score >= 0.6) return '良好'
  if (score >= 0.4) return '一般'
  return '较差'
}

const getProfitabilityClass = (score: number) => {
  if (!score) return 'unknown'
  if (score >= 0.8) return 'excellent'
  if (score >= 0.6) return 'good'
  if (score >= 0.4) return 'average'
  return 'poor'
}

const getProfitabilityText = (score: number) => {
  if (!score) return '未知'
  if (score >= 0.8) return '优秀'
  if (score >= 0.6) return '良好'
  if (score >= 0.4) return '一般'
  return '较差'
}

const getSafetyClass = (margin: number) => {
  if (!margin) return 'unknown'
  if (margin >= 0.3) return 'excellent'
  if (margin >= 0.2) return 'good'
  if (margin >= 0.1) return 'average'
  return 'poor'
}

const getSafetyText = (margin: number) => {
  if (!margin) return '未知'
  if (margin >= 0.3) return '充足'
  if (margin >= 0.2) return '适中'
  if (margin >= 0.1) return '偏低'
  return '不足'
}

const getRatingClass = (advice: string) => {
  if (!advice) return 'rating-unknown'
  const rating = advice.toLowerCase()
  if (rating.includes('买入') || rating.includes('buy')) {
    return 'rating-buy'
  } else if (rating.includes('卖出') || rating.includes('sell')) {
    return 'rating-sell'
  } else if (rating.includes('持有') || rating.includes('hold')) {
    return 'rating-hold'
  }
  return 'rating-unknown'
}

const getAdviceRatingText = (advice: string) => {
  if (!advice) return 'N/A'
  const rating = advice.toLowerCase()
  if (rating.includes('买入') || rating.includes('buy')) {
    return '买入'
  } else if (rating.includes('卖出') || rating.includes('sell')) {
    return '卖出'
  } else if (rating.includes('持有') || rating.includes('hold')) {
    return '持有'
  }
  return '观望'
}

const getAdviceTitle = (advice: string) => {
  if (!advice) return '观望'
  const rating = advice.toLowerCase()
  if (rating.includes('买入') || rating.includes('buy')) {
    return '建议买入'
  } else if (rating.includes('卖出') || rating.includes('sell')) {
    return '建议卖出'
  } else if (rating.includes('持有') || rating.includes('hold')) {
    return '建议持有'
  }
  return '观望'
}

const getUpsideClass = (upside: number) => {
  if (!upside) return 'neutral'
  if (upside > 20) return 'positive'
  if (upside < -10) return 'negative'
  return 'neutral'
}

const getRiskClass = (risk: string) => {
  switch (risk?.toLowerCase()) {
    case 'low':
    case '低':
      return 'risk-low'
    case 'medium':
    case '中':
      return 'risk-medium'
    case 'high':
    case '高':
      return 'risk-high'
    default:
      return 'risk-unknown'
  }
}

const getRecommendationFromAdvice = (advice: string) => {
  if (!advice) return 'hold'
  const rating = advice.toLowerCase()
  if (rating.includes('买入') || rating.includes('buy')) {
    return 'buy'
  } else if (rating.includes('卖出') || rating.includes('sell')) {
    return 'sell'
  } else if (rating.includes('持有') || rating.includes('hold')) {
    return 'hold'
  }
  return 'wait'
}

// 动态估值相关的辅助方法
const getPEGRatingType = (rating: string) => {
  if (!rating) return 'info'
  switch (rating) {
    case '严重低估': return 'success'
    case '低估': return 'success'
    case '合理': return 'warning'
    case '偏高': return 'danger'
    case '高估': return 'danger'
    default: return 'info'
  }
}

const getGrowthScoreColor = (score: number) => {
  if (!score) return 'var(--el-color-info)'
  if (score >= 80) return 'var(--el-color-success)'
  if (score >= 60) return 'var(--el-color-warning)'
  if (score >= 40) return 'var(--el-color-danger)'
  return 'var(--el-color-info-light-5)'
}

const getQualityScoreColor = (score: number) => {
  if (!score) return 'var(--el-color-info)'
  if (score >= 80) return 'var(--el-color-success)'
  if (score >= 60) return 'var(--el-color-warning)'
  if (score >= 40) return 'var(--el-color-danger)'
  return 'var(--el-color-info-light-5)'
}

const getComprehensiveScoreColor = (score: number) => {
  if (!score) return 'var(--el-color-info)'
  if (score >= 75) return 'var(--el-color-success)'
  if (score >= 60) return 'var(--el-color-warning)'
  if (score >= 45) return 'var(--el-color-danger)'
  return 'var(--el-color-info-light-5)'
}

const getInvestmentActionClass = (action: string) => {
  if (!action) return 'rating-unknown'
  switch (action) {
    case '买入': return 'rating-buy'
    case '持有': return 'rating-hold'
    case '卖出': return 'rating-sell'
    default: return 'rating-unknown'
  }
}

const getComprehensiveRatingType = (rating: string) => {
  if (!rating) return 'info'
  switch (rating) {
    case '强烈推荐': return 'success'
    case '推荐': return 'success'
    case '中性': return 'warning'
    case '谨慎': return 'danger'
    case '不推荐': return 'danger'
    default: return 'info'
  }
}

// 监听选中股票变化
watch(() => props.selectedStock, (newStock) => {
  if (newStock && newStock.code) {
    analysisResult.value = null
    analysisError.value = null
    chartDataLoaded.value = false
    trendChartLoaded.value = false
  }
}, { immediate: true })

// 组件挂载时的初始化
onMounted(() => {
  // 初始化逻辑
})

// 组件卸载时的清理
onUnmounted(() => {
  // 清理逻辑
})

// 暴露方法给父组件
defineExpose({
  refreshAnalysis: startAnalysis,
  triggerAnalysis: triggerAnalysis,
  retryAnalysis: retryAnalysis
})
</script>

<style scoped>
/* ========== 基础样式 ========== */
.relative-valuation-panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: auto;
  min-height: 800px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-lg);
  margin-bottom: var(--spacing-lg);
  overflow: hidden;
}

/* ========== 面板头部 ========== */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--gradient-accent);
  border-bottom: 1px solid var(--border-primary);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
}

.title-icon {
  width: 20px;
  height: 20px;
  color: #ffffff;
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.date-range-selector {
  margin-right: var(--spacing-sm);
}

.action-icon {
  width: 14px;
  height: 14px;
}

/* ========== 面板内容 ========== */
.panel-content {
  padding: var(--spacing-md);
  width: 100%;
  background: var(--bg-primary);
}

.scrollable-content {
  width: 100%;
}

/* ========== 空状态 ========== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-lg);
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-sm);
}

.empty-hint {
  font-size: 14px;
  color: var(--text-tertiary);
  margin: 0;
}

/* ========== 分析中状态 ========== */
.analyzing-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  text-align: center;
}

.analyzing-animation {
  margin-bottom: var(--spacing-lg);
}

.analyzing-icon {
  width: 48px;
  height: 48px;
  color: var(--accent-primary);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.analyzing-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.analyzing-hint {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-lg);
}

/* ========== 错误状态 ========== */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  text-align: center;
}

.error-icon {
  width: 48px;
  height: 48px;
  color: var(--danger-primary);
  margin-bottom: var(--spacing-lg);
}

.error-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--danger-primary);
  margin-bottom: var(--spacing-sm);
}

.error-hint {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-lg);
}

/* ========== 分析结果 ========== */
.analysis-result {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  flex: 1;
  height: 100%;
}

.result-section {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-secondary);
  overflow: hidden;
  flex-shrink: 0;
  margin-bottom: 0;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base);
}

.result-section:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--border-accent);
}



.section-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border-secondary);
}

.section-title .title-icon {
  width: 16px;
  height: 16px;
  color: var(--accent-primary);
}

/* ========== 估值指标概览 ========== */
.valuation-overview {
  padding: var(--spacing-md);
}

.valuation-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
}

.metric-mini-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}

.metric-mini-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--gradient-accent);
}

.metric-mini-card:hover {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-glow);
  transform: translateY(-2px);
}

.metric-header-mini {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.metric-icon-mini {
  width: 18px;
  height: 18px;
  color: var(--accent-primary);
}

.metric-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.metric-value-large {
  font-size: 28px;
  font-weight: 700;
  color: var(--accent-primary);
  margin-bottom: var(--spacing-md);
  text-align: center;
  line-height: 1;
}

.metric-comparison-mini {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.comparison-item-mini {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-secondary);
}

.label-mini {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 500;
}

.value-mini {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-primary);
}

.metric-card {
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-secondary);
  padding: 4px;
  transition: all 0.3s ease;
}

.metric-card:hover {
  border-color: var(--accent-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.metric-header {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 3px;
}

.metric-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  background: var(--accent-primary);
  border-radius: var(--radius-sm);
}

.metric-icon .icon {
  width: 10px;
  height: 10px;
  color: white;
}

.metric-info {
  flex: 1;
}

.metric-label {
  font-size: 9px;
  color: var(--text-secondary);
  margin-bottom: 1px;
  font-weight: 500;
}

.metric-value {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary);
}

.metric-comparison {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.comparison-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2px 4px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
}

.comparison-label {
  font-size: 8px;
  color: var(--text-secondary);
  font-weight: 500;
}

.comparison-value {
  font-size: 9px;
  font-weight: 600;
  color: var(--text-primary);
}

/* ========== 估值水平评估 ========== */
.valuation-assessment {
  display: flex;
  align-items: center;
  gap: var(--spacing-xl);
  padding: var(--spacing-lg);
}

.assessment-gauge {
  flex-shrink: 0;
}

.assessment-content {
  text-align: center;
}

.assessment-value {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.assessment-label {
  font-size: 10px;
  color: var(--text-secondary);
  margin-top: 2px;
  font-weight: 500;
}

.assessment-level {
  font-size: 10px;
  color: var(--accent-primary);
  margin-top: 2px;
  font-weight: 600;
}

.assessment-indicators {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
  flex: 1;
}

.indicator-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-secondary);
  transition: all 0.3s ease;
}

.indicator-card:hover {
  border-color: var(--accent-primary);
  transform: translateY(-2px);
}

.card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--accent-primary);
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.card-icon .icon {
  width: 18px;
  height: 18px;
  color: white;
}

.card-content {
  flex: 1;
}

.card-label {
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 4px;
  font-weight: 500;
}

.card-value {
  font-size: 14px;
  font-weight: 600;
}

.card-value.excellent {
  color: var(--success-primary);
}

.card-value.good {
  color: var(--info-primary);
}

.card-value.average {
  color: var(--warning-primary);
}

.card-value.poor {
  color: var(--danger-primary);
}

.card-value.unknown {
  color: var(--text-tertiary);
}

/* ========== 行业对比分析 ========== */
.industry-comparison {
  padding: var(--spacing-lg);
}

.ranking-overview {
  margin-bottom: var(--spacing-lg);
}

.ranking-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-secondary);
}

.ranking-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex: 1;
}

.ranking-icon {
  width: 32px;
  height: 32px;
  color: var(--warning-primary);
}

.ranking-info {
  flex: 1;
}

.ranking-title {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
  font-weight: 500;
}

.ranking-position {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.ranking-percentile {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.percentile-label {
  font-size: 10px;
  color: var(--text-secondary);
  font-weight: 500;
}

.percentile-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--accent-primary);
}

.comparison-charts {
  margin-top: var(--spacing-lg);
}

/* ========== 历史估值趋势 ========== */
.historical-trend {
  padding: var(--spacing-lg);
}

.trend-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-secondary);
}

/* ========== 图表容器 ========== */
.chart-container {
  position: relative;
  height: 300px;
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-secondary);
  overflow: hidden;
}

.comparison-chart,
.trend-chart {
  width: 100%;
  height: 100%;
}

.chart-no-data {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
}

.no-data-icon {
  width: 48px;
  height: 48px;
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-md);
}

.no-data-text {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-sm);
}

/* ========== 投资建议 ========== */
.investment-advice {
  padding: var(--spacing-md);
}

.advice-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
}

.advice-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}

.advice-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--gradient-accent);
}

.advice-card:hover {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-glow);
  transform: translateY(-2px);
}

.advice-card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.advice-icon {
  width: 18px;
  height: 18px;
  color: var(--accent-primary);
}

.advice-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.advice-rating-display {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
}

.rating-info {
  flex: 1;
}

.confidence-level,
.time-horizon,
.advice-level {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.advice-description {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: var(--spacing-md);
}

.risk-catalyst-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

.risk-section,
.catalyst-section {
  padding: var(--spacing-sm);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-secondary);
}

.section-subtitle {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-sm) 0;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.advice-metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.metric-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-sm);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-secondary);
  text-align: center;
}

.metric-label {
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.metric-value.price-value {
  color: var(--accent-primary);
}

.metric-value.neutral {
  color: var(--text-primary);
}

.advice-main {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 20px;
  background: var(--bg-primary);
  padding: 20px;
  border-radius: 12px;
  border: 1px solid var(--border-secondary);
  box-shadow: var(--shadow-sm);
}

.advice-rating {
  flex-shrink: 0;
}

.rating-circle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  border: 4px solid;
  position: relative;
  overflow: hidden;
}

.rating-circle::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: conic-gradient(from 0deg, transparent, currentColor, transparent);
  animation: rotate 3s linear infinite;
  opacity: 0.3;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.rating-circle.rating-buy {
  border-color: var(--el-color-success);
  background: linear-gradient(135deg, rgba(var(--el-color-success-rgb), 0.1) 0%, rgba(var(--el-color-success-rgb), 0.05) 100%);
  color: var(--el-color-success);
}

.rating-circle.rating-sell {
  border-color: var(--el-color-danger);
  background: linear-gradient(135deg, rgba(var(--el-color-danger-rgb), 0.1) 0%, rgba(var(--el-color-danger-rgb), 0.05) 100%);
  color: var(--el-color-danger);
}

.rating-circle.rating-hold {
  border-color: var(--el-color-warning);
  background: linear-gradient(135deg, rgba(var(--el-color-warning-rgb), 0.1) 0%, rgba(var(--el-color-warning-rgb), 0.05) 100%);
  color: var(--el-color-warning);
}

.rating-circle.rating-unknown {
  border-color: var(--el-color-info);
  background: linear-gradient(135deg, rgba(var(--el-color-info-rgb), 0.1) 0%, rgba(var(--el-color-info-rgb), 0.05) 100%);
  color: var(--el-color-info);
}

.rating-text {
  font-size: 16px;
  font-weight: 800;
  z-index: 1;
  position: relative;
}

.advice-content {
  flex: 1;
}

.advice-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.advice-description {
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.detail-value {
  font-size: 16px;
  font-weight: 600;
}

.detail-value.price-value {
  color: var(--accent-primary);
}

.detail-value.positive {
  color: var(--success-primary);
}

.detail-value.negative {
  color: var(--danger-primary);
}

.detail-value.neutral {
  color: var(--text-primary);
}

.detail-value.risk-low {
  color: var(--success-primary);
}

.detail-value.risk-medium {
  color: var(--warning-primary);
}

.detail-value.risk-high {
  color: var(--danger-primary);
}

.detail-value.risk-unknown {
  color: var(--text-tertiary);
}

/* ========== 操作按钮 ========== */
.result-actions {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: center;
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-primary);
  background: var(--bg-elevated);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
}

.btn-icon {
  width: 16px;
  height: 16px;
  margin-right: var(--spacing-xs);
}

.result-actions .el-button {
  background: var(--gradient-accent);
  border: none;
  color: #ffffff;
  font-weight: 600;
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-base);
}

.result-actions .el-button:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow);
}

/* ========== Element Plus 样式覆盖 ========== */
:deep(.el-tag) {
  border: none;
  font-weight: 600;
  border-radius: 6px;
  padding: 4px 12px;
}

:deep(.el-tag--success) {
  background: var(--el-color-success);
  color: #ffffff;
}

:deep(.el-tag--warning) {
  background: var(--el-color-warning);
  color: #ffffff;
}

:deep(.el-tag--danger) {
  background: var(--el-color-danger);
  color: #ffffff;
}

:deep(.el-tag--info) {
  background: var(--el-color-info);
  color: #ffffff;
}

:deep(.el-progress-bar__outer) {
  background: var(--el-fill-color-light);
  border-radius: var(--el-border-radius-base);
}

:deep(.el-progress-bar__inner) {
  border-radius: 10px;
}

:deep(.el-button--small) {
  height: 32px;
  padding: 0 16px;
  font-size: 14px;
  border-radius: 8px;
}

:deep(.el-radio-button__inner) {
  border: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  font-size: 12px;
  padding: 8px 16px;
  border-radius: var(--el-border-radius-base);
  font-weight: 600;
}

:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: var(--el-color-primary);
  border-color: var(--el-color-primary);
  color: white;
  box-shadow: var(--el-box-shadow-light);
}

/* ========== 动画效果 ========== */
.metric-mini-card {
  animation: fadeInUp 0.6s ease-out forwards;
  opacity: 0;
  transform: translateY(20px);
}

.metric-mini-card:nth-child(1) { animation-delay: 0.1s; }
.metric-mini-card:nth-child(2) { animation-delay: 0.2s; }
.metric-mini-card:nth-child(3) { animation-delay: 0.3s; }

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.result-section {
  animation: slideInLeft 0.5s ease-out forwards;
  opacity: 0;
  transform: translateX(-30px);
}

.result-section:nth-child(1) { animation-delay: 0.1s; }
.result-section:nth-child(2) { animation-delay: 0.2s; }
.result-section:nth-child(3) { animation-delay: 0.3s; }

@keyframes slideInLeft {
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* ========== 响应式设计 ========== */
@media (max-width: 1200px) {
  .valuation-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .peg-analysis-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .compact-analysis-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .advice-main {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }
  
  .advice-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }
  
  .rating-cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .rating-main-card {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .panel-content {
    padding: 16px;
  }
  
  .valuation-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .metric-value-large {
    font-size: 24px;
  }
  
  .section-title {
    font-size: 14px;
    padding: 12px 16px;
  }
  
  .peg-analysis-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .compact-analysis-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
  
  .compact-score-card {
    grid-column: span 2;
  }
  
  .advice-main {
    padding: 16px;
  }
  
  .rating-circle {
    width: 80px;
    height: 80px;
  }
  
  .rating-text {
    font-size: 14px;
  }
  
  .result-actions {
    flex-direction: column;
    gap: 8px;
    padding: 16px;
  }
  
  .advice-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }
  
  .rating-cards-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-sm);
  }
  
  .risk-catalyst-grid {
    grid-template-columns: 1fr;
  }
  
  .advice-metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .panel-header {
    padding: 16px;
  }
  
  .panel-title {
    font-size: 16px;
  }
  
  .panel-content {
    padding: 12px;
  }
  
  .analysis-result {
    gap: 12px;
  }
  
  .metric-mini-card {
    padding: 16px;
  }
  
  .metric-value-large {
    font-size: 20px;
  }
  
  .compact-analysis-grid {
    grid-template-columns: 1fr;
  }
  
  .compact-score-card {
    grid-column: span 1;
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
}

/* ========== 滚动条样式 ========== */
.scrollable-content::-webkit-scrollbar {
  width: 4px;
}

.scrollable-content::-webkit-scrollbar-track {
  background: var(--bg-elevated);
}

.scrollable-content::-webkit-scrollbar-thumb {
  background: var(--border-primary);
  border-radius: 2px;
}

.scrollable-content::-webkit-scrollbar-thumb:hover {
  background: var(--accent-primary);
}


/* ========== 动态估值分析样式 ========== */
.dynamic-valuation {
  padding: 0;
  display: grid;
  gap: var(--spacing-md);
}

.dynamic-metric-group {
  background: transparent;
  padding: var(--spacing-md);
  transition: all var(--el-transition-duration);
  min-height: 120px; /* 减少最小高度 */
}

.metric-group-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
  padding: 0;
}

/* PEG分析网格 - 统一卡片样式 */
.peg-analysis-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
}

.peg-item {
  background: var(--bg-primary);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
  text-align: center;
}

.peg-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--gradient-accent);
}

.peg-item:hover {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-glow);
  transform: translateY(-2px);
}

.peg-label {
  font-size: 13px;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
  font-weight: 600;
}

.peg-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--accent-primary);
  margin-bottom: var(--spacing-md);
  text-align: center;
  line-height: 1;
}

.peg-desc {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 500;
}

.dynamic-metrics-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 3px;
  margin-bottom: 2px;
}

.dynamic-metric-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  padding: 3px;
  text-align: center;
  transition: all 0.3s ease;
}

.dynamic-metric-card:hover {
  border-color: var(--accent-primary);
  box-shadow: 0 2px 6px rgba(var(--accent-rgb), 0.15);
}

.dynamic-metric-card .metric-label {
  font-size: 8px;
  color: var(--text-secondary);
  margin-bottom: 1px;
}

.dynamic-metric-card .metric-value {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1px;
}

.dynamic-metric-card .metric-desc {
  font-size: 7px;
  color: var(--text-tertiary);
}

/* 成长性分析样式 */
.growth-analysis {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--spacing-xl);
  align-items: start;
}

.growth-score-display, .quality-score-display {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-shrink: 0;
}

.score-content {
  text-align: center;
}

.score-content .score-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.score-content .score-label {
  font-size: 10px;
  color: var(--text-secondary);
}

.score-description {
  text-align: left;
}

.score-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.score-trend {
  font-size: 12px;
  color: var(--text-secondary);
}

.growth-details, .profitability-details {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-xs);
}

.growth-item, .profitability-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-xs);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-primary);
  text-align: center;
}

.growth-label, .profitability-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.growth-value, .profitability-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

/* 盈利质量分析样式 */
.profitability-analysis {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--spacing-xl);
  align-items: start;
}

/* 综合评级样式 */
.comprehensive-rating {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--spacing-xl);
  align-items: center;
}

.rating-display {
  flex-shrink: 0;
}

.comprehensive-score-content {
  text-align: center;
}

.comprehensive-score-content .score-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.comprehensive-score-content .score-rating {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.rating-breakdown {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.rating-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-primary);
}

.rating-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.rating-score {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}


/* 响应式设计 */
@media (max-width: 1200px) {
  .valuation-metrics {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .growth-details, .profitability-details {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .valuation-metrics {
    grid-template-columns: 1fr;
  }
  
  .dynamic-metrics-row {
    grid-template-columns: 1fr;
  }
  
  .growth-analysis, .profitability-analysis {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }
  
  .comprehensive-rating {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }
  
  .risk-catalyst-section {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }
  
  .growth-details, .profitability-details {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .growth-details, .profitability-details {
    grid-template-columns: 1fr;
  }
  
  .compact-analysis-grid {
    grid-template-columns: repeat(3, 1fr) !important;
  }
}

/* 紧凑型布局样式 - 统一卡片样式 */
.compact-analysis-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--spacing-sm);
  align-items: stretch;
}

.compact-score-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  grid-column: span 2;
  background: var(--bg-primary);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-secondary);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}

.compact-score-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--gradient-accent);
}

.compact-score-card:hover {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-glow);
  transform: translateY(-2px);
}

.compact-score-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.compact-score-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: var(--el-spacing-extra-small);
}

.compact-score-trend {
  font-size: 10px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.compact-score-content {
  text-align: center;
}

.compact-score-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-color-primary);
}

.compact-data-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--el-spacing-small);
  background: var(--el-bg-color);
  border-radius: var(--el-border-radius-base);
  border: 1px solid var(--el-border-color-light);
  text-align: center;
  box-shadow: var(--el-box-shadow-light);
  transition: all var(--el-transition-duration);
  min-height: 80px; /* 统一卡片高度 */
}

.compact-data-item:hover {
  border-color: var(--el-color-primary);
  box-shadow: var(--el-box-shadow);
  transform: translateY(-1px);
}

.compact-label {
  font-size: 10px;
  color: var(--el-text-color-regular);
  margin-bottom: var(--el-spacing-extra-small);
  font-weight: 500;
}

.compact-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

/* 综合评级紧凑布局样式 */
.compact-comprehensive-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: var(--spacing-sm);
  align-items: center;
}

.compact-rating-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.compact-rating-info {
  display: flex;
  flex-direction: column;
}

.compact-rating-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.compact-rating-text {
  font-size: 9px;
  color: var(--text-secondary);
}

.compact-rating-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-xs);
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-primary);
  text-align: center;
  gap: 2px;
}

.compact-rating-item .el-tag {
  margin: 2px 0;
}

/* ========== 综合评级样式 ========== */
.rating-cards-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: var(--spacing-md);
  align-items: stretch;
}

.rating-main-card,
.rating-sub-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 120px;
}

.rating-main-card::before,
.rating-sub-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--gradient-accent);
}

.rating-main-card:hover,
.rating-sub-card:hover {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-glow);
  transform: translateY(-2px);
}

.rating-card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.rating-icon {
  width: 16px;
  height: 16px;
  color: var(--accent-primary);
}

.rating-card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.rating-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  flex: 1;
  justify-content: center;
}

.rating-level-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--accent-primary);
  text-align: center;
}

.rating-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  text-align: center;
}

.rating-score-large {
  font-size: 28px;
  font-weight: 700;
  color: var(--accent-primary);
  line-height: 1;
  margin-bottom: var(--spacing-xs);
}

.rating-score-large.growth-score {
  color: var(--el-color-success);
}

.rating-score-large.quality-score {
  color: var(--el-color-primary);
}

.rating-label {
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-sm);
}

.rating-desc {
  font-size: 10px;
  color: var(--text-tertiary);
  margin-top: var(--spacing-xs);
}

.main-rating-card {
  display: flex;
  align-items: center;
  gap: var(--el-spacing-large);
  padding: var(--el-spacing-large);
  background: var(--el-bg-color);
  border-radius: var(--el-border-radius-base);
  border: 1px solid var(--el-border-color-light);
  box-shadow: var(--el-box-shadow-light);
  transition: all var(--el-transition-duration);
  min-height: 100px; /* 统一卡片高度 */
}

.main-rating-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: var(--el-box-shadow);
}

.rating-circle-container {
  flex-shrink: 0;
}

.rating-score-display {
  text-align: center;
}

.score-number {
  font-size: 16px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1;
}

.score-label {
  font-size: 10px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.rating-info {
  display: flex;
  flex-direction: column;
  gap: var(--el-spacing-extra-small);
}

.rating-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.rating-level {
  font-size: 12px;
  color: var(--el-color-primary);
  font-weight: 600;
}

.rating-details {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--el-spacing-medium);
}

.rating-detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--el-spacing-medium);
  background: var(--el-bg-color);
  border-radius: var(--el-border-radius-base);
  border: 1px solid var(--el-border-color-light);
  transition: all var(--el-transition-duration);
  min-height: 60px; /* 统一卡片高度 */
}

.rating-detail-item:hover {
  border-color: var(--el-color-primary);
  box-shadow: var(--el-box-shadow-light);
}

.detail-header {
  display: flex;
  align-items: center;
  gap: var(--el-spacing-small);
}

.detail-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
}

.detail-score {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.detail-score.growth-score {
  color: var(--el-color-success);
}

.detail-score.quality-score {
  color: var(--el-color-primary);
}

/* ========== 成长性分析和盈利质量分析样式 ========== */
.growth-analysis-grid,
.profitability-analysis-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--spacing-md);
}

.growth-item,
.profitability-item {
  background: var(--bg-primary);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}

.growth-item::before,
.profitability-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--gradient-accent);
}

.growth-item:hover,
.profitability-item:hover {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-glow);
  transform: translateY(-2px);
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .growth-analysis-grid,
  .profitability-analysis-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .growth-analysis-grid,
  .profitability-analysis-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .growth-analysis-grid,
  .profitability-analysis-grid {
    grid-template-columns: 1fr;
  }
}

/* ========== 自定义股票池对话框样式 ========== */
.custom-stock-pool-dialog :deep(.el-dialog) {
  position: fixed !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) !important;
  margin: 0 !important;
  width: 70% !important;
  max-width: 800px !important;
  min-width: 600px !important;
}

.custom-stock-pool-dialog :deep(.el-dialog__header) {
  background: var(--gradient-accent);
  padding: var(--spacing-md) var(--spacing-lg);
}

.custom-stock-pool-dialog :deep(.el-dialog__title) {
  color: #ffffff;
  font-weight: 600;
}

.custom-stock-pool-dialog :deep(.el-dialog__body) {
  padding: var(--spacing-lg);
  background: var(--bg-primary);
}

.custom-stock-pool-dialog :deep(.el-dialog__footer) {
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-primary);
}
</style>