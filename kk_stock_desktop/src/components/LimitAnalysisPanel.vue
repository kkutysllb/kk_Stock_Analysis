<template>
  <div class="limit-analysis-panel">
    <div class="panel-header">
      <div class="panel-title-section">
        <h3 class="panel-title">
          <ArrowTrendingUpIcon class="title-icon" />
          每日涨停板块分析
        </h3>
        <AskAIComponent :data-context="aiDataContext" />
      </div>
      
      <div class="panel-controls">
        <el-radio-group v-model="activeTab" @change="onTabChange" size="default">
          <el-radio-button value="overview">概览</el-radio-button>
          <el-radio-button value="ladder">连板天梯</el-radio-button>
          <el-radio-button value="concept">概念轮动</el-radio-button>
          <el-radio-button value="trend">趋势分析</el-radio-button>
        </el-radio-group>
        
        <div class="date-control">
          <el-date-picker
            v-model="selectedDate"
            type="date"
            placeholder="选择日期"
            size="default"
            format="YYYY-MM-DD"
            value-format="YYYYMMDD"
            class="date-picker"
            clearable
            @change="onDateChange"
          />
        </div>
      </div>
    </div>

    <div class="panel-body">
      <div v-if="loading" class="loading-container">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span class="loading-text">加载中...</span>
      </div>
      
      <div v-else-if="error" class="error-container">
        <el-icon class="error-icon"><Warning /></el-icon>
        <span class="error-text">{{ error }}</span>
        <el-button @click="loadAllData" type="primary" size="small" class="retry-button">
          重试
        </el-button>
      </div>
      
      <div v-else class="panel-content">
        <!-- 概览面板 -->
        <div v-if="activeTab === 'overview'" class="overview-panel">
          <div class="summary-section">
            <div class="section-title">涨停概况</div>
            <div class="summary-grid">
              <div class="summary-card limit-up">
                <div class="card-icon">
                  <i class="icon-arrow-up"></i>
                </div>
                <div class="card-content">
                  <div class="card-value">{{ limitStats.up_limit_count || 0 }}</div>
                  <div class="card-label">涨停股票</div>
                </div>
              </div>
              
              <div class="summary-card limit-down">
                <div class="card-icon">
                  <i class="icon-arrow-down"></i>
                </div>
                <div class="card-content">
                  <div class="card-value">{{ limitStats.down_limit_count || 0 }}</div>
                  <div class="card-label">跌停股票</div>
                </div>
              </div>
              
              <div class="summary-card avg-ratio">
                <div class="card-icon">
                  <i class="icon-bar-chart"></i>
                </div>
                <div class="card-content">
                  <div class="card-value">{{ formatAmount(limitStats.up_limit_stats?.avg_fd_amount) }}</div>
                  <div class="card-label">平均封单额</div>
                </div>
              </div>
              
              <div class="summary-card market-mood">
                <div class="card-icon">
                  <i class="icon-heart"></i>
                </div>
                <div class="card-content">
                  <div class="card-value">{{ getMoodLevel() }}</div>
                  <div class="card-label">市场情绪</div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="charts-section">
            <div class="chart-container">
              <div class="section-title">涨停股票分布</div>
              <div ref="limitDistributionChart" class="chart-content"></div>
            </div>
          </div>
        </div>

      <!-- 连板天梯 -->
      <div v-if="activeTab === 'ladder'" class="ladder-section">
        <div class="ladder-stats">
          <div class="ladder-header">
            <h3>连板天梯统计</h3>
            <div class="ladder-summary">
              总计 {{ getTotalStepStocks() }} 只连板股
            </div>
          </div>
          <div class="ladder-chart">
            <div ref="stepChart" class="chart-content"></div>
          </div>
        </div>

        <!-- 连板股票列表 -->
        <div class="step-stocks-list">
          <div class="list-header">
            <h4>连板股票详情</h4>
          </div>
          <div class="step-groups">
            <div
              v-for="group in stepStats"
              :key="group._id"
              class="step-group"
            >
              <div class="group-header">
                <span class="step-badge">{{ group._id }}连板</span>
                <span class="stock-count">{{ group.count }}只</span>
              </div>
              <div class="stock-tags">
                <el-tag
                  v-for="stock in group.stocks"
                  :key="stock.ts_code"
                  :type="getStepTagType(group._id)"
                  size="small"
                  class="stock-tag"
                >
                  {{ stock.name }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 概念轮动 -->
      <div v-if="activeTab === 'concept'" class="concept-section">
        <div class="concept-ranking">
          <div class="ranking-header">
            <h3>强势概念板块</h3>
            <div class="ranking-date">{{ formatDate(selectedDate) }}</div>
          </div>
          <div class="concept-list">
            <div
              v-for="(concept, index) in conceptList"
              :key="concept.name"
              class="concept-item"
              :class="{ 'top-concept': index < 3 }"
            >
              <div class="concept-rank">{{ concept.rank }}</div>
              <div class="concept-info">
                <div class="concept-name">{{ concept.name }}</div>
                <div class="concept-stats">
                  <span class="up-count">{{ concept.up_nums }}只上涨</span>
                  <span class="change-rate" :class="getChangeClass(concept.pct_chg)">
                    {{ formatPercent(concept.pct_chg) }}
                  </span>
                </div>
              </div>
              <div class="concept-status">
                <el-tag :type="getStatusTagType(concept.up_stat)" size="small">
                  {{ concept.up_stat }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>

        <!-- 概念轮动趋势图 -->
        <div class="concept-trend">
          <div class="trend-header">
            <h3>概念轮动趋势</h3>
            <el-select v-model="trendDays" size="small" @change="loadConceptTrend">
              <el-option label="7天" :value="7" />
              <el-option label="15天" :value="15" />
              <el-option label="30天" :value="30" />
            </el-select>
          </div>
          <div ref="conceptTrendChart" class="chart-content"></div>
        </div>
      </div>

      <!-- 趋势分析 -->
      <div v-if="activeTab === 'trend'" class="trend-section">
        <div class="trend-analysis">
          <div class="analysis-header">
            <h3>涨停趋势分析</h3>
            <el-select v-model="analysisDays" size="small" @change="loadTrendAnalysis">
              <el-option label="7天" :value="7" />
              <el-option label="15天" :value="15" />
              <el-option label="30天" :value="30" />
            </el-select>
          </div>
          <div ref="trendAnalysisChart" class="chart-content"></div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { limitDataAPI } from '@/api/limitData'
import AskAIComponent from '@/components/AskAIComponent.vue'
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChartBarIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon
} from '@heroicons/vue/24/outline'
import { Loading, Warning } from '@element-plus/icons-vue'

export default {
  name: 'LimitAnalysisPanel',
  components: {
      AskAIComponent,
      ArrowTrendingUpIcon,
      ArrowTrendingDownIcon,
      ChartBarIcon,
      ArrowPathIcon,
      ExclamationTriangleIcon,
      Loading,
      Warning
    },
  setup() {
    // 响应式数据
    const loading = ref(false)
    const error = ref('')
    const selectedDate = ref(new Date().toISOString().slice(0, 10).replace(/-/g, ''))
    const activeTab = ref('overview')
    const trendDays = ref(7)
    const analysisDays = ref(7)

    // 数据状态 - 使用ref替代reactive以避免深层响应式问题
    const limitStats = ref({
      up_limit_count: 0,
      down_limit_count: 0,
      up_limit_stats: {
        avg_fc_ratio: null
      },
      down_limit_stats: {
        avg_fc_ratio: null
      }
    })
    const limitList = ref([])
    const stepStats = ref([])
    const conceptList = ref([])
    const conceptTrend = ref([])
    const trendAnalysis = ref([])

    // 图表实例
    const limitDistributionChart = ref(null)
    const stepChart = ref(null)
    const conceptTrendChart = ref(null)
    const trendAnalysisChart = ref(null)

    // 选项卡配置
    const tabs = [
      { key: 'overview', label: '涨停概览' },
      { key: 'ladder', label: '连板天梯' },
      { key: 'concept', label: '概念轮动' },
      { key: 'trend', label: '趋势分析' }
    ]

    // AI数据上下文
    const aiDataContext = computed(() => {
      const tabNames = {
        overview: '涨停概览',
        ladder: '连板天梯',
        concept: '概念轮动',
        trend: '趋势分析'
      }

      let summary = `当前查看${tabNames[activeTab.value]}数据，日期：${formatDate(selectedDate.value)}。`

      if (activeTab.value === 'overview') {
        summary += `涨停股票${limitStats.value.up_limit_count || 0}只，跌停股票${limitStats.value.down_limit_count || 0}只，平均封单比${formatPercent(limitStats.value.up_limit_stats?.avg_fc_ratio)}，市场情绪${getMoodLevel()}。`
      } else if (activeTab.value === 'ladder') {
        summary += `连板股票总计${getTotalStepStocks()}只，`
        if (stepStats.value.length > 0) {
          const maxStep = Math.max(...stepStats.value.map(s => s._id))
          summary += `最高${maxStep}连板。`
        }
      } else if (activeTab.value === 'concept') {
        summary += `强势概念板块${conceptList.value.length}个，`
        if (conceptList.value.length > 0) {
          const topConcept = conceptList.value[0]
          summary += `领涨板块：${topConcept.name}(${formatPercent(topConcept.pct_chg)})。`
        }
      }

      return {
        type: 'limit_analysis',
        data: {
          activeTab: activeTab.value,
          selectedDate: selectedDate.value,
          limitStats: limitStats,
          stepStats: stepStats.value,
          conceptList: conceptList.value,
          conceptTrend: conceptTrend.value,
          trendAnalysis: trendAnalysis.value
        },
        summary
      }
    })

    // 方法
    const formatPercent = (value) => {
      if (value === null || value === undefined) return '--'
      return `${(value * 100).toFixed(2)}%`
    }

    const formatAmount = (value) => {
      if (value === null || value === undefined) return '--'
      if (value >= 100000000) {
        return `${(value / 100000000).toFixed(2)}亿`
      } else if (value >= 10000) {
        return `${(value / 10000).toFixed(2)}万`
      } else {
        return value.toFixed(2)
      }
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return '--'
      const year = dateStr.slice(0, 4)
      const month = dateStr.slice(4, 6)
      const day = dateStr.slice(6, 8)
      return `${year}-${month}-${day}`
    }

    const getMoodLevel = () => {
      const upCount = limitStats.value.up_limit_count || 0
      const downCount = limitStats.value.down_limit_count || 0
      const total = upCount + downCount
      
      if (total === 0) return '待观察'
      
      const ratio = upCount / total
      
      // 根据涨停跌停比例和绝对数量综合判断市场情绪
      if (ratio >= 0.9 && upCount >= 50) return '极度乐观'
      if (ratio >= 0.8 && upCount >= 30) return '非常乐观'
      if (ratio >= 0.7) return '乐观'
      if (ratio >= 0.6) return '偏乐观'
      if (ratio >= 0.4) return '中性'
      if (ratio >= 0.3) return '偏悲观'
      if (ratio >= 0.2) return '悲观'
      return '极度悲观'
    }

    const getTotalStepStocks = () => {
      return stepStats.value.reduce((total, group) => total + group.count, 0)
    }

    const getStepTagType = (step) => {
      if (step >= 5) return 'danger'
      if (step >= 3) return 'warning'
      return 'success'
    }

    const getChangeClass = (change) => {
      if (change > 0) return 'positive'
      if (change < 0) return 'negative'
      return 'neutral'
    }

    const getStatusTagType = (status) => {
      if (status === '强势') return 'danger'
      if (status === '活跃') return 'warning'
      return 'info'
    }

    // 数据加载方法
    const loadLimitStats = async () => {
      try {
        const response = await limitDataAPI.getLimitStats({
          trade_date: selectedDate.value
        })
        if (response.success) {
          // console.log('🔍 API响应数据:', response.data)
          // console.log('🔢 API中的涨停数:', response.data.up_limit_count)
          // console.log('🔢 API中的跌停数:', response.data.down_limit_count)
          
          // 整体替换ref对象以确保响应式更新
          // console.log('⏰ 赋值前 limitStats.value.up_limit_count:', limitStats.value.up_limit_count)
          
          limitStats.value = {
            up_limit_count: response.data.up_limit_count || 0,
            down_limit_count: response.data.down_limit_count || 0,
            up_limit_stats: response.data.up_limit_stats || {},
            down_limit_stats: response.data.down_limit_stats || {},
            trade_date: response.data.trade_date,
            timestamp: response.data.timestamp
          }
          
          // console.log('⏰ 赋值后 limitStats.value.up_limit_count:', limitStats.value.up_limit_count)
          // console.log('📊 更新后的limitStats (简化):', {
          //   up_limit_count: limitStats.value.up_limit_count,
          //   down_limit_count: limitStats.value.down_limit_count,
          //   trade_date: limitStats.value.trade_date
          // })
          // console.log('📈 涨停数:', limitStats.value.up_limit_count)
          // console.log('📉 跌停数:', limitStats.value.down_limit_count)
        }
      } catch (error) {
        console.error('加载涨停统计失败:', error)
      }
    }

    const loadLimitList = async () => {
      try {
        const response = await limitDataAPI.getLimitList({
          trade_date: selectedDate.value,
          limit: 100
        })
        if (response.success) {
          limitList.value = response.data.limit_list || []
        }
      } catch (error) {
        console.error('加载涨停列表失败:', error)
      }
    }

    const loadStepStats = async () => {
      try {
        const response = await limitDataAPI.getLimitStepStats({
          trade_date: selectedDate.value
        })
        if (response.success) {
          stepStats.value = response.data.step_stats || []
        }
      } catch (error) {
        console.error('加载连板统计失败:', error)
      }
    }

    const loadConceptList = async () => {
      try {
        const response = await limitDataAPI.getConceptList({
          trade_date: selectedDate.value,
          limit: 20
        })
        if (response.success) {
          conceptList.value = response.data.concept_list || []
        }
      } catch (error) {
        console.error('加载概念列表失败:', error)
      }
    }

    const loadConceptTrend = async () => {
      try {
        const response = await limitDataAPI.getConceptTrend({
          days: trendDays.value
        })
        if (response.success) {
          conceptTrend.value = response.data.trend_data || []
          await nextTick()
          renderConceptTrendChart()
        }
      } catch (error) {
        console.error('加载概念趋势失败:', error)
      }
    }

    const loadTrendAnalysis = async () => {
      try {
        const response = await limitDataAPI.getLimitTrendAnalysis({
          days: analysisDays.value
        })
        if (response.success) {
          trendAnalysis.value = response.data.trend_data || []
          await nextTick()
          renderTrendAnalysisChart()
        }
      } catch (error) {
        console.error('加载趋势分析失败:', error)
      }
    }

    // 图表渲染方法
    const renderLimitDistributionChart = () => {
      // console.log('🎨 renderLimitDistributionChart 开始执行')
      // console.log('📊 Chart容器存在:', !!limitDistributionChart.value)
      // console.log('📋 数据源长度:', limitList.value.length)
      // console.log('🏷️ 当前活动标签:', activeTab.value)
      
      if (!limitDistributionChart.value) {
        // console.log('❌ Chart容器不存在，等待300ms后重试')  
        setTimeout(() => {
          if (limitDistributionChart.value && activeTab.value === 'overview') {
            // console.log('🔄 重试渲染图表')
            renderLimitDistributionChart()
          }
        }, 300)
        return
      }
      
      // 先检查是否已有实例，如果有则销毁
      let chart = echarts.getInstanceByDom(limitDistributionChart.value)
      if (chart) {
        chart.dispose()
      }
      chart = echarts.init(limitDistributionChart.value)
      const industries = {}
      
      limitList.value.forEach(item => {
        if (item.limit === 'U') {
          industries[item.industry] = (industries[item.industry] || 0) + 1
        }
      })
      
      // console.log('🏭 行业分布数据:', industries)
      
      const data = Object.entries(industries)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 10)
        
      // console.log('📊 图表数据:', data)
      
      const option = {
        title: {
          text: '涨停行业分布',
          left: 'center',
          textStyle: { color: '#333', fontSize: 14 }
        },
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        series: [{
          name: '涨停股票',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '60%'],
          data: data,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      }
      
      chart.setOption(option)
    }

    const renderStepChart = () => {
      if (!stepChart.value) return
      
      // 先检查是否已有实例，如果有则销毁
      let chart = echarts.getInstanceByDom(stepChart.value)
      if (chart) {
        chart.dispose()
      }
      chart = echarts.init(stepChart.value)
      const data = stepStats.value.map(item => ({
        name: `${item._id}连板`,
        value: item.count
      })).reverse()
      
      const option = {
        title: {
          text: '连板分布',
          left: 'center',
          textStyle: { color: '#333', fontSize: 14 }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' }
        },
        xAxis: {
          type: 'category',
          data: data.map(item => item.name),
          axisLabel: { rotate: 45 }
        },
        yAxis: {
          type: 'value',
          name: '股票数量'
        },
        series: [{
          name: '连板股票',
          type: 'bar',
          data: data.map(item => item.value),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#ff6b6b' },
              { offset: 1, color: '#ee5a24' }
            ])
          }
        }]
      }
      
      chart.setOption(option)
    }

    const renderConceptTrendChart = () => {
      if (!conceptTrendChart.value || conceptTrend.value.length === 0) return
      
      // 先检查是否已有实例，如果有则销毁
      let chart = echarts.getInstanceByDom(conceptTrendChart.value)
      if (chart) {
        chart.dispose()
      }
      chart = echarts.init(conceptTrendChart.value)
      const dates = conceptTrend.value.map(item => formatDate(item.trade_date)).reverse()
      
      // 获取前5个概念的趋势数据
      const topConcepts = new Set()
      conceptTrend.value.forEach(day => {
        day.concepts.slice(0, 5).forEach(concept => {
          topConcepts.add(concept.name)
        })
      })
      
      const series = Array.from(topConcepts).map(conceptName => {
        const data = conceptTrend.value.map(day => {
          const concept = day.concepts.find(c => c.name === conceptName)
          return concept ? concept.rank : null
        }).reverse()
        
        return {
          name: conceptName,
          type: 'line',
          data: data,
          smooth: true
        }
      })
      
      const option = {
        title: {
          text: '概念板块排名趋势',
          left: 'center',
          textStyle: { color: '#333', fontSize: 14 }
        },
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          top: 30,
          type: 'scroll'
        },
        xAxis: {
          type: 'category',
          data: dates
        },
        yAxis: {
          type: 'value',
          name: '排名',
          inverse: true,
          min: 1
        },
        series: series
      }
      
      chart.setOption(option)
    }

    const renderTrendAnalysisChart = () => {
      if (!trendAnalysisChart.value || trendAnalysis.value.length === 0) return
      
      // 先检查是否已有实例，如果有则销毁
      let chart = echarts.getInstanceByDom(trendAnalysisChart.value)
      if (chart) {
        chart.dispose()
      }
      chart = echarts.init(trendAnalysisChart.value)
      
      // 按日期正序排列数据（最早的在左边）
      const sortedData = [...trendAnalysis.value].sort((a, b) => a.trade_date.localeCompare(b.trade_date))
      
      const dates = sortedData.map(item => formatDate(item.trade_date))
      const limitUpData = sortedData.map(item => item.up_limit_count || 0)
      const limitDownData = sortedData.map(item => item.down_limit_count || 0)
      
      const option = {
        title: {
          text: '涨跌停趋势分析',
          left: 'center',
          textStyle: { color: '#333', fontSize: 14 }
        },
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          top: 30,
          data: ['涨停', '跌停']
        },
        xAxis: {
          type: 'category',
          data: dates
        },
        yAxis: {
          type: 'value',
          name: '股票数量'
        },
        series: [
          {
            name: '涨停',
            type: 'line',
            data: limitUpData,
            itemStyle: { color: '#ff4757' },
            areaStyle: { opacity: 0.3 }
          },
          {
            name: '跌停',
            type: 'line',
            data: limitDownData,
            itemStyle: { color: '#2ed573' },
            areaStyle: { opacity: 0.3 }
          }
        ]
      }
      
      chart.setOption(option)
    }

    // 事件处理
    const onDateChange = () => {
      loadAllData()
    }

    const onTabChange = async (newTab) => {
      await nextTick()
      if (newTab === 'overview') {
        renderLimitDistributionChart()
      } else if (newTab === 'ladder') {
        renderStepChart()
      } else if (newTab === 'concept') {
        await loadConceptTrend()
      } else if (newTab === 'trend') {
        await loadTrendAnalysis()
      }
    }

    const loadAllData = async () => {
      loading.value = true
      error.value = ''
      try {
        await Promise.all([
          loadLimitStats(),
          loadLimitList(),
          loadStepStats(),
          loadConceptList()
        ])
        
        await nextTick()
        // console.log('🎯 当前标签页:', activeTab.value)
        // console.log('📋 涨停列表数据长度:', limitList.value.length)
        
        if (activeTab.value === 'overview') {
          // console.log('🎨 开始渲染概览图表 - 等待DOM更新')
          // 增加延迟确保DOM元素完全加载
          setTimeout(() => {
            renderLimitDistributionChart()
          }, 200)
        } else if (activeTab.value === 'ladder') {
          renderStepChart()
        } else if (activeTab.value === 'concept') {
          await loadConceptTrend()
        } else if (activeTab.value === 'trend') {
          await loadTrendAnalysis()
        }
      } catch (err) {
        error.value = '数据加载失败，请重试'
        console.error('加载数据失败:', err)
      } finally {
        loading.value = false
      }
    }

    // 监听选项卡变化
    watch(activeTab, async (newTab) => {
      // console.log('🔄 标签页切换到:', newTab)
      await nextTick()
      if (newTab === 'overview') {
        // console.log('🎨 标签页切换 - 渲染概览图表')
        renderLimitDistributionChart()
      } else if (newTab === 'ladder') {
        renderStepChart()
      } else if (newTab === 'concept') {
        await loadConceptTrend()
      } else if (newTab === 'trend') {
        await loadTrendAnalysis()
      }
    })

    // 监听数据变化，自动渲染图表
    watch(limitList, (newData) => {
      // console.log('📊 limitList数据变化，长度:', newData.length)
      if (activeTab.value === 'overview' && newData.length > 0) {
        // console.log('🎨 数据变化 - 等待DOM更新后渲染概览图表')
        // 等待更长时间确保DOM完全更新
        setTimeout(() => {
          renderLimitDistributionChart()
        }, 100)
      }
    }, { deep: true })

    // 组件挂载
    onMounted(() => {
      // console.log('🚀 组件挂载，开始加载数据')
      loadAllData()
    })

    return {
      // 响应式数据
      loading,
      error,
      selectedDate,
      activeTab,
      trendDays,
      analysisDays,
      tabs,
      
      // 数据状态
      limitStats,
      limitList,
      stepStats,
      conceptList,
      conceptTrend,
      trendAnalysis,
      
      // 图表引用
      limitDistributionChart,
      stepChart,
      conceptTrendChart,
      trendAnalysisChart,
      
      // 计算属性
      aiDataContext,
      
      // 方法
      formatPercent,
      formatAmount,
      formatDate,
      getMoodLevel,
      getTotalStepStocks,
      getStepTagType,
      getChangeClass,
      getStatusTagType,
      onDateChange,
      onTabChange,
      loadAllData,
      loadConceptTrend,
      loadTrendAnalysis
    }
  }
}
</script>

<style scoped>
.limit-analysis-panel {
  height: 100%;
  min-height: 500px;
  display: flex;
  flex-direction: column;
  background: var(--bg-content);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-primary);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  gap: var(--spacing-md);
}

.panel-title-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin: 0;
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 600;
}

.title-icon {
  width: 20px;
  height: 20px;
  color: var(--accent-primary);
}

.panel-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.date-control {
  min-width: 140px;
}

.date-picker {
  width: 140px;
}

.panel-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  overflow: hidden;
}


.panel-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

/* 概览样式 */
.overview-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.summary-section {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
  padding: var(--spacing-lg);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.summary-card {
  display: flex;
  align-items: center;
  padding: var(--spacing-lg);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
  border: 1px solid var(--border-color);
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}


.card-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: var(--spacing-md);
  color: white;
}

.card-icon svg {
  width: 24px;
  height: 24px;
}

.limit-up .card-icon {
  background: linear-gradient(135deg, #F56C6C, #E6A23C);
}

.limit-down .card-icon {
  background: linear-gradient(135deg, #67C23A, #5CB85C);
}

.avg-ratio .card-icon {
  background: linear-gradient(135deg, #409EFF, #3F9AFF);
}

.market-mood .card-icon {
  background: linear-gradient(135deg, #ab47bc, #8e24aa);
}

.card-content {
  flex: 1;
}

.card-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.card-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.card-change {
  font-size: 12px;
  margin-top: 4px;
}

.positive {
  color: #F56C6C;
}

.negative {
  color: #67C23A;
}

.neutral {
  color: var(--text-secondary);
}

.card-content {
  flex: 1;
}

.card-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.card-label {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 图表容器样式 */
.chart-container {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
  padding: var(--spacing-lg);
}

.chart-header {
  margin-bottom: var(--spacing-md);
}

.chart-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.chart-content {
  width: 100%;
  height: 300px;
}

/* 标签页样式 */
.tab-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 连板天梯样式 */
.ladder-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.ladder-stats {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
  padding: var(--spacing-lg);
}

.ladder-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.ladder-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
}

.ladder-summary {
  color: var(--text-secondary);
  font-size: 14px;
}

.step-stocks-list {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
  padding: var(--spacing-lg);
}

.list-header h4 {
  margin: 0 0 var(--spacing-md) 0;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
}

.step-groups {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.step-group {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.group-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.step-badge {
  background: linear-gradient(135deg, #F56C6C, #E6A23C);
  color: white;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
}

.stock-count {
  color: var(--text-secondary);
  font-size: 14px;
}

.stock-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.stock-tag {
  margin: 0;
}

/* 概念轮动样式 */
.concept-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.concept-ranking {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
  padding: var(--spacing-lg);
}

.ranking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.ranking-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
}

.ranking-date {
  color: var(--text-secondary);
  font-size: 14px;
}

.concept-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.concept-item {
  display: flex;
  align-items: center;
  padding: var(--spacing-sm);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  transition: all 0.3s ease;
}

.concept-item:hover {
  border-color: var(--primary-color);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.concept-item.top-concept {
  background: linear-gradient(135deg, rgba(255, 107, 107, 0.1), rgba(230, 162, 60, 0.1));
  border-color: #F56C6C;
}

.concept-rank {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-color), #5A6ACF);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  margin-right: var(--spacing-md);
}

.concept-info {
  flex: 1;
}

.concept-name {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.concept-stats {
  display: flex;
  gap: var(--spacing-sm);
  font-size: 12px;
}

.up-count {
  color: var(--text-secondary);
}

.change-rate.positive {
  color: #F56C6C;
}

.change-rate.negative {
  color: #67C23A;
}

.change-rate.neutral {
  color: var(--text-secondary);
}

.concept-status {
  margin-left: var(--spacing-md);
}

.concept-trend {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
  padding: var(--spacing-lg);
}

.trend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.trend-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
}

/* 趋势分析样式 */
.trend-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.trend-analysis {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
  padding: var(--spacing-lg);
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.analysis-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
}

/* 现代化控件样式 */
:deep(.el-radio-group) {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 2px;
  border: 1px solid var(--border-secondary);
}

:deep(.el-radio-button__inner) {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 6px;
  transition: all 0.3s ease;
  font-weight: 500;
}

:deep(.el-radio-button.is-active .el-radio-button__inner) {
  background: var(--primary-color);
  color: #ffffff;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.3);
}

:deep(.el-radio-button:hover .el-radio-button__inner) {
  background: rgba(64, 158, 255, 0.1);
  color: var(--primary-color);
}

/* 加载和错误状态样式 */
.loading-container,
.error-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  background-color: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(5px);
  z-index: 10;
  border-radius: var(--radius-lg);
}

:deep(.dark) .loading-container,
:deep(.dark) .error-container {
  background-color: rgba(0, 0, 0, 0.8);
}

.loading-icon,
.error-icon {
  font-size: 32px;
  color: var(--primary-color);
}

.loading-text,
.error-text {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.retry-button {
  margin-top: var(--spacing-sm);
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .panel-header {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-sm);
  }
  
  .panel-controls {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-sm);
  }
  
  .summary-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: var(--spacing-sm);
  }
  
  .summary-card {
    padding: var(--spacing-md);
  }
  
  .card-icon {
    width: 40px;
    height: 40px;
    margin-right: var(--spacing-sm);
  }
  
  .card-value {
    font-size: 20px;
  }
  
  .concept-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
  }
  
  .concept-rank {
    margin-right: 0;
  }
  
  .step-groups {
    gap: var(--spacing-sm);
  }
  
  .chart-content {
    height: 250px;
  }
}
</style>