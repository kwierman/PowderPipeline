# Powder Pipeline

<img src="public/SnowAnalytics.png" alt="Snow Analytics" width="400"/>



## The Problem This Library Solves

You're an avid skier. You intend on getting as many days on fresh snow as possible. The question that you pose year-after-year is: "Which pass should I buy? Where should I plan my trips?"

The problems faced here are:

* Each pass provider (Epic, Ikon, Indy, Mountain Collective) offer different price points, early bird pricing, blackout days, etc...
* Every year we face challenges with climate change, El Niño/La Niña cycles, different opening and closing days for resorts, you name it.
* Every season pass has dynamic pricing every year, and there's no readily available historic record of pass prices (as of the writing of this README).
* Each pass has diffent resorts associated with it.
* Just buying EVERY pass invariably ends up wasting money unless you have a season like I had two years ago and you can eek out ~100 days of skiing. I don't think every working professional can do that.

## The Solution

The solution is to gather as much information as possible from open sources. We can then create an output table and perform some analytics to get us the final ROI: # Days/ $Dollar for each pass.

## The Approach

Normally, I'd call this a methods session, but the intended audience would be an avid skier, so it's an approach.

### Setup

Clone this repo with 

``` bash
git clone https://github.com/kwierman/PowderPipeline
```

Then, edit the example config in `example_config.yml` to suit your system. Install in a `venv` using your tool of choice, and you're off to the races!

### 1. Use the internet's Way Back Machine to fetch the pass prices

| Pass | Operator | Since |
|------|----------|-------|
| **Epic Pass** | Vail Resorts | ~2008 |
| **Ikon Pass** | Alterra Mountain Co. | 2018 |
| **Indy Pass** | Powder Alliance (independent) | 2019 |
| **Mountain Collective** | Independent co-op | 2012 |

This _should_ be relatively straight-forward, but bot mitigation tends to be a problem. The good news is that **I** have some experience using Playwright to get past this, which brings us to a brief aside on ethics.

#### Legal & Ethical Notes

- This tool uses the _Internet Archive (Wayback Machine)_ for historical data — a public resource explicitly designed for archival research.
- Live scraping respects a 1.5-second delay between requests (`REQUEST_DELAY`).
- **Data is used for personal/research analysis only.**
- Always check a website's `robots.txt` and Terms of Service before scraping.

This should output a CSV with the following schema:

| Column | Type | Description |
|--------|------|-------------|
| `pass_brand` | str | Ikon / Epic / Indy / Mountain Collective |
| `pass_name` | str | Full product name (e.g. "Epic Local Pass") |
| `season` | str | "2023-24" format |
| `price_usd` | float | Full retail price at launch |
| `early_bird_price` | float | Pre-sale / early-bird price if available |
| `early_bird_deadline` | str | Date by which early-bird price expires |
| `num_resorts` | int | Number of participating resorts |
| `blackout_days` | int | Number of blackout days (−1 = no blackouts) |
| `unlimited_days` | bool | True if unlimited access |
| `limited_days` | int | Number of days if access is limited |
| `resorts_list` | str | Comma-separated resort names (when available) |
| `source_url` | str | URL from which this record was scraped |
| `snapshot_date` | str | Wayback Machine capture timestamp |
| `scraped_at` | str | ISO timestamp of when the script ran |
| `notes` | str | Free-text notes / anomalies |

This is accessible from the CLI with the following command:

~~~ bash
powderpipeline scrape ski-passes
~~~

In the future, we can replace this with two commands, one for backfilling the data, and one for getting the current price, and run this pipeline once a year on automation.

> Before running any commands, reference, the setup guide above.

### 2. Obtain a list of resorts and which of the big passes (if any) they are associated with

Once again, we're going to need to do some web scraping. We can also use this step to fill in information regarding the location of each resort. The Python Package, `GeoPy` can help us out there. Here, we can reference open information to obtain an output csv with the following format:

| Column | Type | Description |
|--------|------|-------------|
| `pass_brand` | str | Matches "pass type" above. |
| `name` | str | The name of the resort. We can treat this as a primary key. |
| `latitude` | float | Location latitude, for finding snow depth later |
| `longitude` | float | Location longitude, for finding snow depth later |
| `base_elevation_ft` | int | The elevation of the base of the resort, in feet |
| `summit_elevation_ft`| int | The elevation of the summit of the resort, in feet |
| `state` | str | The name of the state for each resort. This can be used for later analysis |
| `scraped_at` | str | ISO timestamp of when the script ran |
| `notes` | str | Free-text notes / anomalies |

I'm choosing to put this in `csv` format for the reason that this should not be a very large dataset and therefore can be safely housed in memory. 

I intend to put this step behind a CLI with the command:

~~~ bash
powderpipeline scrape ski-resorts
~~~


### 3. Get Snow Depth for each resort and additional information.

For this, `meteo` provides a rate-limited API which we can use to house this information. I'm going to store this in `DuckDB` so that I can _slowly_ fill this. This should output a table of the format:

| Column | Type | Description |
|--------|------|-------------|
| `ski_resort` | str | Matches "name" in the ski resort data. |
| `date` | datetime | The date at which this measurement was taken.|
| `base_snow_depth_ft` | int | The snow depth at the base, in feet |
| `base_snowfall_in` | int | The snowfall for this day, in inches. Should be aggregate over the 24 hour period. |
| `summit_snow_depth_ft` | int | The snow depth at the summit, in feet |
| `summit_snowfall_in` | int | The snowfall for this day, in inches. Should be aggregate over the 24 hour period. |  
| `scraped_at` | str | ISO timestamp of when the script ran |
| `notes` | str | Free-text notes / anomalies |

This should run behind two commands:

~~~ bash
powderpipeline scrape snowfall-backfill
~~~

This should be run as a backfill to get historic data.

~~~ bash
powderpipeline scrape snowfall
~~~

This should be run under automation daily.

### 4. Run analysis

All of these individual datasets can be analyzed individually, but it's far more useful to combine these into a single dataset for later analysis. This should be output into parquet for analysis with `Dask` using the command:

~~~ bash
powderpipeline analyze
~~~


### 5. Run Visualization

Likewise, there is a Dashboard built with Plotly Dash, that you can bring up with

~~~ bash
powderpipeline viz
~~~


# References

| Data Model | Source Name | Link |
| ---------- | ----------- | ---- |
| Snowpack   | USDA        | [Link](https://wcc.sc.egov.usda.gov/awdbRestApi/swagger-ui/index.html#) |



