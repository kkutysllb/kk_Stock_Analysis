/**
 * 涨停板块数据API接口
 */

import { apiClient, ApiResponse } from './base'

// 涨跌停数据接口
export interface LimitData {
  ts_code: string
  name: string
  trade_date: string
  close: number
  pct_chg: number
  amount: number
  limit: string
  limit_times: number
  up_stat: string
  industry?: string
}

// 涨跌停统计接口
export interface LimitStats {
  trade_date: string
  limit_up_count: number
  limit_down_count: number
  avg_limit_ratio: number
  total_amount: number
}

// 连板天梯数据接口
export interface LimitStepData {
  ts_code: string
  name: string
  trade_date: string
  nums: number
}

// 概念板块数据接口
export interface ConceptData {
  ts_code: string
  name: string
  trade_date: string
  cons_nums: number
  days: number
  pct_chg: number
  rank: number
  up_nums: number
  up_stat: string
}

// 请求参数接口
export interface LimitQueryParams {
  trade_date?: string
  ts_code?: string
  limit_type?: 'U' | 'D'
  min_nums?: number
  days?: number
}

export const limitDataAPI = {
  // 获取涨跌停列表
  getLimitList: (params: LimitQueryParams = {}): Promise<ApiResponse<LimitData[]>> => {
    return apiClient.get('/limit_data/daily/list', params)
  },

  // 获取涨跌停统计
  getLimitStats: (params: LimitQueryParams = {}): Promise<ApiResponse<LimitStats[]>> => {
    return apiClient.get('/limit_data/daily/stats', params)
  },

  // 获取连板天梯数据
  getLimitStep: (params: LimitQueryParams = {}): Promise<ApiResponse<LimitStepData[]>> => {
    return apiClient.get('/limit_data/step/list', params)
  },

  // 获取连板天梯统计
  getLimitStepStats: (params: LimitQueryParams = {}): Promise<ApiResponse<any>> => {
    return apiClient.get('/limit_data/step/stats', params)
  },

  // 获取概念板块列表
  getConceptList: (params: LimitQueryParams = {}): Promise<ApiResponse<ConceptData[]>> => {
    return apiClient.get('/limit_data/concept/list', params)
  },

  // 获取概念板块轮动趋势
  getConceptTrend: (params: LimitQueryParams = {}): Promise<ApiResponse<any>> => {
    return apiClient.get('/limit_data/concept/trend', params)
  },

  // 获取涨跌停趋势分析
  getLimitTrendAnalysis: (params: LimitQueryParams = {}): Promise<ApiResponse<any>> => {
    return apiClient.get('/limit_data/trend/analysis', params)
  }
}