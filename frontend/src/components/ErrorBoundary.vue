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
    
    <div v-if="error" class="error-detail">
      <pre>{{ error }}</pre>
    </div>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'

const hasError = ref(false)
const error = ref<Error | null>(null)

onErrorCaptured((err: Error) => {
  console.error('ErrorBoundary caught:', err)
  hasError.value = true
  error.value = err
  
  // 上报错误
  reportError(err)
  
  return false
})

function reload() {
  window.location.reload()
}

function reset() {
  hasError.value = false
  error.value = null
}

function reportError(err: Error) {
  // 可以发送到监控服务
  console.error('Report error:', {
    message: err.message,
    stack: err.stack,
    time: new Date().toISOString()
  })
}
</script>

<style scoped>
.error-boundary {
  padding: 40px;
}

.error-detail {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
  overflow: auto;
}

.error-detail pre {
  margin: 0;
  font-size: 12px;
  color: #666;
}
</style>
