"""购物车接口：列表、加购、改数量、删除（均需登录）。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemResponse, CartItemUpdate
from app.services import cart as cart_service

router = APIRouter(prefix="/api/cart", tags=["cart"])


@router.get("/items", response_model=list[CartItemResponse])
def list_items(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return cart_service.get_cart_items(db, current_user.id)


@router.post("/items", response_model=CartItemResponse, status_code=201)
def add_item(
    data: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return cart_service.add_to_cart(db, current_user, data)


@router.put("/items/{item_id}", response_model=CartItemResponse)
def update_item(
    item_id: int,
    data: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return cart_service.update_quantity(db, current_user, item_id, data.quantity)


@router.delete("/items/{item_id}", status_code=204)
def remove_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart_service.remove_from_cart(db, current_user, item_id)
