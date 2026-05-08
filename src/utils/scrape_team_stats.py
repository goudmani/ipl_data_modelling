"""
Dataset 1: IPL Team Stats (Wins, Losses, NRR) across all years
URL: https://www.iplt20.com/matches/points-table/{year}
Common join column: 'team'

pip install playwright pandas
playwright install chromium
"""

import asyncio
import pandas as pd
from playwright.async_api import async_playwright

IPL_YEARS = list(range(2008, 2027))
POINTS_TABLE_URL = "https://www.iplt20.com/matches/points-table/{year}"

async def scrape_points_table(page, year):
    url = POINTS_TABLE_URL.format(year=year)
    print(f"  Scraping {url}...")
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        await page.wait_for_selector(".standings-table tbody tr", timeout=10000)

        rows = await page.query_selector_all(".standings-table tbody tr")
        records = []
        for row in rows:
            cols = await row.query_selector_all("td")
            if len(cols) < 7:
                continue
            texts = [await c.inner_text() for c in cols]
            record = {
                "year":      year,
                "position":  texts[0].strip() if len(texts) > 0 else "",
                "team":      texts[1].strip() if len(texts) > 1 else "",
                "matches":   texts[2].strip() if len(texts) > 2 else "",
                "won":       texts[3].strip() if len(texts) > 3 else "",
                "lost":      texts[4].strip() if len(texts) > 4 else "",
                "no_result": texts[5].strip() if len(texts) > 5 else "",
                "points":    texts[6].strip() if len(texts) > 6 else "",
                "nrr":       texts[7].strip() if len(texts) > 7 else "",
                "form":      texts[8].strip() if len(texts) > 8 else "",
            }
            if record["team"]:
                records.append(record)
        print(f"    ✓ {len(records)} teams for {year}")
        return records
    except Exception as e:
        print(f"    ✗ Failed for {year}: {e}")
        return []

async def main():
    all_records = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        for year in IPL_YEARS:
            records = await scrape_points_table(page, year)
            all_records.extend(records)
            await asyncio.sleep(1.5)
        await browser.close()

    if not all_records:
        print("No data scraped — check selectors in DevTools.")
        return

    df = pd.DataFrame(all_records)
    df["team"] = df["team"].str.strip().str.upper()
    for col in ["matches", "won", "lost", "no_result", "points"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["nrr"] = pd.to_numeric(df["nrr"], errors="coerce")

    df.to_csv("ipl_team_stats.csv", index=False)
    print(f"\n✅ Saved {len(df)} rows → ipl_team_stats.csv")
    print(df.head(10).to_string())

if __name__ == "__main__":
    asyncio.run(main())