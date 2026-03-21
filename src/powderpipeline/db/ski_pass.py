from sqlmodel import Field, SQLModel
import uuid


class SkiPass(SQLModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    provider: str
    pass_name: str
    pass_type: str
    age_range: str
    price: str

