<template>
  <div class="dow-analysis-panel glass-effect">
    <!-- 面板标题 -->
    <div class="panel-header">
      <div class="panel-title">
        <ArrowTrendingUpIcon class="title-icon" />
        <span>道氏理论分析</span>
        <el-tag v-if="selectedStock" size="small" type="info">
          {{ selectedStock.code }} {{ selectedStock.name }}
        </el-tag>
      </div>
      <div class="panel-actions">
        <!-- 时间范围选择 -->
        <div class="date-range-selector">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="small"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :clearable="false"
            :disabled="analyzing"
            @change="onDateRangeChange"
          />
        </div>
        <el-tooltip content="分析设置" placement="top">
          <el-button size="small" @click="showSettingsModal">
            <Cog6ToothIcon class="action-icon" />
          </el-button>
        </el-tooltip>
        <el-tooltip content="开始分析" placement="top">
          <el-button 
            type="primary" 
            size="small" 
            @click="startAnalysis" 
            :loading="analyzing"
            :disabled="!selectedStock"
          >
            <PlayIcon class="action-icon" />
            {{ analyzing ? '分析中' : '分析' }}
          </el-button>
        </el-tooltip>
        
        <!-- 功能按钮 -->
        <el-button size="small" @click="exportReport" :loading="exporting" :disabled="!analysisResult">
          <DocumentArrowDownIcon class="btn-icon" v-if="!exporting" />
          {{ exporting ? '导出中...' : '导出报告' }}
        </el-button>
        <el-button size="small" @click="saveToPool" :loading="savingToPool" :disabled="!analysisResult">
          <BookmarkIcon class="btn-icon" v-if="!savingToPool" />
          {{ savingToPool ? '获取中...' : '保存到股票池' }}
        </el-button>
      </div>
    </div>

    <!-- 面板内容 -->
    <div class="panel-content">
      <!-- 未选择股票状态 -->
      <div v-if="!selectedStock" class="empty-state">
        <ChartBarIcon class="empty-icon" />
        <p class="empty-text">请选择要分析的股票</p>
        <p class="empty-hint">可从左侧股票池选择，或从上方搜索组件中搜索股票</p>
      </div>

      <!-- 分析中状态 -->
      <div v-else-if="analyzing" class="analyzing-state">
        <div class="analyzing-animation">
          <ArrowTrendingUpIcon class="analyzing-icon" />
        </div>
        <p class="analyzing-text">正在执行道氏理论分析...</p>
        <p class="analyzing-hint">分析多时间周期趋势、技术指标、成交量等</p>
        <el-progress 
          :percentage="analysisProgress" 
          :show-text="false"
          stroke-width="4"
          color="var(--accent-primary)"
        />
      </div>

      <!-- 分析结果 -->
      <div v-else-if="analysisResult" class="analysis-result">
        <!-- 道氏理论综合图表 -->
        <div class="result-section chart-section">
          <h4 class="section-title">
            <ChartBarIcon class="title-icon" />
            道氏理论技术分析图表
          </h4>
          <div class="chart-container">
            <div ref="dowTheoryChart" class="dow-theory-chart"></div>
            <div v-if="!chartDataLoaded" class="chart-no-data">
              <ChartBarIcon class="no-data-icon" />
              <p class="no-data-text">图表数据加载中...</p>
              <p class="no-data-hint">正在获取真实历史数据</p>
            </div>
          </div>
        </div>
        
        <!-- 综合评价仪表板 -->
        <div class="result-section">
          <h4 class="section-title">综合评价</h4>
          <div class="analysis-dashboard">
            <!-- 中心信心指数圆形进度条 -->
            <div class="confidence-gauge">
              <el-progress 
                type="circle" 
                :percentage="analysisResult.overall_assessment?.overall_confidence || 0" 
                :width="100"
                :stroke-width="8"
                :color="getConfidenceColor(analysisResult.overall_assessment?.overall_confidence)"
              >
                <template #default="{ percentage }">
                  <div class="confidence-content">
                    <div class="confidence-value">{{ percentage }}%</div>
                    <div class="confidence-label">信心指数</div>
                  </div>
                </template>
              </el-progress>
            </div>
            
            <!-- 趋势指标卡片组 -->
            <div class="trend-indicators">
              <div class="indicator-card trend-card">
                <div class="card-icon">
                  <ArrowTrendingUpIcon class="icon" />
                </div>
                <div class="card-content">
                  <div class="card-label">整体趋势</div>
                  <div class="card-value" :class="getTrendClass(analysisResult.overall_assessment?.overall_trend)">
                    {{ getTrendText(analysisResult.overall_assessment?.overall_trend) }}
                  </div>
                </div>
              </div>
              
              <div class="indicator-card phase-card">
                <div class="card-icon">
                  <ChartBarIcon class="icon" />
                </div>
                <div class="card-content">
                  <div class="card-label">趋势阶段</div>
                  <div class="card-value" :class="getPhaseClass(analysisResult.overall_assessment?.overall_phase)">
                    {{ getPhaseText(analysisResult.overall_assessment?.overall_phase) }}
                  </div>
                </div>
              </div>
              
              <div class="indicator-card action-card">
                <div class="card-icon">
                  <PlayIcon class="icon" />
                </div>
                <div class="card-content">
                  <div class="card-label">操作建议</div>
                  <div class="card-value" :class="getRecommendationClass(analysisResult.overall_assessment?.action_recommendation)">
                    {{ getRecommendationText(analysisResult.overall_assessment?.action_recommendation) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 多时间周期分析 -->
        <div class="result-section">
          <h4 class="section-title">多时间周期分析</h4>
          <div class="timeframe-analysis">
            <div 
              v-for="(analysis, timeframe) in analysisResult.timeframe_analysis"
              :key="String(timeframe)"
              class="timeframe-card"
            >
              <div class="timeframe-header">
                <div class="timeframe-title">
                  <span class="timeframe-name">{{ getTimeframeName(String(timeframe)) }}</span>
                  <div class="confidence-badge">
                    <span class="confidence-text">{{ analysis.confidence_score?.toFixed(1) }}%</span>
                    <div class="confidence-bar">
                      <div 
                        class="confidence-fill" 
                        :style="{ width: analysis.confidence_score + '%', backgroundColor: getConfidenceColor(analysis.confidence_score) }"
                      ></div>
                    </div>
                  </div>
                </div>
                <el-tag 
                  size="small" 
                  :type="getTrendTagType(analysis.direction)"
                  class="trend-badge"
                >
                  {{ getTrendText(analysis.direction) }}
                </el-tag>
              </div>
              
              <div class="timeframe-content">
                <!-- 技术指标网格 -->
                <div class="technical-grid">
                  <div class="tech-item">
                    <div class="tech-label">当前价格</div>
                    <div class="tech-value price-value">¥{{ analysis.technical_indicators?.current_price?.toFixed(2) }}</div>
                  </div>
                  <div class="tech-item">
                    <div class="tech-label">MA20</div>
                    <div class="tech-value ma-value">¥{{ analysis.technical_indicators?.ma_20?.toFixed(2) }}</div>
                  </div>
                  <div class="tech-item">
                    <div class="tech-label">RSI</div>
                    <div class="tech-value rsi-value">{{ analysis.technical_indicators?.rsi?.toFixed(2) }}</div>
                  </div>
                </div>
                
                <!-- 支撑阻力位可视化 -->
                <div v-if="analysis.support_resistance?.length > 0" class="support-resistance-chart">
                  <div class="sr-title">关键位置</div>
                  <div class="sr-levels">
                    <div 
                      v-for="sr in analysis.support_resistance.slice(0, 3)"
                      :key="sr.level"
                      class="sr-level"
                      :class="sr.type"
                    >
                      <div class="sr-label">{{ sr.type === 'support' ? '支撑' : '阻力' }}</div>
                      <div class="sr-value">¥{{ sr.level?.toFixed(2) }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 风险评估 -->
        <div class="result-section">
          <h4 class="section-title">风险评估</h4>
          <div class="risk-assessment">
            <!-- 风险等级可视化 -->
            <div class="risk-level-display">
              <div class="risk-level-indicator">
                <div class="risk-level-circle" :class="getRiskLevelClass(analysisResult.risk_assessment?.risk_level)">
                  <span class="risk-level-text">{{ getRiskText(analysisResult.risk_assessment?.risk_level) }}</span>
                </div>
              </div>
              <div class="risk-metrics">
                <div class="metric-item">
                  <div class="metric-icon stop-loss">
                    <ArrowDownIcon class="icon" />
                  </div>
                  <div class="metric-content">
                    <div class="metric-label">止损价位</div>
                    <div class="metric-value price-down">¥{{ analysisResult.risk_assessment?.stop_loss_price?.toFixed(2) }}</div>
                  </div>
                </div>
                <div class="metric-item">
                  <div class="metric-icon target">
                    <ArrowUpIcon class="icon" />
                  </div>
                  <div class="metric-content">
                    <div class="metric-label">目标价位</div>
                    <div class="metric-value price-up">¥{{ analysisResult.risk_assessment?.target_price?.toFixed(2) }}</div>
                  </div>
                </div>
                <div class="metric-item">
                  <div class="metric-icon position">
                    <ChartPieIcon class="icon" />
                  </div>
                  <div class="metric-content">
                    <div class="metric-label">建议仓位</div>
                    <div class="metric-value">{{ analysisResult.risk_assessment?.position_suggestion ? (analysisResult.risk_assessment.position_suggestion > 1 ? analysisResult.risk_assessment.position_suggestion.toFixed(1) : (analysisResult.risk_assessment.position_suggestion * 100).toFixed(1)) : 'N/A' }}%</div>
                    <div class="position-bar">
                      <div 
                        class="position-fill" 
                        :style="{ width: (analysisResult.risk_assessment?.position_suggestion ? (analysisResult.risk_assessment.position_suggestion > 1 ? analysisResult.risk_assessment.position_suggestion : analysisResult.risk_assessment.position_suggestion * 100) : 0) + '%' }"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 风险因素 -->
            <div v-if="analysisResult.risk_assessment?.key_risk_factors?.length > 0" class="risk-factors">
              <div class="factors-title">关键风险因素</div>
              <div class="factors-grid">
                <div 
                  v-for="(factor, index) in analysisResult.risk_assessment.key_risk_factors"
                  :key="factor"
                  class="factor-card"
                >
                  <div class="factor-index">{{ index + 1 }}</div>
                  <div class="factor-text">{{ factor }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 增强分析 -->
        <div v-if="analysisResult.enhanced_analysis" class="result-section">
          <h4 class="section-title">🚀 增强分析</h4>
          <div class="enhanced-analysis">
            <!-- 道氏理论123法则 -->
            <div v-if="analysisResult.enhanced_analysis.rule_123_analysis" class="rule-analysis-card">
              <div class="rule-header">
                <div class="rule-title">
                  <span class="rule-icon">123️⃣</span>
                  <span class="rule-name">道氏理论123法则</span>
                </div>
                <el-tag 
                  :type="analysisResult.enhanced_analysis.rule_123_analysis.trading_signal === 'buy' ? 'success' : 
                        analysisResult.enhanced_analysis.rule_123_analysis.trading_signal === 'sell' ? 'danger' : 'info'"
                  size="small"
                >
                  {{ getRecommendationText(analysisResult.enhanced_analysis.rule_123_analysis.trading_signal) }}
                </el-tag>
              </div>
              <div class="rule-content">
                <div class="rule-metrics">
                  <div class="rule-metric">
                    <span class="metric-label">信号强度</span>
                    <span class="metric-value" :class="getSignalStrengthClass(analysisResult.enhanced_analysis.rule_123_analysis.signal_strength)">
                      {{ analysisResult.enhanced_analysis.rule_123_analysis.signal_strength }}
                    </span>
                  </div>
                  <div class="rule-metric">
                    <span class="metric-label">反转概率</span>
                    <span class="metric-value">{{ (analysisResult.enhanced_analysis.rule_123_analysis.reversal_probability * 100).toFixed(1) }}%</span>
                  </div>
                </div>
                <div class="rule-conditions">
                  <div class="condition-item">
                    <span class="condition-label">趋势线突破</span>
                    <el-tag size="small" :type="analysisResult.enhanced_analysis.rule_123_analysis.condition1_trendline_break?.is_broken ? 'success' : 'info'">
                      {{ analysisResult.enhanced_analysis.rule_123_analysis.condition1_trendline_break?.is_broken ? '已突破' : '未突破' }}
                    </el-tag>
                  </div>
                  <div class="condition-item">
                    <span class="condition-label">无新极值</span>
                    <el-tag size="small" :type="analysisResult.enhanced_analysis.rule_123_analysis.condition2_no_new_extreme?.no_new_extreme ? 'success' : 'info'">
                      {{ analysisResult.enhanced_analysis.rule_123_analysis.condition2_no_new_extreme?.no_new_extreme ? '满足' : '不满足' }}
                    </el-tag>
                  </div>
                  <div class="condition-item">
                    <span class="condition-label">回撤突破</span>
                    <el-tag size="small" :type="analysisResult.enhanced_analysis.rule_123_analysis.condition3_retracement_break?.retracement_broken ? 'success' : 'info'">
                      {{ analysisResult.enhanced_analysis.rule_123_analysis.condition3_retracement_break?.retracement_broken ? '已突破' : '未突破' }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>

            <!-- 道氏理论2B法则 -->
            <div v-if="analysisResult.enhanced_analysis.rule_2b_analysis" class="rule-analysis-card">
              <div class="rule-header">
                <div class="rule-title">
                  <span class="rule-icon">2️⃣🅱️</span>
                  <span class="rule-name">道氏理论2B法则</span>
                </div>
                <el-tag 
                  :type="analysisResult.enhanced_analysis.rule_2b_analysis.trading_signal === 'buy' ? 'success' : 
                        analysisResult.enhanced_analysis.rule_2b_analysis.trading_signal === 'sell' ? 'danger' : 'info'"
                  size="small"
                >
                  {{ getRecommendationText(analysisResult.enhanced_analysis.rule_2b_analysis.trading_signal) }}
                </el-tag>
              </div>
              <div class="rule-content">
                <div class="rule-metrics">
                  <div class="rule-metric">
                    <span class="metric-label">信号强度</span>
                    <span class="metric-value" :class="getSignalStrengthClass(analysisResult.enhanced_analysis.rule_2b_analysis.signal_strength)">
                      {{ analysisResult.enhanced_analysis.rule_2b_analysis.signal_strength }}
                    </span>
                  </div>
                  <div class="rule-metric">
                    <span class="metric-label">反转概率</span>
                    <span class="metric-value">{{ (analysisResult.enhanced_analysis.rule_2b_analysis.reversal_probability * 100).toFixed(1) }}%</span>
                  </div>
                </div>
                <div class="rule-status">
                  <div class="status-item">
                    <span class="status-label">条件满足</span>
                    <el-tag size="small" :type="analysisResult.enhanced_analysis.rule_2b_analysis.conditions_met ? 'success' : 'warning'">
                      {{ analysisResult.enhanced_analysis.rule_2b_analysis.conditions_met ? '是' : '否' }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>

            <!-- MACD信号分析 -->
            <div v-if="analysisResult.enhanced_analysis.macd_signals" class="rule-analysis-card">
              <div class="rule-header">
                <div class="rule-title">
                  <span class="rule-icon">📊</span>
                  <span class="rule-name">MACD信号分析</span>
                </div>
                <el-tag 
                  :type="analysisResult.enhanced_analysis.macd_signals.signal_strength === 'strong' ? 'success' : 
                        analysisResult.enhanced_analysis.macd_signals.signal_strength === 'weak' ? 'warning' : 'info'"
                  size="small"
                >
                  {{ analysisResult.enhanced_analysis.macd_signals.signal_strength }}
                </el-tag>
              </div>
              <div class="rule-content">
                <div class="macd-values">
                  <div class="macd-item">
                    <span class="macd-label">MACD</span>
                    <span class="macd-value" :class="analysisResult.enhanced_analysis.macd_signals.current_macd > 0 ? 'positive' : 'negative'">
                      {{ analysisResult.enhanced_analysis.macd_signals.current_macd.toFixed(3) }}
                    </span>
                  </div>
                  <div class="macd-item">
                    <span class="macd-label">DIF</span>
                    <span class="macd-value" :class="analysisResult.enhanced_analysis.macd_signals.current_dif > 0 ? 'positive' : 'negative'">
                      {{ analysisResult.enhanced_analysis.macd_signals.current_dif.toFixed(3) }}
                    </span>
                  </div>
                  <div class="macd-item">
                    <span class="macd-label">DEA</span>
                    <span class="macd-value" :class="analysisResult.enhanced_analysis.macd_signals.current_dea > 0 ? 'positive' : 'negative'">
                      {{ analysisResult.enhanced_analysis.macd_signals.current_dea.toFixed(3) }}
                    </span>
                  </div>
                </div>
                <div v-if="analysisResult.enhanced_analysis.macd_signals.golden_cross" class="macd-signals">
                  <div class="signal-item">
                    <span class="signal-label">金叉信息</span>
                    <span class="signal-value">{{ analysisResult.enhanced_analysis.macd_signals.golden_cross.days_ago }}天前</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 综合评分 -->
            <div v-if="analysisResult.enhanced_analysis.comprehensive_score" class="rule-analysis-card">
              <div class="rule-header">
                <div class="rule-title">
                  <span class="rule-icon">🎯</span>
                  <span class="rule-name">综合评分</span>
                </div>
                <el-tag 
                  :type="analysisResult.enhanced_analysis.comprehensive_score.total_score > 60 ? 'success' : 
                        analysisResult.enhanced_analysis.comprehensive_score.total_score > 30 ? 'warning' : 'danger'"
                  size="small"
                >
                  {{ analysisResult.enhanced_analysis.comprehensive_score.total_score }}分
                </el-tag>
              </div>
              <div class="rule-content">
                <div class="score-breakdown">
                  <div 
                    v-for="(value, scoreKey) in analysisResult.enhanced_analysis.comprehensive_score.score_breakdown"
                    :key="scoreKey"
                    class="score-item"
                  >
                    <span class="score-label">{{ getScoreLabel(String(scoreKey)) }}</span>
                    <el-tag 
                      size="small"
                      :type="value === 'STRONG' ? 'success' : value === 'MODERATE' ? 'warning' : 'info'"
                    >
                      {{ value }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 分析摘要 -->
        <div class="result-section">
          <h4 class="section-title">分析摘要</h4>
          <div class="analysis-summary">
            <p class="summary-text">{{ analysisResult.analysis_summary }}</p>
          </div>
        </div>
        <!-- 操作按钮已移除 -->
      </div>

      <!-- 无分析结果状态 -->
      <div v-else class="no-result-state">
        <ChartBarIcon class="no-result-icon" />
        <p class="no-result-text">暂无分析结果</p>
        <p class="no-result-hint">点击"分析"按钮开始分析所选股票</p>
      </div>
    </div>

    <!-- 分析设置弹窗 -->
    <AnalysisSettingsModal 
      v-model="settingsModalVisible"
      :settings="analysisSettings"
      @settings-updated="onSettingsUpdated"
    />

    <!-- 股票池选择对话框 -->
    <StockPoolSelectDialog
      v-model="showStockPoolDialog"
      :pre-selected-stocks="currentStockForPool"
      :title="`将 ${selectedStock?.name} 添加到股票池`"
      :selector-title="'请选择要添加股票的股票池'"
      :allow-create="true"
      @confirmed="handleStockPoolConfirmed"
      @canceled="handleStockPoolCanceled"
      class="custom-stock-pool-dialog"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick, onUnmounted, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { 
  ArrowTrendingUpIcon,
  Cog6ToothIcon,
  PlayIcon,
  ChartBarIcon,
  ArrowDownIcon,
  ArrowUpIcon,
  ChartPieIcon,
  DocumentArrowDownIcon,
  BookmarkIcon
} from '@heroicons/vue/24/outline'

// 导入组件
import AnalysisSettingsModal from './AnalysisSettingsModal.vue'
import StockPoolSelectDialog from '@/components/StockPool/StockPoolSelectDialog.vue'

// 导入API
import { apiClient } from '@/api/base'

// PDF导出功能已移除

// Props
const props = defineProps<{
  selectedStock: {
    code: string
    name: string
    industry?: string
    market?: string
    poolId?: string
  } | null
}>()

// Emits
const emit = defineEmits<{
  analysisCompleted: [result: any]
  stockSelected: [stock: { code: string, name: string, industry?: string, market?: string }]
}>()

// 响应式数据
const analyzing = ref(false)
const analysisProgress = ref(0)
const analysisResult = ref<any>(null)
const settingsModalVisible = ref(false)
const chartDataLoaded = ref(false)

// 功能按钮相关状态
const exporting = ref(false)
const savingToPool = ref(false)
const showStockPoolDialog = ref(false)

// 时间范围选择
const dateRange = ref<[string, string]>([
  // 默认最近30天
  new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  new Date().toISOString().split('T')[0]
])

// 图表相关
const dowTheoryChart = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null
let resizeTimer: number | null = null

// 主题检测
const isDarkTheme = ref(false)

// 检测系统主题
const detectTheme = () => {
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  const htmlElement = document.documentElement
  const hasHtmlDarkClass = htmlElement.classList.contains('dark')
  const hasBodyDarkClass = document.body.classList.contains('dark')
  
  isDarkTheme.value = prefersDark || hasHtmlDarkClass || hasBodyDarkClass
}

// 获取主题相关颜色
const getThemeColors = () => {
  const isDark = isDarkTheme.value
  return {
    textPrimary: isDark ? '#ffffff' : '#1f2937',
    textSecondary: isDark ? '#d1d5db' : '#4b5563',
    textTertiary: isDark ? '#9ca3af' : '#6b7280',
    gridLine: isDark ? '#374151' : '#e5e7eb',
    tooltipBg: isDark ? '#374151' : '#ffffff',
    tooltipBorder: isDark ? '#4b5563' : '#d1d5db'
  }
}

// 搜索相关（简化）

// 分析设置
const analysisSettings = reactive({
  includeVolume: true,
  includeTechnical: true,
  timeframes: ['daily', 'weekly', 'monthly'],
  confidenceThreshold: 60
})


// 监听选中股票变化
watch(() => props.selectedStock, (newStock) => {
  if (newStock) {
    // 清空之前的分析结果
    analysisResult.value = null
    chartDataLoaded.value = false
  }
})

// 监听窗口尺寸变化和侧边栏状态变化
watch(() => {
  // 创建一个依赖项，当页面布局发生变化时触发
  return [window.innerWidth, window.innerHeight]
}, () => {
  // 延迟触发resize，确保布局稳定
  nextTick(() => {
    setTimeout(() => {
      if (chartInstance) {
        // 强制重新计算图表尺寸
        const container = dowTheoryChart.value
        if (container) {
          // 重置容器样式
          container.style.width = '100%'
          container.style.height = '100%'
          
          // 等待DOM更新后再resize
          requestAnimationFrame(() => {
            if (chartInstance) {
              chartInstance.resize({
                width: 'auto',
                height: 'auto'
              })
            }
          })
        }
      }
    }, 200)
  })
}, { deep: true })

// 监听侧边栏状态变化
const observeSidebarChanges = () => {
  const sidebar = document.querySelector('.sidebar')
  if (sidebar) {
    const sidebarObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          // 侧边栏状态改变，强制重新初始化图表
          console.log('侧边栏状态变化，重新计算图表尺寸')
          setTimeout(() => {
            if (chartInstance && dowTheoryChart.value) {
              console.log('开始重新计算图表尺寸')
              
              // 销毁当前图表实例
              chartInstance.dispose()
              
              // 重新创建图表实例
              chartInstance = echarts.init(dowTheoryChart.value)
              
              // 重新设置图表配置
              const currentData = analysisResult.value
              if (currentData) {
                // 延迟重新初始化确保DOM完全更新
                setTimeout(() => {
                  initChart()
                }, 100)
              }
            }
          }, 400) // 更长延迟确保侧边栏动画完成
        }
      })
    })
    
    sidebarObserver.observe(sidebar, {
      attributes: true,
      attributeFilter: ['class']
    })
    
    // 清理函数
    onUnmounted(() => {
      sidebarObserver.disconnect()
    })
  }
}

// 在组件挂载时开始观察
onMounted(() => {
  observeSidebarChanges()
  
  // 额外的全局resize监听
  const globalResize = () => {
    if (chartInstance && dowTheoryChart.value) {
      setTimeout(() => {
        console.log('全局resize触发图表重新计算')
        if (chartInstance) {
          chartInstance.resize({
            width: 'auto',
            height: 'auto'
          })
        }
      }, 200)
    }
  }
  
  window.addEventListener('resize', globalResize)
  
  // 清理函数
  onUnmounted(() => {
    window.removeEventListener('resize', globalResize)
  })
})

// 监听分析结果变化，更新图表
watch(() => analysisResult.value, (newResult) => {
  if (newResult) {
    nextTick(async () => {
      await initChart()
    })
  }
})

// 方法
const onDateRangeChange = (range: [string, string] | null) => {
  if (range) {
    dateRange.value = range
    // 如果已有分析结果，清除并提示重新分析
    if (analysisResult.value) {
      analysisResult.value = null
      chartDataLoaded.value = false
      ElMessage.info('时间范围已更改，请重新开始分析')
    }
  }
}

const startAnalysis = async () => {
  if (!props.selectedStock) {
    ElMessage.warning('请先选择要分析的股票')
    return
  }

  if (!dateRange.value || !dateRange.value[0] || !dateRange.value[1]) {
    ElMessage.warning('请选择分析时间范围')
    return
  }

  analyzing.value = true
  analysisProgress.value = 0
  
  try {
    // 模拟分析进度
    const progressInterval = setInterval(() => {
      if (analysisProgress.value < 90) {
        analysisProgress.value += Math.random() * 20
      }
    }, 200)

    // 调用后端API进行道氏理论分析，传递时间范围参数
    try {
      console.log('开始调用API分析股票:', props.selectedStock.code, '时间范围:', dateRange.value)
      const response = await apiClient.get(`/dow_theory/analyze/${props.selectedStock.code}`, {
        params: {
          start_date: dateRange.value[0],
          end_date: dateRange.value[1]
        }
      })
      
      console.log('API响应:', response)
      console.log('响应code:', response.code)
      console.log('响应数据:', response.data)
      
      // apiClient已经处理了HTTP状态码，这里检查业务状态码
      if (response.success && response.code === 200) {
        analysisResult.value = response.data
        console.log('设置分析结果:', analysisResult.value)
      } else {
        throw new Error(response.message || '分析失败')
      }
    } catch (apiError: any) {
      console.error('API调用详细错误:', apiError)
      console.error('错误类型:', typeof apiError)
      console.error('错误消息:', apiError.message)
      if (apiError.stack) {
        console.error('错误堆栈:', apiError.stack)
      }
      ElMessage.error(`分析失败: ${apiError.message || '未知错误'}`)
      return
    }
    
    analysisProgress.value = 100
    
    // 发送分析完成事件
    emit('analysisCompleted', {
      id: `${props.selectedStock.code}_dow_${Date.now()}`,
      stockCode: props.selectedStock.code,
      stockName: props.selectedStock.name,
      analysisType: 'dow_theory',  // 新增：分析类型标识
      overallTrend: analysisResult.value.overall_assessment?.overall_trend || 'unknown',
      overallPhase: analysisResult.value.overall_assessment?.overall_phase || 'unknown',
      confidence: analysisResult.value.overall_assessment?.overall_confidence || 0,
      recommendation: analysisResult.value.overall_assessment?.action_recommendation || 'hold',
      analysisDate: new Date().toISOString(),
      detailed: analysisResult.value
    })
    
    ElMessage.success('分析完成')
    
    clearInterval(progressInterval)
  } catch (error) {
    console.error('道氏理论分析失败:', error)
    ElMessage.error('分析失败，请重试')
  } finally {
    analyzing.value = false
    analysisProgress.value = 0
  }
}

const showSettingsModal = () => {
  settingsModalVisible.value = true
}

const onSettingsUpdated = (settings: any) => {
  Object.assign(analysisSettings, settings)
  settingsModalVisible.value = false
  ElMessage.success('设置已更新')
}

// exportAnalysis 方法已移除

const shareAnalysis = () => {
  if (!analysisResult.value) return
  
  // 分享分析结果逻辑
  const shareText = `${props.selectedStock?.name}(${props.selectedStock?.code}) 道氏理论分析：\n` +
    `整体趋势：${getTrendText(analysisResult.value.overall_assessment?.overall_trend)}\n` +
    `信心指数：${analysisResult.value.overall_assessment?.overall_confidence?.toFixed(1)}%\n` +
    `操作建议：${getRecommendationText(analysisResult.value.overall_assessment?.action_recommendation)}`
  
  if (navigator.share) {
    navigator.share({
      title: '道氏理论分析报告',
      text: shareText
    })
  } else {
    navigator.clipboard.writeText(shareText).then(() => {
      ElMessage.success('分析结果已复制到剪贴板')
    })
  }
}

const viewDetailedAnalysis = () => {
  // 查看详细分析逻辑
  ElMessage.info('详细分析功能开发中')
}

// 导出报告
const exportReport = async () => {
  if (!analysisResult.value || !props.selectedStock) {
    ElMessage.warning('暂无分析数据可导出')
    return
  }

  exporting.value = true
  try {
    const markdown = generateMarkdownReport()
    
    // 创建blob并下载
    const blob = new Blob([markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${props.selectedStock.name}(${props.selectedStock.code})_道氏理论分析报告_${new Date().toISOString().split('T')[0]}.md`
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

// 保存到股票池
const saveToPool = () => {
  if (!props.selectedStock) {
    ElMessage.warning('请先选择股票')
    return
  }

  if (!analysisResult.value) {
    ElMessage.warning('没有可添加的分析数据')
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

// 生成当前股票池数据
const currentStockForPool = computed(() => {
  if (!props.selectedStock) return []
  
  return [{
    ts_code: props.selectedStock.code,
    name: props.selectedStock.name,
    industry: props.selectedStock.industry || '',
    market_cap: 0,
    pe_ratio: 0,
    pb_ratio: 0
  }]
})

// 生成Markdown报告
const generateMarkdownReport = (): string => {
  const stock = props.selectedStock!
  const result = analysisResult.value
  const currentDate = new Date().toLocaleDateString('zh-CN')
  
  if (!result) {
    return `# 道氏理论分析报告\n\n暂无分析数据`
  }

  // 构建完整的分析报告
  let report = `# 道氏理论分析报告

## 📋 基本信息
- **股票代码**: ${stock.code}
- **股票名称**: ${stock.name}
- **所属行业**: ${stock.industry || 'N/A'}
- **当前价格**: ${result.basic_info?.current_price ? result.basic_info.current_price.toFixed(2) : 'N/A'} 元
- **分析日期**: ${result.basic_info?.analysis_date || currentDate}
- **分析时间范围**: ${dateRange.value[0]} 至 ${dateRange.value[1]}

## 📈 整体评估
- **整体趋势**: ${getTrendText(result.overall_assessment?.overall_trend || 'unknown')}
- **趋势阶段**: ${getPhaseText(result.overall_assessment?.overall_phase || 'unknown')}
- **信心指数**: ${result.overall_assessment?.overall_confidence ? result.overall_assessment.overall_confidence.toFixed(1) : 'N/A'}%
- **操作建议**: ${getRecommendationText(result.overall_assessment?.action_recommendation || 'hold')}

`

  // 添加多时间周期分析
  if (result.timeframe_analysis || result.detailed_analysis) {
    report += `## ⏰ 多时间周期分析

### 月线分析
${formatTimeframeAnalysis(result.timeframe_analysis?.monthly, 'monthly', result.detailed_analysis)}

### 周线分析
${formatTimeframeAnalysis(result.timeframe_analysis?.weekly, 'weekly', result.detailed_analysis)}

### 日线分析
${formatTimeframeAnalysis(result.timeframe_analysis?.daily, 'daily', result.detailed_analysis)}

`
  }

  // 添加多时间框架确认
  if (result.multi_timeframe_confirmation) {
    const confirmation = result.multi_timeframe_confirmation
    report += `## 🔄 多时间框架确认
- **主次要趋势一致性**: ${confirmation.primary_secondary_alignment ? '✅ 一致' : '❌ 不一致'}
- **次要短期趋势一致性**: ${confirmation.secondary_minor_alignment ? '✅ 一致' : '❌ 不一致'}
- **整体一致性**: ${confirmation.overall_alignment ? '✅ 一致' : '❌ 不一致'}
- **确认强度**: ${confirmation.confirmation_strength || 'N/A'}
${confirmation.conflicting_signals && confirmation.conflicting_signals.length > 0 ? 
  `- **冲突信号**: ${confirmation.conflicting_signals.join(', ')}` : ''}

`
  }

  // 添加风险评估
  if (result.risk_assessment) {
    const risk = result.risk_assessment
    report += `## ⚠️ 风险评估
- **风险等级**: ${risk.risk_level || 'N/A'}
- **止损价位**: ${risk.stop_loss_price ? risk.stop_loss_price.toFixed(2) : 'N/A'} 元
- **目标价位**: ${risk.target_price ? risk.target_price.toFixed(2) : 'N/A'} 元
- **建议仓位**: ${risk.position_suggestion ? (risk.position_suggestion > 1 ? risk.position_suggestion.toFixed(1) : (risk.position_suggestion * 100).toFixed(1)) : 'N/A'}%
${risk.key_risk_factors && risk.key_risk_factors.length > 0 ? 
  `- **主要风险因素**: ${risk.key_risk_factors.join(', ')}` : ''}

`
  }

  // 添加关键价位
  if (result.key_levels && result.key_levels.length > 0) {
    report += `## 🎯 关键价位
${result.key_levels.map((level: number) => `- ${level.toFixed(2)} 元`).join('\n')}

`
  }

  // 添加增强分析结果
  if (result.enhanced_analysis) {
    const enhanced = result.enhanced_analysis
    report += `## 🚀 增强分析

### 道氏理论123法则分析
${formatRuleAnalysis(enhanced.rule_123_analysis)}

### 道氏理论2B法则分析
${formatRuleAnalysis(enhanced.rule_2b_analysis)}

### MACD信号分析
${formatMACDAnalysis(enhanced.macd_signals)}

### 综合评分
${formatComprehensiveScore(enhanced.comprehensive_score)}

### 最终建议
${formatFinalRecommendation(enhanced.final_recommendation)}

`
  }

  // 添加详细分析
  if (result.detailed_analysis) {
    report += `## 📝 详细分析
${formatDetailedAnalysis(result.detailed_analysis.detailed_analysis || result.detailed_analysis)}

`
  }

  // 添加分析摘要
  if (result.analysis_summary) {
    report += `## 📊 分析摘要
${result.analysis_summary}

`
  }

  // 添加下次复查日期
  if (result.next_review_date) {
    report += `## 📅 下次复查日期
${result.next_review_date}

`
  }

  report += `---
*报告生成时间: ${new Date().toLocaleString('zh-CN')}*
*分析引擎: 道氏理论智能分析系统*`

  return report
}

// 格式化详细分析
const formatDetailedAnalysis = (detailedAnalysis: any): string => {
  if (!detailedAnalysis) return '暂无详细分析数据'
  
  if (typeof detailedAnalysis === 'string') {
    return detailedAnalysis
  }
  
  let content = ''
  
  // 格式化月线分析
  if (detailedAnalysis.monthly_analysis) {
    content += `### 📅 月线分析\n${detailedAnalysis.monthly_analysis.replace(/\\n/g, '\n')}\n\n`
  }
  
  // 格式化周线分析
  if (detailedAnalysis.weekly_analysis) {
    content += `### 📊 周线分析\n${detailedAnalysis.weekly_analysis.replace(/\\n/g, '\n')}\n\n`
  }
  
  // 格式化日线分析
  if (detailedAnalysis.daily_analysis) {
    content += `### 📈 日线分析\n${detailedAnalysis.daily_analysis.replace(/\\n/g, '\n')}\n\n`
  }
  
  // 格式化确认分析
  if (detailedAnalysis.confirmation_analysis) {
    content += `### 🔄 多时间周期确认分析\n${detailedAnalysis.confirmation_analysis.replace(/\\n/g, '\n')}\n\n`
  }
  
  // 如果没有结构化数据，尝试直接显示
  if (!content && detailedAnalysis) {
    // 尝试解析对象的所有键值对
    Object.entries(detailedAnalysis).forEach(([key, value]) => {
      const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
      content += `### ${formattedKey}\n${value}\n\n`
    })
  }
  
  return content || '详细分析数据格式异常'
}

// 获取信号强度样式类
const getSignalStrengthClass = (strength: string) => {
  const classMap: Record<string, string> = {
    'strong': 'strength-strong',
    'moderate': 'strength-moderate', 
    'weak': 'strength-weak'
  }
  return classMap[strength] || 'strength-unknown'
}

// 获取评分标签
const getScoreLabel = (key: string) => {
  const labelMap: Record<string, string> = {
    'rule_123': '123法则',
    'rule_2b': '2B法则',
    'macd': 'MACD',
    'trend': '趋势'
  }
  return labelMap[key] || key
}

// 辅助方法
const getTrendText = (trend: string) => {
  const trendMap: Record<string, string> = {
    'upward': '上升',
    'downward': '下降',
    'sideways': '横盘',
    'unknown': '未知'
  }
  return trendMap[trend] || trend
}

// 格式化时间周期分析
const formatTimeframeAnalysis = (analysis: any, timeframeName: string, detailedAnalysis: any): string => {
  if (!analysis && !detailedAnalysis) return '暂无数据'
  
  let content = ''
  
  // 优先从analysis获取数据，如果没有则从detailedAnalysis解析
  let trendDirection = analysis?.direction || analysis?.trend_direction
  let trendStrength = analysis?.trend_strength || analysis?.strength || '中等'
  let confidenceLevel = analysis?.confidence_score || analysis?.confidence_level
  let supportLevels: string[] = []
  let resistanceLevels: string[] = []
  
  // 如果analysis没有数据，尝试从detailed_analysis解析
  if (!trendDirection && detailedAnalysis) {
    const analysisKey = `${timeframeName.toLowerCase()}_analysis`
    const detailText = detailedAnalysis[analysisKey] || ''
    
    // 解析趋势方向
    const trendMatch = detailText.match(/趋势方向：(\w+)/)
    if (trendMatch) {
      trendDirection = trendMatch[1]
    }
    
    // 解析信心指数
    const confidenceMatch = detailText.match(/信心指数：([\d.]+)%/)
    if (confidenceMatch) {
      confidenceLevel = parseFloat(confidenceMatch[1])
    }
    
    // 解析支撑位
    const supportMatch = detailText.match(/支撑位：([\d., ]+)/)
    if (supportMatch) {
      supportLevels = supportMatch[1].split(', ').filter((s: string) => s.trim())
    }
    
    // 解析阻力位
    const resistanceMatch = detailText.match(/阻力位：([\d., ]+)/)
    if (resistanceMatch) {
      resistanceLevels = resistanceMatch[1].split(', ').filter((s: string) => s.trim())
    }
  } else if (analysis) {
    // 从analysis结构获取支撑阻力位
    if (analysis.support_resistance) {
      const supports = analysis.support_resistance.filter((sr: any) => sr.type === 'support')
      const resistances = analysis.support_resistance.filter((sr: any) => sr.type === 'resistance')
      supportLevels = supports.map((s: any) => s.level.toString())
      resistanceLevels = resistances.map((r: any) => r.level.toString())
    }
  }
  
  content += `- **趋势方向**: ${getTrendText(trendDirection || 'unknown')}\n`
  content += `- **趋势强度**: ${trendStrength || '中等'}\n`
  content += `- **信心水平**: ${confidenceLevel ? confidenceLevel.toFixed(1) : 'N/A'}%\n`
  
  if (supportLevels.length > 0) {
    content += `- **支撑位**: ${supportLevels.join(', ')} 元\n`
  }
  
  if (resistanceLevels.length > 0) {
    content += `- **阻力位**: ${resistanceLevels.join(', ')} 元\n`
  }
  
  if (analysis?.signals && analysis.signals.length > 0) {
    content += `- **信号**: ${analysis.signals.map((s: any) => `${s.type}(${s.strength})`).join(', ')}\n`
  }
  
  return content
}

// 格式化法则分析
const formatRuleAnalysis = (ruleAnalysis: any): string => {
  if (!ruleAnalysis) return '- **状态**: 暂无相关分析数据\n'
  
  let content = ''
  
  // 兼容不同的数据结构
  const triggered = ruleAnalysis.triggered ?? ruleAnalysis.is_triggered ?? false
  const strength = ruleAnalysis.strength ?? ruleAnalysis.signal_strength ?? 'N/A'
  const reliability = ruleAnalysis.reliability ?? ruleAnalysis.confidence ?? null
  const description = ruleAnalysis.description ?? ruleAnalysis.analysis ?? ruleAnalysis.summary
  
  content += `- **触发状态**: ${triggered ? '✅ 已触发' : '❌ 未触发'}\n`
  content += `- **信号强度**: ${strength}\n`
  content += `- **可信度**: ${reliability ? (typeof reliability === 'number' ? reliability.toFixed(1) : reliability) : 'N/A'}%\n`
  
  if (description) {
    content += `- **描述**: ${description}\n`
  }
  
  return content
}

// 格式化MACD分析
const formatMACDAnalysis = (macdAnalysis: any): string => {
  if (!macdAnalysis) return '- **状态**: 暂无MACD信号分析数据\n'
  
  let content = ''
  
  // 获取MACD当前状态
  const currentState = macdAnalysis.current_state ?? 
                      macdAnalysis.state ?? 
                      (macdAnalysis.golden_cross ? '金叉' : macdAnalysis.death_cross ? '死叉' : '正常')
  
  // 获取信号类型
  const signalType = macdAnalysis.signal_type ?? 
                    macdAnalysis.signal ?? 
                    (macdAnalysis.golden_cross ? '金叉信号' : macdAnalysis.death_cross ? '死叉信号' : '无明确信号')
  
  // 获取强度
  const strength = macdAnalysis.signal_strength ?? 
                  macdAnalysis.strength ?? 
                  (macdAnalysis.golden_cross?.strength ? 
                    (macdAnalysis.golden_cross.strength > 0.5 ? '强' : '弱') : 'N/A')
  
  // 获取背离情况
  const divergence = macdAnalysis.divergence ?? 
                    macdAnalysis.divergence_type ??
                    (macdAnalysis.divergence_signals ? 
                      (macdAnalysis.divergence_signals.bullish_divergence ? '看涨背离' : 
                       macdAnalysis.divergence_signals.bearish_divergence ? '看跌背离' : '无背离') : null)
  
  // 获取当前MACD值
  const currentMACD = macdAnalysis.current_macd
  const currentDIF = macdAnalysis.current_dif
  const currentDEA = macdAnalysis.current_dea
  
  content += `- **当前状态**: ${currentState}\n`
  content += `- **信号类型**: ${signalType}\n`
  content += `- **强度**: ${strength}\n`
  
  if (currentMACD !== undefined) {
    content += `- **当前MACD值**: ${currentMACD.toFixed(3)}\n`
  }
  
  if (currentDIF !== undefined && currentDEA !== undefined) {
    content += `- **DIF/DEA**: ${currentDIF.toFixed(3)} / ${currentDEA.toFixed(3)}\n`
  }
  
  if (divergence) {
    content += `- **背离情况**: ${divergence}\n`
  }
  
  // 如果有金叉信息
  if (macdAnalysis.golden_cross) {
    const daysAgo = macdAnalysis.golden_cross.days_ago
    content += `- **金叉信息**: ${daysAgo}天前发生金叉\n`
  }
  
  return content
}

// 格式化综合评分
const formatComprehensiveScore = (scoreData: any): string => {
  if (!scoreData) return '- **状态**: 暂无综合评分数据\n'
  
  let content = ''
  const totalScore = scoreData.total_score ?? scoreData.score ?? scoreData.overall_score
  
  content += `- **总分**: ${totalScore !== undefined ? totalScore : 'N/A'}\n`
  
  // 如果有评分组件信息
  if (scoreData.signal_components && scoreData.signal_components.length > 0) {
    content += `- **组件评分**:\n`
    scoreData.signal_components.forEach((component: any) => {
      const componentName = component.component === 'macd_analysis' ? 'MACD分析' :
                           component.component === 'enhanced_trend' ? '增强趋势' : component.component
      content += `  - ${componentName}: ${component.score} (权重: ${component.weight})\n`
    })
  }
  
  // 如果有评分细分
  if (scoreData.score_breakdown) {
    content += `- **评分细分**:\n`
    Object.entries(scoreData.score_breakdown).forEach(([key, value]) => {
      const keyMap: Record<string, string> = {
        'rule_123': '123法则',
        'rule_2b': '2B法则', 
        'macd': 'MACD',
        'trend': '趋势'
      }
      const translatedKey = keyMap[key] || key
      content += `  - ${translatedKey}: ${value}\n`
    })
  }
  
  return content
}

// 格式化最终建议
const formatFinalRecommendation = (recommendation: any): string => {
  if (!recommendation) return '- **状态**: 暂无最终建议数据\n'
  
  let content = ''
  const action = recommendation.action ?? recommendation.recommendation ?? 'hold'
  const confidence = recommendation.confidence
  const totalScore = recommendation.total_score
  const reasons = recommendation.reasons
  const riskFactors = recommendation.risk_factors
  
  content += `- **建议操作**: ${getRecommendationText(action)}\n`
  
  if (confidence !== undefined) {
    content += `- **信心度**: ${confidence}%\n`
  }
  
  if (totalScore !== undefined) {
    content += `- **综合得分**: ${totalScore}\n`
  }
  
  if (reasons && reasons.length > 0) {
    content += `- **理由**: ${reasons.join('; ')}\n`
  }
  
  if (riskFactors && riskFactors.length > 0) {
    content += `- **风险因素**: ${riskFactors.join('; ')}\n`
  }
  
  return content
}

const getTrendTagType = (trend: string) => {
  const typeMap: Record<string, string> = {
    'upward': 'success',
    'downward': 'danger',
    'sideways': 'warning',
    'unknown': 'info'
  }
  return typeMap[trend] || 'info'
}

const getPhaseText = (phase: string) => {
  const phaseMap: Record<string, string> = {
    'accumulation': '累积期',
    'public_participation': '公众参与期',
    'panic': '恐慌期',
    'unknown': '未知'
  }
  return phaseMap[phase] || phase
}


const getRecommendationText = (recommendation: string) => {
  const recMap: Record<string, string> = {
    'buy': '买入',
    'sell': '卖出',
    'hold': '持有',
    'wait': '观望'
  }
  return recMap[recommendation] || recommendation
}


const getRiskText = (riskLevel: string) => {
  const riskMap: Record<string, string> = {
    'low': '低风险',
    'medium': '中风险',
    'high': '高风险'
  }
  return riskMap[riskLevel] || riskLevel
}


const getTimeframeName = (timeframe: string) => {
  const nameMap: Record<string, string> = {
    'daily': '日线',
    'weekly': '周线',
    'monthly': '月线'
  }
  return nameMap[timeframe] || timeframe
}

const getConfidenceColor = (confidence: number | undefined) => {
  if (!confidence) return '#ef4444'
  if (confidence >= 80) return '#22c55e'
  if (confidence >= 60) return '#eab308'
  return '#ef4444'
}

// 新增样式类方法
const getTrendClass = (trend: string) => {
  const classMap: Record<string, string> = {
    'upward': 'trend-up',
    'downward': 'trend-down',
    'sideways': 'trend-sideways',
    'unknown': 'trend-unknown'
  }
  return classMap[trend] || 'trend-unknown'
}

const getPhaseClass = (phase: string) => {
  const classMap: Record<string, string> = {
    'accumulation': 'phase-accumulation',
    'public_participation': 'phase-participation',
    'panic': 'phase-panic',
    'unknown': 'phase-unknown'
  }
  return classMap[phase] || 'phase-unknown'
}

const getRecommendationClass = (recommendation: string) => {
  const classMap: Record<string, string> = {
    'buy': 'action-buy',
    'sell': 'action-sell',
    'hold': 'action-hold',
    'wait': 'action-wait'
  }
  return classMap[recommendation] || 'action-hold'
}

const getRiskLevelClass = (riskLevel: string) => {
  const classMap: Record<string, string> = {
    'low': 'risk-low',
    'medium': 'risk-medium',
    'high': 'risk-high'
  }
  return classMap[riskLevel] || 'risk-medium'
}

// 图表相关方法
const initChart = async () => {
  if (!dowTheoryChart.value || !analysisResult.value) return
  
  chartDataLoaded.value = false
  
  // 销毁现有图表实例
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  // 获取真实历史数据
  const priceData = await fetchHistoricalData()
  
  if (!priceData) {
    chartDataLoaded.value = false
    return
  }
  
  // 创建新的图表实例
  chartInstance = echarts.init(dowTheoryChart.value)
  chartDataLoaded.value = true
  
  // 强制设置图表尺寸
  if (chartInstance) {
    setTimeout(() => {
      if (chartInstance) {
        chartInstance.resize({
          width: 'auto',
          height: 'auto'
        })
      }
    }, 100)
  }
  
  // 配置图表选项 - 简化版线图
  const option = {
    backgroundColor: 'transparent',
    title: {
      text: `${props.selectedStock?.name || ''} 道氏理论分析`,
      subtext: `趋势: ${getTrendText(analysisResult.value.overall_assessment?.overall_trend)} | 信心: ${analysisResult.value.overall_assessment?.overall_confidence?.toFixed(1)}%`,
      left: 'center',
      textStyle: {
        color: '#ffffff',
        fontSize: 16
      },
      subtextStyle: {
        color: '#00d4ff',
        fontSize: 12
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      backgroundColor: getThemeColors().tooltipBg,
      borderColor: getThemeColors().tooltipBorder,
      textStyle: {
        color: getThemeColors().textPrimary
      },
      formatter: (params: any) => {
        let result = `<div style="margin-bottom: 8px; font-weight: bold;">${params[0].axisValue}</div>`
        params.forEach((param: any) => {
          if (param.seriesName === '收盘价' && param.value !== null) {
            result += `<div style="margin: 4px 0;">
              <span style="color: #00d4ff;">●</span> 收盘价: ¥${param.value.toFixed(2)}
            </div>`
          } else if (param.seriesName === '信心强度' && param.value !== null) {
            result += `<div style="margin: 4px 0;">
              <span style="color: #22c55e;">●</span> 信心强度: ${param.value.toFixed(1)}%
            </div>`
          } else if (param.seriesName === '成交量' && param.value !== null) {
            const volume = param.value >= 1000000 ? (param.value / 1000000).toFixed(1) + 'M' : 
                          param.value >= 1000 ? (param.value / 1000).toFixed(1) + 'K' : param.value
            result += `<div style="margin: 4px 0;">
              <span style="color: #ffa500;">■</span> 成交量: ${volume}
            </div>`
          } else if (param.seriesName === '背离信号' && param.value !== null) {
            const signalType = param.value[3] === 'bullish' ? '看涨背离' : '看跌背离'
            const strength = (param.value[2] * 100).toFixed(0)
            result += `<div style="margin: 4px 0;">
              <span style="color: ${param.value[3] === 'bullish' ? '#22c55e' : '#ef4444'};">◆</span> ${signalType} (强度: ${strength}%)
            </div>`
          } else if (param.seriesName.includes('支撑') && param.value !== null) {
            const color = param.seriesName.includes('日线') ? '#86efac' : 
                         param.seriesName.includes('周线') ? '#22c55e' : '#059669'
            result += `<div style="margin: 3px 0;">
              <span style="color: ${color};">━</span> ${param.seriesName}: ¥${param.value.toFixed(2)}
            </div>`
          } else if (param.seriesName.includes('阻力') && param.value !== null) {
            const color = param.seriesName.includes('日线') ? '#fca5a5' : 
                         param.seriesName.includes('周线') ? '#ef4444' : '#dc2626'
            result += `<div style="margin: 3px 0;">
              <span style="color: ${color};">━</span> ${param.seriesName}: ¥${param.value.toFixed(2)}
            </div>`
          }
        })
        return result
      }
    },
    legend: {
      data: ['收盘价', '信心强度', '成交量', '日线支撑', '周线支撑', '月线支撑', '日线阻力', '周线阻力', '月线阻力', '背离信号'],
      top: 50,
      textStyle: {
        color: getThemeColors().textPrimary
      }
    },
    grid: {
      left: '5%',
      right: '5%',
      bottom: '15%',
      top: '20%',
      containLabel: true
    },
    toolbox: {
      feature: {
        dataZoom: {
          yAxisIndex: 'none'
        },
        restore: {},
        saveAsImage: {
          backgroundColor: isDarkTheme.value ? '#1a1a1a' : '#ffffff'
        }
      },
      iconStyle: {
        borderColor: getThemeColors().textSecondary
      }
    },
    xAxis: {
      type: 'category',
      data: priceData?.dates || [],
      axisLine: {
        lineStyle: {
          color: getThemeColors().textSecondary
        }
      },
      axisTick: {
        lineStyle: {
          color: getThemeColors().textSecondary
        }
      },
      axisLabel: {
        color: getThemeColors().textSecondary
      }
    },
    yAxis: [
      {
        type: 'value',
        scale: true,
        position: 'left',
        axisLine: {
          lineStyle: {
            color: getThemeColors().textSecondary
          }
        },
        axisTick: {
          lineStyle: {
            color: getThemeColors().textSecondary
          }
        },
        axisLabel: {
          color: getThemeColors().textSecondary
        },
        splitLine: {
          lineStyle: {
            color: getThemeColors().gridLine
          }
        }
      },
      {
        type: 'value',
        scale: true,
        position: 'right',
        min: 0,
        max: 100,
        axisLine: {
          lineStyle: {
            color: '#00d4ff'
          }
        },
        axisTick: {
          lineStyle: {
            color: '#00d4ff'
          }
        },
        axisLabel: {
          color: '#00d4ff',
          formatter: '{value}%'
        },
        splitLine: {
          show: false
        }
      },
      {
        type: 'value',
        scale: true,
        position: 'right',
        offset: 60,
        min: 0,
        axisLine: {
          lineStyle: {
            color: '#ffa500'
          }
        },
        axisTick: {
          lineStyle: {
            color: '#ffa500'
          }
        },
        axisLabel: {
          color: '#ffa500',
          formatter: (value: number) => {
            if (value >= 1000000) {
              return (value / 1000000).toFixed(1) + 'M'
            } else if (value >= 1000) {
              return (value / 1000).toFixed(1) + 'K'
            }
            return value.toString()
          }
        },
        splitLine: {
          show: false
        }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        start: 70,
        end: 100
      },
      {
        show: true,
        type: 'slider',
        top: '90%',
        start: 70,
        end: 100,
        textStyle: {
          color: getThemeColors().textSecondary
        }
      }
    ],
    series: [
      // 收盘价线图
      {
        name: '收盘价',
        type: 'line',
        data: priceData?.closePrices || [],
        smooth: true,
        lineStyle: {
          color: '#00d4ff',
          width: 2
        },
        itemStyle: {
          color: '#00d4ff'
        },
        symbol: 'circle',
        symbolSize: 4,
        emphasis: {
          focus: 'series'
        }
      },
      // 信心强度线图
      {
        name: '信心强度',
        type: 'line',
        yAxisIndex: 1,
        data: generateConfidenceData(priceData?.dates || [], analysisResult.value),
        smooth: true,
        lineStyle: {
          color: '#22c55e',
          width: 2
        },
        itemStyle: {
          color: '#22c55e'
        },
        symbol: 'circle',
        symbolSize: 4,
        emphasis: {
          focus: 'series'
        }
      },
      // 成交量面积图
      {
        name: '成交量',
        type: 'line',
        yAxisIndex: 2,
        data: priceData.volume || [],  
        lineStyle: {
          width: 1,
          color: '#ffa500'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [{
              offset: 0,
              color: 'rgba(255, 165, 0, 0.6)'
            }, {
              offset: 1,
              color: 'rgba(255, 165, 0, 0.1)'
            }]
          }
        },
        symbol: 'none',
        emphasis: {
          focus: 'series'
        }
      },
      // 日线支撑位标记 - 浅绿色
      {
        name: '日线支撑',
        type: 'line',
        data: generateSupportResistanceData(priceData?.dates || [], analysisResult.value, 'support', 'daily'),
        lineStyle: {
          color: '#86efac',
          width: 1.5,
          type: 'dashed'
        },
        symbol: 'none',
        emphasis: {
          focus: 'series'
        }
      },
      // 周线支撑位标记 - 中绿色
      {
        name: '周线支撑',
        type: 'line',
        data: generateSupportResistanceData(priceData?.dates || [], analysisResult.value, 'support', 'weekly'),
        lineStyle: {
          color: '#22c55e',
          width: 2,
          type: 'dashed'
        },
        symbol: 'none',
        emphasis: {
          focus: 'series'
        }
      },
      // 月线支撑位标记 - 深绿色
      {
        name: '月线支撑',
        type: 'line',
        data: generateSupportResistanceData(priceData?.dates || [], analysisResult.value, 'support', 'monthly'),
        lineStyle: {
          color: '#059669',
          width: 3,
          type: 'solid'
        },
        symbol: 'none',
        emphasis: {
          focus: 'series'
        }
      },
      // 日线阻力位标记 - 浅红色
      {
        name: '日线阻力',
        type: 'line',
        data: generateSupportResistanceData(priceData?.dates || [], analysisResult.value, 'resistance', 'daily'),
        lineStyle: {
          color: '#fca5a5',
          width: 1.5,
          type: 'dashed'
        },
        symbol: 'none',
        emphasis: {
          focus: 'series'
        }
      },
      // 周线阻力位标记 - 中红色
      {
        name: '周线阻力',
        type: 'line',
        data: generateSupportResistanceData(priceData?.dates || [], analysisResult.value, 'resistance', 'weekly'),
        lineStyle: {
          color: '#ef4444',
          width: 2,
          type: 'dashed'
        },
        symbol: 'none',
        emphasis: {
          focus: 'series'
        }
      },
      // 月线阻力位标记 - 深红色
      {
        name: '月线阻力',
        type: 'line',
        data: generateSupportResistanceData(priceData?.dates || [], analysisResult.value, 'resistance', 'monthly'),
        lineStyle: {
          color: '#dc2626',
          width: 3,
          type: 'solid'
        },
        symbol: 'none',
        emphasis: {
          focus: 'series'
        }
      },
      // 背离信号点标注
      {
        name: '背离信号',
        type: 'scatter',
        data: generateDivergenceSignals(priceData?.dates || [], analysisResult.value),
        symbolSize: (value: any) => {
          return value[2] * 20 // 根据信号强度调整大小
        },
        itemStyle: {
          color: (params: any) => {
            return params.value[3] === 'bullish' ? '#22c55e' : '#ef4444'
          },
          borderColor: '#ffffff',
          borderWidth: 2
        },
        emphasis: {
          focus: 'series'
        },
        zlevel: 10
      }
    ]
  }
  
  // 设置图表配置
  chartInstance.setOption(option)
  
  // 立即调整图表大小
  nextTick(() => {
    if (chartInstance) {
      chartInstance.resize()
    }
  })
  
  // 响应式调整大小 - 防抖处理
  const handleResize = () => {
    if (resizeTimer) {
      clearTimeout(resizeTimer)
    }
    
    resizeTimer = setTimeout(() => {
      if (chartInstance && chartInstance.getDom()) {
        // 强制重新计算容器尺寸
        const container = dowTheoryChart.value
        if (container) {
          // 确保容器尺寸被重新计算
          container.style.width = '100%'
          container.style.height = '100%'
        }
        
        // 延迟调用resize确保DOM更新完成
        requestAnimationFrame(() => {
          if (chartInstance) {
            chartInstance.resize({
              width: 'auto',
              height: 'auto'
            })
          }
        })
      }
    }, 150)
  }
  
  // 移除之前的监听器并添加新的
  window.removeEventListener('resize', handleResize)
  window.addEventListener('resize', handleResize)
  
  // 使用ResizeObserver监听容器尺寸变化
  if (dowTheoryChart.value) {
    // 清理旧的observer
    if (resizeObserver) {
      resizeObserver.disconnect()
    }
    
    resizeObserver = new ResizeObserver((entries) => {
      if (chartInstance && chartInstance.getDom()) {
        // 检查容器是否可见
        const container = dowTheoryChart.value
        if (container && container.offsetWidth > 0 && container.offsetHeight > 0) {
          console.log('ResizeObserver 检测到容器尺寸变化:', container.offsetWidth, container.offsetHeight)
          handleResize()
        }
      }
    })
    resizeObserver.observe(dowTheoryChart.value)
    
    // 观察父容器变化
    const parentContainer = dowTheoryChart.value.closest('.chart-container')
    if (parentContainer) {
      resizeObserver.observe(parentContainer)
    }
    
    // 观察面板容器变化
    const panelContainer = dowTheoryChart.value.closest('.dow-analysis-panel')
    if (panelContainer) {
      resizeObserver.observe(panelContainer)
    }
  }
}

// 获取真实历史数据
const fetchHistoricalData = async () => {
  if (!props.selectedStock) return null
  
  try {
    // 根据用户选择的日期范围或默认60天来获取历史数据
    let apiUrl
    if (dateRange.value && dateRange.value[0] && dateRange.value[1]) {
      // 使用用户选择的日期范围
      apiUrl = `/dow_theory/historical_data/${props.selectedStock.code}?start_date=${dateRange.value[0]}&end_date=${dateRange.value[1]}`
    } else {
      // 使用默认60天
      apiUrl = `/dow_theory/historical_data/${props.selectedStock.code}?days=60`
    }
    
    const response = await apiClient.get(apiUrl)
    
    if (response.success && response.code === 200) {
      const data = response.data
      
      // 转换为图表需要的格式
      const dates = data.dates
      const closePrices = data.prices.close
      const klineData = dates.map((date: string, i: number) => [
        data.prices.open[i],
        data.prices.close[i],
        data.prices.low[i],
        data.prices.high[i]
      ])
      
      // 获取MA20数据
      const ma20Data = data.technical_indicators.ma20 || []
      
      return { dates, klineData, ma20Data, closePrices, volume: data.volume }
    } else {
      throw new Error(response.message || '获取历史数据失败')
    }
  } catch (error) {
    console.error('获取历史数据失败:', error)
    ElMessage.error('获取历史数据失败，图表将不显示')
    return null
  }
}


// 生成信心强度数据
const generateConfidenceData = (dates: string[], analysisData: any) => {
  const data = []
  const baseConfidence = analysisData.overall_assessment?.overall_confidence || 60
  
  // 根据分析结果生成信心强度曲线
  for (let i = 0; i < dates.length; i++) {
    // 模拟信心强度随时间的变化
    const progress = i / dates.length
    let confidence = baseConfidence
    
    // 根据道氏理论阶段调整信心强度
    const phase = analysisData.overall_assessment?.overall_phase
    if (phase === 'accumulation') {
      confidence += Math.sin(progress * Math.PI * 2) * 10
    } else if (phase === 'public_participation') {
      confidence += 15 - progress * 20
    } else if (phase === 'panic') {
      confidence -= progress * 30
    }
    
    // 确保在合理范围内
    confidence = Math.max(0, Math.min(100, confidence))
    data.push(Number(confidence.toFixed(1)))
  }
  
  return data
}

// 生成支撑阻力位数据
const generateSupportResistanceData = (dates: string[], analysisData: any, type: 'support' | 'resistance', timeframe?: string) => {
  const data = []
  
  // 获取基准价格
  let basePrice = 50.0
  if (analysisData?.timeframe_analysis) {
    const timeframes = Object.values(analysisData.timeframe_analysis)
    const currentPriceData = timeframes.find((tf: any) => tf.technical_indicators?.current_price)
    if (currentPriceData) {
      basePrice = (currentPriceData as any).technical_indicators.current_price
    }
  }
  
  // 从分析结果中获取支撑阻力位
  const timeframes = analysisData.timeframe_analysis || {}
  let levels: number[] = []
  
  // 如果指定了时间周期，只从该周期获取数据
  if (timeframe) {
    const timeframeData = timeframes[timeframe]
    if (timeframeData?.support_resistance) {
      const filteredLevels = timeframeData.support_resistance
        .filter((sr: any) => sr.type === type)
        .map((sr: any) => sr.level)
      levels = levels.concat(filteredLevels)
    }
  } else {
    // 从所有时间周期获取数据
    Object.values(timeframes).forEach((timeframeData: any) => {
      if (timeframeData.support_resistance) {
        const filteredLevels = timeframeData.support_resistance
          .filter((sr: any) => sr.type === type)
          .map((sr: any) => sr.level)
        levels = levels.concat(filteredLevels)
      }
    })
  }
  
  // 如果没有数据，生成合理的支撑阻力位
  let avgLevel: number
  if (levels.length > 0) {
    avgLevel = levels.reduce((a, b) => a + b, 0) / levels.length
  } else {
    // 基于当前价格和时间周期生成合理的支撑阻力位
    let multiplier = 1.0
    if (timeframe === 'daily') {
      multiplier = type === 'support' ? 0.97 : 1.03
    } else if (timeframe === 'weekly') {
      multiplier = type === 'support' ? 0.95 : 1.05
    } else if (timeframe === 'monthly') {
      multiplier = type === 'support' ? 0.90 : 1.10
    } else {
      multiplier = type === 'support' ? 0.95 : 1.05
    }
    avgLevel = basePrice * multiplier
  }
  
  // 在图表中显示关键位置线
  for (let i = 0; i < dates.length; i++) {
    data.push(Number(avgLevel.toFixed(2)))
  }
  
  return data
}

// 生成趋势强度数据
const generateTrendStrengthData = (dates: string[], analysisData: any) => {
  const data = []
  const baseConfidence = analysisData.overall_assessment?.overall_confidence || 60
  
  // 根据分析结果生成趋势强度曲线
  for (let i = 0; i < dates.length; i++) {
    // 模拟趋势强度随时间的变化
    const progress = i / dates.length
    let strength = baseConfidence
    
    // 根据道氏理论阶段调整强度
    const phase = analysisData.overall_assessment?.overall_phase
    if (phase === 'accumulation') {
      strength += Math.sin(progress * Math.PI * 2) * 10
    } else if (phase === 'public_participation') {
      strength += 15 - progress * 20
    } else if (phase === 'panic') {
      strength -= progress * 30
    }
    
    // 确保在合理范围内
    strength = Math.max(0, Math.min(100, strength))
    data.push(strength.toFixed(1))
  }
  
  return data
}

// 生成背离信号点
const generateDivergenceSignals = (dates: string[], analysisData: any) => {
  const signals: Array<[number, number, number, string]> = []
  
  // 获取基准价格
  let basePrice = 50.0
  if (analysisData?.timeframe_analysis) {
    const timeframes = Object.values(analysisData.timeframe_analysis)
    const currentPriceData = timeframes.find((tf: any) => tf.technical_indicators?.current_price)
    if (currentPriceData) {
      basePrice = (currentPriceData as any).technical_indicators.current_price
    }
  }
  
  // 分析各时间周期的成交量背离信号
  const timeframes = analysisData.timeframe_analysis || {}
  Object.entries(timeframes).forEach(([timeframe, data]: [string, any]) => {
    if (data.volume_analysis?.divergence_signal) {
      const signalIndex = Math.floor(dates.length * (timeframe === 'daily' ? 0.9 : timeframe === 'weekly' ? 0.7 : 0.5))
      if (signalIndex < dates.length) {
        const signalType = data.volume_analysis.pattern === 'increasing' ? 'bullish' : 'bearish'
        const strength = data.volume_analysis.strength === 'strong' ? 0.8 : 0.5
        
        // [x坐标, y坐标(价格), 信号强度, 信号类型]
        signals.push([
          signalIndex,
          basePrice * (signalType === 'bullish' ? 1.02 : 0.98),
          strength,
          signalType
        ])
      }
    }
  })
  
  // 如果没有真实的背离信号，生成示例信号点用于演示
  if (signals.length === 0) {
    signals.push([Math.floor(dates.length * 0.3), basePrice * 0.98, 0.6, 'bearish'])
    signals.push([Math.floor(dates.length * 0.8), basePrice * 1.02, 0.7, 'bullish'])
  }
  
  return signals
}

// 生成道氏理论关键信号点
const generateDowTheorySignals = (dates: string[], analysisData: any) => {
  const signals: Array<[number, number, number, string]> = []
  
  // 获取基准价格
  let basePrice = 50.0
  if (analysisData?.timeframe_analysis) {
    const timeframes = Object.values(analysisData.timeframe_analysis)
    const currentPriceData = timeframes.find((tf: any) => tf.technical_indicators?.current_price)
    if (currentPriceData) {
      basePrice = (currentPriceData as any).technical_indicators.current_price
    }
  }
  
  // 根据道氏理论阶段设定信号点
  const phase = analysisData.overall_assessment?.overall_phase || 'accumulation'
  const trend = analysisData.overall_assessment?.overall_trend || 'sideways'
  const confidence = (analysisData.overall_assessment?.overall_confidence || 60) / 100
  
  // 在关键时间点标注道氏理论信号
  const signalPoints = [
    { 
      index: Math.floor(dates.length * 0.2), 
      type: phase === 'accumulation' ? '累积期开始' : '趋势起始', 
      confidence: 0.7,
      price: basePrice * 0.98
    },
    { 
      index: Math.floor(dates.length * 0.4), 
      type: trend === 'upward' ? '向上突破' : trend === 'downward' ? '向下突破' : '横盘确认', 
      confidence: 0.8,
      price: basePrice * 1.02
    },
    { 
      index: Math.floor(dates.length * 0.7), 
      type: '趋势延续', 
      confidence: 0.6,
      price: basePrice * 1.01
    },
    { 
      index: Math.floor(dates.length * 0.9), 
      type: '当前位置', 
      confidence: confidence,
      price: basePrice
    }
  ]
  
  signalPoints.forEach(signal => {
    if (signal.index < dates.length) {
      // [x坐标, y坐标(价格), 信心度, 信号类型]
      signals.push([signal.index, Number(signal.price.toFixed(2)), signal.confidence, signal.type])
    }
  })
  
  return signals
}


// 生命周期钩子
onMounted(() => {
  // 初始化主题检测
  detectTheme()
  
  // 监听系统主题变化
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  const handleThemeChange = () => {
    detectTheme()
    // 如果图表已经初始化，重新绘制以应用新主题
    if (chartInstance && analysisResult.value) {
      nextTick(() => {
        initChart()
      })
    }
  }
  
  mediaQuery.addEventListener('change', handleThemeChange)
  
  // 监听DOM类名变化（用于手动切换主题）
  const observer = new MutationObserver(() => {
    detectTheme()
    if (chartInstance && analysisResult.value) {
      nextTick(() => {
        initChart()
      })
    }
  })
  
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class']
  })
  observer.observe(document.body, {
    attributes: true,
    attributeFilter: ['class']
  })
  
  // 清理函数将在组件卸载时调用
  onUnmounted(() => {
    mediaQuery.removeEventListener('change', handleThemeChange)
    observer.disconnect()
  })
})

onUnmounted(() => {
  // 清理定时器
  if (resizeTimer) {
    clearTimeout(resizeTimer)
    resizeTimer = null
  }
  
  // 清理图表实例
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  
  // 清理ResizeObserver
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  
  // 清理window resize监听器
  const handleResize = () => {
    if (resizeTimer) {
      clearTimeout(resizeTimer)
    }
    
    resizeTimer = setTimeout(() => {
      if (chartInstance && chartInstance.getDom()) {
        // 强制重新计算容器尺寸
        const container = dowTheoryChart.value
        if (container) {
          // 确保容器尺寸被重新计算
          container.style.width = '100%'
          container.style.height = '100%'
        }
        
        // 延迟调用resize确保DOM更新完成
        requestAnimationFrame(() => {
          if (chartInstance) {
            chartInstance.resize({
              width: 'auto',
              height: 'auto'
            })
          }
        })
      }
    }, 150)
  }
  window.removeEventListener('resize', handleResize)
})

// 暴露给父组件的方法
defineExpose({
  refreshAnalysis: startAnalysis
})
</script>

<style scoped>
.dow-analysis-panel {
  min-height: 600px; /* 设置最小高度，允许内容自动扩展 */
  height: auto; /* 改为自动高度 */
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  background: var(--bg-secondary);
  overflow: visible; /* 允许内容自然展开 */
  max-width: 100%;
  box-sizing: border-box;
}

/* ========== 面板标题 ========== */
.panel-header {
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-elevated);
  gap: var(--spacing-md);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  flex: 0 0 auto;
}

.title-icon {
  width: 20px;
  height: 20px;
  color: var(--accent-primary);
}

.panel-search {
  flex: 1;
  max-width: 300px;
  margin: 0 var(--spacing-md);
}

.panel-actions {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
  flex: 0 0 auto;
}

/* 日期范围选择器样式 */
.date-range-selector {
  min-width: 280px;
  
  .el-date-editor {
    --el-date-editor-width: 280px;
  }
}

.action-icon {
  width: 14px;
  height: 14px;
}

/* ========== 面板内容 ========== */
.panel-content {
  flex: 1;
  overflow-y: visible; /* 移除滚动条，允许内容自然展开 */
  padding: var(--spacing-lg);
  max-width: 100%;
  box-sizing: border-box;
}

/* ========== 空状态 ========== */
.empty-state,
.no-result-state {
  text-align: center;
  padding: var(--spacing-xl) 0;
}

/* ========== 股票搜索 ========== */
.stock-search-section {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  text-align: left;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}

.search-header h4 {
  margin: 0 0 var(--spacing-md) 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
}

.empty-icon,
.no-result-icon {
  width: 64px;
  height: 64px;
  color: var(--text-tertiary);
  margin: 0 auto var(--spacing-lg);
}

.empty-text,
.no-result-text {
  font-size: 16px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-sm);
}

.empty-hint,
.no-result-hint {
  font-size: 14px;
  color: var(--text-tertiary);
}

/* ========== 分析中状态 ========== */
.analyzing-state {
  text-align: center;
  padding: var(--spacing-xl) 0;
}

.analyzing-animation {
  margin-bottom: var(--spacing-lg);
}

.analyzing-icon {
  width: 64px;
  height: 64px;
  color: var(--accent-primary);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.5;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.1);
  }
}

.analyzing-text {
  font-size: 16px;
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.analyzing-hint {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-lg);
}

/* ========== 分析结果 ========== */
.analysis-result {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  max-width: 100%;
  overflow: hidden;
}

/* ========== 图表区域 ========== */
.chart-section {
  padding: 0;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.chart-section .section-title {
  padding: var(--spacing-md) var(--spacing-lg);
  margin: 0;
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border-primary);
}

.chart-container {
  padding: var(--spacing-md);
  background: var(--bg-primary);
  position: relative;
  min-height: 500px; /* 设置最小高度 */
  height: auto; /* 改为自动高度 */
  overflow: visible; /* 允许内容自然展开 */
  display: flex;
  flex-direction: column;
  width: 100%;
  box-sizing: border-box;
  transition: all 0.3s ease;
}

.dow-theory-chart {
  width: 100%;
  min-height: 500px; /* 设置最小高度 */
  height: auto; /* 改为自动高度 */
  max-width: 100%;
  background: transparent;
  transition: all 0.3s ease;
  flex: 1;
  overflow: visible; /* 允许内容自然展开 */
}

.chart-no-data {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  z-index: 10;
}

.no-data-icon {
  width: 48px;
  height: 48px;
  color: var(--text-tertiary);
  margin: 0 auto var(--spacing-md);
}

.no-data-text {
  font-size: 16px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-sm);
}

.no-data-hint {
  font-size: 14px;
  color: var(--text-tertiary);
}

.result-section {
  padding: var(--spacing-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-md) 0;
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

/* ========== 综合评价仪表板 ========== */
.analysis-dashboard {
  display: flex;
  align-items: center;
  gap: var(--spacing-xl);
  padding: var(--spacing-lg);
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-secondary);
}

.confidence-gauge {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

.confidence-content {
  text-align: center;
}

.confidence-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.confidence-label {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.trend-indicators {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
}

.indicator-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-primary);
  transition: all var(--transition-base);
}

.indicator-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-icon {
  flex: 0 0 auto;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--accent-primary);
}

.card-icon .icon {
  width: 20px;
  height: 20px;
  color: white;
}

.card-content {
  flex: 1;
  min-width: 0;
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
  line-height: 1.2;
}

/* 趋势值颜色 */
.trend-up {
  color: var(--success-primary);
}

.trend-down {
  color: var(--danger-primary);
}

.trend-sideways {
  color: var(--warning-primary);
}

.trend-unknown {
  color: var(--text-tertiary);
}

/* 阶段值颜色 */
.phase-accumulation {
  color: var(--accent-primary);
}

.phase-participation {
  color: var(--success-primary);
}

.phase-panic {
  color: var(--danger-primary);
}

.phase-unknown {
  color: var(--text-tertiary);
}

/* 操作建议颜色 */
.action-buy {
  color: var(--success-primary);
}

.action-sell {
  color: var(--danger-primary);
}

.action-hold {
  color: var(--accent-primary);
}

.action-wait {
  color: var(--warning-primary);
}

/* ========== 多时间周期分析 ========== */
.timeframe-analysis {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.timeframe-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all var(--transition-base);
}

.timeframe-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border-color: var(--accent-primary);
}

.timeframe-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-secondary);
}

.timeframe-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.timeframe-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.confidence-badge {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.confidence-text {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 500;
  min-width: 35px;
}

.confidence-bar {
  width: 60px;
  height: 6px;
  background: var(--bg-secondary);
  border-radius: 3px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  border-radius: 3px;
  transition: width var(--transition-base);
}

.trend-badge {
  flex-shrink: 0;
}

.timeframe-content {
  padding: var(--spacing-md);
}

.technical-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.tech-item {
  text-align: center;
  padding: var(--spacing-sm);
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-primary);
}

.tech-label {
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 4px;
  font-weight: 500;
}

.tech-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.price-value {
  color: var(--accent-primary);
}

.ma-value {
  color: var(--warning-primary);
}

.rsi-value {
  color: var(--success-primary);
}

.support-resistance-chart {
  border-top: 1px solid var(--border-secondary);
  padding-top: var(--spacing-sm);
}

.sr-title {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-sm);
  font-weight: 500;
}

.sr-levels {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.sr-level {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-primary);
  background: var(--bg-primary);
  min-width: 80px;
  text-align: center;
}

.sr-level.support {
  border-color: var(--success-primary);
  background: rgba(34, 197, 94, 0.1);
}

.sr-level.resistance {
  border-color: var(--warning-primary);
  background: rgba(234, 179, 8, 0.1);
}

.sr-label {
  font-size: 10px;
  color: var(--text-tertiary);
  margin-bottom: 2px;
}

.sr-level.support .sr-label {
  color: var(--success-primary);
}

.sr-level.resistance .sr-label {
  color: var(--warning-primary);
}

.sr-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

/* ========== 风险评估 ========== */
.risk-assessment {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.risk-level-display {
  display: flex;
  align-items: center;
  gap: var(--spacing-xl);
  padding: var(--spacing-lg);
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-secondary);
}

.risk-level-indicator {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

.risk-level-circle {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4px solid;
  transition: all var(--transition-base);
}

.risk-level-circle.risk-low {
  border-color: var(--success-primary);
  background: rgba(34, 197, 94, 0.1);
}

.risk-level-circle.risk-medium {
  border-color: var(--warning-primary);
  background: rgba(234, 179, 8, 0.1);
}

.risk-level-circle.risk-high {
  border-color: var(--danger-primary);
  background: rgba(239, 68, 68, 0.1);
}

.risk-level-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.risk-metrics {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.metric-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-primary);
}

.metric-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.metric-icon.stop-loss {
  background: rgba(239, 68, 68, 0.1);
}

.metric-icon.target {
  background: rgba(34, 197, 94, 0.1);
}

.metric-icon.position {
  background: rgba(0, 212, 255, 0.1);
}

.metric-icon .icon {
  width: 20px;
  height: 20px;
}

.metric-icon.stop-loss .icon {
  color: var(--danger-primary);
}

.metric-icon.target .icon {
  color: var(--success-primary);
}

.metric-icon.position .icon {
  color: var(--accent-primary);
}

.metric-content {
  flex: 1;
  min-width: 0;
}

.metric-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
  font-weight: 500;
}

.metric-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.metric-value.price-up {
  color: var(--success-primary);
}

.metric-value.price-down {
  color: var(--danger-primary);
}

.position-bar {
  width: 100%;
  height: 6px;
  background: var(--bg-secondary);
  border-radius: 3px;
  overflow: hidden;
}

.position-fill {
  height: 100%;
  background: var(--accent-primary);
  border-radius: 3px;
  transition: width var(--transition-base);
}

.risk-factors {
  padding: var(--spacing-lg);
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-secondary);
}

.factors-title {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 600;
  margin-bottom: var(--spacing-md);
}

.factors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-sm);
}

.factor-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-primary);
  transition: all var(--transition-base);
}

.factor-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.factor-index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--warning-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.factor-text {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
  flex: 1;
}

/* ========== 增强分析 ========== */
.enhanced-analysis {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.rule-analysis-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all var(--transition-base);
}

.rule-analysis-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-secondary);
}

.rule-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.rule-icon {
  font-size: 18px;
}

.rule-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.rule-content {
  padding: var(--spacing-md);
}

.rule-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.rule-metric {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.metric-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.metric-value.strength-strong {
  color: var(--success-color);
}

.metric-value.strength-moderate {
  color: var(--warning-color);
}

.metric-value.strength-weak {
  color: var(--text-secondary);
}

.rule-conditions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.condition-item, .status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
}

.condition-label, .status-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.macd-values {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.macd-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
}

.macd-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.macd-value {
  font-size: 14px;
  font-weight: 600;
  font-family: 'Monaco', 'Menlo', monospace;
}

.macd-value.positive {
  color: var(--success-color);
}

.macd-value.negative {
  color: var(--danger-color);
}

.macd-signals {
  padding: var(--spacing-sm);
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
}

.signal-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.signal-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.signal-value {
  font-size: 12px;
  color: var(--text-primary);
  font-weight: 500;
}

.score-breakdown {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: var(--spacing-sm);
}

.score-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
}

.score-label {
  font-size: 12px;
  color: var(--text-secondary);
  text-align: center;
}

/* ========== 分析摘要 ========== */
.summary-text {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary);
  margin: 0;
}

/* ========== 操作按钮 ========== */
.result-actions {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: center;
  padding: var(--spacing-md);
  border-top: 1px solid var(--border-primary);
  background: var(--bg-elevated);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
}

.btn-icon {
  width: 14px;
  height: 14px;
  margin-right: var(--spacing-xs);
}

/* ========== Element Plus 样式覆盖 ========== */
:deep(.el-tag) {
  border: none;
  font-weight: 500;
}

:deep(.el-progress-bar__outer) {
  background: var(--bg-elevated);
}

:deep(.el-button--small) {
  height: 24px;
  padding: 0 8px;
  font-size: 12px;
}

/* ========== 响应式设计 ========== */
/* 侧边栏状态适配 */
:deep(.sidebar.collapsed) ~ .main-content .chart-container {
  max-width: calc(100vw - 100px); /* 侧边栏收起时的宽度 */
}

:deep(.sidebar:not(.collapsed)) ~ .main-content .chart-container {
  max-width: calc(100vw - 320px); /* 侧边栏展开时的宽度 */
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .dow-analysis-panel {
    min-height: 500px; /* 中等屏幕减少最小高度 */
  }
  
  .chart-container {
    min-height: 400px;
  }
  
  .dow-theory-chart {
    min-height: 400px;
  }
}

@media (max-width: 768px) {
  .dow-analysis-panel {
    min-height: 400px; /* 移动端进一步减少最小高度 */
  }
  
  .chart-container {
    min-height: 350px;
    padding: var(--spacing-sm);
  }
  
  .dow-theory-chart {
    min-height: 300px;
  }
}
@media (max-width: 1200px) {
  .analysis-dashboard {
    flex-direction: column;
    gap: var(--spacing-lg);
    text-align: center;
  }
  
  .trend-indicators {
    grid-template-columns: 1fr;
  }
  
  .risk-level-display {
    flex-direction: column;
    text-align: center;
  }
}

@media (max-width: 768px) {
  .analysis-dashboard {
    padding: var(--spacing-md);
  }
  
  .trend-indicators {
    grid-template-columns: 1fr;
  }
  
  .indicator-card {
    padding: var(--spacing-sm);
  }
  
  .confidence-gauge :deep(.el-progress-circle) {
    width: 80px !important;
    height: 80px !important;
  }
  
  .card-icon {
    width: 32px;
    height: 32px;
  }
  
  .card-icon .icon {
    width: 18px;
    height: 18px;
  }
  
  .technical-grid {
    grid-template-columns: 1fr;
  }
  
  .risk-level-circle {
    width: 80px;
    height: 80px;
  }
  
  .risk-level-text {
    font-size: 14px;
  }
  
  .metric-icon {
    width: 36px;
    height: 36px;
  }
  
  .metric-icon .icon {
    width: 18px;
    height: 18px;
  }
  
  .factors-grid {
    grid-template-columns: 1fr;
  }
  
  .result-actions {
    flex-direction: column;
  }
  
  .dow-theory-chart {
    height: 300px;
  }
  
  .chart-container {
    padding: var(--spacing-sm);
    min-height: 300px;
  }
}

@media (max-width: 480px) {
  .dow-theory-chart {
    height: 250px;
  }
  
  .chart-container {
    padding: var(--spacing-sm);
    min-height: 250px;
  }
}

/* ========== 滚动条样式 ========== */
.panel-content::-webkit-scrollbar {
  width: 4px;
}

.panel-content::-webkit-scrollbar-track {
  background: var(--bg-elevated);
}

.panel-content::-webkit-scrollbar-thumb {
  background: var(--border-primary);
  border-radius: 2px;
}

.panel-content::-webkit-scrollbar-thumb:hover {
  background: var(--accent-primary);
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