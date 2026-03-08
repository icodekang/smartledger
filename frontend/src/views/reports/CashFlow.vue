<template>
  <div class="cash-flow">
    <div class="page-header">
      <h2>现金流量表</h2>
      <div class="header-actions">
        <el-select v-model="selectedPeriod" placeholder="选择账期">
          <el-option v-for="item in periods" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-button type="primary" @click="exportReport">
          <el-icon><Download /></el-icon>导出
        </el-button>
      </div>
    </div>

    <div class="report-header">
      <h3>现金流量表</h3>
      <p>账期: {{ selectedPeriod }} | 单位: 元</p>
    </div>

    <el-card>
      <!-- 经营活动 -->
      <div class="section">
        <div class="section-title">一、经营活动产生的现金流量</div>
        <el-table :data="operatingItems" :show-header="false" stripe>
          <el-table-column prop="name" label="项目" />
          <el-table-column prop="amount" label="本期金额" width="150" align="right">
            <template #default="{ row }">
              <span :class="row.amount >= 0 ? 'positive' : 'negative'">
                {{ formatAmount(row.amount) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="lastAmount" label="上期金额" width="150" align="right">
            <template #default="{ row }">
              <span :class="row.lastAmount >= 0 ? 'positive' : 'negative'">
                {{ formatAmount(row.lastAmount) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
        <div class="highlight-row">
          <span>经营活动现金流入小计</span>
          <span class="positive">{{ formatAmount(operatingInflow) }}</span>
          <span class="positive">{{ formatAmount(operatingInflowLast) }}</span>
        </div>
        <div class="highlight-row secondary">
          <span>经营活动现金流出小计</span>
          <span class="negative">{{ formatAmount(operatingOutflow) }}</span>
          <span class="negative">{{ formatAmount(operatingOutflowLast) }}</span>
        </div>
        <div class="highlight-row final">
          <span>经营活动现金流量净额</span>
          <span :class="operatingNet >= 0 ? 'positive' : 'negative'">
            {{ formatAmount(operatingNet) }}
          </span>
          <span :class="operatingNetLast >= 0 ? 'positive' : 'negative'">
            {{ formatAmount(operatingNetLast) }}
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
                {{ formatAmount(row.amount) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="lastAmount" label="上期金额" width="150" align="right">
            <template #default="{ row }">
              <span :class="row.lastAmount >= 0 ? 'positive' : 'negative'">
                {{ formatAmount(row.lastAmount) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
        <div class="highlight-row final">
          <span>投资活动现金流量净额</span>
          <span :class="investingNet >= 0 ? 'positive' : 'negative'">
            {{ formatAmount(investingNet) }}
          </span>
          <span :class="investingNetLast >= 0 ? 'positive' : 'negative'">
            {{ formatAmount(investingNetLast) }}
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
                {{ formatAmount(row.amount) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="lastAmount" label="上期金额" width="150" align="right">
            <template #default="{ row }">
              <span :class="row.lastAmount >= 0 ? 'positive' : 'negative'">
                {{ formatAmount(row.lastAmount) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
        <div class="highlight-row final">
          <span>筹资活动现金流量净额</span>
          <span :class="financingNet >= 0 ? 'positive' : 'negative'">
            {{ formatAmount(financingNet) }}
          </span>
          <span :class="financingNetLast >= 0 ? 'positive' : 'negative'">
            {{ formatAmount(financingNetLast) }}
          </span>
        </div>
      </div>

      <!-- 现金净增加额 -->
      <div class="section">
        <div class="highlight-row grand-total">
          <span>四、现金及现金等价物净增加额</span>
          <span :class="totalNet >= 0 ? 'positive' : 'negative'">
            {{ formatAmount(totalNet) }}
          </span>
          <span :class="totalNetLast >= 0 ? 'positive' : 'negative'">
            {{ formatAmount(totalNetLast) }}
          </span>
        </div>

        <el-table :show-header="false" :data="[
          {name: '加: 期初现金及现金等价物余额', amount: openingCash, lastAmount: openingCashLast}
        ]">
          <el-table-column prop="name" label="项目" />
          <el-table-column prop="amount" label="本期金额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.amount) }}</template>
          </el-table-column>
          <el-table-column prop="lastAmount" label="上期金额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.lastAmount) }}</template>
          </el-table-column>
        </el-table>

        <div class="highlight-row grand-total final">
          <span>五、期末现金及现金等价物余额</span>
          <span class="positive">{{ formatAmount(endingCash) }}</span>
          <span class="positive">{{ formatAmount(endingCashLast) }}</span>
        </div>
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

// 经营活动
const operatingItems = ref([
  { name: '销售商品、提供劳务收到的现金', amount: 820000, lastAmount: 750000 },
  { name: '收到的税费返还', amount: 15000, lastAmount: 12000 },
  { name: '收到的其他与经营活动有关的现金', amount: 8000, lastAmount: 6500 },
  { name: '购买商品、接受劳务支付的现金', amount: -450000, lastAmount: -420000 },
  { name: '支付给职工以及为职工支付的现金', amount: -180000, lastAmount: -170000 },
  { name: '支付的各项税费', amount: -85000, lastAmount: -78000 },
  { name: '支付的其他与经营活动有关的现金', amount: -68000, lastAmount: -65000 }
])

const operatingInflow = computed(() => 
  operatingItems.value.filter(item => item.amount > 0).reduce((sum, item) => sum + item.amount, 0))
const operatingOutflow = computed(() => 
  operatingItems.value.filter(item => item.amount < 0).reduce((sum, item) => sum + item.amount, 0))
const operatingNet = computed(() => operatingInflow.value + operatingOutflow.value)

const operatingInflowLast = computed(() => 
  operatingItems.value.filter(item => item.lastAmount > 0).reduce((sum, item) => sum + item.lastAmount, 0))
const operatingOutflowLast = computed(() => 
  operatingItems.value.filter(item => item.lastAmount < 0).reduce((sum, item) => sum + item.lastAmount, 0))
const operatingNetLast = computed(() => operatingInflowLast.value + operatingOutflowLast.value)

// 投资活动
const investingItems = ref([
  { name: '收回投资所收到的现金', amount: 50000, lastAmount: 30000 },
  { name: '取得投资收益所收到的现金', amount: 8000, lastAmount: 6500 },
  { name: '处置固定资产、无形资产收回的现金', amount: 15000, lastAmount: 12000 },
  { name: '购建固定资产、无形资产支付的现金', amount: -120000, lastAmount: -150000 },
  { name: '投资所支付的现金', amount: -50000, lastAmount: -80000 }
])

const investingNet = computed(() => 
  investingItems.value.reduce((sum, item) => sum + item.amount, 0))
const investingNetLast = computed(() => 
  investingItems.value.reduce((sum, item) => sum + item.lastAmount, 0))

// 筹资活动
const financingItems = ref([
  { name: '吸收投资所收到的现金', amount: 0, lastAmount: 100000 },
  { name: '借款所收到的现金', amount: 200000, lastAmount: 150000 },
  { name: '偿还债务所支付的现金', amount: -150000, lastAmount: -100000 },
  { name: '分配股利、利润所支付的现金', amount: -30000, lastAmount: -25000 },
  { name: '偿付利息所支付的现金', amount: -8000, lastAmount: -7500 }
])

const financingNet = computed(() => 
  financingItems.value.reduce((sum, item) => sum + item.amount, 0))
const financingNetLast = computed(() => 
  financingItems.value.reduce((sum, item) => sum + item.lastAmount, 0))

// 现金净增加额
const totalNet = computed(() => 
  operatingNet.value + investingNet.value + financingNet.value)
const totalNetLast = computed(() => 
  operatingNetLast.value + investingNetLast.value + financingNetLast.value)

// 期初期末现金
const openingCash = 480000
const openingCashLast = 420000
const endingCash = computed(() => openingCash + totalNet.value)
const endingCashLast = computed(() => openingCashLast + totalNetLast.value)

const formatAmount = (amount: number) => {
  const absAmount = Math.abs(amount)
  return '¥' + absAmount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const exportReport = () => {
  ElMessage.success('报表导出成功')
}
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

.highlight-row.secondary {
  background: #fdf6ec;
}

.highlight-row.final {
  background: #f0f9ff;
}

.highlight-row.grand-total {
  background: #409EFF;
  color: #fff;
  font-size: 16px;
  padding: 15px 20px;
}

.highlight-row.grand-total.final {
  background: #67C23A;
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