<template>
  <div class="income-statement">
    <div class="page-header">
      <h2>利润表</h2>
      <div class="header-actions">
        <el-select v-model="selectedPeriod" placeholder="选择账期">
          <el-option v-for="item in periods" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-button type="primary" @click="exportReport">
          <el-icon><Download /></el-icon>导出
        </el-button>
      </div>
    </div>

    <!-- 表头 -->
    <div class="report-header">
      <h3>利润表</h3>
      <p>账期: {{ selectedPeriod }} | 单位: 元</p>
    </div>

    <el-card>
      <!-- 营业收入 -->
      <div class="section">
        <div class="section-title">一、营业收入</div>
        <el-table :data="revenueItems" :show-header="false" stripe>
          <el-table-column prop="name" label="项目" />
          <el-table-column prop="amount" label="本期金额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.amount) }}</template>
          </el-table-column>
          <el-table-column prop="lastAmount" label="上期金额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.lastAmount) }}</template>
          </el-table-column>
        </el-table>
        <div class="total-row">
          <span>营业收入合计</span>
          <span>{{ formatAmount(totalRevenue) }}</span>
          <span>{{ formatAmount(totalRevenueLast) }}</span>
        </div>
      </div>

      <!-- 营业成本 -->
      <div class="section">
        <div class="section-title">减: 营业成本</div>
        <el-table :data="costItems" :show-header="false" stripe>
          <el-table-column prop="name" label="项目" />
          <el-table-column prop="amount" label="本期金额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.amount) }}</template>
          </el-table-column>
          <el-table-column prop="lastAmount" label="上期金额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.lastAmount) }}</template>
          </el-table-column>
        </el-table>
        <div class="total-row">
          <span>营业成本合计</span>
          <span>{{ formatAmount(totalCost) }}</span>
          <span>{{ formatAmount(totalCostLast) }}</span>
        </div>
      </div>

      <!-- 税金及附加 -->
      <div class="section">
        <div class="section-title">减: 税金及附加</div>
        <el-table :data="taxItems" :show-header="false" stripe>
          <el-table-column prop="name" label="项目" />
          <el-table-column prop="amount" label="本期金额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.amount) }}</template>
          </el-table-column>
          <el-table-column prop="lastAmount" label="上期金额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.lastAmount) }}</template>
          </el-table-column>
        </el-table>
        <div class="total-row">
          <span>税金及附加合计</span>
          <span>{{ formatAmount(totalTax) }}</span>
          <span>{{ formatAmount(totalTaxLast) }}</span>
        </div>
      </div>

      <!-- 期间费用 -->
      <div class="section">
        <div class="section-title">减: 期间费用</div>
        <el-table :data="expenseItems" :show-header="false" stripe>
          <el-table-column prop="name" label="项目" />
          <el-table-column prop="amount" label="本期金额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.amount) }}</template>
          </el-table-column>
          <el-table-column prop="lastAmount" label="上期金额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.lastAmount) }}</template>
          </el-table-column>
        </el-table>
        <div class="total-row">
          <span>期间费用合计</span>
          <span>{{ formatAmount(totalExpense) }}</span>
          <span>{{ formatAmount(totalExpenseLast) }}</span>
        </div>
      </div>

      <!-- 营业利润 -->
      <div class="highlight-row">
        <span>营业利润</span>
        <span :class="operatingProfit >= 0 ? 'positive' : 'negative'">
          {{ formatAmount(operatingProfit) }}
        </span>
        <span :class="operatingProfitLast >= 0 ? 'positive' : 'negative'">
          {{ formatAmount(operatingProfitLast) }}
        </span>
      </div>

      <!-- 营业外收支 -->
      <div class="section">
        <div class="section-title">加: 营业外收入</div>
        <el-table :data="nonOperatingIncome" :show-header="false" stripe>
          <el-table-column prop="name" label="项目" />
          <el-table-column prop="amount" label="本期金额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.amount) }}</template>
          </el-table-column>
          <el-table-column prop="lastAmount" label="上期金额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.lastAmount) }}</template>
          </el-table-column>
        </el-table>
      </div>

      <div class="section">
        <div class="section-title">减: 营业外支出</div>
        <el-table :data="nonOperatingExpense" :show-header="false" stripe>
          <el-table-column prop="name" label="项目" />
          <el-table-column prop="amount" label="本期金额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.amount) }}</template>
          </el-table-column>
          <el-table-column prop="lastAmount" label="上期金额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.lastAmount) }}</template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 利润总额 -->
      <div class="highlight-row secondary">
        <span>利润总额</span>
        <span :class="totalProfit >= 0 ? 'positive' : 'negative'">{{ formatAmount(totalProfit) }}</span>
        <span :class="totalProfitLast >= 0 ? 'positive' : 'negative'">{{ formatAmount(totalProfitLast) }}</span>
      </div>

      <!-- 所得税 -->
      <div class="section">
        <div class="section-title">减: 所得税费用</div>
        <el-table :show-header="false" :data="[{name: '所得税费用', amount: incomeTax, lastAmount: incomeTaxLast}]">
          <el-table-column prop="name" label="项目" />
          <el-table-column prop="amount" label="本期金额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.amount) }}</template>
          </el-table-column>
          <el-table-column prop="lastAmount" label="上期金额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.lastAmount) }}</template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 净利润 -->
      <div class="highlight-row final">
        <span>净利润</span>
        <span :class="netProfit >= 0 ? 'positive' : 'negative'">{{ formatAmount(netProfit) }}</span>
        <span :class="netProfitLast >= 0 ? 'positive' : 'negative'">{{ formatAmount(netProfitLast) }}</span>
      </div>

      <!-- 利润分析 -->
      <div class="analysis-section">
        <h4>利润分析</h4>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-statistic title="毛利率" :value="grossMargin" suffix="%" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="营业利润率" :value="operatingMargin" suffix="%" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="净利润率" :value="netMargin" suffix="%" />
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'

const selectedPeriod = ref('2024-03')
const periods = ref([
  { label: '2024年3月', value: '2024-03' },
  { label: '2024年2月', value: '2024-02' },
  { label: '2024年1月', value: '2024-01' }
])

// 营业收入
const revenueItems = ref([
  { name: '主营业务收入', amount: 850000, lastAmount: 780000 },
  { name: '其他业务收入', amount: 50000, lastAmount: 45000 }
])

const totalRevenue = computed(() => revenueItems.value.reduce((sum, item) => sum + item.amount, 0))
const totalRevenueLast = computed(() => revenueItems.value.reduce((sum, item) => sum + item.lastAmount, 0))

// 营业成本
const costItems = ref([
  { name: '主营业务成本', amount: 520000, lastAmount: 480000 },
  { name: '其他业务成本', amount: 30000, lastAmount: 28000 }
])

const totalCost = computed(() => costItems.value.reduce((sum, item) => sum + item.amount, 0))
const totalCostLast = computed(() => costItems.value.reduce((sum, item) => sum + item.lastAmount, 0))

// 税金及附加
const taxItems = ref([
  { name: '城市维护建设税', amount: 3500, lastAmount: 3200 },
  { name: '教育费附加', amount: 1500, lastAmount: 1400 },
  { name: '地方教育附加', amount: 1000, lastAmount: 900 }
])

const totalTax = computed(() => taxItems.value.reduce((sum, item) => sum + item.amount, 0))
const totalTaxLast = computed(() => taxItems.value.reduce((sum, item) => sum + item.lastAmount, 0))

// 期间费用
const expenseItems = ref([
  { name: '销售费用', amount: 45000, lastAmount: 42000 },
  { name: '管理费用', amount: 68000, lastAmount: 65000 },
  { name: '研发费用', amount: 35000, lastAmount: 32000 },
  { name: '财务费用', amount: 8000, lastAmount: 8500 }
])

const totalExpense = computed(() => expenseItems.value.reduce((sum, item) => sum + item.amount, 0))
const totalExpenseLast = computed(() => expenseItems.value.reduce((sum, item) => sum + item.lastAmount, 0))

// 营业利润
const operatingProfit = computed(() => 
  totalRevenue.value - totalCost.value - totalTax.value - totalExpense.value)
const operatingProfitLast = computed(() => 
  totalRevenueLast.value - totalCostLast.value - totalTaxLast.value - totalExpenseLast.value)

// 营业外收支
const nonOperatingIncome = ref([
  { name: '政府补助', amount: 15000, lastAmount: 12000 },
  { name: '盘盈利得', amount: 2000, lastAmount: 1500 }
])

const nonOperatingExpense = ref([
  { name: '捐赠支出', amount: 5000, lastAmount: 8000 },
  { name: '罚款支出', amount: 1500, lastAmount: 2000 }
])

const nonOperatingTotal = computed(() => 
  nonOperatingIncome.value.reduce((sum, item) => sum + item.amount, 0) -
  nonOperatingExpense.value.reduce((sum, item) => sum + item.amount, 0))

const nonOperatingTotalLast = computed(() => 
  nonOperatingIncome.value.reduce((sum, item) => sum + item.lastAmount, 0) -
  nonOperatingExpense.value.reduce((sum, item) => sum + item.lastAmount, 0))

// 利润总额
const totalProfit = computed(() => operatingProfit.value + nonOperatingTotal.value)
const totalProfitLast = computed(() => operatingProfitLast.value + nonOperatingTotalLast.value)

// 所得税
const incomeTax = computed(() => Math.max(0, totalProfit.value * 0.25))
const incomeTaxLast = computed(() => Math.max(0, totalProfitLast.value * 0.25))

// 净利润
const netProfit = computed(() => totalProfit.value - incomeTax.value)
const netProfitLast = computed(() => totalProfitLast.value - incomeTaxLast.value)

// 利润率分析
const grossMargin = computed(() => 
  ((totalRevenue.value - totalCost.value) / totalRevenue.value * 100).toFixed(2))
const operatingMargin = computed(() => 
  (operatingProfit.value / totalRevenue.value * 100).toFixed(2))
const netMargin = computed(() => 
  (netProfit.value / totalRevenue.value * 100).toFixed(2))

const formatAmount = (amount: number) => {
  return '¥' + amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const exportReport = () => {
  ElMessage.success('报表导出成功')
}
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

.total-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 20px;
  background: #ecf5ff;
  font-weight: bold;
  margin-top: 10px;
}

.total-row span:first-child {
  flex: 1;
}

.total-row span:not(:first-child) {
  width: 150px;
  text-align: right;
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