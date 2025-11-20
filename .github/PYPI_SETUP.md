# PyPI Auto-Publishing Setup Guide

This guide explains how to set up automatic publishing to PyPI using GitHub Actions.

## Overview

The workflow automatically:
1. ✅ Detects version changes in `setup.py`
2. ✅ Runs tests across multiple Python versions and OS
3. ✅ Builds the package
4. ✅ Creates a Git tag (e.g., `v0.2.0`)
5. ✅ Creates a GitHub Release with changelog
6. ✅ Publishes to PyPI
7. ✅ Updates CHANGELOG.md

## Prerequisites

### 1. PyPI API Token

1. **Create PyPI account** (if you don't have one):
   - Go to https://pypi.org/account/register/

2. **Generate API token**:
   - Go to https://pypi.org/manage/account/token/
   - Click "Add API token"
   - Token name: `github-actions-reroute`
   - Scope: "Entire account" (or specific project after first upload)
   - Click "Add token"
   - **⚠️ IMPORTANT**: Copy the token immediately (it won't be shown again)

3. **Add token to GitHub Secrets**:
   - Go to your repository: https://github.com/cbsajan/reroute
   - Navigate to **Settings** → **Secrets and variables** → **Actions**
   - Click **"New repository secret"**
   - Name: `PYPI_API_TOKEN`
   - Value: Paste your PyPI API token
   - Click **"Add secret"**

### 2. First Manual Upload (Optional but Recommended)

For the first release, it's recommended to upload manually to register the project:

```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Upload to PyPI
twine upload dist/*
# Enter your PyPI credentials when prompted
```

After the first upload, you can restrict the API token scope to just the `reroute` project for better security.

## How It Works

### Automatic Trigger

The workflow triggers automatically when:
- ✅ You push changes to `setup.py` or `pyproject.toml` on the `main` branch
- ✅ The version in `setup.py` is different from the latest Git tag

### Manual Trigger

You can also trigger manually:
1. Go to **Actions** tab in GitHub
2. Select **"Publish to PyPI"** workflow
3. Click **"Run workflow"**
4. Enter version number (e.g., `0.2.0`)
5. Click **"Run workflow"**

## Release Process

### Method 1: Automatic (Recommended)

1. **Update version in `setup.py`**:
   ```python
   setup(
       name="reroute",
       version="0.2.0",  # Update this
       # ... rest of setup
   )
   ```

2. **Update CHANGELOG.md**:
   ```markdown
   ## [Unreleased]

   ### Added
   - New feature XYZ
   - Feature ABC

   ### Fixed
   - Bug in feature XYZ

   ## [0.1.0] - 2025-01-15
   (previous version)
   ```

3. **Commit and push**:
   ```bash
   git add setup.py CHANGELOG.md
   git commit -m "chore: bump version to 0.2.0"
   git push origin main
   ```

4. **GitHub Actions automatically**:
   - Runs all tests
   - Builds the package
   - Creates tag `v0.2.0`
   - Creates GitHub Release
   - Publishes to PyPI
   - Updates CHANGELOG.md with date

### Method 2: Manual

1. **Update version** (same as above)

2. **Trigger workflow manually**:
   - Go to Actions → Publish to PyPI → Run workflow
   - Enter version: `0.2.0`
   - Click "Run workflow"

## Workflow Files

### 1. `publish-pypi.yml` - Main Publishing Workflow

**Triggers:**
- Push to `main` with changes to `setup.py` or `pyproject.toml`
- Manual workflow dispatch

**Jobs:**
- `check-version`: Extracts version, checks if tag exists
- `build-and-publish`: Builds, tags, releases, publishes

**Features:**
- Prevents duplicate releases
- Extracts changelog from CHANGELOG.md
- Creates GitHub Release with artifacts
- Uses PyPI trusted publishing
- Updates CHANGELOG with version date

### 2. `test.yml` - Test Workflow

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests

**Matrix Testing:**
- OS: Ubuntu, Windows, macOS
- Python: 3.8, 3.9, 3.10, 3.11, 3.12

## Version Management

### Semantic Versioning

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (e.g., 1.0.0): Breaking changes
- **MINOR** (e.g., 0.2.0): New features, backward compatible
- **PATCH** (e.g., 0.1.1): Bug fixes, backward compatible

### Version Update Locations

When releasing a new version, update:

1. **`setup.py`** - Line 16:
   ```python
   version="0.2.0",
   ```

2. **`CHANGELOG.md`** - Add unreleased changes:
   ```markdown
   ## [Unreleased]

   ### Added
   - Your new features

   ### Fixed
   - Your bug fixes
   ```

3. **Commit and push** - GitHub Actions handles the rest!

## CHANGELOG Format

Follow [Keep a Changelog](https://keepachangelog.com/):

```markdown
# Changelog

## [Unreleased]

### Added
- New features go here

### Changed
- Changes to existing functionality

### Fixed
- Bug fixes

### Removed
- Removed features

## [0.2.0] - 2025-01-20

### Added
- FastAPI-style parameter injection
- Pydantic model generation CLI
```

## Monitoring

### Check Workflow Status

1. **GitHub Actions**:
   - https://github.com/cbsajan/reroute/actions

2. **View logs**:
   - Click on workflow run
   - View each step's output

### Verify Release

1. **GitHub Release**:
   - https://github.com/cbsajan/reroute/releases

2. **PyPI**:
   - https://pypi.org/project/reroute/

3. **Install from PyPI**:
   ```bash
   pip install reroute==0.2.0
   ```

## Troubleshooting

### Error: "403: Invalid or non-existent authentication information"

**Cause**: PyPI API token is invalid or not set

**Solution**:
1. Verify `PYPI_API_TOKEN` secret exists in GitHub
2. Generate new token if needed
3. Update GitHub secret

### Error: "File already exists"

**Cause**: Version already published to PyPI

**Solution**:
1. Bump version number in `setup.py`
2. Commit and push

### Error: "Tag already exists"

**Cause**: Git tag already created

**Solution**:
1. Delete tag: `git tag -d v0.2.0 && git push origin :refs/tags/v0.2.0`
2. Or bump to new version

### Tests Failing

**Cause**: Tests not passing

**Solution**:
1. Check test output in Actions
2. Fix failing tests
3. Push fixes
4. Workflow will retry

## Security Best Practices

1. **Use API tokens**, not passwords
2. **Scope tokens** to specific projects (after first upload)
3. **Never commit tokens** to repository
4. **Rotate tokens** periodically
5. **Use trusted publishing** (configured in workflow)

## Advanced Configuration

### Skip CI for Commits

Add `[skip ci]` to commit message:
```bash
git commit -m "docs: update README [skip ci]"
```

### Pre-release Versions

For beta/alpha releases:

```python
# setup.py
version="0.2.0b1",  # Beta 1
version="0.2.0rc1",  # Release candidate 1
```

### Custom Build Process

Modify `publish-pypi.yml`:

```yaml
- name: Build package
  run: |
    # Your custom build steps
    python -m build
```

## Quick Reference

### Release Checklist

- [ ] Update version in `setup.py`
- [ ] Add changes to CHANGELOG.md under `[Unreleased]`
- [ ] Run tests locally: `pytest`
- [ ] Commit changes: `git commit -m "chore: bump version to X.Y.Z"`
- [ ] Push to main: `git push origin main`
- [ ] Monitor GitHub Actions workflow
- [ ] Verify GitHub Release created
- [ ] Verify PyPI package published
- [ ] Test installation: `pip install reroute==X.Y.Z`

### Commands

```bash
# Build locally
python -m build

# Test upload to TestPyPI
twine upload --repository testpypi dist/*

# Upload to PyPI manually
twine upload dist/*

# Check workflow status (gh CLI)
gh run list --workflow=publish-pypi.yml

# View workflow logs
gh run view

# Create release manually
gh release create v0.2.0 dist/* --title "Release v0.2.0" --notes "Release notes"
```

## Support

- **GitHub Actions Logs**: https://github.com/cbsajan/reroute/actions
- **PyPI Help**: https://pypi.org/help/
- **Workflow Issues**: Check [GitHub Actions documentation](https://docs.github.com/en/actions)

---

**Last Updated:** 2025-01-XX
**Maintainer:** C B Sajan
