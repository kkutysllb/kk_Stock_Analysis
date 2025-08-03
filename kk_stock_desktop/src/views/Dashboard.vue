<template>
    <!-- 欢迎横幅 -->
    <div class="welcome-banner glass-effect glow-effect">
      <div class="banner-content">
        <div class="banner-left">
          <h1 class="welcome-title text-gradient">
            <SunIcon class="icon-size"></SunIcon>
            欢迎使用 KK 股票量化分析系统
          </h1>
          <p class="welcome-subtitle dynamic-greeting">{{ currentGreeting }}</p>
          <p class="welcome-back-message">{{ currentWelcomeBack }}</p>
          
          <!-- 智能分析 -->
          <div class="smart-analysis-inline">
            <component :is="smartAnalysisIcon" class="analysis-icon-mini" />
            <span class="analysis-title-mini">{{ smartAnalysisTitle }}</span>
            <span class="analysis-desc-mini">{{ smartAnalysisDescription }}</span>
          </div>
        </div>
        <div class="banner-right">
          <div class="market-indicators">
            <!-- 市场走势 -->
            <div class="market-status" :class="marketTrendClass">
              <div class="status-icon">
                <component :is="marketTrendIcon" class="icon-size" />
              </div>
              <div class="status-info">
                <div class="status-label">市场走势</div>
                <div class="status-value">{{ marketTrendText }}</div>
                <div class="status-detail">{{ marketTrendDetail }}</div>
              </div>
            </div>
            
            <!-- 市场情绪 -->
            <div class="market-sentiment" :class="marketSentimentClass">
              <div class="sentiment-icon">
                <component :is="marketSentimentIcon" class="icon-size" />
              </div>
              <div class="sentiment-info">
                <div class="sentiment-label">市场情绪</div>
                <div class="sentiment-value">{{ marketSentimentText }}</div>
                <div class="sentiment-detail">{{ marketSentimentDetail }}</div>
              </div>
            </div>
          </div>
          
          <!-- 指数详情 -->
          <div v-if="marketTrendData.keyIndices.length > 0" class="indices-detail">
            <div class="indices-header">主要指数表现</div>
            <div class="indices-list">
              <div 
                v-for="index in marketTrendData.keyIndices" 
                :key="index.name"
                class="index-item"
                :class="getIndexTrendClass(index.pct_chg)"
              >
                <div class="index-name">{{ index.name }}</div>
                <div class="index-change">
                  <component :is="getIndexIcon(index.pct_chg)" class="trend-icon" />
                  <span class="change-value">{{ formatIndexChange(index.pct_chg) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 核心指标卡片 -->
    <div class="metrics-grid">
      <!-- 投资组合总价值 -->
      <div class="metric-card card glow-effect" :class="getTrendClass(portfolioData.totalReturn)">
        <div class="metric-header">
          <div class="metric-icon">
            <CurrencyDollarIcon class="metric-icon-size" />
          </div>
          <div class="metric-trend" :class="getTrendClass(portfolioData.totalReturn)">
            <span class="trend-value">{{ formattedTotalReturnRate }}</span>
          </div>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ formattedTotalValue }}</div>
          <div class="metric-label">投资组合总价值</div>
          <div class="metric-detail">收益: {{ formattedTotalReturn }}</div>
        </div>
      </div>

      <!-- 每日收益 -->
      <div class="metric-card card glow-effect" :class="getTrendClass(portfolioData.dailyReturn)">
        <div class="metric-header">
          <div class="metric-icon">
            <ArrowTrendingUpIcon class="metric-icon-size" />
          </div>
          <div class="metric-trend" :class="getTrendClass(portfolioData.dailyReturn)">
            <span class="trend-value">{{ formattedDailyReturnRate }}</span>
          </div>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ formattedDailyReturn }}</div>
          <div class="metric-label">每日收益</div>
          <div class="metric-detail">今日盈亏</div>
        </div>
      </div>

      <!-- 持仓股数 -->
      <div class="metric-card card glow-effect info">
        <div class="metric-header">
          <div class="metric-icon">
            <BuildingLibraryIcon class="metric-icon-size" />
          </div>
          <div class="metric-trend info">
            <span class="trend-value">{{ portfolioData.holdingStocks }}</span>
          </div>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ portfolioData.holdingStocks }}</div>
          <div class="metric-label">持仓股数</div>
          <div class="metric-detail">当前持有</div>
        </div>
      </div>


      <!-- 可用资金 -->
      <div class="metric-card card glow-effect warning">
        <div class="metric-header">
          <div class="metric-icon">
            <CurrencyDollarIcon class="metric-icon-size" />
          </div>
          <div class="metric-trend warning">
            <span class="trend-value">{{ formattedAvailableCash }}</span>
          </div>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ formattedAvailableCash }}</div>
          <div class="metric-label">可用资金</div>
          <div class="metric-detail">可交易余额</div>
        </div>
      </div>
    </div>

    <!-- 市场情绪分析面板 -->
    <SentimentIndicator />

    <!-- 数据展示区域 - 主要板块数据分析 -->
    <div class="data-display-section">
      <div class="chart-section card">
        <div class="card-header">
          <div class="header-left">
            <div class="title-row">
              <h3 class="section-title">
                <ChartBarIcon class="icon-size"></ChartBarIcon>
                主要指数数据分析
              </h3>
              <div class="title-actions">
                <AskAIComponent :data-context="aiDataContext" />
              </div>
            </div>
            <div class="subtitle-row">
              <p class="section-subtitle">{{ sectorPeriodInfo }}</p>
              <!-- 日期范围选择器 -->
              <div class="date-range-selector">
                <el-select 
                  v-model="selectedDateRange" 
                  @change="onDateRangeChange"
                  size="small"
                  style="width: 180px;"
                  :placeholder="dateRangePlaceholder"
                >
                  <el-option
                    v-for="range in dateRangeOptions"
                    :key="range.value"
                    :label="range.label"
                    :value="range.value"
                  />
                </el-select>
                
                <!-- 自定义日期范围弹窗按钮 -->
                <el-button 
                  v-if="selectedDateRange === 'custom'"
                  size="small" 
                  type="primary" 
                  @click="showCustomDatePicker = true"
                  style="margin-left: 8px;"
                >
                  选择日期
                </el-button>
              </div>
              
              <!-- 自定义日期范围弹窗 -->
              <el-dialog
                v-model="showCustomDatePicker"
                title="选择自定义日期范围"
                width="500px"
                :before-close="handleCustomDateClose"
              >
                <div class="custom-date-content">
                  <div class="date-info">
                    <p>当前时间粒度：<strong>{{ periodDisplayName }}</strong></p>
                    <p class="date-tip">{{ customDateTip }}</p>
                  </div>
                  
                  <div class="date-picker-container">
                    <el-date-picker
                      v-model="tempCustomDateRange"
                      type="daterange"
                      range-separator="至"
                      start-placeholder="开始日期"
                      end-placeholder="结束日期"
                      format="YYYY-MM-DD"
                      value-format="YYYY-MM-DD"
                      :disabled-date="disabledDate"
                      size="default"
                      style="width: 100%;"
                    />
                  </div>
                  
                  <div class="date-preview" v-if="tempCustomDateRange && tempCustomDateRange[0] && tempCustomDateRange[1]">
                    <h4>预览信息</h4>
                    <p>选择范围：{{ tempCustomDateRange[0] }} 至 {{ tempCustomDateRange[1] }}</p>
                    <p>预计数据点：{{ getEstimatedDataPoints() }} 个</p>
                  </div>
                </div>
                
                <template #footer>
                  <div class="dialog-footer">
                    <el-button @click="handleCustomDateClose">取消</el-button>
                    <el-button 
                      type="primary" 
                      @click="confirmCustomDateRange"
                      :disabled="!tempCustomDateRange || !tempCustomDateRange[0] || !tempCustomDateRange[1]"
                    >
                      确定
                    </el-button>
                  </div>
                </template>
              </el-dialog>
            </div>
          </div>
          <div class="header-controls">
            <!-- 指数选择器 -->
            <div class="index-selector">
              <el-radio-group v-model="selectedSector" @change="onSectorChange" size="small">
                <el-radio-button 
                  v-for="sector in sectorConfig" 
                  :key="sector.code"
                  :value="sector.code"
                >
                  {{ sector.name }}
                </el-radio-button>
              </el-radio-group>
              <button class="more-button" @click="goToIndexAnalysis" title="查看指数分析详情">
                <EllipsisHorizontalIcon class="more-icon" />
                <span class="more-text">More</span>
              </button>
            </div>
            <!-- 时间选择器 -->
            <div class="time-selector">
              <el-radio-group v-model="activeSectorPeriod" @change="onSectorPeriodChange" size="default">
                <el-radio-button value="daily">日</el-radio-button>
                <el-radio-button value="weekly">周</el-radio-button>
                <el-radio-button value="monthly">月</el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </div>
        
        <div class="card-body">
          <div v-if="sectorLoading" class="loading-container">
            <div class="chart-loading-animation">
              <div class="loading-spinner"></div>
              <div class="loading-text">加载图表数据中...</div>
            </div>
          </div>
          
          <div v-else class="sector-chart-container">
            <div class="chart-container" ref="sectorChart" :key="sectorChartKey"></div>
            
            <div class="legend-section">
              <div class="legend-item">
                <span class="legend-line line-primary"></span>
                <span>{{ selectedSectorInfo?.name || '指数' }}价格走势</span>
              </div>
              <div class="legend-item">
                <span class="legend-bar" :style="{ background: selectedSectorInfo?.color || '#5470c6' }"></span>
                <span>{{ selectedSectorInfo?.name || '指数' }}成交量（红涨绿跌）</span>
              </div>
              <div class="legend-item">
                <span style="font-size: 12px; color: #888;">使用上方指数选择器切换显示</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 板块详情卡片 -->
        <div class="sector-cards">
          <div class="sector-cards-container">
            <el-card 
              v-for="sector in sectorData" 
              :key="sector.code"
              class="sector-card" 
              :class="{ 
                'positive': sector.pct_chg > 0, 
                'negative': sector.pct_chg < 0,
                'selected': selectedSector === sector.code
              }"
              @click="selectSector(sector.code)"
            >
              <div class="sector-header">
                <h4>{{ sector.name }}</h4>
                <span class="sector-code">{{ sector.code }}</span>
              </div>
              <div class="sector-metrics">
                <div class="metric">
                  <span class="label">指数</span>
                  <span class="value">{{ sector.index.toFixed(2) }}</span>
                </div>
                <div class="metric">
                  <span class="label">涨跌幅</span>
                  <span class="value change" :class="{ 'positive': sector.pct_chg > 0, 'negative': sector.pct_chg < 0 }">
                    {{ sector.pct_chg > 0 ? '+' : '' }}{{ sector.pct_chg.toFixed(2) }}%
                  </span>
                </div>
                <div class="metric">
                  <span class="label">涨跌点位</span>
                  <span class="value change" :class="{ 'positive': sector.change > 0, 'negative': sector.change < 0 }">
                    {{ sector.change > 0 ? '+' : '' }}{{ sector.change.toFixed(2) }}
                  </span>
                </div>
                <div class="metric">
                  <span class="label">成交量</span>
                  <span class="value">{{ formatSectorVolume(sector.volume) }}</span>
                </div>
                <div class="metric">
                  <span class="label">成交额</span>
                  <span class="value">{{ formatSectorAmount(sector.amount) }}</span>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </div>
    </div>

    <!-- 龙虎榜数据面板 -->
    <div class="function-section">
      <DragonTigerPanel />
    </div>

    <!-- 每日资金流分析面板 -->
    <div class="function-section">
      <MoneyFlowPanel />
    </div>

    <!-- 股指期货持仓分析面板 -->
    <div class="function-section">
      <FuturesOverviewPanel />
    </div>

    <!-- 股指期货正反向市场分析面板 -->
    <div class="function-section">
      <ContangoOverviewPanel />
    </div>

    <!-- 底部区域 -->
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { marketAPI } from '../api/market'
import { simulationApi } from '../api/simulation'
import * as echarts from 'echarts'
import { useAppStore } from '../stores/app'
import DragonTigerPanel from '../components/DragonTigerPanel.vue'
import { usePageRefresh, PAGE_REFRESH_CONFIG } from '../utils/usePageRefresh'
import MoneyFlowPanel from '../components/MoneyFlowPanel.vue'
import FuturesOverviewPanel from '../components/FuturesOverviewPanel.vue'
import ContangoOverviewPanel from '../components/ContangoOverviewPanel.vue'
import SentimentIndicator from '../components/SentimentIndicator.vue'
import AskAIComponent from '../components/AskAIComponent.vue'
import {
  SunIcon,
  ChartBarIcon,
  DocumentIcon,
  BoltIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusIcon,
  CurrencyDollarIcon,
  BuildingLibraryIcon,
  FaceSmileIcon,
  FaceFrownIcon,
  ExclamationTriangleIcon,
  HeartIcon,
  FireIcon,
  EllipsisHorizontalIcon
} from '@heroicons/vue/24/outline'

// 引入应用状态管理和路由
const appStore = useAppStore()
const router = useRouter()

// 统一刷新函数
const refreshDashboard = async () => {
  // console.log('开始刷新Dashboard数据...')
  try {
    // 重新加载所有数据
    await Promise.all([
      fetchMarketTrend(),
      loadSectorData()
    ])
    
    // 刷新选中板块数据
    await loadSelectedSectorData()
    
    // console.log('Dashboard数据刷新完成')
  } catch (error) {
    console.error('Dashboard数据刷新失败:', error)
  }
}

// 使用页面刷新组合函数
const { refresh } = usePageRefresh(
  refreshDashboard,
  PAGE_REFRESH_CONFIG.DASHBOARD.path,
  PAGE_REFRESH_CONFIG.DASHBOARD.event
)

// 真实API接口 - 使用后端接口
const api = {
  market: {
    getMarketTrend: async () => {
      try {
        // 获取市场概览数据分析大盘走势
        const response = await marketAPI.get('/index/market/overview')
        
        if (!response.success) {
          throw new Error('API返回失败状态')
        }
        
        const result = response
        
        // 分析主要指数涨跌情况判断市场走势
        const { major_indices, market_summary } = result.data
        
        // 计算加权平均涨跌幅（使用成交额作为权重）
        let totalWeightedChange = 0
        let totalAmount = 0
        
        // 主要关注上证指数、深证成指、创业板指的表现
        const keyIndices = major_indices.filter((index: any) => 
          ['000001.SH', '399001.SZ', '399006.SZ'].includes(index.ts_code)
        )
        
        keyIndices.forEach((index: any) => {
          const amount = index.data.amount || 0
          const pctChg = index.data.pct_chg || 0
          totalWeightedChange += pctChg * amount
          totalAmount += amount
        })
        
        const averageChange = totalAmount > 0 ? totalWeightedChange / totalAmount : 0
        
        // 根据综合涨跌幅判断趋势：-5%到5%为震荡，超出为明显上涨下跌
        let trend: 'up' | 'down' | 'neutral'
        if (averageChange > 5) {
          trend = 'up'
        } else if (averageChange < -5) {
          trend = 'down'
        } else {
          trend = 'neutral'
        }
        
        return {
          success: true,
          data: {
            trend,
            changePercent: Math.round(averageChange * 100) / 100,
            period: '近一个月',
            lastUpdate: new Date(),
            marketSummary: market_summary,
            keyIndices: keyIndices.map((index: any) => ({
              name: index.name,
              pct_chg: index.data.pct_chg || 0,
              amount: index.data.amount || 0
            }))
          },
          error: undefined
        }
      } catch (error) {
        console.error('获取市场走势失败:', error)
        throw error
      }
    }
  },
  portfolio: {
    getPortfolioData: async () => {
      // 模拟API调用延迟
      await new Promise(resolve => setTimeout(resolve, 300))
      
      const baseCapital = 2995000
      const totalReturnRate = (Math.random() - 0.3) * 50
      const totalReturn = baseCapital * (totalReturnRate / 100)
      const currentValue = baseCapital + totalReturn
      const dailyReturnRate = (Math.random() - 0.4) * 13
      const dailyReturn = currentValue * (dailyReturnRate / 100)
      
      return {
        success: true,
        data: {
          totalCapital: baseCapital,
          currentValue: Math.round(currentValue),
          totalReturn: Math.round(totalReturn),
          totalReturnRate: Math.round(totalReturnRate * 100) / 100,
          dailyReturn: Math.round(dailyReturn),
          dailyReturnRate: Math.round(dailyReturnRate * 100) / 100,
          holdingStocks: Math.floor(Math.random() * 50),
          availableCash: Math.round(baseCapital * 0.6), // 假设60%为可用现金
          lastUpdate: new Date()
        },
        error: undefined
      }
    }
  }
}

// 基础响应式数据
const loading = ref(false)
const currentTime = ref(new Date())

// 板块数据相关
const sectorLoading = ref(false)
const activeSectorPeriod = ref<'daily' | 'weekly' | 'monthly'>('daily')
const sectorChart = ref()
const sectorChartKey = ref(0)
const sectorData = ref<any[]>([])
const sectorChartData = ref<any[]>([])
const selectedSector = ref<string>('000001.SH') // 默认选择上证指数
const selectedSectorData = ref<any[]>([])

// 日期范围选择器相关
const selectedDateRange = ref<string>('recent_week') // 默认选择近一周
const customDateRange = ref<[string | null, string | null]>([null, null])
const showCustomDatePicker = ref(false)
const tempCustomDateRange = ref<[string | null, string | null]>([null, null])

// 板块配置 - 使用真实的指数代码
const sectorConfig = [
  { code: '000001.SH', name: '上证指数', color: '#3b82f6' },
  { code: '399001.SZ', name: '深证成指', color: '#10b981' },
  { code: '399006.SZ', name: '创业板指', color: '#f59e0b' },
  { code: '000688.SH', name: '科创50', color: '#ef4444' },
  { code: '899050.BJ', name: '北证50', color: '#8b5cf6' }
]

// 市场走势数据
const marketTrendData = ref({
  trend: 'neutral' as 'up' | 'down' | 'neutral',
  changePercent: 0,
  period: '近一个月',
  lastUpdate: new Date(),
  marketSummary: null as any,
  keyIndices: [] as any[]
})

// 投资组合数据 - 底金300万，整体保持正收益
const portfolioData = ref({
  totalCapital: 3000000, // 总盘资金300万
  currentValue: 0, // 当前总价值（示例正收益）
  totalReturn: 0, // 总收益（示例+21.5万）
  totalReturnRate: 0, // 总收益率（示例+7.17%）
  dailyReturn: 0, // 每日收益（示例+1.85万）
  dailyReturnRate: 0, // 每日收益率（示例+0.58%）
  holdingStocks: 0, // 持仓股数（示例37只）
  availableCash: 0, // 可用资金
  lastUpdate: new Date()
})

// 获取市场走势数据
const fetchMarketTrend = async () => {
  try {
    const response = await api.market.getMarketTrend()
    
            if (response.success && response.data) {
          marketTrendData.value = {
            trend: response.data.trend as 'up' | 'down' | 'neutral',
            changePercent: response.data.changePercent,
            period: response.data.period,
            lastUpdate: response.data.lastUpdate,
            marketSummary: response.data.marketSummary,
            keyIndices: response.data.keyIndices
          }
        } else {
          throw new Error(response.error || '获取数据失败')
        }
      } catch (error) {
        console.error('获取市场走势数据失败:', error)
        // // 使用模拟数据作为降级方案
        // const mockData = generateMockMarketData()
        // marketTrendData.value = {
        //   trend: mockData.trend as 'up' | 'down' | 'neutral',
        //   changePercent: mockData.changePercent,
        //   period: '近一个月',
        //   lastUpdate: new Date(),
        //   marketSummary: null,
        //   keyIndices: []
        // }
  }
}

// 获取投资组合数据
const fetchPortfolioData = async () => {
  try {
    // 使用模拟交易系统API获取真实数据
    const response = await simulationApi.getDashboardPortfolioData()
    
    if (response.success && response.data) {
      portfolioData.value = response.data
      // console.log('Dashboard数据更新成功:', response.data)
    } else {
      throw new Error(response.error || '获取模拟交易数据失败')
    }
  } catch (error) {
    console.error('获取投资组合数据失败:', error)
    // // 使用模拟数据作为降级方案
    // const mockData = generateMockPortfolioData()
    // portfolioData.value = mockData
  }
}

// // 生成模拟市场数据 - 体现涨多跌少
// const generateMockMarketData = () => {
//   // 涨多跌少：60%上涨，25%震荡，15%下跌
//   const random = Math.random()
//   let randomTrend
//   if (random < 0.6) {
//     randomTrend = 'up'
//   } else if (random < 0.85) {
//     randomTrend = 'neutral'
//   } else {
//     randomTrend = 'down'
//   }
  
//   let changePercent = 0
//   switch (randomTrend) {
//     case 'up':
//       changePercent = Math.random() * 8 + 1 // 1% 到 9%
//       break
//     case 'down':
//       changePercent = -(Math.random() * 4 + 1) // -1% 到 -5%
//       break
//     case 'neutral':
//       changePercent = (Math.random() - 0.5) * 2 // -1% 到 1%
//       break
//   }
  
//   return {
//     trend: randomTrend,
//     changePercent: Math.round(changePercent * 100) / 100
//   }
// }

// // 生成投资组合模拟数据 - 体现涨多跌少，保持正收益
// const generateMockPortfolioData = () => {
//   const baseCapital = 3000000 // 300万基础资金
  
//   // 总收益率保持正数，在2%到25%之间，体现涨多跌少
//   const totalReturnRate = Math.random() * 23 + 2 // 2% 到 25%
//   const totalReturn = baseCapital * (totalReturnRate / 100)
//   const currentValue = baseCapital + totalReturn
  
//   // 每日收益率偏向正数，在-1%到+3%之间，75%概率为正
//   const isDailyPositive = Math.random() > 0.25 // 75%概率正收益
//   const dailyReturnRate = isDailyPositive 
//     ? Math.random() * 3 // 0% 到 3%
//     : -Math.random() * 1 // 0% 到 -1%
//   const dailyReturn = currentValue * (dailyReturnRate / 100)
  
//   // 持仓股数在20到50之间，表示多元化投资
//   const holdingStocks = Math.floor(Math.random() * 31) + 20
  
//   // 预测准确率在75%到95%之间，体现系统专业性
//   return {
//     totalCapital: baseCapital,
//     currentValue: Math.round(currentValue),
//     totalReturn: Math.round(totalReturn),
//     totalReturnRate: Math.round(totalReturnRate * 100) / 100,
//     dailyReturn: Math.round(dailyReturn),
//     dailyReturnRate: Math.round(dailyReturnRate * 100) / 100,
//     holdingStocks,
//     lastUpdate: new Date()
//   }
// }

// 动态问候语配置
const greetingConfig = {
  morning: {
    time: [5, 11],
    greetings: [
      '🌅 早上好！新的一天，新的机遇等待着您',
      '☀️ 晨光正好，开始您的量化分析之旅吧',
      '🌤️ 美好的早晨，愿您今日收获满满',
      '🌞 早安！让我们一起探索市场的奥秘'
    ]
  },
  noon: {
    time: [11, 14],
    greetings: [
      '🌞 中午好！午间时光，数据分析正当时',
      '☀️ 正午阳光，照亮您的投资智慧',
      '🌤️ 午间好时光，继续您的量化探索',
      '🌅 中午时分，让数据为您指引方向'
    ]
  },
  afternoon: {
    time: [14, 18],
    greetings: [
      '🌤️ 下午好！午后时光，深度分析的好时机',
      '☀️ 下午阳光正好，数据洞察更清晰',
      '🌞 午后时光，让我们一起挖掘市场机会',
      '🌅 下午好！继续您的量化分析征程'
    ]
  },
  evening: {
    time: [18, 22],
    greetings: [
      '🌆 晚上好！夜幕降临，总结今日收获',
      '🌃 傍晚时分，回顾分析成果的时刻',
      '🌇 晚间好！让数据为明日策略护航',
      '🌉 夜色渐浓，智慧在数据中闪耀'
    ]
  },
  night: {
    time: [22, 5],
    greetings: [
      '🌙 夜深了，感谢您的辛勤分析',
      '⭐ 星光点点，数据洞察永不停歇',
      '🌌 深夜时光，专注成就卓越',
      '🌃 夜色中的坚持，明日必有收获'
    ]
  }
}

// 计算当前时段的问候语
const currentGreeting = computed(() => {
  const hour = currentTime.value.getHours()
  
  for (const [period, config] of Object.entries(greetingConfig)) {
    const [start, end] = config.time
    if ((start <= end && hour >= start && hour < end) || 
        (start > end && (hour >= start || hour < end))) {
      const randomIndex = Math.floor(Math.random() * config.greetings.length)
      return config.greetings[randomIndex]
    }
  }
  
  return '🎉 欢迎回到【KK 量化】，开启您的智能分析之旅'
})

// 欢迎回归语句
const welcomeBackMessages = [
  '欢迎回到【KK 量化】💎 您的专业量化分析伙伴',
  '再次相遇【KK 量化】🚀 让数据驱动您的投资决策',
  '回到【KK 量化】🎯 精准分析，智慧投资',
  '欢迎使用【KK 量化】⚡ 专业工具，助力成功',
  '【KK 量化】为您服务 🌟 数据洞察，价值发现'
]

const currentWelcomeBack = computed(() => {
  const index = Math.floor(Date.now() / (1000 * 60 * 30)) % welcomeBackMessages.length
  return welcomeBackMessages[index]
})

// 市场走势计算属性
const marketTrendClass = computed(() => {
  switch (marketTrendData.value.trend) {
    case 'up':
      return 'bull'
    case 'down':
      return 'bear'
    default:
      return 'neutral'
  }
})

const marketTrendIcon = computed(() => {
  switch (marketTrendData.value.trend) {
    case 'up':
      return ArrowTrendingUpIcon
    case 'down':
      return ArrowTrendingDownIcon
    default:
      return MinusIcon
  }
})

const marketTrendText = computed(() => {
  switch (marketTrendData.value.trend) {
    case 'up':
      return '上涨'
    case 'down':
      return '下跌'
    default:
      return '震荡'
  }
})

const marketTrendDetail = computed(() => {
  const percent = marketTrendData.value.changePercent
  const sign = percent > 0 ? '+' : ''
  const summary = marketTrendData.value.marketSummary
  
  if (summary) {
    const { rising_indices, falling_indices, total_indices } = summary
    return `${sign}${percent}% (${rising_indices}涨${falling_indices}跌)`
  } else {
    return `${sign}${percent}%`
  }
})

// 市场情绪计算属性
const marketSentimentClass = computed(() => {
  const sentiment = marketTrendData.value.marketSummary?.market_sentiment
  if (!sentiment) return 'neutral'
  
  switch (sentiment) {
    case '积极':
    case '乐观':
      return 'positive'
    case '谨慎':
    case '观望':
      return 'neutral'
    case '悲观':
    case '消极':
      return 'negative'
    default:
      return 'neutral'
  }
})

const marketSentimentIcon = computed(() => {
  const sentiment = marketTrendData.value.marketSummary?.market_sentiment
  if (!sentiment) return HeartIcon
  
  switch (sentiment) {
    case '积极':
    case '乐观':
      return FaceSmileIcon
    case '谨慎':
    case '观望':
      return ExclamationTriangleIcon
    case '悲观':
    case '消极':
      return FaceFrownIcon
    default:
      return HeartIcon
  }
})

const marketSentimentText = computed(() => {
  return marketTrendData.value.marketSummary?.market_sentiment || '中性'
})

const marketSentimentDetail = computed(() => {
  const summary = marketTrendData.value.marketSummary
  if (!summary) return ''
  
  const { total_indices, rising_indices, falling_indices } = summary
  return `${total_indices}只指数 ${rising_indices}涨${falling_indices}跌`
})

// 指数相关计算方法
const getIndexTrendClass = (pctChg: number) => {
  if (pctChg > 0) return 'index-up'
  if (pctChg < 0) return 'index-down'
  return 'index-neutral'
}

const getIndexIcon = (pctChg: number) => {
  if (pctChg > 0) return ArrowTrendingUpIcon
  if (pctChg < 0) return ArrowTrendingDownIcon
  return MinusIcon
}

const formatIndexChange = (pctChg: number) => {
  const sign = pctChg > 0 ? '+' : ''
  return `${sign}${pctChg.toFixed(2)}%`
}

// 智能分析计算属性 - 基于市场情绪和收益情况动态生成
const smartAnalysisIcon = computed(() => {
  const marketSentiment = marketTrendData.value.marketSummary?.market_sentiment
  const totalReturn = portfolioData.value.totalReturnRate
  const dailyReturn = portfolioData.value.dailyReturnRate
  
  // 根据收益情况和市场情绪选择图标
  if (totalReturn > 15 && dailyReturn > 2) {
    return FireIcon // 火热行情
  } else if (totalReturn > 8 && marketSentiment === '积极') {
    return FaceSmileIcon // 积极向上
  } else if (totalReturn > 0 && dailyReturn > 0) {
    return ArrowTrendingUpIcon // 稳步上涨
  } else if (dailyReturn < 0) {
    return ExclamationTriangleIcon // 谨慎观望
  } else {
    return HeartIcon // 平稳持有
  }
})

const smartAnalysisTitle = computed(() => {
  const marketSentiment = marketTrendData.value.marketSummary?.market_sentiment || '中性'
  const totalReturn = portfolioData.value.totalReturnRate
  const dailyReturn = portfolioData.value.dailyReturnRate
  const marketTrend = marketTrendData.value.trend
  
  // 根据综合情况生成标题
  if (totalReturn > 20) {
    return '🚀 投资表现卓越，收益领跑大盘'
  } else if (totalReturn > 15) {
    return '📈 组合表现优异，超越市场预期'
  } else if (totalReturn > 10) {
    return '💎 稳健增长态势，投资策略有效'
  } else if (totalReturn > 5) {
    return '🌟 投资收益稳定，市场表现良好'
  } else if (totalReturn > 0) {
    return '💰 保持正收益，投资方向正确'
  } else {
    return '🔍 市场波动调整，关注投资机会'
  }
})

const smartAnalysisDescription = computed(() => {
  const marketSentiment = marketTrendData.value.marketSummary?.market_sentiment || '中性'
  const totalReturn = portfolioData.value.totalReturnRate
  const dailyReturn = portfolioData.value.dailyReturnRate
  const marketTrend = marketTrendData.value.trend
  const holdings = portfolioData.value.holdingStocks
  
  const trendText = marketTrend === 'up' ? '上涨' : marketTrend === 'down' ? '下跌' : '震荡'
  
  // 生成个性化的分析描述
  let description = ''
  
  if (totalReturn > 15) {
    description = `当前投资组合表现卓越，总收益率达到${totalReturn.toFixed(2)}%，远超市场平均水平。`
    if (dailyReturn > 2) {
      description += `今日收益强劲，单日涨幅${dailyReturn.toFixed(2)}%，显示出强大的盈利能力。`
    } else if (dailyReturn > 0) {
      description += `今日保持正收益${dailyReturn.toFixed(2)}%，投资策略持续有效。`
    }
    description += `在当前市场${trendText}环境下，为您的${holdings}只持仓股票提供精准指导。`
  } else if (totalReturn > 8) {
    description = `投资组合运行良好，累计收益${totalReturn.toFixed(2)}%，展现出稳健的增长势头。`
    if (marketSentiment === '积极') {
      description += `市场情绪${marketSentiment}，配合当前${trendText}走势，为后续投资创造有利条件。`
    }
    description += `AI系统助您在${holdings}只股票的投资组合中把握每一次机会。`
  } else if (totalReturn > 3) {
    description = `投资组合保持稳定增长，收益率${totalReturn.toFixed(2)}%符合预期。`
    if (dailyReturn > 1) {
      description += `今日表现亮眼，获得${dailyReturn.toFixed(2)}%的单日收益。`
    }
    description += `在市场${trendText}的背景下，${holdings}只精选股票展现出良好的抗风险能力。`
  } else if (totalReturn > 0) {
    description = `投资组合维持正收益${totalReturn.toFixed(2)}%，在当前市场环境中表现稳健。`
    if (marketSentiment === '谨慎' || marketSentiment === '观望') {
      description += `面对市场${marketSentiment}情绪，我们的投资策略显示出良好的防御性。`
    }
    description += `通过AI算法精准分析，${holdings}只持仓股票布局合理，为未来增长奠定基础。`
  } else {
    description = `当前市场处于调整期，投资组合暂时承压。`
    description += `但我们的AI系统仍保持高水平分析，`
    description += `相信通过${holdings}只优质股票的合理配置，将在市场回暖时获得更好收益。`
  }
  
  return description
})

// 投资组合计算属性 - 显示具体数字，不使用"万"字
const formattedTotalValue = computed(() => {
  return portfolioData.value.currentValue.toLocaleString('zh-CN')
})

const formattedTotalReturn = computed(() => {
  const value = portfolioData.value.totalReturn
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toLocaleString('zh-CN')}`
})

const formatPercentage = (value: number): string => {
  if (value === undefined || value === null) return '0.00%'
  return `${(value * 100).toFixed(2)}%`
}

const formattedTotalReturnRate = computed(() => {
  return formatPercentage(portfolioData.value.totalReturnRate)
})

const formattedDailyReturn = computed(() => {
  const value = portfolioData.value.dailyReturn
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toLocaleString('zh-CN')}`
})

const formattedDailyReturnRate = computed(() => {
  return formatPercentage(portfolioData.value.dailyReturnRate)
})

const formattedAvailableCash = computed(() => {
  return portfolioData.value.availableCash?.toLocaleString('zh-CN') || '0'
})

const getTrendClass = (value: number) => {
  if (value > 0) return 'success'
  if (value < 0) return 'warning'
  return 'info'
}

// AI数据上下文
const selectedSectorInfo = computed(() => {
  return sectorConfig.find(s => s.code === selectedSector.value)
})

const aiDataContext = computed(() => {
  const selectedSectorInfo = sectorConfig.find(s => s.code === selectedSector.value)
  const selectedSectorStats = sectorData.value.find(s => s.code === selectedSector.value)
  
  // 统计数据
  const totalSectors = sectorData.value.length
  const positiveSectors = sectorData.value.filter(s => s.pct_chg > 0).length
  const negativeSectors = sectorData.value.filter(s => s.pct_chg < 0).length
  const neutralSectors = totalSectors - positiveSectors - negativeSectors
  
  // 计算历史数据统计
  const getHistoricalStats = (data: any[]) => {
    if (!data || data.length === 0) return null
    
    const pctChanges = data.map(item => item.pct_chg || 0)
    const volumes = data.map(item => item.volume || item.vol || 0)
    const amounts = data.map(item => item.amount || 0)
    
    return {
      dataPoints: data.length,
      priceRange: {
        min: Math.min(...data.map(item => item.close || 0)),
        max: Math.max(...data.map(item => item.close || 0)),
        latest: data[data.length - 1]?.close || 0
      },
      changeRange: {
        min: Math.min(...pctChanges),
        max: Math.max(...pctChanges),
        avg: pctChanges.reduce((sum, val) => sum + val, 0) / pctChanges.length
      },
      volumeStats: {
        min: Math.min(...volumes),
        max: Math.max(...volumes),
        avg: volumes.reduce((sum, val) => sum + val, 0) / volumes.length
      },
      amountStats: {
        min: Math.min(...amounts),
        max: Math.max(...amounts),
        total: amounts.reduce((sum, val) => sum + val, 0)
      }
    }
  }
  
  const historicalStats = getHistoricalStats(selectedSectorData.value)
  
  return {
    type: 'sector_analysis',
    title: '主要板块数据分析',
    period: activeSectorPeriod.value,
    dateRange: selectedDateRange.value,
    data: {
      selectedSector: {
        code: selectedSector.value,
        name: selectedSectorInfo?.name || '未知板块',
        color: selectedSectorInfo?.color || '#5470c6',
        stats: selectedSectorStats
      },
      allSectors: sectorData.value,
      historicalData: selectedSectorData.value,
      statistics: {
        totalSectors,
        positiveSectors,
        negativeSectors,
        neutralSectors,
        historical: historicalStats
      }
    },
    summary: `主要板块数据分析报告（${activeSectorPeriod.value === 'daily' ? '日线' : activeSectorPeriod.value === 'weekly' ? '周线' : '月线'}数据）：

## 当前选中板块
- 板块：${selectedSectorInfo?.name || '未知板块'}（${selectedSector.value}）
- 时间周期：${activeSectorPeriod.value === 'daily' ? '日线' : activeSectorPeriod.value === 'weekly' ? '周线' : '月线'}
- 数据范围：${selectedDateRange.value}

## 实时板块表现
${selectedSectorStats ? `
- 当前指数：${selectedSectorStats.index.toFixed(2)}
- 涨跌幅：${selectedSectorStats.pct_chg > 0 ? '+' : ''}${selectedSectorStats.pct_chg.toFixed(2)}%
- 涨跌点位：${selectedSectorStats.change > 0 ? '+' : ''}${selectedSectorStats.change.toFixed(2)}
- 成交量：${formatSectorVolume(selectedSectorStats.volume)}
- 成交额：${formatSectorAmount(selectedSectorStats.amount)}
` : '- 暂无实时数据'}

## 所有板块概览
- 总板块数：${totalSectors}个
- 上涨板块：${positiveSectors}个
- 下跌板块：${negativeSectors}个
- 平盘板块：${neutralSectors}个

### 各板块详情
${sectorData.value.map(sector => 
  `- ${sector.name}（${sector.code}）：${sector.index.toFixed(2)}，${sector.pct_chg > 0 ? '+' : ''}${sector.pct_chg.toFixed(2)}%，成交额${formatSectorAmount(sector.amount)}`
).join('\n')}

## 历史数据分析
${historicalStats ? `
- 历史数据点：${historicalStats.dataPoints}个
- 价格区间：${historicalStats.priceRange.min.toFixed(2)} - ${historicalStats.priceRange.max.toFixed(2)}
- 最新价格：${historicalStats.priceRange.latest.toFixed(2)}
- 涨跌幅统计：
  * 最大涨幅：${historicalStats.changeRange.max.toFixed(2)}%
  * 最大跌幅：${historicalStats.changeRange.min.toFixed(2)}%
  * 平均涨跌幅：${historicalStats.changeRange.avg.toFixed(2)}%
- 成交量统计：
  * 最大成交量：${formatSectorVolume(historicalStats.volumeStats.max)}
  * 最小成交量：${formatSectorVolume(historicalStats.volumeStats.min)}
  * 平均成交量：${formatSectorVolume(historicalStats.volumeStats.avg)}
- 成交额统计：
  * 最大成交额：${formatSectorAmount(historicalStats.amountStats.max)}
  * 最小成交额：${formatSectorAmount(historicalStats.amountStats.min)}
  * 累计成交额：${formatSectorAmount(historicalStats.amountStats.total)}
` : '- 暂无历史数据'}

## 技术分析要点
- 当前选中板块趋势：${selectedSectorStats?.pct_chg > 2 ? '强势上涨' : selectedSectorStats?.pct_chg > 0 ? '温和上涨' : selectedSectorStats?.pct_chg < -2 ? '明显下跌' : selectedSectorStats?.pct_chg < 0 ? '小幅下跌' : '横盘整理'}
- 市场整体情绪：${positiveSectors > negativeSectors ? '偏多' : positiveSectors < negativeSectors ? '偏空' : '中性'}
- 板块轮动状态：${positiveSectors > totalSectors * 0.6 ? '普涨格局' : negativeSectors > totalSectors * 0.6 ? '普跌格局' : '结构性分化'}

请基于以上完整的板块数据分析，提供投资建议和风险提示。`
  }
})

// 板块数据计算属性
const sectorPeriodInfo = computed(() => {
  switch (activeSectorPeriod.value) {
    case 'daily':
      return '近一周交易日数据'
    case 'weekly':
      return '近5周交易日数据'
    case 'monthly':
      return '近5个月交易日数据'
    default:
      return ''
  }
})

// 日期范围选择器相关计算属性
const dateRangeOptions = computed(() => {
  switch (activeSectorPeriod.value) {
    case 'daily':
      return [
        { label: '近3天', value: 'recent_3_days' },
        { label: '近一周', value: 'recent_week' },
        { label: '近两周', value: 'recent_2_weeks' },
        { label: '近一月', value: 'recent_month' },
        { label: '自定义', value: 'custom' }
      ]
    case 'weekly':
      return [
        { label: '近2周', value: 'recent_2_weeks' },
        { label: '近1个月', value: 'recent_month' },
        { label: '近3个月', value: 'recent_3_months' },
        { label: '近半年', value: 'recent_6_months' },
        { label: '自定义', value: 'custom' }
      ]
    case 'monthly':
      return [
        { label: '近3个月', value: 'recent_3_months' },
        { label: '近半年', value: 'recent_6_months' },
        { label: '近一年', value: 'recent_year' },
        { label: '近两年', value: 'recent_2_years' },
        { label: '自定义', value: 'custom' }
      ]
    default:
      return []
  }
})

const dateRangePlaceholder = computed(() => {
  switch (activeSectorPeriod.value) {
    case 'daily':
      return '选择日期范围'
    case 'weekly':
      return '选择周范围'
    case 'monthly':
      return '选择月份范围'
    default:
      return '选择时间范围'
  }
})

// 自定义日期选择器相关计算属性
const periodDisplayName = computed(() => {
  switch (activeSectorPeriod.value) {
    case 'daily':
      return '日粒度'
    case 'weekly':
      return '周粒度'
    case 'monthly':
      return '月粒度'
    default:
      return '未知粒度'
  }
})

const customDateTip = computed(() => {
  switch (activeSectorPeriod.value) {
    case 'daily':
      return '选择具体的开始和结束日期，系统将获取该期间内每日的数据'
    case 'weekly':
      return '选择日期范围，系统将按周汇总该期间的数据'
    case 'monthly':
      return '选择日期范围，系统将按月汇总该期间的数据'
    default:
      return '请选择日期范围'
  }
})

// 格式化板块成交额（统一显示为亿元，保留2位小数）
const formatSectorAmount = (amount: number): string => {
  // amount 已经是以元为单位，转换为亿元
  const amountInYi = amount / 1e8
  return `${amountInYi.toFixed(2)}亿元`
}

// 格式化板块成交量（volume 单位为手，优先显示亿手）
const formatSectorVolume = (volume: number): string => {
  if (volume >= 1e8) {
    return `${(volume / 1e8).toFixed(2)}亿手`
  } else if (volume >= 1e4) {
    return `${(volume / 1e4).toFixed(1)}万手`
  }
  return `${Math.round(volume)}手`
}

// // 从后端获取真实板块数据
// const fetchRealSectorData = async () => {
//   try {
//     // 使用真实的板块数据API
//     const response = await marketAPI.getSectorData()
    
//     if (response && response.success && response.data) {
//       return {
//         realSectors: response.data.sectors || [],
//         realChartData: response.data.chartData || []
//       }
//     }
    
//     throw new Error('获取板块数据失败')
//   } catch (error) {
//     console.error('获取真实板块数据失败:', error)
//     // 返回空数据而不是模拟数据
//     return {
//       realSectors: [],
//       realChartData: []
//     }
//   }
// }

// // 从后端获取选中板块的真实历史数据
// const fetchRealSelectedSectorData = async (sectorCode: string, period: 'daily' | 'weekly' | 'monthly') => {
//   try {
//     // 使用真实的板块历史数据API
//     const response = await marketAPI.getSectorDetail(sectorCode, period)
    
//     if (response && response.success && response.data) {
//       console.log(`获取${period}真实数据:`, response.data.history?.length || 0, '条记录')
//       return response.data.history || []
//     }
    
//     throw new Error('获取板块历史数据失败')
//   } catch (error) {
//     console.error('获取真实板块历史数据失败:', error)
//     // 返回空数组而不是模拟数据
//     return []
//   }
// }

// 获取板块数据
const fetchSectorData = async () => {
  try {
    // console.log('正在获取板块数据，时间粒度:', activeSectorPeriod.value)
    
    // 调用真实的板块数据API
    const sectorCodes = sectorConfig.map(s => s.code)
    
    // 并行获取实时数据和历史数据
    const [realTimeResponse, historyResponse] = await Promise.all([
      marketAPI.getSectorData(),
      marketAPI.getSectorHistory(
        sectorCodes, 
        activeSectorPeriod.value, 
        activeSectorPeriod.value === 'daily' ? 7 : activeSectorPeriod.value === 'weekly' ? 35 : 150
      )
    ])
    
    // console.log('实时数据响应:', realTimeResponse)
    // console.log('历史数据响应:', historyResponse)
    
    if (realTimeResponse.success && realTimeResponse.data) {
      // 处理实时数据 - 使用市场指数数据
      const responseData = realTimeResponse.data as any
      const realTimeData = responseData.data || responseData.indices || responseData
      const processedSectorData = sectorConfig.map(config => {
        const apiData = realTimeData.find((item: any) => item.ts_code === config.code)
        if (apiData && apiData.latest_data) {
          const latestData = apiData.latest_data
          return {
            code: config.code,
            name: config.name,
            index: latestData.close || 0,
            change: latestData.change || 0, // 涨跌点位数
            pct_chg: latestData.pct_chg || 0, // 涨跌幅百分比
            amount: latestData.amount || 0, // 保持原始单位（元），格式化时再转换
            volume: latestData.vol || 0, // 保持原始单位（手）
            volumeChange: 0 // 暂时使用0，如果API提供则使用真实值
          }
        } else {
          // 如果API没有返回该板块数据，使用默认值
          const indexValue = 3000 + Math.random() * 1000
          const changeValue = (Math.random() - 0.5) * 60 // 涨跌点位数
          const pctChgValue = (changeValue / indexValue) * 100 // 计算涨跌幅百分比
          return {
            code: config.code,
            name: config.name,
            index: indexValue,
            change: changeValue, // 涨跌点位数
            pct_chg: pctChgValue, // 涨跌幅百分比
            amount: (Math.random() * 50 + 10) * 1e8, // 生成50-60亿元的模拟数据（以元为单位）
            volume: (Math.random() * 1000 + 200) * 1e4, // 生成200-1200万手的模拟数据（以手为单位）
            volumeChange: (Math.random() - 0.5) * 40
          }
        }
      })
      
      sectorData.value = processedSectorData
    }
    
    if (historyResponse.success && historyResponse.data) {
      // 处理历史数据用于图表展示
      const historyData = historyResponse.data
      const chartData: any[] = []
      
      // 找出所有日期
      const allDates = new Set<string>()
      historyData.forEach((sectorHistory: any) => {
        if (sectorHistory.data && Array.isArray(sectorHistory.data)) {
          sectorHistory.data.forEach((item: any) => {
            allDates.add(item.trade_date || item.date)
          })
        }
      })
      
      // 按日期排序
      const sortedDates = Array.from(allDates).sort()
      
      // 构建图表数据
      sortedDates.forEach(date => {
        const dataPoint: any = { date }
        
        sectorConfig.forEach(config => {
          const sectorHistory = historyData.find((h: any) => h.code === config.code)
          if (sectorHistory && sectorHistory.data) {
            const dayData = sectorHistory.data.find((d: any) => (d.trade_date || d.date) === date)
            if (dayData) {
              dataPoint[`${config.name}_volume`] = (dayData.vol || dayData.volume || 0) / 1e8 // 转换为亿手便于图表显示
              dataPoint[`${config.name}_change`] = dayData.pct_chg || dayData.change_percent || 0
              dataPoint[`${config.name}_volumeChange`] = Math.random() * 40 - 20 // 暂时随机，如果API提供则使用真实值
            } else {
              // 默认值
              dataPoint[`${config.name}_volume`] = (5 + Math.random() * 3) / 100 // 转换为亿手
              dataPoint[`${config.name}_change`] = (Math.random() - 0.5) * 6
              dataPoint[`${config.name}_volumeChange`] = (Math.random() - 0.5) * 30
            }
          } else {
            // 默认值
            dataPoint[`${config.name}_volume`] = (5 + Math.random() * 3) / 100 // 转换为亿手
            dataPoint[`${config.name}_change`] = (Math.random() - 0.5) * 6
            dataPoint[`${config.name}_volumeChange`] = (Math.random() - 0.5) * 30
          }
        })
        
        chartData.push(dataPoint)
      })
      
      sectorChartData.value = chartData
      // console.log('成功处理板块数据，图表数据点数量:', chartData.length)
      return true
    }
    
    console.warn('API响应无效，使用模拟数据')
    return false
    
  } catch (error) {
    console.error('板块API调用失败:', error)
    return false
  }
}

// 添加一个变量来存储图表实例和resize事件处理函数
const chartInstance = ref<echarts.ECharts | null>(null)
const chartResizeHandler = ref<(() => void) | null>(null)
const chartResizeObserver = ref<ResizeObserver | null>(null)
const visibilityHandler = ref<(() => void) | null>(null)

// 初始化板块图表 - 显示选中指数的分析图表
const initSectorChart = () => {
  // console.log('初始化图表，sectorChart.value:', sectorChart.value)
  // console.log('selectedSectorData.value.length:', selectedSectorData.value.length)
  
  // 使用requestAnimationFrame确保DOM已经渲染
  requestAnimationFrame(() => {
    // 再使用nextTick确保Vue更新已完成
    nextTick(() => {
      if (!sectorChart.value) {
        console.error('图表容器DOM元素不存在')
        return
      }
      
      // 检查容器尺寸
      const containerRect = sectorChart.value.getBoundingClientRect()
      if (containerRect.width === 0 || containerRect.height === 0) {
        console.error('图表容器尺寸为0，无法渲染图表')
        // 如果容器尺寸为0，延迟再试一次
        setTimeout(() => initSectorChart(), 200)
        return
      }
      
      // 如果已经存在图表实例，先销毁它
      if (chartInstance.value) {
        chartInstance.value.dispose()
        chartInstance.value = null
      }
      
      // 如果存在之前的resize处理函数，先移除它
      if (chartResizeHandler.value) {
        window.removeEventListener('resize', chartResizeHandler.value)
        chartResizeHandler.value = null
      }
      
      // 如果存在之前的ResizeObserver，先断开连接
      if (chartResizeObserver.value) {
        chartResizeObserver.value.disconnect()
        chartResizeObserver.value = null
      }
      
      // 如果存在之前的可见性变化处理函数，先移除它
      if (visibilityHandler.value) {
        document.removeEventListener('visibilitychange', visibilityHandler.value)
        visibilityHandler.value = null
      }

      if (selectedSectorData.value.length === 0) {
        console.error('选中板块数据为空')
        return
      }

      // console.log('开始初始化ECharts...')
      // 先检查是否已有实例，避免重复初始化
  const existingInstance = echarts.getInstanceByDom(sectorChart.value)
  if (existingInstance) {
    existingInstance.dispose()
  }
  const chart = echarts.init(sectorChart.value)
      chartInstance.value = chart // 保存图表实例引用
      
      // 显示加载动画
      chart.showLoading({
        text: '图表数据加载中...',
        color: '#3b82f6',
        textColor: '#888',
        maskColor: 'rgba(255, 255, 255, 0.2)',
        zlevel: 0
      })
      
      // 获取选中指数的配置信息
      const selectedConfig = sectorConfig.find(config => config.code === selectedSector.value)
      const sectorName = selectedConfig?.name || '指数'
      
      // 准备数据
      const dates = selectedSectorData.value.map(item => {
        // 处理API返回的日期格式：20250627 -> 2025-06-27
        let dateStr = item.date
        if (typeof dateStr === 'string' && dateStr.length === 8) {
          // 格式：YYYYMMDD -> YYYY-MM-DD
          dateStr = `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`
        }
        
        const date = new Date(dateStr)
        if (isNaN(date.getTime())) {
          console.error('无效日期:', item.date, '->', dateStr)
          return item.date // 返回原始日期作为降级
        }
        
        if (activeSectorPeriod.value === 'monthly') {
          return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
        } else if (activeSectorPeriod.value === 'weekly') {
          const weekNum = Math.ceil(date.getDate() / 7)
          return `${date.getMonth() + 1}月第${weekNum}周`
        } else {
          return `${date.getMonth() + 1}-${String(date.getDate()).padStart(2, '0')}`
        }
      })

      // 提取数据
      const volumeData = selectedSectorData.value.map(item => {
        const volume = item.volume || 0
        return volume / 1e8 // 转换为亿手，但确保数值合理
      })
      const pctChgData = selectedSectorData.value.map(item => item.pct_chg || 0)
      
      // 计算成交量变化幅度
      const volumeChangeData = selectedSectorData.value.map((item, index) => {
        if (index === 0) return 0
        const prevVolume = selectedSectorData.value[index - 1].volume || 0
        return prevVolume > 0 ? ((item.volume - prevVolume) / prevVolume) * 100 : 0
      })
      
      // console.log('图表数据:', {
      //   selectedSectorDataSample: selectedSectorData.value.slice(0, 3),
      //   dates,
      //   volumeData: volumeData.slice(0, 3),
      //   pctChgData: pctChgData.slice(0, 3),
      //   volumeChangeData: volumeChangeData.slice(0, 3),
      //   sectorName
      // })

      // 根据主题设置文字颜色
      const textColor = appStore.isDarkMode ? '#ffffff' : '#333333'
      const tooltipBgColor = appStore.isDarkMode ? 'rgba(0,0,0,0.8)' : 'rgba(255,255,255,0.9)'
      const axisLineColor = appStore.isDarkMode ? '#555555' : '#cccccc'
      const gridLineColor = appStore.isDarkMode ? '#333333' : '#f0f0f0'

      // 创建经典价量分析图配置
      const option = {
        title: {
          text: `${sectorName} - ${sectorPeriodInfo.value}`,
          left: 'center',
          textStyle: {
            color: textColor,
            fontSize: 16
          }
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: tooltipBgColor,
          borderColor: appStore.isDarkMode ? '#555555' : '#cccccc',
          borderWidth: 1,
          textStyle: {
            color: textColor
          },
          formatter: function(params: any[]) {
            const dataIndex = params[0].dataIndex
            const data = selectedSectorData.value[dataIndex]
            if (!data) return ''
            
            const pctChange = data.pct_chg || 0
            const changeColor = pctChange >= 0 ? '#ff4757' : '#2ed573'
            const changeSign = pctChange >= 0 ? '+' : ''
            
            // 根据时间周期计算成交量变化幅度
            let volumeChange = 0
            let volumeChangeLabel = ''
            if (dataIndex > 0) {
              const current = data.volume
              const previous = selectedSectorData.value[dataIndex - 1].volume
              if (previous > 0) {
                volumeChange = ((current - previous) / previous) * 100
              }
              
              // 根据时间粒度设置标签
              switch (activeSectorPeriod.value) {
                case 'daily':
                  volumeChangeLabel = '量变幅度（日环比）'
                  break
                case 'weekly':
                  volumeChangeLabel = '量变幅度（周环比）'
                  break
                case 'monthly':
                  volumeChangeLabel = '量变幅度（月环比）'
                  break
                default:
                  volumeChangeLabel = '量变幅度'
              }
            }
            
            // 根据时间周期计算均量变化幅度
            let volumeVsMA = 0
            let volumeVsMALabel = ''
            let requiredPeriods = 0
            
            switch (activeSectorPeriod.value) {
              case 'daily':
                requiredPeriods = 20 // 20日均量
                volumeVsMALabel = '相对20日均量'
                break
              case 'weekly':
                requiredPeriods = 8  // 8周均量（约2个月）
                volumeVsMALabel = '相对8周均量'
                break
              case 'monthly':
                requiredPeriods = 6  // 6月均量（半年）
                volumeVsMALabel = '相对6月均量'
                break
              default:
                requiredPeriods = 20
                volumeVsMALabel = '相对均量'
            }
            
            if (dataIndex >= requiredPeriods - 1) {
              let sum = 0
              for (let i = dataIndex - requiredPeriods + 1; i <= dataIndex; i++) {
                sum += selectedSectorData.value[i].volume
              }
              const currentMA = sum / requiredPeriods
              if (currentMA > 0) {
                volumeVsMA = ((data.volume - currentMA) / currentMA) * 100
              }
            }
            
            const volumeChangeColor = volumeChange >= 0 ? '#ff4757' : '#2ed573'
            const volumeChangeSign = volumeChange >= 0 ? '+' : ''
            const volumeVsMAColor = volumeVsMA >= 0 ? '#ff4757' : '#2ed573'
            const volumeVsMASign = volumeVsMA >= 0 ? '+' : ''
            
            // 根据时间粒度显示不同的单位
            let volumeUnit = ''
            let amountUnit = ''
            switch (activeSectorPeriod.value) {
              case 'daily':
                volumeUnit = '亿手'
                amountUnit = '亿元'
                break
              case 'weekly':
                volumeUnit = '亿手/周'
                amountUnit = '亿元/周'
                break
              case 'monthly':
                volumeUnit = '亿手/月'
                amountUnit = '亿元/月'
                break
              default:
                volumeUnit = '亿手'
                amountUnit = '亿元'
            }
            
            return `
              <div style="font-weight: 600; margin-bottom: 8px;">${params[0].axisValue}</div>
              <div>指数点位：${data.close?.toFixed(2)}</div>
              <div style="color: ${changeColor};">涨跌幅：${changeSign}${pctChange.toFixed(2)}%</div>
              <div>成交量：${(data.volume / 1e8).toFixed(2)}${volumeUnit}</div>
              <div>成交额：${(data.amount / 1e8).toFixed(2)}${amountUnit}</div>
              ${dataIndex > 0 ? `<div style="color: ${volumeChangeColor};">${volumeChangeLabel}：${volumeChangeSign}${volumeChange.toFixed(2)}%</div>` : ''}
              ${dataIndex >= requiredPeriods - 1 ? `<div style="color: ${volumeVsMAColor};">${volumeVsMALabel}：${volumeVsMASign}${volumeVsMA.toFixed(2)}%</div>` : ''}
            `
          }
        },
        legend: {
          data: [`${sectorName}指数`, `${sectorName}成交量`],
          top: 30,
          textStyle: {
            color: textColor
          }
        },
        grid: [
          {
            left: '8%',
            right: '8%',
            top: '20%',
            height: '60%',
            containLabel: true
          },
          {
            left: '8%',
            right: '8%',
            top: '85%',
            height: '12%',
            containLabel: true
          }
        ],
        xAxis: [
          {
            type: 'category',
            data: dates,
            axisLabel: {
              color: textColor,
              fontSize: 12
            },
            axisLine: {
              lineStyle: { color: axisLineColor }
            },
            splitLine: {
              show: false
            }
          },
          {
            type: 'category',
            gridIndex: 1,
            data: dates,
            axisLabel: {
              color: textColor,
              fontSize: 12
            },
            axisLine: {
              lineStyle: { color: axisLineColor }
            },
            splitLine: {
              show: false
            }
          }
        ],
        yAxis: [
          {
            type: 'value',
            name: '指数点位',
            axisLabel: {
              color: textColor,
              formatter: function(value: number) {
                return value.toFixed(0)
              }
            },
            axisLine: {
              lineStyle: { color: axisLineColor }
            },
            nameTextStyle: {
              color: textColor
            },
            splitLine: {
              lineStyle: { 
                color: gridLineColor,
                type: 'dashed'
              }
            }
          },
          {
            type: 'value',
            gridIndex: 1,
            name: '成交量(亿手)',
            axisLabel: {
              color: textColor,
              formatter: function(value: number) {
                return value.toFixed(1)
              }
            },
            axisLine: {
              lineStyle: { color: axisLineColor }
            },
            nameTextStyle: {
              color: textColor
            },
            splitLine: {
              lineStyle: { 
                color: gridLineColor,
                type: 'dashed'
              }
            }
          }
        ],
        series: [
          {
            name: `${sectorName}指数`,
            type: 'line',
            data: selectedSectorData.value.map(item => item.close),
            lineStyle: {
              width: 2,
              color: function(params: any) {
                // 根据整体趋势动态着色
                const firstValue = selectedSectorData.value[0]?.close || 0
                const lastValue = selectedSectorData.value[selectedSectorData.value.length - 1]?.close || 0
                return lastValue >= firstValue ? '#ff4757' : '#2ed573'
              }
            },
            itemStyle: {
              color: function(params: any) {
                const dataIndex = params.dataIndex
                const currentData = selectedSectorData.value[dataIndex]
                const pctChange = currentData?.pct_chg || 0
                return pctChange >= 0 ? '#ff4757' : '#2ed573'
              }
            },
            symbol: 'circle',
            symbolSize: 4,
            areaStyle: {
              color: {
                type: 'linear',
                x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
                  { offset: 1, color: 'rgba(59, 130, 246, 0.05)' }
                ]
              }
            },
            animationDelay: function(idx: number) {
              return idx * 5;
            }
          },
          {
            name: `${sectorName}成交量`,
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumeData,
            itemStyle: {
              color: function(params: any) {
                const dataIndex = params.dataIndex
                const currentData = selectedSectorData.value[dataIndex]
                const pctChange = currentData?.pct_chg || 0
                return pctChange >= 0 ? '#ff4757' : '#2ed573'
              }
            },
            barWidth: '60%',
            animationDelay: function(idx: number) {
              return idx * 5 + 100;
            }
          }
        ],
        // 添加全局动画配置
        animation: true,
        animationThreshold: 1000,
        animationDuration: 1000,
        animationEasing: 'cubicOut' as const,
        animationDurationUpdate: 300,
        animationEasingUpdate: 'cubicInOut' as const
      }

      // console.log('设置图表配置:', option)
      try {
        // 延迟一点设置选项，让加载动画显示一会儿
        setTimeout(() => {
          chart.hideLoading()
          chart.setOption(option)
          // console.log('图表配置设置成功')    
        }, 300)
      } catch (error) {
        console.error('设置图表配置失败:', error)
        chart.hideLoading()
        return
      }
      
      // 创建响应式调整处理函数
      const resizeHandler = () => {
        if (chartInstance.value) {
          // console.log('窗口大小变化，调整图表尺寸')  
          chartInstance.value.resize()
        }
      }
      
      // 保存resize处理函数引用，便于后续清理
      chartResizeHandler.value = resizeHandler
      
      // 添加窗口大小变化事件监听
      window.addEventListener('resize', resizeHandler)
      
      // 使用ResizeObserver监听容器大小变化
      try {
        const observer = new ResizeObserver(() => {
          if (chartInstance.value) {
            // console.log('图表容器大小变化，调整图表尺寸')
            chartInstance.value.resize()
          }
        })
        
        observer.observe(sectorChart.value)
        chartResizeObserver.value = observer
        // console.log('ResizeObserver已设置')
      } catch (error) {
        console.error('ResizeObserver设置失败:', error)
        // 如果ResizeObserver不可用，依赖window resize事件
      }
      
      // 监听页面可见性变化，在页面重新变为可见时刷新图表
      const handleVisibilityChange = () => {
        if (document.visibilityState === 'visible' && chartInstance.value) {
          // console.log('页面重新变为可见，刷新图表')
          chartInstance.value.resize()
        }
      }
      
      document.addEventListener('visibilitychange', handleVisibilityChange)
      visibilityHandler.value = handleVisibilityChange
      
      // console.log('图表初始化完成')
    })
  })
}

// 加载板块数据（用于卡片显示）
const loadSectorData = async () => {
  // console.log('开始加载板块数据...')  
  try {
    // console.log('开始获取真实API板块数据...')
    const isRealDataLoaded = await fetchSectorData()
    
    if (!isRealDataLoaded) {
      console.error('真实API数据加载失败')
      throw new Error('无法获取真实的板块数据')
    }
    console.log('板块数据加载完成，数据条数:', sectorData.value.length)
  } catch (error) {
    console.error('板块数据加载失败:', error)
    console.error('错误详情:', error)
    
    // 清空数据，不使用模拟数据
    sectorData.value = []
  }
}

// 加载选中板块的详细数据（用于图表显示）
const loadSelectedSectorData = async () => {
  // 显示加载动画
  sectorLoading.value = true
  
  try {
    console.log('加载选中板块数据:', selectedSector.value, '时间粒度:', activeSectorPeriod.value)
    console.log('当前日期范围选择:', selectedDateRange.value)
    console.log('自定义日期范围:', customDateRange.value)
    
    let historyResponse
    
    // 如果是自定义日期范围，使用日期范围查询
    if (selectedDateRange.value === 'custom' && customDateRange.value[0] && customDateRange.value[1]) {
      const startDate = customDateRange.value[0].replace(/-/g, '') // 转换为YYYYMMDD格式
      const endDate = customDateRange.value[1].replace(/-/g, '')   // 转换为YYYYMMDD格式
      
      // console.log(`使用自定义日期范围查询: ${startDate} 至 ${endDate}`)
      
      historyResponse = await marketAPI.getSectorHistory(
        [selectedSector.value],
        activeSectorPeriod.value,
        undefined, // limit参数不需要
        startDate,
        endDate
      )
    } else {
      // 使用智能交易日历获取选中板块的历史数据，根据日期范围选择器设置limit
      const limit = getDateRangeLimit()
      // console.log(`使用limit查询: ${limit}`)
      
      historyResponse = await marketAPI.getSectorHistory(
        [selectedSector.value],
        activeSectorPeriod.value,
        limit
      )
    }
    
    // console.log('API响应详情:', historyResponse)
    
    if (historyResponse.success && historyResponse.data && historyResponse.data.length > 0) {
      const sectorHistoryData = historyResponse.data[0] // 获取第一个（也是唯一的）板块数据
      // console.log('板块历史数据:', sectorHistoryData)
      
      const historyData = sectorHistoryData.data
      // console.log('历史数据明细:', historyData?.slice(0, 3)) // 只打印前3条    
      
      // 处理数据用于图表展示
      const chartData = historyData.map((item: any) => ({
        date: item.trade_date,   // API返回格式：20250627
        close: item.close,
        open: item.open,
        high: item.high,
        low: item.low,
        volume: item.vol,        // 真实数据：单位为手
        amount: item.amount,     // 真实数据：单位为元
        change: item.change || 0,
        pct_chg: item.pct_change || item.pct_chg || 0  // 修复字段名：API返回pct_change
      }))
      
      selectedSectorData.value = chartData.reverse() // 反转数组，最早的数据在前面
      // console.log('成功加载选中板块数据，数据点数量:', chartData.length)
      // console.log('处理后的图表数据样例:', chartData.slice(0, 3))
      
      // 延迟一点隐藏加载动画，让用户感知到加载过程
      setTimeout(() => {
        // 数据加载完成后初始化图表
        initSectorChart()
        // 最后隐藏加载动画
        sectorLoading.value = false
      }, 500)
    } else {
      console.error('API数据无效:', {
        success: historyResponse.success,
        hasData: !!historyResponse.data,
        dataLength: historyResponse.data?.length,
        error: historyResponse.error
      })
      throw new Error('API返回的数据无效')
    }
  } catch (error) {
    console.error('选中板块数据加载失败:', error)
    console.error('错误详情:', error)
    
    // 清空数据并显示错误状态
    selectedSectorData.value = []
    
    // 延迟一点隐藏加载动画，让用户感知到加载过程
    setTimeout(() => {
      // 仍然尝试初始化图表，这样可以显示空状态
      initSectorChart()
      // 最后隐藏加载动画
      sectorLoading.value = false
    }, 500)
  }
}

// 添加一个立即加载并渲染图表的方法
const loadAndRenderChart = async () => {
  // console.log('开始立即加载并渲染图表...')
  try {
    // 显示加载动画
    sectorLoading.value = true
    
    // 先加载板块数据
    await loadSectorData()
    
    // 然后加载选中板块的详细数据并渲染图表
    // 这里不需要设置sectorLoading.value = true，因为loadSelectedSectorData会处理
    await loadSelectedSectorData()
    
    // console.log('图表加载完成')
  } catch (error) {
    console.error('图表加载失败:', error)
    sectorLoading.value = false
  }
}

// 选择板块
const selectSector = (sectorCode: string) => {
  selectedSector.value = sectorCode
  loadSelectedSectorData()
}

// 指数选择切换
const onSectorChange = () => {
  sectorChartKey.value++
  loadSelectedSectorData()
}

// 时间粒度切换
const onSectorPeriodChange = () => {
  sectorChartKey.value++
  // 重置日期范围选择为默认值
  resetDateRangeSelection()
  loadSelectedSectorData()
}

// 日期范围切换
const onDateRangeChange = () => {
  // console.log('日期范围切换:', selectedDateRange.value)
  sectorChartKey.value++
  loadSelectedSectorData()
}

// 重置日期范围选择
const resetDateRangeSelection = () => {
  switch (activeSectorPeriod.value) {
    case 'daily':
      selectedDateRange.value = 'recent_week'
      break
    case 'weekly':
      selectedDateRange.value = 'recent_month'
      break
    case 'monthly':
      selectedDateRange.value = 'recent_6_months'
      break
    default:
      selectedDateRange.value = 'recent_week'
  }
}

// 根据日期范围计算API请求的limit参数
const getDateRangeLimit = (): number => {
  // 如果是自定义日期范围，使用预估的数据点数量
  if (selectedDateRange.value === 'custom' && customDateRange.value[0] && customDateRange.value[1]) {
    const startDate = new Date(customDateRange.value[0])
    const endDate = new Date(customDateRange.value[1])
    const diffTime = Math.abs(endDate.getTime() - startDate.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    switch (activeSectorPeriod.value) {
      case 'daily':
        return Math.max(Math.floor(diffDays * 5 / 7), 1) // 交易日数量
      case 'weekly':
        return Math.max(Math.ceil(diffDays / 7), 1)
      case 'monthly':
        return Math.max(Math.ceil(diffDays / 30), 1)
      default:
        return Math.max(diffDays, 1)
    }
  }
  
  // 预设的日期范围选项
  switch (selectedDateRange.value) {
    // 日粒度
    case 'recent_3_days':
      return 3
    case 'recent_week':
      return 7
    case 'recent_2_weeks':
      return 14
    case 'recent_month':
      return 30
    
    // 周粒度
    case 'recent_2_weeks':
      return 2
    case 'recent_month':
      return 4
    case 'recent_3_months':
      return 12
    case 'recent_6_months':
      return 24
    
    // 月粒度
    case 'recent_3_months':
      return 3
    case 'recent_6_months':
      return 6
    case 'recent_year':
      return 12
    case 'recent_2_years':
      return 24
    
    default:
      // 默认值
      return activeSectorPeriod.value === 'daily' ? 7 : 
             activeSectorPeriod.value === 'weekly' ? 4 : 6
  }
}

// 自定义日期范围相关方法
const disabledDate = (time: Date) => {
  // 禁用未来的日期
  return time.getTime() > Date.now()
}

const getEstimatedDataPoints = (): number => {
  if (!tempCustomDateRange.value || !tempCustomDateRange.value[0] || !tempCustomDateRange.value[1]) {
    return 0
  }
  
  const startDate = new Date(tempCustomDateRange.value[0])
  const endDate = new Date(tempCustomDateRange.value[1])
  const diffTime = Math.abs(endDate.getTime() - startDate.getTime())
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  switch (activeSectorPeriod.value) {
    case 'daily':
      // 假设每周5个交易日
      return Math.floor(diffDays * 5 / 7)
    case 'weekly':
      // 每周1个数据点
      return Math.ceil(diffDays / 7)
    case 'monthly':
      // 每月1个数据点
      return Math.ceil(diffDays / 30)
    default:
      return diffDays
  }
}

const handleCustomDateClose = () => {
  showCustomDatePicker.value = false
  tempCustomDateRange.value = [null, null]
}

const confirmCustomDateRange = () => {
  if (tempCustomDateRange.value && tempCustomDateRange.value[0] && tempCustomDateRange.value[1]) {
    customDateRange.value = [...tempCustomDateRange.value]
    showCustomDatePicker.value = false
    // console.log('确认自定义日期范围:', customDateRange.value)
    
    // 重新加载数据
    sectorChartKey.value++
    loadSelectedSectorData()
  }
}

// 跳转到指数分析详情页面
const goToIndexAnalysis = () => {
  // 跳转到指数看板页面，并传递当前选中的指数代码和时间粒度
  router.push({
    path: '/analysis/indices',
    query: {
      code: selectedSector.value,
      period: activeSectorPeriod.value
    }
  })
}

// 更新时间
const updateTime = () => {
  currentTime.value = new Date()
}

// 监听主题变化，重新渲染图表
watch(() => appStore.isDarkMode, (newVal, oldVal) => {
  // console.log('主题变化检测:', { oldVal, newVal })
  if (newVal !== oldVal) {
    // 延迟一点重新渲染图表，确保CSS变量已更新
    nextTick(() => {
      setTimeout(() => {
        initSectorChart()
      }, 50)
    })
  }
}, { deep: true })

// 监听选中板块变化，重新加载数据
watch(selectedSector, () => {
  loadSelectedSectorData()
})

// 监听时间粒度变化，重新加载数据
watch(activeSectorPeriod, () => {
  loadSelectedSectorData()
})

// 添加一个刷新图表的方法
const refreshChart = () => {
  if (chartInstance.value) {
    console.log('主动刷新图表尺寸')
    chartInstance.value.resize()
  }
}

// 添加组件激活时的钩子
onActivated(() => {
  // console.log('Dashboard组件被激活，刷新图表')
  
  // 使用requestAnimationFrame确保DOM已经渲染
  requestAnimationFrame(() => {
    // 如果图表实例存在，直接调整大小
    if (chartInstance.value) {
      chartInstance.value.resize()
    } else {
      // 如果图表实例不存在，可能是首次加载或被销毁，需要重新加载
      loadAndRenderChart()
    }
  })
})

// 生命周期
onMounted(() => {
  // console.log('Dashboard组件已挂载，开始初始化数据...')
  
  // 初始化日期范围选择器
  resetDateRangeSelection()
  
  // 优化数据加载策略 - 分批加载，避免并发过多
  // console.log('开始分批加载数据...')
  
  // 第一批：核心数据
  fetchMarketTrend()
  
  // 延迟500ms后加载第二批
  setTimeout(() => {
    fetchPortfolioData()
  }, 500)
  
  // 延迟1000ms后加载图表数据
  setTimeout(() => {
    loadAndRenderChart()
  }, 1000)
  
  // 每分钟更新一次时间，确保问候语及时更新
  const timeTimer = setInterval(updateTime, 60000)
  
  // 每5分钟更新一次市场走势数据
  const marketTimer = setInterval(fetchMarketTrend, 5 * 60 * 1000)
  
  // 每天更新一次投资组合数据（24小时）
  const portfolioTimer = setInterval(fetchPortfolioData, 24 * 60 * 60 * 1000)
  
  // 每10分钟更新一次板块数据
  const sectorTimer = setInterval(loadSectorData, 10 * 60 * 1000)
  
  // 组件卸载时清理定时器
  onUnmounted(() => {
    // console.log('Dashboard组件卸载，清理定时器和图表资源...')
    clearInterval(timeTimer)
    clearInterval(marketTimer)
    clearInterval(portfolioTimer)
    clearInterval(sectorTimer)
    
    // 清理图表实例和事件监听器
    if (chartResizeHandler.value) {
      window.removeEventListener('resize', chartResizeHandler.value)
      chartResizeHandler.value = null
    }
    
    if (chartResizeObserver.value) {
      chartResizeObserver.value.disconnect()
      chartResizeObserver.value = null
    }
    
    if (visibilityHandler.value) {
      document.removeEventListener('visibilitychange', visibilityHandler.value)
      visibilityHandler.value = null
    }
    
    if (chartInstance.value) {
      chartInstance.value.dispose()
      chartInstance.value = null
    }
  })
})

// 监听主题变化
watch(() => appStore.isDarkMode, (newValue, oldValue) => {
  if (newValue !== oldValue) {
    // console.log('主题变化，立即重新渲染图表')
    // 立即重新初始化图表，不再使用setTimeout延迟
    sectorChartKey.value++
    initSectorChart()
  }
}, { immediate: false })

</script>

<style scoped>
.dashboard-container {
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  min-height: 100%;
}

/* ========== 欢迎横幅 ========== */
.welcome-banner {
  padding: var(--spacing-xl);
  border-radius: var(--radius-xl);
  background: var(--gradient-glow);
  position: relative;
  overflow: hidden;
}

.banner-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
}

.banner-left {
  flex: 1;
}

.welcome-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: var(--spacing-sm);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.welcome-subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0;
}

.dynamic-greeting {
  font-size: 18px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
  line-height: 1.4;
  animation: fadeInUp 0.8s ease-out;
}

.welcome-back-message {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  opacity: 0.9;
  font-style: italic;
  animation: fadeInUp 1s ease-out 0.2s both;
}

/* 智能分析内联样式 */
.smart-analysis-inline {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background: rgba(59, 130, 246, 0.08);
  border-radius: var(--radius-md);
  border: 1px solid rgba(59, 130, 246, 0.2);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  max-width: 600px;
  animation: fadeInUp 1.2s ease-out 0.4s both;
}

.analysis-icon-mini {
  width: 16px;
  height: 16px;
  color: #3b82f6;
  flex-shrink: 0;
}

.analysis-title-mini {
  font-size: 13px;
  font-weight: 600;
  color: #3b82f6;
  margin-right: var(--spacing-xs);
  flex-shrink: 0;
}

.analysis-desc-mini {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
  opacity: 0.8;
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.banner-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--spacing-md);
}



.market-indicators {
  display: flex;
  gap: var(--spacing-md);
  align-items: center;
}

.market-status, .market-sentiment {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.05);
  min-width: 120px;
}

/* 市场走势样式 */
.market-status.bull .status-icon {
  color: #ef4444; /* 上涨红色 */
}

.market-status.bear .status-icon {
  color: #22c55e; /* 下跌绿色 */
}

.market-status.neutral .status-icon {
  color: #eab308; /* 震荡黄色 */
}

/* 市场情绪样式 */
.market-sentiment.positive .sentiment-icon {
  color: #ef4444; /* 积极红色 */
}

.market-sentiment.negative .sentiment-icon {
  color: #22c55e; /* 消极绿色 */
}

.market-sentiment.neutral .sentiment-icon {
  color: #eab308; /* 中性黄色 */
}

.status-icon, .sentiment-icon {
  font-size: 32px;
}

.status-info, .sentiment-info {
  text-align: center;
}

.status-label, .sentiment-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.status-value, .sentiment-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.status-detail, .sentiment-detail {
  font-size: 14px;
  font-weight: 500;
  margin-top: 2px;
}

.market-status.bull .status-detail {
  color: #ef4444; /* 上涨红色 */
}

.market-status.bear .status-detail {
  color: #22c55e; /* 下跌绿色 */
}

.market-status.neutral .status-detail {
  color: #eab308; /* 震荡黄色 */
}

.market-sentiment.positive .sentiment-value {
  color: #ef4444; /* 积极红色 */
}

.market-sentiment.negative .sentiment-value {
  color: #22c55e; /* 消极绿色 */
}

.market-sentiment.neutral .sentiment-value {
  color: #eab308; /* 中性黄色 */
}

.market-sentiment.positive .sentiment-detail {
  color: #ef4444; /* 积极红色 */
}

.market-sentiment.negative .sentiment-detail {
  color: #22c55e; /* 消极绿色 */
}

.market-sentiment.neutral .sentiment-detail {
  color: #eab308; /* 中性黄色 */
}

/* 指数详情样式 */
.indices-detail {
  background: rgba(255, 255, 255, 0.03);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.indices-header {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
  text-align: center;
}

.indices-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.index-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.02);
  transition: all 0.2s ease;
}

.index-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.index-name {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.index-change {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 12px;
  font-weight: 600;
}

.trend-icon {
  width: 14px;
  height: 14px;
}

.index-item.index-up .change-value,
.index-item.index-up .trend-icon {
  color: #ef4444; /* 上涨红色 */
}

.index-item.index-down .change-value,
.index-item.index-down .trend-icon {
  color: #22c55e; /* 下跌绿色 */
}

.index-item.index-neutral .change-value,
.index-item.index-neutral .trend-icon {
  color: #eab308; /* 平盘黄色 */
}



/* ========== 指标网格 ========== */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 60px var(--spacing-xl); /* 行间距60px，列间距32px */
  margin-bottom: var(--spacing-xl); /* 增加底部间距 */
}

.metric-card {
  padding: var(--spacing-lg);
  position: relative;
  overflow: hidden;
}

.metric-card.success {
  border-left: 4px solid var(--neon-green);
}

.metric-card.warning {
  border-left: 4px solid #fbbf24;
}

.metric-card.info {
  border-left: 4px solid var(--accent-primary);
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: var(--gradient-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
}

.metric-trend {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 14px;
  font-weight: 600;
}

.metric-trend.up {
  color: var(--neon-green);
}

.metric-trend.down {
  color: var(--neon-pink);
}

.metric-trend.neutral {
  color: var(--text-secondary);
}

.metric-content {
  margin-bottom: var(--spacing-md);
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.metric-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.metric-detail {
  font-size: 0.75rem;
  color: var(--text-secondary);
  opacity: 0.8;
  margin-top: 0.25rem;
}

.metric-chart {
  height: 60px;
}

.mini-chart {
  width: 100%;
  height: 100%;
}

/* ========== 数据展示区域 ========== */
.data-display-section {
  width: 100%;
  margin-bottom: var(--spacing-xl);
}

.function-section {
  margin-bottom: var(--spacing-xl);
}

.activity-section {
  margin-bottom: var(--spacing-lg);
}

.chart-section {
  min-height: 400px;
}

.main-chart {
  height: 320px;
  width: 100%;
}

/* ========== 功能区域 ========== */
.function-section {
  width: 100%;
}

/* ========== 空状态 ========== */
.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-tertiary);
}

.empty-state i {
  font-size: 48px;
  margin-bottom: var(--spacing-md);
  opacity: 0.5;
}

/* ========== 卡片头部 ========== */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  color: var(--text-tertiary);
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-top: 2px solid var(--accent-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* ========== 板块数据展示样式 ========== */
.header-left {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.title-actions {
  display: flex;
  align-items: center;
}

.subtitle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xs);
}

.section-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  font-weight: 500;
}

.date-range-selector {
  display: flex;
  align-items: center;
}

/* 自定义日期范围弹窗样式 */
.custom-date-content {
  padding: var(--spacing-md);
}

.date-info {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: rgba(59, 130, 246, 0.05);
  border-radius: var(--radius-md);
  border-left: 4px solid #3b82f6;
}

.date-info p {
  margin: var(--spacing-xs) 0;
  color: var(--text-primary);
}

.date-info .date-tip {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: var(--spacing-sm);
}

.date-picker-container {
  margin-bottom: var(--spacing-lg);
}

.date-preview {
  padding: var(--spacing-md);
  background: rgba(16, 185, 129, 0.05);
  border-radius: var(--radius-md);
  border-left: 4px solid #10b981;
}

.date-preview h4 {
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 600;
}

.date-preview p {
  margin: var(--spacing-xs) 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

.header-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.index-selector {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.index-selector .el-radio-group {
  margin-right: 0;
}

.more-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: 6px 12px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: var(--radius-md);
  color: #3b82f6;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.more-button:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.5);
  transform: translateY(-1px);
}

.more-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.more-text {
  font-size: 12px;
  letter-spacing: 0.5px;
}

.time-selector {
  display: flex;
  align-items: center;
}

.loading-container {
  padding: var(--spacing-lg);
}

.skeleton-chart {
  height: 400px;
}

.sector-chart-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.chart-container {
  height: 500px;
  width: 100%;
  transition: height 0.3s ease, width 0.3s ease;
}

.legend-section {
  display: flex;
  justify-content: center;
  gap: 24px;
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 14px;
  color: var(--text-secondary);
}

.legend-bar {
  width: 16px;
  height: 12px;
  border-radius: 2px;
  /* 动态背景色由内联样式设置 */
}

.legend-line {
  width: 20px;
  height: 2px;
  border-radius: 1px;
}

.line-primary {
  background: #3b82f6;
}

.line-secondary {
  background: #f59e0b;
  background-image: repeating-linear-gradient(
    90deg,
    transparent,
    transparent 3px,
    #f59e0b 3px,
    #f59e0b 6px
  );
}

.sector-cards {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-lg);
}

.sector-cards-container {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.sector-card {
  flex: 1;
  min-width: 200px;
  max-width: calc(20% - 13px); /* 5个卡片均匀分布，减去gap */
  transition: all 0.3s ease;
  border-radius: var(--radius-md);
  overflow: hidden;
  height: 100%;
  min-height: 180px; /* 增加最小高度以容纳成交量字段 */
}

.sector-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

.sector-card.positive {
  border-left: 4px solid #ff4757; /* 红涨 */
}

.sector-card.negative {
  border-left: 4px solid #2ed573; /* 绿跌 */
}

.sector-card.selected {
  border: 2px solid #3b82f6;
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);
}

.sector-card {
  cursor: pointer;
}

.sector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.sector-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: bold;
  color: var(--text-primary);
}

.sector-code {
  font-size: 12px;
  color: var(--text-tertiary);
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}

.sector-metrics {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-xs);
}

.metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric .label {
  font-size: 13px; /* 稍微减小字体以适应更多内容 */
  color: var(--text-secondary);
}

.metric .value {
  font-size: 13px; /* 稍微减小字体以适应更多内容 */
  font-weight: 600;
  color: var(--text-primary);
}

.metric .value.change.positive {
  color: #ff4757; /* 红涨 */
}

.metric .value.change.negative {
  color: #2ed573; /* 绿跌 */
}

/* ========== 响应式设计 ========== */
@media (max-width: 768px) {
  .banner-content {
    flex-direction: column;
    text-align: center;
    gap: var(--spacing-md);
  }
  
  .dynamic-greeting {
    font-size: 16px;
  }
  
  .welcome-back-message {
    font-size: 13px;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }
  
  .card-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .sector-cards-container {
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .sector-card {
    max-width: 100%;
    min-width: 100%;
  }
}

@media (max-width: 1200px) and (min-width: 769px) {
  .sector-cards-container {
    gap: 12px;
  }
  
  .sector-card {
    max-width: calc(50% - 6px);
    min-width: calc(50% - 6px);
  }
}

@media (max-width: 1600px) and (min-width: 1201px) {
  .sector-cards-container {
    gap: 14px;
  }
  
  .sector-card {
    max-width: calc(33.33% - 10px);
    min-width: calc(33.33% - 10px);
  }
}

.chart-loading-animation {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  color: var(--text-tertiary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-top: 4px solid var(--accent-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-top: var(--spacing-xs);
}
</style>