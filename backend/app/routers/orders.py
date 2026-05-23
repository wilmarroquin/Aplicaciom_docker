"""Módulo retirado de la aplicación activa.

Las rutas de pedidos no se registran en app.main porque la funcionalidad fue
eliminada del alcance actual. Se conserva el archivo para no alterar la
estructura histórica del proyecto ni romper referencias existentes durante una
limpieza gradual.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permissions
from app.config.database import get_db
from app.models.access import User
from app.models.delivery import Courier, DeliveryAddress, DeliveryLog, DeliveryOrder, DeliveryStatus, OrderAssignment
from app.schemas import AssignmentCreate, OrderCreate, OrderRead, OrderStatusUpdate

router = APIRouter(prefix="/api/orders", tags=["Pedidos"])


@router.get("", response_model=list[OrderRead])
def list_orders(db: Session = Depends(get_db), _=Depends(require_permissions("orders.manage"))):
    return db.query(DeliveryOrder).order_by(DeliveryOrder.ordered_at.desc()).all()


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("orders.manage")),
):
    address = db.get(DeliveryAddress, payload.delivery_address_id)
    if not address or address.customer_id != payload.customer_id:
        raise HTTPException(status_code=400, detail="La dirección no pertenece al cliente indicado")

    pending_status = db.query(DeliveryStatus).filter(DeliveryStatus.code == "pending").first()
    order = DeliveryOrder(
        customer_id=payload.customer_id,
        delivery_address_id=payload.delivery_address_id,
        status_id=pending_status.id,
        order_total=payload.order_total,
        created_by_user_id=current_user.id,
    )
    db.add(order)
    db.flush()
    db.add(DeliveryLog(order_id=order.id, new_status_id=pending_status.id, changed_by_user_id=current_user.id, comment="Pedido creado"))
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("orders.manage")),
):
    order = db.get(DeliveryOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    next_status = db.query(DeliveryStatus).filter(DeliveryStatus.code == payload.status_code).first()
    if not next_status:
        raise HTTPException(status_code=404, detail="Estado no encontrado")

    previous_status_id = order.status_id
    order.status_id = next_status.id
    db.add(DeliveryLog(
        order_id=order.id,
        previous_status_id=previous_status_id,
        new_status_id=next_status.id,
        changed_by_user_id=current_user.id,
        comment=payload.comment,
    ))
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/assign", status_code=status.HTTP_201_CREATED)
def assign_order(
    order_id: int,
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("orders.assign")),
):
    order = db.get(DeliveryOrder, order_id)
    courier = db.get(Courier, payload.courier_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if not courier or not courier.is_available:
        raise HTTPException(status_code=400, detail="Repartidor no disponible")

    assignment = OrderAssignment(order_id=order.id, courier_id=courier.id, assigned_by_user_id=current_user.id)
    courier.is_available = False
    db.add(assignment)
    db.commit()
    return {"message": "Pedido asignado correctamente", "assignment_id": assignment.id}
