import { apiClient } from './base'
import type { ApiResponse } from './base'

// 股票池类型定义
export interface StockPool {
  id: string
  name: string
  description?: string
  stock_count?: number
  created_at: string
  updated_at: string
}

export interface StockPoolStock {
  ts_code: string
  name: string
  industry?: string
  added_at: string
}

export interface CreateStockPoolRequest {
  name: string
  description?: string
}

export interface StockPoolDetailResponse {
  pool: StockPool
  stocks: StockPoolStock[]
}

// 获取用户股票池列表
export const getStockPools = (): Promise<ApiResponse<StockPool[]>> => {
  return apiClient.get<StockPool[]>('/user/stock-pools')
}

// 创建股票池
export const createStockPool = (data: CreateStockPoolRequest): Promise<ApiResponse<StockPool>> => {
  return apiClient.post<StockPool>('/user/stock-pools', data)
}

// 获取股票池详情
export const getStockPoolDetail = (poolId: string): Promise<ApiResponse<StockPoolDetailResponse>> => {
  return apiClient.get<StockPoolDetailResponse>(`/user/stock-pools/${poolId}`)
}

// 删除股票池
export const deleteStockPool = (poolId: string): Promise<ApiResponse<{ success: boolean }>> => {
  return apiClient.delete<{ success: boolean }>(`/user/stock-pools/${poolId}`)
}

// 向股票池添加股票
export const addStockToPool = (poolId: string, stocks: any[]): Promise<ApiResponse<{ success: number; failed: number }>> => {
  return apiClient.post<{ success: number; failed: number }>(`/user/stock-pools/${poolId}/stocks`, { stocks: stocks })
}

// 从股票池移除股票
export const removeStockFromPool = (poolId: string, stockCode: string): Promise<ApiResponse<{ success: boolean }>> => {
  return apiClient.delete<{ success: boolean }>(`/user/stock-pools/${poolId}/stocks/${stockCode}`)
}

// 导出股票池
export const exportStockPool = (poolId: string, format: 'excel' | 'csv' = 'excel'): Promise<ApiResponse<Blob>> => {
  return apiClient.get<Blob>(`/user/stock-pools/${poolId}/export`, { format })
}