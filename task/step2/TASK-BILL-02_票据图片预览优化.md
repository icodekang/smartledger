# 任务编号：TASK-BILL-02
# 任务名称：票据图片预览优化
# 优先级：P1
# 预估工期：2天
# 负责人：前端开发

================================================================================
                              任务描述
================================================================================

开发票据图片预览组件，支持缩放、OCR 框选标注、区域重新识别等功能。

================================================================================
                              功能需求
================================================================================

## 1. 图片预览组件

### 1.1 基础功能
```
┌─────────────────────────────────────────────────────────┐
│  [←] [放大] [缩小] [适应窗口] [原始尺寸] [旋转] [下载]    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                      ┌─────────┐                       │
│                      │ 票据图片 │                       │
│                      │         │                       │
│                      │ ┌─────┐ │                       │
│                      │ │框选区│ │ ← OCR识别区域高亮     │
│                      │ └─────┘ │                       │
│                      │         │                       │
│                      └─────────┘                       │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  缩放: 100%  |  文件: xxx.jpg (2.3MB)                    │
└─────────────────────────────────────────────────────────┘
```

### 1.2 组件 Props
```typescript
interface BillImageViewerProps {
  // 图片URL
  url: string
  // OCR识别框数据
  ocrBoxes?: OcrBox[]
  // 是否可编辑（显示重新识别按钮）
  editable?: boolean
  // 初始缩放比例
  initialScale?: number
  // 框选颜色配置
  boxColors?: {
    high: string    // 高置信度 (>0.9)
    medium: string  // 中置信度 (0.7-0.9)
    low: string     // 低置信度 (<0.7)
  }
}

interface OcrBox {
  field: string      // 字段名
  text: string       // 识别文本
  confidence: number // 置信度
  x: number          // 左上角x（相对图片比例 0-1）
  y: number          // 左上角y
  width: number      // 宽度
  height: number     // 高度
}
```

### 1.3 组件事件
```typescript
interface BillImageViewerEmits {
  // 点击识别框
  boxClick: (box: OcrBox) => void
  // 框选区域（用户手动选择）
  regionSelect: (region: Region) => void
  // 缩放变化
  scaleChange: (scale: number) => void
}
```

## 2. 图片标注功能

### 2.1 OCR 识别区域高亮
- 根据置信度显示不同颜色边框
- 悬停显示识别文本和置信度
- 点击字段名在右侧表单中定位

### 2.2 手动框选识别
```
操作步骤:
1. 点击"区域识别"按钮进入选择模式
2. 鼠标拖拽框选图片上的区域
3. 松开鼠标弹出识别结果
4. 选择要填充的表单字段
```

### 2.3 框选交互
- 支持拖拽调整框选区域
- 支持删除误识别的框
- 支持手动添加框选区域

## 3. 重新识别功能

### 3.1 接口设计
```
POST /api/v1/invoices/{id}/re-recognize

请求体:
{
  "region": {  // 可选，不传则全图识别
    "x": 0.1,
    "y": 0.2,
    "width": 0.3,
    "height": 0.1
  },
  "field": "seller_name"  // 可选，指定识别的字段
}

响应:
{
  "code": 200,
  "data": {
    "text": "识别结果文本",
    "confidence": 0.95,
    "box": {...}
  }
}
```

### 3.2 重新识别按钮
在详情页每个表单字段旁添加"重新识别"按钮：
- 点击后该字段对应的图片区域闪烁高亮
- 用户可调整框选范围
- 确认后重新识别并填充

## 4. 缩略图导航

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                    [大图预览区]                          │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ [缩略图] [缩略图] [缩略图] [缩略图] [+ 添加图片]         │
│  图1     图2     图3     图4                            │
└─────────────────────────────────────────────────────────┘
```

- 支持多张票据图片切换
- 缩略图显示处理状态图标
- 点击缩略图切换大图

## 5. 组件实现

```vue
<!-- BillImageViewer.vue -->
<template>
  <div class="image-viewer" ref="container">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button-group>
        <el-button @click="zoomOut" :icon="ZoomOut" />
        <el-button @click="zoomIn" :icon="ZoomIn" />
        <el-button @click="fitToWindow">适应窗口</el-button>
        <el-button @click="resetScale">原始尺寸</el-button>
      </el-button-group>
      <el-divider direction="vertical" />
      <el-button @click="rotate" :icon="RefreshRight" />
      <el-button @click="download" :icon="Download" />
      <el-button v-if="editable" @click="startRegionSelect" 
                    :type="isSelecting ? 'primary' : ''">区域识别</el-button>
    </div>
    
    <!-- 图片区域 -->
    <div class="image-container" @wheel="handleWheel"
         @mousedown="startDrag" @mousemove="onDrag" @mouseup="endDrag"
         @mouseleave="endDrag">
      <div class="image-wrapper" :style="wrapperStyle">
        <img ref="image" :src="url" @load="onImageLoad" />
        
        <!-- OCR 框选层 -->
        <div class="ocr-overlay">
          <div v-for="box in ocrBoxes"
               :key="box.field"
               class="ocr-box"
               :class="getConfidenceClass(box.confidence)"
               :style="getBoxStyle(box)"
               @click="$emit('boxClick', box)"
               @mouseenter="hoverBox = box"
               @mouseleave="hoverBox = null">
            <!-- 悬停提示 -->
            <div v-if="hoverBox === box" class="box-tooltip">
              <div>{{ box.field }}: {{ box.text }}</div>
              <div class="confidence">置信度: {{ (box.confidence * 100).toFixed(1) }}%</div>
            </div>
          </div>
        </div>
        
        <!-- 用户框选层 -->
        <div v-if="userSelection" class="user-selection"
             :style="getSelectionStyle(userSelection)">
          <div class="selection-actions">
            <el-button size="small" @click="recognizeRegion">识别</el-button>
            <el-button size="small" @click="cancelSelection">取消</el-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 状态栏 -->
    <div class="statusbar">
      <span>缩放: {{ Math.round(scale * 100) }}%</span>
      <el-divider direction="vertical" />
      <span v-if="imageInfo">{{ imageInfo.name }} ({{ formatSize(imageInfo.size) }})</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ZoomIn, ZoomOut, RefreshRight, Download } from '@element-plus/icons-vue'

const props = defineProps<BillImageViewerProps>()
const emit = defineEmits<BillImageViewerEmits>()

// 缩放控制
const scale = ref(props.initialScale || 1)
const minScale = 0.1
const maxScale = 5

const zoomIn = () => {
  scale.value = Math.min(scale.value * 1.2, maxScale)
}

const zoomOut = () => {
  scale.value = Math.max(scale.value / 1.2, minScale)
}

const handleWheel = (e: WheelEvent) => {
  e.preventDefault()
  if (e.deltaY < 0) {
    zoomIn()
  } else {
    zoomOut()
  }
}

// 框选样式计算
const getBoxStyle = (box: OcrBox) => {
  return {
    left: `${box.x * 100}%`,
    top: `${box.y * 100}%`,
    width: `${box.width * 100}%`,
    height: `${box.height * 100}%`,
  }
}

const getConfidenceClass = (confidence: number) => {
  if (confidence >= 0.9) return 'high'
  if (confidence >= 0.7) return 'medium'
  return 'low'
}

// 区域选择
const isSelecting = ref(false)
const userSelection = ref<Region | null>(null)
const selectionStart = ref<{ x: number; y: number } | null>(null)

const startRegionSelect = () => {
  isSelecting.value = true
}

// 拖拽框选逻辑...
</script>

<style scoped>
.image-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1a1a1a;
}

.image-container {
  flex: 1;
  overflow: hidden;
  position: relative;
  cursor: grab;
}

.image-container:active {
  cursor: grabbing;
}

.image-wrapper {
  position: relative;
  transform-origin: center;
  transition: transform 0.1s;
}

.ocr-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
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

.ocr-box:hover {
  background: rgba(64, 158, 255, 0.3);
}

.box-tooltip {
  position: absolute;
  bottom: 100%;
  left: 0;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  z-index: 100;
}
</style>
```

## 6. 技术选型

| 功能 | 方案 | 说明 |
|------|------|------|
| 图片预览基础 | viewerjs / 自研 | 支持缩放、旋转 |
| 图片裁剪 | cropperjs | 区域选择 |
| 手势支持 | hammerjs | 移动端缩放拖拽 |
| 图片加载 | 渐进式加载 | 大图片优化 |

================================================================================
                              验收标准
================================================================================

1. [ ] 图片缩放范围 10%~500%，流畅无卡顿
2. [ ] OCR 框选区域正确显示在图片对应位置
3. [ ] 框选颜色根据置信度正确区分
4. [ ] 悬停显示识别文本和置信度
5. [ ] 区域识别功能正常，框选后可重新识别
6. [ ] 图片旋转功能正常
7. [ ] 下载功能正常
8. [ ] 移动端手势操作支持

================================================================================
                              开发提示
================================================================================

1. 使用 CSS transform: scale() 实现缩放，性能更好
2. OCR 框坐标使用百分比（0-1），适配不同尺寸
3. 大图片使用懒加载，避免内存溢出
4. 拖拽使用 transform: translate() 实现
5. 考虑使用 Canvas 绘制框选区域（性能更好）
