#!/usr/bin/env python3
"""创建测试用户"""
import sys
sys.path.insert(0, '/app')

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
import hashlib

db = SessionLocal()
try:
    # 使用简单密码哈希
    password_hash = hashlib.sha256("TestPass1".encode()).hexdigest()
    
    test_user = User(
        username="testuser",
        password_hash=password_hash,
        name="测试用户",
        role="admin",
        is_active=True
    )
    db.add(test_user)
    db.commit()
    print("Test user created successfully")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
