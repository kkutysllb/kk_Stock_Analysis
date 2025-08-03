import { apiClient } from './base'



// 新增：专门策略筛选参数
export interface StrategyScreeningParams {
  market_cap?: string  // large/mid/small/all
  stock_pool?: string  // all/main/gem/star
  limit?: number
}

// 高股息策略专用参数
export interface DividendStrategyParams extends StrategyScreeningParams {
  dividend_yield_min?: number
  payout_ratio_min?: number
  dividend_fundraising_ratio_min?: number
  net_cash_min?: number
}

// 技术突破策略专用参数
export interface TechnicalBreakthroughParams extends StrategyScreeningParams {
  rsi_min?: number
  rsi_max?: number
  volume_ratio_min?: number
  macd_requirement?: boolean
  ma_alignment?: boolean
  bollinger_position?: string
}

// 超跌反弹策略专用参数
export interface OversoldReboundParams extends StrategyScreeningParams {
  rsi_min?: number
  rsi_max?: number
  volume_ratio_min?: number
  pe_max?: number
  pb_max?: number
  decline_days?: number
}

// 连板龙头策略专用参数
export interface LimitUpLeaderParams extends StrategyScreeningParams {
  min_limit_times?: number
  max_limit_times?: number
  max_open_times?: number
  min_turnover?: number
  max_turnover?: number
}

// 资金趋势跟踪策略专用参数
export interface FundFlowParams extends StrategyScreeningParams {
  margin_buy_trend_min?: number
  margin_balance_growth_min?: number
  margin_activity_min?: number
  short_sell_trend_min?: number
  large_order_inflow_min?: number
  super_large_inflow_min?: number
  fund_continuity_min?: number
  institutional_ratio_min?: number
  industry_rank_max?: number
  industry_strength_min?: number
  fund_tracking_score_min?: number
}

export interface TechnicalConditions {
  rsi_range?: [number, number]
  macd_signal?: string
  ma_trend?: string
}

export interface FundamentalConditions {
  pe_min?: number
  pe_max?: number
  pb_min?: number
  pb_max?: number
  roe_min?: number
  roe_max?: number
}

export interface SpecialConditions {
  limit_days?: number
  dragon_tiger?: boolean
}

export interface AdvancedScreeningParams {
  strategy_name: string
  strategy_type: string
  technical?: TechnicalConditions
  fundamental?: FundamentalConditions
  special?: SpecialConditions
  stock_pool?: string[]
  limit?: number
}

export interface StrategyTemplate {
  id: string
  name: string
  description: string
  strategy_type: string
  conditions: any
  is_system: boolean
}

export interface ScreeningResult {
  ts_code: string
  name: string
  close?: number
  pct_chg?: number
  pe?: number
  pb?: number
  total_mv?: number
  score?: number
  industry?: string
  concept?: string
  market?: string
  technical?: any
  fundamental?: any
  special?: any
}

export interface ScreeningResponse {
  strategy_name: string
  strategy_type: string
  total_count: number
  screening_time: string
  results: ScreeningResult[]
  saved_to_pool: boolean
  pool_name?: string
}

export interface ScreeningHistory {
  id: string
  name: string
  conditions: any
  result_count: number
  created_at: string
}

// 专门策略筛选接口
export const valueInvestmentScreening = (params: StrategyScreeningParams) => {
  return apiClient.post<ScreeningResponse>('/strategy/value-investment', params)
}

export const growthStockScreening = (params: StrategyScreeningParams) => {
  return apiClient.post<ScreeningResponse>('/strategy/growth-stock', params)
}

export const momentumBreakthroughScreening = (params: StrategyScreeningParams) => {
  return apiClient.post<ScreeningResponse>('/strategy/momentum-breakthrough', params)
}

export const highDividendScreening = (params: DividendStrategyParams) => {
  return apiClient.post<ScreeningResponse>('/strategy/high-dividend', params)
}

export const technicalBreakthroughScreening = (params: TechnicalBreakthroughParams) => {
  return apiClient.post<ScreeningResponse>('/strategy/technical-breakthrough', params)
}

export const oversoldReboundScreening = (params: OversoldReboundParams) => {
  return apiClient.post<ScreeningResponse>('/strategy/oversold-rebound', params)
}

export const limitUpLeaderScreening = (params: LimitUpLeaderParams) => {
  return apiClient.post<ScreeningResponse>('/strategy/limit-up-leader', params)
}

export const fundFlowTrackingScreening = (params: FundFlowParams) => {
  return apiClient.post<ScreeningResponse>('/strategy/fund-flow-tracking', params)
}

// 统一策略筛选接口 - 使用策略模板
export const unifiedStrategyScreening = (strategy_type: string, params: StrategyScreeningParams) => {
  // 根据策略类型获取对应的数据库模板ID（与数据库实际ID保持一致）
  const templateMapping: { [key: string]: string } = {
    'value': '686a347c09e24f7707f7b4d8',      // 价值投资策略
    'growth': '686a347c09e24f7707f7b4d9',     // 成长股策略
    'momentum': '686a78a59faddf493bb01c60',   // 动量突破策略
    'dividend': '686a71f4c51f290dcebb0742',   // 高股息策略
    'technical': '686a347c09e24f7707f7b4da',  // 技术突破策略
    'oversold': '686a347c09e24f7707f7b4db',   // 超跌反弹策略
    'limit_up': '686a347c09e24f7707f7b4dc',   // 连板龙头策略
    'fund_flow': '686a347c09e24f7707f7b4dd'   // 资金追踪策略
  }
  
  const templateId = templateMapping[strategy_type]
  if (!templateId) {
    throw new Error(`不支持的策略类型: ${strategy_type}`)
  }
  
  return apiClient.post<ScreeningResponse>(`/strategy/templates/${templateId}/apply`, params)
}

// 策略筛选映射函数
export const strategyScreeningMap = {
  'value': valueInvestmentScreening,
  'growth': growthStockScreening,
  'momentum': momentumBreakthroughScreening,
  'dividend': highDividendScreening,
  'technical': technicalBreakthroughScreening,
  'oversold': oversoldReboundScreening,
  'limit_up': limitUpLeaderScreening,
  'fund_flow': fundFlowTrackingScreening
}

// 高级筛选 - 使用兼容接口
export const advancedScreening = (params: AdvancedScreeningParams) => {
  return apiClient.post<ScreeningResponse>('/strategy/advanced-screening-compatible', params)
}

// 获取策略模板
export const getStrategyTemplates = () => {
  return apiClient.get<StrategyTemplate[]>('/strategy/templates')
}

// 应用策略模板
export const applyStrategyTemplate = (templateId: string, params?: any) => {
  return apiClient.post<ScreeningResponse>(`/strategy/templates/${templateId}/apply`, params)
}

// 保存筛选条件为模板
export const saveAsTemplate = (name: string, conditions: any) => {
  return apiClient.post<{ id: string }>('/strategy/templates', {
    name,
    conditions
  })
}

// 获取筛选历史
export const getScreeningHistory = (limit = 20) => {
  return apiClient.get<ScreeningHistory[]>('/strategy/history', { limit })
}

// 删除筛选历史
export const deleteScreeningHistory = (historyId: string) => {
  return apiClient.delete<void>(`/strategy/history/${historyId}`)
}

// 导出筛选结果
export const exportScreeningResults = (results: ScreeningResult[], format = 'excel') => {
  return apiClient.post<Blob>('/strategy/export', {
    results,
    format
  })
}

// 获取行业板块数据
export const getIndustryData = () => {
  return apiClient.get<Array<{ name: string; code: string }>>('/strategy/industries')
}

// 获取概念板块数据
export const getConceptData = () => {
  return apiClient.get<Array<{ name: string; code: string }>>('/strategy/concepts')
}

// 获取股票池列表
export const getStockPools = () => {
  return apiClient.get<Array<{ name: string; code: string; count: number }>>('/user/stock-pools')
}

// 添加到股票池
export const addToStockPool = (poolId: string, stockCodes: string[]) => {
  return apiClient.post<{ success: number; failed: number }>('/user/stock-pools/add-stocks', {
    pool_id: poolId,
    stock_codes: stockCodes
  })
}

// 获取技术指标配置
export const getTechnicalIndicators = () => {
  return apiClient.get<Array<{
    name: string
    code: string
    params: any
    description: string
  }>>('/strategy/technical-indicators')
}

// 获取基本面指标配置
export const getFundamentalIndicators = () => {
  return apiClient.get<Array<{
    name: string
    code: string
    unit: string
    description: string
  }>>('/strategy/fundamental-indicators')
}

// ==================== 策略模板分析API ====================

// 策略模板分析数据类型
export interface TemplateUsageStats {
  total_usage: number
  avg_results: number
  success_rate: number
  last_used?: string
}

export interface TemplatePerformance {
  screening_time: string
  total_count: number
  processing_time: number
}

export interface TemplateAnalytics {
  templates: Array<{
    template_id: string
    template_name: string
    total_usage: number
    avg_results: number
    success_rate: number
    last_used: string
  }>
  summary: {
    total_templates: number
    total_usage: number
    avg_success_rate: number
  }
}

export interface TemplateAnalyticsResponse {
  total_templates: number
  analytics: TemplateAnalytics[]
  generated_at: string
}

export interface PerformanceSummary {
  total_screenings: number
  total_results: number
  avg_results: number
  success_rate: number
  avg_processing_time: number
}

export interface TrendData {
  date: string
  avg_results: number
  screenings_count: number
}

export interface TemplatePerformanceResponse {
  template_id: string
  template_name: string
  analysis_period: string
  performance_summary: PerformanceSummary
  trend_analysis: TrendData[]
  recommendations: string[]
  generated_at: string
}

export interface ComparisonMetrics {
  total_screenings: number
  avg_results: number
  success_rate: number
  avg_processing_time: number
}

export interface ComparisonData {
  template_id: string
  template_name: string
  strategy_type: string
  metrics: ComparisonMetrics
}

export interface TemplateComparisonResponse {
  comparison_period: string
  templates_compared: number
  comparison_data: ComparisonData[]
  conclusions: string[]
  generated_at: string
}

export interface OptimizationSuggestion {
  type: string
  priority: 'high' | 'medium' | 'low'
  suggestion: string
  reason: string
}

export interface TemplateOptimizationResponse {
  template_id: string
  template_name: string
  optimization_type: string
  suggestions: OptimizationSuggestion[]
  generated_at: string
}

export interface BacktestSummary {
  total_test_days: number
  avg_stocks_found: number
  avg_score: number
  success_rate: number
}

export interface BacktestResult {
  date: string
  stocks_found: number
  avg_score: number
  top_stocks: string[]
}

export interface BacktestResponse {
  template_id: string
  template_name: string
  backtest_period: string
  backtest_summary: BacktestSummary
  daily_results: BacktestResult[]
  generated_at: string
}

// 获取策略模板聚合分析数据
export const getTemplateAnalytics = () => {
  return apiClient.get<TemplateAnalyticsResponse>('/strategy/templates/analytics')
}

// 获取特定策略模板的性能分析
export const getTemplatePerformance = (templateId: string, days = 30) => {
  return apiClient.get<TemplatePerformanceResponse>(`/strategy/templates/${templateId}/performance?days=${days}`)
}

// 对比多个策略模板的性能
export const compareTemplates = (templateIds: string[], days = 30) => {
  return apiClient.post<TemplateComparisonResponse>(`/strategy/templates/compare?days=${days}`, templateIds)
}

// 获取策略模板优化建议
export const optimizeTemplate = (templateId: string, optimizationType = 'performance') => {
  return apiClient.post<TemplateOptimizationResponse>(`/strategy/templates/optimize?template_id=${templateId}&optimization_type=${optimizationType}`)
}

// 策略模板历史回测分析
export const backtestTemplate = (templateId: string, backtestDays = 30, stockPool?: string[]) => {
  return apiClient.post<BacktestResponse>(`/strategy/templates/${templateId}/backtest`, {
    backtest_days: backtestDays,
    stock_pool: stockPool
  })
}