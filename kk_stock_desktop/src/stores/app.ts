import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'

export interface UserInfo {
  user_id: string
  phone: string
  email: string
  nickname?: string
  roles: string[]
  status: number
  create_time: string
  last_login?: string
  login_count: number
}

export interface AppSettings {
  theme: 'light' | 'dark' | 'auto'
  language: 'zh-CN' | 'en-US'
  autoRefresh: boolean
  refreshInterval: number
  notifications: boolean
  soundEnabled: boolean
}

export const useAppStore = defineStore('app', () => {
  // 状态
  const isInitialized = ref(false)
  const isLoading = ref(false)
  const user = ref<UserInfo | null>(null)
  const settings = reactive<AppSettings>({
    theme: 'light',
    language: 'zh-CN',
    autoRefresh: true,
    refreshInterval: 30000, // 30秒
    notifications: true,
    soundEnabled: false
  })

  // 应用信息
  const appInfo = reactive({
    name: 'KK Stock Analysis',
    version: '1.0.0',
    buildTime: new Date().toISOString(),
    environment: 'development'
  })

  // 操作
  const initialize = async () => {
    if (isInitialized.value) return

    isLoading.value = true
    try {
      // 加载用户设置
      await loadSettings()
      
      // 加载用户信息（如果有登录状态）
      await loadUserInfo()
      
      // 初始化Electron API
      if ((window as any).electronAPI) {
        // 获取应用版本信息
        try {
          const version = await (window as any).electronAPI.getVersion()
          appInfo.version = version
        } catch (error) {
          console.warn('无法获取应用版本:', error)
        }
      }
      
      isInitialized.value = true
    } catch (error) {
      console.error('应用初始化失败:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const loadSettings = async () => {
    try {
      const savedSettings = localStorage.getItem('app-settings')
      if (savedSettings) {
        const parsed = JSON.parse(savedSettings)
        Object.assign(settings, parsed)
      }
      
      // 应用主题设置
      applyTheme(settings.theme)
    } catch (error) {
      console.error('加载设置失败:', error)
    }
  }

  const saveSettings = async () => {
    try {
      localStorage.setItem('app-settings', JSON.stringify(settings))
      
      // 应用新设置
      applyTheme(settings.theme)
    } catch (error) {
      console.error('保存设置失败:', error)
      throw error
    }
  }

  const loadUserInfo = async () => {
    try {
      const savedUser = localStorage.getItem('user-info')
      if (savedUser) {
        user.value = JSON.parse(savedUser)
      }
    } catch (error) {
      console.error('加载用户信息失败:', error)
    }
  }

  const setUser = (userInfo: UserInfo | null) => {
    user.value = userInfo
    if (userInfo) {
      localStorage.setItem('user-info', JSON.stringify(userInfo))
    } else {
      localStorage.removeItem('user-info')
    }
  }

  const updateSettings = async (newSettings: Partial<AppSettings>) => {
    Object.assign(settings, newSettings)
    await saveSettings()
  }

  const applyTheme = (theme: AppSettings['theme']) => {
    const isDark = theme === 'dark' || 
      (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)
    
    document.documentElement.classList.toggle('dark', isDark)
  }

  const logout = () => {
    user.value = null
    localStorage.removeItem('user-info')
    localStorage.removeItem('access-token')
    localStorage.removeItem('refresh-token')
  }

  const checkAppUpdates = async () => {
    if ((window as any).electronAPI) {
      try {
        const hasUpdate = await (window as any).electronAPI.checkForUpdates()
        return hasUpdate
      } catch (error) {
        console.error('检查更新失败:', error)
        return false
      }
    }
    return false
  }

  // 监听系统主题变化
  if (typeof window !== 'undefined') {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (settings.theme === 'auto') {
        applyTheme('auto')
      }
    })
  }

  // 计算属性
  const isDarkMode = computed(() => {
    return settings.theme === 'dark' || 
      (settings.theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)
  })

  return {
    // 状态
    isInitialized,
    isLoading,
    user,
    settings,
    appInfo,
    
    // 计算属性
    isDarkMode,
    
    // 操作
    initialize,
    loadSettings,
    saveSettings,
    loadUserInfo,
    setUser,
    updateSettings,
    applyTheme,
    logout,
    checkAppUpdates
  }
})