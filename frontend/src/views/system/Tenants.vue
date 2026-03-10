<template>
  <div class="tenant-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>租户管理</span>
          <el-button type="primary" @click="handleCreate">+ 新建租户</el-button>
        </div>
      </template>

      <el-table :data="tenants" v-loading="loading" border>
        <el-table-column prop="name" label="租户名称" />
        <el-table-column prop="domain" label="域名" />
        <el-table-column prop="quota" label="配额">
          <template #default="{ row }">
            <span>用户: {{ row.quota?.users || 0 }} / 存储: {{ row.quota?.storage || 0 }}GB</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '正常' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button :type="row.status === 'active' ? 'warning' : 'success'" link @click="handleToggleStatus(row)">
              {{ row.status === 'active' ? '停用' : '启用' }}
            </el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 租户编辑对话框 -->
    <el-dialog v-model="showDialog" :title="isCreate ? '新建租户' : '编辑租户'" width="550px">
      <el-form :model="form" :rules="formRules" label-width="80px">
        <el-form-item label="租户名称" required>
          <el-input v-model="form.name" placeholder="请输入租户名称" />
        </el-form-item>
        <el-form-item label="域名">
          <el-input v-model="form.domain" placeholder="例如: tenant1.example.com" />
        </el-form-item>
        <el-form-item label="用户配额">
          <el-input-number v-model="form.quota.users" :min="1" :max="10000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="存储配额(GB)">
          <el-input-number v-model="form.quota.storage" :min="1" :max="10000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.status">启用租户</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { systemApi } from '../../api/system'

const tenants = ref([])
const loading = ref(false)
const showDialog = ref(false)
const isCreate = ref(false)
const saving = ref(false)
const form = ref({
  name: '',
  domain: '',
  quota: { users: 100, storage: 50 },
  description: '',
  status: true
})
const currentTenantId = ref('')

// 表单验证规则
const validateDomain = (_rule: any, value: string, callback: any) => {
  if (value && !/^[a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)+$/.test(value)) {
    callback(new Error('请输入有效的域名格式'))
  } else {
    callback()
  }
}

const formRules = {
  name: [{ required: true, message: '请输入租户名称', trigger: 'blur' }],
  domain: [{ validator: validateDomain, trigger: 'blur' }]
}

const fetchTenants = async () => {
  loading.value = true
  try {
    const res = await systemApi.getTenants()
    tenants.value = res.data.items
  } catch (e) {
    // 模拟数据
    tenants.value = [
      { id: '1', name: '主租户', domain: 'main.example.com', quota: { users: 100, storage: 50 }, status: 'active', created_at: '2024-01-01 10:00:00' },
      { id: '2', name: '测试租户', domain: 'test.example.com', quota: { users: 50, storage: 20 }, status: 'active', created_at: '2024-01-15 10:00:00' }
    ]
  }
  loading.value = false
}

const handleCreate = () => {
  isCreate.value = true
  currentTenantId.value = ''
  form.value = { name: '', domain: '', quota: { users: 100, storage: 50 }, description: '', status: true }
  showDialog.value = true
}

const handleEdit = (row: any) => {
  isCreate.value = false
  currentTenantId.value = row.id
  form.value = { ...row, quota: row.quota || { users: 100, storage: 50 }, status: row.status === 'active' }
  showDialog.value = true
}

const handleSave = async () => {
  if (!form.value.name) {
    ElMessage.warning('请输入租户名称')
    return
  }
  saving.value = true
  try {
    const data = {
      ...form.value,
      status: form.value.status ? 'active' : 'inactive'
    }
    if (isCreate.value) {
      await systemApi.createTenant(data)
    } else {
      await systemApi.updateTenant(currentTenantId.value, data)
    }
    ElMessage.success('保存成功')
    showDialog.value = false
    fetchTenants()
  } finally {
    saving.value = false
  }
}

const handleToggleStatus = async (row: any) => {
  const action = row.status === 'active' ? '停用' : '启用'
  try {
    await ElMessageBox.confirm(`确定${action}租户 ${row.name} 吗？`, '确认', { type: 'warning' })
    await systemApi.updateTenant(row.id, { status: row.status === 'active' ? 'inactive' : 'active' })
    ElMessage.success(`${action}成功`)
    fetchTenants()
  } catch {}
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定删除租户 ${row.name} 吗？此操作不可恢复！`, '确认删除', { type: 'warning' })
    await systemApi.deleteTenant(row.id)
    ElMessage.success('删除成功')
    fetchTenants()
  } catch {}
}

onMounted(fetchTenants)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
