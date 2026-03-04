from typing import Optional, Dict, Any
import base64

from app.core.config import settings
from app.core.logging import logger


class OCRService:
    """百度OCR服务"""
    
    def __init__(self):
        self.app_id = settings.BAIDU_APP_ID
        self.api_key = settings.BAIDU_API_KEY
        self.secret_key = settings.BAIDU_SECRET_KEY
        self.client = None
        
        if self.app_id and self.api_key and self.secret_key:
            try:
                from aip import AipOcr
                self.client = AipOcr(self.app_id, self.api_key, self.secret_key)
            except ImportError:
                logger.warning("baidu-aip not installed, OCR will be mocked")
    
    async def recognize_vat_invoice(self, image_path: str) -> Optional[Dict[str, Any]]:
        """识别增值税发票"""
        if not self.client:
            logger.warning("OCR client not initialized, returning mock data")
            return self._mock_invoice_data()
        
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            result = self.client.vatInvoice(image_data)
            
            if 'words_result' in result:
                return self._parse_vat_invoice(result['words_result'])
            else:
                logger.error(f"OCR failed: {result}")
                return None
                
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return None
    
    def _parse_vat_invoice(self, words_result: dict) -> dict:
        """解析增值税发票结果"""
        return {
            "invoice_type": words_result.get("InvoiceType"),
            "invoice_code": words_result.get("InvoiceCode"),
            "invoice_number": words_result.get("InvoiceNum"),
            "invoice_date": words_result.get("InvoiceDate"),
            "buyer_name": words_result.get("PurchaserName"),
            "buyer_tax_no": words_result.get("PurchaserRegisterNum"),
            "seller_name": words_result.get("SellerName"),
            "seller_tax_no": words_result.get("SellerRegisterNum"),
            "amount": words_result.get("TotalAmount"),
            "tax_amount": words_result.get("TotalTax"),
            "total_amount": words_result.get("AmountInFiguers"),
            "goods_name": self._extract_goods_name(words_result),
        }
    
    def _extract_goods_name(self, words_result: dict) -> str:
        """提取商品名称"""
        commodities = words_result.get("CommodityName", [])
        if commodities:
            return ", ".join([c.get("word", "") for c in commodities])
        return ""
    
    def _mock_invoice_data(self) -> dict:
        """模拟发票数据（测试用）"""
        return {
            "invoice_type": "增值税普通发票",
            "invoice_code": "011001900211",
            "invoice_number": "12345678",
            "invoice_date": "2024-03-15",
            "buyer_name": "测试公司",
            "buyer_tax_no": "91110000123456789X",
            "seller_name": "销售方公司",
            "seller_tax_no": "91110000987654321Y",
            "amount": "1000.00",
            "tax_amount": "130.00",
            "total_amount": "1130.00",
            "goods_name": "咨询服务"
        }
