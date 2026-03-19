# Generating Synthetic Synthea Data

This project uses only fake synthetic healthcare data. Do not place real PHI in this repository.

1. Install Java 11+.
2. Clone Synthea:

```bash
git clone https://github.com/synthetichealth/synthea.git
cd synthea
```

3. Generate CSV output:

```bash
./run_synthea -p 100 --exporter.csv.export true
```

On Windows PowerShell:

```powershell
.\run_synthea.bat -p 100 --exporter.csv.export true
```

4. Copy CSV files from `synthea/output/csv` into this repo's `data/synthea/csv`.
5. Run:

```bash
python scripts/ingest_synthea.py
python scripts/build_index.py
```
