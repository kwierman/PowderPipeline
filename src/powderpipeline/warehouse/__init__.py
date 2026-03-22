import logging
from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from ..config import Settings

# These are noqa so that mypy doesn't complain about unused imports
# Import them to instantiate the models in the database
from .ski_resorts import SkiResort  # noqa: F401
from .snow import Snow  # noqa: F401

logger = logging.getLogger(__name__)

__engine__ = None


def get_engine(settings: Settings):
    global __engine__
    if __engine__ is None:
        full_path = settings.base_data_path / settings.db_name
        if not settings.base_data_path.exists():
            logger.info(f"Creating data directory at {settings.base_data_path}")
            settings.base_data_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Connecting to database at {full_path}")
        __engine__ = create_engine(f"sqlite:///{full_path}")
        SQLModel.metadata.create_all(__engine__)
    return __engine__


@contextmanager
def get_session(settings: Settings):
    logger.info("Creating database session...")
    session = Session(get_engine(settings))
    try:
        yield session
    finally:
        session.close()
    logger.info("Closing database session...")
