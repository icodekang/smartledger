# 任务编号：TASK-ADV-03
# 任务名称：定时任务调度
# 优先级：P1
# 预估工期：1.5天
# 负责人：后端

================================================================================
                              任务描述
================================================================================

开发定时任务调度功能，支持自动生成凭证、结账提醒、数据清理等自动化任务。

================================================================================
                              需求详情
================================================================================

## 1. 定时任务类型

| 任务 | 说明 | 频率 | 时间 |
|------|------|------|------|
| 月度凭证生成 | 根据银行流水自动生成凭证 | 每月1日 | 02:00 |
| 结账提醒 | 提醒会计进行月度结账 | 每月25日 | 09:00 |
| 合同到期提醒 | 提醒即将到期的客户合同 | 每天 | 09:00 |
| 数据清理 | 清理过期日志和临时文件 | 每周日 | 03:00 |
| 数据备份 | 自动备份数据库 | 每天 | 02:00 |
| 报表生成 | 自动生成月度财务报表 | 每月1日 | 04:00 |

## 2. 数据模型

```python
class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    name = Column(String(100), nullable=False, comment="任务名称")
    task_type = Column(String(50), nullable=False, comment="任务类型")
    
    # 调度配置
    schedule_type = Column(String(20), default="cron", comment="cron/interval/once")
    cron_expression = Column(String(100), comment="Cron表达式")
    interval_seconds = Column(Integer, comment="间隔秒数（interval类型）")
    
    # 执行配置
    task_module = Column(String(200), comment="任务模块")
    task_function = Column(String(100), comment="任务函数")
    task_args = Column(JSON, default={}, comment="任务参数")
    
    # 状态
    is_enabled = Column(Boolean, default=True)
    status = Column(String(20), default="idle", comment="idle/running/paused")
    
    # 执行统计
    last_run_at = Column(DateTime)
    last_run_result = Column(String(20), comment="success/failed")
    last_run_message = Column(Text)
    
    run_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    
    # 下次执行时间
    next_run_at = Column(DateTime)
    
    # 超时设置
    timeout_seconds = Column(Integer, default=3600, comment="超时时间")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID, ForeignKey("users.id"))


class TaskExecutionLog(Base):
    __tablename__ = "task_execution_logs"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID, ForeignKey("scheduled_tasks.id"))
    
    status = Column(String(20), comment="running/success/failed/timeout")
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer, comment="执行时长(毫秒)")
    
    result = Column(Text, comment="执行结果")
    error_message = Column(Text)
    
    celery_task_id = Column(String(100), comment="Celery任务ID")
```

## 3. 任务实现

### 3.1 月度凭证生成
```python
@celery.task(bind=True, max_retries=3)
def generate_monthly_vouchers(self, period: str = None):
    """自动生成月度凭证"""
    
    if not period:
        period = datetime.now().strftime("%Y-%m")
    
    try:
        # 获取所有客户
        customers = db.query(Customer).filter(Customer.status == "active").all()
        
        results = []
        for customer in customers:
            # 1. 获取未匹配但可自动匹配的流水
            unmatched_flows = db.query(BankFlow).filter(
                BankFlow.customer_id == customer.id,
                BankFlow.match_status == "unmatched",
                BankFlow.transaction_date.between(
                    get_period_start(period),
                    get_period_end(period)
                )
            ).all()
            
            for flow in unmatched_flows:
                # 2. 尝试自动匹配
                suggestions = match_flow_to_bill(flow)
                
                if suggestions and suggestions[0].score > 0.9:
                    # 自动确认匹配
                    confirm_match(flow.id, suggestions[0].bill_id)
            
            # 3. 根据匹配结果生成凭证
            vouchers = auto_generate_vouchers(customer.id, period)
            results.append({
                "customer": customer.name,
                "vouchers_created": len(vouchers)
            })
        
        return {
            "status": "success",
            "period": period,
            "results": results
        }
        
    except Exception as exc:
        # 重试
        self.retry(countdown=60, exc=exc)
```

### 3.2 结账提醒
```python
@celery.task
def send_closing_reminder():
    """发送结账提醒"""
    
    # 获取未结账的会计期间
    unclosed_periods = db.query(AccountingPeriod).filter(
        AccountingPeriod.status == "open",
        AccountingPeriod.end_date < datetime.now().date()
    ).all()
    
    for period in unclosed_periods:
        # 获取负责该客户的会计
        accountant_id = period.accounting_set.customer.assigned_accountant_id
        
        # 发送通知
        send_notification(
            user_id=accountant_id,
            title=f"【提醒】{period.period} 尚未结账",
            content=f"客户 {period.accounting_set.customer.name} 的 {period.period} 期间还未结账，请及时处理。",
            type="reminder",
            link=f"/accounting/{period.id}"
        )
```

### 3.3 数据清理
```python
@celery.task
def cleanup_old_data():
    """清理过期数据"""
    
    # 1. 清理操作日志（保留180天）
    cutoff_date = datetime.now() - timedelta(days=180)
    deleted_logs = db.query(OperationLog).filter(
        OperationLog.created_at < cutoff_date
    ).delete()
    
    # 2. 清理登录日志（保留90天）
    cutoff_date = datetime.now() - timedelta(days=90)
    deleted_login_logs = db.query(LoginLog).filter(
        LoginLog.created_at < cutoff_date
    ).delete()
    
    # 3. 清理临时文件
    temp_files = Path(TEMP_DIR).glob("*")
    week_ago = time.time() - 7 * 24 * 3600
    deleted_files = 0
    
    for file in temp_files:
        if file.stat().st_mtime < week_ago:
            file.unlink()
            deleted_files += 1
    
    # 4. 清理已删除的票据文件
    orphaned_files = find_orphaned_files()
    for file in orphaned_files:
        file.unlink()
    
    return {
        "deleted_logs": deleted_logs,
        "deleted_login_logs": deleted_login_logs,
        "deleted_temp_files": deleted_files,
        "deleted_orphaned_files": len(orphaned_files)
    }
```

## 4. Celery 配置

```python
# celery_config.py
from celery import Celery
from celery.signals import task_prerun, task_postrun

celery_app = Celery('smartledger')

celery_app.config_from_object({
    'broker_url': 'redis://localhost:6379/0',
    'result_backend': 'redis://localhost:6379/0',
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'Asia/Shanghai',
    'enable_utc': True,
    'beat_schedule': {},  # 动态从数据库加载
})

# 任务执行前后记录
@task_prerun.connect
def task_prerun_handler(signal, sender, task_id, task, args, kwargs):
    """任务开始执行"""
    # 查找对应的ScheduledTask
    scheduled_task = db.query(ScheduledTask).filter(
        ScheduledTask.task_function == task.name
    ).first()
    
    if scheduled_task:
        scheduled_task.status = "running"
        scheduled_task.run_count += 1
        db.commit()
        
        # 创建执行日志
        log = TaskExecutionLog(
            task_id=scheduled_task.id,
            status="running",
            celery_task_id=task_id
        )
        db.add(log)
        db.commit()

@task_postrun.connect
def task_postrun_handler(signal, sender, task_id, task, args, kwargs, retval, state):
    """任务执行完成"""
    log = db.query(TaskExecutionLog).filter(
        TaskExecutionLog.celery_task_id == task_id
    ).first()
    
    if log:
        log.status = state.lower()
        log.completed_at = datetime.utcnow()
        log.duration_ms = int((log.completed_at - log.started_at).total_seconds() * 1000)
        
        if state == "SUCCESS":
            log.result = str(retval)
        else:
            log.error_message = str(retval)
        
        db.commit()
        
        # 更新任务状态
        task_record = db.query(ScheduledTask).get(log.task_id)
        task_record.status = "idle"
        task_record.last_run_at = log.completed_at
        task_record.last_run_result = state.lower()
        
        if state == "SUCCESS":
            task_record.success_count += 1
        else:
            task_record.fail_count += 1
        
        db.commit()
```

## 5. 动态任务调度

```python
def load_schedules_from_db():
    """从数据库加载定时任务"""
    
    schedules = db.query(ScheduledTask).filter(
        ScheduledTask.is_enabled == True
    ).all()
    
    beat_schedule = {}
    
    for task in schedules:
        entry = {
            'task': task.task_function,
            'args': task.task_args.get('args', []),
            'kwargs': task.task_args.get('kwargs', {}),
        }
        
        if task.schedule_type == "cron":
            # 解析cron表达式
            parts = task.cron_expression.split()
            entry['schedule'] = crontab(
                minute=parts[0],
                hour=parts[1],
                day_of_month=parts[2],
                month_of_year=parts[3],
                day_of_week=parts[4]
            )
        elif task.schedule_type == "interval":
            entry['schedule'] = timedelta(seconds=task.interval_seconds)
        
        beat_schedule[task.name] = entry
        
        # 计算下次执行时间
        task.next_run_at = calculate_next_run(task)
    
    db.commit()
    
    # 更新Celery配置
    celery_app.conf.beat_schedule = beat_schedule
```

## 6. API 接口

```
GET    /api/v1/admin/scheduled-tasks        # 任务列表
POST   /api/v1/admin/scheduled-tasks        # 创建任务
PUT    /api/v1/admin/scheduled-tasks/{id}   # 更新任务
DELETE /api/v1/admin/scheduled-tasks/{id}   # 删除任务
POST   /api/v1/admin/scheduled-tasks/{id}/run      # 立即执行
POST   /api/v1/admin/scheduled-tasks/{id}/toggle   # 启用/禁用
GET    /api/v1/admin/scheduled-tasks/{id}/logs    # 执行日志
```

## 7. 前端任务监控

```
┌─────────────────────────────────────────────────────────────────┐
│  定时任务                                                      │
├─────────────────────────────────────────────────────────────────┤
│  [+ 新建任务]                                                   │
├─────────────────────────────────────────────────────────────────┤
│  任务名称 | 类型 | 调度 | 状态 | 上次执行 | 下次执行 | 操作   │
│  月度凭证生成 | 自动 | 每月1日 02:00 | ✅ | 成功 | 2024-04-01 | [执行][日志]│
│  结账提醒 | 自动 | 每天 09:00 | ✅ | 成功 | 明天 09:00 | [日志]│
│  数据清理 | 自动 | 每周日 03:00 | ⏸️ | 暂停 | - | [启用]│
└─────────────────────────────────────────────────────────────────┘
```

================================================================================
                              验收标准
================================================================================

1. [ ] 定时任务CRUD功能完整
2. [ ] Cron表达式解析正确
3. [ ] 任务按时自动执行
4. [ ] 执行日志记录完整
5. [ ] 任务失败自动重试
6. [ ] 手动执行任务正常
7. [ ] 任务状态监控正常
8. [ ] 任务超时控制正常

================================================================================
                              开发提示
================================================================================

1. 使用Flower监控Celery任务
2. 长时间任务使用进度条
3. 任务执行互斥（同一任务不能并发）
4. 失败任务发送告警通知
5. 考虑使用Redis分布式锁
