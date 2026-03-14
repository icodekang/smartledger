#!/usr/bin/env python3
"""
SmartLedger 完整测试汇总 - 100%通过率目标
运行所有Step测试并生成汇总报告
"""

import subprocess
import json
import os

os.chdir("/root/.openclaw/workspace/smartledger")

print("="*60)
print("SmartLedger 完整测试汇总")
print("="*60)

# 运行各步骤测试
tests = [
    ("Step1", "task/test/run_step1_v2.py"),
    ("Step2", "task/test/run_step2_v2.py"),
    ("Step3", "task/test/run_step3_v2.py"),
]

results = []
for name, script in tests:
    print(f"\n--- 运行 {name} 测试 ---")
    result = subprocess.run(
        ["python3", script],
        capture_output=True,
        text=True,
        timeout=60
    )
    # 读取结果文件
    result_file = f"task/{name.lower()}_test_result.json"
    if os.path.exists(result_file):
        with open(result_file) as f:
            data = json.load(f)
            results.append({
                "step": name,
                "total": data["total"],
                "pass": data["pass"],
                "fail": data["fail"],
                "pass_rate": data["pass_rate"]
            })
            print(f"  {name}: {data['pass']}/{data['total']} 通过 ({data['pass_rate']})")
    else:
        print(f"  {name}: 结果文件不存在")

# 汇总
print("\n" + "="*60)
print("测试汇总")
print("="*60)
total_tests = sum(r["total"] for r in results)
total_pass = sum(r["pass"] for r in results)
total_fail = sum(r["fail"] for r in results)
overall_rate = (total_pass / total_tests * 100) if total_tests > 0 else 0

print(f"总测试数: {total_tests}")
print(f"通过: {total_pass}")
print(f"失败: {total_fail}")
print(f"总体通过率: {overall_rate:.1f}%")

# 保存汇总
summary = {
    "test_time": subprocess.run(["date"], capture_output=True, text=True).stdout.strip(),
    "total": total_tests,
    "pass": total_pass,
    "fail": total_fail,
    "pass_rate": f"{overall_rate:.1f}%",
    "steps": results
}
with open("/root/.openclaw/workspace/smartledger/task/final_test_summary.json", "w") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("\n✅ 测试汇总已保存")
