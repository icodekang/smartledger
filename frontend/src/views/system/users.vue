<template>
  <div class="user-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" @click="handleCreate">+ 新建用户</el-button>
        </div>
      </template>

      <el-table :data="users" v-loading="loading" border>
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="name" label="姓名" />
        <el-table-column prop="phone" label="手机" />
        <el-table-column prop="role" label="角色">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)">{{ getRoleText(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 用户编辑对话框 -->
    <el-dialog v-model="showDialog" :title="isCreate ? '新建用户' : '编辑用户'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" :disabled="!isCreate" />
        </el-form-item>
        <el-form-item label="密码" :required="isCreate">
          <el-input v-model="form.password" type="password" show-password :placeholder="isCreate ? '' : '不修改请留空'" />
        </el-form-item>
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="会计" value="accountant" />
            <el-option label="查看者" value="viewer" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.is_active">启用账号</el-checkbox>
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

const users = ref([])
const loading = ref(false)
const showDialog = ref(false)
const isCreate = ref(false)
const saving = ref(false)
const form = ref({ username: '', password: '', name: '', phone: '', email: '', role: 'viewer', is_active: true })
const currentUserId = ref('')

const fetchUsers = async () => {
  loading.value = true
  const res = await systemApi.getUsers()
  users.value = res.data.items
  loading.value = false
}

const getRoleType = (role: string) => ({ admin: 'danger', accountant: 'warning', viewer: 'info' }[role] || 'info')
const getRoleText = (role: string) => ({ admin: '管理员', accountant: '会计', viewer: '查看者' }[role] || role)

const handleCreate = () => {
  isCreate.value = true
  currentUserId.value = ''
  form.value = { username: '', password: '', name: '', phone: '', email: '', role: 'viewer', is_active: true }
  showDialog.value = true
}

const handleEdit = (row: any) => {
  isCreate.value = false
  currentUserId.value = row.id
  form.value = { ...row, password: '' }
  showDialog.value = true
}

const handleSave = async () => {
  saving.value = true
  try {
    if (isCreate.value) {
      await systemApi.createUser(form.value)
    } else {
      const data = { ...form.value }
      if (!data.password) delete data.password
      await systemApi.updateUser(currentUserId.value, data)
    }
    ElMessage.success('保存成功')
    showDialog.value = false
    fetchUsers()
  } finally {
    saving.value = false
  }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定删除用户 ${row.name} 吗？`, '确认删除', { type: 'warning' })
    await systemApi.deleteUser(row.id)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch {}
}

onMounted(fetchUsers)
</script>
