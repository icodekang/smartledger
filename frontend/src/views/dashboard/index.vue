<template>
  <div class="dashboard">
    <!-- 欢迎语 -->
    <div class="welcome-section">
      <h1 class="welcome-title">👋 欢迎回来，{{ authStore.user?.name || authStore.user?.username }}</h1>
      <p class="welcome-subtitle">今天是 {{ today }}，祝您工作顺利！</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card bills-card">
          <div class="stat-icon">
            <el-icon :size="40"><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.billsCount }}</div>
            <div class="stat-label">票据总数</div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card vouchers-card">
          <div class="stat-icon">
            <el-icon :size="40"><Tickets /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.vouchersCount }}</div>
            <div class="stat-label">凭证总数</div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card pending-card">
          <div class="stat-icon">
            <el-icon :size="40"><Clock /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.pendingCount }}</div>
            <div class="stat-label">待审核</div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card approved-card">
          <div class="stat-icon">
            <el-icon :size="40"><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.approvedCount }}</div>
            <div class="stat-label">本月已审核</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-row :gutter="20" class="section-row">
      <el-col :span="24">
        <el-card class="quick-actions">
          <template #header>
            <div class="card-header">
              <span>⚡ 快捷操作</span>
            </div>
          </template>
          <div class="action-buttons">
            <el-button type="primary" size="large" @click="$router.push('/bills')">
              <el-icon><Plus /></el-icon>
              上传票据
            </el-button>
            <el-button type="success" size="large" @click="$router.push('/vouchers')">
              <el-icon><DocumentChecked /></el-icon>
              生成凭证
            </el-button>
            <el-button type="warning" size="large" @click="$router.push('/audit')">
              <el-icon><View /></el-icon>
              审核工作台
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 审核统计图表和最近活动 -->
    <el-row :gutter="20" class="section-row">
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>📊 审核状态分布</span>
            </div>
          </template>
          <div class="chart-container">
            <div v-if="auditStats.overview" class="progress-list">
              <div class="progress-item">
                <div class="progress-label">
                  <span>草稿</span>
                  <span>{{ auditStats.overview.draft_count || 0 }}</span>
                </div>
                <el-progress 
                  :percentage="calculatePercentage(auditStats.overview.draft_count)" 
                  :color="'#909399'"
                  :stroke-width="16"
                  :show-text="false"
                />
              </div>
              <div class="progress-item">
                <div class="progress-label">
                  <span>待审核</span>
                  <span>{{ auditStats.overview.pending_count || 0 }}</span>
                </div>
                <el-progress 
                  :percentage="calculatePercentage(auditStats.overview.pending_count)" 
                  :color="'#E6A23C'"
                  :stroke-width="16"
                  :show-text="false"
                />
              </div>
              <div class="progress-item">
                <div class="progress-label">
                  <span>已通过</span>
                  <span>{{ auditStats.overview.approved_count || 0 }}</span>
                </div>
                <el-progress 
                  :percentage="calculatePercentage(auditStats.overview.approved_count)" 
                  :color="'#67C23A'"
                  :stroke-width="16"
                  :show-text="false"
                />
              </div>
              <div class="progress-item">
                <div class="progress-label">
                  <span>已拒绝</span>
                  <span>{{ auditStats.overview.rejected_count || 0 }}</span>
                </div>
                <el-progress 
                  :percentage="calculatePercentage(auditStats.overview.rejected_count)" 
                  :color="'#F56C6C'"
                  :stroke-width="16"
                  :show-text="false"
                />
              </div>
            </div>
            <el-empty v-else description="暂无数据" />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card class="recent-card">
          <template #header>
            <div class="card-header">
              <span>🕐 最近上传的票据</span>
              <el-button text @click="$router.push('/bills')">查看更多</el-button>
            </div>
          </template>
          <div class="recent-list">
            <div v-for="item in recentBills" :key="item.id" class="recent-item">
              <div class="recent-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="recent-content">
                <div class="recent-title">{{ item.seller_name || '未知销售方' }}</div>
                <div class="recent-meta">
                  <span>金额: ¥{{ formatAmount(item.total_amount) }}</span>
                  <el-tag :type="getStatusType(item.process_status)" size="small">
                    {{ getStatusText(item.process_status) }}
                  </el-tag>
                </div>
              </div>
              <div class="recent-time">{{ formatDate(item.created_at) }}</div>
            </div>
            <el-empty v-if="recentBills.length === 0" description="暂无数据" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 工作流指南 -->
    <el-row :gutter="20" class="section-row">
      <el-col :span="24">
        <el-card class="workflow-card">
          <template #header>
            <div class="card-header">
              <span>📋 工作流程</span>
            </div>
          </template>
          <div class="workflow-steps">
            <div class="step-item">
              <div class="step-number">1</div>
              <div class="step-content">
                <div class="step-title">上传票据</div>
                <div class="step-desc">上传发票、收据等原始凭证</div>
              </div>
              <el-icon class="step-arrow"><ArrowRight /></el-icon>
            </div>
            <div class="step-item">
              <div class="step-number">2</div>
              <div class="step-content">
                <div class="step-title">AI识别</div>
                <div class="step-desc">自动提取票据信息</div>
              </div>
              <el-icon class="step-arrow"><ArrowRight /></el-icon>
            </div>
            <div class="step-item">
              <div class="step-number">3</div>
              <div class="step-content">
                <div class="step-title">生成凭证</div>
                <div class="step-desc">智能生成记账凭证</div>
              </div>
              <el-icon class="step-arrow"><ArrowRight /></el-icon>
            </div>
            <div class="step-item">
              <div class="step-number">4</div>
              <div class="step-content">
                <div class="step-title">审核确认</div>
                <div class="step-desc">审核凭证并确认</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../../stores/auth'
import api from '../../api/index'
import {
  Document, Tickets, Clock, CircleCheck,
  Plus, DocumentChecked, View, ArrowRight
} from '@element-plus/icons-vue'

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

const calculatePercentage = (count: number) => {
  return Math.round((count / totalCount.value) * 100)
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
    'ocr_pending': 'info',
    'ocr_completed': 'success',
    'ocr_failed': 'danger',
    'voucher_generated': 'warning'
  }
  return map[status] || 'info'
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
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.welcome-section {
  margin-bottom: 24px;
}

.welcome-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.welcome-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 24px;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s, box-shadow 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.bills-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.vouchers-card {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: #fff;
}

.pending-card {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: #fff;
}

.approved-card {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: #fff;
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.2);
  margin-right: 16px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  margin-top: 4px;
}

.section-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

.quick-actions {
  .action-buttons {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;

    .el-button {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 24px;
    }
  }
}

.chart-container {
  padding: 20px 0;
}

.progress-list {
  .progress-item {
    margin-bottom: 20px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .progress-label {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    font-size: 14px;
    color: #606266;
  }
}

.recent-list {
  .recent-item {
    display: flex;
    align-items: center;
    padding: 16px 0;
    border-bottom: 1px solid #ebeef5;

    &:last-child {
      border-bottom: none;
    }
  }

  .recent-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 8px;
    background: #f0f9ff;
    color: #409eff;
    margin-right: 12px;
  }

  .recent-content {
    flex: 1;
    min-width: 0;
  }

  .recent-title {
    font-size: 14px;
    font-weight: 500;
    color: #303133;
    margin-bottom: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .recent-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 12px;
    color: #909399;
  }

  .recent-time {
    font-size: 12px;
    color: #c0c4cc;
  }
}

.workflow-card {
  .workflow-steps {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 0;
    flex-wrap: wrap;
    gap: 20px;
  }

  .step-item {
    display: flex;
    align-items: center;
    flex: 1;
    min-width: 200px;
  }

  .step-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    font-size: 20px;
    font-weight: 600;
    margin-right: 16px;
    flex-shrink: 0;
  }

  .step-content {
    flex: 1;
  }

  .step-title {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 4px;
  }

  .step-desc {
    font-size: 12px;
    color: #909399;
  }

  .step-arrow {
    font-size: 24px;
    color: #c0c4cc;
    margin: 0 20px;
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 12px;
  }

  .welcome-title {
    font-size: 20px;
  }

  .stat-card {
    margin-bottom: 12px;
  }

  .workflow-card .step-arrow {
    display: none;
  }
}
</style>
