// 回测相关的TypeScript接口定义

export interface BacktestConfig {
  strategy_name: string
  strategy_type: 'multi_trend' | 'boll' | 'taishang_3factor'
  initial_cash: number
  start_date: string
  end_date: string
  benchmark: string
  // 交易成本配置
  commission_rate?: number  // 手续费率（万一）
  stamp_tax_rate?: number   // 印花税率（千一，仅卖出）
  slippage_rate?: number    // 滑点率（千一）
  params?: Record<string, any>
}

export interface BacktestBasicMetrics {
  total_return: number
  annual_return: number
  volatility: number
  sharpe_ratio: number
  max_drawdown: number
  calmar_ratio: number
  trading_days: number
}

export interface BacktestAdvancedMetrics {
  sortino_ratio: number
  var_5: number
  cvar_5: number
  max_consecutive_losses: number
  winning_days_ratio: number
  avg_win_loss_ratio: number
}

export interface BacktestTradeMetrics {
  total_trades: number
  buy_trades: number
  sell_trades: number
  total_commission: number
  total_stamp_tax: number
  total_fees: number
  monthly_trade_frequency: number
  avg_holding_period_days: number
}

export interface BacktestPerformanceReport {
  strategy_name: string
  report_date: string
  basic_metrics: BacktestBasicMetrics
  advanced_metrics: BacktestAdvancedMetrics
  trade_metrics: BacktestTradeMetrics
  portfolio_summary: {
    final_value: number
    initial_value: number
    cash_ratio: number
    positions_count: number
    backtest_period: {
      start_date: string
      end_date: string
    }
  }
}

export interface BacktestPortfolioSummary {
  total_value: number
  cash: number
  positions_value: number
  cash_ratio: number
  total_positions: number
  total_unrealized_pnl: number
  cumulative_return: number
  max_drawdown: number
  total_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
}

export interface BacktestTradingSummary {
  orders: {
    total: number
    executed: number
    pending: number
    cancelled: number
    rejected: number
  }
  trades: {
    total: number
    buy_trades: number
    sell_trades: number
  }
  fees: {
    total_commission: number
    total_stamp_tax: number
    total_fees: number
  }
}

export interface BacktestChartData {
  portfolio_value: {
    title: string
    type: string
    data: {
      dates: string[]
      portfolio_values: number[]
      cumulative_returns: number[]
      daily_returns: number[]
    }
    config: any
  }
  returns_distribution: {
    title: string
    type: string
    data: {
      bin_centers: number[]
      frequencies: number[]
      statistics: {
        mean: number
        std: number
        skewness: number
        kurtosis: number
      }
    }
    config: any
  }
  drawdown: {
    title: string
    type: string
    data: {
      dates: string[]
      portfolio_values: number[]
      peak_values: number[]
      drawdown: number[]
    }
    config: any
  }
  monthly_heatmap: {
    title: string
    type: string
    data: {
      data: [number, number, number][]
      years: number[]
      months: string[]
    }
    config: any
  }
  trades_analysis: {
    title: string
    type: string
    data: {
      trade_counts: {
        dates: string[]
        counts: number[]
      }
      trade_types: {
        buy_count: number
        sell_count: number
      }
      trade_amounts: {
        buy_amount: number
        sell_amount: number
      }
    }
    config: any
  }
}

export interface BacktestResult {
  backtest_config: {
    initial_cash: number
    start_date: string
    end_date: string
    total_stocks: number
    trading_days: number
  }
  strategy_info: {
    strategy_name: string
    strategy_version: string
    strategy_type: string
    max_positions: number
    max_single_weight: number
    min_resonance_score: number
    strong_resonance_score: number
    current_positions: number
    buy_signals_count: number
    sell_signals_count: number
    total_signals: number
    total_trades: number
    description: string
  }
  performance_report: BacktestPerformanceReport
  portfolio_summary: BacktestPortfolioSummary
  trading_summary: BacktestTradingSummary
  chart_files: string[]
  chart_data: BacktestChartData
  benchmark_data?: {
    benchmark_code: string
    cumulative_returns: number[]
    final_return: number
    data_points: number
    is_simulated?: boolean
  }
}

export interface BacktestTask {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  created_at: string
  updated_at?: string
  user_id: string
  config: BacktestConfig
  result?: BacktestResult
  error_message?: string
}

export interface BacktestDisplayMetrics {
  totalReturn: number
  annualReturn: number
  benchmarkReturn: number
  sharpeRatio: number
  beta: number
  alpha: number
  maxDrawdown: number
  winRate: number
  totalTrades: number
  calmarRatio: number
  sortinoRatio: number
  volatility: number
  profit2Loss: number
}

export interface Position {
  symbol: string
  name: string
  shares: number
  avg_price: number
  current_price: number
  market_value: number
  unrealized_pnl: number
  weight: number
}

export interface Trade {
  trade_id?: string
  date: string
  trade_date?: string
  symbol: string
  stock_code?: string
  name?: string
  action?: 'buy' | 'sell'
  order_type?: 'buy' | 'sell'
  shares: number
  quantity?: number
  price: number
  amount?: number
  net_amount?: number
  commission: number
  stamp_tax: number
  total_cost?: number
  pnl?: number
}

// API响应类型定义
export interface PositionsApiResponse {
  portfolio_history: Position[]
  total: number
}

export interface TradesApiResponse {
  trades: Trade[]
  total: number
}