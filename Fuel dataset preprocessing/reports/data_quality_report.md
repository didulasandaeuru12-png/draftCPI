# Fuel data quality and final dataset

## Scope and outputs
The final dataset covers all nine grades: Petrol 92, Petrol 95, Auto Diesel, Super Diesel, Kerosene, Industrial Kerosene, Furnace Oil 800, Furnace Oil 1500 High and Furnace Oil 1500 Low.

`data/cleaned/fuel_prices_final_cleaned.csv` is the consolidated long-format dataset. `data/cleaned/by_fuel_type/` contains one CSV per fuel, each with all source metadata, price status and measurement-unit evidence retained. The original 185-row wide files remain compatible intermediate exports; they are identical copies, not separate training evidence. `fuel_forecasting_inputs_long.csv` remains a three-fuel subset and is not the final nine-fuel table.

## Counts and coverage
- CPC revision records: 185; nine-fuel rows: 1665.
- Coverage: 1990-03-01 to 2026-11-02.
- Valid observed prices: 1576; blank prices: 89.
- Missing-price status: {'observed': 1576, 'not_reported': 88, 'invalid_source_value': 1}.
- Each fuel retains 185 source revision slots. See final_dataset_summary.csv for observed and missing counts by fuel.
- Furnace Oil 1500 High has 88 unreported prices. Furnace Oil 800 has one invalid source value, `53.9.00` on 6 December 2008, withheld from numeric analysis.

## Source reconciliation and duplicate policy
The initial intermediate pipeline reconciles 299 Auto Diesel, Super Diesel and Kerosene observations. The final consolidation additionally checks both supplied petrol grades: all 513 supplied observations match existing CPC prices. See final_source_reconciliation.csv. Agreement is reconciliation, not independent validation: both sources share CPC provenance.

Exact matching supplied observations add source and unit evidence; they never add duplicate price rows. No source price is overwritten. Every valid wide-table price is preserved exactly in the final table. The key is (source_record_id, fuel_code), not date alone. Multiple same-day source records remain intact; no within-day ordering is inferred beyond recorded annotations. The newer CPC endpoint is preserved.

## Units and missingness
Currency is LKR. measurement_unit is litre only on exact matches supported by the supplied CSV; other observations remain unverified. Product-grade continuity and other historical units require original-source review. Blank prices are never zero and are never filled. price_status distinguishes observed, not_reported and invalid_source_value. Missing-price rows retain provenance for audit but must not be used as numeric model targets.

## Verification
The intermediate checks are recorded in validation_checks.csv. Final dataset checks are in final_dataset_checks.csv; all 8 pass. The final table is pivoted back and compared exactly against every original price column. Source hashes are in final_dataset_validation.json. The split stage reads back all nine files, verifies each against its source subset, and checks that recombining them exactly reproduces the final table. Per-file counts and hashes are in per_fuel_dataset_manifest.csv; split verification is in per_fuel_dataset_validation.json.

## Forecasting limits
These are irregular revision records, not daily or monthly observations. No imputation, interpolation, scaling, feature engineering, outlier removal or model training is performed. Calendar gaps do not establish unchanged prices. Resolve same-day records, verify coverage and choose a documented aggregation rule before monthly forecasting. All inputs are local snapshots; this run does not refresh live data.

## Reproduce
Run the notebook top to bottom, or run these scripts in order from the package directory:

1. python fuel_preprocessing.py
2. python build_final_dataset.py
3. python split_fuel_datasets.py

Step 1 writes intermediate reports; step 2 updates this report for the final nine-fuel scope; step 3 writes the split-file validation evidence. Original pre-update files are preserved in ../output/fuel_package_before_update_2026-11-09/.
