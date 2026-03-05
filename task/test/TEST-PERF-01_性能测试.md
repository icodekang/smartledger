# 任务编号：TEST-PERF-01
# 任务名称：性能测试
# 负责人：测试工程师
# 工期：2天
# 依赖：全部MVP开发任务完成

================================================================================
                            任务详细说明书
================================================================================

## 一、任务目标
验证系统在高并发、大数据量场景下的性能表现，识别性能瓶颈。

## 二、测试范围

### 2.1 负载测试（Load Testing）
- [ ] 并发用户登录
- [ ] 并发发票上传
- [ ] 并发OCR识别
- [ ] 并发凭证生成
- [ ] 并发查询请求

### 2.2 压力测试（Stress Testing）
- [ ] 系统最大承载用户数
- [ ] API响应时间恶化点
- [ ] 内存泄漏检测
- [ ] 连接池耗尽场景
- [ ] 数据库死锁检测

### 2.3 稳定性测试（Soak Testing）
- [ ] 24小时持续运行
- [ ] 内存/CPU趋势监控
- [ ] 日志文件增长
- [ ] 数据库连接稳定性

### 2.4 大数据量测试
- [ ] 10万条发票数据查询
- [ ] 批量操作性能（100/500/1000条）
- [ ] 数据库索引优化验证
- [ ] 分页查询性能

## 三、测试用例示例

```python
# tests/performance/test_load.py

import pytest
import asyncio
import aiohttp
import time
from statistics import mean, median

class TestPerformance:
    """性能测试套件"""
    
    BASE_URL = "http://localhost:8000"
    
    async def make_request(self, session, endpoint, method="GET", data=None, headers=None):
        """发起单个请求并记录耗时"""
        start = time.time()
        try:
            if method == "GET":
                async with session.get(f"{self.BASE_URL}{endpoint}", headers=headers) as resp:
                    await resp.read()
                    status = resp.status
            else:
                async with session.post(f"{self.BASE_URL}{endpoint}", json=data, headers=headers) as resp:
                    await resp.read()
                    status = resp.status
            
            elapsed = time.time() - start
            return {"status": status, "elapsed": elapsed, "error": None}
        except Exception as e:
            elapsed = time.time() - start
            return {"status": None, "elapsed": elapsed, "error": str(e)}
    
    async def run_concurrent_requests(self, endpoint, method="GET", data=None, 
                                       headers=None, concurrency=10, total=100):
        """执行并发请求"""
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_request(session):
            async with semaphore:
                return await self.make_request(session, endpoint, method, data, headers)
        
        async with aiohttp.ClientSession() as session:
            tasks = [bounded_request(session) for _ in range(total)]
            results = await asyncio.gather(*tasks)
        
        return results
    
    @pytest.mark.asyncio
    async def test_login_concurrent(self):
        """并发登录测试"""
        login_data = {
            "email": "test_{}.@example.com",
            "password": "TestPass123!"
        }
        
        results = []
        for i in range(100):
            data = {
                "email": login_data["email"].format(i),
                "password": login_data["password"]
            }
            result = await self.run_concurrent_requests(
                "/api/v1/auth/login",
                method="POST",
                data=data,
                concurrency=20,
                total=100
            )
            results.extend(result)
        
        # 分析结果
        success_count = sum(1 for r in results if r["status"] == 200)
        response_times = [r["elapsed"] for r in results if r["status"] == 200]
        
        print(f"\n并发登录测试结果:")
        print(f"  成功率: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
        print(f"  平均响应时间: {mean(response_times):.3f}s")
        print(f"  P50响应时间: {median(response_times):.3f}s")
        print(f"  P95响应时间: {sorted(response_times)[int(len(response_times)*0.95)]:.3f}s")
        print(f"  P99响应时间: {sorted(response_times)[int(len(response_times)*0.99)]:.3f}s")
        
        # 验收标准
        assert success_count / len(results) >= 0.95  # 成功率>95%
        assert mean(response_times) < 2.0  # 平均响应<2秒
        assert median(response_times) < 1.0  # P50<1秒
    
    @pytest.mark.asyncio
    async def test_invoice_list_query_performance(self, auth_headers):
        """发票列表查询性能"""
        # 预热
        await self.run_concurrent_requests(
            "/api/v1/invoices?page=1&page_size=20",
            headers=auth_headers,
            concurrency=1,
            total=5
        )
        
        # 正式测试
        results = await self.run_concurrent_requests(
            "/api/v1/invoices?page=1&page_size=20",
            headers=auth_headers,
            concurrency=50,
            total=500
        )
        
        response_times = [r["elapsed"] for r in results if r["status"] == 200]
        
        print(f"\n发票列表查询性能:")
        print(f"  并发数: 50")
        print(f"  总请求数: 500")
        print(f"  平均响应时间: {mean(response_times):.3f}s")
        print(f"  P95响应时间: {sorted(response_times)[int(len(response_times)*0.95)]:.3f}s")
        
        assert mean(response_times) < 0.5  # 平均<500ms
        assert max(response_times) < 3.0  # 最大<3秒
    
    @pytest.mark.asyncio
    async def test_large_dataset_query(self, auth_headers):
        """大数据集查询性能"""
        # 测试不同分页大小
        for page_size in [20, 50, 100]:
            start = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/api/v1/invoices?page=1&page_size={page_size}",
                    headers=auth_headers
                ) as resp:
                    data = await resp.json()
            elapsed = time.time() - start
            
            print(f"\n分页大小 {page_size}: {elapsed:.3f}s")
            assert elapsed < 2.0  # 每种分页<2秒
    
    @pytest.mark.asyncio
    async def test_batch_operations_performance(self, auth_headers):
        """批量操作性能"""
        batch_sizes = [10, 50, 100]
        
        for size in batch_sizes:
            invoice_ids = [f"inv-{i}" for i in range(size)]
            
            start = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/api/v1/vouchers/generate-batch",
                    headers=auth_headers,
                    json={"invoice_ids": invoice_ids}
                ) as resp:
                    await resp.read()
            elapsed = time.time() - start
            
            print(f"\n批量生成 {size} 张凭证: {elapsed:.3f}s")
            assert elapsed < 10.0  # 批量操作<10秒
    
    def test_ocr_processing_throughput(self):
        """OCR处理吞吐量测试"""
        import subprocess
        
        # 使用locust进行压力测试
        result = subprocess.run([
            "locust", "-f", "tests/performance/locustfile.py",
            "--headless", "-u", "10", "-r", "2", "--run-time", "60s",
            "--host", self.BASE_URL
        ], capture_output=True, text=True)
        
        print(result.stdout)
        assert result.returncode == 0
```

```python
# tests/performance/locustfile.py

from locust import HttpUser, task, between

class InvoiceUser(HttpUser):
    """Locust性能测试用户"""
    wait_time = between(1, 3)
    
    def on_start(self):
        """登录获取token"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(5)
    def list_invoices(self):
        """查询发票列表"""
        self.client.get("/api/v1/invoices?page=1&page_size=20", headers=self.headers)
    
    @task(3)
    def get_invoice_detail(self):
        """获取发票详情"""
        self.client.get("/api/v1/invoices/inv-test-001", headers=self.headers)
    
    @task(2)
    def create_invoice(self):
        """创建发票"""
        self.client.post("/api/v1/invoices", headers=self.headers, json={
            "invoice_type": "vat_normal",
            "amount": 1000.00,
            "seller_name": "测试供应商"
        })
    
    @task(1)
    def generate_voucher(self):
        """生成凭证"""
        self.client.post("/api/v1/vouchers/generate", headers=self.headers, json={
            "invoice_ids": ["inv-test-001"],
            "voucher_date": "2024-03-15"
        })
```

## 四、性能指标基准

| 场景 | 目标 | 警告阈值 | 失败阈值 |
|------|------|----------|----------|
| 登录响应 | < 500ms | < 1s | > 2s |
| 列表查询 | < 300ms | < 500ms | > 1s |
| 详情查询 | < 200ms | < 400ms | > 800ms |
| 文件上传 | < 3s | < 5s | > 10s |
| OCR识别 | < 5s | < 8s | > 15s |
| 凭证生成 | < 2s | < 4s | > 8s |
| 并发登录(100) | 成功率>99% | >95% | < 90% |
| 并发查询(500) | 成功率>99% | >95% | < 90% |

## 五、验收标准
- [ ] 所有API响应时间满足基准要求
- [ ] 并发测试成功率>95%
- [ ] 24小时稳定性测试通过
- [ ] 内存增长<10%
- [ ] CPU使用率<80%
- [ ] 性能测试报告完整

================================================================================
                              提交要求
================================================================================

1. 提交 tests/performance/ 目录
2. 提交 Locust 测试脚本
3. 提交性能测试报告（含图表）
4. 提交性能优化建议
