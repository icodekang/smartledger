# 任务编号：TEST-E2E-02
# 任务名称：前端功能测试
# 负责人：测试工程师
# 工期：2天
# 依赖：FE-01, FE-08 前端开发任务

================================================================================
                            任务详细说明书
================================================================================

## 一、任务目标
验证前端页面的功能完整性、交互逻辑和UI显示正确性。

## 二、测试范围

### 2.1 登录页面测试
- [ ] 页面元素渲染
- [ ] 表单验证（必填、格式）
- [ ] 登录成功跳转
- [ ] 登录失败提示
- [ ] 记住密码功能
- [ ] 密码可见性切换

### 2.2 审核工作台测试
- [ ] 待办列表展示
- [ ] 审核详情弹窗
- [ ] 通过/驳回操作
- [ ] 批量操作
- [ ] 筛选与搜索
- [ ] 分页功能

### 2.3 通用UI测试
- [ ] 响应式布局
- [ ] 浏览器兼容性
- [ ] 加载状态
- [ ] 空状态
- [ ] 错误提示

## 三、测试用例示例

```python
# tests/e2e/test_frontend.py

import pytest
from playwright.sync_api import sync_playwright

class TestFrontend:
    """前端功能测试"""
    
    @pytest.fixture(scope="class")
    def browser(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            yield browser
            browser.close()
    
    def test_login_page_elements(self, browser):
        """登录页面元素检查"""
        page = browser.new_page()
        page.goto("http://localhost:3000/login")
        
        # 检查必要元素存在
        assert page.is_visible("[data-testid=login-form]")
        assert page.is_visible("[data-testid=email-input]")
        assert page.is_visible("[data-testid=password-input]")
        assert page.is_visible("[data-testid=login-button]")
        assert page.is_visible("[data-testid=remember-me]")
        
        page.close()
    
    def test_login_form_validation(self, browser):
        """登录表单验证"""
        page = browser.new_page()
        page.goto("http://localhost:3000/login")
        
        # 空表单提交
        page.click("[data-testid=login-button]")
        assert page.is_visible("text=请输入邮箱")
        
        # 无效邮箱格式
        page.fill("[data-testid=email-input]", "invalid-email")
        page.fill("[data-testid=password-input]", "password123")
        page.click("[data-testid=login-button]")
        assert page.is_visible("text=邮箱格式不正确")
        
        # 密码太短
        page.fill("[data-testid=email-input]", "test@example.com")
        page.fill("[data-testid=password-input]", "123")
        page.click("[data-testid=login-button]")
        assert page.is_visible("text=密码长度不能少于6位")
        
        page.close()
    
    def test_audit_workbench_display(self, browser):
        """审核工作台展示"""
        page = browser.new_page()
        
        # 登录
        page.goto("http://localhost:3000/login")
        page.fill("[data-testid=email-input]", "auditor@example.com")
        page.fill("[data-testid=password-input]", "password123")
        page.click("[data-testid=login-button]")
        page.wait_for_url("http://localhost:3000/dashboard")
        
        # 进入审核工作台
        page.click("[data-testid=nav-audit]")
        
        # 检查工作台元素
        assert page.is_visible("[data-testid=audit-workbench]")
        assert page.is_visible("[data-testid=pending-tab]")
        assert page.is_visible("[data-testid=completed-tab]")
        assert page.is_visible("[data-testid=audit-list]")
        
        page.close()
    
    def test_audit_approve_action(self, browser):
        """审核通过操作"""
        page = browser.new_page()
        
        # 登录并进入审核页面
        page.goto("http://localhost:3000/login")
        page.fill("[data-testid=email-input]", "auditor@example.com")
        page.fill("[data-testid=password-input]", "password123")
        page.click("[data-testid=login-button]")
        page.click("[data-testid=nav-audit]")
        
        # 点击第一条待审核
        page.click("[data-testid=audit-item]:first-child [data-testid=view-btn]")
        
        # 查看详情弹窗
        assert page.is_visible("[data-testid=audit-detail-modal]")
        
        # 点击通过
        page.click("[data-testid=approve-btn]")
        
        # 输入审核意见
        page.fill("[data-testid=comment-input]", "审核通过")
        page.click("[data-testid=confirm-approve-btn]")
        
        # 验证成功提示
        assert page.is_visible("text=审核成功")
        
        page.close()
    
    def test_responsive_layout(self, browser):
        """响应式布局测试"""
        viewports = [
            {"width": 1920, "height": 1080},  # Desktop
            {"width": 1366, "height": 768},   # Laptop
            {"width": 768, "height": 1024},   # Tablet
            {"width": 375, "height": 667},    # Mobile
        ]
        
        for viewport in viewports:
            page = browser.new_page(viewport=viewport)
            page.goto("http://localhost:3000/login")
            
            # 检查关键元素可见
            assert page.is_visible("[data-testid=login-form]")
            
            page.close()
```

## 四、验收标准
- [ ] 所有页面元素渲染正确
- [ ] 表单验证100%生效
- [ ] 交互操作反馈及时
- [ ] 响应式布局适配正常
- [ ] 无控制台报错

================================================================================
                              提交要求
================================================================================

1. 提交 tests/e2e/test_frontend.py
2. 提交浏览器兼容性报告
