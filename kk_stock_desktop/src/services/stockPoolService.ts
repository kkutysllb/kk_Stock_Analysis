import { apiClient } from '@/api/base'

// 数据类型定义
export interface StockInfo {
  ts_code: string
  name: string
  industry?: string
  market?: string
  add_time?: Date
  add_reason?: string
  tags?: string[]
}

export interface StockPool {
  pool_id: string
  pool_name: string
  description?: string
  pool_type: 'default' | 'custom' | 'strategy'
  is_default: boolean
  is_public: boolean
  is_deletable: boolean
  share_code?: string
  tags: string[]
  stock_count: number
  stocks: StockInfo[]
  create_time: Date
  update_time: Date
}

export interface CreatePoolData {
  pool_name: string
  description?: string
  pool_type?: string
  is_public?: boolean
  is_deletable?: boolean
  tags?: string[]
  stocks?: StockInfo[]
}

export interface UpdatePoolData {
  pool_name?: string
  description?: string
  is_public?: boolean
  tags?: string[]
}

export interface BatchAddData {
  pool_ids: string[]
  stocks: StockInfo[]
}

export interface BatchResult {
  success_pools: Array<{
    pool_id: string
    pool_name: string
    added_count: number
  }>
  failed_pools: Array<{
    pool_id: string
    reason: string
  }>
  total_added: number
  total_failed: number
}

export interface StockSearchResult {
  ts_code: string
  name: string
  industry?: string
  market?: string
  list_date?: string
}

/**
 * 股票池管理服务类
 * 提供完整的股票池管理功能，支持复用于各种量化策略模块
 */
export class StockPoolService {
  
  // ==================== 股票池基础操作 ====================
  
  /**
   * 获取用户所有股票池
   */
  async getUserPools(): Promise<StockPool[]> {
    const response = await apiClient.get<StockPool[]>('/user/stock-pools')
    return response.data || []
  }

  /**
   * 创建新股票池
   */
  async createPool(data: CreatePoolData): Promise<StockPool> {
    const response = await apiClient.post<StockPool>('/user/stock-pools/create', data)
    return response.data
  }

  /**
   * 更新股票池信息
   */
  async updatePool(id: string, data: UpdatePoolData): Promise<StockPool> {
    const response = await apiClient.put<StockPool>(`/user/stock-pools/${id}`, data)
    return response.data
  }

  /**
   * 删除股票池（检查is_deletable）
   */
  async deletePool(id: string): Promise<void> {
    await apiClient.delete(`/user/stock-pools/${id}`)
  }

  /**
   * 获取股票池详情
   */
  async getPoolDetail(id: string): Promise<StockPool> {
    const response = await apiClient.get<StockPool>(`/user/stock-pools/${id}`)
    return response.data
  }

  // ==================== 股票管理操作 ====================

  /**
   * 添加股票到股票池
   */
  async addStocksToPool(poolId: string, stocks: StockInfo[]): Promise<{
    message: string
    added_count: number
    updated_count: number
    total_stocks: number
  }> {
    const response = await apiClient.post(`/user/stock-pools/${poolId}/stocks`, {
      stocks: stocks
    })
    return response.data
  }

  /**
   * 从股票池移除股票
   */
  async removeStockFromPool(poolId: string, stockCode: string): Promise<void> {
    await apiClient.delete(`/user/stock-pools/${poolId}/stocks`, {
      ts_codes: [stockCode]
    })
  }

  /**
   * 批量添加股票到多个股票池
   */
  async addStocksToPools(data: BatchAddData): Promise<BatchResult> {
    const response = await apiClient.post('/user/stock-pools/batch-add-stocks', data)
    
    // API客户端已经处理了响应格式，检查results字段
    // 后端返回 { message: "批量添加完成", results: {...} }
    // API客户端处理后可能在data中或直接在response中
    const responseData = response.data || response
    return responseData.results || responseData
  }

  // ==================== 股票搜索 ====================

  /**
   * 搜索股票
   */
  async searchStocks(keyword: string, limit: number = 20): Promise<StockSearchResult[]> {
    const response = await apiClient.get('/user/stock-pools/search-stocks', { keyword, limit })
    
    // API客户端已经处理了响应格式，检查data字段
    // 后端返回 { success: true, data: [...], total: 1 }
    // API客户端处理后变成 { success: true, data: [...], ... }
    const responseData = response.data || response
    if (Array.isArray(responseData)) {
      return responseData
    }
    if (responseData && Array.isArray(responseData.data)) {
      return responseData.data
    }
    return []
  }

  /**
   * 根据股票代码获取股票信息
   */
  async getStockInfo(code: string): Promise<StockInfo | null> {
    try {
      const results = await this.searchStocks(code, 1)
      if (results.length > 0) {
        const stock = results[0]
        return {
          ts_code: stock.ts_code,
          name: stock.name,
          industry: stock.industry,
          market: stock.market,
          add_time: new Date(),
          add_reason: '手动添加',
          tags: ['手动添加']
        }
      }
      return null
    } catch (error) {
      console.error('获取股票信息失败:', error)
      return null
    }
  }

  // ==================== 工具方法 ====================

  /**
   * 检查股票池是否可删除
   */
  canDeletePool(pool: StockPool): boolean {
    return pool.is_deletable && !pool.is_default
  }

  /**
   * 获取默认股票池
   */
  async getDefaultPool(): Promise<StockPool | null> {
    const pools = await this.getUserPools()
    return pools.find(pool => pool.is_default) || null
  }

  /**
   * 获取自定义股票池列表
   */
  async getCustomPools(): Promise<StockPool[]> {
    const pools = await this.getUserPools()
    return pools.filter(pool => pool.pool_type === 'custom')
  }

  /**
   * 根据标签过滤股票池
   */
  filterPoolsByTags(pools: StockPool[], tags: string[]): StockPool[] {
    return pools.filter(pool => 
      tags.some(tag => pool.tags.includes(tag))
    )
  }

  /**
   * 检查股票是否已存在于股票池中
   */
  isStockInPool(pool: StockPool, stockCode: string): boolean {
    return pool.stocks.some(stock => stock.ts_code === stockCode)
  }

  /**
   * 获取股票池统计信息
   */
  getPoolStats(pools: StockPool[]): {
    totalPools: number
    totalStocks: number
    defaultPools: number
    customPools: number
    publicPools: number
  } {
    return {
      totalPools: pools.length,
      totalStocks: pools.reduce((sum, pool) => sum + pool.stock_count, 0),
      defaultPools: pools.filter(pool => pool.is_default).length,
      customPools: pools.filter(pool => pool.pool_type === 'custom').length,
      publicPools: pools.filter(pool => pool.is_public).length
    }
  }
}

// 导出单例实例
export const stockPoolService = new StockPoolService()