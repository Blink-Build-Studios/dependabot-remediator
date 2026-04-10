# Automated Dependabot Remediation with Claude Code

This repository demonstrates how to automatically fix Dependabot security alerts using [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and GitHub Actions. When Dependabot finds vulnerable dependencies, Claude Code upgrades them, runs your tests, and opens a PR — no human intervention required.

## How It Works

```
Dependabot detects vulnerability
         ↓
GitHub Actions workflow runs (daily cron or manual trigger)
         ↓
Preflight checks: alerts exist? no existing PR?
         ↓
Claude Code worker starts in Docker container
         ↓
Claude reads alerts via `gh api`, upgrades packages, runs tests
         ↓
Claude opens a PR with all fixes
         ↓
CI runs on the PR (tests + linting)
         ↓
Human reviews and merges (always review before merging!)
```

The key insight: **Claude Code doesn't need to know your tech stack ahead of time.** The remediation command discovers what package managers you use, reads the Dependabot alerts, and figures out how to fix them. This works for Python, JavaScript, Rust, Go, Ruby — any ecosystem Dependabot supports.

## Prerequisites

Before this automation can work, you need two things in place:

### 1. Good Test Coverage + CI

This is non-negotiable. The only way to trust that a dependency upgrade didn't break anything is to have automated tests that catch regressions. You need:

- **A test suite** that covers your critical paths
- **Linting** to catch code quality issues
- **A CI workflow** that runs both on every PR

Without this, you're blindly merging dependency upgrades with no correctness verification. The automation is only as trustworthy as your test suite.

This repo includes a sample CI workflow (`.github/workflows/ci.yml`) as a reference.

### 2. A Reproducible Build Environment

Your CI needs to be able to install dependencies, run migrations, and execute tests from scratch. This typically means:

- **A `Makefile`** (or equivalent) with `test` and `lint` targets
- **Docker Compose** for infrastructure services (database, cache, etc.)
- **Lock files** committed to the repo (`uv.lock`, `pnpm-lock.yaml`, `yarn.lock`, `Cargo.lock`, etc.)

The Claude worker runs inside a Docker container that needs access to the same infrastructure your tests need. If your tests require Postgres, the worker needs Postgres too.

## Setup Guide

### Step 1: Get a Claude Code OAuth Token

You need a Claude Max or Pro subscription. Generate a token:

```bash
claude setup-token
```

This outputs an OAuth token. Save it — you'll add it as a repository secret.

### Step 2: Create a GitHub Personal Access Token

The Dependabot alerts API is **not accessible** via the default `GITHUB_TOKEN` — GitHub does not expose a `vulnerability-alerts` permission for it. You need a separate token.

Create a **fine-grained Personal Access Token** at [github.com/settings/tokens](https://github.com/settings/tokens?type=beta):
- **Repository access**: Select your repository
- **Permissions**:
  - **Dependabot alerts**: Read
  - **Contents**: Read and write (to push branches)
  - **Pull requests**: Read and write (to create PRs)
  - **Metadata**: Read (automatically included)

Alternatively, a **classic PAT** with `repo` and `security_events` scopes will work.

### Step 3: Add Repository Secrets

Go to your repository → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Value |
|--------|-------|
| `CLAUDE_CODE_OAUTH_TOKEN` | The token from `claude setup-token` |
| `GH_PAT` | The GitHub PAT from Step 2 |

### Step 4: Enable Dependabot Alerts

Go to your repository → Settings → Code security → Enable "Dependabot alerts".

Optionally, add a `.github/dependabot.yml` to configure which ecosystems to scan:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "daily"
    open-pull-requests-limit: 0  # We handle remediation ourselves
```

Setting `open-pull-requests-limit: 0` prevents Dependabot from opening its own PRs — Claude Code handles remediation instead, consolidating all fixes into a single PR.

### Step 5: Copy the Workflow Files

Copy these files into your repository:

```
.github/workflows/dependabot-remediation.yml   ← The automation workflow
.claude/commands/remediate-dependabot-alerts.md ← Instructions for Claude Code
```

### Step 6: Copy and Adapt the Docker Worker

Copy the `docker/claude-worker/` directory. You'll need to adapt the Dockerfile and entrypoint to your stack:

**Dockerfile** — Add whatever tools your project needs:
```dockerfile
# Python project? Add Python.
# Node.js project? Add Node.js.
# Rust project? Add Rust.
# Monorepo? Add all of them.
```

**entrypoint.sh** — Update the dependency installation and migration steps:
```bash
# Replace these with your project's setup commands:
pip install -e ".[dev]"           # or: npm install, cargo build, etc.
python manage.py migrate          # or: whatever setup your tests need
```

### Step 7: Adapt the Workflow

Edit `.github/workflows/dependabot-remediation.yml`:

1. **Infrastructure**: Update the `docker-compose.yml` path and services to match your stack
2. **Timeout**: Adjust `timeout-minutes` based on how long your test suite takes
3. **Runner**: Change `runs-on` if you need a self-hosted runner (e.g., for GPU, ARM, or large memory)

### Step 8: Test It

Trigger the workflow manually to verify everything works:

1. Go to Actions → "Dependabot Remediation" → "Run workflow"
2. Watch the logs
3. If there are open Dependabot alerts, Claude Code will attempt to fix them and open a PR

## File Reference

```
.github/
  dependabot.yml                          # Dependabot configuration
  workflows/
    ci.yml                                # CI: tests + linting on every PR
    dependabot-remediation.yml            # Automation: daily Claude Code run
.claude/
  commands/
    remediate-dependabot-alerts.md        # Instructions Claude Code follows
docker/
  docker-compose.yml                      # Infrastructure services (Postgres, etc.)
  claude-worker/
    Dockerfile                            # Claude Code worker container
    entrypoint.sh                         # Worker initialization script
CLAUDE.md                                 # Project-level instructions for Claude Code
Makefile                                  # Build targets (test, lint, migrate)
```

## How the Claude Command Works

The file `.claude/commands/remediate-dependabot-alerts.md` is the instruction set that Claude Code follows. It's language-agnostic by design:

1. **Discover** — Detect what package managers and build tools are in use
2. **Query** — Fetch all open Dependabot alerts via `gh api`
3. **Upgrade** — Use the appropriate package manager to upgrade each vulnerable dependency
4. **Test** — Run the project's test suite and linting
5. **Fix** — If tests fail, investigate and fix (could be breaking API changes)
6. **PR** — Commit, push, and open a pull request with a detailed description
7. **Verify** — Wait for CI to pass; fix if it doesn't

You can customize this file for your project. For example, if you have specific test commands, migration steps, or packages that need special handling, add those instructions.

## Workflow Details

### Preflight Checks

Before spinning up a worker, the workflow checks:

1. **Kill switch** — Is `AUTONOMOUS_WORKFLOW_ENABLED` set to `"false"`? (Defaults to enabled)
2. **Open alerts** — Are there any open Dependabot alerts? (Skip if none)
3. **Existing PR** — Is there already an open PR on `claude/dependabot-remediation`? (Skip to avoid duplicate work)

### Concurrency

The workflow uses `concurrency: { group: dependabot-remediation, cancel-in-progress: false }` to ensure only one remediation job runs at a time.

### Branch Strategy

Claude Code always pushes to `claude/dependabot-remediation`. If a PR already exists on this branch, the workflow skips. After merging a remediation PR, the next daily run will pick up any new alerts.

## Kill Switch

To disable the automation without removing the workflow file:

1. Go to Settings → Secrets and variables → Actions → Variables
2. Create a variable named `AUTONOMOUS_WORKFLOW_ENABLED` with value `false`

Delete the variable (or set it back to `true`) to re-enable.

## Adapting to Your Stack

This sample uses a Django/Python project, but the pattern works for any tech stack:

### Node.js / TypeScript
- **Dockerfile**: Install Node.js, npm/pnpm/yarn
- **entrypoint.sh**: `npm install` or `pnpm install`, then `npm test`
- **dependabot.yml**: `package-ecosystem: "npm"`

### Rust
- **Dockerfile**: Install Rust toolchain
- **entrypoint.sh**: `cargo build`, then `cargo test`
- **dependabot.yml**: `package-ecosystem: "cargo"`

### Go
- **Dockerfile**: Install Go
- **entrypoint.sh**: `go mod download`, then `go test ./...`
- **dependabot.yml**: `package-ecosystem: "gomod"`

### Monorepo
- **Dockerfile**: Install all required toolchains
- **entrypoint.sh**: Install dependencies for each subdirectory
- **dependabot.yml**: Multiple `updates` entries, one per ecosystem/directory
- **Claude command**: It will detect multiple manifest files and handle each one

## Troubleshooting

### "No open Dependabot alerts" but I know there are vulnerabilities
- Check that Dependabot alerts are enabled: Settings → Code security → Dependabot alerts
- The `GITHUB_TOKEN` needs `security-events: read` permission (already configured in the workflow)

### Claude Code fails to authenticate
- Verify `CLAUDE_CODE_OAUTH_TOKEN` is set correctly in repository secrets
- Tokens expire — regenerate with `claude setup-token` if needed

### Tests fail after upgrade
- This is expected sometimes — breaking changes happen
- Claude Code will attempt to fix test failures, but major version bumps may need manual intervention
- Review the PR, fix manually if needed, and push to the same branch

### Worker times out
- Default timeout is 60 minutes
- Increase `timeout-minutes` in the workflow if your test suite is slow
- Consider using a faster self-hosted runner

### CI doesn't run on the remediation PR
- The default `GITHUB_TOKEN` can create PRs but those PRs won't trigger `on: pull_request` workflows
- Solution: Use a GitHub App or Personal Access Token for authentication instead
- See the [GitHub docs on triggering workflows from other workflows](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication#using-the-github_token-in-a-workflow)

## Review Expectations

This automation opens PRs — it does **not** merge them. A human should always review before merging. Pay attention to:

- **Major version bumps** — These are most likely to introduce breaking changes. Even if tests pass, skim the changelog for behavioral changes that tests might not cover.
- **Transitive dependency changes** — Lock file diffs can be large. Focus on the direct dependency changes and spot-check that transitive updates look reasonable.
- **Code changes beyond version bumps** — If Claude had to update call sites, import paths, or API usage to fix breaking changes, review those changes carefully.
- **Unfixable alerts** — If the PR documents alerts with no patched version available, verify that's accurate and consider whether the vulnerability is exploitable in your context.

The automation is only as trustworthy as your test suite. If your tests are thin, treat the PR with more scrutiny.

## Advanced: GitHub App Authentication

For production use, consider using a GitHub App instead of `GITHUB_TOKEN`. Benefits:

- PRs created by the App trigger CI workflows (unlike `GITHUB_TOKEN`)
- Tokens are short-lived and auto-rotated
- Fine-grained permissions

This requires additional setup (creating a GitHub App, storing its credentials as secrets, and minting installation tokens in the entrypoint). See the [GitHub documentation on GitHub Apps](https://docs.github.com/en/apps/creating-github-apps) for details.

## License

[The Unlicense](https://unlicense.org/) — public domain. Do whatever you want with this.
