"""
SQLAlchemy ORM models (database schema)

"""

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import (
    BigInteger
    ,Boolean
    ,Column
    ,DateTime
    ,Integer
    ,MetaData
    ,String
    ,Table
    ,Text
    ,func
    ,true
    ,UniqueConstraint
    )


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


class UsersRaw(Base):
    __tablename__ = "users_raw"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    username: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(256), nullable=False)
    phone: Mapped[str] = mapped_column(String(256), nullable=False)
    website: Mapped[str] = mapped_column(String(256), nullable=False)
    address_street: Mapped[str] = mapped_column(String(256), nullable=False)
    address_suite: Mapped[str] = mapped_column(String(256), nullable=False)
    address_city: Mapped[str] = mapped_column(String(256), nullable=False)
    address_zipcode: Mapped[str] = mapped_column(String(256), nullable=False)
    address_geo_lat: Mapped[str] = mapped_column(String(256), nullable=False)
    address_geo_lng: Mapped[str] = mapped_column(String(256), nullable=False)
    company_name: Mapped[str] = mapped_column(String(256), nullable=False)
    company_catch_phrase: Mapped[str] = mapped_column(String(256), nullable=False)
    company_bs: Mapped[str] = mapped_column(String(256), nullable=False)

    ingested_run_id: Mapped[str] = mapped_column(String(256), nullable=False)
    ingested_at_epoch_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)


class CommentsRaw(Base):

    __tablename__ = "comments_raw"

    id: Mapped[str] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[str] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    email: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    ingested_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    ingested_at_epoch_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)



class PostsEnrichedSnapshot(Base):
    "Current enriched version of posts"

    __tablename__ = "posts_enriched_snapshot"

    post_id: Mapped[int] = mapped_column(Integer, primary_key = True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_name: Mapped[str] = mapped_column(String(256), nullable=False)
    user_email: Mapped[str] = mapped_column(String(256), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    loaded_run_id: Mapped[str] = mapped_column(Integer, nullable=False)
    loaded_at_epoch_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    row_hash: Mapped[str| None] = mapped_column(String(64), nullable=True)


class PostsEnrichedHistory(Base):
    "Historical enriched posts"

    __tablename__ = "posts_enriched_history"

    id: Mapped[int] = mapped_column(Integer, nullable=False)
    post_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_name: Mapped[str] = mapped_column(String(256), nullable=False)
    user_email: Mapped[str] = mapped_column(String(256), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False)

    row_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    valid_form_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    valid_from_epoch_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())


#posts_enriched_stage has no primary key in
#Adding a primary key can slow bulk loading because PostgreSQL must maintain a unique index for every inserted row.
#it is represented as sqlalchemy core table of an ORM-mapped class


posts_enriched_stage = Table(
    "posts_enriched_stage",
    Base.metadata,
    Column("post_id", Integer, nullable= False)
    ,Column("user_id", Integer, nullable= False)
    ,Column("user_name", String(256), nullable=False)
    ,Column("user_email", String(256), nullable=False)
    ,Column("title", String(256), nullable=False)
    ,Column("body", Text, nullable=False)
    ,Column("comment_count", Integer, nullable=False)
    ,Column("row_hash", String(64), nullable=False)
    ,Column("load_run_id", String(64), nullable=False)
    ,Column("load_at_epoch_ms", BigInteger, nullable=False)
    ,UniqueConstraint(
        "load_run_id"
        ,"post_id"
        ,name = "uq_posts_enriched_stage_run_post"
    )
)


# class PostsEnriched(Base):
#     #Curated / transformed table

#     __tablename__ = "posts_enriched"

#     post_id: Mapped[int] = mapped_column(Integer, primary_key=True)

#     user_id: Mapped[int] = mapped_column(Integer, nullable=False)
#     user_name: Mapped[str] = mapped_column(String(256), nullable=False)
#     user_email: Mapped[str] = mapped_column(String(256), nullable=False) #no email check, validation should be from Software Engineer side - performance aspect

#     title: Mapped[str] = mapped_column(String(512), nullable=False)
#     body: Mapped[str] = mapped_column(Text, nullable=False)

#     comment_count: Mapped[int] = mapped_column(Integer, nullable=False)

#     loaded_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
#     loaded_at_epoch_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
