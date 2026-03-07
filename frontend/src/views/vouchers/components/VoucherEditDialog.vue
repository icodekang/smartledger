<template>
  <el-dialog
    v-model="visible"
    title="编辑凭证"
    width="900px"
    :close-on-click-modal="false"
  >
    <div v-loading="loading" class="voucher-editor">
      <!-- 基本信息 -->
      <el-form :model="form" label-position="top">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="凭证日期">
              <el-date-picker
                v-model="form.voucher_date"
                type="date"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="会计期间">
              <el-input v-model="form.period" disabled />
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="凭证号">
              <el-input v-model="form.voucher_no" disabled />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="摘要">
          <el-input v-model="form.summary" placeholder="输入凭证摘要" />
        </el-form-item>
      </el-form>

      <!-- 分录明细 -->
      <div class="items-section">
        <div class="section-header">
          <span class="section-title">分录明细</span>
          <el-button type="primary" size="small" @click="addItem">
            <Plus /> 添加行
          </el-button>
        </div>

        <el-table :data="form.items" border size="small">
          <el-table-column type="index" label="行号" width="60" />
          
          <el-table-column label="科目代码" width="120">
            <template #default="{ row }">
              <el-input v-model="row.subject_code" size="small" placeholder="科目代码" />
            </template>
          </el-table-column>
          
          <el-table-column label="科目名称" width="150">
            <template #default="{ row }">
              <el-input v-model="row.subject_name" size="small" placeholder="科目名称" />
            </template>
          </el-table-column>
          
          <el-table-column label="摘要" min-width="150">
            <template #default="{ row }">
              <el-input v-model="row.summary" size="small" placeholder="明细摘要" />
            </template>
          </el-table-column>
          
          <el-table-column label="借方" width="140" align="right">
            <template #default="{ row }">
              <el-input-number
                v-model="row.debit_amount"
                size="small"
                :precision="2"
                :min="0"
                style="width: 100%"
                @change="onDebitChange(row)"
              />
            </template>
          </el-table-column>
          
          <el-table-column label="贷方" width="140" align="right">
            <template #default="{ row }">
              <el-input-number
                v-model="row.credit_amount"
                size="small"
                :precision="2"
                :min="0"
                style="width: 100%"
                @change="onCreditChange(row)"
              />
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ $index }">
              <el-button type="danger" link size="small" @click="removeItem($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 合计行 -->
        <div class="totals-row" :class="{ balanced: isBalanced }">
          <span class="totals-label">合计:</span>
          <span class="totals-debit">借方: {{ formatAmount(totalDebit) }}</span>
          <span class="totals-credit">贷方: {{ formatAmount(totalCredit) }}</span>
          <el-tag :type="isBalanced ? 'success' : 'danger'" size="small">
            {{ isBalanced ? '✅ 借贷平衡' : `❌ 差额: ${formatAmount(difference)}` }}
          </el-tag>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { voucherApi, type Voucher, type VoucherItem } from '../../api/voucher'

const props = defineProps<{
  modelValue: boolean
  voucherId?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const saving = ref(false)

const form = ref({
  voucher_no: '',
  voucher_date: '',
  period: '',
  summary: '',
  items: [] as VoucherItem[]
})

// 计算合计
const totalDebit = computed(() => {
  return form.value.items.reduce((sum, item) => sum + (item.debit_amount || 0), 0)
})

const totalCredit = computed(() => {
  return form.value.items.reduce((sum, item) => sum + (item.credit_amount || 0), 0)
})

const isBalanced = computed(() => {
  return Math.abs(totalDebit.value - totalCredit.value) < 0.01 && totalDebit.value > 0
})

const difference = computed(() => {
  return totalDebit.value - totalCredit.value
})

// 借贷互斥
const onDebitChange = (row: VoucherItem) => {
  if (row.debit_amount > 0) {
    row.credit_amount = 0
  }
}

const onCreditChange = (row: VoucherItem) => {
  if (row.credit_amount > 0) {
    row.debit_amount = 0
  }
}

// 获取详情
const fetchDetail = async () => {
  if (!props.voucherId) return
  
  loading.value = true
  try {
    const res = await voucherApi.getDetail(props.voucherId)
    const data = res.data
    
    form.value = {
      voucher_no: data.voucher_no,
      voucher_date: data.voucher_date,
      period: data.period,
      summary: data.summary,
      items: data.items || []
    }
  } catch (error) {
    console.error('获取详情失败:', error)
  } finally {
    loading.value = false
  }
}

// 添加行
const addItem = () => {
  form.value.items.push({
    line_no: form.value.items.length + 1,
    subject_code: '',
    subject_name: '',
    summary: '',
    debit_amount: 0,
    credit_amount: 0
  })
}

// 删除行
const removeItem = (index: number) => {
  form.value.items.splice(index, 1)
  // 重新编号
  form.value.items.forEach((item, idx) => {
    item.line_no = idx + 1
  })
}

// 保存
const handleSave = async () => {
  // 校验
  if (form.value.items.length < 2) {
    ElMessage.error('凭证至少需要两条分录')
    return
  }
  
  if (!isBalanced.value) {
    ElMessage.error('借贷不平衡，请检查分录金额')
    return
  }
  
  // 校验每条分录
  for (let i = 0; i < form.value.items.length; i++) {
    const item = form.value.items[i]
    if (item.debit_amount > 0 && item.credit_amount > 0) {
      ElMessage.error(`第${i + 1}行：借贷方不能同时有金额`)
      return
    }
    if (item.debit_amount === 0 && item.credit_amount === 0) {
      ElMessage.error(`第${i + 1}行：借贷方必须输入一个金额`)
      return
    }
  }
  
  saving.value = true
  try {
    await voucherApi.update(props.voucherId!, {
      voucher_date: form.value.voucher_date,
      summary: form.value.summary,
      items: form.value.items
    })
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

// 格式化金额
const formatAmount = (amount: number) => {
  return amount.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// 监听打开
watch(() => props.modelValue, (val) => {
  if (val && props.voucherId) {
    fetchDetail()
  }
})
</script>

<style scoped>
.voucher-editor {
  padding: 0 10px;
}

.items-section {
  margin-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.totals-row {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 20px;
  padding: 12px 20px;
  background: #f5f7fa;
  border: 1px solid #ebeef5;
  border-top: none;
}

.totals-row.balanced {
  background: #f0fff4;
}

.totals-label {
  font-weight: 600;
  color: #606266;
}

.totals-debit,
.totals-credit {
  font-family: monospace;
  font-size: 14px;
}

.totals-debit {
  color: #67c23a;
}

.totals-credit {
  color: #f56c6c;
}
</style>
