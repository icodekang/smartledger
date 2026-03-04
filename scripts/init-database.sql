-- 初始化数据库脚本
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. 用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'viewer',
    phone VARCHAR(20),
    max_daily_capacity INT DEFAULT 50,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- 2. 客户表
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    tax_no VARCHAR(20) UNIQUE,
    industry VARCHAR(50),
    taxpayer_type VARCHAR(20),
    contact_name VARCHAR(100),
    contact_phone VARCHAR(20),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 票据表
CREATE TABLE IF NOT EXISTS bills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(id),
    bill_type VARCHAR(20),
    storage_path VARCHAR(500),
    ocr_result JSONB,
    ocr_confidence DECIMAL(3,2),
    invoice_code VARCHAR(20),
    invoice_number VARCHAR(20),
    invoice_date DATE,
    seller_name VARCHAR(200),
    amount DECIMAL(12,2),
    tax_amount DECIMAL(12,2),
    total_amount DECIMAL(12,2),
    process_status VARCHAR(20) DEFAULT 'pending',
    ai_confidence DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 凭证表
CREATE TABLE IF NOT EXISTS vouchers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(id),
    voucher_no VARCHAR(20),
    voucher_date DATE,
    summary TEXT,
    ai_confidence DECIMAL(3,2),
    status VARCHAR(20) DEFAULT 'draft',
    assigned_to UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 凭证明细表
CREATE TABLE IF NOT EXISTS voucher_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    voucher_id UUID REFERENCES vouchers(id) ON DELETE CASCADE,
    line_no INT,
    subject_code VARCHAR(20),
    subject_name VARCHAR(100),
    debit_amount DECIMAL(12,2) DEFAULT 0,
    credit_amount DECIMAL(12,2) DEFAULT 0
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_bills_customer ON bills(customer_id);
CREATE INDEX IF NOT EXISTS idx_bills_status ON bills(process_status);
CREATE INDEX IF NOT EXISTS idx_vouchers_status ON vouchers(status);
CREATE INDEX IF NOT EXISTS idx_vouchers_assigned ON vouchers(assigned_to, status);

-- 插入默认管理员用户 (密码: admin123)
INSERT INTO users (username, password_hash, name, role, is_active)
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I1K', '管理员', 'admin', TRUE)
ON CONFLICT (username) DO NOTHING;
