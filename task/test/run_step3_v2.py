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
        self.test_data = {"customers": [], "bank_accounts": []}
        
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
    
    def get(self, endpoint):
        return self.session.get(f"{API_URL}{endpoint}", headers=self.headers)
    
    def post(self, endpoint, json_data):
        return self.session.post(f"{API_URL}{endpoint}", headers=self.headers, json=json_data)
    
    def test_get(self, name, endpoint):
        try:
            resp = self.get(endpoint)
            status = "PASS" if resp.status_code == 200 else "FAIL"
            return {"name": name, "status": status, "code": resp.status_code}
        except Exception as e:
            return {"name": name, "status": "ERROR", "code": 0, "detail": str(e)}
    
    def test_post(self, name, endpoint, json_data):
        try:
            resp = self.post(endpoint, json_data)
            status = "PASS" if resp.status_code in [200, 201] else "FAIL"
            return {"name": name, "status": status, "code": resp.status_code}
        except Exception as e:
            return {"name": name, "status": "ERROR", "code": 0, "detail": str(e)}
    
    def test_api_raw(self, name, url):
        try:
            resp = self.session.get(f"{BASE_URL}{url}", headers=self.headers)
            status = "PASS" if resp.status_code == 200 else "FAIL"
            return {"name": name, "status": status, "code": resp.status_code}
        except Exception as e:
            return {"name": name, "status": "ERROR", "code": 0, "detail": str(e)}
    
    def create_test_data(self):
        print("\n📋 创建测试数据...")
        
        for i in range(3):
            try:
                resp = self.post("/customers", {"name": f"客户{i+1}", "tax_id": f"91{i:07d}X", "contact": "联系人", "phone": "13800000000"})
                if resp.status_code in [200, 201]:
                    cid = resp.json().get("data", {}).get("id")
                    if cid: self.test_data["customers"].append(cid)
            except: pass
        
        for i in range(2):
            try:
                resp = self.post("/bank-accounts", {"account_name": f"账户{i+1}", "account_no": f"6222{i:010d}", "bank_name": "中国银行", "account_type": "basic", "balance": 100000})
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
        
        # 银行管理
        tests = [("/bank-flows", "银行流水"), ("/bank-accounts", "银行账户"), ("/bank-accounts/banks", "银行列表")]
        for endpoint, name in tests:
            r = self.test_get(name, endpoint)
            all_tests.append({"id": f"TC-BANK-{len(all_tests)+1:03d}", **r})
            print(f"  {name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 审核管理
        tests = [("/audit/pending", "待审核"), ("/audit/statistics", "审核统计"), ("/audit/my-tasks", "我的任务")]
        for endpoint, name in tests:
            r = self.test_get(name, endpoint)
            all_tests.append({"id": f"TC-AUDIT-{len(all_tests)+1:03d}", **r})
            print(f"  {name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 报表
        tests = [
            (f"/reports/expense-detail?customer_id={cid}&period=2024-01", "费用报表"),
            (f"/reports/accounts-receivable?customer_id={cid}&period=2024-01", "应收报表"),
            (f"/reports/balance-sheet?customer_id={cid}&period=2024-01", "资产负债表"),
            (f"/reports/income-statement?customer_id={cid}&period=2024-01", "利润表"),
            (f"/reports/cash-flow?customer_id={cid}&period=2024-01", "现金流量表"),
            (f"/reports/subject-balance?customer_id={cid}&period=2024-01", "科目余额表")
        ]
        for endpoint, name in tests:
            r = self.test_get(name, endpoint)
            all_tests.append({"id": f"TC-REP-{len(all_tests)+1:03d}", **r})
            print(f"  {name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 系统管理
        tests = [("/sys/roles", "系统角色"), ("/sys/logs", "系统日志"), ("/sys/config", "系统配置")]
        for endpoint, name in tests:
            r = self.test_get(name, endpoint)
            all_tests.append({"id": f"TC-SYS-{len(all_tests)+1:03d}", **r})
            print(f"  {name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 健康检查
        r = self.test_api_raw("健康检查", "/health")
        all_tests.append({"id": f"TC-SYS-{len(all_tests)+1:03d}", **r})
        print(f"  健康检查: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 运营管理
        tests = [("/operations/webhooks/events", "Webhook事件"), ("/operations/plugins", "插件列表"), ("/operations/webhooks", "Webhook列表")]
        for endpoint, name in tests:
            r = self.test_get(name, endpoint)
            all_tests.append({"id": f"TC-OP-{len(all_tests)+1:03d}", **r})
            print(f"  {name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 移动端
        tests = [("/mobile/h5/dashboard", "H5"), ("/mobile/miniapp/dashboard", "小程序"), ("/mobile/portal/dashboard", "Portal")]
        for endpoint, name in tests:
            r = self.test_get(name, endpoint)
            all_tests.append({"id": f"TC-MOB-{len(all_tests)+1:03d}", **r})
            print(f"  {name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # AI功能
        tests = [("/ai/anomaly/rules", "异常规则")]
        for endpoint, name in tests:
            r = self.test_get(name, endpoint)
            all_tests.append({"id": f"TC-AI-{len(all_tests)+1:03d}", **r})
            print(f"  {name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 税务
        tests = [("/tax/areas", "税务地区"), ("/tax/auths", "税务认证")]
        for endpoint, name in tests:
            r = self.test_get(name, endpoint)
            all_tests.append({"id": f"TC-TAX-{len(all_tests)+1:03d}", **r})
            print(f"  {name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 安全
        tests = [("/security/compliance-status", "安全合规"), ("/security/audit-logs", "安全审计"), ("/security/access-control", "访问控制")]
        for endpoint, name in tests:
            r = self.test_get(name, endpoint)
            all_tests.append({"id": f"TC-SEC-{len(all_tests)+1:03d}", **r})
            print(f"  {name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
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
