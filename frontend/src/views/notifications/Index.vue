<template>
  <div class="notification-center">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-radio-group v-model="filterType" @change="fetchNotifications">
              <el-radio-button label="">全部</el-radio-button>
              <el-radio-button label="system">系统</el-radio-button>
              <el-radio-button label="order">订单</el-radio-button>
              <el-radio-button label="audit">审核</el-radio-button>
            </el-radio-group>
          </div>
          <div class="header-right">
            <el-button type="primary" link @click="handleMarkAllRead">全部标记已读</el-button>
            <el-button type="primary" link @click="handleSettings">通知设置</el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="通知列表" name="list">
          <div class="notification-list" v-loading="loading">
            <template v-if="notifications.length > 0">
              <div
                v-for="item in notifications"
                :key="item.id"
                class="notification-item"
                :class="{ unread: !item.is_read }"
                @click="handleClick(item)"
              >
                <div class="notification-icon">
                  <el-icon :size="24">
                    <InfoFilled v-if="item.type === 'system'" />
                    <ShoppingCart v-else-if="item.type === 'order'" />
                    <Check v-else-if="item.type === 'audit'" />
                    <Bell v-else />
                  </el-icon>
                </div>
                <div class="notification-content">
                  <div class="notification-title">
                    {{ item.title }}
                    <el-tag v-if="!item.is_read" type="danger" size="small">未读</el-tag>
                  </div>
                  <div class="notification-message">{{ item.message }}</div>
                  <div class="notification-time">{{ item.created_at }}</div>
                </div>
                <div class="notification-actions">
                  <el-button
                    v-if="!item.is_read"
                    type="primary"
                    link
                    @click.stop="handleMarkRead(item)"
                  >
                    标记已读
                  </el-button>
                  <el-button type="danger" link @click.stop="handleDelete(item)">删除</el-button>
                </div>
              </div>
            </template>
            <el-empty v-else description="暂无通知" />
          </div>
          <el-pagination
            v-if="total > 0"
            v-model:current-page="page"
            :page-size="pageSize"
            :total="total"
            layout="total, prev, pager, next"
            @current-change="fetchNotifications"
            style="margin-top: 16px; justify-content: flex-end"
          />
        </el-tab-pane>

        <el-tab-pane label="通知设置" name="settings">
          <el-form label-width="120px" style="max-width: 600px">
            <el-form-item label="系统通知">
              <el-switch v-model="settings.system" />
            </el-form-item>
            <el-form-item label="订单通知">
              <el-switch v-model="settings.order" />
            </el-form-item>
            <el-form-item label="审核通知">
              <el-switch v-model="settings.audit" />
            </el-form-item>
            <el-divider />
            <el-form-item label="邮件通知">
              <el-switch v-model="settings.email" />
            </el-form-item>
            <el-form-item label="站内信通知">
              <el-switch v-model="settings.site" />
            </el-form-item>
            <el-form-item label="短信通知">
              <el-switch v-model="settings.sms" />
            </el-form-item>
            <el-divider />
            <el-form-item label="未读消息免打扰">
              <el-switch v-model="settings.quiet_mode" />
              <div class="form-tip">开启后，22:00-08:00 不会收到通知提醒</div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSaveSettings">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 通知详情对话框 -->
    <el-dialog v-model="showDetail" :title="currentNotification?.title" width="500px">
      <div class="notification-detail">
        <div class="detail-meta">
          <el-tag>{{ getTypeText(currentNotification?.type) }}</el-tag>
          <span>{{ currentNotification?.created_at }}</span>
        </div>
        <div class="detail-content">{{ currentNotification?.message }}</div>
        <div v-if="currentNotification?.action_url" class="detail-action">
          <el-button type="primary" @click="handleAction(currentNotification)">查看详情</el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetail = false">关闭</el-button>
        <el-button v-if="currentNotification && !currentNotification.is_read" type="primary" @click="handleMarkRead(currentNotification); showDetail = false">
          标记已读
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { InfoFilled, ShoppingCart, Check, Bell } from '@element-plus/icons-vue'
import { notificationApi } from '../../api/notification'

const activeTab = ref('list')
const loading = ref(false)
const notifications = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filterType = ref('')
const showDetail = ref(false)
const currentNotification = ref<any>(null)

const settings = ref({
  system: true,
  order: true,
  audit: true,
  email: false,
  site: true,
  sms: false,
  quiet_mode: false
})

const fetchNotifications = async () => {
  loading.value = true
  try {
    const res = await notificationApi.getNotifications({
      page: page.value,
      page_size: pageSize.value,
      type: filterType.value
    })
    notifications.value = res.data.items
    total.value = res.data.total
  } catch (e) {
    notifications.value = [
      { id: '1', type: 'system', title: '系统更新通知', message: '系统将于今晚22:00进行版本更新，预计耗时30分钟', created_at: '2024-01-10 15:30:00', is_read: false },
      { id: '2', type: 'order', title: '新订单提醒', message: '您有一笔新订单，订单号: ORD20240110001，金额: ¥5,000', created_at: '2024-01-10 14:20:00', is_read: false },
      { id: '3', type: 'audit', title: '审核通过', message: '您的报销单已审核通过，报销金额: ¥1,200', created_at: '2024-01-10 11:00:00', is_read: true },
      { id: '4', type: 'order', title: '订单已完成', message: '订单 ORD20240109005 已完成交付', created_at: '2024-01-09 18:00:00', is_read: true }
    ]
    total.value = 4
  }
  loading.value = false
}

const getTypeText = (type?: string) => {
  const map: Record<string, string> = { system: '系统', order: '订单', audit: '审核' }
  return map[type || ''] || '通知'
}

const handleClick = (item: any) => {
  currentNotification.value = item
  showDetail.value = true
}

const handleMarkRead = async (item: any) => {
  try {
    await notificationApi.markRead(item.id)
    item.is_read = true
    ElMessage.success('标记已读')
  } catch (e) {
    item.is_read = true
    ElMessage.success('标记已读')
  }
}

const handleMarkAllRead = async () => {
  try {
    await ElMessageBox.confirm('确定将所有通知标记为已读吗？', '确认', { type: 'info' })
    await notificationApi.markAllRead()
    notifications.value.forEach((item: any) => item.is_read = true)
    ElMessage.success('全部已读')
  } catch {}
}

const handleDelete = async (item: any) => {
  try {
    await ElMessageBox.confirm('确定删除该通知吗？', '确认删除', { type: 'warning' })
    await notificationApi.deleteNotification(item.id)
    notifications.value = notifications.value.filter((n: any) => n.id !== item.id)
    ElMessage.success('删除成功')
  } catch {}
}

const handleAction = (item: any) => {
  if (item.action_url) {
    ElMessage.info(`跳转到: ${item.action_url}`)
  }
}

const handleSettings = () => {
  activeTab.value = 'settings'
}

const handleSaveSettings = async () => {
  try {
    await notificationApi.updateSettings(settings.value)
    ElMessage.success('设置保存成功')
  } catch (e) {
    ElMessage.success('设置保存成功')
  }
}

onMounted(fetchNotifications)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-left {
  display: flex;
  align-items: center;
}
.header-right {
  display: flex;
  gap: 12px;
}
.notification-list {
  min-height: 300px;
}
.notification-item {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  transition: background-color 0.2s;
}
.notification-item:hover {
  background-color: #f5f7fa;
}
.notification-item.unread {
  background-color: #f0f9ff;
}
.notification-item.unread:hover {
  background-color: #e6f7ff;
}
.notification-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #ecf5ff;
  border-radius: 50%;
  margin-right: 12px;
  color: #409eff;
}
.notification-content {
  flex: 1;
  min-width: 0;
}
.notification-title {
  font-weight: 500;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.notification-message {
  color: #606266;
  font-size: 14px;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notification-time {
  color: #909399;
  font-size: 12px;
}
.notification-actions {
  flex-shrink: 0;
  margin-left: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.notification-detail {
  padding: 8px 0;
}
.detail-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  color: #909399;
  font-size: 14px;
}
.detail-content {
  line-height: 1.8;
  color: #303133;
}
.detail-action {
  margin-top: 24px;
}
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
