from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from database import Base


class Fault(Base):
    __tablename__ = "faults"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String(32), nullable=False)
    location = Column(String(120), nullable=False)
    description = Column(String(500), nullable=False)
    severity = Column(String(20), nullable=False)
    priority = Column(String(10), nullable=False)
    reporter_id = Column(String(32), nullable=False)
    status = Column(String(20), nullable=False, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)
