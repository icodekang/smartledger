import re
from typing import Tuple
from app.core.exceptions import BusinessException

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    校验密码强度
    要求:
    - 至少8个字符
    - 至少1个大写字母
    - 至少1个小写字母
    - 至少1个数字
    - 至少1个特殊字符
    """
    if len(password) < 8:
        return False, "密码长度至少8个字符"
    
    if not re.search(r'[A-Z]', password):
        return False, "密码必须包含至少一个大写字母"
    
    if not re.search(r'[a-z]', password):
        return False, "密码必须包含至少一个小写字母"
    
    if not re.search(r'\d', password):
        return False, "密码必须包含至少一个数字"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "密码必须包含至少一个特殊字符"
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    """清理文件名，防止目录遍历"""
    # 移除路径分隔符
    filename = filename.replace('/', '').replace('\\', '')
    # 移除空字符
    filename = filename.replace('\x00', '')
    # 限制长度
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255-len(ext)-1] + '.' + ext if ext else filename[:255]
    return filename


def mask_sensitive_string(value: str, mask_char: str = '*', show_prefix: int = 3, show_suffix: int = 4) -> str:
    """
    敏感数据脱敏
    例如: 1234567890123456 -> 123***********3456
    """
    if not value or len(value) <= show_prefix + show_suffix:
        return value
    
    prefix = value[:show_prefix]
    suffix = value[-show_suffix:]
    middle_length = len(value) - show_prefix - show_suffix
    
    return prefix + mask_char * middle_length + suffix
