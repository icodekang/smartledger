<template>
  <el-dialog
    v-model="visible"
    title="导入银行流水"
    width="800px"
    :close-on-click-modal="false"
    @closed="handleClose"
  >
    <!-- 步骤条 -->
    <el-steps :active="currentStep" finish-status="success" class="steps">
      <el-step title="上传文件" />
      <el-step title="预览确认" />
      <el-step title="导入完成" />
    </el-steps>

    <!-- Step 1: 上传文件 -->
    <div v-if="currentStep === 0" class="step-content">
      <el-form :model="uploadForm" label-position="top">
        <el-form-item label="选择银行">
          <el-select v-model="uploadForm.bankType" placeholder="自动检测" style="width: 100%">
            <el-option label="自动检测" value="auto" />
            <el-option label="工商银行" value="icbc" />
            <el-option label="建设银行" value="ccb" />
            <el-option label="农业银行" value="abc" />
            <el-option label="中国银行" value="boc" />
            <el-option label="交通银行" value="comm" />
            <el-option label="招商银行" value="cmb" />
            <el-option label="其他银行" value="other" />
          </el-select>
        </el-form-item>

        <el-form-item label="上传文件">
          <el-upload
            ref="uploadRef"
            drag
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            accept=".csv,.xlsx,.xls"
            class="upload-area"
          >
            <el-icon class="upload-icon"><Upload /></el-icon>
            <div class="upload-text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="upload-tip">
                支持 CSV、Excel 格式，文件大小不超过 10MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
    </div>

    <!-- Step 2: 预览确认 -->
    <div v-if="currentStep === 1" class="step-content">
      <div class="preview-summary">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-value">{{ previewData.total_count }}</div>
              <div class="summary-label">总行数</div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-value">{{ previewData.valid_count }}</div>
              <div class="summary-label">有效数据</div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-value">{{ previewData.amount_summary?.income?.toFixed(2) }}</div>
              <div class="summary-label">收入合计</div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-value">{{ previewData.amount_summary?.expense?.toFixed(2) }}</div>
              <div class="summary-label">支出合计</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 错误提示 -->
      <el-alert
        v-if="previewData.error_count > 0"
        :title="`有 ${previewData.error_count} 行数据格式错误，将被跳过`"
        type="warning"
        :closable="false"
        class="error-alert"
      />

      <!-- 预览表格 -->
      <el-table
        :data="previewData.preview"
        height="300"
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="row_number" label="行号" width="80" />
        
        <el-table-column prop="transaction_date" label="日期" width="120" />
        
        <el-table-column label="金额" width="120" align="right">
          <template #default="{ row }">
            <span :class="row.amount >= 0 ? 'positive' : 'negative'">
              {{ row.amount >= 0 ? '+' : '' }}{{ row.amount.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column prop="counterparty_name" label="对方户名" min-width="150" show-overflow-tooltip />
        
        <el-table-column prop="summary" label="摘要" min-width="150" show-overflow-tooltip />
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_duplicate" type="warning" size="small">重复</el-tag>
            <el-tag v-else type="success" size="small">正常</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Step 3: 导入结果 -->
    <div v-if="currentStep === 2" class="step-content">
      <div class="result-container">
        <el-result
          :icon="importResult.imported_count > 0 ? 'success' : 'warning'"
          :title="importResult.imported_count > 0 ? '导入成功' : '导入完成'"
          :sub-title="`成功导入 ${importResult.imported_count} 条数据，跳过 ${importResult.skipped_count} 条`"
        >
          <template #extra>
            <el-button type="primary" @click="handleClose">查看流水列表</el-button>
            <el-button @click="handleImportAnother">继续导入</el-button>
          </template>
        </el-result>
      </div>
    </div>

    <template #footer>
      <div v-if="currentStep === 0">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploading">下一步</el-button>
      </div>
      
      <div v-if="currentStep === 1">
        <el-button @click="currentStep = 0">上一步</el-button>
        <el-button type="primary" @click="handleImport" :loading="importing">
          导入{{ selectedRows.length > 0 ? `(${selectedRows.length}条)` : '(全部)' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import { bankFlowApi, type UploadPreviewResponse } from '../../../api/bank-flow'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 步骤控制
const currentStep = ref(0)

// 上传表单
const uploadForm = ref({
  bankType: 'auto',
  file: null as File | null
})

const uploadRef = ref()
const uploading = ref(false)
const importing = ref(false)

// 预览数据
const previewData = ref<UploadPreviewResponse>({
  preview: [],
  total_count: 0,
  valid_count: 0,
  error_count: 0,
  errors: [],
  date_range: { start: '', end: '' },
  amount_summary: { income: 0, expense: 0 },
  detected_bank_type: ''
})

const selectedRows = ref<any[]>([])

// 导入结果
const importResult = ref({
  imported_count: 0,
  skipped_count: 0,
  import_id: ''
})

// 文件变化
const handleFileChange = (file: any) => {
  uploadForm.value.file = file.raw
}

// 选择变化
const handleSelectionChange = (selection: any[]) => {
  selectedRows.value = selection
}

// 上传并解析
const handleUpload = async () => {
  if (!uploadForm.value.file) {
    ElMessage.warning('请选择文件')
    return
  }
  
  uploading.value = true
  try {
    const res = await bankFlowApi.upload(uploadForm.value.file, uploadForm.value.bankType)
    previewData.value = res.data
    currentStep.value = 1
    ElMessage.success('文件解析成功')
  } catch (error) {
    console.error('上传失败:', error)
  } finally {
    uploading.value = false
  }
}

// 确认导入
const handleImport = async () => {
  importing.value = true
  try {
    const selectedIndices = selectedRows.value.length > 0 
      ? selectedRows.value.map(row => row.index)
      : undefined
    
    const res = await bankFlowApi.import({
      preview_data: previewData.value.preview,
      selected_indices: selectedIndices
    })
    
    importResult.value = res.data
    currentStep.value = 2
    ElMessage.success('导入成功')
    emit('success')
  } catch (error) {
    console.error('导入失败:', error)
  } finally {
    importing.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  reset()
}

// 继续导入
const handleImportAnother = () => {
  reset()
  currentStep.value = 0
}

// 重置状态
const reset = () => {
  currentStep.value = 0
  uploadForm.value = { bankType: 'auto', file: null }
  previewData.value = {
    preview: [],
    total_count: 0,
    valid_count: 0,
    error_count: 0,
    errors: [],
    date_range: { start: '', end: '' },
    amount_summary: { income: 0, expense: 0 },
    detected_bank_type: ''
  }
  selectedRows.value = []
  importResult.value = { imported_count: 0, skipped_count: 0, import_id: '' }
  
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 监听对话框打开
watch(() => props.modelValue, (val) => {
  if (val) {
    reset()
  }
})
</script>

<style scoped>
.steps {
  margin-bottom: 30px;
}

.step-content {
  min-height: 300px;
}

.upload-area {
  width: 100%;
}

.upload-icon {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 16px;
}

.upload-text {
  font-size: 14px;
  color: #606266;
}

.upload-text em {
  color: #409eff;
  font-style: normal;
  cursor: pointer;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.preview-summary {
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.summary-item {
  text-align: center;
}

.summary-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.summary-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.error-alert {
  margin-bottom: 16px;
}

.positive {
  color: #67c23a;
}

.negative {
  color: #f56c6c;
}

.result-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}
</style>
