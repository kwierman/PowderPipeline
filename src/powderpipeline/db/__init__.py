import duckdb
from typing import Optional

# from .ski_pass import SkiPass
from sqlmodel import SQLModel, Session, create_engine
from ..config import Settings

import logging
from contextlib import contextmanager

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
        __engine__ = create_engine(f"duckdb:///{full_path}")
        SQLModel.metadata.create_all(__engine__)
    return __engine__


@contextmanager
def get_session(settings: Settings):
    logger.info("Creating database session...")
    yield Session(get_engine(settings))
    logger.info("Closing database session...")


""""
from sqlmodel import Field, SQLModel, Session, create_engine, select
import duckdb

# 1. Define your SQLModel model
class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: int | None = None

# 2. Create the DuckDB engine
# The 'duckdb:///:memory:' connection string creates an in-memory database.
# Use 'duckdb:///./test.db' for a persistent disk-based database.
sqlite_file_name = "database.db"
sqlite_url = f"duckdb:///{sqlite_file_name}"
# Use the duckdb-engine dialect
engine = create_engine(sqlite_url)

# 3. Create tables in the database

# 4. Create and add data
def create_heroes():
    with Session(engine) as session:
        hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
        hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
        session.add(hero_1)
        session.add(hero_2)
        session.commit()

# 5. Select and retrieve data
def select_heroes():
    with Session(engine) as session:
        statement = select(Hero).where(Hero.name == "Spider-Boy")
        hero = session.exec(statement).first()
        print(hero)

if __name__ == "__main__":
    create_heroes()
    select_heroes()
"""
