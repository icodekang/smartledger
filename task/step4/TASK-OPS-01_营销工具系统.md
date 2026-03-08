# 任务编号：TASK-OPS-01
# 任务名称：营销工具系统
# 优先级：P1
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发营销工具系统，支持优惠券、推荐返利、限时活动等，帮助平台获客和留存。

================================================================================
                              需求详情
================================================================================

## 1. 优惠券系统

### 1.1 数据模型
```python
class Coupon(Base):
    """优惠券"""
    __tablename__ = "coupons"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    coupon_code = Column(String(20), unique=True, nullable=False)
    coupon_name = Column(String(100), nullable=False)
    coupon_type = Column(String(20), nullable=False)  # amount/discount/percent
    
    # 优惠金额
    discount_amount = Column(Numeric(10, 2))  # 直减金额
    discount_percent = Column(Numeric(5, 2))  # 折扣比例
    max_discount = Column(Numeric(10, 2))     # 最高优惠
    
    # 使用门槛
    min_order_amount = Column(Numeric(10, 2), default=0)
    
    # 有效期
    valid_start = Column(DateTime)
    valid_end = Column(DateTime)
    
    # 发放限制
    total_quantity = Column(Integer)
    remaining_quantity = Column(Integer)
    per_user_limit = Column(Integer, default=1)
    
    # 适用范围
    applicable_scope = Column(String(20), default="all")  # all/new_customer/specific_plan
    applicable_plans = Column(JSON, default=[])
    
    is_active = Column(Boolean, default=True)


class UserCoupon(Base):
    """用户优惠券"""
    __tablename__ = "user_coupons"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    coupon_id = Column(UUID, ForeignKey("coupons.id"))
    
    status = Column(String(20), default="unused")  # unused/used/expired
    used_at = Column(DateTime)
    used_order_id = Column(UUID)
    
    received_at = Column(DateTime, default=datetime.utcnow)
    valid_end = Column(DateTime)
```

### 1.2 优惠券发放
```python
@app.post("/api/v1/coupons/{id}/claim")
def claim_coupon(coupon_id: str, user: User = Depends(get_current_user)):
    """领取优惠券"""
    
    coupon = db.query(Coupon).get(coupon_id)
    
    # 检查库存
    if coupon.remaining_quantity <= 0:
        raise HTTPException(400, "优惠券已领完")
    
    # 检查用户领取次数
    claimed_count = db.query(UserCoupon).filter(
        UserCoupon.user_id == user.id,
        UserCoupon.coupon_id == coupon_id
    ).count()
    
    if claimed_count >= coupon.per_user_limit:
        raise HTTPException(400, "您已达到领取上限")
    
    # 检查新用户专享
    if coupon.applicable_scope == "new_customer":
        order_count = db.query(Order).filter(
            Order.user_id == user.id,
            Order.status == "paid"
        ).count()
        if order_count > 0:
            raise HTTPException(400, "该优惠券仅限新用户")
    
    # 发放优惠券
    user_coupon = UserCoupon(
        user_id=user.id,
        coupon_id=coupon_id,
        valid_end=coupon.valid_end
    )
    db.add(user_coupon)
    
    coupon.remaining_quantity -= 1
    db.commit()
    
    return {"code": 200, "message": "领取成功"}
```

### 1.3 优惠券使用
```python
def apply_coupon(order_amount: Decimal, coupon: UserCoupon) -> Decimal:
    """应用优惠券计算折扣"""
    
    # 检查最低消费
    if order_amount < coupon.coupon.min_order_amount:
        raise ValueError("订单金额未达到优惠券使用门槛")
    
    # 计算优惠
    if coupon.coupon.coupon_type == "amount":
        discount = coupon.coupon.discount_amount
    elif coupon.coupon.coupon_type == "percent":
        discount = order_amount * (coupon.coupon.discount_percent / 100)
        if coupon.coupon.max_discount:
            discount = min(discount, coupon.coupon.max_discount)
    
    return order_amount - discount
```

## 2. 推荐返利

```python
class ReferralProgram(Base):
    """推荐计划"""
    __tablename__ = "referral_programs"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    referrer_id = Column(UUID, ForeignKey("users.id"))
    referee_id = Column(UUID, ForeignKey("users.id"))
    
    referral_code = Column(String(20))
    
    # 奖励
    referrer_reward = Column(Numeric(10, 2), default=0)
    referee_reward = Column(Numeric(10, 2), default=0)
    
    # 状态
    status = Column(String(20), default="pending")  # pending/completed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


@app.post("/api/v1/referrals")
def create_referral(data: ReferralCreate, user: User = Depends(get_current_user)):
    """创建推荐关系"""
    
    # 生成推荐码
    referral_code = generate_referral_code(user.id)
    
    # 被推荐人注册时使用推荐码
    # 首次付费后发放奖励
    
    return {"referral_code": referral_code, "share_url": f"https://sl.ai/r/{referral_code}"}


# 被推荐人注册
def process_referral_reward(referral_code: str, new_user_id: str):
    """处理推荐奖励"""
    
    referral = db.query(ReferralProgram).filter(
        ReferralProgram.referral_code == referral_code
    ).first()
    
    if referral:
        referral.referee_id = new_user_id
        db.commit()
        
        # 被推荐人获得注册奖励
        give_reward(new_user_id, referral.referee_reward, "注册奖励")


# 被推荐人首次付费
def complete_referral(new_user_id: str):
    """完成推荐"""
    
    referral = db.query(ReferralProgram).filter(
        ReferralProgram.referee_id == new_user_id,
        ReferralProgram.status == "pending"
    ).first()
    
    if referral:
        referral.status = "completed"
        referral.completed_at = datetime.utcnow()
        
        # 推荐人获得奖励
        give_reward(referral.referrer_id, referral.referrer_reward, "推荐奖励")
        
        db.commit()
```

## 3. 限时活动

```python
class Promotion(Base):
    """营销活动"""
    __tablename__ = "promotions"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    name = Column(String(100), nullable=False)
    promotion_type = Column(String(20))  # flash_sale/bundle/flash_discount
    
    # 活动时间
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    
    # 活动内容
    content = Column(JSON)  # 根据类型不同结构不同
    
    is_active = Column(Boolean, default=True)


# 限时折扣示例
flash_sale = {
    "plan_id": "uuid",
    "original_price": 500,
    "sale_price": 300,
    "quantity_limit": 100
}
```

## 4. API接口

```
GET    /api/v1/coupons/available             # 可领取优惠券
POST   /api/v1/coupons/{id}/claim            # 领取优惠券
GET    /api/v1/user/coupons                  # 我的优惠券
POST   /api/v1/orders/{id}/apply-coupon      # 使用优惠券

POST   /api/v1/referrals                     # 创建推荐
GET    /api/v1/referrals/stats               # 推荐统计
GET    /api/v1/referrals/rewards             # 奖励记录

GET    /api/v1/promotions                    # 营销活动
GET    /api/v1/promotions/current            # 当前活动
```

## 5. 前端页面

```
┌─────────────────────────────────────────────────────────────────┐
│  优惠券中心                                                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 🔥 新用户专享                                               ││
│  │ ¥100 无门槛优惠券                                           ││
│  │ 有效期至: 2024-12-31                                       ││
│  │                          [立即领取]                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 满减券                                                      ││
│  │ 满500减50                                                   ││
│  │ 剩余: 50张                                                  ││
│  │                          [领取]                            ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

================================================================================
                              验收标准
================================================================================

1. [ ] 优惠券创建/发放正常
2. [ ] 优惠券使用计算正确
3. [ ] 推荐码生成/追踪正常
4. [ ] 奖励发放准确
5. [ ] 营销活动可配置
6. [ ] 库存扣减准确

================================================================================
                              开发提示
================================================================================

1. 优惠券使用要有幂等性
2. 并发领取要加锁
3. 过期优惠券自动清理
4. 防止刷券（IP/设备限制）
5. 营销活动数据统计
