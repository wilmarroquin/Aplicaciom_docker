from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.delivery import Customer, DeliveryAddress, DeliveryZone
from app.schemas import AddressCreate, AddressRead, ZoneRead

router = APIRouter(prefix="/api", tags=["Direcciones"])


@router.get("/zones", response_model=list[ZoneRead])
def list_zones(db: Session = Depends(get_db)):
    return db.query(DeliveryZone).filter(DeliveryZone.is_active.is_(True)).order_by(DeliveryZone.name).all()


@router.get("/addresses", response_model=list[AddressRead])
def list_addresses(db: Session = Depends(get_db)):
    return db.query(DeliveryAddress).order_by(DeliveryAddress.created_at.desc()).all()


@router.post("/addresses", response_model=AddressRead, status_code=status.HTTP_201_CREATED)
def create_address(payload: AddressCreate, db: Session = Depends(get_db)):
    if not db.get(Customer, payload.customer_id):
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    zone = db.get(DeliveryZone, payload.zone_id)
    if not zone or not zone.is_active:
        raise HTTPException(status_code=404, detail="Zona no encontrada")

    address = DeliveryAddress(**payload.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@router.put("/addresses/{address_id}", response_model=AddressRead)
def update_address(
    address_id: int,
    payload: AddressCreate,
    db: Session = Depends(get_db),
):
    address = db.get(DeliveryAddress, address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Dirección no encontrada")
    if not db.get(Customer, payload.customer_id):
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    zone = db.get(DeliveryZone, payload.zone_id)
    if not zone or not zone.is_active:
        raise HTTPException(status_code=404, detail="Zona no encontrada")

    for field, value in payload.model_dump().items():
        setattr(address, field, value)

    db.commit()
    db.refresh(address)
    return address
