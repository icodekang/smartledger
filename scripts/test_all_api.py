#!/usr/bin/env python3
"""
Step3 API 测试 - 全量接口测试
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
TOKEN = None

def login():
    """登录获取token"""
    global TOKEN
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data={
            "username": "testadmin",
            "password": "Test123456"
        }, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            TOKEN = data.get("data", {}).get("access_token")
            return True
    except Exception as e:
        print(f"登录失败: {e}")
    return False

def test_api(name, method, endpoint, data=None):
    """测试单个API"""
    headers = {}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    if method in ["POST", "PUT"] and data:
        headers["Content-Type"] = "application/json"
    
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            resp = requests.post(url, json=data, headers=headers, timeout=5)
        elif method == "PUT":
            resp = requests.put(url, json=data, headers=headers, timeout=5)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=5)
        else:
            return {"name": name, "status": "SKIP", "code": 0}
        
        return {
            "name": name,
            "status": "PASS" if resp.status_code < 400 else "FAIL",
            "code": resp.status_code
        }
    except Exception as e:
        return {
            "name": name,
            "status": "FAIL",
            "code": 0,
            "error": str(e)
        }

def main():
    print("="*70)
    print("Step3 API 接口测试")
    print("="*70)
    
    if not login():
        print("❌ 登录失败")
        return
    print("✅ 登录成功\n")
    
    tests = []
    
    # 客户管理模块
    print("--- 客户管理模块 ---")
    tests.append(test_api("客户列表", "GET", "/api/v1/customers"))
    tests.append(test_api("客户统计", "GET", "/api/v1/customers/statistics"))
    print(f"客户列表: {'✅' if tests[-2]['status']=='PASS' else '❌'} ({tests[-2]['code']})")
    print(f"客户统计: {'✅' if tests[-1]['status']=='PASS' else '❌'} ({tests[-1]['code']})")
    
    # 合同管理
    print("\n--- 合同管理模块 ---")
    tests.append(test_api("合同列表", "GET", "/api/v1/contracts"))
    tests.append(test_api("合同统计", "GET", "/api/v1/contracts/statistics"))
    print(f"合同列表: {'✅' if tests[-2]['status']=='PASS' else '❌'} ({tests[-2]['code']})")
    print(f"合同统计: {'✅' if tests[-1]['status']=='PASS' else '❌'} ({tests[-1]['code']})")
    
    # 用户管理
    print("\n--- 用户管理模块 ---")
    tests.append(test_api("用户列表", "GET", "/api/v1/users"))
    tests.append(test_api("当前用户", "GET", "/api/v1/auth/me"))
    print(f"用户列表: {'✅' if tests[-2]['status']=='PASS' else '❌'} ({tests[-2]['code']})")
    print(f"当前用户: {'✅' if tests[-1]['status']=='PASS' else '❌'} ({tests[-1]['code']})")
    
    # 银行流水
    print("\n--- 银行流水模块 ---")
    tests.append(test_api("银行流水列表", "GET", "/api/v1/bank-flows"))
    tests.append(test_api("银行账户列表", "GET", "/api/v1/bank-accounts"))
    print(f"银行流水列表: {'✅' if tests[-2]['status']=='PASS' else '❌'} ({tests[-2]['code']})")
    print(f"银行账户列表: {'✅' if tests[-1]['status']=='PASS' else '❌'} ({tests[-1]['code']})")
    
    # 票据管理
    print("\n--- 票据管理模块 ---")
    tests.append(test_api("票据列表", "GET", "/api/v1/invoices"))
    print(f"票据列表: {'✅' if tests[-1]['status']=='PASS' else '❌'} ({tests[-1]['code']})")
    
    # 凭证管理
    print("\n--- 凭证管理模块 ---")
    tests.append(test_api("凭证列表", "GET", "/api/v1/vouchers"))
    tests.append(test_api("科目列表", "GET", "/api/v1/vouchers/accounts"))
    print(f"凭证列表: {'✅' if tests[-1]['status']=='PASS' else '❌'} ({tests[-1]['code']})")
    print(f"科目列表: {'✅' if tests[-2]['status']=='PASS' else '❌'} ({tests[-2]['code']})")
    
    # 审核管理
    print("\n--- 审核管理模块 ---")
    tests.append(test_api("待审核任务", "GET", "/api/v1/audit/pending"))
    tests.append(test_api("审核统计", "GET", "/api/v1/audit/statistics"))
    tests.append(test_api("我的任务", "GET", "/api/v1/audit/my-tasks"))
    print(f"待审核任务: {'✅' if tests[-3]['status']=='PASS' else '❌'} ({tests[-3]['code']})")
    print(f"审核统计: {'✅' if tests[-2]['status']=='PASS' else '❌'} ({tests[-2]['code']})")
    print(f"我的任务: {'✅' if tests[-1]['status']=='PASS' else '❌'} ({tests[-1]['code']})")
    
    # 系统模块 (预期可能失败)
    print("\n--- 系统管理模块 (Step3 待开发) ---")
    tests.append(test_api("角色列表", "GET", "/api/v1/roles"))
    tests.append(test_api("操作日志", "GET", "/api/v1/audit/logs"))
    tests.append(test_api("系统配置", "GET", "/api/v1/config"))
    print(f"角色列表: {'✅' if tests[-3]['status']=='PASS' else '❌'} ({tests[-3]['code']}) {'- 未实现' if tests[-3]['code']==404 else ''}")
    print(f"操作日志: {'✅' if tests[-2]['status']=='PASS' else '❌'} ({tests[-2]['code']}) {'- 未实现' if tests[-2]['code']==404 else ''}")
    print(f"系统配置: {'✅' if tests[-1]['status']=='PASS' else '❌'} ({tests[-1]['code']}) {'- 未实现' if tests[-1]['code']==404 else ''}")
    
    # 汇总
    print("\n" + "="*70)
    print("测试汇总")
    print("="*70)
    pass_count = sum(1 for t in tests if t['status'] == 'PASS')
    fail_count = len(tests) - pass_count
    print(f"总计: {len(tests)} 项")
    print(f"通过: {pass_count} 项")
    print(f"失败: {fail_count} 项")
    print(f"通过率: {pass_count/len(tests)*100:.1f}%")
    
    # 保存结果
    result = {
        "test_time": datetime.now().isoformat(),
        "total": len(tests),
        "pass": pass_count,
        "fail": fail_count,
        "pass_rate": f"{pass_count/len(tests)*100:.1f}%",
        "details": tests
    }
    
    with open("task/step3/test/result3/api_test_result.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n测试结果已保存到: task/step3/test/result3/api_test_result.json")

if __name__ == "__main__":
    main()
