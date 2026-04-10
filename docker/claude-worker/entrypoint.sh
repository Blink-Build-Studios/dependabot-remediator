#!/bin/bash
# Entrypoint for the Claude Code worker container.
#
# Initializes the environment, waits for infrastructure, installs dependencies,
# runs migrations, and then invokes Claude Code with the specified command.
#
# Required environment variables:
#   CLAUDE_CODE_OAUTH_TOKEN  - OAuth token for Claude Code API access
#   GITHUB_TOKEN             - GitHub token for gh CLI and git push
#   COMMAND                  - The Claude Code slash command to run

set -e

# ============================================================================
# Configuration
# ============================================================================

if [ -z "${GITHUB_TOKEN:-}" ]; then
    echo "ERROR: GITHUB_TOKEN must be set" >&2
    exit 1
fi

if [ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
    echo "ERROR: CLAUDE_CODE_OAUTH_TOKEN must be set" >&2
    exit 1
fi

export CLAUDE_CODE_OAUTH_TOKEN

# Save the GitHub token and unset the env var immediately.
# gh CLI refuses to store credentials when GITHUB_TOKEN is in the environment.
GH_TOKEN_VALUE="$GITHUB_TOKEN"
unset GITHUB_TOKEN

COMMAND="${COMMAND:-/remediate-dependabot-alerts}"
GIT_USER_NAME="${GIT_USER_NAME:-claude-bot}"
GIT_USER_EMAIL="${GIT_USER_EMAIL:-claude-bot@users.noreply.github.com}"
CLAUDE_MODEL="${CLAUDE_MODEL:-sonnet}"

# Auto-detect Docker networking
if getent hosts host.docker.internal >/dev/null 2>&1; then
    DOCKER_HOST_ALIAS="host.docker.internal"
else
    DOCKER_HOST_ALIAS="localhost"
fi
POSTGRES_HOST="${POSTGRES_HOST:-$DOCKER_HOST_ALIAS}"

# ============================================================================
# Helpers
# ============================================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

wait_for_postgres() {
    log "Waiting for PostgreSQL at $POSTGRES_HOST:5432..."
    local max_attempts=30
    local attempt=1
    while ! pg_isready -h "$POSTGRES_HOST" -p 5432 -U postgres -q; do
        if [ $attempt -ge $max_attempts ]; then
            echo "ERROR: PostgreSQL not available after $max_attempts attempts" >&2
            return 1
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    log "PostgreSQL is ready"
}

# ============================================================================
# Main
# ============================================================================

log "=== Claude Code Worker Starting ==="
log "Command: $COMMAND"

# Configure git
git config --global user.name "$GIT_USER_NAME"
git config --global user.email "$GIT_USER_EMAIL"
git config --global --add safe.directory /workspace

# Clear any stale credential config from actions/checkout
if [ -f /workspace/.git/config ]; then
    git config --local --unset-all http.https://github.com/.extraheader 2>/dev/null || true
fi

# Use a simple credential helper that passes the token for git push
git config --global credential.https://github.com.helper '!f() { echo "username=x-access-token"; echo "password=${GH_TOKEN}"; }; f'

# Authenticate gh CLI using the saved token.
# Use --skip-ssh-key to avoid interactive prompts. The GH_TOKEN env var
# approach is simpler than gh auth login for CI — just export it for gh.
export GH_TOKEN="$GH_TOKEN_VALUE"
unset GH_TOKEN_VALUE
log "GitHub CLI authenticated via GH_TOKEN"

# Wait for database
wait_for_postgres

# Export database connection for Django
export POSTGRES_HOST
export POSTGRES_USER="${POSTGRES_USER:-postgres}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
export POSTGRES_DB="${POSTGRES_DB:-sample_app}"

# Install dependencies
log "Installing dependencies..."
cd /workspace
pip install -e ".[dev]" --quiet

# Run migrations
log "Running migrations..."
python manage.py migrate --no-input

log "=== Environment Ready ==="

# Run Claude Code
log "Invoking Claude Code..."
timeout "${CLAUDE_TIMEOUT:-55m}" claude \
    --model "$CLAUDE_MODEL" \
    --print \
    --output-format stream-json \
    --verbose \
    --dangerously-skip-permissions \
    "$COMMAND"
