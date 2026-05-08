# IPL Data Modelling

A full-stack data platform for IPL (Indian Premier League) analytics and predictive modelling.

## Project Structure

```
├── data/
│   ├── raw/          # Original, immutable source data
│   ├── interim/      # Intermediate transformed data
│   ├── processed/    # Final datasets ready for modelling
│   └── external/     # Third-party / supplementary data
│
├── notebooks/
│   ├── 01_eda/       # Exploratory data analysis
│   ├── 02_features/  # Feature engineering experiments
│   ├── 03_modeling/  # Model development
│   └── 04_evaluation/# Model evaluation and reporting
│
├── src/
│   ├── ingestion/    # Data ingestion layer
│   ├── processing/   # Data transformation layer
│   ├── features/     # Feature engineering
│   ├── models/       # Model training and prediction
│   ├── serving/      # Model serving / inference
│   └── utils/        # Shared utilities
│
├── pipelines/        # Orchestration / pipeline definitions
├── models/           # Saved model artifacts
├── reports/figures/  # Generated charts and figures
├── tests/            # Unit and integration tests
└── configs/          # Configuration files
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```