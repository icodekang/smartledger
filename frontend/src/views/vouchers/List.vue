<template>
  <div class="voucher-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>凭证管理</span>
        </div>
      </template>
      
      <!-- 筛选 -->
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable>
            <el-option label="草稿" value="draft" />
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已驳回" value="rejected" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="会计期间">
          <el-input v-model="filterForm.period" placeholder="如：202403" clearable />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
      
      <!-- 表格 -->
      <el-table :data="tableData" v-loading="loading" border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="voucher_no" label="凭证号" width="120" />
        
        <el-table-column prop="voucher_date" label="凭证日期" width="120" />
        
        <el-table-column prop="period" label="会计期间" width="100" />
        
        <el-table-column prop="summary" label="摘要" min-width="200" show-overflow-tooltip />
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="ai_confidence" label="AI置信度" width="100">
          <template #default="{ row }">
            <el-progress 
              :percentage="Math.round((row.ai_confidence || 0) * 100)" 
              :status="(row.ai_confidence || 0) > 0.85 ? 'success' : 'warning'"
            />
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchData"
        @current-change="fetchData"
        class="pagination"
      />
    </el-card>
    
    <!-- 详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="凭证详情" width="700px">
      <template v-if="currentVoucher">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="凭证号">{{ currentVoucher.voucher_no }}</el-descriptions-item>
          <el-descriptions-item label="日期">{{ currentVoucher.voucher_date }}</el-descriptions-item>
          <el-descriptions-item label="期间">{{ currentVoucher.period }}</el-descriptions-item>
          <el-descriptions-item label="摘要" :span="3">{{ currentVoucher.summary }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentVoucher.status)">
              {{ getStatusText(currentVoucher.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="AI置信度" :span="2">
            {{ Math.round((currentVoucher.ai_confidence || 0) * 100) }}%
          </el-descriptions-item>
        </el-descriptions>
        
        <h4 style="margin: 20px 0 10px">分录明细</h4>
        
        <el-table :data="currentVoucher.items" border size="small">
          <el-table-column prop="line_no" label="行号" width="60" />
          <el-table-column prop="subject_code" label="科目代码" width="100" />
          <el-table-column prop="subject_name" label="科目名称" min-width="150" />
          <el-table-column prop="summary" label="摘要" min-width="150" show-overflow-tooltip />
          <el-table-column prop="debit_amount" label="借方金额" width="120" align="right">
            <template #default="{ row }">
              {{ row.debit_amount > 0 ? formatAmount(row.debit_amount) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="credit_amount" label="贷方金额" width="120" align="right">
            <template #default="{ row }">
              {{ row.credit_amount > 0 ? formatAmount(row.credit_amount) : '-' }}
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { voucherApi, type Voucher } from '../../api/voucher'

const loading = ref(false)
const tableData = ref<Voucher[]>([])
const showDetailDialog = ref(false)
const currentVoucher = ref<Voucher | null>(null)
const selectedIds = ref<string[]>([])

const filterForm = reactive({
  status: '',
  period: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await voucherApi.getList({
      page: pagination.page,
      page_size: pagination.page_size,
      ...filterForm
    })
    tableData.value = res.items
    pagination.total = res.total
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.status = ''
  filterForm.period = ''
  fetchData()
}

const formatAmount = (amount: number) => {
  return `¥${amount.toFixed(2)}`
}

const getStatusType = (status?: string) => {
  const map: Record<string, string> = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return map[status || ''] || 'info'
}

const getStatusText = (status?: string) => {
  const map: Record<string, string> = {
    draft: '草稿',
    pending: '待审核',
    approved: '已通过',
    rejected: '已驳回'
  }
  return map[status || ''] || status
}

const viewDetail = async (row: Voucher) => {
  const res = await voucherApi.getDetail(row.id)
  currentVoucher.value = res
  showDetailDialog.value = true
}

const handleSelectionChange = (selection: Voucher[]) => {
  selectedIds.value = selection.map(item => item.id)
}

onMounted(fetchData)
</script>

<style scoped>
.voucher-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}

/* 移动端样式 */
@media (max-width: 768px) {
  .voucher-list {
    padding: 12px;
  }
  
  .card-header span {
    font-size: 16px;
    font-weight: 600;
  }
  
  .el-form--inline .el-form-item {
    display: block;
    margin-right: 0;
    margin-bottom: 12px;
  }
  
  .el-form--inline .el-form-item__content {
    width: 100%;
  }
  
  .el-form--inline .el-select {
    width: 100%;
  }
  
  .el-table {
    font-size: 12px;
  }
  
  .el-table .el-table__header-wrapper th,
  .el-table .el-table__body-wrapper td {
    padding: 8px 0;
  }
  
  .pagination {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .el-dialog {
    width: 95% !important;
    margin: 10px auto !important;
  }
  
  .el-dialog__body {
    padding: 16px;
  }
}

/* 超小屏幕 */
@media (max-width: 480px) {
  .voucher-list {
    padding: 8px;
  }
  
  .el-table {
    font-size: 11px;
  }
  
  .el-tag {
    font-size: 10px;
  }
}
</style>
