import uuid
from typing import Optional

from sqlmodel import Field, Session, SQLModel, select


class SkiResort(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    resort_name: str
    pass_affiliation: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    base_elevation: Optional[float] = None
    summit_elevation: Optional[float] = None

    @classmethod
    def get_all(cls, session: Session):
        return session.exec(select(cls)).all()
