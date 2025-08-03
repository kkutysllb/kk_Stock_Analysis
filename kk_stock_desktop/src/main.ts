import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import './style.css'

import App from './App.vue'
import router from './router'

// 创建Vue应用实例
const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 使用插件
app.use(createPinia())
app.use(router)
app.use(ElementPlus, {
  size: 'default',
  zIndex: 3000,
})

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('全局错误:', err)
  console.error('错误信息:', info)
  
  // 检查是否是DOM相关错误
  const isDOMError = err instanceof TypeError && 
    (err.message.includes('insertBefore') || 
     err.message.includes('removeChild') || 
     err.message.includes('appendChild'))
  
  if (isDOMError) {
    console.warn('检测到DOM操作错误，这可能是由于组件快速更新造成的')
    console.warn('组件实例:', vm)
    console.warn('错误上下文:', info)
    
    // 尝试在下一个tick中重新渲染
    if (vm && typeof vm.$forceUpdate === 'function') {
      setTimeout(() => {
        try {
          vm.$forceUpdate()
        } catch (e) {
          console.warn('强制更新失败:', e)
        }
      }, 100)
    }
  }
  
  // 在生产环境中，可以将错误发送到错误监控服务
  if (import.meta.env.PROD) {
    // TODO: 发送错误到监控服务
  }
}

// 全局属性
app.config.globalProperties.$ELEMENT = {
  size: 'default',
  zIndex: 3000
}

// 挂载应用
app.mount('#app') 