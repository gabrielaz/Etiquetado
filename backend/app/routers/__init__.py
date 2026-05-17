from app.routers.projects import router as projects_router
from app.routers.documents import router as documents_router
from app.routers.words import router as words_router
from app.routers.labels import router as labels_router
from app.routers.segmentation import router as segmentation_router
from app.routers.layout import types_router as layout_types_router
from app.routers.layout import regions_router as layout_regions_router

__all__ = [
    "projects_router",
    "documents_router",
    "words_router",
    "labels_router",
    "segmentation_router",
    "layout_types_router",
    "layout_regions_router",
]
