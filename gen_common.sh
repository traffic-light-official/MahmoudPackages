#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

declare -A MODULE=(
  [drf-partial-response-fields]="drf_partial_response_fields"
  [drf-llm-gateway]="drf_llm_gateway"
  [drf-idempotency]="drf_idempotency"
  [drf-ratelimit-plus]="drf_ratelimit_plus"
  [drf-contract-test]="drf_contract_test"
  [drf-multitenant]="drf_multitenant"
  [drf-file-pipeline]="drf_file_pipeline"
)

declare -A DESC=(
  [drf-partial-response-fields]="GraphQL-like sparse fieldsets and automatic query optimization for Django REST Framework"
  [drf-llm-gateway]="Expose Django REST Framework serializers and viewsets as OpenAI / MCP tools with automatic JSON Schema generation"
  [drf-idempotency]="Stripe-style idempotency keys for Django REST Framework with pluggable Redis/database backends"
  [drf-ratelimit-plus]="Advanced rate limiting for Django REST Framework: token bucket, sliding window, tiers, and Redis Cluster support"
  [drf-contract-test]="Contract testing and breaking-change detection for Django REST Framework APIs from OpenAPI schemas"
  [drf-multitenant]="Shared-schema multi-tenancy for Django REST Framework with automatic queryset and serializer enforcement"
  [drf-file-pipeline]="Direct-to-S3 upload pipeline for Django REST Framework with resumable uploads, virus scanning, and image processing"
)

declare -A EXTRA_MYPY=(
  [drf-partial-response-fields]=""
  [drf-llm-gateway]="types-jsonschema"
  [drf-idempotency]="types-redis"
  [drf-ratelimit-plus]="types-redis"
  [drf-contract-test]="types-jsonschema"
  [drf-multitenant]=""
  [drf-file-pipeline]="types-redis boto3-stubs"
)

render() {
  local tmpl="$1" out="$2" pkg="$3" mod="$4" desc="$5"
  sed -e "s|__PKG__|${pkg}|g" -e "s|__MODULE__|${mod}|g" -e "s|__DESC__|${desc}|g" "_templates/${tmpl}" > "${out}"
}

for pkg in "${!MODULE[@]}"; do
  mod="${MODULE[$pkg]}"
  desc="${DESC[$pkg]}"

  mkdir -p "$pkg/src/$mod" "$pkg/.github/workflows"

  render SECURITY.md.tmpl "$pkg/SECURITY.md" "$pkg" "$mod" "$desc"
  render CONTRIBUTING.md.tmpl "$pkg/CONTRIBUTING.md" "$pkg" "$mod" "$desc"
  render MANIFEST.in.tmpl "$pkg/MANIFEST.in" "$pkg" "$mod" "$desc"
  render mkdocs.yml.tmpl "$pkg/mkdocs.yml" "$pkg" "$mod" "$desc"
  render ci.yml.tmpl "$pkg/.github/workflows/ci.yml" "$pkg" "$mod" "$desc"
  render release.yml.tmpl "$pkg/.github/workflows/release.yml" "$pkg" "$mod" "$desc"

  extra_lines=""
  for d in ${EXTRA_MYPY[$pkg]}; do
    extra_lines="${extra_lines}          - ${d}"$'\n'
  done
  # render pre-commit config with multi-line extra deps insertion
  awk -v extra="$extra_lines" '{
    if ($0 == "__EXTRA_MYPY_LINES__") { printf "%s", extra } else { print }
  }' "_templates/pre-commit-config.yaml.tmpl" > "$pkg/.pre-commit-config.yaml"

  touch "$pkg/src/$mod/py.typed"
done

echo "RENDER_DONE"
