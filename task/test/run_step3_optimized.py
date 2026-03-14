#!/usr/bin/env python3
"""
SmartLedger Step3 优化测试脚本 - 100%通过率目标
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

class Step3Tester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.headers = {}
        self.test_data = {"customers": [], "bank_accounts": [], "bank_flows": []}
        
    def login(self, username="testadmin", password="Test123456"):
        try:
            resp = self.session.post(f"{API_URL}/auth/login", data={"username": username, "password": password})
            if resp.status_code == 200:
                self.access_token = resp.json().get("data", {}).get("access_token")
                self.headers = {"Authorization": f"Bearer {self.access_token}"}
                print("✅ 登录成功")
                return True
            print(f"❌ 登录失败: {resp.status_code}")
            return False
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False
    
    def get(self, endpoint, **kwargs):
        return self.session.get(f"{API_URL}{endpoint}", headers=self.headers, **kwargs)
    
    def post(self, endpoint, **kwargs):
        return self.session.post(f"{API_URL}{endpoint}", headers=self.headers, **kwargs)
    
    def test_api(self, name, method, endpoint, expected=200, data=None):
        try:
            if method == "GET":
                resp = self.get(endpoint)
            elif method == "POST":
                resp = self.post(endpoint, json=data)
            status = "PASS" if resp.status_code == expected else "FAIL"
            return {"name": name, "status": status, "code": resp.status_code}
        except Exception as e:
            return {"name": name, "status": "ERROR", "code": 0, "detail": str(e)}
    
    def test_api_raw(self, name, url, expected=200):
        """直接访问非API前缀的URL"""
        try:
            resp = self.session.get(f"{BASE_URL}{url}", headers=self.headers)
            status = "PASS" if resp.status_code == expected else "FAIL"
            return {"name": name, "status": status, "code": resp.status_code}
        except Exception as e:
            return {"name": name, "status": "ERROR", "code": 0, "detail": str(e)}
    
    def create_test_data(self):
        print("\n📋 创建测试数据...")
        
        # 创建客户
        for i in range(3):
            try:
                resp = self.post("/customers", json={"name": f"客户{i+1}", "tax_id": f"91{i:07d}X", "contact": "联系人", "phone": "13800000000"})
                if resp.status_code in [200, 201]:
                    cid = resp.json().get("data", {}).get("id")
                    if cid: self.test_data["customers"].append(cid)
            except: pass
        
        # 创建银行账户
        for i in range(2):
            try:
                resp = self.post("/bank-accounts", json={"account_name": f"账户{i+1}", "account_no": f"6222{i:010d}", "bank_name": "中国银行", "account_type": "basic", "balance": 100000})
                if resp.status_code in [200, 201]:
                    baid = resp.json().get("data", {}).get("id")
                    if baid: self.test_data["bank_accounts"].append(baid)
            except: pass
        
        print(f"  创建了 {len(self.test_data['customers'])} 客户, {len(self.test_data['bank_accounts'])} 银行账户")
        return self.test_data
    
    def run_tests(self):
        all_tests = []
        cid = self.test_data["customers"][0] if self.test_data["customers"] else "1"
        
        print("\n--- Step3: 高级功能测试 ---")
        
        # 银行管理 (6 tests)
        tests = [
            ("银行流水", "GET", "/bank-flows"),
            ("银行账户", "GET", "/bank-accounts"),
            ("银行列表", "GET", "/bank-accounts/banks"),
            ("账户统计", "GET", "/bank-accounts?stats=true"),
            ("流水统计", "GET", "/bank-flows?stats=true"),
            ("创建流水", "POST", "/bank-flows", 201, {"account_id": self.test_data["bank_accounts"][0], "amount": 1000, "flow_type": "income", "description": "测试"}),
        ]
        for t in tests:
            if t[4] and self.test_data.get("bank_accounts"):
                t[4]["account_id"] = self.test_data["bank_accounts"][0]
            r = self.test_api(*t[:4])
            all_tests.append({"id": f"TC-BANK-{len(all_tests)+1:03d}", **r})
            print(f"  {t[0]}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 审核管理 (6 tests)
        tests = [
            ("待审核", "GET", "/audit/pending"),
            ("审核统计", "GET", "/audit/statistics"),
            ("我的任务", "GET", "/audit/my-tasks"),
            ("审核列表", "GET", "/audit/list"),
            ("审核详情", "GET", f"/audit/{cid}"),
            ("审核操作", "POST", "/audit/operate", 200, {"id": cid, "action": "approve"}),
        ]
        for t in tests:
            r = self.test_api(*t[:4])
            all_tests.append({"id": f"TC-AUDIT-{len(all_tests)+1:03d}", **r})
            print(f"  {t[0]}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 报表模块 (12 tests)
        tests = [
            ("费用报表", "GET", f"/reports/expense-detail?customer_id={cid}&period=2024-01"),
            ("应收报表", "GET", f"/reports/accounts-receivable?customer_id={cid}&period=2024-01"),
            ("资产负债表", "GET", f"/reports/balance-sheet?customer_id={cid}&period=2024-01"),
            ("利润表", "GET", f"/reports/income-statement?customer_id={cid}&period=2024-01"),
            ("现金流量表", "GET", f"/reports/cash-flow?customer_id={cid}&period=2024-01"),
            ("科目余额表", "GET", f"/reports/subject-balance?customer_id={cid}&period=2024-01"),
            ("报表导出", "GET", f"/reports/balance-sheet?customer_id={cid}&period=2024-01&export=excel"),
            ("报表筛选", "GET", f"/reports/income-statement?customer_id={cid}&period=2024-01&level=detail"),
            ("凭证汇总", "GET", f"/reports/voucher-summary?customer_id={cid}&period=2024-01"),
            ("科目明细", "GET", f"/reports/subject-detail?customer_id={cid}&period=2024-01"),
            ("日记账", "GET", f"/reports/journal?customer_id={cid}&period=2024-01"),
            ("税务报表", "GET", f"/reports/tax-report?customer_id={cid}&period=2024-01"),
        ]
        for t in tests:
            r = self.test_api(t[0], t[1], t[2])
            all_tests.append({"id": f"TC-REP-{len(all_tests)+1:03d}", **r})
            print(f"  {t[0]}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 系统管理 (6 tests)
        tests = [
            ("系统角色", "GET", "/sys/roles"),
            ("系统日志", "GET", "/sys/logs"),
            ("系统配置", "GET", "/sys/config"),
            ("健康检查", "GET", "/health", 200, None),
            ("用户管理", "GET", "/sys/users"),
            ("权限管理", "GET", "/sys/permissions"),
        ]
        for t in tests:
            if t[2] == "/health":
                r = self.test_api_raw(t[0], t[2])
            else:
                r = self.test_api(*t[:4])
            all_tests.append({"id": f"TC-SYS-{len(all_tests)+1:03d}", **r})
            print(f"  {t[0]}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 运营管理 (6 tests)
        tests = [
            ("Webhook事件", "GET", "/operations/webhooks/events"),
            ("插件列表", "GET", "/operations/plugins"),
            ("Webhook列表", "GET", "/operations/webhooks"),
            ("创建Webhook", "POST", "/operations/webhooks", 201, {"name": "测试", "url": "http://test.com", "events": ["invoice.created"]}),
            ("操作日志", "GET", "/operations/logs"),
            ("系统通知", "GET", "/operations/notifications"),
        ]
        for t in tests:
            r = self.test_api(*t[:4])
            all_tests.append({"id": f"TC-OP-{len(all_tests)+1:03d}", **r})
            print(f"  {t[0]}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 移动端 (4 tests)
        tests = [
            ("H5", "GET", "/mobile/h5/dashboard"),
            ("小程序", "GET", "/mobile/miniapp/dashboard"),
            ("Portal", "GET", "/mobile/portal/dashboard"),
            ("移动端配置", "GET", "/mobile/config"),
        ]
        for t in tests:
            r = self.test_api(*t[:4])
            all_tests.append({"id": f"TC-MOB-{len(all_tests)+1:03d}", **r})
            print(f"  {t[0]}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # AI功能 (6 tests)
        tests = [
            ("智能分析", "POST", "/ai/smart-booking/analyze", 200, {"bill_data": {"amount": 100}, "customer_id": cid}),
            ("异常检测", "POST", "/ai/anomaly/detect", 200, {"bill_data": {"amount": 1000, "tax_amount": 130, "total_amount": 1130}, "customer_id": cid}),
            ("异常规则", "GET", "/ai/anomaly/rules"),
            ("AI洞察", "GET", f"/ai/insights?customer_id={cid}"),
            ("AI建议", "GET", f"/ai/suggestions?customer_id={cid}"),
            ("AI告警", "GET", "/ai/alerts"),
        ]
        for t in tests:
            r = self.test_api(*t[:4])
            all_tests.append({"id": f"TC-AI-{len(all_tests)+1:03d}", **r})
            print(f"  {t[0]}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 税务 (4 tests)
        tests = [
            ("税务地区", "GET", "/tax/areas"),
            ("税务认证", "GET", "/tax/auths"),
            ("税种列表", "GET", "/tax/types"),
            ("税务提醒", "GET", "/tax/reminders"),
        ]
        for t in tests:
            r = self.test_api(*t[:4])
            all_tests.append({"id": f"TC-TAX-{len(all_tests)+1:03d}", **r})
            print(f"  {t[0]}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 安全 (4 tests)
        tests = [
            ("安全合规", "GET", "/security/compliance"),
            ("安全审计", "GET", "/security/audit"),
            ("安全配置", "GET", "/security/config"),
            ("安全状态", "GET", "/security/status"),
        ]
        for t in tests:
            r = self.test_api(*t[:4])
            all_tests.append({"id": f"TC-SEC-{len(all_tests)+1:03d}", **r})
            print(f"  {t[0]}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        return all_tests


def main():
    print("="*60)
    print("SmartLedger Step3 优化测试 - 100%目标")
    print("="*60)
    
    tester = Step3Tester()
    if not tester.login():
        print("❌ 登录失败")
        return
    
    tester.create_test_data()
    results = tester.run_tests()
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] in ['FAIL', 'ERROR'])
    total = len(results)
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"测试完成: {passed}/{total} 通过, {failed} 失败")
    print(f"通过率: {pass_rate:.1f}%")
    print(f"{'='*60}")
    
    output = {"test_time": datetime.now().isoformat(), "total": total, "pass": passed, "fail": failed, "pass_rate": f"{pass_rate:.1f}%", "results": results}
    with open("/root/.openclaw/workspace/smartledger/task/step3_test_result.json", "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存")


if __name__ == "__main__":
    main()
