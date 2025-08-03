/**
 * 回测API客户端
 * 提供回测相关的API接口
 */

import { BaseApiClient, ApiResponse } from './base'
import type { BacktestConfig, BacktestResult, BacktestTask, Position, Trade, PositionsApiResponse, TradesApiResponse } from '../types/backtest'

export class BacktestAPI extends BaseApiClient {
  
  /**
   * 开始回测
   */
  async startBacktest(config: BacktestConfig): Promise<ApiResponse<{ task_id: string }>> {
    return this.post<{ task_id: string }>('/backtest/run', config)
  }

  /**
   * 获取回测结果
   */
  async getResult(taskId: string): Promise<ApiResponse<BacktestResult>> {
    return this.get<BacktestResult>(`/backtest/result/${taskId}`)
  }

  /**
   * 获取回测任务状态
   */
  async getTask(taskId: string): Promise<ApiResponse<BacktestTask>> {
    return this.get<BacktestTask>(`/backtest/task/${taskId}`)
  }

  /**
   * 获取回测任务状态（别名方法）
   */
  async getTaskStatus(taskId: string): Promise<ApiResponse<BacktestTask>> {
    return this.getTask(taskId)
  }

  /**
   * 获取回测任务列表
   */
  async getTasks(): Promise<ApiResponse<BacktestTask[]>> {
    return this.get<BacktestTask[]>('/backtest/tasks')
  }

  /**
   * 获取持仓信息
   */
  async getPositions(taskId: string): Promise<ApiResponse<PositionsApiResponse>> {
    return this.get<PositionsApiResponse>(`/backtest/result/${taskId}/portfolio`)
  }

  /**
   * 获取交易记录
   */
  async getTrades(taskId: string): Promise<ApiResponse<TradesApiResponse>> {
    return this.get<TradesApiResponse>(`/backtest/result/${taskId}/trades`)
  }

  /**
   * 停止回测
   */
  async stopBacktest(taskId: string): Promise<ApiResponse<any>> {
    return this.post<any>(`/backtest/stop/${taskId}`)
  }

  /**
   * 删除回测任务
   */
  async deleteTask(taskId: string): Promise<ApiResponse<any>> {
    return this.delete<any>(`/backtest/task/${taskId}`)
  }

  /**
   * 获取回测分析报告（markdown格式）
   */
  async getMarkdownReport(taskId: string): Promise<ApiResponse<{ content: string; task_id: string }>> {
    return this.get<{ content: string; task_id: string }>(`/backtest/result/${taskId}/markdown`)
  }
}

// 创建回测API实例
export const backtestApi = new BacktestAPI()