"""产品原图背景隔离（bg removal）。

上传产品原图后可选生成 ``*_isolated.png`` 作为额外参考（**不覆盖**原件锚点，ADR 0034）。
优先使用可选依赖 ``rembg``；未安装时返回 None，调用方跳过隔离步骤。
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def rembg_available() -> bool:
    try:
        import rembg  # noqa: F401

        return True
    except ImportError:
        return False


def isolate_product_bytes(image_bytes: bytes) -> bytes | None:
    """从原图字节生成去背景 PNG 字节；不可用或失败返回 None。"""
    try:
        from rembg import remove
    except ImportError:
        logger.debug("rembg 未安装，跳过产品背景隔离")
        return None
    try:
        result = remove(image_bytes)
        if not result:
            return None
        return bytes(result)
    except Exception:
        logger.warning("产品背景隔离失败", exc_info=True)
        return None


def isolate_product_file(src_path: Path, dest_path: Path) -> Path | None:
    """读 src 写 isolated PNG 到 dest；成功返回 dest，否则 None。"""
    if not src_path.is_file():
        return None
    try:
        raw = src_path.read_bytes()
    except OSError:
        return None
    out = isolate_product_bytes(raw)
    if not out:
        return None
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(out)
    return dest_path


def isolated_ref_filename(original_filename: str) -> str:
    """``foo_1.jpg`` → ``foo_1_isolated.png``。"""
    stem = Path(original_filename).stem
    return f"{stem}_isolated.png"
