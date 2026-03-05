# 任务编号：TEST-INT-02
# 任务名称：票据处理流程集成测试
# 负责人：测试工程师
# 工期：3天
# 依赖：BA-01~BA-12 票据Agent全部任务

================================================================================
                            任务详细说明书
================================================================================

## 一、任务目标
验证票据从上传、OCR识别、解析、到数据存储的完整处理流程，确保各模块协同工作正常。

## 二、测试范围

### 2.1 票据上传测试
- [ ] 单文件上传（PNG/JPG/PDF）
- [ ] 批量上传（最多20张）
- [ ] 大文件限制（>10MB拒绝）
- [ ] 文件类型校验（非图片拒绝）
- [ ] 存储路径正确性

### 2.2 OCR识别流程测试
- [ ] 增值税专票识别
- [ ] 增值税普票识别
- [ ] 电子发票识别
- [ ] 识别失败重试机制
- [ ] OCR结果缓存

### 2.3 票据解析测试
- [ ] 字段提取完整性
- [ ] 日期格式标准化
- [ ] 金额计算准确性
- [ ] 税率税额校验
- [ ] 发票代码有效性校验

### 2.4 银行流水匹配测试
- [ ] 自动匹配算法准确性
- [ ] 手动匹配功能
- [ ] 匹配结果持久化
- [ ] 匹配异常处理

### 2.5 异常检测测试
- [ ] 重复发票检测
- [ ] 发票真伪校验
- [ ] 金额异常标记
- [ ] 供应商异常标记

## 三、测试用例示例

```python
# tests/integration/test_invoice_flow.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
import io

client = TestClient(app)

class TestInvoiceFlow:
    """票据处理全流程测试"""
    
    def test_upload_single_invoice(self, auth_headers):
        """单张发票上传"""
        # 准备测试文件
        with open("tests/fixtures/vat_invoice_sample.jpg", "rb") as f:
            response = client.post(
                "/api/v1/invoices/upload",
                headers=auth_headers,
                files={"file": ("invoice.jpg", f, "image/jpeg")}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["status"] == "pending"
        assert data["file_url"] is not None
    
    def test_upload_invalid_file_type(self, auth_headers):
        """非法文件类型上传"""
        response = client.post(
            "/api/v1/invoices/upload",
            headers=auth_headers,
            files={"file": ("test.txt", io.BytesIO(b"invalid"), "text/plain")}
        )
        
        assert response.status_code == 400
        assert "不支持的文件类型" in response.json()["detail"]
    
    def test_upload_oversized_file(self, auth_headers):
        """超大文件上传"""
        large_file = io.BytesIO(b"x" * (11 * 1024 * 1024))  # 11MB
        response = client.post(
            "/api/v1/invoices/upload",
            headers=auth_headers,
            files={"file": ("large.jpg", large_file, "image/jpeg")}
        )
        
        assert response.status_code == 413
        assert "文件大小超过限制" in response.json()["detail"]
    
    def test_invoice_processing_pipeline(self, auth_headers):
        """完整处理流水线测试"""
        # 1. 上传发票
        with open("tests/fixtures/vat_invoice_sample.jpg", "rb") as f:
            upload_resp = client.post(
                "/api/v1/invoices/upload",
                headers=auth_headers,
                files={"file": ("invoice.jpg", f, "image/jpeg")}
            )
        invoice_id = upload_resp.json()["id"]
        
        # 2. 触发OCR识别（同步等待或轮询）
        import time
        max_wait = 30
        elapsed = 0
        
        while elapsed < max_wait:
            status_resp = client.get(
                f"/api/v1/invoices/{invoice_id}",
                headers=auth_headers
            )
            status = status_resp.json()["status"]
            
            if status == "completed":
                break
            elif status == "failed":
                pytest.fail("发票处理失败")
            
            time.sleep(1)
            elapsed += 1
        
        # 3. 验证解析结果
        detail_resp = client.get(
            f"/api/v1/invoices/{invoice_id}",
            headers=auth_headers
        )
        invoice = detail_resp.json()
        
        assert invoice["invoice_type"] in ["vat_special", "vat_normal"]
        assert invoice["invoice_code"] is not None
        assert invoice["invoice_number"] is not None
        assert float(invoice["amount"]) > 0
        assert invoice["seller_name"] is not None
        assert invoice["buyer_name"] is not None
    
    def test_duplicate_invoice_detection(self, auth_headers):
        """重复发票检测"""
        # 第一次上传
        with open("tests/fixtures/vat_invoice_sample.jpg", "rb") as f:
            client.post(
                "/api/v1/invoices/upload",
                headers=auth_headers,
                files={"file": ("invoice.jpg", f, "image/jpeg")}
            )
        
        # 第二次上传相同发票
        with open("tests/fixtures/vat_invoice_sample.jpg", "rb") as f:
            response = client.post(
                "/api/v1/invoices/upload",
                headers=auth_headers,
                files={"file": ("invoice2.jpg", f, "image/jpeg")}
            )
        
        # 应该被标记为重复或警告
        assert response.status_code in [201, 409]
        if response.status_code == 201:
            assert response.json().get("is_duplicate") == True
    
    def test_bank_statement_matching(self, auth_headers):
        """银行流水匹配测试"""
        # 创建已识别的发票
        invoice_id = self._create_test_invoice(auth_headers)
        
        # 上传对应的银行流水
        with open("tests/fixtures/bank_statement_sample.csv", "rb") as f:
            response = client.post(
                "/api/v1/bank-statements/upload",
                headers=auth_headers,
                files={"file": ("statement.csv", f, "text/csv")}
            )
        
        statement_id = response.json()["id"]
        
        # 执行匹配
        match_resp = client.post(
            "/api/v1/invoices/auto-match",
            headers=auth_headers,
            json={"invoice_ids": [invoice_id]}
        )
        
        assert match_resp.status_code == 200
        matches = match_resp.json()["matches"]
        assert len(matches) > 0
        assert matches[0]["confidence"] > 0.8
```

## 四、测试数据准备

### 4.1 测试发票图片
- tests/fixtures/vat_invoice_sample.jpg（增值税专票）
- tests/fixtures/vat_normal_sample.jpg（增值税普票）
- tests/fixtures/e_invoice_sample.pdf（电子发票）
- tests/fixtures/invalid_format.txt（非法格式）

### 4.2 测试银行流水
```csv
transaction_date,amount,counterparty,description
2024-03-15,11300.00,供应商A,货款支付
2024-03-16,5000.00,供应商B,服务费
```

## 五、验收标准
- [ ] 上传功能支持所有指定格式
- [ ] OCR识别准确率>95%
- [ ] 解析结果字段完整
- [ ] 异常检测准确标记
- [ ] 流水线执行时间<10秒/张
- [ ] 测试覆盖率>75%

================================================================================
                              提交要求
================================================================================

1. 提交 tests/integration/test_invoice_flow.py
2. 提交 tests/fixtures/ 下的测试资源文件
3. 提交性能测试报告
