import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/auth/Login.vue'),
      meta: { public: true }
    },
    {
      path: '/',
      component: () => import('@/components/Layout.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/index.vue')
        },
        {
          path: 'bills',
          name: 'Bills',
          component: () => import('@/views/bills/List.vue')
        },
        {
          path: 'vouchers',
          name: 'Vouchers',
          component: () => import('@/views/vouchers/List.vue')
        },
        {
          path: 'bank-flows',
          name: 'BankFlows',
          component: () => import('@/views/bank-flows/index.vue')
        },
        {
          path: 'customers/list',
          name: 'Customers',
          component: () => import('@/views/customers/index.vue')
        },
        {
          path: 'contracts/list',
          name: 'Contracts',
          component: () => import('@/views/contracts/index.vue')
        },
        {
          path: 'reports',
          name: 'Reports',
          component: () => import('@/views/reports/index.vue')
        },
        {
          path: 'system/users',
          name: 'SystemUsers',
          component: () => import('@/views/system/users.vue')
        },
        {
          path: 'audit',
          name: 'Audit',
          component: () => import('@/views/audit/Workbench.vue')
        },
        {
          path: 'customers/analytics',
          name: 'CustomerAnalytics',
          component: () => import('@/views/customers/Analytics.vue')
        },
        {
          path: 'reports/balance-sheet',
          name: 'BalanceSheet',
          component: () => import('@/views/reports/BalanceSheet.vue')
        },
        {
          path: 'reports/income-statement',
          name: 'IncomeStatement',
          component: () => import('@/views/reports/IncomeStatement.vue')
        },
        {
          path: 'reports/cash-flow',
          name: 'CashFlow',
          component: () => import('@/views/reports/CashFlow.vue')
        },
        {
          path: 'reports/subject-balance',
          name: 'SubjectBalance',
          component: () => import('@/views/reports/SubjectBalance.vue')
        },
        {
          path: 'system/roles',
          name: 'SystemRoles',
          component: () => import('@/views/system/roles.vue')
        },
        {
          path: 'system/logs',
          name: 'SystemLogs',
          component: () => import('@/views/system/logs.vue')
        },
        {
          path: 'system/settings',
          name: 'SystemSettings',
          component: () => import('@/views/system/settings.vue')
        },
        {
          path: 'system/tenants',
          name: 'SystemTenants',
          component: () => import('@/views/system/Tenants.vue')
        },
        {
          path: 'system/backup',
          name: 'SystemBackup',
          component: () => import('@/views/system/Backup.vue')
        },
        {
          path: 'system/scheduler',
          name: 'SystemScheduler',
          component: () => import('@/views/system/Scheduler.vue')
        },
        {
          path: 'notifications',
          name: 'Notifications',
          component: () => import('@/views/notifications/Index.vue')
        }
      ]
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta?.public) {
    next()
  } else if (!authStore.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router
