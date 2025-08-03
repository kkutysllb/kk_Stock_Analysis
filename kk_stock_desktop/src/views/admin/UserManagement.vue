<template>
  <div class="user-management">
    <div class="header">
      <h1 class="title">用户管理</h1>
      <p class="subtitle">管理系统中的所有用户账户</p>
    </div>

    <!-- 用户统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">
          <UsersIcon class="w-8 h-8 text-blue-500" />
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ totalUsers }}</div>
          <div class="stat-label">总用户数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <CheckCircleIcon class="w-8 h-8 text-green-500" />
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ activeUsers }}</div>
          <div class="stat-label">活跃用户</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <XCircleIcon class="w-8 h-8 text-red-500" />
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ disabledUsers }}</div>
          <div class="stat-label">禁用用户</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <ClockIcon class="w-8 h-8 text-yellow-500" />
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ onlineUsers }}</div>
          <div class="stat-label">在线用户</div>
        </div>
      </div>
    </div>

    <!-- 用户列表 -->
    <div class="user-list-container">
      <div class="list-header">
        <h2>用户列表</h2>
        <div class="header-actions">
          <button @click="showInviteModal = true" class="invite-btn">
            <UserPlusIcon class="w-5 h-5" />
            邀请用户
          </button>
          <button @click="refreshUsers" class="refresh-btn">
            <ArrowPathIcon class="w-5 h-5" />
            刷新
          </button>
        </div>
      </div>

      <div v-if="loading" class="loading">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <div v-else-if="error" class="error">
        <ExclamationTriangleIcon class="w-8 h-8 text-red-500" />
        <p>{{ error }}</p>
        <button @click="refreshUsers" class="retry-btn">重试</button>
      </div>

      <div v-else class="user-table">
        <table>
          <thead>
            <tr>
              <th>用户ID</th>
              <th>手机号</th>
              <th>邮箱</th>
              <th>昵称</th>
              <th>角色</th>
              <th>状态</th>
              <th>注册时间</th>
              <th>最后登录</th>
              <th>登录次数</th>
              <th>在线状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.user_id" class="user-row">
              <td class="user-id">{{ user.user_id }}</td>
              <td class="phone">{{ user.phone }}</td>
              <td class="email">{{ user.email }}</td>
              <td class="nickname">{{ user.nickname || '-' }}</td>
              <td class="roles">
                <span 
                  v-for="role in user.roles" 
                  :key="role" 
                  class="role-badge"
                  :class="getRoleClass(role)"
                >
                  {{ getRoleLabel(role) }}
                </span>
              </td>
              <td class="status">
                <span 
                  class="status-badge"
                  :class="user.status === 1 ? 'status-active' : 'status-disabled'"
                >
                  {{ user.status === 1 ? '正常' : '禁用' }}
                </span>
              </td>
              <td class="create-time">{{ formatDate(user.create_time) }}</td>
              <td class="last-login">{{ formatDate(user.last_login) || '-' }}</td>
              <td class="login-count">{{ user.login_count || 0 }}</td>
              <td class="online-status">
                <span 
                  class="online-indicator"
                  :class="user.is_online ? 'online' : 'offline'"
                >
                  {{ user.is_online ? '在线' : '离线' }}
                </span>
              </td>
              <td class="actions">
                <button 
                  @click="toggleUserStatus(user)"
                  class="action-btn"
                  :class="user.status === 1 ? 'disable-btn' : 'enable-btn'"
                  :disabled="user.user_id === currentUserId"
                >
                  {{ user.status === 1 ? '禁用' : '启用' }}
                </button>
                <button 
                  @click="editUserRoles(user)"
                  class="action-btn edit-btn"
                >
                  编辑角色
                </button>
                <button 
                  @click="deleteUser(user)"
                  class="action-btn delete-btn"
                  :disabled="user.user_id === currentUserId"
                >
                  删除
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 邀请用户弹窗 -->
    <div v-if="showInviteModal" class="modal-overlay" @click="closeInviteModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>邀请新用户</h3>
          <button @click="closeInviteModal" class="close-btn">
            <XMarkIcon class="w-5 h-5" />
          </button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="inviteUser" class="invite-form">
            <div class="form-group">
              <label class="form-label">手机号 *</label>
              <input 
                v-model="inviteForm.phone"
                type="tel"
                placeholder="请输入11位手机号"
                class="form-input"
                pattern="^1[3-9]\d{9}$"
                maxlength="11"
                required
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">邮箱 *</label>
              <input 
                v-model="inviteForm.email"
                type="email"
                placeholder="请输入邮箱地址"
                class="form-input"
                required
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">昵称</label>
              <input 
                v-model="inviteForm.nickname"
                type="text"
                placeholder="请输入用户昵称（可选）"
                class="form-input"
                maxlength="20"
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">用户角色</label>
              <div class="role-checkboxes">
                <label v-for="role in availableRoles" :key="role" class="role-checkbox">
                  <input 
                    type="checkbox" 
                    :value="role"
                    v-model="inviteForm.roles"
                  />
                  <span>{{ getRoleLabel(role) }}</span>
                </label>
              </div>
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button @click="closeInviteModal" class="cancel-btn">取消</button>
          <button @click="inviteUser" class="save-btn" :disabled="inviteLoading">
            {{ inviteLoading ? '邀请中...' : '发送邀请' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 编辑角色弹窗 -->
    <div v-if="showRoleModal" class="modal-overlay" @click="closeRoleModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>编辑用户角色</h3>
          <button @click="closeRoleModal" class="close-btn">
            <XMarkIcon class="w-5 h-5" />
          </button>
        </div>
        <div class="modal-body">
          <p class="user-info">用户: {{ editingUser?.nickname || editingUser?.phone }}</p>
          <div class="role-checkboxes">
            <label v-for="role in availableRoles" :key="role" class="role-checkbox">
              <input 
                type="checkbox" 
                :value="role"
                v-model="selectedRoles"
              />
              <span>{{ getRoleLabel(role) }}</span>
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeRoleModal" class="cancel-btn">取消</button>
          <button @click="saveUserRoles" class="save-btn">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  UsersIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  XMarkIcon,
  UserPlusIcon
} from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { apiClient } from '@/api/base'
import { usePageRefresh, PAGE_REFRESH_CONFIG } from '@/utils/usePageRefresh'

interface User {
  _id: string
  user_id: string
  phone: string
  email: string
  nickname?: string
  roles: string[]
  status: number
  create_time: string
  last_login?: string
  login_count: number
  is_online?: boolean
}

const authStore = useAuthStore()
const users = ref<User[]>([])
const loading = ref(false)
const error = ref('')
const showRoleModal = ref(false)
const showInviteModal = ref(false)
const editingUser = ref<User | null>(null)
const selectedRoles = ref<string[]>([])
const inviteLoading = ref(false)

// 邀请用户表单
const inviteForm = ref({
  phone: '',
  email: '',
  nickname: '',
  roles: ['user'] as string[]
})

const availableRoles = ['user', 'analyst', 'operator', 'admin', 'super_admin']

const currentUserId = computed(() => authStore.user?.user_id)

const totalUsers = computed(() => users.value.length)
const activeUsers = computed(() => users.value.filter(u => u.status === 1).length)
const disabledUsers = computed(() => users.value.filter(u => u.status === 0).length)
const onlineUsers = computed(() => users.value.filter(u => u.is_online).length)

const getRoleClass = (role: string) => {
  const classes = {
    'super_admin': 'role-super-admin',
    'admin': 'role-admin',
    'operator': 'role-operator',
    'analyst': 'role-analyst',
    'user': 'role-user'
  }
  return classes[role as keyof typeof classes] || 'role-user'
}

const getRoleLabel = (role: string) => {
  const labels = {
    'super_admin': '超级管理员',
    'admin': '管理员',
    'operator': '操作员',
    'analyst': '分析师',
    'user': '普通用户'
  }
  return labels[role as keyof typeof labels] || role
}

const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return ''
  try {
    return new Date(dateStr).toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

const fetchUsers = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await apiClient.get('/user/admin/users')
    
    if (response.success && response.data) {
      users.value = response.data
    } else {
      throw new Error(response.message || '获取用户列表失败')
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '获取用户列表失败'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

const refreshUsers = () => {
  fetchUsers()
}

const toggleUserStatus = async (user: User) => {
  const newStatus = user.status === 1 ? 0 : 1
  const action = newStatus === 1 ? '启用' : '禁用'
  
  try {
    await ElMessageBox.confirm(
      `确定要${action}用户 ${user.nickname || user.phone} 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await apiClient.put(`/user/admin/users/${user.user_id}/status?status=${newStatus}`)
    
    if (response.success) {
      user.status = newStatus
      ElMessage.success(`用户已${action}`)
    } else {
      throw new Error(response.message || `${action}用户失败`)
    }
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err instanceof Error ? err.message : `${action}用户失败`)
    }
  }
}

const editUserRoles = (user: User) => {
  editingUser.value = user
  selectedRoles.value = [...user.roles]
  showRoleModal.value = true
}

const closeRoleModal = () => {
  showRoleModal.value = false
  editingUser.value = null
  selectedRoles.value = []
}

const saveUserRoles = async () => {
  if (!editingUser.value) return
  
  try {
    const response = await apiClient.put(`/user/admin/users/${editingUser.value.user_id}/roles`, selectedRoles.value)
    
    if (response.success) {
      editingUser.value.roles = [...selectedRoles.value]
      ElMessage.success('用户角色已更新')
      closeRoleModal()
    } else {
      throw new Error(response.message || '更新用户角色失败')
    }
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '更新用户角色失败')
  }
}

const deleteUser = async (user: User) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 ${user.nickname || user.phone} 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    const response = await apiClient.delete(`/user/admin/users/${user.user_id}`)
    
    if (response.success) {
      users.value = users.value.filter(u => u.user_id !== user.user_id)
      ElMessage.success('用户已删除')
    } else {
      throw new Error(response.message || '删除用户失败')
    }
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err instanceof Error ? err.message : '删除用户失败')
    }
  }
}

// 邀请用户相关方法
const closeInviteModal = () => {
  showInviteModal.value = false
  resetInviteForm()
}

const resetInviteForm = () => {
  inviteForm.value = {
    phone: '',
    email: '',
    nickname: '',
    roles: ['user']
  }
}

const validateInviteForm = () => {
  const { phone, email, roles } = inviteForm.value
  
  if (!phone) {
    ElMessage.error('请输入手机号')
    return false
  }
  
  if (!/^1[3-9]\d{9}$/.test(phone)) {
    ElMessage.error('请输入正确的手机号格式')
    return false
  }
  
  if (!email) {
    ElMessage.error('请输入邮箱')
    return false
  }
  
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    ElMessage.error('请输入正确的邮箱格式')
    return false
  }
  
  if (!roles || roles.length === 0) {
    ElMessage.error('请至少选择一个用户角色')
    return false
  }
  
  return true
}

const inviteUser = async () => {
  if (!validateInviteForm()) return
  
  try {
    inviteLoading.value = true
    
    // 确保手机号格式正确，自动补全+86前缀
    let phoneNumber = inviteForm.value.phone
    if (!phoneNumber.startsWith('+86')) {
      phoneNumber = `+86${phoneNumber}`
    }
    
    const response = await apiClient.post('/user/admin/invite-user', {
      phone: phoneNumber,
      email: inviteForm.value.email,
      nickname: inviteForm.value.nickname || undefined,
      roles: inviteForm.value.roles
    })
    
    if (response.success) {
      if (response.data?.email_sent) {
        ElMessage.success('用户邀请成功！邀请邮件已发送')
      } else {
        ElMessage.success(`用户邀请成功！初始密码：${response.data?.password || '请联系用户获取'}`)
      }
      closeInviteModal()
      // 刷新用户列表
      await fetchUsers()
    } else {
      throw new Error(response.message || '邀请用户失败')
    }
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '邀请用户失败')
  } finally {
    inviteLoading.value = false
  }
}

// 使用页面刷新组合函数
const { refresh } = usePageRefresh(
  fetchUsers,
  PAGE_REFRESH_CONFIG.USER_MANAGEMENT.path,
  PAGE_REFRESH_CONFIG.USER_MANAGEMENT.event
)

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
/* 用户管理页面 - 深色主题适配 */
.user-management {
  padding: 24px;
  background: var(--bg-primary);
  min-height: 100vh;
  transition: all var(--transition-base);
}

.page-header {
  margin-bottom: 32px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  background: var(--gradient-accent);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: var(--gradient-primary);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-primary);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all var(--transition-base);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--border-accent);
}

.stat-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: var(--gradient-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.user-list-container {
  background: var(--gradient-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-primary);
  overflow: hidden;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid var(--border-secondary);
  background: var(--bg-tertiary);
}

.list-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.invite-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--gradient-accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-base);
}

.invite-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-elevated);
  color: var(--text-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
  transition: all var(--transition-base);
}

.refresh-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading, .error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px;
  gap: 16px;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-primary);
  border-top: 3px solid var(--accent-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error {
  color: var(--neon-pink);
}

.retry-btn {
  padding: 8px 16px;
  background: var(--gradient-accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-base);
}

.retry-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}

.user-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-secondary);
}

th {
  background: var(--bg-tertiary);
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

td {
  font-size: 14px;
  color: var(--text-primary);
}

tbody tr:hover {
  background: var(--bg-tertiary);
}

.user-id {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--accent-primary);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--gradient-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: white;
  font-size: 14px;
  border: 2px solid var(--border-accent);
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.user-email {
  color: var(--text-secondary);
  font-size: 12px;
}

.user-roles {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.role-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  margin-right: 4px;
  margin-bottom: 2px;
}

.role-super-admin {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  color: white;
  box-shadow: 0 0 10px rgba(251, 191, 36, 0.3);
}

.role-admin {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: white;
  box-shadow: 0 0 10px rgba(139, 92, 246, 0.3);
}

.role-operator {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  color: white;
  box-shadow: 0 0 10px rgba(14, 165, 233, 0.3);
}

.role-analyst {
  background: linear-gradient(135deg, var(--neon-green), #10b981);
  color: white;
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.3);
}

.role-user {
  background: var(--bg-elevated);
  color: var(--text-primary);
  border: 1px solid var(--border-primary);
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-active {
  background: linear-gradient(135deg, var(--neon-green), #10b981);
  color: white;
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.3);
}

.status-disabled {
  background: linear-gradient(135deg, var(--neon-pink), #ef4444);
  color: white;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
}

.online-indicator {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.online {
  background: linear-gradient(135deg, var(--neon-green), #10b981);
  color: white;
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.3);
}

.offline {
  background: var(--bg-elevated);
  color: var(--text-secondary);
  border: 1px solid var(--border-primary);
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 4px 8px;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: all var(--transition-base);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.enable-btn {
  background: linear-gradient(135deg, var(--neon-green), #10b981);
  color: white;
}

.enable-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 0 15px rgba(34, 197, 94, 0.4);
}

.disable-btn {
  background: linear-gradient(135deg, var(--neon-pink), #ef4444);
  color: white;
}

.disable-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);
}

.edit-btn {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  color: white;
}

.edit-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 0 15px rgba(14, 165, 233, 0.4);
}

.delete-btn {
  background: linear-gradient(135deg, var(--neon-pink), #ef4444);
  color: white;
}

.delete-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--gradient-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid var(--border-secondary);
  background: var(--bg-tertiary);
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.close-btn {
  padding: 4px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  transition: all var(--transition-base);
}

.close-btn:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.modal-body {
  padding: 24px;
}

.user-info {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.role-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.role-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-base);
}

.role-checkbox:hover {
  background: var(--bg-tertiary);
}

.role-checkbox input {
  margin: 0;
  accent-color: var(--accent-primary);
}

.role-checkbox label {
  color: var(--text-primary);
  cursor: pointer;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 24px;
  border-top: 1px solid var(--border-secondary);
  background: var(--bg-tertiary);
}

.cancel-btn {
  padding: 8px 16px;
  background: var(--bg-elevated);
  color: var(--text-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-base);
}

.cancel-btn:hover {
  background: var(--bg-primary);
  border-color: var(--border-accent);
}

.save-btn {
  padding: 8px 16px;
  background: var(--gradient-accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-base);
}

.save-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* 邀请表单样式 */
.invite-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.form-input {
  padding: 12px;
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  color: var(--text-primary);
  font-size: 14px;
  transition: all var(--transition-base);
}

.form-input:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.1);
}

.form-input::placeholder {
  color: var(--text-tertiary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-management {
    padding: 16px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .user-table {
    font-size: 12px;
  }
  
  th, td {
    padding: 8px;
  }
  
  .actions {
    flex-direction: column;
    gap: 4px;
  }
  
  .action-btn {
    width: 100%;
  }
}

/* 深色主题特殊效果 */
.dark .stat-card {
  background: var(--gradient-primary);
  border-color: var(--border-accent);
}

.dark .stat-icon {
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}

.dark .page-title {
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
}

.dark .user-list-container {
  border-color: var(--border-accent);
}

.dark tbody tr:hover {
  background: rgba(0, 212, 255, 0.05);
}
</style>