# SAFA Global System: Recovery & Maintenance Guide

## 1. Loading All Fixtures

If your database is empty or corrupted, run:

```
python manage.py load_all_fixtures
```

Or use the shell script:
```
bash scripts/load_geography_fixtures.sh
```

## 2. Importing Data from CSV

To convert a CSV to a Django JSON fixture:

```
python scripts/csv_to_json_fixture.py input.csv app_label.model_name output.json
```

Then load with:
```
python manage.py loaddata output.json
```

## 3. Hourly Database Backups

Backups are stored in `/home/shaun/safa_global/backups`.

To enable hourly backups, add this to your crontab:

```
0 * * * * bash /home/shaun/safa_global/scripts/backup_db_hourly.sh
```

## 4. Restoring from Backup

To restore a backup:

1. Copy the desired `.sql` file from `backups/` to your server.
2. Run:
   ```
   docker-compose exec db psql -U neetiesister safa_db < /path/to/backup.sql
   ```

## 5. Disaster Recovery Steps

- If the system is down, check Docker containers with `docker-compose ps`.
- If the database is lost, restore the latest backup as above.
- If fixtures are missing, reload with the management command or script.
- For user activation or admin issues, use the Django admin panel or management commands.

## 6. Where to Find This Guide

This document is located at:

`/home/shaun/safa_global/RECOVERY_AND_MAINTENANCE.md`

Keep this file up to date with any new processes or scripts.
