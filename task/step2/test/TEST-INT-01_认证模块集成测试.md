# 任务编号：TEST-INT-01
# 任务名称：用户认证模块集成测试
# 负责人：测试工程师
# 工期：2天
# 依赖：INF-06 认证模块, INF-07 权限控制

================================================================================
                            任务详细说明书
================================================================================

## 一、任务目标
验证用户认证和权限控制模块的完整功能链路，确保登录、注册、Token刷新、权限校验等功能正常。

## 二、测试范围

### 2.1 登录功能测试
- [ ] 正常邮箱+密码登录
- [ ] 手机号+验证码登录
- [ ] 错误密码提示（剩余尝试次数）
- [ ] 账户锁定机制（连续5次错误）
- [ ] Token生成与返回格式

### 2.2 注册功能测试
- [ ] 新用户注册完整流程
- [ ] 邮箱验证码发送与校验
- [ ] 手机号重复性检查
- [ ] 企业信息绑定

### 2.3 Token管理测试
- [ ] Access Token有效性验证
- [ ] Refresh Token刷新机制
- [ ] Token过期处理（401返回）
- [ ] 多设备登录处理

### 2.4 权限控制测试
- [ ] 角色权限中间件拦截
- [ ] 无权限访问返回403
- [ ] 数据权限隔离（企业间隔离）
- [ ] API权限粒度控制

## 三、测试用例示例

```python
# tests/integration/test_auth.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAuthFlow:
    """认证流程集成测试"""
    
    def test_login_success(self):
        """正常登录流程"""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
    def test_login_wrong_password(self):
        """错误密码登录"""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPass123!"
        })
        assert response.status_code == 401
        assert "剩余尝试次数" in response.json()["detail"]
        
    def test_login_account_locked(self):
        """账户锁定测试"""
        # 连续5次错误登录
        for i in range(5):
            response = client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "WrongPass123!"
            })
        
        # 第6次应被锁定
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass123!"
        })
        assert response.status_code == 403
        assert "账户已锁定" in response.json()["detail"]
    
    def test_token_refresh(self):
        """Token刷新测试"""
        # 先登录获取token
        login_resp = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass123!"
        })
        refresh_token = login_resp.json()["refresh_token"]
        
        # 刷新token
        response = client.post("/api/v1/auth/refresh", headers={
            "Authorization": f"Bearer {refresh_token}"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        
    def test_access_protected_api(self):
        """访问受保护API"""
        # 无Token访问
        response = client.get("/api/v1/invoices")
        assert response.status_code == 401
        
        # 有Token访问
        login_resp = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass123!"
        })
        access_token = login_resp.json()["access_token"]
        
        response = client.get("/api/v1/invoices", headers={
            "Authorization": f"Bearer {access_token}"
        })
        assert response.status_code == 200
```

## 四、测试数据准备

```sql
-- 测试用户数据
INSERT INTO users (id, email, phone, password_hash, status, tenant_id) VALUES 
('test-user-1', 'test@example.com', '13800138000', '$2b$12$...', 'active', 'tenant-1'),
('test-user-2', 'locked@example.com', '13800138001', '$2b$12$...', 'locked', 'tenant-1');

-- 测试角色权限
INSERT INTO roles (id, name, permissions) VALUES 
('role-1', 'admin', '["invoice:*", "voucher:*", "audit:*"]'),
('role-2', 'accountant', '["invoice:read", "invoice:create", "voucher:read"]');
```

## 五、验收标准
- [ ] 所有登录场景测试通过
- [ ] Token生命周期管理正确
- [ ] 权限拦截逻辑符合预期
- [ ] 测试覆盖率>80%
- [ ] 边界情况（并发、重放攻击）已测试

================================================================================
                              提交要求
================================================================================

1. 提交 tests/integration/test_auth.py
2. 提交 tests/fixtures/auth_fixtures.py （测试数据）
3. 提交测试报告截图
