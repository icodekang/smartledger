# 任务编号：TEST-INT-04
# 任务名称：审核工作流集成测试
# 负责人：测试工程师
# 工期：3天
# 依赖：AUDIT-01~AUDIT-03 审核模块全部任务

================================================================================
                            任务详细说明书
================================================================================

## 一、任务目标
验证审核工作流的完整流转，包括任务分配、状态变更、权限控制和审核记录追溯。

## 二、测试范围

### 2.1 审核状态机测试
- [ ] 待审核 → 审核中 → 已通过
- [ ] 待审核 → 审核中 → 已驳回
- [ ] 已驳回 → 修改后 → 重新提交
- [ ] 状态转换权限校验
- [ ] 非法状态转换拦截

### 2.2 任务分配算法测试
- [ ] 轮询分配均匀性
- [ ] 负载均衡分配
- [ ] 指定审核人分配
- [ ] 自动分配与手动分配
- [ ] 审核人离线处理

### 2.3 审核权限测试
- [ ] 审核人只能查看分配给自己的任务
- [ ] 提交人不能审核自己的单据
- [ ] 多级审核权限控制
- [ ] 审核记录只读保护

### 2.4 审核操作测试
- [ ] 通过操作与备注
- [ ] 驳回操作与原因
- [ ] 转交他人审核
- [ ] 批量审核
- [ ] 审核超时提醒

### 2.5 审核工作台测试
- [ ] 待办列表实时更新
- [ ] 已办列表查询
- [ ] 审核统计面板
- [ ] 筛选与排序功能

## 三、测试用例示例

```python
# tests/integration/test_audit_flow.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAuditFlow:
    """审核工作流集成测试"""
    
    def test_complete_audit_approval(self, auth_headers_auditor):
        """完整审核通过流程"""
        # 1. 获取待审核任务列表
        pending_resp = client.get(
            "/api/v1/audit/pending",
            headers=auth_headers_auditor
        )
        assert pending_resp.status_code == 200
        pending_tasks = pending_resp.json()["tasks"]
        
        # 假设至少有一个待审核任务
        if len(pending_tasks) == 0:
            pytest.skip("No pending audit tasks")
        
        task = pending_tasks[0]
        task_id = task["id"]
        
        # 2. 开始审核（认领任务）
        claim_resp = client.post(
            f"/api/v1/audit/{task_id}/claim",
            headers=auth_headers_auditor
        )
        assert claim_resp.status_code == 200
        assert claim_resp.json()["status"] == "auditing"
        assert claim_resp.json()["auditor_id"] == auth_headers_auditor["user_id"]
        
        # 3. 提交审核结果（通过）
        approve_resp = client.post(
            f"/api/v1/audit/{task_id}/approve",
            headers=auth_headers_auditor,
            json={
                "comment": "发票信息完整，金额正确，予以通过",
                "attachments": []
            }
        )
        assert approve_resp.status_code == 200
        
        result = approve_resp.json()
        assert result["status"] == "approved"
        assert result["audit_log"]["action"] == "approve"
        assert result["audit_log"]["auditor_id"] == auth_headers_auditor["user_id"]
        
        # 4. 验证状态变更
        detail_resp = client.get(
            f"/api/v1/audit/{task_id}",
            headers=auth_headers_auditor
        )
        assert detail_resp.json()["status"] == "approved"
    
    def test_audit_rejection_flow(self, auth_headers_auditor):
        """审核驳回流程"""
        # 创建测试任务
        task_id = self._create_test_audit_task()
        
        # 1. 认领任务
        client.post(
            f"/api/v1/audit/{task_id}/claim",
            headers=auth_headers_auditor
        )
        
        # 2. 驳回
        reject_resp = client.post(
            f"/api/v1/audit/{task_id}/reject",
            headers=auth_headers_auditor,
            json={
                "reason": "发票金额与合同不符",
                "reject_type": "amount_mismatch",
                "suggestion": "请核对合同金额后重新提交"
            }
        )
        
        assert reject_resp.status_code == 200
        result = reject_resp.json()
        assert result["status"] == "rejected"
        assert result["reject_reason"] == "发票金额与合同不符"
        assert result["can_resubmit"] == True
    
    def test_task_assignment_distribution(self, admin_headers):
        """任务分配均匀性测试"""
        # 模拟多个审核员
        auditors = ["auditor-1", "auditor-2", "auditor-3"]
        
        # 创建多个测试任务
        task_ids = []
        for i in range(9):
            task_id = self._create_test_audit_task()
            task_ids.append(task_id)
        
        # 触发自动分配
        assign_resp = client.post(
            "/api/v1/audit/auto-assign",
            headers=admin_headers,
            json={"task_ids": task_ids, "strategy": "round_robin"}
        )
        
        assert assign_resp.status_code == 200
        assignments = assign_resp.json()["assignments"]
        
        # 验证轮询分配均匀（每人3个）
        auditor_counts = {}
        for assignment in assignments:
            auditor_id = assignment["auditor_id"]
            auditor_counts[auditor_id] = auditor_counts.get(auditor_id, 0) + 1
        
        for auditor in auditors:
            assert auditor_counts.get(auditor, 0) == 3
    
    def test_cannot_audit_own_submission(self, auth_headers):
        """提交人不能审核自己的单据"""
        # 1. 用户提交发票
        submit_resp = client.post(
            "/api/v1/invoices",
            headers=auth_headers,
            json={
                "invoice_type": "vat_special",
                "amount": 1000.00,
                "seller_name": "测试供应商"
            }
        )
        invoice_id = submit_resp.json()["id"]
        
        # 2. 触发审核流程
        audit_resp = client.post(
            "/api/v1/audit/submit",
            headers=auth_headers,
            json={"invoice_id": invoice_id}
        )
        task_id = audit_resp.json()["task_id"]
        
        # 3. 同一用户尝试审核（应该被拒绝）
        claim_resp = client.post(
            f"/api/v1/audit/{task_id}/claim",
            headers=auth_headers
        )
        
        assert claim_resp.status_code == 403
        assert "不能审核自己提交的单据" in claim_resp.json()["detail"]
    
    def test_audit_permission_isolation(self, auth_headers_auditor_a, auth_headers_auditor_b):
        """审核人只能查看自己的任务"""
        # 创建并分配给审核员A的任务
        task_id = self._create_test_audit_task(auditor_id="auditor-a")
        
        # 审核员B尝试查看
        detail_resp = client.get(
            f"/api/v1/audit/{task_id}",
            headers=auth_headers_auditor_b
        )
        
        assert detail_resp.status_code == 403
        assert "无权查看此审核任务" in detail_resp.json()["detail"]
        
        # 审核员A可以正常查看
        detail_resp_a = client.get(
            f"/api/v1/audit/{task_id}",
            headers=auth_headers_auditor_a
        )
        assert detail_resp_a.status_code == 200
    
    def test_invalid_status_transition(self, auth_headers_auditor):
        """非法状态转换测试"""
        # 创建已通过的任务
        task_id = self._create_test_audit_task(status="approved")
        
        # 尝试对已通过的进行驳回
        reject_resp = client.post(
            f"/api/v1/audit/{task_id}/reject",
            headers=auth_headers_auditor,
            json={"reason": "测试驳回"}
        )
        
        assert reject_resp.status_code == 400
        assert "当前状态不允许此操作" in reject_resp.json()["detail"]
    
    def test_batch_audit(self, auth_headers_auditor):
        """批量审核测试"""
        # 创建多个待审核任务
        task_ids = []
        for i in range(5):
            task_id = self._create_test_audit_task(status="pending")
            client.post(
                f"/api/v1/audit/{task_id}/claim",
                headers=auth_headers_auditor
            )
            task_ids.append(task_id)
        
        # 批量通过
        batch_resp = client.post(
            "/api/v1/audit/batch-approve",
            headers=auth_headers_auditor,
            json={
                "task_ids": task_ids,
                "comment": "批量审核通过"
            }
        )
        
        assert batch_resp.status_code == 200
        result = batch_resp.json()
        assert result["total"] == 5
        assert result["success"] == 5
        
        # 验证所有任务状态
        for task_id in task_ids:
            detail_resp = client.get(
                f"/api/v1/audit/{task_id}",
                headers=auth_headers_auditor
            )
            assert detail_resp.json()["status"] == "approved"
    
    def test_audit_workload_stats(self, auth_headers_manager):
        """审核工作量统计"""
        response = client.get(
            "/api/v1/audit/statistics",
            headers=auth_headers_manager,
            params={"start_date": "2024-03-01", "end_date": "2024-03-31"}
        )
        
        assert response.status_code == 200
        stats = response.json()
        
        # 验证统计结构
        assert "total_submitted" in stats
        assert "total_approved" in stats
        assert "total_rejected" in stats
        assert "average_audit_time" in stats
        assert "auditor_stats" in stats
        
        # 验证数据一致性
        assert stats["total_submitted"] == stats["total_approved"] + stats["total_rejected"] + stats["total_pending"]
        
        # 审核员统计
        for auditor_stat in stats["auditor_stats"]:
            assert auditor_stat["auditor_id"] is not None
            assert auditor_stat["completed_count"] >= 0
            assert auditor_stat["average_time"] >= 0
```

## 四、测试数据准备

### 4.1 审核员账号
```json
{
  "auditors": [
    {"id": "auditor-1", "name": "审核员A", "role": "auditor"},
    {"id": "auditor-2", "name": "审核员B", "role": "auditor"},
    {"id": "auditor-3", "name": "审核员C", "role": "auditor"},
    {"id": "audit-manager", "name": "审核主管", "role": "audit_manager"}
  ]
}
```

### 4.2 状态转换规则
```python
VALID_TRANSITIONS = {
    "pending": ["auditing", "cancelled"],
    "auditing": ["approved", "rejected", "transferred"],
    "rejected": ["pending"],  # 重新提交后
    "approved": [],  # 终态
    "cancelled": []  # 终态
}
```

## 五、验收标准
- [ ] 状态机转换100%正确
- [ ] 任务分配均匀性误差<10%
- [ ] 权限隔离严格生效
- [ ] 审核日志完整可追溯
- [ ] 批量审核性能<2秒/100条
- [ ] 测试覆盖率>80%

================================================================================
                              提交要求
================================================================================

1. 提交 tests/integration/test_audit_flow.py
2. 提交 tests/fixtures/audit_fixtures.py
3. 提交状态机测试报告
