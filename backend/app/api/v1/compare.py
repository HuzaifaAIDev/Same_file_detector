import uuid

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.core.logging_config import get_logger
from app.database.session import get_db
from app.models.user import User
from app.repositories.comparison_repository import ComparisonRepository
from app.schemas.compare import (
    ComparePathsRequest,
    ComparisonJobOut,
    ComparisonJobSummaryOut,
)
from app.services.comparison_service import run_comparison, save_comparison_job
from app.utils.file_validation import resolve_safe_local_path, save_upload

router = APIRouter(prefix="/compare", tags=["compare"])
logger = get_logger(__name__)


@router.post("", response_model=ComparisonJobOut, status_code=201)
async def compare_uploaded_files(
    base_files: list[UploadFile],
    compare_files: list[UploadFile],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload BASE and COMPARE files directly and run the comparison.
    This is the primary, secure comparison endpoint — no server file
    paths are ever taken from the client."""
    total_files = len(base_files) + len(compare_files)
    if total_files > settings.MAX_FILES_PER_REQUEST:
        raise ValidationAppError(
            f"Too many files in one request (max {settings.MAX_FILES_PER_REQUEST})."
        )

    job_dir = settings.UPLOAD_DIR / uuid.uuid4().hex

    base_paths: dict[str, str] = {}
    for f in base_files:
        display_name, path = await save_upload(f, job_dir / "base")
        base_paths[display_name] = str(path)

    compare_paths: dict[str, str] = {}
    for f in compare_files:
        display_name, path = await save_upload(f, job_dir / "compare")
        compare_paths[display_name] = str(path)

    results, error_message = run_comparison(base_paths, compare_paths)

    job = save_comparison_job(
        db=db,
        user_id=current_user.id,
        base_count=len(base_paths),
        compare_count=len(compare_paths),
        results=results,
        error_message=error_message,
    )

    if error_message:
        raise ValidationAppError(error_message)

    return job


@router.post("/paths", response_model=ComparisonJobOut, status_code=201)
def compare_local_paths(
    payload: ComparePathsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Legacy behaviour preserved from the original app: compare files
    already present on the server by path. Disabled by default because
    it allows reading arbitrary server files; enable only for trusted,
    single-user, local deployments via ENABLE_LOCAL_PATH_COMPARE=true.
    When enabled, paths are still sandboxed to ALLOWED_LOCAL_ROOT."""
    if not settings.ENABLE_LOCAL_PATH_COMPARE:
        raise ForbiddenError(
            "Path-based comparison is disabled. Upload files via POST /api/v1/compare instead, "
            "or set ENABLE_LOCAL_PATH_COMPARE=true for trusted local use."
        )

    base_paths = {p: str(resolve_safe_local_path(p)) for p in payload.base_files}
    compare_paths = {p: str(resolve_safe_local_path(p)) for p in payload.compare_files}

    results, error_message = run_comparison(base_paths, compare_paths)

    job = save_comparison_job(
        db=db,
        user_id=current_user.id,
        base_count=len(base_paths),
        compare_count=len(compare_paths),
        results=results,
        error_message=error_message,
    )

    if error_message:
        raise ValidationAppError(error_message)

    return job


@router.get("/history", response_model=list[ComparisonJobSummaryOut])
def comparison_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ComparisonRepository(db).list_for_user(current_user.id, limit=limit, offset=offset)


@router.get("/history/{job_id}", response_model=ComparisonJobOut)
def comparison_detail(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = ComparisonRepository(db).get_by_id_for_user(job_id, current_user.id)
    if not job:
        raise NotFoundError("Comparison job not found.")
    return job
