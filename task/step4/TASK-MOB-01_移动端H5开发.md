# 任务编号：TASK-MOB-01
# 任务名称：移动端H5开发
# 优先级：P1
# 预估工期：3天
# 负责人：前端

================================================================================
                              任务描述
================================================================================

开发移动端H5页面，支持手机浏览器访问，实现核心功能的移动端适配。

================================================================================
                              需求详情
================================================================================

## 1. 技术选型

- **框架**: Vue3 + Vite
- **UI库**: Vant 4 (移动端组件库)
- **适配方案**: Viewport + Rem 适配
- **状态管理**: Pinia
- **路由**: Vue Router 4

## 2. 目录结构

```
mobile/
├── public/
├── src/
│   ├── api/           # API接口
│   ├── assets/        # 静态资源
│   ├── components/    # 公共组件
│   ├── views/         # 页面
│   │   ├── login/     # 登录
│   │   ├── dashboard/ # 首页
│   │   ├── bills/     # 票据
│   │   ├── vouchers/  # 凭证
│   │   ├── reports/   # 报表
│   │   └── profile/   # 我的
│   ├── router/        # 路由
│   ├── stores/        # 状态
│   ├── utils/         # 工具
│   └── App.vue
├── index.html
├── package.json
└── vite.config.ts
```

## 3. 核心功能模块

### 3.1 登录模块
```vue
<!-- views/login/index.vue -->
<template>
  <div class="login-page">
    <div class="logo">
      <img src="/logo.png" />
      <h1>SmartLedger</h1>
    </div>
    
    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field
          v-model="form.username"
          name="username"
          label="用户名"
          placeholder="请输入用户名"
          :rules="[{ required: true, message: '请填写用户名' }]"
        />
        <van-field
          v-model="form.password"
          type="password"
          name="password"
          label="密码"
          placeholder="请输入密码"
          :rules="[{ required: true, message: '请填写密码' }]"
        />
      </van-cell-group>
      
      <div class="submit-btn">
        <van-button 
          round 
          block 
          type="primary" 
          native-type="submit"
          :loading="loading"
        >
          登录
        </van-button>
      </div>
    </van-form>
  </div>
</template>
```

### 3.2 票据管理（移动端）
```vue
<!-- views/bills/index.vue -->
<template>
  <div class="bills-page">
    <!-- 上传按钮 -->
    <van-uploader
      v-model="fileList"
      :after-read="afterRead"
      accept="image/*"
      capture="camera"
      multiple
    >
      <van-button icon="plus" type="primary">拍照上传</van-button>
    </van-uploader>
    
    <!-- 票据列表 -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        @load="onLoad"
      >
        <van-swipe-cell v-for="bill in bills" :key="bill.id">
          <van-card
            :title="bill.seller_name"
            :desc="`发票号码: ${bill.invoice_no}`"
          >
            <template #tags>
              <van-tag :type="getStatusType(bill.status)">
                {{ bill.status_text }}
              </van-tag>
            </template>
            
            <template #footer>
              <span class="amount">¥{{ bill.total_amount }}</span>
              <span class="date">{{ bill.invoice_date }}</span>
            </template>
          </van-card>
          
          <template #right>
            <van-button
              square
              text="删除"
              type="danger"
              @click="deleteBill(bill.id)"
            />
          </template>
        </van-swipe-cell>
      </van-list>
    </van-pull-refresh>
    
    <!-- 底部导航 -->
    <van-tabbar v-model="active">
      <van-tabbar-item icon="home-o" to="/">首页</van-tabbar-item>
      <van-tabbar-item icon="records" to="/bills">票据</van-tabbar-item>
      <van-tabbar-item icon="chart-trending-o" to="/reports">报表</van-tabbar-item>
      <van-tabbar-item icon="user-o" to="/profile">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>
```

### 3.3 报表查看（移动端）
```vue
<!-- views/reports/index.vue -->
<template>
  <div class="reports-page">
    <van-picker-group
      title="选择期间"
      :tabs="['年份', '月份']"
      @confirm="onPeriodConfirm"
    >
      <van-picker :columns="years" />
      <van-picker :columns="months" />
    </van-picker-group>
    
    <!-- 报表卡片 -->
    <van-grid :column-num="2">
      <van-grid-item 
        icon="balance-list-o" 
        text="资产负债表"
        to="/reports/balance"
      />
      <van-grid-item 
        icon="chart-trending-o" 
        text="利润表"
        to="/reports/income"
      />
      <van-grid-item 
        icon="cash-back-record" 
        text="现金流量表"
        to="/reports/cashflow"
      />
      <van-grid-item 
        icon="orders-o" 
        text="科目余额表"
        to="/reports/subjects"
      />
    </van-grid>
    
    <!-- 关键指标 -->
    <van-cell-group title="关键指标" inset>
      <van-cell title="营业收入" :value="`¥${stats.revenue}`" />
      <van-cell title="净利润" :value="`¥${stats.profit}`" />
      <van-cell title="毛利率" :value="`${stats.margin}%`" />
    </van-cell-group>
  </div>
</template>
```

## 4. 移动端适配配置

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { VantResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    Components({
      resolvers: [VantResolver()]
    })
  ],
  css: {
    postcss: {
      plugins: [
        require('postcss-px-to-viewport')({
          viewportWidth: 375,
          viewportHeight: 667,
          unitPrecision: 5,
          viewportUnit: 'vw',
          selectorBlackList: ['.ignore'],
          minPixelValue: 1,
          mediaQuery: false
        })
      ]
    }
  }
})
```

## 5. API 封装

```typescript
// api/index.ts
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      // 未授权，跳转登录
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

## 6. 路由配置

```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    component: () => import('@/views/login/index.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('@/views/dashboard/index.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/bills',
    component: () => import('@/views/bills/index.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/bills/:id',
    component: () => import('@/views/bills/detail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/reports',
    component: () => import('@/views/reports/index.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    component: () => import('@/views/profile/index.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory('/mobile'),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
```

================================================================================
                              验收标准
================================================================================

1. [ ] 支持iOS Safari、Android Chrome
2. [ ] 适配375px-414px屏幕宽度
3. [ ] 核心功能可用（上传、查询、查看报表）
4. [ ] 拍照上传票据正常
5. [ ] 手势操作流畅
6. [ ] 首屏加载时间<3秒
7. [ ] 支持PWA离线访问

================================================================================
                              开发提示
================================================================================

1. 使用Chrome DevTools移动端模拟器开发
2. 真机调试使用vConsole
3. 图片上传前压缩
4. 列表使用虚拟滚动优化性能
5. 支持扫码登录
