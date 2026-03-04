class BusinessException(Exception):
    """业务异常基类"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class NotFoundException(BusinessException):
    """资源不存在异常"""
    def __init__(self, resource: str):
        super().__init__(404, f"{resource} not found")


class ValidationException(BusinessException):
    """参数校验异常"""
    def __init__(self, message: str):
        super().__init__(400, message)


class AuthenticationException(BusinessException):
    """认证异常"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(401, message)


class PermissionDeniedException(BusinessException):
    """权限拒绝异常"""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(403, message)
