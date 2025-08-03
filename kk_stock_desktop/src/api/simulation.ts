/**
 * 模拟交易API
 * 提供模拟交易系统相关接口
 */

import { BaseApiClient, ApiResponse } from './base'

// ==================== 请求接口 ====================

export interface BuyRequest {
  stock_code: string
  stock_name: string
  quantity: number
  price?: number
  order_type?: 'MARKET' | 'LIMIT'
  strategy_name?: string
  remarks?: string
}

export interface SellRequest {
  stock_code: string
  stock_name: string
  quantity: number
  price?: number
  order_type?: 'MARKET' | 'LIMIT'
  strategy_name?: string
  remarks?: string
}

export interface TradeHistoryQuery {
  page?: number
  page_size?: number
  stock_code?: string
  start_date?: string
  end_date?: string
  strategy_name?: string
}

export interface BatchQuoteRequest {
  stock_codes: string[]
}

// ==================== 响应接口 ====================

export interface SimulationAccountResponse {
  user_id: string
  account_name: string
  initial_capital: number
  available_cash: number
  frozen_cash: number
  total_assets: number
  total_market_value: number
  daily_return: number
  daily_return_rate: number
  total_return: number
  total_return_rate: number
  max_drawdown: number
  win_rate: number
  trade_count: number
  profit_trades: number
  loss_trades: number
  create_time: string
  last_update_time: string
  status: number
}

export interface SimulationPositionResponse {
  user_id: string
  stock_code: string
  stock_name: string
  market: string
  board_type: string
  total_quantity: number
  available_quantity: number
  frozen_quantity: number
  avg_cost: number
  current_price: number
  market_value: number
  cost_value: number
  unrealized_pnl: number
  unrealized_pnl_rate: number
  last_price_update: string
  position_date: string
  update_time: string
}

export interface SimulationTradeResponse {
  user_id: string
  trade_id: string
  stock_code: string
  stock_name: string
  trade_type: string
  order_type: string
  quantity: number
  price: number
  amount: number
  commission: number
  stamp_tax: number
  transfer_fee: number
  slippage: number
  total_cost: number
  trade_source: string
  strategy_name?: string
  trade_time: string
  settlement_date: string
  status: string
  remarks?: string
}

export interface SimulationPositionListResponse {
  total: number
  data: SimulationPositionResponse[]
}

export interface SimulationTradeListResponse {
  total: number
  page: number
  page_size: number
  total_pages: number
  data: SimulationTradeResponse[]
}

export interface StockQuote {
  stock_code: string
  current_price: number
  update_time: string
}

export interface BatchQuoteResponse {
  quotes: StockQuote[]
  total: number
  update_time: string
}

export interface TradingCostCalculation {
  amount: number
  trade_type: string
  market: string
  commission: number
  stamp_tax: number
  transfer_fee: number
  slippage: number
  total_cost: number
  net_amount: number
}

export interface AccountSnapshot {
  user_id: string
  snapshot_date: string
  total_assets: number
  available_cash: number
  total_market_value: number
  daily_return: number
  daily_return_rate: number
  cumulative_return: number
  cumulative_return_rate: number
  position_count: number
  trade_count: number
  create_time: string
}

// ==================== 策略自动化接口 ====================

export interface StrategyActivateRequest {
  strategy_name: string
  allocated_cash: number
  custom_params?: Record<string, any>
}

export interface StrategyStatusResponse {
  strategy_name: string
  is_active: boolean
  last_execution: string | null
  next_run_time: string | null
  current_positions: number
  execution_count: number
  total_trades: number
}

export interface StrategyPerformanceResponse {
  strategy_name: string
  total_return: number
  total_return_rate: number
  win_rate: number
  max_drawdown: number
  sharpe_ratio: number
  trade_count: number
}

export interface StrategyPositionResponse {
  stock_code: string
  stock_name: string
  quantity: number
  avg_cost: number
  current_price: number
  unrealized_pnl: number
  unrealized_pnl_rate: number
}

// ==================== Dashboard数据接口 ====================

export interface DashboardPortfolioData {
  totalCapital: number      // 总资本（初始资金）
  currentValue: number      // 当前总价值
  totalReturn: number       // 总收益金额
  totalReturnRate: number   // 总收益率
  dailyReturn: number       // 每日收益金额
  dailyReturnRate: number   // 每日收益率
  holdingStocks: number     // 持仓股数
  availableCash: number     // 可用资金
  lastUpdate: Date          // 最后更新时间
}

/**
 * 模拟交易API客户端
 */
export class SimulationApiClient extends BaseApiClient {
  
  // ==================== 模拟账户接口 ====================
  
  /**
   * 获取模拟账户信息
   */
  async getAccount(): Promise<ApiResponse<SimulationAccountResponse>> {
    return this.get('/api/simulation/account')
  }
  
  /**
   * 初始化模拟账户
   */
  async initAccount(initialCapital: number = 3000000): Promise<ApiResponse<SimulationAccountResponse>> {
    return this.post('/api/simulation/account/init', { initial_capital: initialCapital })
  }
  
  /**
   * 重置模拟账户
   */
  async resetAccount(): Promise<ApiResponse<{ message: string; success: boolean }>> {
    return this.post('/api/simulation/account/reset', {})
  }
  
  /**
   * 获取账户历史快照
   */
  async getAccountSnapshots(days: number = 30): Promise<ApiResponse<AccountSnapshot[]>> {
    return this.get(`/api/simulation/account/snapshots?days=${days}`)
  }
  
  // ==================== 持仓管理接口 ====================
  
  /**
   * 获取持仓列表
   */
  async getPositions(): Promise<ApiResponse<SimulationPositionListResponse>> {
    return this.get('/api/simulation/positions')
  }
  
  /**
   * 获取单只股票持仓
   */
  async getPosition(stockCode: string): Promise<ApiResponse<SimulationPositionResponse>> {
    return this.get(`/api/simulation/positions/${stockCode}`)
  }
  
  // ==================== 交易执行接口 ====================
  
  /**
   * 提交买入订单
   */
  async buyStock(request: BuyRequest): Promise<ApiResponse<{ message: string; trade_id: string; success: boolean }>> {
    return this.post('/api/simulation/trade/buy', request)
  }
  
  /**
   * 提交卖出订单
   */
  async sellStock(request: SellRequest): Promise<ApiResponse<{ message: string; trade_id: string; success: boolean }>> {
    return this.post('/api/simulation/trade/sell', request)
  }
  
  // ==================== 交易记录接口 ====================
  
  /**
   * 获取交易记录
   */
  async getTrades(query: TradeHistoryQuery = {}): Promise<ApiResponse<SimulationTradeListResponse>> {
    const params = new URLSearchParams()
    
    if (query.page) params.append('page', query.page.toString())
    if (query.page_size) params.append('page_size', query.page_size.toString())
    if (query.stock_code) params.append('stock_code', query.stock_code)
    if (query.start_date) params.append('start_date', query.start_date)
    if (query.end_date) params.append('end_date', query.end_date)
    if (query.strategy_name) params.append('strategy_name', query.strategy_name)
    
    const url = params.toString() ? `/api/simulation/trades?${params}` : '/api/simulation/trades'
    return this.get(url)
  }
  
  /**
   * 获取交易详情
   */
  async getTradeDetail(tradeId: string): Promise<ApiResponse<SimulationTradeResponse>> {
    return this.get(`/api/simulation/trades/${tradeId}`)
  }
  
  // ==================== 行情数据接口 ====================
  
  /**
   * 获取实时股价
   */
  async getStockQuote(stockCode: string): Promise<ApiResponse<StockQuote>> {
    return this.get(`/api/simulation/quote/${stockCode}`)
  }
  
  /**
   * 批量获取股价
   */
  async getBatchQuotes(request: BatchQuoteRequest): Promise<ApiResponse<BatchQuoteResponse>> {
    return this.post('/api/simulation/quotes', request)
  }
  
  // ==================== 费用计算接口 ====================
  
  /**
   * 计算交易费用
   */
  async calculateTradingCost(
    amount: number, 
    tradeType: 'BUY' | 'SELL', 
    market: 'SH' | 'SZ' = 'SH'
  ): Promise<ApiResponse<TradingCostCalculation>> {
    return this.get(`/api/simulation/trading-cost?amount=${amount}&trade_type=${tradeType}&market=${market}`)
  }
  
  // ==================== 交易日历接口 ====================
  
  /**
   * 获取交易日历
   */
  async getTradingCalendar(): Promise<ApiResponse<any>> {
    return this.get('/api/simulation/calendar')
  }
  
  // ==================== Dashboard数据转换 ====================
  
  /**
   * 获取Dashboard组合数据
   */
  async getDashboardPortfolioData(): Promise<ApiResponse<DashboardPortfolioData>> {
    try {
      // 获取账户信息
      const accountResponse = await this.getAccount()
      if (!accountResponse.success || !accountResponse.data) {
        throw new Error('获取账户信息失败')
      }
      
      const account = accountResponse.data
      
      // 获取持仓信息
      const positionsResponse = await this.getPositions()
      
      // 兼容处理：由于API响应结构不同，需要灵活处理
      let positions: any[] = []
      if (positionsResponse && (positionsResponse.success !== false)) {
        if (positionsResponse.data && positionsResponse.data.data) {
          // 标准格式: {success: true, data: {total: 3, data: [...]}}
          positions = positionsResponse.data.data || []
        } else if (positionsResponse.data && Array.isArray(positionsResponse.data)) {
          // 直接数组格式: {success: true, data: [...]}
          positions = positionsResponse.data
        } else if (positionsResponse.data && positionsResponse.data.total !== undefined) {
          // 模拟交易格式: {total: 3, data: [...]}
          positions = positionsResponse.data.data || []
        }
      }
      
      // 转换为Dashboard需要的格式
      const portfolioData: DashboardPortfolioData = {
        totalCapital: account.initial_capital,
        currentValue: account.total_assets,
        totalReturn: account.total_return,
        totalReturnRate: account.total_return_rate,
        dailyReturn: account.daily_return,
        dailyReturnRate: account.daily_return_rate,
        holdingStocks: positions.length,
        availableCash: account.available_cash,
        lastUpdate: new Date()
      }
      
      return {
        success: true,
        data: portfolioData,
        timestamp: new Date().toISOString()
      }
      
    } catch (error) {
      console.error('获取Dashboard组合数据失败:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取数据失败',
        timestamp: new Date().toISOString()
      }
    }
  }
  
  // ==================== 系统管理接口 ====================
  
  /**
   * 处理T+1交割（管理员功能）
   */
  async processSettlement(): Promise<ApiResponse<{ message: string; success: boolean }>> {
    return this.post('/api/simulation/admin/process-settlement', {})
  }
  
  /**
   * 创建每日快照（管理员功能）
   */
  async createDailySnapshots(): Promise<ApiResponse<{ message: string; success: boolean }>> {
    return this.post('/api/simulation/admin/create-snapshots', {})
  }
  
  // ==================== 策略自动化接口 ====================
  
  /**
   * 激活策略自动交易
   */
  async activateStrategy(request: StrategyActivateRequest): Promise<ApiResponse<{ message: string; success: boolean }>> {
    // 后端使用Query参数，需要通过URL参数传递
    const params = new URLSearchParams({
      strategy_name: request.strategy_name,
      allocated_cash: request.allocated_cash.toString()
    })
    
    if (request.custom_params) {
      // 如果有自定义参数，作为JSON字符串传递
      params.append('custom_params', JSON.stringify(request.custom_params))
    }
    
    return this.post(`/api/simulation/strategy/activate?${params.toString()}`)
  }
  
  /**
   * 停用策略自动交易
   */
  async deactivateStrategy(strategyName: string): Promise<ApiResponse<{ message: string; success: boolean }>> {
    // 后端使用Query参数
    return this.post(`/api/simulation/strategy/deactivate?strategy_name=${encodeURIComponent(strategyName)}`)
  }
  
  /**
   * 获取策略状态
   */
  async getStrategyStatus(strategyName: string): Promise<ApiResponse<StrategyStatusResponse>> {
    // 获取所有策略状态，然后筛选指定策略
    const response = await this.get('/api/simulation/strategy/status')
    if (response.success && response.data && response.data.strategies) {
      // 从所有策略中找到指定策略
      const strategy = response.data.strategies.find((s: any) => s.strategy_name === strategyName)
      if (strategy) {
        return {
          success: true,
          data: {
            strategy_name: strategy.strategy_name,
            is_active: strategy.is_active,
            last_execution: strategy.last_execution,
            next_run_time: strategy.next_run_time,
            current_positions: strategy.current_positions,
            execution_count: strategy.execution_count,
            total_trades: strategy.total_trades
          }
        }
      } else {
        // 策略不存在或未配置，返回默认状态
        return {
          success: true,
          data: {
            strategy_name: strategyName,
            is_active: false,
            last_execution: null,
            next_run_time: null,
            current_positions: 0,
            execution_count: 0,
            total_trades: 0
          }
        }
      }
    }
    return response
  }
  
  /**
   * 获取策略绩效分析
   */
  async getStrategyPerformance(strategyName: string): Promise<ApiResponse<StrategyPerformanceResponse>> {
    return this.get(`/api/simulation/strategy/performance?strategy_name=${strategyName}`)
  }
  
  /**
   * 获取策略持仓
   */
  async getStrategyPositions(strategyName: string): Promise<ApiResponse<StrategyPositionResponse[]>> {
    return this.get(`/api/simulation/strategy/positions?strategy_name=${strategyName}`)
  }
  
  /**
   * 获取所有策略配置信息
   */
  async getStrategyConfigs(): Promise<ApiResponse<any>> {
    return this.get('/api/simulation/strategy/configs')
  }
}

// 创建模拟交易API实例
export const simulationApi = new SimulationApiClient()

// 导出默认实例
export default simulationApi