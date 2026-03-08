<template>
  <div class="system-logs">
    <div class="page-header">
      <h2>操作日志审计</h2>
      <div class="header-actions">
        <el-button type="danger" @click="clearLogs">
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
          <el-select v-model="filterForm.type" placeholder="全部类型" clearable>
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
          <el-input v-model="filterForm.username" placeholder="用户名" clearable />
        </el-form-item>

        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filterForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="searchLogs"><el-icon><Search /></el-icon>查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志列表 -->
    <el-card>
      <el-table :data="logList" stripe v-loading="loading"
        @row-click="showLogDetail"
      >
        <el-table-column type="index" width="50" />
        
        <el-table-column prop="createdAt" label="时间" width="160" sortable>
          <template #default="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </el-table-column>

        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getLogType(row.type)">{{ getLogTypeText(row.type) }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="username" label="操作用户" width="120" />
        
        <el-table-column prop="module" label="操作模块" width="120" />

        <el-table-column prop="action" label="操作内容" min-width="200" show-overflow-tooltip />

        <el-table-column prop="ip" label="IP地址" width="130" />

        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100">
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
          <el-descriptions-item label="操作时间">{{ formatDate(selectedLog.createdAt) }}</el-descriptions-item>
          <el-descriptions-item label="操作用户">{{ selectedLog.username }}</el-descriptions-item>
          <el-descriptions-item label="用户角色">{{ selectedLog.role }}</el-descriptions-item>
          <el-descriptions-item label="操作类型">
            <el-tag :type="getLogType(selectedLog.type)">{{ getLogTypeText(selectedLog.type) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="操作模块">{{ selectedLog.module }}</el-descriptions-item>
          <el-descriptions-item label="操作内容">{{ selectedLog.action }}</el-descriptions-item>
          <el-descriptions-item label="IP地址">{{ selectedLog.ip }}</el-descriptions-item>
          <el-descriptions-item label="浏览器">{{ selectedLog.userAgent }}</el-descriptions-item>
          <el-descriptions-item label="请求参数">
            <pre>{{ JSON.stringify(selectedLog.params, null, 2) }}</pre>
          </el-descriptions-item>
          <el-descriptions-item label="执行状态">
            <el-tag :type="selectedLog.status === 'success' ? 'success' : 'danger'">
              {{ selectedLog.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedLog.error" label="错误信息">
            <div class="error-message">{{ selectedLog.error }}</div>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Download, Search } from '@element-plus/icons-vue'

const loading = ref(false)
const detailVisible = ref(false)
const selectedLog = ref<any>(null)

const stats = ref({
  todayCount: 156,
  loginCount: 23,
  errorCount: 2,
  totalCount: 12580
})

const filterForm = reactive({
  type: '',
  username: '',
  dateRange: []
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 12580
})

const logList = ref([
  {
    id: 'log_001',
    createdAt: '2024-03-08 14:30:25',
    type: 'login',
    username: 'admin',
    role: '管理员',
    module: '系统',
    action: '用户登录',
    ip: '192.168.1.100',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    params: { username: 'admin' },
    status: 'success'
  },
  {
    id: 'log_002',
    createdAt: '2024-03-08 14:25:10',
    type: 'create',
    username: 'zhangsan',
    role: '会计',
    module: '票据管理',
    action: '创建票据',
    ip: '192.168.1.105',
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
    params: { invoice_no: '00123456', amount: 15000 },
    status: 'success'
  },
  {
    id: 'log_003',
    createdAt: '2024-03-08 14:20:00',
    type: 'audit',
    username: 'lisi',
    role: '审计员',
    module: '审核工作台',
    action: '审核通过凭证 #V202403001',
    ip: '192.168.1.108',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    params: { voucher_id: 'V202403001', result: 'approved' },
    status: 'success'
  },
  {
    id: 'log_004',
    createdAt: '2024-03-08 14:15:30',
    type: 'update',
    username: 'wangwu',
    role: '会计',
    module: '客户管理',
    action: '修改客户信息',
    ip: '192.168.1.110',
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
    params: { customer_id: 'C001', fields: ['phone', 'address'] },
    status: 'success'
  },
  {
    id: 'log_005',
    createdAt: '2024-03-08 14:10:15',
    type: 'delete',
    username: 'admin',
    role: '管理员',
    module: '系统管理',
    action: '删除用户',
    ip: '192.168.1.100',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    params: { user_id: 'U123' },
    status: 'error',
    error: '无法删除，该用户有关联数据'
  }
])

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

const formatDate = (date: string) => {
  return date
}

const searchLogs = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
    ElMessage.success('查询完成')
  }, 500)
}

const resetFilter = () => {
  filterForm.type = ''
  filterForm.username = ''
  filterForm.dateRange = []
}

const handleSizeChange = (val: number) => {
  pagination.pageSize = val
  searchLogs()
}

const handlePageChange = (val: number) => {
  pagination.page = val
}

const showLogDetail = (row: any) => {
  selectedLog.value = row
  detailVisible.value = true
}

const clearLogs = () => {
  ElMessageBox.confirm(
    '确定要清空所有操作日志吗？此操作不可恢复！',
    '警告',
    { type: 'warning', confirmButtonText: '确定清空' }
  ).then(() => {
    logList.value = []
    stats.value.totalCount = 0
    ElMessage.success('日志已清空')
  })
}

const exportLogs = () => {
  ElMessage.success('日志导出成功')
}
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
</style>