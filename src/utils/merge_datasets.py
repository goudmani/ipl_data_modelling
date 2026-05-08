"""
Merge ipl_player_stats.csv + ipl_auction_data.csv
Join keys: 'player' + 'year'  (season-level analysis)
       or: 'player'           (career-level analysis)

Run this AFTER both scrapers have finished.
"""

import pandas as pd

# ── Load ──────────────────────────────────────────────────────────────────────
stats   = pd.read_csv("ipl_player_stats.csv")
auction = pd.read_csv("ipl_auction_data.csv")

print("=== Player Stats sample ===")
print(stats.dtypes)
print(stats.head(3).to_string())

print("\n=== Auction Data sample ===")
print(auction.dtypes)
print(auction.head(3).to_string())

# ── Normalise join keys (already done in scrapers, but be safe) ───────────────
stats["player"]   = stats["player"].str.strip().str.title()
stats["team"]     = stats["team"].str.strip().str.upper()
auction["player"] = auction["player"].str.strip().str.title()
auction["team"]   = auction["team"].str.strip().str.upper()

# ── Join 1: Season-level — one row per player per year ───────────────────────
# auction is already one row per player per year
season_merged = stats.merge(
    auction[["year", "player", "team", "sold_price_cr",
             "base_price_cr", "player_type", "nationality"]],
    on=["year", "player"],          # join on season + name
    how="left",
    suffixes=("", "_auction"),
)
# prefer team from stats (more consistent), drop auction duplicate
season_merged.drop(columns=["team_auction"], inplace=True, errors="ignore")

season_merged.to_csv("ipl_merged_by_season.csv", index=False)
print(f"\n✅ Season-level merge: {len(season_merged)} rows → ipl_merged_by_season.csv")

# ── Join 2: Career-level — aggregate per player across all seasons ────────────
batting_career = (
    stats.groupby("player")
    .agg(
        teams          = ("team",   lambda x: ", ".join(x.dropna().unique())),
        seasons_played = ("year",   "nunique"),
        total_runs     = ("runs",   "sum"),
        avg_sr_bat     = ("sr",     "mean"),
        total_50s      = ("50s",    "sum"),
        total_100s     = ("100s",   "sum"),
        total_4s       = ("4s",     "sum"),
        total_6s       = ("6s",     "sum"),
        total_wkts     = ("wkts",   "sum"),
        avg_econ       = ("econ",   "mean"),
        avg_sr_bowl    = ("sr_bowl","mean"),
    )
    .reset_index()
)

auction_career = (
    auction.groupby("player")
    .agg(
        total_earned_cr    = ("sold_price_cr", "sum"),
        avg_sold_price_cr  = ("sold_price_cr", "mean"),
        auctions_sold_in   = ("year",          "count"),
        player_type        = ("player_type",   "first"),
        nationality        = ("nationality",   "first"),
    )
    .reset_index()
)

career_merged = batting_career.merge(auction_career, on="player", how="outer")
career_merged.to_csv("ipl_merged_career.csv", index=False)
print(f"✅ Career-level merge:  {len(career_merged)} rows → ipl_merged_career.csv")

# ── Quick analysis ─────────────────────────────────────────────────────────────
print("\n=== Top 10 earners vs. their total runs ===")
top = (
    career_merged
    .sort_values("total_earned_cr", ascending=False)
    .head(10)
    [["player", "teams", "total_runs", "total_wkts",
      "avg_econ", "total_earned_cr", "auctions_sold_in"]]
)
print(top.to_string(index=False))

print("\n=== Correlation matrix: performance vs. auction price ===")
corr_cols = ["total_runs", "total_wkts", "avg_econ",
             "total_50s", "total_100s", "total_earned_cr"]
avail = [c for c in corr_cols if c in career_merged.columns]
print(career_merged[avail].corr().round(3).to_string())
