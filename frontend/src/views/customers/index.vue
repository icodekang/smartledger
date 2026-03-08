<template>
  <div class="customer-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>客户管理</span>
          <el-button type="primary" @click="handleCreate">
            <Plus /> 新建客户
          </el-button>
        </div>
      </template>

      <!-- 筛选区 -->
      <div class="filter-section">
        <el-form :inline="true" :model="filterForm">
          <el-form-item label="关键词">
            <el-input
              v-model="filterForm.keyword"
              placeholder="客户名称/编码/税号"
              clearable
              @keyup.enter="fetchData"
            />
          </el-form-item>

          <el-form-item label="状态">
            <el-select v-model="filterForm.status" placeholder="全部" clearable @change="fetchData">
              <el-option label="全部" value="" />
              <el-option label="活跃" value="active" />
              <el-option label="停用" value="inactive" />
            </el-select>
          </el-form-item>

          <el-form-item label="行业">
            <el-select v-model="filterForm.industry" placeholder="全部" clearable @change="fetchData">
              <el-option label="全部" value="" />
              <el-option label="科技" value="科技" />
              <el-option label="制造" value="制造" />
              <el-option label="贸易" value="贸易" />
              <el-option label="服务" value="服务" />
            </el-select>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="fetchData">查询</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 统计卡片 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-statistic title="总客户" :value="summary.total" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="活跃客户" :value="summary.active_count">
            <template #suffix>
              <el-tag type="success" size="small">活跃</el-tag>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="停用客户" :value="summary.inactive_count">
            <template #suffix>
              <el-tag type="info" size="small">停用</el-tag>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="即将到期" :value="summary.expiring_soon">
            <template #suffix>
              <el-tag type="warning" size="small">30天内</el-tag>
            </template>
          </el-statistic>
        </el-col>
      </el-row>

      <!-- 数据表格 -->
      <el-table :data="tableData" v-loading="loading" border @row-click="handleRowClick">
        <el-table-column prop="code" label="客户编码" width="120" />
        
        <el-table-column prop="name" label="客户名称" min-width="200" show-overflow-tooltip />
        
        <el-table-column prop="tax_no" label="税号" width="180">
          <template #default="{ row }">
            {{ row.tax_no || '-' }}
          </template>
        </el-table-column>
        
        <el-table-column prop="industry" label="行业" width="120" />
        
        <el-table-column prop="phone" label="联系电话" width="130" />
        
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '活跃' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="服务到期" width="120">
          <template #default="{ row }">
            <span :class="{ 'expiring-soon': isExpiringSoon(row.service_end_date) }">
              {{ row.service_end_date || '-' }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click.stop="handleDelete(row)">删除</el-button>
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

    <!-- 客户详情/编辑对话框 -->
    <CustomerDetailDialog
      v-model="showDialog"
      :customer-id="currentCustomerId"
      :is-create="isCreate"
      @success="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { customerApi, type Customer } from '../../api/customer'
import CustomerDetailDialog from './components/CustomerDetailDialog.vue'

const loading = ref(false)
const tableData = ref<Customer[]>([])
const showDialog = ref(false)
const isCreate = ref(false)
const currentCustomerId = ref('')

const filterForm = reactive({
  keyword: '',
  status: '',
  industry: ''
})

const summary = reactive({
  total: 0,
  active_count: 0,
  inactive_count: 0,
  expiring_soon: 0
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await customerApi.getList({
      page: pagination.page,
      page_size: pagination.page_size,
      keyword: filterForm.keyword || undefined,
      status: filterForm.status || undefined,
      industry: filterForm.industry || undefined
    })
    
    tableData.value = res.data.items
    pagination.total = res.data.total
    
    // 更新统计
    summary.total = res.data.total
    summary.active_count = res.data.summary.active_count
    summary.inactive_count = res.data.summary.inactive_count
    summary.expiring_soon = res.data.summary.expiring_soon
  } catch (error) {
    console.error('获取客户列表失败:', error)
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.keyword = ''
  filterForm.status = ''
  filterForm.industry = ''
  fetchData()
}

const isExpiringSoon = (date?: string) => {
  if (!date) return false
  const endDate = new Date(date)
  const now = new Date()
  const diffDays = Math.ceil((endDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
  return diffDays <= 30 && diffDays >= 0
}

const handleCreate = () => {
  isCreate.value = true
  currentCustomerId.value = ''
  showDialog.value = true
}

const handleEdit = (row: Customer) => {
  isCreate.value = false
  currentCustomerId.value = row.id
  showDialog.value = true
}

const handleRowClick = (row: Customer) => {
  handleEdit(row)
}

const handleDelete = async (row: Customer) => {
  try {
    await ElMessageBox.confirm(
      `确定删除客户 "${row.name}" 吗？删除后不可恢复。`,
      '确认删除',
      { type: 'warning' }
    )
    
    await customerApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    // 取消或错误
  }
}

onMounted(fetchData)
</script>

<style scoped>
.customer-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-section {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.expiring-soon {
  color: #e6a23c;
  font-weight: bold;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}

:deep(.el-table__row) {
  cursor: pointer;
}
</style>
