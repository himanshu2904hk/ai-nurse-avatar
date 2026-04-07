"""
################################################################################
#                                                                              #
#                    PATIENT PRE-ASSESSMENT SYSTEM                             #
#                         FastAPI Application                                  #
#                                                                              #
#   Description: Backend API for Tavus AI Avatar patient intake system        #
#   Database:    PostgreSQL (3 tables: registry, assessment, visits)          #
#   Endpoints:   /api/tool/lookup_patient                                     #
#                /api/tool/store_patient                                       #
#                /api/tool/update_complaint                                    #
#                                                                              #
################################################################################
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.middleware import RequestLoggingMiddleware
from app.api.routes import tool_routes
from app.db.postgres_base import init_postgres, close_postgres, create_tables


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                           INITIALIZATION                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Patient Pre-Assessment API for Tavus AI Avatar",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                            MIDDLEWARE                                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for tool calls
    allow_credentials=False,  # Must be False when using wildcard origin
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                              ROUTES                                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝

app.include_router(tool_routes.router, prefix="/api")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                         LIFECYCLE EVENTS                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    try:
        init_postgres()
        await create_tables()
        logger.info("PostgreSQL connected — 3 tables ready (patient_registry, patient_assessment, patient_visits)")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    logger.info("Shutting down application")
    await close_postgres()


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                          HEALTH ENDPOINTS                                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                         ERROR HANDLING                                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": str(exc) if settings.DEBUG else "Internal server error"}
    )


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                      STATIC FILE SERVING (FRONTEND)                       ║
# ║                                                                          ║
# ║   Must be LAST — after all API routes, so /api/* is matched first.       ║
# ║   Serves frontend files at / so ngrok users get the full app.            ║
# ╚══════════════════════════════════════════════════════════════════════════╝

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                           MAIN ENTRY                                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
