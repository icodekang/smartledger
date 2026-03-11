<template>
  <div class="bill-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>票据管理</span>
          <el-button type="primary" size="small" @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon> 上传
          </el-button>
        </div>
      </template>
      
      <!-- 筛选 - 移动端简化版 -->
      <div class="filter-section">
        <el-form :inline="true" :model="filterForm" class="filter-form">
          <el-form-item label="类型" class="filter-item">
            <el-select v-model="filterForm.bill_type" placeholder="全部" clearable size="small">
              <el-option label="增值税发票" value="invoice" />
              <el-option label="收据" value="receipt" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="状态" class="filter-item">
            <el-select v-model="filterForm.process_status" placeholder="全部" clearable size="small">
              <el-option label="待处理" value="pending" />
              <el-option label="OCR完成" value="ocr_completed" />
              <el-option label="已生成凭证" value="voucher_generated" />
            </el-select>
          </el-form-item>
          
          <el-form-item class="filter-actions">
            <el-button type="primary" size="small" @click="fetchData">查询</el-button>
            <el-button size="small" @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 表格 -->
      <el-table :data="tableData" v-loading="loading" border>
        <el-table-column prop="invoice_code" label="发票代码" width="120" />
        <el-table-column prop="invoice_number" label="发票号码" width="120" />
        <el-table-column prop="seller_name" label="销售方" min-width="150" show-overflow-tooltip />
        <el-table-column prop="invoice_date" label="开票日期" width="120" />
        <el-table-column prop="amount" label="金额" width="120" align="right">
          <template #default="{ row }">
            {{ formatAmount(row.amount) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="total_amount" label="价税合计" width="120" align="right">
          <template #default="{ row }">
            {{ formatAmount(row.total_amount) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="process_status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.process_status)">
              {{ getStatusText(row.process_status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="info" link @click="viewDetail(row)">查看</el-button>
            <el-button 
              type="success" 
              link 
              :disabled="row.process_status !== 'ocr_completed'"
              @click="generateVoucher(row)"
            >
              生成凭证
            </el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
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
    
    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传票据" width="500px">
      <el-upload
        drag
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        accept=".jpg,.jpeg,.png,.pdf"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 JPG、PNG、PDF 格式，单个文件不超过 10MB
          </div>
        </template>
      </el-upload>
      
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">
          上传
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 详情编辑对话框 -->
    <BillDetailDialog
      v-model="showEditDialog"
      :bill-id="currentBillId"
      @success="handleEditSuccess"
    />
    
    <!-- 详情查看对话框 -->
    <el-dialog v-model="showDetailDialog" title="票据详情" width="600px">
      <el-descriptions :column="2" border v-if="currentBill">
        <el-descriptions-item label="发票代码">{{ currentBill.invoice_code }}</el-descriptions-item>
        <el-descriptions-item label="发票号码">{{ currentBill.invoice_number }}</el-descriptions-item>
        <el-descriptions-item label="销售方" :span="2">{{ currentBill.seller_name }}</el-descriptions-item>
        <el-descriptions-item label="开票日期">{{ currentBill.invoice_date }}</el-descriptions-item>
        <el-descriptions-item label="金额">{{ formatAmount(currentBill.amount) }}</el-descriptions-item>
        <el-descriptions-item label="税额">{{ formatAmount(currentBill.tax_amount) }}</el-descriptions-item>
        <el-descriptions-item label="价税合计">{{ formatAmount(currentBill.total_amount) }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentBill.process_status)">
            {{ getStatusText(currentBill.process_status) }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { billApi, type Bill } from '../../api/bill'
import { voucherApi } from '../../api/voucher'
import BillDetailDialog from './components/BillDetailDialog.vue'

const loading = ref(false)
const tableData = ref<Bill[]>([])
const showUploadDialog = ref(false)
const showDetailDialog = ref(false)
const showEditDialog = ref(false)
const currentBill = ref<Bill | null>(null)
const currentBillId = ref<string>('')
const uploading = ref(false)
const uploadFile = ref<File | null>(null)

const filterForm = reactive({
  bill_type: '',
  process_status: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await billApi.getList({
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
  filterForm.bill_type = ''
  filterForm.process_status = ''
  fetchData()
}

const formatAmount = (amount?: number) => {
  if (!amount) return '-'
  return `¥${amount.toFixed(2)}`
}

const getStatusType = (status?: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    ocr_pending: 'warning',
    ocr_completed: 'success',
    ocr_failed: 'danger',
    voucher_generated: 'primary'
  }
  return map[status || ''] || 'info'
}

const getStatusText = (status?: string) => {
  const map: Record<string, string> = {
    pending: '待处理',
    ocr_pending: '识别中',
    ocr_completed: '识别完成',
    ocr_failed: '识别失败',
    voucher_generated: '已生成凭证'
  }
  return map[status || ''] || status
}

// 编辑票据
const handleEdit = (row: Bill) => {
  currentBillId.value = row.id
  showEditDialog.value = true
}

// 编辑成功
const handleEditSuccess = () => {
  fetchData()
}

const viewDetail = (row: Bill) => {
  currentBill.value = row
  showDetailDialog.value = true
}

const handleFileChange = (file: any) => {
  uploadFile.value = file.raw
}

const handleUpload = async () => {
  if (!uploadFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  
  uploading.value = true
  try {
    await billApi.upload(uploadFile.value)
    ElMessage.success('上传成功')
    showUploadDialog.value = false
    uploadFile.value = null
    fetchData()
  } finally {
    uploading.value = false
  }
}

const generateVoucher = async (row: Bill) => {
  try {
    await voucherApi.generate([row.id])
    ElMessage.success('凭证生成成功')
    fetchData()
  } catch (error) {
    // 错误已在拦截器处理
  }
}

const handleDelete = async (row: Bill) => {
  try {
    await ElMessageBox.confirm('确定删除该票据吗？', '提示', { type: 'warning' })
    await billApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    // 取消或错误
  }
}

onMounted(fetchData)
</script>

<style scoped>
.bill-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 筛选区域 */
.filter-section {
  margin-bottom: 16px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-item {
  margin-right: 8px;
  margin-bottom: 8px;
}

.filter-item :deep(.el-form-item__label) {
  font-size: 13px;
  padding: 0 4px;
}

.filter-actions {
  margin-left: auto;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}

/* 移动端样式 */
@media (max-width: 768px) {
  .bill-list {
    padding: 12px;
  }
  
  .card-header {
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .card-header span {
    font-size: 16px;
    font-weight: 600;
  }
  
  .filter-form {
    flex-direction: column;
  }
  
  .filter-item {
    width: 100%;
    margin-right: 0;
    margin-bottom: 8px;
  }
  
  .filter-item :deep(.el-select) {
    width: 100%;
  }
  
  .filter-actions {
    width: 100%;
    margin-left: 0;
    display: flex;
    gap: 8px;
  }
  
  .filter-actions .el-button {
    flex: 1;
  }
  
  /* 移动端表格优化 */
  .el-table {
    font-size: 12px;
  }
  
  .el-table .el-table__header-wrapper th,
  .el-table .el-table__body-wrapper td {
    padding: 8px 0;
  }
  
  .el-table .el-table__body tr > td {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 6px 8px;
    min-width: 100%;
  }
  
  /* 操作按钮 */
  .el-table .el-button {
    padding: 4px 8px;
    font-size: 12px;
  }
  
  .el-table .el-button + .el-button {
    margin-left: 8px;
  }
  
  /* 分页 */
  .pagination {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  /* 对话框 */
  .el-dialog {
    width: 95% !important;
    max-width: 100%;
    margin: 10px auto !important;
  }
  
  .el-dialog__header {
    padding: 12px 16px;
  }
  
  .el-dialog__body {
    padding: 16px;
  }
  
  /* 描述列表 */
  .el-descriptions {
    font-size: 13px;
  }
  
  .el-descriptions__label,
  .el-descriptions__content {
    padding: 8px 12px;
  }
  
  /* 移动端上传区域 */
  .el-upload-dragger {
    padding: 20px;
  }
  
  .el-upload__text {
    font-size: 13px;
  }
}

/* 超小屏幕 */
@media (max-width: 480px) {
  .bill-list {
    padding: 8px;
  }
  
  .card-header span {
    font-size: 15px;
  }
  
  .el-table {
    font-size: 11px;
  }
  
  .el-tag {
    font-size: 10px;
    padding: 2px 6px;
  }
  
  .pagination {
    padding: 8px 0;
  }
  
  .el-pagination button,
  .el-pagination .el-pager li {
    min-width: 28px;
    height: 28px;
    line-height: 28px;
    font-size: 12px;
  }
}
</style>
