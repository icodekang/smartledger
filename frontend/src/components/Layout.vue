<template>
  <el-container class="layout">
    <el-aside width="200px" class="sidebar">
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
          <el-menu-item index="/customers">客户资料</el-menu-item>
          <el-menu-item index="/contracts">合同管理</el-menu-item>
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
        </el-sub-menu>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header class="header">
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
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { HomeFilled, Document, Tickets, Money, Checked, User, TrendCharts, Setting, ArrowDown } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const handleCommand = (command: string) => {
  if (command === 'logout') {
    authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}
</script>

<style scoped>
.layout {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
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
  justify-content: flex-end;
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
}

.main {
  background-color: #f0f2f5;
  padding: 0;
}
</style>
