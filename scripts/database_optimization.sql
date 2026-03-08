-- 数据库性能优化 - 索引
-- 执行时间: 2024-03-07

-- 票据表索引
CREATE INDEX IF NOT EXISTS idx_bills_customer_status ON bills(customer_id, process_status);
CREATE INDEX IF NOT EXISTS idx_bills_created_at ON bills(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bills_invoice_date ON bills(invoice_date);
CREATE INDEX IF NOT EXISTS idx_bills_seller_name ON bills(seller_name);
CREATE INDEX IF NOT EXISTS idx_bills_customer_date_status ON bills(customer_id, invoice_date, process_status);

-- 凭证表索引
CREATE INDEX IF NOT EXISTS idx_vouchers_customer_status ON vouchers(customer_id, status);
CREATE INDEX IF NOT EXISTS idx_vouchers_period ON vouchers(period);
CREATE INDEX IF NOT EXISTS idx_vouchers_date ON vouchers(voucher_date);
CREATE INDEX IF NOT EXISTS idx_vouchers_assigned_status ON vouchers(assigned_to, status);

-- 银行流水表索引
CREATE INDEX IF NOT EXISTS idx_bank_flows_customer_date ON bank_flows(customer_id, transaction_date);
CREATE INDEX IF NOT EXISTS idx_bank_flows_match_status ON bank_flows(match_status);
CREATE INDEX IF NOT EXISTS idx_bank_flows_date_status ON bank_flows(transaction_date, status);

-- 用户表索引
CREATE INDEX IF NOT EXISTS idx_users_customer ON users(customer_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 分析表，更新统计信息
ANALYZE bills;
ANALYZE vouchers;
ANALYZE bank_flows;
