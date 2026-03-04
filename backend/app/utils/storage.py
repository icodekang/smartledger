import uuid
from datetime import datetime


def generate_object_name(
    file_type: str,
    customer_id: str,
    original_filename: str
) -> str:
    """生成存储路径"""
    now = datetime.now()
    file_ext = original_filename.split('.')[-1] if '.' in original_filename else 'bin'
    unique_id = str(uuid.uuid4())[:8]
    
    object_name = f"{file_type}/{now.year}/{now.month:02d}/{customer_id}/{now.strftime('%Y%m%d%H%M%S')}_{unique_id}.{file_ext}"
    return object_name
