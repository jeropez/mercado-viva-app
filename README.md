# Mercado VIVA — Gestión de Inventario

MVP con dos módulos: **Cliente** (marketplace) y **Administrador** (panel técnico
de inventario), ambos con registro e inicio de sesión propios. Implementa el
documento actualizado del ciclo de vida de software: HU-1 a HU-10.

## Qué incluye

- **Cliente**: crea perfil, inicia sesión, navega el catálogo por sede,
  compra con actualización de inventario en tiempo real, recibe sugerencias
  de producto o sede alterna cuando algo no tiene stock, y en el checkout
  ingresa sus datos de **facturación** y de **residencia/entrega**.
- **Administrador**: crea perfil eligiendo la sede que va a gestionar, inicia
  sesión, agrega/elimina/actualiza productos y consulta el inventario
  completo de su sede — nunca puede tocar otra sede.
- Backend en **FastAPI**, base de datos con **SQLAlchemy** (SQLite en local,
  PostgreSQL en Render), autenticación con **JWT** y contraseñas con **bcrypt**.
- Frontend en HTML/CSS/JS puro (sin frameworks), con la paleta de marca
  solicitada y comentarios en el código marcando dónde insertar el logo real.

## Estructura del proyecto

```
mercado-viva-app/
├── backend/
│   ├── main.py            # App FastAPI, sirve la API y el frontend
│   ├── database.py        # Conexión SQLAlchemy (SQLite / PostgreSQL)
│   ├── models.py          # Modelos ORM
│   ├── schemas.py         # Esquemas Pydantic (validación)
│   ├── auth.py             # JWT + hashing de contraseñas
│   ├── seed.py             # Datos de ejemplo (2 sedes, 11 productos)
│   ├── requirements.txt
│   ├── .env.example
│   └── routers/
│       ├── auth_router.py     # Registro / login (cliente y admin)
│       ├── cliente_router.py  # Catálogo, checkout, historial
│       └── admin_router.py    # CRUD de productos por sede
├── frontend/
│   ├── index.html          # Marketplace (cliente)
│   ├── admin.html          # Panel técnico (administrador)
│   ├── css/
│   │   ├── variables.css   # Paleta de marca compartida
│   │   ├── cliente.css
│   │   └── admin.css
│   ├── js/
│   │   ├── cliente.js
│   │   └── admin.js
│   └── img/                 # Coloca aquí tu logo (ver sección "Insertar el logo")
└── render.yaml               # Despliegue automático en Render
```

## Cómo ejecutar en local

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Abre `http://localhost:8000/` (cliente) y `http://localhost:8000/admin`
(administrador). La base de datos SQLite se crea sola con datos de ejemplo
la primera vez.

> Si ves un error de `email-validator`, corre `pip install email-validator`.
> Si ves un error de `pip` por permisos en Windows, usa un entorno virtual
> (`python -m venv venv` → `venv\Scripts\activate`) antes de instalar.

## Insertar el logo real

Hay 4 puntos marcados en el código con comentarios `INSERCIÓN DE LOGO`:

1. `frontend/index.html` → barra superior del cliente (`.marca__logo`)
2. `frontend/index.html` → banner principal, imagen grande (`.hero__imagen-slot`)
3. `frontend/admin.html` → pantalla de login del admin (`.login-admin__logo`)
4. `frontend/admin.html` → sidebar del dashboard (`.sidebar__logo`)

Coloca tu archivo de logo en `frontend/img/logo.png` (y uno más grande para
el banner si quieres, ej. `frontend/img/banner-logo.png`), y en cada punto
reemplaza el `<div>` marcado por un `<img src="/img/logo.png" ...>`, tal como
indica el comentario en ese lugar del código.

Las imágenes de producto no se suben como archivo: el catálogo guarda una
**URL** de imagen (campo "url de la imagen" al crear un producto desde el
panel admin), porque Render no ofrece almacenamiento de archivos persistente
por defecto.

## Paleta de colores

| Variable CSS | Color | Uso |
|---|---|---|
| `--color-texto` | `#3E333A` | Texto, sidebar del admin |
| `--color-primario` | `#F5F06E` | Color primario, banner principal |
| `--color-teal` | `#A0E0DC` | Acentos informativos, badges |
| `--color-fondo` | `#EFF7F3` | Fondo general |
| `--color-coral` | `#F5865A` | Acciones destacadas, alertas |

Definida una sola vez en `frontend/css/variables.css`.

---

## Despliegue en Render

### Opción A — Automática con `render.yaml` (recomendada)

1. Sube este proyecto a un repositorio de GitHub.
2. En [Render](https://render.com), ve a **New → Blueprint**.
3. Selecciona tu repositorio. Render detecta `render.yaml` y crea:
   - Un **Web Service** para el backend (que también sirve el frontend).
   - Una base de datos **PostgreSQL** gestionada, ya conectada por la
     variable `DATABASE_URL`.
4. Espera a que termine el build (instala `requirements.txt` y arranca con
   `uvicorn main:app --host 0.0.0.0 --port $PORT`).
5. Al iniciar, la app crea las tablas automáticamente y carga los datos de
   ejemplo (2 sedes, 11 productos) si la base de datos está vacía.
6. Tu app queda disponible en la URL que Render te asigna, por ejemplo
   `https://mercado-viva-api.onrender.com`.

### Opción B — Manual desde el panel de Render

1. **Crear la base de datos**: New → PostgreSQL → nómbrala `mercado-viva-db`
   → plan Free → Create Database. Copia la "Internal Database URL".
2. **Crear el Web Service**: New → Web Service → conecta tu repositorio.
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. **Variables de entorno** del Web Service:
   - `DATABASE_URL` → pega la Internal Database URL del paso 1
   - `JWT_SECRET` → cualquier cadena larga y aleatoria
   - `ALLOWED_ORIGINS` → `*` (o el dominio real si separas el frontend)
4. Create Web Service y espera el despliegue.

### Notas importantes para producción

- **No subas tu `.env` real** al repositorio; usa `.env.example` como
  referencia y configura las variables desde el panel de Render.
- El plan gratuito de Render "duerme" el servicio tras un rato sin uso; la
  primera petición después de dormir tarda unos segundos más.
- Si más adelante separas el frontend a otro servicio (por ejemplo Netlify),
  cambia `const API = ""` por la URL completa del backend en
  `frontend/js/cliente.js` y `frontend/js/admin.js`, y ajusta
  `ALLOWED_ORIGINS` al dominio real del frontend en vez de `*`.
