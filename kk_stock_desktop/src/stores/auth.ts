/**
 * 用户认证状态管理
 * 管理用户登录状态、Token、用户信息等
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { UserInfo } from './app'
import type { LoginRequest, RegisterRequest, UserInfoResponse, UpdateUserInfoRequest } from '@/api/auth'

export interface AuthState {
  isAuthenticated: boolean
  accessToken: string | null
  refreshToken: string | null
  user: UserInfo | null
  loginLoading: boolean
  codeLoading: boolean
}

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const isAuthenticated = ref(false)
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const user = ref<UserInfo | null>(null)
  const loginLoading = ref(false)
  const codeLoading = ref(false)

  // 计算属性
  const isLoggedIn = computed(() => isAuthenticated.value && !!accessToken.value)
  const userRoles = computed(() => user.value?.roles || [])
  const hasRole = (role: string) => userRoles.value.includes(role)

  // 初始化认证状态
  const initAuth = () => {
    const savedToken = localStorage.getItem('access-token')
    const savedRefreshToken = localStorage.getItem('refresh-token')
    const savedUser = localStorage.getItem('user-info')

    if (savedToken) {
      accessToken.value = savedToken
      isAuthenticated.value = true
    }

    if (savedRefreshToken) {
      refreshToken.value = savedRefreshToken
    }

    if (savedUser) {
      try {
        user.value = JSON.parse(savedUser)
      } catch (error) {
        console.error('解析用户信息失败:', error)
        clearAuth()
      }
    }
  }

  // 设置认证信息
  const setAuth = (token: string, userInfo?: UserInfo, refresh?: string) => {
    accessToken.value = token
    isAuthenticated.value = true
    localStorage.setItem('access-token', token)

    if (refresh) {
      refreshToken.value = refresh
      localStorage.setItem('refresh-token', refresh)
    }

    if (userInfo) {
      user.value = userInfo
      localStorage.setItem('user-info', JSON.stringify(userInfo))
    }
  }

  // 清除认证信息
  const clearAuth = () => {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    isAuthenticated.value = false
    localStorage.removeItem('access-token')
    localStorage.removeItem('refresh-token')
    localStorage.removeItem('user-info')
  }

  // 普通登录
  const login = async (loginData: LoginRequest): Promise<boolean> => {
    try {
      loginLoading.value = true
      
      const response = await authApi.login(loginData)
      
      if (response.success && response.data) {
        const { access_token, refresh_token, user_info } = response.data
        setAuth(access_token, user_info, refresh_token)
        
        // 获取完整用户信息
        await fetchUserInfo()
        return true
      } else {
        throw new Error(response.error || '登录失败')
      }
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    } finally {
      loginLoading.value = false
    }
  }

  // 用户注册
  const register = async (registerData: RegisterRequest): Promise<boolean> => {
    try {
      loginLoading.value = true
      
      const response = await authApi.register(registerData)
      
      if (response.success) {
        return true
      } else {
        throw new Error(response.error || '注册失败')
      }
    } catch (error) {
      console.error('注册失败:', error)
      throw error
    } finally {
      loginLoading.value = false
    }
  }

  // 获取用户信息
  const fetchUserInfo = async (): Promise<void> => {
    try {
      const response = await authApi.getUserInfo()
      
      if (response.success && response.data) {
        const userInfo = response.data
        // 转换为UserInfo格式
        const convertedUser: UserInfo = {
          user_id: userInfo.user_id,
          phone: userInfo.phone,
          email: userInfo.email || '',
          nickname: userInfo.nickname,
          roles: userInfo.roles || ['user'],
          status: userInfo.status,
          create_time: userInfo.create_time,
          last_login: userInfo.last_login,
          login_count: userInfo.login_count
        }
        
        user.value = convertedUser
        localStorage.setItem('user-info', JSON.stringify(convertedUser))
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果获取用户信息失败，可能token已过期
      if (error instanceof Error && error.message.includes('401')) {
        await logout()
      }
    }
  }

  // 刷新Token
  const refreshAccessToken = async (): Promise<boolean> => {
    try {
      if (!refreshToken.value) {
        throw new Error('没有刷新令牌')
      }

      const response = await authApi.refreshToken()
      
      if (response.success && response.data) {
        const { access_token } = response.data
        setAuth(access_token)
        return true
      } else {
        throw new Error(response.error || '刷新Token失败')
      }
    } catch (error) {
      console.error('刷新Token失败:', error)
      await logout()
      return false
    }
  }

  // 登出
  const logout = async (): Promise<void> => {
    try {
      if (isAuthenticated.value) {
        await authApi.logout()
      }
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      clearAuth()
    }
  }

  // 检查认证状态
  const checkAuth = async (): Promise<boolean> => {
    if (!accessToken.value) {
      return false
    }

    try {
      await fetchUserInfo()
      return true
    } catch (error) {
      // 尝试刷新Token
      return await refreshAccessToken()
    }
  }

  // 更新用户信息
  const updateUserInfo = async (data: UpdateUserInfoRequest): Promise<void> => {
    try {
      const response = await authApi.updateUserInfo(data)
      
      if (response.success && response.data) {
        const userInfo = response.data
        // 转换为UserInfo格式
        const convertedUser: UserInfo = {
          user_id: userInfo.user_id,
          phone: userInfo.phone,
          email: userInfo.email || '',
          nickname: userInfo.nickname,
          roles: userInfo.roles || ['user'],
          status: userInfo.status,
          create_time: userInfo.create_time,
          last_login: userInfo.last_login,
          login_count: userInfo.login_count
        }
        
        user.value = convertedUser
        localStorage.setItem('user-info', JSON.stringify(convertedUser))
      } else {
        throw new Error(response.error || '更新用户信息失败')
      }
    } catch (error) {
      console.error('更新用户信息失败:', error)
      throw error
    }
  }

  // 修改密码
  const changePassword = async (data: ChangePasswordRequest): Promise<void> => {
    try {
      const response = await authApi.changePassword(data)
      
      if (response.success) {
        // 修改密码成功，建议用户重新登录
        return
      } else {
        throw new Error(response.error || '修改密码失败')
      }
    } catch (error) {
      console.error('修改密码失败:', error)
      throw error
    }
  }

  return {
    // 状态
    isAuthenticated,
    accessToken,
    refreshToken,
    user,
    loginLoading,
    codeLoading,
    
    // 计算属性
    isLoggedIn,
    userRoles,
    hasRole,
    
    // 方法
    initAuth,
    setAuth,
    clearAuth,
    login,
    register,
    fetchUserInfo,
    refreshAccessToken,
    logout,
    checkAuth,
    updateUserInfo,
    changePassword
  }
})