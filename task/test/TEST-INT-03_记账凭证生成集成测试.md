# 任务编号：TEST-INT-03
# 任务名称：记账凭证生成集成测试
# 负责人：测试工程师
# 工期：3天
# 依赖：VA-01~VA-06 记账Agent全部任务

================================================================================
                            任务详细说明书
================================================================================

## 一、任务目标
验证从发票数据生成会计凭证的完整流程，包括科目推荐、借贷平衡校验、凭证预览和确认。

## 二、测试范围

### 2.1 科目推荐测试
- [ ] 费用类发票科目匹配
- [ ] 资产类发票科目匹配
- [ ] 成本类发票科目匹配
- [ ] 历史科目复用
- [ ] DeepSeek智能推荐

### 2.2 记账规则引擎测试
- [ ] 按发票类型匹配规则
- [ ] 按金额范围匹配规则
- [ ] 按供应商匹配规则
- [ ] 规则优先级执行
- [ ] 自定义规则生效

### 2.3 凭证生成测试
- [ ] 单张发票生成凭证
- [ ] 多张发票合并凭证
- [ ] 借贷分录准确性
- [ ] 辅助核算填充
- [ ] 摘要自动生成

### 2.4 借贷平衡校验测试
- [ ] 借贷金额相等
- [ ] 多币种折算平衡
- [ ] 增值税分录准确
- [ ] 误差容忍处理（0.01元）

### 2.5 凭证管理测试
- [ ] 凭证预览功能
- [ ] 凭证修改调整
- [ ] 凭证确认入账
- [ ] 凭证作废/删除
- [ ] 凭证编号连续性

## 三、测试用例示例

```python
# tests/integration/test_voucher_flow.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestVoucherFlow:
    """记账凭证全流程测试"""
    
    def test_generate_voucher_from_invoice(self, auth_headers, test_invoice):
        """从单张发票生成凭证"""
        response = client.post(
            "/api/v1/vouchers/generate",
            headers=auth_headers,
            json={
                "invoice_ids": [test_invoice["id"]],
                "voucher_date": "2024-03-15"
            }
        )
        
        assert response.status_code == 200
        voucher = response.json()
        
        # 验证凭证结构
        assert voucher["id"] is not None
        assert voucher["voucher_no"] is not None
        assert len(voucher["entries"]) >= 2  # 至少借贷两方
        assert voucher["total_debit"] == voucher["total_credit"]
        
        # 验证分录
        debit_entry = [e for e in voucher["entries"] if e["direction"] == "debit"][0]
        credit_entry = [e for e in voucher["entries"] if e["direction"] == "credit"][0]
        
        assert debit_entry["account_code"] is not None
        assert credit_entry["account_code"] is not None
        assert debit_entry["amount"] == credit_entry["amount"]
    
    def test_account_recommendation(self, auth_headers, test_invoice):
        """科目推荐功能测试"""
        response = client.post(
            "/api/v1/vouchers/recommend-accounts",
            headers=auth_headers,
            json={"invoice_id": test_invoice["id"]}
        )
        
        assert response.status_code == 200
        recommendations = response.json()
        
        # 验证推荐结构
        assert len(recommendations) > 0
        for rec in recommendations:
            assert rec["account_code"] is not None
            assert rec["account_name"] is not None
            assert 0 <= rec["confidence"] <= 1
            assert rec["reason"] is not None
        
        # 第一个推荐应该是置信度最高的
        assert recommendations[0]["confidence"] >= recommendations[-1]["confidence"]
    
    def test_voucher_debit_credit_balance(self, auth_headers):
        """借贷平衡校验"""
        # 创建测试发票（金额1000元，税额130元）
        test_invoice = {
            "id": "inv-test-001",
            "invoice_type": "vat_special",
            "amount": 1000.00,
            "tax_amount": 130.00,
            "total_amount": 1130.00,
            "seller_name": "测试供应商",
            "item_name": "办公用品"
        }
        
        response = client.post(
            "/api/v1/vouchers/generate",
            headers=auth_headers,
            json={
                "invoice_ids": [test_invoice["id"]],
                "voucher_date": "2024-03-15"
            }
        )
        
        voucher = response.json()
        entries = voucher["entries"]
        
        # 计算借贷总额
        total_debit = sum(e["amount"] for e in entries if e["direction"] == "debit")
        total_credit = sum(e["amount"] for e in entries if e["direction"] == "credit")
        
        assert abs(total_debit - total_credit) < 0.01  # 允许0.01元误差
        assert total_debit == 1130.00  # 价税合计
    
    def test_vat_entry_split(self, auth_headers):
        """增值税分录拆分测试"""
        response = client.post(
            "/api/v1/vouchers/generate",
            headers=auth_headers,
            json={
                "invoice_ids": ["vat-special-invoice"],
                "voucher_date": "2024-03-15",
                "split_vat": True  # 分离增值税
            }
        )
        
        voucher = response.json()
        entries = voucher["entries"]
        
        # 应该有3条分录：借费用、借进项税、贷应付/银行
        assert len(entries) == 3
        
        # 找出进项税分录
        vat_entry = [e for e in entries if "进项税额" in e.get("summary", "")]
        assert len(vat_entry) == 1
        assert vat_entry[0]["amount"] == 130.00  # 税额
        assert vat_entry[0]["account_code"].startswith("2221")  # 应交税费
    
    def test_batch_voucher_generation(self, auth_headers):
        """批量生成凭证测试"""
        invoice_ids = [f"inv-{i}" for i in range(1, 6)]
        
        response = client.post(
            "/api/v1/vouchers/generate-batch",
            headers=auth_headers,
            json={
                "invoice_ids": invoice_ids,
                "group_by": "date",  # 按日期分组
                "voucher_date": "2024-03-15"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["total"] == 5
        assert result["success"] == 5
        assert len(result["vouchers"]) > 0
        
        # 验证凭证编号连续
        voucher_nos = [v["voucher_no"] for v in result["vouchers"]]
        for i in range(1, len(voucher_nos)):
            prev_no = int(voucher_nos[i-1].split("-")[-1])
            curr_no = int(voucher_nos[i].split("-")[-1])
            assert curr_no == prev_no + 1
    
    def test_voucher_preview_and_confirm(self, auth_headers):
        """凭证预览与确认"""
        # 1. 生成预览凭证
        preview_resp = client.post(
            "/api/v1/vouchers/preview",
            headers=auth_headers,
            json={
                "invoice_ids": ["inv-test-001"],
                "voucher_date": "2024-03-15"
            }
        )
        
        assert preview_resp.status_code == 200
        preview = preview_resp.json()
        preview_id = preview["preview_id"]
        
        # 2. 修改分录（调整科目）
        preview["entries"][0]["account_code"] = "660201"  # 改为管理费用-办公费
        
        # 3. 确认凭证
        confirm_resp = client.post(
            f"/api/v1/vouchers/confirm/{preview_id}",
            headers=auth_headers,
            json=preview
        )
        
        assert confirm_resp.status_code == 200
        voucher = confirm_resp.json()
        assert voucher["status"] == "confirmed"
        assert voucher["confirmed_at"] is not None
        assert voucher["confirmed_by"] is not None
    
    def test_rule_engine_priority(self, auth_headers):
        """规则引擎优先级测试"""
        # 测试发票同时匹配多条规则时的优先级
        response = client.post(
            "/api/v1/vouchers/test-rules",
            headers=auth_headers,
            json={
                "invoice_type": "vat_special",
                "amount": 5000.00,
                "seller_name": "特定供应商A",
                "item_name": "电脑设备"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 验证应用了优先级最高的规则
        assert result["applied_rule"] is not None
        assert result["applied_rule"]["priority"] == max(
            r["priority"] for r in result["matched_rules"]
        )
```

## 四、测试数据准备

### 4.1 会计科目表
```json
{
  "accounts": [
    {"code": "1002", "name": "银行存款", "type": "asset"},
    {"code": "2202", "name": "应付账款", "type": "liability"},
    {"code": "222101", "name": "应交税费-进项税额", "type": "liability"},
    {"code": "660201", "name": "管理费用-办公费", "type": "expense"},
    {"code": "660202", "name": "管理费用-差旅费", "type": "expense"},
    {"code": "160101", "name": "固定资产-办公设备", "type": "asset"}
  ]
}
```

### 4.2 记账规则
```json
{
  "rules": [
    {
      "id": "rule-001",
      "name": "办公用品费用",
      "condition": "item_name contains '办公用品'",
      "debit_account": "660201",
      "credit_account": "2202",
      "priority": 10
    },
    {
      "id": "rule-002", 
      "name": "大额设备采购",
      "condition": "amount > 2000 and item_name contains '设备'",
      "debit_account": "160101",
      "credit_account": "2202",
      "priority": 20
    }
  ]
}
```

## 五、验收标准
- [ ] 科目推荐准确率>90%
- [ ] 凭证借贷100%平衡
- [ ] 增值税分录计算准确
- [ ] 规则引擎优先级正确
- [ ] 凭证编号连续无断号
- [ ] 测试覆盖率>80%

================================================================================
                              提交要求
================================================================================

1. 提交 tests/integration/test_voucher_flow.py
2. 提交 tests/fixtures/accounts.json
3. 提交测试用例执行报告
