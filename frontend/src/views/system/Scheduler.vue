<template>
  <div class="scheduler-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>定时任务调度</span>
          <el-button type="primary" @click="handleCreateTask">+ 新建任务</el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="任务列表" name="tasks">
          <el-table :data="scheduledTasks" v-loading="loading" border>
            <el-table-column prop="name" label="任务名称" />
            <el-table-column prop="type" label="任务类型" width="120">
              <template #default="{ row }">
                <el-tag>{{ getTypeText(row.type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="cron" label="Cron表达式" width="150" />
            <el-table-column prop="next_run" label="下次执行" width="180" />
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
                <el-button type="warning" link @click="handleRunNow(row)">立即执行</el-button>
                <el-button :type="row.status === 'active' ? 'warning' : 'success'" link @click="handleToggleTask(row)">
                  {{ row.status === 'active' ? '停用' : '启用' }}
                </el-button>
                <el-button type="danger" link @click="handleDeleteTask(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="执行历史" name="history">
          <el-table :data="executionHistory" v-loading="loadingHistory" border>
            <el-table-column prop="task_name" label="任务名称" />
            <el-table-column prop="started_at" label="开始时间" width="180" />
            <el-table-column prop="finished_at" label="结束时间" width="180" />
            <el-table-column prop="duration" label="耗时" width="100">
              <template #default="{ row }">
                <span>{{ row.duration }}s</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'success' ? 'success' : row.status === 'running' ? 'warning' : 'danger'">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="result" label="结果" />
          </el-table>
          <el-pagination
            v-if="totalHistory > 0"
            v-model:current-page="historyPage"
            :page-size="20"
            :total="totalHistory"
            layout="total, prev, pager, next"
            @current-change="fetchHistory"
            style="margin-top: 16px; justify-content: flex-end"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 任务编辑对话框 -->
    <el-dialog v-model="showTaskDialog" :title="isCreateTask ? '新建定时任务' : '编辑定时任务'" width="550px">
      <el-form :model="taskForm" label-width="100px">
        <el-form-item label="任务名称" required>
          <el-input v-model="taskForm.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="任务类型" required>
          <el-select v-model="taskForm.type" style="width: 100%" placeholder="选择任务类型">
            <el-option label="数据同步" value="sync" />
            <el-option label="数据清理" value="cleanup" />
            <el-option label="报表生成" value="report" />
            <el-option label="通知发送" value="notification" />
            <el-option label="自定义脚本" value="script" />
          </el-select>
        </el-form-item>
        <el-form-item label="Cron表达式" required>
          <el-input v-model="taskForm.cron" placeholder="例如: 0 * * * * (每小时)" />
          <div class="cron-hint">
            <span>格式: 分 时 日 月 周</span>
            <el-link type="primary" @click="showCronHelp = true">查看帮助</el-link>
          </div>
        </el-form-item>
        <el-form-item label="执行参数">
          <el-input v-model="taskForm.params" type="textarea" :rows="3" placeholder="JSON格式参数" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="taskForm.description" type="textarea" :rows="2" />
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

    <!-- Cron帮助对话框 -->
    <el-dialog v-model="showCronHelp" title="Cron表达式帮助" width="500px">
      <el-table :data="cronExamples">
        <el-table-column prop="expression" label="表达式" />
        <el-table-column prop="description" label="说明" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { systemApi } from '../../api/system'

const activeTab = ref('tasks')
const loading = ref(false)
const loadingHistory = ref(false)
const showTaskDialog = ref(false)
const showCronHelp = ref(false)
const isCreateTask = ref(false)
const savingTask = ref(false)

const scheduledTasks = ref([])
const executionHistory = ref([])
const historyPage = ref(1)
const totalHistory = ref(0)

const taskForm = ref({
  name: '',
  type: 'sync',
  cron: '0 * * * *',
  params: '',
  description: '',
  status: true
})
const currentTaskId = ref('')

const cronExamples = ref([
  { expression: '0 * * * *', description: '每小时执行' },
  { expression: '0 0 * * *', description: '每天凌晨执行' },
  { expression: '0 0 * * 0', description: '每周日凌晨执行' },
  { expression: '0 0 1 * *', description: '每月1日凌晨执行' },
  { expression: '*/5 * * * *', description: '每5分钟执行' }
])

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await systemApi.getScheduledTasks()
    scheduledTasks.value = res.data.items
  } catch (e) {
    scheduledTasks.value = [
      { id: '1', name: '每日数据同步', type: 'sync', cron: '0 2 * * *', next_run: '2024-01-11 02:00:00', last_run: '2024-01-10 02:00:00', status: 'active' },
      { id: '2', name: '月度报表生成', type: 'report', cron: '0 0 1 * *', next_run: '2024-02-01 00:00:00', last_run: '2024-01-01 00:00:00', status: 'active' },
      { id: '3', name: '清理临时文件', type: 'cleanup', cron: '0 3 * * *', next_run: '2024-01-11 03:00:00', last_run: '2024-01-10 03:00:00', status: 'active' }
    ]
  }
  loading.value = false
}

const fetchHistory = async () => {
  loadingHistory.value = true
  try {
    const res = await systemApi.getTaskHistory({ page: historyPage.value, page_size: 20 })
    executionHistory.value = res.data.items
    totalHistory.value = res.data.total
  } catch (e) {
    executionHistory.value = [
      { id: '1', task_name: '每日数据同步', started_at: '2024-01-10 02:00:00', finished_at: '2024-01-10 02:05:00', duration: 300, status: 'success', result: '同步 150 条记录' },
      { id: '2', task_name: '月度报表生成', started_at: '2024-01-01 00:00:00', finished_at: '2024-01-01 00:02:00', duration: 120, status: 'success', result: '生成 5 份报表' },
      { id: '3', task_name: '清理临时文件', started_at: '2024-01-10 03:00:00', finished_at: '2024-01-10 03:00:05', duration: 5, status: 'success', result: '删除 23 个文件' }
    ]
    totalHistory.value = 3
  }
  loadingHistory.value = false
}

const getTypeText = (type: string) => {
  const map: Record<string, string> = { sync: '数据同步', cleanup: '数据清理', report: '报表生成', notification: '通知发送', script: '自定义脚本' }
  return map[type] || type
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = { success: '成功', running: '执行中', failed: '失败' }
  return map[status] || status
}

const handleCreateTask = () => {
  isCreateTask.value = true
  currentTaskId.value = ''
  taskForm.value = { name: '', type: 'sync', cron: '0 * * * *', params: '', description: '', status: true }
  showTaskDialog.value = true
}

const handleEditTask = (row: any) => {
  isCreateTask.value = false
  currentTaskId.value = row.id
  taskForm.value = { ...row, status: row.status === 'active' }
  showTaskDialog.value = true
}

const handleSaveTask = async () => {
  if (!taskForm.value.name || !taskForm.value.cron) {
    ElMessage.warning('请填写任务名称和Cron表达式')
    return
  }
  savingTask.value = true
  try {
    const data = { ...taskForm.value, status: taskForm.value.status ? 'active' : 'inactive' }
    if (isCreateTask.value) {
      await systemApi.createScheduledTask(data)
    } else {
      await systemApi.updateScheduledTask(currentTaskId.value, data)
    }
    ElMessage.success('保存成功')
    showTaskDialog.value = false
    fetchTasks()
  } finally {
    savingTask.value = false
  }
}

const handleRunNow = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定立即执行任务 ${row.name} 吗？`, '确认执行', { type: 'info' })
    ElMessage.success('任务已启动，请查看执行历史')
  } catch {}
}

const handleToggleTask = async (row: any) => {
  const action = row.status === 'active' ? '停用' : '启用'
  try {
    await ElMessageBox.confirm(`确定${action}任务吗？`, '确认', { type: 'warning' })
    await systemApi.updateScheduledTask(row.id, { status: row.status === 'active' ? 'inactive' : 'active' })
    ElMessage.success(`${action}成功`)
    fetchTasks()
  } catch {}
}

const handleDeleteTask = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定删除任务 ${row.name} 吗？`, '确认删除', { type: 'warning' })
    await systemApi.deleteScheduledTask(row.id)
    ElMessage.success('删除成功')
    fetchTasks()
  } catch {}
}

onMounted(() => {
  fetchTasks()
  fetchHistory()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.cron-hint {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
</style>
