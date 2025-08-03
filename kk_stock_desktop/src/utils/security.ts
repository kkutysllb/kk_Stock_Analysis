/**
 * 前端安全工具
 * 提供密码验证、输入清理等安全功能
 */

/**
 * 验证密码强度
 * @param password 密码
 * @returns 验证结果
 */
export const validatePasswordStrength = (password: string): { 
  isValid: boolean; 
  message: string;
  score: number; // 0-100 强度分数
} => {
  if (!password) {
    return { isValid: false, message: '密码不能为空', score: 0 }
  }

  if (password.length < 6) {
    return { isValid: false, message: '密码长度至少6位', score: 10 }
  }
  
  if (password.length > 128) {
    return { isValid: false, message: '密码长度不能超过128位', score: 0 }
  }

  let score = 0
  let feedback = []

  // 长度检查
  if (password.length >= 8) score += 20
  else if (password.length >= 6) score += 10

  // 包含小写字母
  if (/[a-z]/.test(password)) {
    score += 15
  } else {
    feedback.push('包含小写字母')
  }

  // 包含大写字母
  if (/[A-Z]/.test(password)) {
    score += 15
  } else {
    feedback.push('包含大写字母')
  }

  // 包含数字
  if (/\d/.test(password)) {
    score += 15
  } else {
    feedback.push('包含数字')
  }

  // 包含特殊字符
  if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    score += 20
  } else {
    feedback.push('包含特殊字符')
  }

  // 没有连续重复字符
  if (!/(.)\1{2,}/.test(password)) {
    score += 15
  } else {
    feedback.push('避免连续重复字符')
  }

  const isValid = score >= 60
  const message = isValid 
    ? '密码强度良好' 
    : `密码强度不足，建议${feedback.join('、')}`

  return { isValid, message, score }
}

/**
 * 检查是否为常见弱密码
 * @param password 密码
 * @returns 是否为弱密码
 */
export const isWeakPassword = (password: string): boolean => {
  const weakPasswords = [
    '123456', 'password', '123456789', '12345678', '12345',
    '1234567', '1234567890', 'qwerty', 'abc123', 'password123',
    '111111', '123123', 'admin', 'root', 'user'
  ]
  
  return weakPasswords.includes(password.toLowerCase())
}

/**
 * 清理用户输入，防止XSS
 * @param input 用户输入
 * @returns 清理后的输入
 */
export const sanitizeInput = (input: string): string => {
  if (!input) return ''
  
  return input
    .replace(/[<>]/g, '') // 移除尖括号
    .replace(/javascript:/gi, '') // 移除javascript协议
    .replace(/on\w+=/gi, '') // 移除事件处理器
    .trim()
}

/**
 * 验证手机号格式
 * @param phone 手机号
 * @returns 是否有效
 */
export const validatePhone = (phone: string): boolean => {
  // 支持+86开头的中国手机号
  const phoneRegex = /^(\+86)?1[3-9]\d{9}$/
  return phoneRegex.test(phone)
}

/**
 * 验证邮箱格式
 * @param email 邮箱
 * @returns 是否有效
 */
export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * 生成随机字符串（用于CSRF token等）
 * @param length 长度
 * @returns 随机字符串
 */
export const generateRandomString = (length: number = 32): string => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

/**
 * 检查当前连接是否为HTTPS
 * @returns 是否为安全连接
 */
export const isSecureConnection = (): boolean => {
  return window.location.protocol === 'https:' || 
         window.location.hostname === 'localhost' ||
         window.location.hostname === '127.0.0.1'
}

/**
 * 安全警告提示
 */
export const checkSecurityWarnings = (): string[] => {
  const warnings: string[] = []
  
  if (!isSecureConnection()) {
    warnings.push('当前连接不安全，建议使用HTTPS')
  }
  
  return warnings
}