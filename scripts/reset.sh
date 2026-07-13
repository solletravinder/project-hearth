#!/usr/bin/env bash
# reset.sh — Remove DB & uploads for a fresh project start.
set -euo pipefail

HEARTH_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "This will DELETE all data (database + uploaded files) and reset Hearth to a fresh state."
read -rp "Are you sure? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborted."
    exit 1
fi

# Remove SQLite database files
rm -vf "$HEARTH_DIR/data/hearth.db"
rm -vf "$HEARTH_DIR/data/hearth.db-wal"
rm -vf "$HEARTH_DIR/data/hearth.db-shm"

# Remove uploaded files
rm -rvf "$HEARTH_DIR/data/uploads/"

# Recreate empty uploads directory
mkdir -p "$HEARTH_DIR/data/uploads"
touch "$HEARTH_DIR/data/uploads/.gitkeep"

echo ""
echo "Done. All data has been reset."
echo "Run the server and the first-run wizard will re-initialize the database."
