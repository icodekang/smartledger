#!/usr/bin/env python3
"""
SmartLedger 测试数据初始化脚本 V2
修正了字段名称以匹配实际API
"""
import requests
import json
import time
from datetime import datetime, date, timedelta

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
            {"name": "阿里巴巴（中国）有限公司", "tax_id": "91330000MA2H4XXX1X", "contact": "马云", "phone": "13800138001", "address": "杭州市余杭区"},
            {"name": "腾讯科技（深圳）有限公司", "tax_id": "91440300MA5DXXX2X", "contact": "马化腾", "phone": "13800138002", "address": "深圳市南山区"},
            {"name": "字节跳动科技有限公司", "tax_id": "91110108MA4AXXX3X", "contact": "张一鸣", "phone": "13800138003", "address": "北京市海淀区"},
            {"name": "京东科技控股股份有限公司", "tax_id": "91110000MA5EXXX4X", "contact": "刘强东", "phone": "13800138004", "address": "北京市亦庄"},
            {"name": "美团网络科技有限公司", "tax_id": "91110000MA5FXXX5X", "contact": "王兴", "phone": "13800138005", "address": "北京市朝阳区"},
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
        
        # 合同需要通过 /contracts/customer/{customer_id} 创建
        for i, customer_id in enumerate(self.customers[:3]):
            contracts_data = [
                {"contract_name": "2024年度服务合同", "start_date": "2024-01-01", "end_date": "2024-12-31", "service_type": "service", "billing_amount": 100000, "billing_cycle": "monthly"},
                {"contract_name": "云服务合同", "start_date": "2024-03-01", "end_date": "2025-02-28", "service_type": "cloud", "billing_amount": 50000, "billing_cycle": "monthly"},
            ]
            
            for contract_data in contracts_data:
                try:
                    resp = self.post(f"/contracts/customer/{customer_id}", json=contract_data)
                    if resp.status_code in [200, 201]:
                        data = resp.json()
                        contract_id = data.get("data", {}).get("id") or data.get("id")
                        if contract_id:
                            self.contracts.append(contract_id)
                            print(f"  ✅ 合同创建成功: {contract_data['contract_name']} (ID: {contract_id})")
                        else:
                            print(f"  ⚠️ 合同创建响应无ID: {data}")
                    else:
                        print(f"  ❌ 合同创建失败: {resp.status_code} - {resp.text[:100]}")
                except Exception as e:
                    print(f"  ❌ 合同创建异常: {e}")
        
        print(f"  共创建 {len(self.contracts)} 个合同")
        return self.contracts

    def create_invoices(self):
        """创建测试票据/账单"""
        print("\n🧾 创建测试票据...")
        if not self.customers:
            print("  ⚠️ 无客户数据，跳过票据创建")
            return []
        
        invoices_data = [
            {"bill_type": "invoice", "amount": 113000, "total_amount": 113000, "tax_amount": 13000},
            {"bill_type": "invoice", "amount": 56500, "total_amount": 56500, "tax_amount": 6500},
            {"bill_type": "invoice", "amount": 226000, "total_amount": 226000, "tax_amount": 26000},
            {"bill_type": "invoice", "amount": 339000, "total_amount": 339000, "tax_amount": 39000},
            {"bill_type": "invoice", "amount": 452000, "total_amount": 452000, "tax_amount": 52000},
            {"bill_type": "invoice", "amount": 169000, "total_amount": 169000, "tax_amount": 19000},
            {"bill_type": "invoice", "amount": 678000, "total_amount": 678000, "tax_amount": 78000},
            {"bill_type": "invoice", "amount": 890000, "total_amount": 890000, "tax_amount": 90000},
        ]
        
        for invoice_data in invoices_data:
            try:
                resp = self.post("/bills", json=invoice_data)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    invoice_id = data.get("data", {}).get("id") or data.get("id")
                    if invoice_id:
                        self.invoices.append(invoice_id)
                        print(f"  ✅ 票据创建成功 (ID: {invoice_id})")
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
            {"voucher_date": "2024-01-31", "amount": 113000, "voucher_type": "receipt", "description": "收到服务费"},
            {"voucher_date": "2024-02-28", "amount": 56500, "voucher_type": "receipt", "description": "收到咨询费"},
            {"voucher_date": "2024-03-31", "amount": 226000, "voucher_type": "receipt", "description": "收到开发费"},
            {"voucher_date": "2024-04-30", "amount": 339000, "voucher_type": "receipt", "description": "收到维护费"},
            {"voucher_date": "2024-05-31", "amount": 452000, "voucher_type": "payment", "description": "支付广告费"},
            {"voucher_date": "2024-06-30", "amount": 678000, "voucher_type": "receipt", "description": "收到货款"},
        ]
        
        for voucher_data in vouchers_data:
            try:
                resp = self.post("/vouchers", json=voucher_data)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    voucher_id = data.get("data", {}).get("id") or data.get("id")
                    if voucher_id:
                        self.vouchers.append(voucher_id)
                        print(f"  ✅ 凭证创建成功 (ID: {voucher_id})")
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
        
        # 获取支持的银行列表
        try:
            resp = self.get("/bank-accounts/banks")
            if resp.status_code == 200:
                banks = resp.json().get("data", {}).get("items", [])
                if banks:
                    print(f"  支持的银行: {[b.get('name') for b in banks[:5]]}")
        except Exception as e:
            print(f"  ⚠️ 获取银行列表失败: {e}")
        
        # 使用常见的银行代码
        bank_codes = ["ICBC", "CCB", "ABC", "BOC", "CMBC"]
        
        for i, bank_code in enumerate(bank_codes):
            account_data = {
                "bank_code": bank_code,
                "account_no": f"6222{i:08d}",
                "account_name": f"测试银行账户{i+1}",
                "account_type": "basic"
            }
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
            {"amount": 113000, "flow_type": "income", "flow_date": "2024-01-15", "description": "收到服务费"},
            {"amount": -50000, "flow_type": "expense", "flow_date": "2024-01-20", "description": "采购办公用品"},
            {"amount": 56500, "flow_type": "income", "flow_date": "2024-02-20", "description": "收到咨询费"},
            {"amount": 226000, "flow_type": "income", "flow_date": "2024-03-10", "description": "收到开发费"},
            {"amount": -100000, "flow_type": "expense", "flow_date": "2024-04-15", "description": "支付工资"},
            {"amount": 339000, "flow_type": "income", "flow_date": "2024-04-05", "description": "收到维护费"},
            {"amount": 452000, "flow_type": "income", "flow_date": "2024-05-12", "description": "收到广告费"},
            {"amount": 678000, "flow_type": "income", "flow_date": "2024-06-15", "description": "收到货款"},
        ]
        
        for flow_data in flows_data:
            try:
                resp = self.post(f"/bank-flows?account_id={self.bank_accounts[0]}", json=flow_data)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    flow_id = data.get("data", {}).get("id") or data.get("id")
                    if flow_id:
                        self.bank_flows.append(flow_id)
                        print(f"  ✅ 银行流水创建成功 (ID: {flow_id})")
                    else:
                        print(f"  ⚠️ 银行流水创建响应无ID: {data}")
                else:
                    print(f"  ❌ 银行流水创建失败: {resp.status_code} - {resp.text[:100]}")
            except Exception as e:
                print(f"  ❌ 银行流水创建异常: {e}")
        
        print(f"  共创建 {len(self.bank_flows)} 条银行流水")
        return self.bank_flows

    def run(self):
        """执行所有数据创建"""
        print("="*60)
        print("SmartLedger 测试数据初始化 V2")
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
