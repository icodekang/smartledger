<template>
  <div class="cash-flow">
    <div class="page-header">
      <h2>现金流量表</h2>
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
      <div class="report-header">
        <h3>现金流量表</h3>
        <p>{{ selectedCustomerName }} | 账期: {{ selectedPeriod }} | 单位: 元</p>
      </div>

      <el-card v-if="cashFlowData">
        <!-- 经营活动 -->
        <div class="section">
          <div class="section-title">一、经营活动产生的现金流量</div>
          <el-table :data="operatingItems" :show-header="false" stripe>
            <el-table-column prop="name" label="项目" />
            <el-table-column prop="amount" label="本期金额" width="150" align="right">
              <template #default="{ row }">
                <span :class="row.amount >= 0 ? 'positive' : 'negative'">
                  {{ formatAmount(Math.abs(row.amount)) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
          <div class="highlight-row">
            <span>经营活动现金流量净额</span>
            <span :class="cashFlowData.operating?.net >= 0 ? 'positive' : 'negative'">
              {{ formatAmount(cashFlowData.operating?.net) }}
            </span>
          </div>
        </div>

        <!-- 投资活动 -->
        <div class="section">
          <div class="section-title">二、投资活动产生的现金流量</div>
          <el-table :data="investingItems" :show-header="false" stripe>
            <el-table-column prop="name" label="项目" />
            <el-table-column prop="amount" label="本期金额" width="150" align="right">
              <template #default="{ row }">
                <span :class="row.amount >= 0 ? 'positive' : 'negative'">
                  {{ formatAmount(Math.abs(row.amount)) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
          <div class="highlight-row">
            <span>投资活动现金流量净额</span>
            <span :class="cashFlowData.investing?.net >= 0 ? 'positive' : 'negative'">
              {{ formatAmount(cashFlowData.investing?.net) }}
            </span>
          </div>
        </div>

        <!-- 筹资活动 -->
        <div class="section">
          <div class="section-title">三、筹资活动产生的现金流量</div>
          <el-table :data="financingItems" :show-header="false" stripe>
            <el-table-column prop="name" label="项目" />
            <el-table-column prop="amount" label="本期金额" width="150" align="right">
              <template #default="{ row }">
                <span :class="row.amount >= 0 ? 'positive' : 'negative'">
                  {{ formatAmount(Math.abs(row.amount)) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
          <div class="highlight-row">
            <span>筹资活动现金流量净额</span>
            <span :class="cashFlowData.financing?.net >= 0 ? 'positive' : 'negative'">
              {{ formatAmount(cashFlowData.financing?.net) }}
            </span>
          </div>
        </div>

        <!-- 现金净增加额 -->
        <div class="section">
          <div class="highlight-row grand-total">
            <span>现金及现金等价物净增加额</span>
            <span :class="cashFlowData.net_increase >= 0 ? 'positive' : 'negative'">
              {{ formatAmount(cashFlowData.net_increase) }}
            </span>
          </div>
        </div>
      </el-card>

      <!-- 空状态 -->
      <el-empty v-if="!loading && !cashFlowData" description="请选择客户和账期查询数据" />
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
const cashFlowData = ref<any>(null)

const selectedCustomerName = computed(() => {
  const customer = customers.value.find(c => c.id === selectedCustomerId.value)
  return customer?.name || ''
})

const operatingItems = computed(() => {
  const items = []
  if (cashFlowData.value?.operating) {
    if (cashFlowData.value.operating.inflow > 0) {
      items.push({ name: '经营活动现金流入', amount: cashFlowData.value.operating.inflow })
    }
    if (cashFlowData.value.operating.outflow > 0) {
      items.push({ name: '经营活动现金流出', amount: -cashFlowData.value.operating.outflow })
    }
  }
  return items
})

const investingItems = computed(() => {
  const items = []
  if (cashFlowData.value?.investing) {
    if (cashFlowData.value.investing.inflow > 0) {
      items.push({ name: '投资活动现金流入', amount: cashFlowData.value.investing.inflow })
    }
    if (cashFlowData.value.investing.outflow > 0) {
      items.push({ name: '投资活动现金流出', amount: -cashFlowData.value.investing.outflow })
    }
  }
  return items
})

const financingItems = computed(() => {
  const items = []
  if (cashFlowData.value?.financing) {
    if (cashFlowData.value.financing.inflow > 0) {
      items.push({ name: '筹资活动现金流入', amount: cashFlowData.value.financing.inflow })
    }
    if (cashFlowData.value.financing.outflow > 0) {
      items.push({ name: '筹资活动现金流出', amount: -cashFlowData.value.financing.outflow })
    }
  }
  return items
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
    const res = await reportApi.getCashFlow(selectedCustomerId.value, selectedPeriod.value)
    cashFlowData.value = res.data
  } catch (error) {
    console.error('获取现金流量表失败', error)
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
  if (!cashFlowData.value) {
    ElMessage.warning('请先查询数据')
    return
  }
  
  const headers = ['项目', '金额']
  const rows = [
    ['经营活动现金流量净额', cashFlowData.value.operating?.net?.toFixed(2) || '0.00'],
    ['投资活动现金流量净额', cashFlowData.value.investing?.net?.toFixed(2) || '0.00'],
    ['筹资活动现金流量净额', cashFlowData.value.financing?.net?.toFixed(2) || '0.00'],
    ['现金净增加额', cashFlowData.value.net_increase?.toFixed(2) || '0.00'],
  ]
  
  const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n')
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `现金流量表_${selectedPeriod.value}.csv`
  link.click()
  
  ElMessage.success('导出成功')
}

onMounted(fetchCustomers)
</script>

<style scoped>
.cash-flow {
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
  margin-bottom: 30px;
}

.section-title {
  font-weight: bold;
  color: #303133;
  padding: 10px;
  background: #f5f7fa;
  margin-bottom: 10px;
}

.highlight-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 20px;
  background: #ecf5ff;
  font-weight: bold;
  margin-top: 10px;
  border-radius: 4px;
}

.highlight-row span:first-child {
  flex: 1;
}

.highlight-row span:not(:first-child) {
  width: 150px;
  text-align: right;
}

.highlight-row.grand-total {
  background: #409EFF;
  color: #fff;
  font-size: 16px;
  padding: 15px 20px;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}

.grand-total .positive,
.grand-total .negative {
  color: #fff;
}
</style>
