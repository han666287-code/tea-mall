"""初始化数据：创建管理员、示例分类与茶叶商品。

管理员账号从环境变量读取：
    ADMIN_USERNAME（可选，默认 admin）
    ADMIN_PASSWORD（必填，至少 12 位，禁止弱密码）

用法：
    python seed.py                        # 创建管理员（幂等）与示例数据
    python seed.py --reset-admin-password # 重置已存在管理员密码
"""

import argparse
import os
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models.category import Category
from app.models.product import Product
from app.models.sku import Sku
from app.models.user import User

ADMIN_USERNAME_ENV = "ADMIN_USERNAME"
ADMIN_PASSWORD_ENV = "ADMIN_PASSWORD"
DEFAULT_ADMIN_USERNAME = "admin"
MIN_ADMIN_PASSWORD_LENGTH = 12
MAX_ADMIN_PASSWORD_BYTES = 72  # bcrypt 上限

# 禁用弱密码（含历史默认 admin123）
WEAK_ADMIN_PASSWORDS = {
    "admin",
    "admin123",
    "password",
    "password123",
    "123456",
    "12345678",
    "123456789",
    "1234567890",
    "123456789012",
    "qwerty",
    "abc123",
    "111111",
    "changeme",
}


def load_admin_credentials() -> tuple[str, str]:
    """从环境变量读取管理员用户名与密码，缺失或不安全时拒绝执行。"""
    username = os.environ.get(ADMIN_USERNAME_ENV, DEFAULT_ADMIN_USERNAME).strip()
    password = os.environ.get(ADMIN_PASSWORD_ENV, "")

    if not username:
        sys.exit(f"错误：{ADMIN_USERNAME_ENV} 不能为空")
    if not password:
        sys.exit(f"错误：未设置 {ADMIN_PASSWORD_ENV}，无法创建/重置管理员，请先设置强密码")
    if len(password) < MIN_ADMIN_PASSWORD_LENGTH:
        sys.exit(f"错误：管理员密码至少 {MIN_ADMIN_PASSWORD_LENGTH} 个字符")
    if len(password.encode("utf-8")) > MAX_ADMIN_PASSWORD_BYTES:
        sys.exit(f"错误：管理员密码 UTF-8 编码后不能超过 {MAX_ADMIN_PASSWORD_BYTES} 字节")
    if password in WEAK_ADMIN_PASSWORDS or "admin123" in password.lower():
        sys.exit("错误：管理员密码命中弱密码名单（如 admin123），请设置强密码")
    return username, password


def create_admin() -> None:
    """创建管理员；用户名已存在则跳过（幂等）。"""
    username, password = load_admin_credentials()
    db = SessionLocal()
    try:
        exists = db.scalar(select(User).where(User.username == username))
        if exists:
            print(f"管理员账号 {username} 已存在，跳过创建")
            return
        db.add(
            User(
                username=username,
                password_hash=hash_password(password),
                nickname="管理员",
                role="admin",
                is_root=True,
            )
        )
        db.commit()
        print(f"管理员账号 {username} 已创建（密码已 bcrypt 哈希存储，不会打印明文）")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def reset_admin_password() -> None:
    """将已存在管理员的密码更新为环境变量指定值。"""
    username, password = load_admin_credentials()
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.username == username))
        if user is None or user.role != "admin":
            sys.exit(f"错误：管理员账号 {username} 不存在，请先运行 seed.py 创建")
        user.password_hash = hash_password(password)
        db.commit()
        print(f"管理员账号 {username} 密码已重置（密码已 bcrypt 哈希存储，不会打印明文）")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


SAMPLE_CATEGORIES = ["绿茶", "红茶", "乌龙茶", "白茶", "普洱茶"]

SAMPLE_PRODUCTS = [
    {"name": "西湖龙井", "category": "绿茶", "price": 88.00, "stock": 100,
     "description": "经典明前龙井，豆香清雅，口感鲜爽。"},
    {"name": "洞庭碧螺春", "category": "绿茶", "price": 128.00, "stock": 80,
     "description": "卷曲成螺，满身白毫，花果香明显。"},
    {"name": "正山小种", "category": "红茶", "price": 158.00, "stock": 60,
     "description": "传统松烟香红茶，滋味醇厚回甘。"},
    {"name": "金骏眉", "category": "红茶", "price": 268.00, "stock": 40,
     "description": "高端红茶代表，蜜香馥郁，汤色金黄。"},
    {"name": "安溪铁观音", "category": "乌龙茶", "price": 98.00, "stock": 90,
     "description": "兰花香明显，观音韵足，耐冲泡。"},
    {"name": "武夷大红袍", "category": "乌龙茶", "price": 198.00, "stock": 50,
     "description": "岩茶代表，岩骨花香，醇厚顺滑。"},
    {"name": "白毫银针", "category": "白茶", "price": 328.00, "stock": 30,
     "description": "白茶之首，毫香蜜韵，一年茶三年药。"},
    {"name": "寿眉", "category": "白茶", "price": 66.00, "stock": 120,
     "description": "口粮白茶，枣香清甜，煮泡皆宜。"},
    {"name": "勐海生普", "category": "普洱茶", "price": 108.00, "stock": 70,
     "description": "生茶新茶，回甘迅猛，适合长期存放。"},
    {"name": "勐海熟普", "category": "普洱茶", "price": 138.00, "stock": 75,
     "description": "熟茶陈香，汤色红浓，温和养胃。"},
]


def create_categories_and_products() -> None:
    """创建示例分类与茶叶商品（已存在则跳过，可重复执行）。"""
    db = SessionLocal()
    try:
        categories: list[Category] = []
        for index, name in enumerate(SAMPLE_CATEGORIES):
            category = db.scalar(select(Category).where(Category.name == name))
            if category is None:
                category = Category(name=name, sort_order=index)
                db.add(category)
            categories.append(category)
        db.flush()

        for item in SAMPLE_PRODUCTS:
            if db.scalar(select(Product).where(Product.name == item["name"])):
                continue
            category = next(c for c in categories if c.name == item["category"])
            product = Product(
                name=item["name"],
                category_id=category.id,
                price=item["price"],
                stock=item["stock"],
                description=item["description"],
            )
            db.add(product)
            db.flush()
            db.add(
                Sku(
                    product_id=product.id,
                    sku_code=f"DEFAULT-{product.id}",
                    price=product.price,
                    stock=product.stock,
                    is_active=True,
                )
            )
        db.commit()
        print(f"示例数据已就绪：{len(SAMPLE_CATEGORIES)} 个分类，{len(SAMPLE_PRODUCTS)} 个商品")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="TeaMall 初始化种子数据")
    parser.add_argument(
        "--reset-admin-password",
        action="store_true",
        help="重置已存在管理员账号的密码（从 ADMIN_USERNAME / ADMIN_PASSWORD 读取）",
    )
    args = parser.parse_args()

    if args.reset_admin_password:
        reset_admin_password()
        return
    create_admin()
    create_categories_and_products()


if __name__ == "__main__":
    main()
