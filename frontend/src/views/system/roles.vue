<template>
  <div class="system-roles">
    <div class="page-header">
      <h2>角色权限管理</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>新增角色
      </el-button>
    </div>

    <!-- 角色列表 -->
    <el-row :gutter="20">
      <el-col :span="8" v-for="role in roles" :key="role.id">
        <el-card class="role-card" :class="{ 'is-default': role.isDefault }">
          <template #header>
            <div class="role-header">
              <div class="role-info"
                <el-tag :type="role.type" size="small">{{ role.tag }}</el-tag>
                <h3>{{ role.name }}</h3>
              </div>
              <div class="role-actions" v-if="!role.isDefault">
                <el-button type="primary" link @click="editRole(role)">编辑</el-button>
                <el-button type="danger" link @click="deleteRole(role)">删除</el-button>
              </div>
            </div>
          </template>
          
          <p class="role-desc">{{ role.description }}</p>
          
          <div class="role-stats"
            <span><el-icon><User /></el-icon> {{ role.userCount }} 人</span>
            <span><el-icon><Key /></el-icon> {{ role.permissionCount }} 项权限</span>
          </div>

          <div class="role-permissions"
            <div class="permission-tag" v-for="perm in role.permissions.slice(0, 5)" :key="perm">
              {{ perm }}
            </div>
            <el-tag v-if="role.permissions.length > 5" type="info" size="small">
              +{{ role.permissions.length - 5 }}
            </el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 创建/编辑角色弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑角色' : '新增角色'"
      width="600px"
    >
      <el-form :model="roleForm" label-width="100px">
        <el-form-item label="角色名称" required>
          <el-input v-model="roleForm.name" placeholder="请输入角色名称" />
        </el-form-item>

        <el-form-item label="角色标识">
          <el-input v-model="roleForm.code" placeholder="如: accountant" />
        </el-form-item>

        <el-form-item label="角色描述">
          <el-input v-model="roleForm.description" type="textarea" rows="3" />
        </el-form-item>

        <el-form-item label="权限配置">
          <div class="permission-tree">
            <el-tree
              ref="permissionTree"
              :data="permissionTreeData"
              show-checkbox
              node-key="id"
              :default-checked-keys="roleForm.permissions"
              :props="{ label: 'name', children: 'children' }"
            />
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRole">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, User, Key } from '@element-plus/icons-vue'

const dialogVisible = ref(false)
const isEdit = ref(false)
const permissionTree = ref()

const roles = ref([
  {
    id: '1',
    name: '系统管理员',
    code: 'admin',
    tag: '管理',
    type: 'danger',
    description: '系统最高权限，可管理所有功能和用户',
    userCount: 2,
    permissionCount: 156,
    permissions: ['*'],
    isDefault: true
  },
  {
    id: '2',
    name: '会计',
    code: 'accountant',
    tag: '财务',
    type: 'primary',
    description: '负责日常账务处理、凭证录入和审核',
    userCount: 5,
    permissionCount: 45,
    permissions: ['bills:read', 'bills:create', 'vouchers:read', 'vouchers:create', 'audit:read'],
    isDefault: true
  },
  {
    id: '3',
    name: '审计员',
    code: 'auditor',
    tag: '审计',
    type: 'warning',
    description: '负责凭证审核和财务数据审查',
    userCount: 3,
    permissionCount: 25,
    permissions: ['audit:read', 'audit:approve', 'vouchers:read'],
    isDefault: true
  },
  {
    id: '4',
    name: '查看者',
    code: 'viewer',
    tag: '只读',
    type: 'info',
    description: '只读权限，可查看报表和数据',
    userCount: 8,
    permissionCount: 12,
    permissions: ['bills:read', 'vouchers:read', 'reports:read'],
    isDefault: true
  },
  {
    id: '5',
    name: '客户',
    code: 'customer',
    tag: '外部',
    type: 'success',
    description: '外部客户权限，可查看自己的票据和报表',
    userCount: 15,
    permissionCount: 8,
    permissions: ['bills:read', 'vouchers:read'],
    isDefault: true
  }
])

const roleForm = reactive({
  id: '',
  name: '',
  code: '',
  description: '',
  permissions: [] as string[]
})

const permissionTreeData = ref([
  {
    id: 'dashboard',
    name: '仪表盘',
    children: [
      { id: 'dashboard:read', name: '查看仪表盘' }
    ]
  },
  {
    id: 'bills',
    name: '票据管理',
    children: [
      { id: 'bills:read', name: '查看票据' },
      { id: 'bills:create', name: '创建票据' },
      { id: 'bills:update', name: '编辑票据' },
      { id: 'bills:delete', name: '删除票据' }
    ]
  },
  {
    id: 'vouchers',
    name: '凭证管理',
    children: [
      { id: 'vouchers:read', name: '查看凭证' },
      { id: 'vouchers:create', name: '创建凭证' },
      { id: 'vouchers:audit', name: '审核凭证' },
      { id: 'vouchers:delete', name: '删除凭证' }
    ]
  },
  {
    id: 'audit',
    name: '审核工作台',
    children: [
      { id: 'audit:read', name: '查看审核任务' },
      { id: 'audit:approve', name: '审核通过' },
      { id: 'audit:reject', name: '审核拒绝' }
    ]
  },
  {
    id: 'customers',
    name: '客户管理',
    children: [
      { id: 'customers:read', name: '查看客户' },
      { id: 'customers:create', name: '创建客户' },
      { id: 'customers:update', name: '编辑客户' },
      { id: 'customers:delete', name: '删除客户' }
    ]
  },
  {
    id: 'contracts',
    name: '合同管理',
    children: [
      { id: 'contracts:read', name: '查看合同' },
      { id: 'contracts:create', name: '创建合同' },
      { id: 'contracts:update', name: '编辑合同' }
    ]
  },
  {
    id: 'reports',
    name: '财务报表',
    children: [
      { id: 'reports:read', name: '查看报表' },
      { id: 'reports:export', name: '导出报表' }
    ]
  },
  {
    id: 'system',
    name: '系统管理',
    children: [
      { id: 'system:users', name: '用户管理' },
      { id: 'system:roles', name: '角色管理' },
      { id: 'system:logs', name: '操作日志' },
      { id: 'system:settings', name: '系统配置' }
    ]
  }
])

const showCreateDialog = () => {
  isEdit.value = false
  roleForm.id = ''
  roleForm.name = ''
  roleForm.code = ''
  roleForm.description = ''
  roleForm.permissions = []
  dialogVisible.value = true
}

const editRole = (role: any) => {
  isEdit.value = true
  roleForm.id = role.id
  roleForm.name = role.name
  roleForm.code = role.code
  roleForm.description = role.description
  roleForm.permissions = [...role.permissions]
  dialogVisible.value = true
}

const deleteRole = (role: any) => {
  ElMessageBox.confirm(
    `确定要删除角色 "${role.name}" 吗？`,
    '确认删除',
    { type: 'warning' }
  ).then(() => {
    roles.value = roles.value.filter(r => r.id !== role.id)
    ElMessage.success('删除成功')
  })
}

const saveRole = () => {
  const checkedKeys = permissionTree.value?.getCheckedKeys() || []
  roleForm.permissions = checkedKeys

  if (isEdit.value) {
    const index = roles.value.findIndex(r => r.id === roleForm.id)
    if (index > -1) {
      roles.value[index] = { ...roles.value[index], ...roleForm }
    }
    ElMessage.success('保存成功')
  } else {
    roles.value.push({
      id: Date.now().toString(),
      name: roleForm.name,
      code: roleForm.code,
      tag: '自定义',
      type: '',
      description: roleForm.description,
      userCount: 0,
      permissionCount: roleForm.permissions.length,
      permissions: roleForm.permissions,
      isDefault: false
    })
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
}
</script>

<style scoped>
.system-roles {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.role-card {
  margin-bottom: 20px;
  transition: all 0.3s;
}

.role-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.role-card.is-default {
  border-left: 4px solid #409EFF;
}

.role-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.role-info h3 {
  margin: 8px 0 0;
  font-size: 18px;
}

.role-desc {
  color: #909399;
  font-size: 14px;
  margin: 10px 0;
  min-height: 40px;
}

.role-stats {
  display: flex;
  gap: 20px;
  margin: 15px 0;
  color: #606266;
  font-size: 14px;
}

.role-stats span {
  display: flex;
  align-items: center;
  gap: 5px;
}

.role-permissions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 15px;
}

.permission-tag {
  padding: 4px 8px;
  background: #ecf5ff;
  color: #409EFF;
  border-radius: 4px;
  font-size: 12px;
}

.permission-tree {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
}
</style>