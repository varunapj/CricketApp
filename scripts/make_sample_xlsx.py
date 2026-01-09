"""Create an Excel sample from `Players_Inventory.tsv`.

Run from the project venv:
  python scripts/make_sample_xlsx.py
"""
from pathlib import Path

try:
  import pandas as pd
except Exception:
  raise SystemExit('pandas is required to generate sample Excel. Install requirements first.')

ROOT = Path(__file__).resolve().parent.parent
tsv = ROOT / 'Players_Inventory.tsv'
outdir = ROOT / 'samples'
outdir.mkdir(exist_ok=True)
out = outdir / 'Players_Inventory.xlsx'

if not tsv.exists():
  raise SystemExit(f'Missing TSV: {tsv}')

df = pd.read_csv(tsv, sep='\t')
df.to_excel(out, index=False)
print('Wrote', out)
