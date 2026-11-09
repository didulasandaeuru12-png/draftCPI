from pathlib import Path
import hashlib
import json
import re
import pandas as pd

PRODUCTS = {'lp_92': 'Petrol 92 octane', 'lp_95': 'Petrol 95 octane',
            'lad': 'Auto diesel', 'lsd': 'Super diesel', 'lk': 'Kerosene',
            'lik': 'Industrial kerosene', 'fur_800': 'Furnace oil 800',
            'fur_1500_high': 'Furnace oil 1500 High', 'fur_1500_low': 'Furnace oil 1500 Low'}
ADDITIONS = {'Auto diesel': 'lad', 'Super diesel': 'lsd', 'Kerosene': 'lk'}
TARGETS = ['Petrol 92 octane', 'Auto diesel', 'Kerosene']

def run(base=None):
    base = Path(base) if base else Path(__file__).resolve().parent
    root = base.parent
    raw_dir, clean_dir, reports = base / 'data/raw', base / 'data/cleaned', base / 'reports'
    original = root / 'output/fuel_package_before_update_2026-11-09/ceypetco_historical_prices_all.csv'
    # First run derives the fuel-only source snapshot from the preserved original.
    if not (raw_dir / 'ceypetco_historical_prices_all.csv').exists():
        raise FileNotFoundError('Fuel source snapshot missing')
    cpc = pd.read_csv(raw_dir / 'ceypetco_historical_prices_all.csv', dtype=str, keep_default_na=False)
    cpc = cpc.loc[cpc['category'].eq('fuel')].copy()
    cpc = cpc[[c for c in cpc if not c.startswith('bitumen_')]]
    cpc.to_csv(raw_dir / 'ceypetco_historical_prices_all.csv', index=False, encoding='utf-8-sig')
    cpc.to_csv(root / 'ceypetco_historical_prices_all.csv', index=False, encoding='utf-8-sig')
    cpc.loc[pd.to_numeric(cpc.year).between(2021, 2025)].to_csv(
        root / 'ceypetco_historical_prices_2021_2025.csv', index=False, encoding='utf-8-sig')

    new_path = raw_dir / 'fuel-prices-2026-10-15.csv'
    incoming = pd.read_csv(new_path)
    incoming['date'] = pd.to_datetime(incoming.date, format='%Y-%m-%d', errors='raise').dt.strftime('%Y-%m-%d')
    incoming['value'] = pd.to_numeric(incoming.value, errors='raise')
    selected = incoming.loc[incoming.indicator.isin(ADDITIONS)].copy()
    assert selected.unit.eq('Rs per litre').all() and selected.geography.eq('LK').all()
    assert selected.value.gt(0).all() and not selected.duplicated(['date', 'indicator']).any()

    clean = cpc.replace('', pd.NA).copy()
    clean['date'] = pd.to_datetime(clean.date, format='%Y-%m-%d', errors='raise').dt.strftime('%Y-%m-%d')
    clean['year'] = pd.to_numeric(clean.year).astype('Int64')
    clean['date_precision'] = 'day'
    clean['effective_time_local'] = clean.source_date_label.str.extract(r'(\d{1,2}[:.]\d{2})\s*[Pp][Mm]', expand=False).map(
        lambda value: f'{int(re.split("[:.]", value)[0]) % 12 + 12:02d}:{re.split("[:.]", value)[1]}' if pd.notna(value) else pd.NA)
    issues = []
    for field in PRODUCTS:
        numeric = pd.to_numeric(clean[field], errors='coerce')
        bad = clean[field].notna() & numeric.isna()
        for i in clean.index[bad]:
            issues.append({'source_record_id': clean.at[i, 'source_record_id'], 'date': clean.at[i, 'date'],
                           'field': field, 'raw_value': clean.at[i, field], 'issue': 'invalid_numeric',
                           'action': 'numeric value withheld; original retained in raw snapshot'})
        clean[field] = numeric
    clean['cleaning_flags'] = clean.source_record_id.map(
        {item['source_record_id']: 'invalid_numeric' for item in issues}).fillna('')
    clean['has_cleaning_issue'] = clean.cleaning_flags.ne('')
    clean['supplement_source_file'] = ''
    clean['supplement_verified_fields'] = ''
    reconciliation = []
    additions = []
    for row in selected.itertuples(index=False):
        field = ADDITIONS[row.indicator]
        same_date = clean.date.eq(row.date)
        match = same_date & clean[field].sub(row.value).abs().lt(1e-8)
        if match.any():
            status = 'matched_existing'
            ids = '|'.join(clean.loc[match, 'source_record_id'])
            for i in clean.index[match]:
                clean.at[i, 'supplement_source_file'] = new_path.name
                old = clean.at[i, 'supplement_verified_fields']
                clean.at[i, 'supplement_verified_fields'] = '|'.join(filter(None, [old, field]))
        elif same_date.any():
            status, ids = 'conflict_retained_for_review', ''
        else:
            status, ids = 'added_new_date', ''
            additions.append(row._asdict())
        reconciliation.append({'date': row.date, 'indicator': row.indicator, 'value': row.value,
                               'unit': row.unit, 'status': status, 'matching_source_record_ids': ids,
                               'source_file': new_path.name, 'source': row.source})

    # New-date observations are appended only for the supplied products; no other prices are filled.
    for date in sorted({r['date'] for r in additions}):
        records = [r for r in additions if r['date'] == date]
        extra = {'date': date, 'year': int(date[:4]), 'category': 'fuel', 'date_precision': 'day',
                 'source_date_label': date, 'source_record_id': 'supplement-' + date,
                 'source_url': 'https://research.dulajmendis.com/data/fuel-prices/',
                 'supplement_source_file': new_path.name,
                 'supplement_verified_fields': '|'.join(ADDITIONS[r['indicator']] for r in records),
                 'cleaning_flags': '', 'has_cleaning_issue': False}
        extra.update({ADDITIONS[r['indicator']]: r['value'] for r in records})
        clean = pd.concat([clean, pd.DataFrame([extra])], ignore_index=True)
    clean = clean.sort_values(['date', 'source_record_id']).reset_index(drop=True)
    for name in ['fuel_prices_cleaned.csv', 'ceypetco_all_cleaned.csv']:
        clean.to_csv(clean_dir / name, index=False, encoding='utf-8-sig')

    metadata = ['date', 'source_record_id', 'source_date_label', 'effective_time_local', 'source_url',
                'retrieved_on', 'supplement_source_file', 'supplement_verified_fields']
    long = clean.melt(id_vars=metadata, value_vars=list(PRODUCTS), var_name='product_code', value_name='price_lkr')
    long = long.loc[long.price_lkr.notna()].copy()
    long['product'] = long.product_code.map(PRODUCTS)
    long['unit'] = 'unverified in CPC export'
    for row in selected.itertuples(index=False):
        mask = long.date.eq(row.date) & long['product'].eq(row.indicator) & long.price_lkr.sub(row.value).abs().lt(1e-8)
        long.loc[mask, 'unit'] = 'LKR/litre (supplied CSV)'
    target = long.loc[long['product'].isin(TARGETS)].sort_values(['product', 'date', 'source_record_id'])
    target.to_csv(clean_dir / 'fuel_forecasting_inputs_long.csv', index=False, encoding='utf-8-sig')
    selected.to_csv(clean_dir / 'diesel_kerosene_supplied.csv', index=False, encoding='utf-8-sig')
    recon = pd.DataFrame(reconciliation)
    recon.to_csv(reports / 'source_reconciliation.csv', index=False)
    pd.DataFrame(issues, columns=['source_record_id', 'date', 'field', 'raw_value', 'issue', 'action']).to_csv(reports / 'cleaning_issues.csv', index=False)
    pd.DataFrame([{'field': f, 'records': len(clean), 'missing': int(clean[f].isna().sum())} for f in PRODUCTS]).to_csv(reports / 'price_missingness.csv', index=False)
    clean.loc[clean.duplicated('date', keep=False)].to_csv(reports / 'same_date_candidates.csv', index=False)
    clean.groupby('year').size().rename('fuel_records').to_csv(reports / 'yearly_record_counts.csv')
    target.groupby('product').agg(observations=('price_lkr', 'size'), distinct_dates=('date', 'nunique'),
                                  first_date=('date', 'min'), last_date=('date', 'max')).to_csv(reports / 'target_series_summary.csv')
    checks = {'fuel_only': clean.category.eq('fuel').all(), 'unique_source_record_ids': clean.source_record_id.is_unique,
              'valid_dates': clean.date.notna().all(), 'positive_numeric_prices': long.price_lkr.gt(0).all(),
              'supplied_values_positive': selected.value.gt(0).all(), 'supplied_keys_unique': not selected.duplicated(['date', 'indicator']).any(),
              'all_supplied_rows_audited': len(recon) == len(selected),
              'no_unreviewed_conflicts': not recon.status.eq('conflict_retained_for_review').any(),
              'target_products_only': set(target['product']) == set(TARGETS),
              'original_cpc_records_preserved': set(cpc.source_record_id).issubset(set(clean.source_record_id))}
    pd.DataFrame([{'check': k, 'passed': bool(v)} for k, v in checks.items()]).to_csv(reports / 'validation_checks.csv', index=False)
    summary = {'cpc_fuel_records': len(cpc), 'cleaned_fuel_records': len(clean),
               'first_date': clean.date.min(), 'last_date': clean.date.max(), 'supplied_rows': len(incoming),
               'supplied_diesel_kerosene_rows': len(selected), 'reconciliation': recon.status.value_counts().to_dict(),
               'invalid_numeric_cells': len(issues), 'checks_passed': sum(bool(v) for v in checks.values()),
               'checks_total': len(checks), 'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in [raw_dir / 'ceypetco_historical_prices_all.csv', new_path]}}
    (reports / 'cleaning_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    dictionary = [{'column': c, 'meaning': PRODUCTS.get(c, c.replace('_', ' ')),
                   'missing_policy': 'unavailable; never assumed zero'} for c in clean.columns]
    pd.DataFrame(dictionary).to_csv(reports / 'data_dictionary.csv', index=False)
    report = f'''# Fuel data quality and source reconciliation

Scope: petrol, diesel, kerosene and other original CPC fuel grades. Forecasting input export selects Petrol 92, Auto Diesel and Kerosene.

## Results
- Original CPC fuel records: {len(cpc)}; cleaned fuel records: {len(clean)}.
- Coverage: {clean.date.min()} to {clean.date.max()}.
- Supplied diesel/kerosene observations: {len(selected)}. Outcomes: {recon.status.value_counts().to_dict()}.
- Invalid numeric cells withheld: {len(issues)}. Review cleaning_issues.csv; raw values are retained.
- Validation: {summary['checks_passed']}/{len(checks)} passed.

## Merge policy
The newer CPC archive remains authoritative for its observations. Matching supplied date/product/price values add provenance, not duplicate training rows. Different values on an existing date are logged for review and never silently overwrite CPC. New dates are appended with prices only for supplied products. The supplied file also contains petrol observations; these are preserved in the input file but not merged because this update requested diesel and kerosene.

The supplied compilation is sourced partly from the same CPC archive, so agreement is reconciliation rather than independent verification. Both same-day CPC entries remain intact; no final within-day order is inferred. The supplied units are Rs per litre; the CPC export itself did not specify product units. Units are marked confirmed by the supplied file only on exact matched observations. Historical grade continuity and units outside those observations still require source review.

## Limits for forecasting
Rows are irregular revision records, not daily observations. No imputation, interpolation, monthly resampling, scaling or outlier removal is applied. Gaps do not establish unchanged prices. Retained repeated dates need a documented resolution before monthly aggregation. This package is cleaned source evidence, not yet a model-ready monthly training table. The supplied file stops before the CPC archive endpoint; newer CPC observations remain included. All source files are local snapshots; no live refresh was performed.

## Reproduce
Run python fuel_preprocessing.py from this folder, or run all notebook cells. Original pre-update files are preserved in ../output/fuel_package_before_update_2026-11-09/. Reconciliation details are in source_reconciliation.csv.
'''
    (reports / 'data_quality_report.md').write_text(report, encoding='utf-8')
    assert all(checks.values()), 'Validation failure; inspect validation_checks.csv'
    return clean, selected, recon, target, summary

if __name__ == '__main__':
    print(json.dumps(run()[-1], indent=2))
