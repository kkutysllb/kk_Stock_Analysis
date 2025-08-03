import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userStockPoolsApi, type StockPool, type CreateStockPoolRequest, type UpdateStockPoolRequest, type AddStocksRequest, type RemoveStocksRequest } from '../api/userStockPools'
import { useAuthStore } from './auth'

export const useUserStockPoolsStore = defineStore('userStockPools', () => {
  // 状态
  const stockPools = ref<StockPool[]>([])
  const currentPool = ref<StockPool | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const poolCount = computed(() => stockPools.value.length)
  const totalStocks = computed(() => {
    return stockPools.value.reduce((total, pool) => total + pool.stocks.length, 0)
  })

  // 获取认证store
  const authStore = useAuthStore()

  // 操作方法
  const setLoading = (value: boolean) => {
    loading.value = value
  }

  const setError = (message: string | null) => {
    error.value = message
  }

  const clearError = () => {
    error.value = null
  }

  /**
   * 获取用户的所有股票池
   */
  const fetchStockPools = async () => {
    if (!authStore.isLoggedIn) {
      setError('用户未登录')
      return
    }

    try {
      setLoading(true)
      clearError()
      const pools = await userStockPoolsApi.getUserStockPools()
      stockPools.value = pools
    } catch (err: any) {
      console.error('获取股票池失败:', err)
      setError(err.message || '获取股票池失败')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 创建新的股票池
   */
  const createStockPool = async (data: CreateStockPoolRequest): Promise<StockPool | null> => {
    if (!authStore.isLoggedIn) {
      setError('用户未登录')
      return null
    }

    try {
      setLoading(true)
      clearError()
      const newPool = await userStockPoolsApi.createStockPool(data)
      stockPools.value.push(newPool)
      return newPool
    } catch (err: any) {
      console.error('创建股票池失败:', err)
      setError(err.message || '创建股票池失败')
      return null
    } finally {
      setLoading(false)
    }
  }

  /**
   * 获取指定股票池详情
   */
  const fetchStockPool = async (poolId: string): Promise<StockPool | null> => {
    if (!authStore.isLoggedIn) {
      setError('用户未登录')
      return null
    }

    try {
      setLoading(true)
      clearError()
      const pool = await userStockPoolsApi.getStockPool(poolId)
      currentPool.value = pool
      
      // 更新列表中的对应项
      const index = stockPools.value.findIndex(p => p.id === poolId)
      if (index !== -1) {
        stockPools.value[index] = pool
      }
      
      return pool
    } catch (err: any) {
      console.error('获取股票池详情失败:', err)
      setError(err.message || '获取股票池详情失败')
      return null
    } finally {
      setLoading(false)
    }
  }

  /**
   * 更新股票池信息
   */
  const updateStockPool = async (poolId: string, data: UpdateStockPoolRequest): Promise<StockPool | null> => {
    if (!authStore.isLoggedIn) {
      setError('用户未登录')
      return null
    }

    try {
      setLoading(true)
      clearError()
      const updatedPool = await userStockPoolsApi.updateStockPool(poolId, data)
      
      // 更新列表中的对应项
      const index = stockPools.value.findIndex(p => p.id === poolId)
      if (index !== -1) {
        stockPools.value[index] = updatedPool
      }
      
      // 更新当前池
      if (currentPool.value?.id === poolId) {
        currentPool.value = updatedPool
      }
      
      return updatedPool
    } catch (err: any) {
      console.error('更新股票池失败:', err)
      setError(err.message || '更新股票池失败')
      return null
    } finally {
      setLoading(false)
    }
  }

  /**
   * 删除股票池
   */
  const deleteStockPool = async (poolId: string): Promise<boolean> => {
    if (!authStore.isLoggedIn) {
      setError('用户未登录')
      return false
    }

    try {
      setLoading(true)
      clearError()
      await userStockPoolsApi.deleteStockPool(poolId)
      
      // 从列表中移除
      const index = stockPools.value.findIndex(p => p.id === poolId)
      if (index !== -1) {
        stockPools.value.splice(index, 1)
      }
      
      // 清除当前池
      if (currentPool.value?.id === poolId) {
        currentPool.value = null
      }
      
      return true
    } catch (err: any) {
      console.error('删除股票池失败:', err)
      setError(err.message || '删除股票池失败')
      return false
    } finally {
      setLoading(false)
    }
  }

  /**
   * 向股票池添加股票
   */
  const addStocksToPool = async (poolId: string, stocks: string[]): Promise<StockPool | null> => {
    if (!authStore.isLoggedIn) {
      setError('用户未登录')
      return null
    }

    try {
      setLoading(true)
      clearError()
      const updatedPool = await userStockPoolsApi.addStocksToPool(poolId, { stocks })
      
      // 更新列表中的对应项
      const index = stockPools.value.findIndex(p => p.id === poolId)
      if (index !== -1) {
        stockPools.value[index] = updatedPool
      }
      
      // 更新当前池
      if (currentPool.value?.id === poolId) {
        currentPool.value = updatedPool
      }
      
      return updatedPool
    } catch (err: any) {
      console.error('添加股票失败:', err)
      setError(err.message || '添加股票失败')
      return null
    } finally {
      setLoading(false)
    }
  }

  /**
   * 从股票池移除股票
   */
  const removeStocksFromPool = async (poolId: string, stocks: string[]): Promise<StockPool | null> => {
    if (!authStore.isLoggedIn) {
      setError('用户未登录')
      return null
    }

    try {
      setLoading(true)
      clearError()
      const updatedPool = await userStockPoolsApi.removeStocksFromPool(poolId, { stocks })
      
      // 更新列表中的对应项
      const index = stockPools.value.findIndex(p => p.id === poolId)
      if (index !== -1) {
        stockPools.value[index] = updatedPool
      }
      
      // 更新当前池
      if (currentPool.value?.id === poolId) {
        currentPool.value = updatedPool
      }
      
      return updatedPool
    } catch (err: any) {
      console.error('移除股票失败:', err)
      setError(err.message || '移除股票失败')
      return null
    } finally {
      setLoading(false)
    }
  }

  /**
   * 设置当前股票池
   */
  const setCurrentPool = (pool: StockPool | null) => {
    currentPool.value = pool
  }

  /**
   * 清空所有数据
   */
  const clearAll = () => {
    stockPools.value = []
    currentPool.value = null
    error.value = null
    loading.value = false
  }

  /**
   * 根据ID查找股票池
   */
  const findPoolById = (poolId: string): StockPool | undefined => {
    return stockPools.value.find(pool => pool.id === poolId)
  }

  return {
    // 状态
    stockPools,
    currentPool,
    loading,
    error,
    
    // 计算属性
    poolCount,
    totalStocks,
    
    // 操作方法
    setLoading,
    setError,
    clearError,
    fetchStockPools,
    createStockPool,
    fetchStockPool,
    updateStockPool,
    deleteStockPool,
    addStocksToPool,
    removeStocksFromPool,
    setCurrentPool,
    clearAll,
    findPoolById
  }
})