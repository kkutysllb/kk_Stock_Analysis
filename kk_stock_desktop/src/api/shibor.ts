/**
 * SHIBOR利率数据API客户端
 * 提供SHIBOR利率数据的获取、缓存和分析功能
 */

import { BaseApiClient, type ApiResponse } from './base'

// SHIBOR数据接口定义
export interface ShiborRateData {
  date: string
  period: string
  rate: number
  change?: number
  change_bp?: number
}

export interface ShiborLatestData {
  period: string
  rate: number
  change: number
  change_bp: number
  update_time: string
}

export interface ShiborTrendData {
  date: string
  rate: number
  volume?: number
  high?: number
  low?: number
  open?: number
  close?: number
}

export interface ShiborAnalysisData {
  period: string
  statistics: {
    averageRate: number
    maxRate: number
    minRate: number
    volatility: number
    correlation?: number
  }
  trend_analysis: {
    trend: 'up' | 'down' | 'stable'
    strength: number
    confidence: number
  }
  report: string
  recommendations: string[]
}

export interface ShiborCurveData {
  date: string
  rates: {
    [period: string]: number
  }
  curve_type: 'normal' | 'inverted' | 'flat'
  steepness: number
}

export interface ShiborDataResponse {
  query_params: {
    start_date?: string
    end_date?: string
    limit: number
  }
  shibor_rates: ShiborRateData[]
  statistics: Record<string, any>
  count: number
  timestamp: string
}

// SHIBOR API参数接口
export interface ShiborQueryParams {
  start_date?: string
  end_date?: string
  period?: string
  limit?: number
  cache_ttl?: number
}

export interface ShiborTrendParams extends ShiborQueryParams {
  period: string
  indicators?: string[]
}

export interface ShiborAnalysisParams {
  period?: string
  analysis_type?: 'basic' | 'detailed' | 'forecast'
  days?: number
}

/**
 * SHIBOR API客户端类
 */
export class ShiborAPI extends BaseApiClient {
  private readonly baseEndpoint = '/macro/shibor'

  constructor() {
    super()
  }

  /**
   * 获取SHIBOR利率数据
   * 支持日期范围查询和缓存
   */
  async getShiborData(params?: ShiborQueryParams): Promise<ApiResponse<ShiborDataResponse>> {
    const query: Record<string, any> = {}
    
    if (params?.start_date) query.start_date = params.start_date
    if (params?.end_date) query.end_date = params.end_date
    if (params?.period) query.period = params.period
    if (params?.limit) query.limit = params.limit
    if (params?.cache_ttl) query.cache_ttl = params.cache_ttl

    return this.get<ShiborDataResponse>(this.baseEndpoint, query)
  }

  /**
   * 获取最新SHIBOR利率数据
   * 包含所有期限的最新利率和变化
   */
  async getLatest(): Promise<ApiResponse<ShiborLatestData[]>> {
    return this.get<ShiborLatestData[]>(`${this.baseEndpoint}/latest`)
  }

  /**
   * 获取指定期限的利率趋势
   * 支持技术指标分析
   */
  async getTrend(
    period: string,
    startDate?: string,
    endDate?: string,
    indicators?: string[]
  ): Promise<ApiResponse<ShiborTrendData[]>> {
    const query: Record<string, any> = { period }
    
    // 如果提供了日期范围，计算天数
    if (startDate && endDate) {
      const start = new Date(startDate)
      const end = new Date(endDate)
      const days = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
      query.days = Math.max(1, days)
    } else {
      // 默认30天
      query.days = 30
    }
    
    if (indicators && indicators.length > 0) query.indicators = indicators.join(',')
    
    // 添加时间戳防止缓存
    query._t = Date.now()

    return this.get<ShiborTrendData[]>(`${this.baseEndpoint}/trend`, query)
  }

  /**
   * 获取SHIBOR利率分析报告
   * 包含统计数据、趋势分析和投资建议
   */
  async getAnalysis(params?: ShiborAnalysisParams): Promise<ApiResponse<ShiborAnalysisData>> {
    const query: Record<string, any> = {}
    
    if (params?.period) query.period = params.period
    if (params?.analysis_type) query.analysis_type = params.analysis_type
    if (params?.days) query.days = params.days

    return this.get<ShiborAnalysisData>(`${this.baseEndpoint}/analysis`, query)
  }

  /**
   * 获取SHIBOR利率曲线数据
   * 分析收益率曲线形态
   */
  async getCurve(date?: string): Promise<ApiResponse<ShiborCurveData>> {
    const query: Record<string, any> = {}
    if (date) query.date = date

    return this.get<ShiborCurveData>(`${this.baseEndpoint}/curve`, query)
  }

  /**
   * 获取历史利率曲线数据
   * 用于曲线变化分析
   */
  async getHistoricalCurves(
    startDate: string,
    endDate: string,
    interval: 'daily' | 'weekly' | 'monthly' = 'daily'
  ): Promise<ApiResponse<ShiborCurveData[]>> {
    const query = {
      start_date: startDate,
      end_date: endDate,
      interval
    }

    return this.get<ShiborCurveData[]>(`${this.baseEndpoint}/curves/historical`, query)
  }

  /**
   * 获取SHIBOR与其他利率的相关性分析
   */
  async getCorrelationAnalysis(
    period: string,
    compareTo: string[] = ['LPR', 'MLF', 'DR'],
    days: number = 30
  ): Promise<ApiResponse<{
    period: string
    correlations: Array<{
      target: string
      correlation: number
      confidence: number
    }>
    analysis: string
  }>> {
    const query = {
      period,
      compare_to: compareTo.join(','),
      days
    }

    return this.get(`${this.baseEndpoint}/correlation`, query)
  }

  /**
   * 获取SHIBOR预测数据
   * 基于历史数据和市场因子的预测
   */
  async getForecast(
    period: string,
    days: number = 7,
    model: 'arima' | 'lstm' | 'ensemble' = 'ensemble'
  ): Promise<ApiResponse<{
    period: string
    forecast_horizon: number
    model_type: string
    predictions: Array<{
      date: string
      predicted_rate: number
      confidence_interval: {
        lower: number
        upper: number
      }
      confidence: number
    }>
    accuracy_metrics: {
      mae: number
      rmse: number
      mape: number
    }
  }>> {
    const query = {
      period,
      days,
      model
    }

    return this.get(`${this.baseEndpoint}/forecast`, query)
  }

  /**
   * 获取SHIBOR统计摘要
   * 包含各期限的统计数据
   */
  async getStatistics(
    startDate?: string,
    endDate?: string
  ): Promise<ApiResponse<{
    period: string
    data: Array<{
      period: string
      count: number
      mean: number
      std: number
      min: number
      max: number
      percentiles: {
        p25: number
        p50: number
        p75: number
        p90: number
        p95: number
      }
    }>
  }>> {
    const query: Record<string, any> = {}
    if (startDate) query.start_date = startDate
    if (endDate) query.end_date = endDate

    return this.get(`${this.baseEndpoint}/statistics`, query)
  }

  /**
   * 获取SHIBOR事件影响分析
   * 分析重要事件对利率的影响
   */
  async getEventImpact(
    eventType: 'monetary_policy' | 'economic_data' | 'market_event' = 'monetary_policy',
    days: number = 30
  ): Promise<ApiResponse<{
    event_type: string
    analysis_period: number
    events: Array<{
      date: string
      event: string
      impact: {
        magnitude: number
        direction: 'up' | 'down' | 'neutral'
        duration: number
      }
      affected_periods: string[]
    }>
    summary: string
  }>> {
    const query = {
      event_type: eventType,
      days
    }

    return this.get(`${this.baseEndpoint}/events/impact`, query)
  }

  /**
   * 批量获取SHIBOR数据
   * 一次性获取多个期限的数据
   */
  async getBatchData(
    periods: string[],
    startDate?: string,
    endDate?: string,
    limit?: number
  ): Promise<ApiResponse<{
    [period: string]: ShiborRateData[]
  }>> {
    const query: Record<string, any> = {
      periods: periods.join(',')
    }
    
    if (startDate) query.start_date = startDate
    if (endDate) query.end_date = endDate
    if (limit) query.limit = limit

    return this.get(`${this.baseEndpoint}/batch`, query)
  }

  /**
   * 获取SHIBOR实时推送配置
   * 用于WebSocket连接配置
   */
  async getRealTimeConfig(): Promise<ApiResponse<{
    websocket_url: string
    channels: string[]
    auth_token: string
    heartbeat_interval: number
    reconnect_interval: number
  }>> {
    return this.get(`${this.baseEndpoint}/realtime/config`)
  }

  /**
   * 清除SHIBOR数据缓存
   * 强制重新获取数据
   */
  async clearCache(cacheKey?: string): Promise<ApiResponse<{
    cleared: boolean
    message: string
  }>> {
    const query: Record<string, any> = {}
    if (cacheKey) query.cache_key = cacheKey

    return this.post(`${this.baseEndpoint}/cache/clear`, query)
  }

  /**
   * 获取API使用统计
   */
  async getApiStats(): Promise<ApiResponse<{
    total_requests: number
    cache_hit_rate: number
    average_response_time: number
    error_rate: number
    popular_endpoints: Array<{
      endpoint: string
      requests: number
      avg_time: number
    }>
  }>> {
    return this.get(`${this.baseEndpoint}/stats`)
  }
}

// 创建SHIBOR API实例
export const shiborAPI = new ShiborAPI()

// 导出常用的期限配置
export const SHIBOR_PERIODS = {
  ON: '隔夜',
  '1W': '1周',
  '2W': '2周',
  '1M': '1个月',
  '3M': '3个月',
  '6M': '6个月',
  '9M': '9个月',
  '1Y': '1年'
} as const

// 导出期限类型
export type ShiborPeriod = keyof typeof SHIBOR_PERIODS

// 导出分析类型
export const ANALYSIS_TYPES = {
  basic: '基础分析',
  detailed: '详细分析',
  forecast: '预测分析'
} as const

// 导出趋势类型
export const TREND_TYPES = {
  up: '上升',
  down: '下降',
  stable: '稳定'
} as const

// 导出曲线类型
export const CURVE_TYPES = {
  normal: '正常',
  inverted: '倒挂',
  flat: '平坦'
} as const