<template>
  <div class="balance-sheet">
    <div class="page-header">
      <h2>资产负债表</h2>
      <div class="header-actions">
        <el-select v-model="selectedPeriod" placeholder="选择账期">
          <el-option v-for="item in periods" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-button type="primary" @click="exportReport">
          <el-icon><Download /></el-icon>导出
        </el-button>
      </div>
    </div>

    <!-- 表头信息 -->
    <div class="report-header">
      <h3>资产负债表</h3>
      <p>账期: {{ selectedPeriod }} | 单位: 元</p>
    </div>

    <!-- 资产 -->
    <el-card class="section">
      <template #header>
        <span class="section-title">一、资产</span>
      </template>
      
      <!-- 流动资产 -->
      <div class="subsection">
        <div class="subsection-title">流动资产</div>
        <el-table :data="currentAssets" :show-header="false" stripe>
          <el-table-column prop="name" label="项目" />
          <el-table-column prop="endAmount" label="期末余额" width="150" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.endAmount) }}
            </template>
          </el-table-column>
          <el-table-column prop="startAmount" label="年初余额" width="150" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.startAmount) }}
            </template>
          </el-table-column>
        </el-table>
        <div class="total-row">
          <span>流动资产合计</span>
          <span>{{ formatAmount(currentAssetsTotal.end) }}</span>
          <span>{{ formatAmount(currentAssetsTotal.start) }}</span>
        </div>
      </div>

      <!-- 非流动资产 -->
      <div class="subsection">
        <div class="subsection-title">非流动资产</div>
        <el-table :data="nonCurrentAssets" :show-header="false" stripe>
          <el-table-column prop="name" label="项目" />
          <el-table-column prop="endAmount" label="期末余额" width="150" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.endAmount) }}
            </template>
          </el-table-column>
          <el-table-column prop="startAmount" label="年初余额" width="150" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.startAmount) }}
            </template>
          </el-table-column>
        </el-table>
        <div class="total-row">
          <span>非流动资产合计</span>
          <span>{{ formatAmount(nonCurrentAssetsTotal.end) }}</span>
          <span>{{ formatAmount(nonCurrentAssetsTotal.start) }}</span>
        </div>
      </div>

      <!-- 资产总计 -->
      <div class="grand-total">
        <span>资产总计</span>
        <span>{{ formatAmount(totalAssets.end) }}</span>
        <span>{{ formatAmount(totalAssets.start) }}</span>
      </div>
    </el-card>

    <!-- 负债 -->
    <el-card class="section">
      <template #header>
        <span class="section-title">二、负债</span>
      </template>

      <!-- 流动负债 -->
      <div class="subsection">
        <div class="subsection-title">流动负债</div>
        <el-table :data="currentLiabilities" :show-header="false" stripe>
          <el-table-column prop="name" label="项目" />
          <el-table-column prop="endAmount" label="期末余额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.endAmount) }}</template>
          </el-table-column>
          <el-table-column prop="startAmount" label="年初余额" width="150" align="right">
            <template #default="{ row }">{{ formatAmount(row.startAmount) }}</template>
          </el-table-column>
        </el-table>
        <div class="total-row">
          <span>流动负债合计</span>
          <span>{{ formatAmount(currentLiabilitiesTotal.end) }}</span>
          <span>{{ formatAmount(currentLiabilitiesTotal.start) }}</span>
        </div>
      </div>

      <div class="grand-total">
        <span>负债合计</span>
        <span>{{ formatAmount(totalLiabilities.end) }}</span>
        <span>{{ formatAmount(totalLiabilities.start) }}</span>
      </div>
    </el-card>

    <!-- 所有者权益 -->
    <el-card class="section">
      <template #header>
        <span class="section-title">三、所有者权益</span>
      </template>

      <el-table :data="equity" :show-header="false" stripe>
        <el-table-column prop="name" label="项目" />
        <el-table-column prop="endAmount" label="期末余额" width="150" align="right">
          <template #default="{ row }">{{ formatAmount(row.endAmount) }}</template>
        </el-table-column>
        <el-table-column prop="startAmount" label="年初余额" width="150" align="right">
          <template #default="{ row }">{{ formatAmount(row.startAmount) }}</template>
        </el-table-column>
      </el-table>

      <div class="grand-total">
        <span>所有者权益合计</span>
        <span>{{ formatAmount(totalEquity.end) }}</span>
        <span>{{ formatAmount(totalEquity.start) }}</span>
      </div>
    </el-card>

    <!-- 校验 -->
    <el-card class="check-section">
      <template #header>
        <span>平衡校验</span>
      </template>
      <div class="check-result">
        <el-result 
          :icon="isBalanced ? 'success' : 'error'"
          :title="isBalanced ? '试算平衡' : '试算不平衡'"
          :sub-title="checkMessage"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import api from '@/api'

const selectedPeriod = ref('2024-03')
const periods = ref([
  { label: '2024年3月', value: '2024-03' },
  { label: '2024年2月', value: '2024-02' },
  { label: '2024年1月', value: '2024-01' }
])

// 流动资产
const currentAssets = ref([
  { name: '货币资金', endAmount: 528000, startAmount: 480000 },
  { name: '应收账款', endAmount: 156000, startAmount: 120000 },
  { name: '预付账款', endAmount: 32000, startAmount: 28000 },
  { name: '存货', endAmount: 89000, startAmount: 95000 }
])

const currentAssetsTotal = computed(() => ({
  end: currentAssets.value.reduce((sum, item) => sum + item.endAmount, 0),
  start: currentAssets.value.reduce((sum, item) => sum + item.startAmount, 0)
}))

// 非流动资产
const nonCurrentAssets = ref([
  { name: '固定资产', endAmount: 320000, startAmount: 350000 },
  { name: '无形资产', endAmount: 80000, startAmount: 85000 },
  { name: '长期待摊费用', endAmount: 15000, startAmount: 20000 }
])

const nonCurrentAssetsTotal = computed(() => ({
  end: nonCurrentAssets.value.reduce((sum, item) => sum + item.endAmount, 0),
  start: nonCurrentAssets.value.reduce((sum, item) => sum + item.startAmount, 0)
}))

const totalAssets = computed(() => ({
  end: currentAssetsTotal.value.end + nonCurrentAssetsTotal.value.end,
  start: currentAssetsTotal.value.start + nonCurrentAssetsTotal.value.start
}))

// 流动负债
const currentLiabilities = ref([
  { name: '应付账款', endAmount: 98000, startAmount: 85000 },
  { name: '预收账款', endAmount: 45000, startAmount: 42000 },
  { name: '应付职工薪酬', endAmount: 32000, startAmount: 30000 },
  { name: '应交税费', endAmount: 28000, startAmount: 25000 }
])

const currentLiabilitiesTotal = computed(() => ({
  end: currentLiabilities.value.reduce((sum, item) => sum + item.endAmount, 0),
  start: currentLiabilities.value.reduce((sum, item) => sum + item.startAmount, 0)
}))

const totalLiabilities = computed(() => currentLiabilitiesTotal.value)

// 所有者权益
const equity = ref([
  { name: '实收资本', endAmount: 500000, startAmount: 500000 },
  { name: '资本公积', endAmount: 50000, startAmount: 50000 },
  { name: '盈余公积', endAmount: 35000, startAmount: 28000 },
  { name: '未分配利润', endAmount: 390000, startAmount: 315000 }
])

const totalEquity = computed(() => ({
  end: equity.value.reduce((sum, item) => sum + item.endAmount, 0),
  start: equity.value.reduce((sum, item) => sum + item.startAmount, 0)
}))

// 平衡校验
const isBalanced = computed(() => {
  return totalAssets.value.end === (totalLiabilities.value.end + totalEquity.value.end)
})

const checkMessage = computed(() => {
  if (isBalanced.value) {
    return `资产 = 负债 + 所有者权益 = ${formatAmount(totalAssets.value.end)}`
  } else {
    const diff = totalAssets.value.end - (totalLiabilities.value.end + totalEquity.value.end)
    return `差额: ${formatAmount(diff)}`
  }
})

const formatAmount = (amount: number) => {
  return '¥' + amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const exportReport = () => {
  ElMessage.success('报表导出成功')
}
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

.check-section {
  margin-top: 20px;
}

.check-result {
  padding: 20px;
}
</style>