#!/bin/bash
# Script to replace secrets in all files in git history
# WARNING: Replace placeholder values with actual secrets before use

git filter-branch --force --tree-filter '
  find . -type f ! -path "./.git/*" -exec sed -i "s|REPLACE_WITH_ACTUAL_REPLICATE_API_KEY|r8_REDACTED_REPLICATE_API_KEY|g" {} +
  find . -type f ! -path "./.git/*" -exec sed -i "s|REPLACE_WITH_ACTUAL_AWS_ACCESS_KEY|AKIA_REDACTED_AWS_ACCESS_KEY|g" {} +
  find . -type f ! -path "./.git/*" -exec sed -i "s|REPLACE_WITH_ACTUAL_AWS_SECRET_KEY|REDACTED_AWS_SECRET_KEY|g" {} +
  find . -type f ! -path "./.git/*" -exec sed -i "s|REPLACE_WITH_ACTUAL_DB_PASSWORD|REDACTED_DB_PASSWORD|g" {} +
  find . -type f ! -path "./.git/*" -exec sed -i "s|REPLACE_WITH_ACTUAL_JWT_SECRET|REDACTED_JWT_SECRET|g" {} +
' --prune-empty --tag-name-filter cat -- --all

