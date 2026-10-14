"""Restore an Azure pg_dump SQL backup into a new, isolated local database.

Leaves the backup and existing databases unchanged. Azure extension, ownership,
and ACL statements are omitted; application schema and COPY rows are preserved.
Does not switch the application's .env or import CSV data.
"""

import argparse
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[2]


def psql(database):
    return ["docker", "compose", "-f", str(ROOT / "docker-compose.database.yml"),
            "exec", "-T", "--env", f"RESTORE_DATABASE={database}", "database", "sh", "-c",
            'export PGPASSWORD="$POSTGRES_PASSWORD"; exec psql -h 127.0.0.1 '
            '-U "$POSTGRES_USER" -d "$RESTORE_DATABASE" --no-psqlrc -v ON_ERROR_STOP=1']


def filtered_lines(path, counts):
    copying = False
    skipping = False
    patterns = (
        r"^(?:CREATE|COMMENT ON) EXTENSION .*\b(?:azure|pgaadauth)\b",
        r"^ALTER .* OWNER TO ",
        r"^(?:GRANT|REVOKE) ",
    )
    with path.open() as source:
        for line in source:
            if copying:
                yield line
                if line.rstrip("\n") == "\\.":
                    copying = False
                continue
            if skipping:
                skipping = not line.rstrip().endswith(";")
                continue
            if any(re.match(pattern, line) for pattern in patterns):
                counts["omitted_cloud_settings"] += 1
                skipping = not line.rstrip().endswith(";")
                continue
            if re.match(r"^(?:CREATE DATABASE|CREATE ROLE|CREATE USER|ALTER SYSTEM|\\)", line):
                raise ValueError("Unexpected database/role/server or psql directive; review the backup first.")
            if line.startswith("COPY "):
                if not line.rstrip().endswith("FROM stdin;"):
                    raise ValueError("Only pg_dump COPY FROM stdin is supported.")
                copying = True
            yield line


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup", type=Path)
    parser.add_argument("--database", required=True, help="New database name; fails if it exists")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", args.database):
        parser.error("Use a lowercase database name with letters, digits, and underscores.")
    if not args.backup.is_file():
        parser.error("Backup file not found.")
    counts = {"omitted_cloud_settings": 0}
    subprocess.run(psql("postgres"), input=f'CREATE DATABASE "{args.database}";\n',
                   text=True, check=True, cwd=ROOT, capture_output=True)
    # Keep error details private: COPY failures may include sensitive restored rows.
    with tempfile.NamedTemporaryFile(mode="w+", prefix="oracle-restore-", suffix=".log", delete=False) as errors:
        with subprocess.Popen(psql(args.database), stdin=subprocess.PIPE, text=True,
                              cwd=ROOT, stdout=subprocess.DEVNULL, stderr=errors) as process:
            try:
                process.stdin.write("BEGIN;\n")
                for line in filtered_lines(args.backup, counts):
                    process.stdin.write(line)
                process.stdin.write("\nCOMMIT;\n")
                process.stdin.close()
                status = process.wait()
            except BaseException:
                if not process.stdin.closed:
                    process.stdin.close()
                process.wait()
                raise
        if status:
            raise RuntimeError(f"Restore rolled back. Private diagnostics: {errors.name}")
    print(f"Restored backup into {args.database}; omitted {counts['omitted_cloud_settings']} cloud settings.")
    print("Existing database, original backup, .env, and CSV data remain unchanged.")


if __name__ == "__main__":
    main()
