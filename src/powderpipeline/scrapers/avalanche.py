from django.core.management.base import BaseCommand
import logging
from nwac.utilities import get_driver_context, backfill_from_nwac
from nwac.models import ForecastZone as Zone

log = logging.getLogger("nwac.backfill")


class Command(BaseCommand):
    help = "Backfill NWAC data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--zone",
            action="store",
            help="Number of seconds to sleep between downloads",
            default=None,
            type=str,
        )

    def handle(self, *args, **options):
        zones = Zone.objects.all()
        if options["zone"]:
            zones = zones.filter(name__iexact=options["zone"])
        with get_driver_context() as driver:
            for zone in zones:
                log.info(f"Backfilling data for zone: {zone.name}")
                # Here you would call the backfill function, e.g.:
                backfill_from_nwac(driver, zone)
                # backfill_zone_data(driver, zone)
                # For demonstration, we'll just log the action.
                log.info(f"Completed backfilling for zone: {zone.name}")


from django.core.management.base import BaseCommand
import logging
from nwac.utilities import get_driver_context, backfill_from_file
from nwac.models import ForecastZone as Zone

log = logging.getLogger("nwac.backfill")


class Command(BaseCommand):
    help = "Backfill NWAC data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--zone",
            action="store",
            help="Number of seconds to sleep between downloads",
            default=None,
            type=str,
        )

    def handle(self, *args, **options):
        zones = Zone.objects.all()
        if options["zone"]:
            zones = zones.filter(name__iexact=options["zone"])
        with get_driver_context(headless=True) as driver:
            for zone in zones:
                log.info(f"Backfilling data for zone: {zone.name}")
                # Here you would call the backfill function, e.g.:
                backfill_from_file(driver, zone)
                # backfill_zone_data(driver, zone)
                # For demonstration, we'll just log the action.
                log.info(f"Completed backfilling for zone: {zone.name}")


from django.core.management.base import BaseCommand
import logging
from nwac.utilities import get_driver_context, scrape_today
from nwac.models import ForecastZone

log = logging.getLogger("video_scraper.clean_videos")


class Command(BaseCommand):
    help = "Cleans Up The Database"

    def add_arguments(self, parser):
        # parser.add_argument("poll_ids", nargs="+", type=int
        ...

    def handle(self, *args, **options):
        with get_driver_context() as driver:
            for zone in ForecastZone.objects.all():
                log.info(f"Scraping today's data for {zone.name}")
                scrape_today(driver, zone)


from datetime import datetime, timezone
import logging

import time
from selenium.common.exceptions import ElementClickInterceptedException
from selenium import webdriver
from .models import ForecastZone, Forecast
from random import randint
from datetime import datetime
from pathlib import Path
import dateutil
from bs4 import BeautifulSoup
from contextlib import contextmanager
from lxml import etree

log = logging.getLogger(__name__)

BASE_PATH = Path("/media/kwierman/Data/nwac")
BASE_URL = "https://www.nwac.us/avalanche-forecast/#/"
AUTHOR_XPATH = '//*[@id="nac-forecast-container"]/div/div[2]/div[3]/div'
DANGER_UPPER_XPATH = '//*[@id="nac-tab-resizer"]/div/div[1]/div/div[1]/div[1]/div[1]/div[2]/div[1]/span[2]'
DANGER_MID_XPATH = '//*[@id="nac-tab-resizer"]/div/div[1]/div/div[1]/div[1]/div[1]/div[2]/div[2]/span[2]'
DANGER_LOWER_XPATH = '//*[@id="nac-tab-resizer"]/div/div[1]/div/div[1]/div[1]/div[1]/div[2]/div[3]/span[2]'
TEMPERATURE_XPATH = '//*[@id="nac-additional-content"]/article/div/div[1]/div[2]/table/tbody/tr[1]/td[1]'
EVENING_SNOWLINE_XPATH = '//*[@id="nac-additional-content"]/article/div/div[1]/div[2]/table/tbody/tr[2]/td[1]'
OVERNIGHT_SNOWLINE_XPATH = '//*[@id="nac-additional-content"]/article/div/div[1]/div[2]/table/tbody/tr[2]/td[2]'
EVENING_WIND_XPATH = '//*[@id="nac-additional-content"]/article/div/div[1]/div[2]/table/tbody/tr[3]/td[1]'
OVERNIGHT_WIND_XPATH = '//*[@id="nac-additional-content"]/article/div/div[1]/div[2]/table/tbody/tr[3]/td[2]'
PRECIP_XPATH = '//*[@id="nac-additional-content"]/article/div/div[1]/div[2]/table/tbody/tr[5]/td[1]'


def get_data_path(product: str, zone: str, dt: datetime) -> Path:
    """Gets a Pathlib path for a given product and zone"""

    path = (
        BASE_PATH
        / product
        / str(zone)
        / str(dt.year)
        / str(dt.month)
        / (str(dt.day) + ".html")
    )
    return path


@contextmanager
def get_driver_context():
    """Context manager for Chrome Driver"""
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/chromium-browser"
    options.chrome_driver_binary = "/usr/bin/chromedriver"
    options.headless = True  # Enable headless mode
    driver = webdriver.Chrome(options=options)
    try:
        yield driver
    finally:
        driver.quit()


def navigate_to(driver: webdriver.Chrome, url: str):
    """Navigates to a URL and waits for the page to load."""
    try:
        driver.get(url)
        time.sleep(randint(2, 5))  # Random sleep to mimic human behavior
    except Exception as e:
        log.error(f"Error navigating to {url}: {e}")


def scrape_issued_date(content: str) -> datetime:
    issued_str = content.split("Issued ")[1].split("\n")[0].strip()
    return dateutil.parser.parse(issued_str)


def download_page(driver: webdriver.Chrome, zone: Forecast) -> Path | None:
    dt = scrape_issued_date(driver.page_source)
    output_path = get_data_path(product="forecast", zone=zone.name, dt=dt)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        f.write(driver.page_source)
    return output_path


def fill_basic_info_from_page(file_path: Path, zone: ForecastZone) -> None:
    content = None
    with file_path.open("r") as f:
        content = f.read()
    issued_date = scrape_issued_date(content)
    Forecast.objects.update_or_create(
        zone=zone,
        date=issued_date.date(),
        defaults={
            "author": "Unknown",
            "upper_elevation_danger": -1,
            "mid_elevation_danger": -1,
            "lower_elevation_danger": -1,
            "evening_temperature": -1,
            "overnight_temperature": -1,
            "evening_snowline": -1,
            "overnight_snowline": -1,
            "evening_wind_speed": -1,
            "overnight_wind_speed": -1,
            "precipitation": -1,
        },
    )


def fill_info_from_page(file_path: Path, zone: ForecastZone) -> None:
    # Read in the file
    content = None
    with file_path.open("r") as f:
        content = f.read()
    issued_date = scrape_issued_date(content)
    soup = BeautifulSoup(content, "html.parser")
    dom = etree.HTML(str(soup))

    # Scrape data, one item at a time
    author = dom.xpath(AUTHOR_XPATH)[0][0].text.split("\n")[-1].strip()
    danger_upper = int(dom.xpath(DANGER_UPPER_XPATH)[0].text.split()[0])
    danger_mid = int(dom.xpath(DANGER_MID_XPATH)[0].text.split()[0])
    danger_lower = int(dom.xpath(DANGER_LOWER_XPATH)[0].text.split()[0])
    temperature = dom.xpath(TEMPERATURE_XPATH)[0].text
    evening_temp = int(temperature.split()[0])
    overnight_temp = int(temperature.split()[2])
    evening_snowline = int(dom.xpath(EVENING_SNOWLINE_XPATH)[0].text.split()[0])
    overnight_snowline = int(dom.xpath(OVERNIGHT_SNOWLINE_XPATH)[0].text.split()[0])
    wind_txt = dom.xpath(EVENING_WIND_XPATH)[0].text.split()
    evening_wind_speed = 0
    for elem in wind_txt[::-1]:
        try:
            evening_wind_speed = int(elem)
            break
        except:
            continue
    wind_txt = dom.xpath(OVERNIGHT_WIND_XPATH)[0].text.split()
    overnight_wind_speed = 0
    for elem in wind_txt[::-1]:
        try:
            overnight_wind_speed = int(elem)
            break
        except:
            continue
    precipitation = 0
    try:
        precipitation = int(dom.xpath(PRECIP_XPATH)[0].text.split()[0])
    except:
        # Bland exception for when there is no precipitation data available
        log.warning(
            f"No precipitation data available for {zone.name} on {issued_date.date()}. Setting to 0."
        )
        precipitation = 0
        pass

    Forecast.objects.update_or_create(
        zone=zone,
        date=issued_date.date(),
        defaults={
            "author": author,
            "upper_elevation_danger": danger_upper,
            "mid_elevation_danger": danger_mid,
            "lower_elevation_danger": danger_lower,
            "evening_temperature": evening_temp,
            "overnight_temperature": overnight_temp,
            "evening_snowline": evening_snowline,
            "overnight_snowline": overnight_snowline,
            "evening_wind_speed": evening_wind_speed,
            "overnight_wind_speed": overnight_wind_speed,
            "precipitation": precipitation,
        },
    )


def scrape_today(driver: webdriver.Chrome, zone: ForecastZone) -> None:
    """Just gets today's data, Downloads it, then fills in the database

    Args:
        driver (webdriver.Chrome): _description_
        zone (ForecastZone): _description_
    """
    url = f"{BASE_URL}{zone.slug}/"
    navigate_to(driver, url)
    file_path = download_page(driver, zone)
    fill_info_from_page(file_path, zone)


def backfill_from_nwac(driver: webdriver.Chrome, zone: ForecastZone) -> None:
    """Backfills data from NWAC by navigating back through the forecast pages.
    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance
        zone (ForecastZone): The forecast zone to backfill data for
    """
    url = f"{BASE_URL}{zone.slug}/"
    navigate_to(driver, url)
    file_path = download_page(driver, zone)
    try:
        fill_info_from_page(file_path, zone)
    except Exception as e:
        log.warning(f"Error filling info from page for {zone.name}: {e}")
        fill_basic_info_from_page(file_path, zone)

    # Try and click the back button
    back_xpath = '//*[@id="nac-forecast-nav"]/div/div[1]/div/button[1]'
    back_elems = driver.find_elements("xpath", back_xpath)
    while len(back_elems) > 0:
        back_elem = back_elems[0]
        try:
            back_elem.click()
            time.sleep(randint(2, 5))
        except ElementClickInterceptedException:
            break
        try:
            file_path = download_page(driver, zone)
        except IndexError:
            log.error(
                f"Error downloading page for {zone.name}. Current page: {driver.current_url} Ending backfill."
            )
        else:
            try:
                fill_info_from_page(file_path, zone)
            except Exception as e:
                log.warning(
                    f"Error filling info from page for {zone.name}: {driver.current_url} : {e}"
                )
                fill_basic_info_from_page(file_path, zone)
        back_elems = driver.find_elements("xpath", back_xpath)


# Backfill from file
def backfill_from_file(file_path: Path, zone: ForecastZone) -> None:
    """Backfills data from a saved HTML file.

    Args:
        file_path (Path): Path to the saved HTML file
        zone (ForecastZone): The forecast zone to backfill data for
    """
    for forecast in Forecast.objects.filter(zone=zone).order_by("-date"):
        dt = forecast.date
        path = get_data_path(product="forecast", zone=zone.name, dt=dt)
        if not path.exists():
            log.warning(f"File {path} does not exist. Skipping.")
            continue
        fill_info_from_page(path, zone)

    driver = get_driver()

    url = "https://www.nwac.us/avalanche-forecast/#/"

    for zone in zones:
        zone_url = f"{url}{zone.slug}/"
        log.info(f"Scraping {zone_url}")
        navigate_to(driver, zone_url)
        scrape_page(driver, zone)
        log.info(f"Finished scraping {zone_url}")

        back_xpath = '//*[@id="nac-forecast-nav"]/div/div[1]/div/button[1]'
        back_elems = driver.find_elements("xpath", back_xpath)
        while len(back_elems) > 0:
            back_elem = back_elems[0]
            try:
                back_elem.click()
                time.sleep(randint(2, 5))
            except ElementClickInterceptedException:
                break
            try:
                scrape_page(driver, zone)
            except Exception as e:
                log.error(f"Error scraping {zone_url}: {e}")
                continue
            log.info(f"Finished scraping {zone_url}")
            back_elems = driver.find_elements("xpath", back_xpath)
    driver.quit()
