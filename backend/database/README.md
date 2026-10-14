# Analytics database objects

The API queries four PostgreSQL materialized views defined in
`analytics_objects.sql`. Run against the same database configured for Django:

```bash
python backend/manage.py setup_analytics_objects
```

Or, using PostgreSQL connection settings supplied securely through your existing
client configuration (for example `PGHOST`, `PGDATABASE`, `PGUSER`, and `.pgpass`):

```bash
psql --set ON_ERROR_STOP=1 --single-transaction -f backend/database/analytics_objects.sql
```

## Persistent database on this machine

The root `.env` configures both Django and the local PostgreSQL service. For Django
running on the host, set `POSTGRES_HOST=127.0.0.1` and `POSTGRES_PORT=5432`.
Start the database with:

```bash
docker compose -f docker-compose.database.yml up -d --wait
```

PostgreSQL is limited to 256 MiB and 0.5 CPU, binds only to the loopback interface,
and stores data in a persistent named Docker volume. It restarts automatically.
This service must remain running for the application to query data. `down` stops
it while keeping the volume; do not use `down -v` unless you intend to delete data.
For a containerized backend, attach it to the same Compose network and override
`POSTGRES_HOST=database` in its container environment; loopback refers to the
backend container itself in that deployment.

Populate it from the existing CSV exports after the source tables and analytics
objects have been created:

```bash
python3 backend/database/import_local_csvs.py
```

Imports 2024–25, 2025–26, then recent exports. Use `--include-historical` only when
also seeding older exports. Maps CSV player names to the API's
`first_name`/`last_name` columns. Existing player-game rows are preserved, including
the backup's duplicates; only missing numeric game/player pairs are added. Among
new duplicate CSV rows, prefer non-null points, then the latest export row.
Metadata is merged by its natural keys, preserving nonempty names and completed
game statuses. Existing predictions are checked for exact preservation. CSV
exports do not contain new model predictions, so new games have NULL predictions.

Works with both the fresh schema and the restored text stats table without a
unique constraint. Uses a numeric-ID index, import lock, and temporary staging
tables instead of requiring destructive deduplication. References and game
identity conflicts are checked before committing. Source imports and all
analytics refreshes commit as one transaction; errors roll back the import.
Memory use is bounded by streaming rows. Preview the merge without persisting
changes or refreshing snapshots:

```bash
python3 backend/database/import_local_csvs.py --dry-run
```

This is an explicit setup operation, not part of Django's existing migrations.
It creates missing views and indexes without dropping source tables or replacing
existing definitions. An existing incompatible object will need review before
replacement. All four objects are initially populated; the transaction rolls back
on any schema or data error. The database role needs access to the source tables
and permission to create objects in `public`. If the API uses a separate role,
grant that role SELECT on the four views.

## Source tables and calculation choices

- `public.player_game_stats`: numeric or numeric-text game/player/team IDs;
  `player_game_stats` containing a JSON object as text, JSON, or JSONB. A JSON string
  containing an object is also supported. Slim stats contain only basketball
  metrics and serialize as text for the current frontend's `JSON.parse` calls.
- Duplicate `(game_id, player_id)` entries count once. Prefer a non-null points
  value, then the largest source `id` if available, then a deterministic JSON
  ordering. Without a source timestamp or ID, recency cannot be recovered; review
  conflicting duplicates in the live database before deployment.
- `public.games`: `game_id`, `season_year`, `game_date`, `home_team_id`, and
  `away_team_id`. Optional `game_time`, `winner`, and `total_score_prediction`
  columns are read if present, otherwise exposed as NULL. Predictions are never
  invented. Leading zeros on game IDs normalize to their numeric form, matching
  the existing API.
- `public.teams`: `team_id`, `season_year`, `team_location`, `team_name`, and
  `team_abbreviation`, with one row per team and season. Joins include the season.
- Season averages cover all game types within the requested season, matching the
  season-statistics endpoint. Players with missing, invalid, or zero minutes are
  excluded. Numeric metrics average over their non-null values; minutes become
  decimal minutes, including legacy strings such as `31.000000:33`. Shooting percentages are per-game arithmetic means, not ratios
  of season totals. No rounding is applied in SQL.
- Scores sum deduplicated player points. Upcoming games remain visible with zero
  scores. Win/loss records require both teams to have positive, unequal scores and
  a `game_time` starting with `Final`. If that field is absent/NULL, score evidence
  is used as a fallback; it cannot distinguish a live game from a completed game.
  Teams with no completed games have a `0 - 0` record. These objects depend on
  complete box-score imports for accurate totals.

## Refresh after data imports and prediction updates

```bash
python backend/manage.py setup_analytics_objects --refresh
```

Or:

```bash
psql --set ON_ERROR_STOP=1 --single-transaction -f backend/database/refresh_analytics_objects.sql
```

Run only after source-data updates commit. This refreshes slim stats, season
averages, game summaries, then team records in dependency order and commits the
snapshots together. Normal refreshes block reads of the refreshed views until
commit; schedule outside busy periods. The existing archived refresh script does
not guarantee dependency order and should not be used for these objects.

## Isolated validation

```bash
docker pull postgres:16-alpine
python3 backend/database/test_analytics_objects.py
```

Uses PostgreSQL 16 in a disposable container capped at 256 MiB memory and 0.5 CPU,
with networking disabled, no published ports, and no bind mounts. Checks text and
numeric IDs, JSON encodings, duplicates, DNP averages, upcoming and live games,
team-season joins, missing prediction columns, reruns, and refresh propagation.
The container and its anonymous volumes are removed in `finally`. The downloaded
image remains until explicitly removed with `docker image rm postgres:16-alpine`.
These fixture checks do not validate the schema or data of the live database.

## Restore the Azure backup locally

Restore into a new database so the current database remains available:

```bash
python3 backend/database/restore_azure_backup.py azure_db_backup.sql --database oracle_db_restored_20261013
```

The restore streams the original SQL without changing the backup. It omits Azure
extensions (`azure`, `pgaadauth`), original ownership assignments, and grant/revoke
statements. Tables, rows, sequences, constraints, indexes, and application
functions are restored in one transaction. Restore errors roll back; diagnostic
logs are stored privately under `/tmp`. The command fails if the target database
already exists and does not change `.env`.

Create the analytics objects in the restored database, validate the results, then
set `POSTGRES_DB` in the root `.env` to that database name. Recreate the database
service with `docker compose -f docker-compose.database.yml up -d --wait` so its
environment and healthcheck match the restored database. The existing named
volume retains both databases. Do not run the fresh source-table creation script
over a restored schema: it does not migrate existing tables.

The original Azure backup has a text stats table without a unique constraint on
`(game_id, player_id)`. The CSV importer supports that schema while keeping
restored stats and predictions intact. Run the dry run first to check new exports.
