import asyncio

import requests
from datetime import date, timedelta
from .base import BaseScraper
import pandas as pd
from csv import DictWriter
import logging
from rich.progress import track

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


class SnowfallScraper(BaseScraper):
    async def scrape_single_row(self): ...

    async def get_snow_data(self):
        logger.info("Starting snowfall data scraping...")
        ski_resorts_file = (
            self.settings.base_data_path / self.settings.ski_resorts_replacement_csv
        )
        if not ski_resorts_file.exists():
            logger.error(
                f"Ski resorts replacement CSV file not found at {ski_resorts_file}. Aborting snowfall scraping."
            )
            return
        ski_resorts_df = pd.read_csv(ski_resorts_file)

        output_file = self.settings.base_data_path / "snowfall.csv"
        with open(
            output_file,
            "w",
        ) as csvfile:
            fieldnames = [
                "resort_name",
                "pass",
                "latitude",
                "longitude",
                "base_elevation_ft",
                "summit_elevation_ft",
                "day_of_year",
                "year",
                "base_total_snowfall_inches",
                "base_snow_depth_inches",
                "summit_total_snowfall_inches",
                "summit_snow_depth_inches",
            ]
            writer = DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for _, row in track(
                ski_resorts_df.iterrows(),
                total=len(ski_resorts_df),
                description="Scraping snowfall data...",
            ):
                name = row["Resort_Name"]
                pass_affiliation = row["Pass_Affiliation"]
                latitude = row["Latitude"]
                longitude = row["Longitude"]
                base_elevation_ft = row["Base_Elevation_ft"]
                summit_elevation_ft = row["Summit_Elevation_ft"]
                for day_of_year in track(
                    range(1, 366), description="Processing days..."
                ):  # Loop through all days of the year
                    for year in track(
                        range(2015, 2025), description="Processing years..."
                    ):  # Loop through multiple years for historical data
                        output_data = {
                            "resort_name": name,
                            "pass": pass_affiliation,
                            "latitude": latitude,
                            "longitude": longitude,
                            "base_elevation_ft": base_elevation_ft,
                            "summit_elevation_ft": summit_elevation_ft,
                            "day_of_year": day_of_year,
                            "year": year,
                        }

                        base_data = get_snow_conditions(
                            lat=latitude,
                            lon=longitude,
                            elevation_ft=base_elevation_ft,
                            day_of_year=day_of_year,
                            year=year,
                        )
                        if base_data:
                            output_data.update(
                                {
                                    "base_total_snowfall_inches": base_data[
                                        "total_snowfall_inches"
                                    ],
                                    "base_snow_depth_inches": base_data[
                                        "snow_depth_inches"
                                    ],
                                }
                            )

                        summit_data = get_snow_conditions(
                            lat=latitude,
                            lon=longitude,
                            elevation_ft=summit_elevation_ft,
                            day_of_year=day_of_year,
                            year=year,
                        )
                        if summit_data:
                            output_data.update(
                                {
                                    "summit_total_snowfall_inches": summit_data[
                                        "total_snowfall_inches"
                                    ],
                                    "summit_snow_depth_inches": summit_data[
                                        "snow_depth_inches"
                                    ],
                                }
                            )
                        writer.writerow(output_data)

    def scrape(self):
        """
        Scrape snowfall data for each ski resort and save it to the database.
        """
        asyncio.run(self.get_snow_data())


async def fetch_user_data(session, user_id):
    """Fetches user data from the API asynchronously."""
    url = f"https://jsonplaceholder.typicode.com{user_id}"
    async with session.get(url) as response:
        # Raise an exception for bad status codes
        response.raise_for_status()
        data = await response.json()
        # Extract relevant fields that match the FIELDNAMES
        user_data = {field: data.get(field, "N/A") for field in FIELDNAMES}
        return user_data


async def main():
    """Main function to run async tasks and write to CSV."""
    # List of user IDs to fetch
    user_ids = range(1, 11)

    # Use aiohttp.ClientSession for efficient, shared network connections
    async with aiohttp.ClientSession() as session:
        # Create tasks for all requests concurrently
        tasks = [fetch_user_data(session, user_id) for user_id in user_ids]
        # Gather results as they complete
        all_users_data = await asyncio.gather(*tasks)

    # Write the gathered data to a CSV file asynchronously
    async with aiofiles.open(
        "users.csv", mode="w", newline="", encoding="utf-8"
    ) as afp:
        # Use AsyncDictWriter from aiocsv
        writer = AsyncDictWriter(afp, fieldnames=FIELDNAMES)

        await writer.writeheader()
        await writer.writerows(all_users_data)

    print(f"Successfully wrote data for {len(all_users_data)} users to users.csv")


if __name__ == "__main__":
    # Run the main asynchronous function
    pass
