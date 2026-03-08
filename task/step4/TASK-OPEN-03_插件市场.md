# 任务编号：TASK-OPEN-03
# 任务名称：插件市场
# 优先级：P1
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发插件市场系统，支持第三方开发者开发插件，用户可安装使用，扩展系统功能。

================================================================================
                              需求详情
================================================================================

## 1. 插件类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 数据导入 | 从特定系统导入数据 | 淘宝订单导入 |
| 报表模板 | 自定义报表 | 行业专用报表 |
| 功能扩展 | 扩展系统功能 | 批量开票 |
| 集成对接 | 对接第三方服务 | 物流查询 |

## 2. 数据模型

```python
class Plugin(Base):
    """插件"""
    __tablename__ = "plugins"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # 基本信息
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(500))
    version = Column(String(20), default="1.0.0")
    
    # 开发者
    developer_id = Column(UUID, ForeignKey("users.id"))
    developer_name = Column(String(100))
    
    # 类型和价格
    plugin_type = Column(String(50))  # importer/report/extension/integration
    price = Column(Numeric(10, 2), default=0)  # 0表示免费
    
    # 状态
    status = Column(String(20), default="pending")  # pending/approved/rejected
    
    # 文件
    package_url = Column(String(500))  # 插件包下载地址
    manifest = Column(JSON)  # 插件配置信息
    
    # 统计
    download_count = Column(Integer, default=0)
    rating = Column(Numeric(3, 2), default=5.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class PluginInstance(Base):
    """插件实例（安装记录）"""
    __tablename__ = "plugin_instances"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    plugin_id = Column(UUID, ForeignKey("plugins.id"))
    customer_id = Column(UUID, ForeignKey("customers.id"))
    
    # 配置
    config = Column(JSON, default={})
    
    # 状态
    is_enabled = Column(Boolean, default=True)
    installed_at = Column(DateTime, default=datetime.utcnow)
```

## 3. 插件开发规范

```json
// manifest.json 示例
{
  "name": "淘宝订单导入",
  "version": "1.0.0",
  "description": "自动导入淘宝订单数据",
  "type": "importer",
  "author": "开发者A",
  "entry": "index.js",
  "permissions": ["read:bills", "write:bills"],
  "config": {
    "fields": [
      {
        "name": "app_key",
        "label": "App Key",
        "type": "text",
        "required": true
      },
      {
        "name": "app_secret",
        "label": "App Secret",
        "type": "password",
        "required": true
      }
    ]
  },
  "hooks": {
    "onInstall": "install",
    "onUninstall": "uninstall",
    "onDataImport": "importData"
  }
}
```

## 4. 插件管理

```python
class PluginManager:
    """插件管理器"""
    
    def install(self, plugin_id: str, customer_id: str, config: dict):
        """安装插件"""
        
        plugin = db.query(Plugin).get(plugin_id)
        
        # 检查权限
        if plugin.price > 0:
            # 检查是否已购买
            if not has_purchased(customer_id, plugin_id):
                raise HTTPException(403, "请先购买插件")
        
        # 创建实例
        instance = PluginInstance(
            plugin_id=plugin_id,
            customer_id=customer_id,
            config=config
        )
        db.add(instance)
        db.commit()
        
        # 调用安装钩子
        self._call_hook(plugin, "onInstall", config)
        
        return instance
    
    def execute(self, instance_id: str, action: str, data: dict):
        """执行插件功能"""
        
        instance = db.query(PluginInstance).get(instance_id)
        
        # 加载插件代码（沙箱执行）
        plugin_code = self._load_plugin_code(instance.plugin)
        
        # 沙箱执行
        result = self._sandbox_execute(plugin_code, action, data, instance.config)
        
        return result
    
    def _sandbox_execute(self, code: str, action: str, data: dict, config: dict):
        """沙箱执行插件代码"""
        
        # 使用受限Python执行环境
        import restrictedpython
        
        # 定义允许的操作
        allowed_globals = {
            "__import__": self._safe_import,
            "requests": safe_requests,
            "json": json,
            "datetime": datetime
        }
        
        # 执行
        compiled = compile_restricted(code, '<plugin>', 'exec')
        exec(compiled, allowed_globals)
        
        # 调用指定函数
        handler = allowed_globals.get(action)
        if handler:
            return handler(data, config)
        
        return None
```

## 5. 插件市场前端

```
┌─────────────────────────────────────────────────────────────────┐
│  插件市场                                          [开发者入口]  │
├─────────────────────────────────────────────────────────────────┤
│  分类: [全部] [数据导入] [报表] [工具] [集成]                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 🔥 淘宝订单导入                              免费   [安装] ││
│  │ 自动同步淘宝订单，生成记账凭证                               ││
│  │ 下载: 1,234  评分: ⭐4.8                                     ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ 📊 餐饮成本分析报表                          ¥99    [购买] ││
│  │ 餐饮行业专用成本分析报表模板                                 ││
│  │ 下载: 567    评分: ⭐4.5                                     ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ 🚚 快递批量查询                              免费   [安装] ││
│  │ 批量查询快递物流信息                                         ││
│  │ 下载: 2,890  评分: ⭐4.9                                     ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## 6. API接口

```
GET    /api/v1/plugins/market              # 插件市场
GET    /api/v1/plugins/{id}                # 插件详情
POST   /api/v1/plugins/{id}/install        # 安装插件
DELETE /api/v1/plugins/instances/{id}      # 卸载插件

POST   /api/v1/plugins                     # 提交插件（开发者）
PUT    /api/v1/plugins/{id}                # 更新插件
GET    /api/v1/developer/plugins           # 我的插件
GET    /api/v1/plugins/instances           # 已安装插件
```

================================================================================
                              验收标准
================================================================================

1. [ ] 插件提交/审核流程
2. [ ] 插件安装/卸载正常
3. [ ] 沙箱执行安全
4. [ ] 插件配置保存
5. [ ] 付费插件购买
6. [ ] 下载统计准确

================================================================================
                              开发提示
================================================================================

1. 插件代码严格沙箱执行
2. 敏感操作需用户确认
3. 插件版本管理
4. 兼容性问题处理
5. 开发者文档完善
