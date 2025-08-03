<template>
  <div class="market-margin-panel glass-effect">
    <!-- 面板标题 -->
    <div class="panel-header">
      <div class="panel-title">
        <PresentationChartLineIcon class="title-icon" />
        <span>两市融资融券分析</span>
        <el-tag v-if="currentPeriod" size="small" type="info">
          {{ currentPeriod }}
        </el-tag>
        <el-tag v-if="analysisResult" size="small" type="success">
          {{ analysisResult.data_count }}条数据
        </el-tag>
      </div>
      <div class="panel-actions">
        <el-select 
          v-model="selectedYears" 
          size="small" 
          style="width: 100px; margin-right: 8px;"
          @change="onPeriodChange"
        >
          <el-option label="1年" :value="1" />
          <el-option label="2年" :value="2" />
          <el-option label="3年" :value="3" />
          <el-option label="5年" :value="5" />
        </el-select>
        <el-button 
          size="small" 
          type="primary"
          :loading="analyzing"
          @click="triggerAnalysis"
        >
          <AdjustmentsHorizontalIcon class="action-icon" v-if="!analyzing" />
          {{ analyzing ? '分析中...' : '开始分析' }}
        </el-button>
      </div>
    </div>

    <!-- 面板内容 -->
    <div class="panel-content scrollable-content">
      <!-- 分析结果 -->
      <div v-if="analysisResult" class="analysis-result">
        <!-- 数据概览 -->
        <div class="result-section">
          <h4 class="section-title">
            <StarIcon class="title-icon" />
            数据概览
          </h4>
          <div class="data-overview">
            <div class="overview-item">
              <span class="overview-label">分析周期:</span>
              <span class="overview-value">{{ analysisResult.period }}</span>
            </div>
            <div class="overview-item">
              <span class="overview-label">数据量:</span>
              <span class="overview-value">{{ analysisResult.data_count }}条记录</span>
            </div>
            <div class="overview-item">
              <span class="overview-label">时间范围:</span>
              <span class="overview-value">{{ formatDate(analysisResult.start_date) }} ~ {{ formatDate(analysisResult.end_date) }}</span>
            </div>
          </div>
        </div>
        
        <!-- 市场概览 -->
        <div class="result-section">
          <h4 class="section-title">
            <StarIcon class="title-icon" />
            市场概览
          </h4>
          <div class="overview-grid">
            <div class="overview-card">
              <div class="card-header">
                <ArrowTrendingUpIcon class="card-icon financing" />
                <span class="card-title">融资余额</span>
              </div>
              <div class="card-content">
                <div class="value-main">{{ formatAmount(analysisResult.avg_rzye) }}</div>
                <div class="value-label">平均水平</div>
                <el-tag size="small" :type="getTrendType(analysisResult.rzye_trend)">
                  {{ getTrendText(analysisResult.rzye_trend) }}
                </el-tag>
              </div>
            </div>

            <div class="overview-card">
              <div class="card-header">
                <ArrowTrendingDownIcon class="card-icon securities" />
                <span class="card-title">融券余额</span>
              </div>
              <div class="card-content">
                <div class="value-main">{{ formatAmount(analysisResult.avg_rqye) }}</div>
                <div class="value-label">平均水平</div>
                <el-tag size="small" :type="getTrendType(analysisResult.rqye_trend)">
                  {{ getTrendText(analysisResult.rqye_trend) }}
                </el-tag>
              </div>
            </div>

            <div class="overview-card">
              <div class="card-header">
                <ChartBarIcon class="card-icon volume" />
                <span class="card-title">成交量</span>
              </div>
              <div class="card-content">
                <div class="value-main">{{ formatAmount(analysisResult.avg_total_volume) }}</div>
                <div class="value-label">平均水平</div>
                <el-tag size="small" :type="getTrendType(analysisResult.volume_trend)">
                  {{ getTrendText(analysisResult.volume_trend) }}
                </el-tag>
              </div>
            </div>

            <div class="overview-card">
              <div class="card-header">
                <HeartIcon class="card-icon sentiment" />
                <span class="card-title">市场情绪</span>
              </div>
              <div class="card-content">
                <div class="value-main">{{ getSentimentText(analysisResult.market_sentiment) }}</div>
                <div class="value-label">综合评估</div>
                <el-tag size="small" :type="getRiskType(analysisResult.risk_level)">
                  {{ getRiskText(analysisResult.risk_level) }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>

        <!-- 相关性分析 -->
        <div class="result-section">
          <h4 class="section-title">
            <ArrowsRightLeftIcon class="title-icon" />
            相关性分析
          </h4>
          <div class="correlation-grid">
            <div class="correlation-item">
              <div class="correlation-header">
                <span class="correlation-label">融资余额 vs 价格</span>
                <div class="correlation-value" :class="getCorrelationClass(analysisResult.correlation_analysis.rzye_price_corr)">
                  {{ analysisResult.correlation_analysis.rzye_price_corr.toFixed(3) }}
                </div>
              </div>
              <div class="correlation-bar">
                <div 
                  class="correlation-fill" 
                  :style="{ 
                    width: Math.abs(analysisResult.correlation_analysis.rzye_price_corr) * 100 + '%',
                    background: getCorrelationColor(analysisResult.correlation_analysis.rzye_price_corr)
                  }"
                ></div>
              </div>
            </div>

            <div class="correlation-item">
              <div class="correlation-header">
                <span class="correlation-label">融资余额 vs 成交量</span>
                <div class="correlation-value" :class="getCorrelationClass(analysisResult.correlation_analysis.rzye_volume_corr)">
                  {{ analysisResult.correlation_analysis.rzye_volume_corr.toFixed(3) }}
                </div>
              </div>
              <div class="correlation-bar">
                <div 
                  class="correlation-fill" 
                  :style="{ 
                    width: Math.abs(analysisResult.correlation_analysis.rzye_volume_corr) * 100 + '%',
                    background: getCorrelationColor(analysisResult.correlation_analysis.rzye_volume_corr)
                  }"
                ></div>
              </div>
            </div>

            <div class="correlation-item">
              <div class="correlation-header">
                <span class="correlation-label">融券余额 vs 价格</span>
                <div class="correlation-value" :class="getCorrelationClass(analysisResult.correlation_analysis.rqye_price_corr)">
                  {{ analysisResult.correlation_analysis.rqye_price_corr.toFixed(3) }}
                </div>
              </div>
              <div class="correlation-bar">
                <div 
                  class="correlation-fill" 
                  :style="{ 
                    width: Math.abs(analysisResult.correlation_analysis.rqye_price_corr) * 100 + '%',
                    background: getCorrelationColor(analysisResult.correlation_analysis.rqye_price_corr)
                  }"
                ></div>
              </div>
            </div>

            <div class="correlation-item">
              <div class="correlation-header">
                <span class="correlation-label">净流入 vs 价格</span>
                <div class="correlation-value" :class="getCorrelationClass(analysisResult.correlation_analysis.net_flow_price_corr)">
                  {{ analysisResult.correlation_analysis.net_flow_price_corr.toFixed(3) }}
                </div>
              </div>
              <div class="correlation-bar">
                <div 
                  class="correlation-fill" 
                  :style="{ 
                    width: Math.abs(analysisResult.correlation_analysis.net_flow_price_corr) * 100 + '%',
                    background: getCorrelationColor(analysisResult.correlation_analysis.net_flow_price_corr)
                  }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 趋势拟合图表 -->
        <div class="result-section">
          <h4 class="section-title">
            <ChartBarIcon class="title-icon" />
            趋势拟合分析
          </h4>
          <!-- 主要趋势图表 - 上下布局 -->
          <div class="main-charts">
            <div class="chart-container large">
              <div class="chart-header">
                <span class="chart-title">融资余额趋势拟合</span>
                <div class="chart-info">
                  <el-tag size="small" type="info">R² = {{ analysisResult.rzye_fitting.r_squared.toFixed(3) }}</el-tag>
                  <span class="chart-desc">{{ getRSquaredDesc(analysisResult.rzye_fitting.r_squared) }}</span>
                </div>
              </div>
              <div ref="rzyeChartContainer" class="chart-element large"></div>
              <div class="chart-analysis">
                <p>{{ getFittingAnalysis('融资余额', analysisResult.rzye_fitting, analysisResult.rzye_trend) }}</p>
              </div>
            </div>

            <div class="chart-container large">
              <div class="chart-header">
                <span class="chart-title">融券余额趋势拟合</span>
                <div class="chart-info">
                  <el-tag size="small" type="info">R² = {{ analysisResult.rqye_fitting.r_squared.toFixed(3) }}</el-tag>
                  <span class="chart-desc">{{ getRSquaredDesc(analysisResult.rqye_fitting.r_squared) }}</span>
                </div>
              </div>
              <div ref="rqyeChartContainer" class="chart-element large"></div>
              <div class="chart-analysis">
                <p>{{ getFittingAnalysis('融券余额', analysisResult.rqye_fitting, analysisResult.rqye_trend) }}</p>
              </div>
            </div>
          </div>

          <!-- 辅助图表 - 可折叠展示 -->
          <div class="auxiliary-charts">
            <el-collapse>
              <el-collapse-item title="查看价格与成交量拟合分析" name="auxiliary">
                <div class="charts-grid secondary">
                  <div class="chart-container">
                    <div class="chart-header">
                      <span class="chart-title">价格指数拟合</span>
                      <el-tag size="small" type="warning">模拟数据</el-tag>
                    </div>
                    <div ref="priceChartContainer" class="chart-element"></div>
                  </div>

                  <div class="chart-container">
                    <div class="chart-header">
                      <span class="chart-title">成交量拟合</span>
                      <el-tag size="small" type="warning">模拟数据</el-tag>
                    </div>
                    <div ref="volumeChartContainer" class="chart-element"></div>
                  </div>
                </div>
                <div class="auxiliary-note">
                  <p><strong>说明：</strong>价格和成交量数据为基于融资融券数据生成的模拟数据，仅用于演示相关性分析算法。在实际应用中，应接入真实的市场价格和成交量数据。</p>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>

        <!-- 关键洞察 -->
        <div class="result-section">
          <h4 class="section-title">
            <LightBulbIcon class="title-icon" />
            分析结论与投资洞察
          </h4>
          
          <!-- 核心结论 -->
          <div class="conclusion-summary">
            <div class="conclusion-item primary">
              <h5>市场情绪评估</h5>
              <p>{{ getMarketSentimentAnalysis(analysisResult.market_sentiment, analysisResult.risk_level) }}</p>
            </div>
            
            <div class="conclusion-item">
              <h5>融资融券趋势</h5>
              <p>{{ getMarginTrendAnalysis(analysisResult.rzye_trend, analysisResult.rqye_trend) }}</p>
            </div>
            
            <div class="conclusion-item">
              <h5>相关性发现</h5>
              <p>{{ getCorrelationInsights(analysisResult.correlation_analysis) }}</p>
            </div>
          </div>
          
          <!-- 详细洞察 -->
          <div class="insights-list">
            <div 
              v-for="(insight, index) in analysisResult.key_insights" 
              :key="index"
              class="insight-item"
            >
              <CheckCircleIcon class="insight-icon" />
              <span class="insight-text">{{ insight }}</span>
            </div>
          </div>
          
          <!-- 投资建议 -->
          <div class="investment-advice">
            <h5>投资参考建议</h5>
            <div class="advice-content">
              <p>{{ getInvestmentAdvice(analysisResult) }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 无数据状态 -->
      <div v-if="!analysisResult && !analyzing" class="empty-state">
        <div class="empty-content">
          <PresentationChartLineIcon class="empty-icon" />
          <h3>两市融资融券分析</h3>
          <p>点击"开始分析"查看两市整体融资融券数据的深度分析</p>
          <div class="empty-features">
            <div class="feature-item">
              <CheckCircleIcon class="feature-icon" />
              <span>价格走势相关性分析</span>
            </div>
            <div class="feature-item">
              <CheckCircleIcon class="feature-icon" />
              <span>成交量变化相关性分析</span>
            </div>
            <div class="feature-item">
              <CheckCircleIcon class="feature-icon" />
              <span>趋势拟合与预测</span>
            </div>
            <div class="feature-item">
              <CheckCircleIcon class="feature-icon" />
              <span>多时间段对比分析</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="analyzing" class="loading-state">
        <div class="loading-content">
          <div class="loading-spinner">
            <div class="spinner"></div>
          </div>
          <h3>正在分析两市融资融券数据...</h3>
          <p>正在处理{{ currentPeriod }}的市场数据，请稍候</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import {
  PresentationChartLineIcon,
  AdjustmentsHorizontalIcon,
  StarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChartBarIcon,
  HeartIcon,
  ArrowsRightLeftIcon,
  LightBulbIcon,
  CheckCircleIcon
} from '@heroicons/vue/24/outline'

import { apiClient } from '@/api/base'

// 响应式数据
const analyzing = ref(false)
const selectedYears = ref(1)
const analysisResult = ref<any>(null)
const currentPeriod = ref('')

// 图表容器引用
const rzyeChartContainer = ref<HTMLElement>()
const rqyeChartContainer = ref<HTMLElement>()
const priceChartContainer = ref<HTMLElement>()
const volumeChartContainer = ref<HTMLElement>()

// 图表实例
let rzyeChart: echarts.ECharts | null = null
let rqyeChart: echarts.ECharts | null = null
let priceChart: echarts.ECharts | null = null
let volumeChart: echarts.ECharts | null = null

// 方法
const triggerAnalysis = async () => {
  analyzing.value = true
  currentPeriod.value = `近${selectedYears.value}年`
  
  try {
    // console.log('发送API请求，参数:', { years: selectedYears.value })
    const response = await apiClient.get(`/api/market-margin/analysis`, { 
      years: selectedYears.value 
    })
    // console.log('API响应:', response)

    if (response.success && response.data) {
      analysisResult.value = response.data
      // console.log('两市融资融券分析结果:', response.data)  
      // console.log(`分析周期: ${response.data.period}, 数据量: ${response.data.data_count}条`)
      // console.log(`时间范围: ${response.data.start_date} ~ ${response.data.end_date}`)
      
      // 更新当前显示的周期信息
      currentPeriod.value = response.data.period || `近${selectedYears.value}年`
      
      // 创建图表
      await nextTick()
      createCharts()
      
      ElMessage.success(`${response.data.period}融资融券分析完成 (${response.data.data_count}条数据)`)
    } else {
      throw new Error(response.message || '分析数据格式错误')
    }
  } catch (error: any) {
    console.error('两市融资融券分析失败:', error)
    ElMessage.error(`分析失败: ${error?.message || '未知错误'}`)
  } finally {
    analyzing.value = false
  }
}

const onPeriodChange = () => {
  // console.log('时间范围改变:', selectedYears.value)
  // 清空之前的结果，确保数据更新
  analysisResult.value = null
  currentPeriod.value = `近${selectedYears.value}年`
  // 触发新的分析
  triggerAnalysis()
}

const createCharts = () => {
  if (!analysisResult.value) return

  // 销毁已存在的图表实例
  if (rzyeChart) {
    rzyeChart.dispose()
    rzyeChart = null
  }
  if (rqyeChart) {
    rqyeChart.dispose()
    rqyeChart = null
  }
  if (priceChart) {
    priceChart.dispose()
    priceChart = null
  }
  if (volumeChart) {
    volumeChart.dispose()
    volumeChart = null
  }

  // 创建融资余额趋势图
  createTrendChart(
    rzyeChartContainer.value,
    analysisResult.value.rzye_fitting,
    '融资余额',
    '#00d4ff',
    (chart) => { rzyeChart = chart }
  )

  // 创建融券余额趋势图
  createTrendChart(
    rqyeChartContainer.value,
    analysisResult.value.rqye_fitting,
    '融券余额',
    '#ff6b6b',
    (chart) => { rqyeChart = chart }
  )

  // 创建价格趋势图
  createTrendChart(
    priceChartContainer.value,
    analysisResult.value.price_fitting,
    '价格指数',
    '#ffa500',
    (chart) => { priceChart = chart }
  )

  // 创建成交量趋势图
  createTrendChart(
    volumeChartContainer.value,
    analysisResult.value.volume_fitting,
    '成交量',
    '#9d50bb',
    (chart) => { volumeChart = chart }
  )
}

const createTrendChart = (
  container: HTMLElement | undefined, 
  fittingData: any, 
  name: string, 
  color: string,
  onChart: (chart: echarts.ECharts) => void
) => {
  if (!container || !fittingData) return

  const chart = echarts.init(container)
  onChart(chart)

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: color,
      textStyle: { color: '#fff' }
    },
    legend: {
      data: ['实际数据', '拟合趋势'],
      textStyle: { color: '#fff' }
    },
    xAxis: {
      type: 'category',
      data: fittingData.data_points.map((_: any, index: number) => `第${index + 1}天`),
      axisLine: { lineStyle: { color: '#333' } },
      axisLabel: { color: '#999' }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#333' } },
      axisLabel: { 
        color: '#999',
        formatter: (value: number) => formatAmount(value)
      }
    },
    series: [
      {
        name: '实际数据',
        type: 'scatter',
        data: fittingData.data_points.map((point: any) => point.y),
        itemStyle: { color: color },
        symbolSize: 4
      },
      {
        name: '拟合趋势',
        type: 'line',
        data: fittingData.trend_line.map((point: any) => point.y),
        smooth: false,
        lineStyle: { color: color, width: 2 },
        itemStyle: { color: color }
      }
    ],
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      top: '15%'
    }
  }

  chart.setOption(option)
}

// 工具函数
const formatAmount = (amount: number | null | undefined): string => {
  if (amount == null) return 'N/A'
  
  const absAmount = Math.abs(amount)
  
  if (absAmount >= 1e12) {
    return (absAmount / 1e12).toFixed(2) + '万亿'
  } else if (absAmount >= 1e8) {
    return (absAmount / 1e8).toFixed(2) + '亿'
  } else if (absAmount >= 1e4) {
    return (absAmount / 1e4).toFixed(2) + '万'
  } else {
    return absAmount.toFixed(2)
  }
}

const getTrendType = (trend: string) => {
  switch (trend) {
    case 'increasing': return 'success'
    case 'decreasing': return 'danger'
    default: return 'info'
  }
}

const getTrendText = (trend: string) => {
  switch (trend) {
    case 'increasing': return '上升趋势'
    case 'decreasing': return '下降趋势'
    default: return '稳定'
  }
}

const getSentimentText = (sentiment: string) => {
  switch (sentiment) {
    case 'bullish': return '乐观'
    case 'bearish': return '谨慎'
    default: return '中性'
  }
}

const getRiskType = (risk: string) => {
  switch (risk) {
    case 'low': return 'success'
    case 'high': return 'danger'
    default: return 'warning'
  }
}

const getRiskText = (risk: string) => {
  switch (risk) {
    case 'low': return '低风险'
    case 'high': return '高风险'
    default: return '中等风险'
  }
}

const getCorrelationClass = (corr: number) => {
  const abs = Math.abs(corr)
  if (abs > 0.7) return 'correlation-strong'
  if (abs > 0.3) return 'correlation-moderate'
  return 'correlation-weak'
}

const getCorrelationColor = (corr: number) => {
  if (corr > 0.3) return 'linear-gradient(90deg, #67c23a, #85ce61)'
  if (corr < -0.3) return 'linear-gradient(90deg, #f56c6c, #f78989)'
  return 'linear-gradient(90deg, #909399, #a6a9ad)'
}

const formatDate = (dateStr: string): string => {
  if (!dateStr || dateStr.length !== 8) return dateStr
  return `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`
}

const getRSquaredDesc = (rSquared: number): string => {
  if (rSquared >= 0.8) return '拟合度极好'
  if (rSquared >= 0.6) return '拟合度良好'
  if (rSquared >= 0.4) return '拟合度一般'
  if (rSquared >= 0.2) return '拟合度较差'
  return '拟合度很差'
}

const getFittingAnalysis = (indicator: string, fitting: any, trend: string): string => {
  const rSquared = fitting.r_squared
  const slope = fitting.slope
  
  let analysis = `${indicator}在${currentPeriod.value}期间`
  
  // 趋势分析
  if (trend === 'increasing') {
    analysis += '呈现上升趋势'
  } else if (trend === 'decreasing') {
    analysis += '呈现下降趋势'
  } else {
    analysis += '保持相对稳定'
  }
  
  // 拟合质量分析
  if (rSquared >= 0.6) {
    analysis += '，趋势线拟合良好，变化规律明显'
  } else if (rSquared >= 0.3) {
    analysis += '，有一定的趋势性，但波动较大'
  } else {
    analysis += '，波动性较强，趋势不够明显'
  }
  
  // 斜率分析
  if (Math.abs(slope) > 1000000000) {
    analysis += '，变化幅度较大'
  } else if (Math.abs(slope) > 100000000) {
    analysis += '，变化幅度适中'
  } else {
    analysis += '，变化幅度较小'
  }
  
  // 投资含义
  if (indicator === '融资余额') {
    if (trend === 'increasing') {
      analysis += '。融资余额上升通常表明投资者看好后市，愿意加杠杆买入。'
    } else if (trend === 'decreasing') {
      analysis += '。融资余额下降可能表明投资者趋于谨慎，去杠杆操作增加。'
    }
  } else if (indicator === '融券余额') {
    if (trend === 'increasing') {
      analysis += '。融券余额上升表明看空情绪增强，投资者预期后市下跌。'
    } else if (trend === 'decreasing') {
      analysis += '。融券余额下降表明看空情绪减弱，市场情绪相对乐观。'
    }
  }
  
  return analysis
}

const getMarketSentimentAnalysis = (sentiment: string, riskLevel: string): string => {
  let analysis = '根据融资融券数据综合分析，当前市场情绪'
  
  switch (sentiment) {
    case 'bullish':
      analysis += '偏向乐观。投资者融资意愿较强，融券活动相对较少，显示出对后市的看好态度。'
      break
    case 'bearish':
      analysis += '偏向谨慎。融资活动减少或融券增加，投资者对后市持相对悲观态度。'
      break
    default:
      analysis += '相对中性。融资融券活动保持平衡，投资者观望情绪较重。'
  }
  
  switch (riskLevel) {
    case 'high':
      analysis += '当前风险等级较高，建议密切关注市场变化。'
      break
    case 'medium':
      analysis += '风险等级适中，投资时需要适当控制仓位。'
      break
    default:
      analysis += '风险等级相对较低，市场环境相对稳定。'
  }
  
  return analysis
}

const getMarginTrendAnalysis = (rzTrend: string, rqTrend: string): string => {
  let analysis = `${currentPeriod.value}期间，`
  
  if (rzTrend === 'increasing' && rqTrend === 'decreasing') {
    analysis += '融资余额上升而融券余额下降，这是典型的看多信号。投资者加大融资买入力度，同时融券做空减少，表明市场整体偏向乐观。'
  } else if (rzTrend === 'decreasing' && rqTrend === 'increasing') {
    analysis += '融资余额下降而融券余额上升，显示市场情绪转向谨慎。投资者减少融资买入，增加融券做空，对后市持相对悲观态度。'
  } else if (rzTrend === 'increasing' && rqTrend === 'increasing') {
    analysis += '融资融券余额同时上升，表明市场分歧加大。既有看多资金进入，也有看空力量增强，需要关注哪种力量占主导。'
  } else if (rzTrend === 'decreasing' && rqTrend === 'decreasing') {
    analysis += '融资融券余额同时下降，市场活跃度降低。投资者整体趋于谨慎，观望情绪浓厚。'
  } else {
    analysis += '融资融券余额保持相对稳定，市场情绪平静，缺乏明确的方向性信号。'
  }
  
  return analysis
}

const getCorrelationInsights = (correlation: any): string => {
  let insights = []
  
  if (Math.abs(correlation.rzye_price_corr) > 0.5) {
    insights.push(`融资余额与价格${correlation.rzye_price_corr > 0 ? '正' : '负'}相关性较强(${correlation.rzye_price_corr.toFixed(2)})`)
  }
  
  if (Math.abs(correlation.rqye_price_corr) > 0.3) {
    insights.push(`融券余额与价格${correlation.rqye_price_corr > 0 ? '正' : '负'}相关性明显(${correlation.rqye_price_corr.toFixed(2)})`)
  }
  
  if (Math.abs(correlation.net_flow_price_corr) > 0.4) {
    insights.push(`融资净流入与价格${correlation.net_flow_price_corr > 0 ? '正' : '负'}相关(${correlation.net_flow_price_corr.toFixed(2)})`)
  }
  
  if (insights.length === 0) {
    return '融资融券数据与价格/成交量的相关性不够明显，可能受到多种因素影响，需要结合其他指标综合分析。'
  }
  
  return insights.join('；') + '。这些相关性为我们理解市场资金流向与价格变动的关系提供了重要参考。'
}

const getInvestmentAdvice = (result: any): string => {
  let advice = '基于两市融资融券数据分析，'
  
  const sentiment = result.market_sentiment
  const riskLevel = result.risk_level
  const rzTrend = result.rzye_trend
  const rqTrend = result.rqye_trend
  
  if (sentiment === 'bullish' && riskLevel === 'low') {
    advice += '建议：可以适当增加仓位。融资情绪乐观且风险较低，有利于股价上涨。但仍需关注个股基本面，避免盲目追高。'
  } else if (sentiment === 'bearish' && riskLevel === 'high') {
    advice += '建议：应当谨慎操作，控制仓位。市场情绪偏向悲观且风险较高，建议等待更好的入场时机。'
  } else if (sentiment === 'neutral') {
    advice += '建议：保持观望，均衡配置。市场情绪中性，适合采取稳健的投资策略，避免激进操作。'
  } else {
    advice += '建议：密切关注市场变化，根据实际情况调整策略。当前市场信号复杂，需要综合多方面因素做出投资决策。'
  }
  
  advice += '\n\n⚠️ 风险提示：融资融券数据仅为市场情绪的参考指标之一，投资决策应结合基本面分析、技术分析等多维度信息，并充分考虑自身风险承受能力。'
  
  return advice
}

// 组件销毁时清理图表
onMounted(() => {
  return () => {
    if (rzyeChart) rzyeChart.dispose()
    if (rqyeChart) rqyeChart.dispose()
    if (priceChart) priceChart.dispose()
    if (volumeChart) volumeChart.dispose()
  }
})
</script>

<style scoped>
.market-margin-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  background: var(--bg-secondary);
  overflow: hidden;
}

/* ========== 面板标题 ========== */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-primary);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.01));
  backdrop-filter: blur(10px);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.title-icon {
  width: 20px;
  height: 20px;
  color: var(--accent-primary);
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.action-icon {
  width: 14px;
  height: 14px;
}

/* ========== 面板内容 ========== */
.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
}

.scrollable-content {
  max-height: calc(100vh - 200px);
}

/* ========== 结果区域 ========== */
.result-section {
  margin-bottom: var(--spacing-xl);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-md) 0;
}

/* ========== 数据概览 ========== */
.data-overview {
  display: flex;
  gap: var(--spacing-lg);
  padding: var(--spacing-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.02);
  margin-bottom: var(--spacing-md);
}

.overview-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.overview-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.overview-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--accent-primary);
}

/* ========== 概览网格 ========== */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.overview-card {
  padding: var(--spacing-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.02);
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.card-icon {
  width: 18px;
  height: 18px;
}

.card-icon.financing { color: #00d4ff; }
.card-icon.securities { color: #ff6b6b; }
.card-icon.volume { color: #ffa500; }
.card-icon.sentiment { color: #9d50bb; }

.card-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.value-main {
  font-size: 18px;
  font-weight: 700;
  color: var(--accent-primary);
}

.value-label {
  font-size: 12px;
  color: var(--text-secondary);
}

/* ========== 相关性分析 ========== */
.correlation-grid {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.correlation-item {
  padding: var(--spacing-sm);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.01);
}

.correlation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
}

.correlation-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.correlation-value {
  font-size: 14px;
  font-weight: 600;
}

.correlation-value.correlation-strong { color: #67c23a; }
.correlation-value.correlation-moderate { color: #e6a23c; }
.correlation-value.correlation-weak { color: #909399; }

.correlation-bar {
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.correlation-fill {
  height: 100%;
  transition: width 0.3s ease;
}

/* ========== 主要图表 ========== */
.main-charts {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
}

.chart-container.large {
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.01);
  overflow: hidden;
}

.chart-element.large {
  width: 100%;
  height: 400px;
}

.chart-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.chart-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

.chart-analysis {
  padding: var(--spacing-md);
  background: rgba(255, 255, 255, 0.02);
  border-top: 1px solid var(--border-primary);
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* ========== 辅助图表 ========== */
.auxiliary-charts {
  margin-top: var(--spacing-lg);
}

.charts-grid.secondary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.auxiliary-note {
  padding: var(--spacing-md);
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.2);
  border-radius: var(--radius-md);
  font-size: 12px;
  color: var(--text-secondary);
}

/* ========== 图表网格 ========== */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-md);
}

.chart-container {
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.01);
  overflow: hidden;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm);
  border-bottom: 1px solid var(--border-primary);
  background: rgba(255, 255, 255, 0.02);
}

.chart-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
}

.chart-element {
  width: 100%;
  height: 200px;
}

/* ========== 结论分析 ========== */
.conclusion-summary {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.conclusion-item {
  padding: var(--spacing-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.02);
}

.conclusion-item.primary {
  border-color: var(--accent-primary);
  background: rgba(0, 212, 255, 0.05);
}

.conclusion-item h5 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-sm) 0;
}

.conclusion-item p {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

.investment-advice {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-lg);
  border: 2px solid var(--accent-primary);
  border-radius: var(--radius-lg);
  background: rgba(0, 212, 255, 0.05);
}

.investment-advice h5 {
  font-size: 16px;
  font-weight: 600;
  color: var(--accent-primary);
  margin: 0 0 var(--spacing-md) 0;
}

.advice-content p {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.7;
  margin: 0;
  white-space: pre-line;
}

/* ========== 洞察列表 ========== */
.insights-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin: var(--spacing-lg) 0;
}

.insight-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.01);
}

.insight-icon {
  width: 16px;
  height: 16px;
  color: var(--accent-primary);
  flex-shrink: 0;
  margin-top: 2px;
}

.insight-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.4;
}

/* ========== 空状态 ========== */
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.empty-content {
  text-align: center;
  max-width: 400px;
}

.empty-icon {
  width: 80px;
  height: 80px;
  color: var(--text-tertiary);
  margin: 0 auto var(--spacing-lg);
}

.empty-content h3 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-md) 0;
}

.empty-content p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 var(--spacing-lg) 0;
  line-height: 1.6;
}

.empty-features {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  align-items: flex-start;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 14px;
  color: var(--text-secondary);
}

.feature-icon {
  width: 16px;
  height: 16px;
  color: var(--accent-primary);
}

/* ========== 加载状态 ========== */
.loading-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.loading-content {
  text-align: center;
  max-width: 300px;
}

.loading-spinner {
  margin: 0 auto var(--spacing-lg);
}

.spinner {
  width: 60px;
  height: 60px;
  border: 4px solid rgba(0, 212, 255, 0.1);
  border-left: 4px solid var(--accent-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-content h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-sm) 0;
}

.loading-content p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

/* ========== 响应式设计 ========== */
@media (max-width: 768px) {
  .data-overview {
    flex-direction: column;
    gap: var(--spacing-sm);
  }
  
  .overview-grid {
    grid-template-columns: 1fr;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .charts-grid.secondary {
    grid-template-columns: 1fr;
  }
  
  .chart-element {
    height: 180px;
  }
  
  .chart-element.large {
    height: 300px;
  }
  
  .conclusion-summary {
    gap: var(--spacing-sm);
  }
  
  .investment-advice {
    padding: var(--spacing-md);
  }
}
</style>