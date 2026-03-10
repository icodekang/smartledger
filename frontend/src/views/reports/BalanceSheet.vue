<template>
  <div class="balance-sheet">
    <div class="page-header">
      <h2>资产负债表</h2>
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
        <el-button type="primary" @click="fetchData">
          <el-icon><Search /></el-icon>查询
        </el-button>
        <el-button type="success" @click="exportReport">
          <el-icon><Download /></el-icon>导出
        </el-button>
      </div>
    </div>

    <div v-loading="loading">
      <!-- 表头信息 -->
      <div class="report-header">
        <h3>资产负债表</h3>
        <p>{{ selectedCustomerName }} | 账期: {{ selectedPeriod }} | 单位: 元</p>
      </div>

      <!-- 平衡校验 -->
      <el-alert
        v-if="balanceData"
        :title="balanceData.balance_check ? '✓ 借贷平衡' : '✗ 借贷不平衡'"
        :type="balanceData.balance_check ? 'success' : 'error'"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      />

      <!-- 资产 -->
      <el-card class="section">
        <template #header>
          <span class="section-title">一、资产 (合计: {{ formatAmount(balanceData?.assets?.total) }})</span>
        </template>
        
        <!-- 流动资产 -->
        <div class="subsection">
          <div class="subsection-title">流动资产</div>
          <el-table :data="currentAssets" :show-header="false" stripe>
            <el-table-column prop="subject_name" label="项目" />
            <el-table-column prop="balance" label="期末余额" width="150" align="right">
              <template #default="{ row }">
                {{ formatAmount(row.balance) }}
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 非流动资产 -->
        <div class="subsection">
          <div class="subsection-title">非流动资产</div>
          <el-table :data="nonCurrentAssets" :show-header="false" stripe>
            <el-table-column prop="subject_name" label="项目" />
            <el-table-column prop="balance" label="期末余额" width="150" align="right">
              <template #default="{ row }">
                {{ formatAmount(row.balance) }}
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 资产总计 -->
        <div class="grand-total">
          <span>资产总计</span>
          <span>{{ formatAmount(balanceData?.assets?.total) }}</span>
        </div>
      </el-card>

      <!-- 负债 -->
      <el-card class="section">
        <template #header>
          <span class="section-title">二、负债 (合计: {{ formatAmount(balanceData?.liabilities?.total) }})</span>
        </template>

        <el-table :data="liabilities" :show-header="false" stripe>
          <el-table-column prop="subject_name" label="项目" />
          <el-table-column prop="balance" label="期末余额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(Math.abs(row.balance)) }}</template>
          </el-table-column>
        </el-table>

        <div class="grand-total">
          <span>负债合计</span>
          <span>{{ formatAmount(balanceData?.liabilities?.total) }}</span>
        </div>
      </el-card>

      <!-- 所有者权益 -->
      <el-card class="section">
        <template #header>
          <span class="section-title">三、所有者权益 (合计: {{ formatAmount(balanceData?.equity?.total) }})</span>
        </template>

        <el-table :data="equity" :show-header="false" stripe>
          <el-table-column prop="subject_name" label="项目" />
          <el-table-column prop="balance" label="期末余额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.balance) }}</template>
          </el-table-column>
        </el-table>

        <div class="grand-total">
          <span>所有者权益合计</span>
          <span>{{ formatAmount(balanceData?.equity?.total) }}</span>
        </div>
      </el-card>

      <!-- 空状态 -->
      <el-empty v-if="!loading && !balanceData" description="请选择客户和账期查询数据" />
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
const customers = ref<any[]>([])
const balanceData = ref<any>(null)

const selectedCustomerName = computed(() => {
  const customer = customers.value.find(c => c.id === selectedCustomerId.value)
  return customer?.name || ''
})

// 流动资产（科目代码以1开头，且为流动资产）
const currentAssets = computed(() => {
  if (!balanceData.value?.assets?.items) return []
  return balanceData.value.assets.items.filter((item: any) => {
    const code = item.subject_code
    // 1001-1003 货币资金, 1121-1231 应收款项, 1401-1408 存货等流动资产
    return code.startsWith('1001') || code.startsWith('1002') || 
           code.startsWith('112') || code.startsWith('122') ||
           code.startsWith('123') || code.startsWith('140')
  })
})

// 非流动资产（固定资产、无形资产等）
const nonCurrentAssets = computed(() => {
  if (!balanceData.value?.assets?.items) return []
  return balanceData.value.assets.items.filter((item: any) => {
    const code = item.subject_code
    return code.startsWith('150') || code.startsWith('160') || 
           code.startsWith('170') || code.startsWith('180') ||
           code.startsWith('190')
  })
})

// 负债
const liabilities = computed(() => {
  return balanceData.value?.liabilities?.items || []
})

// 所有者权益
const equity = computed(() => {
  return balanceData.value?.equity?.items || []
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
    const res = await reportApi.getBalanceSheet(selectedCustomerId.value, selectedPeriod.value)
    balanceData.value = res.data
  } catch (error) {
    console.error('获取资产负债表失败', error)
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
  if (!balanceData.value) {
    ElMessage.warning('请先查询数据')
    return
  }
  
  // 导出为CSV
  const headers = ['科目代码', '科目名称', '期末余额']
  const rows: string[][] = []
  
  // 资产
  rows.push(['一、资产', '', ''])
  balanceData.value.assets?.items?.forEach((item: any) => {
    rows.push([item.subject_code, item.subject_name, item.balance.toFixed(2)])
  })
  rows.push(['', '资产合计', balanceData.value.assets?.total?.toFixed(2) || '0.00'])
  
  // 负债
  rows.push(['二、负债', '', ''])
  balanceData.value.liabilities?.items?.forEach((item: any) => {
    rows.push([item.subject_code, item.subject_name, Math.abs(item.balance).toFixed(2)])
  })
  rows.push(['', '负债合计', balanceData.value.liabilities?.total?.toFixed(2) || '0.00'])
  
  // 所有者权益
  rows.push(['三、所有者权益', '', ''])
  balanceData.value.equity?.items?.forEach((item: any) => {
    rows.push([item.subject_code, item.subject_name, item.balance.toFixed(2)])
  })
  rows.push(['', '权益合计', balanceData.value.equity?.total?.toFixed(2) || '0.00'])
  
  const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n')
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `资产负债表_${selectedPeriod.value}.csv`
  link.click()
  
  ElMessage.success('导出成功')
}

onMounted(fetchCustomers)
</script>

<style scoped>
.balance-sheet {
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

.section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.subsection {
  margin-bottom: 20px;
}

.subsection-title {
  font-weight: bold;
  color: #606266;
  padding: 10px;
  background: #f5f7fa;
  margin-bottom: 10px;
}

.grand-total {
  display: flex;
  justify-content: space-between;
  padding: 15px 20px;
  background: #409EFF;
  color: #fff;
  font-weight: bold;
  font-size: 16px;
  border-radius: 4px;
  margin-top: 20px;
}

.grand-total span:first-child {
  flex: 1;
}

.grand-total span:not(:first-child) {
  width: 150px;
  text-align: right;
}
</style>
