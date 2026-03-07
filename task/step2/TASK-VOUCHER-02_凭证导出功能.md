# 任务编号：TASK-VOUCHER-02
# 任务名称：凭证导出功能
# 优先级：P1
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发凭证导出功能，支持导出为 PDF 和 Excel 格式，支持批量导出。

================================================================================
                              功能需求
================================================================================

## 1. 后端 API

### 1.1 导出单个凭证
```
GET /api/v1/vouchers/{id}/export?format=pdf

响应: 文件流 (Content-Type: application/pdf 或 application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)
```

### 1.2 批量导出
```
POST /api/v1/vouchers/export

请求体:
{
  "ids": ["uuid1", "uuid2", "uuid3"],
  "format": "pdf",  // pdf 或 excel
  "options": {
    "template": "standard",  // 模板样式
    "include_attachment": false  // 是否包含附件
  }
}

响应:
{
  "code": 200,
  "data": {
    "download_url": "/files/export/vouchers_20240307.zip",
    "expires_at": "2024-03-07T12:00:00",
    "file_size": 1024000
  }
}
```

### 1.3 获取导出模板列表
```
GET /api/v1/vouchers/export-templates

响应:
{
  "code": 200,
  "data": [
    {"id": "standard", "name": "标准格式", "description": "通用记账凭证格式"},
    {"id": "compact", "name": "紧凑格式", "description": "一页多张凭证"},
    {"id": "detail", "name": "详细格式", "description": "包含完整辅助信息"}
  ]
}
```

## 2. PDF 导出实现

### 2.1 单张凭证模板
```
┌─────────────────────────────────────────────────────────────────┐
│                         记 账 凭 证                              │
├─────────────────────────────────────────────────────────────────┤
│  日期: 2024年03月01日    凭证号: 记字第001号    附单据: 1张     │
├─────────────────┬───────────────────────────────────────────────┤
│     摘  要      │   会计科目   │ 借方金额 │ 贷方金额 │ 过账 │
├─────────────────┼──────────────┼──────────┼──────────┼──────┤
│ 支付货款-材料   │  原材料      │ 10,000.00│          │      │
├─────────────────┼──────────────┼──────────┼──────────┼──────┤
│ 支付货款-进项税 │  应交税费    │  1,300.00│          │      │
├─────────────────┼──────────────┼──────────┼──────────┼──────┤
│ 支付货款-银行   │  银行存款    │          │ 11,300.00│      │
├─────────────────┼──────────────┼──────────┼──────────┼──────┤
│     合  计      │              │ 11,300.00│ 11,300.00│      │
├─────────────────┴──────────────┴──────────┴──────────┴──────┤
│  主管: ______  记账: ______  出纳: ______  审核: ______        │
│  制单: 张三                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 技术实现
```python
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 注册中文字体
pdfmetrics.registerFont(TTFont('SimSun', 'simsun.ttc'))

def generate_voucher_pdf(voucher: Voucher) -> bytes:
    """生成凭证 PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # 标题
    title = Paragraph("记账凭证", styles['Title'])
    elements.append(title)
    
    # 表头信息
    header_data = [
        f"日期: {voucher.voucher_date}",
        f"凭证号: {voucher.voucher_no}",
        f"附单据: {len(voucher.attachments)}张"
    ]
    
    # 分录表格
    table_data = [['摘要', '会计科目', '借方金额', '贷方金额', '过账']]
    for item in voucher.items:
        table_data.append([
            item.summary,
            f"{item.subject_code} {item.subject_name}",
            f"{item.debit_amount:,.2f}" if item.debit_amount else '',
            f"{item.credit_amount:,.2f}" if item.credit_amount else '',
            ''
        ])
    
    # 合计行
    total_debit = sum(item.debit_amount for item in voucher.items)
    total_credit = sum(item.credit_amount for item in voucher.items)
    table_data.append(['合计', '', f"{total_debit:,.2f}", f"{total_credit:,.2f}", ''])
    
    # 创建表格
    table = Table(table_data, colWidths=[120, 150, 80, 80, 40])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'SimSun'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    return buffer.getvalue()
```

### 2.3 批量导出（Zip 打包）
```python
def batch_export_vouchers(voucher_ids: List[str], format: str) -> str:
    """批量导出凭证"""
    import zipfile
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"vouchers_{datetime.now().strftime('%Y%m%d')}.zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for voucher_id in voucher_ids:
            voucher = get_voucher(voucher_id)
            
            if format == 'pdf':
                content = generate_voucher_pdf(voucher)
                filename = f"{voucher.voucher_no}.pdf"
            else:
                content = generate_voucher_excel(voucher)
                filename = f"{voucher.voucher_no}.xlsx"
            
            zipf.writestr(filename, content)
    
    # 上传到 MinIO，返回下载链接
    return upload_to_minio(zip_path)
```

## 3. Excel 导出实现

### 3.1 单张凭证 Excel 格式
```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side

def generate_voucher_excel(voucher: Voucher) -> bytes:
    """生成凭证 Excel"""
    wb = Workbook()
    ws = wb.active
    ws.title = voucher.voucher_no
    
    # 标题
    ws.merge_cells('A1:E1')
    ws['A1'] = '记账凭证'
    ws['A1'].font = Font(size=16, bold=True)
    ws['A1'].alignment = Alignment(horizontal='center')
    
    # 表头信息
    ws['A2'] = f'日期: {voucher.voucher_date}'
    ws['C2'] = f'凭证号: {voucher.voucher_no}'
    ws['E2'] = f'附单据: {len(voucher.attachments)}张'
    
    # 表头
    headers = ['摘要', '会计科目', '借方金额', '贷方金额', '过账']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
    
    # 数据行
    for row, item in enumerate(voucher.items, 5):
        ws.cell(row=row, column=1, value=item.summary)
        ws.cell(row=row, column=2, value=f"{item.subject_code} {item.subject_name}")
        if item.debit_amount:
            ws.cell(row=row, column=3, value=item.debit_amount)
        if item.credit_amount:
            ws.cell(row=row, column=4, value=item.credit_amount)
    
    # 合计行
    total_row = 5 + len(voucher.items)
    ws.cell(row=total_row, column=1, value='合计')
    ws.cell(row=total_row, column=3, value=sum(i.debit_amount for i in voucher.items))
    ws.cell(row=total_row, column=4, value=sum(i.credit_amount for i in voucher.items))
    
    # 设置边框
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    for row in ws.iter_rows(min_row=4, max_row=total_row, min_col=1, max_col=5):
        for cell in row:
            cell.border = thin_border
    
    # 调整列宽
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 10
    
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return buffer.getvalue()
```

### 3.2 批量凭证汇总表
```python
def generate_voucher_summary_excel(voucher_ids: List[str]) -> bytes:
    """生成凭证汇总表"""
    wb = Workbook()
    ws = wb.active
    ws.title = "凭证汇总"
    
    # 标题行
    headers = ['凭证号', '日期', '摘要', '科目代码', '科目名称', '借方金额', '贷方金额']
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    
    # 数据行
    row = 2
    for voucher_id in voucher_ids:
        voucher = get_voucher(voucher_id)
        for item in voucher.items:
            ws.cell(row=row, column=1, value=voucher.voucher_no)
            ws.cell(row=row, column=2, value=voucher.voucher_date)
            ws.cell(row=row, column=3, value=item.summary)
            ws.cell(row=row, column=4, value=item.subject_code)
            ws.cell(row=row, column=5, value=item.subject_name)
            ws.cell(row=row, column=6, value=item.debit_amount or '')
            ws.cell(row=row, column=7, value=item.credit_amount or '')
            row += 1
    
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return buffer.getvalue()
```

## 4. 前端实现

### 4.1 导出按钮和菜单
```vue
<el-dropdown @command="handleExport">
  <el-button type="primary">
    <el-icon><Download /></el-icon>
    导出
    <el-icon><ArrowDown /></el-icon>
  </el-button>
  
  <template #dropdown>
    <el-dropdown-menu>
      <el-dropdown-item command="pdf">导出为 PDF</el-dropdown-item>
      <el-dropdown-item command="excel">导出为 Excel</el-dropdown-item>
      <el-dropdown-item divided command="batch">批量导出...</el-dropdown-item>
    </el-dropdown-menu>
  </template>
</el-dropdown>
```

### 4.2 批量导出对话框
```
┌─────────────────────────────────────────────────────────┐
│  批量导出                                        [X]    │
├─────────────────────────────────────────────────────────┤
│  已选择 3 张凭证                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ ☑ PZ202403001 | 2024-03-01 | 支付货款          │   │
│  │ ☑ PZ202403002 | 2024-03-02 | 采购材料          │   │
│  │ ☑ PZ202403003 | 2024-03-02 | 办公费用          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  导出格式:  ● PDF    ○ Excel                             │
│  导出模板:  [标准格式 ▼]                                  │
│                                                          │
│  高级选项:                                               │
│  ☑ 每张凭证单独文件                                     │
│  ☐ 打包为 Zip                                           │
│  ☐ 包含关联附件                                         │
│                                                          │
│              [取消]  [开始导出]                          │
└─────────────────────────────────────────────────────────┘
```

### 4.3 导出进度
```
导出中...
[████████████████████░░░░░] 80%

正在导出: PZ202403003.pdf
已导出: 2/3 个文件
```

### 4.4 下载处理
```typescript
const handleExport = async (command: string) => {
  if (command === 'pdf' || command === 'excel') {
    // 单张导出
    const res = await voucherApi.export(voucherId.value, command)
    downloadFile(res.data, `${voucher.value.voucher_no}.${command}`)
  } else if (command === 'batch') {
    // 批量导出
    showBatchExportDialog.value = true
  }
}

const downloadFile = (data: Blob, filename: string) => {
  const url = window.URL.createObjectURL(new Blob([data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
```

## 5. 技术要求

### 5.1 依赖库
```
# Python 后端
reportlab==3.6.12      # PDF 生成
openpyxl==3.1.2        # Excel 生成
Pillow==9.5.0          # 图片处理

# Node.js 前端
file-saver             # 文件下载
```

### 5.2 字体支持
- 系统需安装中文字体（宋体、黑体）
- Docker 镜像中需包含字体文件

### 5.3 性能考虑
- 单张凭证导出响应时间 < 2 秒
- 批量导出最多支持 50 张凭证
- 大文件使用流式传输

================================================================================
                              验收标准
================================================================================

1. [ ] PDF 导出格式正确，包含完整凭证信息
2. [ ] Excel 导出数据正确，格式规范
3. [ ] 批量导出打包为 Zip 正常
4. [ ] 导出文件中文显示正常
5. [ ] 文件名包含凭证号，便于识别
6. [ ] 批量导出进度提示正常
7. [ ] 导出下载链接有过期时间（24小时）
8. [ ] 模板选择功能正常

================================================================================
                              开发提示
================================================================================

1. PDF 生成使用 reportlab，注意中文字体注册
2. Excel 使用 openpyxl，支持样式设置
3. 批量导出使用异步任务 + WebSocket 进度通知
4. 导出文件上传到 MinIO，返回临时下载链接
5. 定期清理过期的导出文件
