# IPL Data Modelling

A comprehensive data platform for Indian Premier League (IPL) analytics, combining historical player performance data, auction insights, and team statistics for exploratory analysis and predictive modelling.

## 📊 Overview

This project provides end-to-end data infrastructure for IPL analytics, including:
- Multi-year auction data (2022-2025) with player valuations
- Performance metrics (Orange Cap & Purple Cap winners)
- Team-level statistics across IPL seasons
- Exploratory data analysis notebooks
- Modular pipeline architecture for data processing and model deployment

## 🗂️ Project Structure

```
ipl_data_modelling/
│
├── data/
│   ├── raw/              # Source datasets (CSV files)
│   │   ├── IPL auction data (2022-2025)
│   │   ├── ipl_orange_cap.csv
│   │   ├── ipl_purple_cap.csv
│   │   └── ipl_team_stats.csv
│   ├── interim/          # Intermediate transformations
│   ├── processed/        # Final datasets ready for analysis
│   │   └── ipl_data.csv
│   └── external/         # Third-party/supplementary data
│
├── notebooks/            # Analysis & experimentation
│   ├── EDA_ipl_data      # General IPL data exploration
│   ├── EDA_orangecap     # Orange Cap (batting) analysis
│   ├── EDA_purple_cap    # Purple Cap (bowling) analysis
│   └── EDA_teamstats     # Team performance analysis
│
├── src/                  # Production source code
│   ├── ingestion/        # Data loading & validation
│   ├── processing/       # ETL transformations
│   ├── features/         # Feature engineering pipelines
│   ├── models/           # ML model training & evaluation
│   ├── serving/          # Model deployment & inference
│   └── utils/            # Shared utilities & helpers
│
├── pipelines/            # Workflow orchestration (DLT/Jobs)
├── models/               # Saved model artifacts & checkpoints
├── reports/              # Generated visualizations & reports
├── tests/                # Unit & integration tests
├── configs/              # Configuration files (YAML/JSON)
│
├── requirements.txt      # Python dependencies
├── .gitignore           # Git exclusions
└── README.md            # This file
```

## 📁 Datasets

### Raw Data Sources

**Auction Data:**
- `IPL_Auction_2022_FullList.csv` - Complete player pool for 2022 mega auction
- `IPL2022_Player_Auction_List.csv` - 2022 auction listings
- `IPL_2022_Sold_Players.csv` - Successfully sold players in 2022
- `IPL_2023_Auction_Pool.csv` - Available players for 2023
- `IPL_2023_Auction_Sold.csv` / `IPL_2023_Auction_Submitted.csv` - 2023 auction results
- `2024_auction.csv` - 2024 auction data
- `ipl_2025_auction_players.csv` - 2025 auction information

**Performance Data:**
- `ipl_orange_cap.csv` - Top run-scorers by season
- `ipl_purple_cap.csv` - Top wicket-takers by season
- `ipl_team_stats.csv` - Team-level statistics across seasons

**Processed Data:**
- `ipl_data.csv` - Consolidated and cleaned dataset for analysis

## 🚀 Getting Started

### Prerequisites

- Databricks workspace access
- Python 3.9+ (for local development)
- Unity Catalog enabled (recommended)

### Databricks Setup

This project is designed for Databricks and leverages serverless compute:

1. **Clone or import this repository** into your Databricks workspace:
   ```
   /Users/<your-email>/ipl_data_modelling/
   ```

2. **Data Access**: Upload CSV files to your workspace or mount external storage:
   ```python
   # Files are currently in: /Users/manikanthgoud98@gmail.com/ipl_data_modelling/data/raw/
   ```

3. **Run Notebooks**: Open any EDA notebook and attach to serverless compute (auto-selected)

4. **Supported Languages**: Python, SQL (R and Scala not supported on serverless)

### Local Development Setup

For local development and testing:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 📓 Notebooks

Explore the data through interactive notebooks:

1. **[EDA_ipl_data](#notebook-3390321571545723)** - Comprehensive overview of IPL data
2. **[EDA_orangecap](#notebook-2785793250192460)** - Analysis of top batsmen
3. **[EDA_purple_cap](#notebook-3160715471738992)** - Analysis of top bowlers
4. **[EDA_teamstats](#notebook-3166569729191270)** - Team performance trends

## 🔧 Development Workflow

1. **Data Ingestion**: Place raw CSV files in `data/raw/`
2. **Exploration**: Use notebooks in `notebooks/` for EDA
3. **Feature Engineering**: Develop features in `src/features/`
4. **Model Development**: Build models in `src/models/`
5. **Pipeline Creation**: Orchestrate workflows in `pipelines/`
6. **Testing**: Write tests in `tests/`

## 🎯 Use Cases

- **Player Performance Analysis**: Identify patterns in batting/bowling statistics
- **Auction Strategy**: Analyze player valuations and bidding trends
- **Team Analytics**: Compare team performance across seasons
- **Predictive Modelling**: Build models for match outcomes, player performance
- **Fantasy League Insights**: Data-driven player selection recommendations

## 📦 Key Technologies

- **Platform**: Databricks (Serverless Compute)
- **Languages**: Python, SQL
- **Data Format**: CSV (raw), Delta Lake (processed)
- **Notebooks**: Jupyter/Databricks notebooks
- **Orchestration**: Databricks Workflows / DLT Pipelines

## 🤝 Contributing

1. Create a new branch for features or analysis
2. Follow the project structure conventions
3. Document your analysis in notebooks
4. Add tests for production code in `src/`
5. Update this README if you add new datasets or major features

## 📝 Notes

- All data files use `.csv` format
- Notebooks support both Python and SQL
- Use `.gitkeep` files to preserve empty directory structure
- Keep raw data immutable; save transformations to `interim/` or `processed/`

## 📧 Contact

For questions or collaboration opportunities, reach out to: manikanthgoud98@gmail.com

---

**Last Updated**: May 2026  
**Project Status**: Active Development
