from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, mesas, productos, consumos, reportes, users, turnos, arqueo, categorias, gastos
from app.database import Base, engine

from fastapi.staticfiles import StaticFiles
from pathlib import Path


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Billar API")

# Servir archivos estáticos (imágenes)
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    #"https://billarfrontendreact-production.up.railway.app",
   #"https://billartiochichi-production.up.railway.app", #nueva que estamos usando
]

#Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#rutas de la API
app.include_router(auth.router)
app.include_router(mesas.router)
app.include_router(productos.router)
app.include_router(consumos.router)
app.include_router(reportes.router)
app.include_router(users.router)
app.include_router(turnos.router)
app.include_router(arqueo.router)
app.include_router(categorias.router)
app.include_router(gastos.router)
