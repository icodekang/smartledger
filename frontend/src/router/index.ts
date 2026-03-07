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
      redirect: '/bills',
      children: [
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
          path: 'audit',
          name: 'Audit',
          component: () => import('@/views/audit/Workbench.vue')
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
