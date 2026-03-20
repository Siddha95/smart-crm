from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from database import Base


class UserProfile(Base):
    __tablename__ = "crm_userprofile"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"), unique=True)
    personal_api_key = Column(String(500), nullable=True)


class DataSource(Base):
    __tablename__ = "crm_datasource"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("auth_user.id"))
    name = Column(String(255))
    label = Column(String(255))
    columns = Column(JSON)
    created_at = Column(DateTime)

    records = relationship("Record", back_populates="data_source")


class Record(Base):
    __tablename__ = "crm_record"

    id = Column(Integer, primary_key=True)
    data_source_id = Column(Integer, ForeignKey("crm_datasource.id"))
    data = Column(JSON)
    embedding = Column(Vector(1536), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    data_source = relationship("DataSource", back_populates="records")
