/**
 * 页面刷新组合函数
 * 用于统一处理页面的刷新逻辑
 */

import { onMounted, onUnmounted } from 'vue'
import { eventBus } from './eventBus'

/**
 * 页面刷新组合函数
 * @param refreshCallback 刷新回调函数
 * @param pagePath 页面路径（可选，如不提供则使用事件名）
 * @param eventName 特定事件名（可选）
 */
export function usePageRefresh(
  refreshCallback: () => void | Promise<void>,
  pagePath?: string,
  eventName?: string
) {
  onMounted(() => {
    // 监听通用页面刷新事件
    if (pagePath) {
      eventBus.on('page-refresh', (path: string) => {
        if (path === pagePath) {
          refreshCallback()
        }
      })
    }
    
    // 监听特定刷新事件
    if (eventName) {
      eventBus.on(eventName, refreshCallback)
    }
  })

  onUnmounted(() => {
    // 清理事件监听器
    if (pagePath) {
      eventBus.off('page-refresh')
    }
    
    if (eventName) {
      eventBus.off(eventName)
    }
  })

  // 返回手动刷新函数
  return {
    refresh: refreshCallback
  }
}

/**
 * 预定义的页面刷新配置
 */
export const PAGE_REFRESH_CONFIG = {
  DASHBOARD: { path: '/dashboard', event: 'refresh-dashboard' },
  INDICES: { path: '/analysis/indices', event: 'refresh-indices' },
  FUTURES: { path: '/analysis/futures', event: 'refresh-futures' },
  SPECIAL_DATA: { path: '/special-data', event: 'refresh-special-data' },
  TREND: { path: '/analysis/trend', event: 'refresh-trend' },
  STRATEGY: { path: '/strategy/screening', event: 'refresh-strategy' },
  BACKTEST: { path: '/quant/backtest', event: 'refresh-backtest' },
  SETTINGS: { path: '/settings', event: 'refresh-settings' },
  PROFILE: { path: '/profile', event: 'refresh-profile' },
  USER_MANAGEMENT: { path: '/admin/users', event: 'refresh-users' }
} as const