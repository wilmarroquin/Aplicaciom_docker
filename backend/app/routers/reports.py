"""Módulo retirado de la aplicación activa.

Las rutas de reportes dependían de pedidos y no se registran en app.main.
El archivo permanece únicamente para mantener estable la estructura mientras se
decide si los modelos históricos de pedidos se eliminan en una migración futura.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permissions
from app.config.database import get_db
from app.models.delivery import Courier, Customer, DeliveryAddress, DeliveryOrder, DeliveryStatus, DeliveryZone, OrderAssignment
from app.schemas import DeliveryReportItem

router = APIRouter(prefix="/api/reports", tags=["Reportes"])


@router.get("/deliveries", response_model=list[DeliveryReportItem])
def delivery_report(
    customer_id: Optional[int] = None,
    courier_id: Optional[int] = None,
    status_code: Optional[str] = None,
    zone_id: Optional[int] = None,
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(require_permissions("reports.read")),
):
    query = (
        db.query(DeliveryOrder, Customer, DeliveryStatus, DeliveryZone, Courier)
        .join(Customer, DeliveryOrder.customer_id == Customer.id)
        .join(DeliveryAddress, DeliveryOrder.delivery_address_id == DeliveryAddress.id)
        .join(DeliveryZone, DeliveryAddress.zone_id == DeliveryZone.id)
        .join(DeliveryStatus, DeliveryOrder.status_id == DeliveryStatus.id)
        .outerjoin(OrderAssignment, OrderAssignment.order_id == DeliveryOrder.id)
        .outerjoin(Courier, OrderAssignment.courier_id == Courier.id)
    )

    if customer_id:
        query = query.filter(DeliveryOrder.customer_id == customer_id)
    if courier_id:
        query = query.filter(Courier.id == courier_id)
    if status_code:
        query = query.filter(DeliveryStatus.code == status_code)
    if zone_id:
        query = query.filter(DeliveryZone.id == zone_id)
    if date_from:
        query = query.filter(DeliveryOrder.ordered_at >= date_from)
    if date_to:
        query = query.filter(DeliveryOrder.ordered_at <= date_to)

    rows = query.order_by(DeliveryOrder.ordered_at.desc()).all()
    return [
        DeliveryReportItem(
            order_id=order.id,
            customer_name=customer.full_name,
            courier_name=courier.full_name if courier else None,
            status=status.name,
            zone=zone.name,
            order_total=order.order_total,
            ordered_at=order.ordered_at,
        )
        for order, customer, status, zone, courier in rows
    ]
