# Import Service

Python service for Excel inspection, cleaning, validation, and database import.

## MVP command

```powershell
python -m import_service.cli inspect "C:\path\to\file.xlsx"
```

Current scope:

- Inspect sheet structure.
- Extract overview validation numbers from `总表-加盟商` and `总表-网点`.
- Prepare for full PostgreSQL import.

Next scope:

- Persist source_file and import_job.
- Parse franchise/site summary rows.
- Unpivot contribution flow sheets.
- Generate validation reports.
