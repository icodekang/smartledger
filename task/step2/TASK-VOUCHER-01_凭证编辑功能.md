# 任务编号：TASK-VOUCHER-01
# 任务名称：凭证编辑功能
# 优先级：P0
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发凭证编辑功能，支持修改会计科目、金额、摘要等信息，支持借贷平衡校验。

================================================================================
                              功能需求
================================================================================

## 1. 后端 API

### 1.1 获取凭证详情（含分录明细）
```
GET /api/v1/vouchers/{id}/detail

响应:
{
  "code": 200,
  "data": {
    "id": "uuid",
    "voucher_no": "PZ202403001",
    "voucher_date": "2024-03-01",
    "period": "202403",
    "summary": "支付货款",
    "status": "draft",
    "ai_confidence": 0.92,
    "source_type": "bill",  // bill:来自票据, manual:手工录入
    "source_bill_id": "uuid",
    
    "items": [
      {
        "id": "uuid",
        "line_no": 1,
        "subject_code": "1403",      // 科目代码
        "subject_name": "原材料",     // 科目名称
        "summary": "支付货款-材料",
        "debit_amount": 10000.00,     // 借方金额
        "credit_amount": 0,           // 贷方金额
        "auxiliary": {                // 辅助核算
          "department": "生产部",
          "project": "项目A"
        }
      },
      {
        "id": "uuid",
        "line_no": 2,
        "subject_code": "22210101",
        "subject_name": "应交税费-应交增值税-进项税额",
        "summary": "支付货款-进项税",
        "debit_amount": 1300.00,
        "credit_amount": 0,
        "auxiliary": {}
      },
      {
        "id": "uuid",
        "line_no": 3,
        "subject_code": "1002",
        "subject_name": "银行存款",
        "summary": "支付货款-银行",
        "debit_amount": 0,
        "credit_amount": 11300.00,
        "auxiliary": {
          "bank_account": "工商银行XXXX"
        }
      }
    ],
    
    "totals": {
      "debit": 11300.00,
      "credit": 11300.00,
      "is_balanced": true
    },
    
    "attachments": [
      {"type": "bill", "id": "uuid", "name": "发票.pdf"}
    ],
    
    "created_at": "2024-03-01T10:00:00",
    "created_by": "张三"
  }
}
```

### 1.2 更新凭证
```
PUT /api/v1/vouchers/{id}

请求体:
{
  "voucher_date": "2024-03-01",
  "period": "202403",
  "summary": "修改后的摘要",
  "items": [
    {
      "id": "uuid",  // 有id更新，无id新增
      "subject_code": "1403",
      "subject_name": "原材料",
      "summary": "明细摘要",
      "debit_amount": 10000,
      "credit_amount": 0,
      "auxiliary": {}
    }
  ]
}

响应: 标准响应
```

### 1.3 借贷平衡校验规则
```python
def validate_voucher_balance(items):
    """
    校验规则：
    1. 每条分录：借方和贷方不能同时有值
    2. 每条分录：借方和贷方必须有一个有值
    3. 整张凭证：借方合计必须等于贷方合计
    4. 整张凭证：至少有两条分录
    """
    total_debit = 0
    total_credit = 0
    
    for item in items:
        # 规则1: 不能同时有借有贷
        if item.debit_amount > 0 and item.credit_amount > 0:
            raise ValidationError(f"第{item.line_no}行：借贷方不能同时有金额")
        
        # 规则2: 必须有借或有贷
        if item.debit_amount == 0 and item.credit_amount == 0:
            raise ValidationError(f"第{item.line_no}行：借贷方必须输入一个金额")
        
        total_debit += item.debit_amount
        total_credit += item.credit_amount
    
    # 规则3: 借贷平衡
    if total_debit != total_credit:
        raise ValidationError(f"借贷不平衡：借方{total_debit} ≠ 贷方{total_credit}")
    
    # 规则4: 至少两条分录
    if len(items) < 2:
        raise ValidationError("凭证至少需要两条分录")
    
    return True
```

### 1.4 会计科目搜索
```
GET /api/v1/account-subjects?keyword=银行&page_size=20

响应:
{
  "code": 200,
  "data": {
    "items": [
      {"code": "1002", "name": "银行存款", "category": "资产", "balance_direction": "借"},
      {"code": "100201", "name": "银行存款-工商银行", "parent_code": "1002"}
    ]
  }
}
```

## 2. 前端页面设计

### 2.1 凭证编辑页面
```
┌─────────────────────────────────────────────────────────────────┐
│  编辑凭证                                            [X]        │
├─────────────────────────────────────────────────────────────────┤
│  基本信息                                                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 凭证日期: [2024-03-01    ]  会计期间: [202403  ]            ││
│  │ 凭证号:   [PZ202403001   ]  状态: [草稿  ]                  ││
│  │ 摘要:     [支付货款____________________________]            ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  分录明细                                            [+ 添加行]  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 行 │ 科目代码 │ 科目名称      │ 摘要       │ 借方    │ 贷方   ││
│  │ 1  │ [1403  ] │ [原材料 ▼]   │ [支付货款] │ [10000] │ [    ] ││
│  │ 2  │ [2221  ] │ [应交税费▼]  │ [进项税  ] │ [ 1300] │ [    ] ││
│  │ 3  │ [1002  ] │ [银行存款▼]  │ [银行支付] │ [     ] │ [11300]││
│  │    │         │              │            │         │        ││
│  │    │         │              │ 合计:      │ [11300] │ [11300]││
│  │    │         │              │            │ ✅平衡  │        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  关联附件                                                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 📎 发票12345678.pdf                              [查看]    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│                    [取消]  [保存草稿]  [提交审核]                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 科目选择组件

**下拉搜索框**:
- 支持按科目代码搜索（如输入 1002）
- 支持按科目名称搜索（如输入 "银行"）
- 支持拼音首字母搜索（如输入 "yh"）
- 显示科目层级（如 资产 > 流动资产 > 银行存款）

**下拉列表格式**:
```
┌───────────────────────────────────┐
│ 🔍 1002                          │
├───────────────────────────────────┤
│ 1002      银行存款        [资产]  │
│ 100201    ├ 工商银行      [资产]  │
│ 100202    ├ 建设银行      [资产]  │
│ 100203    └ 农业银行      [资产]  │
│                                   │
│ 1001      库存现金        [资产]  │ ← 相似科目 │
└───────────────────────────────────┘
```

### 2.3 金额输入优化

**智能输入**:
- 输入数字自动添加千分位
- 按 = 键自动计算（如输入 `5000+300`，按 = 显示 5300）
- Tab 键切换借贷方（借方有值时，Tab 自动跳到贷方）

**借贷平衡提示**:
```
合计行显示:
- 平衡: 借方 11,300.00 = 贷方 11,300.00 ✅
- 不平衡: 借方 10,000.00 ≠ 贷方 11,300.00 ❌ (差额: -1,300.00)
```

## 3. 组件设计

```vue
<!-- VoucherEditor.vue -->
<template>
  <el-dialog v-model="visible" title="编辑凭证" width="900px">
    <!-- 基本信息 -->
    <div class="basic-info">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="凭证日期">
            <el-date-picker v-model="form.voucher_date" value-format="YYYY-MM-DD" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="会计期间">
            <el-input v-model="form.period" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="凭证号">
            <el-input v-model="form.voucher_no" disabled />
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-form-item label="摘要">
        <el-input v-model="form.summary" placeholder="输入凭证摘要" />
      </el-form-item>
    </div>
    
    <!-- 分录表格 -->
    <div class="items-section">
      <div class="section-header">
        <span>分录明细</span>
        <el-button type="primary" size="small" @click="addItem" :icon="Plus">
          添加行
        </el-button>
      </div>
      
      <el-table :data="form.items" border class="items-table">
        <el-table-column type="index" label="行" width="50" />
        
        <el-table-column label="科目" min-width="200">
          <template #default="{ row, $index }">
            <AccountSubjectSelect
              v-model:code="row.subject_code"
              v-model:name="row.subject_name"
              @change="onSubjectChange($index, $event)"
            />
          </template>
        </el-table-column>
        
        <el-table-column label="摘要" min-width="150">
          <template #default="{ row }">
            <el-input v-model="row.summary" placeholder="明细摘要" />
          </template>
        </el-table-column>
        
        <el-table-column label="借方" width="140" align="right">
          <template #default="{ row }">
            <AmountInput v-model="row.debit_amount" @blur="onDebitBlur(row)" />
          </template>
        </el-table-column>
        
        <el-table-column label="贷方" width="140" align="right"
003e
          <template #default="{ row }">
            <AmountInput v-model="row.credit_amount" @blur="onCreditBlur(row)" />
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="80">
          <template #default="{ $index }">
            <el-button type="danger" link @click="removeItem($index)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 合计行 -->
      <div class="totals-row" :class="{ balanced: isBalanced }">
        <span class="label">合计:</span>
        <span class="debit">借方: {{ formatAmount(totalDebit) }}</span>
        <span class="credit">贷方: {{ formatAmount(totalCredit) }}</span>
        <el-tag :type="isBalanced ? 'success' : 'danger'">
          {{ isBalanced ? '✅ 借贷平衡' : `❌ 差额: ${formatAmount(difference)}` }}
        </el-tag>
      </div>
    </div>
    
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleSave" :loading="saving">保存草稿</el-button>
      <el-button type="success" @click="handleSubmit" :loading="submitting">提交审核</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// 借贷平衡计算
const totalDebit = computed(() => {
  return form.value.items.reduce((sum, item) => sum + (item.debit_amount || 0), 0)
})

const totalCredit = computed(() => {
  return form.value.items.reduce((sum, item) => sum + (item.credit_amount || 0), 0)
})

const isBalanced = computed(() => {
  return totalDebit.value === totalCredit.value && totalDebit.value > 0
})

const difference = computed(() => {
  return totalDebit.value - totalCredit.value
})

// 借贷互斥逻辑
const onDebitBlur = (row: VoucherItem) => {
  if (row.debit_amount > 0) {
    row.credit_amount = 0
  }
}

const onCreditBlur = (row: VoucherItem) => {
  if (row.credit_amount > 0) {
    row.debit_amount = 0
  }
}

// 保存前校验
const validate = () => {
  if (!isBalanced.value) {
    ElMessage.error('借贷不平衡，请检查分录金额')
    return false
  }
  if (form.value.items.length < 2) {
    ElMessage.error('凭证至少需要两条分录')
    return false
  }
  return true
}
</script>
```

## 4. 数据结构

```typescript
interface Voucher {
  id: string
  voucher_no: string
  voucher_date: string
  period: string
  summary: string
  status: 'draft' | 'pending' | 'approved' | 'rejected'
  ai_confidence?: number
  items: VoucherItem[]
  attachments: Attachment[]
}

interface VoucherItem {
  id?: string
  line_no: number
  subject_code: string
  subject_name: string
  summary: string
  debit_amount: number
  credit_amount: number
  auxiliary?: Record<string, string>
}

interface AccountSubject {
  code: string
  name: string
  category: '资产' | '负债' | '权益' | '成本' | '损益'
  balance_direction: '借' | '贷'
  parent_code?: string
  level: number
  is_active: boolean
}
```

================================================================================
                              验收标准
================================================================================

1. [ ] 凭证基本信息可编辑，保存后更新正确
2. [ ] 分录支持增删改，行号自动重排
3. [ ] 科目选择组件搜索功能正常，显示层级
4. [ ] 借贷金额输入互斥，不能同时有值
5. [ ] 借贷平衡实时计算，提示清晰
6. [ ] 不平衡时禁止保存，提示差额
7. [ ] 少于两条分录时禁止保存
8. [ ] 提交审核后状态变更正确

================================================================================
                              开发提示
================================================================================

1. 会计科目数据预加载到前端或使用虚拟滚动
2. 金额输入使用 input[type="number"] 或 el-input-number
3. 借贷平衡计算使用 Decimal.js 避免精度问题
4. 表格行拖拽排序可选（使用 Sortable.js）
5. 保存前在前端做一次完整校验，减少无效请求
