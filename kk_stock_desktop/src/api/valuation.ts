/**
 * 估值分析API接口
 * 包括相对估值分析
 */

import { BaseApiClient, type ApiResponse } from './base'

// 创建API客户端实例
const apiClient = new BaseApiClient()

// ==================== 相对估值分析接口 ====================

// 估值指标接口
export interface ValuationMetrics {
  pe_ratio: number | null
  pb_ratio: number | null
  ps_ratio: number | null
  pcf_ratio: number | null
  market_cap: number | null
  end_date: string
}

// 行业对比接口
export interface IndustryComparison {
  industry: string
  industry_pe_percentile: number | null
  industry_pb_percentile: number | null
  industry_ps_percentile: number | null
  industry_pe_median: number | null
  industry_pb_median: number | null
  industry_ps_median: number | null
  industry_sample_count: number
  pe_rating: string
  pb_rating: string
  ps_rating: string
  overall_rating: string
}

// 历史估值分析接口
export interface HistoricalValuation {
  pe_percentile_1y: number | null
  pe_percentile_3y: number | null
  pe_percentile_5y: number | null
  pb_percentile_1y: number | null
  pb_percentile_3y: number | null
  pb_percentile_5y: number | null
  ps_percentile_1y: number | null
  ps_percentile_3y: number | null
  ps_percentile_5y: number | null
  historical_pe_rating: string
  historical_pb_rating: string
  historical_ps_rating: string
}

// 相对估值分析结果接口
export interface RelativeValuationResult {
  ts_code: string
  stock_name: string
  industry: string
  analysis_date: string
  current_metrics: ValuationMetrics
  industry_comparison: IndustryComparison
  historical_analysis: HistoricalValuation
  overall_rating: string
  rating_score: number
  investment_advice: string
  risk_warnings: string[]
  analysis_summary: string
  analyzed_at: string
}

// 批量分析请求接口
export interface BatchAnalysisRequest {
  ts_codes: string[]
  end_date?: string
}

// 批量分析结果接口
export interface BatchAnalysisResult {
  total_count: number
  success_count: number
  results: Record<string, {
    stock_name: string
    industry: string
    overall_rating: string
    rating_score: number
    investment_advice: string
    current_pe: number | null
    current_pb: number | null
    industry_pe_percentile: number | null
    historical_pe_percentile_3y: number | null
  }>
}


// ==================== API方法定义 ====================

// 相对估值分析API
export const relativeValuationAPI = {
  // 分析个股相对估值
  async analyzeStock(ts_code: string, end_date?: string): Promise<ApiResponse<RelativeValuationResult>> {
    const params: Record<string, any> = {}
    if (end_date) {
      params.end_date = end_date
    }
    return apiClient.get<RelativeValuationResult>(`/relative-valuation/analyze/${ts_code}`, params)
  },

  // 批量分析多只股票
  async batchAnalyze(request: BatchAnalysisRequest): Promise<ApiResponse<BatchAnalysisResult>> {
    return apiClient.post<BatchAnalysisResult>('/relative-valuation/batch-analyze', request)
  },

  // 行业估值对比
  async industryComparison(industry: string, end_date?: string): Promise<ApiResponse<any>> {
    const params: Record<string, any> = { industry }
    if (end_date) {
      params.end_date = end_date
    }
    return apiClient.get<any>('/relative-valuation/industry-comparison', params)
  },

  // 历史估值趋势
  async historicalTrend(ts_code: string, start_date?: string, end_date?: string): Promise<ApiResponse<any>> {
    const params: Record<string, any> = {}
    if (start_date) {
      params.start_date = start_date
    }
    if (end_date) {
      params.end_date = end_date
    }
    return apiClient.get<any>(`/relative-valuation/historical-trend/${ts_code}`, params)
  }
}

// 导出所有接口和API方法
export {
  apiClient as valuationApiClient
}