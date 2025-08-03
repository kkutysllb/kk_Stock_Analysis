<template>
  <el-dialog
    v-model="visible"
    width="450px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    class="login-modal"
    align-center
  >
    <template #header>
      <div class="login-header">
        <div class="login-logo">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" class="logo-svg">
              <path d="M12 2L13.09 8.26L20 9L13.09 9.74L12 16L10.91 9.74L4 9L10.91 8.26L12 2Z" fill="currentColor"/>
              <circle cx="12" cy="12" r="3" fill="currentColor" opacity="0.6"/>
            </svg>
          </div>
          <h2 class="login-title">{{ showRegister ? '用户注册' : '用户登录' }}</h2>
        </div>
        <div class="login-subtitle">
          {{ showRegister ? '创建您的量化分析账户' : '欢迎使用 KK 量化分析系统' }}
        </div>
      </div>
    </template>

    <div class="login-container">
      <!-- 登录表单 -->
      <transition name="form-slide" mode="out-in">
        <el-form
          v-if="!showRegister"
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          label-width="0"
          class="login-form"
          @submit.prevent="handleLogin"
        >
          <div class="form-group">
            <el-form-item prop="phone">
              <div class="input-wrapper">
                <el-input
                  v-model="loginForm.phone"
                  placeholder="请输入手机号"
                  size="large"
                  maxlength="11"
                  class="custom-input"
                  @keyup.enter="handleLogin"
                >
                  <template #prefix>
                    <el-icon class="input-icon"><Phone /></el-icon>
                  </template>
                  <template #prepend>
                    <span class="country-code">+86</span>
                  </template>
                </el-input>
              </div>
            </el-form-item>
            
            <el-form-item prop="password">
              <div class="input-wrapper">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="请输入密码"
                  size="large"
                  show-password
                  class="custom-input"
                  @keyup.enter="handleLogin"
                >
                  <template #prefix>
                    <el-icon class="input-icon"><Lock /></el-icon>
                  </template>
                </el-input>
              </div>
            </el-form-item>
          </div>
          
          <div class="form-actions">
            <el-button
              type="primary"
              size="large"
              :loading="authStore.loginLoading"
              @click="handleLogin"
              class="login-btn"
            >
              <template #loading>
                <div class="loading-spinner">
                  <div class="spinner-ring"></div>
                </div>
              </template>
              {{ authStore.loginLoading ? '登录中...' : '立即登录' }}
            </el-button>
            
            <div class="form-links">
              <el-button
                link
                size="small"
                @click="showRegister = true"
                class="link-btn"
              >
                没有账号？立即注册
              </el-button>
            </div>
          </div>
        </el-form>
        
        <!-- 注册表单 -->
        <el-form
          v-else
          ref="registerFormRef"
          :model="registerForm"
          :rules="registerRules"
          label-width="0"
          class="login-form register-form"
          @submit.prevent="handleRegister"
        >
          <div class="form-group">
            <el-form-item prop="phone">
              <div class="input-wrapper">
                <el-input
                  v-model="registerForm.phone"
                  placeholder="请输入手机号"
                  size="large"
                  maxlength="11"
                  class="custom-input"
                >
                  <template #prefix>
                    <el-icon class="input-icon"><Phone /></el-icon>
                  </template>
                  <template #prepend>
                    <span class="country-code">+86</span>
                  </template>
                </el-input>
              </div>
            </el-form-item>
            
            <el-form-item prop="email">
              <div class="input-wrapper">
                <el-input
                  v-model="registerForm.email"
                  placeholder="请输入邮箱地址"
                  size="large"
                  class="custom-input"
                >
                  <template #prefix>
                    <el-icon class="input-icon"><Message /></el-icon>
                  </template>
                </el-input>
              </div>
            </el-form-item>
            
            <el-form-item prop="password">
              <div class="input-wrapper">
                <el-input
                  v-model="registerForm.password"
                  type="password"
                  placeholder="请输入密码（至少6位）"
                  size="large"
                  show-password
                  class="custom-input"
                >
                  <template #prefix>
                    <el-icon class="input-icon"><Lock /></el-icon>
                  </template>
                </el-input>
              </div>
            </el-form-item>
            
            <el-form-item prop="nickname">
              <div class="input-wrapper">
                <el-input
                  v-model="registerForm.nickname"
                  placeholder="请输入昵称（可选）"
                  size="large"
                  class="custom-input"
                >
                  <template #prefix>
                    <el-icon class="input-icon"><User /></el-icon>
                  </template>
                </el-input>
              </div>
            </el-form-item>
          </div>
          
          <div class="form-actions">
            <el-button
              type="primary"
              size="large"
              :loading="authStore.loginLoading"
              @click="handleRegister"
              class="login-btn"
            >
              <template #loading>
                <div class="loading-spinner">
                  <div class="spinner-ring"></div>
                </div>
              </template>
              {{ authStore.loginLoading ? '注册中...' : '立即注册' }}
            </el-button>
            
            <div class="form-links">
              <el-button
                link
                size="small"
                @click="showRegister = false"
                class="link-btn"
              >
                已有账号？返回登录
              </el-button>
            </div>
          </div>
        </el-form>
      </transition>
      
      <!-- 登录提示 -->
      <div class="login-tips">
        <div class="tip-card">
          <el-icon class="tip-icon"><InfoFilled /></el-icon>
          <div class="tip-content">
            <p class="tip-title">温馨提示</p>
            <p class="tip-text">首次使用需要管理员添加用户权限</p>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Phone, Message, Lock, User, InfoFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { validatePasswordStrength, isWeakPassword, checkSecurityWarnings } from '@/utils/security'
import { debugLogin, validatePhoneFormat, generateDebugReport } from '@/utils/loginDebug'
import type { FormInstance, FormRules } from 'element-plus'

// Props
interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()

// Emits
interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'login-success'): void
}

const emit = defineEmits<Emits>()

// Stores
const authStore = useAuthStore()

// 响应式数据
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const showRegister = ref(false)
const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()

// 登录表单
const loginForm = reactive({
  phone: '',
  password: ''
})

// 注册表单
const registerForm = reactive({
  phone: '',
  email: '',
  password: '',
  nickname: ''
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

// 注册表单验证规则
const registerRules: FormRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ]
}

// 计算属性
const isPhoneValid = computed(() => {
  return /^1[3-9]\d{9}$/.test(loginForm.phone)
})

const codeCountdown = ref(0)
const countdownTimer = ref<number | null>(null)

const codeButtonText = computed(() => {
  if (authStore.codeLoading) return '发送中...'
  if (codeCountdown.value > 0) return `${codeCountdown.value}s后重发`
  return '获取验证码'
})

// 方法
const startCountdown = () => {
  codeCountdown.value = 60
  countdownTimer.value = setInterval(() => {
    codeCountdown.value--
    if (codeCountdown.value <= 0) {
      if (countdownTimer.value) {
        clearInterval(countdownTimer.value)
        countdownTimer.value = null
      }
    }
  }, 1000)
}

// 普通登录
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
    visible.value = false
    emit('login-success')
    
    // 重置表单
    resetForm()
  } catch (error) {
    console.error('登录错误详情:', error)
    
    // 生成调试报告
    const debugResult = await debugLogin(phoneValidation.normalizedPhone, loginForm.password)
    const debugReport = generateDebugReport(debugResult)
    // console.log('登录调试报告:\n', debugReport)
    
    // 显示用户友好的错误信息
    if (debugResult.statusCode === 401) {
      ElMessage.error('手机号或密码错误，请检查后重试')
    } else {
      ElMessage.error(error instanceof Error ? error.message : '登录失败')
    }
  }
}

// 用户注册
const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  const valid = await registerFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  // 密码强度检查
  const passwordCheck = validatePasswordStrength(registerForm.password)
  if (!passwordCheck.isValid) {
    ElMessage.error(passwordCheck.message)
    return
  }
  
  // 弱密码检查
  if (isWeakPassword(registerForm.password)) {
    ElMessage.error('密码过于简单，请使用更强的密码')
    return
  }
  
  try {
    await authStore.register({
      phone: `+86${registerForm.phone}`,
      email: registerForm.email,
      password: registerForm.password,
      nickname: registerForm.nickname
    })
    
    ElMessage.success('注册成功，请登录')
    showRegister.value = false
    // 清空注册表单
    Object.assign(registerForm, {
      phone: '',
      email: '',
      password: '',
      nickname: ''
    })
  } catch (error) {
    console.error('注册错误详情:', error)
    ElMessage.error(error instanceof Error ? error.message : '注册失败')
  }
}

const resetForm = () => {
  loginForm.phone = ''
  loginForm.password = ''
  loginFormRef.value?.resetFields()
  
  registerForm.phone = ''
  registerForm.email = ''
  registerForm.password = ''
  registerForm.nickname = ''
  registerFormRef.value?.resetFields()
  
  showRegister.value = false
}

// 监听弹窗关闭，重置表单
watch(visible, (newVal) => {
  if (!newVal) {
    resetForm()
  }
})
</script>

<style scoped>
/* ============ 登录弹窗样式 ============ */
.login-modal {
  --el-dialog-border-radius: 20px;
  --el-dialog-box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.login-modal :deep(.el-dialog) {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.95) 0%, 
    rgba(248, 250, 252, 0.95) 100%
  );
  backdrop-filter: blur(20px);
  border: 1px solid rgba(14, 165, 233, 0.1);
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.1),
    0 0 40px rgba(14, 165, 233, 0.1);
}

.dark .login-modal :deep(.el-dialog) {
  background: linear-gradient(135deg, 
    rgba(26, 26, 26, 0.95) 0%, 
    rgba(42, 42, 42, 0.95) 100%
  );
  border: 1px solid rgba(0, 212, 255, 0.2);
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.4),
    0 0 40px rgba(0, 212, 255, 0.1);
}

/* ============ 登录头部 ============ */
.login-header {
  text-align: center;
  padding: 0 0 20px 0;
  border-bottom: 1px solid rgba(14, 165, 233, 0.1);
  margin-bottom: 30px;
}

.login-logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.logo-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  animation: logoGlow 2s ease-in-out infinite alternate;
}

.logo-svg {
  width: 32px;
  height: 32px;
  color: white;
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.3));
}

.login-title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-align: center;
}

.login-subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 400;
  opacity: 0.8;
}

/* ============ 表单容器 ============ */
.login-container {
  padding: 0;
}

.form-group {
  margin-bottom: 24px;
}

.input-wrapper {
  position: relative;
  margin-bottom: 20px;
}

/* ============ 自定义输入框 ============ */
.custom-input :deep(.el-input__wrapper) {
  background: rgba(248, 250, 252, 0.8);
  border: 2px solid rgba(14, 165, 233, 0.1);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  padding: 12px 16px;
  height: 56px;
}

.custom-input :deep(.el-input__wrapper):hover {
  border-color: rgba(14, 165, 233, 0.3);
  box-shadow: 0 6px 20px rgba(14, 165, 233, 0.1);
}

.custom-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.1);
  background: rgba(255, 255, 255, 0.95);
}

.dark .custom-input :deep(.el-input__wrapper) {
  background: rgba(42, 42, 42, 0.8);
  border-color: rgba(0, 212, 255, 0.2);
}

.dark .custom-input :deep(.el-input__wrapper):hover {
  border-color: rgba(0, 212, 255, 0.4);
  box-shadow: 0 6px 20px rgba(0, 212, 255, 0.1);
}

.dark .custom-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 4px rgba(0, 212, 255, 0.1);
  background: rgba(58, 58, 58, 0.95);
}

.input-icon {
  color: var(--accent-primary);
  font-size: 18px;
}

.country-code {
  color: var(--text-secondary);
  font-weight: 500;
  padding: 0 8px;
  border-right: 1px solid rgba(14, 165, 233, 0.2);
  margin-right: 8px;
}

/* ============ 表单操作区域 ============ */
.form-actions {
  margin-top: 32px;
}

.login-btn {
  width: 100%;
  height: 56px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  border: none;
  color: white;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  margin-bottom: 20px;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(14, 165, 233, 0.4);
}

.login-btn:active {
  transform: translateY(0);
}

.login-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.login-btn:hover::before {
  left: 100%;
}

/* ============ 加载动画 ============ */
.loading-spinner {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.spinner-ring {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* ============ 表单链接 ============ */
.form-links {
  text-align: center;
}

.link-btn {
  color: var(--accent-primary);
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.link-btn:hover {
  color: var(--accent-secondary);
  transform: translateY(-1px);
}

/* ============ 提示卡片 ============ */
.login-tips {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid rgba(14, 165, 233, 0.1);
}

.tip-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, 
    rgba(14, 165, 233, 0.05) 0%, 
    rgba(139, 92, 246, 0.05) 100%
  );
  border: 1px solid rgba(14, 165, 233, 0.1);
  border-radius: 12px;
  position: relative;
  overflow: hidden;
}

.tip-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
}

.tip-icon {
  color: var(--accent-primary);
  font-size: 20px;
  margin-top: 2px;
  flex-shrink: 0;
}

.tip-content {
  flex: 1;
}

.tip-title {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.tip-text {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.4;
}

/* ============ 动画效果 ============ */
@keyframes logoGlow {
  0% {
    box-shadow: 0 0 20px rgba(14, 165, 233, 0.3);
  }
  100% {
    box-shadow: 0 0 30px rgba(14, 165, 233, 0.6);
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 表单切换动画 */
.form-slide-enter-active,
.form-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.form-slide-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.form-slide-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

/* ============ 响应式设计 ============ */
@media (max-width: 480px) {
  .login-modal :deep(.el-dialog) {
    width: 90vw !important;
    margin: 5vh auto;
  }
  
  .login-title {
    font-size: 24px;
  }
  
  .login-subtitle {
    font-size: 13px;
  }
  
  .custom-input :deep(.el-input__wrapper) {
    height: 52px;
    padding: 10px 14px;
  }
  
  .login-btn {
    height: 52px;
    font-size: 15px;
  }
}

/* ============ 暗色主题适配 ============ */
.dark .tip-card {
  background: linear-gradient(135deg, 
    rgba(0, 212, 255, 0.05) 0%, 
    rgba(139, 92, 246, 0.05) 100%
  );
  border-color: rgba(0, 212, 255, 0.2);
}

.dark .tip-card::before {
  background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
}

.dark .country-code {
  border-right-color: rgba(0, 212, 255, 0.3);
}
</style>