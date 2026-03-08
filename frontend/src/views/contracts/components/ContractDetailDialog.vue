<template>
  <el-dialog v-model="visible" :title="isCreate ? '新建合同' : '合同详情'" width="700px">
    <el-form :model="form" label-width="100px">
      <el-form-item label="合同名称" required>
        <el-input v-model="form.contract_name" placeholder="请输入合同名称" />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="开始日期" required>
            <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="结束日期" required>
            <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="服务类型">
        <el-select v-model="form.service_type" style="width: 100%">
          <el-option label="代理记账" value="代理记账" />
          <el-option label="税务咨询" value="税务咨询" />
          <el-option label="财务顾问" value="财务顾问" />
        </el-select>
      </el-form-item>

      <el-form-item label="服务内容">
        <el-input v-model="form.service_content" type="textarea" :rows="3" />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="计费周期">
            <el-select v-model="form.billing_cycle" style="width: 100%">
              <el-option label="按月" value="monthly" />
              <el-option label="按季" value="quarterly" />
              <el-option label="按年" value="yearly" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="计费金额">
            <el-input-number v-model="form.billing_amount" :precision="2" :min="0" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="备注">
        <el-input v-model="form.remark" type="textarea" :rows="2" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { contractApi } from '../../../api/contract'

const props = defineProps<{
  modelValue: boolean
  contract: any
  customerId: string
  isCreate: boolean
}>()

const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

const form = ref({
  contract_name: '',
  start_date: '',
  end_date: '',
  service_type: '代理记账',
  service_content: '',
  billing_cycle: 'monthly',
  billing_amount: 500,
  remark: ''
})

const saving = ref(false)

const handleSave = async () => {
  if (!form.value.contract_name || !form.value.start_date || !form.value.end_date) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  saving.value = true
  try {
    await contractApi.create(props.customerId, form.value)
    ElMessage.success('创建成功')
    emit('success')
    visible.value = false
  } catch (error) {
    console.error(error)
  } finally {
    saving.value = false
  }
}

watch(() => props.modelValue, (v) => {
  if (v && props.isCreate) {
    form.value = {
      contract_name: '',
      start_date: '',
      end_date: '',
      service_type: '代理记账',
      service_content: '',
      billing_cycle: 'monthly',
      billing_amount: 500,
      remark: ''
    }
  }
})
</script>
