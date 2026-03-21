import re

from .base import BaseScraper
from playwright.sync_api import sync_playwright
from rich.progress import track
from ..db.ski_pass import SkiPass
from playwright_stealth import stealth
import logging
import time
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

class SkiPassScraper(BaseScraper):

    logger = logging.getLogger(__name__)

    def clean_text(self, text: str) -> str:
        """Removes excess whitespace and newlines from scraped text."""
        return re.sub(r'\s+', ' ', text).strip() if text else "N/A"

    async def scrape_site(self, ski_pass_meta: dict, page):
        await page.goto(ski_pass_meta.url, timeout=60000)
        try:
            await page.wait_for_selector(ski_pass_meta.wait_for, timeout=150000)
        except TimeoutError:
            print(f"[{ski_pass_meta.name.upper()}] Warning: Could not find main container. The DOM might have changed.")
        await asyncio.sleep(3) 
        main_title_locator = await page.locator(ski_pass_meta.name).first
        main_pass_name = self.clean_text(main_title_locator.inner_text()) if main_title_locator.is_visible() else f"{ski_pass_meta.provider.capitalize()} Pass"

        # Locate all pricing cards/rows
        cards = await page.locator(ski_pass_meta.card).all()
        
        if not cards:
            print(f"[{ski_pass_meta.provider.upper()}] No pricing cards found using selector: '{ski_pass_meta.card}'")
            return

        for card in cards:
            try:
                # In some layouts, the pass name is inside the card (e.g., Ikon Base vs Ikon Pro)
                card_title_loc = await card.locator(ski_pass_meta.name).first
                pass_name = self.clean_text(card_title_loc.inner_text()) if card_title_loc.is_visible() else main_pass_name
                
                age_loc = await card.locator(ski_pass_meta.age).first
                age_range = self.clean_text(age_loc.inner_text()) if age_loc.is_visible() else "All Ages / Unknown"
                
                price_loc = await card.locator(ski_pass_meta.price).first
                price = self.clean_text(price_loc.inner_text()) if price_loc.is_visible() else "Price Hidden"
                ski_pass = SkiPass(
                    provider=ski_pass_meta.provider.capitalize(),
                    pass_name=pass_name,
                    pass_type=ski_pass_meta.get('type', 'Standard'),
                    age_range=age_range,
                    price=price
                )
                self.logging.info(f"Scraped ski pass: {ski_pass.provider} - {ski_pass.pass_name} - {ski_pass.age_range} - {ski_pass.price}")
                self.session.add(ski_pass)

            except Exception as e:
                print(f"[{ski_pass_meta.provider.upper()}] Error parsing a card: {e}")



    async def scrape_async(self):
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=False) 
            page = await browser.new_page()
            webdriver_status = await page.evaluate("navigator.webdriver")
            self.logger.info(f"Navigator.webdriver status: {webdriver_status}")
            for ski_pass_meta in track(self.settings.ski_passes, description="Scraping ski pass data..."):
                await self.scrape_site(ski_pass_meta, page)
            self.session.commit()

    def scrape(self):
        asyncio.run(self.scrape_async())
"""
api_key=
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
from openai import OpenAI
client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
model_name = 'google/gemini-3-pro-preview'
response = client.chat.completions.create(model=model_name,messages=[{'role':'user', 'content':'What are the prices for Epic Pass'}]
)
response = client.chat.completions.create(model=model_name,messages=[{'role':'user', 'content':'What are the prices for Epic Pass', 'max_tokens': '3333'}]
)
response = client.chat.completions.create(model=model_name,messages=[{'role':'user', 'content':'What are the prices for Epic Pass'}], max_tokens= 3333)
response
response.choices
len(response.choices)
response.choices[0]
choice = response.choices[0]
choice.dict
choice.dict.keys()
choice.dict().keys()
choice.to_dict()
choice.to_dict().keys()
choice.to_dict()['finish_reason']
choice.to_dict()['message']
type(choice.to_dict()['message'])
choice.to_dict()['message'].keys()
choice.to_dict()['message']['content']
choice.to_dict()['message']['content'].split('\n')
history
import readline
for i in range(1, readline.get_current_history_length() + 1):
    print(readline.get_history_item(i))

"""