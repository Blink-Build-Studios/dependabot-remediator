# Dependabot Security Alert Remediation

Review and fix all open Dependabot security alerts by upgrading vulnerable dependencies, running tests, and creating a PR.

## Objective

Fix all open Dependabot security alerts in this repository. The task is not complete until:
1. All fixable security alerts are addressed
2. Tests pass
3. Linting passes
4. A PR is created and CI is green

## Steps

### 1. Discover the project structure

Before doing anything, understand what you're working with:

```bash
# What package managers are in use?
ls -la pyproject.toml setup.py setup.cfg requirements*.txt package.json pnpm-lock.yaml yarn.lock Cargo.toml go.mod Gemfile 2>/dev/null

# Is there a Makefile with test/lint targets?
cat Makefile 2>/dev/null | head -50

# Read CLAUDE.md for project-specific instructions
cat CLAUDE.md 2>/dev/null
```

### 2. Query Dependabot alerts

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
gh api "repos/${REPO}/dependabot/alerts?state=open&per_page=100" \
  --jq '.[] | {number, summary: .security_advisory.summary, package: .dependency.package.name, severity: .security_advisory.severity, manifest: .dependency.manifest_path, patched_versions: .security_vulnerability.first_patched_version.identifier}'
```

Review each alert to understand:
- Which package is vulnerable
- What the vulnerability is
- Which manifest file contains it
- Severity level
- **Whether a patched version exists** (`patched_versions` will be null if no fix is available yet)

### 3. Upgrade dependencies

For each vulnerable dependency, use the appropriate package manager:

**Python (pip/uv):**
```bash
# If using uv (check for uv.lock):
uv add "package-name@latest"
uv sync

# If using pip (check for requirements.txt):
pip install --upgrade package-name
pip freeze > requirements.txt

# If using pyproject.toml with pip:
# Edit the version constraint in pyproject.toml, then:
pip install -e ".[dev]"
```

**JavaScript/TypeScript (npm/pnpm/yarn):**
```bash
# npm
npm update package-name

# pnpm
pnpm update package-name

# yarn
yarn upgrade package-name
```

**Rust (Cargo):**
```bash
cargo update -p package-name
```

**Go:**
```bash
go get -u package-name
go mod tidy
```

**Ruby (Bundler):**
```bash
bundle update package-name
```

#### Alerts with no patched version available

Some alerts have no fix available yet — the upstream maintainer hasn't released a patched version. For these:

1. **Check if an alternative package exists** that provides the same functionality without the vulnerability. If so, migrate to it.
2. **If no alternative exists**, skip the alert and document it in the PR body under a "Unfixable Alerts" section, explaining that no patched version is available.
3. **Never downgrade or remove a dependency** just to close an alert — that will break the application.

### 4. Run tests and fix everything until they pass

After upgrading, run the project's test suite and linting:

```bash
# Check Makefile for targets
make test 2>/dev/null || true
make lint 2>/dev/null || true

# Or run directly
pytest 2>/dev/null || true
npm test 2>/dev/null || true
cargo test 2>/dev/null || true
go test ./... 2>/dev/null || true
```

**If tests or linting fail, you must fix the failures.** This is the core of the job — not just upgrading versions, but making the codebase work with the new versions. Common scenarios:

- **Deprecated API removed in new version**: Read the package's CHANGELOG or migration guide, then update every call site in the codebase to use the new API.
- **Function signature changed**: Find all callers and update their arguments.
- **Import paths changed**: Update all import statements across the codebase.
- **Type changes**: Fix any type errors introduced by the upgrade.
- **New lint rules triggered by upgraded linter**: Fix the lint violations.
- **Major version bump required**: Do the major version bump, read the migration guide, and update all affected code.

**Keep iterating** — upgrade, run tests, fix failures, run tests again — until the full test suite and linting pass cleanly. Do not proceed to creating a PR until everything is green.

### 5. Create PR

First, clean up any stale remote branch from a previous run:

```bash
git push origin --delete claude/dependabot-remediation 2>/dev/null || true
```

Then create the branch and PR:

```bash
git checkout -b claude/dependabot-remediation
git add .
git commit -m "Fix Dependabot security alerts

- Upgrade [package] from X.Y.Z to A.B.C (fixes CVE-XXXX-XXXX)
[repeat for each package]

Addresses Dependabot alerts: #N, #N, #N"

git push -u origin claude/dependabot-remediation
```

```bash
gh pr create \
  --title "Fix Dependabot security alerts" \
  --body "## Summary

This PR addresses all open Dependabot security alerts.

## Security Fixes

- **[Package]**: X.Y.Z → A.B.C — [CVE or description] (Severity: High/Medium/Low)
[repeat for each]

## Unfixable Alerts

[List any alerts where no patched version is available, or remove this section if all were fixed]

## Testing

- Tests passing
- Linting passing
- No breaking changes detected

## Verification

Dependabot alerts will auto-close when this PR is merged.

## Review

This PR was generated automatically. Please review the dependency changes and
test results before merging. Pay particular attention to any major version bumps."
```

### 6. Monitor CI

After creating the PR:
1. Watch CI: `gh pr checks --watch`
2. If CI fails, investigate and fix — push additional commits to the same branch
3. **The task is not complete until CI is green**

## Important Notes

- **Never ignore alerts** — always upgrade or document why you can't
- **Test thoroughly** — security fixes can introduce breaking changes
- **Check all manifest files** — don't miss transitive or dev dependencies
- **One PR for all fixes** — consolidate into a single remediation PR
- **CI must pass** — incomplete if CI is failing
- **Document unfixable alerts** — if no patched version exists, say so in the PR
