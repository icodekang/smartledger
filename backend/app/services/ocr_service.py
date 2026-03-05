from typing import Optional, Dict, Any, Union
import base64
import io
import tempfile
import os

from app.core.config import settings
from app.core.logging import logger


class OCRService:
    """百度OCR服务 - 支持PDF和图片"""
    
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
    
    async def recognize_vat_invoice(self, file_path: str) -> Optional[Dict[str, Any]]:
        """识别增值税发票（支持PDF和图片）"""
        if not self.client:
            logger.warning("OCR client not initialized, returning mock data")
            return self._mock_invoice_data()
        
        try:
            # 检查文件类型
            is_pdf = file_path.lower().endswith('.pdf')
            
            if is_pdf:
                # PDF处理：转换为图片
                image_data = await self._convert_pdf_to_image(file_path)
                if not image_data:
                    return None
            else:
                # 直接读取图片
                with open(file_path, 'rb') as f:
                    image_data = f.read()
            
            # 调用OCR
            result = self.client.vatInvoice(image_data)
            
            if 'words_result' in result:
                return self._parse_vat_invoice(result['words_result'])
            else:
                logger.error(f"OCR failed: {result}")
                return None
                
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return None
    
    async def recognize_vat_invoice_from_bytes(self, file_bytes: bytes, filename: str) -> Optional[Dict[str, Any]]:
        """从字节流识别发票（支持PDF和图片）"""
        if not self.client:
            logger.warning("OCR client not initialized, returning mock data")
            return self._mock_invoice_data()
        
        try:
            # 检查文件类型
            is_pdf = filename.lower().endswith('.pdf')
            
            if is_pdf:
                # PDF处理：先保存临时文件，再转换
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                    tmp_pdf.write(file_bytes)
                    tmp_pdf_path = tmp_pdf.name
                
                try:
                    image_data = await self._convert_pdf_to_image(tmp_pdf_path)
                    if not image_data:
                        return None
                finally:
                    os.unlink(tmp_pdf_path)
            else:
                image_data = file_bytes
            
            # 调用OCR
            result = self.client.vatInvoice(image_data)
            
            if 'words_result' in result:
                return self._parse_vat_invoice(result['words_result'])
            else:
                logger.error(f"OCR failed: {result}")
                return None
                
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return None
    
    async def _convert_pdf_to_image(self, pdf_path: str) -> Optional[bytes]:
        """将PDF第一页转换为图片"""
        try:
            # 尝试使用pdf2image
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=200)
                if images:
                    img_byte_arr = io.BytesIO()
                    images[0].save(img_byte_arr, format='JPEG', quality=95)
                    return img_byte_arr.getvalue()
            except ImportError:
                logger.warning("pdf2image not installed, trying PyMuPDF")
            
            # 备选：使用PyMuPDF
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(pdf_path)
                page = doc[0]
                
                # 提高分辨率
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                
                # 转换为JPEG
                img_data = pix.tobytes("jpeg")
                doc.close()
                return img_data
            except ImportError:
                logger.warning("PyMuPDF not installed, trying pypdf")
            
            # 最后备选：使用pypdf + Pillow（仅提取图片）
            try:
                from pypdf import PdfReader
                from PIL import Image
                
                reader = PdfReader(pdf_path)
                page = reader.pages[0]
                
                # 尝试提取页面中的图片
                if "/XObject" in page["/Resources"]:
                    xObject = page["/Resources"]["/XObject"].get_object()
                    
                    for obj in xObject:
                        if xObject[obj]["/Subtype"] == "/Image":
                            try:
                                size = (xObject[obj]["/Width"], xObject[obj]["/Height"])
                                data = xObject[obj].get_data()
                                
                                if xObject[obj]["/Filter"] == "/DCTDecode":
                                    # JPEG格式
                                    return data
                                elif xObject[obj]["/Filter"] == "/FlateDecode":
                                    # 需要解码
                                    img = Image.frombytes("RGB", size, data)
                                    img_byte_arr = io.BytesIO()
                                    img.save(img_byte_arr, format='JPEG')
                                    return img_byte_arr.getvalue()
                            except Exception as e:
                                logger.warning(f"Failed to extract image: {e}")
                                continue
                
                logger.error("No extractable image found in PDF")
                return None
            except ImportError:
                logger.error("No PDF conversion library available")
                return None
                
        except Exception as e:
            logger.error(f"PDF conversion error: {e}")
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
