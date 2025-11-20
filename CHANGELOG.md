# Changelog

All notable changes to REROUTE will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

## [0.1.0] - 2024-01-15

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

[unreleased]: https://github.com/cbsajan/reroute/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/cbsajan/reroute/releases/tag/v0.1.0
