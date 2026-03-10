<template>
  <div class="income-statement">
    <div class="page-header">
      <h2>利润表</h2>
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
      <!-- 表头 -->
      <div class="report-header">
        <h3>利润表</h3>
        <p>{{ selectedCustomerName }} | 账期: {{ selectedPeriod }} | 单位: 元</p>
      </div>

      <el-card v-if="incomeData">
        <!-- 营业收入 -->
        <div class="section">
          <div class="section-title">一、营业收入</div>
          <div class="amount-display">
            <span class="label">营业收入</span>
            <span class="value positive">{{ formatAmount(incomeData.revenue) }}</span>
          </div>
        </div>

        <!-- 营业成本 -->
        <div class="section">
          <div class="section-title">减: 营业成本</div>
          <div class="amount-display">
            <span class="label">营业成本</span>
            <span class="value negative">{{ formatAmount(incomeData.cost) }}</span>
          </div>
        </div>

        <!-- 毛利 -->
        <div class="highlight-row">
          <span>毛利</span>
          <span :class="incomeData.gross_profit >= 0 ? 'positive' : 'negative'">
            {{ formatAmount(incomeData.gross_profit) }}
          </span>
        </div>

        <!-- 期间费用 -->
        <div class="section">
          <div class="section-title">减: 期间费用</div>
          <div class="amount-display">
            <span class="label">期间费用</span>
            <span class="value negative">{{ formatAmount(incomeData.expenses) }}</span>
          </div>
        </div>

        <!-- 营业利润 -->
        <div class="highlight-row secondary">
          <span>营业利润</span>
          <span :class="(incomeData.gross_profit - incomeData.expenses) >= 0 ? 'positive' : 'negative'">
            {{ formatAmount(incomeData.gross_profit - incomeData.expenses) }}
          </span>
        </div>

        <!-- 净利润 -->
        <div class="highlight-row final">
          <span>净利润</span>
          <span :class="incomeData.net_profit >= 0 ? 'positive' : 'negative'">
            {{ formatAmount(incomeData.net_profit) }}
          </span>
        </div>

        <!-- 利润分析 -->
        <div class="analysis-section">
          <h4>利润分析</h4>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-statistic 
                title="毛利率" 
                :value="grossMargin" 
                suffix="%"
                :precision="2"
              />
            </el-col>
            <el-col :span="8">
              <el-statistic 
                title="营业利润率" 
                :value="operatingMargin" 
                suffix="%"
                :precision="2"
              />
            </el-col>
            <el-col :span="8">
              <el-statistic 
                title="净利润率" 
                :value="netMargin" 
                suffix="%"
                :precision="2"
              />
            </el-col>
          </el-row>
        </div>
      </el-card>

      <!-- 空状态 -->
      <el-empty v-if="!loading && !incomeData" description="请选择客户和账期查询数据" />
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
const incomeData = ref<any>(null)

const selectedCustomerName = computed(() => {
  const customer = customers.value.find(c => c.id === selectedCustomerId.value)
  return customer?.name || ''
})

const grossMargin = computed(() => {
  if (!incomeData.value?.revenue || incomeData.value.revenue === 0) return 0
  return ((incomeData.value.revenue - incomeData.value.cost) / incomeData.value.revenue * 100)
})

const operatingMargin = computed(() => {
  if (!incomeData.value?.revenue || incomeData.value.revenue === 0) return 0
  return ((incomeData.value.gross_profit - incomeData.value.expenses) / incomeData.value.revenue * 100)
})

const netMargin = computed(() => {
  if (!incomeData.value?.revenue || incomeData.value.revenue === 0) return 0
  return (incomeData.value.net_profit / incomeData.value.revenue * 100)
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
    const res = await reportApi.getIncomeStatement(selectedCustomerId.value, selectedPeriod.value)
    incomeData.value = res.data
  } catch (error) {
    console.error('获取利润表失败', error)
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
  if (!incomeData.value) {
    ElMessage.warning('请先查询数据')
    return
  }
  
  const headers = ['项目', '金额']
  const rows = [
    ['营业收入', incomeData.value.revenue?.toFixed(2) || '0.00'],
    ['营业成本', incomeData.value.cost?.toFixed(2) || '0.00'],
    ['毛利', incomeData.value.gross_profit?.toFixed(2) || '0.00'],
    ['期间费用', incomeData.value.expenses?.toFixed(2) || '0.00'],
    ['净利润', incomeData.value.net_profit?.toFixed(2) || '0.00'],
  ]
  
  const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n')
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `利润表_${selectedPeriod.value}.csv`
  link.click()
  
  ElMessage.success('导出成功')
}

onMounted(fetchCustomers)
</script>

<style scoped>
.income-statement {
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
  font-weight: bold;
  color: #606266;
  padding: 10px;
  background: #f5f7fa;
  margin-bottom: 10px;
}

.amount-display {
  display: flex;
  justify-content: space-between;
  padding: 15px 20px;
  background: #fafafa;
  border-radius: 4px;
}

.amount-display .label {
  font-weight: bold;
  color: #303133;
}

.amount-display .value {
  font-size: 18px;
  font-weight: bold;
}

.highlight-row {
  display: flex;
  justify-content: space-between;
  padding: 15px 20px;
  background: #409EFF;
  color: #fff;
  font-weight: bold;
  font-size: 16px;
  border-radius: 4px;
  margin: 20px 0;
}

.highlight-row.secondary {
  background: #67C23A;
}

.highlight-row.final {
  background: #E6A23C;
}

.highlight-row span:first-child {
  flex: 1;
}

.highlight-row span:not(:first-child) {
  width: 150px;
  text-align: right;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}

.highlight-row .positive,
.highlight-row .negative {
  color: #fff;
}

.analysis-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #EBEEF5;
}

.analysis-section h4 {
  margin: 0 0 20px;
  color: #303133;
}
</style>
