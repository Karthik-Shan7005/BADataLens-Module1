from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db import Base


class User(Base):
    __tablename__ = "DataLens_users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    role = Column(String(50), nullable=False)  # superadmin | supervisor | viewer
    password_hash = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)


class Project(Base):
    __tablename__ = "DataLens_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expiry_months = Column(Integer, default=3)

    datasets = relationship("Dataset", back_populates="project", cascade="all, delete-orphan")
    datamaps = relationship("Datamap", back_populates="project", cascade="all, delete-orphan")
    access_grants = relationship("AccessGrant", back_populates="project", cascade="all, delete-orphan")


class Dataset(Base):
    __tablename__ = "DataLens_datasets"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("DataLens_projects.id"), nullable=False)
    spss_path = Column(String(1000), nullable=False)
    parquet_path = Column(String(1000), nullable=False)
    wave_variable = Column(String(200), nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="datasets")


class Datamap(Base):
    __tablename__ = "DataLens_datamaps"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("DataLens_projects.id"), nullable=False)
    question_registry = Column(Text, nullable=False)
    weight_variable = Column(String(200), nullable=True)

    project = relationship("Project", back_populates="datamaps")


class AccessGrant(Base):
    __tablename__ = "DataLens_access_grants"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("DataLens_users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("DataLens_projects.id"), nullable=False)
    granted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)

    user = relationship("User")
    project = relationship("Project", back_populates="access_grants")


class ChatHistory(Base):
    __tablename__ = "DataLens_chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("DataLens_users.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("DataLens_projects.id"), nullable=False)
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    chart_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", foreign_keys=[user_id])
