"""Build one auditable nine-product table from the existing cleaned fuel records."""
from pathlib import Path
import hashlib
import json
import pandas as pd

BASE = Path(__file__).resolve().parent
PRODUCTS = {
    'lp_92': 'Petrol 92', 'lp_95': 'Petrol 95', 'lad': 'Auto Diesel',
    'lsd': 'Super Diesel', 'lk': 'Kerosene', 'lik': 'Industrial Kerosene',
    'fur_800': 'Furnace Oil 800', 'fur_1500_high': 'Furnace Oil 1500 High',
    'fur_1500_low': 'Furnace Oil 1500 Low',
}
SUPPLIED_NAMES = {'Petrol 92 octane': 'lp_92', 'Petrol 95 octane': 'lp_95',
                  'Auto diesel': 'lad', 'Super diesel': 'lsd', 'Kerosene': 'lk'}


def build():
    source = BASE / 'data/cleaned/fuel_prices_cleaned.csv'
    supplied_path = BASE / 'data/raw/fuel-prices-2026-10-15.csv'
    wide = pd.read_csv(source)
    supplied = pd.read_csv(supplied_path)
    assert wide.source_record_id.is_unique
    metadata = ['date', 'source_record_id', 'source_date_label', 'effective_time_local',
                'source_url', 'source_api_url', 'retrieved_on']
    final = wide.melt(id_vars=metadata, value_vars=list(PRODUCTS),
                      var_name='fuel_code', value_name='price_lkr')
    final['fuel_type'] = final.fuel_code.map(PRODUCTS)
    final['currency'] = 'LKR'
    final['geography'] = 'LK'
    final['measurement_unit'] = 'unverified'
    final['price_status'] = final.price_lkr.map(lambda x: 'not_reported' if pd.isna(x) else 'observed')
    issues = pd.read_csv(BASE / 'reports/cleaning_issues.csv')
    for issue in issues.itertuples(index=False):
        mask = final.source_record_id.eq(issue.source_record_id) & final.fuel_code.eq(issue.field)
        final.loc[mask, 'price_status'] = 'invalid_source_value'
    final['supplement_source_file'] = ''
    final['supplement_source'] = ''
    final['supplement_status'] = ''
    audits = []
    for row in supplied.itertuples(index=False):
        code = SUPPLIED_NAMES[row.indicator]
        mask = final.date.eq(row.date) & final.fuel_code.eq(code) & final.price_lkr.sub(row.value).abs().lt(1e-8)
        assert row.unit == 'Rs per litre' and row.geography == 'LK'
        audits.append({'date': row.date, 'fuel_code': code, 'value': row.value,
                       'matching_records': int(mask.sum()), 'status': 'matched' if mask.any() else 'unmatched'})
        final.loc[mask, 'measurement_unit'] = 'litre'
        final.loc[mask, 'supplement_source_file'] = supplied_path.name
        final.loc[mask, 'supplement_source'] = row.source
        final.loc[mask, 'supplement_status'] = row.status
    audit = pd.DataFrame(audits)
    assert audit.status.eq('matched').all(), 'Supplied observations require review before final export'
    final = final[['date', 'fuel_type', 'fuel_code', 'price_lkr', 'currency', 'measurement_unit',
                   'geography', 'price_status', *metadata[1:], 'supplement_source_file',
                   'supplement_source', 'supplement_status']].sort_values(
                       ['date', 'fuel_type', 'source_record_id']).reset_index(drop=True)
    assert len(final) == len(wide) * 9
    assert not final.duplicated(['source_record_id', 'fuel_code']).any()
    assert final.fuel_type.nunique() == 9
    assert pd.to_datetime(final.date, format='%Y-%m-%d', errors='raise').notna().all()
    assert final.price_lkr.dropna().gt(0).all()
    # Round-trip each source field to prove no observation was lost or changed.
    rebuilt = final.pivot(index='source_record_id', columns='fuel_code', values='price_lkr')
    for field in PRODUCTS:
        pd.testing.assert_series_equal(rebuilt[field].sort_index(),
            wide.set_index('source_record_id')[field].sort_index(), check_names=False)
    destination = BASE / 'data/cleaned/fuel_prices_final_cleaned.csv'
    final.to_csv(destination, index=False, encoding='utf-8-sig')
    audit.to_csv(BASE / 'reports/final_source_reconciliation.csv', index=False)
    counts = final.groupby('fuel_type').agg(records=('fuel_code', 'size'),
        observed_prices=('price_lkr', 'count'), first_date=('date', 'min'), last_date=('date', 'max'))
    counts['missing_prices'] = counts.records - counts.observed_prices
    counts.to_csv(BASE / 'reports/final_dataset_summary.csv')
    summary = {'rows': len(final), 'fuel_types': 9, 'observed_prices': int(final.price_lkr.notna().sum()),
               'missing_prices': int(final.price_lkr.isna().sum()),
               'price_status_counts': final.price_status.value_counts().to_dict(),
               'supplied_observations_matched': len(audit),
               'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [source, supplied_path]}}
    (BASE / 'reports/final_dataset_validation.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    checks = {
        'nine_fuel_types': final.fuel_type.nunique() == 9,
        'one_row_per_source_record_and_fuel': not final.duplicated(['source_record_id', 'fuel_code']).any(),
        'all_source_record_fuel_pairs_preserved': len(final) == len(wide) * len(PRODUCTS),
        'all_supplied_observations_matched': audit.status.eq('matched').all(),
        'all_observed_prices_positive': final.price_lkr.dropna().gt(0).all(),
        'all_dates_valid': pd.to_datetime(final.date, errors='raise').notna().all(),
        'missing_prices_have_explicit_status': final.loc[final.price_lkr.isna(), 'price_status'].isin(
            ['not_reported', 'invalid_source_value']).all(),
        'source_price_round_trip_preserved': True,
    }
    pd.DataFrame([{'check': name, 'passed': bool(result)} for name, result in checks.items()]).to_csv(
        BASE / 'reports/final_dataset_checks.csv', index=False)
    assert all(checks.values())
    (BASE / 'reports/data_quality_report.md').write_text(f'''# Fuel data quality and final dataset

## Scope and outputs
The final dataset covers all nine grades: Petrol 92, Petrol 95, Auto Diesel, Super Diesel, Kerosene, Industrial Kerosene, Furnace Oil 800, Furnace Oil 1500 High and Furnace Oil 1500 Low.

`data/cleaned/fuel_prices_final_cleaned.csv` is the consolidated long-format dataset. `data/cleaned/by_fuel_type/` contains one CSV per fuel, each with all source metadata, price status and measurement-unit evidence retained. The original 185-row wide files remain compatible intermediate exports; they are identical copies, not separate training evidence. `fuel_forecasting_inputs_long.csv` remains a three-fuel subset and is not the final nine-fuel table.

## Counts and coverage
- CPC revision records: {len(wide)}; nine-fuel rows: {len(final)}.
- Coverage: {final.date.min()} to {final.date.max()}.
- Valid observed prices: {summary['observed_prices']}; blank prices: {summary['missing_prices']}.
- Missing-price status: {summary['price_status_counts']}.
- Each fuel retains 185 source revision slots. See final_dataset_summary.csv for observed and missing counts by fuel.
- Furnace Oil 1500 High has 88 unreported prices. Furnace Oil 800 has one invalid source value, `53.9.00` on 6 December 2008, withheld from numeric analysis.

## Source reconciliation and duplicate policy
The initial intermediate pipeline reconciles 299 Auto Diesel, Super Diesel and Kerosene observations. The final consolidation additionally checks both supplied petrol grades: all {len(audit)} supplied observations match existing CPC prices. See final_source_reconciliation.csv. Agreement is reconciliation, not independent validation: both sources share CPC provenance.

Exact matching supplied observations add source and unit evidence; they never add duplicate price rows. No source price is overwritten. Every valid wide-table price is preserved exactly in the final table. The key is (source_record_id, fuel_code), not date alone. Multiple same-day source records remain intact; no within-day ordering is inferred beyond recorded annotations. The newer CPC endpoint is preserved.

## Units and missingness
Currency is LKR. measurement_unit is litre only on exact matches supported by the supplied CSV; other observations remain unverified. Product-grade continuity and other historical units require original-source review. Blank prices are never zero and are never filled. price_status distinguishes observed, not_reported and invalid_source_value. Missing-price rows retain provenance for audit but must not be used as numeric model targets.

## Verification
The intermediate checks are recorded in validation_checks.csv. Final dataset checks are in final_dataset_checks.csv; all {len(checks)} pass. The final table is pivoted back and compared exactly against every original price column. Source hashes are in final_dataset_validation.json. The split stage reads back all nine files, verifies each against its source subset, and checks that recombining them exactly reproduces the final table. Per-file counts and hashes are in per_fuel_dataset_manifest.csv; split verification is in per_fuel_dataset_validation.json.

## Forecasting limits
These are irregular revision records, not daily or monthly observations. No imputation, interpolation, scaling, feature engineering, outlier removal or model training is performed. Calendar gaps do not establish unchanged prices. Resolve same-day records, verify coverage and choose a documented aggregation rule before monthly forecasting. All inputs are local snapshots; this run does not refresh live data.

## Reproduce
Run the notebook top to bottom, or run these scripts in order from the package directory:

1. python fuel_preprocessing.py
2. python build_final_dataset.py
3. python split_fuel_datasets.py

Step 1 writes intermediate reports; step 2 updates this report for the final nine-fuel scope; step 3 writes the split-file validation evidence. Original pre-update files are preserved in ../output/fuel_package_before_update_2026-11-09/.
''', encoding='utf-8')
    destination.with_suffix('.md').write_text('''# Final cleaned fuel dataset

One row per original CPC revision record and fuel type, covering all nine fuel grades. The key is (source_record_id, fuel_code); dates alone are not unique. This file reshapes the existing cleaned fuel table rather than concatenating duplicate copies of the same evidence. Every valid source price is preserved exactly.

Columns include readable fuel names, original product codes, numeric prices in LKR, source dates and identifiers, source links, extraction date and exact-match references to the supplied CSV. All five supplied series, including both petrol grades, are reconciled here. They share CPC provenance and are not independent observations.

Missing prices remain blank: price_status distinguishes not_reported from invalid_source_value. The malformed furnace-oil value is withheld, never guessed. Rows without a usable price should be excluded from model targets, not treated as zeros. Same-day source records remain separate and require review before aggregation.

measurement_unit is litre only where the supplied CSV explicitly supports an exact matched observation; other records remain unverified. No forward filling, monthly aggregation, feature engineering or training is performed. Run python build_final_dataset.py to regenerate. Supporting reports: final_dataset_summary.csv, final_source_reconciliation.csv and final_dataset_validation.json.
''', encoding='utf-8')
    return summary


if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
