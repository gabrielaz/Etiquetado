"""
Servicio de gestión de imágenes: carga, validación y utilidades.
"""

import os
import uuid
from PIL import Image
from fastapi import UploadFile, HTTPException
import logging

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
# Formatos que el navegador no puede mostrar → se convierten a PNG
CONVERT_TO_PNG = {".tif", ".tiff", ".bmp"}
MAX_FILE_SIZE_MB = 50


def get_upload_dir() -> str:
    base = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
    os.makedirs(base, exist_ok=True)
    return os.path.abspath(base)


async def save_uploaded_image(file: UploadFile, project_id: int) -> dict:
    """
    Guarda la imagen subida y devuelve metadatos.
    Returns: dict con filename, file_path, image_width, image_height
    """
    # Validar extensión
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado. Usa: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Generar nombre único
    unique_name = f"{uuid.uuid4().hex}{ext}"

    # Crear directorio por proyecto
    project_dir = os.path.join(get_upload_dir(), str(project_id))
    os.makedirs(project_dir, exist_ok=True)

    file_path = os.path.join(project_dir, unique_name)

    # Guardar archivo
    content = await file.read()

    # Validar tamaño
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo supera el límite de {MAX_FILE_SIZE_MB} MB"
        )

    with open(file_path, "wb") as f:
        f.write(content)

    # Convertir formatos no soportados por el navegador → PNG
    if ext in CONVERT_TO_PNG:
        try:
            png_name = f"{os.path.splitext(unique_name)[0]}.png"
            png_path = os.path.join(project_dir, png_name)
            with Image.open(file_path) as img:
                # Convertir a RGB para evitar problemas con capas alpha o CMYK
                rgb = img.convert("RGB")
                rgb.save(png_path, "PNG")
            os.remove(file_path)
            unique_name = png_name
            file_path = png_path
            logger.info(f"Imagen TIF/BMP convertida a PNG: {png_path}")
        except Exception as e:
            logger.warning(f"No se pudo convertir {file_path} a PNG: {e}")

    # Obtener dimensiones
    try:
        with Image.open(file_path) as img:
            width, height = img.size
    except Exception:
        width, height = None, None

    logger.info(f"Imagen guardada: {file_path} ({width}x{height})")

    return {
        "filename": unique_name,
        "original_filename": file.filename,
        "file_path": file_path,
        "image_width": width,
        "image_height": height,
    }


def delete_image_file(file_path: str) -> None:
    """Elimina el archivo de imagen del disco."""
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"Imagen eliminada: {file_path}")


def get_image_url(filename: str, project_id: int) -> str:
    """Construye la URL pública de la imagen."""
    return f"/uploads/{project_id}/{filename}"
