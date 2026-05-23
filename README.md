# RouteBite Delivery Manager

Aplicación de demostración para administrar clientes, direcciones de entrega y puntos geográficos usando una solución contenerizada con Docker, FastAPI, PostgreSQL/PostGIS y Nginx.

La interfaz principal abre directamente para facilitar la entrega académica y demostrar el funcionamiento del stack: proxy web, API REST, base de datos geoespacial, seed inicial y persistencia Docker.

## Tecnologías

- FastAPI
- PostgreSQL + PostGIS
- SQLAlchemy
- Docker Compose
- Nginx
- HTML, CSS y JavaScript
- Leaflet para visualización de mapa
- JWT disponible en API para autenticación opcional

## Requisitos Previos

- Docker
- Docker Compose
- Navegador web moderno

## Configuración

Crear el archivo `.env` tomando como base `.env.example`.

Variables principales:

```text
DELIVERY_DB_NAME=routebite_db
DELIVERY_DB_USER=routebite_user
DELIVERY_DB_PASSWORD=replace-with-a-strong-database-password
DELIVERY_SECRET_KEY=replace-with-a-long-random-secret-key
DELIVERY_ADMIN_EMAIL=admin@example.com
DELIVERY_ADMIN_PASSWORD=replace-with-a-strong-admin-password
```

Proteger el archivo local de variables:

```bash
chmod 600 .env
```

Para producción se deben rotar la contraseña de base de datos, la clave secreta, el usuario administrador y cualquier token o clave privada.

## Ejecución

Levantar la aplicación:

```bash
docker compose up --build -d
```

Abrir en navegador:

```text
http://localhost:8080
```

Documentación interactiva de la API:

```text
http://localhost:8080/docs
```

Detener los contenedores:

```bash
docker compose down
```

## Servicios Docker

- `database`: PostgreSQL con PostGIS.
- `api`: servidor FastAPI.
- `web`: Nginx como proxy y servidor del frontend estático.

El único puerto publicado hacia el host es:

```text
8080 -> 80/tcp
```

La API y la base de datos se comunican dentro de la red Docker `routebite_network`.

## Persistencia

La base de datos usa el volumen Docker:

```text
routebite_postgres_data
```

Los datos sobreviven al reiniciar o recrear contenedores mientras no se elimine el volumen.

## Backup y Restauración

Crear un backup de la base de datos:

```bash
docker exec routebite_database pg_dump -U <usuario> <base_datos> > backup.sql
```

Restaurar un backup:

```bash
cat backup.sql | docker exec -i routebite_database psql -U <usuario> <base_datos>
```

Los valores `<usuario>` y `<base_datos>` deben coincidir con `DELIVERY_DB_USER` y `DELIVERY_DB_NAME` del archivo `.env`.

## Funcionalidades De La Interfaz

- Listado y registro de clientes.
- Registro de direcciones de entrega con latitud y longitud.
- Edición de direcciones existentes.
- Cancelación de edición de direcciones.
- Listado de direcciones registradas.
- Mapa con marcadores de ubicaciones.
- Botón para localizar una dirección específica en el mapa.
- Botón para ajustar el mapa y ver todas las ubicaciones.

La pantalla de login no forma parte del flujo visual principal para esta entrega. La autenticación se conserva en la API, pero no bloquea la demostración de la aplicación.

## Puntos De Interés

La API incluye una entidad de puntos de interés con:

- Nombre.
- Descripción.
- Categoría.
- Latitud.
- Longitud.

También incluye búsqueda geoespacial por radio usando PostGIS.

## Endpoints Principales

Sistema:

- `GET /api/health`

Clientes:

- `GET /api/customers`
- `POST /api/customers`
- `GET /api/customers/{customer_id}`

Direcciones y zonas:

- `GET /api/zones`
- `GET /api/addresses`
- `POST /api/addresses`
- `PUT /api/addresses/{address_id}`

Puntos de interés:

- `GET /api/points`
- `POST /api/points`
- `GET /api/points?category=parque`
- `GET /api/points?latitude=14.6349&longitude=-90.5068&radius_m=1000`

Autenticación opcional:

- `POST /api/auth/login`
- `GET /api/auth/me`

## Seed Inicial

El seed se ejecuta automáticamente al iniciar la API.

Carga:

- Roles y permisos.
- Usuario administrador.
- Zona inicial.
- Cliente de demostración.
- Dirección de entrega de demostración.
- Repartidor de demostración.
- 5 puntos de interés de ejemplo.

El código del seed está en:

```text
backend/app/services/seed_data.py
```

## Validación Rápida

Validar la configuración Docker:

```bash
docker compose config
```

Construir y levantar el entorno:

```bash
docker compose build
docker compose up -d
```

Verificar contenedores y logs:

```bash
docker compose ps
docker compose logs api
docker compose logs database
docker compose logs web
```

Verificar frontend:

```bash
curl http://localhost:8080
```

Verificar API:

```bash
curl http://localhost:8080/api/health
curl http://localhost:8080/api/points
curl "http://localhost:8080/api/points?category=parque"
curl "http://localhost:8080/api/points?latitude=14.6349&longitude=-90.5068&radius_m=1000"
```

Verificar documentación de la API:

```bash
curl -I http://localhost:8080/docs
curl -I http://localhost:8080/openapi.json
```

Verificar recursos Docker:

```bash
docker volume ls
docker network ls
```

## Notas Técnicas

- Nginx sirve el frontend y redirige `/api` hacia FastAPI.
- El backend no expone puerto directo al host.
- PostGIS se habilita al inicializar la base de datos y también durante el arranque de la API.
- SQLAlchemy crea las tablas necesarias para el entorno de demostración.
- Se crea un índice GiST para consultas geoespaciales de puntos de interés.
- Leaflet y los mapas usan recursos externos; para un entorno 100% offline deben servirse localmente.
- Las rutas históricas de pedidos y reportes no forman parte de la aplicación activa.
- Los scripts en `docker-entrypoint-initdb.d` solo se ejecutan al crear un volumen nuevo de PostgreSQL. Para cambios futuros de esquema se recomienda incorporar una estrategia de migraciones versionadas.
- Para entornos no locales se recomienda definir límites de recursos, rotación de logs y una política periódica de backups.

## Despliegue seguro en Render

Requisitos previos:

- Repositorio sin archivo `.env` real.
- Web Service Docker en Render usando `backend/Dockerfile`.
- Base de datos Render PostgreSQL administrada, preferiblemente con PostGIS disponible.
- Variables sensibles configuradas desde el panel de Render, no en el código fuente.

Variables de entorno necesarias:

```text
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=<connection-string-de-render-postgresql>
DELIVERY_SECRET_KEY=<secret-key-segura>
DELIVERY_ADMIN_EMAIL=<email-admin>
DELIVERY_ADMIN_PASSWORD=<password-admin-seguro>
ALLOWED_ORIGINS=https://nombre-servicio.onrender.com
```

La aplicación también conserva compatibilidad local con variables separadas:

```text
DELIVERY_DB_HOST=database
DELIVERY_DB_PORT=5432
DELIVERY_DB_NAME=routebite_db
DELIVERY_DB_USER=routebite_user
DELIVERY_DB_PASSWORD=<password>
```

Pasos recomendados:

1. Crear una base de datos PostgreSQL administrada en Render.
2. Copiar la variable `DATABASE_URL` desde Render PostgreSQL hacia el Web Service.
3. Crear un Web Service con runtime Docker y `backend/Dockerfile`.
4. Configurar el Health Check Path como `/api/health`.
5. Definir `ALLOWED_ORIGINS` con el dominio real de Render o dominio personalizado.
6. Confirmar que `DEBUG=false` en producción.

Validación en Render:

```bash
curl https://NOMBRE-SERVICIO.onrender.com
curl https://NOMBRE-SERVICIO.onrender.com/api/health
curl -I https://NOMBRE-SERVICIO.onrender.com/docs
curl -I https://NOMBRE-SERVICIO.onrender.com/openapi.json
```

Checklist de seguridad:

- `.env` no debe estar versionado.
- `.env.example` no debe contener secretos reales.
- `DELIVERY_SECRET_KEY` debe ser único y fuerte.
- `DATABASE_URL` debe venir de Render PostgreSQL.
- `DEBUG` debe ser `false`.
- `ALLOWED_ORIGINS` no debe usar `*` en producción.
- `/api/health` debe responder sin exponer secretos ni detalles internos.
- Login, JWT y endpoints protegidos deben probarse después del despliegue.

## Credenciales De Demostración

La interfaz no requiere inicio de sesión. Si se desea probar la autenticación opcional:

```text
admin@routebite.example.com
Admin12345
```
