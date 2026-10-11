#!/bin/sh
# SeaweedFS に Lightdash 用のバケットを作成する。
# 公式の docker/init-minio.sh と同じく、バケットの作成、ライフサイクル（一定日数後に削除）、CORS を設定する。
set -e

S3="aws --endpoint-url ${S3_ENDPOINT}"

echo "Waiting for SeaweedFS S3 API to become available..."
until ${S3} s3api list-buckets >/dev/null 2>&1; do
    sleep 1
done

if ${S3} s3api head-bucket --bucket "${S3_BUCKET}" >/dev/null 2>&1; then
    echo "Bucket '${S3_BUCKET}' already exists"
else
    echo "Creating bucket '${S3_BUCKET}'..."
    ${S3} s3api create-bucket --bucket "${S3_BUCKET}"
fi

echo "Setting lifecycle policy: expire after ${EXPIRATION_DAYS} day(s)"
${S3} s3api put-bucket-lifecycle-configuration --bucket "${S3_BUCKET}" --lifecycle-configuration "{
  \"Rules\": [{\"ID\": \"expire\", \"Status\": \"Enabled\", \"Filter\": {\"Prefix\": \"\"}, \"Expiration\": {\"Days\": ${EXPIRATION_DAYS}}}]
}"

# ブラウザから署名付き URL で直接アップロード・ダウンロードできるよう CORS を設定する
echo "Configuring CORS for presigned uploads..."
${S3} s3api put-bucket-cors --bucket "${S3_BUCKET}" --cors-configuration '{
  "CORSRules": [{
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "PUT", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"]
  }]
}'

echo "Done"
