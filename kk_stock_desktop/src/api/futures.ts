/**
 * 期货数据API客户端
 */

import { BaseApiClient, type ApiResponse } from './base'

// 期货基本信息接口
export interface FuturesBasicInfo {
  ts_code: string
  symbol: string
  name: string
  fut_code: string
  multiplier: number
  trade_unit: string
  per_unit: number
  quote_unit: string
  d_mode_desc: string
  list_date: string
  delist_date: string
}

// 期货日线数据接口
export interface FuturesKlineData {
  ts_code: string
  trade_date: string
  open: number
  high: number
  low: number
  close: number
  settle: number
  vol: number
  amount: number
  oi: number
}

// 期货持仓数据接口
export interface FuturesHoldingData {
  symbol: string
  broker: string
  trade_date: string
  long_hld: number
  short_hld: number
  long_chg: number
  short_chg: number
  vol: number
  vol_chg: number
}

// 期货持仓汇总数据接口
export interface BrokerHoldingData {
  total_long: number
  total_short: number
  net_position: number
  total_long_chg: number
  total_short_chg: number
  net_position_chg: number
  total_vol: number
  total_vol_chg: number
  institution_count: number
}

export interface FuturesHoldingSummary {
  symbol: string
  trade_date: string
  total_long: number
  total_short: number
  net_position: number
  total_long_chg: number
  total_short_chg: number
  net_position_chg: number
  total_vol: number
  total_vol_chg: number
  institution_count: number
  broker_breakdown: {
    citic: BrokerHoldingData
    others: BrokerHoldingData
  }
}

// 活跃期货合约汇总数据接口
export interface ActiveFuturesContract {
  symbol: string
  ts_code: string
  volume: number
  amount: number
  oi: number
  avg_price: number
  price_range: {
    high: number
    low: number
  }
}

export interface ActiveFuturesSymbolSummary {
  symbol: string
  trade_date?: string
  active_contracts_count: number
  active_contracts?: string[]
  total_long: number
  total_short: number
  net_position: number
  total_long_chg: number
  total_short_chg: number
  net_position_chg: number
  total_vol: number
  total_vol_chg: number
  institution_count: number
  main_contract: {
    symbol: string // 主力合约代码
    ts_code?: string // 保持向后兼容
    total_volume?: number
    total_long?: number
    total_short?: number
    volume?: number
    oi?: number
  }
  active_contracts_data?: ActiveFuturesContract[]
}

export interface ActiveFuturesSummary {
  trade_date: string
  overall_stats?: {
    total_active_contracts: number
    total_volume: number
    total_amount: number
    total_oi: number
    avg_price: number
    price_range: {
      high: number
      low: number
    }
  }
  symbol_details?: Record<string, ActiveFuturesSymbolSummary>
  summary_by_symbol?: Record<string, ActiveFuturesSymbolSummary>
  total_stats?: {
    total_active_contracts: number
    total_long: number
    total_short: number
    total_net_position: number
    total_vol: number
    total_institutions: number
  }
  symbols?: string[]
  timestamp?: string
}

// 正反向市场分析接口
export interface ContractAnalysis {
  ts_code: string
  futures_price: number
  spot_price: number
  basis: number
  basis_rate: number
  is_contango: boolean
  days_to_expiry: number
}

export interface ContangoAnalysisData {
  trade_date: string
  analysis_results: Array<{
    symbol: string
    spot_index_code: string
    spot_index_name: string
    trade_date: string
    spot_price: number
    contracts: ContractAnalysis[]
    term_structure: Record<string, number>
    market_sentiment: string
    analysis_summary: string
  }>
  timestamp: string
}

export interface HistoricalContangoData {
  symbol: string
  start_date: string
  end_date: string
  historical_data: Array<{
    trade_date: string
    avg_basis: number
    avg_basis_rate: number
    contango_ratio: number
    contract_count: number
  }>
  summary: {
    avg_basis: number
    avg_basis_rate: number
    contango_days: number
    backwardation_days: number
    total_days: number
  }
  timestamp: string
}

export class FuturesAPI extends BaseApiClient {
  constructor() {
    super()
  }

  private futuresRequest<T>(endpoint: string, config?: any): Promise<ApiResponse<T>> {
    if (config?.params) {
      // 使用get方法处理params参数
      return this.get<T>(`/futures${endpoint}`, config.params, config)
    } else {
      // 没有params时使用request方法
      return this.request<T>(`/futures${endpoint}`, config)
    }
  }

  /**
   * 获取期货基本信息列表
   */
  async getFuturesList(
    exchange?: string,
    futType?: string,
    limit: number = 100
  ): Promise<ApiResponse<{
    futures_list: FuturesBasicInfo[]
    count: number
    timestamp: string
  }>> {
    const params: Record<string, any> = { limit }
    if (exchange) params.exchange = exchange
    if (futType) params.fut_type = futType
    
    return this.futuresRequest('/basic/list', { params })
  }

  /**
   * 获取单个期货基本信息
   */
  async getFuturesInfo(tsCode: string): Promise<ApiResponse<{
    futures_info: FuturesBasicInfo
    timestamp: string
  }>> {
    return this.futuresRequest(`/basic/${tsCode}`)
  }

  /**
   * 获取期货日线数据
   */
  async getFuturesDaily(
    tsCode: string,
    startDate?: string,
    endDate?: string,
    limit: number = 100
  ): Promise<ApiResponse<{
    ts_code: string
    start_date: string | null
    end_date: string | null
    daily_data: FuturesKlineData[]
    count: number
    timestamp: string
  }>> {
    const params: Record<string, any> = { limit }
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    
    
    // 注意：tsCode可能包含点号，需要正确编码
    const encodedTsCode = encodeURIComponent(tsCode)
    const response = await this.futuresRequest<{
      ts_code: string
      start_date: string | null
      end_date: string | null
      daily_data: FuturesKlineData[]
      count: number
      timestamp: string
    }>(`/daily/${encodedTsCode}`, { params })
    
    return response
  }

  /**
   * 获取期货持仓数据
   */
  async getFuturesHolding(
    tsCode: string,
    startDate?: string,
    endDate?: string,
    limit: number = 50
  ): Promise<ApiResponse<{
    ts_code: string
    start_date: string | null
    end_date: string | null
    holding_data: FuturesHoldingData[]
    count: number
    timestamp: string
  }>> {
    const params: Record<string, any> = { limit }
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    
    return this.futuresRequest(`/holding/${tsCode}`, { params })
  }

  /**
   * 获取股指期货机构持仓汇总数据
   * 用于Dashboard概览面板展示
   */
  async getFuturesHoldingSummary(
    tradeDate?: string,
    symbols: string = 'IF,IC,IH,IM'
  ): Promise<ApiResponse<{
    summary: Record<string, FuturesHoldingSummary>
    trade_date: string
    symbols: string[]
    timestamp: string
  }>> {
    const params: Record<string, any> = { symbols }
    if (tradeDate) {
      params.trade_date = tradeDate
    }

    return this.futuresRequest<{
      summary: Record<string, FuturesHoldingSummary>
      trade_date: string
      symbols: string[]
      timestamp: string
    }>('/holding/summary', { params })
  }

  /**
   * 获取期货仓单数据
   */
  async getFuturesWarehouse(
    symbol: string,
    startDate?: string,
    endDate?: string,
    limit: number = 50
  ): Promise<ApiResponse<{
    symbol: string
    start_date: string | null
    end_date: string | null
    warehouse_data: any[]
    count: number
    timestamp: string
  }>> {
    const params: Record<string, any> = { limit }
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    
    return this.futuresRequest(`/warehouse/${symbol}`, { params })
  }

  /**
   * 获取期货前20机构持仓详细数据
   * 用于分析页面展示机构排名和图表
   */
  async getFuturesTop20Holdings(
    symbols: string = 'IF,IC,IH,IM',
    tradeDate?: string,
    days: number = 7
  ): Promise<ApiResponse<{
    trade_date: string
    symbols: string[]
    holdings_by_symbol: Record<string, {
      symbol: string
      trade_date: string
      top20_institutions: Array<{
        rank: number
        broker: string
        long_hld: number
        short_hld: number
        net_position: number
        long_chg: number
        short_chg: number
        net_chg: number
        vol: number
        vol_chg: number
      }>
      daily_trends: Array<{
        trade_date: string
        total_long: number
        total_short: number
        net_position: number
        total_long_chg: number
        total_short_chg: number
        net_position_chg: number
        institution_count: number
      }>
    }>
    timestamp: string
  }>> {
    const params: Record<string, any> = { symbols, days }
    if (tradeDate) {
      params.trade_date = tradeDate
    }
    
    return this.futuresRequest<{
      trade_date: string
      symbols: string[]
      holdings_by_symbol: Record<string, {
        symbol: string
        trade_date: string
        top20_institutions: Array<{
          rank: number
          broker: string
          long_hld: number
          short_hld: number
          net_position: number
          long_chg: number
          short_chg: number
          net_chg: number
          vol: number
          vol_chg: number
        }>
        daily_trends: Array<{
          trade_date: string
          total_long: number
          total_short: number
          net_position: number
          total_long_chg: number
          total_short_chg: number
          net_position_chg: number
          institution_count: number
        }>
      }>
      timestamp: string
    }>('/holding/top20', { params })
  }

  /**
   * 批量获取期货日线数据
   */
  async getBatchFuturesDaily(requestData: {
    ts_codes: string[]
    start_date?: string
    end_date?: string
    limit?: number
  }): Promise<ApiResponse<{
    results: Array<{
      ts_code: string
      data: FuturesKlineData[]
      success: boolean
      error?: string
    }>
    total_requested: number
    success_count: number
    failed_count: number
    timestamp: string
  }>> {
    const response = await this.post<{
      results: Array<{
        ts_code: string
        data: FuturesKlineData[]
        success: boolean
        error?: string
      }>
      total_requested: number
      success_count: number
      failed_count: number
      timestamp: string
    }>('/futures/batch/daily', requestData)
    
    return response
  }

  /**
   * 获取期货交易日历
   */
  async getFuturesCalendar(
    startDate?: string,
    endDate?: string,
    exchange?: string
  ): Promise<ApiResponse<{
    calendar: Array<{
      cal_date: string
      exchange: string
      is_open: number
      pretrade_date: string
    }>
    count: number
    timestamp: string
  }>> {
    const params: Record<string, any> = {}
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    if (exchange) params.exchange = exchange
    
    return this.futuresRequest('/calendar', { params })
  }

  /**
   * 获取活跃期货合约汇总数据
   * 用于分析页面展示活跃合约的统计信息
   */
  async getActiveFuturesSummary(
    tradeDate?: string,
    symbols: string = 'IH,IF,IC,IM'
  ): Promise<ApiResponse<ActiveFuturesSummary>> {
    const params: Record<string, any> = { symbols }
    if (tradeDate) {
      params.trade_date = tradeDate
    }
    
    return this.get<ActiveFuturesSummary>('/futures/active/summary', params)
  }

  /**
   * 获取股指期货正反向市场分析
   * 用于分析当前市场的正反向状态和期限结构
   */
  async getContangoAnalysis(
    tradeDate?: string,
    symbols: string = 'IF,IC,IH,IM'
  ): Promise<ApiResponse<ContangoAnalysisData>> {
    const params: Record<string, any> = { symbols }
    if (tradeDate) {
      params.trade_date = tradeDate
    }
    
    return this.futuresRequest<ContangoAnalysisData>('/contango-analysis', { params })
  }

  /**
   * 获取单个期货品种的历史正反向市场分析
   * 用于分析特定品种的历史正反向趋势
   */
  async getHistoricalContangoAnalysis(
    symbol: string,
    startDate?: string,
    endDate?: string,
    limit: number = 30
  ): Promise<ApiResponse<HistoricalContangoData>> {
    const params: Record<string, any> = { limit }
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    
    return this.futuresRequest<HistoricalContangoData>(`/contango-analysis/${symbol}`, { params })
  }
}

export const futuresAPI = new FuturesAPI()
