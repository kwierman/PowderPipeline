from abc import ABC, abstractmethod


class BaseScraper(ABC):

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }


    def __init__(self, settings, session):
        self.settings = settings
        self.session = session

    @abstractmethod
    def scrape(self):
        """
        Main method to perform the scraping. This should be implemented by all subclasses.
        """
        raise NotImplementedError("Subclasses must implement the scrape method.")
"""


def scrape_quotes():
    # Use a context manager to ensure the browser is closed automatically
    with sync_playwright() as p:
        # Launch the Chromium browser in headless mode (background operation)
        # Set headless=False to watch the browser actions
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()

        # Navigate to the target page and wait for it to load
        page.goto("http://quotes.toscrape.com")
        
        # Use Playwright's auto-waiting to ensure elements are present
        # Here we wait for the first quote element to be visible
        page.wait_for_selector(".quote") 

        # Extract data using locators
        quotes = page.locator(".quote").all()
        
        scraped_data = []
        for quote_element in quotes:
            # Get the text content of the elements within the quote container
            text = quote_element.locator(".text").inner_text()
            author = quote_element.locator(".author").inner_text()
            scraped_data.append({"quote": text, "author": author})

        # Close the browser instance
        browser.close()
        
        return scraped_data

if __name__ == "__main__":
    data = scrape_quotes()
    for item in data:
        print(f"Quote: {item['quote']}")
        print(f"Author: {item['author']}")
        print("-" * 20)
"""