<template>
  <div class="bill-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>票据管理</span>
          <el-button type="primary" @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon> 上传票据
          </el-button>
        </div>
      </template>
      
      <!-- 筛选 -->
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="票据类型">
          <el-select v-model="filterForm.bill_type" placeholder="全部" clearable>
            <el-option label="增值税发票" value="invoice" />
            <el-option label="收据" value="receipt" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select v-model="filterForm.process_status" placeholder="全部" clearable>
            <el-option label="待处理" value="pending" />
            <el-option label="OCR完成" value="ocr_completed" />
            <el-option label="已生成凭证" value="voucher_generated" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
      
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
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">查看</el-button>
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
    
    <!-- 详情对话框 -->
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

const loading = ref(false)
const tableData = ref<Bill[]>([])
const showUploadDialog = ref(false)
const showDetailDialog = ref(false)
const currentBill = ref<Bill | null>(null)
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

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
