<template>
  <div class="subject-balance">
    <div class="page-header">
      <h2>科目余额表</h2>
      <div class="header-actions">
        <el-select v-model="selectedCustomerId" placeholder="选择客户" style="width: 200px">
          <el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-date-picker
          v-model="selectedPeriod"
          type="month"
          placeholder="选择月份"
          value-format="YYYY-MM"
          style="width: 150px"
        />
        <el-input v-model="searchKeyword" placeholder="搜索科目" clearable style="width: 200px" />
        <el-button type="primary" @click="fetchData">
          <el-icon><Search /></el-icon>查询
        </el-button>
        <el-button type="success" @click="exportReport">
          <el-icon><Download /></el-icon>导出
        </el-button>
      </div>
    </div>

    <div v-loading="loading">
      <div class="report-header">
        <h3>科目余额表</h3>
        <p>{{ selectedCustomerName }} | 账期: {{ selectedPeriod }} | 单位: 元</p>
      </div>

      <!-- 试算平衡 -->
      <el-card v-if="subjectData" class="balance-check">
        <template #header>
          <span>试算平衡</span>
        </template>
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="check-item">
              <label>借方合计</label>
              <div class="amount">{{ formatAmount(subjectData.total?.debit) }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="check-item">
              <label>贷方合计</label>
              <div class="amount">{{ formatAmount(subjectData.total?.credit) }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="check-item">
              <label>平衡状态</label>
              <div class="status">
                <el-tag :type="subjectData.is_balanced ? 'success' : 'danger'" size="large">
                  {{ subjectData.is_balanced ? '✓ 平衡' : '✗ 不平衡' }}
                </el-tag>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 科目余额表 -->
      <el-card v-if="subjectData" class="subject-table">
        <template #header>
          <span>科目明细 ({{ filteredSubjects.length }} 条)</span>
        </template>
        <el-table :data="filteredSubjects" stripe border>
          <el-table-column prop="subject_code" label="科目代码" width="120" sortable />
          <el-table-column prop="subject_name" label="科目名称" min-width="180" />
          
          <!-- 本期发生额 -->
          <el-table-column label="本期发生额" align="center">
            <el-table-column prop="debit" label="借方" width="120" align="right">
              <template #default="{ row }">
                {{ row.debit > 0 ? formatAmount(row.debit) : '' }}
              </template>
            </el-table-column>
            <el-table-column prop="credit" label="贷方" width="120" align="right">
              <template #default="{ row }">
                {{ row.credit > 0 ? formatAmount(row.credit) : '' }}
              </template>
            </el-table-column>
          </el-table-column>

          <!-- 余额 -->
          <el-table-column label="余额" align="center">
            <el-table-column prop="balance" label="金额" width="120" align="right">
              <template #default="{ row }">
                <span :class="row.direction === '借' ? '' : 'credit-balance'">
                  {{ formatAmount(Math.abs(row.balance)) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="direction" label="方向" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.direction === '借' ? 'primary' : 'warning'" size="small">
                  {{ row.direction }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 空状态 -->
      <el-empty v-if="!loading && !subjectData" description="请选择客户和账期查询数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Download } from '@element-plus/icons-vue'
import { reportApi } from '@/api/report'
import { customerApi } from '@/api/customer'

const loading = ref(false)
const selectedCustomerId = ref('')
const selectedPeriod = ref(new Date().toISOString().slice(0, 7))
const searchKeyword = ref('')
const customers = ref<any[]>([])
const subjectData = ref<any>(null)

const selectedCustomerName = computed(() => {
  const customer = customers.value.find(c => c.id === selectedCustomerId.value)
  return customer?.name || ''
})

// 过滤
const filteredSubjects = computed(() => {
  if (!subjectData.value?.items) return []
  const items = subjectData.value.items
  if (!searchKeyword.value) return items
  const keyword = searchKeyword.value.toLowerCase()
  return items.filter((s: any) => 
    s.subject_code.toLowerCase().includes(keyword) || 
    s.subject_name.toLowerCase().includes(keyword)
  )
})

const fetchCustomers = async () => {
  try {
    const res = await customerApi.getList({ page_size: 1000 })
    customers.value = res.data.items || []
    if (customers.value.length > 0) {
      selectedCustomerId.value = customers.value[0].id
      fetchData()
    }
  } catch (error) {
    console.error('获取客户列表失败', error)
  }
}

const fetchData = async () => {
  if (!selectedCustomerId.value || !selectedPeriod.value) {
    ElMessage.warning('请选择客户和账期')
    return
  }
  
  loading.value = true
  try {
    const res = await reportApi.getSubjectBalance(selectedCustomerId.value, selectedPeriod.value)
    subjectData.value = res.data
  } catch (error) {
    console.error('获取科目余额表失败', error)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const formatAmount = (amount: number | undefined) => {
  if (amount === undefined || amount === null) return '¥0.00'
  return '¥' + amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const exportReport = () => {
  if (!subjectData.value) {
    ElMessage.warning('请先查询数据')
    return
  }
  
  const headers = ['科目代码', '科目名称', '借方发生额', '贷方发生额', '余额', '方向']
  const rows = subjectData.value.items.map((item: any) => [
    item.subject_code,
    item.subject_name,
    item.debit?.toFixed(2) || '0.00',
    item.credit?.toFixed(2) || '0.00',
    Math.abs(item.balance).toFixed(2),
    item.direction
  ])
  
  const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n')
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `科目余额表_${selectedPeriod.value}.csv`
  link.click()
  
  ElMessage.success('导出成功')
}

onMounted(fetchCustomers)
</script>

<style scoped>
.subject-balance {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.report-header {
  text-align: center;
  margin-bottom: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.report-header h3 {
  margin: 0 0 10px;
  font-size: 24px;
}

.report-header p {
  margin: 0;
  color: #909399;
}

.balance-check {
  margin-bottom: 20px;
}

.check-item {
  text-align: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.check-item label {
  display: block;
  color: #909399;
  font-size: 14px;
  margin-bottom: 8px;
}

.check-item .amount {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.check-item .status {
  margin-top: 5px;
}

.subject-table {
  margin-top: 20px;
}

.credit-balance {
  color: #E6A23C;
}
</style>
