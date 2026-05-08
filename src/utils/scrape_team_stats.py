"""
Dataset 1: IPL Team Stats (Wins, Losses, NRR) across all years
URL: https://www.iplt20.com/matches/points-table
"""

import asyncio
import os
import pandas as pd
from playwright.async_api import async_playwright

BASE_URL = "https://www.iplt20.com/matches/points-table"

async def browser_context(playwright):
    browser = await playwright.chromium.launch(
        headless=False,
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
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
    )
    return browser, ctx

async def get_season_options(page):
    print("Waiting for Angular elements to load...")
    try:
        cookie_btn = page.locator('.cookie__accept_btn')
        if await cookie_btn.is_visible(timeout=4000):
            await cookie_btn.click()
    except Exception:
        pass

    try:
        await page.wait_for_selector('.cSBDisplay', state='visible', timeout=15000)
    except Exception:
        print("  ✗ Timeout waiting for dropdown. Page might not be loading fully.")
        return [], None

    dropdown_container = page.locator('.customSelecBox').filter(has_text="SEASON")
    dropdown_display = dropdown_container.locator('.cSBDisplay')
    
    await dropdown_display.click()
    await page.wait_for_timeout(1000)

    options = dropdown_container.locator('.cSBListItems')
    count = await options.count()
    
    season_values = []
    for i in range(count):
        text = await options.nth(i).inner_text()
        if "SEASON" in text.upper():
            season_values.append(text.strip())

    await dropdown_display.click()
    return season_values, dropdown_container

async def scrape_season(page, season_text, dropdown_container):
    print(f"Scraping data for {season_text}...")
    
    await dropdown_container.locator('.cSBDisplay').click()
    await page.wait_for_timeout(500)
    await dropdown_container.locator(f'.cSBListItems:has-text("{season_text}")').click()

    await page.wait_for_timeout(2000)
    
    try:
        await page.wait_for_selector('tbody#pointsdata tr.team0', state='visible', timeout=10000)
    except Exception:
        print(f"  ✗ No table data found for {season_text}")
        return []

    rows = page.locator('tbody#pointsdata tr.team0')
    row_count = await rows.count()

    records = []
    for i in range(row_count):
        row = rows.nth(i)
        
        # 1. Safest way to get Team Name: Extract from the logo image URL!
        team_name = ""
        img_locator = row.locator("img[src*='teamlogos']").first
        if await img_locator.is_visible():
            src = await img_locator.get_attribute("src")
            # Example src: "https://.../teamlogos/SRH.png?v=2"
            team_name = src.split("/")[-1].split(".")[0].strip().upper()
        
        if not team_name:
            continue
            
        # 2. Extract all texts from the row's columns
        tds = row.locator('td')
        col_count = await tds.count()
        
        nums = []
        for j in range(col_count):
            text = await tds.nth(j).inner_text()
            try:
                # We only keep strictly numeric values (e.g. 14, 10, -0.316)
                # This ignores fractional strings like '2332/217.1' (runs for/against)
                nums.append(float(text.strip()))
            except ValueError:
                pass
                
        # The numbers array will cleanly map to: [Position, Matches, Won, Lost, Tied/NR, NRR, Points]
        if len(nums) >= 7:
            records.append({
                'year': season_text.replace("SEASON", "").strip(),
                'team': team_name,
                'matches': int(nums[1]),
                'won': int(nums[2]),
                'lost': int(nums[3]),
                'no_result': int(nums[4]),
                'nrr': nums[5],
                'points': int(nums[-1])  # Points is always the last numeric column
            })
            
    return records

async def main():
    all_records = []
    async with async_playwright() as pw:
        browser, ctx = await browser_context(pw)
        page = await ctx.new_page()

        print(f"Loading {BASE_URL} ...")
        await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        season_values, dropdown_sel = await get_season_options(page)
        if not season_values:
            print("✗ Could not find season dropdown.")
            await browser.close()
            return

        for season in season_values:
            records = await scrape_season(page, season, dropdown_sel)
            all_records.extend(records)
            await asyncio.sleep(1.5)

        await browser.close()

    if not all_records:
        print("No data scraped.")
        return

    df = pd.DataFrame(all_records)
    
    output_dir = "data/raw"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "ipl_team_stats.csv")
    df.to_csv(output_path, index=False)
    print(f"\n✅ Successfully saved {len(df)} rows to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())