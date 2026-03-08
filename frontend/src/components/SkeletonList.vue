<template>
  <div class="skeleton-list">
    <div v-for="i in rows" :key="i" class="skeleton-item">
      <el-skeleton animated>
        <template #template>
          <div class="skeleton-row">
            <el-skeleton-item variant="text" style="width: 15%" />
            <el-skeleton-item variant="text" style="width: 20%; margin-left: 2%" />
            <el-skeleton-item variant="text" style="width: 25%; margin-left: 2%" />
            <el-skeleton-item variant="text" style="width: 15%; margin-left: 2%" />
            <el-skeleton-item variant="text" style="width: 15%; margin-left: 2%" />
          </div>
        </template>
      </el-skeleton>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  rows?: number
}>({
  rows: 5
})
</script>

<style scoped>
.skeleton-list {
  padding: 16px;
}

.skeleton-item {
  margin-bottom: 16px;
}

.skeleton-row {
  display: flex;
  align-items: center;
}
</style>
