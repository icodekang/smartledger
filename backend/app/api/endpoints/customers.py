from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, date
from sqlalchemy import func
import uuid

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.permissions import require_permission
from app.models.customer import Customer
from app.models.customer_ext import CustomerContact, CustomerAddress, CustomerInvoiceInfo

router = APIRouter(prefix="/customers", tags=["客户管理"])


# ============== 请求模型 ==============

class CustomerCreateRequest(BaseModel):
    name: str
    short_name: Optional[str] = None
    company_type: Optional[str] = None
    industry: Optional[str] = None
    scale: Optional[str] = None
    tax_no: Optional[str] = None
    tax_type: Optional[str] = "一般纳税人"
    phone: Optional[str] = None
    email: Optional[str] = None
    fax: Optional[str] = None
    website: Optional[str] = None
    service_start_date: Optional[date] = None
    service_end_date: Optional[date] = None
    assigned_accountant_id: Optional[str] = None
    remark: Optional[str] = None


class CustomerUpdateRequest(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    company_type: Optional[str] = None
    industry: Optional[str] = None
    scale: Optional[str] = None
    tax_no: Optional[str] = None
    tax_type: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    fax: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = None
    service_start_date: Optional[date] = None
    service_end_date: Optional[date] = None
    assigned_accountant_id: Optional[str] = None
    remark: Optional[str] = None


class ContactCreateRequest(BaseModel):
    name: str
    title: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    tel: Optional[str] = None
    email: Optional[str] = None
    wechat: Optional[str] = None
    is_primary: bool = False
    remark: Optional[str] = None


class AddressCreateRequest(BaseModel):
    address_type: str
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    detail: Optional[str] = None
    postcode: Optional[str] = None
    is_primary: bool = False


class InvoiceInfoCreateRequest(BaseModel):
    title: str
    tax_no: str
    address: Optional[str] = None
    phone: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    is_default: bool = True


# ============== 辅助函数 ==============

def generate_customer_code(db: Session) -> str:
    """生成客户编码: C + 年份 + 4位序号"""
    year = datetime.now().strftime("%Y")
    
    # 查询当年最大序号
    from sqlalchemy import func
    result = db.query(func.max(Customer.code)).filter(
        Customer.code.like(f"C{year}%")
    ).scalar()
    
    if result:
        seq = int(result[5:]) + 1
    else:
        seq = 1
    
    return f"C{year}{seq:04d}"


# ============== API 接口 ==============

@router.get("")
async def list_customers(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态"),
    industry: Optional[str] = Query(None, description="行业"),
    assigned_accountant_id: Optional[str] = Query(None, description="负责会计"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_permission("customers:read")),
    db: Session = Depends(get_db)
):
    """客户列表查询"""
    from sqlalchemy import or_
    
    query = db.query(Customer)
    
    # 筛选条件
    if keyword:
        query = query.filter(
            or_(
                Customer.name.ilike(f"%{keyword}%"),
                Customer.code.ilike(f"%{keyword}%"),
                Customer.tax_no.ilike(f"%{keyword}%")
            )
        )
    
    if status:
        query = query.filter(Customer.status == status)
    
    if industry:
        query = query.filter(Customer.industry == industry)
    
    if assigned_accountant_id:
        query = query.filter(Customer.assigned_accountant_id == assigned_accountant_id)
    
    # 统计
    total = query.count()
    active_count = query.filter(Customer.status == "active").count()
    inactive_count = query.filter(Customer.status == "inactive").count()
    
    # 即将到期（30天内）
    from datetime import timedelta
    deadline = datetime.now() + timedelta(days=30)
    expiring_soon = query.filter(
        Customer.service_end_date <= deadline,
        Customer.service_end_date >= datetime.now(),
        Customer.status == "active"
    ).count()
    
    # 分页查询
    customers = query.order_by(Customer.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    # 构建响应
    items = []
    for c in customers:
        items.append({
            "id": str(c.id),
            "code": c.code,
            "name": c.name,
            "short_name": c.short_name,
            "tax_no": c.tax_no,
            "phone": c.phone,
            "status": c.status,
            "industry": c.industry,
            "assigned_accountant_id": str(c.assigned_accountant_id) if c.assigned_accountant_id else None,
            "service_end_date": c.service_end_date.isoformat() if c.service_end_date else None,
            "created_at": c.created_at.isoformat() if c.created_at else ""
        })
    
    return success_response(data={
        "items": items,
        "total": total,
        "summary": {
            "active_count": active_count,
            "inactive_count": inactive_count,
            "expiring_soon": expiring_soon
        }
    })


@router.post("")
async def create_customer(
    request: CustomerCreateRequest,
    current_user=Depends(require_permission("customers:create")),
    db: Session = Depends(get_db)
):
    """创建客户"""
    # 生成客户编码
    code = generate_customer_code(db)
    
    customer = Customer(
        id=str(uuid.uuid4()),
        code=code,
        name=request.name,
        short_name=request.short_name,
        company_type=request.company_type,
        industry=request.industry,
        scale=request.scale,
        tax_no=request.tax_no,
        tax_type=request.tax_type or "一般纳税人",
        phone=request.phone,
        email=request.email,
        fax=request.fax,
        website=request.website,
        service_start_date=request.service_start_date,
        service_end_date=request.service_end_date,
        assigned_accountant_id=request.assigned_accountant_id,
        remark=request.remark,
        status="active",
        created_by=current_user.id
    )
    
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return success_response(data={
        "id": str(customer.id),
        "code": customer.code,
        "message": "客户创建成功"
    })


@router.get("/{customer_id}")
async def get_customer_detail(
    customer_id: str,
    current_user=Depends(require_permission("customers:read")),
    db: Session = Depends(get_db)
):
    """获取客户详情"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return error_response(404, "客户不存在")
    
    # 联系人
    contacts = []
    for c in customer.contacts:
        contacts.append({
            "id": str(c.id),
            "name": c.name,
            "title": c.title,
            "department": c.department,
            "phone": c.phone,
            "tel": c.tel,
            "email": c.email,
            "wechat": c.wechat,
            "is_primary": c.is_primary,
            "is_enabled": c.is_enabled
        })
    
    # 地址
    addresses = []
    for a in customer.addresses:
        addresses.append({
            "id": str(a.id),
            "address_type": a.address_type,
            "province": a.province,
            "city": a.city,
            "district": a.district,
            "detail": a.detail,
            "postcode": a.postcode,
            "is_primary": a.is_primary
        })
    
    # 开票信息
    invoice_infos = []
    for i in customer.invoice_infos:
        invoice_infos.append({
            "id": str(i.id),
            "title": i.title,
            "tax_no": i.tax_no,
            "address": i.address,
            "phone": i.phone,
            "bank_name": i.bank_name,
            "bank_account": i.bank_account,
            "is_default": i.is_default
        })
    
    # 统计信息
    from app.models.bill import Bill
    from app.models.voucher import Voucher
    
    total_bills = db.query(Bill).filter(Bill.customer_id == customer_id).count()
    total_vouchers = db.query(Voucher).filter(Voucher.customer_id == customer_id).count()
    
    return success_response(data={
        "id": str(customer.id),
        "code": customer.code,
        "name": customer.name,
        "short_name": customer.short_name,
        "company_type": customer.company_type,
        "industry": customer.industry,
        "scale": customer.scale,
        "tax_no": customer.tax_no,
        "tax_type": customer.tax_type,
        "phone": customer.phone,
        "email": customer.email,
        "fax": customer.fax,
        "website": customer.website,
        "status": customer.status,
        "service_start_date": customer.service_start_date.isoformat() if customer.service_start_date else None,
        "service_end_date": customer.service_end_date.isoformat() if customer.service_end_date else None,
        "assigned_accountant_id": str(customer.assigned_accountant_id) if customer.assigned_accountant_id else None,
        "remark": customer.remark,
        "contacts": contacts,
        "addresses": addresses,
        "invoice_infos": invoice_infos,
        "statistics": {
            "total_bills": total_bills,
            "total_vouchers": total_vouchers
        }
    })


@router.put("/{customer_id}")
async def update_customer(
    customer_id: str,
    request: CustomerUpdateRequest,
    current_user=Depends(require_permission("customers:update")),
    db: Session = Depends(get_db)
):
    """更新客户"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return error_response(404, "客户不存在")
    
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    
    for key, value in update_data.items():
        setattr(customer, key, value)
    
    db.commit()
    
    return success_response(data={"message": "客户更新成功"})


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: str,
    current_user=Depends(require_permission("customers:delete")),
    db: Session = Depends(get_db)
):
    """删除客户（仅允许删除无关联数据的客户）"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return error_response(404, "客户不存在")
    
    # 检查关联数据
    from app.models.bill import Bill
    from app.models.voucher import Voucher
    
    bill_count = db.query(Bill).filter(Bill.customer_id == customer_id).count()
    if bill_count > 0:
        return error_response(400, f"该客户存在 {bill_count} 张票据，无法删除")
    
    voucher_count = db.query(Voucher).filter(Voucher.customer_id == customer_id).count()
    if voucher_count > 0:
        return error_response(400, f"该客户存在 {voucher_count} 张凭证，无法删除")
    
    db.delete(customer)
    db.commit()
    
    return success_response(data={"message": "客户删除成功"})


# ============== 联系人管理 ==============

@router.post("/{customer_id}/contacts")
async def add_contact(
    customer_id: str,
    request: ContactCreateRequest,
    current_user=Depends(require_permission("customers:update")),
    db: Session = Depends(get_db)
):
    """添加联系人"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return error_response(404, "客户不存在")
    
    contact = CustomerContact(
        id=uuid.uuid4(),
        customer_id=customer_id,
        name=request.name,
        title=request.title,
        department=request.department,
        phone=request.phone,
        tel=request.tel,
        email=request.email,
        wechat=request.wechat,
        is_primary=request.is_primary,
        remark=request.remark
    )
    
    db.add(contact)
    db.commit()
    
    return success_response(data={"id": str(contact.id), "message": "联系人添加成功"})


@router.delete("/contacts/{contact_id}")
async def delete_contact(
    contact_id: str,
    current_user=Depends(require_permission("customers:update")),
    db: Session = Depends(get_db)
):
    """删除联系人"""
    contact = db.query(CustomerContact).filter(CustomerContact.id == contact_id).first()
    if not contact:
        return error_response(404, "联系人不存在")
    
    db.delete(contact)
    db.commit()
    
    return success_response(data={"message": "联系人删除成功"})


# ============== 地址管理 ==============

@router.post("/{customer_id}/addresses")
async def add_address(
    customer_id: str,
    request: AddressCreateRequest,
    current_user=Depends(require_permission("customers:update")),
    db: Session = Depends(get_db)
):
    """添加地址"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return error_response(404, "客户不存在")
    
    address = CustomerAddress(
        id=uuid.uuid4(),
        customer_id=customer_id,
        address_type=request.address_type,
        province=request.province,
        city=request.city,
        district=request.district,
        detail=request.detail,
        postcode=request.postcode,
        is_primary=request.is_primary
    )
    
    db.add(address)
    db.commit()
    
    return success_response(data={"id": str(address.id), "message": "地址添加成功"})


@router.delete("/addresses/{address_id}")
async def delete_address(
    address_id: str,
    current_user=Depends(require_permission("customers:update")),
    db: Session = Depends(get_db)
):
    """删除地址"""
    address = db.query(CustomerAddress).filter(CustomerAddress.id == address_id).first()
    if not address:
        return error_response(404, "地址不存在")
    
    db.delete(address)
    db.commit()
    
    return success_response(data={"message": "地址删除成功"})


# ============== 开票信息管理 ==============

@router.post("/{customer_id}/invoice-infos")
async def add_invoice_info(
    customer_id: str,
    request: InvoiceInfoCreateRequest,
    current_user=Depends(require_permission("customers:update")),
    db: Session = Depends(get_db)
):
    """添加开票信息"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return error_response(404, "客户不存在")
    
    info = CustomerInvoiceInfo(
        id=uuid.uuid4(),
        customer_id=customer_id,
        title=request.title,
        tax_no=request.tax_no,
        address=request.address,
        phone=request.phone,
        bank_name=request.bank_name,
        bank_account=request.bank_account,
        is_default=request.is_default
    )
    
    db.add(info)
    db.commit()
    
    return success_response(data={"id": str(info.id), "message": "开票信息添加成功"})


@router.delete("/invoice-infos/{info_id}")
async def delete_invoice_info(
    info_id: str,
    current_user=Depends(require_permission("customers:update")),
    db: Session = Depends(get_db)
):
    """删除开票信息"""
    info = db.query(CustomerInvoiceInfo).filter(CustomerInvoiceInfo.id == info_id).first()
    if not info:
        return error_response(404, "开票信息不存在")
    
    db.delete(info)
    db.commit()
    
    return success_response(data={"message": "开票信息删除成功"})
