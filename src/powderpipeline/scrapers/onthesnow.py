import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
import time

# --- Configuration ---
# Target the main US ski resorts page on OnTheSnow
BASE_URL = "https://www.onthesnow.com"
START_URL = f"{BASE_URL}/united-states/ski-resorts/"

# Headers are critical to avoid 403 Forbidden errors and mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

def extract_json_ld(soup):
    """Extracts and parses JSON-LD script tags to reliably find geographical data."""
    # Target: <script type="application/ld+json">
    script_tags = soup.find_all('script', type='application/ld+json')
    for tag in script_tags:
        try:
            data = json.loads(tag.string)
            # JSON-LD can be a list or a dictionary
            if isinstance(data, list):
                for item in data:
                    if item.get('@type') in ['SkiResort', 'Place'] and 'geo' in item:
                        return item['geo']
            elif isinstance(data, dict):
                if data.get('@type') in['SkiResort', 'Place'] and 'geo' in data:
                    return data['geo']
        except (json.JSONDecodeError, TypeError):
            continue
    return {}

def scrape_resort_details(resort_url):
    """Scrapes individual resort pages for precise elevation, lat/lon, and pass data."""
    try:
        response = requests.get(resort_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Initialize data dictionary with 'N/A' defaults
        data = {
            'latitude': 'N/A',
            'longitude': 'N/A',
            'base_elevation': 'N/A',
            'summit_elevation': 'N/A',
            'pass_provider': 'N/A'
        }
        
        # 2. Extract Lat/Lon using JSON-LD (Schema markup)
        geo_data = extract_json_ld(soup)
        if geo_data:
            try:
                # Ensure they are extracted as floats
                data['latitude'] = float(geo_data.get('latitude', 'N/A'))
                data['longitude'] = float(geo_data.get('longitude', 'N/A'))
            except ValueError:
                pass # Fallback to 'N/A' if conversion fails
                
        # 3. Extract Elevations
        # Target: Commonly found in stat blocks like <div class="elevation-stats"> or <dl>
        # We use regex to find the text "Base" and "Summit" to make it robust against class changes
        base_elem = soup.find(string=re.compile("Base Elevation", re.IGNORECASE))
        if base_elem:
            # Look at the parent or next sibling to grab the actual number (e.g., <span>8,500 ft</span>)
            parent = base_elem.find_parent()
            if parent and parent.find_next_sibling():
                data['base_elevation'] = parent.find_next_sibling().get_text(strip=True)

        summit_elem = soup.find(string=re.compile("Summit Elevation", re.IGNORECASE))
        if summit_elem:
            parent = summit_elem.find_parent()
            if parent and parent.find_next_sibling():
                data['summit_elevation'] = parent.find_next_sibling().get_text(strip=True)

        # 4. Extract Pass Provider
        # Target: Scanning the entire page text or specific ticket wrappers for pass keywords
        page_text = soup.get_text().lower()
        if 'epic pass' in page_text:
            data['pass_provider'] = 'Epic'
        elif 'ikon pass' in page_text:
            data['pass_provider'] = 'Ikon'
        elif 'indy pass' in page_text:
            data['pass_provider'] = 'Indy'
        elif 'mountain collective' in page_text:
            data['pass_provider'] = 'Mountain Collective'
            
        return data

    except requests.RequestException as e:
        print(f"Error scraping {resort_url}: {e}")
        return None

def main():
    print(f"Fetching main list from {START_URL}...")
    try:
        response = requests.get(START_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch the main page: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    resorts_data =[]

    # Target: The resort list items. OnTheSnow usually wraps these in an anchor tag 
    # with a specific class, or inside a list <ul> with class 'resortList'
    # We look for all links that have '/skiresort/' or '/ski-resort/' in the href.
    resort_links = soup.find_all('a', href=re.compile(r'/.*(ski-resorts?|profile).*\.html'))
    
    # Deduplicate links
    seen_urls = set()
    valid_resort_links =[]
    for link in resort_links:
        url = link.get('href')
        name = link.get_text(strip=True)
        if url and url not in seen_urls and name:
            seen_urls.add(url)
            # Make sure it's a full URL
            full_url = url if url.startswith('http') else BASE_URL + url
            valid_resort_links.append((name, full_url))

    print(f"Found {len(valid_resort_links)} potential resorts. Beginning detail scrape...")

    # Limit to the first 10 for demonstration/testing so we don't spam the server
    # Remove '[:10]' to scrape the entire site.
    for name, url in valid_resort_links[:10]:
        print(f"Scraping data for: {name}...")
        
        details = scrape_resort_details(url)
        
        if details:
            resort_info = {
                'name': name,
                'latitude': details['latitude'],
                'longitude': details['longitude'],
                'base_elevation': details['base_elevation'],
                'summit_elevation': details['summit_elevation'],
                'pass_provider': details['pass_provider']
            }
            resorts_data.append(resort_info)
            
        # Polite scraping: Wait 1-2 seconds between requests to avoid IP bans
        time.sleep(1.5)

    # Output to Pandas DataFrame
    df = pd.DataFrame(resorts_data)
    
    # Fill any genuinely missing blank strings with 'N/A' to be safe
    df.replace("", "N/A", inplace=True)
    df.fillna("N/A", inplace=True)

    print("\nScraping Complete. Here is a preview of the data:")
    print(df.head())

    # Save to CSV
    csv_filename = 'ski_resorts.csv'
    df.to_csv(csv_filename, index=False)
    print(f"\nData successfully saved to {csv_filename}")

if __name__ == "__main__":
    main()