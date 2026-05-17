from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging

from app.database import engine, Base
from app.routers import (
    projects_router,
    documents_router,
    words_router,
    labels_router,
    segmentation_router,
    layout_types_router,
    layout_regions_router,
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# Crear tablas en la BD
Base.metadata.create_all(bind=engine)

# Crear directorio de uploads
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

app = FastAPI(
    title="Etiquetado de Manuscritos API",
    description="API para el etiquetado de texto de documentos manuscritos palabra a palabra",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — permitir frontend en desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Servir imágenes subidas de forma estática
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# Registrar routers
app.include_router(projects_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(words_router, prefix="/api/v1")
app.include_router(labels_router, prefix="/api/v1")
app.include_router(segmentation_router, prefix="/api/v1")
app.include_router(layout_types_router, prefix="/api/v1")
app.include_router(layout_regions_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "app": "Etiquetado de Manuscritos",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
