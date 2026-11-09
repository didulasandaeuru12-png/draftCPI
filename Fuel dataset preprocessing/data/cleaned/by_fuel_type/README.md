# Cleaned datasets by fuel type

Each CSV contains one fuel from ../fuel_prices_final_cleaned.csv, with every original column and value retained. Dates are sorted; source identifiers, source links, units and quality flags are preserved.

Blank prices remain blank. Check price_status before using observations as forecasting targets. These are irregular revision records, not monthly training series.

| File | Records | Valid prices |
| --- | ---: | ---: |
| petrol_92_cleaned.csv | 185 | 185 |
| petrol_95_cleaned.csv | 185 | 185 |
| auto_diesel_cleaned.csv | 185 | 185 |
| super_diesel_cleaned.csv | 185 | 185 |
| kerosene_cleaned.csv | 185 | 185 |
| industrial_kerosene_cleaned.csv | 185 | 185 |
| furnace_oil_800_cleaned.csv | 185 | 184 |
| furnace_oil_1500_high_cleaned.csv | 185 | 97 |
| furnace_oil_1500_low_cleaned.csv | 185 | 185 |

Regenerate with python split_fuel_datasets.py from the package folder. All nine saved CSVs were read back and verified against the final dataset with no lost or duplicated records.
