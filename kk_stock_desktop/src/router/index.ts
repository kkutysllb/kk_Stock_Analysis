import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { eventBus } from '@/utils/eventBus'

// 使用类型断言解决导入Vue组件时的类型错误
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: {
      title: '用户登录',
      requireAuth: false,
      hideInMenu: true
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: {
      title: '数据概览',
      icon: 'Odometer',
      requireAuth: true
    }
  },
  
  // {
  //   path: '/analysis/indices',
  //   name: 'IndexBoard',
  //   component: () => import('@/views/analysis/IndexBoard.vue'),
  //   meta: {
  //     title: '指数分析',
  //     icon: 'DataBoard',
  //     requireAuth: true
  //   }
  // },
  {
    path: '/analysis/futures',
    name: 'FuturesAnalysis',
    component: () => import('@/views/analysis/FuturesAnalysis.vue'),
    meta: {
      title: '股指期货',
      icon: 'ChartBarSquare',
      requireAuth: true
    }
  },
  {
    path: '/special-data',
    name: 'SpecialData',
    component: () => import('@/views/SpecialData.vue'),
    meta: {
      title: '特色数据',
      icon: 'Star',
      requireAuth: true
    }
  },
  {
    path: '/analysis/trend',
    name: 'TrendAnalysis',
    component: () => import('@/views/analysis/TrendAnalysis.vue'),
    meta: {
      title: '趋势分析',
      icon: 'ArrowTrendingUp',
      requireAuth: true
    }
  },
  // {
  //   path: '/analysis/results-summary',
  //   name: 'AnalysisResultsSummaryPage',
  //   component: () => import('@/views/analysis/AnalysisResultsSummaryPage.vue'),
  //   meta: {
  //     title: '分析结果汇总',
  //     icon: 'ChartBar',
  //     requireAuth: true
  //   }
  // },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: {
      title: '个人资料',
      requireAuth: true,
      hideInMenu: true
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: {
      title: '设置中心',
      icon: 'Setting',
      requireAuth: true
    }
  },
  {
    path: '/strategy/screening',
    name: 'StrategyScreening',
    component: () => import('@/views/StrategyScreening.vue'),
    meta: {
      title: '策略选股',
      icon: 'ChartBar',
      requireAuth: true
    }
  },
  {
    path: '/quant/backtest',
    name: 'QuantBacktest',
    component: () => import('@/views/QuantBacktest.vue'),
    meta: {
      title: '量化回测',
      icon: 'ChartLine',
      requireAuth: true
    }
  },
  {
    path: '/simulation/trading',
    name: 'SimulationTrading',
    component: () => import('@/views/SimulationTrading.vue'),
    meta: {
      title: '模拟交易',
      icon: 'ArrowTrendingUp',
      requireAuth: true
    }
  },
  {
    path: '/admin/users',
    name: 'UserManagement',
    component: () => import('@/views/admin/UserManagement.vue'),
    meta: {
      title: '用户管理',
      icon: 'Users',
      requireAuth: true,
      requireRole: 'admin'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: {
      title: '页面未找到'
    }
  }
]

const router = createRouter({
  history: createWebHistory('/'),
  routes
})

// 全局前置守卫
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 股票量化分析系统`
  } else {
    document.title = '股票量化分析系统'
  }
  
  // 如果有token但认证状态未初始化，尝试初始化
  const savedToken = localStorage.getItem('access-token')
  if (savedToken && !authStore.isAuthenticated) {
    authStore.initAuth()
    // 如果初始化后仍然没有认证状态，尝试验证token
    if (!authStore.isAuthenticated) {
      try {
        await authStore.checkAuth()
      } catch (error) {
        console.error('Token验证失败:', error)
        // Token无效，清除认证信息
        authStore.clearAuth()
      }
    }
  }
  
  // 如果已登录且访问登录页面，重定向到首页
  if (to.name === 'Login' && authStore.isAuthenticated) {
    next('/dashboard')
    return
  }
  
  // 检查是否需要认证
  if (to.meta.requireAuth !== false && !authStore.isAuthenticated) {
    // 如果需要认证但用户未登录，重定向到登录页面
    next('/login')
    return
  }
  
  // 检查角色权限
  if (to.meta.requireRole && authStore.isAuthenticated) {
    const userRoles = authStore.user?.roles || []
    const requiredRole = to.meta.requireRole as string
    
    // 对于admin权限，同时检查admin和super_admin角色
    let hasPermission = false
    if (requiredRole === 'admin') {
      hasPermission = userRoles.includes('admin') || userRoles.includes('super_admin')
    } else {
      hasPermission = userRoles.includes(requiredRole)
    }
    
    if (!hasPermission) {
      // 用户没有所需角色权限，重定向到首页
      next('/dashboard')
      return
    }
  }
  
  next()
})

export default router