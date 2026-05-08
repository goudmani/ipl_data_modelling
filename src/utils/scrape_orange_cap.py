"""
Dataset: IPL Orange Cap Stats (Batters) across all years
URL: https://www.iplt20.com/stats/
"""

import asyncio
import os
import pandas as pd
from playwright.async_api import async_playwright

BASE_URL = "https://www.iplt20.com/stats/"

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
    """
    Finds the custom dropdown for the Season and extracts all available years.
    """
    print("Waiting for Angular elements to load...")
    
    # Dismiss cookie banner
    try:
        cookie_btn = page.locator('.cookie__accept_btn')
        if await cookie_btn.is_visible(timeout=4000):
            await cookie_btn.click()
            print("  ✓ Closed cookie banner.")
    except Exception:
        pass

    try:
        await page.wait_for_selector('.cSBDisplay', state='visible', timeout=15000)
    except Exception:
        print("  ✗ Timeout waiting for '.cSBDisplay'. Page might not be loading fully.")
        return [], None

    # STRONGER TARGETING: We only want the dropdown that has the ".seasonFilterItems" class inside it.
    dropdown_container = page.locator('.customSelecBox:has(.seasonFilterItems)').first
    dropdown_display = dropdown_container.locator('.cSBDisplay').first

    # Click to open the dropdown
    await dropdown_display.click()
    await page.wait_for_timeout(1000)

    # Extract all the season text options (e.g. "SEASON 2026")
    options = dropdown_container.locator('.seasonFilterItems')
    count = await options.count()
    
    season_values = []
    for i in range(count):
        text = await options.nth(i).inner_text()
        text = text.strip()
        if "SEASON" in text.upper():
            season_values.append(text)

    # Close the dropdown
    await dropdown_display.click()
    
    return season_values, dropdown_container


async def scrape_season(page, season_text, dropdown_container):
    """
    Selects a season, ensures Orange Cap is active, and parses the table.
    """
    print(f"Scraping data for {season_text}...")
    
    # 1. Select the season
    await dropdown_container.locator('.cSBDisplay').first.click()
    await page.wait_for_timeout(500)
    
    # We force the click in case another element obscures it
    await dropdown_container.locator(f'.seasonFilterItems:has-text("{season_text}")').first.click(force=True)

    await page.wait_for_timeout(2000)

    # 2. Make sure "Orange Cap" is selected.
    # Using JS evaluation is much faster and bypasses "Element not visible" errors.
    try:
        await page.evaluate("""() => {
            const btn = document.querySelector('a.toprunsscorers');
            if (btn && !btn.classList.contains('active')) {
                btn.click();
            }
        }""")
        await page.wait_for_timeout(1500)
    except Exception as e:
        print(f"  ⚠ Could not click Orange Cap tab: {e}")

    # 3. Expand the "View All" button if it exists so we get all players, not just the top 20
    try:
        # Evaluate JS to click the View All button directly to avoid visibility issues
        await page.evaluate("""() => {
            const viewAll = document.querySelector('.np-mostrunsTab__btn.view-all a');
            if (viewAll && viewAll.offsetParent !== null) {
                viewAll.click();
            }
        }""")
        await page.wait_for_timeout(2000)
    except Exception:
        pass 

    # 4. Parse the table
    try:
        # Wait for the first row to be visible in the batting tab
        await page.wait_for_selector('#battingTAB tbody tr:not(.st-table__head)', state='visible', timeout=10000)
    except Exception:
        print(f"  ✗ No table data found for {season_text}")
        return []

    rows = page.locator('#battingTAB tbody tr:not(.st-table__head)')
    row_count = await rows.count()
    
    records = []
    
    for i in range(row_count):
        row = rows.nth(i)
        tds = row.locator('td')
        
        try:
            # POS, Player, Runs, Mat, Inns, NO, HS, Avg, BF, SR, 100, 50, 4s, 6s
            
            # The player cell is tds[1]. It contains name and team.
            player_cell = tds.nth(1)
            player_name = await player_cell.locator('.st-ply-name').inner_text(timeout=2000)
            team_name = await player_cell.locator('.st-ply-tm-name').inner_text(timeout=2000)
            
            runs = await tds.nth(2).inner_text()
            matches = await tds.nth(3).inner_text()
            inns = await tds.nth(4).inner_text()
            no_outs = await tds.nth(5).inner_text()
            hs = await tds.nth(6).inner_text()
            avg = await tds.nth(7).inner_text()
            bf = await tds.nth(8).inner_text()
            sr = await tds.nth(9).inner_text()

            # Clean HS (remove the * indicating not out)
            hs = hs.replace('*', '').strip()

            records.append({
                'year': season_text.replace("SEASON", "").strip(),
                'player': player_name.strip(),
                'team': team_name.strip(),
                'runs': runs.strip(),
                'matches': matches.strip(),
                'inns': inns.strip(),
                'not_outs': no_outs.strip(),
                'highest_score': hs,
                'average': avg.strip(),
                'balls_faced': bf.strip(),
                'strike_rate': sr.strip()
            })
        except Exception:
            # Reached end of table or malformed row
            continue
        
    print(f"  ✓ Extracted {len(records)} player records.")
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
            print("✗ Could not find season dropdown — inspect the page in DevTools.")
            await browser.close()
            return

        print(f"✓ Found {len(season_values)} seasons.")

        for season in season_values:
            records = await scrape_season(page, season, dropdown_sel)
            all_records.extend(records)
            await asyncio.sleep(1.5)

        await browser.close()

    if not all_records:
        print("No data scraped.")
        return

    df = pd.DataFrame(all_records)
    
    # Convert numeric columns
    numeric_cols = ["runs", "matches", "inns", "not_outs", "highest_score", "balls_faced"]
    float_cols = ["average", "strike_rate"]
    
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        
    for col in float_cols:
        # Handle cases where Average is '-'
        df[col] = pd.to_numeric(df[col].astype(str).str.replace('-', '0'), errors="coerce")

    output_dir = "data/raw"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "ipl_orange_cap.csv")
    df.to_csv(output_path, index=False)
    print(f"\n✅ Successfully saved {len(df)} rows to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())