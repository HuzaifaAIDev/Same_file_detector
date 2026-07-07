from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ComparePathsRequest(BaseModel):
    """Legacy path-based comparison. Disabled by default — see
    settings.ENABLE_LOCAL_PATH_COMPARE."""

    base_files: list[str] = Field(..., min_length=1)
    compare_files: list[str] = Field(..., min_length=1)


class ComparisonResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_name: str
    score: float
    status: str
    message: str | None = None


class ComparisonJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    base_file_count: int
    compare_file_count: int
    created_at: datetime
    error_message: str | None = None
    results: list[ComparisonResultOut] = []


class ComparisonJobSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    base_file_count: int
    compare_file_count: int
    created_at: datetime
