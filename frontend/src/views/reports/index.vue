<template>
  <div class="reports">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>财务报表</span>
          <el-select v-model="selectedCustomerId" placeholder="选择客户" style="width: 200px; margin-right: 10px">
            <el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
          <el-date-picker v-model="selectedPeriod" type="month" placeholder="选择月份" value-format="YYYY-MM" style="width: 150px; margin-right: 10px" />
          <el-button type="primary" @click="fetchReports">查询</el-button>
        </div>      </template>

      <el-tabs v-model="activeTab">
        <!-- 资产负债表 -->
        <el-tab-pane label="资产负债表" name="balance">
          <div v-if="balanceSheet" class="report-content">
            <h3>资产负债表</h3>
            <p class="period">会计期间: {{ selectedPeriod }}</p>
            
            <div class="balance-check" :class="{ ok: balanceSheet.balance_check }">
              <el-tag :type="balanceSheet.balance_check ? 'success' : 'danger'">
                {{ balanceSheet.balance_check ? '✓ 借贷平衡' : '✗ 借贷不平衡' }}
              </el-tag>
            </div>

            <el-row :gutter="20">
              <el-col :span="12">
                <h4>资产 (合计: ¥{{ balanceSheet.assets?.total?.toFixed(2) }})</h4>
                <el-table :data="balanceSheet.assets?.items" border size="small">
                  <el-table-column prop="subject_code" label="科目代码" width="100" />
                  <el-table-column prop="subject_name" label="科目名称" />
                  <el-table-column prop="balance" label="金额" width="120" align="right">
                    <template #default="{ row }">¥{{ row.balance.toFixed(2) }}</template>
                  </el-table-column>
                </el-table>
              </el-col>

              <el-col :span="12">
                <h4>负债 (合计: ¥{{ balanceSheet.liabilities?.total?.toFixed(2) }})</h4>
                <el-table :data="balanceSheet.liabilities?.items" border size="small">
                  <el-table-column prop="subject_code" label="科目代码" width="100" />
                  <el-table-column prop="subject_name" label="科目名称" />
                  <el-table-column prop="balance" label="金额" width="120" align="right">
                    <template #default="{ row }">¥{{ Math.abs(row.balance).toFixed(2) }}</template>
                  </el-table-column>
                </el-table>

                <h4 style="margin-top: 20px">所有者权益 (合计: ¥{{ balanceSheet.equity?.total?.toFixed(2) }})</h4>
                <el-table :data="balanceSheet.equity?.items" border size="small">
                  <el-table-column prop="subject_code" label="科目代码" width="100" />
                  <el-table-column prop="subject_name" label="科目名称" />
                  <el-table-column prop="balance" label="金额" width="120" align="right">
                    <template #default="{ row }">¥{{ row.balance.toFixed(2) }}</template>
                  </el-table-column>
                </el-table>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <!-- 利润表 -->
        <el-tab-pane label="利润表" name="income">
          <div v-if="incomeStatement" class="report-content">
            <h3>利润表</h3>
            <p class="period">会计期间: {{ selectedPeriod }}</p>

            <el-descriptions border :column="1">
              <el-descriptions-item label="营业收入"><span class="amount">¥{{ incomeStatement.revenue?.toFixed(2) }}</span></el-descriptions-item>
              <el-descriptions-item label="营业成本"><span class="amount">¥{{ incomeStatement.cost?.toFixed(2) }}</span></el-descriptions-item>
              <el-descriptions-item label="毛利">
                <span class="amount highlight">¥{{ incomeStatement.gross_profit?.toFixed(2) }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="期间费用"><span class="amount">¥{{ incomeStatement.expenses?.toFixed(2) }}</span></el-descriptions-item>
              <el-descriptions-item label="净利润">
                <span class="amount highlight" :class="{ profit: incomeStatement.net_profit >= 0, loss: incomeStatement.net_profit < 0 }">
                  ¥{{ incomeStatement.net_profit?.toFixed(2) }}
                </span>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-tab-pane>

        <!-- 现金流量表 -->
        <el-tab-pane label="现金流量表" name="cashflow">
          <div v-if="cashFlow" class="report-content">
            <h3>现金流量表</h3>
            <p class="period">会计期间: {{ selectedPeriod }}</p>

            <el-descriptions border :column="1">
              <el-descriptions-item label="经营活动现金流入"><span class="amount">¥{{ cashFlow.operating?.inflow?.toFixed(2) }}</span></el-descriptions-item>
              <el-descriptions-item label="经营活动现金流出"><span class="amount">¥{{ cashFlow.operating?.outflow?.toFixed(2) }}</span></el-descriptions-item>
              <el-descriptions-item label="经营活动现金流量净额">
                <span class="amount highlight">¥{{ cashFlow.operating?.net?.toFixed(2) }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="现金净增加额">
                <span class="amount highlight">¥{{ cashFlow.net_increase?.toFixed(2) }}</span>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-tab-pane>

        <!-- 科目余额表 -->
        <el-tab-pane label="科目余额表" name="subject">
          <div v-if="subjectBalance" class="report-content">
            <h3>科目余额表</h3>
            <p class="period">会计期间: {{ selectedPeriod }}</p>

            <div class="balance-check" :class="{ ok: subjectBalance.is_balanced }">
              <el-tag :type="subjectBalance.is_balanced ? 'success' : 'danger'">
                {{ subjectBalance.is_balanced ? '✓ 试算平衡' : '✗ 试算不平衡' }}
              </el-tag>
            </div>

            <el-table :data="subjectBalance.items" border size="small">
              <el-table-column prop="subject_code" label="科目代码" width="120" />
              <el-table-column prop="subject_name" label="科目名称" />
              <el-table-column prop="debit" label="借方" width="150" align="right">
                <template #default="{ row }">¥{{ row.debit.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="credit" label="贷方" width="150" align="right">
                <template #default="{ row }">¥{{ row.credit.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="direction" label="方向" width="80" align="center" />
              <el-table-column prop="balance" label="余额" width="150" align="right">
                <template #default="{ row }">¥{{ Math.abs(row.balance).toFixed(2) }}</template>
              </el-table-column>
            </el-table>

            <div class="report-summary">
              <span>借方合计: ¥{{ subjectBalance.total?.debit?.toFixed(2) }}</span>
              <span>贷方合计: ¥{{ subjectBalance.total?.credit?.toFixed(2) }}</span>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { customerApi } from '../api/customer'
import { reportApi } from '../api/report'

const customers = ref([])
const selectedCustomerId = ref('')
const selectedPeriod = ref(new Date().toISOString().slice(0, 7))
const activeTab = ref('balance')

const balanceSheet = ref<any>(null)
const incomeStatement = ref<any>(null)
const cashFlow = ref<any>(null)
const subjectBalance = ref<any>(null)

const fetchCustomers = async () => {
  const res = await customerApi.getList({ page_size: 1000 })
  customers.value = res.data.items
  if (customers.value.length > 0) {
    selectedCustomerId.value = customers.value[0].id
    fetchReports()
  }
}

const fetchReports = async () => {
  if (!selectedCustomerId.value || !selectedPeriod.value) return

  const [balanceRes, incomeRes, cashRes, subjectRes] = await Promise.all([
    reportApi.getBalanceSheet(selectedCustomerId.value, selectedPeriod.value),
    reportApi.getIncomeStatement(selectedCustomerId.value, selectedPeriod.value),
    reportApi.getCashFlow(selectedCustomerId.value, selectedPeriod.value),
    reportApi.getSubjectBalance(selectedCustomerId.value, selectedPeriod.value)
  ])

  balanceSheet.value = balanceRes.data
  incomeStatement.value = incomeRes.data
  cashFlow.value = cashRes.data
  subjectBalance.value = subjectRes.data
}

onMounted(fetchCustomers)
</script>

<style scoped>
.reports {
  padding: 20px;
}
.card-header {
  display: flex;
  align-items: center;
}
.report-content {
  padding: 20px;
}
.period {
  color: #666;
  margin-bottom: 20px;
}
.balance-check {
  margin-bottom: 20px;
}
.amount {
  font-family: monospace;
  font-size: 16px;
}
.amount.highlight {
  font-weight: bold;
  color: #409eff;
}
.amount.profit {
  color: #67c23a;
}
.amount.loss {
  color: #f56c6c;
}
.report-summary {
  margin-top: 20px;
  padding: 15px;
  background: #f5f7fa;
  display: flex;
  justify-content: space-around;
}
</style>
