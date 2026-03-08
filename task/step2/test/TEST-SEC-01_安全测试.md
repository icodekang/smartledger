# 任务编号：TEST-SEC-01
# 任务名称：安全测试
# 负责人：测试工程师
# 工期：2天
# 依赖：全部MVP开发任务完成

================================================================================
                            任务详细说明书
================================================================================

## 一、任务目标
识别系统中的安全漏洞，验证安全措施的有效性，确保数据安全和系统稳定。

## 二、测试范围

### 2.1 认证与授权测试
- [ ] 密码强度策略
- [ ] 暴力破解防护
- [ ] Token安全（签名、过期、刷新）
- [ ] 会话管理（并发登录、超时）
- [ ] 权限越界访问
- [ ] 水平越权（访问他人数据）
- [ ] 垂直越权（低权限访问高权限接口）

### 2.2 输入安全测试
- [ ] SQL注入
- [ ] XSS（反射型、存储型）
- [ ] 命令注入
- [ ] 路径遍历
- [ ] 文件上传安全
- [ ] 反序列化漏洞

### 2.3 API安全测试
- [ ] 未授权访问
- [ ] 参数篡改
- [ ] 重放攻击
- [ ] CSRF防护
- [ ] 敏感信息泄露
- [ ] API限流/防刷

### 2.4 数据安全测试
- [ ] 敏感数据加密存储
- [ ] 传输层加密（TLS）
- [ ] 日志脱敏
- [ ] 数据导出权限

## 三、测试用例示例

```python
# tests/security/test_security.py

import pytest
import jwt
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestSecurity:
    """安全测试套件"""
    
    # ========== SQL注入测试 ==========
    
    def test_sql_injection_in_search(self, auth_headers):
        """搜索功能SQL注入测试"""
        malicious_inputs = [
            "'; DROP TABLE invoices; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "1; DELETE FROM invoices WHERE '1'='1",
            "%' OR 1=1 --"
        ]
        
        for payload in malicious_inputs:
            response = client.get(
                f"/api/v1/invoices?search={payload}",
                headers=auth_headers
            )
            # 应该正常返回空结果或400错误，而不是500
            assert response.status_code in [200, 400]
            # 系统不应该崩溃
            assert response.status_code != 500
    
    def test_sql_injection_in_login(self):
        """登录SQL注入测试"""
        response = client.post("/api/v1/auth/login", json={
            "email": "admin' OR '1'='1",
            "password": "anything"
        })
        # 应该返回401，不应该登录成功
        assert response.status_code == 401
    
    # ========== XSS测试 ==========
    
    def test_xss_in_invoice_data(self, auth_headers):
        """发票数据XSS测试"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<body onload=alert('xss')>",
            "<iframe src='javascript:alert(1)'>"
        ]
        
        for payload in xss_payloads:
            # 创建包含XSS的数据
            response = client.post("/api/v1/invoices", headers=auth_headers, json={
                "invoice_type": "vat_normal",
                "amount": 1000,
                "seller_name": payload,
                "buyer_name": payload,
                "remark": payload
            })
            
            if response.status_code == 201:
                invoice_id = response.json()["id"]
                
                # 读取数据并验证XSS被转义
                get_response = client.get(
                    f"/api/v1/invoices/{invoice_id}",
                    headers=auth_headers
                )
                
                data = get_response.json()
                # 验证脚本标签被转义或过滤
                assert "<script>" not in data.get("seller_name", "")
                assert "<script>" not in data.get("buyer_name", "")
                assert "javascript:" not in data.get("remark", "")
    
    # ========== 认证安全测试 ==========
    
    def test_brute_force_protection(self):
        """暴力破解防护测试"""
        # 连续5次错误登录
        for i in range(5):
            response = client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": f"wrong_pass_{i}"
            })
            assert response.status_code == 401
        
        # 第6次尝试（应该被限制）
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "correct_password"
        })
        # 应该返回429或403（被限流或账户锁定）
        assert response.status_code in [403, 429]
    
    def test_token_expiration(self, auth_headers):
        """Token过期测试"""
        # 创建一个已过期token（手动设置过期时间）
        expired_token = jwt.encode(
            {"sub": "test-user", "exp": time.time() - 3600},
            "secret_key",
            algorithm="HS256"
        )
        
        response = client.get(
            "/api/v1/invoices",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower() or "无效" in response.json()["detail"]
    
    def test_token_tampering(self):
        """Token篡改测试"""
        # 创建一个有效token后篡改签名
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0In0.invalid_signature"
        
        response = client.get(
            "/api/v1/invoices",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
    
    # ========== 权限测试 ==========
    
    def test_horizontal_privilege_escalation(self, auth_headers_user_a):
        """水平越权测试"""
        # 用户A尝试访问用户B的发票
        response = client.get(
            "/api/v1/invoices/inv-owned-by-user-b",
            headers=auth_headers_user_a
        )
        assert response.status_code == 403
        assert "无权" in response.json()["detail"] or "Forbidden" in response.json()["detail"]
    
    def test_vertical_privilege_escalation(self, auth_headers_normal_user):
        """垂直越权测试"""
        # 普通用户尝试访问管理员接口
        response = client.get(
            "/api/v1/admin/users",
            headers=auth_headers_normal_user
        )
        assert response.status_code == 403
    
    def test_unauthorized_api_access(self):
        """未授权API访问测试"""
        protected_endpoints = [
            ("/api/v1/invoices", "GET"),
            ("/api/v1/vouchers", "GET"),
            ("/api/v1/audit/pending", "GET"),
            ("/api/v1/admin/statistics", "GET"),
        ]
        
        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint)
            
            assert response.status_code == 401
    
    # ========== 文件上传安全测试 ==========
    
    def test_upload_executable_file(self, auth_headers):
        """上传可执行文件测试"""
        import io
        
        # 尝试上传伪装成图片的可执行文件
        fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"MZ" + b"\x00" * 100)  # PE文件头
        
        response = client.post(
            "/api/v1/invoices/upload",
            headers=auth_headers,
            files={"file": ("malware.exe.png", fake_image, "image/png")}
        )
        
        # 应该被拒绝或安全处理
        assert response.status_code in [400, 415, 422]
    
    def test_upload_path_traversal(self, auth_headers):
        """路径遍历上传测试"""
        import io
        
        response = client.post(
            "/api/v1/invoices/upload",
            headers=auth_headers,
            files={"file": ("../../../etc/passwd.jpg", io.BytesIO(b"fake"), "image/jpeg")}
        )
        
        # 文件名应该被净化
        if response.status_code == 201:
            data = response.json()
            assert "../" not in data.get("file_url", "")
            assert "etc/passwd" not in data.get("file_url", "")
    
    # ========== 敏感信息泄露测试 ==========
    
    def test_sensitive_data_in_error_messages(self):
        """错误信息敏感数据泄露测试"""
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "test"
        })
        
        # 错误信息不应该暴露系统内部信息
        assert "database" not in response.text.lower()
        assert "sql" not in response.text.lower()
        assert "stack trace" not in response.text.lower()
        assert "password hash" not in response.text.lower()
    
    def test_api_response_data_leak(self, auth_headers):
        """API响应数据泄露测试"""
        response = client.get("/api/v1/invoices/inv-test-001", headers=auth_headers)
        
        data = response.json()
        
        # 不应该返回敏感字段
        assert "password" not in data
        assert "secret_key" not in data
        assert "internal_id" not in data
        assert "db_row_id" not in data
    
    # ========== CSRF测试 ==========
    
    def test_csrf_protection(self, auth_headers):
        """CSRF防护测试"""
        # 不带CSRF Token的请求应该被拒绝（如果启用了CSRF保护）
        response = client.post(
            "/api/v1/invoices",
            headers={**auth_headers, "X-CSRF-Token": ""},
            json={"invoice_type": "vat_normal", "amount": 1000}
        )
        
        # 如果系统实现了CSRF保护，应该返回403
        # 注意：基于JWT Token的API通常不需要CSRF保护
        # 这里只是演示测试思路
    
    # ========== 限流测试 ==========
    
    def test_rate_limiting(self):
        """API限流测试"""
        # 快速发送大量请求
        responses = []
        for i in range(100):
            response = client.get("/api/v1/invoices")
            responses.append(response.status_code)
        
        # 前面应该成功，后面应该被限流
        success_count = responses.count(200)
        rate_limited_count = responses.count(429)
        
        # 应该有一定比例被限流
        assert rate_limited_count > 0 or success_count < 100
```

## 四、安全测试工具清单

| 工具 | 用途 | 使用场景 |
|------|------|----------|
| OWASP ZAP | 自动化安全扫描 | 全站扫描 |
| sqlmap | SQL注入检测 | 表单参数测试 |
| Burp Suite | 手工渗透测试 | 复杂场景 |
| Postman | API安全测试 | 接口测试 |
| bandit | Python代码安全扫描 | 代码审查 |

## 五、验收标准
- [ ] SQL注入风险全部修复
- [ ] XSS漏洞全部修复
- [ ] 权限控制100%生效
- [ ] Token安全机制完善
- [ ] 敏感信息无泄露
- [ ] 暴力破解防护有效
- [ ] 安全测试报告完整

## 六、高危漏洞修复优先级

| 优先级 | 漏洞类型 | 修复时限 |
|--------|----------|----------|
| P0 | SQL注入、任意文件上传 | 24小时内 |
| P1 | XSS、权限越界 | 3天内 |
| P2 | 敏感信息泄露、CSRF | 1周内 |
| P3 | 配置不当、日志泄露 | 2周内 |

================================================================================
                              提交要求
================================================================================

1. 提交 tests/security/ 目录
2. 提交安全扫描报告
3. 提交漏洞修复清单
4. 提交安全加固建议
