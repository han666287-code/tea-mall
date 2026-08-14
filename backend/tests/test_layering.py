"""V2.0-2.5 分层治理服务层单测：图片上传校验与半成品清理。"""

import io

import pytest
from starlette.datastructures import Headers, UploadFile

from app.config import UPLOAD_DIR
from app.core.exceptions import BusinessException
from app.services import product as product_service


def _fake_upload(content: bytes, filename: str = "x.png", content_type: str = "image/png"):
    return UploadFile(
        file=io.BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


def _upload_dir_files() -> set[str]:
    return {p.name for p in UPLOAD_DIR.iterdir() if p.is_file()}


def test_save_product_image_rejects_invalid_content_type():
    upload = _fake_upload(b"data", content_type="text/plain")
    with pytest.raises(BusinessException) as exc_info:
        product_service.save_product_image(upload)
    assert exc_info.value.code == "UNSUPPORTED_IMAGE_TYPE"
    assert exc_info.value.status_code == 400


def test_save_product_image_rejects_invalid_extension():
    upload = _fake_upload(b"data", filename="x.txt")
    with pytest.raises(BusinessException) as exc_info:
        product_service.save_product_image(upload)
    assert exc_info.value.code == "UNSUPPORTED_IMAGE_TYPE"
    assert exc_info.value.status_code == 400


def test_save_product_image_cleans_partial_file_on_too_large():
    before = _upload_dir_files()
    oversized = b"x" * (product_service.MAX_UPLOAD_SIZE_BYTES + 1)
    with pytest.raises(BusinessException) as exc_info:
        product_service.save_product_image(_fake_upload(oversized))
    assert exc_info.value.code == "FILE_TOO_LARGE"
    assert exc_info.value.status_code == 413
    assert _upload_dir_files() == before  # 半成品文件已清理


def test_save_product_image_success_returns_filename():
    before = _upload_dir_files()
    filename = product_service.save_product_image(_fake_upload(b"png-data"))
    assert filename.endswith(".png")
    assert (UPLOAD_DIR / filename).is_file()
    assert len(_upload_dir_files()) == len(before) + 1
    (UPLOAD_DIR / filename).unlink(missing_ok=True)  # 清理本次测试文件
