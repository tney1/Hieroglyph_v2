from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
import logging

logger = logging.getLogger(__name__)
# define sqlite connection url
SQLALCHEMY_DATABASE_URL = "sqlite:///./src/hieroglyph/db/hieroglyph.db"

# create new engine instance
try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, echo=False
        )
    # create sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base = declarative_base()
    logger.debug("Creating database tables")
    Base.metadata.create_all(bind=engine, checkfirst=True)
    logger.debug(f"Database tables: {Base.metadata.tables.keys()}")

except OperationalError as e:
    logger.warning(f"Database already exists. {e}")
    pass
