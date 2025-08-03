/**
 * API模块统一导出
 * 提供所有API客户端的统一入口
 */

// 导出基础API客户端
export { BaseApiClient, apiClient, get, post, put, del as delete, patch } from './base'
export type { ApiResponse, RequestConfig, ApiError, NetworkError, TimeoutError } from './base'

// 导出市场数据API
export { MarketAPI, marketAPI } from './market'
export type { IndexData, DragonTigerItem, DragonTigerSummary } from './market'

// 导出内容生成API
// 智能收评API已删除
// 智能收评类型已删除

// 导出期货数据API
export { FuturesAPI, futuresAPI } from './futures'
export type { FuturesBasicInfo, FuturesKlineData, FuturesHoldingData, FuturesHoldingSummary } from './futures'

// 导出回测API
export { BacktestAPI, backtestApi } from './backtest'
export type { BacktestConfig, BacktestResult, BacktestTask, BacktestDisplayMetrics, Position, Trade } from '../types/backtest'

// 导出估值API
export * from './valuation'

// 导出模拟交易API
export { SimulationApiClient, simulationApi } from './simulation'
export type { DashboardPortfolioData, SimulationAccountResponse, SimulationPositionResponse } from './simulation'

// 导入API实例
import { marketAPI } from './market'
// 智能收评API已删除
import { futuresAPI } from './futures'
import { backtestApi } from './backtest'
import { simulationApi } from './simulation'

// 投资组合API（使用真实的模拟交易数据）
class PortfolioAPI {
  async getPortfolioData() {
    try {
      // 使用真实的模拟交易数据
      const response = await simulationApi.getDashboardPortfolioData()
      
      if (response.success && response.data) {
        return {
          success: true,
          data: response.data
        }
      } else {
        throw new Error(response.error || '获取模拟交易数据失败')
      }
    } catch (error) {
      console.error('获取投资组合数据失败，使用降级数据:', error)
      
      // // 降级到模拟数据
      // return {
      //   success: true,
      //   data: {
      //     totalCapital: 3000000,
      //     currentValue: 3000000,
      //     totalReturn: 0,
      //     totalReturnRate: 0,
      //     dailyReturn: 0,
      //     dailyReturnRate: 0,
      //     holdingStocks: 0,
      //     predictionAccuracy: 0,
      //     lastUpdate: new Date()
      //   }
      // }
    }
  }
}

export const portfolioAPI = new PortfolioAPI()

// 创建统一的API实例对象
export const api = {
  market: marketAPI,
  // content: contentAPI, // 智能收评API已删除
  portfolio: portfolioAPI,
  futures: futuresAPI,
  backtest: backtestApi,
  simulation: simulationApi,
} as const

// 默认导出统一API对象
export default api