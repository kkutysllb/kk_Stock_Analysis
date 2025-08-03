import { ref } from 'vue'

// 事件总线类型定义
type EventCallback = (...args: any[]) => void

class EventBus {
  private events: Map<string, EventCallback[]> = new Map()

  // 监听事件
  on(event: string, callback: EventCallback) {
    if (!this.events.has(event)) {
      this.events.set(event, [])
    }
    this.events.get(event)!.push(callback)
  }

  // 移除事件监听
  off(event: string, callback: EventCallback) {
    const callbacks = this.events.get(event)
    if (callbacks) {
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
  }

  // 触发事件
  emit(event: string, ...args: any[]) {
    const callbacks = this.events.get(event)
    if (callbacks) {
      callbacks.forEach(callback => callback(...args))
    }
  }

  // 移除所有事件监听
  clear() {
    this.events.clear()
  }
}

// 创建全局事件总线实例
const eventBusInstance = new EventBus()
export const eventBus = eventBusInstance
export default eventBusInstance

// 登录弹窗状态管理
export const loginModalVisible = ref(false)

// 监听显示登录弹窗事件
eventBus.on('show-login-modal', () => {
  loginModalVisible.value = true
})

// 监听隐藏登录弹窗事件
eventBus.on('hide-login-modal', () => {
  loginModalVisible.value = false
})