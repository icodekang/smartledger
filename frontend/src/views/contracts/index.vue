<template>
  <div class="contract-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>服务合同管理</span>
          <el-button type="primary" @click="handleCreate">
            <Plus /> 新建合同
          </el-button>
        </div>
      </template>

      <!-- 客户选择 -->
      <el-form :inline="true">
        <el-form-item label="客户">
          <el-select v-model="selectedCustomerId" placeholder="请选择客户" @change="fetchContracts" style="width: 300px">
            <el-option
              v-for="c in customers"
              :key="c.id"
              :label="`${c.code} - ${c.name}`"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <!-- 合同列表 -->
      <el-table :data="contracts" v-loading="loading" border>
        <el-table-column prop="contract_no" label="合同编号" width="130" />
        
        <el-table-column prop="contract_name" label="合同名称" min-width="200" show-overflow-tooltip />
        
        <el-table-column prop="service_type" label="服务类型" width="120" />
        
        <el-table-column label="服务期限" width="200">
          <template #default="{ row }">
            {{ row.start_date }} ~ {{ row.end_date }}
          </template>
        </el-table-column>
        
        <el-table-column label="服务费" width="120">
          <template #default="{ row }">
            ¥{{ row.billing_amount }}/{{ row.billing_cycle === 'monthly' ? '月' : row.billing_cycle === 'quarterly' ? '季' : '年' }}
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">查看</el-button>
            <el-button type="success" link @click="handlePayments(row)">收费记录</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 合同详情对话框 -->
    <ContractDetailDialog
      v-model="showDialog"
      :contract="currentContract"
      :customer-id="selectedCustomerId"
      :is-create="isCreate"
      @success="fetchContracts"
    />

    <!-- 收费记录对话框 -->
    <PaymentListDialog
      v-model="showPaymentDialog"
      :contract="currentContract"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { customerApi } from '../../api/customer'
import { contractApi } from '../../api/contract'
import ContractDetailDialog from './components/ContractDetailDialog.vue'
import PaymentListDialog from './components/PaymentListDialog.vue'

const customers = ref([])
const selectedCustomerId = ref('')
const contracts = ref([])
const loading = ref(false)
const showDialog = ref(false)
const showPaymentDialog = ref(false)
const isCreate = ref(false)
const currentContract = ref(null)

const fetchCustomers = async () => {
  const res = await customerApi.getList({ page_size: 1000 })
  customers.value = res.data.items
  if (customers.value.length > 0 && !selectedCustomerId.value) {
    selectedCustomerId.value = customers.value[0].id
    fetchContracts()
  }
}

const fetchContracts = async () => {
  if (!selectedCustomerId.value) return
  loading.value = true
  try {
    const res = await contractApi.getList(selectedCustomerId.value)
    contracts.value = res.data.items
  } finally {
    loading.value = false
  }
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    active: 'success',
    expired: 'info',
    terminated: 'danger',
    draft: 'warning'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    active: '生效中',
    expired: '已过期',
    terminated: '已终止',
    draft: '草稿'
  }
  return map[status] || status
}

const handleCreate = () => {
  isCreate.value = true
  currentContract.value = null
  showDialog.value = true
}

const handleView = (row: any) => {
  isCreate.value = false
  currentContract.value = row
  showDialog.value = true
}

const handlePayments = (row: any) => {
  currentContract.value = row
  showPaymentDialog.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定删除合同 "${row.contract_name}" 吗？`, '确认删除', { type: 'warning' })
    await contractApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchContracts()
  } catch (error) {
    // 取消
  }
}

onMounted(fetchCustomers)
</script>

<style scoped>
.contract-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
