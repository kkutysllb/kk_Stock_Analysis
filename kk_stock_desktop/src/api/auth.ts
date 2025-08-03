/**
 * 用户认证API
 * 提供登录、注册、用户信息等认证相关接口
 */

import { BaseApiClient, ApiResponse } from './base'
import type { UserInfo } from '@/stores/app'

// 用户注册请求接口
export interface RegisterRequest {
  phone: string
  password: string
  email: string
  nickname?: string
}

// 登录请求接口
export interface LoginRequest {
  phone: string
  password: string
}

// 密码重置请求接口
export interface PasswordResetRequest {
  email: string
}

// 密码重置确认请求接口
export interface PasswordResetConfirmRequest {
  email: string
  reset_token: string
  new_password: string
}

// 修改密码请求接口
export interface ChangePasswordRequest {
  phone: string
  old_password: string
  new_password: string
}

// 更新用户信息请求接口
export interface UpdateUserInfoRequest {
  nickname?: string
  email?: string
}

// 登录响应接口
export interface LoginResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  user_info?: UserInfo
}

// 用户信息响应接口
export interface UserInfoResponse {
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

/**
 * 用户认证API客户端
 */
export class AuthApiClient extends BaseApiClient {
  /**
   * 用户注册
   */
  async register(data: RegisterRequest): Promise<ApiResponse<LoginResponse>> {
    return this.post('/user/register', data)
  }

  /**
   * 用户登录
   */
  async login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    return this.post('/user/login', data)
  }



  /**
   * 请求密码重置
   */
  async requestPasswordReset(data: PasswordResetRequest): Promise<ApiResponse<{ message: string }>> {
    return this.post('/user/password/reset', data)
  }

  /**
   * 确认密码重置
   */
  async confirmPasswordReset(data: PasswordResetConfirmRequest): Promise<ApiResponse<{ message: string }>> {
    return this.post('/user/password/reset/confirm', data)
  }

  /**
   * 修改密码
   */
  async changePassword(data: ChangePasswordRequest): Promise<ApiResponse<{ message: string }>> {
    return this.post('/user/password/change', data)
  }

  /**
   * 刷新访问令牌
   */
  async refreshToken(): Promise<ApiResponse<{ access_token: string }>> {
    return this.post('/user/refresh-token', {})
  }

  /**
   * 获取用户信息
   */
  async getUserInfo(): Promise<ApiResponse<UserInfoResponse>> {
    return this.get('/user/user-info')
  }

  /**
   * 更新用户信息
   */
  async updateUserInfo(data: UpdateUserInfoRequest): Promise<ApiResponse<UserInfoResponse>> {
    return this.post('/user/user-info', data)
  }

  /**
   * 登出
   */
  async logout(): Promise<ApiResponse<{ msg: string }>> {
    // 清除本地存储的token
    localStorage.removeItem('access-token')
    localStorage.removeItem('refresh-token')
    localStorage.removeItem('user-info')
    return Promise.resolve({ 
      success: true, 
      data: { msg: '登出成功' },
      timestamp: new Date().toISOString()
    })
  }
}

// 创建认证API实例
export const authApi = new AuthApiClient()

// 导出默认实例
export default authApi