from fastapi import APIRouter
from .api_routes import router as api_routes_router
from .generate_api import router as generate_router
from .language_api import router as language_router
from .monitoring_api import router as monitoring_router
from .knowledge_api import router as knowledge_router
from .pattern_api import router as pattern_router
from .adaptation_api import router as adaptation_router
from .narrative_api import router as narrative_router
from .version_api import router as version_router

api_router = APIRouter()
api_router.include_router(api_routes_router, prefix="/api/v1")
api_router.include_router(generate_router)
api_router.include_router(language_router)
api_router.include_router(knowledge_router)
api_router.include_router(monitoring_router)
api_router.include_router(pattern_router)
api_router.include_router(adaptation_router)
api_router.include_router(narrative_router)
api_router.include_router(version_router) 