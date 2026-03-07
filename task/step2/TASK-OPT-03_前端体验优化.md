# 任务编号：TASK-OPT-03
# 任务名称：前端体验优化
# 优先级：P1
# 预估工期：1天
# 负责人：前端开发

================================================================================
                              任务描述
================================================================================

优化前端用户体验，包括加载速度、交互流畅度、错误处理、响应式适配。

================================================================================
                              优化清单
================================================================================

## 1. 加载优化

### 1.1 骨架屏
```vue
<!-- BillListSkeleton.vue -->
<template>
  <div class="skeleton-list">
    <div v-for="i in 5" :key="i" class="skeleton-item">
      <el-skeleton animated>
        <template #template>
          <el-skeleton-item variant="text" style="width: 30%" />
          <el-skeleton-item variant="text" style="width: 20%; margin-left: 10%" />
          <el-skeleton-item variant="text" style="width: 15%; margin-left: 10%" />
        </template>
      </el-skeleton>
    </div>
  </div>
</template>

<!-- 使用 -->
<BillListSkeleton v-if="loading" />
<BillListTable v-else :data="bills" />
```

### 1.2 页面加载进度条
```typescript
// router/index.ts
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

router.beforeEach((to, from, next) => {
  NProgress.start()
  next()
})

router.afterEach(() => {
  NProgress.done()
})
```

### 1.3 预加载关键资源
```html
<!-- index.html -->
<link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>
<link rel="prefetch" href="/views/audit.js" />
```

## 2. 交互优化

### 2.1 操作反馈
```typescript
// 统一的 Toast 提示
export function showSuccess(message: string) {
  ElMessage.success({ message, duration: 2000 })
}

export function showError(message: string) {
  ElMessage.error({ message, duration: 5000, showClose: true })
}

// 确认对话框
export async function confirmDelete(itemName: string): Promise<boolean> {
  try {
    await ElMessageBox.confirm(
      `确定删除 "${itemName}" 吗？删除后不可恢复。`,
      '确认删除',
      { type: 'warning', confirmButtonClass: 'el-button--danger' }
    )
    return true
  } catch {
    return false
  }
}

// 使用
async function handleDelete(bill: Bill) {
  if (await confirmDelete(bill.invoice_no)) {
    await deleteBill(bill.id)
    showSuccess('删除成功')
    refreshList()
  }
}
```

### 2.2 按钮防重复点击
```vue
<el-button 
  type="primary" 
  :loading="submitting"
  @click="handleSubmit"
>
  {{ submitting ? '提交中...' : '提交' }}
</el-button>

<script setup>
const submitting = ref(false)

async function handleSubmit() {
  if (submitting.value) return
  submitting.value = true
  
  try {
    await submitForm()
    showSuccess('提交成功')
  } finally {
    submitting.value = false
  }
}
</script>
```

### 2.3 自动保存草稿
```typescript
// 凭证编辑自动保存
import { useDebounceFn } from '@vueuse/core'

const autoSave = useDebounceFn(async () => {
  if (!formChanged.value) return
  
  try {
    await api.post('/vouchers/draft', form.value)
    lastSavedAt.value = Date.now()
    formChanged.value = false
  } catch (error) {
    console.error('自动保存失败', error)
  }
}, 5000)  // 5秒防抖

// 监听表单变化
watch(form, () => {
  formChanged.value = true
  autoSave()
}, { deep: true })

// 显示保存状态
<template>
  <div class="save-status">
    <span v-if="formChanged">编辑中...</span>
    <span v-else-if="lastSavedAt">已保存 {{ formatTime(lastSavedAt) }}</span>
  </div>
</template>
```

## 3. 错误处理

### 3.1 全局错误处理
```typescript
// main.ts
app.config.errorHandler = (err, vm, info) => {
  console.error('全局错误:', err, info)
  
  // 上报监控
  reportError({
    type: 'vue_error',
    error: err?.toString(),
    component: vm?.$options?.name,
    info
  })
  
  showError('系统出现错误，请刷新页面重试')
}

// API 错误处理
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      authStore.logout()
      router.push('/login')
      showError('登录已过期，请重新登录')
    } else if (error.response?.status === 403) {
      showError('没有操作权限')
    } else if (error.response?.status >= 500) {
      showError('服务器错误，请稍后重试')
    } else {
      showError(error.response?.data?.message || '请求失败')
    }
    return Promise.reject(error)
  }
)
```

### 3.2 错误边界
```vue
<!-- ErrorBoundary.vue -->
<template>
  <div v-if="hasError" class="error-boundary">
    <el-result
      icon="error"
      title="页面出错"
      sub-title="抱歉，页面加载出现问题"
    >
      <template #extra>
        <el-button @click="reload">刷新页面</el-button>
        <el-button type="primary" @click="reset">重置</el-button>
      </template>
    </el-result>
  </div>
  <slot v-else />
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'

const hasError = ref(false)
const error = ref(null)

onErrorCaptured((err) => {
  hasError.value = true
  error.value = err
  return false  // 阻止错误继续传播
})

function reload() {
  window.location.reload()
}

function reset() {
  hasError.value = false
  error.value = null
}
</script>

<!-- 使用 -->
<ErrorBoundary>
  <RouterView />
</ErrorBoundary>
```

## 4. 响应式适配

### 4.1 断点设计
```scss
// styles/responsive.scss
$breakpoints: (
  'xs': 480px,   // 手机
  'sm': 768px,   // 平板
  'md': 1024px,  // 小笔记本
  'lg': 1280px,  // 桌面
  'xl': 1920px   // 大屏
);

// Element Plus 断点变量（已内置）
// xs: <768px
// sm: ≥768px
// md: ≥992px
// lg: ≥1200px
// xl: ≥1920px
```

### 4.2 移动端适配
```vue
<!-- 响应式表格 -->
<el-table
  :data="bills"
  :class="{ 'mobile-table': isMobile }"
>
  <!-- 桌面显示所有列 -->
  <el-table-column v-if="!isMobile" prop="invoice_code" label="发票代码" />
  
  <!-- 移动端简化显示 -->
  <el-table-column v-if="isMobile" label="票据信息">
    <template #default="{ row }">
      <div class="mobile-bill-info">
        <div class="title">{{ row.seller_name }}</div>
        <div class="meta">{{ row.invoice_date }} | ¥{{ row.amount }}</div>
      </div>
    </template>
  </el-table-column>
</el-table>

<script setup>
import { useWindowSize } from '@vueuse/core'

const { width } = useWindowSize()
const isMobile = computed(() => width.value < 768)
</script>
```

### 4.3 触摸优化
```scss
// 增大触摸目标
.mobile {
  .el-button {
    min-height: 44px;
    min-width: 44px;
  }
  
  .el-table__row {
    min-height: 48px;
  }
  
  // 滑动操作
  .swipe-item {
    position: relative;
    
    .actions {
      position: absolute;
      right: -100px;
      top: 0;
      bottom: 0;
      display: flex;
      align-items: center;
      
      &.visible {
        right: 0;
      }
    }
  }
}
```

## 5. 键盘快捷键

```typescript
// composables/useKeyboard.ts
import { onMounted, onUnmounted } from 'vue'

export function useKeyboardShortcuts(shortcuts: Record<string, () => void>) {
  const handler = (e: KeyboardEvent) => {
    // 忽略输入框内的快捷键
    if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) {
      return
    }
    
    const key = `${e.ctrlKey ? 'Ctrl+' : ''}${e.key}`
    if (shortcuts[key]) {
      e.preventDefault()
      shortcuts[key]()
    }
  }
  
  onMounted(() => document.addEventListener('keydown', handler))
  onUnmounted(() => document.removeEventListener('keydown', handler))
}

// 使用
useKeyboardShortcuts({
  'Ctrl+S': () => saveDraft(),
  'Ctrl+N': () => createNew(),
  'Ctrl+F': () => focusSearch(),
  'Escape': () => closeDialog()
})
```

## 6. 暗黑模式

```typescript
// stores/theme.ts
export const useThemeStore = defineStore('theme', {
  state: () => ({
    isDark: localStorage.getItem('theme') === 'dark'
  }),
  
  actions: {
    toggle() {
      this.isDark = !this.isDark
      localStorage.setItem('theme', this.isDark ? 'dark' : 'light')
      document.documentElement.classList.toggle('dark', this.isDark)
    }
  }
})

// 初始化
themeStore.isDark && document.documentElement.classList.add('dark')
```

## 7. 无障碍支持

```vue
<!-- 按钮增加 aria-label -->
<el-button 
  type="danger" 
  :icon="Delete"
  aria-label="删除票据"
  @click="handleDelete"
/>

<!-- 表单增加 label 关联 -->
<el-form-item label="发票号码">
  <el-input 
    id="invoice-number"
    aria-describedby="invoice-help"
    v-model="form.invoice_number"
  />
  <span id="invoice-help" class="help-text">请输入10位发票号码</span>
</el-form-item>

<!-- 焦点管理 -->
<script setup>
const inputRef = ref<HTMLInputElement>()

onMounted(() => {
  inputRef.value?.focus()  // 自动聚焦
})
</script>
```

================================================================================
                              验收标准
================================================================================

1. [ ] 骨架屏在数据加载时显示
2. [ ] 页面切换有进度条提示
3. [ ] 操作后有 Toast 反馈（成功/失败）
4. [ ] 按钮有 loading 状态防重复
5. [ ] 表单有自动保存提示
6. [ ] 错误页面有友好的错误提示
7. [ ] 移动端布局正常可用
8. [ ] 触摸目标大小 ≥ 44px
9. [ ] 支持 Ctrl+S 等常用快捷键
10. [ ] 暗黑模式可切换

================================================================================
                              开发提示
================================================================================

1. 使用 Lighthouse 进行体验评分，目标 > 90 分
2. 使用 Chrome DevTools Performance 面板分析性能
3. 移动端测试使用真实设备，不只是模拟器
4. 考虑使用 PWA 提升体验（可选）
5. 关注 Core Web Vitals 指标
