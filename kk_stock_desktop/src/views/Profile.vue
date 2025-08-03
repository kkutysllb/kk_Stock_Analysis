<template>
  <div class="profile-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <UserIcon class="page-icon" />
          <div class="header-info">
            <h1 class="page-title">个人资料</h1>
            <p class="page-subtitle">管理您的账户信息和偏好设置</p>
          </div>
        </div>
        <div class="header-actions">
          <el-button type="primary" :icon="EditIcon" @click="toggleEditMode">
            {{ isEditing ? '保存更改' : '编辑资料' }}
          </el-button>
        </div>
      </div>
    </div>

    <div class="profile-content">
      <!-- 用户基本信息卡片 -->
      <div class="profile-section">
        <div class="section-header">
          <h2 class="section-title">
            <IdentificationIcon class="section-icon" />
            基本信息
          </h2>
        </div>
        
        <div class="info-grid">
          <!-- 用户头像和昵称 -->
          <div class="info-card user-avatar-card">
            <div class="avatar-section">
              <div class="user-avatar-large">
                <div class="avatar-inner-large">
                  {{ getAvatarText(userInfo?.nickname || userInfo?.user_id || '用户') }}
                </div>
                <div class="online-indicator-large"></div>
              </div>
              <div class="avatar-info">
                <div class="nickname-section">
                  <template v-if="!isEditing">
                    <h3 class="user-nickname">{{ userInfo?.nickname || userInfo?.user_id || '未设置昵称' }}</h3>
                  </template>
                  <template v-else>
                    <el-input
                      v-model="editForm.nickname"
                      placeholder="请输入昵称"
                      size="large"
                      class="nickname-input"
                      maxlength="20"
                      show-word-limit
                    />
                  </template>
                </div>
                <div class="user-role-badge">
                  <el-tag :type="getRoleTagType(userInfo?.roles?.[0])">
                    {{ getRoleText(userInfo?.roles?.[0]) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>

          <!-- 用户ID -->
          <div class="info-card">
            <div class="info-item">
              <div class="info-label">
                <FingerPrintIcon class="info-icon" />
                用户ID
              </div>
              <div class="info-value">{{ userInfo?.user_id }}</div>
            </div>
          </div>

          <!-- 注册邮箱 -->
          <div class="info-card">
            <div class="info-item">
              <div class="info-label">
                <EnvelopeIcon class="info-icon" />
                注册邮箱
              </div>
              <div class="info-value">{{ userInfo?.email || '未设置' }}</div>
            </div>
          </div>

          <!-- 手机号 -->
          <div class="info-card">
            <div class="info-item">
              <div class="info-label">
                <PhoneIcon class="info-icon" />
                手机号码
              </div>
              <div class="info-value">{{ formatPhone(userInfo?.phone) }}</div>
            </div>
          </div>

          <!-- 用户状态 -->
          <div class="info-card">
            <div class="info-item">
              <div class="info-label">
                <ShieldCheckIcon class="info-icon" />
                账户状态
              </div>
              <div class="info-value">
                <el-tag :type="userInfo?.status === 1 ? 'success' : 'danger'">
                  {{ userInfo?.status === 1 ? '正常' : '已禁用' }}
                </el-tag>
              </div>
            </div>
          </div>

          <!-- 注册时间 -->
          <div class="info-card">
            <div class="info-item">
              <div class="info-label">
                <CalendarIcon class="info-icon" />
                注册时间
              </div>
              <div class="info-value">{{ formatDateTimeBeijing(userInfo?.create_time) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 登录统计信息 -->
      <div class="profile-section">
        <div class="section-header">
          <h2 class="section-title">
            <ChartBarIcon class="section-icon" />
            登录统计
          </h2>
        </div>

        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon success">
              <ArrowRightOnRectangleIcon class="stat-icon-inner" />
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ userInfo?.login_count || 0 }}</div>
              <div class="stat-label">总登录次数</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon primary">
              <ClockIcon class="stat-icon-inner" />
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatDateTimeBeijing(userInfo?.last_login) || '从未登录' }}</div>
              <div class="stat-label">最后登录时间</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon warning">
              <CalendarDaysIcon class="stat-icon-inner" />
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ getAccountAge() }}</div>
              <div class="stat-label">账户使用天数</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 股票池信息 -->
      <div class="profile-section">
        <div class="section-header">
          <h2 class="section-title">
            <RectangleStackIcon class="section-icon" />
            我的股票池
          </h2>
          <div class="section-actions">
            <el-button size="small" @click="refreshStockPools">
              <ArrowPathIcon class="action-icon" />
              刷新
            </el-button>
          </div>
        </div>

        <div class="stock-pools-container" v-loading="stockPoolsLoading">
          <div v-if="stockPools.length === 0" class="empty-state">
            <RectangleStackIcon class="empty-icon" />
            <p class="empty-text">暂无股票池</p>
          </div>
          
          <div v-else class="stock-pools-grid">
            <div
              v-for="pool in stockPools"
              :key="pool.pool_id"
              class="stock-pool-card"
            >
              <div class="pool-header">
                <div class="pool-info">
                  <h4 class="pool-name">{{ pool.pool_name }}</h4>
                  <p class="pool-description">{{ pool.description || '暂无描述' }}</p>
                  <div class="pool-tags" v-if="pool.tags && pool.tags.length > 0">
                    <el-tag v-for="tag in pool.tags" :key="tag" size="small" type="info">{{ tag }}</el-tag>
                  </div>
                </div>
                <div class="pool-stats">
                  <div class="stock-count">
                    <span class="count-number">{{ pool.stock_count || 0 }}</span>
                    <span class="count-label">只股票</span>
                  </div>
                  <div class="pool-type">
                    <el-tag size="small" :type="pool.is_default ? 'success' : 'primary'">
                      {{ pool.is_default ? '默认' : '自定义' }}
                    </el-tag>
                  </div>
                </div>
              </div>
              
              <div class="pool-meta">
                <div class="meta-item">
                  <CalendarIcon class="meta-icon" />
                  <span class="meta-text">{{ formatDateTimeBeijing(pool.create_time) }}</span>
                </div>
                <div class="meta-item">
                  <ClockIcon class="meta-icon" />
                  <span class="meta-text">{{ formatDateTimeBeijing(pool.update_time) }}</span>
                </div>
              </div>

              <!-- 股票列表预览 -->
              <div v-if="pool.stocks && pool.stocks.length > 0" class="stocks-preview">
                <div class="stocks-header">
                  <span class="stocks-title">股票列表</span>
                </div>
                <div class="stocks-list">
                  <div
                    v-for="stock in pool.stocks.slice(0, 3)"
                    :key="stock.ts_code"
                    class="stock-item"
                  >
                    <span class="stock-symbol">{{ stock.ts_code }}</span>
                    <span class="stock-name">{{ stock.name }}</span>
                  </div>
                  <div v-if="pool.stocks.length > 3" class="more-stocks">
                    +{{ pool.stocks.length - 3 }} 更多
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  UserIcon,
  IdentificationIcon,
  FingerPrintIcon,
  EnvelopeIcon,
  PhoneIcon,
  ShieldCheckIcon,
  CalendarIcon,
  ChartBarIcon,
  ArrowRightOnRectangleIcon,
  ClockIcon,
  CalendarDaysIcon,
  RectangleStackIcon,
  ArrowPathIcon,
  PencilIcon as EditIcon
} from '@heroicons/vue/24/outline'

import { useAuthStore } from '@/stores/auth'
import { userStockPoolsApi } from '@/api/userStockPools'
import type { StockPool } from '@/api/userStockPools'
import type { UserInfoResponse } from '@/api/auth'

// Stores
const authStore = useAuthStore()

// 响应式数据
const isEditing = ref(false)
const stockPoolsLoading = ref(false)
const stockPools = ref<StockPool[]>([])

// 编辑表单
const editForm = reactive({
  nickname: ''
})

// 已在导入时获取API客户端实例

// 计算属性
const userInfo = computed<UserInfoResponse | null>(() => {
  return authStore.user as UserInfoResponse | null
})

// 方法
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

const formatPhone = (phone: string | undefined): string => {
  if (!phone) return '未设置'
  if (phone.startsWith('+86')) {
    const num = phone.substring(3)
    return `${num.substring(0, 3)}****${num.substring(7)}`
  }
  return phone
}

const formatDateTime = (dateTime: string | undefined): string => {
  if (!dateTime) return '未知'
  const date = new Date(dateTime)
  return date.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
}

const formatDate = (dateTime: string | undefined): string => {
  if (!dateTime) return '未知'
  const date = new Date(dateTime)
  return date.toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai' })
}

const formatDateTimeBeijing = (dateTime: string | undefined): string => {
  if (!dateTime) return '未知'
  
  // 如果是UTC时间字符串，直接解析
  const date = new Date(dateTime)
  
  // 确保以北京时间显示
  return date.toLocaleString('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const getRoleText = (role: string | undefined): string => {
  const roleMap: Record<string, string> = {
    'super_admin': '超级管理员',
    'admin': '管理员',
    'analyst': '分析师',
    'operator': '操作员',
    'user': '普通用户'
  }
  return roleMap[role || 'user'] || '普通用户'
}

const getRoleTagType = (role: string | undefined): string => {
  const roleTypeMap: Record<string, string> = {
    'super_admin': 'danger',
    'admin': 'warning',
    'analyst': 'success',
    'operator': 'info',
    'user': 'primary'
  }
  return roleTypeMap[role || 'user'] || 'primary'
}

const getAccountAge = (): string => {
  if (!userInfo.value?.create_time) return '0 天'
  
  const createDate = new Date(userInfo.value.create_time)
  const now = new Date()
  const diffTime = Math.abs(now.getTime() - createDate.getTime())
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  return `${diffDays} 天`
}

const toggleEditMode = async () => {
  if (isEditing.value) {
    // 保存更改
    try {
      await authStore.updateUserInfo({ 
        nickname: editForm.nickname || undefined 
      })
      ElMessage.success('资料更新成功')
      isEditing.value = false
    } catch (error) {
      console.error('更新用户信息失败:', error)
      ElMessage.error('更新失败，请重试')
    }
  } else {
    // 进入编辑模式
    editForm.nickname = userInfo.value?.nickname || ''
    isEditing.value = true
  }
}

const refreshStockPools = async () => {
  try {
    stockPoolsLoading.value = true
    stockPools.value = await userStockPoolsApi.getUserStockPools()
  } catch (error) {
    console.error('获取股票池失败:', error)
    ElMessage.error('获取股票池信息失败')
  } finally {
    stockPoolsLoading.value = false
  }
}

// 生命周期
onMounted(async () => {
  // 加载股票池信息
  await refreshStockPools()
})
</script>

<style scoped>
/* ============ 页面布局 ============ */
.profile-page {
  min-height: 100vh;
  background: var(--bg-primary);
  padding: var(--spacing-lg);
}

/* ============ 页面头部 ============ */
.page-header {
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  margin-bottom: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.page-icon {
  width: 32px;
  height: 32px;
  color: var(--accent-primary);
  background: var(--gradient-accent);
  padding: 8px;
  border-radius: var(--radius-md);
  color: white;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

/* ============ 内容区域 ============ */
.profile-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.profile-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base);
}

.profile-section:hover {
  border-color: var(--border-accent);
  box-shadow: var(--shadow-md);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--border-secondary);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.section-icon {
  width: 20px;
  height: 20px;
  color: var(--accent-primary);
}

.section-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.action-icon {
  width: 16px;
  height: 16px;
}

/* ============ 信息网格 ============ */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-md);
}

.info-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  transition: all var(--transition-base);
}

.info-card:hover {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-sm);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.info-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.info-icon {
  width: 16px;
  height: 16px;
  color: var(--accent-primary);
}

.info-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  word-break: break-all;
}

/* ============ 用户头像卡片 ============ */
.user-avatar-card {
  grid-column: 1 / -1;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.user-avatar-large {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--gradient-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-glow);
  flex-shrink: 0;
}

.avatar-inner-large {
  color: white;
  font-size: 24px;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.online-indicator-large {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 20px;
  height: 20px;
  background: var(--neon-green);
  border: 3px solid var(--bg-primary);
  border-radius: 50%;
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.6);
}

.avatar-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.nickname-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.user-nickname {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.nickname-input {
  max-width: 200px;
}

.user-role-badge {
  display: flex;
  align-items: center;
}

/* ============ 统计卡片 ============ */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-md);
}

.stat-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  transition: all var(--transition-base);
}

.stat-card:hover {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-sm);
  transform: translateY(-2px);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon.success {
  background: rgba(34, 197, 94, 0.1);
  color: var(--neon-green);
}

.stat-icon.primary {
  background: rgba(14, 165, 233, 0.1);
  color: var(--accent-primary);
}

.stat-icon.warning {
  background: rgba(251, 191, 36, 0.1);
  color: #fbbf24;
}

.stat-icon-inner {
  width: 24px;
  height: 24px;
}

.stat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
}

/* ============ 股票池 ============ */
.stock-pools-container {
  min-height: 200px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2xl);
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-md);
}

.empty-text {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0;
}

.stock-pools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: var(--spacing-md);
}

.stock-pool-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  transition: all var(--transition-base);
}

.stock-pool-card:hover {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-sm);
  transform: translateY(-2px);
}

.pool-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-md);
}

.pool-info {
  flex: 1;
}

.pool-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-xs) 0;
}

.pool-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 var(--spacing-xs) 0;
}

.pool-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-xs);
}

.pool-stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--spacing-sm);
}

.stock-count {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-sm);
  background: var(--gradient-accent);
  border-radius: var(--radius-sm);
  color: white;
  min-width: 60px;
}

.count-number {
  font-size: 18px;
  font-weight: 700;
}

.count-label {
  font-size: 12px;
  opacity: 0.8;
}

.pool-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-secondary);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 12px;
  color: var(--text-tertiary);
}

.meta-icon {
  width: 14px;
  height: 14px;
}

.stocks-preview {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-secondary);
}

.stocks-header {
  margin-bottom: var(--spacing-sm);
}

.stocks-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.stocks-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.stock-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-xs);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.stock-symbol {
  font-weight: 600;
  color: var(--accent-primary);
}

.stock-name {
  color: var(--text-secondary);
}

.more-stocks {
  text-align: center;
  font-size: 12px;
  color: var(--text-tertiary);
  padding: var(--spacing-xs);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

/* ============ 响应式设计 ============ */
@media (max-width: 768px) {
  .profile-page {
    padding: var(--spacing-md);
  }
  
  .page-header {
    padding: var(--spacing-lg);
  }
  
  .header-content {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .avatar-section {
    flex-direction: column;
    text-align: center;
    gap: var(--spacing-md);
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stock-pools-grid {
    grid-template-columns: 1fr;
  }
}
</style>