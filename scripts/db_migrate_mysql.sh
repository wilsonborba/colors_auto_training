#!/usr/bin/env bash
set -euo pipefail

MIGRATIONS_DIR="${MIGRATIONS_DIR:-api/domain/migrations}"
MIGRATIONS_TABLE="${MIGRATIONS_TABLE:-schema_migrations}"
ENV_FILE="${ENV_FILE:-.env}"

die() { echo "ERROR: $*" >&2; exit 1; }
info() { echo "==> $*"; }

usage() {
  cat <<'EOF'
Usage:
  ./scripts/db_migrate.sh all
  ./scripts/db_migrate.sh one <filename.sql>
  ./scripts/db_migrate.sh status
  ./scripts/db_migrate.sh list

Env (.env):
  COLORS_DB_HOST
  COLORS_DB_PORT
  COLORS_DB_USER
  COLORS_DB_PASSWORD
  COLORS_DB_NAME

Optional SSL:
  COLORS_DB_SSL_CA   (path to CA pem, e.g. ./ca.pem)
  COLORS_DB_SSL_MODE (VERIFY_CA, VERIFY_IDENTITY, REQUIRED)
    - On older mysql clients, VERIFY_IDENTITY will degrade to VERIFY_CA behavior.
EOF
}

# ---- Load .env ----
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
else
  die "ENV file not found: $ENV_FILE"
fi

: "${COLORS_DB_HOST:?Missing COLORS_DB_HOST}"
: "${COLORS_DB_PORT:?Missing COLORS_DB_PORT}"
: "${COLORS_DB_USER:?Missing COLORS_DB_USER}"
: "${COLORS_DB_PASSWORD:?Missing COLORS_DB_PASSWORD}"
: "${COLORS_DB_NAME:?Missing COLORS_DB_NAME}"

command -v mysql >/dev/null 2>&1 || die "mysql client not found in PATH"

# ---- Auto-detect CA file ----
if [[ -z "${COLORS_DB_SSL_CA:-}" && -f "./ca.pem" ]]; then
  COLORS_DB_SSL_CA="./ca.pem"
fi

# If CA is present and ssl-mode not set, default to VERIFY_CA
if [[ -n "${COLORS_DB_SSL_CA:-}" && -z "${COLORS_DB_SSL_MODE:-}" ]]; then
  COLORS_DB_SSL_MODE="VERIFY_CA"
fi

# ---- Base mysql args ----
MYSQL_BASE_ARGS=(
  "-h" "$COLORS_DB_HOST"
  "-P" "$COLORS_DB_PORT"
  "-u" "$COLORS_DB_USER"
  "--password=$COLORS_DB_PASSWORD"
  "$COLORS_DB_NAME"
  "--protocol=TCP"
  "--batch" "--raw" "--silent"
)

# ---- SSL args with feature detection ----
MYSQL_SSL_ARGS=()

MYSQL_HELP="$(mysql --help 2>/dev/null || true)"

supports_ssl_mode() {
  echo "$MYSQL_HELP" | grep -q -- '--ssl-mode'
}

supports_verify_server_cert() {
  echo "$MYSQL_HELP" | grep -q -- '--ssl-verify-server-cert'
}

# Always include CA if provided
if [[ -n "${COLORS_DB_SSL_CA:-}" ]]; then
  MYSQL_SSL_ARGS+=( "--ssl-ca=${COLORS_DB_SSL_CA}" )
fi

# Apply SSL mode
if [[ -n "${COLORS_DB_SSL_MODE:-}" ]]; then
  case "$COLORS_DB_SSL_MODE" in
    VERIFY_CA|VERIFY_IDENTITY)
      if supports_ssl_mode; then
        MYSQL_SSL_ARGS+=( "--ssl-mode=${COLORS_DB_SSL_MODE}" )
      else
        # Older clients: best effort
        # VERIFY_IDENTITY is not available; degrade to CA verification
        if supports_verify_server_cert; then
          MYSQL_SSL_ARGS+=( "--ssl-verify-server-cert" )
        fi
        # Force TLS on older clients
        MYSQL_SSL_ARGS+=( "--ssl" )
      fi
      ;;
    REQUIRED)
      if supports_ssl_mode; then
        MYSQL_SSL_ARGS+=( "--ssl-mode=REQUIRED" )
      else
        MYSQL_SSL_ARGS+=( "--ssl" )
      fi
      ;;
    *)
      die "Unknown COLORS_DB_SSL_MODE='$COLORS_DB_SSL_MODE' (use VERIFY_CA, VERIFY_IDENTITY, REQUIRED)"
      ;;
  esac
fi

mysql_exec() {
  mysql "${MYSQL_BASE_ARGS[@]}" "${MYSQL_SSL_ARGS[@]}" -e "$1"
}

ensure_migrations_table() {
  mysql_exec "
    CREATE TABLE IF NOT EXISTS ${MIGRATIONS_TABLE} (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      filename VARCHAR(255) NOT NULL UNIQUE,
      applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
  "
}

is_applied() {
  local fname="$1"
  mysql "${MYSQL_BASE_ARGS[@]}" "${MYSQL_SSL_ARGS[@]}" \
    -e "SELECT 1 FROM ${MIGRATIONS_TABLE} WHERE filename='${fname}' LIMIT 1;" \
    | grep -q "^1$"
}

apply_file() {
  local file_path="$1"
  local fname
  fname="$(basename "$file_path")"

  [[ -f "$file_path" ]] || die "Migration not found: $file_path"

  if is_applied "$fname"; then
    info "SKIP (already applied): $fname"
    return 0
  fi

  info "APPLY: $fname"
  mysql "${MYSQL_BASE_ARGS[@]}" "${MYSQL_SSL_ARGS[@]}" < "$file_path"
  mysql_exec "INSERT INTO ${MIGRATIONS_TABLE}(filename) VALUES('${fname}');"
  info "DONE: $fname"
}

list_files() {
  [[ -d "$MIGRATIONS_DIR" ]] || die "Migrations dir not found: $MIGRATIONS_DIR"
  ls -1 "$MIGRATIONS_DIR"/*.sql 2>/dev/null | xargs -n 1 basename || true
}

status() {
  ensure_migrations_table
  info "Applied migrations in ${MIGRATIONS_TABLE}:"
  mysql "${MYSQL_BASE_ARGS[@]}" "${MYSQL_SSL_ARGS[@]}" \
    -e "SELECT filename, applied_at FROM ${MIGRATIONS_TABLE} ORDER BY applied_at, filename;"
}

run_all() {
  ensure_migrations_table
  [[ -d "$MIGRATIONS_DIR" ]] || die "Migrations dir not found: $MIGRATIONS_DIR"

  shopt -s nullglob
  local files=( "$MIGRATIONS_DIR"/*.sql )
  shopt -u nullglob
  ((${#files[@]} > 0)) || die "No .sql files found in $MIGRATIONS_DIR"

  IFS=$'\n' files=( $(printf '%s\n' "${files[@]}" | sort) ); unset IFS
  for f in "${files[@]}"; do
    apply_file "$f"
  done
}

run_one() {
  ensure_migrations_table
  local fname="${1:-}"
  [[ -n "$fname" ]] || die "Missing filename. Try: ./scripts/db_migrate.sh one <file.sql>"
  apply_file "$MIGRATIONS_DIR/$fname"
}

cmd="${1:-}"
case "$cmd" in
  all)    run_all ;;
  one)    shift; run_one "${1:-}" ;;
  status) status ;;
  list)   list_files ;;
  -h|--help|"") usage ;;
  *) die "Unknown command: $cmd (use --help)" ;;
esac
