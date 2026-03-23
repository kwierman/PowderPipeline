import logging
from datetime import date, timedelta
from tracemalloc import start

import requests
from rich.progress import track

from ..warehouse import SkiResort, Snow
from .base import Analyzer

logger = logging.getLogger(__name__)


async def get_snow_conditions(lat, lon, elevation_ft, day_of_year, year=2024):
    """
    Fetches the total snowfall and average snow depth for a specific location,
    elevation, and day of the year using the Open-Meteo Archive API.

    Parameters:
    - lat (float): Latitude of the ski resort
    - lon (float): Longitude of the ski resort
    - elevation_ft (float): Elevation in feet (tool converts it to meters for the API)
    - day_of_year (int): Day of the year (1 to 365/366)
    - year (int): The historical year to query. Defaults to 2024.

    Returns:
    - dict: A dictionary containing snowfall and snow depth in inches.
    """

    # 1. Convert elevation from feet to meters (required by the API)
    elevation_m = int(elevation_ft * 0.3048)

    # 2. Convert "Day of the Year" into a specific Date string (YYYY-MM-DD)
    # We use Jan 1st of the specified year and add the day_of_year minus 1
    target_date = date(year, 1, 1) + timedelta(days=day_of_year - 1)
    date_str = target_date.strftime("%Y-%m-%d")

    # 3. Setup the Open-Meteo API request
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "elevation": elevation_m,
        "start_date": date_str,
        "end_date": date_str,
        "hourly": "snowfall,snow_depth",  # Fetching hourly to aggregate accurately
        "timezone": "auto",
    }

    try:
        # 4. Make the API Call
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # 5. Extract the hourly data
        hourly_snowfall_cm = data.get("hourly", {}).get("snowfall", [])
        hourly_snow_depth_m = data.get("hourly", {}).get("snow_depth", [])

        # Filter out any missing (None) values
        hourly_snowfall_cm = [s for s in hourly_snowfall_cm if s is not None]
        hourly_snow_depth_m = [d for d in hourly_snow_depth_m if d is not None]

        # 6. Aggregate the data
        # Snowfall is cumulative, so we sum the hourly amounts
        total_snowfall_cm = sum(hourly_snowfall_cm) if hourly_snowfall_cm else 0.0
        # Snow depth is a standing measurement, so we take the daily maximum
        max_snow_depth_m = max(hourly_snow_depth_m) if hourly_snow_depth_m else 0.0

        # 7. Convert from Metric back to Imperial (Inches) for U.S. standards
        total_snowfall_in = total_snowfall_cm * 0.393701
        max_snow_depth_in = max_snow_depth_m * 39.3701

        return {
            "query_date": date_str,
            "day_of_year": day_of_year,
            "total_snowfall_inches": round(total_snowfall_in, 2),
            "snow_depth_inches": round(max_snow_depth_in, 2),
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from API. Error: {e}")
        return None


class SnowAnalyzer(Analyzer):
    def __init__(self, session, settings, buffer_len=100):
        self.session = session
        self.settings = settings
        self.buffer = []
        self.buffer_len = buffer_len

    async def analyze(
        self,
    ):
        start_day_of_year = self.settings.start_of_snow_year_day
        end_day_of_year = self.settings.end_of_snow_year_day
        this_year = date.today().year
        ten_years_ago = this_year - 10
        days_to_analyze = list(range(start_day_of_year, 366))
        days_to_analyze.extend(range(1, end_day_of_year + 1))

        for day_of_year in track(
            days_to_analyze, description="Analyzing daily data..."
        ):
            for year in track(
                range(this_year, ten_years_ago, -1),
                description="Analyzing yearly data...",
            ):
                for resort in track(
                    SkiResort.get_all(self.session),
                    description="Analyzing ski resorts...",
                ):
                    if resort.base_elevation is None or resort.summit_elevation is None:
                        continue

                    date_ = date(year, 1, 1) + timedelta(days=day_of_year - 1)
                    snow, created = Snow.get_or_create(
                        self.session, resort_id=resort.id, record_date=date_
                    )
                    if created:
                        logger.info(
                            f"Analyzing snow data for {resort.resort_name} on {date_}"
                        )
                        logger.info(
                            f"Elevation Base: {resort.base_elevation}, Summit: {resort.summit_elevation}"
                        )

                        base_data = await get_snow_conditions(
                            resort.latitude,
                            resort.longitude,
                            resort.base_elevation,
                            day_of_year,
                            year=year,
                        )
                        if base_data is None:
                            continue
                        summit_data = None
                        summit_data = await get_snow_conditions(
                            resort.latitude,
                            resort.longitude,
                            resort.summit_elevation,
                            day_of_year,
                            year=year,
                        )
                        if summit_data is None:
                            continue

                        snow.base_snowfall_inches = base_data["total_snowfall_inches"]
                        snow.base_snow_depth_inches = base_data["snow_depth_inches"]
                        snow.summit_snowfall_inches = summit_data[
                            "total_snowfall_inches"
                        ]
                        snow.summit_snow_depth_inches = summit_data["snow_depth_inches"]
                        self.buffer.append(snow)
                        if len(self.buffer) > self.buffer_len:
                            for snow in self.buffer:
                                self.session.add(snow)
                            self.session.commit()
                            self.buffer = []
