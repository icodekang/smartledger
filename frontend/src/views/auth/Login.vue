<template>
  <div class="login-container">
    <!-- 动态背景 -->
    <div class="animated-bg">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
        <div class="shape shape-4"></div>
      </div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-wrapper">
      <el-card class="login-box" shadow="never">
        <!-- LOGO 区域 -->
        <div class="login-header">
          <div class="logo-container">
            <div class="logo-icon">
              <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="4" y="8" width="40" height="32" rx="4" fill="url(#logoGradient)" />
                <path d="M12 20H36M12 28H28" stroke="white" stroke-width="2" stroke-linecap="round" />
                <circle cx="36" cy="28" r="4" fill="white" />
                <defs>
                  <linearGradient id="logoGradient" x1="4" y1="8" x2="44" y2="40" gradientUnits="userSpaceOnUse">
                    <stop stop-color="#3b5cf5" />
                    <stop offset="1" stop-color="#6366f1" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <h1 class="logo-text">SmartLedger</h1>
            <span class="logo-badge">AI</span>
          </div>
          <p class="tagline">智能代理记账系统</p>
        </div>

        <!-- 标签页切换 -->
        <el-tabs v-model="activeTab" class="auth-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form
              ref="loginForm"
              :model="loginData"
              :rules="loginRules"
              @submit.prevent="handleLogin"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="loginData.username"
                  placeholder="请输入用户名"
                  prefix-icon="User"
                  size="large"
                  class="custom-input"
                />
              </el-form-item>
              
              <el-form-item prop="password">
                <el-input
                  v-model="loginData.password"
                  type="password"
                  placeholder="请输入密码"
                  prefix-icon="Lock"
                  size="large"
                  show-password
                  class="custom-input"
                  @keyup.enter="handleLogin"
                />
              </el-form-item>
              
              <div class="form-options">
                <el-checkbox v-model="rememberMe">记住我</el-checkbox>
                <a href="#" class="forgot-link">忘记密码？</a>
              </div>
              
              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  :loading="loading"
                  class="login-btn"
                  @click="handleLogin"
                >
                  <span v-if="!loading">登录</span>
                  <span v-else>登录中...</span>
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          
          <el-tab-pane label="注册" name="register">
            <el-form
              ref="registerForm"
              :model="registerData"
              :rules="registerRules"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="registerData.username"
                  placeholder="请输入用户名"
                  prefix-icon="User"
                  size="large"
                  class="custom-input"
                />
              </el-form-item>
              
              <el-form-item prop="name">
                <el-input
                  v-model="registerData.name"
                  placeholder="请输入姓名"
                  prefix-icon="Avatar"
                  size="large"
                  class="custom-input"
                />
              </el-form-item>
              
              <el-form-item prop="password">
                <el-input
                  v-model="registerData.password"
                  type="password"
                  placeholder="请输入密码（至少8位）"
                  prefix-icon="Lock"
                  size="large"
                  show-password
                  class="custom-input"
                />
              </el-form-item>
              
              <el-form-item prop="confirmPassword">
                <el-input
                  v-model="registerData.confirmPassword"
                  type="password"
                  placeholder="请再次输入密码"
                  prefix-icon="Lock"
                  size="large"
                  show-password
                  class="custom-input"
                />
              </el-form-item>
              
              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  :loading="loading"
                  class="login-btn"
                  @click="handleRegister"
                >
                  <span v-if="!loading">注册</span>
                  <span v-else>注册中...</span>
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <!-- 底部版权 -->
      <div class="login-footer">
        <span>© 2024 SmartLedger AI. All rights reserved.</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '../../api/auth'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const activeTab = ref('login')
const rememberMe = ref(false)

// 登录表单
const loginData = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 注册表单
const registerData = reactive({
  username: '',
  name: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule: any, value: string, callback: Function) => {
  if (value !== registerData.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const registerRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少8个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const loginForm = ref()
const registerForm = ref()

const handleLogin = async () => {
  const valid = await loginForm.value?.validate()
  if (!valid) return
  
  loading.value = true
  try {
    const res = await authApi.login(loginData)
    const { access_token, user } = res.data
    await authStore.login(access_token, user)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    // 错误已在拦截器处理
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  const valid = await registerForm.value?.validate()
  if (!valid) return
  
  loading.value = true
  try {
    await authApi.register({
      username: registerData.username,
      password: registerData.password,
      name: registerData.name
    })
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
    registerForm.value?.resetFields()
  } catch (error) {
    // 错误已在拦截器处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 容器与背景 */
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
}

/* 动态背景 */
.animated-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
  z-index: 0;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, #3b5cf5, #6366f1);
  top: -200px;
  right: -100px;
  animation-delay: 0s;
}

.orb-2 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, #8b5cf6, #a855f7);
  bottom: -150px;
  left: -100px;
  animation-delay: -7s;
}

.orb-3 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #06b6d4, #3b82f6);
  top: 50%;
  left: 30%;
  animation-delay: -14s;
  opacity: 0.3;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(30px, -30px) scale(1.05);
  }
  50% {
    transform: translate(-20px, 20px) scale(0.95);
  }
  75% {
    transform: translate(-30px, -20px) scale(1.02);
  }
}

/* 浮动形状 */
.floating-shapes {
  position: absolute;
  inset: 0;
}

.shape {
  position: absolute;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(2px);
  border-radius: 8px;
  animation: drift 15s ease-in-out infinite;
}

.shape-1 {
  width: 80px;
  height: 80px;
  top: 15%;
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 60px;
  height: 60px;
  top: 60%;
  left: 5%;
  border-radius: 50%;
  animation-delay: -3s;
}

.shape-3 {
  width: 100px;
  height: 100px;
  top: 20%;
  right: 10%;
  border-radius: 50%;
  animation-delay: -6s;
}

.shape-4 {
  width: 70px;
  height: 70px;
  bottom: 20%;
  right: 15%;
  animation-delay: -9s;
}

@keyframes drift {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
    opacity: 0.1;
  }
  50% {
    transform: translateY(-30px) rotate(180deg);
    opacity: 0.2;
  }
}

/* 登录卡片容器 */
.login-wrapper {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 玻璃拟态卡片 */
.login-box {
  width: 420px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 24px;
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.05) inset;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.login-box:hover {
  transform: translateY(-5px);
  box-shadow: 
    0 30px 60px -12px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
}

.login-box :deep(.el-card__body) {
  padding: 40px 48px;
}

/* 头部 LOGO */
.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 8px;
}

.logo-icon {
  width: 52px;
  height: 52px;
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    filter: drop-shadow(0 0 8px rgba(59, 92, 245, 0.4));
  }
  50% {
    filter: drop-shadow(0 0 20px rgba(99, 102, 241, 0.6));
  }
}

.logo-icon svg {
  width: 100%;
  height: 100%;
}

.logo-text {
  font-size: 28px;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 1px;
}

.logo-badge {
  background: linear-gradient(135deg, #3b5cf5, #6366f1);
  color: white;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 6px;
  letter-spacing: 0.5px;
}

.tagline {
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
  margin: 8px 0 0;
  letter-spacing: 2px;
  text-transform: uppercase;
}

/* 标签页样式 */
.auth-tabs :deep(.el-tabs__header) {
  margin-bottom: 24px;
}

.auth-tabs :deep(.el-tabs__nav-wrap::after) {
  background-color: rgba(255, 255, 255, 0.1);
}

.auth-tabs :deep(.el-tabs__item) {
  color: rgba(255, 255, 255, 0.5);
  font-size: 16px;
  font-weight: 500;
  padding: 0 24px;
  transition: all 0.3s ease;
}

.auth-tabs :deep(.el-tabs__item:hover) {
  color: rgba(255, 255, 255, 0.8);
}

.auth-tabs :deep(.el-tabs__item.is-active) {
  color: #fff;
  font-weight: 600;
}

.auth-tabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(90deg, #3b5cf5, #6366f1);
  height: 3px;
  border-radius: 3px;
}

/* 输入框样式 */
.custom-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: none;
  padding: 4px 16px;
  transition: all 0.3s ease;
}

.custom-input :deep(.el-input__wrapper:hover) {
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.08);
}

.custom-input :deep(.el-input__wrapper.is-focus) {
  border-color: #3b5cf5;
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 0 3px rgba(59, 92, 245, 0.2);
}

.custom-input :deep(.el-input__inner) {
  color: #fff;
  height: 44px;
}

.custom-input :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.4);
}

.custom-input :deep(.el-input__prefix) {
  color: rgba(255, 255, 255, 0.4);
}

.custom-input :deep(.el-input__prefix .el-icon) {
  font-size: 18px;
}

.custom-input :deep(.el-input__suffix .el-input__password) {
  color: rgba(255, 255, 255, 0.4);
}

/* 表单选项 */
.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.form-options :deep(.el-checkbox__label) {
  color: rgba(255, 255, 255, 0.6);
}

.form-options :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #3b5cf5;
  border-color: #3b5cf5;
}

.forgot-link {
  color: #3b5cf5;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.3s ease;
}

.forgot-link:hover {
  color: #818cf8;
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #3b5cf5 0%, #6366f1 100%);
  border: none;
  color: white;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.login-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, transparent 0%, rgba(255, 255, 255, 0.2) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(59, 92, 245, 0.4);
}

.login-btn:hover::before {
  opacity: 1;
}

.login-btn:active {
  transform: translateY(0);
}

.login-btn:deep(.el-icon) {
  margin-right: 8px;
}

/* 底部版权 */
.login-footer {
  margin-top: 24px;
  text-align: center;
  color: rgba(255, 255, 255, 0.3);
  font-size: 12px;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-box {
    width: 90vw;
    max-width: 380px;
  }

  .login-box :deep(.el-card__body) {
    padding: 32px 24px;
  }

  .logo-text {
    font-size: 24px;
  }

  .logo-icon {
    width: 44px;
    height: 44px;
  }

  .auth-tabs :deep(.el-tabs__item) {
    padding: 0 16px;
  }
}

/* 深色主题适配 */
html.dark .login-box {
  background: rgba(30, 41, 59, 0.8);
  border-color: rgba(255, 255, 255, 0.08);
}

html.dark .custom-input :deep(.el-input__wrapper) {
  background: rgba(15, 23, 42, 0.5);
}
</style>
