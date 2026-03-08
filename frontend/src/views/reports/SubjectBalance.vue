<template>
  <div class="subject-balance">
    <div class="page-header">
      <h2>科目余额表</h2>
      <div class="header-actions">
        <el-select v-model="selectedPeriod" placeholder="选择账期">
          <el-option v-for="item in periods" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-input v-model="searchKeyword" placeholder="搜索科目" clearable style="width: 200px" />
        <el-button type="primary" @click="exportReport">
          <el-icon><Download /></el-icon>导出
        </el-button>
      </div>
    </div>

    <div class="report-header">
      <h3>科目余额表</h3>
      <p>账期: {{ selectedPeriod }} | 单位: 元</p>
    </div>

    <!-- 试算平衡 -->
    <el-card class="balance-check">
      <template #header>
        <span>试算平衡</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="check-item">
            <label>期初借方合计</label>
            <div class="amount">{{ formatAmount(totalOpenDebit) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="check-item">
            <label>期初贷方合计</label>
            <div class="amount">{{ formatAmount(totalOpenCredit) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="check-item">
            <label>本期借方合计</label>
            <div class="amount">{{ formatAmount(totalPeriodDebit) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="check-item">
            <label>本期贷方合计</label>
            <div class="amount">{{ formatAmount(totalPeriodCredit) }}</div>
          </div>
        </el-col>
      </el-row>
      <el-divider />
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="check-item">
            <label>期末借方合计</label>
            <div class="amount">{{ formatAmount(totalCloseDebit) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="check-item">
            <label>期末贷方合计</label>
            <div class="amount">{{ formatAmount(totalCloseCredit) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="check-item">
            <label>平衡状态</label>
            <div class="status">
              <el-tag :type="isBalanced ? 'success' : 'danger'" size="large">
                {{ isBalanced ? '✓ 平衡' : '✗ 不平衡' }}
              </el-tag>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="check-item">
            <label>差额</label>
            <div class="amount" :class="difference === 0 ? 'balanced' : 'unbalanced'">
              {{ formatAmount(difference) }}
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 科目余额表 -->
    <el-card class="subject-table">
      <template #header>
        <span>科目明细</span>
      </template>
      <el-table :data="filteredSubjects" stripe border
        :default-sort="{ prop: 'code', order: 'ascending' }"
        row-key="code"
        :tree-props="{ children: 'children' }"
      >
        <el-table-column prop="code" label="科目代码" width="120" sortable />
        <el-table-column prop="name" label="科目名称" min-width="180">
          <template #default="{ row }">
            <span :style="{ paddingLeft: row.level * 20 + 'px' }">
              {{ row.name }}
            </span>
          </template>
        </el-table-column>

        <!-- 期初余额 -->
        <el-table-column label="期初余额" align="center">
          <el-table-column prop="openDebit" label="借方" width="120" align="right">
            <template #default="{ row }">
              {{ row.openDebit > 0 ? formatAmount(row.openDebit) : '' }}
            </template>
          </el-table-column>
          <el-table-column prop="openCredit" label="贷方" width="120" align="right">
            <template #default="{ row }">
              {{ row.openCredit > 0 ? formatAmount(row.openCredit) : '' }}
            </template>
          </el-table-column>
        </el-table-column>

        <!-- 本期发生额 -->
        <el-table-column label="本期发生额" align="center">
          <el-table-column prop="periodDebit" label="借方" width="120" align="right">
            <template #default="{ row }">
              {{ row.periodDebit > 0 ? formatAmount(row.periodDebit) : '' }}
            </template>
          </el-table-column>
          <el-table-column prop="periodCredit" label="贷方" width="120" align="right">
            <template #default="{ row }">
              {{ row.periodCredit > 0 ? formatAmount(row.periodCredit) : '' }}
            </template>
          </el-table-column>
        </el-table-column>

        <!-- 期末余额 -->
        <el-table-column label="期末余额" align="center">
          <el-table-column prop="closeDebit" label="借方" width="120" align="right">
            <template #default="{ row }">
              {{ row.closeDebit > 0 ? formatAmount(row.closeDebit) : '' }}
            </template>
          </el-table-column>
          <el-table-column prop="closeCredit" label="贷方" width="120" align="right">
            <template #default="{ row }">
              {{ row.closeCredit > 0 ? formatAmount(row.closeCredit) : '' }}
            </template>
          </el-table-column>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'

const selectedPeriod = ref('2024-03')
const searchKeyword = ref('')
const periods = ref([
  { label: '2024年3月', value: '2024-03' },
  { label: '2024年2月', value: '2024-02' },
  { label: '2024年1月', value: '2024-01' }
])

// 科目数据
const subjects = ref([
  // 资产类
  { code: '1001', name: '库存现金', level: 0, openDebit: 50000, openCredit: 0, periodDebit: 150000, periodCredit: 130000, closeDebit: 70000, closeCredit: 0 },
  { code: '1002', name: '银行存款', level: 0, openDebit: 450000, openCredit: 0, periodDebit: 850000, periodCredit: 680000, closeDebit: 620000, closeCredit: 0 },
  { code: '1101', name: '交易性金融资产', level: 0, openDebit: 100000, openCredit: 0, periodDebit: 50000, periodCredit: 30000, closeDebit: 120000, closeCredit: 0 },
  { code: '1121', name: '应收票据', level: 0, openDebit: 80000, openCredit: 0, periodDebit: 200000, periodCredit: 150000, closeDebit: 130000, closeCredit: 0 },
  { code: '1122', name: '应收账款', level: 0, openDebit: 120000, openCredit: 0, periodDebit: 450000, periodCredit: 380000, closeDebit: 190000, closeCredit: 0 },
  { code: '1231', name: '坏账准备', level: 0, openDebit: 0, openCredit: 5000, periodDebit: 2000, periodCredit: 3000, closeDebit: 0, closeCredit: 6000 },
  { code: '1403', name: '原材料', level: 0, openDebit: 200000, openCredit: 0, periodDebit: 500000, periodCredit: 520000, closeDebit: 180000, closeCredit: 0 },
  { code: '1405', name: '库存商品', level: 0, openDebit: 150000, openCredit: 0, periodDebit: 800000, periodCredit: 750000, closeDebit: 200000, closeCredit: 0 },
  { code: '1601', name: '固定资产', level: 0, openDebit: 800000, openCredit: 0, periodDebit: 200000, periodCredit: 50000, closeDebit: 950000, closeCredit: 0 },
  { code: '1602', name: '累计折旧', level: 0, openDebit: 0, openCredit: 200000, periodDebit: 0, periodCredit: 80000, closeDebit: 0, closeCredit: 280000 },
  
  // 负债类
  { code: '2001', name: '短期借款', level: 0, openDebit: 0, openCredit: 300000, periodDebit: 150000, periodCredit: 200000, closeDebit: 0, closeCredit: 350000 },
  { code: '2201', name: '应付票据', level: 0, openDebit: 0, openCredit: 80000, periodDebit: 50000, periodCredit: 70000, closeDebit: 0, closeCredit: 100000 },
  { code: '2202', name: '应付账款', level: 0, openDebit: 0, openCredit: 150000, periodDebit: 200000, periodCredit: 280000, closeDebit: 0, closeCredit: 230000 },
  { code: '2211', name: '应付职工薪酬', level: 0, openDebit: 0, openCredit: 50000, periodDebit: 180000, periodCredit: 192000, closeDebit: 0, closeCredit: 62000 },
  { code: '2221', name: '应交税费', level: 0, openDebit: 0, openCredit: 30000, periodDebit: 85000, periodCredit: 88000, closeDebit: 0, closeCredit: 33000 },
  
  // 所有者权益
  { code: '4001', name: '实收资本', level: 0, openDebit: 0, openCredit: 1000000, periodDebit: 0, periodCredit: 0, closeDebit: 0, closeCredit: 1000000 },
  { code: '4103', name: '本年利润', level: 0, openDebit: 0, openCredit: 150000, periodDebit: 500000, periodCredit: 620000, closeDebit: 0, closeCredit: 270000 },
  { code: '4104', name: '利润分配', level: 0, openDebit: 0, openCredit: 50000, periodDebit: 30000, periodCredit: 50000, closeDebit: 0, closeCredit: 70000 },
  
  // 成本类
  { code: '5001', name: '生产成本', level: 0, openDebit: 100000, openCredit: 0, periodDebit: 600000, periodCredit: 580000, closeDebit: 120000, closeCredit: 0 },
  { code: '5101', name: '制造费用', level: 0, openDebit: 20000, openCredit: 0, periodDebit: 150000, periodCredit: 150000, closeDebit: 20000, closeCredit: 0 },
  
  // 损益类
  { code: '6001', name: '主营业务收入', level: 0, openDebit: 0, openCredit: 0, periodDebit: 500000, periodCredit: 800000, closeDebit: 0, closeCredit: 300000 },
  { code: '6401', name: '主营业务成本', level: 0, openDebit: 0, openCredit: 0, periodDebit: 480000, periodCredit: 480000, closeDebit: 0, closeCredit: 0 },
  { code: '6601', name: '销售费用', level: 0, openDebit: 0, openCredit: 0, periodDebit: 45000, periodCredit: 45000, closeDebit: 0, closeCredit: 0 },
  { code: '6602', name: '管理费用', level: 0, openDebit: 0, openCredit: 0, periodDebit: 68000, periodCredit: 68000, closeDebit: 0, closeCredit: 0 },
  { code: '6603', name: '财务费用', level: 0, openDebit: 0, openCredit: 0, periodDebit: 8000, periodCredit: 8000, closeDebit: 0, closeCredit: 0 }
])

// 过滤
const filteredSubjects = computed(() => {
  if (!searchKeyword.value) return subjects.value
  const keyword = searchKeyword.value.toLowerCase()
  return subjects.value.filter(s => 
    s.code.includes(keyword) || 
    s.name.toLowerCase().includes(keyword)
  )
})

// 计算合计
const totalOpenDebit = computed(() => subjects.value.reduce((sum, s) => sum + s.openDebit, 0))
const totalOpenCredit = computed(() => subjects.value.reduce((sum, s) => sum + s.openCredit, 0))
const totalPeriodDebit = computed(() => subjects.value.reduce((sum, s) => sum + s.periodDebit, 0))
const totalPeriodCredit = computed(() => subjects.value.reduce((sum, s) => sum + s.periodCredit, 0))
const totalCloseDebit = computed(() => subjects.value.reduce((sum, s) => sum + s.closeDebit, 0))
const totalCloseCredit = computed(() => subjects.value.reduce((sum, s) => sum + s.closeCredit, 0))

const isBalanced = computed(() => {
  return totalOpenDebit.value === totalOpenCredit.value &&
         totalPeriodDebit.value === totalPeriodCredit.value &&
         totalCloseDebit.value === totalCloseCredit.value
})

const difference = computed(() => {
  return Math.abs(totalCloseDebit.value - totalCloseCredit.value)
})

const formatAmount = (amount: number) => {
  return '¥' + amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const exportReport = () => {
  ElMessage.success('报表导出成功')
}
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

.check-item .amount.balanced {
  color: #67C23A;
}

.check-item .amount.unbalanced {
  color: #F56C6C;
}

.check-item .status {
  margin-top: 5px;
}

.subject-table {
  margin-top: 20px;
}
</style>