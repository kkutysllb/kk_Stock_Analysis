/**
 * 登录调试工具
 * 帮助诊断登录问题
 */

import { authApi } from '@/api/auth'

export interface LoginDebugInfo {
  phone: string
  password: string
  timestamp: string
  userAgent: string
  url: string
}

export interface LoginDebugResult {
  success: boolean
  error?: string
  statusCode?: number
  debugInfo: LoginDebugInfo
  suggestions: string[]
}

/**
 * 调试登录问题
 */
export const debugLogin = async (phone: string, password: string): Promise<LoginDebugResult> => {
  const debugInfo: LoginDebugInfo = {
    phone,
    password: '***隐藏***', // 不记录真实密码
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    url: window.location.href
  }

  const suggestions: string[] = []

  try {
    // 尝试登录
    const response = await authApi.login({ phone, password })
    
    return {
      success: true,
      debugInfo,
      suggestions: ['登录成功']
    }
  } catch (error: any) {
    console.error('登录调试 - 详细错误信息:', error)
    
    let statusCode: number | undefined
    let errorMessage = '未知错误'

    if (error.code) {
      statusCode = error.code
    }

    if (error.message) {
      errorMessage = error.message
    }

    // 根据错误类型提供建议
    if (statusCode === 401) {
      suggestions.push('用户名或密码错误')
      suggestions.push('请检查手机号格式是否正确')
      suggestions.push('请确认密码是否正确')
      suggestions.push('请确认用户是否已注册')
    } else if (statusCode === 422) {
      suggestions.push('请求参数格式错误')
      suggestions.push('请检查手机号和密码格式')
    } else if (statusCode === 500) {
      suggestions.push('服务器内部错误')
      suggestions.push('请稍后重试或联系管理员')
    } else if (statusCode === 0 || !statusCode) {
      suggestions.push('网络连接问题')
      suggestions.push('请检查网络连接')
      suggestions.push('请确认服务器地址是否正确')
    }

    return {
      success: false,
      error: errorMessage,
      statusCode,
      debugInfo,
      suggestions
    }
  }
}

/**
 * 验证手机号格式
 */
export const validatePhoneFormat = (phone: string): { isValid: boolean; normalizedPhone: string; suggestions: string[] } => {
  const suggestions: string[] = []
  
  // 移除所有空格和特殊字符
  let normalizedPhone = phone.replace(/[\s\-\(\)]/g, '')
  
  // 检查是否以+86开头
  if (normalizedPhone.startsWith('+86')) {
    normalizedPhone = normalizedPhone.substring(3)
  } else if (normalizedPhone.startsWith('86')) {
    normalizedPhone = normalizedPhone.substring(2)
  }
  
  // 检查是否为11位数字
  if (!/^\d{11}$/.test(normalizedPhone)) {
    suggestions.push('手机号应为11位数字')
    return { isValid: false, normalizedPhone: `+86${normalizedPhone}`, suggestions }
  }
  
  // 检查是否以1开头
  if (!normalizedPhone.startsWith('1')) {
    suggestions.push('中国手机号应以1开头')
    return { isValid: false, normalizedPhone: `+86${normalizedPhone}`, suggestions }
  }
  
  // 检查第二位数字
  const secondDigit = normalizedPhone[1]
  if (!/[3-9]/.test(secondDigit)) {
    suggestions.push('手机号第二位应为3-9之间的数字')
    return { isValid: false, normalizedPhone: `+86${normalizedPhone}`, suggestions }
  }
  
  return { 
    isValid: true, 
    normalizedPhone: `+86${normalizedPhone}`, 
    suggestions: ['手机号格式正确'] 
  }
}

/**
 * 生成登录调试报告
 */
export const generateDebugReport = (result: LoginDebugResult): string => {
  const report = [
    '=== 登录调试报告 ===',
    `时间: ${result.debugInfo.timestamp}`,
    `手机号: ${result.debugInfo.phone}`,
    `URL: ${result.debugInfo.url}`,
    `用户代理: ${result.debugInfo.userAgent}`,
    '',
    '=== 结果 ===',
    `成功: ${result.success ? '是' : '否'}`,
  ]

  if (!result.success) {
    report.push(`错误: ${result.error}`)
    if (result.statusCode) {
      report.push(`状态码: ${result.statusCode}`)
    }
  }

  report.push('')
  report.push('=== 建议 ===')
  result.suggestions.forEach((suggestion, index) => {
    report.push(`${index + 1}. ${suggestion}`)
  })

  return report.join('\n')
}