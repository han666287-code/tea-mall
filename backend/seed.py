"""初始化数据：创建默认管理员、示例分类与茶叶商品。

用法：
    python seed.py
"""

from sqlalchemy import select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models.category import Category
from app.models.product import Product
from app.models.user import User

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def create_admin() -> None:
    db = SessionLocal()
    try:
        exists = db.scalar(select(User).where(User.username == ADMIN_USERNAME))
        if exists:
            print("管理员账号已存在，跳过创建")
            return
        db.add(
            User(
                username=ADMIN_USERNAME,
                password_hash=hash_password(ADMIN_PASSWORD),
                nickname="管理员",
                role="admin",
            )
        )
        db.commit()
        print(f"默认管理员已创建：{ADMIN_USERNAME} / {ADMIN_PASSWORD}")
        print("注意：本地学习项目默认密码，请勿用于生产环境")
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
            db.add(
                Product(
                    name=item["name"],
                    category_id=category.id,
                    price=item["price"],
                    stock=item["stock"],
                    description=item["description"],
                )
            )
        db.commit()
        print(f"示例数据已就绪：{len(SAMPLE_CATEGORIES)} 个分类，{len(SAMPLE_PRODUCTS)} 个商品")
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
    create_categories_and_products()
