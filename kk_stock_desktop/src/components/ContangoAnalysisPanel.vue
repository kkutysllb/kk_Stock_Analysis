<template>
  <div class="contango-analysis-panel card glass-effect">
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="header-left">
        <div class="panel-title-section">
          <h3 class="panel-title">
            <ArrowTrendingUpIcon class="section-icon" />
            股指期货正反向市场分析
          </h3>
        </div>
        <p class="section-subtitle">期货与现货价差分析，判断市场结构状态</p>
      </div>
      <div class="header-actions">
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYYMMDD"
          @change="onDateChange"
          size="default"
          class="date-picker"
          :clearable="false"
        />
        <el-button 
          @click="refreshData" 
          :loading="loading" 
          type="primary" 
          size="default"
          class="refresh-btn"
        >
          <ArrowPathIcon class="btn-icon" />
          刷新
        </el-button>
      </div>
    </div>

    <!-- 市场概览 -->
    <div class="market-overview" v-if="!loading && analysisData">
      <div class="overview-cards">
        <div class="overview-card contango">
          <div class="card-icon">
            <ArrowTrendingUpIcon class="icon" />
          </div>
          <div class="card-content">
            <div class="card-value">{{ marketOverview.contangoCount }}</div>
            <div class="card-label">正向市场合约</div>
          </div>
        </div>
        
        <div class="overview-card backwardation">
          <div class="card-icon">
            <ArrowTrendingDownIcon class="icon" />
          </div>
          <div class="card-content">
            <div class="card-value">{{ marketOverview.backwardationCount }}</div>
            <div class="card-label">反向市场合约</div>
          </div>
        </div>
        
        <div class="overview-card total">
          <div class="card-icon">
            <ChartBarIcon class="icon" />
          </div>
          <div class="card-content">
            <div class="card-value">{{ marketOverview.totalContracts }}</div>
            <div class="card-label">总合约数</div>
          </div>
        </div>
        
        <div class="overview-card basis-rate">
          <div class="card-icon">
            <CalculatorIcon class="icon" />
          </div>
          <div class="card-content">
            <div class="card-value" :class="getBasisRateClass(marketOverview.avgBasisRate)">
              {{ formatBasisRate(marketOverview.avgBasisRate) }}
            </div>
            <div class="card-label">平均基差率</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 期货品种分析 -->
    <div class="card-body">
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <div class="loading-text">加载正反向市场分析数据中...</div>
      </div>
      
      <div v-else class="analysis-cards-container">
        <div 
          v-for="symbolData in analysisData?.analysis_results" 
          :key="symbolData.symbol"
          class="analysis-card"
          :class="getSymbolCardClass(symbolData)"
        >
          <!-- 卡片头部 -->
          <div class="analysis-header">
            <div class="symbol-info">
              <h4 class="symbol-name">{{ getSymbolName(symbolData.symbol) }}</h4>
              <span class="symbol-code">{{ symbolData.symbol }}</span>
              <span class="spot-index">现货: {{ symbolData.spot_index_code }}</span>
            </div>
            <div class="header-actions">
              <div class="market-status" :class="getMarketStatusClass(symbolData)">
                <component :is="getMarketStatusIcon(symbolData)" class="status-icon" />
                <span class="status-text">{{ getMarketStatusText(symbolData) }}</span>
              </div>
              <AskAIComponent :data-context="getSymbolAIContext(symbolData)" />
            </div>
          </div>

          <!-- 期限结构图表 -->
          <div class="term-structure-chart" v-if="symbolData.contracts && symbolData.contracts.length > 0">
            <div class="chart-header">
              <h5>期限结构</h5>
              <span class="spot-price">现货价格: {{ symbolData.spot_price }}</span>
            </div>
            
            <div class="contracts-list">
              <div 
                v-for="contract in symbolData.contracts"
                :key="contract.ts_code"
                class="contract-item"
                :class="{ 'contango': contract.is_contango, 'backwardation': !contract.is_contango }"
              >
                <div class="contract-info">
                  <span class="contract-code">{{ contract.ts_code }}</span>
                  <span class="contract-price">{{ formatPrice(contract.futures_price) }}</span>
                </div>
                <div class="basis-info">
                  <span class="basis">基差: {{ formatBasis(contract.basis) }}</span>
                  <span class="basis-rate" :class="getBasisRateClass(contract.basis_rate)">
                    {{ formatBasisRate(contract.basis_rate) }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 基差和基差率组合图表 -->
          <div class="basis-chart-container" v-if="symbolData.contracts && symbolData.contracts.length > 0">
            <VChart 
              :option="getBasisChartOption(symbolData)" 
              :style="{ height: '300px', width: '100%' }"
              autoresize
            />
          </div>

          <!-- 所有合约列表 -->
          <div class="contracts-list" v-if="symbolData.contracts && symbolData.contracts.length > 0">
            <div class="list-header">
              <span class="list-title">所有活跃合约 ({{ symbolData.contracts.length }}个)</span>
            </div>
            <div class="contracts-table">
              <div class="table-header">
                <span class="col-contract">合约代码</span>
                <span class="col-price">期货价格</span>
                <span class="col-basis">基差</span>
                <span class="col-basis-rate">基差率</span>
                <span class="col-days">到期天数</span>
                <span class="col-status">状态</span>
              </div>
              <div class="table-body">
                <div 
                  v-for="contract in symbolData.contracts" 
                  :key="contract.ts_code"
                  class="table-row"
                  :class="getContractRowClass(contract)"
                >
                  <span class="col-contract">{{ contract.ts_code }}</span>
                  <span class="col-price">{{ formatPrice(contract.futures_price) }}</span>
                  <span class="col-basis" :class="getBasisClass(contract.basis)">
                    {{ formatBasis(contract.basis) }}
                  </span>
                  <span class="col-basis-rate" :class="getBasisRateClass(contract.basis_rate)">
                    {{ formatBasisRate(contract.basis_rate) }}
                  </span>
                  <span class="col-days">{{ contract.days_to_expiry }}天</span>
                  <span class="col-status" :class="getContractStatusClass(contract.is_contango)">
                    {{ contract.is_contango ? '正向' : '反向' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 数据为空时的提示 -->
      <div v-if="!loading && (!analysisData || !analysisData.analysis_results || analysisData.analysis_results.length === 0)" class="empty-state">
        <ExclamationTriangleIcon class="empty-icon" />
        <p class="empty-text">暂无正反向市场分析数据</p>
        <p class="empty-hint">请检查数据源或选择其他日期</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { futuresAPI } from '../api/futures'
import AskAIComponent from './AskAIComponent.vue'
import { useAppStore } from '../stores/app'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import {
  CanvasRenderer
} from 'echarts/renderers'
import {
  LineChart,
  BarChart
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ArrowPathIcon,
  ChartBarIcon,
  CalculatorIcon,
  ExclamationTriangleIcon
} from '@heroicons/vue/24/outline'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

// 注册组件
const components = {
  VChart
}

// 响应式数据
const loading = ref(false)
const selectedDate = ref(new Date().toISOString().split('T')[0].replace(/-/g, '')) // YYYYMMDD格式
const analysisData = ref(null)
const appStore = useAppStore()

// 期货品种配置
const symbolNames = {
  'IF': 'IF沪深300',
  'IC': 'IC中证500', 
  'IH': 'IH上证50',
  'IM': 'IM中证1000'
}

// 获取正反向市场分析数据
const fetchAnalysisData = async () => {
  loading.value = true
  try {
    const response = await futuresAPI.getContangoAnalysis(selectedDate.value)
    if (response.success && response.data) {
      analysisData.value = response.data
    } else {
      throw new Error(response.message || '获取数据失败')
    }
  } catch (error) {
    ElMessage.error(`获取正反向市场分析数据失败: ${error.message || error}`)
    analysisData.value = null
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = () => {
  fetchAnalysisData()
}

// 日期变化处理
const onDateChange = (date) => {
  selectedDate.value = date
  fetchAnalysisData()
}

// 市场概览数据
const marketOverview = computed(() => {
  if (!analysisData.value || !analysisData.value.analysis_results) {
    return {
      contangoCount: 0,
      backwardationCount: 0,
      totalContracts: 0,
      avgBasisRate: 0
    }
  }
  
  let totalContango = 0
  let totalBackwardation = 0
  let totalBasisRate = 0
  let totalContracts = 0
  
  analysisData.value.analysis_results.forEach(result => {
    result.contracts.forEach(contract => {
      if (contract.is_contango) {
        totalContango++
      } else {
        totalBackwardation++
      }
      totalBasisRate += contract.basis_rate
      totalContracts++
    })
  })
  
  return {
    contangoCount: totalContango,
    backwardationCount: totalBackwardation,
    totalContracts: totalContracts,
    avgBasisRate: totalContracts > 0 ? totalBasisRate / totalContracts : 0
  }
})

// AI数据上下文
const aiDataContext = computed(() => {
  const dateStr = selectedDate.value ? `${selectedDate.value.slice(0,4)}-${selectedDate.value.slice(4,6)}-${selectedDate.value.slice(6,8)}` : ''
  
  if (!analysisData.value || !analysisData.value.analysis_results) {
    return `股指期货正反向市场分析 (${dateStr}):\n\n暂无数据`
  }
  
  const overview = marketOverview.value
  let summary = `股指期货正反向市场分析 (${dateStr}):\n\n`
  summary += `市场概览:\n`
  summary += `- 正向市场合约: ${overview.contangoCount}个\n`
  summary += `- 反向市场合约: ${overview.backwardationCount}个\n`
  summary += `- 总合约数: ${overview.totalContracts}个\n`
  summary += `- 平均基差率: ${formatBasisRate(overview.avgBasisRate)}\n\n`
  
  summary += `各品种分析:\n`
  analysisData.value.analysis_results.forEach((symbolData, index) => {
    const symbolName = getSymbolName(symbolData.symbol)
    const statusText = getMarketStatusText(symbolData)
    const contangoCount = symbolData.contracts.filter(c => c.is_contango).length
    const backwardationCount = symbolData.contracts.length - contangoCount
    
    summary += `${index + 1}. ${symbolName} (${symbolData.symbol}):\n`
    summary += `   - 现货价格: ${symbolData.spot_price}\n`
    summary += `   - 市场状态: ${statusText}\n`
    summary += `   - 正向合约: ${contangoCount}个, 反向合约: ${backwardationCount}个\n`
    
    if (symbolData.contracts && symbolData.contracts.length > 0) {
      const nearContract = symbolData.contracts.sort((a, b) => a.days_to_expiry - b.days_to_expiry)[0]
      summary += `   - 近月合约: ${nearContract.ts_code}, 基差: ${formatBasis(nearContract.basis)}, 基差率: ${formatBasisRate(nearContract.basis_rate)}\n`
    }
    summary += '\n'
  })
  
  return summary
})

// 获取品种名称
const getSymbolName = (symbol) => {
  return symbolNames[symbol] || symbol
}

// 为每个品种创建独立的AI数据上下文
const getSymbolAIContext = (symbolData) => {
  const dateStr = selectedDate.value ? `${selectedDate.value.slice(0,4)}-${selectedDate.value.slice(4,6)}-${selectedDate.value.slice(6,8)}` : ''
  const symbolName = getSymbolName(symbolData.symbol)
  
  if (!symbolData || !symbolData.contracts) {
    return {
      type: 'contango_symbol_analysis',
      title: `${symbolName}正反向市场分析`,
      period: dateStr,
      data: { 
        symbol: symbolData.symbol,
        symbolName: symbolName,
        date: dateStr 
      },
      summary: `${symbolName}正反向市场分析 (${dateStr}):\n\n暂无数据`
    }
  }
  
  const contracts = symbolData.contracts || []
  const contangoCount = contracts.filter(c => c.is_contango).length
  const backwardationCount = contracts.length - contangoCount
  const statusText = getMarketStatusText(symbolData)
  
  // 计算平均基差率
  const avgBasisRate = contracts.length > 0 
    ? contracts.reduce((sum, c) => sum + (c.basis_rate || 0), 0) / contracts.length 
    : 0
  
  // 获取主力合约（通常是最近到期的合约）
  const nearContract = contracts.length > 0 
    ? contracts.sort((a, b) => a.days_to_expiry - b.days_to_expiry)[0] 
    : null
  
  // 获取远月合约（最远到期的合约）
  const farContract = contracts.length > 0 
    ? contracts.sort((a, b) => b.days_to_expiry - a.days_to_expiry)[0] 
    : null
  
  let summary = `${symbolName}正反向市场分析 (${dateStr}):\n\n`
  summary += `## 品种基本信息\n`
  summary += `- 品种名称：${symbolName}\n`
  summary += `- 品种代码：${symbolData.symbol}\n`
  summary += `- 现货指数：${symbolData.spot_index_code || '--'}\n`
  summary += `- 现货价格：${symbolData.spot_price || '--'}\n`
  summary += `- 分析日期：${dateStr}\n\n`
  
  summary += `## 市场结构分析\n`
  summary += `- 市场状态：${statusText}\n`
  summary += `- 活跃合约数：${contracts.length}个\n`
  summary += `- 正向市场合约：${contangoCount}个\n`
  summary += `- 反向市场合约：${backwardationCount}个\n`
  summary += `- 平均基差率：${formatBasisRate(avgBasisRate)}\n\n`
  
  if (nearContract) {
    summary += `## 主力合约分析\n`
    summary += `- 合约代码：${nearContract.ts_code}\n`
    summary += `- 期货价格：${formatPrice(nearContract.futures_price)}\n`
    summary += `- 基差：${formatBasis(nearContract.basis)}点\n`
    summary += `- 基差率：${formatBasisRate(nearContract.basis_rate)}\n`
    summary += `- 到期天数：${nearContract.days_to_expiry}天\n`
    summary += `- 合约状态：${nearContract.is_contango ? '正向市场' : '反向市场'}\n\n`
  }
  
  if (farContract && farContract.ts_code !== nearContract?.ts_code) {
    summary += `## 远月合约分析\n`
    summary += `- 合约代码：${farContract.ts_code}\n`
    summary += `- 期货价格：${formatPrice(farContract.futures_price)}\n`
    summary += `- 基差：${formatBasis(farContract.basis)}点\n`
    summary += `- 基差率：${formatBasisRate(farContract.basis_rate)}\n`
    summary += `- 到期天数：${farContract.days_to_expiry}天\n`
    summary += `- 合约状态：${farContract.is_contango ? '正向市场' : '反向市场'}\n\n`
  }
  
  summary += `## 期限结构详情\n`
  contracts.forEach((contract, index) => {
    summary += `${index + 1}. ${contract.ts_code}：\n`
    summary += `   - 期货价格：${formatPrice(contract.futures_price)}\n`
    summary += `   - 基差：${formatBasis(contract.basis)}点\n`
    summary += `   - 基差率：${formatBasisRate(contract.basis_rate)}\n`
    summary += `   - 到期天数：${contract.days_to_expiry}天\n`
    summary += `   - 状态：${contract.is_contango ? '正向' : '反向'}\n\n`
  })
  
  summary += `## 投资策略建议\n`
  if (contangoCount > backwardationCount) {
    summary += `- 当前${symbolName}主要呈现正向市场特征，期货价格普遍高于现货\n`
    summary += `- 可考虑卖出远月合约、买入近月合约的期限套利策略\n`
    summary += `- 关注基差收敛风险，合理设置止损位\n`
  } else if (backwardationCount > contangoCount) {
    summary += `- 当前${symbolName}主要呈现反向市场特征，期货价格普遍低于现货\n`
    summary += `- 可考虑买入远月合约、卖出近月合约的期限套利策略\n`
    summary += `- 注意供需基本面变化对期限结构的影响\n`
  } else {
    summary += `- 当前${symbolName}正反向市场混合，期限结构分化明显\n`
    summary += `- 建议谨慎操作，密切关注市场变化\n`
    summary += `- 可考虑跨月价差交易机会\n`
  }
  
  summary += `\n请基于以上${symbolName}的完整正反向市场分析，制定具体的投资策略和风险控制方案。`
  
  return {
    type: 'contango_symbol_analysis',
    title: `${symbolName}正反向市场分析`,
    period: dateStr,
    data: {
      symbol: symbolData.symbol,
      symbolName: symbolName,
      date: dateStr,
      spotPrice: symbolData.spot_price,
      contracts: contracts,
      marketStatus: statusText,
      contangoCount: contangoCount,
      backwardationCount: backwardationCount,
      avgBasisRate: avgBasisRate,
      nearContract: nearContract,
      farContract: farContract
    },
    summary: summary
  }
}

// 格式化价格
const formatPrice = (price) => {
  if (!price) return '0.00'
  return price.toFixed(2)
}

// 格式化基差
const formatBasis = (basis) => {
  if (!basis) return '0.00'
  return basis > 0 ? `+${basis.toFixed(2)}` : basis.toFixed(2)
}

// 格式化基差率
const formatBasisRate = (rate) => {
  if (!rate) return '0.00%'
  return `${(rate * 100).toFixed(2)}%`
}

// 格式化价差
const formatSpread = (spread) => {
  if (!spread) return '0.00'
  return spread > 0 ? `+${spread.toFixed(2)}` : spread.toFixed(2)
}

// 获取基差样式类
const getBasisClass = (basis) => {
  if (basis > 0) return 'positive'
  if (basis < 0) return 'negative'
  return 'neutral'
}

// 获取基差率样式类
const getBasisRateClass = (rate) => {
  if (rate > 0) return 'positive'
  if (rate < 0) return 'negative'
  return 'neutral'
}

// 获取价差样式类
const getSpreadClass = (spread) => {
  if (spread > 0) return 'positive'
  if (spread < 0) return 'negative'
  return 'neutral'
}

// 获取品种卡片样式类
const getSymbolCardClass = (symbolData) => {
  if (!symbolData || !symbolData.contracts) return 'neutral'
  
  const contracts = symbolData.contracts
  const contangoCount = contracts.filter(c => c.is_contango).length
  const backwardationCount = contracts.length - contangoCount
  
  // 判断整体市场状态
  if (contangoCount > backwardationCount) {
    return 'full-contango'
  } else if (backwardationCount > contangoCount) {
    return 'full-backwardation'
  } else {
    return 'mixed'
  }
}

// 获取市场状态样式类
const getMarketStatusClass = (symbolData) => {
  if (!symbolData || !symbolData.contracts) return 'neutral'
  
  const contracts = symbolData.contracts
  const contangoCount = contracts.filter(c => c.is_contango).length
  const backwardationCount = contracts.length - contangoCount
  
  if (contangoCount > backwardationCount) return 'contango'
  if (backwardationCount > contangoCount) return 'backwardation'
  return 'mixed'
}

// 获取市场状态图标
const getMarketStatusIcon = (symbolData) => {
  if (!symbolData || !symbolData.contracts) return ArrowTrendingUpIcon
  
  const contracts = symbolData.contracts
  const contangoCount = contracts.filter(c => c.is_contango).length
  const backwardationCount = contracts.length - contangoCount
  
  if (contangoCount > backwardationCount) return ArrowTrendingUpIcon
  if (backwardationCount > contangoCount) return ArrowTrendingDownIcon
  return ChartBarIcon
}

// 获取市场状态文本
const getMarketStatusText = (symbolData) => {
  if (!symbolData || !symbolData.contracts) return '数据不足'
  
  const contracts = symbolData.contracts
  const contangoCount = contracts.filter(c => c.is_contango).length
  const backwardationCount = contracts.length - contangoCount
  
  if (contangoCount > backwardationCount) return '正向市场'
  if (backwardationCount > contangoCount) return '反向市场'
  return '混合市场'
}

// 获取合约行样式类
const getContractRowClass = (contract) => {
  return contract.is_contango ? 'contango-row' : 'backwardation-row'
}

// 获取合约状态样式类
const getContractStatusClass = (isContango) => {
  return isContango ? 'contango-status' : 'backwardation-status'
}

// 生成基差和基差率组合图表配置
const getBasisChartOption = (symbolData) => {
  if (!symbolData || !symbolData.contracts || symbolData.contracts.length === 0) {
    return {}
  }

  const contracts = symbolData.contracts.sort((a, b) => a.days_to_expiry - b.days_to_expiry)
  const contractCodes = contracts.map(c => c.ts_code.replace(symbolData.symbol, ''))
  const basisData = contracts.map(c => c.basis)
  const basisRateData = contracts.map(c => c.basis_rate * 100) // 转换为百分比

  // 根据主题设置颜色
  const textColor = appStore.isDarkMode ? '#e5e7eb' : '#374151'
  const tooltipBgColor = appStore.isDarkMode ? '#374151' : '#ffffff'
  const tooltipBorderColor = appStore.isDarkMode ? '#4b5563' : '#d1d5db'
  const axisLineColor = appStore.isDarkMode ? '#4b5563' : '#d1d5db'

  return {
    title: {
      text: '基差与基差率分析',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal',
        color: textColor
      },
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      backgroundColor: tooltipBgColor,
      borderColor: tooltipBorderColor,
      textStyle: {
        color: textColor
      },
      formatter: function(params) {
        let result = `<div style="font-weight: bold; margin-bottom: 5px;">${symbolData.symbol}${params[0].axisValue}</div>`
        params.forEach(param => {
          const value = param.seriesName === '基差率' ? `${param.value.toFixed(2)}%` : param.value.toFixed(2)
          result += `<div style="margin: 2px 0;">
            <span style="display: inline-block; width: 10px; height: 10px; background-color: ${param.color}; border-radius: 50%; margin-right: 5px;"></span>
            ${param.seriesName}: ${value}
          </div>`
        })
        return result
      }
    },
    legend: {
      data: ['基差', '基差率'],
      bottom: 0,
      textStyle: {
        fontSize: 12,
        color: textColor
      }
    },
    grid: {
      left: '10%',
      right: '10%',
      top: '20%',
      bottom: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: contractCodes,
      axisLabel: {
        fontSize: 11,
        rotate: 45,
        color: textColor
      },
      splitLine: {
        show: false
      },
      axisLine: {
        lineStyle: {
          color: axisLineColor
        }
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '基差',
        position: 'left',
        axisLabel: {
          formatter: '{value}',
          fontSize: 11,
          color: textColor
        },
        nameTextStyle: {
          fontSize: 11,
          color: textColor
        },
        splitLine: {
          show: false
        },
        axisLine: {
          lineStyle: {
            color: axisLineColor
          }
        }
      },
      {
        type: 'value',
        name: '基差率(%)',
        position: 'right',
        axisLabel: {
          formatter: '{value}%',
          fontSize: 11,
          color: textColor
        },
        nameTextStyle: {
          fontSize: 11,
          color: textColor
        },
        splitLine: {
          show: false
        },
        axisLine: {
          lineStyle: {
            color: axisLineColor
          }
        }
      }
    ],
    series: [
      {
        name: '基差',
        type: 'bar',
        yAxisIndex: 0,
        data: basisData,
        itemStyle: {
          color: function(params) {
            return params.value >= 0 ? '#ef4444' : '#22c55e'
          }
        },
        barWidth: '40%'
      },
      {
        name: '基差率',
        type: 'line',
        yAxisIndex: 1,
        data: basisRateData,
        lineStyle: {
          color: '#3b82f6',
          width: 2
        },
        itemStyle: {
          color: '#3b82f6'
        },
        symbol: 'circle',
        symbolSize: 6
      }
    ]
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchAnalysisData()
})
</script>

<style scoped>
.contango-analysis-panel {
  margin-bottom: 24px;
}
/* 卡片头部 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.dark .card-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-left {
  flex: 1;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.dark .section-title {
  color: #ffffff;
}

.section-icon {
  width: 20px;
  height: 20px;
  color: var(--el-color-primary);
}

.dark .section-icon {
  color: #3b82f6;
}

.section-subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.dark .section-subtitle {
  color: rgba(255, 255, 255, 0.7);
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.date-picker {
  width: 160px;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-icon {
  width: 16px;
  height: 16px;
}

/* 市场概览 */
.market-overview {
  padding: 20px 24px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.dark .market-overview {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.overview-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}

.dark .overview-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
}

.overview-card.contango .card-icon {
  background: rgba(239, 68, 68, 0.2);
}

.overview-card.backwardation .card-icon {
  background: rgba(34, 197, 94, 0.2);
}

.overview-card.total .card-icon {
  background: rgba(59, 130, 246, 0.2);
}

.overview-card.basis-rate .card-icon {
  background: rgba(168, 85, 247, 0.2);
}

.card-icon .icon {
  width: 20px;
  height: 20px;
  color: var(--el-text-color-primary);
}

.dark .card-icon .icon {
  color: #ffffff;
}

.card-content {
  flex: 1;
}

.card-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.dark .card-value {
  color: #ffffff;
}

.card-value.positive {
  color: #ef4444;
}

.card-value.negative {
  color: #22c55e;
}

.card-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.dark .card-label {
  color: rgba(255, 255, 255, 0.7);
}

/* 卡片主体 */
.card-body {
  padding: 24px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.dark .loading-text {
  color: rgba(255, 255, 255, 0.7);
}

.analysis-cards-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.analysis-card {
  background: var(--el-bg-color-page);
  border-radius: 12px;
  border: 1px solid var(--el-border-color-light);
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

/* 暗色主题下的特殊样式 */
.dark .analysis-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.analysis-card.full-contango {
  border-color: rgba(34, 197, 94, 0.3);
}

.analysis-card.full-backwardation {
  border-color: rgba(239, 68, 68, 0.3);
}

.analysis-card.mixed {
  border-color: rgba(251, 191, 36, 0.3);
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.dark .analysis-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.symbol-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.symbol-name {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.dark .symbol-name {
  color: #ffffff;
}

.symbol-code {
  padding: 4px 8px;
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.spot-index {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.dark .spot-index {
  color: rgba(255, 255, 255, 0.6);
}

.market-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
}

.market-status.contango {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.market-status.backwardation {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.market-status.mixed {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.status-icon {
  width: 16px;
  height: 16px;
}

/* 期限结构图表 */
.term-structure-chart {
  padding: 20px 24px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.dark .term-structure-chart {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

/* 基差图表容器 */
.basis-chart-container {
  padding: 20px 24px;
  border-bottom: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
}

.dark .basis-chart-container {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
}

.basis-chart-container .echarts {
  background: transparent !important;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-header h5 {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}

.dark .chart-header h5 {
  color: #ffffff;
}

.spot-price {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.dark .spot-price {
  color: rgba(255, 255, 255, 0.7);
}

.contracts-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.contract-item {
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 12px;
  border: 1px solid var(--el-border-color-light);
  transition: all 0.2s;
}

.dark .contract-item {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.contract-item.contango {
  border-left: 3px solid #ef4444;
}

.contract-item.backwardation {
  border-left: 3px solid #22c55e;
}

.contract-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.contract-code {
  font-size: 12px;
  color: var(--el-text-color-primary);
  font-family: monospace;
  font-weight: 600;
}

.dark .contract-code {
  color: #ffffff;
}

.contract-price {
  font-size: 14px;
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.dark .contract-price {
  color: #ffffff;
}

.basis-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.basis {
  color: var(--el-text-color-regular);
}

.dark .basis {
  color: rgba(255, 255, 255, 0.7);
}

.basis-rate {
  font-weight: 500;
}

.basis-rate.positive {
  color: #ef4444;
}

.basis-rate.negative {
  color: #22c55e;
}

/* 合约列表 */
.contracts-list {
  padding: 20px 24px;
}

.list-header {
  margin-bottom: 16px;
}

.list-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.dark .list-title {
  color: #ffffff;
}

.contracts-table {
  background: var(--el-bg-color);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--el-border-color-light);
}

.dark .contracts-table {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.table-header {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1fr 1fr 0.8fr 0.8fr;
  gap: 16px;
  padding: 12px 16px;
  background: var(--el-fill-color-light);
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-regular);
  text-transform: uppercase;
}

.dark .table-header {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.8);
}

.table-body {
  max-height: 300px;
  overflow-y: auto;
}

.table-row {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1fr 1fr 0.8fr 0.8fr;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  font-size: 13px;
  transition: background-color 0.2s;
}

.dark .table-row {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.table-row:hover {
  background: var(--el-fill-color-lighter);
}

.dark .table-row:hover {
  background: rgba(255, 255, 255, 0.05);
}

.table-row:last-child {
  border-bottom: none;
}

.table-row.contango-row {
  border-left: 3px solid #ef4444;
}

.table-row.backwardation-row {
  border-left: 3px solid #22c55e;
}

.col-contract {
  font-family: monospace;
  color: var(--el-text-color-primary);
}

.dark .col-contract {
  color: #ffffff;
}

.col-price {
  color: var(--el-text-color-primary);
  text-align: right;
}

.dark .col-price {
  color: #ffffff;
}

.col-basis {
  text-align: right;
  font-weight: 500;
}

.col-basis.positive {
  color: #ef4444;
}

.col-basis.negative {
  color: #22c55e;
}

.col-basis-rate {
  text-align: right;
  font-weight: 500;
}

.col-basis-rate.positive {
  color: #ef4444;
}

.col-basis-rate.negative {
  color: #22c55e;
}

.col-days {
  color: var(--el-text-color-regular);
  text-align: center;
}

.dark .col-days {
  color: rgba(255, 255, 255, 0.7);
}

.col-status {
  text-align: center;
  font-weight: 500;
}

.contango-status {
  color: #ef4444;
}

.backwardation-status {
  color: #22c55e;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: var(--el-text-color-placeholder);
  margin-bottom: 16px;
}

.dark .empty-icon {
  color: rgba(255, 255, 255, 0.4);
}

.empty-text {
  font-size: 16px;
  color: var(--el-text-color-regular);
  margin: 0 0 8px 0;
}

.dark .empty-text {
  color: rgba(255, 255, 255, 0.7);
}

.empty-hint {
  font-size: 14px;
  color: var(--el-text-color-placeholder);
  margin: 0;
}

.dark .empty-hint {
  color: rgba(255, 255, 255, 0.5);
}

/* 面板标题区域样式 */
.panel-title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.panel-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.dark .panel-title {
  color: #ffffff;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .contracts-list {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: space-between;
  }
  
  .overview-cards {
    grid-template-columns: 1fr;
  }
  
  .table-header,
  .table-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .table-header {
    display: none;
  }
  
  .table-row {
    display: flex;
    flex-direction: column;
    padding: 16px;
  }
  
  .table-row > span {
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
  }
  
  .table-row > span::before {
    content: attr(data-label);
    font-weight: 600;
    color: var(--el-text-color-regular);
  }
  
  .dark .table-row > span::before {
    color: rgba(255, 255, 255, 0.7);
  }
}
</style>