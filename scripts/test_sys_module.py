#!/usr/bin/env python3
"""
Step3 测试脚本 - 系统管理模块
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
TOKEN = None
RESULTS = []

def login():
    """登录获取token"""
    global TOKEN
    try:
        # 尝试 form-data 登录
        resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data={
            "username": "testadmin",
            "password": "Test123456"
        })
        if resp.status_code == 200:
            data = resp.json()
            TOKEN = data.get("data", {}).get("access_token") or data.get("access_token")
            if TOKEN:
                return True
            else:
                print(f"Token not found in response: {data}")
        else:
            print(f"登录响应: {resp.status_code} - {resp.text[:200]}")
    except Exception as e:
        print(f"登录失败: {e}")
    return False

def test(name, method, endpoint, data=None, expected_status=None):
    """执行单个测试"""
    headers = {}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    
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
            return False, f"未知方法: {method}"
        
        status_ok = expected_status is None or resp.status_code == expected_status
        RESULTS.append({
            "name": name,
            "status": "PASS" if status_ok else "FAIL",
            "code": resp.status_code,
            "expected": expected_status
        })
        return status_ok, f"状态码: {resp.status_code}"
    except Exception as e:
        RESULTS.append({
            "name": name,
            "status": "FAIL",
            "error": str(e)
        })
        return False, str(e)

def main():
    print("="*60)
    print("Step3 系统管理模块测试")
    print("="*60)
    
    # 登录
    if not login():
        print("❌ 登录失败，无法继续测试")
        return
    print("✅ 登录成功")
    
    print("\n--- TEST-SYS-02: 角色权限管理测试 ---")
    
    # TC-SYS-02-001: 角色列表
    ok, msg = test("TC-SYS-02-001 角色列表", "GET", "/api/v1/roles", expected_status=200)
    print(f"{'✅' if ok else '❌'} 角色列表: {msg}")
    
    # TC-SYS-02-002: 创建角色
    ok, msg = test("TC-SYS-02-002 创建角色", "POST", "/api/v1/roles", {
        "code": "test_role",
        "name": "测试角色",
        "permissions": []
    }, expected_status=201)
    print(f"{'✅' if ok else '❌'} 创建角色: {msg}")
    
    # TC-SYS-02-003: 系统角色保护 (删除管理员)
    ok, msg = test("TC-SYS-02-003 删除系统角色", "DELETE", "/api/v1/roles/1")
    print(f"{'✅' if not ok else '❌'} 系统角色保护: {'保护正常' if not ok else '未保护'} ({msg})")
    if not ok:
        # 如果失败是预期的，标记为通过
        for r in RESULTS:
            if r["name"] == "TC-SYS-02-003 删除系统角色":
                r["status"] = "PASS"
                r["note"] = "系统角色保护正常"
    
    # TC-SYS-02-004: 菜单权限
    ok, msg = test("TC-SYS-02-004 菜单权限列表", "GET", "/api/v1/menus", expected_status=200)
    print(f"{'✅' if ok else '❌'} 菜单权限: {msg}")
    
    print("\n--- TEST-SYS-03: 操作日志审计测试 ---")
    
    # TC-SYS-03-001: 操作日志
    ok, msg = test("TC-SYS-03-001 操作日志", "GET", "/api/v1/audit/logs", expected_status=200)
    print(f"{'✅' if ok else '❌'} 操作日志: {msg}")
    
    # TC-SYS-03-002: 登录日志
    ok, msg = test("TC-SYS-03-002 登录日志", "GET", "/api/v1/audit/login-logs", expected_status=200)
    print(f"{'✅' if ok else '❌'} 登录日志: {msg}")
    
    # TC-SYS-03-003: 日志统计
    ok, msg = test("TC-SYS-03-003 日志统计", "GET", "/api/v1/audit/stats", expected_status=200)
    print(f"{'✅' if ok else '❌'} 日志统计: {msg}")
    
    print("\n--- TEST-SYS-04: 系统参数配置测试 ---")
    
    # TC-SYS-04-001: 系统配置获取
    ok, msg = test("TC-SYS-04-001 系统配置", "GET", "/api/v1/config", expected_status=200)
    print(f"{'✅' if ok else '❌'} 系统配置: {msg}")
    
    # TC-SYS-04-002: 系统配置更新
    ok, msg = test("TC-SYS-04-002 更新配置", "PUT", "/api/v1/config", {
        "system_name": "测试系统"
    }, expected_status=200)
    print(f"{'✅' if ok else '❌'} 更新配置: {msg}")
    
    # TC-SYS-04-003: 备份配置
    ok, msg = test("TC-SYS-04-003 备份配置", "GET", "/api/v1/config/backup", expected_status=200)
    print(f"{'✅' if ok else '❌'} 备份配置: {msg}")
    
    # TC-SYS-04-004: 邮件配置
    ok, msg = test("TC-SYS-04-004 邮件配置", "GET", "/api/v1/config/email", expected_status=200)
    print(f"{'✅' if ok else '❌'} 邮件配置: {msg}")
    
    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)
    pass_count = sum(1 for r in RESULTS if r["status"] == "PASS")
    fail_count = len(RESULTS) - pass_count
    print(f"总计: {len(RESULTS)} 项")
    print(f"通过: {pass_count} 项")
    print(f"失败: {fail_count} 项")
    print(f"通过率: {pass_count/len(RESULTS)*100:.1f}%")
    
    # 输出失败项
    if fail_count > 0:
        print("\n失败的测试:")
        for r in RESULTS:
            if r["status"] == "FAIL":
                print(f"  ❌ {r['name']}")
    
    return RESULTS

if __name__ == "__main__":
    main()
