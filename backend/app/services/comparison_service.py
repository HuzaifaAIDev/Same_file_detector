"""
Comparison orchestration.

Compares a set of BASE files against a set of COMPARE files using text
extraction + fuzzy similarity, and persists the job/results for the
requesting user.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import get_logger
from app.models.comparison import ComparisonJob, ComparisonResult
from app.services.extraction_service import extract, similarity

logger = get_logger(__name__)

EXACT_THRESHOLD = 90.0
SIMILAR_THRESHOLD = 75.0


@dataclass
class FileResult:
    file_name: str
    score: float
    status: str
    message: str | None = None


def _classify(score: float) -> str:
    if score >= EXACT_THRESHOLD:
        return "EXACT"
    if score >= SIMILAR_THRESHOLD:
        return "SIMILAR"
    return "DIFFERENT"


def _compare_one(file_name: str, file_path: str, base_text: str) -> FileResult:
    try:
        compare_text = extract(file_path)
        score = round(similarity(base_text, compare_text), 2)
        return FileResult(file_name=file_name, score=score, status=_classify(score))
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Comparison failed for %s", file_name)
        return FileResult(file_name=file_name, score=0.0, status="ERROR", message=str(exc))


def run_comparison(
    base_paths: dict[str, str],
    compare_paths: dict[str, str],
) -> tuple[list[FileResult], str | None]:
    """
    base_paths / compare_paths: {display_name: absolute_path_on_disk}
    Returns (results, error_message).
    """
    base_texts = [extract(p) for p in base_paths.values()]
    base_text = " ".join(t for t in base_texts if t).strip()

    if not base_text:
        return [], "No text could be extracted from the BASE files."

    results: list[FileResult] = []
    with ThreadPoolExecutor(max_workers=settings.COMPARISON_WORKERS) as executor:
        futures = [
            executor.submit(_compare_one, name, path, base_text)
            for name, path in compare_paths.items()
        ]
        for future in futures:
            results.append(future.result())

    return results, None


def save_comparison_job(
    db: Session,
    user_id: str,
    base_count: int,
    compare_count: int,
    results: list[FileResult],
    error_message: str | None = None,
) -> ComparisonJob:
    job = ComparisonJob(
        user_id=user_id,
        status="failed" if error_message else "completed",
        base_file_count=base_count,
        compare_file_count=compare_count,
        error_message=error_message,
    )
    db.add(job)
    db.flush()

    for r in results:
        db.add(
            ComparisonResult(
                job_id=job.id,
                file_name=r.file_name,
                score=r.score,
                status=r.status,
                message=r.message,
            )
        )

    db.commit()
    db.refresh(job)
    return job
