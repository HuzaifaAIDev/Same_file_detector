import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging_config import configure_logging, get_logger
from app.core.seed import seed_admin_and_test_users
from app.database.session import SessionLocal, init_db
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("%s starting up (environment=%s)", settings.APP_NAME, settings.ENVIRONMENT)
    init_db()
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        seed_admin_and_test_users(db)
    finally:
        db.close()

    yield
    logger.info("%s shutting down", settings.APP_NAME)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="2.0.0",
        description="Enterprise-ready document similarity & intelligence platform.",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # ------------------------------------------------------------------
    # Frontend (server-rendered UI + static assets), kept for parity
    # with the original app's /ui page.
    # ------------------------------------------------------------------
    from pathlib import Path

    frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
    app.mount("/static", StaticFiles(directory=frontend_dir / "static"), name="static")
    templates = Jinja2Templates(directory=frontend_dir / "templates")

    @app.get("/", response_class=HTMLResponse, tags=["ui"])
    async def ui_home(request: Request):
        return templates.TemplateResponse(request=request, name="index.html")

    @app.get("/api", tags=["health"])
    def api_root():
        return {"success": True, "message": f"{settings.APP_NAME} API running."}

    # ------------------------------------------------------------------
    # Exception handlers — never leak stack traces to the client.
    # ------------------------------------------------------------------
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": exc.message},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Validation error.",
                "errors": jsonable_encoder(exc.errors()),
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception on %s: %s\n%s", request.url.path, exc, traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Internal server error."},
        )

    return app


app = create_app()
