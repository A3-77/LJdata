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
python -m import_service.cli extract contribution-flow "C:\path\to\file.xlsx" --scope region --limit 5
python -m import_service.cli extract contribution-flow "C:\path\to\file.xlsx" --scope franchise --limit 5
```

Load summary rows into PostgreSQL:

```powershell
python -m import_service.cli load-workbook "C:\path\to\file.xlsx" --database-url $env:DATABASE_URL --replace-period
python -m import_service.cli load-summary "C:\path\to\file.xlsx" --database-url $env:DATABASE_URL --replace-period
python -m import_service.cli load-contribution-flow "C:\path\to\file.xlsx" --database-url $env:DATABASE_URL --scope region --replace-period
python -m import_service.cli load-contribution-flow "C:\path\to\file.xlsx" --database-url $env:DATABASE_URL --scope franchise --replace-period
```

Use `load-workbook` for normal imports. It creates `source_file`, records one `import_job`, refreshes `source_sheet`, and assigns `file_id` to loaded facts.

Current scope:

- Inspect sheet structure.
- Extract overview validation numbers from `总表-加盟商` and `总表-网点`.
- Extract normalized rows from `总表-加盟商`.
- Extract normalized rows from `总表-网点`.
- Unpivot `辽宁区域贡献`.
- Unpivot `加盟商贡献`.
- Load summary rows into PostgreSQL when dependencies and database are available.
- Load contribution flow rows into PostgreSQL when dependencies and database are available.
- Persist `source_file`, `source_sheet`, and `import_job` for supported workbook imports.
- Prepare for full PostgreSQL import.

Next scope:

- Generate validation reports.
