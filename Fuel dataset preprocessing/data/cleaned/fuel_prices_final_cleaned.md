# Final cleaned fuel dataset

One row per original CPC revision record and fuel type, covering all nine fuel grades. The key is (source_record_id, fuel_code); dates alone are not unique. This file reshapes the existing cleaned fuel table rather than concatenating duplicate copies of the same evidence. Every valid source price is preserved exactly.

Columns include readable fuel names, original product codes, numeric prices in LKR, source dates and identifiers, source links, extraction date and exact-match references to the supplied CSV. All five supplied series, including both petrol grades, are reconciled here. They share CPC provenance and are not independent observations.

Missing prices remain blank: price_status distinguishes not_reported from invalid_source_value. The malformed furnace-oil value is withheld, never guessed. Rows without a usable price should be excluded from model targets, not treated as zeros. Same-day source records remain separate and require review before aggregation.

measurement_unit is litre only where the supplied CSV explicitly supports an exact matched observation; other records remain unverified. No forward filling, monthly aggregation, feature engineering or training is performed. Run python build_final_dataset.py to regenerate. Supporting reports: final_dataset_summary.csv, final_source_reconciliation.csv and final_dataset_validation.json.
