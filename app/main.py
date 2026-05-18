"""
Application principale FastAPI - Chatbot L0027
Statut Général des Agents de l'État de la République de Guinée
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from contextlib import asynccontextmanager
import logging
import time
from pathlib import Path
import os

from app.core.config import get_settings
from app.api.routes import router as api_router
from app.db.database import init_db, close_db, check_db_connection
from app.services.cache_service import redis_cache
from app.services.vector_service import vector_store
from app.services.llm_service import llm_service
from app.services.rag_service import initialize_rag_service
from app.models.schemas import HealthResponse, ErrorResponse

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('chatbot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

settings = get_settings()


# ============================================================================
# MIDDLEWARE PERSONNALISÉ POUR AUTORISER L'EMBEDDING EN IFRAME
# ============================================================================

class FrameOptionsMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour autoriser l'embedding du chatbot en iframe.
    
    Ce middleware ajoute l'en-tête Content-Security-Policy avec frame-ancestors
    pour autoriser certains domaines à afficher le chatbot dans une iframe.
    
    X-Frame-Options est obsolète et remplacé par CSP frame-ancestors.
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Liste des domaines autorisés à afficher le chatbot en iframe
        # En mode DEBUG, on ajoute automatiquement localhost
        frame_ancestors = ["'self'"] + settings.frame_ancestors
        
        if settings.DEBUG:
            # En développement, autoriser localhost sur différents ports
            frame_ancestors.extend([
                "http://localhost:5173",     # Vite
                "http://localhost:3000",     # React/Next
                "http://localhost:8080",     # Alternative
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080",
            ])
            logger.debug(f"🔓 Mode DEBUG: {len(frame_ancestors)} domaines autorisés pour iframe")
        
        # Construire l'en-tête Content-Security-Policy
        csp_value = f"frame-ancestors {' '.join(set(frame_ancestors))}"
        response.headers["Content-Security-Policy"] = csp_value
        
        # IMPORTANT: Retirer X-Frame-Options s'il existe
        # X-Frame-Options est obsolète et peut entrer en conflit avec CSP
        if "X-Frame-Options" in response.headers:
            del response.headers["X-Frame-Options"]
            logger.debug("🗑️  X-Frame-Options retiré (remplacé par CSP)")
        
        # Logger uniquement pour les routes du widget
        if "/widget" in request.url.path or request.url.path.endswith(".html"):
            logger.info(f"🖼️  Widget servi avec CSP: frame-ancestors activé pour {len(frame_ancestors)} domaines")
        
        return response


# ============================================================================
# CYCLE DE VIE DE L'APPLICATION
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    logger.info("🚀 Démarrage du Chatbot L0027...")
    
    # Initialisation des services
    try:
        # Base de données PostgreSQL
        logger.info("📦 Connexion à PostgreSQL...")
        await init_db()
        
        # Cache Redis
        logger.info("📦 Connexion à Redis...")
        await redis_cache.connect()
        
        # Vector Store Qdrant
        logger.info("📦 Connexion à Qdrant...")
        await vector_store.connect()
        
        # Service LLM
        logger.info("🤖 Initialisation des LLMs...")
        await llm_service.initialize()
        
        # Service RAG
        logger.info("📚 Chargement des données de la loi...")
        data_dir = Path(settings.DATA_DIR)
        await initialize_rag_service(
            law_path=str(data_dir / settings.LAW_FILE),
            qa_path=str(data_dir / settings.QA_FILE)
        )
        
        logger.info("✅ Chatbot L0027 démarré avec succès!")
        logger.info(f"📍 API disponible sur http://{settings.API_HOST}:{settings.API_PORT}")
        
        # Afficher la configuration iframe
        if settings.frame_ancestors:
            logger.info(f"🖼️  Iframe autorisée pour {len(settings.frame_ancestors)} domaine(s)")
            for domain in settings.frame_ancestors:
                logger.info(f"   ✓ {domain}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage: {e}")
        raise
    
    yield
    
    # Arrêt propre
    logger.info("🛑 Arrêt du Chatbot L0027...")
    await close_db()
    await redis_cache.disconnect()
    await vector_store.disconnect()
    logger.info("👋 Au revoir!")


# ============================================================================
# CRÉATION DE L'APPLICATION FASTAPI
# ============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "Questions",
            "description": "Endpoints pour poser des questions sur la loi L0027"
        },
        {
            "name": "Recherche",
            "description": "Endpoints de recherche dans les articles"
        },
        {
            "name": "Suggestions",
            "description": "Suggestions de questions"
        },
        {
            "name": "Informations",
            "description": "Informations sur la loi et le système"
        },
        {
            "name": "Administration",
            "description": "Endpoints d'administration"
        }
    ]
)


# ============================================================================
# MIDDLEWARES
# ============================================================================

# 1. CORS - Pour les requêtes API (fetch, XHR)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Frame Options - Pour autoriser l'embedding en iframe
app.add_middleware(FrameOptionsMiddleware)

# 3. Compression GZip
app.add_middleware(GZipMiddleware, minimum_size=1000)


# 4. Middleware de timing
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    """Middleware pour mesurer le temps de réponse"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response


# 5. Middleware de logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware pour logger les requêtes"""
    logger.info(f"📥 {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"📤 {request.method} {request.url.path} - {response.status_code}")
    return response


# ============================================================================
# FICHIERS STATIQUES ET WIDGET
# ============================================================================

# Fichiers statiques pour le frontend
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    logger.info(f"📁 Fichiers statiques montés depuis: {FRONTEND_DIR}")


# Route pour servir le widget directement
@app.get("/", include_in_schema=False)
async def serve_widget():
    """
    Sert le widget de chat pour l'intégration iframe.
    
    Le widget sera automatiquement autorisé pour l'embedding grâce au
    FrameOptionsMiddleware qui ajoute les en-têtes CSP appropriés.
    """
    widget_path = FRONTEND_DIR / "widget.html"
    if widget_path.exists():
        logger.info(f"📄 Serving widget from: {widget_path}")
        return FileResponse(
            widget_path,
            media_type="text/html",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    logger.error(f"❌ Widget not found at: {widget_path}")
    raise HTTPException(status_code=404, detail="Widget non trouvé")


# Route pour le script d'intégration
@app.get("/embed.js", include_in_schema=False)
async def serve_embed_script():
    """Sert le script d'intégration JavaScript"""
    script_path = FRONTEND_DIR / "embed.js"
    if script_path.exists():
        return FileResponse(
            script_path,
            media_type="application/javascript",
            headers={
                "Cache-Control": "public, max-age=3600"
            }
        )
    raise HTTPException(status_code=404, detail="Script non trouvé")


# ============================================================================
# ROUTES API
# ============================================================================

# Inclusion des routes API
app.include_router(
    api_router,
    prefix=settings.API_PREFIX,
    tags=["API"]
)


# ============================================================================
# ROUTES DE BASE
# ============================================================================


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="État de santé du système",
    tags=["Administration"]
)
async def health_check():
    """Vérifie l'état de santé de tous les services"""
    # Vérifie chaque service
    db_ok = await check_db_connection()
    redis_ok = await redis_cache.health_check()
    qdrant_ok = await vector_store.health_check()
    llm_health = await llm_service.check_providers_health()
    
    # Détermine le statut global
    all_ok = db_ok and redis_ok and qdrant_ok and any(llm_health.values())
    status = "healthy" if all_ok else "degraded"
    
    return HealthResponse(
        status=status,
        version=settings.APP_VERSION,
        database=db_ok,
        redis=redis_ok,
        qdrant=qdrant_ok,
        llm_providers=llm_health
    )


@app.get(
    "/ready",
    summary="Vérification de disponibilité",
    tags=["Administration"]
)
async def readiness_check():
    """Vérifie si le service est prêt à recevoir des requêtes"""
    try:
        # Vérifie les services critiques
        redis_ok = await redis_cache.health_check()
        qdrant_ok = await vector_store.health_check()
        
        if not redis_ok or not qdrant_ok:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "message": "Services non disponibles"}
            )
        
        return {"status": "ready"}
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)}
        )


# ============================================================================
# GESTIONNAIRES D'ERREURS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Gestionnaire d'erreurs HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "code": f"HTTP_{exc.status_code}",
            "path": request.url.path
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Gestionnaire d'erreurs génériques"""
    logger.error(f"Erreur non gérée: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Une erreur interne s'est produite",
            "code": "INTERNAL_ERROR"
        }
    )


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        workers=1,
        log_level="info"
    )