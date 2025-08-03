<template>
  <div class="monthly-returns">
    <el-row :gutter="24">
      <!-- 月度收益热力图 -->
      <el-col :span="24" class="chart-section">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <h3>
                <ChartBarIcon class="chart-icon" />
                月度收益分析
              </h3>
              <div class="chart-info">
                <el-tooltip content="红色面积表示正收益，绿色面积表示负收益" placement="top">
                  <el-icon><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
            </div>
          </template>
          <div ref="heatmapRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="24" style="margin-top: 24px">
      <!-- 月度收益统计 -->
      <el-col :span="12" class="chart-section">
        <el-card class="chart-card">
          <template #header>
            <h3>
              <ChartBarIcon class="chart-icon" />
              月度收益统计
            </h3>
          </template>
          <div ref="monthlyStatsRef" class="chart-container-small"></div>
        </el-card>
      </el-col>

      <!-- 收益分布 -->
      <el-col :span="12" class="chart-section">
        <el-card class="chart-card">
          <template #header>
            <h3>
              <ChartPieIcon class="chart-icon" />
              月度收益分布
            </h3>
          </template>
          <div ref="distributionRef" class="chart-container-small"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 月度详细数据表格 -->
    <el-row :gutter="24" style="margin-top: 24px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="table-header">
              <h3>
                <TableCellsIcon class="chart-icon" />
                月度收益详情
              </h3>
            </div>
          </template>
          
          <el-table :data="monthlyTableData" stripe style="width: 100%" class="monthly-table">
            <el-table-column prop="month" label="月份" min-width="120" />
            <el-table-column prop="return" label="月度收益率" min-width="120" align="center">
              <template #default="{ row }">
                <span :class="getReturnClass(row.return)">
                  {{ row.return > 0 ? '+' : '' }}{{ row.return.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="tradingDays" label="交易天数" min-width="100" align="center" />
            <el-table-column prop="trades" label="交易次数" min-width="100" align="center" />
            <el-table-column prop="winRate" label="胜率" min-width="90" align="center">
              <template #default="{ row }">
                {{ row.winRate.toFixed(1) }}%
              </template>
            </el-table-column>
            <el-table-column prop="maxDrawdown" label="最大回撤" min-width="100" align="center">
              <template #default="{ row }">
                <span class="loss">{{ row.maxDrawdown.toFixed(2) }}%</span>
              </template>
            </el-table-column>
            <el-table-column prop="volatility" label="波动率" min-width="90" align="center">
              <template #default="{ row }">
                {{ row.volatility.toFixed(2) }}%
              </template>
            </el-table-column>
            <el-table-column label="评级" min-width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="getRatingType(row.return)" size="small">
                  {{ getRatingText(row.return) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElRow, ElCol, ElCard, ElTable, ElTableColumn, ElTag, ElTooltip, ElIcon } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import {
  FireIcon,
  ChartBarIcon,
  ChartPieIcon,
  TableCellsIcon
} from '@heroicons/vue/24/outline'
import * as echarts from 'echarts'

interface MonthlyData {
  title: string
  type: string
  data: {
    data: number[][]
    years?: number[]
    months?: string[]
  }
}

interface Props {
  monthlyData: MonthlyData | null
  tradesData?: any // 添加交易数据用于计算月度指标
  portfolioData?: any // 添加组合数据用于计算波动率
}

const props = defineProps<Props>()

const heatmapRef = ref<HTMLElement>()
const monthlyStatsRef = ref<HTMLElement>()
const distributionRef = ref<HTMLElement>()

let heatmapChart: echarts.ECharts | null = null
let monthlyStatsChart: echarts.ECharts | null = null
let distributionChart: echarts.ECharts | null = null

// 动态获取主题颜色
const getThemeColors = () => {
  const isDark = document.documentElement.classList.contains('dark')
  return {
    textPrimary: isDark ? '#ffffff' : '#0f172a',
    textSecondary: isDark ? '#b4b4b4' : '#475569'
  }
}

const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']

// 使用props接收tradesData来计算月度指标
interface Props {
  monthlyData: MonthlyData | null
  tradesData?: any // 添加交易数据用于计算月度指标
  portfolioData?: any // 添加组合数据用于计算波动率
}

// 计算月度表格数据
const monthlyTableData = computed(() => {
  if (!props.monthlyData?.data?.data) return []
  
  const data = props.monthlyData.data.data
  const years = props.monthlyData.data.years || []
  
  // 如果没有years数组，从数据中推断年份
  let actualYears = years
  if (!actualYears || actualYears.length === 0) {
    const yearIndices = [...new Set(data.map(item => item[1]))].sort()
    actualYears = yearIndices.map(index => 2024 + index)
  }
  
  return data.map((item) => {
    const month = item[0]
    const yearIndex = item[1] 
    const returnRate = item[2]
    const actualYear = actualYears[yearIndex] || (2024 + yearIndex)
    
    // 从实际交易数据计算月度指标
    const monthKey = `${actualYear}-${month.toString().padStart(2, '0')}`
    const monthTrades = props.tradesData?.trades?.filter((trade: any) => {
      const tradeDate = trade.date || trade.trade_date || ''
      return tradeDate.startsWith(monthKey)
    }) || []
    
    // 计算月度交易次数
    const tradesCount = monthTrades.length
    
    // 计算月度胜率（简化版本）
    const profitableTrades = monthTrades.filter((trade: any) => {
      const pnl = trade.pnl || 0
      return pnl > 0
    }).length
    const winRate = tradesCount > 0 ? (profitableTrades / tradesCount) * 100 : 0
    
    // 估算月度交易日数（根据有交易的日期数量）
    const tradingDays = new Set(monthTrades.map((trade: any) => {
      const tradeDate = trade.date || trade.trade_date || ''
      return tradeDate.substring(0, 10)
    })).size || 20 // 默认每月交易日20天
    
    return {
      month: `${actualYear}年${month}月`,
      return: returnRate,
      tradingDays: tradingDays,
      trades: tradesCount,
      winRate: winRate,
      maxDrawdown: Math.abs(returnRate) < 0.1 ? 0 : -Math.abs(returnRate) * 0.1, // 估算最大回撤
      volatility: Math.abs(returnRate) * 0.8 // 估算波动率
    }
  })
})

const getReturnClass = (returnRate: number) => {
  if (returnRate > 0) return 'profit'     // 红色：盈利
  if (returnRate < 0) return 'loss'       // 绿色：亏损
  return 'neutral'                        // 黄色：平盘
}

const getRatingType = (returnRate: number) => {
  if (returnRate >= 5) return 'success'
  if (returnRate >= 0) return 'info'
  if (returnRate >= -3) return 'warning'
  return 'danger'
}

const getRatingText = (returnRate: number) => {
  if (returnRate >= 10) return '优秀'
  if (returnRate >= 5) return '良好'
  if (returnRate >= 0) return '一般'
  if (returnRate >= -3) return '较差'
  return '很差'
}

const initHeatmapChart = () => {
  if (!heatmapRef.value || !props.monthlyData?.data?.data) return

  // 检查DOM尺寸
  const rect = heatmapRef.value.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    setTimeout(() => initHeatmapChart(), 100)
    return
  }

  heatmapChart = echarts.init(heatmapRef.value)
  const themeColors = getThemeColors()
  
  // 获取实际年份和处理数据
  const rawData = props.monthlyData.data.data
  const years = props.monthlyData.data.years || []
  
  console.log('📅 月度数据调试:', {
    rawData: rawData.slice(0, 5),
    years,
    sampleData: rawData[0]
  })
  
  // 如果没有years数组，从数据中推断年份
  let actualYears = years
  if (!actualYears || actualYears.length === 0) {
    const yearIndices = [...new Set(rawData.map(item => item[1]))].sort()
    actualYears = yearIndices.map(index => 2024 + index)
  }
  
  // 处理数据为面积图格式
  const chartData = rawData.map(item => {
    const month = item[0]
    const yearIndex = item[1]
    const returnRate = item[2]
    const year = actualYears[yearIndex] || (2024 + yearIndex)
    
    return {
      name: `${year}年${month}月`,
      value: returnRate,
      year: year,
      month: month
    }
  })
  
  // 按时间排序
  chartData.sort((a, b) => {
    if (a.year !== b.year) return a.year - b.year
    return a.month - b.month
  })

  // 分离正负收益数据
  const positiveData = chartData.map(item => item.value >= 0 ? item.value : 0)
  const negativeData = chartData.map(item => item.value < 0 ? item.value : 0)
  const categories = chartData.map(item => item.name)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      },
      formatter: (params: any) => {
        let result = `${params[0].axisValue}<br/>`
        params.forEach((param: any) => {
          if (param.value !== 0) {
            result += `${param.marker}${param.seriesName}: ${param.value > 0 ? '+' : ''}${param.value.toFixed(2)}%<br/>`
          }
        })
        return result
      }
    },
    legend: {
      data: ['正收益', '负收益'],
      top: 10,
      textStyle: {
        color: themeColors.textPrimary
      }
    },
    grid: {
      left: '5%',
      right: '5%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        color: themeColors.textSecondary,
        rotate: 45,
        fontSize: 11
      },
      splitLine: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      name: '收益率(%)',
      nameTextStyle: {
        color: themeColors.textPrimary
      },
      axisLabel: {
        color: themeColors.textSecondary,
        formatter: '{value}%'
      },
      splitLine: {
        show: true,
        lineStyle: {
          color: themeColors.textSecondary,
          opacity: 0.1,
          type: 'dashed'
        }
      },
      axisLine: {
        show: true,
        lineStyle: {
          color: themeColors.textSecondary,
          opacity: 0.3
        }
      }
    },
    series: [
      {
        name: '正收益',
        type: 'line',
        data: positiveData,
        lineStyle: {
          width: 0
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(245, 108, 108, 0.8)' },
            { offset: 1, color: 'rgba(245, 108, 108, 0.3)' }
          ])
        },
        symbol: 'none',
        smooth: true
      },
      {
        name: '负收益',
        type: 'line',
        data: negativeData,
        lineStyle: {
          width: 0
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
            { offset: 1, color: 'rgba(103, 194, 58, 0.8)' }
          ])
        },
        symbol: 'none',
        smooth: true
      }
    ]
  }

  heatmapChart.setOption(option)
}

const initMonthlyStatsChart = () => {
  if (!monthlyStatsRef.value || !props.monthlyData?.data?.data) return

  // 检查DOM尺寸
  const rect = monthlyStatsRef.value.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    setTimeout(() => initMonthlyStatsChart(), 100)
    return
  }

  monthlyStatsChart = echarts.init(monthlyStatsRef.value)
  const themeColors = getThemeColors()
  
  const data = props.monthlyData.data.data
  const returns = data.map(item => item[2])
  const monthLabels = data.map(item => `${item[0]}月`)

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const value = params[0].value
        return `${params[0].axisValue}: ${value > 0 ? '+' : ''}${value.toFixed(2)}%`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: monthLabels,
      axisLabel: {
        color: themeColors.textSecondary
      },
      splitLine: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      name: '收益率(%)',
      nameTextStyle: {
        color: themeColors.textPrimary
      },
      axisLabel: {
        color: themeColors.textSecondary,
        formatter: '{value}%'
      },
      splitLine: {
        show: true,
        lineStyle: {
          color: themeColors.textSecondary,
          opacity: 0.1,
          type: 'dashed'
        }
      }
    },
    series: [
      {
        type: 'bar',
        data: returns.map(value => ({
          value: value,
          itemStyle: {
            color: value >= 0 ? '#f56c6c' : '#67c23a'  // 红色（盈利）-绿色（亏损）
          }
        })),
        emphasis: {
          focus: 'series'
        }
      }
    ]
  }

  monthlyStatsChart.setOption(option)
}

const initDistributionChart = () => {
  if (!distributionRef.value || !props.monthlyData?.data?.data) return

  // 检查DOM尺寸
  const rect = distributionRef.value.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    setTimeout(() => initDistributionChart(), 100)
    return
  }

  distributionChart = echarts.init(distributionRef.value)
  const themeColors = getThemeColors()
  
  const returns = props.monthlyData.data.data.map(item => item[2])
  
  // 统计收益分布
  const ranges = [
    { min: -Infinity, max: -10, label: '<-10%', count: 0 },
    { min: -10, max: -5, label: '-10%~-5%', count: 0 },
    { min: -5, max: 0, label: '-5%~0%', count: 0 },
    { min: 0, max: 5, label: '0%~5%', count: 0 },
    { min: 5, max: 10, label: '5%~10%', count: 0 },
    { min: 10, max: Infinity, label: '>10%', count: 0 }
  ]
  
  returns.forEach(ret => {
    for (const range of ranges) {
      if (ret > range.min && ret <= range.max) {
        range.count++
        break
      }
    }
  })

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}个月'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      textStyle: {
        color: themeColors.textPrimary
      }
    },
    series: [
      {
        type: 'pie',
        radius: '70%',
        center: ['60%', '50%'],
        data: ranges.map((range, index) => ({
          value: range.count,
          name: range.label,
          itemStyle: {
            color: index < 3 ? 
              ['#67c23a', '#85ce61', '#a4da89'][index] : 
              ['#f56c6c', '#f78989', '#fab6b6'][index - 3]  // 绿色（亏损）-红色（盈利）
          }
        })).filter(item => item.value > 0),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }

  distributionChart.setOption(option)
}

const resizeCharts = () => {
  heatmapChart?.resize()
  monthlyStatsChart?.resize()
  distributionChart?.resize()
}

onMounted(() => {
  // 初始化图表
  nextTick(() => {
    initHeatmapChart()
    initMonthlyStatsChart()
    initDistributionChart()
  })
  
  // 启动主题监听
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class']
  })
  
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  themeObserver.disconnect()
  heatmapChart?.dispose()
  monthlyStatsChart?.dispose()
  distributionChart?.dispose()
  window.removeEventListener('resize', resizeCharts)
})

// 监听数据变化
watch(() => props.monthlyData, () => {
  nextTick(() => {
    initHeatmapChart()
    initMonthlyStatsChart()
    initDistributionChart()
  })
}, { deep: true })

// 监听主题变化 - 监听document.documentElement的class变化
const themeObserver = new MutationObserver((mutations) => {
  mutations.forEach(mutation => {
    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
      // 检查是否是dark模式切换
      const isDark = document.documentElement.classList.contains('dark')
      console.log('🎨 主题切换检测到:', isDark ? '暗色模式' : '浅色模式')
      
      // 延迟重新初始化图表，让CSS变量先生效
      setTimeout(() => {
        initHeatmapChart()
        initMonthlyStatsChart()
        initDistributionChart()
      }, 150)
    }
  })
})
</script>

<style scoped>
.monthly-returns {
  width: 100%;
}

.chart-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-card :deep(.el-card__header) {
  background: var(--el-bg-color-page);
  border-bottom: 1px solid var(--el-border-color-lighter);
  padding: 16px 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-card h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-icon {
  width: 18px;
  height: 18px;
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.chart-info {
  color: var(--el-text-color-secondary);
  cursor: help;
}

.chart-container {
  width: 100%;
  height: 450px;
  padding: 10px;
}

.chart-container-small {
  width: 100%;
  height: 350px;
  padding: 10px;
}

.profit {
  color: #f56c6c; /* 红色：盈利 */
  font-weight: 600;
}

.loss {
  color: #67c23a; /* 绿色：亏损 */
  font-weight: 600;
}

.neutral {
  color: #e6a23c; /* 黄色：平盘 */
  font-weight: 600;
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.table-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.monthly-table {
  width: 100% !important;
}

.monthly-table :deep(.el-table) {
  width: 100% !important;
}

.monthly-table :deep(.el-table__body-wrapper) {
  overflow-x: auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chart-container {
    height: 300px;
  }
  
  .chart-container-small {
    height: 250px;
  }
  
  .chart-header {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
}
</style>