/**
 * API基础客户端
 * 提供统一的HTTP请求处理、错误处理、重试机制、请求队列等
 */

// 临时配置，避免循环导入问题
const CONFIG = {
  API: {
    // BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://f1.ttyt.cc:41726',
    BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:9001',
    TIMEOUT: 45000, // 增加超时时间到45秒
    RETRY_COUNT: 2, // 减少重试次数
    RETRY_DELAY: 1000,
    MAX_CONCURRENT_REQUESTS: 3 // 最大并发请求数
  }
}

// 通用API响应接口
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
  timestamp: string
  code?: number
}

// 请求配置接口
export interface RequestConfig extends RequestInit {
  timeout?: number
  retry?: number
  retryDelay?: number
}

// API错误类
export class ApiError extends Error {
  public code: number
  public response?: Response
  
  constructor(message: string, code: number, response?: Response) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.response = response
  }
}

// 网络错误类
export class NetworkError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'NetworkError'
  }
}

// 超时错误类
export class TimeoutError extends Error {
  constructor(message: string = '请求超时') {
    super(message)
    this.name = 'TimeoutError'
  }
}

// 请求队列项接口
interface QueueItem {
  url: string
  config: RequestConfig
  resolve: (value: any) => void
  reject: (reason?: any) => void
}

/**
 * API基础客户端类
 */
export class BaseApiClient {
  private baseUrl: string
  private defaultTimeout: number
  private defaultRetry: number
  private defaultRetryDelay: number
  private maxConcurrentRequests: number
  private activeRequests: number
  private requestQueue: QueueItem[]

  constructor(baseUrl: string = CONFIG.API.BASE_URL) {
    this.baseUrl = baseUrl
    this.defaultTimeout = CONFIG.API.TIMEOUT
    this.defaultRetry = CONFIG.API.RETRY_COUNT
    this.defaultRetryDelay = CONFIG.API.RETRY_DELAY
    this.maxConcurrentRequests = CONFIG.API.MAX_CONCURRENT_REQUESTS
    this.activeRequests = 0
    this.requestQueue = []
  }

  /**
   * 创建带超时的fetch请求
   */
  private createTimeoutFetch(timeout: number) {
    return (url: string, options: RequestInit = {}) => {
      return Promise.race([
        fetch(url, options),
        new Promise<never>((_, reject) => {
          setTimeout(() => reject(new TimeoutError()), timeout)
        })
      ])
    }
  }

  /**
   * 延迟函数
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * 处理请求队列
   */
  private async processQueue(): Promise<void> {
    if (this.activeRequests >= this.maxConcurrentRequests || this.requestQueue.length === 0) {
      return
    }

    const item = this.requestQueue.shift()
    if (!item) return

    this.activeRequests++
    
    try {
      const result = await this.executeRequest(item.url, item.config)
      item.resolve(result)
    } catch (error) {
      item.reject(error)
    } finally {
      this.activeRequests--
      // 处理下一个请求
      this.processQueue()
    }
  }

  /**
   * 执行实际的HTTP请求
   */
  private async executeRequest<T = any>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const {
      timeout = this.defaultTimeout,
      retry = this.defaultRetry,
      retryDelay = this.defaultRetryDelay,
      ...requestConfig
    } = config

    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`
    
    // 添加请求URL日志
    console.log(`🌐 API请求: ${config.method || 'GET'} ${url}`)
    
    let lastError: Error | null = null
    
    for (let attempt = 0; attempt <= retry; attempt++) {
      try {
        // 请求拦截
        const [finalUrl, finalConfig] = await this.requestInterceptor(url, requestConfig)
        
        // 发送请求
        const timeoutFetch = this.createTimeoutFetch(timeout)
        const response = await timeoutFetch(finalUrl, finalConfig)
        
        // 响应拦截
        return await this.responseInterceptor<T>(response)
        
      } catch (error) {
        lastError = error as Error
        
        // 如果是最后一次尝试，直接抛出错误
        if (attempt === retry) {
          break
        }
        
        // 判断是否需要重试
        if (error instanceof TimeoutError || 
            error instanceof NetworkError ||
            (error instanceof ApiError && error.code >= 500)) {
          
          console.warn(`请求失败，${retryDelay}ms后进行第${attempt + 1}次重试:`, error.message)
          await this.delay(retryDelay)
          continue
        }
        
        // 其他错误直接抛出
        break
      }
    }
    
    // 处理网络错误
    if (lastError instanceof TypeError && lastError.message.includes('fetch')) {
      throw new NetworkError('网络连接失败，请检查网络设置')
    }
    
    throw lastError
  }

  /**
   * 请求拦截器
   */
  private async requestInterceptor(url: string, config: RequestConfig): Promise<[string, RequestConfig]> {
    // 添加默认headers
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
    
    // 合并config中的headers
    if (config.headers) {
      Object.entries(config.headers).forEach(([key, value]) => {
        if (typeof value === 'string') {
          headers[key] = value
        }
      })
    }

    // 处理认证token（如果需要）
    const token = localStorage.getItem('access-token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const finalConfig: RequestConfig = {
      ...config,
      headers
    }

    return [url, finalConfig]
  }

  /**
   * 响应拦截器
   */
  private async responseInterceptor<T>(response: Response): Promise<ApiResponse<T>> {
    let data: any
    
    try {
      const text = await response.text()
      data = text ? JSON.parse(text) : {}
    } catch (error) {
      throw new ApiError('响应数据解析失败', response.status, response)
    }

    if (!response.ok) {
      const errorMessage = data.message || data.error || `HTTP ${response.status}: ${response.statusText}`
      
      // 对于422错误，输出更详细的错误信息用于调试
      if (response.status === 422) {
        console.error('API参数验证失败 (422):', {
          url: response.url,
          status: response.status,
          statusText: response.statusText,
          errorData: data,
          errorMessage: errorMessage
        })
      }
      
      throw new ApiError(errorMessage, response.status, response)
    }

    // 标准化响应格式
    return {
      success: true,
      data: data.data || data,
      message: data.message,
      timestamp: new Date().toISOString(),
      code: response.status,
      ...data
    }
  }

  /**
   * 核心请求方法（使用队列管理）
   */
  public async request<T = any>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<ApiResponse<T>> {
    return new Promise((resolve, reject) => {
      // 如果当前活跃请求数小于最大并发数，直接执行
      if (this.activeRequests < this.maxConcurrentRequests) {
        this.activeRequests++
        
        this.executeRequest<T>(endpoint, config)
          .then(resolve)
          .catch(reject)
          .finally(() => {
            this.activeRequests--
            // 处理队列中的下一个请求
            this.processQueue()
          })
      } else {
        // 否则加入队列
        this.requestQueue.push({
          url: endpoint,
          config,
          resolve,
          reject
        })
      }
    })
  }

  /**
   * GET请求
   */
  public async get<T = any>(endpoint: string, params?: Record<string, any>, config?: RequestConfig): Promise<ApiResponse<T>> {
    let url = endpoint
    
    if (params) {
      const searchParams = new URLSearchParams()
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value))
        }
      })
      url += `?${searchParams.toString()}`
    }
    
    return this.request<T>(url, { ...config, method: 'GET' })
  }

  /**
   * POST请求
   */
  public async post<T = any>(endpoint: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined
    })
  }

  /**
   * PUT请求
   */
  public async put<T = any>(endpoint: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined
    })
  }

  /**
   * DELETE请求
   */
  public async delete<T = any>(endpoint: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'DELETE',
      body: data ? JSON.stringify(data) : undefined
    })
  }

  /**
   * PATCH请求
   */
  public async patch<T = any>(endpoint: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined
    })
  }
}

// 创建默认的API客户端实例
export const apiClient = new BaseApiClient()

// 导出便捷方法
export const { get, post, put, delete: del, patch } = apiClient

// 数据库配置相关接口
export interface DatabaseConfig {
  cloud_database: {
    host: string
    port: number
    database: string
  }
  local_database: {
    host: string
    port: number
    database: string
  }
  priority: 'local' | 'cloud'
}

export interface DatabaseTestRequest {
  db_type: 'cloud_database' | 'local_database'
}

export interface DatabaseTestResult {
  success: boolean
  message: string
  server_version?: string
  connection_uri?: string
  error_type?: string
}

export interface DatabaseStatus {
  cloud_database: DatabaseTestResult
  local_database: DatabaseTestResult
  current_priority: 'local' | 'cloud'
  active_database: 'local_database' | 'cloud_database' | 'none'
}

// 数据库配置API
export const databaseConfigAPI = {
  // 获取数据库配置
  async getConfig(): Promise<ApiResponse<DatabaseConfig>> {
    return apiClient.get<DatabaseConfig>('/admin/database/config')
  },

  // 更新数据库配置
  async updateConfig(config: {
    cloud_database: { host: string; port: number }
    local_database: { host: string; port: number }
    priority: 'local' | 'cloud'
  }): Promise<ApiResponse<DatabaseConfig>> {
    return apiClient.post<DatabaseConfig>('/admin/database/config', config)
  },

  // 测试数据库连接
  async testConnection(request: DatabaseTestRequest): Promise<ApiResponse<DatabaseTestResult>> {
    return apiClient.post<DatabaseTestResult>('/admin/database/test', request)
  },

  // 获取数据库状态
  async getStatus(): Promise<ApiResponse<DatabaseStatus>> {
    return apiClient.get<DatabaseStatus>('/admin/database/status')
  },

  // 重新加载数据库配置
  async reloadConfig(): Promise<ApiResponse<any>> {
    return apiClient.post<any>('/admin/database/reload')
  }
}