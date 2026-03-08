#!/usr/bin/env python3
"""初始化数据库表结构"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace/smartledger/backend')

from app.core.database import engine, Base
from app.models import Base, User, Customer, Bill, Voucher, VoucherItem, BankFlow, AccountSubject

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")

# 创建测试用户
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()
try:
    # 检查是否已有用户
    existing = db.query(User).filter(User.username == "testuser").first()
    if not existing:
        test_user = User(
            username="testuser",
            password_hash=pwd_context.hash("TestPass123"),
            name="测试用户",
            role="admin",
            is_active=True
        )
        db.add(test_user)
        db.commit()
        print("Test user created: testuser / TestPass123")
    else:
        print("Test user already exists")
finally:
    db.close()
