from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship
from .sqlite_db import Base
import datetime


class SQLBatchJobs(Base):
    """
    """

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    dst_lang = Column(String(200))
    image_type = Column(String(200))
    timestamp = Column(TIMESTAMP, default=datetime.datetime.now())
    running = Column(Boolean)
    failure = Column(Boolean)
    success = Column(Boolean)
    completed = Column(Boolean)
    output_location = Column(String(200))
    internal_id = Column(String(200))
