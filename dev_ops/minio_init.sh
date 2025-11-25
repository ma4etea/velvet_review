#!/bin/sh
set -e

# Await MinIO run
sleep 2
until mc alias set local "$S3_ENDPOINT_URL" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"; do
  echo "Waiting for MinIO..."
  sleep 2
done

# Create bucket
mc mb --ignore-existing local/"$S3_BUCKET"
echo "✅ Bucket $S3_BUCKET ready!"

# Apply policy to bucket for anonymous users
mc anonymous set-json minio_policy.json local/"$S3_BUCKET"
echo "✅ Bucket $S3_BUCKET download_object_only policy applied (anonymous can download objects, but cannot list bucket)"
