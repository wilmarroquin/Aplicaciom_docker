from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config.database import Base, SessionLocal, engine
from app.config.settings import settings
from app.models import *  # noqa: F401,F403
from app.routers import addresses, auth, couriers, customers, points
from app.services.seed_data import seed_initial_data

app = FastAPI(
    title="RouteBite Delivery Manager API",
    description="API para administrar ubicaciones y entregas de restaurante.",
    version="1.0.0",
    debug=settings.debug,
)

allowed_origins = settings.allowed_origins

if isinstance(allowed_origins, str):
    allowed_origins = [
        origin.strip()
        for origin in allowed_origins.split(",")
        if origin.strip()
    ]

if not allowed_origins:
    allowed_origins = [
        "https://aplicacion-docker-frontend.onrender.com"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_points_of_interest_location_gist
            ON points_of_interest
            USING GIST (
                (ST_SetSRID(ST_MakePoint(longitude::double precision, latitude::double precision), 4326)::geography)
            )
        """))
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()


@app.get("/api/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "service": "routebite-delivery-manager"}


app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(addresses.router)
app.include_router(couriers.router)
app.include_router(points.router)
