# 任务编号：TEST-API-01
# 任务名称：API接口测试（票据管理模块）
# 负责人：测试工程师
# 工期：2天
# 依赖：BA-10, BA-11, BA-12 票据相关API

================================================================================
                            任务详细说明书
================================================================================

## 一、任务目标
验证票据管理模块所有API接口的功能正确性、参数校验、错误处理和响应格式。

## 二、测试范围

### 2.1 票据CRUD操作
- [ ] GET /api/v1/invoices - 列表查询
- [ ] GET /api/v1/invoices/{id} - 详情获取
- [ ] POST /api/v1/invoices - 手动创建
- [ ] PUT /api/v1/invoices/{id} - 更新
- [ ] DELETE /api/v1/invoices/{id} - 删除

### 2.2 票据上传API
- [ ] POST /api/v1/invoices/upload - 文件上传
- [ ] POST /api/v1/invoices/batch-upload - 批量上传
- [ ] 文件类型、大小校验
- [ ] 上传进度反馈

### 2.3 查询参数测试
- [ ] 分页参数（page, page_size）
- [ ] 排序参数（sort_by, sort_order）
- [ ] 筛选条件（status, date_range, amount_range）
- [ ] 关键词搜索
- [ ] 字段过滤（fields）

### 2.4 错误处理测试
- [ ] 404 Not Found
- [ ] 400 Bad Request（参数错误）
- [ ] 403 Forbidden（无权限）
- [ ] 422 Validation Error
- [ ] 500 Internal Error（服务端异常）

## 三、测试用例示例

```python
# tests/api/test_invoice_api.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestInvoiceAPI:
    """票据管理API测试"""
    
    # ========== 列表查询测试 ==========
    
    def test_list_invoices_pagination(self, auth_headers):
        """分页功能测试"""
        # 测试默认分页
        resp1 = client.get("/api/v1/invoices", headers=auth_headers)
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert "items" in data1
        assert "total" in data1
        assert "page" in data1
        assert "page_size" in data1
        
        # 测试自定义分页
        resp2 = client.get(
            "/api/v1/invoices?page=2&page_size=20",
            headers=auth_headers
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["page"] == 2
        assert data2["page_size"] == 20
    
    def test_list_invoices_filtering(self, auth_headers):
        """筛选功能测试"""
        # 按状态筛选
        resp = client.get(
            "/api/v1/invoices?status=completed",
            headers=auth_headers
        )
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "completed"
        
        # 按日期范围筛选
        resp = client.get(
            "/api/v1/invoices?start_date=2024-03-01&end_date=2024-03-31",
            headers=auth_headers
        )
        assert resp.status_code == 200
        
        # 按金额范围筛选
        resp = client.get(
            "/api/v1/invoices?min_amount=1000&max_amount=5000",
            headers=auth_headers
        )
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert 1000 <= float(item["amount"]) <= 5000
    
    def test_list_invoices_sorting(self, auth_headers):
        """排序功能测试"""
        # 按金额升序
        resp_asc = client.get(
            "/api/v1/invoices?sort_by=amount&sort_order=asc",
            headers=auth_headers
        )
        items_asc = resp_asc.json()["items"]
        for i in range(1, len(items_asc)):
            assert float(items_asc[i-1]["amount"]) <= float(items_asc[i]["amount"])
        
        # 按日期降序
        resp_desc = client.get(
            "/api/v1/invoices?sort_by=created_at&sort_order=desc",
            headers=auth_headers
        )
        assert resp_desc.status_code == 200
    
    def test_list_invoices_search(self, auth_headers):
        """搜索功能测试"""
        resp = client.get(
            "/api/v1/invoices?search=阿里巴巴",
            headers=auth_headers
        )
        assert resp.status_code == 200
        # 验证搜索结果包含关键词
        for item in resp.json()["items"]:
            match_found = (
                "阿里巴巴" in item.get("seller_name", "") or
                "阿里巴巴" in item.get("buyer_name", "")
            )
            assert match_found
    
    def test_list_invoices_field_filtering(self, auth_headers):
        """字段过滤测试"""
        resp = client.get(
            "/api/v1/invoices?fields=id,amount,status",
            headers=auth_headers
        )
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert "id" in item
            assert "amount" in item
            assert "status" in item
            assert "seller_name" not in item  # 未请求的字段不应返回
    
    # ========== 详情获取测试 ==========
    
    def test_get_invoice_detail_success(self, auth_headers):
        """获取发票详情成功"""
        resp = client.get(
            "/api/v1/invoices/inv-test-001",
            headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "inv-test-001"
        assert "invoice_type" in data
        assert "invoice_code" in data
        assert "invoice_number" in data
        assert "amount" in data
        assert "tax_amount" in data
        assert "seller_name" in data
        assert "buyer_name" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_get_invoice_not_found(self, auth_headers):
        """获取不存在的发票"""
        resp = client.get(
            "/api/v1/invoices/non-existent-id",
            headers=auth_headers
        )
        assert resp.status_code == 404
        assert "不存在" in resp.json()["detail"]
    
    # ========== 创建/更新测试 ==========
    
    def test_create_invoice_manual(self, auth_headers):
        """手动创建发票"""
        payload = {
            "invoice_type": "vat_normal",
            "invoice_code": "011001900111",
            "invoice_number": "12345678",
            "invoice_date": "2024-03-15",
            "amount": 5000.00,
            "tax_amount": 650.00,
            "seller_name": "测试供应商",
            "seller_tax_id": "91110000123456789X",
            "buyer_name": "测试购买方",
            "buyer_tax_id": "91110000987654321Y"
        }
        
        resp = client.post(
            "/api/v1/invoices",
            headers=auth_headers,
            json=payload
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] is not None
        assert data["status"] == "pending"
        assert data["amount"] == 5000.00
    
    def test_create_invoice_validation_error(self, auth_headers):
        """创建发票参数校验失败"""
        # 缺少必填字段
        resp = client.post(
            "/api/v1/invoices",
            headers=auth_headers,
            json={"invoice_type": "vat_normal"}  # 缺少其他必填项
        )
        assert resp.status_code == 422
        assert "amount" in str(resp.json())  # 应该提示缺少amount
    
    def test_update_invoice_success(self, auth_headers):
        """更新发票成功"""
        resp = client.put(
            "/api/v1/invoices/inv-test-001",
            headers=auth_headers,
            json={"amount": 6000.00, "remark": "金额修正"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["amount"] == 6000.00
        assert data["remark"] == "金额修正"
    
    def test_update_invoice_not_modifiable(self, auth_headers):
        """更新已确认的发票失败"""
        resp = client.put(
            "/api/v1/invoices/inv-confirmed-001",
            headers=auth_headers,
            json={"amount": 6000.00}
        )
        assert resp.status_code == 400
        assert "已确认" in resp.json()["detail"]
    
    # ========== 删除测试 ==========
    
    def test_delete_invoice_success(self, auth_headers):
        """删除发票成功"""
        resp = client.delete(
            "/api/v1/invoices/inv-deletable-001",
            headers=auth_headers
        )
        assert resp.status_code == 204
        
        # 验证已删除
        get_resp = client.get(
            "/api/v1/invoices/inv-deletable-001",
            headers=auth_headers
        )
        assert get_resp.status_code == 404
    
    def test_delete_invoice_with_voucher(self, auth_headers):
        """删除已生成凭证的发票失败"""
        resp = client.delete(
            "/api/v1/invoices/inv-with-voucher-001",
            headers=auth_headers
        )
        assert resp.status_code == 400
        assert "已生成凭证" in resp.json()["detail"]
    
    # ========== 批量操作测试 ==========
    
    def test_batch_delete_invoices(self, auth_headers):
        """批量删除发票"""
        resp = client.post(
            "/api/v1/invoices/batch-delete",
            headers=auth_headers,
            json={"ids": ["inv-001", "inv-002", "inv-003"]}
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["total"] == 3
        assert result["success"] >= 0
        assert result["failed"] >= 0
    
    def test_batch_update_status(self, auth_headers):
        """批量更新状态"""
        resp = client.post(
            "/api/v1/invoices/batch-update",
            headers=auth_headers,
            json={
                "ids": ["inv-001", "inv-002"],
                "updates": {"status": "archived"}
            }
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["updated"] == 2
```

## 四、API响应格式规范

```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {
    // 具体数据
  },
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

## 五、验收标准
- [ ] 所有API返回状态码正确
- [ ] 响应格式符合统一规范
- [ ] 参数校验100%覆盖
- [ ] 错误信息清晰可读
- [ ] 分页、筛选、排序功能正常
- [ ] 测试覆盖率>90%

================================================================================
                              提交要求
================================================================================

1. 提交 tests/api/test_invoice_api.py
2. 提交 API测试报告
