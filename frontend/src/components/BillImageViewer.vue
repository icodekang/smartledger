<template>
  <div class="bill-image-viewer" ref="container">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button-group size="small">
        <el-button @click="zoomOut" :icon="ZoomOut" title="缩小" />
        <el-button @click="zoomIn" :icon="ZoomIn" title="放大" />
        <el-button @click="fitToWindow" title="适应窗口">适应</el-button>
        <el-button @click="resetScale" title="原始尺寸">1:1</el-button>
      </el-button-group>
      
      <el-divider direction="vertical" />
      
      <el-button-group size="small">
        <el-button @click="rotateLeft" :icon="RefreshLeft" title="左旋" />
        <el-button @click="rotateRight" :icon="RefreshRight" title="右旋" />
      </el-button-group>
      
      <el-divider direction="vertical" />
      
      <el-button 
        v-if="editable" 
        size="small"
        :type="isSelecting ? 'primary' : ''" 
        @click="toggleSelection"
      >
        {{ isSelecting ? '取消框选' : '区域识别' }}
      </el-button>
      
      <el-button size="small" :icon="Download" @click="downloadImage">下载</el-button>
    </div>
    
    <!-- 图片区域 -->
    <div 
      class="image-container" 
      ref="imageContainer"
      @wheel.prevent="handleWheel"
    >
      <div 
        class="image-wrapper" 
        :style="wrapperStyle"
        @mousedown="startDrag"
        @mousemove="onDrag"
        @mouseup="endDrag"
        @mouseleave="endDrag"
      >
        <img 
          ref="image" 
          :src="url" 
          @load="onImageLoad"
          class="bill-image"
          draggable="false"
        />
        
        <!-- OCR 框选层 -->
        <div 
          v-if="!isSelecting"
          class="ocr-overlay"
          :style="overlayStyle"
        >
          <div
            v-for="box in displayBoxes"
            :key="box.field"
            class="ocr-box"
            :class="[getConfidenceClass(box.confidence), { active: activeBox === box }]"
            :style="getBoxStyle(box)"
            @click="handleBoxClick(box)"
            @mouseenter="activeBox = box"
            @mouseleave="activeBox = null"
          >
            <!-- 悬停提示 -->
            <div v-if="activeBox === box" class="box-tooltip">
              <div class="field-name">{{ fieldLabels[box.field] || box.field }}</div>
              <div class="text">{{ box.text }}</div>
              <div class="confidence" :class="getConfidenceClass(box.confidence)">
                置信度: {{ (box.confidence * 100).toFixed(1) }}%
              </div>
            </div>
          </div>
        </div>
        
        <!-- 用户框选层 -->
        <div
          v-if="isSelecting"
          class="selection-overlay"
          :style="overlayStyle"
          @mousedown="startSelection"
          @mousemove="updateSelection"
          @mouseup="endSelection"
        >
          <div
            v-if="selectionBox"
            class="selection-box"
            :style="getSelectionStyle(selectionBox)"
          >
            <div class="selection-actions">
              <el-button size="small" type="primary" @click.stop="confirmSelection">识别</el-button>
              <el-button size="small" @click.stop="cancelSelection">取消</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 状态栏 -->
    <div class="statusbar">
      <span>缩放: {{ Math.round(scale * 100) }}%</span>
      <el-divider direction="vertical" />
      <span>旋转: {{ rotation }}°</span>
      <el-divider direction="vertical" />
      <span v-if="imageSize">{{ imageSize.width }} × {{ imageSize.height }}</span>
    </div>
  </div></template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ZoomIn, ZoomOut, RefreshLeft, RefreshRight, Download } from '@element-plus/icons-vue'

interface OcrBox {
  field: string
  text: string
  confidence: number
  x: number
  y: number
  width: number
  height: number
}

interface Props {
  url: string
  ocrBoxes?: OcrBox[]
  editable?: boolean
  initialScale?: number
}

const props = withDefaults(defineProps<Props>(), {
  ocrBoxes: () => [],
  editable: false,
  initialScale: 1
})

const emit = defineEmits<{
  (e: 'boxClick', box: OcrBox): void
  (e: 'regionSelect', region: { x: number; y: number; width: number; height: number }): void
}>()

// 缩放控制
const scale = ref(props.initialScale)
const minScale = 0.1
const maxScale = 5
const container = ref<HTMLElement>()
const imageContainer = ref<HTMLElement>()
const image = ref<HTMLImageElement>()
const imageSize = ref<{ width: number; height: number } | null>(null)

// 拖拽控制
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const translate = ref({ x: 0, y: 0 })

// 旋转
const rotation = ref(0)

// 框选模式
const isSelecting = ref(false)
const selectionStart = ref<{ x: number; y: number } | null>(null)
const selectionBox = ref<{ x: number; y: number; width: number; height: number } | null>(null)

// 高亮框
const activeBox = ref<OcrBox | null>(null)

// 字段标签映射
const fieldLabels: Record<string, string> = {
  invoice_code: '发票代码',
  invoice_number: '发票号码',
  invoice_date: '开票日期',
  seller_name: '销售方名称',
  seller_tax_no: '销售方税号',
  buyer_name: '购买方名称',
  buyer_tax_no: '购买方税号',
  amount: '金额',
  tax_amount: '税额',
  total_amount: '价税合计'
}

// 显示的框（根据置信度排序）
const displayBoxes = computed(() => {
  return [...props.ocrBoxes].sort((a, b) => a.confidence - b.confidence)
})

// 图片加载
const onImageLoad = () => {
  if (image.value) {
    imageSize.value = {
      width: image.value.naturalWidth,
      height: image.value.naturalHeight
    }
    fitToWindow()
  }
}

// 缩放操作
const zoomIn = () => {
  scale.value = Math.min(scale.value * 1.2, maxScale)
}

const zoomOut = () => {
  scale.value = Math.max(scale.value / 1.2, minScale)
}

const handleWheel = (e: WheelEvent) => {
  if (e.deltaY < 0) {
    zoomIn()
  } else {
    zoomOut()
  }
}

// 适应窗口
const fitToWindow = () => {
  if (!image.value || !imageContainer.value) return
  
  const containerWidth = imageContainer.value.clientWidth
  const containerHeight = imageContainer.value.clientHeight
  const imgWidth = image.value.naturalWidth
  const imgHeight = image.value.naturalHeight
  
  const scaleX = (containerWidth - 40) / imgWidth
  const scaleY = (containerHeight - 40) / imgHeight
  
  scale.value = Math.min(scaleX, scaleY, 1)
  translate.value = { x: 0, y: 0 }
}

// 原始尺寸
const resetScale = () => {
  scale.value = 1
  translate.value = { x: 0, y: 0 }
}

// 旋转
const rotateLeft = () => {
  rotation.value -= 90
}

const rotateRight = () => {
  rotation.value += 90
}

// 下载图片
const downloadImage = () => {
  const link = document.createElement('a')
  link.href = props.url
  link.download = `bill-image-${Date.now()}.jpg`
  link.click()
  ElMessage.success('下载已开始')
}

// 拖拽逻辑
const startDrag = (e: MouseEvent) => {
  if (isSelecting.value) return
  isDragging.value = true
  dragStart.value = {
    x: e.clientX - translate.value.x,
    y: e.clientY - translate.value.y
  }
}

const onDrag = (e: MouseEvent) => {
  if (!isDragging.value) return
  translate.value = {
    x: e.clientX - dragStart.value.x,
    y: e.clientY - dragStart.value.y
  }
}

const endDrag = () => {
  isDragging.value = false
}

// 框选模式切换
const toggleSelection = () => {
  isSelecting.value = !isSelecting.value
  if (!isSelecting.value) {
    cancelSelection()
  }
}

// 框选逻辑
const startSelection = (e: MouseEvent) => {
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  selectionStart.value = {
    x: (e.clientX - rect.left) / scale.value,
    y: (e.clientY - rect.top) / scale.value
  }
}

const updateSelection = (e: MouseEvent) => {
  if (!selectionStart.value) return
  
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const currentX = (e.clientX - rect.left) / scale.value
  const currentY = (e.clientY - rect.top) / scale.value
  
  const width = Math.abs(currentX - selectionStart.value.x)
  const height = Math.abs(currentY - selectionStart.value.y)
  
  if (width > 10 && height > 10) {
    selectionBox.value = {
      x: Math.min(selectionStart.value.x, currentX),
      y: Math.min(selectionStart.value.y, currentY),
      width,
      height
    }
  }
}

const endSelection = () => {
  selectionStart.value = null
}

const cancelSelection = () => {
  selectionBox.value = null
  selectionStart.value = null
}

const confirmSelection = () => {
  if (!selectionBox.value || !imageSize.value) return
  
  // 转换为相对坐标（0-1）
  const region = {
    x: selectionBox.value.x / imageSize.value.width,
    y: selectionBox.value.y / imageSize.value.height,
    width: selectionBox.value.width / imageSize.value.width,
    height: selectionBox.value.height / imageSize.value.height
  }
  
  emit('regionSelect', region)
  cancelSelection()
  isSelecting.value = false
}

// 点击 OCR 框
const handleBoxClick = (box: OcrBox) => {
  emit('boxClick', box)
}

// 获取置信度样式类
const getConfidenceClass = (confidence: number) => {
  if (confidence >= 0.9) return 'high'
  if (confidence >= 0.7) return 'medium'
  return 'low'
}

// 计算样式
const wrapperStyle = computed(() => ({
  transform: `translate(${translate.value.x}px, ${translate.value.y}px) scale(${scale.value}) rotate(${rotation.value}deg)`,
  cursor: isDragging.value ? 'grabbing' : isSelecting.value ? 'crosshair' : 'grab'
}))

const overlayStyle = computed(() => ({
  width: imageSize.value ? `${imageSize.value.width}px` : '100%',
  height: imageSize.value ? `${imageSize.value.height}px` : '100%'
}))

const getBoxStyle = (box: OcrBox) => ({
  left: `${box.x * 100}%`,
  top: `${box.y * 100}%`,
  width: `${box.width * 100}%`,
  height: `${box.height * 100}%`
})

const getSelectionStyle = (box: { x: number; y: number; width: number; height: number }) => ({
  left: `${box.x}px`,
  top: `${box.y}px`,
  width: `${box.width}px`,
  height: `${box.height}px`
})

// 快捷键
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    if (isSelecting.value) {
      cancelSelection()
      isSelecting.value = false
    }
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.bill-image-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1a1a1a;
  border-radius: 8px;
  overflow: hidden;
}

.toolbar {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #2a2a2a;
  border-bottom: 1px solid #3a3a3a;
}

.image-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.image-wrapper {
  position: relative;
  transition: transform 0.1s ease-out;
}

.bill-image {
  display: block;
  max-width: none;
  max-height: none;
}

.ocr-overlay,
.selection-overlay {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

.selection-overlay {
  pointer-events: auto;
}

.ocr-box {
  position: absolute;
  border: 2px solid;
  pointer-events: auto;
  cursor: pointer;
  transition: all 0.2s;
}

.ocr-box.high {
  border-color: #67c23a;
  background: rgba(103, 194, 58, 0.1);
}

.ocr-box.medium {
  border-color: #e6a23c;
  background: rgba(230, 162, 60, 0.1);
}

.ocr-box.low {
  border-color: #f56c6c;
  background: rgba(245, 108, 108, 0.1);
}

.ocr-box:hover,
.ocr-box.active {
  background: rgba(64, 158, 255, 0.3);
  z-index: 10;
}

.box-tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.9);
  color: #fff;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  z-index: 100;
  pointer-events: none;
}

.box-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: rgba(0, 0, 0, 0.9);
}

.box-tooltip .field-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.box-tooltip .text {
  color: #409eff;
  margin-bottom: 4px;
}

.box-tooltip .confidence {
  font-size: 11px;
}

.box-tooltip .confidence.high {
  color: #67c23a;
}

.box-tooltip .confidence.medium {
  color: #e6a23c;
}

.box-tooltip .confidence.low {
  color: #f56c6c;
}

.selection-box {
  position: absolute;
  border: 2px dashed #409eff;
  background: rgba(64, 158, 255, 0.2);
}

.selection-actions {
  position: absolute;
  bottom: -40px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  white-space: nowrap;
}

.statusbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 16px;
  background: #2a2a2a;
  border-top: 1px solid #3a3a3a;
  font-size: 12px;
  color: #999;
}
</style>