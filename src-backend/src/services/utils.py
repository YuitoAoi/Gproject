# ruff: noqa: RUF002
"""服务层通用校验工具。"""

import re

_HTML_TAG = re.compile(r"<\s*/?\s*(script|iframe|object|embed|svg|img|style|link|meta).*?>", re.IGNORECASE)
_SCRIPT_PROTO = re.compile(r"javascript\s*:", re.IGNORECASE)


def is_safe_name(name: str) -> bool:
    """校验名称：非空，不含空格/引号/HTML 标签/危险协议。"""
    if not name or not name.strip():
        return False
    if re.search(r"[\s'\"]", name):
        return False
    if _HTML_TAG.search(name):
        return False
    return not _SCRIPT_PROTO.search(name)


def is_valid_email(email: str) -> bool:
    """校验邮箱格式。"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_safe_password(password: str) -> bool:
    """校验密码不含空格/引号/控制字符。"""
    return not re.search(r"[\s'\"\x00-\x1f\x7f]", password)


def is_strong_password(password: str) -> bool:
    """校验密码强度：至少 8 位，包含大小写/数字/特殊字符中至少两类。"""
    if len(password) < 8:
        return False
    categories = 0
    if re.search(r"[A-Z]", password):
        categories += 1
    if re.search(r"[a-z]", password):
        categories += 1
    if re.search(r"\d", password):
        categories += 1
    if re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", password):
        categories += 1
    return categories >= 2
