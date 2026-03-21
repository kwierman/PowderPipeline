from sqlmodel import Field, SQLModel
import uuid


class SkiResort(SQLModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    resort_name: str
    pass_affiliation: str
    latitude: float
    longitude: float
    base_elevation: float
    summit_elevation: float
