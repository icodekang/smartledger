<template>
  <div class="system-settings">
    <div class="page-header">
      <h2>系统参数配置</h2>
      <el-button type="primary" @click="saveSettings" :loading="saving">
        <el-icon><Check /></el-icon>保存配置
      </el-button>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 基本配置 -->
      <el-tab-pane label="基本配置" name="basic">
        <el-form :model="settings.basic" label-width="150px" class="setting-form">
          <el-form-item label="系统名称">
            <el-input v-model="settings.basic.systemName" />
          </el-form-item>

          <el-form-item label="系统Logo">
            <el-upload
              class="logo-uploader"
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleLogoChange"
            >
              <img v-if="settings.basic.logo" :src="settings.basic.logo" class="logo-preview" />
              <el-icon v-else class="logo-uploader-icon"><Plus /></el-icon>
            </el-upload>
          </el-form-item>

          <el-form-item label="版权信息">
            <el-input v-model="settings.basic.copyright" />
          </el-form-item>

          <el-form-item label="ICP备案号">
            <el-input v-model="settings.basic.icp" placeholder="京ICP备XXXXXXXX号" />
          </el-form-item>

          <el-form-item label="系统维护模式">
            <el-switch
              v-model="settings.basic.maintenanceMode"
              active-text="开启"
              inactive-text="关闭"
            />
          </el-form-item>

          <el-form-item v-if="settings.basic.maintenanceMode" label="维护提示信息">
            <el-input
              v-model="settings.basic.maintenanceMessage"
              type="textarea"
              rows="3"
              placeholder="系统维护中，请稍后再试..."
            />
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 邮件配置 -->
      <el-tab-pane label="邮件配置" name="email">
        <el-form :model="settings.email" label-width="150px" class="setting-form">
          <el-form-item label="SMTP服务器">
            <el-input v-model="settings.email.smtpHost" placeholder="smtp.example.com" />
          </el-form-item>

          <el-form-item label="SMTP端口">
            <el-input-number v-model="settings.email.smtpPort" :min="1" :max="65535" />
          </el-form-item>

          <el-form-item label="发件人邮箱">
            <el-input v-model="settings.email.fromEmail" placeholder="noreply@example.com" />
          </el-form-item>

          <el-form-item label="发件人名称">
            <el-input v-model="settings.email.fromName" placeholder="SmartLedger" />
          </el-form-item>

          <el-form-item label="SMTP用户名">
            <el-input v-model="settings.email.smtpUser" />
          </el-form-item>

          <el-form-item label="SMTP密码">
            <el-input v-model="settings.email.smtpPassword" type="password" show-password />
          </el-form-item>

          <el-form-item label="启用SSL">
            <el-switch v-model="settings.email.useSsl" />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="testEmail" :loading="testingEmail">测试邮件发送</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 安全设置 -->
      <el-tab-pane label="安全设置" name="security">
        <el-form :model="settings.security" label-width="150px" class="setting-form">
          <el-form-item label="登录失败锁定">
            <el-switch v-model="settings.security.enableLock" />
          </el-form-item>

          <el-form-item label="最大失败次数">
            <el-input-number v-model="settings.security.maxFailedAttempts" :min="3" :max="10" />
          </el-form-item>

          <el-form-item label="锁定时间(分钟)">
            <el-input-number v-model="settings.security.lockDuration" :min="5" :max="120" />
          </el-form-item>

          <el-form-item label="密码最小长度">
            <el-input-number v-model="settings.security.passwordMinLength" :min="6" :max="20" />
          </el-form-item>

          <el-form-item label="密码复杂度">
            <el-checkbox-group v-model="settings.security.passwordComplexity">
              <el-checkbox label="uppercase">大写字母</el-checkbox>
              <el-checkbox label="lowercase">小写字母</el-checkbox>
              <el-checkbox label="number">数字</el-checkbox>
              <el-checkbox label="special">特殊字符</el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <el-form-item label="会话超时(分钟)">
            <el-input-number v-model="settings.security.sessionTimeout" :min="10" :max="1440" />
          </el-form-item>

          <el-form-item label="允许IP白名单">
            <el-input
              v-model="settings.security.ipWhitelist"
              type="textarea"
              rows="3"
              placeholder="每行一个IP，如：192.168.1.100"
            />
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 备份设置 -->
      <el-tab-pane label="备份设置" name="backup">
        <el-form :model="settings.backup" label-width="150px" class="setting-form">
          <el-form-item label="自动备份">
            <el-switch v-model="settings.backup.autoBackup" />
          </el-form-item>

          <el-form-item label="备份周期">
            <el-radio-group v-model="settings.backup.backupFrequency">
              <el-radio label="daily">每天</el-radio>
              <el-radio label="weekly">每周</el-radio>
              <el-radio label="monthly">每月</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="备份时间">
            <el-time-picker v-model="settings.backup.backupTime" format="HH:mm" />
          </el-form-item>

          <el-form-item label="保留备份数">
            <el-input-number v-model="settings.backup.keepCount" :min="1" :max="30" />
            <span class="tip">最多保留最近{{ settings.backup.keepCount }}个备份</span>
          </el-form-item>

          <el-form-item label="备份存储位置">
            <el-radio-group v-model="settings.backup.storageType">
              <el-radio label="local">本地存储</el-radio>
              <el-radio label="s3">对象存储(S3)</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item v-if="settings.backup.storageType === 's3'" label="S3配置">
            <div class="s3-config">
              <el-form-item label="Endpoint">
                <el-input v-model="settings.backup.s3Endpoint" placeholder="https://s3.amazonaws.com" />
              </el-form-item>
              <el-form-item label="Bucket">
                <el-input v-model="settings.backup.s3Bucket" />
              </el-form-item>
              <el-form-item label="Access Key">
                <el-input v-model="settings.backup.s3AccessKey" />
              </el-form-item>
              <el-form-item label="Secret Key">
                <el-input v-model="settings.backup.s3SecretKey" type="password" />
              </el-form-item>
            </div>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="manualBackup" :loading="backingUp">立即备份</el-button>
            <el-button @click="showBackupHistory">备份历史</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 关于系统 -->
      <el-tab-pane label="关于系统" name="about">
        <div class="about-section">
          <div class="logo-large">SmartLedger</div>
          <div class="version-info">
            <p><strong>版本号:</strong> {{ systemInfo.version }}</p>
            <p><strong>构建时间:</strong> {{ systemInfo.buildTime }}</p>
            <p><strong>Git Commit:</strong> {{ systemInfo.gitCommit }}</p>
            <p><strong>运行环境:</strong> {{ systemInfo.runtime }}</p>
          </div>

          <el-divider />

          <div class="license-info">
            <h4>授权信息</h4>
            <p><strong>授权类型:</strong> {{ systemInfo.licenseType }}</p>
            <p><strong>授权到期:</strong> {{ systemInfo.licenseExpire }}</p>
            <p><strong>授权用户数:</strong> {{ systemInfo.licenseUsers }}人</p>
          </div>

          <el-divider />

          <div class="contact-info">
            <h4>技术支持</h4>
            <p>官方网址: {{ systemInfo.website }}</p>
            <p>技术支持: {{ systemInfo.supportEmail }}</p>
            <p>客服热线: {{ systemInfo.hotline }}</p>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Plus } from '@element-plus/icons-vue'
import api from '@/api'

const activeTab = ref('basic')
const saving = ref(false)
const testingEmail = ref(false)
const backingUp = ref(false)

const settings = reactive({
  basic: {
    systemName: 'SmartLedger 智能账本',
    logo: '',
    copyright: '© 2024 SmartLedger. All rights reserved.',
    icp: '',
    maintenanceMode: false,
    maintenanceMessage: '系统维护中，请稍后再试...'
  },
  email: {
    smtpHost: 'smtp.example.com',
    smtpPort: 587,
    fromEmail: 'noreply@smartledger.com',
    fromName: 'SmartLedger',
    smtpUser: '',
    smtpPassword: '',
    useSsl: true
  },
  security: {
    enableLock: true,
    maxFailedAttempts: 5,
    lockDuration: 30,
    passwordMinLength: 8,
    passwordComplexity: ['uppercase', 'lowercase', 'number'],
    sessionTimeout: 120,
    ipWhitelist: ''
  },
  backup: {
    autoBackup: true,
    backupFrequency: 'daily',
    backupTime: new Date(2024, 0, 1, 2, 0),
    keepCount: 7,
    storageType: 'local',
    s3Endpoint: '',
    s3Bucket: '',
    s3AccessKey: '',
    s3SecretKey: ''
  }
})

const systemInfo = reactive({
  version: 'v2.1.0',
  buildTime: '2024-03-08 10:30:00',
  gitCommit: '1749298',
  runtime: 'Node.js 18.x + PostgreSQL 15',
  licenseType: '企业版',
  licenseExpire: '2025-03-08',
  licenseUsers: 50,
  website: 'https://smartledger.example.com',
  supportEmail: 'support@smartledger.example.com',
  hotline: '400-888-8888'
})

// 加载设置
const loadSettings = async () => {
  try {
    const res = await api.get('/sys/config')
    if (res.data) {
      // 映射配置到表单
      if (res.data.system_name) settings.basic.systemName = res.data.system_name
      if (res.data.company_name) settings.basic.companyName = res.data.company_name
      if (res.data.logo_url) settings.basic.logo = res.data.logo_url
      if (res.data.copyright) settings.basic.copyright = res.data.copyright
      if (res.data.icp) settings.basic.icp = res.data.icp
      if (res.data.theme_color) settings.basic.themeColor = res.data.theme_color
      if (res.data.session_timeout) settings.security.sessionTimeout = res.data.session_timeout
      if (res.data.enable_register !== undefined) settings.basic.enableRegister = res.data.enable_register
    }
  } catch (error) {
    console.error('加载设置失败', error)
  }
}

// 保存设置
const saveSettings = async () => {
  saving.value = true
  try {
    const configData = {
      system_name: settings.basic.systemName,
      company_name: settings.basic.companyName,
      logo_url: settings.basic.logo,
      copyright: settings.basic.copyright,
      icp: settings.basic.icp,
      theme_color: settings.basic.themeColor,
      session_timeout: settings.security.sessionTimeout,
      enable_register: settings.basic.enableRegister
    }
    await api.put('/sys/config', configData)
    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 测试邮件
const testEmail = async () => {
  testingEmail.value = true
  try {
    await api.post('/sys/config/test-email', {
      smtp_host: settings.email.smtpHost,
      smtp_port: settings.email.smtpPort,
      from_email: settings.email.fromEmail,
      smtp_user: settings.email.smtpUser,
      smtp_password: settings.email.smtpPassword,
      use_ssl: settings.email.useSsl
    })
    ElMessage.success('测试邮件已发送，请查收')
  } catch (error) {
    ElMessage.error('邮件发送失败')
  } finally {
    testingEmail.value = false
  }
}

// 手动备份
const manualBackup = async () => {
  backingUp.value = true
  try {
    await api.post('/sys/backup/manual')
    ElMessage.success('备份任务已启动，请在备份历史中查看进度')
  } catch (error) {
    ElMessage.error('备份启动失败')
  } finally {
    backingUp.value = false
  }
}

// 查看备份历史
const showBackupHistory = () => {
  ElMessageBox.alert(
    '备份历史功能正在开发中，敬请期待！',
    '提示',
    { type: 'info' }
  )
}

// 处理Logo上传
const handleLogoChange = (file: any) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    settings.basic.logo = e.target?.result as string
  }
  reader.readAsDataURL(file.raw)
}

onMounted(loadSettings)
</script>

<style scoped>
.system-settings {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.setting-form {
  max-width: 600px;
  padding: 20px;
}

.logo-uploader {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: 120px;
  height: 120px;
}

.logo-uploader:hover {
  border-color: #409EFF;
}

.logo-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 120px;
  height: 120px;
  line-height: 120px;
  text-align: center;
}

.logo-preview {
  width: 120px;
  height: 120px;
  object-fit: contain;
}

.tip {
  margin-left: 10px;
  color: #909399;
  font-size: 13px;
}

.s3-config {
  width: 100%;
}

.about-section {
  padding: 40px;
  text-align: center;
}

.logo-large {
  font-size: 36px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 20px;
}

.version-info,
.license-info,
.contact-info {
  margin: 20px 0;
}

.version-info p,
.license-info p,
.contact-info p {
  margin: 8px 0;
  color: #606266;
}

.version-info h4,
.license-info h4,
.contact-info h4 {
  margin: 20px 0 10px;
  color: #303133;
}
</style>
