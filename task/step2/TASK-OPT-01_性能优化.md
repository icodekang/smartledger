# 任务编号：TASK-OPT-01
# 任务名称：性能优化
# 优先级：P1
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

对系统进行全面性能优化，包括数据库查询优化、接口响应优化、前端加载优化。

================================================================================
                              优化清单
================================================================================

## 1. 数据库优化

### 1.1 索引优化
```sql
-- 票据表索引
CREATE INDEX idx_bills_customer_status ON bills(customer_id, process_status);
CREATE INDEX idx_bills_created_at ON bills(created_at DESC);
CREATE INDEX idx_bills_invoice_date ON bills(invoice_date);
CREATE INDEX idx_bills_seller_name ON bills(seller_name);

-- 凭证表索引
CREATE INDEX idx_vouchers_customer_status ON vouchers(customer_id, status);
CREATE INDEX idx_vouchers_period ON vouchers(period);
CREATE INDEX idx_vouchers_date ON vouchers(voucher_date);

-- 银行流水表索引
CREATE INDEX idx_bank_flows_customer_date ON bank_flows(customer_id, transaction_date);
CREATE INDEX idx_bank_flows_match_status ON bank_flows(match_status);

-- 复合索引（常用查询组合）
CREATE INDEX idx_bills_customer_date_status ON bills(customer_id, invoice_date, process_status);
```

### 1.2 查询优化
```python
# 优化前（N+1查询）
for bill in bills:
    customer = db.query(Customer).get(bill.customer_id)  # N次查询

# 优化后（Join查询）
bills = db.query(Bill, Customer).join(Customer).all()

# 优化前（全表统计）
total = db.query(Bill).filter(Bill.customer_id == cid).count()

# 优化后（缓存统计）
total = redis.get(f"bill_count:{cid}") or calculate_and_cache()
```

### 1.3 分页优化
```python
# 优化深分页问题
def get_bills_optimized(customer_id: str, page: int, page_size: int):
    """使用游标分页替代 offset 分页"""
    if page <= 3:
        # 浅页使用 offset
        return query.offset((page-1)*page_size).limit(page_size).all()
    else:
        # 深页使用游标（基于上一页最后一条的ID）
        last_id = get_last_seen_id(page-1)
        return query.filter(Bill.id > last_id).limit(page_size).all()
```

## 2. 缓存策略

### 2.1 Redis 缓存层
```python
# 配置
CACHE_CONFIG = {
    "default_ttl": 300,  # 5分钟
    "long_ttl": 3600,    # 1小时
    "short_ttl": 60      # 1分钟
}

# 装饰器缓存
@cache_result(ttl=300, key_prefix="voucher_stats")
def get_voucher_statistics(customer_id: str):
    """凭证统计缓存5分钟"""
    return calculate_statistics(customer_id)

# 手动缓存
def get_bill_list_with_cache(customer_id: str, page: int):
    cache_key = f"bills:{customer_id}:{page}"
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    result = fetch_from_db(customer_id, page)
    redis.setex(cache_key, 60, json.dumps(result))
    return result
```

### 2.2 缓存失效策略
```python
# 数据更新时清除相关缓存
def update_bill(bill_id: str, data: dict):
    bill = db.query(Bill).get(bill_id)
    bill.update(data)
    db.commit()
    
    # 清除缓存
    redis.delete(f"bill:{bill_id}")
    redis.delete(f"bills:{bill.customer_id}:*")  # 清除该客户的列表缓存
    redis.delete(f"bill_stats:{bill.customer_id}")
```

## 3. 接口性能优化

### 3.1 响应时间目标
| 接口类型 | 目标响应时间 | 优化措施 |
|----------|--------------|----------|
| 简单查询 | < 100ms | 缓存 + 索引 |
| 列表查询 | < 200ms | 分页 + 延迟加载 |
| 复杂统计 | < 500ms | 异步计算 + 缓存 |
| 文件上传 | < 3s | 异步处理 + 流式上传 |

### 3.2 批量操作接口
```python
# 批量更新替代循环单条更新
@app.post("/api/v1/bills/batch-update")
def batch_update_bills(data: BatchUpdateRequest):
    """批量更新状态"""
    # 单条 UPDATE 改为批量 UPDATE
    db.query(Bill).filter(Bill.id.in_(data.ids)).update({
        Bill.status: data.status
    }, synchronize_session=False)
    db.commit()
```

### 3.3 数据压缩
```python
# 大响应启用 Gzip
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

## 4. 前端性能优化

### 4.1 懒加载
```typescript
// 路由懒加载
const routes = [
  {
    path: '/bills',
    component: () => import('@/views/bills/List.vue')  // 懒加载
  }
]

// 图片懒加载
<img v-lazy="bill.image_url" />

// 表格虚拟滚动（大数据量）
<ElTableV2 :data="largeData" :height="400" />
```

### 4.2 资源优化
```typescript
// 依赖按需加载
import { ElButton, ElTable } from 'element-plus'

// 图片压缩
// 使用 webp 格式，质量 80%

// CDN 资源
const CDN_ASSETS = {
  vue: 'https://cdn.jsdelivr.net/npm/vue@3.4.0',
  element: 'https://cdn.jsdelivr.net/npm/element-plus@2.5.0'
}
```

### 4.3 状态管理优化
```typescript
// Pinia 分模块，按需加载
import { defineStore } from 'pinia'

export const useBillStore = defineStore('bill', {
  state: () => ({
    list: [],
    cache: new Map()  // 本地缓存
  }),
  
  actions: {
    async getList(params) {
      const cacheKey = JSON.stringify(params)
      if (this.cache.has(cacheKey)) {
        return this.cache.get(cacheKey)
      }
      const data = await api.getList(params)
      this.cache.set(cacheKey, data)
      return data
    }
  }
})
```

## 5. 异步处理

### 5.1 耗时任务异步化
```python
# 使用 Celery 处理耗时任务
from celery import Celery

celery_app = Celery('smartledger')

@celery_app.task
def process_ocr_async(bill_id: str, image_path: str):
    """异步 OCR 处理"""
    result = ocr_service.recognize(image_path)
    update_bill_ocr_result(bill_id, result)

# 接口中调用
@app.post("/api/v1/bills/upload")
def upload_bill(file: UploadFile):
    bill = save_bill(file)
    # 异步处理 OCR
    process_ocr_async.delay(bill.id, bill.image_path)
    return {"id": bill.id, "status": "processing"}
```

### 5.2 任务队列监控
```python
# Flower 监控 Celery
# 启动: celery -A tasks flower --port=5555
```

## 6. 性能监控

### 6.1 接口性能埋点
```python
# 中间件记录接口耗时
@app.middleware("http")
async def performance_monitor(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    # 记录慢查询
    if duration > 1.0:
        logger.warning(f"Slow request: {request.url.path} took {duration:.2f}s")
    
    # 上报监控
    metrics.histogram("http_request_duration", duration, 
                      tags={"path": request.url.path})
    
    return response
```

### 6.2 性能测试基准
```python
# locust 压测脚本
from locust import HttpUser, task

class SmartLedgerUser(HttpUser):
    @task(3)
    def get_bills(self):
        self.client.get("/api/v1/invoices")
    
    @task(1)
    def upload_bill(self):
        self.client.post("/api/v1/invoices/upload", files={...})
```

================================================================================
                              验收标准
================================================================================

1. [ ] 列表接口平均响应时间 < 200ms
2. [ ] 详情接口平均响应时间 < 100ms
3. [ ] 数据库慢查询日志中无 > 1s 的查询
4. [ ] Redis 缓存命中率 > 80%
5. [ ] 前端首屏加载时间 < 3s
6. [ ] 100 并发用户系统稳定
7. [ ] 内存使用稳定，无泄漏

================================================================================
                              开发提示
================================================================================

1. 使用 EXPLAIN ANALYZE 分析 SQL 执行计划
2. 使用 Redis INFO 监控缓存命中率
3. 使用 PyInstrument 进行 Python 性能分析
4. 使用 Lighthouse 进行前端性能审计
5. 优化后务必进行压测验证
