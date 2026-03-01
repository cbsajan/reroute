# Changelog

All notable changes to REROUTE are documented here.

## [0.2.4] - 2026-01-03

### Fixed
- **CRITICAL: CLI import error** - Fixed `ModuleNotFoundError` caused by `utils.py` shadowing `utils/` package
- Renamed `cli/utils.py` to `cli/cli_utils.py` to resolve package conflict
- **CI environment detection** - GitHub Actions no longer incorrectly detected as production
- **Python 3.8 compatibility** - Added future annotations for type hint support

---

## [0.2.3] - 2026-01-03

### Fixed
- **SecurityHeadersConfig attribute error** - Fixed `hsts.max_age` access to use flat attribute `hsts_max_age`
- **security_logger undefined** - Fixed missing import in `cli/utils/security.py`
- **CSP methods don't exist** - Fixed to use `get_directive().add_source()` pattern
- **Path containment security bug** - Fixed RouteLoader path validation for proper ancestry checking
- **Test assertion failures** - Fixed validation error messages and mock patch paths
- **Testing environment permissions** - Fixed RouteLoader to allow temp directories in testing

### Changed
- Improved path security with proper ancestry checking
- Enhanced error messages for validation failures

---

## [0.2.2] - 2026-01-02

### Added

#### Animated Terminal Documentation
- **Termynal.js integration** - Animated terminal effect like FastAPI documentation
- **Custom.js initialization** - Lazy loading for terminals on scroll

#### Documentation Versioning
- **Mike-based versioning** - Major version docs (0.1, 0.2) with "latest" alias
- **Version selector** - Dropdown in header to switch between versions
- **Auto-deployment** - Docs deploy automatically on PyPI release
- **Cross-repo trigger** - Main repo release triggers docs deployment

### Changed
- **Deploy workflow** - Now triggered by PyPI release instead of push to main
- **README updates** - Both repos updated with new workflow documentation

### Fixed
- **Terminal output** - Now matches actual CLI output exactly
- **Header animation** - Fixed REROUTE brand name staying constant (not animated)
- **versions.json 404** - Added placeholder for local development

---

## [0.2.1] - 2026-01-02

### Added

#### Comprehensive Security Headers
- **OWASP-compliant security headers** - Automatic CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, and more
- **SecurityHeadersConfig** - Flexible configuration class for security headers
- **SecurityHeadersFactory** - Factory methods for common use cases (SPA, API-only, static site)
- **Environment detection** - Automatic development/production/testing detection
- **Framework integration** - Security middleware for both FastAPI and Flask adapters

#### Documentation Overhaul
- **FastAPI-style documentation** - Complete restructure following FastAPI documentation patterns
- **Deep Blue theme** - Custom theme matching REROUTE logo colors
- **Styled terminal examples** - Professional terminal output styling for CLI commands
- **FastAPI-style navigation** - Learn / Reference / Examples / About structure
- **Version selector** - Documentation versioning with mike support
- **Announcement bar** - Release announcements at the top of docs

### Changed
- **Theme colors** - Updated from indigo to Deep Blue (#17469E) matching REROUTE logo
- **Navigation structure** - Reorganized to match FastAPI documentation pattern
- **Version references** - All documentation updated to reflect v0.2.1

### Fixed
- **Flask support claim** - Documentation now correctly shows Flask as fully supported
- **Incomplete examples** - Fixed undefined method references in lifecycle hooks documentation
- **Emoji removal** - Removed unprofessional emojis from documentation

---

## [0.1.4] - 2025-11-21

### Added

#### Flask Adapter - OpenAPI Support
- **Spectree Integration** - Automatic OpenAPI documentation with Swagger UI and Scalar UI
- **Dynamic HTTP Method Decorators** - `@adapter.get()`, `@adapter.post()`, `@adapter.put()`, `@adapter.patch()`, `@adapter.delete()`, `@adapter.head()`, `@adapter.options()`, `@adapter.route()`
- **Request/Response Validation** - Automatic validation using Pydantic models via Spectree
- **Documentation UIs**:
  - Swagger UI at `/swagger/`
  - Scalar UI at `/scalar/`
  - OpenAPI JSON at `/openapi.json`
  - ReDoc disabled (broken CDN URL)

#### FastAPI Adapter Enhancements
- **Auto-Reload Detection** - Automatically constructs import string (`main:app`) for uvicorn reload mode
- **Route Removal for Disabled Endpoints** - Properly removes routes when OpenAPI paths set to `None`
- **Explicit None Handling** - Ensures empty strings treated as `None` for OpenAPI paths

#### Configuration
- **OpenAPI Configuration Section**:
  - `OpenAPI.ENABLE` - Enable/disable documentation
  - `OpenAPI.DOCS_PATH` - Swagger UI endpoint (set to `None` to disable)
  - `OpenAPI.REDOC_PATH` - ReDoc endpoint (Flask: `None`, FastAPI: `"/redoc"`)
  - `OpenAPI.JSON_PATH` - OpenAPI JSON spec endpoint
  - `OpenAPI.TITLE` - API title (auto-generated if `None`)
  - `OpenAPI.VERSION` - API version
  - `OpenAPI.DESCRIPTION` - API description (auto-generated if `None`)

#### Parameter Override Support
- **Runtime Configuration** - `run_server()` kwargs override config values
- **Enhanced Documentation** - Comprehensive docstrings with available parameters

### Changed

#### Flask
- **Documentation URLs**:
  - Swagger UI: `/swagger/` (not `/docs`)
  - Scalar UI: `/scalar/` (new)
  - ReDoc: Disabled
- **Decorator Syntax**: Use `@adapter.get()` instead of `@adapter.app.get()`
- **Spectree Registration**: Happens automatically after `register_routes()`

#### FastAPI
- **Parameter Precedence**: Config defaults, kwargs override
- **Startup Messages**: Only show enabled documentation endpoints

#### Dependencies
- Added `spectree>=1.2.0` to Flask extras
- Added `colorama>=0.4.0` for Windows console colors

### Fixed
- Flask parameter override in `run_server()`
- FastAPI parameter override in `run_server()`
- FastAPI ReDoc disable (`REDOC_PATH = None` now removes route completely)
- Colorama initialization for Windows
- Uvicorn reload warning ("must pass application as import string")

### Migration Guide

#### Flask Projects
1. Install: `pip install spectree flask-cors`
2. Add OpenAPI config section
3. Update syntax: `@adapter.app.get()` → `@adapter.get()`
4. Update URLs: `/docs` → `/swagger/`

#### FastAPI Projects
1. Add OpenAPI config (if missing)
2. Optional: Set `REDOC_PATH = None` to disable ReDoc
3. Use parameter overrides: `adapter.run_server(port=8080)`

### Breaking Changes
- **Flask**: Must use `@adapter.get()` instead of `@adapter.app.get()`
- **Flask**: Documentation moved to `/swagger/` and `/scalar/`
- **Configuration**: Must add `OpenAPI` nested class

---

## [0.1.7] - 2025-11-28

### Security Enhancements

#### Column-Validated Database Queries
- **Enhanced**: `Model.get_all()` now includes built-in column validation for `order_by` parameter
- Uses SQLAlchemy's `inspect().mapper.column_attrs` for validation
- Provides helpful error messages listing valid column names
- **Test Coverage**: 4 test cases

#### Input-Validated CLI Commands
- **Enhanced**: All CLI commands now include comprehensive input validation
- `reroute db downgrade --steps` validates as positive integer (1-100)
- Clear error messages for invalid inputs
- **Test Coverage**: 5 test cases

#### Bounded Cache with LRU Eviction
- **Enhanced**: `@cache` decorator now includes automatic memory management
- Maximum cache size: 1000 entries
- LRU (Least Recently Used) eviction strategy
- Background cleanup every 60 seconds
- Full error logging for observability
- **Test Coverage**: 4 test cases

#### Fail-Safe Authorization
- **Enhanced**: `@requires` decorator implements fail-safe authorization pattern
- Access denied by default unless explicitly granted
- Proper HTTP status codes: 401 (auth), 403 (authz), 500 (config error)
- Integrated error logging
- **Breaking Change**: `@requires("role")` now requires explicit `check_func` parameter
- **Test Coverage**: 7 test cases

### Added

#### Security Logging (OWASP A09)
- **New**: `SecurityLogger` class for structured security event logging
- JSON-formatted output for SIEM integration
- Automatic sensitive data redaction (passwords, tokens, API keys)
- Security event types: AUTH_SUCCESS, AUTH_FAILURE, AUTHZ_FAILURE, RATE_LIMIT_EXCEEDED, etc.
- Integrated with `@rate_limit` and `@requires` decorators

#### Health Check Endpoint
- **New**: Built-in `/health` endpoint for monitoring and load balancers
- Configurable via `HEALTH_CHECK_ENABLED` and `HEALTH_CHECK_PATH`
- Returns service status, name, and version in JSON format
- Automatically registered with FastAPI and Flask adapters

#### Error Response Helper
- **New**: `error_response()` helper function in decorators module
- Consistent error response formatting across the application
- Supports custom error types and detailed messages

### Enhanced
- **Rate Limiter**: Added bounded storage with LRU eviction (max 10,000 keys)
- **Cache**: Thread-safe operations with double-checked locking
- **Decorators**: Added `__all__` exports for cleaner imports

### Test Suite
- Comprehensive security test suite (`tests/test_security_fixes.py`)
- 27 test cases covering security features
- Integration tests and platform-specific edge cases

### Documentation
- Added "Security Logging (OWASP A09)" section to security guide
- Updated security best practices with new feature examples
- Added Health Check configuration documentation

### Breaking Changes
- **@requires decorator**: Now requires explicit `check_func` parameter when roles are specified
  - Migration: Add `check_func` parameter with your authorization logic

---

## [Unreleased]

### Documentation
- **BREAKING**: Fixed incorrect decorator imports throughout documentation
  - Changed `from reroute import rate_limit, cache` to `from reroute.decorators import`
  - Affects: quickstart, API reference, guides, and all examples
- Updated quickstart guide to use CLI commands instead of manual file creation
  - Replaced `mkdir` commands with `reroute init`
  - Replaced manual code writing with `reroute create route`
  - Reduced setup time from 5 minutes to 2 minutes
- Added warnings for unimplemented decorators (`@requires`, `@validate`, `@timeout`)
- Created IMPLEMENTATION_STATUS.md tracking file for feature accuracy

### Fixed
- Documentation now accurately reflects actual REROUTE features
- Removed fake features and methods from examples
- Corrected import statements across all documentation pages

## [0.1.2] - 2025-11-20

### Added
- Lazy imports for optional framework dependencies
- Automatic update notifications in CLI (`reroute --version`)
- Clear error messages for missing framework dependencies

### Changed
- Optimized CI/CD pipeline (15 → 8 test jobs, 47% faster)
- Improved GitHub Actions workflow error handling

### Fixed
- Module import errors for optional dependencies
- Version consistency across configuration files
- GitHub Release 403 authorization errors

## [0.1.1] - 20-11-2025

### Added
- Version display with `--version` and `-V` flags
- Modular CLI architecture

### Fixed
- Duplicate banner display in CLI
- Unicode compatibility for Windows
- pyproject.toml license format

## [0.1.0] - 19-11-2025

### Added
- Initial release
- File-based routing
- FastAPI and Flask adapters
- Built-in decorators (`@rate_limit`, `@cache`, etc.)
- CLI for project scaffolding
- Configuration system
- Parameter injection
- Lifecycle hooks

---

[View full changelog on GitHub](https://github.com/cbsajan/reroute/blob/main/CHANGELOG.md)
