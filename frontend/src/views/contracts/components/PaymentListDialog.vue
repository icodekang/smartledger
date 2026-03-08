<template>
  <el-dialog v-model="visible" :title="`收费记录 - ${contract?.contract_name || ''}`" width="800px">
    <!-- 统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-statistic title="应收金额" :value="summary.total_amount" prefix="¥" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="已收金额" :value="summary.paid_amount" prefix="¥">
          <template #suffix><el-tag type="success">已收</el-tag></template>
        </el-statistic>
      </el-col>
      <el-col :span="6">
        <el-statistic title="待收金额" :value="summary.pending_amount" prefix="¥">
          <template #suffix><el-tag type="warning">待收</el-tag></template>
        </el-statistic>
      </el-col>
      <el-col :span="6">
        <el-statistic title="逾期金额" :value="summary.overdue_amount" prefix="¥">
          <template #suffix><el-tag type="danger">逾期</el-tag></template>
        </el-statistic>
      </el-col>
    </el-row>

    <!-- 收费记录表 -->
    <el-table :data="payments" border size="small">
      <el-table-column prop="period" label="账期" width="100" />
      <el-table-column prop="amount" label="应收金额" width="120">
        <template #default="{ row }">¥{{ row.amount.toFixed(2) }}</template>
      </el-table-column>
      
      <el-table-column prop="paid_amount" label="已收金额" width="120">
        <template #default="{ row }">¥{{ (row.paid_amount || 0).toFixed(2) }}</template>
      </el-table-column>
      
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="paid_at" label="付款时间" width="150" />
      
      <el-table-column prop="invoice_no" label="发票号" width="120" />
      
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button v-if="row.status !== 'paid'" type="primary" link size="small" @click="handlePay(row)">记录付款</el-button>
          <el-button v-if="!row.invoice_no" type="success" link size="small" @click="handleInvoice(row)">记录开票</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 付款对话框 -->
    <el-dialog v-model="showPayDialog" title="记录付款" width="400px" append-to-body>
      <el-form :model="payForm" label-width="100px">
        <el-form-item label="付款金额" required>
          <el-input-number v-model="payForm.paid_amount" :precision="2" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="付款人">
          <el-input v-model="payForm.paid_by" />
        </el-form-item>
        <el-form-item label="付款方式">
          <el-select v-model="payForm.payment_method" style="width: 100%">
            <el-option label="银行转账" value="银行转账" />
            <el-option label="现金" value="现金" />
            <el-option label="支付宝" value="支付宝" />
            <el-option label="微信" value="微信" />
          </el-select>
        </el-form-item>
        <el-form-item label="交易流水号">
          <el-input v-model="payForm.transaction_no" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPayDialog = false">取消</el-button>
        <el-button type="primary" @click="submitPayment">确认</el-button>
      </template>
    </el-dialog>

    <!-- 开票对话框 -->
    <el-dialog v-model="showInvoiceDialog" title="记录开票" width="400px" append-to-body>
      <el-form :model="invoiceForm" label-width="100px">
        <el-form-item label="发票号码" required>
          <el-input v-model="invoiceForm.invoice_no" />
        </el-form-item>
        <el-form-item label="开票日期" required>
          <el-date-picker v-model="invoiceForm.invoiced_at" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showInvoiceDialog = false">取消</el-button>
        <el-button type="primary" @click="submitInvoice">确认</el-button>
      </template>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { contractApi } from '../../../api/contract'

const props = defineProps<{
  modelValue: boolean
  contract: any
}>()

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

const payments = ref([])
const summary = ref({ total_amount: 0, paid_amount: 0, pending_amount: 0, overdue_amount: 0 })

const showPayDialog = ref(false)
const showInvoiceDialog = ref(false)
const currentPayment = ref<any>(null)

const payForm = ref({ paid_amount: 0, paid_by: '', payment_method: '', transaction_no: '' })
const invoiceForm = ref({ invoice_no: '', invoiced_at: '' })

const fetchPayments = async () => {
  if (!props.contract?.id) return
  const res = await contractApi.getPayments(props.contract.id)
  payments.value = res.data.items
  summary.value = res.data.summary
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = { paid: 'success', pending: 'warning', overdue: 'danger', partial: 'info' }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = { paid: '已付款', pending: '待付款', overdue: '逾期', partial: '部分付款' }
  return map[status] || status
}

const handlePay = (row: any) => {
  currentPayment.value = row
  payForm.value = { paid_amount: row.amount, paid_by: '', payment_method: '', transaction_no: '' }
  showPayDialog.value = true
}

const handleInvoice = (row: any) => {
  currentPayment.value = row
  invoiceForm.value = { invoice_no: '', invoiced_at: new Date().toISOString().split('T')[0] }
  showInvoiceDialog.value = true
}

const submitPayment = async () => {
  await contractApi.recordPayment(currentPayment.value.id, payForm.value)
  ElMessage.success('付款记录成功')
  showPayDialog.value = false
  fetchPayments()
}

const submitInvoice = async () => {
  await contractApi.recordInvoice(currentPayment.value.id, invoiceForm.value)
  ElMessage.success('开票记录成功')
  showInvoiceDialog.value = false
  fetchPayments()
}

watch(() => props.modelValue, (v) => {
  if (v) fetchPayments()
})
</script>

<style scoped>
.stats-row {
  margin-bottom: 20px;
}
</style>
