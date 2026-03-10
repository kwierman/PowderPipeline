from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict
from pydantic_settings_yaml import YamlBaseSettings#, SettingsConfigDict
from pathlib import Path


#class Database(BaseModel):
#    host: str
#    port: int
"""
class SkiPass(BaseModel):
    url: str
    wait_for: str
    card: str
    name: str
    age: str
    price: str

class SnowFall(BaseModel):
    name: str
    url: str
    wait_for: str
    record: str
    date: str
    snowfall_amount: str

class SkiResort(BaseModel):
    name: str
    url: str
    wait_for: str
    card: str
    name: str
    location: str
    pass_affiliation: str
"""
class Settings(YamlBaseSettings):
    model_config = SettingsConfigDict(yaml_file="config.yaml", extra='allow')
    base_data_path: Path
    base_db_path: Path
    #ski_passes: list[SkiPass]
    #snowfall: list[SnowFall]
    #ski_resorts: list[SkiResort]
    ski_resorts_replacement_csv: str
