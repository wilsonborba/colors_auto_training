#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${ENV_FILE:-.env}"

die() { echo "ERROR: $*" >&2; exit 1; }

# Load .env
[[ -f "$ENV_FILE" ]] || die "ENV file not found: $ENV_FILE"
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${COLORS_DB_HOST:?Missing COLORS_DB_HOST}"
: "${COLORS_DB_PORT:?Missing COLORS_DB_PORT}"
: "${COLORS_DB_USER:?Missing COLORS_DB_USER}"
: "${COLORS_DB_PASSWORD:?Missing COLORS_DB_PASSWORD}"
: "${COLORS_DB_NAME:?Missing COLORS_DB_NAME}"

command -v mysql >/dev/null 2>&1 || die "mysql client not found in PATH"

# Auto-detect CA file (prefer env, else ./ca.pem)
CA_PATH="${COLORS_DB_SSL_CA:-}"
if [[ -z "$CA_PATH" && -f "./ca.pem" ]]; then
  CA_PATH="./ca.pem"
fi

MYSQL_HELP="$(mysql --help 2>/dev/null || true)"

supports_ssl_mode() {
  echo "$MYSQL_HELP" | grep -q -- '--ssl-mode'
}

supports_verify_server_cert() {
  echo "$MYSQL_HELP" | grep -q -- '--ssl-verify-server-cert'
}

# Base args
ARGS=(
  "-h" "$COLORS_DB_HOST"
  "-P" "$COLORS_DB_PORT"
  "-u" "$COLORS_DB_USER"
  "--password=$COLORS_DB_PASSWORD"
  "--protocol=TCP"
  "$COLORS_DB_NAME"
)

# SSL args (Aiven typically needs CA verification)
SSL_ARGS=()
if [[ -n "$CA_PATH" ]]; then
  SSL_ARGS+=( "--ssl-ca=$CA_PATH" )
fi

if supports_ssl_mode; then
  # MySQL 8+ / newer client
  # VERIFY_CA is ideal when you have the CA
  if [[ -n "$CA_PATH" ]]; then
    SSL_ARGS+=( "--ssl-mode=VERIFY_CA" )
  else
    SSL_ARGS+=( "--ssl-mode=REQUIRED" )
  fi
else
  # Older client (no --ssl-mode)
  SSL_ARGS+=( "--ssl" )
  if [[ -n "$CA_PATH" && supports_verify_server_cert ]]; then
    SSL_ARGS+=( "--ssl-verify-server-cert" )
  fi
fi

exec mysql "${ARGS[@]}" "${SSL_ARGS[@]}"
