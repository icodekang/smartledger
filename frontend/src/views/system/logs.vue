<template>
  <div class="system-logs">
    <div class="page-header">
      <h2>操作日志审计</h2>
      <div class="header-actions">
        <el-button type="danger" @click="clearLogs" :disabled="!hasPermission">
          <el-icon><Delete /></el-icon>清空日志
        </el-button>
        <el-button type="primary" @click="exportLogs">
          <el-icon><Download /></el-icon>导出
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card>
          <template #header>
            <span>今日操作</span>
          </template>
          <div class="stat-value">{{ stats.todayCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>
            <span>登录次数</span>
          </template>
          <div class="stat-value">{{ stats.loginCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>
            <span>异常操作</span>
          </template>
          <div class="stat-value error">{{ stats.errorCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>
            <span>总记录数</span>
          </template>
          <div class="stat-value">{{ stats.totalCount }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="操作类型">
          <el-select v-model="filterForm.type" placeholder="全部类型" clearable style="width: 120px">
            <el-option label="登录" value="login" />
            <el-option label="登出" value="logout" />
            <el-option label="创建" value="create" />
            <el-option label="修改" value="update" />
            <el-option label="删除" value="delete" />
            <el-option label="导出" value="export" />
            <el-option label="审核" value="audit" />
          </el-select>
        </el-form-item>

        <el-form-item label="操作用户">
          <el-input v-model="filterForm.username" placeholder="用户名" clearable style="width: 120px" />
        </el-form-item>

        <el-form-item label="关键词">
          <el-input v-model="filterForm.keyword" placeholder="操作内容关键词" clearable style="width: 150px" />
        </el-form-item>

        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filterForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="searchLogs">
            <el-icon><Search /></el-icon>查询
          </el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志列表 -->
    <el-card>
      <el-table 
        :data="logList" 
        stripe 
        v-loading="loading"
        @row-click="showLogDetail"
        row-class-name="log-row"
      >
        <el-table-column type="index" width="50" />
        
        <el-table-column prop="created_at" label="时间" width="160" sortable>
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column prop="action_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getLogType(row.action_type)">{{ getLogTypeText(row.action_type) }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="username" label="操作用户" width="120" />
        
        <el-table-column prop="module" label="操作模块" width="120" />

        <el-table-column prop="description" label="操作内容" min-width="200" show-overflow-tooltip />

        <el-table-column prop="ip_address" label="IP地址" width="130" />

        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="showLogDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 日志详情弹窗 -->
    <el-dialog v-model="detailVisible" title="日志详情" width="600px">
      <div v-if="selectedLog" class="log-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="日志ID">{{ selectedLog.id }}</el-descriptions-item>
          <el-descriptions-item label="操作时间">{{ formatDate(selectedLog.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="操作用户">{{ selectedLog.username }}</el-descriptions-item>
          <el-descriptions-item label="用户角色">{{ selectedLog.role || '-' }}</el-descriptions-item>
          <el-descriptions-item label="操作类型">
            <el-tag :type="getLogType(selectedLog.action_type)">{{ getLogTypeText(selectedLog.action_type) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="操作模块">{{ selectedLog.module }}</el-descriptions-item>
          <el-descriptions-item label="操作内容">{{ selectedLog.description }}</el-descriptions-item>
          <el-descriptions-item label="IP地址">{{ selectedLog.ip_address }}</el-descriptions-item>
          <el-descriptions-item label="User-Agent">{{ selectedLog.user_agent || '-' }}</el-descriptions-item>
          <el-descriptions-item label="请求参数">
            <pre>{{ formatJson(selectedLog.request_params) }}</pre>
          </el-descriptions-item>
          <el-descriptions-item label="执行状态">
            <el-tag :type="selectedLog.status === 'success' ? 'success' : 'danger'">
              {{ selectedLog.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedLog.error_message" label="错误信息">
            <div class="error-message">{{ selectedLog.error_message }}</div>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Download, Search } from '@element-plus/icons-vue'
import api from '@/api'

const loading = ref(false)
const detailVisible = ref(false)
const selectedLog = ref<any>(null)
const hasPermission = ref(true) // 可根据权限调整

const stats = ref({
  todayCount: 0,
  loginCount: 0,
  errorCount: 0,
  totalCount: 0
})

const filterForm = reactive({
  type: '',
  username: '',
  keyword: '',
  dateRange: [] as string[]
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const logList = ref<any[]>([])

// 获取日志列表
const fetchLogs = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    
    if (filterForm.type) params.action = filterForm.type
    if (filterForm.username) params.user_id = filterForm.username
    if (filterForm.dateRange?.length === 2) {
      params.start_date = filterForm.dateRange[0]
      params.end_date = filterForm.dateRange[1]
    }
    
    const res = await api.get('/sys/logs', { params })
    logList.value = res.data.items || []
    pagination.total = res.data.total || 0
    
    // 更新统计
    if (res.data.stats) {
      stats.value = res.data.stats
    }
  } catch (error) {
    console.error('获取日志列表失败', error)
    ElMessage.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

// 获取统计信息
const fetchStats = async () => {
  try {
    const res = await api.get('/system/logs/stats')
    if (res.data) {
      stats.value = res.data
    }
  } catch (error) {
    console.error('获取统计失败', error)
  }
}

const getLogType = (type: string) => {
  const map: Record<string, string> = {
    login: 'success',
    logout: 'info',
    create: 'primary',
    update: 'warning',
    delete: 'danger',
    export: 'info',
    audit: 'success'
  }
  return map[type] || 'info'
}

const getLogTypeText = (type: string) => {
  const map: Record<string, string> = {
    login: '登录',
    logout: '登出',
    create: '创建',
    update: '修改',
    delete: '删除',
    export: '导出',
    audit: '审核'
  }
  return map[type] || type
}

const formatDate = (date: string | undefined) => {
  if (!date) return '-'
  return date.replace('T', ' ').substring(0, 19)
}

const formatJson = (data: any) => {
  if (!data) return '-'
  try {
    return typeof data === 'string' ? JSON.stringify(JSON.parse(data), null, 2) : JSON.stringify(data, null, 2)
  } catch {
    return data
  }
}

const searchLogs = () => {
  pagination.page = 1
  fetchLogs()
}

const resetFilter = () => {
  filterForm.type = ''
  filterForm.username = ''
  filterForm.keyword = ''
  filterForm.dateRange = []
  pagination.page = 1
  fetchLogs()
}

const handleSizeChange = (val: number) => {
  pagination.pageSize = val
  fetchLogs()
}

const handlePageChange = (val: number) => {
  pagination.page = val
  fetchLogs()
}

const showLogDetail = (row: any) => {
  selectedLog.value = row
  detailVisible.value = true
}

const clearLogs = () => {
  ElMessageBox.confirm(
    '确定要清空所有操作日志吗？此操作不可恢复！',
    '警告',
    { type: 'warning', confirmButtonText: '确定清空', cancelButtonText: '取消' }
  ).then(async () => {
    try {
      await api.delete('/system/logs/clear')
      ElMessage.success('日志已清空')
      fetchLogs()
      fetchStats()
    } catch (error) {
      ElMessage.error('清空失败')
    }
  }).catch(() => {})
}

const exportLogs = () => {
  if (logList.value.length === 0) {
    ElMessage.warning('没有可导出的数据')
    return
  }
  
  const headers = ['时间', '类型', '用户', '模块', '操作内容', 'IP地址', '状态']
  const rows = logList.value.map(log => [
    formatDate(log.created_at),
    getLogTypeText(log.action_type),
    log.username,
    log.module,
    log.description,
    log.ip_address,
    log.status === 'success' ? '成功' : '失败'
  ])
  
  const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n')
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `操作日志_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  
  ElMessage.success('导出成功')
}

onMounted(() => {
  fetchLogs()
  fetchStats()
})
</script>

<style scoped>
.system-logs {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.stat-row {
  margin-bottom: 20px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
}

.stat-value.error {
  color: #F56C6C;
}

.filter-card {
  margin-bottom: 20px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.log-detail pre {
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  max-height: 200px;
  overflow: auto;
  margin: 0;
  font-size: 12px;
}

.error-message {
  color: #F56C6C;
  padding: 10px;
  background: #fef0f0;
  border-radius: 4px;
}

.log-row {
  cursor: pointer;
}

.log-row:hover {
  background-color: #f5f7fa;
}
</style>
