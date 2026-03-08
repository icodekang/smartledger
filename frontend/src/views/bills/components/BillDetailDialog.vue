<template>
  <el-dialog
    v-model="visible"
    title="票据详情"
    width="900px"
    :close-on-click-modal="false"
    class="bill-detail-dialog"
  >
    <div v-loading="loading" class="detail-content">
      <!-- 左右布局 -->
      <div class="detail-layout">
        <!-- 左侧图片 -->
        <div class="image-section">
          <div v-if="billData.image_url" class="image-wrapper">
            <el-image
              :src="billData.image_url"
              :preview-src-list="[billData.image_url]"
              fit="contain"
              class="bill-image"
            />
          </div>
          <div v-else class="no-image">
            <el-empty description="暂无图片" />
          </div>
          
          <div class="image-actions">
            <el-button v-if="billData.image_url" type="primary" link @click="previewImage">
              <View /> 查看原图
            </el-button>
          </div>
        </div>

        <!-- 右侧表单 -->
        <div class="form-section">
          <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
            <!-- 基本信息 -->
            <div class="section-title">基本信息</div>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="发票代码" prop="invoice_code">
                  <el-input v-model="form.invoice_code" placeholder="请输入发票代码" />
                </el-form-item>
              </el-col>
              
              <el-col :span="12">
                <el-form-item label="发票号码" prop="invoice_number">
                  <el-input v-model="form.invoice_number" placeholder="请输入发票号码" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="开票日期" prop="invoice_date">
                  <el-date-picker
                    v-model="form.invoice_date"
                    type="date"
                    placeholder="选择日期"
                    value-format="YYYY-MM-DD"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 金额信息 -->
            <div class="section-title">金额信息</div>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="金额" prop="amount">
                  <el-input-number
                    v-model="form.amount"
                    :precision="2"
                    :min="0"
                    style="width: 100%"
                    @change="calculateTax"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="税额">
                  <el-input-number
                    v-model="form.tax_amount"
                    :precision="2"
                    :min="0"
                    style="width: 100%"
                    @change="calculateTotal"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="价税合计">
                  <el-input-number
                    v-model="form.total_amount"
                    :precision="2"
                    :min="0"
                    style="width: 100%"
                    disabled
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 销售方信息 -->
            <div class="section-title">销售方信息</div>
            <el-form-item label="名称" prop="seller_name">
              <el-input v-model="form.seller_name" placeholder="请输入销售方名称" />
            </el-form-item>
            
            <el-form-item label="税号">
              <el-input v-model="form.seller_tax_no" placeholder="请输入销售方税号" />
            </el-form-item>

            <!-- 购买方信息 -->
            <div class="section-title">购买方信息</div>
            <el-form-item label="名称">
              <el-input v-model="form.buyer_name" placeholder="请输入购买方名称" />
            </el-form-item>
            
            <el-form-item label="税号">
              <el-input v-model="form.buyer_tax_no" placeholder="请输入购买方税号" />
            </el-form-item>
          </el-form>

          <!-- 商品明细 -->
          <div class="section-title">商品明细</div>
          <div class="items-section">
            <el-table :data="form.items" border size="small">
              <el-table-column type="index" label="行号" width="60" />
              
              <el-table-column label="商品名称" min-width="150">
                <template #default="{ row, $index }">
                  <el-input v-model="row.name" size="small" placeholder="商品名称" />
                </template>
              </el-table-column>
              
              <el-table-column label="规格" width="100">
                <template #default="{ row }">
                  <el-input v-model="row.spec" size="small" />
                </template>
              </el-table-column>
              
              <el-table-column label="数量" width="100">
                <template #default="{ row }">
                  <el-input-number v-model="row.quantity" size="small" :precision="2" :min="0" />
                </template>
              </el-table-column>
              
              <el-table-column label="单价" width="120">
                <template #default="{ row }">
                  <el-input-number v-model="row.unit_price" size="small" :precision="2" :min="0" />
                </template>
              </el-table-column>
              
              <el-table-column label="金额" width="120">
                <template #default="{ row }">
                  <el-input-number v-model="row.amount" size="small" :precision="2" :min="0" />
                </template>
              </el-table-column>
              
              <el-table-column label="税率" width="80">
                <template #default="{ row }">
                  <el-select v-model="row.tax_rate" size="small" style="width: 70px">
                    <el-option label="0%" value="0%" />
                    <el-option label="1%" value="1%" />
                    <el-option label="3%" value="3%" />
                    <el-option label="6%" value="6%" />
                    <el-option label="9%" value="9%" />
                    <el-option label="13%" value="13%" />
                  </el-select>
                </template>
              </el-table-column>
              
              <el-table-column label="操作" width="80" fixed="right">
                <template #default="{ $index }">
                  <el-button type="danger" link size="small" @click="removeItem($index)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            
            <div class="add-item">
              <el-button type="primary" link @click="addItem">
                <Plus /> 添加明细行
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSave" :loading="saving">保存修改</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { View, Plus } from '@element-plus/icons-vue'
import { billApi, type BillDetail, type BillItem } from '../../../api/bill'
import BillImageViewer from '../../../../components/BillImageViewer.vue'

const props = defineProps<{
  modelValue: boolean
  billId?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 其他代码保持不变...

// 加载状态
const loading = ref(false)
const saving = ref(false)

// 原始数据
const billData = ref<BillDetail>({
  id: '',
  items: [],
  process_status: '',
  created_at: ''
})

// 表单数据
const form = ref({
  invoice_code: '',
  invoice_number: '',
  invoice_date: '',
  invoice_type: '',
  amount: undefined as number | undefined,
  tax_amount: undefined as number | undefined,
  total_amount: undefined as number | undefined,
  seller_name: '',
  seller_tax_no: '',
  seller_address: '',
  seller_bank: '',
  buyer_name: '',
  buyer_tax_no: '',
  buyer_address: '',
  buyer_bank: '',
  items: [] as BillItem[]
})

// 表单校验规则
const rules = {
  invoice_code: [
    { pattern: /^\d{10,12}$/, message: '发票代码应为10-12位数字', trigger: 'blur' }
  ],
  invoice_number: [
    { required: true, message: '请输入发票号码', trigger: 'blur' },
    { pattern: /^[\da-zA-Z]{8,20}$/, message: '发票号码格式不正确', trigger: 'blur' }
  ],
  invoice_date: [
    { required: true, message: '请选择开票日期', trigger: 'change' }
  ],
  seller_name: [
    { required: true, message: '请输入销售方名称', trigger: 'blur' }
  ]
}

const formRef = ref()

// 获取详情
const fetchDetail = async () => {
  if (!props.billId) return
  
  loading.value = true
  try {
    const res = await billApi.getDetail(props.billId)
    billData.value = res.data
    
    // 填充表单
    form.value = {
      invoice_code: res.data.invoice_code || '',
      invoice_number: res.data.invoice_number || '',
      invoice_date: res.data.invoice_date || '',
      invoice_type: res.data.invoice_type || '',
      amount: res.data.amount,
      tax_amount: res.data.tax_amount,
      total_amount: res.data.total_amount,
      seller_name: res.data.seller_name || '',
      seller_tax_no: res.data.seller_tax_no || '',
      seller_address: res.data.seller_address || '',
      seller_bank: res.data.seller_bank || '',
      buyer_name: res.data.buyer_name || '',
      buyer_tax_no: res.data.buyer_tax_no || '',
      buyer_address: res.data.buyer_address || '',
      buyer_bank: res.data.buyer_bank || '',
      items: res.data.items || []
    }
  } catch (error) {
    console.error('获取详情失败:', error)
  } finally {
    loading.value = false
  }
}

// 计算税额和合计
const calculateTax = () => {
  const amount = form.value.amount || 0
  // 默认税率13%
  const taxRate = 0.13
  form.value.tax_amount = Math.round(amount * taxRate * 100) / 100
  calculateTotal()
}

const calculateTotal = () => {
  const amount = form.value.amount || 0
  const tax = form.value.tax_amount || 0
  form.value.total_amount = Math.round((amount + tax) * 100) / 100
}

// 添加明细行
const addItem = () => {
  form.value.items.push({
    name: '',
    spec: '',
    unit: '',
    quantity: 1,
    unit_price: 0,
    amount: 0,
    tax_rate: '13%',
    tax_amount: 0
  })
}

// 删除明细行
const removeItem = (index: number) => {
  form.value.items.splice(index, 1)
}

// 预览图片
const previewImage = () => {
  if (billData.value.image_url) {
    window.open(billData.value.image_url, '_blank')
  }
}

// 保存
const handleSave = async () => {
  if (!formRef.value) return
  
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  saving.value = true
  try {
    // 更新基本信息
    await billApi.update(props.billId!, {
      invoice_code: form.value.invoice_code,
      invoice_number: form.value.invoice_number,
      invoice_date: form.value.invoice_date,
      amount: form.value.amount,
      tax_amount: form.value.tax_amount,
      total_amount: form.value.total_amount,
      seller_name: form.value.seller_name,
      seller_tax_no: form.value.seller_tax_no,
      seller_address: form.value.seller_address,
      seller_bank: form.value.seller_bank,
      buyer_name: form.value.buyer_name,
      buyer_tax_no: form.value.buyer_tax_no,
      buyer_address: form.value.buyer_address,
      buyer_bank: form.value.buyer_bank
    })
    
    // 更新明细
    await billApi.updateItems(props.billId!, form.value.items)
    
    ElMessage.success('保存成功')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    saving.value = false
  }
}

// 关闭
const handleClose = () => {
  visible.value = false
}

// 监听对话框打开
watch(() => props.modelValue, (val) => {
  if (val && props.billId) {
    fetchDetail()
  }
})
</script>

<style scoped>
.bill-detail-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.detail-content {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-layout {
  display: flex;
  gap: 20px;
  padding: 20px;
}

.image-section {
  width: 300px;
  flex-shrink: 0;
}

.image-wrapper {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  background: #f5f7fa;
}

.bill-image {
  width: 100%;
  height: 400px;
}

.no-image {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 4px;
}

.image-actions {
  margin-top: 12px;
  text-align: center;
}

.form-section {
  flex: 1;
  min-width: 0;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 20px 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.section-title:first-child {
  margin-top: 0;
}

.items-section {
  margin-top: 16px;
}

.add-item {
  margin-top: 12px;
  text-align: center;
}

@media (max-width: 768px) {
  .detail-layout {
    flex-direction: column;
  }
  
  .image-section {
    width: 100%;
  }
}
</style>
