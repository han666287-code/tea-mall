"""商品业务逻辑：列表（筛选/分页/缓存）、详情、增删改、图片上传。"""

from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.config import UPLOAD_DIR
from app.core.exceptions import BusinessException
from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.sku import ProductSpec, ProductSpecValue, Sku, SkuSpecValue
from app.repositories.product_repository import ProductRepository
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
    SkuPayload,
)
from app.services import cache

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

_MISSING = object()


def _sku_code_or_generate(product_id: int, sku_code: str | None) -> str:
    """SKU 编码：显式传入时去空格使用，否则自动生成。"""
    if sku_code and sku_code.strip():
        return sku_code.strip()
    return f"SKU-{product_id}-{uuid4().hex[:6].upper()}"


def _validate_sku_payloads(sku_payloads: list[SkuPayload]) -> None:
    """SKU 载荷规则：非空、规格名一致、单个 SKU 规格名不重复、组合唯一。"""
    if not sku_payloads:
        raise BusinessException(
            "PRODUCT_NEEDS_SKU", "商品至少需要一个 SKU", status_code=400
        )
    name_sets = [
        frozenset(item.name for item in payload.specs) for payload in sku_payloads
    ]
    if any(ns != name_sets[0] for ns in name_sets[1:]):
        raise BusinessException(
            "SKU_INVALID_SPECS", "同一商品所有 SKU 的规格名必须一致", status_code=400
        )
    seen_combos: set[tuple[tuple[str, str], ...]] = set()
    for payload in sku_payloads:
        names = [item.name for item in payload.specs]
        if len(names) != len(set(names)):
            raise BusinessException(
                "SKU_INVALID_SPECS", "单个 SKU 内规格名不能重复", status_code=400
            )
        combo = tuple(sorted((item.name, item.value) for item in payload.specs))
        if combo in seen_combos:
            raise BusinessException(
                "SKU_DUPLICATE_SPECS", "规格组合重复", status_code=400
            )
        seen_combos.add(combo)


def _get_or_create_spec(
    db: Session, product_id: int, name: str, sort_order: int
) -> ProductSpec:
    spec = db.scalar(
        select(ProductSpec).where(
            ProductSpec.product_id == product_id, ProductSpec.name == name
        )
    )
    if spec is None:
        spec = ProductSpec(product_id=product_id, name=name, sort_order=sort_order)
        db.add(spec)
        db.flush()
    elif spec.sort_order != sort_order:
        spec.sort_order = sort_order
    return spec


def _get_or_create_spec_value(
    db: Session, spec: ProductSpec, value: str, sort_order: int
) -> ProductSpecValue:
    spec_value = db.scalar(
        select(ProductSpecValue).where(
            ProductSpecValue.spec_id == spec.id, ProductSpecValue.value == value
        )
    )
    if spec_value is None:
        spec_value = ProductSpecValue(
            spec_id=spec.id, value=value, sort_order=sort_order
        )
        db.add(spec_value)
        db.flush()
    elif spec_value.sort_order != sort_order:
        spec_value.sort_order = sort_order
    return spec_value


def _sync_skus(db: Session, product: Product, sku_payloads: list[SkuPayload]) -> None:
    """校验并按载荷整体替换商品的 SKU（含规格/规格值），随后清理孤立规格。"""
    # model_dump() 会把嵌套模型转成 dict（如 ProductUpdate 携带 skus 时），统一转回模型
    sku_payloads = [
        payload
        if isinstance(payload, SkuPayload)
        else SkuPayload.model_validate(payload)
        for payload in sku_payloads
    ]
    _validate_sku_payloads(sku_payloads)

    for sku in list(product.skus):
        db.delete(sku)
    db.flush()

    spec_order: dict[str, int] = {}
    for payload in sku_payloads:
        sku_code = _sku_code_or_generate(product.id, payload.sku_code)
        exists = db.scalar(
            select(Sku).where(Sku.product_id == product.id, Sku.sku_code == sku_code)
        )
        if exists is not None:
            raise BusinessException("SKU_CODE_TAKEN", "SKU 编码已存在", status_code=400)
        sku = Sku(
            product_id=product.id,
            sku_code=sku_code,
            price=payload.price,
            stock=payload.stock,
            is_active=payload.is_active,
        )
        db.add(sku)
        db.flush()

        spec_value_ids: list[int] = []
        for item in payload.specs:
            if item.name not in spec_order:
                spec_order[item.name] = len(spec_order)
            spec = _get_or_create_spec(
                db, product.id, item.name, sort_order=spec_order[item.name]
            )
            spec_value = _get_or_create_spec_value(db, spec, item.value, sort_order=0)
            spec_value_ids.append(spec_value.id)
            db.add(SkuSpecValue(sku_id=sku.id, spec_value_id=spec_value.id))
        sku.spec_signature = "-".join(str(v) for v in sorted(spec_value_ids))

    db.flush()
    # 清理不再被引用的规格值与规格名
    for spec_value in db.scalars(
        select(ProductSpecValue).where(~ProductSpecValue.skus.any())
    ):
        db.delete(spec_value)
    for spec in db.scalars(select(ProductSpec).where(~ProductSpec.values.any())):
        db.delete(spec)
    db.flush()


def _load_product_skus(db: Session, product_id: int) -> list[Sku]:
    """按 id 加载商品全部 SKU（含规格信息），避免 N+1。"""
    return list(
        db.scalars(
            select(Sku)
            .options(selectinload(Sku.spec_values).selectinload(ProductSpecValue.spec))
            .where(Sku.product_id == product_id)
            .order_by(Sku.id)
        )
    )


def _recompute_product_summary(product: Product) -> None:
    """商品级 price/stock 汇总：启用 SKU 的最低价格与库存之和。"""
    active = [sku for sku in product.skus if sku.is_active]
    product.price = min((sku.price for sku in active), default=Decimal("0.00"))
    product.stock = sum((sku.stock for sku in active), start=0)


def refresh_product_summaries(db: Session, product_ids: list[int]) -> None:
    """按商品重新计算 price/stock 汇总（下单扣减、取消恢复库存后调用）。"""
    for product_id in product_ids:
        product = db.get(Product, product_id)
        if product is None:
            continue
        product.skus = _load_product_skus(db, product_id)
        _recompute_product_summary(product)


def list_products(
    db: Session,
    *,
    category_id: int | None,
    keyword: str | None,
    page: int,
    page_size: int,
    include_off_sale: bool,
    is_admin: bool,
) -> ProductListResponse:
    """商品列表：公开只显示上架商品；管理员可用 include_off_sale=true 查看全部。"""
    if include_off_sale and not is_admin:
        raise BusinessException(
            "ADMIN_PERMISSION_REQUIRED", "需要管理员权限", status_code=403
        )

    cache_key = cache.product_list_key(
        category_id, keyword, page, page_size, include_off_sale
    )
    cached = cache.get_json(cache_key)
    if cached is not None:
        return ProductListResponse.model_validate(cached)

    products, total = ProductRepository(db).list_for_page(
        category_id=category_id,
        keyword=keyword,
        include_off_sale=include_off_sale,
        page=page,
        page_size=page_size,
    )
    result = ProductListResponse(
        items=products, total=total, page=page, page_size=page_size
    )
    cache.set_json(cache_key, result.model_dump(mode="json"))
    return result


def get_product(db: Session, product_id: int, *, is_admin: bool) -> Product:
    """商品详情：下架商品仅管理员可见。"""
    cache_key = cache.product_detail_key(product_id)
    cached = cache.get_json(cache_key)
    if cached is not None:
        return ProductResponse.model_validate(cached)

    product = ProductRepository(db).get_by_id(product_id)
    if product is None:
        raise BusinessException("PRODUCT_NOT_FOUND", "商品不存在", status_code=404)
    if not product.is_on_sale and not is_admin:
        raise BusinessException("PRODUCT_NOT_FOUND", "商品不存在", status_code=404)

    if product.is_on_sale:
        cache.set_json(
            cache_key, ProductResponse.model_validate(product).model_dump(mode="json")
        )
    return product


def create_product(db: Session, data: ProductCreate) -> Product:
    if db.get(Category, data.category_id) is None:
        raise BusinessException(
            "PRODUCT_CATEGORY_NOT_FOUND", "分类不存在", status_code=400
        )
    payload = data.model_dump(exclude={"skus"})
    # ID 显式分配为"现存最大商品 ID + 1"，删除最大行后不会跳号；
    # 极端并发下两个请求可能拿到同一个 ID，由数据库唯一约束兜底（409，可重试）
    next_id = (db.scalar(select(func.max(Product.id))) or 0) + 1
    product = Product(id=next_id, **payload)
    db.add(product)
    db.flush()
    if data.skus:
        _sync_skus(db, product, data.skus)
    else:
        # 无 SKU 载荷时自动生成默认 SKU，保持既有创建行为
        db.add(
            Sku(
                product_id=product.id,
                sku_code=f"DEFAULT-{product.id}",
                price=product.price,
                stock=product.stock,
                is_active=True,
            )
        )
        db.flush()
    product.skus = _load_product_skus(db, product.id)
    _recompute_product_summary(product)
    db.commit()
    db.refresh(product)
    product.skus = _load_product_skus(db, product.id)
    cache.invalidate_products()
    return product


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    product = ProductRepository(db).get_by_id(product_id)
    if product is None:
        raise BusinessException("PRODUCT_NOT_FOUND", "商品不存在", status_code=404)
    updates = data.model_dump(exclude_unset=True)
    skus_payload = updates.pop("skus", _MISSING)
    if "category_id" in updates and db.get(Category, updates["category_id"]) is None:
        raise BusinessException(
            "PRODUCT_CATEGORY_NOT_FOUND", "分类不存在", status_code=400
        )
    if skus_payload is not _MISSING and skus_payload is not None:
        _sync_skus(db, product, skus_payload)
    elif "price" in updates or "stock" in updates:
        # 兼容既有接口：单 SKU 商品可直接改商品级价格/库存（落到 SKU）
        sku_count = db.scalar(
            select(func.count()).select_from(Sku).where(Sku.product_id == product.id)
        )
        if sku_count and sku_count > 1:
            raise BusinessException(
                "PRODUCT_HAS_SKUS",
                "多规格商品请通过 SKU 管理修改价格与库存",
                status_code=400,
            )
        sku = db.scalar(select(Sku).where(Sku.product_id == product.id))
        if sku is not None:
            if "price" in updates:
                sku.price = updates["price"]
            if "stock" in updates:
                sku.stock = updates["stock"]
    for field, value in updates.items():
        setattr(product, field, value)
    db.flush()
    product.skus = _load_product_skus(db, product.id)
    _recompute_product_summary(product)
    db.commit()
    db.refresh(product)
    product.skus = _load_product_skus(db, product.id)
    cache.invalidate_products()
    return product


def replace_skus(
    db: Session, product_id: int, sku_payloads: list[SkuPayload]
) -> Product:
    """管理员批量替换商品 SKU（含规格定义），并重算商品汇总。"""
    product = ProductRepository(db).get_by_id(product_id)
    if product is None:
        raise BusinessException("PRODUCT_NOT_FOUND", "商品不存在", status_code=404)
    _sync_skus(db, product, sku_payloads)
    product.skus = _load_product_skus(db, product.id)
    _recompute_product_summary(product)
    db.commit()
    db.refresh(product)
    product.skus = _load_product_skus(db, product.id)
    cache.invalidate_products()
    return product


def delete_product(db: Session, product_id: int) -> None:
    product = db.get(Product, product_id)
    if product is None:
        raise BusinessException("PRODUCT_NOT_FOUND", "商品不存在", status_code=404)
    db.delete(product)
    db.commit()
    cache.invalidate_products()


def save_product_image(file) -> str:
    """校验并保存上传图片，返回随机文件名；超限清理半成品文件。"""
    if not (file.content_type or "").startswith("image/"):
        raise BusinessException(
            "UNSUPPORTED_IMAGE_TYPE", "只支持上传图片文件", status_code=400
        )
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise BusinessException(
            "UNSUPPORTED_IMAGE_TYPE",
            f"不支持的图片格式：{ext or '未知'}",
            status_code=400,
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{ext}"
    target_path = UPLOAD_DIR / filename
    written = 0
    try:
        with open(target_path, "wb") as target:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > MAX_UPLOAD_SIZE_BYTES:
                    raise BusinessException(
                        "FILE_TOO_LARGE",
                        "文件过大：单个图片不能超过 10MB",
                        status_code=413,
                    )
                target.write(chunk)
    except BusinessException:
        # 超限时清理半成品文件，避免残留
        target_path.unlink(missing_ok=True)
        raise
    return filename


def upload_product_image(db: Session, product_id: int, file) -> Product:
    """上传商品图片：保存文件并更新 image_url。"""
    product = ProductRepository(db).get_by_id(product_id)
    if product is None:
        raise BusinessException("PRODUCT_NOT_FOUND", "商品不存在", status_code=404)
    filename = save_product_image(file)
    url = f"/uploads/{filename}"
    product.image_url = url
    main_image = db.scalar(
        select(ProductImage).where(
            ProductImage.product_id == product_id, ProductImage.kind == "main"
        )
    )
    if main_image is None:
        db.add(ProductImage(product_id=product_id, url=url, kind="main", sort_order=0))
    else:
        main_image.url = url
    db.commit()
    cache.invalidate_products()
    return ProductRepository(db).get_by_id(product_id)


def upload_product_images(db: Session, product_id: int, files: list) -> Product:
    """上传多张详情图：追加 kind=detail 行，返回更新后的商品。"""
    product = ProductRepository(db).get_by_id(product_id)
    if product is None:
        raise BusinessException("PRODUCT_NOT_FOUND", "商品不存在", status_code=404)
    max_sort = (
        db.scalar(
            select(func.max(ProductImage.sort_order)).where(
                ProductImage.product_id == product_id,
                ProductImage.kind == "detail",
            )
        )
        or 0
    )
    for index, file in enumerate(files):
        filename = save_product_image(file)
        db.add(
            ProductImage(
                product_id=product_id,
                url=f"/uploads/{filename}",
                kind="detail",
                sort_order=max_sort + index + 1,
            )
        )
    db.commit()
    cache.invalidate_products()
    return ProductRepository(db).get_by_id(product_id)


def remove_product_image(db: Session, product_id: int, url: str) -> Product:
    """移除一张详情图（主图请通过主图上传接口替换），并清理 uploads 文件。"""
    product = ProductRepository(db).get_by_id(product_id)
    if product is None:
        raise BusinessException("PRODUCT_NOT_FOUND", "商品不存在", status_code=404)
    image = db.scalar(
        select(ProductImage).where(
            ProductImage.product_id == product_id,
            ProductImage.kind == "detail",
            ProductImage.url == url,
        )
    )
    if image is None:
        raise BusinessException(
            "PRODUCT_IMAGE_NOT_FOUND", "商品图片不存在", status_code=404
        )
    db.delete(image)
    db.commit()
    # 清理 uploads 目录中的文件（仅限本地上传路径）
    if url.startswith("/uploads/"):
        (UPLOAD_DIR / Path(url).name).unlink(missing_ok=True)
    cache.invalidate_products()
    return ProductRepository(db).get_by_id(product_id)
