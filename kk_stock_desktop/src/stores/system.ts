import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'

export interface SystemStatus {
  cpu: number
  memory: number
  diskUsage: number
  networkStatus: 'online' | 'offline'
  lastUpdate: string
}

export interface DatabaseStatus {
  connected: boolean
  responseTime: number
  documentsCount: number
  collectionsCount: number
  lastSyncTime: string
}

export interface ServiceStatus {
  dataCollector: 'running' | 'stopped' | 'error'
  contentGenerator: 'running' | 'stopped' | 'error'
  apiServer: 'running' | 'stopped' | 'error'
}

export const useSystemStore = defineStore('system', () => {
  // 状态
  const systemStatus = ref<'healthy' | 'warning' | 'error'>('healthy')
  const isMonitoring = ref(false)
  const lastHealthCheck = ref<string>('')
  
  const systemInfo = reactive<SystemStatus>({
    cpu: 0,
    memory: 0,
    diskUsage: 0,
    networkStatus: 'online',
    lastUpdate: ''
  })
  
  const databaseStatus = reactive<DatabaseStatus>({
    connected: false,
    responseTime: 0,
    documentsCount: 0,
    collectionsCount: 0,
    lastSyncTime: ''
  })
  
  const serviceStatus = reactive<ServiceStatus>({
    dataCollector: 'stopped',
    contentGenerator: 'stopped',
    apiServer: 'stopped'
  })

  // 操作
  const initialize = async () => {
    await checkSystemHealth()
    startMonitoring()
  }

  const checkSystemHealth = async () => {
    try {
      // 检查网络连接
      systemInfo.networkStatus = navigator.onLine ? 'online' : 'offline'
      
      // 检查数据库连接
      await checkDatabaseConnection()
      
      // 检查服务状态
      await checkServiceStatus()
      
      // 更新系统状态
      updateSystemStatus()
      
      lastHealthCheck.value = new Date().toISOString()
    } catch (error) {
      console.error('系统健康检查失败:', error)
      systemStatus.value = 'error'
    }
  }

  const checkDatabaseConnection = async () => {
    try {
      const startTime = Date.now()
      
      // 模拟数据库连接检查
      // 在实际应用中，这里应该调用后端API
      const response = await fetch('/api/health/database').catch(() => null)
      
      if (response && response.ok) {
        const contentType = response.headers.get('content-type')
        if (contentType && contentType.includes('application/json')) {
        const data = await response.json()
        databaseStatus.connected = true
        databaseStatus.responseTime = Date.now() - startTime
        databaseStatus.documentsCount = data.documentsCount || 0
        databaseStatus.collectionsCount = data.collectionsCount || 0
        databaseStatus.lastSyncTime = data.lastSyncTime || new Date().toISOString()
        } else {
          // 返回的不是JSON，可能是HTML错误页面
          console.warn('数据库健康检查API返回非JSON响应，可能服务未启动')
          databaseStatus.connected = false
          databaseStatus.responseTime = 0
        }
      } else {
        databaseStatus.connected = false
        databaseStatus.responseTime = 0
      }
    } catch (error) {
      console.warn('数据库连接检查失败 (开发环境正常):', error.message)
      databaseStatus.connected = false
      databaseStatus.responseTime = 0
    }
  }

  const checkServiceStatus = async () => {
    try {
      // 检查各个服务状态
      // 在实际应用中，这里应该调用相应的API
      const services = ['dataCollector', 'contentGenerator', 'apiServer'] as const
      
      for (const service of services) {
        try {
          const response = await fetch(`/api/health/${service}`).catch(() => null)
          if (response && response.ok) {
            const contentType = response.headers.get('content-type')
            if (contentType && contentType.includes('application/json')) {
            serviceStatus[service] = 'running'
            } else {
              serviceStatus[service] = 'stopped'
            }
          } else {
            serviceStatus[service] = 'stopped'
          }
        } catch (error) {
          serviceStatus[service] = 'stopped' // 开发环境下将错误状态改为停止状态
        }
      }
    } catch (error) {
      console.error('服务状态检查失败:', error)
    }
  }

  const updateSystemStatus = () => {
    const hasErrors = !databaseStatus.connected || 
      Object.values(serviceStatus).some(status => status === 'error')
    
    const hasWarnings = systemInfo.networkStatus === 'offline' ||
      Object.values(serviceStatus).some(status => status === 'stopped')
    
    if (hasErrors) {
      systemStatus.value = 'error'
    } else if (hasWarnings) {
      systemStatus.value = 'warning'
    } else {
      systemStatus.value = 'healthy'
    }
  }

  const startMonitoring = () => {
    if (isMonitoring.value) return
    
    isMonitoring.value = true
    
    // 每30秒检查一次系统状态
    const healthCheckInterval = setInterval(() => {
      checkSystemHealth()
    }, 30000)
    
    // 每5秒更新一次系统信息
    const systemInfoInterval = setInterval(() => {
      updateSystemInfo()
    }, 5000)
    
    // 存储定时器ID以便清理
    ;(window as any).healthCheckInterval = healthCheckInterval
    ;(window as any).systemInfoInterval = systemInfoInterval
  }

  const stopMonitoring = () => {
    if (!isMonitoring.value) return
    
    isMonitoring.value = false
    
    // 清理定时器
    if ((window as any).healthCheckInterval) {
      clearInterval((window as any).healthCheckInterval)
      delete (window as any).healthCheckInterval
    }
    
    if ((window as any).systemInfoInterval) {
      clearInterval((window as any).systemInfoInterval)
      delete (window as any).systemInfoInterval
    }
  }

  const updateSystemInfo = () => {
    // 模拟系统信息获取
    // 在实际应用中，可以通过Electron API获取真实的系统信息
    systemInfo.cpu = Math.floor(Math.random() * 100)
    systemInfo.memory = Math.floor(Math.random() * 100)
    systemInfo.diskUsage = Math.floor(Math.random() * 100)
    systemInfo.lastUpdate = new Date().toISOString()
  }

  const refreshData = async () => {
    await checkSystemHealth()
  }

  const restartService = async (serviceName: keyof ServiceStatus) => {
    try {
      serviceStatus[serviceName] = 'stopped'
      
      // 模拟重启服务
      // 在实际应用中，这里应该调用相应的API
      const response = await fetch(`/api/services/${serviceName}/restart`, {
        method: 'POST'
      }).catch(() => null)
      
      if (response && response.ok) {
        const contentType = response.headers.get('content-type')
        if (contentType && contentType.includes('application/json')) {
        serviceStatus[serviceName] = 'running'
        return true
        } else {
          serviceStatus[serviceName] = 'stopped'
          return false
        }
      } else {
        serviceStatus[serviceName] = 'stopped'
        return false
      }
    } catch (error) {
      console.error(`重启服务 ${serviceName} 失败:`, error)
      serviceStatus[serviceName] = 'error'
      return false
    }
  }

  const getSystemMetrics = () => {
    return {
      systemInfo: { ...systemInfo },
      databaseStatus: { ...databaseStatus },
      serviceStatus: { ...serviceStatus },
      systemStatus: systemStatus.value,
      lastHealthCheck: lastHealthCheck.value
    }
  }

  // 监听网络状态变化
  if (typeof window !== 'undefined') {
    window.addEventListener('online', () => {
      systemInfo.networkStatus = 'online'
      updateSystemStatus()
    })
    
    window.addEventListener('offline', () => {
      systemInfo.networkStatus = 'offline'
      updateSystemStatus()
    })
  }

  // 计算属性
  const cpuUsage = computed(() => systemInfo.cpu)
  const memoryUsage = computed(() => systemInfo.memory)
  const refreshSystemInfo = () => updateSystemInfo()

  return {
    // 状态
    systemStatus,
    isMonitoring,
    lastHealthCheck,
    systemInfo,
    databaseStatus,
    serviceStatus,
    
    // 计算属性
    cpuUsage,
    memoryUsage,
    
    // 操作
    initialize,
    checkSystemHealth,
    startMonitoring,
    stopMonitoring,
    refreshData,
    refreshSystemInfo,
    restartService,
    getSystemMetrics
  }
}) 