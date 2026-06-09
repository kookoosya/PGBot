from pydantic import BaseModel


class CategoryStat(BaseModel):
    category: str
    count: int


class MonthlyStat(BaseModel):
    month: str
    count: int
    resolved: int


class StreetStat(BaseModel):
    street: str
    count: int


class StatisticsResponse(BaseModel):
    total_issues: int
    resolved_issues: int
    in_progress_issues: int
    rejected_issues: int
    avg_resolution_hours: float | None
    top_categories: list[CategoryStat]
    top_streets: list[StreetStat]
    monthly_dynamics: list[MonthlyStat]
