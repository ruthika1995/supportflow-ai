"""
Order routes — order CRUD, status, cancellation, refunds.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.schemas import OrderOut, OrderCreate

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", response_model=List[OrderOut])
def list_orders(db: Session = Depends(get_db)):
    return db.query(Order).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/{order_id}/status")
def get_order_status(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "order_id": order.id,
        "status": order.status,
        "tracking_number": order.tracking_number,
        "estimated_delivery": order.estimated_delivery,
    }


@router.post("/", response_model=OrderOut)
def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    total = 0.0
    items = []
    for item_data in data.items:
        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_data['product_id']} not found")
        qty = item_data.get("quantity", 1)
        total += product.price * qty
        items.append({"product_id": product.id, "quantity": qty, "unit_price": product.price})

    order = Order(
        customer_id=data.customer_id,
        total_amount=round(total, 2),
        shipping_address=data.shipping_address,
        status="processing",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    for item in items:
        oi = OrderItem(order_id=order.id, **item)
        db.add(oi)
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "processing":
        raise HTTPException(status_code=400, detail=f"Cannot cancel order with status '{order.status}'")
    order.status = "cancelled"
    db.commit()
    return {"order_id": order.id, "status": "cancelled"}
