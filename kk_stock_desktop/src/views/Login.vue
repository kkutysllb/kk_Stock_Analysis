<template>
  <div class="login-page" :class="{ dark: appStore.isDarkMode }">
    <!-- 背景装饰 -->
    <div class="login-background">
      <div class="bg-particles">
        <div class="particle" v-for="i in 30" :key="i"></div>
      </div>
      <div class="bg-grid"></div>
    </div>

    <!-- 主要内容区域 -->
    <div class="login-container">
      <!-- 左侧品牌区域 -->
      <div class="brand-section">
        <div class="brand-content">
          <div class="brand-logo">
            <div class="logo-wrapper">
              <!-- 使用真实的KK Logo -->
              <div class="logo-icon">
                <img 
                  v-if="logoImageUrl" 
                  :src="logoImageUrl" 
                  alt="KK Logo" 
                  class="logo-image"
                  @error="handleLogoError"
                />
                <ChartBarIcon v-else class="default-logo-icon"></ChartBarIcon>
              </div>
            </div>
            <h1 class="brand-title">KK 量化分析系统</h1>
            <p class="brand-subtitle">专业的股票量化分析平台</p>
          </div>
          
          <div class="feature-list">
            <div class="feature-item">
              <el-icon class="feature-icon"><TrendCharts /></el-icon>
              <div class="feature-text">
                <h3>智能策略选股</h3>
                <p>基于多维度量化模型的精准选股策略</p>
              </div>
            </div>
            <div class="feature-item">
              <el-icon class="feature-icon"><DataAnalysis /></el-icon>
              <div class="feature-text">
                <h3>量化回测分析</h3>
                <p>历史数据回测验证策略有效性</p>
              </div>
            </div>
            <div class="feature-item">
              <el-icon class="feature-icon"><Monitor /></el-icon>
              <div class="feature-text">
                <h3>实时市场监控</h3>
                <p>全市场数据实时跟踪与分析</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧登录表单区域 -->
      <div class="form-section">
        <div class="form-container">
          <!-- 表单头部 -->
          <div class="form-header">
            <h2 class="form-title">{{ showChangePassword ? '修改密码' : '欢迎回来' }}</h2>
            <p class="form-subtitle">
              {{ showChangePassword ? '修改您的登录密码' : '登录您的量化分析账户' }}
            </p>
          </div>

          <!-- 登录表单 -->
          <transition name="form-slide" mode="out-in">
            <el-form
              v-if="!showChangePassword"
              ref="loginFormRef"
              :model="loginForm"
              :rules="loginRules"
              class="login-form"
              @submit.prevent="handleLogin"
            >
              <el-form-item prop="phone" class="form-item">
                <label class="form-label">手机号</label>
                <el-input
                  v-model="loginForm.phone"
                  placeholder="请输入手机号"
                  size="large"
                  maxlength="11"
                  class="form-input"
                  @keyup.enter="handleLogin"
                >
                  <template #prefix>
                    <el-icon class="input-icon"><Phone /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-form-item prop="password" class="form-item">
                <label class="form-label">密码</label>
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="请输入密码"
                  size="large"
                  show-password
                  class="form-input"
                  @keyup.enter="handleLogin"
                >
                  <template #prefix>
                    <el-icon class="input-icon"><Lock /></el-icon>
                  </template>
                </el-input>
              </el-form-item>

              <el-button
                type="primary"
                size="large"
                :loading="authStore.loginLoading"
                @click="handleLogin"
                class="login-button"
              >
                {{ authStore.loginLoading ? '登录中...' : '立即登录' }}
              </el-button>

              <div class="form-footer">
                <el-button
                  type="link"
                  @click="showChangePassword = true"
                  class="switch-button"
                >
                  修改密码
                </el-button>
              </div>
            </el-form>

            <!-- 修改密码表单 -->
            <el-form
              v-else
              ref="changePasswordFormRef"
              :model="changePasswordForm"
              :rules="changePasswordRules"
              class="login-form"
              @submit.prevent="handleChangePassword"
            >
              <el-form-item prop="phone" class="form-item">
                <label class="form-label">手机号</label>
                <el-input
                  v-model="changePasswordForm.phone"
                  placeholder="请输入手机号"
                  size="large"
                  maxlength="11"
                  class="form-input"
                >
                  <template #prefix>
                    <el-icon class="input-icon"><Phone /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-form-item prop="oldPassword" class="form-item">
                <label class="form-label">原密码</label>
                <el-input
                  v-model="changePasswordForm.oldPassword"
                  type="password"
                  placeholder="请输入原密码"
                  size="large"
                  show-password
                  class="form-input"
                >
                  <template #prefix>
                    <el-icon class="input-icon"><Lock /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-form-item prop="newPassword" class="form-item">
                <label class="form-label">新密码</label>
                <el-input
                  v-model="changePasswordForm.newPassword"
                  type="password"
                  placeholder="请输入新密码（至少6位）"
                  size="large"
                  show-password
                  class="form-input"
                >
                  <template #prefix>
                    <el-icon class="input-icon"><Lock /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-form-item prop="confirmPassword" class="form-item">
                <label class="form-label">确认新密码</label>
                <el-input
                  v-model="changePasswordForm.confirmPassword"
                  type="password"
                  placeholder="请再次输入新密码"
                  size="large"
                  show-password
                  class="form-input"
                  @keyup.enter="handleChangePassword"
                >
                  <template #prefix>
                    <el-icon class="input-icon"><Lock /></el-icon>
                  </template>
                </el-input>
              </el-form-item>

              <el-button
                type="primary"
                size="large"
                :loading="changePasswordLoading"
                @click="handleChangePassword"
                class="login-button"
              >
                {{ changePasswordLoading ? '修改中...' : '确认修改' }}
              </el-button>

              <div class="form-footer">
                <el-button
                  type="link"
                  @click="showChangePassword = false"
                  class="switch-button"
                >
                  返回登录
                </el-button>
              </div>
            </el-form>
          </transition>

          <!-- 登录提示 -->
          <div class="login-notice">
            <el-alert
              title="温馨提示"
              type="info"
              :closable="false"
              show-icon
            >
              <template #default>
                本系统采用邀请制，请联系管理员获取账户权限
              </template>
            </el-alert>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部版权信息 -->
    <div class="login-footer">
      <p>&copy; 2024 【KK 量化】团队打造 @作者: kkutysllb 邮箱:31468130@qq.com  版本: 1.0.0</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Phone, Message, Lock, User, TrendCharts, DataAnalysis, Monitor } from '@element-plus/icons-vue'
import { ChartBarIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { validatePasswordStrength, isWeakPassword, checkSecurityWarnings } from '@/utils/security'
import { debugLogin, validatePhoneFormat, generateDebugReport } from '@/utils/loginDebug'
import type { FormInstance, FormRules } from 'element-plus'

// Router and Store
const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()

// 响应式数据
const showChangePassword = ref(false)
const loginFormRef = ref<FormInstance>()
const changePasswordFormRef = ref<FormInstance>()
const changePasswordLoading = ref(false)

// Logo管理
const logoImageUrl = ref('')

// 登录表单
const loginForm = reactive({
  phone: '',
  password: ''
})

// 修改密码表单
const changePasswordForm = reactive({
  phone: '',
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 登录表单验证规则
const loginRules: FormRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ]
}

// 修改密码表单验证规则
const changePasswordRules: FormRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  oldPassword: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== changePasswordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 登录处理
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  const valid = await loginFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  // 验证手机号格式
  const phoneValidation = validatePhoneFormat(loginForm.phone)
  if (!phoneValidation.isValid) {
    ElMessage.error(`手机号格式错误: ${phoneValidation.suggestions.join(', ')}`)
    return
  }
  
  // 安全检查
  const securityWarnings = checkSecurityWarnings()
  if (securityWarnings.length > 0) {
    console.warn('安全警告:', securityWarnings)
  }
  
  // 检查弱密码
  if (isWeakPassword(loginForm.password)) {
    ElMessage.warning('检测到弱密码，建议修改密码以提高安全性')
  }
  
  try {
    // 使用标准化的手机号
    const normalizedPhone = phoneValidation.normalizedPhone
    
    await authStore.login({
      phone: normalizedPhone,
      password: loginForm.password
    })
    
    ElMessage.success('登录成功')
    
    // 跳转到主页面
    router.push('/dashboard')
    
  } catch (error) {
    console.error('登录错误详情:', error)
    
    // 生成调试报告
    const debugResult = await debugLogin(phoneValidation.normalizedPhone, loginForm.password)
    const debugReport = generateDebugReport(debugResult)
    console.log('登录调试报告:\n', debugReport)
    
    // 显示用户友好的错误信息
    if (debugResult.statusCode === 401) {
      ElMessage.error('手机号或密码错误，请检查后重试')
    } else {
      ElMessage.error(error instanceof Error ? error.message : '登录失败')
    }
  }
}

// 修改密码处理
const handleChangePassword = async () => {
  if (!changePasswordFormRef.value) return
  
  const valid = await changePasswordFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  // 验证手机号格式
  const phoneValidation = validatePhoneFormat(changePasswordForm.phone)
  if (!phoneValidation.isValid) {
    ElMessage.error(`手机号格式错误: ${phoneValidation.suggestions.join(', ')}`)
    return
  }
  
  // 密码强度检查
  const passwordCheck = validatePasswordStrength(changePasswordForm.newPassword)
  if (!passwordCheck.isValid) {
    ElMessage.error(passwordCheck.message)
    return
  }
  
  // 弱密码检查
  if (isWeakPassword(changePasswordForm.newPassword)) {
    ElMessage.error('新密码过于简单，请使用更强的密码')
    return
  }
  
  try {
    changePasswordLoading.value = true
    
    await authStore.changePassword({
      phone: phoneValidation.normalizedPhone,
      old_password: changePasswordForm.oldPassword,
      new_password: changePasswordForm.newPassword
    })
    
    ElMessage.success('密码修改成功，请使用新密码重新登录')
    showChangePassword.value = false
    
    // 清空修改密码表单
    Object.assign(changePasswordForm, {
      phone: '',
      oldPassword: '',
      newPassword: '',
      confirmPassword: ''
    })
  } catch (error) {
    console.error('修改密码错误详情:', error)
    ElMessage.error(error instanceof Error ? error.message : '修改密码失败')
  } finally {
    changePasswordLoading.value = false
  }
}

// Logo相关方法
const handleLogoError = () => {
  // logo图片加载失败时，清空logoImageUrl，显示默认图标
  logoImageUrl.value = ''
}

const loadLogo = () => {
  // 直接使用已知的logo.jpg文件
  try {
    // 使用Vite的静态资源导入
    logoImageUrl.value = new URL('../assets/images/logo.jpg', import.meta.url).href
  } catch (error) {
    logoImageUrl.value = ''
  }
}

// 检查是否已登录
onMounted(() => {
  if (authStore.isAuthenticated) {
    router.push('/dashboard')
  }
  
  // 加载logo
  loadLogo()
})
</script>

<style scoped>
/* ============ 页面布局 ============ */
.login-page {
  min-height: 100vh;
  position: relative;
  display: flex;
  flex-direction: column;
  background: var(--gradient-primary);
  overflow: hidden;
  transition: all var(--transition-base);
}

/* ============ 背景装饰 ============ */
.login-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  opacity: 0.6;
}

.bg-particles {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.particle {
  position: absolute;
  width: 3px;
  height: 3px;
  background: var(--accent-primary);
  border-radius: 50%;
  animation: float 8s ease-in-out infinite;
  opacity: 0.4;
}

.particle:nth-child(odd) {
  animation-delay: -2s;
}

.particle:nth-child(even) {
  animation-delay: -4s;
}

.bg-grid {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(var(--border-primary) 1px, transparent 1px),
    linear-gradient(90deg, var(--border-primary) 1px, transparent 1px);
  background-size: 60px 60px;
  animation: grid-move 30s linear infinite;
  opacity: 0.3;
}

/* ============ 主容器 ============ */
.login-container {
  flex: 1;
  display: flex;
  position: relative;
  z-index: 1;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  padding: 40px;
  gap: 60px;
}

/* ============ 品牌区域 ============ */
.brand-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.brand-content {
  max-width: 500px;
  color: var(--text-primary);
  text-align: center;
}

.brand-logo {
  margin-bottom: 60px;
}

.logo-wrapper {
  width: 80px;
  height: 80px;
  margin: 0 auto 30px;
}

.logo-icon {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: var(--gradient-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  animation: logoGlow 3s ease-in-out infinite alternate;
  box-shadow: var(--shadow-glow);
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: inherit;
}

.default-logo-icon {
  width: 40px;
  height: 40px;
  color: white;
}

.brand-title {
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 16px 0;
  background: var(--gradient-accent);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-subtitle {
  font-size: 18px;
  opacity: 0.8;
  margin: 0;
  font-weight: 400;
  color: var(--text-secondary);
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  text-align: left;
  padding: 20px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  transition: all var(--transition-base);
}

.feature-item:hover {
  background: var(--bg-elevated);
  border-color: var(--accent-primary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.feature-icon {
  width: 48px;
  height: 48px;
  background: var(--gradient-accent);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
  color: white;
  box-shadow: var(--shadow-sm);
}

.feature-text h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.feature-text p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* ============ 表单区域 ============ */
.form-section {
  flex: 0 0 450px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-container {
  width: 100%;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 40px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
  position: relative;
  z-index: 10;
  transition: all 0.3s ease;
  overflow: hidden;
}

.form-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  z-index: -1;
}

.form-container::after {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.03) 0%, transparent 70%);
  z-index: -1;
  animation: pulse 4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.5;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

.form-container:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.15);
  box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.25);
  transform: translateY(-2px);
}

/* 深色模式下的样式调整 */
.login-page.dark .form-container {
  background: rgba(0, 0, 0, 0.15);
  border-color: rgba(255, 255, 255, 0.08);
}

.login-page.dark .form-container:hover {
  background: rgba(0, 0, 0, 0.25);
  border-color: rgba(255, 255, 255, 0.12);
}

.form-header {
  text-align: center;
  margin-bottom: 40px;
}

.form-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  background: linear-gradient(135deg, var(--text-primary) 0%, rgba(14, 165, 233, 0.8) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.form-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  opacity: 0.8;
}

/* ============ 表单样式 ============ */
.login-form {
  width: 100%;
}

.form-item {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.form-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 12px 16px;
  height: 48px;
  transition: all var(--transition-base);
}

.form-input :deep(.el-input__wrapper):hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(14, 165, 233, 0.4);
  box-shadow: 0 0 20px 0 rgba(14, 165, 233, 0.1);
}

.form-input :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.1);
  border-color: var(--accent-primary);
  box-shadow: 0 0 25px 0 rgba(14, 165, 233, 0.15);
}

/* 深色模式下输入框样式 */
.login-page.dark .form-input :deep(.el-input__wrapper) {
  background: rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.1);
}

.login-page.dark .form-input :deep(.el-input__wrapper):hover {
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(14, 165, 233, 0.5);
}

.login-page.dark .form-input :deep(.el-input__wrapper.is-focus) {
  background: rgba(0, 0, 0, 0.4);
}

.input-icon {
  color: var(--text-tertiary);
  font-size: 18px;
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: rgba(14, 165, 233, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(14, 165, 233, 0.3);
  margin-bottom: 24px;
  transition: all var(--transition-base);
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.login-button:hover {
  background: rgba(14, 165, 233, 0.9);
  border-color: rgba(14, 165, 233, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px 0 rgba(14, 165, 233, 0.3);
}

.form-footer {
  text-align: center;
}

.switch-button {
  color: var(--accent-primary);
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-base);
}

.switch-button:hover {
  color: var(--accent-secondary);
}

/* ============ 登录提示 ============ */
.login-notice {
  margin-top: 24px;
}

.login-notice :deep(.el-alert) {
  background: rgba(14, 165, 233, 0.1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(14, 165, 233, 0.2);
  border-radius: 12px;
  color: var(--text-primary);
}

.login-notice :deep(.el-alert__content) {
  color: var(--text-secondary);
}

.login-notice :deep(.el-alert__icon) {
  color: var(--accent-primary);
}

/* ============ 底部版权 ============ */
.login-footer {
  text-align: center;
  padding: 20px;
  color: var(--text-tertiary);
  font-size: 14px;
  position: relative;
  z-index: 1;
}

/* ============ 动画效果 ============ */
@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
    opacity: 0.4;
  }
  50% {
    transform: translateY(-30px) rotate(180deg);
    opacity: 0.8;
  }
}

@keyframes grid-move {
  0% {
    transform: translate(0, 0);
  }
  100% {
    transform: translate(60px, 60px);
  }
}

@keyframes logoGlow {
  0% {
    box-shadow: var(--shadow-glow);
  }
  100% {
    box-shadow: 0 0 30px var(--accent-primary);
  }
}

.form-slide-enter-active,
.form-slide-leave-active {
  transition: all var(--transition-slow) cubic-bezier(0.4, 0, 0.2, 1);
}

.form-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.form-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* ============ 随机粒子位置 ============ */
.particle:nth-child(1) { top: 15%; left: 8%; animation-duration: 7s; }
.particle:nth-child(2) { top: 75%; left: 18%; animation-duration: 9s; }
.particle:nth-child(3) { top: 35%; left: 65%; animation-duration: 6s; }
.particle:nth-child(4) { top: 55%; left: 85%; animation-duration: 8s; }
.particle:nth-child(5) { top: 8%; left: 45%; animation-duration: 10s; }
.particle:nth-child(6) { top: 85%; left: 75%; animation-duration: 5s; }
.particle:nth-child(7) { top: 25%; left: 25%; animation-duration: 11s; }
.particle:nth-child(8) { top: 65%; left: 5%; animation-duration: 7s; }

/* ============ 响应式设计 ============ */
@media (max-width: 1200px) {
  .login-container {
    flex-direction: column;
    gap: 40px;
    padding: 20px;
  }
  
  .brand-section {
    padding: 20px;
  }
  
  .form-section {
    flex: none;
  }
  
  .brand-title {
    font-size: 28px;
  }
  
  .feature-list {
    gap: 20px;
  }
}

@media (max-width: 768px) {
  .login-container {
    padding: 10px;
  }
  
  .form-container {
    padding: 30px 20px;
  }
  
  .brand-content {
    max-width: 100%;
  }
  
  .feature-item {
    flex-direction: column;
    text-align: center;
    gap: 12px;
    padding: 16px;
  }
  
  .feature-text {
    text-align: center;
  }
  
  .brand-logo {
    margin-bottom: 40px;
  }
  
  .logo-icon {
    width: 60px;
    height: 60px;
  }
  
  .brand-title {
    font-size: 24px;
  }
}
</style>