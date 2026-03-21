AWDB_BASE_URL = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/"
ELEMENT_CODES = ["TAVG", "PRCP", "PRCPSA", "SNWD"]



from django.core.management.base import BaseCommand
import logging

from snowpack.models import Station, SnowfallRecord
import requests
from snowpack.utilities import AWDB_BASE_URL, ELEMENT_CODES
import datetime
from rich.progress import Progress
import dateutil.parser as parser
import json

log = logging.getLogger("snowpack.backfill_snowpack")


class Command(BaseCommand):
    help = "Backfills the snowpack database with stations from AWDB"

    def handle(self, *args, **options):
        today = datetime.date.today()

        url = f"{AWDB_BASE_URL}data"
        stations = Station.objects.all()
        with Progress() as progress:
            station_task = progress.add_task(
                "[green]Backfilling Stations...", total=len(stations)
            )
            element_task = progress.add_task(
                "[cyan]Processing Elements...", total=len(ELEMENT_CODES)
            )
            datum_task = progress.add_task("[magenta]Processing Data...", total=0)
            for station in stations:
                log.info("Backfilling station: {}".format(station.name))
                progress.update(element_task, completed=0)
                for element in ELEMENT_CODES:
                    payload = {
                        "stationTriplets": station.nwcc_id,
                        "elements": element,
                        "beginDate": "1980-01-01",
                        "endDate": today.strftime("%Y-%m-%d"),
                        "duration": "DAILY",
                    }
                    log.info(
                        "Fetching element: {} for station: {}".format(
                            element, station.name
                        )
                    )
                    response = requests.get(url, params=payload)
                    data = json.loads(response.text)
                    if len(data):
                        data = data[0]
                    else:
                        continue
                    records_to_update = []
                    records_to_create = []

                    progress.update(
                        datum_task, completed=0, total=len(data["data"][0]["values"])
                    )
                    for datum in data["data"][0]["values"]:
                        date = parser.parse(datum["date"]).date()
                        if not "value" in datum:
                            continue
                        value = datum["value"]
                        create = bool(
                            SnowfallRecord.objects.filter(
                                station=station, date=date
                            ).count()
                            == 0
                        )

                        record = None
                        if create:
                            record = SnowfallRecord(station=station, date=date)
                        else:
                            record = SnowfallRecord.objects.get(
                                station=station, date=date
                            )

                        if element == "SNWD":
                            record.snow_depth = value
                        elif element == "TAVG":
                            record.temperature = value
                        elif element == "PRCP":
                            record.precipitation = value
                        elif element == "PRCPSA":
                            record.snowfall_amount = value

                        if create:
                            records_to_create.append(record)
                        else:
                            records_to_update.append(record)

                        progress.update(datum_task, advance=1)
                    SnowfallRecord.objects.bulk_create(records_to_create)
                    SnowfallRecord.objects.bulk_update(
                        records_to_update,
                        [
                            "snowfall_amount",
                            "snow_depth",
                            "temperature",
                            "precipitation",
                        ],
                    )
                    log.info(
                        "Updated {} records for element: {} at station: {}".format(
                            len(records_to_update), element, station.name
                        )
                    )
                    log.info(
                        "Created {} records for element: {} at station: {}".format(
                            len(records_to_create), element, station.name
                        )
                    )
                    progress.update(element_task, advance=1)
                progress.update(station_task, advance=1)
            log.info("Backfilling complete.")


from django.core.management.base import BaseCommand
import logging
from nwac.utilities import get_driver_context, scrape_today

from snowpack.models import Station
import requests
from snowpack.utilities import AWDB_BASE_URL

log = logging.getLogger("snowpack.scrape_stations")


class Command(BaseCommand):
    help = "Cleans Up The Database"

    def add_arguments(self, parser):
        # parser.add_argument("poll_ids", nargs="+", type=int
        ...

    def handle(self, *args, **options):

        url = f"{AWDB_BASE_URL}stations"
        payload = {
            "stationTriplets": "*:WA:SNTL",
            "returnForecastPointMetadata": False,
            "returnReservoirMetadata": False,
            "returnStationElements": False,
            "activeOnly": False,
        }
        response = requests.get(url, params=payload)
        data = response.json()
        for item in data:
            nwcc_id = item.get("stationTriplet", "")
            name = item.get("name", "Unknown Station")
            latitude = item.get("latitude", 0.0)
            longitude = item.get("longitude", 0.0)
            elevation = item.get("elevation", 0.0)

            station, created = Station.objects.get_or_create(
                nwcc_id=nwcc_id,
                defaults={
                    "name": name,
                    "latitude": latitude,
                    "longitude": longitude,
                    "elevation": elevation,
                },
            )
            if created:
                log.info(f"Created new station: {name} ({nwcc_id})")
            else:
                log.info(f"Station already exists: {name} ({nwcc_id})")
