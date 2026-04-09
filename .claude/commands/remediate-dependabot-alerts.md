# Dependabot Security Alert Remediation

Review and fix all open Dependabot security alerts by upgrading vulnerable dependencies, running tests, and creating a PR.

## Objective

Fix all open Dependabot security alerts in this repository. The task is not complete until:
1. All security alerts are addressed
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
```

### 2. Query Dependabot alerts

```bash
gh api repos/{owner}/{repo}/dependabot/alerts?state=open \
  --jq '.[] | {number, summary: .security_advisory.summary, package: .dependency.package.name, severity: .security_advisory.severity, manifest: .dependency.manifest_path}'
```

Review each alert to understand:
- Which package is vulnerable
- What the vulnerability is
- Which manifest file contains it
- Severity level

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

### 4. Check for breaking changes

After upgrading:
1. Read the package's CHANGELOG or release notes for breaking changes
2. Update code if necessary to handle API changes
3. If a major version bump is required and introduces breaking changes, document this in the PR

### 5. Run tests

Run whatever test commands exist in the project:

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

Fix any test failures or lint errors before proceeding.

### 6. Create PR

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

## Testing

- Tests passing
- Linting passing
- No breaking changes detected

## Verification

Dependabot alerts will auto-close when this PR is merged."
```

### 7. Monitor CI

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
