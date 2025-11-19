# Changelog

All notable changes to REROUTE will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
