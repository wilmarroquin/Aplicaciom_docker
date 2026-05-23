CREATE EXTENSION IF NOT EXISTS postgis;

-- La aplicación crea el esquema mediante SQLAlchemy para mantener los modelos como fuente de verdad.
-- Este archivo asegura que PostGIS esté disponible durante la primera inicialización del contenedor.
