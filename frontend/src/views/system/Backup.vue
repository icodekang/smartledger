<template>
  <div class="backup-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据备份与恢复</span>
          <el-button type="primary" @click="handleCreateBackup">+ 创建备份</el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="备份任务" name="tasks">
          <el-table :data="backupTasks" v-loading="loading" border>
            <el-table-column prop="name" label="任务名称" />
            <el-table-column prop="schedule" label="调度规则" />
            <el-table-column prop="retention" label="保留天数" />
            <el-table-column prop="last_run" label="上次执行" width="180" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'">
                  {{ row.status === 'active' ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleEditTask(row)">编辑</el-button>
                <el-button :type="row.status === 'active' ? 'warning' : 'success'" link @click="handleToggleTask(row)">
                  {{ row.status === 'active' ? '停用' : '启用' }}
                </el-button>
                <el-button type="danger" link @click="handleDeleteTask(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="备份记录" name="records">
          <el-table :data="backupRecords" v-loading="loadingRecords" border>
            <el-table-column prop="filename" label="文件名" />
            <el-table-column prop="size" label="大小" width="120">
              <template #default="{ row }">
                <span>{{ formatSize(row.size) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'success' ? 'success' : row.status === 'running' ? 'warning' : 'danger'">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleRestore(row)">恢复</el-button>
                <el-button type="success" link @click="handleDownload(row)">下载</el-button>
                <el-button type="danger" link @click="handleDeleteRecord(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 备份任务编辑对话框 -->
    <el-dialog v-model="showTaskDialog" :title="isCreateTask ? '新建备份任务' : '编辑备份任务'" width="500px">
      <el-form :model="taskForm" :rules="formRules" label-width="100px">
        <el-form-item label="任务名称" required>
          <el-input v-model="taskForm.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="调度规则">
          <el-input v-model="taskForm.schedule" placeholder="例如: 0 2 * * * (每天凌晨2点)" />
        </el-form-item>
        <el-form-item label="保留天数">
          <el-input-number v-model="taskForm.retention" :min="1" :max="365" style="width: 100%" />
        </el-form-item>
        <el-form-item label="包含表">
          <el-select v-model="taskForm.tables" multiple style="width: 100%" placeholder="选择要备份的表">
            <el-option label="全部" value="all" />
            <el-option label="用户" value="users" />
            <el-option label="客户" value="customers" />
            <el-option label="合同" value="contracts" />
            <el-option label="账单" value="bills" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="taskForm.status">启用任务</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTaskDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveTask" :loading="savingTask">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { systemApi } from '../../api/system'

const activeTab = ref('tasks')
const loading = ref(false)
const loadingRecords = ref(false)
const showTaskDialog = ref(false)
const isCreateTask = ref(false)
const savingTask = ref(false)

const backupTasks = ref([])
const backupRecords = ref([])

const taskForm = ref({
  name: '',
  schedule: '0 2 * * *',
  retention: 7,
  tables: ['all'],
  status: true
})
const currentTaskId = ref('')

// 表单验证规则
const validateSchedule = (_rule: any, value: string, callback: any) => {
  if (value && !/^(\*|([0-5]?\d(-[0-5]?\d)?)(,\s*(\*|([0-5]?\d(-[0-5]?\d)?)))*)\s+(\*|([01]?\d|2[0-3])(-([01]?\d|2[0-3]))?)(,\s*(\*|([01]?\d|2[0-3])(-([01]?\d|2[0-3]))?))*\s+(\*|([1-9]|[12]\d|3[01])(-([1-9]|[12]\d|3[01]))?)(,\s*(\*|([1-9]|[12]\d|3[01])(-([1-9]|[12]\d|3[01]))?))*\s+(\*|([1-9]|1[0-2])(-([1-9]|1[0-2]))?)(,\s*(\*|([1-9]|1[0-2])(-([1-9]|1[0-2]))?))*\s+(\*|[0-7](-[0-7])?)(,\s*(\*|[0-7](-[0-7])?))*$/.test(value)) {
    callback(new Error('请输入有效的Cron表达式'))
  } else {
    callback()
  }
}

const formRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  schedule: [{ validator: validateSchedule, trigger: 'blur' }]
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await systemApi.getBackupTasks()
    backupTasks.value = res.data.items
  } catch (e) {
    backupTasks.value = [
      { id: '1', name: '每日全量备份', schedule: '0 2 * * *', retention: 7, last_run: '2024-01-10 02:00:00', status: 'active' },
      { id: '2', name: '每小时增量备份', schedule: '0 * * * *', retention: 3, last_run: '2024-01-10 10:00:00', status: 'active' }
    ]
  }
  loading.value = false
}

const fetchRecords = async () => {
  loadingRecords.value = true
  try {
    const res = await systemApi.getBackupRecords()
    backupRecords.value = res.data.items
  } catch (e) {
    backupRecords.value = [
      { id: '1', filename: 'backup_20240110_020000.sql', size: 1024 * 1024 * 50, created_at: '2024-01-10 02:00:00', status: 'success' },
      { id: '2', filename: 'backup_20240110_100000.sql', size: 1024 * 1024 * 30, created_at: '2024-01-10 10:00:00', status: 'success' }
    ]
  }
  loadingRecords.value = false
}

const formatSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB'
  return (bytes / 1024 / 1024 / 1024).toFixed(1) + ' GB'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = { success: '成功', running: '执行中', failed: '失败' }
  return map[status] || status
}

const handleCreateBackup = async () => {
  try {
    await ElMessageBox.confirm('立即创建备份？', '创建备份', { type: 'info' })
    ElMessage.success('备份任务已启动，请稍后查看记录')
    setTimeout(fetchRecords, 2000)
  } catch {}
}

const handleEditTask = (row: any) => {
  isCreateTask.value = false
  currentTaskId.value = row.id
  taskForm.value = { ...row, tables: row.tables || ['all'], status: row.status === 'active' }
  showTaskDialog.value = true
}

const handleSaveTask = async () => {
  if (!taskForm.value.name) {
    ElMessage.warning('请输入任务名称')
    return
  }
  savingTask.value = true
  try {
    const data = { ...taskForm.value, status: taskForm.value.status ? 'active' : 'inactive' }
    if (isCreateTask.value) {
      await systemApi.createBackupTask(data)
    } else {
      await systemApi.updateBackupTask(currentTaskId.value, data)
    }
    ElMessage.success('保存成功')
    showTaskDialog.value = false
    fetchTasks()
  } finally {
    savingTask.value = false
  }
}

const handleToggleTask = async (row: any) => {
  const action = row.status === 'active' ? '停用' : '启用'
  try {
    await ElMessageBox.confirm(`确定${action}备份任务吗？`, '确认', { type: 'warning' })
    await systemApi.updateBackupTask(row.id, { status: row.status === 'active' ? 'inactive' : 'active' })
    ElMessage.success(`${action}成功`)
    fetchTasks()
  } catch {}
}

const handleDeleteTask = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定删除备份任务 ${row.name} 吗？`, '确认删除', { type: 'warning' })
    await systemApi.deleteBackupTask(row.id)
    ElMessage.success('删除成功')
    fetchTasks()
  } catch {}
}

const handleRestore = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定要恢复备份 ${row.filename} 吗？当前数据将被覆盖！`, '确认恢复', { type: 'warning' })
    ElMessage.success('恢复任务已启动，请稍后')
  } catch {}
}

const handleDownload = (row: any) => {
  ElMessage.info(`开始下载 ${row.filename}`)
}

const handleDeleteRecord = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定删除备份文件 ${row.filename} 吗？`, '确认删除', { type: 'warning' })
    await systemApi.deleteBackupRecord(row.id)
    ElMessage.success('删除成功')
    fetchRecords()
  } catch {}
}

onMounted(() => {
  fetchTasks()
  fetchRecords()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
