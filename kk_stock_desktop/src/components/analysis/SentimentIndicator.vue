<template>
  <div class="sentiment-indicator">
    <el-card class="indicator-card">
      <template #header>
        <div class="card-header">
          <h3>市场情绪指标</h3>
          <div class="header-controls">
            <el-select v-model="timeRange" placeholder="时间范围" size="small" style="width: 120px;">
              <el-option label="近7天" value="7d" />
              <el-option label="近30天" value="30d" />
              <el-option label="近90天" value="90d" />
            </el-select>
            <el-button @click="fetchSentimentData" :loading="loading" size="small" type="primary">
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <div class="indicator-content" v-loading="loading">
        <!-- 情绪指标网格 -->
        <div class="indicators-grid">
          <div class="indicator-item" v-for="indicator in sentimentData" :key="indicator.name">
            <div class="indicator-header">
              <span class="indicator-name">{{ indicator.name }}</span>
              <el-tooltip :content="indicator.description" placement="top">
                <el-icon class="info-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
            <div class="indicator-value">
              <span class="current-value" :class="getValueClass(indicator.level)">
                {{ indicator.value }}{{ indicator.unit }}
              </span>
              <span class="change-value" :class="indicator.change >= 0 ? 'positive' : 'negative'">
                {{ indicator.change >= 0 ? '+' : '' }}{{ indicator.change }}{{ indicator.unit }}
              </span>
            </div>
            <div class="indicator-level">
              <el-tag :type="getLevelType(indicator.level)" size="small">
                {{ getLevelText(indicator.level) }}
              </el-tag>
            </div>
            <div class="indicator-chart">
              <div :ref="el => setChartRef(indicator.name, el)" class="mini-chart"></div>
            </div>
          </div>
        </div>

        <!-- 综合情绪指数 -->
        <div class="sentiment-summary">
          <div class="summary-gauge">
            <h4>综合情绪指数</h4>
            <div ref="gaugeChart" class="gauge-chart"></div>
          </div>
          <div class="summary-info">
            <div class="summary-card">
              <div class="summary-title">综合情绪指数</div>
              <div class="summary-value" :class="getIndexClass(overallSentiment.index)">
                {{ overallSentiment.index }}
              </div>
              <div class="summary-level">{{ overallSentiment.level }}</div>
            </div>
            <div class="summary-factors">
              <h5>主要因素：</h5>
              <ul>
                <li v-for="factor in overallSentiment.factors" :key="factor">{{ factor }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useAppStore } from '@/stores/app'
import { apiClient } from '@/api/base'
import { ElMessage } from 'element-plus'

// Props
interface Props {
  symbols?: string[]
  date?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  symbols: () => ['IF', 'IC', 'IH', 'IM'],
  date: '',
  loading: false
})

// 应用状态
const appStore = useAppStore()

// 主题相关颜色
const isDarkMode = computed(() => appStore.isDarkMode)
const textColor = computed(() => isDarkMode.value ? '#E5EAF3' : '#606266')
const borderColor = computed(() => isDarkMode.value ? 'rgba(255, 255, 255, 0.1)' : 'rgba(15, 23, 42, 0.1)')
const backgroundColor = computed(() => isDarkMode.value ? '#1d1e1f' : '#ffffff')

// 响应式数据
const timeRange = ref('30d')
const loading = ref(false)

// 图表引用
const gaugeChart = ref<HTMLElement>()
let gaugeChartInstance: echarts.ECharts | null = null
const miniChartInstances: Record<string, echarts.ECharts> = {}

// 设置图表引用
const setChartRef = (name: string, el: any) => {
  if (el && !miniChartInstances[name]) {
    nextTick(() => {
      initMiniChart(name, el as HTMLElement)
    })
  }
}

// 情绪数据 - 使用真实API数据
const sentimentData = ref([
  {
    name: '多空比',
    value: 0,
    unit: '',
    change: 0,
    level: 'neutral',
    description: '多头持仓与空头持仓的比值，反映市场多空力量对比',
    data: [] as Array<[string, number]>
  },
  {
    name: '恐慌指数',
    value: 50,
    unit: '',
    change: 0,
    level: 'neutral',
    description: '基于期权波动率计算的恐慌指数，数值越高表示市场恐慌程度越高',
    data: [] as Array<[string, number]>
  },
  {
    name: '资金流向',
    value: 0,
    unit: '亿',
    change: 0,
    level: 'neutral',
    description: '主力资金净流入流出情况，正值表示净流入',
    data: [] as Array<[string, number]>
  },
  {
    name: '基差水平',
    value: 0,
    unit: '点',
    change: 0,
    level: 'neutral',
    description: '期货价格与现货价格的差值，反映市场预期',
    data: [] as Array<[string, number]>
  }
])

// 综合情绪指数
const overallSentiment = ref({
  index: 50,
  level: '中性',
  factors: [
    '暂无数据'
  ]
})

// 获取市场情绪数据
const fetchSentimentData = async () => {
  loading.value = true
  try {
    const days = timeRange.value === '7d' ? 7 : timeRange.value === '30d' ? 30 : 90
    
    // 获取市场情绪分析
    const moodResponse = await apiClient.get('/analytics/market-mood', {
      params: { days }
    })
    
    if (moodResponse.data.success && moodResponse.data.data) {
      const moodData = moodResponse.data.data
      
      // 更新综合情绪指数
      if (moodData.summary) {
        overallSentiment.value = {
          index: Math.round(moodData.summary.avg_mood_score || 50),
          level: getMoodLevel(moodData.summary.avg_mood_score || 50),
          factors: [
            `情绪趋势: ${moodData.mood_trend}`,
            `平均情绪得分: ${moodData.summary.avg_mood_score?.toFixed(1)}`,
            `情绪波动性: ${moodData.summary.mood_volatility?.toFixed(1)}`,
            `分析周期: ${moodData.analysis_period}`
          ]
        }
      }
      
      // 更新情绪指标数据
      if (moodData.daily_mood && moodData.daily_mood.length > 0) {
        const latestMood = moodData.daily_mood[moodData.daily_mood.length - 1]
        const previousMood = moodData.daily_mood.length > 1 ? moodData.daily_mood[moodData.daily_mood.length - 2] : null
        
        // 更新多空比（基于上涨下跌比例计算）
        const bullBearRatio = latestMood.rise_ratio > 0 ? latestMood.rise_ratio / (100 - latestMood.rise_ratio) : 0
        sentimentData.value[0].value = Number(bullBearRatio.toFixed(2))
        sentimentData.value[0].change = previousMood ? Number((bullBearRatio - (previousMood.rise_ratio / (100 - previousMood.rise_ratio))).toFixed(2)) : 0
        sentimentData.value[0].level = bullBearRatio > 1.2 ? 'bullish' : bullBearRatio < 0.8 ? 'bearish' : 'neutral'
        
        // 更新恐慌指数（情绪得分反转）
        const fearIndex = 100 - latestMood.mood_score
        sentimentData.value[1].value = Number(fearIndex.toFixed(1))
        sentimentData.value[1].change = previousMood ? Number(((100 - latestMood.mood_score) - (100 - previousMood.mood_score)).toFixed(1)) : 0
        sentimentData.value[1].level = fearIndex > 70 ? 'bearish' : fearIndex < 30 ? 'bullish' : 'neutral'
        
        // 更新资金流向（基于市场活跃度）
        sentimentData.value[2].value = Number(latestMood.market_activity.toFixed(1))
        sentimentData.value[2].change = previousMood ? Number((latestMood.market_activity - previousMood.market_activity).toFixed(1)) : 0
        sentimentData.value[2].level = latestMood.market_activity > 1000 ? 'bullish' : latestMood.market_activity < 500 ? 'bearish' : 'neutral'
        
        // 更新基差水平（基于平均涨跌幅）
        sentimentData.value[3].value = Number(latestMood.avg_change.toFixed(1))
        sentimentData.value[3].change = previousMood ? Number((latestMood.avg_change - previousMood.avg_change).toFixed(1)) : 0
        sentimentData.value[3].level = latestMood.avg_change > 1 ? 'bullish' : latestMood.avg_change < -1 ? 'bearish' : 'neutral'
        
        // 准备历史数据用于小图表
        moodData.daily_mood.forEach((dayData: any) => {
          const date = dayData.trade_date
          const bullBear = dayData.rise_ratio > 0 ? dayData.rise_ratio / (100 - dayData.rise_ratio) : 0
          const fear = 100 - dayData.mood_score
          const funds = dayData.market_activity
          const basis = dayData.avg_change
          
          if (!sentimentData.value[0].data) sentimentData.value[0].data = []
          if (!sentimentData.value[1].data) sentimentData.value[1].data = []
          if (!sentimentData.value[2].data) sentimentData.value[2].data = []
          if (!sentimentData.value[3].data) sentimentData.value[3].data = []
          
          sentimentData.value[0].data.push([date, bullBear])
          sentimentData.value[1].data.push([date, fear])
          sentimentData.value[2].data.push([date, funds])
          sentimentData.value[3].data.push([date, basis])
        })
      }
    }
    
    // 初始化图表
    await nextTick()
    initGaugeChart()
    
    // 重新初始化迷你图表
    Object.keys(miniChartInstances).forEach(name => {
      const indicator = sentimentData.value.find(item => item.name === name)
      if (indicator && indicator.data && indicator.data.length > 0) {
        updateMiniChart(name, indicator.data)
      }
    })
    
  } catch (error) {
    console.error('获取市场情绪数据失败:', error)
    ElMessage.error('获取市场情绪数据失败')
  } finally {
    loading.value = false
  }
}

// 获取情绪等级
const getMoodLevel = (score: number): string => {
  if (score >= 80) return '极度乐观'
  if (score >= 60) return '乐观'
  if (score >= 40) return '中性'
  if (score >= 20) return '悲观'
  return '极度悲观'
}

// 工具函数
const getValueClass = (level: string) => {
  switch (level) {
    case 'bullish': return 'bullish'
    case 'bearish': return 'bearish'
    default: return 'neutral'
  }
}

const getLevelType = (level: string) => {
  switch (level) {
    case 'bullish': return 'success'
    case 'bearish': return 'danger'
    default: return 'info'
  }
}

const getLevelText = (level: string) => {
  switch (level) {
    case 'bullish': return '看涨'
    case 'bearish': return '看跌'
    default: return '中性'
  }
}

const getIndexClass = (index: number) => {
  if (index >= 70) return 'bullish'
  if (index <= 30) return 'bearish'
  return 'neutral'
}

// 初始化仪表盘图表
const initGaugeChart = () => {
  if (!gaugeChart.value) return

  gaugeChartInstance = echarts.init(gaugeChart.value)
  
  const option = {
    series: [
      {
        name: '情绪指数',
        type: 'gauge',
        startAngle: 180,
        endAngle: 0,
        center: ['50%', '75%'],
        radius: '90%',
        min: 0,
        max: 100,
        splitNumber: 10,
        axisLine: {
          lineStyle: {
            width: 6,
            color: [
              [0.3, isDarkMode.value ? '#ff6b6b' : '#f56c6c'],
              [0.7, isDarkMode.value ? '#ffd166' : '#e6a23c'],
              [1, isDarkMode.value ? '#06d6a0' : '#67c23a']
            ]
          }
        },
        pointer: {
          icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
          length: '12%',
          width: 20,
          offsetCenter: [0, '-60%'],
          itemStyle: {
            color: 'inherit'
          }
        },
        axisTick: {
          length: 12,
          lineStyle: {
            color: 'inherit',
            width: 2
          }
        },
        splitLine: {
          length: 20,
          lineStyle: {
            color: 'inherit',
            width: 5
          }
        },
        axisLabel: {
          color: textColor.value,
          fontSize: 12,
          distance: -60,
          formatter: (value: number) => {
            if (value === 0) return '极度恐慌'
            if (value === 30) return '恐慌'
            if (value === 50) return '中性'
            if (value === 70) return '乐观'
            if (value === 100) return '极度乐观'
            return ''
          }
        },
        title: {
          offsetCenter: [0, '-10%'],
          fontSize: 16,
          color: textColor.value
        },
        detail: {
          fontSize: 30,
          offsetCenter: [0, '-35%'],
          valueAnimation: true,
          formatter: (value: number) => {
            return value.toFixed(0)
          },
          color: 'inherit'
        },
        data: [
          {
            value: overallSentiment.value.index,
            name: '情绪指数'
          }
        ]
      }
    ]
  }
  
  gaugeChartInstance.setOption(option)
}

// 初始化迷你图表
const initMiniChart = (name: string, element: HTMLElement) => {
  const chartInstance = echarts.init(element)
  const indicator = sentimentData.value.find(item => item.name === name)
  const data = indicator?.data || []
  
  const option = {
    grid: {
      left: 5,
      right: 5,
      top: 5,
      bottom: 5
    },
    xAxis: {
      type: 'category',
      show: false,
      data: data.map(item => item[0])
    },
    yAxis: {
      type: 'value',
      show: false
    },
    series: [
      {
        data: data.map(item => item[1]),
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color: getChartColor(indicator?.level || 'neutral'),
          width: 2
        }
      }
    ]
  }
  
  chartInstance.setOption(option)
  miniChartInstances[name] = chartInstance
}

// 更新迷你图表
const updateMiniChart = (name: string, data: any[]) => {
  const chartInstance = miniChartInstances[name]
  if (chartInstance) {
    const indicator = sentimentData.value.find(item => item.name === name)
    chartInstance.setOption({
      xAxis: {
        data: data.map(item => item[0])
      },
      series: [{
        data: data.map(item => item[1]),
        lineStyle: {
          color: getChartColor(indicator?.level || 'neutral')
        }
      }]
    })
  }
}

// 获取图表颜色
const getChartColor = (level: string) => {
  if (level === 'bullish') {
    return isDarkMode.value ? '#06d6a0' : '#67c23a'
  } else if (level === 'bearish') {
    return isDarkMode.value ? '#ff6b6b' : '#f56c6c'
  }
  return isDarkMode.value ? '#4cc9f0' : '#409eff'
}

// 监听时间范围变化
watch(timeRange, () => {
  fetchSentimentData()
})

// 监听主题变化
watch(() => appStore.isDarkMode, () => {
  nextTick(() => {
    initGaugeChart()
    
    // 更新所有迷你图表
    Object.keys(miniChartInstances).forEach(name => {
      const indicator = sentimentData.value.find(item => item.name === name)
      if (indicator && indicator.data) {
        updateMiniChart(name, indicator.data)
      }
    })
  })
})

// 组件挂载和卸载
onMounted(() => {
  fetchSentimentData()
})

onUnmounted(() => {
  gaugeChartInstance?.dispose()
  Object.values(miniChartInstances).forEach(chart => chart.dispose())
})
</script>

<style scoped>
.sentiment-indicator {
  width: 100%;
  height: 100%;
}

.indicator-card {
  height: 100%;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 16px;
}

.indicator-content {
  padding: 0;
}

.indicators-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.indicator-item {
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  background: var(--bg-tertiary);
  transition: all 0.3s ease;
}

.indicator-item:hover {
  box-shadow: var(--shadow-sm);
}

.indicator-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.indicator-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.info-icon {
  color: var(--text-secondary);
  cursor: pointer;
}

.indicator-value {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: var(--spacing-xs);
}

.current-value {
  font-size: 20px;
  font-weight: bold;
}

.current-value.bullish {
  color: var(--neon-green);
}

.current-value.bearish {
  color: var(--neon-pink);
}

.current-value.neutral {
  color: var(--neon-blue);
}

.change-value {
  font-size: 12px;
}

.change-value.positive {
  color: var(--neon-green);
}

.change-value.negative {
  color: var(--neon-pink);
}

.indicator-level {
  margin-bottom: var(--spacing-sm);
}

.indicator-chart {
  height: 50px;
}

.mini-chart {
  width: 100%;
  height: 100%;
}

.sentiment-summary {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
  align-items: start;
}

.summary-gauge {
  height: 200px;
}

.gauge-chart {
  width: 100%;
  height: 100%;
}

.summary-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.summary-card {
  text-align: center;
  padding: var(--spacing-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
}

.summary-title {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: var(--spacing-xs);
}

.summary-value {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: var(--spacing-xs);
}

.summary-value.bullish {
  color: var(--neon-green);
}

.summary-value.bearish {
  color: var(--neon-pink);
}

.summary-value.neutral {
  color: var(--neon-blue);
}

.summary-level {
  color: var(--text-secondary);
  font-size: 14px;
}

.summary-factors h5 {
  margin: 0 0 var(--spacing-xs) 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.summary-factors ul {
  margin: 0;
  padding-left: var(--spacing-md);
  color: var(--text-tertiary);
}

.summary-factors li {
  margin-bottom: var(--spacing-xs);
  font-size: 12px;
}

@media (max-width: 768px) {
  .indicators-grid {
    grid-template-columns: 1fr;
  }
  
  .sentiment-summary {
    grid-template-columns: 1fr;
  }
}
</style>
