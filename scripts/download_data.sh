#!/usr/bin/env bash
# Download NYC TLC yellow taxi trips, Jan to Mar 2024, into data/raw/ (DVC tracks this folder, git does not).
set -euo pipefail

BASE_URL="https://d37ci6vzurychx.cloudfront.net/trip-data"
OUT_DIR="data/raw"

mkdir -p "$OUT_DIR"
for month in 2024-01 2024-02 2024-03; do
  curl -fL --retry 3 -o "$OUT_DIR/yellow_tripdata_${month}.parquet" \
    "$BASE_URL/yellow_tripdata_${month}.parquet"
done
