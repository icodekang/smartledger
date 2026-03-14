#!/usr/bin/env python3
"""
SmartLedger 最终测试脚本
使用正确的端点和参数
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

class FinalTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.headers = {}
        self.test_data = {"customers": [], "invoices": []}
        
    def login(self):
        try:
            resp = self.session.post(f"{API_URL}/auth/login", data={"username": "testadmin", "password": "Test123456"})
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
    
    def put(self, endpoint, **kwargs):
        return self.session.put(f"{API_URL}{endpoint}", headers=self.headers, **kwargs)
    
    def delete(self, endpoint, **kwargs):
        return self.session.delete(f"{API_URL}{endpoint}", headers=self.headers, **kwargs)
    
    def raw_get(self, url):
        # Handle both absolute and relative URLs
        if url.startswith('http'):
            return self.session.get(url, headers=self.headers)
        return self.session.get(f"{BASE_URL}{url}", headers=self.headers)
    
    def test_api(self, name, method, endpoint, expected=200, data=None, raw=False):
        try:
            if raw:
                resp = self.raw_get(endpoint)
            elif method == "GET":
                resp = self.get(endpoint)
            elif method == "POST":
                resp = self.post(endpoint, json=data)
            elif method == "PUT":
                resp = self.put(endpoint, json=data)
            elif method == "DELETE":
                resp = self.delete(endpoint)
            
            status = "PASS" if resp.status_code == expected else "FAIL"
            return {"name": name, "status": status, "code": resp.status_code}
        except Exception as e:
            return {"name": name, "status": "ERROR", "code": 0, "detail": str(e)}
    
    def create_data(self):
        print("\n📋 创建测试数据...")
        for i, name in enumerate(["阿里", "腾讯", "字节", "京东", "美团"]):
            try:
                resp = self.post("/customers", json={"name": f"{name}公司", "tax_id": f"91{i:08d}X", "contact": "测试", "phone": f"138{i:08d}"})
                if resp.status_code in [200, 201]:
                    cid = resp.json().get("data", {}).get("id")
                    if cid: self.test_data["customers"].append(cid)
            except: pass
        
        for i in range(3):
            try:
                resp = self.post("/invoices", json={"bill_type": "invoice", "amount": 1000*(i+1), "total_amount": 1130*(i+1), "tax_amount": 130*(i+1)})
                if resp.status_code in [200, 201]:
                    iid = resp.json().get("data", {}).get("id")
                    if iid: self.test_data["invoices"].append(iid)
            except: pass
        
        print(f"  创建了 {len(self.test_data['customers'])} 客户, {len(self.test_data['invoices'])} 发票")
        return self.test_data
    
    def run_tests(self):
        print("\n" + "="*60)
        print("SmartLedger 最终测试")
        print("="*60)
        
        all_tests = []
        cid = self.test_data["customers"][0] if self.test_data["customers"] else "test"
        iid = self.test_data["invoices"][0] if self.test_data["invoices"] else "test"
        
        # 1. 认证
        print("\n--- 认证 ---")
        for name, ep in [("当前用户", "/auth/me"), ("用户列表", "/users")]:
            r = self.test_api(name, "GET", ep)
            all_tests.append(r)
            print(f"  {name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 2. 客户
        print("\n--- 客户 ---")
        r = self.test_api("客户列表", "GET", "/customers")
        all_tests.append(r)
        print(f"  客户列表: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 3. 发票
        print("\n--- 发票 ---")
        for name, ep in [("列表", "/invoices"), ("详情", f"/invoices/{iid}")] if iid != "test" else [("列表", "/invoices")]:
            r = self.test_api(f"发票{name}", "GET", ep)
            all_tests.append(r)
            print(f"  发票{name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 4. 凭证
        print("\n--- 凭证 ---")
        for name, ep in [("列表", "/vouchers"), ("科目", "/vouchers/accounts"), ("规则", "/vouchers/rules")]:
            r = self.test_api(f"凭证{name}", "GET", ep)
            all_tests.append(r)
            print(f"  凭证{name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 5. 银行
        print("\n--- 银行 ---")
        for name, ep in [("流水", "/bank-flows"), ("账户", "/bank-accounts"), ("银行列表", "/bank-accounts/banks")]:
            r = self.test_api(f"银行{name}", "GET", ep)
            all_tests.append(r)
            print(f"  银行{name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 6. 合同
        print("\n--- 合同 ---")
        r = self.test_api("合同列表", "GET", "/contracts")
        all_tests.append(r)
        print(f"  合同列表: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 7. 审核
        print("\n--- 审核 ---")
        for name, ep in [("待审核", "/audit/pending"), ("统计", "/audit/statistics"), ("我的任务", "/audit/my-tasks")]:
            r = self.test_api(f"审核{name}", "GET", ep)
            all_tests.append(r)
            print(f"  审核{name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 8. 报表
        print("\n--- 报表 ---")
        for name, ep in [
            ("费用", f"/reports/expense-detail?customer_id={cid}&period=2024-01"),
            ("应收", f"/reports/accounts-receivable?customer_id={cid}&period=2024-01"),
            ("资产", f"/reports/balance-sheet?customer_id={cid}&period=2024-01"),
            ("利润", f"/reports/income-statement?customer_id={cid}&period=2024-01"),
            ("现金", f"/reports/cash-flow?customer_id={cid}&period=2024-01"),
            ("科目", f"/reports/subject-balance?customer_id={cid}&period=2024-01"),
        ]:
            r = self.test_api(f"报表{name}", "GET", ep)
            all_tests.append(r)
            print(f"  报表{name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 9. 系统
        print("\n--- 系统 ---")
        for name, ep, raw in [("角色", "/sys/roles", False), ("日志", "/sys/logs", False), ("配置", "/sys/config", False), ("健康", "/health", True)]:
            r = self.test_api(f"系统{name}", "GET", ep, raw=raw)
            all_tests.append(r)
            print(f"  系统{name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 10. 运营
        print("\n--- 运营 ---")
        for name, ep in [("Webhook事件", "/operations/webhooks/events"), ("插件", "/operations/plugins"), ("Webhook列表", "/operations/webhooks")]:
            r = self.test_api(f"运营{name}", "GET", ep)
            all_tests.append(r)
            print(f"  运营{name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 11. 移动端
        print("\n--- 移动端 ---")
        for name, ep in [("H5", "/mobile/h5/dashboard"), ("小程序", "/mobile/miniapp/dashboard"), ("Portal", "/mobile/portal/dashboard")]:
            r = self.test_api(f"移动{name}", "GET", ep)
            all_tests.append(r)
            print(f"  移动{name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 12. AI
        print("\n--- AI ---")
        for name, ep, data, method in [
            ("智能分析", "/ai/smart-booking/analyze", {"bill_data": {"amount": 100}, "customer_id": cid}, "POST"),
            ("异常检测", "/ai/anomaly/detect", {"bill_data": {"amount": 1000, "tax_amount": 130, "total_amount": 1130}, "customer_id": cid}, "POST"),
            ("异常规则", "/ai/anomaly/rules", None, "GET"),
        ]:
            r = self.test_api(f"AI{name}", method, ep, data=data)
            all_tests.append(r)
            print(f"  AI{name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 13. 税务
        print("\n--- 税务 ---")
        for name, ep in [("地区", "/tax/areas"), ("认证", "/tax/auths")]:
            r = self.test_api(f"税务{name}", "GET", ep)
            all_tests.append(r)
            print(f"  税务{name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 14. 安全
        print("\n--- 安全 ---")
        for name, ep in [("合规", "/security/compliance-status"), ("审计", "/security/audit-logs")]:
            r = self.test_api(f"安全{name}", "GET", ep)
            all_tests.append(r)
            print(f"  安全{name}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 汇总
        print("\n" + "="*60)
        passed = sum(1 for t in all_tests if t['status'] == 'PASS')
        failed = sum(1 for t in all_tests if t['status'] == 'FAIL')
        total = len(all_tests)
        rate = passed/total*100
        
        print(f"总计: {total} 项 | 通过: {passed} | 失败: {failed}")
        print(f"通过率: {rate:.1f}%")
        
        result = {"test_time": datetime.now().isoformat(), "total": total, "pass": passed, "fail": failed, "pass_rate": f"{rate:.1f}%", "details": all_tests}
        with open("task/final_test_result.json", "w") as f:
            json.dump(result, f, indent=2)
        
        return result

if __name__ == "__main__":
    t = FinalTester()
    if t.login():
        t.create_data()
        t.run_tests()
