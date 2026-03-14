#!/usr/bin/env python3
"""
SmartLedger 测试数据初始化脚本
用于创建测试所需的各类数据，以便运行完整的测试用例
"""
import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

class TestDataGenerator:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.headers = {}
        self.customers = []
        self.contracts = []
        self.invoices = []
        self.vouchers = []
        self.bank_accounts = []
        self.bank_flows = []
        
    def login(self, username="testadmin", password="Test123456"):
        """登录获取 token"""
        try:
            resp = self.session.post(
                f"{API_URL}/auth/login",
                data={"username": username, "password": password}
            )
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data.get("data", {}).get("access_token")
                self.headers = {"Authorization": f"Bearer {self.access_token}"}
                print(f"✅ 登录成功")
                return True
            else:
                print(f"❌ 登录失败: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False
    
    def get(self, endpoint, **kwargs):
        return self.session.get(f"{API_URL}{endpoint}", headers=self.headers, **kwargs)
    
    def post(self, endpoint, **kwargs):
        return self.session.post(f"{API_URL}{endpoint}", headers=self.headers, **kwargs)
    
    def put(self, endpoint, **kwargs):
        return self.session.put(f"{API_URL}{endpoint}", headers=self.headers, **kwargs)
    
    def delete(self, endpoint, **kwargs):
        return self.session.delete(f"{API_URL}{endpoint}", headers=self.headers, **kwargs)

    def create_customers(self):
        """创建测试客户"""
        print("\n📋 创建测试客户...")
        customers_data = [
            {"name": "阿里巴巴（中国）有限公司", "tax_id": "91330000MA2H4XXX1X", "contact": "马云", "phone": "13800138001", "address": "杭州市余杭区", "customer_type": "enterprise"},
            {"name": "腾讯科技（深圳）有限公司", "tax_id": "91440300MA5DXXX2X", "contact": "马化腾", "phone": "13800138002", "address": "深圳市南山区", "customer_type": "enterprise"},
            {"name": "字节跳动科技有限公司", "tax_id": "91110108MA4AXXX3X", "contact": "张一鸣", "phone": "13800138003", "address": "北京市海淀区", "customer_type": "enterprise"},
            {"name": "京东科技控股股份有限公司", "tax_id": "91110000MA5EXXX4X", "contact": "刘强东", "phone": "13800138004", "address": "北京市亦庄", "customer_type": "enterprise"},
            {"name": "美团网络科技有限公司", "tax_id": "91110000MA5FXXX5X", "contact": "王兴", "phone": "13800138005", "address": "北京市朝阳区", "customer_type": "enterprise"},
        ]
        
        for customer_data in customers_data:
            try:
                resp = self.post("/customers", json=customer_data)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    customer_id = data.get("data", {}).get("id") or data.get("id")
                    if customer_id:
                        self.customers.append(customer_id)
                        print(f"  ✅ 客户创建成功: {customer_data['name']} (ID: {customer_id})")
                    else:
                        print(f"  ⚠️ 客户创建响应无ID: {data}")
                else:
                    print(f"  ❌ 客户创建失败: {resp.status_code} - {resp.text[:100]}")
            except Exception as e:
                print(f"  ❌ 客户创建异常: {e}")
        
        print(f"  共创建 {len(self.customers)} 个客户")
        return self.customers

    def create_contracts(self):
        """创建测试合同"""
        print("\n📄 创建测试合同...")
        if not self.customers:
            print("  ⚠️ 无客户数据，跳过合同创建")
            return []
        
        contracts_data = [
            {"customer_id": self.customers[0], "name": "2024年度服务合同", "contract_no": "CT2024001", "amount": 1000000, "start_date": "2024-01-01", "end_date": "2024-12-31", "status": "active"},
            {"customer_id": self.customers[0], "name": "云服务合同", "contract_no": "CT2024002", "amount": 500000, "start_date": "2024-03-01", "end_date": "2025-02-28", "status": "active"},
            {"customer_id": self.customers[1], "name": "软件开发合同", "contract_no": "CT2024003", "amount": 800000, "start_date": "2024-02-01", "end_date": "2024-11-30", "status": "active"},
            {"customer_id": self.customers[1], "name": "运维服务合同", "contract_no": "CT2024004", "amount": 300000, "start_date": "2024-01-01", "end_date": "2024-06-30", "status": "active"},
            {"customer_id": self.customers[2], "name": "广告推广合同", "contract_no": "CT2024005", "amount": 1200000, "start_date": "2024-04-01", "end_date": "2025-03-31", "status": "active"},
        ]
        
        for contract_data in contracts_data:
            try:
                resp = self.post("/contracts", json=contract_data)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    contract_id = data.get("data", {}).get("id") or data.get("id")
                    if contract_id:
                        self.contracts.append(contract_id)
                        print(f"  ✅ 合同创建成功: {contract_data['name']} (ID: {contract_id})")
                    else:
                        print(f"  ⚠️ 合同创建响应无ID: {data}")
                else:
                    print(f"  ❌ 合同创建失败: {resp.status_code} - {resp.text[:100]}")
            except Exception as e:
                print(f"  ❌ 合同创建异常: {e}")
        
        print(f"  共创建 {len(self.contracts)} 个合同")
        return self.contracts

    def create_invoices(self):
        """创建测试票据"""
        print("\n🧾 创建测试票据...")
        if not self.customers:
            print("  ⚠️ 无客户数据，跳过票据创建")
            return []
        
        invoices_data = [
            {"customer_id": self.customers[0], "invoice_no": "INV20240001", "amount": 113000, "tax_amount": 13000, "invoice_type": "vat_special", "status": "issued", "issue_date": "2024-01-15"},
            {"customer_id": self.customers[0], "invoice_no": "INV20240002", "amount": 56500, "tax_amount": 6500, "invoice_type": "vat_special", "status": "issued", "issue_date": "2024-02-20"},
            {"customer_id": self.customers[1], "invoice_no": "INV20240003", "amount": 226000, "tax_amount": 26000, "invoice_type": "vat_special", "status": "issued", "issue_date": "2024-03-10"},
            {"customer_id": self.customers[1], "invoice_no": "INV20240004", "amount": 339000, "tax_amount": 39000, "invoice_type": "vat_special", "status": "issued", "issue_date": "2024-04-05"},
            {"customer_id": self.customers[2], "invoice_no": "INV20240005", "amount": 452000, "tax_amount": 52000, "invoice_type": "vat_special", "status": "issued", "issue_date": "2024-05-12"},
            {"customer_id": self.customers[2], "invoice_no": "INV20240006", "amount": 169000, "tax_amount": 19000, "invoice_type": "vat_special", "status": "draft", "issue_date": "2024-06-01"},
            {"customer_id": self.customers[3], "invoice_no": "INV20240007", "amount": 678000, "tax_amount": 78000, "invoice_type": "vat_special", "status": "issued", "issue_date": "2024-06-15"},
            {"customer_id": self.customers[4], "invoice_no": "INV20240008", "amount": 890000, "tax_amount": 90000, "invoice_type": "vat_special", "status": "issued", "issue_date": "2024-07-20"},
        ]
        
        for invoice_data in invoices_data:
            try:
                resp = self.post("/invoices", json=invoice_data)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    invoice_id = data.get("data", {}).get("id") or data.get("id")
                    if invoice_id:
                        self.invoices.append(invoice_id)
                        print(f"  ✅ 票据创建成功: {invoice_data['invoice_no']} (ID: {invoice_id})")
                    else:
                        print(f"  ⚠️ 票据创建响应无ID: {data}")
                else:
                    print(f"  ❌ 票据创建失败: {resp.status_code} - {resp.text[:100]}")
            except Exception as e:
                print(f"  ❌ 票据创建异常: {e}")
        
        print(f"  共创建 {len(self.invoices)} 张票据")
        return self.invoices

    def create_vouchers(self):
        """创建测试凭证"""
        print("\n📒 创建测试凭证...")
        if not self.customers:
            print("  ⚠️ 无客户数据，跳过凭证创建")
            return []
        
        vouchers_data = [
            {"customer_id": self.customers[0], "voucher_no": "VZ20240101", "voucher_date": "2024-01-31", "amount": 113000, "voucher_type": "receipt", "status": "approved", "description": "收到服务费"},
            {"customer_id": self.customers[0], "voucher_no": "VZ20240102", "voucher_date": "2024-02-28", "amount": 56500, "voucher_type": "receipt", "status": "approved", "description": "收到咨询费"},
            {"customer_id": self.customers[1], "voucher_no": "VZ20240301", "voucher_date": "2024-03-31", "amount": 226000, "voucher_type": "receipt", "status": "approved", "description": "收到开发费"},
            {"customer_id": self.customers[1], "voucher_no": "VZ20240401", "voucher_date": "2024-04-30", "amount": 339000, "voucher_type": "receipt", "status": "draft", "description": "收到维护费"},
            {"customer_id": self.customers[2], "voucher_no": "VZ20240501", "voucher_date": "2024-05-31", "amount": 452000, "voucher_type": "payment", "status": "approved", "description": "支付广告费"},
            {"customer_id": self.customers[3], "voucher_no": "VZ20240601", "voucher_date": "2024-06-30", "amount": 678000, "voucher_type": "receipt", "status": "approved", "description": "收到货款"},
        ]
        
        for voucher_data in vouchers_data:
            try:
                resp = self.post("/vouchers", json=voucher_data)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    voucher_id = data.get("data", {}).get("id") or data.get("id")
                    if voucher_id:
                        self.vouchers.append(voucher_id)
                        print(f"  ✅ 凭证创建成功: {voucher_data['voucher_no']} (ID: {voucher_id})")
                    else:
                        print(f"  ⚠️ 凭证创建响应无ID: {data}")
                else:
                    print(f"  ❌ 凭证创建失败: {resp.status_code} - {resp.text[:100]}")
            except Exception as e:
                print(f"  ❌ 凭证创建异常: {e}")
        
        print(f"  共创建 {len(self.vouchers)} 张凭证")
        return self.vouchers

    def create_bank_accounts(self):
        """创建测试银行账户"""
        print("\n🏦 创建测试银行账户...")
        if not self.customers:
            print("  ⚠️ 无客户数据，跳过银行账户创建")
            return []
        
        accounts_data = [
            {"customer_id": self.customers[0], "account_name": "阿里巴巴（中国）有限公司", "account_no": "1234567890", "bank_name": "中国工商银行", "account_type": "basic", "balance": 1000000},
            {"customer_id": self.customers[0], "account_name": "阿里巴巴（中国）有限公司", "account_no": "1234567891", "bank_name": "中国建设银行", "account_type": "general", "balance": 500000},
            {"customer_id": self.customers[1], "account_name": "腾讯科技（深圳）有限公司", "account_no": "2345678901", "bank_name": "招商银行", "account_type": "basic", "balance": 2000000},
            {"customer_id": self.customers[2], "account_name": "字节跳动科技有限公司", "account_no": "3456789012", "bank_name": "中国银行", "account_type": "basic", "balance": 1500000},
            {"customer_id": self.customers[3], "account_name": "京东科技控股股份有限公司", "account_no": "4567890123", "bank_name": "中国农业银行", "account_type": "general", "balance": 800000},
        ]
        
        for account_data in accounts_data:
            try:
                resp = self.post("/bank-accounts", json=account_data)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    account_id = data.get("data", {}).get("id") or data.get("id")
                    if account_id:
                        self.bank_accounts.append(account_id)
                        print(f"  ✅ 银行账户创建成功: {account_data['account_no']} (ID: {account_id})")
                    else:
                        print(f"  ⚠️ 银行账户创建响应无ID: {data}")
                else:
                    print(f"  ❌ 银行账户创建失败: {resp.status_code} - {resp.text[:100]}")
            except Exception as e:
                print(f"  ❌ 银行账户创建异常: {e}")
        
        print(f"  共创建 {len(self.bank_accounts)} 个银行账户")
        return self.bank_accounts

    def create_bank_flows(self):
        """创建测试银行流水"""
        print("\n💸 创建测试银行流水...")
        if not self.bank_accounts:
            print("  ⚠️ 无银行账户数据，跳过银行流水创建")
            return []
        
        flows_data = [
            {"account_id": self.bank_accounts[0], "flow_no": "BF20240101001", "amount": 113000, "flow_type": "income", "flow_date": "2024-01-15", "description": "收到服务费"},
            {"account_id": self.bank_accounts[0], "flow_no": "BF20240102001", "amount": -50000, "flow_type": "expense", "flow_date": "2024-01-20", "description": "采购办公用品"},
            {"account_id": self.bank_accounts[0], "flow_no": "BF20240201001", "amount": 56500, "flow_type": "income", "flow_date": "2024-02-20", "description": "收到咨询费"},
            {"account_id": self.bank_accounts[1], "flow_no": "BF20240301001", "amount": 226000, "flow_type": "income", "flow_date": "2024-03-10", "description": "收到开发费"},
            {"account_id": self.bank_accounts[2], "flow_no": "BF20240401001", "amount": 339000, "flow_type": "income", "flow_date": "2024-04-05", "description": "收到维护费"},
            {"account_id": self.bank_accounts[2], "flow_no": "BF20240402001", "amount": -100000, "flow_type": "expense", "flow_date": "2024-04-15", "description": "支付工资"},
            {"account_id": self.bank_accounts[3], "flow_no": "BF20240501001", "amount": 452000, "flow_type": "income", "flow_date": "2024-05-12", "description": "收到广告费"},
            {"account_id": self.bank_accounts[4], "flow_no": "BF20240601001", "amount": 678000, "flow_type": "income", "flow_date": "2024-06-15", "description": "收到货款"},
        ]
        
        for flow_data in flows_data:
            try:
                resp = self.post("/bank-flows", json=flow_data)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    flow_id = data.get("data", {}).get("id") or data.get("id")
                    if flow_id:
                        self.bank_flows.append(flow_id)
                        print(f"  ✅ 银行流水创建成功: {flow_data['flow_no']} (ID: {flow_id})")
                    else:
                        print(f"  ⚠️ 银行流水创建响应无ID: {data}")
                else:
                    print(f"  ❌ 银行流水创建失败: {resp.status_code} - {resp.text[:100]}")
            except Exception as e:
                print(f"  ❌ 银行流水创建异常: {e}")
        
        print(f"  共创建 {len(self.bank_flows)} 条银行流水")
        return self.bank_flows

    def create_audit_tasks(self):
        """创建测试审核任务"""
        print("\n✅ 创建测试审核任务...")
        
        # 创建一些待审核的发票
        if self.invoices:
            # 尝试提交审核
            try:
                for invoice_id in self.invoices[:3]:
                    resp = self.post(f"/invoices/{invoice_id}/submit")
                    if resp.status_code in [200, 201]:
                        print(f"  ✅ 发票提交审核成功: {invoice_id}")
                    else:
                        print(f"  ⚠️ 发票提交审核: {resp.status_code} - {resp.text[:100]}")
            except Exception as e:
                print(f"  ❌ 提交审核异常: {e}")
        
        # 创建一些待审核的凭证
        if self.vouchers:
            try:
                for voucher_id in self.vouchers[:3]:
                    resp = self.post(f"/vouchers/{voucher_id}/submit")
                    if resp.status_code in [200, 201]:
                        print(f"  ✅ 凭证提交审核成功: {voucher_id}")
                    else:
                        print(f"  ⚠️ 凭证提交审核: {resp.status_code} - {resp.text[:100]}")
            except Exception as e:
                print(f"  ❌ 提交审核异常: {e}")
        
        print("  审核任务创建完成")
        return True

    def run(self):
        """执行所有数据创建"""
        print("="*60)
        print("SmartLedger 测试数据初始化")
        print("="*60)
        
        if not self.login():
            print("❌ 登录失败，无法创建测试数据")
            return False
        
        # 创建各类测试数据
        self.create_customers()
        self.create_contracts()
        self.create_invoices()
        self.create_vouchers()
        self.create_bank_accounts()
        self.create_bank_flows()
        self.create_audit_tasks()
        
        # 保存测试数据摘要
        summary = {
            "test_data": {
                "customers": self.customers,
                "contracts": self.contracts,
                "invoices": self.invoices,
                "vouchers": self.vouchers,
                "bank_accounts": self.bank_accounts,
                "bank_flows": self.bank_flows
            },
            "timestamp": datetime.now().isoformat()
        }
        
        print("\n" + "="*60)
        print("测试数据创建完成")
        print("="*60)
        print(f"客户: {len(self.customers)} 个")
        print(f"合同: {len(self.contracts)} 个")
        print(f"票据: {len(self.invoices)} 张")
        print(f"凭证: {len(self.vouchers)} 张")
        print(f"银行账户: {len(self.bank_accounts)} 个")
        print(f"银行流水: {len(self.bank_flows)} 条")
        
        # 保存摘要
        with open("task/test_data_summary.json", "w") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return True

if __name__ == "__main__":
    generator = TestDataGenerator()
    generator.run()
