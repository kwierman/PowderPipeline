import uuid
from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel, select


class Snow(SQLModel, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True
    )  # Unique snowpack ID
    resort_id: uuid.UUID = Field(
        foreign_key="skiresort.id"
    )  # Foreign key to ski_resort table
    record_date: date = Field()
    base_snowfall_inches: Optional[float] = Field()
    base_snow_depth_inches: Optional[float] = Field()
    summit_snowfall_inches: Optional[float] = Field()
    summit_snow_depth_inches: Optional[float] = Field()

    @classmethod
    def get_or_create(cls, session, resort_id: uuid.UUID, record_date: date):
        query = select(cls).where(
            cls.resort_id == resort_id, cls.record_date == record_date
        )
        result = session.exec(query).first()
        if result:
            return result, False
        else:
            snow = cls(resort_id=resort_id, record_date=record_date)  # noqa
            return snow, True
