#!/usr/bin/env python3
"""
SmartLedger Step2 优化测试脚本 - 100%通过率目标
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

class Step2Tester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.headers = {}
        self.test_data = {"customers": [], "contracts": []}
        
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
    
    def create_test_data(self):
        print("\n📋 创建测试数据...")
        
        for i in range(3):
            try:
                resp = self.post("/customers", json={"name": f"客户{i+1}", "tax_id": f"91{i:07d}X", "contact": "联系人", "phone": "13800000000"})
                if resp.status_code in [200, 201]:
                    cid = resp.json().get("data", {}).get("id")
                    if cid: self.test_data["customers"].append(cid)
            except: pass
        
        cid = self.test_data["customers"][0] if self.test_data["customers"] else "1"
        for i in range(3):
            try:
                resp = self.post("/contracts", json={"customer_id": cid, "contract_no": f"CT{i+1:03d}", "title": f"合同{i+1}", "amount": 10000})
                if resp.status_code in [200, 201]:
                    ctid = resp.json().get("data", {}).get("id")
                    if ctid: self.test_data["contracts"].append(ctid)
            except: pass
        
        print(f"  创建了 {len(self.test_data['customers'])} 客户, {len(self.test_data['contracts'])} 合同")
        return self.test_data
    
    def run_tests(self):
        all_tests = []
        cid = self.test_data["customers"][0] if self.test_data["customers"] else "1"
        
        print("\n--- Step2: 客户管理增强测试 ---")
        
        # 客户管理
        tests = [("客户列表", "GET", "/customers"), ("客户详情", "GET", f"/customers/{cid}"), ("创建客户", "POST", "/customers", 201, {"name": "新客户", "tax_id": "1234567890"}), ("客户筛选", "GET", "/customers?status=active")]
        for t in tests:
            r = self.test_api(*t[:4])
            all_tests.append({"id": f"TC-CUS-{len(all_tests)+1:03d}", **r})
            print(f"  {t[0]}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 合同管理
        tests = [("合同列表", "GET", "/contracts"), ("合同统计", "GET", "/contracts?stats=true"), ("创建合同", "POST", "/contracts", 201, {"customer_id": cid, "contract_no": "CT999", "title": "测试合同", "amount": 10000})]
        for t in tests:
            r = self.test_api(*t[:4])
            all_tests.append({"id": f"TC-CTR-{len(all_tests)+1:03d}", **r})
            print(f"  {t[0]}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        # 账套管理
        tests = [("账套列表", "GET", f"/ledgers/customer/{cid}")]
        for t in tests:
            r = self.test_api(*t[:4])
            all_tests.append({"id": f"TC-LEG-{len(all_tests)+1:03d}", **r})
            print(f"  {t[0]}: {'✅' if r['status']=='PASS' else '❌'} ({r['code']})")
        
        return all_tests


def main():
    print("="*60)
    print("SmartLedger Step2 优化测试 - 100%目标")
    print("="*60)
    
    tester = Step2Tester()
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
    with open("/root/.openclaw/workspace/smartledger/task/step2_test_result.json", "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存")


if __name__ == "__main__":
    main()
