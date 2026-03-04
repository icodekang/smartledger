# 数据库设计文档

## ER图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  customers  │────<│    bills    │>────│  vouchers   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │            ┌──────┴──────┐     ┌──────┴──────┐
       │            │ bank_flows  │     │voucher_items│
       │            └─────────────┘     └─────────────┘
       │
┌──────┴──────┐
│    users    │
└─────────────┘
```

## 表结构

### 1. customers（客户表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | VARCHAR(200) | 客户名称 |
| tax_no | VARCHAR(20) | 税号 |
| industry | VARCHAR(50) | 行业 |
| status | VARCHAR(20) | 状态 |

### 2. users（用户表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| username | VARCHAR(50) | 用户名 |
| password_hash | VARCHAR(255) | 密码哈希 |
| role | VARCHAR(20) | 角色 |
| is_active | BOOLEAN | 是否激活 |

### 3. bills（票据表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| customer_id | UUID | 客户ID |
| bill_type | VARCHAR(20) | 票据类型 |
| amount | DECIMAL | 金额 |
| status | VARCHAR(20) | 处理状态 |

### 4. vouchers（凭证表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| customer_id | UUID | 客户ID |
| voucher_no | VARCHAR(20) | 凭证号 |
| status | VARCHAR(20) | 状态 |

## 索引设计

- idx_bills_customer: bills(customer_id)
- idx_bills_status: bills(process_status)
- idx_vouchers_status: vouchers(status)
