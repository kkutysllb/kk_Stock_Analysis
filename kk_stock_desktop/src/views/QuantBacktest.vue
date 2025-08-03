<template>
  <div class="backtest-container">
    <!-- 页面标题横幅 -->
    <div class="page-banner glass-effect glow-effect">
      <div class="banner-content">
        <div class="banner-left">
          <h1 class="page-title text-gradient">
            <ChartBarIcon class="icon-size"></ChartBarIcon>
            太上老君量化回测
          </h1>
          <p class="page-subtitle">配置策略参数，运行历史回测，分析策略表现</p>
          <p class="page-description">通过历史数据验证策略有效性，优化投资决策</p>
        </div>
        <div class="banner-right">
          <div class="feature-highlights">
            <div class="highlight-item">
              <div class="highlight-icon">
                <CogIcon class="icon-size" />
              </div>
              <div class="highlight-info">
                <div class="highlight-label">策略配置</div>
                <div class="highlight-value">专业</div>
              </div>
            </div>
            <div class="highlight-item">
              <div class="highlight-icon">
                <ClockIcon class="icon-size" />
              </div>
              <div class="highlight-info">
                <div class="highlight-label">回测速度</div>
                <div class="highlight-value">高效</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 回测配置面板 -->
    <div class="config-section">
      <el-card class="config-card">
        <template #header>
          <div class="card-header">
            <h3>
              <CogIcon class="header-icon"></CogIcon>
              回测配置
            </h3>
          </div>
        </template>
        
        <el-form :model="backtestConfig" :rules="configRules" ref="configFormRef" label-width="120px">
          <!-- 基础配置区域 -->
          <div class="config-section-wrapper">
            <div class="section-title">
              <DocumentTextIcon class="section-icon"></DocumentTextIcon>
              基础设置
            </div>
            <el-row :gutter="24">
              <el-col :span="8">
                <el-form-item label="策略类型" prop="strategy_type">
                  <el-select v-model="backtestConfig.strategy_type" placeholder="选择策略" style="width: 100%">
                    <el-option
                      v-for="strategy in strategies"
                      :key="strategy.name"
                      :label="strategy.label"
                      :value="strategy.name"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="初始资金" prop="initial_cash">
                  <el-input-number
                    v-model="backtestConfig.initial_cash"
                    :min="10000"
                    :max="100000000"
                    :step="10000"
                    placeholder="初始资金"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="基准指数" prop="benchmark">
                  <el-select v-model="backtestConfig.benchmark" placeholder="选择基准" style="width: 100%">
                    <el-option label="上证指数" value="000001.SH" />
                    <el-option label="沪深300" value="000300.SH" />
                    <el-option label="中证500" value="000905.SH" />
                    <el-option label="中证1000" value="000852.SH" />
                    <el-option label="创业板指" value="399006.SZ" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="开始日期" prop="start_date">
                  <el-date-picker
                    v-model="backtestConfig.start_date"
                    type="date"
                    placeholder="选择开始日期"
                    style="width: 100%"
                    value-format="YYYY-MM-DD"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="12">
                <el-form-item label="结束日期" prop="end_date">
                  <el-date-picker
                    v-model="backtestConfig.end_date"
                    type="date"
                    placeholder="选择结束日期"
                    style="width: 100%"
                    value-format="YYYY-MM-DD"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
          
          <!-- 交易成本配置区域 -->
          <div class="config-section-wrapper">
            <div class="section-title">
              <CurrencyDollarIcon class="section-icon"></CurrencyDollarIcon>
              交易成本设置
            </div>
            <el-row :gutter="24">
              <el-col :span="8">
                <el-form-item label="手续费率" prop="commission_rate">
                  <el-input-number
                    v-model="backtestConfig.commission_rate"
                    :min="0.00001"
                    :max="0.01"
                    :step="0.00001"
                    :precision="5"
                    placeholder="万一"
                    style="width: 100%"
                  />
                  <div class="form-help-text">万分之一（双向收费）</div>
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="印花税率" prop="stamp_tax_rate">
                  <el-input-number
                    v-model="backtestConfig.stamp_tax_rate"
                    :min="0.0001"
                    :max="0.01"
                    :step="0.0001"
                    :precision="4"
                    placeholder="千一"
                    style="width: 100%"
                  />
                  <div class="form-help-text">千分之一（仅卖出收取）</div>
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="滑点率" prop="slippage_rate">
                  <el-input-number
                    v-model="backtestConfig.slippage_rate"
                    :min="0.0001"
                    :max="0.01"
                    :step="0.0001"
                    :precision="4"
                    placeholder="千一"
                    style="width: 100%"
                  />
                  <div class="form-help-text">千分之一（价格冲击成本）</div>
                </el-form-item>
              </el-col>
            </el-row>
          </div>
          
          <!-- 操作按钮区域 -->
          <div class="action-section">
            <el-button 
              type="primary" 
              size="large"
              @click="startBacktest" 
              :loading="isRunning"
              :disabled="!canStartBacktest"
              class="start-button"
            >
              {{ isRunning ? '回测中...' : '开始回测' }}
            </el-button>
          </div>
        </el-form>
      </el-card>
    </div>

    <!-- 概要面板 -->
    <div v-if="shouldShowOverview" class="overview-section">
      <el-card class="overview-card">
        <template #header>
          <div class="card-header">
            <h3>
              <PresentationChartLineIcon class="header-icon"></PresentationChartLineIcon>
              概要
            </h3>
            <div v-if="currentTask" class="task-status">
              <el-tag :type="getTaskStatusType(currentTask.status)">
                {{ getTaskStatusText(currentTask.status) }}
              </el-tag>
            </div>
          </div>
        </template>
        
        <div class="metrics-grid">
          <div class="metric-card highlight">
            <div class="metric-value" :class="{ positive: displayMetrics.totalReturn > 0, negative: displayMetrics.totalReturn < 0 }">
              {{ formatPercent(displayMetrics.totalReturn) }}%
            </div>
            <div class="metric-label">累计收益率</div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value">{{ formatPercent(displayMetrics.annualReturn) }}%</div>
            <div class="metric-label">年化收益率</div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value">{{ formatPercent(displayMetrics.benchmarkReturn) }}%</div>
            <div class="metric-label">基准收益率</div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value">{{ displayMetrics.sharpeRatio?.toFixed(2) || '0.00' }}</div>
            <div class="metric-label">夏普比率</div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value">{{ displayMetrics.beta?.toFixed(2) || '0.00' }}</div>
            <div class="metric-label">贝塔</div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value">{{ formatPercent(displayMetrics.alpha) }}%</div>
            <div class="metric-label">阿尔法</div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value">{{ formatPercent(displayMetrics.winRate) }}%</div>
            <div class="metric-label">胜率</div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value">{{ displayMetrics.profit2Loss?.toFixed(2) || '0.00' }}</div>
            <div class="metric-label">盈亏比</div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value">{{ formatPercent(displayMetrics.volatility) }}%</div>
            <div class="metric-label">收益波动率</div>
          </div>
          
          <div class="metric-card negative">
            <div class="metric-value">{{ formatPercent(displayMetrics.maxDrawdown) }}%</div>
            <div class="metric-label">最大回撤</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 策略收益率对比图表 -->
    <div v-if="shouldShowChart" class="chart-section">
      <el-card class="chart-card">
        <template #header>
          <div class="card-header">
            <h3>
              <ChartBarIcon class="header-icon"></ChartBarIcon>
              策略收益率对比
            </h3>
            <div class="chart-controls">
              <span class="benchmark-info">基准指数: {{ getBenchmarkName(backtestConfig.benchmark) }}</span>
            </div>
          </div>
        </template>
        
        <div class="chart-legend">
          <span class="legend-item strategy">
            <span class="legend-color"></span>
            策略收益率 {{ formatPercent(displayMetrics.totalReturn) }}%
          </span>
          <span class="legend-item benchmark">
            <span class="legend-color"></span>
            基准收益率 {{ formatPercent(displayMetrics.benchmarkReturn) }}%
          </span>
          <span class="legend-item drawdown">
            <span class="legend-color"></span>
            最大回撤 -{{ formatPercent(displayMetrics.maxDrawdown) }}%
          </span>
        </div>
        
        <div ref="chartRef" class="chart-area" style="height: 400px;"></div>
      </el-card>
    </div>

    <!-- 持仓信息面板 -->
    <div v-if="positions.length > 0" class="positions-section">
      <el-card class="positions-card">
        <template #header>
          <div class="card-header">
            <h3>
              <BriefcaseIcon class="header-icon"></BriefcaseIcon>
              当前持仓
            </h3>
            <div class="positions-summary">
              持仓数量: {{ positions.length }} | 总市值: {{ formatCurrency(totalPositionValue) }}
            </div>
          </div>
        </template>
        
        <BacktestPositions :positions="positions" />
      </el-card>
    </div>

    <!-- 交易记录面板 -->
    <div v-if="trades.length > 0" class="trades-section">
      <el-card class="trades-card">
        <template #header>
          <div class="card-header">
            <h3>
              <ClipboardDocumentListIcon class="header-icon"></ClipboardDocumentListIcon>
              交易记录
            </h3>
            <div class="trades-summary">
              总交易次数: {{ trades.length }}
            </div>
          </div>
        </template>
        
        <BacktestTrades :trades="trades" />
      </el-card>
    </div>

    <!-- 详细分析结果 -->
    <div v-if="shouldShowDetailedResults" class="detailed-results-section">
      <BacktestDetailedResults 
        :backtest-result="backtestResult"
        :positions="positions"
        :trades="trades"
        :markdown-report="markdownReport"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage, ElCard, ElForm, ElFormItem, ElRow, ElCol, ElSelect, ElOption, ElInputNumber, ElDatePicker, ElButton, ElTag } from 'element-plus'
import { backtestApi } from '../api/backtest'
import {
  ChartBarIcon,
  CogIcon,
  ClockIcon,
  DocumentTextIcon,
  CurrencyDollarIcon,
  PresentationChartLineIcon,
  BriefcaseIcon,
  ClipboardDocumentListIcon
} from '@heroicons/vue/24/outline'
import type { BacktestConfig, BacktestTask, BacktestResult, BacktestDisplayMetrics, Position, Trade } from '../types/backtest'
import BacktestPositions from '../components/backtest/BacktestPositions.vue'
import BacktestTrades from '../components/backtest/BacktestTrades.vue'
import BacktestDetailedResults from '../components/backtest/BacktestDetailedResults.vue'
import * as echarts from 'echarts'

// 响应式数据
const configFormRef = ref()
const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.EChartsType | null = null

// 回测配置
const backtestConfig = reactive<BacktestConfig>({
  strategy_name: '太上老君1号策略',
  strategy_type: 'multi_trend',
  initial_cash: 1000000,
  start_date: '2024-01-01',
  end_date: '2024-12-31',
  benchmark: '000300.SH',
  // 交易成本配置 - 使用A股市场的合理默认值
  commission_rate: 0.0001,  // 万一手续费
  stamp_tax_rate: 0.001,    // 千一印花税（仅卖出）
  slippage_rate: 0.001      // 千一滑点
})

// 表单验证规则
const configRules = {
  strategy_type: [{ required: true, message: '请选择策略类型', trigger: 'change' }],
  initial_cash: [{ required: true, message: '请输入初始资金', trigger: 'blur' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }],
  benchmark: [{ required: true, message: '请选择基准指数', trigger: 'change' }],
  commission_rate: [
    { required: true, message: '请输入手续费率', trigger: 'blur' },
    { validator: (rule: any, value: number, callback: any) => {
        if (value < 0.00001 || value > 0.01) {
          callback(new Error('手续费率范围：0.00001-0.01'))
        } else {
          callback()
        }
      }, trigger: 'blur' }
  ],
  stamp_tax_rate: [
    { required: true, message: '请输入印花税率', trigger: 'blur' },
    { validator: (rule: any, value: number, callback: any) => {
        if (value < 0.0001 || value > 0.01) {
          callback(new Error('印花税率范围：0.0001-0.01'))
        } else {
          callback()
        }
      }, trigger: 'blur' }
  ],
  slippage_rate: [
    { required: true, message: '请输入滑点率', trigger: 'blur' },
    { validator: (rule: any, value: number, callback: any) => {
        if (value < 0.0001 || value > 0.01) {
          callback(new Error('滑点率范围：0.0001-0.01'))
        } else {
          callback()
        }
      }, trigger: 'blur' }
  ]
}

// 状态数据
const isRunning = ref(false)
const currentTask = ref<BacktestTask | null>(null)
const backtestResult = ref<BacktestResult | null>(null)
const markdownReport = ref('')
const positions = ref<Position[]>([])
const trades = ref<Trade[]>([])
const 
strategies = ref([
  { name: 'multi_trend', label: '太上老君1号策略', description: '基于多时间周期技术分析' },
  { name: 'boll', label: '太上老君2号策略', description: '基于布林带指标的策略' },
  { name: 'taishang_3factor', label: '太上老君3号策略', description: '基于三因子模型的策略' }
])

// 轮询管理
let pollingTimer: number | null = null
const pollingInterval = 2000 // 2秒轮询间隔

// 计算属性
const canStartBacktest = computed(() => {
  return backtestConfig.strategy_type &&
         backtestConfig.initial_cash > 0 &&
         backtestConfig.start_date &&
         backtestConfig.end_date &&
         !isRunning.value &&
         new Date(backtestConfig.start_date) < new Date(backtestConfig.end_date)
})

const shouldShowOverview = computed(() => {
  return backtestConfig.benchmark || backtestResult.value
})

const shouldShowChart = computed(() => {
  return backtestResult.value?.chart_data?.portfolio_value
})

const shouldShowDetailedResults = computed(() => {
  return backtestResult.value && 
         (backtestResult.value.chart_data || positions.value.length > 0 || trades.value.length > 0 || markdownReport.value)
})

const totalPositionValue = computed(() => {
  return positions.value.reduce((sum, pos) => sum + pos.market_value, 0)
})

const displayMetrics = computed<BacktestDisplayMetrics>(() => {
  if (backtestResult.value) {
    const basic = backtestResult.value.performance_report.basic_metrics
    const advanced = backtestResult.value.performance_report.advanced_metrics
    const portfolio = backtestResult.value.portfolio_summary
    
    // 获取基准数据
    const benchmarkData = (backtestResult.value as any).benchmark_data
    const benchmarkReturn = benchmarkData?.final_return ? benchmarkData.final_return * 100 : 0
    
    // 简单的beta和alpha计算
    const strategyReturn = portfolio.cumulative_return
    const benchmarkReturnDecimal = benchmarkData?.final_return || 0
    const beta = benchmarkReturnDecimal !== 0 ? strategyReturn / benchmarkReturnDecimal : 0
    const alpha = (basic.annual_return - benchmarkReturnDecimal) * 100
    
    return {
      totalReturn: portfolio.cumulative_return * 100,
      annualReturn: basic.annual_return * 100,
      benchmarkReturn: benchmarkReturn,
      sharpeRatio: basic.sharpe_ratio,
      beta: beta,
      alpha: alpha,
      maxDrawdown: Math.abs(basic.max_drawdown) * 100,
      winRate: portfolio.win_rate * 100,
      totalTrades: portfolio.total_trades,
      calmarRatio: basic.calmar_ratio,
      sortinoRatio: advanced.sortino_ratio,
      volatility: basic.volatility * 100,
      profit2Loss: advanced.avg_win_loss_ratio
    }
  }
  
  return {
    totalReturn: 0,
    annualReturn: 0,
    benchmarkReturn: 0,
    sharpeRatio: 0,
    beta: 0,
    alpha: 0,
    maxDrawdown: 0,
    winRate: 0,
    totalTrades: 0,
    calmarRatio: 0,
    sortinoRatio: 0,
    volatility: 0,
    profit2Loss: 0
  }
})

// 方法
const startBacktest = async () => {
  if (!canStartBacktest.value) return
  
  try {
    await configFormRef.value?.validate()
    
    isRunning.value = true
    
    // 调试：打印传递给后端的配置
    // console.log('🔍 前端传递的配置:', {
    //   strategy_name: backtestConfig.strategy_name,
    //   strategy_type: backtestConfig.strategy_type
    // })
    
    const response = await backtestApi.startBacktest(backtestConfig)
    if (response.success) {
      currentTask.value = {
        task_id: response.data?.task_id || '',
        status: 'pending',
        progress: 0,
        created_at: new Date().toISOString(),
        user_id: 'current_user',
        config: { ...backtestConfig }
      }
      
      ElMessage.success('回测任务已启动')
      if (response.data?.task_id) {
        startPolling(response.data.task_id)
      }
    } else {
      throw new Error(response.message || '启动回测失败')
    }
  } catch (error) {
    console.error('启动回测失败:', error)
    ElMessage.error(error instanceof Error ? error.message : '启动回测失败')
    isRunning.value = false
  }
}

const startPolling = (taskId: string) => {
  // console.log('🔄 开始轮询任务状态:', taskId)
  
  const pollTaskStatus = async () => {
    try {
      const response = await backtestApi.getTask(taskId)
      if (response.success && response.data) {
        currentTask.value = response.data
        
        // 检查任务状态
        if (response.data.status === 'completed') {
          // console.log('✅ 回测任务完成')
          isRunning.value = false
          stopPolling()
          await loadBacktestResults(taskId)
          ElMessage.success('回测完成')
        } else if (response.data.status === 'failed') {
          // console.log('❌ 回测任务失败')
          isRunning.value = false
          stopPolling()
          ElMessage.error(`回测失败: ${response.data.error_message || '未知错误'}`)
        } else if (response.data.status === 'running') {
          // console.log(`🔄 回测进行中: ${(response.data.progress * 100).toFixed(1)}%`)
        }
      }
    } catch (error) {
      console.error('轮询任务状态失败:', error)
    }
  }
  
  // 立即执行一次
  pollTaskStatus()
  
  // 设置定时轮询
  pollingTimer = window.setInterval(pollTaskStatus, pollingInterval)
}

const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
    // console.log('🛑 停止轮询')
  }
}


const loadBacktestResults = async (taskId: string) => {
  try {
    // 获取回测结果
    const resultResponse = await backtestApi.getResult(taskId)
    if (resultResponse.success && resultResponse.data) {
      backtestResult.value = resultResponse.data
      await nextTick()
      renderChart()
    }
    
    // 获取持仓数据
    try {
      // console.log('📊 正在获取持仓数据...', 'taskId:', taskId)
      const positionsResponse = await backtestApi.getPositions(taskId)
      // console.log('📊 持仓数据API响应:', positionsResponse)
      
      if (positionsResponse.success && positionsResponse.data) {
        // 后端返回的是 {portfolio_history: [], total: 0} 格式
        positions.value = positionsResponse.data.portfolio_history || []
        // console.log('📊 成功加载持仓数据:', positions.value.length, '条')
      }
    } catch (error) {
      console.warn('获取持仓数据失败:', error)
    }
    
    // 获取交易记录
    try {
      // console.log('📊 正在获取交易记录...', 'taskId:', taskId)
      // console.log('📊 预期的API URL:', `/backtest/result/${taskId}/trades`)
      const tradesResponse = await backtestApi.getTrades(taskId)
      // console.log('📊 交易记录API响应:', tradesResponse)
      // console.log('📊 API响应详情:', {
      //   success: tradesResponse.success,
      //   dataType: typeof tradesResponse.data,
      //   data: tradesResponse.data,
      //   tradesLength: tradesResponse.data?.trades?.length,
      //   total: tradesResponse.data?.total
      // })
      
      if (tradesResponse.success && tradesResponse.data) {
        trades.value = tradesResponse.data.trades || []
        // console.log('📊 成功加载交易记录:', trades.value.length, '条，总数:', tradesResponse.data.total)
      } else {
        console.warn('📊 交易记录API响应异常:', tradesResponse)  
      }
    } catch (error) {
      console.warn('获取交易记录失败:', error)
    }
    
    // 获取Markdown报告
    try {
      const markdownResponse = await backtestApi.getMarkdownReport(taskId)
      if (markdownResponse.success && markdownResponse.data) {
        markdownReport.value = markdownResponse.data.content
      }
    } catch (error) {
      console.warn('获取Markdown报告失败:', error)
    }
  } catch (error) {
    console.error('加载回测结果失败:', error)
    ElMessage.error('加载回测结果失败')
  }
}

// 计算最大回撤区间
const calculateMaxDrawdownPeriod = (returns: number[], dates: string[]) => {
  if (!returns || returns.length === 0) return '无数据'
  
  let maxDrawdown = 0
  let peakIndex = 0
  let troughIndex = 0
  let currentPeak = returns[0]
  let currentPeakIndex = 0
  
  for (let i = 1; i < returns.length; i++) {
    if (returns[i] > currentPeak) {
      currentPeak = returns[i]
      currentPeakIndex = i
    }
    
    const drawdown = currentPeak - returns[i]
    if (drawdown > maxDrawdown) {
      maxDrawdown = drawdown
      peakIndex = currentPeakIndex
      troughIndex = i
    }
  }
  
  if (maxDrawdown === 0) return '无回撤'
  
  return `${dates[peakIndex]} 至 ${dates[troughIndex]}`
}

const renderChart = () => {
  if (!chartRef.value || !backtestResult.value?.chart_data?.portfolio_value) {
    // console.log('📊 renderChart: 缺少必要数据或DOM元素')
    return
  }
  
  // console.log('📊 开始渲染图表...', {
  //   有基准数据: !!backtestResult.value.benchmark_data,
  //   基准代码: backtestResult.value.benchmark_data?.benchmark_code,
  //   配置的基准: backtestConfig.benchmark
  // })
  
  try {
    if (chartInstance) {
      chartInstance.dispose()
    }
    
    chartInstance = echarts.init(chartRef.value)
    
    const chartData = backtestResult.value.chart_data.portfolio_value.data
    const dates = chartData.dates
    // 策略收益率数据已经是百分比格式，无需转换
    const portfolioReturns = chartData.cumulative_returns
    
    // 获取基准收益率数据
    const benchmarkData = (backtestResult.value as any).benchmark_data
    let benchmarkReturns = new Array(dates.length).fill(0)
    
    if (benchmarkData?.cumulative_returns) {
      // 基准收益率数据是小数格式，需要转换为百分比
      benchmarkReturns = benchmarkData.cumulative_returns.map((r: number) => r * 100)
      
      // 如果基准数据长度不匹配，进行填充或截断
      if (benchmarkReturns.length !== dates.length) {
        if (benchmarkReturns.length < dates.length) {
          // 用最后一个值填充
          const lastValue = benchmarkReturns[benchmarkReturns.length - 1] || 0
          while (benchmarkReturns.length < dates.length) {
            benchmarkReturns.push(lastValue)
          }
        } else {
          // 截断到匹配长度
          benchmarkReturns = benchmarkReturns.slice(0, dates.length)
        }
      }
    }
    
    // 计算相对收益率（策略收益率 - 基准收益率）
    const relativeReturns = portfolioReturns.map((strategy, index) => {
      const benchmark = benchmarkReturns[index] || 0
      return strategy - benchmark
    })
    
    // 检测当前主题
    const isDarkMode = document.documentElement.classList.contains('dark') || 
                      document.body.classList.contains('dark') ||
                      window.getComputedStyle(document.body).backgroundColor.includes('rgb(0, 0, 0)') ||
                      window.getComputedStyle(document.body).backgroundColor.includes('rgb(26, 26, 26)')
    
    // 主题颜色配置
    const themeColors = {
      textColor: isDarkMode ? '#e4e7ed' : '#303133',
      axisLineColor: isDarkMode ? '#4c4d4f' : '#d0d3d6',
      splitLineColor: isDarkMode ? '#363739' : '#e4e7ed',
      tooltipBg: isDarkMode ? 'rgba(48, 49, 51, 0.95)' : 'rgba(255, 255, 255, 0.95)',
      tooltipBorder: isDarkMode ? '#4c4d4f' : '#e4e7ed',
      tooltipText: isDarkMode ? '#e4e7ed' : '#303133'
    }
    
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        },
        backgroundColor: themeColors.tooltipBg,
        borderColor: themeColors.tooltipBorder,
        borderWidth: 1,
        textStyle: {
          color: themeColors.tooltipText,
          fontSize: 12
        },
        formatter: function(params: any) {
          const date = params[0].axisValue
          const strategyValue = params[0]?.value || 0
          const benchmarkValue = params[1]?.value || 0
          const relativeValue = params[2]?.value || 0
          
          // 计算最大回撤区间
          const drawdownPeriod = calculateMaxDrawdownPeriod(portfolioReturns, dates)
          
          return `
            <div style="padding: 8px; font-size: 13px; line-height: 1.6;">
              <div style="font-weight: bold; margin-bottom: 8px; color: ${themeColors.tooltipText};">${date}</div>
              
              <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <span style="display: inline-block; width: 8px; height: 8px; background: #00d4aa; border-radius: 50%; margin-right: 6px;"></span>
                <span style="color: ${themeColors.tooltipText};">策略收益率</span>
              </div>
              <div style="margin-left: 14px; margin-bottom: 8px; font-size: 16px; font-weight: bold; color: #00d4aa;">
                ${strategyValue.toFixed(2)}%
              </div>
              
              <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <span style="display: inline-block; width: 8px; height: 8px; background: #409eff; border-radius: 50%; margin-right: 6px;"></span>
                <span style="color: ${themeColors.tooltipText};">相对收益率</span>
              </div>
              <div style="margin-left: 14px; margin-bottom: 8px; font-size: 16px; font-weight: bold; color: ${relativeValue >= 0 ? '#00d4aa' : '#f56c6c'};">
                ${relativeValue.toFixed(2)}%
              </div>
              
              <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <span style="display: inline-block; width: 8px; height: 8px; background: #ff9800; border-radius: 50%; margin-right: 6px;"></span>
                <span style="color: ${themeColors.tooltipText};">基准指数</span>
              </div>
              <div style="margin-left: 14px; margin-bottom: 8px; font-size: 16px; font-weight: bold; color: #ff9800;">
                ${benchmarkValue.toFixed(2)}%
              </div>
              
              <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <span style="display: inline-block; width: 8px; height: 8px; background: #f56c6c; border-radius: 50%; margin-right: 6px;"></span>
                <span style="color: ${themeColors.tooltipText};">最大回撤区间</span>
              </div>
              <div style="margin-left: 14px; font-size: 12px; color: ${isDarkMode ? '#909399' : '#606266'};">
                ${drawdownPeriod}
              </div>
            </div>
          `
        }
      },
      legend: {
        data: ['策略收益率', '基准收益率', '相对收益率'],
        textStyle: {
          color: themeColors.textColor
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      },
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: 0,
          filterMode: 'none',
          start: 0,
          end: 100
        },
        {
          type: 'slider',
          xAxisIndex: 0,
          filterMode: 'none',
          start: 0,
          end: 100,
          bottom: '5%'
        }
      ],
      xAxis: {
        type: 'category',
        data: dates,
        boundaryGap: false,
        axisLabel: {
          color: themeColors.textColor
        },
        axisLine: {
          lineStyle: {
            color: themeColors.axisLineColor
          }
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: '{value}%',
          color: themeColors.textColor
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: themeColors.splitLineColor
          }
        },
        axisLine: {
          show: true,
          lineStyle: {
            color: themeColors.axisLineColor
          }
        }
      },
      series: [
        {
          name: '策略收益率',
          type: 'line',
          data: portfolioReturns,
          smooth: true,
          symbol: 'none',
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [{
                offset: 0, color: 'rgba(0, 212, 170, 0.6)'
              }, {
                offset: 1, color: 'rgba(0, 212, 170, 0.1)'
              }]
            }
          },
          lineStyle: {
            color: '#00d4aa',
            width: 2
          }
        },
        {
          name: '基准收益率',
          type: 'line',
          data: benchmarkReturns,
          smooth: true,
          symbol: 'none',
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [{
                offset: 0, color: 'rgba(255, 152, 0, 0.4)'
              }, {
                offset: 1, color: 'rgba(255, 152, 0, 0.1)'
              }]
            }
          },
          lineStyle: {
            color: '#ff9800',
            width: 2
          }
        },
        {
          name: '相对收益率',
          type: 'line',
          data: relativeReturns,
          smooth: true,
          symbol: 'none',
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [{
                offset: 0, color: 'rgba(64, 158, 255, 0.4)'
              }, {
                offset: 1, color: 'rgba(64, 158, 255, 0.1)'
              }]
            }
          },
          lineStyle: {
            color: '#409eff',
            width: 2
          }
        }
      ]
    }
    
    chartInstance.setOption(option)
  } catch (error) {
    console.error('渲染图表失败:', error)
  }
}

// 工具函数
const formatPercent = (value: number) => {
  return isFinite(value) ? value.toFixed(2) : '0.00'
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(value)
}

const getTaskStatusType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'running': return 'warning'
    default: return 'info'
  }
}

const getTaskStatusText = (status: string) => {
  switch (status) {
    case 'pending': return '等待中'
    case 'running': return '运行中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    default: return '未知'
  }
}

const getBenchmarkName = (benchmarkCode: string) => {
  const benchmarkMap: Record<string, string> = {
    '000001.SH': '上证指数',
    '000300.SH': '沪深300',
    '000905.SH': '中证500',
    '000852.SH': '中证1000',
    '399006.SZ': '创业板指'
  }
  return benchmarkMap[benchmarkCode] || benchmarkCode
}

// 生命周期
onMounted(() => {
  // 初始化
})

onUnmounted(() => {
  stopPolling()
  if (chartInstance) {
    chartInstance.dispose()
  }
})

// 监听策略类型变化，更新策略名称
watch(() => backtestConfig.strategy_type, (newStrategyType) => {
  const strategy = strategies.value.find(s => s.name === newStrategyType)
  if (strategy) {
    backtestConfig.strategy_name = strategy.label
  }
}, { immediate: true })

// 监听回测结果变化，自动更新图表
watch(backtestResult, (newResult) => {
  if (newResult && newResult.chart_data?.portfolio_value) {
    nextTick(() => {
      renderChart()
    })
  }
}, { deep: true })
</script>

<style scoped>
.backtest-container {
  padding: 24px;
  width: 100%;
  max-width: none;
  margin: 0;
  min-height: 100vh;
  box-sizing: border-box;
  background: var(--el-bg-color-page);
}

/* 页面横幅样式 */
.page-banner {
  margin-bottom: 32px;
  padding: 32px;
  border-radius: 16px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: var(--el-box-shadow-light);
}

.banner-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  flex-wrap: wrap;
}

.banner-left {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  flex-wrap: nowrap;
}

.page-subtitle {
  font-size: 16px;
  font-weight: 500;
  color: var(--el-text-color-regular);
  margin: 0 0 8px 0;
}

.page-description {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin: 0;
  line-height: 1.5;
}

.banner-right {
  flex-shrink: 0;
  min-width: 280px;
}

.feature-highlights {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.highlight-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  min-width: 110px;
  flex: 1;
}

.highlight-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #79bbff, #409eff);
  border-radius: 8px;
  color: white;
  flex-shrink: 0;
}

.highlight-info {
  flex: 1;
}

.highlight-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.highlight-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

/* 图标样式 */
.icon-size {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.header-icon {
  width: 16px;
  height: 16px;
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.section-icon {
  width: 16px;
  height: 16px;
  margin-right: 6px;
  color: var(--el-color-primary);
}

/* 横幅响应式样式 */
@media (max-width: 1200px) {
  .banner-content {
    flex-direction: column;
    align-items: stretch;
    gap: 20px;
  }
  
  .banner-right {
    min-width: auto;
  }
  
  .feature-highlights {
    justify-content: flex-start;
  }
  
  .page-title {
    font-size: 22px;
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 20px;
    gap: 6px;
  }
  
  .icon-size {
    width: 18px;
    height: 18px;
  }
  
  .banner-content {
    gap: 16px;
  }
  
  .feature-highlights {
    flex-direction: column;
    gap: 12px;
  }
  
  .highlight-item {
    min-width: auto;
  }
  
  .card-header h3 {
    font-size: 14px;
    gap: 6px;
  }
  
  .header-icon {
    width: 14px;
    height: 14px;
  }
}

@media (max-width: 480px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .card-header h3 {
    font-size: 14px;
    gap: 4px;
  }
}

.config-section,
.overview-section,
.chart-section,
.positions-section,
.trades-section,
.report-section {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
  flex-wrap: nowrap;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 20px;
  
  /* 响应式设计 */
  @media (max-width: 1400px) {
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 16px;
  }
  
  @media (max-width: 1200px) {
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 14px;
  }
  
  @media (max-width: 900px) {
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }
  
  @media (max-width: 600px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
}

.metric-card {
  text-align: center;
  padding: 20px 16px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  background: var(--el-bg-color-page);
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
  
  /* 响应式字体调整 */
  @media (max-width: 900px) {
    padding: 16px 12px;
  }
  
  @media (max-width: 600px) {
    padding: 14px 10px;
  }
}

.metric-card.highlight {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.metric-card.negative {
  border-color: var(--el-color-danger);
  background: var(--el-color-danger-light-9);
}

.metric-value {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 6px;
  line-height: 1.2;
  
  /* 响应式字体大小 */
  @media (max-width: 1200px) {
    font-size: 20px;
  }
  
  @media (max-width: 900px) {
    font-size: 18px;
    margin-bottom: 4px;
  }
  
  @media (max-width: 600px) {
    font-size: 16px;
    margin-bottom: 3px;
  }
}

.metric-value.positive {
  color: var(--el-color-success);
}

.metric-value.negative {
  color: var(--el-color-danger);
}

.metric-label {
  font-size: 13px;
  color: var(--el-text-color-regular);
  font-weight: 500;
  line-height: 1.3;
  
  /* 响应式字体大小 */
  @media (max-width: 900px) {
    font-size: 12px;
  }
  
  @media (max-width: 600px) {
    font-size: 11px;
  }
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.benchmark-info {
  font-size: 14px;
  color: var(--el-text-color-regular);
  background: var(--el-color-info-light-9);
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid var(--el-color-info-light-7);
  
  @media (max-width: 600px) {
    font-size: 13px;
    padding: 3px 10px;
  }
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  
  /* 响应式设计 */
  @media (max-width: 900px) {
    gap: 16px;
    padding: 10px;
    flex-wrap: wrap;
  }
  
  @media (max-width: 600px) {
    gap: 12px;
    padding: 8px;
  }
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  white-space: nowrap;
  
  /* 响应式字体大小 */
  @media (max-width: 900px) {
    font-size: 13px;
    gap: 5px;
  }
  
  @media (max-width: 600px) {
    font-size: 12px;
    gap: 4px;
  }
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
  
  /* 响应式大小调整 */
  @media (max-width: 600px) {
    width: 10px;
    height: 10px;
  }
}

.legend-item.strategy .legend-color {
  background: #00d4aa;
}

.legend-item.benchmark .legend-color {
  background: #909399;
}

.legend-item.drawdown .legend-color {
  background: #f56c6c;
}

.chart-area {
  border-radius: 6px;
}

.positions-summary,
.trades-summary {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.markdown-container {
  max-height: 600px;
  overflow-y: auto;
}

.markdown-content {
  line-height: 1.6;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3 {
  color: var(--el-text-color-primary);
  margin-top: 24px;
  margin-bottom: 12px;
}

.markdown-content h1:first-child,
.markdown-content h2:first-child,
.markdown-content h3:first-child {
  margin-top: 0;
}

.markdown-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
}

.markdown-content th,
.markdown-content td {
  border: 1px solid var(--el-border-color);
  padding: 8px 12px;
  text-align: left;
}

.markdown-content th {
  background: var(--el-bg-color-page);
  font-weight: 600;
}

/* 全局响应式优化 */
@media (max-width: 1600px) {
  .backtest-container {
    padding: 16px 18px;
  }
}

@media (max-width: 1200px) {
  .backtest-container {
    padding: 14px 16px;
  }
  
  .page-title {
    font-size: 22px;
  }
  
  .chart-area {
    height: 350px !important;
  }
}

@media (max-width: 900px) {
  .backtest-container {
    padding: 12px 14px;
  }
  
  .page-title {
    font-size: 20px;
  }
  
  .page-header {
    margin-bottom: 20px;
  }
  
  .config-section,
  .overview-section,
  .chart-section,
  .positions-section,
  .trades-section,
  .report-section {
    margin-bottom: 20px;
  }
  
  .chart-area {
    height: 320px !important;
  }
}

@media (max-width: 600px) {
  .backtest-container {
    padding: 10px 12px;
  }
  
  .page-title {
    font-size: 18px;
  }
  
  .page-header {
    margin-bottom: 16px;
  }
  
  .config-section,
  .overview-section,
  .chart-section,
  .positions-section,
  .trades-section,
  .report-section {
    margin-bottom: 16px;
  }
  
  .chart-area {
    height: 280px !important;
  }
  
  .card-header h3 {
    font-size: 15px;
  }
}

/* 卡片容器的响应式优化 */
.el-card {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  
  /* 在小屏幕上减少内边距 */
  @media (max-width: 600px) {
    .el-card__body {
      padding: 16px !important;
    }
    
    .el-card__header {
      padding: 14px 16px !important;
    }
  }
}

/* 表单控件的响应式优化 */
@media (max-width: 900px) {
  .el-form-item {
    margin-bottom: 16px;
  }
  
  .el-form-item__label {
    font-size: 13px;
  }
}

@media (max-width: 600px) {
  .el-form-item {
    margin-bottom: 14px;
  }
  
  .el-form-item__label {
    font-size: 12px;
    width: 100px !important;
  }
}

/* 配置区域分组样式 */
.config-section-wrapper {
  margin-bottom: 32px;
  position: relative;
}

.config-section-wrapper:last-of-type {
  margin-bottom: 24px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 16px;
  padding: 8px 0 8px 12px;
  border-left: 3px solid var(--el-color-primary);
  background: linear-gradient(90deg, 
    var(--el-color-primary-light-9) 0%, 
    transparent 100%);
  border-radius: 4px;
  display: flex;
  align-items: center;
}

/* 操作按钮区域样式 */
.action-section {
  text-align: center;
  padding: 24px 0 8px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.start-button {
  min-width: 200px;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  transition: all 0.3s ease;
}

.start-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
}

.start-button:disabled {
  box-shadow: none;
}

/* 表单帮助文本样式 */
.form-help-text {
  font-size: 11px;
  color: var(--el-text-color-regular);
  margin-top: 4px;
  line-height: 1.2;
  opacity: 0.75;
  font-weight: 400;
}

/* 表单项样式优化 */
.el-form-item {
  margin-bottom: 20px;
}

.el-form-item__label {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

/* 响应式优化 */
@media (max-width: 768px) {
  .config-section-wrapper {
    margin-bottom: 24px;
  }
  
  .section-title {
    font-size: 13px;
    margin-bottom: 12px;
    padding: 6px 0 6px 10px;
  }
  
  .action-section {
    padding: 20px 0 8px;
  }
  
  .start-button {
    min-width: 160px;
    height: 44px;
    font-size: 15px;
  }
  
  .form-help-text {
    font-size: 10px;
    margin-top: 2px;
  }
}

@media (max-width: 600px) {
  .config-section-wrapper {
    margin-bottom: 20px;
  }
  
  .section-title {
    font-size: 12px;
    margin-bottom: 10px;
    padding: 5px 0 5px 8px;
  }
  
  .start-button {
    width: 100%;
    min-width: unset;
  }
}
</style>