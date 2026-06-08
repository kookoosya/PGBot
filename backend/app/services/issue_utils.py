from app.models.issue import Issue


def issue_display_summary(issue: Issue, *, max_len: int = 100) -> str:
    if issue.ai_analysis and issue.ai_analysis.summary:
        return issue.ai_analysis.summary
    return issue.description[:max_len]
