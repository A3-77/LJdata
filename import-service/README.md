# Import Service

Python service for Excel inspection, cleaning, validation, and database import.

## MVP command

```powershell
python -m import_service.cli inspect "C:\path\to\file.xlsx"
```

Extract normalized summary rows:

```powershell
python -m import_service.cli extract franchise-summary "C:\path\to\file.xlsx" --limit 5
python -m import_service.cli extract site-summary "C:\path\to\file.xlsx" --limit 5
```

Load summary rows into PostgreSQL:

```powershell
python -m import_service.cli load-summary "C:\path\to\file.xlsx" --database-url $env:DATABASE_URL --replace-period
```

Current scope:

- Inspect sheet structure.
- Extract overview validation numbers from `总表-加盟商` and `总表-网点`.
- Extract normalized rows from `总表-加盟商`.
- Extract normalized rows from `总表-网点`.
- Load summary rows into PostgreSQL when dependencies and database are available.
- Prepare for full PostgreSQL import.

Next scope:

- Persist source_file and import_job.
- Unpivot contribution flow sheets.
- Generate validation reports.
