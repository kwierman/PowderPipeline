import asyncio
import json
import logging
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup
from playwright.async_api import Page

from ..scrapers.base import BaseScraper
from ..warehouse.ski_resorts import SkiResort

BASE_URL = "https://www.onthesnow.com"

REGION_URLS = [
    "https://www.onthesnow.com/united-states/ski-resorts/",
    "https://www.onthesnow.com/alabama/ski-resorts/",
    "https://www.onthesnow.com/alaska/ski-resorts/",
    "https://www.onthesnow.com/arizona/ski-resorts/",
    "https://www.onthesnow.com/arkansas/ski-resorts/",
    "https://www.onthesnow.com/california/ski-resorts/",
    "https://www.onthesnow.com/colorado/ski-resorts/",
    "https://www.onthesnow.com/connecticut/ski-resorts/",
    "https://www.onthesnow.com/delaware/ski-resorts/",
    "https://www.onthesnow.com/georgia/ski-resorts/",
    "https://www.onthesnow.com/idaho/ski-resorts/",
    "https://www.onthesnow.com/illinois/ski-resorts/",
    "https://www.onthesnow.com/indiana/ski-resorts/",
    "https://www.onthesnow.com/iowa/ski-resorts/",
    "https://www.onthesnow.com/maine/ski-resorts/",
    "https://www.onthesnow.com/maryland/ski-resorts/",
    "https://www.onthesnow.com/massachusetts/ski-resorts/",
    "https://www.onthesnow.com/michigan/ski-resorts/",
    "https://www.onthesnow.com/minnesota/ski-resorts/",
    "https://www.onthesnow.com/missouri/ski-resorts/",
    "https://www.onthesnow.com/montana/ski-resorts/",
    "https://www.onthesnow.com/nebraska/ski-resorts/",
    "https://www.onthesnow.com/nevada/ski-resorts/",
    "https://www.onthesnow.com/new-hampshire/ski-resorts/",
    "https://www.onthesnow.com/new-jersey/ski-resorts/",
    "https://www.onthesnow.com/new-mexico/ski-resorts/",
    "https://www.onthesnow.com/new-york/ski-resorts/",
    "https://www.onthesnow.com/north-carolina/ski-resorts/",
    "https://www.onthesnow.com/north-dakota/ski-resorts/",
    "https://www.onthesnow.com/ohio/ski-resorts/",
    "https://www.onthesnow.com/oklahoma/ski-resorts/",
    "https://www.onthesnow.com/oregon/ski-resorts/",
    "https://www.onthesnow.com/pennsylvania/ski-resorts/",
    "https://www.onthesnow.com/rhode-island/ski-resorts/",
    "https://www.onthesnow.com/south-carolina/ski-resorts/",
    "https://www.onthesnow.com/south-dakota/ski-resorts/",
    "https://www.onthesnow.com/tennessee/ski-resorts/",
    "https://www.onthesnow.com/texas/ski-resorts/",
    "https://www.onthesnow.com/utah/ski-resorts/",
    "https://www.onthesnow.com/vermont/ski-resorts/",
    "https://www.onthesnow.com/virginia/ski-resorts/",
    "https://www.onthesnow.com/washington/ski-resorts/",
    "https://www.onthesnow.com/west-virginia/ski-resorts/",
    "https://www.onthesnow.com/wisconsin/ski-resorts/",
    "https://www.onthesnow.com/wyoming/ski-resorts/",
    "https://www.onthesnow.com/canada/ski-resorts/",
    "https://www.onthesnow.com/alberta/ski-resorts/",
    "https://www.onthesnow.com/british-columbia/ski-resorts/",
    "https://www.onthesnow.com/manitoba/ski-resorts/",
    "https://www.onthesnow.com/new-brunswick/ski-resorts/",
    "https://www.onthesnow.com/newfoundland-and-labrador/ski-resorts/",
    "https://www.onthesnow.com/nova-scotia/ski-resorts/",
    "https://www.onthesnow.com/ontario/ski-resorts/",
    "https://www.onthesnow.com/quebec/ski-resorts/",
    "https://www.onthesnow.com/saskatchewan/ski-resorts/",
    "https://www.onthesnow.com/austria/ski-resorts/",
    "https://www.onthesnow.com/france/ski-resorts/",
    "https://www.onthesnow.com/switzerland/ski-resorts/",
    "https://www.onthesnow.com/italy/ski-resorts/",
    "https://www.onthesnow.com/germany/ski-resorts/",
    "https://www.onthesnow.com/norway/ski-resorts/",
    "https://www.onthesnow.com/sweden/ski-resorts/",
    "https://www.onthesnow.com/spain/ski-resorts/",
    "https://www.onthesnow.com/andorra/ski-resorts/",
    "https://www.onthesnow.com/japan/ski-resorts/",
    "https://www.onthesnow.com/australia/ski-resorts/",
    "https://www.onthesnow.com/new-zealand/ski-resorts/",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}


class SkiResortScraper(BaseScraper):
    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scraped_count = 0
        self.error_count = 0
        self.batch_size = 50
        self.pending_resorts = []
        self.max_retries = 3
        self.base_delay = 2

    async def scrape_site(self, page: Page):
        self.logger.info("Starting ski resort scraping...")

        for region_url in REGION_URLS:
            try:
                self.logger.info(f"Scraping region: {region_url}")
                resort_links = await self.get_resort_links_from_region(region_url)
                self.logger.info(f"Found {len(resort_links)} resorts in region")

                for resort_name, resort_url in resort_links:
                    try:
                        details = await self.scrape_resort_details(
                            page, resort_url, resort_name
                        )
                        if details:
                            self.pending_resorts.append(details)

                            if len(self.pending_resorts) >= self.batch_size:
                                await self.flush_batch()

                        await asyncio.sleep(self.settings.scrape_delay_seconds)

                    except Exception as e:
                        self.logger.error(f"Error scraping {resort_name}: {e}")
                        self.error_count += 1

            except Exception as e:
                self.logger.error(f"Error scraping region {region_url}: {e}")

        if self.pending_resorts:
            await self.flush_batch()

        self.logger.info(
            f"Scraping complete. Total: {self.scraped_count}, Errors: {self.error_count}"
        )

    async def get_resort_links_from_region(
        self, region_url: str
    ) -> list[tuple[str, str]]:
        try:
            response = requests.get(region_url, headers=HEADERS, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch region page {region_url}: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        resort_links = []
        seen_urls = set()

        resort_elements = soup.find_all("a", href=re.compile(r"/\w+.*/ski-resort"))

        for elem in resort_elements:
            url = elem.get("href")
            name = elem.get_text(strip=True)

            if url and isinstance(url, str) and url not in seen_urls and name:
                if "VIEW" not in name and len(name) > 2:
                    seen_urls.add(url)
                    full_url = url if url.startswith("http") else BASE_URL + url
                    resort_links.append((name, full_url))

        return resort_links

    async def scrape_resort_details(
        self, page: Page, resort_url: str, fallback_name: str
    ) -> Optional[dict]:
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Navigating to resort page: {resort_url}")
                await page.goto(resort_url, timeout=60000)
                await page.wait_for_load_state("load", timeout=60000)
                await asyncio.sleep(self.sleep)

                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")

                details = {
                    "resort_name": None,
                    "latitude": None,
                    "longitude": None,
                    "base_elevation": None,
                    "summit_elevation": None,
                    "pass_affiliation": None,
                }

                details["resort_name"] = self._extract_resort_name(soup, fallback_name)

                geo_data = self._extract_json_ld(soup)
                if geo_data:
                    details["latitude"] = geo_data.get("latitude")
                    details["longitude"] = geo_data.get("longitude")

                elevations = await self._extract_elevations(page)
                if elevations:
                    details["base_elevation"] = elevations.get("base_elevation")
                    details["summit_elevation"] = elevations.get("summit_elevation")

                details["pass_affiliation"] = self._detect_pass_affiliation(soup)

                return details

            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed for {resort_url}: {e}"
                )
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2**attempt)
                    self.logger.info(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"All retries exhausted for {resort_url}")
                    return None

    def _extract_resort_name(self, soup: BeautifulSoup, fallback: str) -> Optional[str]:
        h1 = soup.find("h1")
        if h1:
            name = h1.get_text(strip=True)
            if name:
                return name

        title = soup.find("title")
        if title:
            title_text = title.get_text(strip=True)
            name = title_text.split("|")[0].split("-")[0].strip()
            if name and len(name) > 2:
                return name

        return fallback

    def _extract_json_ld(self, soup: BeautifulSoup) -> dict:
        script_tags = soup.find_all("script", type="application/ld+json")
        for tag in script_tags:
            try:
                data = json.loads(tag.string)
                if isinstance(data, list):
                    for item in data:
                        if (
                            item.get("@type")
                            in ["SkiResort", "Place", "TouristAttraction"]
                            and "geo" in item
                        ):
                            return item["geo"]
                elif isinstance(data, dict):
                    if (
                        data.get("@type") in ["SkiResort", "Place", "TouristAttraction"]
                        and "geo" in data
                    ):
                        return data["geo"]
                    if "geo" in data:
                        return data["geo"]
            except (json.JSONDecodeError, TypeError):
                continue
        return {}

    async def _extract_elevations(self, page: Page) -> dict:
        elevations: dict[str, Optional[float]] = {
            "base_elevation": None,
            "summit_elevation": None,
        }

        try:
            json_ld_data = await self._extract_json_ld_elevations(page)
            if json_ld_data:
                elevations["base_elevation"] = json_ld_data.get("base_elevation")
                elevations["summit_elevation"] = json_ld_data.get("summit_elevation")
                if elevations["base_elevation"] and elevations["summit_elevation"]:
                    return elevations

            main_texts = await page.query_selector_all(".styles_main_text__vitr9")
            secondary_texts = await page.query_selector_all(
                ".styles_secondary_text__iHrky"
            )

            for i, main_text in enumerate(main_texts):
                if i >= len(secondary_texts):
                    break
                value = await main_text.inner_text()
                elev_match = re.search(r"([\d,]+)\s*['\"]?", value)
                if elev_match:
                    elev = float(elev_match.group(1).replace(",", ""))
                    if 1000 < elev < 16000:
                        label = await secondary_texts[i].inner_text()
                        label_lower = label.lower()
                        if "base" in label_lower:
                            elevations["base_elevation"] = elev
                        elif "summit" in label_lower or "top" in label_lower:
                            elevations["summit_elevation"] = elev

            if (
                elevations["base_elevation"] is None
                or elevations["summit_elevation"] is None
            ):
                page_text = await page.inner_text("body")
                all_elevations = re.findall(r"([\d,]+)\s*['\"]", page_text)
                valid_elevs = []
                for n in all_elevations:
                    try:
                        val = float(n.replace(",", ""))
                        if 1000 < val < 16000:
                            valid_elevs.append(val)
                    except ValueError:
                        continue

                if elevations["base_elevation"] is None and valid_elevs:
                    elevations["base_elevation"] = min(valid_elevs)
                if elevations["summit_elevation"] is None and len(valid_elevs) >= 2:
                    elevations["summit_elevation"] = max(valid_elevs)

        except Exception as e:
            self.logger.error(f"Error extracting elevations: {e}")

        return elevations

    async def _extract_json_ld_elevations(self, page: Page) -> dict:
        try:
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")
            script_tags = soup.find_all("script", type="application/ld+json")
            for tag in script_tags:
                try:
                    text = tag.string
                    if not text:
                        continue
                    data = json.loads(text)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if "additionalProperty" in item:
                            result = {}
                            for prop in item.get("additionalProperty", []):
                                name = prop.get("name", "").lower()
                                value = prop.get("value")
                                if "base elevation" in name and value:
                                    result["base_elevation"] = float(value)
                                elif "summit elevation" in name and value:
                                    result["summit_elevation"] = float(value)
                            if result:
                                return result
                except (json.JSONDecodeError, TypeError):
                    continue
        except Exception:
            pass
        return {}

    def _normalize_elevation(self, value: float, unit: str) -> float:
        """Convert elevation to feet. Defaults to feet if unit is unknown."""
        if unit and unit.lower() == "m":
            return value * 3.28084
        return value

    def _detect_pass_affiliation(self, soup: BeautifulSoup) -> Optional[str]:
        page_text = soup.get_text().lower()

        if "epic pass" in page_text or "epic day" in page_text:
            return "Epic"
        if "ikon pass" in page_text or "ikon day" in page_text:
            return "Ikon"
        if "indy pass" in page_text:
            return "Indy"
        if "mountain collective" in page_text:
            return "Mountain Collective"

        return None

    async def flush_batch(self):
        if not self.pending_resorts:
            return

        self.logger.info(
            f"Flushing batch of {len(self.pending_resorts)} resorts to database..."
        )

        for details in self.pending_resorts:
            try:
                resort = SkiResort(**details)
                self.session.add(resort)
                self.scraped_count += 1
                self.logger.info(
                    f"Inserted resort: {details.get('resort_name')} | "
                    f"Base: {details.get('base_elevation')} | "
                    f"Summit: {details.get('summit_elevation')} | "
                    f"Lat: {details.get('latitude')} | Lon: {details.get('longitude')}"
                )
            except Exception as e:
                self.logger.error(f"Error creating SkiResort: {e}")
                self.error_count += 1

        self.session.commit()
        self.pending_resorts = []
        self.logger.info(f"Batch flush complete. Total scraped: {self.scraped_count}")
