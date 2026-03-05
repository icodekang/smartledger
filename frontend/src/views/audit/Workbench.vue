<template>
  <div class="workbench">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card>
          <el-statistic title="待审核" :value="stats.pending_count">
            <template #suffix>
              <el-button type="primary" link @click="autoAssign" :loading="assigning">领取任务</el-button>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card>
          <el-statistic title="我的任务" :value="stats.my_assigned" />
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card>
          <el-statistic title="今日已通过" :value="performance.today_approved" />
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card>
          <el-statistic title="平均处理时间" :value="performance.avg_audit_time_hours" suffix="小时" />
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 任务列表 -->
    <el-card class="task-list">
      <template #header>
        <div class="card-header">
          <span>待审任务</span>
          <div>
            <el-button 
              type="danger" 
              :disabled="!selectedTasks.length"
              @click="batchReject"
            >
              批量驳回
            </el-button>
            <el-button 
              type="success" 
              :disabled="!selectedTasks.length"
              @click="batchApprove"
            >
              批量通过
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table
        :data="tasks"
        @selection-change="handleSelectionChange"
        v-loading="loading"
        border
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="voucher_no" label="凭证号" width="120" />
        <el-table-column prop="submitter" label="提交人" width="120" />
        <el-table-column prop="summary" label="摘要" min-width="200" show-overflow-tooltip />
        <el-table-column prop="total_amount" label="金额" width="120" align="right">
          <template #default="{ row }">
            {{ formatAmount(row.total_amount) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'pending' ? 'warning' : 'info'">
              {{ row.status === 'pending' ? '待审核' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="success" size="small" @click="approve(row)">通过</el-button>
            <el-button type="danger" size="small" @click="reject(row)">驳回</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchData"
        @current-change="fetchData"
        class="pagination"
      />
    </el-card>
    
    <!-- 批量审核对话框 -->
    <el-dialog v-model="showAuditDialog" :title="auditAction === 'approve' ? '批量通过' : '批量驳回'" width="500px">
      <el-form :model="auditForm">
        <el-form-item label="审核意见">
          <el-input 
            v-model="auditForm.note" 
            type="textarea" 
            :rows="3"
            placeholder="请输入审核意见（可选）"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAuditDialog = false">取消</el-button>
        <el-button :type="auditAction === 'approve' ? 'success' : 'danger'" @click="confirmBatchAudit">
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { auditApi, type AuditTask, type AuditStats } from '../../api/audit'

const loading = ref(false)
const assigning = ref(false)
const tasks = ref<AuditTask[]>([])
const stats = ref<AuditStats>({
  pending_count: 0,
  assigned_count: 0,
  my_assigned: 0
})
const performance = ref({
  today_approved: 0,
  month_approved: 0,
  avg_audit_time_hours: 0
})
const selectedTasks = ref<AuditTask[]>([])
const showAuditDialog = ref(false)
const auditAction = ref<'approve' | 'reject'>('approve')

const auditForm = reactive({
  note: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await auditApi.getPendingTasks({
      page: pagination.page,
      page_size: pagination.page_size
    })
    tasks.value = res.items
    pagination.total = res.total
    
    // 更新统计
    if (res.stats) {
      stats.value = res.stats
    }
  } finally {
    loading.value = false
  }
}

const fetchStatistics = async () => {
  try {
    const res = await auditApi.getStatistics()
    if (res.overview) {
      stats.value.pending_count = res.overview.pending_count
      stats.value.assigned_count = res.overview.assigned_count
    }
    if (res.performance) {
      performance.value = res.performance
    }
  } catch (error) {
    console.error('获取统计失败', error)
  }
}

const autoAssign = async () => {
  assigning.value = true
  try {
    await auditApi.autoAssign()
    ElMessage.success('领取任务成功')
    fetchData()
    fetchStatistics()
  } finally {
    assigning.value = false
  }
}

const handleSelectionChange = (selection: AuditTask[]) => {
  selectedTasks.value = selection
}

const formatAmount = (amount: number) => {
  return '¥' + amount?.toFixed(2)
}

const approve = async (row: AuditTask) => {
  try {
    await ElMessageBox.confirm('确定通过该凭证吗？', '提示', { type: 'warning' })
    await auditApi.batchAudit([row.voucher_id], 'approve')
    ElMessage.success('审核通过')
    fetchData()
    fetchStatistics()
  } catch (error) {
    // 取消或错误
  }
}

const reject = async (row: AuditTask) => {
  try {
    await ElMessageBox.confirm('确定驳回该凭证吗？', '提示', { type: 'warning' })
    await auditApi.batchAudit([row.voucher_id], 'reject')
    ElMessage.success('审核驳回')
    fetchData()
    fetchStatistics()
  } catch (error) {
    // 取消或错误
  }
}

const batchApprove = () => {
  auditAction.value = 'approve'
  auditForm.note = ''
  showAuditDialog.value = true
}

const batchReject = () => {
  auditAction.value = 'reject'
  auditForm.note = ''
  showAuditDialog.value = true
}

const confirmBatchAudit = async () => {
  const ids = selectedTasks.value.map(t => t.voucher_id)
  try {
    await auditApi.batchAudit(ids, auditAction.value, auditForm.note)
    ElMessage.success(`批量${auditAction.value === 'approve' ? '通过' : '驳回'}成功`)
    showAuditDialog.value = false
    selectedTasks.value = []
    fetchData()
    fetchStatistics()
  } catch (error) {
    // 错误已在拦截器处理
  }
}

onMounted(() => {
  fetchData()
  fetchStatistics()
})
</script>

<style scoped>
.workbench {
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-list {
  margin-top: 20px;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
