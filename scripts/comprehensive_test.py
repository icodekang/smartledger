#!/usr/bin/env python3
"""
SmartLedger 完整测试脚本
创建测试数据后运行全面测试
"""
import requests
import json
import time
from datetime import datetime, date, timedelta

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

class ComprehensiveTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.headers = {}
        self.test_data = {
            "customers": [],
            "contracts": [],
            "invoices": [],
            "vouchers": [],
            "bank_accounts": [],
            "bank_flows": []
        }
        
    def login(self, username="testadmin", password="Test123456"):
        """登录获取 token"""
        try:
            resp = self.session.post(
                f"{API_URL}/auth/login",
                data={"username": username, "password": password}
            )
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data.get("data", {}).get("access_token")
                self.headers = {"Authorization": f"Bearer {self.access_token}"}
                print(f"✅ 登录成功")
                return True
            else:
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
    
    def create_test_data(self):
        """创建测试数据"""
        print("\n📋 创建测试数据...")
        
        # 创建客户
        for name in ["阿里巴巴", "腾讯科技", "字节跳动", "京东", "美团"]:
            try:
                idx = len(self.test_data["customers"])
                resp = self.post("/customers", json={
                    "name": f"{name}有限公司",
                    "tax_id": f"91330000MA2H4{idx:04d}X",
                    "contact": "测试联系人",
                    "phone": f"138{idx:08d}"
                })
                if resp.status_code in [200, 201]:
                    customer_id = resp.json().get("data", {}).get("id")
                    if customer_id:
                        self.test_data["customers"].append(customer_id)
                        print(f"  ✅ 客户: {name}")
            except Exception as e:
                print(f"  ⚠️ 客户创建失败: {e}")
        
        # 创建发票
        for i in range(5):
            try:
                resp = self.post("/invoices", json={
                    "bill_type": "invoice",
                    "amount": 1000 * (i + 1),
                    "total_amount": 1130 * (i + 1),
                    "tax_amount": 130 * (i + 1),
                    "seller_name": f"供应商{i+1}"
                })
                if resp.status_code in [200, 201]:
                    invoice_id = resp.json().get("data", {}).get("id")
                    if invoice_id:
                        self.test_data["invoices"].append(invoice_id)
                        print(f"  ✅ 发票: INV{i+1}")
            except Exception as e:
                print(f"  ⚠️ 发票创建失败: {e}")
        
        # 创建凭证
        for i in range(3):
            try:
                resp = self.post("/vouchers", json={
                    "voucher_date": "2024-01-31",
                    "amount": 10000 * (i + 1),
                    "voucher_type": "receipt",
                    "description": f"测试凭证{i+1}"
                })
                if resp.status_code in [200, 201]:
                    voucher_id = resp.json().get("data", {}).get("id")
                    if voucher_id:
                        self.test_data["vouchers"].append(voucher_id)
                        print(f"  ✅ 凭证: VZ{i+1}")
            except Exception as e:
                print(f"  ⚠️ 凭证创建失败: {e}")
        
        print(f"\n  测试数据: {len(self.test_data['customers'])} 客户, {len(self.test_data['invoices'])} 发票, {len(self.test_data['vouchers'])} 凭证")
        return self.test_data
    
    def test_api(self, name, method, endpoint, expected_code=200, data=None):
        """测试单个API"""
        try:
            if method == "GET":
                resp = self.get(endpoint)
            elif method == "POST":
                resp = self.post(endpoint, json=data)
            elif method == "PUT":
                resp = self.put(endpoint, json=data)
            elif method == "DELETE":
                resp = self.delete(endpoint)
            
            passed = resp.status_code == expected_code
            return {
                "name": name,
                "status": "PASS" if passed else "FAIL",
                "code": resp.status_code,
                "detail": f"期望: {expected_code}, 实际: {resp.status_code}" if not passed else "成功"
            }
        except Exception as e:
            return {
                "name": name,
                "status": "ERROR",
                "code": 0,
                "detail": str(e)
            }
    
    def run_comprehensive_tests(self):
        """运行全面测试"""
        print("\n" + "="*60)
        print("SmartLedger 全面API测试")
        print("="*60)
        
        all_tests = []
        
        # 1. 认证模块
        print("\n--- 认证模块 ---")
        tests = [
            ("登录", "POST", "/auth/login", 200, {"username": "testadmin", "password": "Test123456"}),
            ("当前用户", "GET", "/auth/me", 200),
            ("用户列表", "GET", "/users", 200),
        ]
        for name, method, endpoint, code, *args in tests:
            result = self.test_api(name, method, endpoint, code, args[0] if args else None)
            all_tests.append(result)
            print(f"  {name}: {'✅' if result['status']=='PASS' else '❌'} ({result['code']})")
        
        # 2. 客户管理
        print("\n--- 客户管理模块 ---")
        tests = [
            ("客户列表", "GET", "/customers", 200),
        ]
        for name, method, endpoint, code in tests:
            result = self.test_api(name, method, endpoint, code)
            all_tests.append(result)
            print(f"  {name}: {'✅' if result['status']=='PASS' else '❌'} ({result['code']})")
        
        # 3. 发票管理
        print("\n--- 发票管理模块 ---")
        tests = [
            ("发票列表", "GET", "/invoices", 200),
            ("发票详情", "GET", f"/invoices/{self.test_data['invoices'][0]}" if self.test_data['invoices'] else "/invoices", 200),
        ]
        for name, method, endpoint, code in tests:
            result = self.test_api(name, method, endpoint, code)
            all_tests.append(result)
            print(f"  {name}: {'✅' if result['status']=='PASS' else '❌'} ({result['code']})")
        
        # 4. 凭证管理
        print("\n--- 凭证管理模块 ---")
        tests = [
            ("凭证列表", "GET", "/vouchers", 200),
            ("会计科目", "GET", "/vouchers/accounts", 200),
            ("记账规则", "GET", "/vouchers/rules", 200),
        ]
        for name, method, endpoint, code in tests:
            result = self.test_api(name, method, endpoint, code)
            all_tests.append(result)
            print(f"  {name}: {'✅' if result['status']=='PASS' else '❌'} ({result['code']})")
        
        # 5. 银行流水
        print("\n--- 银行流水模块 ---")
        tests = [
            ("银行流水列表", "GET", "/bank-flows", 200),
            ("银行账户列表", "GET", "/bank-accounts", 200),
            ("支持的银行", "GET", "/bank-accounts/banks", 200),
        ]
        for name, method, endpoint, code in tests:
            result = self.test_api(name, method, endpoint, code)
            all_tests.append(result)
            print(f"  {name}: {'✅' if result['status']=='PASS' else '❌'} ({result['code']})")
        
        # 6. 合同管理
        print("\n--- 合同管理模块 ---")
        tests = [
            ("合同列表", "GET", "/contracts", 200),
        ]
        for name, method, endpoint, code in tests:
            result = self.test_api(name, method, endpoint, code)
            all_tests.append(result)
            print(f"  {name}: {'✅' if result['status']=='PASS' else '❌'} ({result['code']})")
        
        # 7. 审核管理
        print("\n--- 审核管理模块 ---")
        tests = [
            ("待审核任务", "GET", "/audit/pending", 200),
            ("审核统计", "GET", "/audit/statistics", 200),
            ("我的任务", "GET", "/audit/my-tasks", 200),
        ]
        for name, method, endpoint, code in tests:
            result = self.test_api(name, method, endpoint, code)
            all_tests.append(result)
            print(f"  {name}: {'✅' if result['status']=='PASS' else '❌'} ({result['code']})")
        
        # 8. 财务报表
        print("\n--- 财务报表模块 ---")
        tests = [
            ("费用明细表", "GET", "/reports/expense-detail", 200),
            ("应收账款报表", "GET", "/reports/receivable", 200),
            ("资产负债表", "GET", "/reports/balance-sheet", 200),
            ("利润表", "GET", "/reports/income-statement", 200),
            ("现金流量表", "GET", "/reports/cash-flow", 200),
            ("科目余额表", "GET", "/reports/account-balance", 200),
        ]
        for name, method, endpoint, code in tests:
            result = self.test_api(name, method, endpoint, code)
            all_tests.append(result)
            print(f"  {name}: {'✅' if result['status']=='PASS' else '❌'} ({result['code']})")
        
        # 9. 系统管理
        print("\n--- 系统管理模块 ---")
        tests = [
            ("角色列表", "GET", "/sys/roles", 200),
            ("操作日志", "GET", "/sys/logs", 200),
            ("系统配置", "GET", "/sys/config", 200),
            ("健康检查", "GET", "/health", 200),
        ]
        for name, method, endpoint, code in tests:
            result = self.test_api(name, method, endpoint, code)
            all_tests.append(result)
            print(f"  {name}: {'✅' if result['status']=='PASS' else '❌'} ({result['code']})")
        
        # 10. 高级功能
        print("\n--- 高级功能模块 ---")
        tests = [
            ("备份任务列表", "GET", "/operations/backup-tasks", 200),
            ("定时任务列表", "GET", "/operations/scheduled-tasks", 200),
            ("通知列表", "GET", "/notifications", 200),
            ("未读通知数", "GET", "/notifications/unread-count", 200),
            ("租户配置", "GET", "/tenant/config", 200),
        ]
        for name, method, endpoint, code in tests:
            result = self.test_api(name, method, endpoint, code)
            all_tests.append(result)
            print(f"  {name}: {'✅' if result['status']=='PASS' else '❌'} ({result['code']})")
        
        # 11. 移动端API
        print("\n--- 移动端API模块 ---")
        tests = [
            ("H5仪表盘", "GET", "/mobile/dashboard/h5", 200),
            ("小程序仪表盘", "GET", "/mobile/dashboard/weapp", 200),
            ("Portal仪表盘", "GET", "/mobile/dashboard/portal", 200),
        ]
        for name, method, endpoint, code in tests:
            result = self.test_api(name, method, endpoint, code)
            all_tests.append(result)
            print(f"  {name}: {'✅' if result['status']=='PASS' else '❌'} ({result['code']})")
        
        # 12. AI功能
        print("\n--- AI智能功能模块 ---")
        tests = [
            ("智能凭证生成", "POST", "/ai/smart-voucher/generate", 200, {"bill_id": self.test_data['invoices'][0] if self.test_data['invoices'] else "test"}),
            ("异常检测", "GET", "/ai/anomaly/detect", 200),
            ("智能洞察", "GET", "/ai/insights", 200),
            ("报表趋势分析", "GET", "/ai/reports/trend", 200),
        ]
        for name, method, endpoint, code, *args in tests:
            result = self.test_api(name, method, endpoint, code, args[0] if args else None)
            all_tests.append(result)
            print(f"  {name}: {'✅' if result['status']=='PASS' else '❌'} ({result['code']})")
        
        # 汇总
        print("\n" + "="*60)
        print("测试汇总")
        print("="*60)
        pass_count = sum(1 for t in all_tests if t['status'] == 'PASS')
        fail_count = sum(1 for t in all_tests if t['status'] == 'FAIL')
        error_count = sum(1 for t in all_tests if t['status'] == 'ERROR')
        
        print(f"总计: {len(all_tests)} 项")
        print(f"通过: {pass_count} 项")
        print(f"失败: {fail_count} 项")
        print(f"错误: {error_count} 项")
        print(f"通过率: {pass_count/len(all_tests)*100:.1f}%")
        
        # 保存结果
        result = {
            "test_time": datetime.now().isoformat(),
            "total": len(all_tests),
            "pass": pass_count,
            "fail": fail_count,
            "error": error_count,
            "pass_rate": f"{pass_count/len(all_tests)*100:.1f}%",
            "details": all_tests
        }
        
        with open("task/comprehensive_test_result.json", "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        return result

def main():
    tester = ComprehensiveTester()
    if not tester.login():
        print("❌ 登录失败，无法运行测试")
        return
    
    # 创建测试数据
    tester.create_test_data()
    
    # 运行测试
    result = tester.run_comprehensive_tests()
    
    print(f"\n✅ 测试完成，结果已保存到: task/comprehensive_test_result.json")

if __name__ == "__main__":
    main()
