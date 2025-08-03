import { apiClient, ApiResponse } from './base'

// 期权基本信息接口
export interface OptionsBasicInfo {
  ts_code: string
  name: string
  call_put: string
  exercise_type: string
  exercise_price: number
  underlying: string
  list_date: string
  delist_date: string
  exchange: string
  opt_type: string
}

// 期权日线数据接口
export interface OptionsDailyData {
  ts_code: string
  trade_date: string
  open: number
  high: number
  low: number
  close: number
  settle: number
  vol: number
  oi: number
  amount: number
}

// 期权API类
export class OptionsAPI {
  private baseURL = '/options'

  // 获取期权基本信息列表
  async getBasicList(params?: {
    underlying?: string
    call_put?: string
    exchange?: string
    limit?: number
    offset?: number
  }): Promise<ApiResponse<OptionsBasicInfo[]>> {
    return apiClient.get(`${this.baseURL}/basic/list`, params)
  }

  // 获取指定期权基本信息
  async getBasicInfo(tsCode: string): Promise<ApiResponse<OptionsBasicInfo>> {
    return apiClient.get(`${this.baseURL}/basic/${tsCode}`)
  }

  // 获取期权日线数据
  async getDailyData(tsCode: string, params?: {
    start_date?: string
    end_date?: string
    limit?: number
  }): Promise<ApiResponse<OptionsDailyData[]>> {
    return apiClient.get(`${this.baseURL}/daily/${tsCode}`, params)
  }

  // 获取期权链数据
  async getOptionsChain(underlying: string, params?: {
    trade_date?: string
    call_put?: string
    limit?: number
  }): Promise<ApiResponse<OptionsBasicInfo[]>> {
    return apiClient.get(`${this.baseURL}/chain/${underlying}`, params)
  }

  // 搜索期权
  async searchOptions(params: {
    keyword: string
    call_put?: string
    exchange?: string
    limit?: number
  }): Promise<ApiResponse<OptionsBasicInfo[]>> {
    return apiClient.get(`${this.baseURL}/search`, params)
  }

  // 获取期权统计摘要
  async getStatsSummary(params?: {
    underlying?: string
    call_put?: string
    trade_date?: string
  }): Promise<ApiResponse<{
    total_contracts: number
    active_contracts: number
    total_volume: number
    total_amount: number
    total_oi: number
    avg_volume: number
    avg_oi: number
  }>> {
    return apiClient.get(`${this.baseURL}/stats/summary`, params)
  }

  // 按到期日查询期权
  async getOptionsByExpiry(params: {
    expiry_date: string
    underlying?: string
    call_put?: string
    limit?: number
  }): Promise<ApiResponse<OptionsBasicInfo[]>> {
    return apiClient.get(`${this.baseURL}/expiry`, params)
  }

  // 获取最新期权数据
  async getLatestData(params?: {
    underlying?: string
    call_put?: string
    limit?: number
    sort_by?: string
  }): Promise<ApiResponse<(OptionsBasicInfo & OptionsDailyData)[]>> {
    return apiClient.get(`${this.baseURL}/latest`, params)
  }

  // 获取期权活跃度分析
  async getActivityAnalysis(params?: {
    underlying?: string
    call_put?: string
    trade_date?: string
  }): Promise<ApiResponse<{
    total_volume: number
    total_amount: number
    total_oi: number
    active_contracts: number
    top_by_volume: (OptionsBasicInfo & OptionsDailyData)[]
    top_by_oi: (OptionsBasicInfo & OptionsDailyData)[]
  }>> {
    return apiClient.get(`${this.baseURL}/activity`, params)
  }

  // 获取期权价格趋势
  async getPriceTrend(tsCode: string, params?: {
    days?: number
    indicator?: string
  }): Promise<ApiResponse<OptionsDailyData[]>> {
    return apiClient.get(`${this.baseURL}/trend/${tsCode}`, params)
  }

  // 获取期权持仓量分析
  async getOIAnalysis(params?: {
    underlying?: string
    call_put?: string
    trade_date?: string
  }): Promise<ApiResponse<{
    total_oi: number
    avg_oi: number
    max_oi: number
    min_oi: number
    oi_distribution: { range: string; count: number }[]
    top_contracts: { ts_code: string; oi: number }[]
  }>> {
    return apiClient.get(`${this.baseURL}/oi-analysis`, params)
  }
}

// 导出API实例
export const optionsAPI = new OptionsAPI()

// 导出默认实例
export default optionsAPI