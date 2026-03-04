<template>
  <div class="workbench">
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-statistic title="待审核" :value="stats.pending" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="今日已审" :value="stats.completed" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="平均处理时间" :value="stats.avgTime" suffix="分钟" />
      </el-col>
    </el-row>
    
    <el-card class="task-list">
      <template #header>
        <div class="card-header">
          <span>待审任务</span>
          <el-button type="primary" :disabled="!selectedTasks.length">
            批量通过
          </el-button>
        </div>
      </template>
      
      <el-table
        :data="tasks"
        @selection-change="handleSelectionChange"
        v-loading="loading"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="voucher_no" label="凭证号" width="120" />
        <el-table-column prop="customer_name" label="客户" />
        <el-table-column prop="summary" label="摘要" show-overflow-tooltip />
        <el-table-column prop="amount" label="金额" width="120">
          <template #default="{ row }">
            {{ formatAmount(row.amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="ai_confidence" label="AI置信度" width="100">
          <template #default="{ row }">
            <el-tag :type="getConfidenceType(row.ai_confidence)">
              {{ row.ai_confidence }}%
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="success" size="small" @click="approve(row)">通过</el-button>
            <el-button type="danger" size="small" @click="reject(row)">驳回</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const loading = ref(false)
const tasks = ref([
  { id: 1, voucher_no: '202403-001', customer_name: '测试公司', summary: '采购办公用品', amount: 1000, ai_confidence: 95 },
  { id: 2, voucher_no: '202403-002', customer_name: '示例公司', summary: '支付服务费', amount: 5000, ai_confidence: 88 }
])
const stats = ref({ pending: 12, completed: 25, avgTime: 5.5 })
const selectedTasks = ref([])

const handleSelectionChange = (selection: any[]) => {
  selectedTasks.value = selection
}

const approve = (row: any) => {
  console.log('通过', row)
}

const reject = (row: any) => {
  console.log('驳回', row)
}

const formatAmount = (amount: number) => {
  return '¥' + amount?.toFixed(2)
}

const getConfidenceType = (confidence: number) => {
  if (confidence >= 90) return 'success'
  if (confidence >= 70) return 'warning'
  return 'danger'
}

onMounted(() => {
  console.log('工作台加载完成')
})
</script>

<style scoped>
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
</style>
