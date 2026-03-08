<template>
  <div class="customer-analytics">
    <div class="page-header">
      <h2>客户统计分析</h2>
      <el-select v-model="selectedCustomer" placeholder="选择客户" clearable @change="loadData">
        <el-option v-for="item in customerOptions" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>票据总数</span>
              <el-tag type="primary">本月</el-tag>
            </div>
          </template>
          <div class="stat-value">{{ stats.totalBills }}</div>
          <div class="stat-trend" :class="stats.billTrend >= 0 ? 'up' : 'down'">
            <span>{{ stats.billTrend >= 0 ? '↑' : '↓' }} {{ Math.abs(stats.billTrend) }}%</span>
            <span class="compare">环比</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>凭证总数</span>
              <el-tag type="success">本月</el-tag>
            </div>
          </template>
          <div class="stat-value">{{ stats.totalVouchers }}</div>
          <div class="stat-trend" :class="stats.voucherTrend >= 0 ? 'up' : 'down'">
            <span>{{ stats.voucherTrend >= 0 ? '↑' : '↓' }} {{ Math.abs(stats.voucherTrend) }}%</span>
            <span class="compare">环比</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>费用总额</span>
              <el-tag type="warning">本月</el-tag>
            </div>
          </template>
          <div class="stat-value">¥{{ formatAmount(stats.totalAmount) }}</div>
          <div class="stat-trend" :class="stats.amountTrend >= 0 ? 'up' : 'down'">
            <span>{{ stats.amountTrend >= 0 ? '↑' : '↓' }} {{ Math.abs(stats.amountTrend) }}%</span>
            <span class="compare">环比</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>待审核</span>
              <el-tag type="danger">待处理</el-tag>
            </div>
          </template>
          <div class="stat-value">{{ stats.pendingCount }}</div>
          <div class="stat-desc">
            <el-button type="primary" link @click="goToAudit">去审核 →</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>票据趋势</span>
          </template>
          <div ref="billTrendChart" class="chart"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>费用构成</span>
          </template>
          <div ref="expenseChart" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近票据 -->
    <el-card class="recent-bills">
      <template #header>
        <div class="card-header">
          <span>最近票据</span>
          <el-button type="primary" link @click="$router.push('/bills')">查看全部</el-button>
        </div>
      </template>
      <el-table :data="recentBills" stripe>
        <el-table-column prop="invoice_no" label="发票号码" width="150" />
        <el-table-column prop="seller_name" label="销售方" show-overflow-tooltip />
        <el-table-column prop="amount" label="金额" width="120">
          <template #default="{ row }">
            ¥{{ formatAmount(row.amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="invoice_date" label="开票日期" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import api from '@/api'

const router = useRouter()
const selectedCustomer = ref('')
const customerOptions = ref([
  { id: '1', name: '客户A' },
  { id: '2', name: '客户B' }
])

const stats = ref({
  totalBills: 128,
  billTrend: 15.3,
  totalVouchers: 96,
  voucherTrend: 8.7,
  totalAmount: 528000,
  amountTrend: -3.2,
  pendingCount: 12
})

const recentBills = ref([
  { invoice_no: '00123456', seller_name: 'ABC科技有限公司', amount: 15000, invoice_date: '2024-03-01', status: 'pending' },
  { invoice_no: '00123457', seller_name: 'DEF贸易公司', amount: 28000, invoice_date: '2024-03-02', status: 'approved' },
  { invoice_no: '00123458', seller_name: 'GHI实业有限公司', amount: 5600, invoice_date: '2024-03-03', status: 'pending' }
])

const billTrendChart = ref()
const expenseChart = ref()
let billChart: echarts.ECharts | null = null
let expChart: echarts.ECharts | null = null

const formatAmount = (amount: number) => {
  if (amount >= 10000) {
    return (amount / 10000).toFixed(2) + '万'
  }
  return amount.toLocaleString()
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝'
  }
  return map[status] || status
}

const goToAudit = () => {
  router.push('/audit')
}

const initCharts = () => {
  if (billTrendChart.value) {
    billChart = echarts.init(billTrendChart.value)
    billChart.setOption({
      xAxis: {
        type: 'category',
        data: ['1月', '2月', '3月', '4月', '5月', '6月']
      },
      yAxis: { type: 'value' },
      series: [{
        data: [120, 132, 101, 134, 90, 230],
        type: 'line',
        smooth: true,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
            ]
          }
        }
      }],
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true }
    })
  }

  if (expenseChart.value) {
    expChart = echarts.init(expenseChart.value)
    expChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: '0%' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: { show: false },
        emphasis: {
          label: { show: true, fontSize: 16, fontWeight: 'bold' }
        },
        data: [
          { value: 1048, name: '办公费用' },
          { value: 735, name: '差旅费用' },
          { value: 580, name: '招待费用' },
          { value: 484, name: '设备采购' },
          { value: 300, name: '其他' }
        ]
      }]
    })
  }
}

const loadData = () => {
  // 加载统计数据
}

const handleResize = () => {
  billChart?.resize()
  expChart?.resize()
}

onMounted(() => {
  initCharts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  billChart?.dispose()
  expChart?.dispose()
})
</script>

<style scoped>
.customer-analytics {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stat-cards {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin: 10px 0;
}

.stat-trend {
  font-size: 14px;
}

.stat-trend.up {
  color: #67C23A;
}

.stat-trend.down {
  color: #F56C6C;
}

.compare {
  margin-left: 8px;
  color: #909399;
}

.stat-desc {
  margin-top: 10px;
}

.chart-row {
  margin-bottom: 20px;
}

.chart {
  height: 300px;
}

.recent-bills {
  margin-top: 20px;
}
</style>