/**
 * 全局配置管理
 * 统一管理所有环境变量和应用配置
 */

// API配置
export const API_CONFIG = {
  // BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://f1.ttyt.cc:41726',
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:9001',
  TIMEOUT: 30000, // 30秒超时
  RETRY_COUNT: 3,
  RETRY_DELAY: 1000, // 1秒重试延迟
} as const

// 开发环境配置
export const DEV_CONFIG = {
  PORT: import.meta.env.VITE_DEV_PORT || 5173,
  HOST: import.meta.env.VITE_DEV_HOST === 'true',
  OPEN: import.meta.env.VITE_DEV_OPEN === 'true',
} as const

// 应用配置
export const APP_CONFIG = {
  TITLE: import.meta.env.VITE_APP_TITLE || 'KK股票量化分析系统',
  VERSION: import.meta.env.VITE_APP_VERSION || '1.0.0',
  DEBUG: import.meta.env.VITE_DEBUG === 'true',
  LOG_LEVEL: import.meta.env.VITE_LOG_LEVEL || 'info',
} as const

// 导出统一配置对象
export const CONFIG = {
  API: API_CONFIG,
  DEV: DEV_CONFIG,
  APP: APP_CONFIG,
} as const

// 配置类型定义
export type ApiConfig = typeof API_CONFIG
export type DevConfig = typeof DEV_CONFIG
export type AppConfig = typeof APP_CONFIG
export type GlobalConfig = typeof CONFIG

// 默认导出
export default CONFIG