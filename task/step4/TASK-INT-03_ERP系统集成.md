# 任务编号：TASK-INT-03
# 任务名称：ERP系统集成
# 优先级：P1
# 预估工期：2天
# 负责人：后端

================================================================================
                              任务描述
================================================================================

实现与主流ERP系统（金蝶、用友、SAP等）的数据对接，支持科目同步、凭证导入、数据交换。

================================================================================
                              需求详情
================================================================================

## 1. 支持ERP系统

| ERP系统 | 对接方式 | 优先级 |
|---------|----------|--------|
| 金蝶K3/KIS | API/数据库直连 | P0 |
| 用友U8/T+ | API/数据库直连 | P0 |
| SAP | RFC/IDoc | P1 |
| 浪潮 | API | P1 |

## 2. 数据模型

```python
class ERPIntegration(Base):
    """ERP集成配置"""
    __tablename__ = "erp_integrations"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    erp_type = Column(String(50), nullable=False)  # kingdee/yonyou/sap
    erp_version = Column(String(50))
    
    # 连接配置
    connection_type = Column(String(20), default="api")  # api/database/file
    connection_config = Column(JSON)
    
    # 同步配置
    sync_direction = Column(String(20), default="bidirectional")  # to_erp/from_erp/bidirectional
    sync_schedule = Column(String(50), default="daily")
    
    # 科目映射
    subject_mapping = Column(JSON, default={})  # {erp_code: local_code}
    
    is_enabled = Column(Boolean, default=True)
    last_sync_at = Column(DateTime)
```

## 3. 金蝶K3对接实现

```python
class KingdeeK3Connector:
    """金蝶K3连接器"""
    
    def __init__(self, config: dict):
        self.server = config["server"]
        self.database = config["database"]
        self.username = config["username"]
        self.password = config["password"]
        
    def connect(self):
        """连接K3数据库"""
        import pymssql
        self.conn = pymssql.connect(
            server=self.server,
            database=self.database,
            user=self.username,
            password=self.password
        )
        return self.conn
    
    def export_vouchers(self, start_date: date, end_date: date) -> List[dict]:
        """从K3导出凭证"""
        
        cursor = self.conn.cursor(as_dict=True)
        
        query = """
        SELECT 
            v.FDate as voucher_date,
            v.FNumber as voucher_no,
            e.FExplanation as summary,
            a.FNumber as account_code,
            a.FName as account_name,
            e.FDebit as debit_amount,
            e.FCredit as credit_amount
        FROM t_Voucher v
        JOIN t_VoucherEntry e ON v.FVoucherID = e.FVoucherID
        JOIN t_Account a ON e.FAccountID = a.FAccountID
        WHERE v.FDate BETWEEN %s AND %s
        AND v.FPosted = 1
        ORDER BY v.FDate, v.FNumber, e.FEntryID
        """
        
        cursor.execute(query, (start_date, end_date))
        return cursor.fetchall()
    
    def import_vouchers(self, vouchers: List[Voucher]):
        """导入凭证到K3"""
        
        cursor = self.conn.cursor()
        
        for voucher in vouchers:
            # 生成K3凭证号
            k3_voucher_no = self._generate_voucher_no(voucher.voucher_date)
            
            # 插入凭证头
            cursor.execute("""
                INSERT INTO t_Voucher (FDate, FNumber, FPeriod, FExplanation, FPosted)
                VALUES (%s, %s, %s, %s, 0)
            """, (
                voucher.voucher_date,
                k3_voucher_no,
                voucher.voucher_date.month,
                voucher.summary
            ))
            
            voucher_id = cursor.lastrowid
            
            # 插入凭证明细
            for idx, item in enumerate(voucher.items, 1):
                k3_account_code = self._map_subject_code(item.subject_code)
                
                cursor.execute("""
                    INSERT INTO t_VoucherEntry 
                    (FVoucherID, FEntryID, FAccountID, FExplanation, FDebit, FCredit)
                    SELECT %s, %s, a.FAccountID, %s, %s, %s
                    FROM t_Account a
                    WHERE a.FNumber = %s
                """, (
                    voucher_id,
                    idx,
                    item.summary,
                    item.debit_amount or 0,
                    item.credit_amount or 0,
                    k3_account_code
                ))
        
        self.conn.commit()
```

## 4. 科目映射

```python
class SubjectMappingService:
    """科目映射服务"""
    
    def __init__(self, customer_id: str, erp_type: str):
        self.customer_id = customer_id
        self.erp_type = erp_type
        self.mapping = self._load_mapping()
    
    def _load_mapping(self) -> dict:
        """加载科目映射"""
        integration = db.query(ERPIntegration).filter(
            ERPIntegration.customer_id == self.customer_id,
            ERPIntegration.erp_type == self.erp_type
        ).first()
        
        return integration.subject_mapping if integration else {}
    
    def to_erp_code(self, local_code: str) -> str:
        """转换为ERP科目代码"""
        reverse_mapping = {v: k for k, v in self.mapping.items()}
        return reverse_mapping.get(local_code, local_code)
    
    def to_local_code(self, erp_code: str) -> str:
        """转换为本地科目代码"""
        return self.mapping.get(erp_code, erp_code)
    
    def auto_match(self, erp_subjects: List[dict], local_subjects: List[dict]) -> dict:
        """自动匹配科目"""
        
        mapping = {}
        
        for erp_subj in erp_subjects:
            best_match = None
            best_score = 0
            
            for local_subj in local_subjects:
                score = self._calculate_similarity(erp_subj, local_subj)
                if score > best_score and score > 0.8:
                    best_score = score
                    best_match = local_subj
            
            if best_match:
                mapping[erp_subj["code"]] = best_match["code"]
        
        return mapping
    
    def _calculate_similarity(self, erp_subj: dict, local_subj: dict) -> float:
        """计算科目相似度"""
        
        from difflib import SequenceMatcher
        
        # 名称相似度
        name_sim = SequenceMatcher(
            None, 
            erp_subj["name"], 
            local_subj["name"]
        ).ratio()
        
        # 如果代码相同，增加权重
        code_sim = 1.0 if erp_subj["code"] == local_subj["code"] else 0.0
        
        # 分类相同增加权重
        category_sim = 1.0 if erp_subj.get("category") == local_subj.get("category") else 0.0
        
        return name_sim * 0.6 + code_sim * 0.3 + category_sim * 0.1
```

## 5. API 接口

```
POST   /api/v1/erp-integrations              # 创建集成配置
PUT    /api/v1/erp-integrations/{id}         # 更新配置
DELETE /api/v1/erp-integrations/{id}         # 删除配置
POST   /api/v1/erp-integrations/{id}/test    # 测试连接
POST   /api/v1/erp-integrations/{id}/sync    # 执行同步
GET    /api/v1/erp-integrations/{id}/subjects # 获取ERP科目列表
POST   /api/v1/erp-integrations/{id}/mapping  # 保存科目映射
```

## 6. 同步任务

```python
@celery.task
def sync_erp_data(integration_id: str, sync_type: str = "voucher"):
    """同步ERP数据"""
    
    integration = db.query(ERPIntegration).get(integration_id)
    
    if integration.erp_type == "kingdee":
        connector = KingdeeK3Connector(integration.connection_config)
    elif integration.erp_type == "yonyou":
        connector = YonyouU8Connector(integration.connection_config)
    
    connector.connect()
    
    if sync_type == "voucher":
        # 导出ERP凭证
        start_date = integration.last_sync_at or datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        erp_vouchers = connector.export_vouchers(start_date, end_date)
        
        # 转换并导入
        for erp_voucher in erp_vouchers:
            local_voucher = convert_erp_voucher(erp_voucher, integration)
            db.add(local_voucher)
    
    elif sync_type == "subject":
        # 同步科目
        erp_subjects = connector.export_subjects()
        
        # 自动匹配
        local_subjects = get_local_subjects(integration.customer_id)
        mapping = SubjectMappingService(
            integration.customer_id, 
            integration.erp_type
        ).auto_match(erp_subjects, local_subjects)
        
        integration.subject_mapping = mapping
    
    integration.last_sync_at = datetime.utcnow()
    db.commit()
```

================================================================================
                              验收标准
================================================================================

1. [ ] 金蝶K3对接正常
2. [ ] 用友U8对接正常
3. [ ] 科目自动匹配准确率>80%
4. [ ] 凭证双向同步正常
5. [ ] 数据格式转换正确
6. [ ] 同步日志记录完整

================================================================================
                              开发提示
================================================================================

1. ERP版本差异大，需要兼容处理
2. 数据库直连需客户开放权限
3. 建议客户使用独立只读账号
4. 同步前做好数据备份
5. 异常数据人工确认机制
