<template>
  <div class="bank-flow-list">
    <!-- 导入向导对话框 -->
    <BankFlowImportDialog
      v-model="showImportDialog"
      @success="handleImportSuccess"
    />

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="stat-card income">
          <div class="stat-icon"><TrendCharts /></div>
          <div class="stat-content">
            <div class="stat-value positive">+¥{{ formatAmount(stats.total_income) }}</div>
            <div class="stat-label">本月总收入</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="stat-card expense">
          <div class="stat-icon"><Money /></div>
          <div class="stat-content">
            <div class="stat-value negative">-¥{{ formatAmount(stats.total_expense) }}</div>
            <div class="stat-label">本月总支出</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="stat-card unmatched">
          <div class="stat-icon"><Connection /></div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.unmatched_count }}</div>
            <div class="stat-label">未匹配笔数</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="stat-card balance">
          <div class="stat-icon"><Wallet /></div>
          <div class="stat-content">
            <div class="stat-value">¥{{ formatAmount(currentBalance) }}</div>
            <div class="stat-label">当前余额</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 主列表卡片 -->
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <span class="title">银行流水管理</span>
          <div class="header-actions">
            <el-button type="primary" @click="showImportDialog = true">
              <el-icon><Upload /></el-icon>
              导入流水
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选区 -->
      <div class="filter-section">
        <el-form :inline="true" :model="filterForm">
          <el-form-item label="日期范围">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              :shortcuts="dateShortcuts"
              @change="handleDateChange"
            />
          </el-form-item>

          <el-form-item label="匹配状态">
            <el-select v-model="filterForm.match_status" placeholder="全部" clearable @change="fetchData">
              <el-option label="全部" value="" />
              <el-option label="未匹配" value="unmatched" />
              <el-option label="已匹配" value="matched" />
              <el-option label="已忽略" value="ignored" />
            </el-select>
          </el-form-item>

          <el-form-item label="关键词">
            <el-input
              v-model="filterForm.keyword"
              placeholder="对方户名/摘要"
              clearable
              @keyup.enter="fetchData"
            >
              <template #append>
                <el-button @click="fetchData"><Search /></el-button>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 批量操作栏 -->
      <div v-if="selectedRows.length > 0" class="batch-bar">
        <span>已选择 {{ selectedRows.length }} 项</span>
        <el-button type="danger" size="small" @click="handleBatchDelete">批量删除</el-button>
      </div>

      <!-- 数据表格 -->
      <el-table
        :data="tableData"
        v-loading="loading"
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="transaction_date" label="交易日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.transaction_date) }}
          </template>
        </el-table-column>

        <el-table-column label="收入" width="120" align="right">
          <template #default="{ row }">
            <span v-if="row.amount > 0" class="positive">+{{ formatAmount(row.amount) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column label="支出" width="120" align="right">
          <template #default="{ row }">
            <span v-if="row.amount < 0" class="negative">{{ formatAmount(row.amount) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="counterparty_name" label="对方户名" min-width="150" show-overflow-tooltip />

        <el-table-column prop="summary" label="摘要" min-width="200" show-overflow-tooltip />

        <el-table-column prop="balance" label="余额" width="120" align="right">
          <template #default="{ row }">
            {{ row.balance ? formatAmount(row.balance) : '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="match_status" label="匹配状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getMatchStatusType(row.match_status)">
              {{ getMatchStatusText(row.match_status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleMatch(row)">
              {{ row.match_status === 'unmatched' ? '匹配' : '查看' }}
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchData"
        @current-change="fetchData"
        class="pagination"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload, Search, TrendCharts, Money, Connection, Wallet
} from '@element-plus/icons-vue'
import { bankFlowApi, type BankFlow } from '../../api/bank-flow'
import BankFlowImportDialog from './components/BankFlowImportDialog.vue'

// 导入对话框
const showImportDialog = ref(false)

// 统计数据
const stats = reactive({
  total_income: 0,
  total_expense: 0,
  unmatched_count: 0
})

const currentBalance = ref(0)

// 筛选表单
const filterForm = reactive({
  match_status: '',
  keyword: ''
})

// 日期范围
const dateRange = ref<Date[] | null>(null)

const dateShortcuts = [
  { text: '本月', value: () => getMonthRange() },
  { text: '上月', value: () => getLastMonthRange() },
  { text: '本季度', value: () => getQuarterRange() },
  { text: '本年', value: () => getYearRange() }
]

function getMonthRange(): Date[] {
  const now = new Date()
  const start = new Date(now.getFullYear(), now.getMonth(), 1)
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  return [start, end]
}

function getLastMonthRange(): Date[] {
  const now = new Date()
  const start = new Date(now.getFullYear(), now.getMonth() - 1, 1)
  const end = new Date(now.getFullYear(), now.getMonth(), 0)
  return [start, end]
}

function getQuarterRange(): Date[] {
  const now = new Date()
  const quarter = Math.floor(now.getMonth() / 3)
  const start = new Date(now.getFullYear(), quarter * 3, 1)
  const end = new Date(now.getFullYear(), quarter * 3 + 3, 0)
  return [start, end]
}

function getYearRange(): Date[] {
  const now = new Date()
  const start = new Date(now.getFullYear(), 0, 1)
  const end = new Date(now.getFullYear(), 11, 31)
  return [start, end]
}

function handleDateChange() {
  fetchData()
}

// 表格数据
const loading = ref(false)
const tableData = ref<BankFlow[]>([])
const selectedRows = ref<BankFlow[]>([])

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size,
      match_status: filterForm.match_status || undefined,
      keyword: filterForm.keyword || undefined
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]?.toISOString().split('T')[0]
      params.end_date = dateRange.value[1]?.toISOString().split('T')[0]
    }
    
    const res = await bankFlowApi.getList(params)
    tableData.value = res.data.items
    pagination.total = res.data.total
    
    // 更新统计
    stats.total_income = res.data.summary.total_income
    stats.total_expense = res.data.summary.total_expense
    stats.unmatched_count = res.data.summary.unmatched_count
    
    // 计算余额
    if (tableData.value.length > 0) {
      const firstRow = tableData.value[0]
      currentBalance.value = firstRow.balance || 0
    }
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 重置筛选
const resetFilter = () => {
  filterForm.match_status = ''
  filterForm.keyword = ''
  dateRange.value = null
  fetchData()
}

// 选择变化
const handleSelectionChange = (selection: BankFlow[]) => {
  selectedRows.value = selection
}

// 匹配票据
const handleMatch = (row: BankFlow) => {
  if (row.match_status === 'unmatched') {
    // TODO: 打开匹配对话框
    ElMessage.info('匹配功能开发中...')
  } else {
    // 查看已匹配详情
    ElMessage.info('查看功能开发中...')
  }
}

// 删除
const handleDelete = async (row: BankFlow) => {
  try {
    await ElMessageBox.confirm('确定删除该银行流水吗？', '提示', { type: 'warning' })
    await bankFlowApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    // 取消或错误
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedRows.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedRows.value.length} 条银行流水吗？`,
      '提示',
      { type: 'warning' }
    )
    const ids = selectedRows.value.map(row => row.id)
    await bankFlowApi.batchDelete(ids)
    ElMessage.success('批量删除成功')
    fetchData()
  } catch (error) {
    // 取消或错误
  }
}

// 导入成功
const handleImportSuccess = () => {
  fetchData()
}

// 格式化金额
const formatAmount = (amount?: number) => {
  if (!amount) return '0.00'
  return Math.abs(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// 格式化日期
const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// 匹配状态类型
const getMatchStatusType = (status: string) => {
  const map: Record<string, string> = {
    unmatched: 'warning',
    matched: 'success',
    ignored: 'info'
  }
  return map[status] || 'info'
}

// 匹配状态文本
const getMatchStatusText = (status: string) => {
  const map: Record<string, string> = {
    unmatched: '未匹配',
    matched: '已匹配',
    ignored: '已忽略'
  }
  return map[status] || status
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.bank-flow-list {
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-right: 16px;
  background: #f0f9ff;
  color: #409eff;
}

.stat-card.income .stat-icon {
  background: #f0fff4;
  color: #67c23a;
}

.stat-card.expense .stat-icon {
  background: #fff5f5;
  color: #f56c6c;
}

.stat-card.unmatched .stat-icon {
  background: #fffaf0;
  color: #e6a23c;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.stat-value.positive {
  color: #67c23a;
}

.stat-value.negative {
  color: #f56c6c;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.list-card {
  margin-top: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header .title {
  font-size: 16px;
  font-weight: 600;
}

.filter-section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.batch-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 16px;
}

.positive {
  color: #67c23a;
  font-weight: 500;
}

.negative {
  color: #f56c6c;
  font-weight: 500;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
