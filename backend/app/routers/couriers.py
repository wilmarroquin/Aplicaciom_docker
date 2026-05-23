from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permissions
from app.config.database import get_db
from app.models.delivery import Courier
from app.schemas import CourierCreate, CourierRead

router = APIRouter(prefix="/api/couriers", tags=["Repartidores"])


@router.get("", response_model=list[CourierRead])
def list_couriers(db: Session = Depends(get_db), _=Depends(require_permissions("couriers.manage"))):
    return db.query(Courier).order_by(Courier.full_name).all()


@router.post("", response_model=CourierRead, status_code=status.HTTP_201_CREATED)
def create_courier(payload: CourierCreate, db: Session = Depends(get_db), _=Depends(require_permissions("couriers.manage"))):
    courier = Courier(**payload.model_dump())
    db.add(courier)
    db.commit()
    db.refresh(courier)
    return courier
