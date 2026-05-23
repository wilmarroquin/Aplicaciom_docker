from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.config.settings import settings
from app.models.access import Permission, Role, User
from app.models.delivery import Courier, Customer, DeliveryAddress, DeliveryZone, PointOfInterest

ROLE_PERMISSIONS = {
    "Administrador": [
        "users.manage", "customers.manage", "addresses.manage", "couriers.manage", "points.manage"
    ],
    "Cajero": ["customers.manage", "addresses.manage", "points.manage"],
    "Repartidor": [],
    "Supervisor": ["couriers.manage"],
}


def seed_initial_data(db: Session) -> None:
    db.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))

    permissions_by_code = {}
    for permission_code in sorted({item for values in ROLE_PERMISSIONS.values() for item in values}):
        permission = db.query(Permission).filter(Permission.code == permission_code).first()
        if not permission:
            permission = Permission(code=permission_code, description=permission_code.replace(".", " ").title())
            db.add(permission)
        permissions_by_code[permission_code] = permission

    roles_by_name = {}
    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(name=role_name, description=f"Rol {role_name.lower()} del sistema")
            db.add(role)
        role.permissions = [permissions_by_code[code] for code in permission_codes]
        roles_by_name[role_name] = role

    admin = db.query(User).filter(User.email == settings.admin_email).first()
    if not admin:
        db.add(User(
            full_name="Administrador Principal",
            email=settings.admin_email,
            password_hash=hash_password(settings.admin_password),
            role=roles_by_name["Administrador"],
            is_active=True,
        ))
    else:
        admin.full_name = "Administrador Principal"
        admin.password_hash = hash_password(settings.admin_password)
        admin.role = roles_by_name["Administrador"]
        admin.is_active = True

    if db.query(DeliveryZone).count() == 0:
        zone = DeliveryZone(name="Zona Central", municipality="Guatemala", department="Guatemala")
        db.add(zone)
        db.flush()

        customer = Customer(
            full_name="Cliente Demo",
            phone="55550000",
            email="cliente.demo@example.com",
            notes="Cliente inicial para pruebas",
        )
        db.add(customer)
        db.flush()

        db.add(DeliveryAddress(
            customer_id=customer.id,
            zone_id=zone.id,
            street_address="12 Calle 3-45, Zona Central",
            reference_note="Casa azul frente al parque",
            latitude=14.6349,
            longitude=-90.5133,
            is_default=True,
        ))
        db.add(Courier(full_name="Repartidor Demo", phone="55551111", is_available=True))

    if db.query(PointOfInterest).count() == 0:
        db.add_all([
            PointOfInterest(
                name="Parque Central",
                description="Punto de referencia principal en el centro de la ciudad.",
                category="parque",
                latitude=14.634915,
                longitude=-90.506882,
            ),
            PointOfInterest(
                name="Mercado Central",
                description="Área comercial con alta afluencia peatonal.",
                category="comercio",
                latitude=14.640124,
                longitude=-90.513268,
            ),
            PointOfInterest(
                name="Hospital General",
                description="Centro hospitalario usado como punto de referencia.",
                category="salud",
                latitude=14.627821,
                longitude=-90.516714,
            ),
            PointOfInterest(
                name="Universidad San Carlos",
                description="Campus universitario con múltiples accesos.",
                category="educacion",
                latitude=14.589002,
                longitude=-90.551942,
            ),
            PointOfInterest(
                name="Terminal Zona 4",
                description="Nodo de transporte y conexión urbana.",
                category="transporte",
                latitude=14.622938,
                longitude=-90.514603,
            ),
        ])

    db.commit()
