from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import IssueCategory, IssueStatus, Priority


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[IssueStatus] = mapped_column(String(50), default=IssueStatus.NEW, index=True)
    category: Mapped[IssueCategory | None] = mapped_column(String(100), index=True)
    priority: Mapped[Priority] = mapped_column(String(20), default=Priority.MEDIUM)
    address: Mapped[str | None] = mapped_column(String(500))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    vk_message_id: Mapped[int | None] = mapped_column(BigInteger)
    vk_peer_id: Mapped[int | None] = mapped_column(BigInteger)
    resident_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    parent_issue_id: Mapped[int | None] = mapped_column(ForeignKey("issues.id"))
    confirmation_count: Mapped[int] = mapped_column(Integer, default=1)
    is_spam: Mapped[bool] = mapped_column(default=False)
    resolution_text: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    resident: Mapped["User | None"] = relationship(
        back_populates="issues", foreign_keys=[resident_id]
    )
    assignee: Mapped["User | None"] = relationship(
        back_populates="assigned_issues", foreign_keys=[assignee_id]
    )
    department: Mapped["Department | None"] = relationship(back_populates="issues")
    parent_issue: Mapped["Issue | None"] = relationship(
        remote_side="Issue.id", back_populates="duplicates"
    )
    duplicates: Mapped[list["Issue"]] = relationship(back_populates="parent_issue")
    photos: Mapped[list["IssuePhoto"]] = relationship(back_populates="issue", cascade="all, delete-orphan")
    comments: Mapped[list["IssueComment"]] = relationship(back_populates="issue", cascade="all, delete-orphan")
    duplicate_links: Mapped[list["IssueDuplicate"]] = relationship(
        back_populates="issue", foreign_keys="IssueDuplicate.issue_id", cascade="all, delete-orphan"
    )
    ai_analysis: Mapped["AIAnalysis | None"] = relationship(back_populates="issue", uselist=False)


class IssuePhoto(Base):
    __tablename__ = "issue_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    vk_photo_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    issue: Mapped["Issue"] = relationship(back_populates="photos")


class IssueComment(Base):
    __tablename__ = "issue_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    issue: Mapped["Issue"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(back_populates="comments")


class IssueDuplicate(Base):
    __tablename__ = "issue_duplicates"

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    duplicate_of_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    issue: Mapped["Issue"] = relationship(back_populates="duplicate_links", foreign_keys=[issue_id])


from app.models.user import User  # noqa: E402
from app.models.department import Department  # noqa: E402
from app.models.ai_analysis import AIAnalysis  # noqa: E402
