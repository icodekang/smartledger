# 任务编号：TASK-ADV-02
# 任务名称：数据备份恢复
# 优先级：P1
# 预估工期：1.5天
# 负责人：后端

================================================================================
                              任务描述
================================================================================

开发数据备份恢复功能，支持自动备份、手动备份、增量备份、一键恢复等。

================================================================================
                              需求详情
================================================================================

## 1. 备份类型

| 类型 | 说明 | 频率 | 保留 |
|------|------|------|------|
| 全量备份 | 完整数据库+文件 | 每周 | 4周 |
| 增量备份 | 自上次备份的变化 | 每日 | 7天 |
| 实时备份 | 关键表实时同步 | 持续 | - |
| 手动备份 | 用户触发 | 按需 | 永久 |

## 2. 数据模型

```python
class Backup(Base):
    __tablename__ = "backups"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    backup_type = Column(String(20), nullable=False, comment="full/incremental/manual")
    backup_scope = Column(String(20), default="all", comment="all/customer/tenant")
    scope_id = Column(UUID, comment="范围ID（如客户ID）")
    
    # 文件信息
    filename = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, default=0)
    checksum = Column(String(64), comment="MD5校验")
    
    # 内容统计
    db_size = Column(BigInteger, comment="数据库大小")
    file_count = Column(Integer, comment="文件数量")
    
    # 状态
    status = Column(String(20), default="running", comment="running/completed/failed")
    progress = Column(Integer, default=0, comment="进度%")
    
    # 时间
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime, comment="过期时间")
    
    # 操作人
    created_by = Column(UUID, ForeignKey("users.id"))
    
    # 恢复记录
    restore_count = Column(Integer, default=0)
    last_restored_at = Column(DateTime)


class BackupSchedule(Base):
    __tablename__ = "backup_schedules"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    name = Column(String(100), nullable=False)
    schedule_type = Column(String(20), default="cron", comment="cron/interval")
    cron_expression = Column(String(100), comment="Cron表达式")
    
    backup_type = Column(String(20), default="incremental")
    retention_days = Column(Integer, default=7)
    
    is_enabled = Column(Boolean, default=True)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
```

## 3. 备份实现

### 3.1 数据库备份
```python
@celery.task(bind=True)
def backup_database(self, backup_id: str, backup_type: str = "full"):
    """备份数据库"""
    
    backup = db.query(Backup).get(backup_id)
    backup.status = "running"
    db.commit()
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"db_{backup_type}_{timestamp}.sql.gz"
        filepath = f"/backups/{filename}"
        
        # 更新进度
        self.update_state(state="PROGRESS", meta={"progress": 10})
        
        # 执行pg_dump
        if backup_type == "full":
            command = f"pg_dump -h {DB_HOST} -U {DB_USER} -d {DB_NAME} | gzip > {filepath}"
        else:
            # 增量备份（使用WAL或时间戳）
            last_backup = get_last_backup_time()
            command = f"pg_dump -h {DB_HOST} -U {DB_USER} -d {DB_NAME} --data-only --inserts | gzip > {filepath}"
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"备份失败: {result.stderr}")
        
        self.update_state(state="PROGRESS", meta={"progress": 50})
        
        # 计算校验和
        checksum = calculate_md5(filepath)
        file_size = os.path.getsize(filepath)
        
        # 上传至对象存储（可选）
        if BACKUP_STORAGE == "s3":
            upload_to_s3(filepath, filename)
        
        # 更新备份记录
        backup.status = "completed"
        backup.filename = filename
        backup.file_path = filepath
        backup.file_size = file_size
        backup.checksum = checksum
        backup.completed_at = datetime.utcnow()
        db.commit()
        
        # 清理旧备份
        cleanup_old_backups(backup_type)
        
        return {"status": "completed", "file_size": file_size}
        
    except Exception as e:
        backup.status = "failed"
        backup.error_message = str(e)
        db.commit()
        raise
```

### 3.2 文件备份
```python
def backup_uploaded_files(backup_id: str):
    """备份上传的文件"""
    
    backup = db.query(Backup).get(backup_id)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"files_{timestamp}.tar.gz"
    filepath = f"/backups/{filename}"
    
    # 打包上传目录
    command = f"tar -czf {filepath} -C {UPLOAD_DIR} ."
    subprocess.run(command, shell=True, check=True)
    
    file_size = os.path.getsize(filepath)
    file_count = len(list(Path(UPLOAD_DIR).rglob("*")))
    
    backup.filename = filename
    backup.file_path = filepath
    backup.file_size = file_size
    backup.file_count = file_count
    db.commit()
```

## 4. 恢复实现

```python
@celery.task(bind=True)
def restore_backup(self, backup_id: str, target_schema: str = None):
    """恢复备份"""
    
    backup = db.query(Backup).get(backup_id)
    
    # 1. 校验备份文件
    if not os.path.exists(backup.file_path):
        raise Exception("备份文件不存在")
    
    current_checksum = calculate_md5(backup.file_path)
    if current_checksum != backup.checksum:
        raise Exception("备份文件校验失败，可能已损坏")
    
    self.update_state(state="PROGRESS", meta={"progress": 10, "message": "校验通过"})
    
    # 2. 创建恢复点（用于回滚）
    recovery_point = create_recovery_point()
    
    try:
        # 3. 恢复数据库
        if backup.filename.endswith('.sql.gz'):
            # 创建新schema或使用临时数据库
            if target_schema:
                db.execute(f"DROP SCHEMA IF EXISTS {target_schema} CASCADE")
                db.execute(f"CREATE SCHEMA {target_schema}")
            
            command = f"gunzip < {backup.file_path} | psql -h {DB_HOST} -U {DB_USER} -d {DB_NAME}"
            subprocess.run(command, shell=True, check=True)
        
        self.update_state(state="PROGRESS", meta={"progress": 60})
        
        # 4. 恢复文件
        if backup.filename.startswith('files_'):
            extract_path = f"/tmp/restore_{backup_id}"
            command = f"tar -xzf {backup.file_path} -C {extract_path}"
            subprocess.run(command, shell=True, check=True)
            
            # 复制文件到目标位置
            sync_files(extract_path, UPLOAD_DIR)
        
        self.update_state(state="PROGRESS", meta={"progress": 100})
        
        # 5. 更新恢复记录
        backup.restore_count += 1
        backup.last_restored_at = datetime.utcnow()
        db.commit()
        
        return {"status": "completed"}
        
    except Exception as e:
        # 回滚到恢复点
        rollback_to_recovery_point(recovery_point)
        raise
```

## 5. 定时调度

```python
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """设置定时备份任务"""
    
    # 每日凌晨2点增量备份
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        daily_backup.s(),
        name='daily-incremental-backup'
    )
    
    # 每周日凌晨3点全量备份
    sender.add_periodic_task(
        crontab(hour=3, minute=0, day_of_week=0),
        weekly_full_backup.s(),
        name='weekly-full-backup'
    )

@app.task
def daily_backup():
    """每日备份"""
    backup_id = create_backup_record("incremental")
    backup_database.delay(backup_id, "incremental")

@app.task
def weekly_full_backup():
    """每周全量备份"""
    backup_id = create_backup_record("full")
    backup_database.delay(backup_id, "full")
```

## 6. API 接口

```
GET    /api/v1/backups              # 备份列表
POST   /api/v1/backups              # 创建手动备份
GET    /api/v1/backups/{id}         # 备份详情
GET    /api/v1/backups/{id}/download # 下载备份
POST   /api/v1/backups/{id}/restore # 恢复备份
DELETE /api/v1/backups/{id}         # 删除备份

GET    /api/v1/backup-schedules     # 备份计划列表
POST   /api/v1/backup-schedules     # 创建计划
PUT    /api/v1/backup-schedules/{id}# 更新计划
```

================================================================================
                              验收标准
================================================================================

1. [ ] 全量备份功能正常
2. [ ] 增量备份功能正常
3. [ ] 手动备份功能正常
4. [ ] 定时备份自动执行
5. [ ] 备份文件校验正常
6. [ ] 恢复功能正常
7. [ ] 备份列表展示正常
8. [ ] 旧备份自动清理

================================================================================
                              开发提示
================================================================================

1. 备份文件异地存储（本地+云端）
2. 定期测试恢复流程
3. 大文件备份使用流式处理
4. 备份时避免锁表影响业务
5. 敏感备份文件加密存储
