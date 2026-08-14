"""业务异常定义。

Service 层禁止直接抛 HTTPException（避免业务逻辑与 HTTP 框架耦合），
统一抛出 BusinessException，由全局异常处理器转为 `{detail, code}` 响应。
"""


class BusinessException(Exception):
    """业务异常：携带稳定错误码与 HTTP 状态码，默认 400。"""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)
