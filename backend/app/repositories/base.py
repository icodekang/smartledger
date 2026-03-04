from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from fastapi import HTTPException

from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """通用Repository基类"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """根据ID获取"""
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_or_404(self, db: Session, id: Any) -> ModelType:
        """获取或抛出404"""
        obj = self.get(db, id)
        if not obj:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found")
        return obj
    
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: dict = None,
        order_by: str = None,
        order: str = "desc"
    ) -> List[ModelType]:
        """查询列表"""
        query = db.query(self.model)
        
        # 应用过滤
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.filter(getattr(self.model, key) == value)
        
        # 排序
        if order_by and hasattr(self.model, order_by):
            order_func = desc if order == "desc" else asc
            query = query.order_by(order_func(getattr(self.model, order_by)))
        else:
            query = query.order_by(desc(self.model.created_at))
        
        return query.offset(skip).limit(limit).all()
    
    def count(self, db: Session, filters: dict = None) -> int:
        """统计数量"""
        query = db.query(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.count()
    
    def create(self, db: Session, *, obj_in: dict) -> ModelType:
        """创建"""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, *, db_obj: ModelType, obj_in: dict) -> ModelType:
        """更新"""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, id: Any) -> ModelType:
        """删除"""
        obj = self.get_or_404(db, id)
        db.delete(obj)
        db.commit()
        return obj


class PaginatedResponse:
    """分页响应"""
    def __init__(self, items: List[Any], total: int, page: int, page_size: int):
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = (total + page_size - 1) // page_size
    
    def to_dict(self):
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages
        }
