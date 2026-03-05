-- scripts/init_chart_of_accounts.sql
-- 小企业会计准则科目表

-- 资产类
INSERT INTO account_subjects (code, name, category, direction) VALUES
('1001', '库存现金', 'asset', 'debit'),
('1002', '银行存款', 'asset', 'debit'),
('1012', '其他货币资金', 'asset', 'debit'),
('1101', '交易性金融资产', 'asset', 'debit'),
('1121', '应收票据', 'asset', 'debit'),
('1122', '应收账款', 'asset', 'debit'),
('1123', '预付账款', 'asset', 'debit'),
('1131', '应收股利', 'asset', 'debit'),
('1132', '应收利息', 'asset', 'debit'),
('1221', '其他应收款', 'asset', 'debit'),
('1401', '材料采购', 'asset', 'debit'),
('1403', '原材料', 'asset', 'debit'),
('1405', '库存商品', 'asset', 'debit'),
('1511', '长期股权投资', 'asset', 'debit'),
('1601', '固定资产', 'asset', 'debit'),
('1602', '累计折旧', 'asset', 'credit'),
('1701', '无形资产', 'asset', 'debit'),
('1801', '长期待摊费用', 'asset', 'debit');

-- 负债类
INSERT INTO account_subjects (code, name, category, direction) VALUES
('2001', '短期借款', 'liability', 'credit'),
('2201', '应付票据', 'liability', 'credit'),
('2202', '应付账款', 'liability', 'credit'),
('2203', '预收账款', 'liability', 'credit'),
('2211', '应付职工薪酬', 'liability', 'credit'),
('2221', '应交税费', 'liability', 'credit'),
('2231', '应付利息', 'liability', 'credit'),
('2232', '应付股利', 'liability', 'credit'),
('2241', '其他应付款', 'liability', 'credit'),
('2501', '长期借款', 'liability', 'credit');

-- 权益类
INSERT INTO account_subjects (code, name, category, direction) VALUES
('3001', '实收资本', 'equity', 'credit'),
('3002', '资本公积', 'equity', 'credit'),
('3101', '盈余公积', 'equity', 'credit'),
('3103', '本年利润', 'equity', 'credit'),
('3104', '利润分配', 'equity', 'credit');

-- 成本类
INSERT INTO account_subjects (code, name, category, direction) VALUES
('4001', '生产成本', 'cost', 'debit'),
('4101', '制造费用', 'cost', 'debit'),
('4301', '研发支出', 'cost', 'debit');

-- 损益类-收入
INSERT INTO account_subjects (code, name, category, direction) VALUES
('5001', '主营业务收入', 'income', 'credit'),
('5051', '其他业务收入', 'income', 'credit'),
('5111', '投资收益', 'income', 'credit'),
('5301', '营业外收入', 'income', 'credit');

-- 损益类-费用
INSERT INTO account_subjects (code, name, category, direction) VALUES
('5401', '主营业务成本', 'expense', 'debit'),
('5402', '其他业务成本', 'expense', 'debit'),
('5403', '税金及附加', 'expense', 'debit'),
('5601', '销售费用', 'expense', 'debit'),
('5602', '管理费用', 'expense', 'debit'),
('5603', '财务费用', 'expense', 'debit'),
('5711', '营业外支出', 'expense', 'debit'),
('5801', '所得税费用', 'expense', 'debit');

-- 管理费用明细
INSERT INTO account_subjects (code, name, parent_code, category, direction) VALUES
('560201', '办公费', '5602', 'expense', 'debit'),
('560202', '差旅费', '5602', 'expense', 'debit'),
('560203', '业务招待费', '5602', 'expense', 'debit'),
('560204', '工资', '5602', 'expense', 'debit'),
('560205', '社保费', '5602', 'expense', 'debit'),
('560206', '折旧费', '5602', 'expense', 'debit'),
('560207', '水电费', '5602', 'expense', 'debit'),
('560208', '房租', '5602', 'expense', 'debit'),
('560209', '通讯费', '5602', 'expense', 'debit'),
('560210', '培训费', '5602', 'expense', 'debit');

-- 应交税费明细
INSERT INTO account_subjects (code, name, parent_code, category, direction) VALUES
('222101', '应交增值税-进项税额', '2221', 'liability', 'credit'),
('222102', '应交增值税-销项税额', '2221', 'liability', 'credit'),
('222103', '应交增值税-已交税金', '2221', 'liability', 'credit');
