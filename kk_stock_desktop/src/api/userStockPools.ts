import { BaseApiClient } from './base'

// 股票信息接口（匹配后端StockInfo模型）
export interface StockInfo {
  ts_code: string
  name: string
  industry?: string
  market?: string
  add_time: string
  add_reason?: string
  tags: string[]
}

// 股票池接口（匹配后端StockPoolResponse模型）
export interface StockPool {
  pool_id: string
  pool_name: string
  description?: string
  pool_type: string
  is_default: boolean
  is_public: boolean
  is_deletable: boolean
  share_code?: string
  tags: string[]
  stock_count: number
  stocks: StockInfo[]
  create_time: string
  update_time: string
}

// 兼容性接口（用于前端显示）
export interface Stock {
  symbol: string
  name: string
  price?: number
  change?: number
  change_percent?: number
}

export interface CreateStockPoolRequest {
  name: string
  description?: string
  stocks?: string[] // 股票代码数组
}

export interface UpdateStockPoolRequest {
  name?: string
  description?: string
}

export interface AddStocksRequest {
  stocks: string[] // 股票代码数组
}

export interface RemoveStocksRequest {
  stocks: string[] // 股票代码数组
}

// 用户股票池API客户端
export class UserStockPoolsApiClient extends BaseApiClient {
  private readonly basePath = '/user/stock-pools'

  /**
   * 获取用户的所有股票池
   */
  async getUserStockPools(): Promise<StockPool[]> {
    const response = await this.request<StockPool[]>(`${this.basePath}`, {
      method: 'GET'
    })
    return response.data || []
  }

  /**
   * 创建新的股票池
   */
  async createStockPool(data: CreateStockPoolRequest): Promise<StockPool> {
    const response = await this.request<StockPool>(`${this.basePath}/`, {
      method: 'POST',
      body: JSON.stringify(data)
    })
    if (!response.data) {
      throw new Error('创建股票池失败：服务器未返回数据')
    }
    return response.data
  }

  /**
   * 获取指定股票池详情
   */
  async getStockPool(poolId: string): Promise<StockPool> {
    const response = await this.request<StockPool>(`${this.basePath}/${poolId}`, {
      method: 'GET'
    })
    if (!response.data) {
      throw new Error('获取股票池详情失败：股票池不存在')
    }
    return response.data
  }

  /**
   * 更新股票池信息
   */
  async updateStockPool(poolId: string, data: UpdateStockPoolRequest): Promise<StockPool> {
    const response = await this.request<StockPool>(`${this.basePath}/${poolId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    })
    if (!response.data) {
      throw new Error('更新股票池失败：服务器未返回数据')
    }
    return response.data
  }

  /**
   * 删除股票池
   */
  async deleteStockPool(poolId: string): Promise<void> {
    await this.request(`${this.basePath}/${poolId}`, {
      method: 'DELETE'
    })
  }

  /**
   * 向股票池添加股票
   */
  async addStocksToPool(poolId: string, data: AddStocksRequest): Promise<StockPool> {
    const response = await this.request<StockPool>(`${this.basePath}/${poolId}/stocks`, {
      method: 'POST',
      body: JSON.stringify(data)
    })
    if (!response.data) {
      throw new Error('添加股票失败：服务器未返回数据')
    }
    return response.data
  }

  /**
   * 从股票池移除股票
   */
  async removeStocksFromPool(poolId: string, data: RemoveStocksRequest): Promise<StockPool> {
    const response = await this.request<StockPool>(`${this.basePath}/${poolId}/stocks`, {
      method: 'DELETE',
      body: JSON.stringify(data)
    })
    if (!response.data) {
      throw new Error('移除股票失败：服务器未返回数据')
    }
    return response.data
  }
}

// 导出单例实例
export const userStockPoolsApi = new UserStockPoolsApiClient()