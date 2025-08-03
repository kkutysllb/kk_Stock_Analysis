import { BaseApiClient } from './base'

// ETF基本信息接口
export interface ETFBasicInfo {
  ts_code: string
  cname: string
  csname: string
  custod_name: string
  etf_type: string
  exchange: string
  extname: string
  list_date: string
  list_status: string
  mgr_name: string
  mgt_fee: number
  setup_date: string
  index_code?: string
  index_name?: string
}

// ETF日线数据接口
export interface ETFDailyData {
  trade_date: string
  ts_code: string
  amount: number
  change: number
  close: number
  high: number
  low: number
  open: number
  pct_change: number
  pre_close: number
  vol: number
}

// ETF列表响应接口
export interface ETFListResponse {
  success: boolean
  data: {
    etf_list: ETFBasicInfo[]
    count: number
    timestamp: string
  }
}

// ETF日线数据响应接口
export interface ETFDailyResponse {
  success: boolean
  data: {
    ts_code: string
    daily_data: ETFDailyData[]
    count: number
    timestamp: string
  }
}

// ETF信息响应接口
export interface ETFInfoResponse {
  success: boolean
  data: {
    etf_info: ETFBasicInfo
    timestamp: string
  }
}

class ETFApiClient extends BaseApiClient {
  constructor() {
    super()
  }
  
  private getEndpoint(path: string): string {
    return `/etf${path}`
  }

  /**
   * 获取ETF基本信息列表
   */
  async getETFList(params?: {
    market?: string
    fund_type?: string
    limit?: number
  }) {
    return this.get(this.getEndpoint('/basic/list'), params)
  }

  /**
   * 获取单个ETF的基本信息
   */
  async getETFInfo(tsCode: string) {
    return this.get(this.getEndpoint(`/basic/${tsCode}`))
  }

  /**
   * 获取ETF日线数据
   */
  async getETFDaily(
    tsCode: string,
    params?: {
      start_date?: string
      end_date?: string
      limit?: number
    }
  ) {
    return this.get(this.getEndpoint(`/daily/${tsCode}`), params)
  }

  /**
   * 搜索ETF
   */
  async searchETF(params: {
    keyword: string
    limit?: number
  }) {
    return this.get(this.getEndpoint('/search'), params)
  }

  /**
   * 获取ETF统计信息
   */
  async getETFStats() {
    return this.get(this.getEndpoint('/stats/summary'))
  }

  /**
   * 批量获取ETF日线数据
   */
  async getBatchETFDaily(data: {
    ts_codes: string[]
    start_date?: string
    end_date?: string
    limit?: number
  }) {
    return this.post(this.getEndpoint('/batch/daily'), data)
  }

  /**
   * 批量获取ETF基本信息
   */
  async getBatchETFBasic(data: {
    ts_codes: string[]
  }) {
    return this.post(this.getEndpoint('/batch/basic'), data)
  }
}

export const etfAPI = new ETFApiClient() 