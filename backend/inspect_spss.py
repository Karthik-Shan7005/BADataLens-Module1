import pyreadstat
import json

file_path = r"C:\Users\KarthikShanmugam\ClaudePOC\DataLens\Module 1\data\spss\Sample data - DataLens.sav"

df, meta = pyreadstat.read_sav(file_path)

print(f"Total records: {len(df)}")
print(f"Total variables: {len(df.columns)}")
print("\n--- Variables ---")
for col in df.columns:
    label = meta.column_labels[meta.column_names.index(col)] if col in meta.column_names else ""
    val_labels = meta.variable_value_labels.get(col, {})
    print(f"\n{col}: {label}")
    if val_labels:
        for k, v in val_labels.items():
            print(f"  {k} = {v}")
    else:
        sample = df[col].dropna().unique()[:5]
        print(f"  Sample values: {list(sample)}")
