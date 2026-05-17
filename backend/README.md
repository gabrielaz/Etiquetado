# Etiquetado de Manuscritos — Backend

API REST construida con **FastAPI** para el etiquetado de texto en documentos manuscritos.

## Requisitos
- Python 3.11+
- pip

## Instalación

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Iniciar el servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Documentación interactiva

- Swagger UI: http://localhost:8000/docs
- ReDoc:       http://localhost:8000/redoc

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | /api/v1/projects | Listar proyectos |
| POST   | /api/v1/projects | Crear proyecto |
| POST   | /api/v1/projects/{id}/documents | Subir documento (imagen) |
| GET    | /api/v1/documents/{id}/image | Obtener imagen |
| POST   | /api/v1/documents/{id}/segment | Previsualizar segmentación asistida |
| POST   | /api/v1/documents/{id}/segment/apply | Aplicar y guardar segmentación |
| GET    | /api/v1/documents/{id}/words | Listar palabras del documento |
| POST   | /api/v1/documents/{id}/words/{wid}/labels | Asignar etiqueta a palabra |

## Métodos de segmentación asistida

| Método | Descripción | Mejor para |
|--------|-------------|------------|
| `contour` | Contornos morfológicos | Escritura aislada, letras separadas |
| `projection` | Proyección H/V | Documentos con líneas regulares |
| `mser` | Regiones estables (MSER) | Texto denso, fondos complejos |

## Estructura del proyecto

```
backend/
├── app/
│   ├── main.py              # Punto de entrada FastAPI
│   ├── database.py          # Configuración SQLite/SQLAlchemy
│   ├── models/              # Modelos ORM
│   │   ├── project.py
│   │   ├── document.py
│   │   ├── word.py
│   │   └── label.py
│   ├── schemas/             # Schemas Pydantic (validación)
│   ├── routers/             # Endpoints REST
│   │   ├── projects.py
│   │   ├── documents.py
│   │   ├── words.py
│   │   ├── labels.py
│   │   └── segmentation.py  ← segmentación asistida
│   └── services/
│       ├── image_service.py
│       └── segmentation_service.py  ← OpenCV
├── uploads/                 # Imágenes subidas (gitignored)
├── etiquetado.db            # SQLite (gitignored)
└── requirements.txt
```
