import asyncio
import logging
from abc import ABC, abstractmethod

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from ..config import Settings
from ..lake.base_writer import BaseWriter
from ..warehouse import Session


class BaseScraper(ABC):
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        session: Session,
        writer: BaseWriter,
        settings: Settings,
        sleep=1,
        headless=False,
    ):
        self.session = session
        self.writer = writer
        self.sleep = sleep
        self.headless = headless
        self.settings = settings

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.commit()

    def scrape(self):
        asyncio.run(self.__scrape_async())

    async def navigate(self, page, url):
        self.logger.info(f"Navigating to: {url}")
        await page.goto(url)
        await asyncio.sleep(self.sleep)

    async def __scrape_async(self):
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            webdriver_status = await page.evaluate("navigator.webdriver")
            self.logger.info(f"Navigator.webdriver status: {webdriver_status}")
            await self.scrape_site(page)
            await browser.close()

    @abstractmethod
    def scrape_site(self, page):
        raise NotImplementedError("Subclasses must implement the scrape_site method.")
