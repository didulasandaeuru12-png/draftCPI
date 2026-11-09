"""Split the final cleaned dataset without changing values or dropping missing prices."""
from pathlib import Path
import hashlib
import json
import pandas as pd

BASE = Path(__file__).resolve().parent
FILES = {
    'Petrol 92': 'petrol_92_cleaned.csv',
    'Petrol 95': 'petrol_95_cleaned.csv',
    'Auto Diesel': 'auto_diesel_cleaned.csv',
    'Super Diesel': 'super_diesel_cleaned.csv',
    'Kerosene': 'kerosene_cleaned.csv',
    'Industrial Kerosene': 'industrial_kerosene_cleaned.csv',
    'Furnace Oil 800': 'furnace_oil_800_cleaned.csv',
    'Furnace Oil 1500 High': 'furnace_oil_1500_high_cleaned.csv',
    'Furnace Oil 1500 Low': 'furnace_oil_1500_low_cleaned.csv',
}


def split():
    source = BASE / 'data/cleaned/fuel_prices_final_cleaned.csv'
    destination = source.parent / 'by_fuel_type'
    # Preserve literal strings and blanks, including provenance and quality flags.
    data = pd.read_csv(source, dtype=str, keep_default_na=False)
    assert set(data.fuel_type) == set(FILES), 'Unexpected fuel types in final dataset'
    assert not data.duplicated(['source_record_id', 'fuel_code']).any()
    destination.mkdir(exist_ok=True)
    reloaded = []
    summary = []
    for fuel, filename in FILES.items():
        subset = data.loc[data.fuel_type.eq(fuel)].sort_values(
            ['date', 'source_record_id']).reset_index(drop=True)
        path = destination / filename
        subset.to_csv(path, index=False, encoding='utf-8-sig')
        saved = pd.read_csv(path, dtype=str, keep_default_na=False)
        pd.testing.assert_frame_equal(subset, saved)
        reloaded.append(saved)
        summary.append((filename, len(saved), int(saved.price_lkr.ne('').sum())))
    key = ['source_record_id', 'fuel_code']
    combined = pd.concat(reloaded, ignore_index=True).sort_values(key).reset_index(drop=True)
    pd.testing.assert_frame_equal(data.sort_values(key).reset_index(drop=True), combined)
    manifest = pd.DataFrame([
        {'fuel_type': fuel, 'filename': filename, 'records': len(part),
         'observed_prices': int(part.price_lkr.ne('').sum()),
         'missing_prices': int(part.price_lkr.eq('').sum()),
         'first_date': part.date.min(), 'last_date': part.date.max(),
         'sha256': hashlib.sha256((destination / filename).read_bytes()).hexdigest()}
        for (fuel, filename), part in zip(FILES.items(), reloaded)
    ])
    manifest.to_csv(BASE / 'reports/per_fuel_dataset_manifest.csv', index=False)
    (BASE / 'reports/per_fuel_dataset_validation.json').write_text(json.dumps({
        'files': len(reloaded), 'records': len(combined),
        'source_file': source.name,
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'round_trip_values_preserved': True, 'combined_exactly_matches_final_dataset': True,
        'unique_source_record_fuel_keys': not combined.duplicated(key).any(),
    }, indent=2), encoding='utf-8')
    lines = ['# Cleaned datasets by fuel type', '',
             'Each CSV contains one fuel from ../fuel_prices_final_cleaned.csv, with every original column and value retained. Dates are sorted; source identifiers, source links, units and quality flags are preserved.', '',
             'Blank prices remain blank. Check price_status before using observations as forecasting targets. These are irregular revision records, not monthly training series.', '',
             '| File | Records | Valid prices |', '| --- | ---: | ---: |']
    lines.extend(f'| {name} | {count} | {valid} |' for name, count, valid in summary)
    lines.extend(['', 'Regenerate with python split_fuel_datasets.py from the package folder. All nine saved CSVs were read back and verified against the final dataset with no lost or duplicated records.', ''])
    (destination / 'README.md').write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(f'{name}: {count} records; {valid} valid prices' for name, count, valid in summary))
    print(f'Verified {len(combined)} records across {len(FILES)} files.')
    return manifest


if __name__ == '__main__':
    split()
