from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, date
import uuid

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.permissions import require_permission
from app.models.erp_integration import ERPIntegration
from app.services.erp_connector import ERPConnectorFactory, SubjectMappingService

router = APIRouter(prefix="/erp-integrations", tags=["ERP集成"])


class ERPIntegrationCreateRequest(BaseModel):
    erp_type: str
    erp_version: Optional[str] = None
    connection_type: str = "api"
    connection_config: dict = {}
    sync_direction: str = "bidirectional"
    sync_schedule: str = "daily"


class SubjectMappingRequest(BaseModel):
    mapping: dict


# 获取支持的ERP系统
@router.get("/supported-erps")
async def get_supported_erps(
    current_user=Depends(require_permission("erp:read"))
):
    """获取支持的ERP系统列表"""
    erps = ERPConnectorFactory.get_supported_erps()
    return success_response(data={"items": erps})


# 创建ERP集成配置
@router.post("")
async def create_erp_integration(
    request: ERPIntegrationCreateRequest,
    current_user=Depends(require_permission("erp:manage")),
    db: Session = Depends(get_db)
):
    """创建ERP集成配置"""
    # 检查是否已存在
    exists = db.query(ERPIntegration).filter(
        ERPIntegration.customer_id == current_user.customer_id,
        ERPIntegration.erp_type == request.erp_type,
        ERPIntegration.is_enabled == True
    ).first()
    
    if exists:
        return error_response(400, "该ERP系统已配置")
    
    integration = ERPIntegration(
        id=uuid.uuid4(),
        customer_id=current_user.customer_id,
        erp_type=request.erp_type,
        erp_version=request.erp_version,
        connection_type=request.connection_type,
        connection_config=request.connection_config,
        sync_direction=request.sync_direction,
        sync_schedule=request.sync_schedule,
        subject_mapping={},
        is_enabled=True,
        connection_status="disconnected"
    )
    
    db.add(integration)
    db.commit()
    db.refresh(integration)
    
    return success_response(data={
        "id": str(integration.id),
        "message": "ERP集成配置创建成功"
    })


# 获取ERP集成列表
@router.get("")
async def list_erp_integrations(
    current_user=Depends(require_permission("erp:read")),
    db: Session = Depends(get_db)
):
    """获取ERP集成列表"""
    integrations = db.query(ERPIntegration).filter(
        ERPIntegration.customer_id == current_user.customer_id,
        ERPIntegration.is_enabled == True
    ).all()
    
    items = []
    for integration in integrations:
        items.append({
            "id": str(integration.id),
            "erp_type": integration.erp_type,
            "erp_version": integration.erp_version,
            "connection_type": integration.connection_type,
            "sync_direction": integration.sync_direction,
            "sync_schedule": integration.sync_schedule,
            "connection_status": integration.connection_status,
            "last_sync_at": integration.last_sync_at.isoformat() if integration.last_sync_at else None,
            "created_at": integration.created_at.isoformat() if integration.created_at else None
        })
    
    return success_response(data={"items": items})


# 测试连接
@router.post("/{integration_id}/test")
async def test_connection(
    integration_id: str,
    current_user=Depends(require_permission("erp:manage")),
    db: Session = Depends(get_db)
):
    """测试ERP连接"""
    integration = db.query(ERPIntegration).filter(
        ERPIntegration.id == integration_id,
        ERPIntegration.customer_id == current_user.customer_id
    ).first()
    
    if not integration:
        return error_response(404, "ERP集成配置不存在")
    
    try:
        connector = ERPConnectorFactory.get_connector(
            integration.erp_type,
            integration.connection_config
        )
        
        success = connector.test_connection()
        
        integration.connection_status = "connected" if success else "error"
        db.commit()
        
        return success_response(data={
            "success": success,
            "message": "连接成功" if success else "连接失败"
        })
    except Exception as e:
        integration.connection_status = "error"
        db.commit()
        return error_response(500, f"连接测试失败: {str(e)}")


# 获取ERP科目列表
@router.get("/{integration_id}/subjects")
async def get_erp_subjects(
    integration_id: str,
    current_user=Depends(require_permission("erp:read")),
    db: Session = Depends(get_db)
):
    """获取ERP科目列表"""
    integration = db.query(ERPIntegration).filter(
        ERPIntegration.id == integration_id,
        ERPIntegration.customer_id == current_user.customer_id
    ).first()
    
    if not integration:
        return error_response(404, "ERP集成配置不存在")
    
    try:
        connector = ERPConnectorFactory.get_connector(
            integration.erp_type,
            integration.connection_config
        )
        
        subjects = connector.get_subjects()
        
        items = []
        for subj in subjects:
            items.append({
                "code": subj.code,
                "name": subj.name,
                "category": subj.category
            })
        
        return success_response(data={"items": items})
    except Exception as e:
        return error_response(500, f"获取科目失败: {str(e)}")


# 自动匹配科目
@router.post("/{integration_id}/auto-match")
async def auto_match_subjects(
    integration_id: str,
    current_user=Depends(require_permission("erp:manage")),
    db: Session = Depends(get_db)
):
    """自动匹配科目"""
    integration = db.query(ERPIntegration).filter(
        ERPIntegration.id == integration_id,
        ERPIntegration.customer_id == current_user.customer_id
    ).first()
    
    if not integration:
        return error_response(404, "ERP集成配置不存在")
    
    try:
        # 获取ERP科目
        connector = ERPConnectorFactory.get_connector(
            integration.erp_type,
            integration.connection_config
        )
        erp_subjects = connector.get_subjects()
        
        # 获取本地科目（从之前的API）
        local_subjects = [
            {"code": "1001", "name": "库存现金"},
            {"code": "1002", "name": "银行存款"},
            {"code": "1122", "name": "应收账款"},
            {"code": "1403", "name": "原材料"},
            {"code": "1405", "name": "库存商品"},
            {"code": "1601", "name": "固定资产"},
            {"code": "2001", "name": "短期借款"},
            {"code": "2202", "name": "应付账款"},
            {"code": "2221", "name": "应交税费"},
            {"code": "4001", "name": "实收资本"},
            {"code": "6001", "name": "主营业务收入"},
            {"code": "6401", "name": "主营业务成本"},
            {"code": "6601", "name": "销售费用"},
            {"code": "6602", "name": "管理费用"},
            {"code": "6603", "name": "财务费用"},
        ]
        
        # 自动匹配
        mapping = SubjectMappingService.auto_match(erp_subjects, local_subjects)
        
        # 保存映射
        integration.subject_mapping = mapping
        db.commit()
        
        return success_response(data={
            "mapping": mapping,
            "matched_count": len(mapping),
            "message": f"成功匹配 {len(mapping)} 个科目"
        })
    except Exception as e:
        return error_response(500, f"自动匹配失败: {str(e)}")


# 保存科目映射
@router.post("/{integration_id}/mapping")
async def save_subject_mapping(
    integration_id: str,
    request: SubjectMappingRequest,
    current_user=Depends(require_permission("erp:manage")),
    db: Session = Depends(get_db)
):
    """保存科目映射"""
    integration = db.query(ERPIntegration).filter(
        ERPIntegration.id == integration_id,
        ERPIntegration.customer_id == current_user.customer_id
    ).first()
    
    if not integration:
        return error_response(404, "ERP集成配置不存在")
    
    integration.subject_mapping = request.mapping
    db.commit()
    
    return success_response(data={"message": "科目映射保存成功"})


# 同步数据
@router.post("/{integration_id}/sync")
async def sync_erp_data(
    integration_id: str,
    sync_type: str = "voucher",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user=Depends(require_permission("erp:manage")),
    db: Session = Depends(get_db)
):
    """同步ERP数据"""
    integration = db.query(ERPIntegration).filter(
        ERPIntegration.id == integration_id,
        ERPIntegration.customer_id == current_user.customer_id
    ).first()
    
    if not integration:
        return error_response(404, "ERP集成配置不存在")
    
    if integration.connection_status != "connected":
        return error_response(400, "ERP未连接")
    
    try:
        connector = ERPConnectorFactory.get_connector(
            integration.erp_type,
            integration.connection_config
        )
        
        if sync_type == "voucher":
            # 凭证同步
            if not start_date:
                start_date = integration.last_sync_at.date() if integration.last_sync_at else date.today()
            if not end_date:
                end_date = date.today()
            
            erp_vouchers = connector.export_vouchers(start_date, end_date)
            
            # 更新同步记录
            integration.last_sync_at = datetime.utcnow()
            integration.last_sync_result = {
                "sync_type": sync_type,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "count": len(erp_vouchers)
            }
            db.commit()
            
            return success_response(data={
                "sync_type": sync_type,
                "count": len(erp_vouchers),
                "message": f"成功同步 {len(erp_vouchers)} 条凭证"
            })
        
        elif sync_type == "subject":
            # 科目同步
            erp_subjects = connector.get_subjects()
            
            return success_response(data={
                "sync_type": sync_type,
                "count": len(erp_subjects),
                "message": f"成功同步 {len(erp_subjects)} 个科目"
            })
        
        else:
            return error_response(400, f"不支持的同步类型: {sync_type}")
    
    except Exception as e:
        return error_response(500, f"同步失败: {str(e)}")


# 删除ERP集成
@router.delete("/{integration_id}")
async def delete_erp_integration(
    integration_id: str,
    current_user=Depends(require_permission("erp:manage")),
    db: Session = Depends(get_db)
):
    """删除ERP集成配置"""
    integration = db.query(ERPIntegration).filter(
        ERPIntegration.id == integration_id,
        ERPIntegration.customer_id == current_user.customer_id
    ).first()
    
    if not integration:
        return error_response(404, "ERP集成配置不存在")
    
    integration.is_enabled = False
    db.commit()
    
    return success_response(data={"message": "ERP集成配置已删除"})
