"""
SQLAlchemy ORM models (database schema)

"""

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, BigInteger, DateTime, Text, func, UniqueConstraint


class Base(DeclarativeBase):
    #  Base class for ORM models
    pass

class EtlRunLog(Base):
    # Track pipeline run

    __tablename__ = "etl_run_log"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False) #business identifier - string

    status: Mapped[str] = mapped_column(String(16), nullable=False)

    started_at: Mapped[DateTime] = mapped_column( DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[DateTime | None] = mapped_column( DateTime(timezone=True), nullable=True)

    message: Mapped[str | None] = mapped_column(Text, nullable=True)


class PostsRaw(Base):
    # landing table for posts from API

    __tablename__= "posts_raw"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False) #VARCHAR(512) Text/CLOB

    #metadata
    ingested_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    ingested_at_epoch_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)

    #Duplicate Checker - tuple
    __table_args__ = (UniqueConstraint("id", name="uq_posts_raw_id"),
                      )


class PostsEnriched(Base):
    #Curated / transformed table

    __tablename__ = "posts_enriched"

    post_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_name: Mapped[str] = mapped_column(String(256), nullable=False)
    user_email: Mapped[str] = mapped_column(String(256), nullable=False) #no email check, validation should be from Software Engineer side - performance aspect

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    comment_count: Mapped[int] = mapped_column(Integer, nullable=False)

    loaded_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    loaded_at_epoch_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
