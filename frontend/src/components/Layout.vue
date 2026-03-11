<template>
  <el-container class="layout">
    <!-- 移动端遮罩层 -->
    <div 
      v-if="isMobile && sidebarVisible" 
      class="sidebar-overlay"
      @click="sidebarVisible = false"
    ></div>
    
    <el-aside 
      width="200px" 
      class="sidebar"
      :class="{ 'sidebar-mobile': isMobile, 'sidebar-visible': sidebarVisible }"
    >
      <div class="logo">
        <h3>SmartLedger</h3>
      </div>
      
      <el-menu
        :default-active="$route.path"
        router
        class="menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        :collapse="isMobile"
        @select="handleMenuSelect"
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        
        <el-menu-item index="/bills">
          <el-icon><Document /></el-icon>
          <span>票据管理</span>
        </el-menu-item>
        
        <el-menu-item index="/vouchers">
          <el-icon><Tickets /></el-icon>
          <span>凭证管理</span>
        </el-menu-item>
        
        <el-menu-item index="/bank-flows">
          <el-icon><Money /></el-icon>
          <span>银行流水</span>
        </el-menu-item>

        <el-menu-item index="/audit">
          <el-icon><Checked /></el-icon>
          <span>审核工作台</span>
        </el-menu-item>

        <el-sub-menu index="/customers">
          <template #title>
            <el-icon><User /></el-icon>
            <span>客户管理</span>
          </template>
          <el-menu-item index="/customers/list">客户资料</el-menu-item>
          <el-menu-item index="/contracts/list">合同管理</el-menu-item>
          <el-menu-item index="/customers/analytics">统计分析</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="/reports">
          <template #title>
            <el-icon><TrendCharts /></el-icon>
            <span>财务报表</span>
          </template>
          <el-menu-item index="/reports/balance-sheet">资产负债表</el-menu-item>
          <el-menu-item index="/reports/income-statement">利润表</el-menu-item>
          <el-menu-item index="/reports/cash-flow">现金流量表</el-menu-item>
          <el-menu-item index="/reports/subject-balance">科目余额表</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="/system">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/system/users">用户管理</el-menu-item>
          <el-menu-item index="/system/roles">角色权限</el-menu-item>
          <el-menu-item index="/system/logs">操作日志</el-menu-item>
          <el-menu-item index="/system/settings">系统配置</el-menu-item>
          <el-menu-item index="/system/tenants">租户管理</el-menu-item>
          <el-menu-item index="/system/backup">数据备份</el-menu-item>
          <el-menu-item index="/system/scheduler">定时任务</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/notifications">
          <el-icon><Bell /></el-icon>
          <span>通知中心</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header class="header">
        <!-- 移动端菜单按钮 -->
        <div class="header-left" v-if="isMobile">
          <el-button 
            text 
            class="menu-toggle"
            @click="sidebarVisible = !sidebarVisible"
          >
            <el-icon :size="24">
              <Fold v-if="sidebarVisible === false" />
              <Expand v-else-if="sidebarVisible === true" />
            </el-icon>
          </el-button>
          <span class="mobile-title">SmartLedger</span>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              {{ authStore.user?.name || authStore.user?.username }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { HomeFilled, Document, Tickets, Money, Checked, User, TrendCharts, Setting, ArrowDown, Bell, Fold, Expand } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

// 响应式状态
const isMobile = ref(false)
const sidebarVisible = ref(false)

// 检测屏幕宽度
const checkScreenSize = () => {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) {
    sidebarVisible.value = false
  }
}

// 菜单选择时关闭侧边栏（移动端）
const handleMenuSelect = () => {
  if (isMobile.value) {
    sidebarVisible.value = false
  }
}

const handleCommand = (command: string) => {
  if (command === 'logout') {
    authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}

onMounted(() => {
  checkScreenSize()
  window.addEventListener('resize', checkScreenSize)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkScreenSize)
})
</script>

<style scoped>
.layout {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  transition: transform 0.3s ease;
}

/* 移动端侧边栏样式 */
.sidebar-mobile {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  z-index: 1001;
  transform: translateX(-100%);
}

.sidebar-mobile.sidebar-visible {
  transform: translateX(0);
}

/* 移动端遮罩层 */
.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  border-bottom: 1px solid #1f2d3d;
}

.logo h3 {
  margin: 0;
}

.menu {
  border-right: none;
}

.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-toggle {
  padding: 4px 8px;
}

.mobile-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--sl-text-primary, #1f2937);
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
}

.main {
  background-color: #f0f2f5;
  padding: 0;
}

/* 移动端响应式 */
@media (max-width: 768px) {
  .sidebar {
    width: 200px !important;
  }
  
  .logo h3 {
    font-size: 16px;
  }
  
  .header {
    padding: 0 12px;
  }
  
  .user-info {
    font-size: 13px;
  }
  
  .main {
    padding: 0;
  }
}

/* 超小屏幕 */
@media (max-width: 480px) {
  .mobile-title {
    font-size: 14px;
  }
}
</style>
