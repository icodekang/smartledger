# 任务编号：TASK-BILL-01
# 任务名称：票据详情编辑功能
# 优先级：P0
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发票据详情查看和编辑功能，支持人工修正 OCR 识别结果。

================================================================================
                              功能需求
================================================================================

## 1. 后端 API

### 1.1 获取票据详情（含图片和 OCR 结果）
```
GET /api/v1/invoices/{id}/detail

响应:
{
  "code": 200,
  "data": {
    "id": "uuid",
    "invoice_code": "发票代码",
    "invoice_number": "发票号码",
    "invoice_date": "2024-03-01",
    "seller_name": "销售方名称",
    "seller_tax_no": "销售方税号",
    "buyer_name": "购买方名称",
    "buyer_tax_no": "购买方税号",
    "amount": 10000.00,
    "tax_amount": 1300.00,
    "total_amount": 11300.00,
    "items": [
      {
        "name": "商品名称",
        "spec": "规格",
        "quantity": 1,
        "unit_price": 10000.00,
        "amount": 10000.00,
        "tax_rate": "13%",
        "tax_amount": 1300.00
      }
    ],
    "image_url": "/files/xxx.jpg",  // 原图
    "ocr_result": {  // OCR 原始识别结果
      "raw_text": "识别的原始文本",
      "confidence": 0.95,
      "fields": {...}
    },
    "process_status": "ocr_completed",
    "created_at": "2024-03-01T10:00:00"
  }
}
```

### 1.2 更新票据信息
```
PUT /api/v1/invoices/{id}

请求体:
{
  "invoice_code": "更新后的发票代码",
  "invoice_number": "更新后的发票号码",
  "invoice_date": "2024-03-01",
  "seller_name": "更新后的销售方",
  "seller_tax_no": "更新后的税号",
  "buyer_name": "更新后的购买方",
  "buyer_tax_no": "更新后的税号",
  "amount": 10000.00,
  "tax_amount": 1300.00,
  "total_amount": 11300.00,
  "items": [...]  // 商品明细
}

响应: 标准响应
```

### 1.3 更新票据明细项
```
PUT /api/v1/invoices/{id}/items

请求体:
{
  "items": [
    {
      "id": "uuid",  // 有id则更新，无则新增
      "name": "商品名称",
      "spec": "规格型号",
      "unit": "单位",
      "quantity": 1,
      "unit_price": 10000.00,
      "amount": 10000.00,
      "tax_rate": "13%",
      "tax_amount": 1300.00
    }
  ]
}
```

## 2. 前端页面设计

### 2.1 详情编辑对话框
```
┌─────────────────────────────────────────────────────────────────┐
│  票据详情                                            [X]        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┬─────────────────────────────────────┐ │
│  │                     │  基本信息                            │ │
│  │   [票据图片预览]     │  ─────────────────────────────────  │ │
│  │                     │  发票代码: [________________] [纠错] │ │
│  │   [查看原图]         │  发票号码: [________________] [纠错] │ │
│  │   [重新识别]         │  开票日期: [________________]       │ │
│  │                     │  金额合计: [________________]       │ │
│  │                     │  税额合计: [________________]       │ │
│  │                     │  价税合计: [________________]       │ │
│  │                     │                                      │ │
│  │                     │  销售方信息                          │ │
│  │                     │  ─────────────────────────────────  │ │
│  │                     │  名称: [________________________]   │ │
│  │                     │  税号: [________________]           │ │
│  │                     │                                      │ │
│  │                     │  购买方信息                          │ │
│  │                     │  ─────────────────────────────────  │ │
│  │                     │  名称: [________________________]   │ │
│  │                     │  税号: [________________]           │ │
│  └─────────────────────┴─────────────────────────────────────┘ │
│                                                                  │
│  商品明细                                                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 行号 │ 商品名称 │ 规格 │ 数量 │ 单价 │ 金额 │ 税率 │ 税额  ││
│  │ 1    │ [输入]  │ [输入]│[输入]│[输入]│[输入]│[选择]│[计算] ││
│  │ 2    │ [输入]  │ [输入]│[输入]│[输入]│[输入]│[选择]│[计算] ││
│  │ [+ 添加行]                                                   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│                    [取消]  [保存修改]                            │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 字段校验规则

| 字段 | 必填 | 校验规则 |
|------|------|----------|
| invoice_code | 是 | 10或12位数字 |
| invoice_number | 是 | 8或20位数字/字母 |
| invoice_date | 是 | 合法日期，不能超过今天 |
| seller_name | 是 | 长度 2-100 |
| seller_tax_no | 是 | 15、18或20位 |
| amount | 是 | 数字，≥0 |
| tax_amount | 是 | 数字，≥0 |
| total_amount | 是 | 必须等于 amount + tax_amount |

### 2.3 智能辅助功能

**金额自动计算**:
```javascript
// 修改金额时自动计算
watch: {
  'form.amount'(val) {
    this.form.tax_amount = calculateTax(val, this.form.tax_rate)
    this.form.total_amount = val + this.form.tax_amount
  }
}
```

**历史输入提示**:
- 销售方名称：输入时提示历史使用过的名称
- 商品名称：输入时提示历史商品库

**一键纠错**:
- 点击字段旁的"纠错"按钮，弹出 OCR 识别置信度低的候选值
- 支持从原图中框选区域重新识别

## 3. 组件设计

```vue
<!-- BillDetailDialog.vue -->
<template>
  <el-dialog v-model="visible" title="票据详情" width="900px">
    <div class="detail-layout">
      <!-- 左侧图片 -->
      <div class="image-section">
        <BillImageViewer 
          :url="bill.image_url" 
          :ocrBoxes="ocrResult.boxes"
          @boxClick="onBoxClick"
        />
      </div>
      
      <!-- 右侧表单 -->
      <div class="form-section">
        <el-form :model="form" :rules="rules" ref="formRef">
          <!-- 基本信息 -->
          <div class="section-title">基本信息</div>
          <el-row :gutter="20">
            <el-col :span="12">
              <FormFieldWithOcr
                label="发票代码"
                v-model="form.invoice_code"
                :ocrCandidates="ocrFields.invoice_code"
              />
            </el-col>
            <el-col :span="12">
              <FormFieldWithOcr
                label="发票号码"
                v-model="form.invoice_number"
                :ocrCandidates="ocrFields.invoice_number"
              />
            </el-col>
          </el-row>
          
          <!-- 金额信息 -->
          <div class="section-title">金额信息</div>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="金额" prop="amount">
                <el-input-number v-model="form.amount" :precision="2" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="税额">
                <el-input-number v-model="form.tax_amount" :precision="2" disabled />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="价税合计">
                <el-input-number v-model="form.total_amount" :precision="2" disabled />
              </el-form-item>
            </el-col>
          </el-row>
          
          <!-- 销售方信息 -->
          <div class="section-title">销售方信息</div>
          <el-form-item label="名称" prop="seller_name">
            <SuggestionInput
              v-model="form.seller_name"
              :fetchSuggestions="fetchSellerSuggestions"
            />
          </el-form-item>
          
          <!-- 商品明细 -->
          <div class="section-title">商品明细</div>
          <BillItemTable v-model="form.items" />
          
        </el-form>
      </div>
    </div>
    
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
    </template>
  </el-dialog>
</template>
```

## 4. 数据结构

```typescript
interface BillDetail {
  id: string
  invoice_code: string
  invoice_number: string
  invoice_date: string
  invoice_type: string
  
  seller_name: string
  seller_tax_no: string
  seller_address: string
  seller_bank: string
  
  buyer_name: string
  buyer_tax_no: string
  buyer_address: string
  buyer_bank: string
  
  amount: number
  tax_amount: number
  total_amount: number
  
  items: BillItem[]
  image_url: string
  ocr_result: OcrResult
  process_status: string
}

interface BillItem {
  id?: string
  name: string
  spec?: string
  unit?: string
  quantity: number
  unit_price: number
  amount: number
  tax_rate: string
  tax_amount: number
}

interface OcrResult {
  raw_text: string
  confidence: number
  fields: Record<string, {
    value: string
    confidence: number
    box: [number, number, number, number]  // x, y, width, height
  }>
}
```

================================================================================
                              验收标准
================================================================================

1. [ ] 详情对话框正常显示，图片和表单左右布局
2. [ ] 所有字段可编辑，保存后数据正确更新
3. [ ] 金额自动计算逻辑正确
4. [ ] 表单校验规则生效，错误提示清晰
5. [ ] 商品明细支持增删改
6. [ ] OCR 候选值提示功能正常
7. [ ] 历史输入提示功能正常
8. [ ] 保存后列表数据自动刷新

================================================================================
                              开发提示
================================================================================

1. 图片预览组件复用 Element Plus 的 Image 或使用 viewerjs
2. 表单使用 el-form，配置 rules 进行校验
3. 金额计算使用 Decimal.js 避免浮点精度问题
4. 历史提示使用 el-autocomplete 组件
5. 明细表格支持拖拽排序（可选）
