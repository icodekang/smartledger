# 任务编号：TEST-E2E-01
# 任务名称：端到端功能测试（票据录入到凭证生成）
# 负责人：测试工程师
# 工期：3天
# 依赖：全部MVP开发任务完成

================================================================================
                            任务详细说明书
================================================================================

## 一、任务目标
模拟真实用户场景，验证从票据上传到最终生成会计凭证的完整业务流程。

## 二、测试场景

### 2.1 场景一：标准业务流程
**流程：** 登录 → 上传发票 → OCR识别 → 解析确认 → 生成凭证 → 审核 → 入账

### 2.2 场景二：批量处理流程
**流程：** 登录 → 批量上传（20张） → 自动识别 → 批量匹配银行流水 → 批量生成凭证

### 2.3 场景三：异常处理流程
**流程：** 上传 → 识别失败 → 重试 → 手动录入 → 异常标记 → 生成凭证

### 2.4 场景四：审核驳回重新提交流程
**流程：** 提交 → 审核驳回 → 修改 → 重新提交 → 审核通过 → 入账

## 三、测试用例示例

```python
# tests/e2e/test_invoice_to_voucher.py

import pytest
from playwright.sync_api import sync_playwright
from app.main import app
from fastapi.testclient import TestClient

class TestEndToEndFlow:
    """端到端业务流程测试"""
    
    @pytest.fixture(scope="class")
    def browser(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            yield browser
            browser.close()
    
    def test_standard_invoice_to_voucher_flow(self, browser):
        """标准业务流程：票据录入到凭证生成"""
        page = browser.new_page()
        
        try:
            # Step 1: 登录系统
            page.goto("http://localhost:3000/login")
            page.fill("[data-testid=email]", "test@example.com")
            page.fill("[data-testid=password]", "TestPass123!")
            page.click("[data-testid=login-btn]")
            
            # 等待登录成功跳转
            page.wait_for_url("http://localhost:3000/dashboard")
            assert page.is_visible("[data-testid=user-menu]")
            
            # Step 2: 进入票据管理页面
            page.click("[data-testid=nav-invoices]")
            page.wait_for_selector("[data-testid=upload-btn]")
            
            # Step 3: 上传发票
            with page.expect_filechooser() as fc_info:
                page.click("[data-testid=upload-btn]")
            filechooser = fc_info.value
            filechooser.set_files("tests/fixtures/vat_invoice_sample.jpg")
            
            # 等待上传成功
            page.wait_for_selector("[data-testid=upload-success]")
            invoice_id = page.get_attribute("[data-testid=invoice-card]:first-child", "data-invoice-id")
            
            # Step 4: 等待OCR识别完成（轮询或WebSocket）
            page.wait_for_selector(
                f"[data-invoice-id='{invoice_id}'][data-status='completed']",
                timeout=30000
            )
            
            # Step 5: 查看识别结果并确认
            page.click(f"[data-invoice-id='{invoice_id}'] [data-testid=view-btn]")
            page.wait_for_selector("[data-testid=invoice-detail]")
            
            # 验证解析结果
            assert page.is_visible("text=增值税")
            assert page.is_visible("text=金额")
            
            # 确认信息无误
            page.click("[data-testid=confirm-btn]")
            page.wait_for_selector("[data-testid=confirm-success]")
            
            # Step 6: 生成凭证
            page.click("[data-testid=generate-voucher-btn]")
            page.wait_for_selector("[data-testid=voucher-preview]")
            
            # 验证凭证预览
            assert page.is_visible("text=借方")
            assert page.is_visible("text=贷方")
            
            # 确认生成凭证
            page.click("[data-testid=confirm-voucher-btn]")
            page.wait_for_selector("[data-testid=voucher-success]")
            
            # Step 7: 验证凭证已创建
            page.click("[data-testid=nav-vouchers]")
            page.wait_for_selector(f"text={invoice_id}")
            
        finally:
            page.close()
    
    def test_batch_invoice_processing(self, browser):
        """批量发票处理流程"""
        page = browser.new_page()
        
        try:
            # 登录
            page.goto("http://localhost:3000/login")
            page.fill("[data-testid=email]", "accountant@example.com")
            page.fill("[data-testid=password]", "TestPass123!")
            page.click("[data-testid=login-btn]")
            page.wait_for_url("http://localhost:3000/dashboard")
            
            # 进入批量上传页面
            page.click("[data-testid=nav-invoices]")
            page.click("[data-testid=batch-upload-btn]")
            
            # 批量选择文件（最多20个）
            test_files = [f"tests/fixtures/invoice_{i}.jpg" for i in range(1, 6)]
            with page.expect_filechooser() as fc_info:
                page.click("[data-testid=select-files-btn]")
            filechooser = fc_info.value
            filechooser.set_files(test_files)
            
            # 等待批量上传完成
            page.wait_for_selector("[data-testid=batch-upload-complete]")
            
            # 验证上传数量
            upload_count = page.inner_text("[data-testid=upload-count]")
            assert upload_count == "5"
            
            # 等待所有识别完成
            page.wait_for_selector(
                "[data-testid=pending-count]",
                state="hidden",
                timeout=120000
            )
            
            # 批量生成凭证
            page.click("[data-testid=select-all]")
            page.click("[data-testid=batch-voucher-btn]")
            
            # 配置批量生成选项
            page.select_option("[data-testid=voucher-date-type]", "invoice_date")
            page.click("[data-testid=confirm-batch-btn]")
            
            # 等待批量处理完成
            page.wait_for_selector("[data-testid=batch-complete]")
            
            # 验证结果
            success_count = page.inner_text("[data-testid=success-count]")
            assert int(success_count) == 5
            
        finally:
            page.close()
    
    def test_error_handling_and_retry(self, browser):
        """错误处理和重试流程"""
        page = browser.new_page()
        
        try:
            # 登录
            page.goto("http://localhost:3000/login")
            page.fill("[data-testid=email]", "test@example.com")
            page.fill("[data-testid=password]", "TestPass123!")
            page.click("[data-testid=login-btn]")
            
            # 上传一张模糊/损坏的发票（模拟识别失败）
            page.click("[data-testid=nav-invoices]")
            with page.expect_filechooser() as fc_info:
                page.click("[data-testid=upload-btn]")
            filechooser = fc_info.value
            filechooser.set_files("tests/fixtures/blurry_invoice.jpg")
            
            # 等待识别失败
            page.wait_for_selector("[data-testid=ocr-failed]")
            
            # 点击重试
            page.click("[data-testid=retry-btn]")
            
            # 如果再次失败，切换到手动录入
            try:
                page.wait_for_selector("[data-testid=ocr-success]", timeout=10000)
            except:
                # 重试失败，手动录入
                page.click("[data-testid=manual-entry-btn]")
                
                # 填写发票信息
                page.fill("[data-testid=invoice-code]", "011001900111")
                page.fill("[data-testid=invoice-number]", "12345678")
                page.fill("[data-testid=seller-name]", "测试供应商")
                page.fill("[data-testid=amount]", "10000")
                
                # 保存
                page.click("[data-testid=save-manual-btn]")
                page.wait_for_selector("[data-testid=save-success]")
            
            # 标记为异常并添加备注
            page.click("[data-testid=mark-exception-btn]")
            page.fill("[data-testid=exception-reason]", "发票模糊，人工核对")
            page.click("[data-testid=confirm-exception-btn]")
            
            # 继续生成凭证
            page.click("[data-testid=generate-voucher-btn]")
            
        finally:
            page.close()
    
    def test_audit_rejection_resubmission_flow(self, browser):
        """审核驳回重新提交流程"""
        page = browser.new_page()
        
        try:
            # 会计登录并提交审核
            page.goto("http://localhost:3000/login")
            page.fill("[data-testid=email]", "accountant@example.com")
            page.fill("[data-testid=password]", "TestPass123!")
            page.click("[data-testid=login-btn]")
            
            # 找到待提交审核的凭证
            page.click("[data-testid=nav-vouchers]")
            page.click("[data-testid=submit-audit-btn]:first-child")
            page.wait_for_selector("[data-testid=submit-success]")
            
            # 记录提交的凭证ID
            voucher_id = page.get_attribute("[data-testid=voucher-item]:first-child", "data-voucher-id")
            
            # 切换审核员账号
            page.click("[data-testid=user-menu]")
            page.click("[data-testid=logout-btn]")
            
            page.goto("http://localhost:3000/login")
            page.fill("[data-testid=email]", "auditor@example.com")
            page.fill("[data-testid=password]", "TestPass123!")
            page.click("[data-testid=login-btn]")
            
            # 进入审核工作台
            page.click("[data-testid=nav-audit]")
            page.wait_for_selector(f"[data-voucher-id='{voucher_id}']")
            
            # 驳回凭证
            page.click(f"[data-voucher-id='{voucher_id}'] [data-testid=reject-btn]")
            page.fill("[data-testid=reject-reason]", "金额与合同不符，请核对")
            page.click("[data-testid=confirm-reject-btn]")
            page.wait_for_selector("[data-testid=reject-success]")
            
            # 切换回会计账号
            page.click("[data-testid=user-menu]")
            page.click("[data-testid=logout-btn]")
            
            page.goto("http://localhost:3000/login")
            page.fill("[data-testid=email]", "accountant@example.com")
            page.fill("[data-testid=password]", "TestPass123!")
            page.click("[data-testid=login-btn]")
            
            # 查看被驳回的凭证
            page.click("[data-testid=nav-vouchers]")
            page.click("[data-testid=filter-rejected]")
            page.click(f"[data-voucher-id='{voucher_id}'] [data-testid=edit-btn]")
            
            # 修改金额
            page.fill("[data-testid=amount-input]", "9000")
            page.click("[data-testid=save-btn]")
            
            # 重新提交审核
            page.click("[data-testid=resubmit-btn]")
            page.wait_for_selector("[data-testid=resubmit-success]")
            
            # 切换审核员再次审核通过
            page.click("[data-testid=user-menu]")
            page.click("[data-testid=logout-btn]")
            
            page.goto("http://localhost:3000/login")
            page.fill("[data-testid=email]", "auditor@example.com")
            page.fill("[data-testid=password]", "TestPass123!")
            page.click("[data-testid=login-btn]")
            
            page.click("[data-testid=nav-audit]")
            page.click(f"[data-voucher-id='{voucher_id}'] [data-testid=approve-btn]")
            page.wait_for_selector("[data-testid=approve-success]")
            
        finally:
            page.close()
```

## 四、测试环境要求

| 组件 | 版本要求 |
|------|----------|
| 后端API | 本地启动或测试环境 |
| 前端应用 | 本地3000端口 |
| 数据库 | PostgreSQL 14+ |
| 文件存储 | MinIO |
| 浏览器 | Chromium |

## 五、验收标准
- [ ] 标准业务流程<5分钟完成
- [ ] 批量处理20张发票<10分钟
- [ ] 所有场景测试通过
- [ ] 截图/录像存档
- [ ] 测试报告包含性能数据

================================================================================
                              提交要求
================================================================================

1. 提交 tests/e2e/ 目录
2. 提交测试执行录像（如有）
3. 提交E2E测试报告
