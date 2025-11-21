# Changelog

All notable changes to REROUTE will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
2. Add OpenAPI config section:
```python
class AppConfig(Config):
    class OpenAPI:
        ENABLE = True
        DOCS_PATH = "/docs"
        REDOC_PATH = None
        JSON_PATH = "/openapi.json"
        TITLE = "My API"
        VERSION = "1.0.0"
        DESCRIPTION = "API Description"
```
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

## [0.1.3] - 2025-11-21

## [0.1.3] - 2025-11-21

### Added
- **Auto-Name Generation** - Intelligent route name generation from paths
  - Automatically generates PascalCase names from route paths (e.g., `/user/profile` → `UserProfile`)
  - Confirmation prompt: accept auto-generated name or provide custom name
  - Smart handling of special cases:
    - Numbers at start: `/123-api` → `Route123Api` (auto-prefix with "Route")
    - Special characters stripped: `/blog-posts` → `BlogPosts`
    - Leading underscores removed: `/_admin` → `Admin`
  - Validation ensures names are valid Python identifiers
  - Applied to both `generate route` and `generate crud` commands

- **Real-Time Input Validation** - Instant feedback as you type
  - Migrated from Click prompts to InquirerPy for all interactive inputs
  - Path validation shows errors immediately while typing (not after Enter)
  - Custom name validation prevents invalid characters in real-time
  - Better user experience with instant feedback

- **Comprehensive Path Validation** - Security and compatibility checks
  - Format: Must start with `/`, cannot end with `/` (except root)
  - Security: No path traversal (`/../`, `/./`)
  - Reserved names: Blocks `/__init__`, `/__pycache__`, `/__main__`
  - Filesystem: No invalid characters (`<>:"|?*`) for Windows compatibility
  - Length limit: Maximum 100 characters to prevent MAX_PATH issues
  - No consecutive slashes (`//`)
  - At least one valid segment required

- **Duplicate Class Name Detection** - Prevents accidental overwrites
  - Checks if class name already exists in `page.py` before creating route
  - Clear error message with actionable guidance
  - Prevents data loss from duplicate route creation

- **Validation Documentation** - Comprehensive reference guide
  - Created `docs/technical/VALIDATION_RULES.md`
  - Documents all validation rules with examples
  - Explains validation timing and error messages
  - Philosophy: fail fast, clear feedback, safe defaults

### Fixed
- **Premature Directory Creation** - Critical bug fix
  - Directories were being created during user prompts (before completion)
  - Now directories only created AFTER all validations pass
  - Applied to both `generate route` and `generate crud` commands
  - Prevents empty folders when user cancels or validation fails

- **Click Prompt Validation** - Fixed callback handling
  - `validate_route_path()` now handles `None` values gracefully
  - Returns `None` early when no value provided (interactive mode)
  - Only validates when path is provided via command-line flag
  - Allows InquirerPy to handle prompting with real-time validation

### Changed
- **Complete InquirerPy Migration** - Unified prompt library
  - Removed all Click `prompt=` parameters across all commands
  - Replaced with InquirerPy prompts with real-time validation
  - Consistent UX across all commands (`init`, `generate route`, `generate crud`, `generate model`)
  - Removed `questionary` dependency completely
  - Updated `setup.py` and `pyproject.toml` dependencies
  - Removed custom questionary styling code
  - Cleaner, more maintainable prompt implementation

- **Validation Helpers** - Code reuse and organization
  - Created `validate_path_realtime()` helper in `helpers.py`
  - Extracted validation logic into reusable functions
  - Consistent validation across all route/CRUD commands
  - Easier to maintain and test

### Internal
- Created helper functions for better code organization:
  - `auto_name_from_path()` - Generate class name from route path
  - `check_class_name_duplicate()` - Check for existing class names
  - `validate_path_realtime()` - Real-time path validation for InquirerPy
  - Enhanced `to_class_name()` - Preserves existing PascalCase
- Directory creation moved to right before file write (after all validations)
- Path calculation done without creating directories for duplicate checking

## [0.1.2] - 2025-11-20

## [0.1.1] - 2025-11-20

### Added
- **Version Display** - CLI version flag support
  - `reroute --version` - Show version and exit
  - `reroute -V` - Short flag for version
  - Dynamic version reading from `__version__`
  - Clean version display format: "REROUTE CLI v0.1.1"

- **Update Notification System** - Automatic update checking
  - Checks PyPI for newer versions once per day
  - Non-blocking and silent on errors
  - Displays update notification when newer version available
  - Shows upgrade command: `pip install --upgrade reroute`
  - Caches check results in `~/.reroute/update_check.json`
  - Smart version comparison (0.1.0 < 0.1.1 < 0.2.0)

- **Modular CLI Architecture** - Improved code organization
  - `reroute/cli/commands/init_command.py` - Project initialization logic
  - `reroute/cli/commands/create_command.py` - Code generation logic (route, crud, model)
  - `reroute/cli/commands/helpers.py` - Shared utility functions
  - `reroute/cli/main.py` - Main CLI entry point
  - Better separation of concerns and maintainability

- **Template Organization** - Structured Jinja2 templates
  - `templates/project/` - Project initialization templates (env.example, gitignore, requirements.txt)
  - `templates/config/` - Configuration templates
  - `templates/app/` - Application templates
  - `templates/routes/` - Route templates
  - `templates/models/` - Model templates
  - `templates/http/` - HTTP test templates
  - `templates/tests/` - Test templates
  - Template README with usage documentation

### Fixed
- **Duplicate Banner Issue** - Removed duplicate CLI banner display
  - Banner was appearing twice (once in group, once in command)
  - Removed banner from `cli()` group function
  - Clean, professional command output

### Changed
- **Info Command** - Temporarily disabled for future implementation
  - Commented out `reroute info` command
  - Added TODO marker for future enhancement
  - Will be re-implemented with more useful features later

### Internal
- Renamed `reroute/cli/commands.py` to `reroute/cli/main.py` to avoid naming conflict with `commands/` package
- Moved `db_commands.py` from `cli/command/` to `cli/commands/`
- Removed old `cli/command/` directory
- Updated all import paths to use new structure

## [Unreleased]

## [0.1.3] - 2025-11-21

## [0.1.2] - 2025-11-20

### Added
- **Parameter Injection System** - FastAPI-style parameter extraction and validation
  - `Query` - URL query parameters with validation (ge, le, min_length, max_length, regex)
  - `Path` - URL path parameters for dynamic routes
  - `Header` - HTTP header extraction (case-insensitive)
  - `Body` - JSON request body with automatic Pydantic model validation
  - `Cookie` - Cookie value extraction
  - `Form` - Form data handling
  - `File` - File upload support
  - Automatic type conversion based on type hints
  - Required vs optional parameter validation
  - Default value support
  - Import: `from reroute.params import Query, Body, Header, Path`

- **Pydantic Model Generation** - CLI command to generate data validation models
  - `reroute generate model` command
  - `reroute create model` command (alias)
  - Auto-generates 5 schemas: Base, Create, Update, InDB, Response
  - Default fields with customization guidance
  - Creates `app/models/` directory structure
  - Template includes field validation examples and TODO comments

- **.env File Support** - Complete environment variable configuration
  - `Config.Env` nested class for environment settings
  - Automatic `.env` file loading with python-dotenv
  - Custom `.env` file paths (`.env.dev`, `.env.prod`, etc.)
  - `DevConfig.Env.file = ".env.dev"` for development
  - `ProdConfig.Env.file = ".env.prod"` for production
  - `Config.load_from_env()` method with optional file path
  - All variables must use `REROUTE_*` prefix
  - Automatic type conversion (bool, int, list, string)
  - Override control with `Env.override` setting

- **Protected Configuration** - Framework-critical settings protection
  - `Config.Internal` nested class for framework internals
  - Protected settings: `ROUTES_DIR_NAME`, `ROUTE_FILE_NAME`, `SUPPORTED_HTTP_METHODS`, etc.
  - `__init_subclass__` hook prevents modification in child classes
  - Clear separation between framework internals and user configuration
  - TypeError raised immediately if Internal class is overridden

- **Examples and Documentation**
  - Complete parameter injection example (`examples/parameter_injection/`)
  - User CRUD API demonstrating all parameter types
  - 21 HTTP test cases in `.http` file
  - Example `.env` configuration file
  - Pydantic models for request/response validation

### Fixed
- **Nested Route Discovery** - Routes now support unlimited nesting depth
  - Changed from `iterdir()` to `rglob()` for recursive scanning
  - Routes like `/users/me/profile` now properly discovered
  - All nested `page.py` files automatically detected
  - Path parameters correctly handled in nested structures

- **Import Organization** - Cleaner, more maintainable import structure
  - Decorators moved to `reroute.decorators` module
  - Parameters moved to `reroute.params` module
  - Root `__init__.py` exports only essentials for minimal setup
  - Updated CLI templates to use organized imports
  - Fixed route file imports (`from reroute.decorators import rate_limit, cache`)

- **Template Updates**
  - `class_route.py.j2` - Updated imports to use `reroute.decorators`
  - `crud_route.py.j2` - Cleaner import structure
  - `model.py.j2` - New template for Pydantic models

### Changed
- **Configuration Structure** - Reorganized for clarity and protection
  - User-configurable settings remain at top level (`DEBUG`, `PORT`, etc.)
  - Framework internals moved to `Config.Internal`
  - Environment settings in `Config.Env`
  - All internal references updated to `config.Internal.*`
  - Better separation of concerns

- **Environment Variable Loading**
  - All env vars must have `REROUTE_*` prefix
  - Old: `DEBUG=true` → New: `REROUTE_DEBUG=true`
  - More consistent and avoids naming conflicts
  - Clear namespace for framework configuration

- **FastAPI Adapter** - Enhanced with parameter injection
  - `_extract_request_data()` method for parameter extraction
  - Signature introspection to identify parameter types
  - Automatic parameter injection into route handlers
  - Support for Pydantic model instantiation from request bodies

### Tests
- Added `test_params.py` - 9 tests for parameter injection classes
- Added `test_adapter_params.py` - 7 tests for adapter parameter extraction
- Added `test_config_env.py` - 9 tests for .env loading and Config.Internal protection
- All tests passing (25 new tests total)

## [0.1.0] - 2025-11-19

### Added
- Initial release of REROUTE framework
- File-based routing system inspired by Next.js
- Class-based route handlers with `RouteBase`
- FastAPI adapter with full integration
- Lifecycle hooks: `before_request`, `after_request`, `on_error`
- Interactive CLI with beautiful prompts (powered by Click and Questionary)
- Project scaffolding: `reroute init`
- Route generation: `reroute generate route`
- CRUD route generation: `reroute generate crud`
- Jinja2-based code templates
- Configuration system with `Config`, `DevConfig`, `ProdConfig`
- API base path support for versioning (e.g., `/api/v1`)
- Decorator system:
  - `@rate_limit("3/min")` - Rate limiting
  - `@cache(duration=60)` - Response caching
  - `@requires("admin")` - Authentication/authorization
  - `@validate(schema={...})` - Request validation
  - `@timeout(5)` - Request timeout
  - `@log_requests()` - Request logging
- Global CORS configuration via middleware
- Swagger/OpenAPI tag support (auto-generated from folder names or custom)
- Logging utilities with standard Python logging
- Auto-generated logger configuration per project
- Port availability checking before server start
- Custom server runner with `run_server()`
- Test case generation with pytest templates
- HTTP test file generation (.http files)
- Configuration review step in project initialization
- Colored CLI output with custom questionary styling
- Default port: 7376
- Complete documentation (README, COMMANDS, CONTRIBUTING, PUBLISHING)

### Framework Features
- Zero-configuration file-based routing
- Automatic route discovery from folder structure
- Class-based routes with method handlers (GET, POST, PUT, DELETE, etc.)
- Framework adapter pattern (FastAPI implemented, Flask planned)
- Thread-safe rate limiting and caching
- Metadata storage on decorators for introspection

### Developer Experience
- Beautiful interactive CLI with arrow-key navigation
- Project name validation
- Colored terminal output
- Configuration preview before project creation
- Comprehensive error messages
- Auto-generated test cases
- HTTP test files for manual testing

### Documentation
- Complete README with examples
- CLI commands reference (COMMANDS.md)
- Contributing guidelines (CONTRIBUTING.md)
- Publishing guide (PUBLISHING.md)
- Inline code documentation
- Template comments and examples

[unreleased]: https://github.com/cbsajan/reroute/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/cbsajan/reroute/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/cbsajan/reroute/releases/tag/v0.1.0

[unreleased]: https://github.com/cbsajan/reroute/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/cbsajan/reroute/compare/v...v0.1.2

[unreleased]: https://github.com/cbsajan/reroute/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/cbsajan/reroute/compare/v...v0.1.3
