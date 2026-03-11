<template>
  <div class="dashboard">
    <!-- 欢迎语 -->
    <div class="welcome-section">
      <div class="welcome-content">
        <h1 class="welcome-title">
          <span class="wave-emoji">👋</span> 欢迎回来，{{ authStore.user?.name || authStore.user?.username }}
        </h1>
        <p class="welcome-subtitle">
          <el-icon><Sunny /></el-icon>
          今天是 {{ today }}，祝您工作顺利！
        </p>
      </div>
      <div class="welcome-decor"></div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="[20, 20]" class="stats-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card bills-card" @click="$router.push('/bills')">
          <div class="stat-card-bg"></div>
          <div class="stat-icon-wrapper">
            <div class="stat-icon">
              <el-icon :size="28"><Document /></el-icon>
            </div>
            <div class="stat-trend up">
              <el-icon><TrendCharts /></el-icon>
              <span>+12%</span>
            </div>
          </div>
          <div class="stat-content">
            <div class="stat-value">
              <CountUp :value="stats.billsCount" />
            </div>
            <div class="stat-label">票据总数</div>
          </div>
          <div class="stat-card-glow"></div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card vouchers-card" @click="$router.push('/vouchers')">
          <div class="stat-card-bg"></div>
          <div class="stat-icon-wrapper">
            <div class="stat-icon">
              <el-icon :size="28"><Tickets /></el-icon>
            </div>
            <div class="stat-trend up">
              <el-icon><TrendCharts /></el-icon>
              <span>+8%</span>
            </div>
          </div>
          <div class="stat-content">
            <div class="stat-value">
              <CountUp :value="stats.vouchersCount" />
            </div>
            <div class="stat-label">凭证总数</div>
          </div>
          <div class="stat-card-glow"></div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card pending-card" @click="$router.push('/audit')">
          <div class="stat-card-bg"></div>
          <div class="stat-icon-wrapper">
            <div class="stat-icon">
              <el-icon :size="28"><Clock /></el-icon>
            </div>
            <div class="stat-trend down">
              <el-icon><TrendCharts /></el-icon>
              <span>-5%</span>
            </div>
          </div>
          <div class="stat-content">
            <div class="stat-value">
              <CountUp :value="stats.pendingCount" />
            </div>
            <div class="stat-label">待审核</div>
          </div>
          <div class="stat-card-glow"></div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card approved-card">
          <div class="stat-card-bg"></div>
          <div class="stat-icon-wrapper">
            <div class="stat-icon">
              <el-icon :size="28"><CircleCheck /></el-icon>
            </div>
            <div class="stat-trend up">
              <el-icon><TrendCharts /></el-icon>
              <span>+24%</span>
            </div>
          </div>
          <div class="stat-content">
            <div class="stat-value">
              <CountUp :value="stats.approvedCount" />
            </div>
            <div class="stat-label">本月已审核</div>
          </div>
          <div class="stat-card-glow"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-row :gutter="20" class="section-row">
      <el-col :span="24">
        <el-card class="quick-actions" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><Promotion /></el-icon>
                <span>快捷操作</span>
              </div>
            </div>
          </template>
          <div class="action-buttons">
            <div class="action-item" @click="$router.push('/bills')">
              <div class="action-icon primary">
                <el-icon :size="24"><Plus /></el-icon>
              </div>
              <span class="action-text">上传票据</span>
              <span class="action-desc">上传发票、收据</span>
            </div>
            <div class="action-item" @click="$router.push('/vouchers')">
              <div class="action-icon success">
                <el-icon :size="24"><DocumentChecked /></el-icon>
              </div>
              <span class="action-text">生成凭证</span>
              <span class="action-desc">智能生成凭证</span>
            </div>
            <div class="action-item" @click="$router.push('/audit')">
              <div class="action-icon warning">
                <el-icon :size="24"><View /></el-icon>
              </div>
              <span class="action-text">审核工作台</span>
              <span class="action-desc">审批待处理任务</span>
            </div>
            <div class="action-item" @click="$router.push('/reports')">
              <div class="action-icon info">
                <el-icon :size="24"><DataAnalysis /></el-icon>
              </div>
              <span class="action-text">数据报表</span>
              <span class="action-desc">查看统计报表</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 审核统计图表和最近活动 -->
    <el-row :gutter="20" class="section-row">
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><PieChart /></el-icon>
                <span>审核状态分布</span>
              </div>
              <div class="header-stats" v-if="totalCount > 0">
                <span class="total-badge">总计: {{ totalCount }}</span>
              </div>
            </div>
          </template>
          <div class="chart-wrapper">
            <!-- 环形图 -->
            <div class="donut-chart" v-if="totalCount > 0">
              <div class="donut-center">
                <div class="donut-value">{{ totalCount }}</div>
                <div class="donut-label">总票据</div>
              </div>
              <svg viewBox="0 0 100 100" class="donut-svg">
                <circle cx="50" cy="50" r="40" fill="none" stroke="#ebeef5" stroke-width="12"/>
                <circle 
                  cx="50" cy="50" r="40" fill="none" 
                  stroke="#909399" stroke-width="12"
                  :stroke-dasharray="getDonutSegment(draftCount, totalCount)"
                  stroke-dashoffset="0"
                  transform="rotate(-90 50 50)"
                />
                <circle 
                  cx="50" cy="50" r="40" fill="none" 
                  stroke="#E6A23C" stroke-width="12"
                  :stroke-dasharray="getDonutSegment(pendingCount, totalCount)"
                  :stroke-dashoffset="'-' + getDonutOffset(draftCount, totalCount)"
                  transform="rotate(-90 50 50)"
                />
                <circle 
                  cx="50" cy="50" r="40" fill="none" 
                  stroke="#67C23A" stroke-width="12"
                  :stroke-dasharray="getDonutSegment(approvedCount, totalCount)"
                  :stroke-dashoffset="'-' + getDonutOffset(draftCount + pendingCount, totalCount)"
                  transform="rotate(-90 50 50)"
                />
                <circle 
                  cx="50" cy="50" r="40" fill="none" 
                  stroke="#F56C6C" stroke-width="12"
                  :stroke-dasharray="getDonutSegment(rejectedCount, totalCount)"
                  :stroke-dashoffset="'-' + getDonutOffset(draftCount + pendingCount + approvedCount, totalCount)"
                  transform="rotate(-90 50 50)"
                />
              </svg>
            </div>
            <!-- 图例 -->
            <div class="chart-legend" v-if="totalCount > 0">
              <div class="legend-item">
                <span class="legend-dot" style="background: #909399"></span>
                <span class="legend-label">草稿</span>
                <span class="legend-value">{{ draftCount }}</span>
                <span class="legend-percent">{{ calculatePercentage(draftCount) }}%</span>
              </div>
              <div class="legend-item">
                <span class="legend-dot" style="background: #E6A23C"></span>
                <span class="legend-label">待审核</span>
                <span class="legend-value">{{ pendingCount }}</span>
                <span class="legend-percent">{{ calculatePercentage(pendingCount) }}%</span>
              </div>
              <div class="legend-item">
                <span class="legend-dot" style="background: #67C23A"></span>
                <span class="legend-label">已通过</span>
                <span class="legend-value">{{ approvedCount }}</span>
                <span class="legend-percent">{{ calculatePercentage(approvedCount) }}%</span>
              </div>
              <div class="legend-item">
                <span class="legend-dot" style="background: #F56C6C"></span>
                <span class="legend-label">已拒绝</span>
                <span class="legend-value">{{ rejectedCount }}</span>
                <span class="legend-percent">{{ calculatePercentage(rejectedCount) }}%</span>
              </div>
            </div>
            <el-empty v-else description="暂无数据" :image-size="80" />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card class="recent-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><Clock /></el-icon>
                <span>最近上传的票据</span>
              </div>
              <el-button text type="primary" @click="$router.push('/bills')">
                查看更多 <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="recent-list">
            <TransitionGroup name="list" tag="div">
              <div v-for="item in recentBills" :key="item.id" class="recent-item">
                <div class="recent-icon" :class="getStatusClass(item.process_status)">
                  <el-icon><Document /></el-icon>
                </div>
                <div class="recent-content">
                  <div class="recent-title">{{ item.seller_name || '未知销售方' }}</div>
                  <div class="recent-meta">
                    <span class="amount">¥{{ formatAmount(item.total_amount) }}</span>
                    <el-tag :type="getStatusType(item.process_status)" size="small" effect="dark">
                      {{ getStatusText(item.process_status) }}
                    </el-tag>
                  </div>
                </div>
                <div class="recent-time">
                  <el-icon><Calendar /></el-icon>
                  {{ formatDate(item.created_at) }}
                </div>
              </div>
            </TransitionGroup>
            <el-empty v-if="recentBills.length === 0" description="暂无数据" :image-size="80" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 工作流指南 -->
    <el-row :gutter="20" class="section-row">
      <el-col :span="24">
        <el-card class="workflow-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><List /></el-icon>
                <span>工作流程</span>
              </div>
            </div>
          </template>
          <div class="workflow-steps">
            <div class="step-item" v-for="(step, index) in workflowSteps" :key="index">
              <div class="step-connector" v-if="index > 0"></div>
              <div class="step-number" :style="{ background: step.color }">
                <el-icon :size="20"><component :is="step.icon" /></el-icon>
              </div>
              <div class="step-content">
                <div class="step-title">{{ step.title }}</div>
                <div class="step-desc">{{ step.desc }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, h } from 'vue'
import { useAuthStore } from '../../stores/auth'
import api from '../../api/index'
import { ElMessage } from 'element-plus'
import {
  Document, Tickets, Clock, CircleCheck,
  Plus, DocumentChecked, View, ArrowRight,
  Sunny, TrendCharts, Promotion, DataAnalysis,
  PieChart, Calendar, List, Upload, MagicStick,
  Coin, Check
} from '@element-plus/icons-vue'

// 数字动画组件
const CountUp = (props: { value: number }) => {
  const displayValue = ref(0)
  
  onMounted(() => {
    const duration = 1000
    const start = 0
    const end = props.value
    const startTime = performance.now()
    
    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)
      // 缓动函数
      const easeOutQuart = 1 - Math.pow(1 - progress, 4)
      displayValue.value = Math.floor(start + (end - start) * easeOutQuart)
      
      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }
    
    requestAnimationFrame(animate)
  })
  
  return h('span', displayValue.value.toLocaleString())
}

const authStore = useAuthStore()

// 统计数据
const stats = ref({
  billsCount: 0,
  vouchersCount: 0,
  pendingCount: 0,
  approvedCount: 0
})

const auditStats = ref<any>({
  overview: { draft_count: 0, pending_count: 0, approved_count: 0, rejected_count: 0 },
  performance: { today_approved: 0, month_approved: 0 }
})

const recentBills = ref<any[]>([])

// 工作流步骤
const workflowSteps = [
  { icon: Upload, title: '上传票据', desc: '上传发票、收据等原始凭证', color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { icon: MagicStick, title: 'AI识别', desc: '自动提取票据信息', color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
  { icon: Coin, title: '生成凭证', desc: '智能生成记账凭证', color: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)' },
  { icon: Check, title: '审核确认', desc: '审核凭证并确认', color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }
]

// 今天的日期
const today = computed(() => {
  const date = new Date()
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
})

// 计算百分比
const totalCount = computed(() => {
  const o = auditStats.value.overview
  return o.draft_count + o.pending_count + o.approved_count + o.rejected_count || 1
})

// 各状态数量
const draftCount = computed(() => auditStats.value.overview?.draft_count || 0)
const pendingCount = computed(() => auditStats.value.overview?.pending_count || 0)
const approvedCount = computed(() => auditStats.value.overview?.approved_count || 0)
const rejectedCount = computed(() => auditStats.value.overview?.rejected_count || 0)

const calculatePercentage = (count: number) => {
  return Math.round((count / totalCount.value) * 100)
}

// 环形图相关函数
const getDonutSegment = (count: number, total: number) => {
  if (total === 0) return '0 251.2'
  const percent = count / total
  const circumference = 2 * Math.PI * 40 // r=40
  const segment = circumference * percent
  return `${segment} ${circumference}`
}

const getDonutOffset = (count: number, total: number) => {
  if (total === 0) return 0
  const percent = count / total
  const circumference = 2 * Math.PI * 40
  return circumference * percent
}

// 格式化金额
const formatAmount = (amount: number | null) => {
  if (!amount) return '0.00'
  return Number(amount).toFixed(2)
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

// 状态类型
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    'pending': 'info',
    'ocr_pending': 'warning',
    'ocr_completed': 'success',
    'ocr_failed': 'danger',
    'voucher_generated': 'primary'
  }
  return map[status] || 'info'
}

// 状态样式类
const getStatusClass = (status: string) => {
  const map: Record<string, string> = {
    'pending': 'status-pending',
    'ocr_pending': 'status-pending',
    'ocr_completed': 'status-success',
    'ocr_failed': 'status-danger',
    'voucher_generated': 'status-primary'
  }
  return map[status] || 'status-default'
}

// 状态文本
const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    'pending': '待处理',
    'ocr_pending': 'OCR识别中',
    'ocr_completed': 'OCR完成',
    'ocr_failed': '识别失败',
    'voucher_generated': '已生成凭证'
  }
  return map[status] || status
}

// 获取数据
const fetchData = async () => {
  try {
    // 获取审核统计
    const auditRes = await api.get('/audit/statistics')
    if (auditRes.data) {
      auditStats.value = auditRes.data
      stats.value.pendingCount = auditRes.data.overview?.pending_count || 0
      stats.value.approvedCount = auditRes.data.performance?.month_approved || 0
    }

    // 获取票据列表（最近5条）
    const billsRes = await api.get('/invoices?page_size=5')
    if (billsRes.data?.items) {
      recentBills.value = billsRes.data.items
      stats.value.billsCount = billsRes.data.total || 0
    }

    // 获取凭证列表（失败不影响其他数据）
    try {
      const vouchersRes = await api.get('/vouchers?page_size=1')
      if (vouchersRes.data) {
        stats.value.vouchersCount = vouchersRes.data.total || 0
      }
    } catch (voucherError) {
      console.log('凭证数据获取失败（无权限或错误）:', voucherError)
      stats.value.vouchersCount = 0
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败，请稍后重试')
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.dashboard {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

/* 欢迎区域 */
.welcome-section {
  position: relative;
  margin-bottom: 28px;
  padding: 28px 32px;
  background: linear-gradient(135deg, var(--sl-primary, #3b5cf5) 0%, #6366f1 100%);
  border-radius: 16px;
  overflow: hidden;
}

.welcome-content {
  position: relative;
  z-index: 1;
}

.welcome-title {
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.wave-emoji {
  display: inline-block;
  animation: wave 1s ease-in-out infinite;
}

@keyframes wave {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(20deg); }
  75% { transform: rotate(-20deg); }
}

.welcome-subtitle {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.welcome-decor {
  position: absolute;
  right: -50px;
  top: -50px;
  width: 200px;
  height: 200px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
}

/* 统计卡片 */
.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 24px;
  border-radius: 16px;
  background: var(--sl-bg-card, #fff);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  cursor: pointer;
  border: 1px solid var(--sl-border, #e5e7eb);
}

.stat-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
}

.stat-card:hover .stat-card-glow {
  opacity: 1;
}

.stat-card:hover .stat-icon {
  transform: scale(1.1) rotate(5deg);
}

.stat-card-bg {
  position: absolute;
  top: 0;
  right: 0;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  opacity: 0.15;
  transform: translate(30%, -30%);
}

.bills-card .stat-card-bg { background: #667eea; }
.vouchers-card .stat-card-bg { background: #11998e; }
.pending-card .stat-card-bg { background: #f5576c; }
.approved-card .stat-card-bg { background: #4facfe; }

.stat-card-glow {
  position: absolute;
  bottom: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.4s;
  pointer-events: none;
}

.stat-icon-wrapper {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 14px;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.bills-card .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.vouchers-card .stat-icon {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: #fff;
  box-shadow: 0 8px 20px rgba(17, 153, 142, 0.4);
}

.pending-card .stat-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: #fff;
  box-shadow: 0 8px 20px rgba(245, 87, 108, 0.4);
}

.approved-card .stat-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: #fff;
  box-shadow: 0 8px 20px rgba(79, 172, 254, 0.4);
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.stat-trend.up {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.stat-trend.down {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--sl-text-primary, #1f2937);
  line-height: 1.2;
  margin-bottom: 6px;
  font-variant-numeric: tabular-nums;
}

.stat-label {
  font-size: 14px;
  color: var(--sl-text-secondary, #6b7280);
  font-weight: 500;
}

/* 通用区域 */
.section-row {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  font-size: 18px;
  color: var(--sl-primary, #3b5cf5);
}

/* 快捷操作 */
.quick-actions :deep(.el-card__body) {
  padding: 24px;
}

.action-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 16px;
  border-radius: 12px;
  background: var(--sl-bg-main, #f8f9fc);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.action-item:hover {
  transform: translateY(-4px);
  background: #fff;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border-color: var(--sl-primary, #3b5cf5);
}

.action-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 14px;
  margin-bottom: 14px;
  transition: transform 0.3s ease;
}

.action-item:hover .action-icon {
  transform: scale(1.1);
}

.action-icon.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.35);
}

.action-icon.success {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: #fff;
  box-shadow: 0 6px 16px rgba(17, 153, 142, 0.35);
}

.action-icon.warning {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: #fff;
  box-shadow: 0 6px 16px rgba(245, 87, 108, 0.35);
}

.action-icon.info {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: #fff;
  box-shadow: 0 6px 16px rgba(79, 172, 254, 0.35);
}

.action-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--sl-text-primary, #1f2937);
  margin-bottom: 6px;
}

.action-desc {
  font-size: 13px;
  color: var(--sl-text-secondary, #6b7280);
}

/* 图表卡片 */
.chart-wrapper {
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 16px 0;
}

.donut-chart {
  position: relative;
  width: 180px;
  height: 180px;
  flex-shrink: 0;
}

.donut-svg {
  width: 100%;
  height: 100%;
  transform: rotate(0deg);
}

.donut-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.donut-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--sl-text-primary, #1f2937);
}

.donut-label {
  font-size: 12px;
  color: var(--sl-text-secondary, #6b7280);
  margin-top: 2px;
}

.chart-legend {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  background: var(--sl-bg-main, #f8f9fc);
  transition: all 0.2s ease;
}

.legend-item:hover {
  background: var(--sl-fill-color-light, #f3f4f6);
  transform: translateX(4px);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-label {
  flex: 1;
  font-size: 14px;
  color: var(--sl-text-regular, #4b5563);
}

.legend-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--sl-text-primary, #1f2937);
  min-width: 40px;
  text-align: right;
}

.legend-percent {
  font-size: 12px;
  color: var(--sl-text-secondary, #6b7280);
  min-width: 36px;
  text-align: right;
}

.total-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  background: linear-gradient(135deg, var(--sl-primary, #3b5cf5) 0%, #6366f1 100%);
  color: #fff;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

/* 最近活动 */
.recent-list {
  padding: 8px 0;
}

.recent-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 12px;
  background: var(--sl-bg-main, #f8f9fc);
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.recent-item:last-child {
  margin-bottom: 0;
}

.recent-item:hover {
  background: #fff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border-color: var(--sl-border, #e5e7eb);
  transform: translateX(4px);
}

.recent-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #f0f9ff;
  color: #409eff;
  margin-right: 14px;
  flex-shrink: 0;
  transition: transform 0.3s ease;
}

.recent-item:hover .recent-icon {
  transform: scale(1.1);
}

.recent-icon.status-success {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}

.recent-icon.status-danger {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}

.recent-icon.status-pending {
  background: rgba(245, 158, 11, 0.12);
  color: #f59e0b;
}

.recent-icon.status-primary {
  background: rgba(59, 92, 245, 0.12);
  color: #3b5cf5;
}

.recent-content {
  flex: 1;
  min-width: 0;
}

.recent-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--sl-text-primary, #1f2937);
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.recent-meta .amount {
  font-size: 13px;
  color: var(--sl-text-secondary, #6b7280);
  font-weight: 500;
}

.recent-time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--sl-text-secondary, #9ca3af);
  flex-shrink: 0;
}

/* 工作流 */
.workflow-card :deep(.el-card__body) {
  padding: 24px;
}

.workflow-steps {
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  gap: 12px;
  flex-wrap: nowrap;
}

.step-item {
  display: flex;
  align-items: center;
  flex: 1;
  position: relative;
}

.step-connector {
  position: absolute;
  left: 0;
  top: 50%;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, var(--sl-primary, #3b5cf5) 0%, #e5e7eb 100%);
  transform: translateY(-50%);
  z-index: 0;
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 14px;
  color: #fff;
  font-size: 20px;
  font-weight: 600;
  margin-right: 14px;
  flex-shrink: 0;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 1;
  transition: transform 0.3s ease;
}

.step-item:hover .step-number {
  transform: scale(1.1);
}

.step-content {
  flex: 1;
}

.step-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--sl-text-primary, #1f2937);
  margin-bottom: 4px;
}

.step-desc {
  font-size: 12px;
  color: var(--sl-text-secondary, #6b7280);
  line-height: 1.4;
}

/* 列表动画 */
.list-enter-active,
.list-leave-active {
  transition: all 0.4s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* 响应式 */
@media (max-width: 1200px) {
  .workflow-steps {
    flex-wrap: wrap;
  }
  
  .step-item {
    flex: none;
    width: calc(50% - 6px);
  }
  
  .step-connector {
    display: none;
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 16px;
  }
  
  .welcome-section {
    padding: 20px;
    margin-bottom: 20px;
  }
  
  .welcome-title {
    font-size: 20px;
  }
  
  .welcome-subtitle {
    font-size: 13px;
    flex-wrap: wrap;
  }
  
  .stat-card {
    margin-bottom: 0;
    padding: 20px;
  }
  
  .stat-icon-wrapper {
    margin-bottom: 16px;
  }
  
  .stat-icon {
    width: 48px;
    height: 48px;
  }
  
  .stat-value {
    font-size: 26px;
  }
  
  .stat-label {
    font-size: 13px;
  }
  
  .chart-wrapper {
    flex-direction: column;
  }
  
  .donut-chart {
    width: 160px;
    height: 160px;
  }
  
  .chart-legend {
    width: 100%;
  }
  
  .legend-item {
    padding: 8px 12px;
  }
  
  .action-buttons {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .step-item {
    width: 100%;
  }
  
  .action-item {
    padding: 16px 12px;
  }
  
  .action-icon {
    width: 48px;
    height: 48px;
  }
  
  .action-text {
    font-size: 14px;
  }
  
  .action-desc {
    font-size: 12px;
  }
  
  .card-header {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .recent-item {
    padding: 12px;
  }
  
  .recent-icon {
    width: 40px;
    height: 40px;
  }
  
  .recent-title {
    font-size: 14px;
  }
  
  .recent-meta {
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .workflow-card :deep(.el-card__body) {
    padding: 16px;
  }
  
  .step-number {
    width: 44px;
    height: 44px;
  }
  
  .step-title {
    font-size: 14px;
  }
  
  .step-desc {
    font-size: 11px;
  }
}

/* 超小屏幕优化 */
@media (max-width: 480px) {
  .dashboard {
    padding: 12px;
  }
  
  .welcome-section {
    padding: 16px;
  }
  
  .welcome-title {
    font-size: 18px;
  }
  
  .welcome-subtitle {
    font-size: 12px;
  }
  
  .stat-value {
    font-size: 22px;
  }
  
  .stat-icon {
    width: 40px;
    height: 40px;
  }
  
  .stat-icon :deep(.el-icon) {
    font-size: 20px !important;
  }
  
  .action-buttons {
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }
  
  .action-item {
    padding: 12px 8px;
  }
  
  .action-icon {
    width: 40px;
    height: 40px;
    margin-bottom: 10px;
  }
  
  .action-icon :deep(.el-icon) {
    font-size: 18px !important;
  }
  
  .donut-chart {
    width: 140px;
    height: 140px;
  }
  
  .donut-value {
    font-size: 22px;
  }
  
  .recent-item {
    flex-wrap: wrap;
  }
  
  .recent-time {
    width: 100%;
    margin-top: 8px;
  }
  
  .workflow-steps {
    flex-direction: column;
    gap: 16px;
  }
  
  .step-item {
    width: 100%;
  }
  
  .step-number {
    width: 40px;
    height: 40px;
  }
}

/* 深色模式适配 */
html.dark {
  .stat-card {
    background: var(--sl-bg-card, #1e293b);
  }
  
  .action-item {
    background: #1e293b;
  }
  
  .action-item:hover {
    background: #334155;
  }
  
  .recent-item {
    background: #1e293b;
  }
  
  .recent-item:hover {
    background: #334155;
  }
  
  .legend-item {
    background: #1e293b;
  }
  
  .welcome-section {
    background: linear-gradient(135deg, #4f46e5 0%, #818cf8 100%);
  }
}
</style>
