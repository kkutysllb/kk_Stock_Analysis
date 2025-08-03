<template>
  <div id="app" class="app-container">
    <!-- 应用标题栏 -->
    <div class="app-titlebar glass-effect" @dblclick.stop="toggleWindowMaximize($event)">
      <div class="titlebar-left">
        <div class="app-logo">
          <div class="logo-icon glow-effect">
            <!-- 使用真实logo图片，如果加载失败则显示默认图标 -->
            <img 
              v-if="logoImageUrl" 
              :src="logoImageUrl" 
              alt="KK Logo" 
              class="logo-image"
              @error="handleLogoError"
            />
            <ChartBarIcon v-else class="default-logo-icon"></ChartBarIcon>
          </div>
          <span class="logo-text text-gradient">【KK 量化】</span>
        </div>

      </div>
      
      <div class="titlebar-center">
        <!-- 空白区域，保持布局平衡 -->
      </div>
      
      <div class="titlebar-right">
        <div class="action-buttons">
          <el-tooltip content="刷新" placement="bottom">
            <button class="btn btn-ghost icon-btn" @click="refreshData">
              <ArrowPathIcon class="icon-size"></ArrowPathIcon>
            </button>
          </el-tooltip>
          
          <el-tooltip content="通知" placement="bottom">
            <button class="btn btn-ghost icon-btn" @click="showNotifications">
              <BellIcon class="icon-size"></BellIcon>
              <span v-if="notificationCount > 0" class="notification-badge">{{ notificationCount }}</span>
            </button>
          </el-tooltip>
          
          <!-- 用户登录状态 -->
          <div class="user-section">
            <template v-if="authStore.isLoggedIn">
              <!-- 用户头像和信息 -->
              <el-dropdown trigger="hover" placement="bottom-end" class="user-dropdown">
                <div class="user-profile">
                  <div class="user-avatar">
                    <div class="avatar-inner">
                      {{ getAvatarText(authStore.user?.nickname || authStore.user?.phone || '用户') }}
                    </div>
                    <div class="online-indicator"></div>
                  </div>
                  <div class="user-info">
                    <div class="user-name">{{ authStore.user?.nickname || '用户' }}</div>
                    <div class="user-role">{{ getUserRoleText(authStore.user?.roles) }}</div>
                  </div>
                  <ChevronDownIcon class="dropdown-arrow" />
                </div>
                
                <template #dropdown>
                  <el-dropdown-menu class="user-dropdown-menu">
                    <el-dropdown-item class="user-menu-header">
                      <div class="menu-user-info">
                        <div class="menu-user-avatar">
                          {{ getAvatarText(authStore.user?.nickname || authStore.user?.phone || '用户') }}
                        </div>
                        <div class="menu-user-details">
                          <div class="menu-user-name">{{ authStore.user?.nickname || '用户' }}</div>
                          <div class="menu-user-phone">{{ authStore.user?.phone }}</div>
                          <div class="menu-user-email">{{ authStore.user?.email }}</div>
                        </div>
                      </div>
                    </el-dropdown-item>
                    
                    <el-dropdown-item divided @click="goToProfile">
                      <UserIcon class="menu-icon" />
                      个人资料
                    </el-dropdown-item>
                    
                    <el-dropdown-item @click="goToSimulationTrading">
                      <ArrowTrendingUpIcon class="menu-icon" />
                      模拟交易
                    </el-dropdown-item>
                    
                    <el-dropdown-item @click="goToSettings">
                      <Cog6ToothIcon class="menu-icon" />
                      账户设置
                    </el-dropdown-item>
                    
                    <el-dropdown-item v-if="authStore.isLoggedIn && authStore.user?.roles && (authStore.user.roles.includes('super_admin') || authStore.user.roles.includes('admin'))" @click="goToUserManagement">
                      <UsersIcon class="menu-icon" />
                      用户管理
                    </el-dropdown-item>
                    
                    <el-dropdown-item divided @click="handleLogout" class="logout-item">
                      <ArrowRightOnRectangleIcon class="menu-icon" />
                      退出登录
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
            <template v-else>
              <div class="guest-info">
                <span class="guest-text">未登录</span>
              </div>
            </template>
          </div>
          
          <el-tooltip content="设置" placement="bottom">
            <button class="btn btn-ghost icon-btn" @click="goToSettings">
              <Cog6ToothIcon class="icon-size" />
            </button>
          </el-tooltip>
        </div>
        
        <div class="theme-toggle">
          <el-tooltip :content="appStore.isDarkMode ? '切换到明亮模式' : '切换到暗色模式'" placement="bottom">
            <button class="btn btn-ghost icon-btn theme-btn" @click="toggleTheme">
              <transition name="bulb-fade" mode="out-in">
                <!-- 暗色模式：点亮的灯泡 -->
                <svg v-if="appStore.isDarkMode" key="light-bulb" class="icon-size bulb-on" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C8.13 2 5 5.13 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.87-3.13-7-7-7zm2.85 11.1l-.85.6V16h-4v-2.3l-.85-.6C7.8 12.16 7 10.63 7 9c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.63-.8 3.16-2.15 4.1z"/>
                  <path d="M9 21h6c.55 0 1-.45 1-1s-.45-1-1-1H9c-.55 0-1 .45-1 1s.45 1 1 1zM10 18h4c.55 0 1-.45 1-1s-.45-1-1-1h-4c-.55 0-1 .45-1 1s.45 1 1 1z"/>
                  <!-- 光芒效果 -->
                  <path d="M12 1l.31.97L12 3l-.31-.97L12 1zM4.22 4.22l.69.69-.69.69-.69-.69.69-.69zM1 12l.97-.31L3 12l-.97.31L1 12zM4.22 19.78l.69-.69.69.69-.69.69-.69-.69zM12 21l-.31.97L12 23l.31-.97L12 21zM19.78 19.78l-.69-.69.69-.69.69.69-.69.69zM21 12l-.97.31L19 12l.97-.31L21 12zM19.78 4.22l-.69.69-.69-.69.69-.69.69.69z"/>
                </svg>
                <!-- 明亮模式：熄灭的灯泡 -->
                <svg v-else key="dark-bulb" class="icon-size bulb-off" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C8.13 2 5 5.13 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.87-3.13-7-7-7zm2.85 11.1l-.85.6V16h-4v-2.3l-.85-.6C7.8 12.16 7 10.63 7 9c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.63-.8 3.16-2.15 4.1z"/>
                  <path d="M9 21h6c.55 0 1-.45 1-1s-.45-1-1-1H9c-.55 0-1 .45-1 1s.45 1 1 1zM10 18h4c.55 0 1-.45 1-1s-.45-1-1-1h-4c-.55 0-1 .45-1 1s.45 1 1 1z"/>
                </svg>
              </transition>
            </button>
          </el-tooltip>
        </div>
      </div>
    </div>
    
    <!-- 主体容器 -->
    <div class="app-body">
      <!-- 侧边导航栏 -->
      <aside class="sidebar glass-effect" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-header">
          <button class="sidebar-toggle btn btn-ghost" @click="toggleSidebar">
            <Bars3Icon v-if="sidebarCollapsed" class="icon-size"></Bars3Icon>
            <ChevronLeftIcon v-else class="icon-size"></ChevronLeftIcon>
          </button>
        </div>
        
        <nav class="sidebar-nav">
          <div class="nav-group">
            <div v-if="!sidebarCollapsed" class="nav-group-title">主要功能</div>
            
            <router-link
              v-for="item in mainNavItems"
              :key="item.path"
              :to="item.path"
              class="nav-item glow-effect"
              :class="{ active: isCurrentRoute(item.path) }"
              @click="handleNavClick(item.path, item.title)"
            >
              <div class="nav-item-content">
                <component :is="item.icon" class="nav-icon" />
                <span v-if="!sidebarCollapsed" class="nav-text">{{ item.title }}</span>
                <div v-if="item.badge && !sidebarCollapsed" class="nav-badge">{{ item.badge }}</div>
              </div>
              <div class="nav-item-glow"></div>
            </router-link>
          </div>
        </nav>
        
        <div class="sidebar-footer">
          <div v-if="!sidebarCollapsed" class="system-stats">
            <div class="stat-item">
              <span class="stat-label">CPU</span>
              <div class="stat-bar">
                <div class="stat-fill" :style="{ width: systemStore.cpuUsage + '%' }"></div>
              </div>
              <span class="stat-value">{{ systemStore.cpuUsage }}%</span>
            </div>
            
            <div class="stat-item">
              <span class="stat-label">内存</span>
              <div class="stat-bar">
                <div class="stat-fill" :style="{ width: systemStore.memoryUsage + '%' }"></div>
              </div>
              <span class="stat-value">{{ systemStore.memoryUsage }}%</span>
            </div>
          </div>
        </div>
      </aside>
      
      <!-- 主内容区域 -->
      <main class="main-content">
        <div class="content-wrapper">
          <router-view></router-view>
        </div>
      </main>
    </div>
    
    <!-- 全局通知 -->
    <teleport to="body">
      <div v-if="notifications.length > 0" class="notification-container">
        <transition-group name="notification" tag="div">
          <div
            v-for="notification in notifications"
            :key="notification.id"
            :class="['notification', notification.type]"
          >
            <div class="notification-content">
              <component :is="getNotificationIcon(notification.type)" class="notification-icon" />
              <div class="notification-body">
                <div class="notification-title">{{ notification.title }}</div>
                <div class="notification-message">{{ notification.message }}</div>
              </div>
              <button class="notification-close" @click="removeNotification(notification.id)">
                <XMarkIcon class="icon-size"></XMarkIcon>
              </button>
            </div>
          </div>
        </transition-group>
      </div>
    </teleport>
    
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from './stores/app'
import { useSystemStore } from './stores/system'
import { useAuthStore } from './stores/auth'
import { eventBus } from '@/utils/eventBus'
// 导入Heroicons图标
import {
  Squares2X2Icon,
  ChartBarIcon,
  PresentationChartLineIcon,
  Cog6ToothIcon,
  BellIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon,
  SignalIcon,
  ChevronLeftIcon,
  Bars3Icon,
  UserIcon,
  ArrowRightOnRectangleIcon,
  UsersIcon,
  ChevronDownIcon,
  FunnelIcon,
  ArrowTrendingUpIcon,
  StarIcon
} from '@heroicons/vue/24/outline'

// 状态管理
const appStore = useAppStore()
const systemStore = useSystemStore()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

// 侧边栏状态
const sidebarCollapsed = ref(true)

// 登录相关状态已移除，使用独立登录页面

// 通知系统
const notifications = ref<any[]>([])
const notificationCount = computed(() => notifications.value.length)

// Logo管理
const logoImageUrl = ref('')

// 导航项类型定义
interface NavItem {
  path: string
  title: string
  icon: any
  badge: string | null
  requireAuth?: boolean
  requireRole?: string
}

// 导航配置
const mainNavItems = computed(() => {
  const baseItems: NavItem[] = [
    { path: '/dashboard', title: '数据概览', icon: Squares2X2Icon, badge: null },
    // { path: '/analysis/indices', title: '指数分析', icon: ChartBarIcon, badge: null },
    { path: '/analysis/futures', title: '股指期货', icon: SignalIcon, badge: null },
    { path: '/special-data', title: '特色数据', icon: StarIcon, badge: null },
    { path: '/analysis/trend', title: '趋势分析', icon: ArrowTrendingUpIcon, badge: null, requireAuth: true },
    { path: '/strategy/screening', title: '策略选股', icon: FunnelIcon, badge: null, requireAuth: true },
    { path: '/quant/backtest', title: '量化回测', icon: PresentationChartLineIcon, badge: null },
    { path: '/settings', title: '设置中心', icon: Cog6ToothIcon, badge: null }
  ]
  
  // 如果是管理员或超级管理员，添加用户管理菜单
  const hasAdminRole = authStore.isLoggedIn && authStore.user?.roles && 
    (authStore.user.roles.includes('super_admin') || authStore.user.roles.includes('admin'));
  
  if (hasAdminRole) {
    baseItems.splice(-1, 0, { 
      path: '/admin/users', 
      title: '用户管理', 
      icon: UsersIcon, 
      badge: null, 
      requireAuth: true,
      requireRole: 'admin'
    })
  }
  
  return baseItems
})

// 方法
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const isCurrentRoute = (path: string) => {
  // 处理根路径重定向到dashboard的情况
  if (path === '/dashboard' && (route.path === '/' || route.path === '/dashboard')) {
    return true
  }
  
  // 精确匹配和子路径匹配
  const isExactMatch = route.path === path
  const isChildMatch = route.path.startsWith(path + '/')
  
  return isExactMatch || isChildMatch
}

// 添加路由变化监听器进行调试
watch(() => route.path, (newPath, oldPath) => {
  // console.log('路由变化:', oldPath, '->', newPath)
}, { immediate: true })

// 导航点击处理函数
const handleNavClick = (path: string, title: string) => {
  // 手动导航以确保路由变化
  router.push(path).then(() => {
  }).catch(err => {})
}

// 用户头像文本生成
const getAvatarText = (name: string): string => {
  if (!name) return 'U'
  
  // 如果是手机号，取后两位
  if (/^\+86\d{11}$/.test(name)) {
    return name.slice(-2)
  }
  
  // 如果是中文名，取最后一个字
  if (/[\u4e00-\u9fa5]/.test(name)) {
    return name.slice(-1)
  }
  
  // 如果是英文名，取首字母
  return name.charAt(0).toUpperCase()
}

// 获取用户角色文本
const getUserRoleText = (roles: string[] | undefined): string => {
  if (!roles || roles.length === 0) return '普通用户'
  
  const roleMap: Record<string, string> = {
    'super_admin': '超级管理员',
    'admin': '管理员',
    'analyst': '分析师',
    'operator': '操作员',
    'user': '普通用户'
  }
  
  // 返回最高权限的角色
  const priorityOrder = ['super_admin', 'admin', 'analyst', 'operator', 'user']
  for (const role of priorityOrder) {
    if (roles.includes(role)) {
      return roleMap[role] || role
    }
  }
  
  return '普通用户'
}

// 导航到个人资料
const goToProfile = () => {
  router.push('/profile')
}

// 导航到用户管理
const goToUserManagement = () => {
  router.push('/admin/users')
}

// 导航到模拟交易
const goToSimulationTrading = () => {
  router.push('/simulation/trading')
}

const toggleTheme = () => {
  // 切换主题状态
  const newTheme = appStore.isDarkMode ? 'light' : 'dark'
  appStore.updateSettings({ theme: newTheme })
  
  // 应用主题
  appStore.applyTheme(newTheme)
}

const refreshData = () => {
  // 根据当前路由刷新对应页面数据
  const currentPath = route.path
  
  // 发送通用页面刷新事件
  eventBus.emit('page-refresh', currentPath)
  
  // 根据路由发送特定的刷新事件
  const refreshEventMap: Record<string, string> = {
    '/admin/users': 'refresh-users',
    '/dashboard': 'refresh-dashboard',
    '/analysis/indices': 'refresh-indices',
    '/analysis/futures': 'refresh-futures',
    '/special-data': 'refresh-special-data',
    '/analysis/trend': 'refresh-trend',
    '/strategy/screening': 'refresh-strategy',
    '/quant/backtest': 'refresh-backtest',
    '/simulation/trading': 'refresh-simulation-trading',
    '/settings': 'refresh-settings',
    '/profile': 'refresh-profile'
  }
  
  // 发送特定页面的刷新事件
  const specificEvent = refreshEventMap[currentPath]
  if (specificEvent) {
    eventBus.emit(specificEvent)
  }
  
  // 通用系统信息刷新
  systemStore.refreshSystemInfo()
  
  // 显示刷新成功通知
  addNotification('success', '刷新成功', `${getPageTitle(currentPath)}数据已更新`)
}

// 获取页面标题
const getPageTitle = (path: string): string => {
  const titleMap: Record<string, string> = {
    '/dashboard': '数据概览',
    '/analysis/indices': '指数分析',
    '/analysis/futures': '股指期货',
    '/special-data': '特色数据',
    '/analysis/trend': '趋势分析',
    '/strategy/screening': '策略选股',
    '/quant/backtest': '量化回测',
    '/simulation/trading': '模拟交易',
    '/settings': '设置中心',
    '/profile': '个人资料',
    '/admin/users': '用户管理'
  }
  return titleMap[path] || '页面'
}

const showNotifications = () => {
  addNotification('info', '通知中心', '您有新的系统通知')
}

const goToSettings = () => {
  router.push('/settings')
}

// 登出相关方法

const handleLogout = async () => {
  try {
    await authStore.logout()
    addNotification('info', '退出登录', '您已成功退出登录')
    // 退出后跳转到登录页面
    router.push('/login')
  } catch (error) {
    console.error('退出登录失败:', error)
    addNotification('error', '退出失败', '退出登录时发生错误')
  }
}

// 双击标题栏最大化/还原窗口
const toggleWindowMaximize = async (event: MouseEvent | undefined) => {
  // 检查 electronAPI 是否存在
  if (!window.electronAPI) {
    console.warn('Electron API 不可用，可能在浏览器环境中运行')
    return
  }
  
  try {
    // 调用 Electron API 切换窗口最大化状态
    console.log('正在调用 toggleMaximize 方法...')
    const isMaximized = await window.electronAPI.toggleMaximize()
    console.log('窗口状态已切换，当前是否最大化:', isMaximized)
  } catch (error) {
    console.error('切换窗口最大化状态失败:', error)
  }
}

const addNotification = (type: string, title: string, message: string) => {
  const id = Date.now()
  notifications.value.push({ id, type, title, message })
  
  // 3秒后自动移除
  setTimeout(() => {
    removeNotification(id)
  }, 3000)
}

const removeNotification = (id: number) => {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index > -1) {
    notifications.value.splice(index, 1)
  }
}

const getNotificationIcon = (type: string) => {
  const icons = {
    success: CheckCircleIcon,
    error: XCircleIcon,
    warning: ExclamationTriangleIcon,
    info: InformationCircleIcon
  }
  return icons[type as keyof typeof icons] || InformationCircleIcon
}

const handleLogoError = () => {
  // logo图片加载失败时，清空logoImageUrl，显示默认图标
  logoImageUrl.value = ''
}

const loadLogo = () => {
  // 直接使用已知的logo.jpg文件
  try {
    // 使用Vite的静态资源导入
    logoImageUrl.value = new URL('./assets/images/logo.jpg', import.meta.url).href
  } catch (error) {
    logoImageUrl.value = ''
  }
}

// 生命周期
onMounted(() => {
  // 初始化应用
  appStore.initialize()
  
  // 初始化认证状态
  authStore.initAuth()
  
  // 加载logo
  loadLogo()
  
  // 启动系统监控
  systemStore.startMonitoring()
  
  // 事件总线已经处理登录弹窗显示逻辑
  
  // 欢迎通知
  setTimeout(() => {
    addNotification('success', '欢迎使用', '【KK 量化】分析系统已就绪')
  }, 1000)
})

onUnmounted(() => {
  systemStore.stopMonitoring()
})
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  overflow: hidden;
  margin: 0;
  padding: 0;
}

/* ========== 标题栏样式 ========== */
.app-titlebar {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-lg);
  border-bottom: 1px solid var(--border-primary);
  z-index: 100;
}

.titlebar-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.app-logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.logo-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--gradient-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: white;
  overflow: hidden;
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: inherit;
}

.default-logo {
  font-size: 18px;
  line-height: 1;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.system-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.status-tag {
  --el-tag-border-radius: var(--radius-sm);
}

.titlebar-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.breadcrumb-nav {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  color: var(--text-secondary);
  font-size: 14px;
}

.titlebar-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.user-section {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 8px;
  padding: 0 8px;
  border-left: 1px solid var(--border-primary);
  border-right: 1px solid var(--border-primary);
}

/* ========== 用户头像和下拉菜单 ========== */
.user-dropdown {
  cursor: pointer;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.user-profile::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(255, 20, 147, 0.1));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.user-profile:hover {
  background: var(--bg-elevated);
  border-color: var(--accent-primary);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.2);
}

.user-profile:hover::before {
  opacity: 1;
}

.user-avatar {
  position: relative;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-primary), var(--neon-cyan));
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 212, 255, 0.3);
  z-index: 1;
}

.avatar-inner {
  color: white;
  font-size: 14px;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.online-indicator {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  background: #00ff88;
  border: 2px solid white;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(0, 255, 136, 0.6);
  animation: pulse-online 2s infinite;
}

@keyframes pulse-online {
  0%, 100% { 
    transform: scale(1);
    box-shadow: 0 0 8px rgba(0, 255, 136, 0.6);
  }
  50% { 
    transform: scale(1.1);
    box-shadow: 0 0 12px rgba(0, 255, 136, 0.8);
  }
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  z-index: 1;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-role {
  font-size: 11px;
  font-weight: 500;
  color: var(--accent-primary);
  opacity: 0.8;
}

.dropdown-arrow {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
  transition: transform 0.3s ease;
  z-index: 1;
}

.user-profile:hover .dropdown-arrow {
  transform: rotate(180deg);
  color: var(--accent-primary);
}

/* ========== 用户下拉菜单样式 ========== */
.user-dropdown-menu {
  min-width: 280px;
  border: 1px solid var(--border-primary);
  border-radius: 12px;
  background: var(--bg-primary);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
  overflow: hidden;
}

.user-menu-header {
  padding: 16px !important;
  background: linear-gradient(135deg, var(--bg-secondary), var(--bg-elevated));
  border-bottom: 1px solid var(--border-primary);
  cursor: default;
}

.user-menu-header:hover {
  background: linear-gradient(135deg, var(--bg-secondary), var(--bg-elevated)) !important;
}

.menu-user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-user-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-primary), var(--neon-cyan));
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
}

.menu-user-details {
  flex: 1;
  min-width: 0;
}

.menu-user-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.menu-user-phone {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 2px;
}

.menu-user-email {
  font-size: 12px;
  color: var(--text-tertiary);
}

.menu-icon {
  width: 16px;
  height: 16px;
  margin-right: 8px;
  color: var(--text-secondary);
}

.logout-item {
  color: var(--danger-primary) !important;
}

.logout-item .menu-icon {
  color: var(--danger-primary) !important;
}

/* ========== 游客状态样式 ========== */
.guest-info {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: 8px;
}

.guest-text {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.btn-primary {
  background: var(--accent-primary);
  color: white;
  border: 1px solid var(--accent-primary);
}

.btn-primary:hover {
  background: var(--neon-cyan);
  border-color: var(--neon-cyan);
}

.icon-btn {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.notification-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--neon-pink);
  color: white;
  font-size: 10px;
  font-weight: 600;
  min-width: 16px;
  height: 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ========== 主体布局 ========== */
.app-body {
  flex: 1;
  display: flex;
  min-height: 0;
  margin: 0;
  padding: 0;
}

/* ========== 侧边栏样式 ========== */
.sidebar {
  width: 280px;
  background: var(--gradient-primary);
  border-right: 1px solid var(--border-primary);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-base);
  z-index: 50;
  flex-shrink: 0;
  margin: 0;
  padding: 0;
}

.sidebar.collapsed {
  width: 70px;
  margin: 0;
  padding: 0;
  border-right-width: 0; /* 收起时移除右边框 */
}

.sidebar-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 var(--spacing-md);
  border-bottom: 1px solid var(--border-secondary);
}

.sidebar-toggle {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
}

.sidebar-nav {
  flex: 1;
  padding: var(--spacing-md);
  overflow-y: auto;
}

.nav-group {
  margin-bottom: var(--spacing-lg);
}

.nav-group-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: var(--spacing-sm);
  padding: 0 var(--spacing-sm);
}

.nav-item {
  position: relative;
  display: block;
  padding: var(--spacing-sm) var(--spacing-md);
  margin-bottom: var(--spacing-xs);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  text-decoration: none;
  transition: all var(--transition-base);
  overflow: hidden;
  z-index: 1;
  pointer-events: auto;
}

.nav-item-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  position: relative;
  z-index: 1;
}

.nav-icon {
  font-size: 18px;
  min-width: 20px;
}

.nav-text {
  font-size: 14px;
  font-weight: 500;
  flex: 1;
}

.nav-badge {
  background: var(--accent-primary);
  color: white;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  min-width: 16px;
  text-align: center;
}

.nav-item:hover,
.nav-item.active {
  color: var(--accent-primary);
  background: rgba(0, 212, 255, 0.1);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--accent-primary);
  border-radius: 0 2px 2px 0;
}

.nav-item-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--gradient-glow);
  opacity: 0;
  transition: opacity var(--transition-base);
}

.nav-item:hover .nav-item-glow {
  opacity: 1;
}

/* 子菜单样式 */
.nav-submenu {
  margin-bottom: var(--spacing-sm);
}

.submenu-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
}

.submenu-header:hover {
  color: var(--accent-primary);
  background: rgba(0, 212, 255, 0.05);
}

.submenu-arrow {
  margin-left: auto;
  font-size: 12px;
  transition: transform var(--transition-base);
}

.submenu-content {
  margin-top: var(--spacing-xs);
  padding-left: var(--spacing-lg);
}

.submenu-item {
  padding: var(--spacing-xs) var(--spacing-md);
  font-size: 13px;
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: var(--spacing-md);
  border-top: 1px solid var(--border-secondary);
}

.system-stats {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 11px;
}

.stat-label {
  color: var(--text-tertiary);
  min-width: 30px;
}

.stat-bar {
  flex: 1;
  height: 4px;
  background: var(--bg-elevated);
  border-radius: 2px;
  overflow: hidden;
}

.stat-fill {
  height: 100%;
  background: var(--gradient-accent);
  transition: width var(--transition-base);
}

.stat-value {
  color: var(--text-secondary);
  min-width: 30px;
  text-align: right;
}

/* ========== 主内容区域 ========== */
.main-content {
  flex: 1;
  min-width: 0;
  background: var(--bg-primary);
  margin-left: 0;
}

.content-wrapper {
  height: 100%;
  overflow: auto;
  padding: var(--spacing-lg);
}

.page-component {
  min-height: calc(100vh - 140px);
}

/* ========== 主题切换按钮样式 ========== */
.theme-btn {
  position: relative;
  transition: all 0.3s ease;
}

.theme-btn:hover {
  transform: scale(1.1);
}

/* 灯泡图标样式 */
.bulb-on {
  color: #fbbf24; /* 黄色，表示点亮 */
  filter: drop-shadow(0 0 8px rgba(251, 191, 36, 0.6));
  animation: glow 2s ease-in-out infinite alternate;
}

.bulb-off {
  color: #6b7280; /* 灰色，表示熄灭 */
  transition: color 0.3s ease;
}

.dark .bulb-off {
  color: #9ca3af;
}

/* 发光动画 */
@keyframes glow {
  from {
    filter: drop-shadow(0 0 8px rgba(251, 191, 36, 0.4));
  }
  to {
    filter: drop-shadow(0 0 12px rgba(251, 191, 36, 0.8));
  }
}

/* 灯泡切换动画 */
.bulb-fade-enter-active,
.bulb-fade-leave-active {
  transition: all 0.3s ease;
}

.bulb-fade-enter-from {
  opacity: 0;
  transform: scale(0.8) rotate(-10deg);
}

.bulb-fade-leave-to {
  opacity: 0;
  transform: scale(0.8) rotate(10deg);
}

/* ========== 页面切换动画 ========== */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: all var(--transition-base);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* ========== 通知系统 ========== */
.notification-container {
  position: fixed;
  top: var(--spacing-lg);
  right: var(--spacing-lg);
  z-index: 2000;
  max-width: 400px;
}

.notification-enter-active,
.notification-leave-active {
  transition: all var(--transition-base);
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.notification-content {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
}

.notification-icon {
  font-size: 20px;
  margin-top: 2px;
}

.notification-body {
  flex: 1;
}

.notification-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: var(--spacing-xs);
}

.notification-message {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.notification-close {
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 2px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.notification-close:hover {
  color: var(--text-primary);
  background: var(--bg-elevated);
}

/* ========== 响应式设计 ========== */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 60px;
    height: calc(100vh - 60px);
    transform: translateX(-100%);
    transition: transform var(--transition-base);
  }
  
  .sidebar.collapsed {
    width: 280px;
    transform: translateX(0);
  }
  
  .main-content {
    margin-left: 0;
  }
  
  .titlebar-center {
    display: none;
  }
  
  .content-wrapper {
    padding: var(--spacing-md);
  }
}
</style>