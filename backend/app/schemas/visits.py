from pydantic import BaseModel, Field


class VisitTrackRequest(BaseModel):
    path: str = Field(min_length=1, max_length=255)


class PageStat(BaseModel):
    path: str
    label: str
    count: int


class DailyVisitStat(BaseModel):
    day: str
    visits: int
    unique_visitors: int


class VisitStatsResponse(BaseModel):
    today: int
    week: int
    month: int
    total: int
    unique_today: int
    unique_week: int
    top_pages: list[PageStat]
    daily: list[DailyVisitStat]
