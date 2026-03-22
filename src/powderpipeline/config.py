from pathlib import Path

import yaml
from pydantic import BaseModel


class Settings(BaseModel):
    base_data_path: Path
    db_name: str
    pass_prices_path: Path = Path("pass_prices.csv")
    scrape_delay_seconds: float = 1.5
    start_of_snow_year_day: int = 274
    end_of_snow_year_day: int = 152


def load_settings(yaml_path: Path) -> Settings:
    with open(yaml_path, "r") as f:
        config = yaml.safe_load(f)
    return Settings(**config)
