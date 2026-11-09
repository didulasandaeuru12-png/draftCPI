# Fuel data preprocessing

This package cleans nine CPC fuel grades, reconciles all five series (including petrol) from `fuel-prices-2026-10-15.csv`, and exports both a final combined table and nine separate fuel datasets. Intermediate exports reconcile diesel and kerosene; the final stage additionally reconciles both petrol grades.

## Files
- `data/cleaned/by_fuel_type/`: nine individual fuel CSVs preserving all columns and missing-price flags from the final dataset. Regenerate with `python split_fuel_datasets.py`.
- `data/cleaned/fuel_prices_final_cleaned.csv`: final nine-fuel dataset with readable fuel names, one row per source revision and fuel type, price-status flags and source references. Run `python build_final_dataset.py` to regenerate; see the adjacent `.md` and `reports/final_dataset_summary.csv` for details.
- `data/raw/ceypetco_historical_prices_all.csv`: fuel-only CPC snapshot. The unchanged pre-update original is backed up outside this package.
- `data/raw/fuel-prices-2026-10-15.csv`: unchanged supplied CSV, including its original petrol series.
- `data/cleaned/fuel_prices_cleaned.csv`: fuel revision records with source metadata and reconciliation flags.
- `data/cleaned/ceypetco_all_cleaned.csv`: compatibility copy of the fuel-only cleaned table.
- `data/cleaned/diesel_kerosene_supplied.csv`: Auto Diesel, Super Diesel and Kerosene rows from the supplied CSV.
- `data/cleaned/fuel_forecasting_inputs_long.csv`: Petrol 92, Auto Diesel and Kerosene observations in long format; not resampled or imputed.
- `reports/source_reconciliation.csv`: every supplied diesel/kerosene observation and its matching outcome.
- `reports/final_source_reconciliation.csv`: all 513 supplied observations, including petrol, and their matches.
- `reports/final_dataset_summary.csv` and `final_dataset_checks.csv`: counts by fuel and final-table validation checks.
- `reports/per_fuel_dataset_manifest.csv` and `per_fuel_dataset_validation.json`: per-file counts, hashes and exact split/recombination checks.
- `reports/data_quality_report.md`: findings, merge policy, limitations and remaining forecasting work.
- `ceypetco_data_cleaning.ipynb` and `.html`: executed workflow and readable preview.

## Run
Install requirements, then execute all notebook cells, or run `python fuel_preprocessing.py`, `python build_final_dataset.py`, and `python split_fuel_datasets.py` in that order. All three stages are required to regenerate the final dataset, separate fuel files and current reports. The pipeline writes only its derived outputs and fuel-only CPC exports. The supplied source CSV is never changed. Previously saved mixed-category files, notebook and reports are backed up in `../output/fuel_package_before_update_2026-11-09/`.

Prices are irregular revisions. Missing values are not zero. Same-day records remain separate. Matching values add source evidence without duplicating training observations. No monthly resampling, imputation, model training or tax-formula estimates are introduced.
