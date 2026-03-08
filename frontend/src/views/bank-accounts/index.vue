<template>
  <div class="bank-accounts">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>银行账户管理</span>
          <el-button type="primary" @click="showAddDialog = true">+ 添加账户</el-button>
        </div>
      </template>

      <!-- 账户列表 -->
      <div v-if="accounts.length === 0" class="empty-state">
        <el-empty description="暂无银行账户">
          <template #extra>
            <el-button type="primary" @click="showAddDialog = true">添加银行账户</el-button>
          </template>
        </el-empty>
      </div>

      <div v-else class="account-list">
        <div v-for="account in accounts" :key="account.id" class="account-card">
          <div class="account-header">
            <div class="bank-info">
              <div class="bank-name">{{ account.bank_name }}</div>
              <div class="account-no">{{ account.account_no }}</div>
            </div>
            <el-tag :type="account.auth_status === 'authorized' ? 'success' : 'warning'">
              {{ account.auth_status === 'authorized' ? '已授权' : '未授权' }}
            </el-tag>
          </div>

          <div class="account-body">
            <div class="balance-info">
              <div class="label">账户余额</div>
              <div class="value">¥{{ (account.balance || 0).toFixed(2) }}</div>
            </div>

            <div class="sync-info">
              <div class="label">上次同步</div>
              <div class="value">{{ account.last_sync_at ? formatTime(account.last_sync_at) : '未同步' }}</div>
            </div>
          </div>

          <div class="account-actions">
            <el-button 
              type="primary" 
              :disabled="account.auth_status !== 'authorized'"
              @click="syncAccount(account)"
              :loading="syncingId === account.id"
            >
              同步流水
            </el-button>
            
            <el-button @click="showConfigDialog(account)">设置</el-button>
            
            <el-button type="danger" link @click="deleteAccount(account)">删除</el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 添加账户对话框 -->
    <el-dialog v-model="showAddDialog" title="添加银行账户" width="500px">
      <el-form :model="addForm" label-width="100px">
        <el-form-item label="选择银行" required>
          <el-select v-model="addForm.bank_code" placeholder="请选择银行" style="width: 100%">
            <el-option
              v-for="bank in supportedBanks"
              :key="bank.code"
              :label="bank.name"
              :value="bank.code"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="银行账号" required>
          <el-input v-model="addForm.account_no" placeholder="请输入银行账号" />
        </el-form-item>

        <el-form-item label="账户名称">
          <el-input v-model="addForm.account_name" placeholder="请输入账户名称" />
        </el-form-item>

        <el-form-item label="账户类型">
          <el-select v-model="addForm.account_type" style="width: 100%">
            <el-option label="基本户" value="basic" />
            <el-option label="一般户" value="general" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addAccount" :loading="adding">下一步</el-button>
      </template>
    </el-dialog>

    <!-- 授权对话框 -->
    <el-dialog v-model="showAuthDialog" title="银行授权" width="500px">
      <div class="auth-content">
        <p>请点击下方按钮跳转到银行授权页面完成授权</p>
        <el-button type="primary" size="large" @click="goToAuth">前往授权页面</el-button>
      </div>
    </el-dialog>

    <!-- 配置对话框 -->
    <el-dialog v-model="showConfigDialogVisible" title="同步配置" width="400px">
      <el-form :model="configForm" label-width="120px">
        <el-form-item label="自动同步">
          <el-switch v-model="configForm.auto_sync" />
        </el-form-item>

        <el-form-item label="同步范围(天)">
          <el-input-number v-model="configForm.sync_range_days" :min="1" :max="90" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showConfigDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveConfig" :loading="savingConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { bankAccountApi } from '../../api/bank-account'

const accounts = ref<any[]>([])
const supportedBanks = ref<any[]>([])
const loading = ref(false)
const syncingId = ref('')
const adding = ref(false)
const savingConfig = ref(false)

const showAddDialog = ref(false)
const showAuthDialog = ref(false)
const showConfigDialogVisible = ref(false)
const currentAccount = ref<any>(null)

const addForm = ref({
  bank_code: '',
  account_no: '',
  account_name: '',
  account_type: 'basic'
})

const configForm = ref({
  auto_sync: true,
  sync_range_days: 30
})

const fetchAccounts = async () => {
  loading.value = true
  try {
    const res = await bankAccountApi.getList()
    accounts.value = res.data.items
  } finally {
    loading.value = false
  }
}

const fetchSupportedBanks = async () => {
  const res = await bankAccountApi.getSupportedBanks()
  supportedBanks.value = res.data.items
}

const addAccount = async () => {
  if (!addForm.value.bank_code || !addForm.value.account_no) {
    ElMessage.warning('请填写完整信息')
    return
  }

  adding.value = true
  try {
    const res = await bankAccountApi.create(addForm.value)
    ElMessage.success('账户添加成功，请完成授权')
    showAddDialog.value = false
    
    // 显示授权对话框
    currentAccount.value = res.data
    showAuthDialog.value = true
    
    // 重置表单
    addForm.value = {
      bank_code: '',
      account_no: '',
      account_name: '',
      account_type: 'basic'
    }
  } finally {
    adding.value = false
  }
}

const goToAuth = () => {
  if (currentAccount.value?.auth_url) {
    window.open(currentAccount.value.auth_url, '_blank')
  }
  showAuthDialog.value = false
  fetchAccounts()
}

const syncAccount = async (account: any) => {
  syncingId.value = account.id
  try {
    const res = await bankAccountApi.sync(account.id)
    ElMessage.success(`同步完成：新增 ${res.data.new_count} 条流水`)
    fetchAccounts()
  } catch (error) {
    console.error(error)
  } finally {
    syncingId.value = ''
  }
}

const showConfigDialog = (account: any) => {
  currentAccount.value = account
  configForm.value = {
    auto_sync: account.auto_sync,
    sync_range_days: account.sync_range_days
  }
  showConfigDialogVisible.value = true
}

const saveConfig = async () => {
  if (!currentAccount.value) return
  
  savingConfig.value = true
  try {
    await bankAccountApi.updateConfig(currentAccount.value.id, configForm.value)
    ElMessage.success('配置保存成功')
    showConfigDialogVisible.value = false
    fetchAccounts()
  } finally {
    savingConfig.value = false
  }
}

const deleteAccount = async (account: any) => {
  try {
    await ElMessageBox.confirm(
      `确定删除银行账户 "${account.bank_name} ${account.account_no}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await bankAccountApi.delete(account.id)
    ElMessage.success('删除成功')
    fetchAccounts()
  } catch {}
}

const formatTime = (time: string) => {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  fetchAccounts()
  fetchSupportedBanks()
})
</script>

<style scoped>
.bank-accounts {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-state {
  padding: 40px 0;
}

.account-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.account-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
  background: #fff;
}

.account-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.bank-name {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.account-no {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.account-body {
  display: flex;
  gap: 40px;
  margin-bottom: 16px;
}

.balance-info, .sync-info {
  .label {
    font-size: 12px;
    color: #909399;
    margin-bottom: 4px;
  }
  .value {
    font-size: 20px;
    font-weight: 600;
    color: #303133;
  }
}

.account-actions {
  display: flex;
  gap: 12px;
}

.auth-content {
  text-align: center;
  padding: 20px;
}
</style>
