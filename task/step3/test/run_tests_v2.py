#!/usr/bin/env python3
"""
SmartLedger Step3 API 测试脚本 - 增强版
测试系统管理、财务报表和高级功能模块
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.headers = {}
        
    def login(self, username="testadmin", password="Test123456"):
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

def run_all_tests():
    tester = APITester()
    if not tester.login():
        return None
    
    all_results = {}
    
    # 客户管理测试
    results = {"name": "客户管理测试", "total": 2, "passed": 0, "failed": 0, "cases": []}
    try:
        resp = tester.get("/customers")
        if resp.status_code == 200:
            data = resp.json()
            results["cases"].append({"id": "TC-CUSTOMER-001", "name": "客户列表查询", "status": "PASS", "detail": f"获取到 {len(data.get('items', []))} 个客户"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-CUSTOMER-001", "name": "客户列表查询", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-CUSTOMER-001", "name": "客户列表查询", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    
    try:
        resp = tester.get("/customers?stats=true")
        if resp.status_code == 200:
            results["cases"].append({"id": "TC-CUSTOMER-002", "name": "客户统计", "status": "PASS", "detail": "客户统计查询成功"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-CUSTOMER-002", "name": "客户统计", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-CUSTOMER-002", "name": "客户统计", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    all_results["TEST-CUSTOMER"] = results
    
    # 合同管理测试
    results = {"name": "合同管理测试", "total": 2, "passed": 0, "failed": 0, "cases": []}
    try:
        resp = tester.get("/contracts")
        if resp.status_code == 200:
            data = resp.json()
            results["cases"].append({"id": "TC-CONTRACT-001", "name": "合同列表查询", "status": "PASS", "detail": f"获取到 {len(data.get('items', []))} 个合同"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-CONTRACT-001", "name": "合同列表查询", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-CONTRACT-001", "name": "合同列表查询", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    
    try:
        resp = tester.get("/contracts?customer_id=1&stats=true")
        if resp.status_code == 200:
            results["cases"].append({"id": "TC-CONTRACT-002", "name": "合同统计", "status": "PASS", "detail": "合同统计查询成功"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-CONTRACT-002", "name": "合同统计", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-CONTRACT-002", "name": "合同统计", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    all_results["TEST-CONTRACT"] = results
    
    # 用户管理测试
    results = {"name": "用户管理测试", "total": 2, "passed": 0, "failed": 0, "cases": []}
    try:
        resp = tester.get("/users")
        if resp.status_code == 200:
            data = resp.json()
            results["cases"].append({"id": "TC-USER-001", "name": "用户列表", "status": "PASS", "detail": f"获取到 {len(data.get('items', []))} 个用户"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-USER-001", "name": "用户列表", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-USER-001", "name": "用户列表", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    
    try:
        resp = tester.get("/auth/me")
        if resp.status_code == 200:
            data = resp.json()
            results["cases"].append({"id": "TC-USER-002", "name": "当前用户信息", "status": "PASS", "detail": f"用户: {data.get('username', 'unknown')}"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-USER-002", "name": "当前用户信息", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-USER-002", "name": "当前用户信息", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    all_results["TEST-USER"] = results
    
    # 银行流水测试
    results = {"name": "银行流水测试", "total": 2, "passed": 0, "failed": 0, "cases": []}
    try:
        resp = tester.get("/bank-flows")
        if resp.status_code == 200:
            data = resp.json()
            results["cases"].append({"id": "TC-BANKFLOW-001", "name": "银行流水列表", "status": "PASS", "detail": f"获取到 {len(data.get('items', []))} 条流水"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-BANKFLOW-001", "name": "银行流水列表", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-BANKFLOW-001", "name": "银行流水列表", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    
    try:
        resp = tester.get("/bank-accounts")
        if resp.status_code == 200:
            data = resp.json()
            results["cases"].append({"id": "TC-BANKFLOW-002", "name": "银行账户列表", "status": "PASS", "detail": f"获取到 {len(data.get('items', []))} 个账户"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-BANKFLOW-002", "name": "银行账户列表", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-BANKFLOW-002", "name": "银行账户列表", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    all_results["TEST-BANKFLOW"] = results
    
    # 票据管理测试
    results = {"name": "票据管理测试", "total": 1, "passed": 0, "failed": 0, "cases": []}
    try:
        resp = tester.get("/invoices")
        if resp.status_code == 200:
            data = resp.json()
            results["cases"].append({"id": "TC-INVOICE-001", "name": "票据列表", "status": "PASS", "detail": f"获取到 {len(data.get('items', []))} 张票据"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-INVOICE-001", "name": "票据列表", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-INVOICE-001", "name": "票据列表", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    all_results["TEST-INVOICE"] = results
    
    # 凭证管理测试
    results = {"name": "凭证管理测试", "total": 2, "passed": 0, "failed": 0, "cases": []}
    try:
        resp = tester.get("/vouchers")
        if resp.status_code == 200:
            data = resp.json()
            results["cases"].append({"id": "TC-VOUCHER-001", "name": "凭证列表", "status": "PASS", "detail": f"获取到 {len(data.get('items', []))} 张凭证"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-VOUCHER-001", "name": "凭证列表", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-VOUCHER-001", "name": "凭证列表", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    
    try:
        resp = tester.get("/vouchers/accounts")
        if resp.status_code == 200:
            results["cases"].append({"id": "TC-VOUCHER-002", "name": "科目列表", "status": "PASS", "detail": "会计科目列表查询成功"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-VOUCHER-002", "name": "科目列表", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-VOUCHER-002", "name": "科目列表", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    all_results["TEST-VOUCHER"] = results
    
    # 审核管理测试
    results = {"name": "审核管理测试", "total": 3, "passed": 0, "failed": 0, "cases": []}
    try:
        resp = tester.get("/audit/pending")
        if resp.status_code == 200:
            data = resp.json()
            results["cases"].append({"id": "TC-AUDIT-001", "name": "待审核任务", "status": "PASS", "detail": f"获取到 {len(data.get('items', []))} 个待审任务"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-AUDIT-001", "name": "待审核任务", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-AUDIT-001", "name": "待审核任务", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    
    try:
        resp = tester.get("/audit/statistics")
        if resp.status_code == 200:
            results["cases"].append({"id": "TC-AUDIT-002", "name": "审核统计", "status": "PASS", "detail": "审核统计查询成功"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-AUDIT-002", "name": "审核统计", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-AUDIT-002", "name": "审核统计", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    
    try:
        resp = tester.get("/audit/my-tasks")
        if resp.status_code == 200:
            results["cases"].append({"id": "TC-AUDIT-003", "name": "我的审核任务", "status": "PASS", "detail": "我的任务查询成功"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-AUDIT-003", "name": "我的审核任务", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-AUDIT-003", "name": "我的审核任务", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    all_results["TEST-AUDIT"] = results
    
    # 系统管理测试
    results = {"name": "系统管理测试", "total": 4, "passed": 0, "failed": 0, "cases": []}
    try:
        resp = tester.get("/sys/roles")
        if resp.status_code == 200:
            data = resp.json()
            results["cases"].append({"id": "TC-SYS-001", "name": "角色列表", "status": "PASS", "detail": f"获取到 {len(data.get('items', []))} 个角色"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-SYS-001", "name": "角色列表", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-SYS-001", "name": "角色列表", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    
    try:
        resp = tester.get("/sys/logs")
        if resp.status_code == 200:
            data = resp.json()
            results["cases"].append({"id": "TC-SYS-002", "name": "操作日志", "status": "PASS", "detail": f"获取到 {len(data.get('items', []))} 条日志"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-SYS-002", "name": "操作日志", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-SYS-002", "name": "操作日志", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    
    try:
        resp = tester.get("/sys/config")
        if resp.status_code == 200:
            results["cases"].append({"id": "TC-SYS-003", "name": "系统配置", "status": "PASS", "detail": "系统配置查询成功"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-SYS-003", "name": "系统配置", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-SYS-003", "name": "系统配置", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    
    try:
        resp = tester.session.get(f"{BASE_URL}/health")
        if resp.status_code == 200:
            results["cases"].append({"id": "TC-SYS-004", "name": "系统健康检查", "status": "PASS", "detail": "系统运行正常"})
            results["passed"] += 1
        else:
            results["cases"].append({"id": "TC-SYS-004", "name": "系统健康检查", "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
            results["failed"] += 1
    except Exception as e:
        results["cases"].append({"id": "TC-SYS-004", "name": "系统健康检查", "status": "ERROR", "detail": str(e)})
        results["failed"] += 1
    all_results["TEST-SYS"] = results
    
    # 报表测试 - 修正API路径和参数
    results = {"name": "财务报表测试", "total": 6, "passed": 0, "failed": 0, "cases": []}
    report_apis = [
        ("/reports/expense-detail?customer_id=1&period=2024-01", "TC-REPORT-001", "费用明细表"),
        ("/reports/accounts-receivable?customer_id=1&period=2024-01", "TC-REPORT-002", "应收账款报表"),
        ("/reports/balance-sheet?customer_id=1&period=2024-01", "TC-REPORT-003", "资产负债表"),
        ("/reports/income-statement?customer_id=1&period=2024-01", "TC-REPORT-004", "利润表"),
        ("/reports/cash-flow?customer_id=1&period=2024-01", "TC-REPORT-005", "现金流量表"),
        ("/reports/subject-balance?customer_id=1&period=2024-01", "TC-REPORT-006", "科目余额表"),
    ]
    for api, tid, name in report_apis:
        try:
            resp = tester.get(api)
            if resp.status_code == 200:
                results["cases"].append({"id": tid, "name": name, "status": "PASS", "detail": f"{name}查询成功"})
                results["passed"] += 1
            else:
                results["cases"].append({"id": tid, "name": name, "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
                results["failed"] += 1
        except Exception as e:
            results["cases"].append({"id": tid, "name": name, "status": "ERROR", "detail": str(e)})
            results["failed"] += 1
    all_results["TEST-REPORT"] = results
    
    # 高级功能测试
    results = {"name": "高级功能测试", "total": 6, "passed": 0, "failed": 0, "cases": []}
    adv_apis = [
        ("/adv/backup/tasks", "TC-ADV-001", "备份任务列表"),
        ("/adv/backup", "TC-ADV-002", "创建备份", "post"),
        ("/adv/scheduler/jobs", "TC-ADV-003", "定时任务列表"),
        ("/adv/notifications", "TC-ADV-004", "通知列表"),
        ("/adv/notifications/unread-count", "TC-ADV-005", "未读通知数"),
        ("/adv/tenant/config", "TC-ADV-006", "租户配置"),
    ]
    for item in adv_apis:
        api = item[0]
        tid = item[1]
        name = item[2]
        method = item[3] if len(item) > 3 else "get"
        try:
            if method == "post":
                resp = tester.post(api, json={"backup_type": "full"})
            else:
                resp = tester.get(api)
            if resp.status_code == 200:
                results["cases"].append({"id": tid, "name": name, "status": "PASS", "detail": f"{name}查询成功"})
                results["passed"] += 1
            else:
                results["cases"].append({"id": tid, "name": name, "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
                results["failed"] += 1
        except Exception as e:
            results["cases"].append({"id": tid, "name": name, "status": "ERROR", "detail": str(e)})
            results["failed"] += 1
    all_results["TEST-ADV"] = results
    
    # 移动端测试
    results = {"name": "移动端API测试", "total": 3, "passed": 0, "failed": 0, "cases": []}
    mobile_apis = [
        ("/mobile/h5/dashboard", "TC-MOBILE-001", "H5仪表盘"),
        ("/mobile/miniapp/dashboard", "TC-MOBILE-002", "小程序仪表盘"),
        ("/mobile/portal/dashboard", "TC-MOBILE-003", "Portal仪表盘"),
    ]
    for api, tid, name in mobile_apis:
        try:
            resp = tester.get(api)
            if resp.status_code == 200:
                results["cases"].append({"id": tid, "name": name, "status": "PASS", "detail": f"{name}查询成功"})
                results["passed"] += 1
            else:
                results["cases"].append({"id": tid, "name": name, "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
                results["failed"] += 1
        except Exception as e:
            results["cases"].append({"id": tid, "name": name, "status": "ERROR", "detail": str(e)})
            results["failed"] += 1
    all_results["TEST-MOBILE"] = results
    
    # AI测试 - 修正参数
    results = {"name": "AI智能功能测试", "total": 4, "passed": 0, "failed": 0, "cases": []}
    ai_apis = [
        ("/ai/smart-booking/generate-voucher", "TC-AI-001", "智能凭证生成", "post", {"bill_data": {"amount": 100}, "customer_id": "1"}),
        ("/ai/anomaly/alerts?customer_id=1", "TC-AI-002", "异常检测告警"),
        ("/ai/insights?customer_id=1", "TC-AI-003", "智能洞察"),
        ("/ai/report/trends?customer_id=1&report_type=balance", "TC-AI-004", "报表趋势分析"),
    ]
    for item in ai_apis:
        api = item[0]
        tid = item[1]
        name = item[2]
        method = item[3] if len(item) > 3 else "get"
        data = item[4] if len(item) > 4 else {}
        try:
            if method == "post":
                resp = tester.post(api, json=data)
            else:
                resp = tester.get(api)
            if resp.status_code in [200, 201]:
                results["cases"].append({"id": tid, "name": name, "status": "PASS", "detail": f"{name}成功"})
                results["passed"] += 1
            else:
                results["cases"].append({"id": tid, "name": name, "status": "FAIL", "detail": f"状态码: {resp.status_code}"})
                results["failed"] += 1
        except Exception as e:
            results["cases"].append({"id": tid, "name": name, "status": "ERROR", "detail": str(e)})
            results["failed"] += 1
    all_results["TEST-AI"] = results
    
    return all_results


def generate_report(all_results):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# SmartLedger Step3 测试报告 (增强版)

## 测试基本信息
- **测试时间**: {timestamp}
- **测试环境**: http://localhost:8000

---

## 测试执行结果汇总

| 测试编号 | 测试名称 | 用例总数 | 通过 | 失败 | 状态 |
|---------|---------|---------|------|------|------|
"""
    
    total_cases = 0
    total_passed = 0
    total_failed = 0
    
    for test_id, result in all_results.items():
        cases = result["total"]
        passed = result["passed"]
        failed = result["failed"]
        
        if passed > 0 and failed == 0:
            status = "✅ PASS"
        elif passed > 0:
            status = "⚠️ PARTIAL"
        else:
            status = "❌ FAIL"
        
        total_cases += cases
        total_passed += passed
        total_failed += failed
        
        report += f"| {test_id} | {result.get('name', test_id)} | {cases} | {passed} | {failed} | {status} |\n"
    
    pass_rate = (total_passed / total_cases * 100) if total_cases > 0 else 0
    
    report += f"""
**总计**: {total_cases} 用例 | **通过**: {total_passed} | **失败**: {total_failed}
**通过率**: {pass_rate:.1f}%

---

## 详细测试结果

"""
    
    for test_id, result in all_results.items():
        report += f"\n### {test_id}: {result.get('name', '')}\n\n"
        report += "| 用例ID | 用例名称 | 状态 | 详情 |\n"
        report += "|--------|----------|------|------|\n"
        
        for case in result["cases"]:
            if case["status"] == "PASS":
                status_icon = "✅"
            elif case["status"] in ["FAIL", "ERROR"]:
                status_icon = "❌"
            else:
                status_icon = "⏸️"
            detail = case["detail"][:60] + "..." if len(case["detail"]) > 60 else case["detail"]
            report += f"| {case['id']} | {case['name']} | {status_icon} {case['status']} | {detail} |\n"
    
    report += f"""

---

## 测试结论

**整体状态**: {"✅ 通过" if total_failed == 0 else ("⚠️ 有条件通过" if pass_rate >= 60 else "❌ 不通过")}
**通过率**: {pass_rate:.1f}%

---

**报告生成时间**: {timestamp}
"""
    
    return report


if __name__ == "__main__":
    print("="*60)
    print("SmartLedger Step3 API 测试 (增强版)")
    print("="*60)
    
    results = run_all_tests()
    
    if results:
        report = generate_report(results)
        with open("/root/.openclaw/workspace/smartledger/task/step3/test/result3/00_增强测试报告.md", "w") as f:
            f.write(report)
        print("\n✅ 测试报告已生成")
        
        # 打印汇总
        total_cases = sum(r["total"] for r in results.values())
        total_passed = sum(r["passed"] for r in results.values())
        total_failed = sum(r["failed"] for r in results.values())
        pass_rate = (total_passed / total_cases * 100) if total_cases > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"测试完成!")
        print(f"{'='*60}")
        print(f"总计: {total_cases} 用例")
        print(f"通过: {total_passed}")
        print(f"失败: {total_failed}")
        print(f"通过率: {pass_rate:.1f}%")
    else:
        print("❌ 测试执行失败")
