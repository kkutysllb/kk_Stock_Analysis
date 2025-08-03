/**
 * 市场数据API客户端
 */

import { BaseApiClient, type ApiResponse } from './base'

export interface IndexData {
  ts_code: string
  name: string
  market: string
  latest_data: {
    trade_date: string
    open: number
    high: number
    low: number
    close: number
    pre_close: number
    change: number
    pct_chg: number
    vol: number
    amount: number
  }
  history_data: any[]
}

// 板块数据接口
export interface SectorData {
  code: string
  name: string
  current_price: number
  change: number
  change_percent: number
  volume: number
  turnover: number
  open: number
  high: number
  low: number
  pre_close: number
  update_time: string
}

export interface SectorHistoryItem {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  turnover: number
  change_percent: number
}

export interface SectorHistoryData {
  code: string
  name: string
  period: string
  data: SectorHistoryItem[]
}

export interface DragonTigerItem {
  ts_code: string
  trade_date: string
  name: string
  close: number
  pct_change: number
  turnover_rate: number
  amount: number
  l_sell: number
  l_buy: number
  l_amount: number
  net_amount: number
  net_rate: number
  amount_rate: number
  reason: string
}

export interface DragonTigerSummary {
  trade_date: string
  total_count: number
  statistics: {
    total_buy_amount: number
    total_sell_amount: number
    total_net_amount: number
  }
  dragon_tiger_list: DragonTigerItem[]
}

export class MarketAPI extends BaseApiClient {
  constructor() {
    super()
  }

  private marketRequest<T>(endpoint: string, config?: any): Promise<ApiResponse<T>> {
    return this.request<T>(`/market${endpoint}`, config)
  }

  /**
   * 获取主要指数数据
   */
  async getIndices(period: 'daily' | 'weekly' | 'monthly' = 'daily', limit: number = 30): Promise<ApiResponse<{
    period: string
    indices: IndexData[]
  }>> {
    return this.get(`/market/indices`, { period, limit })
  }

  /**
   * 获取单个指数详细数据
   */
  async getIndexDetail(tsCode: string, period: 'daily' | 'weekly' | 'monthly' = 'daily', limit: number = 60): Promise<ApiResponse<{
    ts_code: string
    name: string
    market: string
    period: string
    data: any[]
  }>> {
    return this.get(`/market/indices/${tsCode}`, { period, limit })
  }

  /**
   * 获取主要指数数据 - 替代板块实时数据
   */
  async getSectorData(): Promise<ApiResponse<any[]>> {
    return this.get('/market/indices')
  }

  /**
   * 获取板块分析数据
   */
  async getSectorAnalysis(): Promise<ApiResponse<any>> {
    return this.get('/analytics/sector-analysis')
  }

  /**
   * 获取指数K线历史数据
   */
  async getIndexKline(
    tsCode: string, 
    period: 'daily' | 'weekly' | 'monthly' = 'daily',
    limit: number = 30,
    startDate?: string,
    endDate?: string
  ): Promise<ApiResponse<any>> {
    const params: Record<string, any> = { period }
    
    // 如果指定了日期范围，优先使用日期范围而不是limit
    if (startDate && endDate) {
      params.start_date = startDate
      params.end_date = endDate
    } else {
      params.limit = limit
    }
    
    return this.get(`/index/kline/${tsCode}`, params)
  }

  /**
   * 获取交易日历数据
   */
  async getTradingDays(startDate: string, endDate: string): Promise<ApiResponse<any[]>> {
    return this.get('/calendar/trading-days', { 
      start_date: startDate, 
      end_date: endDate,
      is_open: 1  // 只获取交易日
    })
  }

  /**
   * 获取基础交易日历（包含所有日期和是否交易日标志）
   */
  async getBasicCalendar(): Promise<ApiResponse<any[]>> {
    return this.get('/calendar/basic')
  }

  /**
   * 根据交易日历智能计算需要获取的交易日数量
   */
  async getSmartTradingDaysLimit(period: 'daily' | 'weekly' | 'monthly'): Promise<number> {
    try {
      // 获取最近30天的交易日历来分析交易日密度
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(endDate.getDate() - 30)
      
      const calendarResponse = await this.getTradingDays(
        startDate.toISOString().split('T')[0],
        endDate.toISOString().split('T')[0]
      )
      
      if (calendarResponse.success && calendarResponse.data) {
        const tradingDaysInMonth = calendarResponse.data.length
        const tradingDaysPerWeek = Math.round(tradingDaysInMonth / 4.3) // 一个月约4.3周
        
        switch (period) {
          case 'daily':
            // 近一周：取1.5周的交易日，确保包含至少5个交易日
            return Math.max(tradingDaysPerWeek * 1.5, 7)
          case 'weekly':
            // 近5周：取6周的交易日
            return Math.max(tradingDaysPerWeek * 6, 25)
          case 'monthly':
            // 近5个月：取5.5个月的交易日
            return Math.max(tradingDaysInMonth * 5.5, 100)
          default:
            return 30
        }
      }
    } catch (error) {
      console.warn('获取交易日历失败，使用默认值:', error)
    }
    
    // 降级使用经验值
    switch (period) {
      case 'daily': return 10  // 近一周约5-7个交易日
      case 'weekly': return 30 // 近5周约25个交易日
      case 'monthly': return 110 // 近5个月约100个交易日
      default: return 30
    }
  }

  /**
   * 获取板块历史数据 - 使用指数K线数据，智能计算交易日数量
   */
  async getSectorHistory(
    codes: string[], 
    period: 'daily' | 'weekly' | 'monthly' = 'daily',
    limit?: number,
    startDate?: string,
    endDate?: string
  ): Promise<ApiResponse<any[]>> {
    // 如果指定了日期范围，使用日期范围查询
    if (startDate && endDate) {
      console.log(`获取${period}数据，日期范围: ${startDate} 至 ${endDate}`)
      
      // 并行获取所有指数的K线数据，使用日期范围
      const promises = codes.map(code => 
        this.getIndexKline(code, period, 30, startDate, endDate)
      )
      
      const results = await Promise.all(promises)
      
      // 处理结果，提取成功的数据
      const historyData = results
        .filter(result => result.success && result.data?.kline_data)
        .map((result, index) => ({
          code: codes[index],
          name: codes[index],
          period,
          data: result.data.kline_data
        }))
      
      return {
        success: true,
        data: historyData,
        message: `获取历史数据成功 (${startDate} 至 ${endDate})`,
        timestamp: new Date().toISOString()
      }
    }
    
    // 如果没有指定limit，智能计算
    if (!limit) {
      limit = await this.getSmartTradingDaysLimit(period)
    }
    
    console.log(`获取${period}数据，智能计算limit: ${limit}`)
    
    // 并行获取所有指数的K线数据
    const promises = codes.map(code => 
      this.getIndexKline(code, period, limit)
    )
    
    const results = await Promise.all(promises)
    
    // 处理结果，提取成功的数据
    const historyData = results
      .filter(result => result.success && result.data?.kline_data)
      .map((result, index) => ({
        code: codes[index],
        name: codes[index], // 可以根据需要映射名称
        period,
        data: result.data.kline_data  // 修正字段名
      }))
    
    return {
      success: true,
      data: historyData,
      message: '获取历史数据成功',
      timestamp: new Date().toISOString()
    }
  }

  /**
   * 获取特定板块的详细数据
   */
  async getSectorDetail(code: string, period: 'daily' | 'weekly' | 'monthly' = 'daily'): Promise<ApiResponse<SectorHistoryData>> {
    return this.get(`/market/sectors/${code}`, { period })
  }

  /**
   * 获取板块成交量排行
   */
  async getSectorVolumeRank(limit: number = 10): Promise<ApiResponse<SectorData[]>> {
    return this.get('/market/sectors/volume-rank', { limit })
  }

  /**
   * 获取板块涨跌幅排行
   */
  async getSectorChangeRank(limit: number = 10): Promise<ApiResponse<SectorData[]>> {
    return this.get('/market/sectors/change-rank', { limit })
  }

  /**
   * 获取龙虎榜数据
   */
  async getDragonTigerList(tradeDate?: string, limit: number = 20): Promise<ApiResponse<DragonTigerSummary>> {
    const params: Record<string, any> = { limit }
    if (tradeDate) params.trade_date = tradeDate
    
    return this.get('/dragon-tiger/stats', params)
  }

  /**
   * 获取龙虎榜统计摘要
   */
  async getDragonTigerSummary(days: number = 5): Promise<ApiResponse<{
    period: string
    daily_statistics: Array<{
      _id: string
      count: number
      total_amount: number
      total_net: number
      avg_change: number
    }>
    most_active_stocks: Array<{
      _id: string
      name: string
      count: number
      total_net: number
    }>
  }>> {
    return this.get('/market/dragon-tiger/summary', { days })
  }

  /**
   * 获取基础行情数据
   */
  async getQuote(): Promise<ApiResponse> {
    return this.get('/market/quote')
  }

  /**
   * 获取市场走势数据
   */
  async getMarketTrend(): Promise<ApiResponse<{
    trend: 'up' | 'down' | 'sideways'
    changePercent: number
    period: string
    lastUpdate: string
  }>> {
    return this.get('/market/trend')
  }

  /**
   * 获取机构交易数据
   */
  async getInstitutionTrades(tradeDate?: string, limit: number = 50): Promise<ApiResponse<{
    institution_trades: any[]
    count: number
    timestamp: string
  }>> {
    const params: Record<string, any> = { limit }
    if (tradeDate) params.trade_date = tradeDate
    
    return this.get('/dragon-tiger/institutions', params)
  }

  /**
   * 获取游资交易统计数据
   */
  async getHotMoneyTrades(startDate: string, topN: number = 20): Promise<ApiResponse<{
    hm_summary: Array<{
      hm_name: string
      desc: string
      orgs: string[]
      total_trades: number
      total_buy_amount: number
      total_sell_amount: number
      total_net_buy: number
      trade_dates: string[]
      stocks_traded: string[]
      avg_buy_rate: number
      avg_sell_rate: number
      recent_trades: Array<{
        trade_date: string
        ts_code: string
        buy: number
        sell: number
        net_buy: number
      }>
      unique_trade_days: number
      unique_stocks_count: number
      activity_score: number
    }>
    overall_stats: {
      total_hm_count: number
      total_trades: number
      total_buy_amount: number
      total_sell_amount: number
      total_net_buy: number
      date_range: {
        start_date: string
        end_date: string | null
      }
    }
    query_params: {
      start_date: string
      end_date: string | null
      top_n: number
    }
    count: number
    timestamp: string
  }>> {
    const params: Record<string, any> = { 
      start_date: startDate,
      top_n: topN
    }
    
    return this.get('/hm/dragon-tiger/hm-summary', params)
  }

  /**
   * 获取申万行业分类列表
   */
  async getSwIndustries(): Promise<ApiResponse<{
    industries: Array<{
      code: string
      name: string
      stock_count: number
      color: string
    }>
    total_count: number
    timestamp: string
  }>> {
    return this.get('/index/shenwan/industries')
  }

  /**
   * 获取申万行业指数日线数据（专用接口）
   */
  async getSwIndustryDaily(
    tsCode: string,
    startDate?: string,
    endDate?: string,
    limit: number = 100
  ): Promise<ApiResponse<{
    ts_code: string
    trade_date: string | null
    start_date: string | null
    end_date: string | null
    sw_industry_data: any[]
    count: number
    timestamp: string
  }>> {
    const params: Record<string, any> = { ts_code: tsCode, limit }
    
    if (startDate && endDate) {
      params.start_date = startDate
      params.end_date = endDate
    }
    
    return this.get('/concept/sw/daily', params)
  }

  // ==================== 资金流向相关API ====================

  /**
   * 获取资金流向综合分析
   */
  async getMoneyFlowAnalysis(tradeDate: string, days: number = 10): Promise<ApiResponse<any>> {
    return this.get('/money_flow/analysis', { trade_date: tradeDate, days })
  }

  /**
   * 获取资金流入排行榜
   */
  async getMoneyFlowInflowRanking(tradeDate: string, limit: number = 20): Promise<ApiResponse<any>> {
    return this.get('/money_flow/rankings/inflow', { trade_date: tradeDate, limit })
  }

  /**
   * 获取资金流出排行榜
   */
  async getMoneyFlowOutflowRanking(tradeDate: string, limit: number = 20): Promise<ApiResponse<any>> {
    return this.get('/money_flow/rankings/outflow', { trade_date: tradeDate, limit })
  }

  /**
   * 获取行业资金流向数据
   */
  async getMoneyFlowIndustry(tradeDate: string, limit: number = 50): Promise<ApiResponse<any>> {
    return this.get('/money_flow/industry', { trade_date: tradeDate, limit })
  }

  /**
   * 获取大盘资金流向数据
   */
  async getMoneyFlowMarket(startDate: string, endDate: string, limit: number = 10): Promise<ApiResponse<any>> {
    return this.get('/money_flow/market', { start_date: startDate, end_date: endDate, limit })
  }
}

export const marketAPI = new MarketAPI()