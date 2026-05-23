from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.delivery import PointOfInterest
from app.schemas import PointOfInterestCreate, PointOfInterestRead

router = APIRouter(prefix="/api/points", tags=["Puntos de interés"])


@router.get("", response_model=list[PointOfInterestRead])
def list_points(
    category: Optional[str] = Query(default=None, min_length=2, max_length=80),
    latitude: Optional[Decimal] = Query(default=None, ge=-90, le=90),
    longitude: Optional[Decimal] = Query(default=None, ge=-180, le=180),
    radius_m: Optional[int] = Query(default=None, gt=0, le=50000),
    db: Session = Depends(get_db),
):
    proximity_values = [latitude, longitude, radius_m]
    if any(value is not None for value in proximity_values) and not all(value is not None for value in proximity_values):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Para filtrar por radio debes enviar latitude, longitude y radius_m",
        )

    if radius_m is not None:
        sql = text("""
            SELECT *
            FROM points_of_interest
            WHERE (:category IS NULL OR category = :category)
              AND ST_DWithin(
                  ST_SetSRID(ST_MakePoint(longitude::double precision, latitude::double precision), 4326)::geography,
                  ST_SetSRID(ST_MakePoint(CAST(:longitude AS double precision), CAST(:latitude AS double precision)), 4326)::geography,
                  :radius_m
              )
            ORDER BY ST_Distance(
                ST_SetSRID(ST_MakePoint(longitude::double precision, latitude::double precision), 4326)::geography,
                ST_SetSRID(ST_MakePoint(CAST(:longitude AS double precision), CAST(:latitude AS double precision)), 4326)::geography
            ), name
        """)
        rows = db.execute(sql, {
            "category": category,
            "latitude": latitude,
            "longitude": longitude,
            "radius_m": radius_m,
        }).mappings().all()
        return [dict(row) for row in rows]

    query = db.query(PointOfInterest)
    if category:
        query = query.filter(PointOfInterest.category == category)

    return query.order_by(PointOfInterest.name).all()


@router.post("", response_model=PointOfInterestRead, status_code=status.HTTP_201_CREATED)
def create_point(
    payload: PointOfInterestCreate,
    db: Session = Depends(get_db),
):
    point = PointOfInterest(**payload.model_dump())
    db.add(point)
    db.commit()
    db.refresh(point)
    return point
