"""
Dataset 2: IPL Auction Data — all seasons (2008–2024)
Output: ipl_auction_data.csv
Common join key with player stats dataset: 'player' (name) and 'team'

How it works:
  - Navigates to https://www.iplt20.com/auction/{year}
  - Waits for Angular to render the auction table
  - Extracts player name, team, base price, sold price, type, nationality
  - Cleans price columns to numeric (₹ crores)

Requirements:
  pip install playwright pandas
  playwright install chromium

IMPORTANT — run from your local machine, NOT a cloud server.
The website blocks datacenter IPs. It works fine from home/office.
"""

import asyncio
import re
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError as PwTimeout

# ── Config ────────────────────────────────────────────────────────────────────
# Auctions were not held every year (2009 mini, 2010 mini, etc.)
# The site has pages for these years — we try them all and skip gracefully.
AUCTION_YEARS = list(range(2008, 2025))
AUCTION_URL   = "https://www.iplt20.com/auction/{year}"

# Typical auction table columns (vary slightly by year)
# Pos | Player | Type | Nationality | Base Price | Sold Price | Team
AUCTION_COLS = ["pos", "player_raw", "player_type", "nationality",
                "base_price_raw", "sold_price_raw", "team_raw"]

# ── Price cleaner ─────────────────────────────────────────────────────────────

def parse_price_cr(val: str) -> float | None:
    """
    Convert IPL price strings to crores (float).
    Handles:  ₹2.4 Cr  |  ₹240 L  |  240 Lacs  |  2.4 Cr  |  2400000
    """
    if not val or val.strip() in ("-", "", "N/A", "Unsold", "RTM"):
        return None
    val = re.sub(r"[₹,\s]", "", val.upper())
    try:
        if "CR" in val:
            return float(val.replace("CR", "").strip())
        if "L" in val:                             # Lacs / Lakhs
            return round(float(val.replace("L", "").replace("LACS", "").strip()) / 100, 4)
        num = float(val)
        if num > 100:                              # raw rupee figure
            return round(num / 1_00_00_000, 4)    # convert to crores
        return num
    except ValueError:
        return None

# ── Browser setup ─────────────────────────────────────────────────────────────

async def browser_context(playwright):
    """Launch Chromium with settings that bypass bot detection."""
    browser = await playwright.chromium.launch(
        headless=False,          # Must be False – site blocks headless fingerprints
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--window-size=1280,900",
        ],
    )
    ctx = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 900},
        locale="en-US",
    )
    await ctx.add_init_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
        "Object.defineProperty(navigator,'plugins',{get:()=>[1,2,3,4,5]});"
    )
    return browser, ctx

# ── Scrape single year ────────────────────────────────────────────────────────

TEAM_ABBRS = {
    "MI", "CSK", "RCB", "KKR", "DC", "PBKS", "RR", "SRH", "GT", "LSG",
    "PWI", "KXIP", "DD", "RPS", "GL", "KTK", "DEC", "TRL", "HYD",
    "MUMBAI INDIANS", "CHENNAI SUPER KINGS", "ROYAL CHALLENGERS",
    "KOLKATA KNIGHT RIDERS", "DELHI CAPITALS", "PUNJAB KINGS",
    "RAJASTHAN ROYALS", "SUNRISERS HYDERABAD", "GUJARAT TITANS",
    "LUCKNOW SUPER GIANTS",
}

# Full team name → abbreviation mapping for normalisation
TEAM_NORM = {
    "MUMBAI INDIANS": "MI",
    "CHENNAI SUPER KINGS": "CSK",
    "ROYAL CHALLENGERS BANGALORE": "RCB",
    "ROYAL CHALLENGERS BENGALURU": "RCB",
    "KOLKATA KNIGHT RIDERS": "KKR",
    "DELHI CAPITALS": "DC",
    "DELHI DAREDEVILS": "DC",
    "PUNJAB KINGS": "PBKS",
    "KINGS XI PUNJAB": "PBKS",
    "RAJASTHAN ROYALS": "RR",
    "SUNRISERS HYDERABAD": "SRH",
    "GUJARAT TITANS": "GT",
    "LUCKNOW SUPER GIANTS": "LSG",
    "PUNE WARRIORS": "PWI",
    "RISING PUNE SUPERGIANT": "RPS",
    "RISING PUNE SUPERGIANTS": "RPS",
    "GUJARAT LIONS": "GL",
    "KOCHI TUSKERS KERALA": "KTK",
    "DECCAN CHARGERS": "DEC",
}


def norm_team(raw: str) -> str:
    """Normalise team name to its standard abbreviation."""
    key = raw.strip().upper()
    return TEAM_NORM.get(key, key)


async def scrape_auction_year(page, year: int) -> pd.DataFrame:
    url = AUCTION_URL.format(year=year)
    print(f"  Loading {url}")

    try:
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        if resp and resp.status == 403:
            print(f"  ✗ 403 — IP blocked. Run from home/office machine.")
            return pd.DataFrame()
        if resp and resp.status == 404:
            print(f"  ⚠ No auction page for {year} (404), skipping.")
            return pd.DataFrame()
    except Exception as e:
        print(f"  ✗ Navigation failed: {e}")
        return pd.DataFrame()

    # Wait for Angular to render
    await page.wait_for_timeout(4000)

    # ── Try to find and click any "View All" / "Load More" button ────────────
    for sel in [
        "a[ng-click*='showAll']",
        "a.view-all",
        "a:has-text('View All')",
        "button:has-text('View All')",
    ]:
        try:
            loc = page.locator(sel)
            if await loc.count() > 0:
                await loc.first.click()
                await page.wait_for_timeout(2000)
                print(f"  ✓ Clicked 'View All': {sel}")
                break
        except Exception:
            continue

    # ── Wait for table rows ───────────────────────────────────────────────────
    for header_sel in [
        "tr.top-players__header",
        "tr[class*='auction']",
        "tr[class*='top-players']",
        "table tbody tr",
    ]:
        try:
            await page.wait_for_selector(header_sel, timeout=8000)
            break
        except PwTimeout:
            continue

    await page.wait_for_timeout(1500)

    # ── Extract rows ──────────────────────────────────────────────────────────
    trs = await page.query_selector_all(
        "tr[class*='top-players']:not([class*='header'])"
    )
    if not trs:
        trs = await page.query_selector_all("tbody tr")

    if not trs:
        print(f"  ✗ No rows found for {year}")
        return pd.DataFrame()

    records = []
    for tr in trs:
        tds = await tr.query_selector_all("td")
        if len(tds) < 4:
            continue
        texts = [(await td.inner_text()).strip() for td in tds]
        # Pad/trim to expected column count
        padded = (texts + [""] * len(AUCTION_COLS))[: len(AUCTION_COLS)]
        rec = dict(zip(AUCTION_COLS, padded))
        rec["year"] = year
        records.append(rec)

    if not records:
        print(f"  ✗ No valid rows parsed for {year}")
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # ── Clean player + team columns ───────────────────────────────────────────
    df["player"] = df["player_raw"].str.strip().str.title()
    df["team"]   = df["team_raw"].apply(norm_team)

    # ── Clean price columns ───────────────────────────────────────────────────
    df["base_price_cr"] = df["base_price_raw"].apply(parse_price_cr)
    df["sold_price_cr"] = df["sold_price_raw"].apply(parse_price_cr)

    # ── Drop raw columns ──────────────────────────────────────────────────────
    df.drop(columns=["player_raw", "team_raw", "base_price_raw", "sold_price_raw"],
            inplace=True)

    print(f"  ✓ {len(df)} player records for {year}")
    return df


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    all_frames: list[pd.DataFrame] = []

    async with async_playwright() as pw:
        browser, ctx = await browser_context(pw)
        page = await ctx.new_page()

        for year in AUCTION_YEARS:
            print(f"\n── {year} ──────────────────────────────────────────")
            df = await scrape_auction_year(page, year)
            if not df.empty:
                all_frames.append(df)
            await asyncio.sleep(2.5)   # polite delay between years

        await browser.close()

    if not all_frames:
        print("\n✗ No data scraped. Are you running on your local machine?")
        return

    final = pd.concat(all_frames, ignore_index=True)

    # Ensure consistent dtypes
    final["year"] = final["year"].astype(int)
    final["base_price_cr"] = pd.to_numeric(final["base_price_cr"], errors="coerce")
    final["sold_price_cr"] = pd.to_numeric(final["sold_price_cr"], errors="coerce")

    out = "ipl_auction_data.csv"
    final.to_csv(out, index=False)
    print(f"\n✅ Saved {len(final)} rows → {out}")
    print(final.head(10).to_string())


if __name__ == "__main__":
    asyncio.run(main())
