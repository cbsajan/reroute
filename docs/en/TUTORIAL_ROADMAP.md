# Tutorial Roadmap

This document tracks planned tutorial content for future releases.

## Hard Level Tutorials (45-60 minutes each)

### 1. Authentication
**Status:** Planned
**Priority:** High
**Topics:**
- JWT token authentication
- API key authentication
- OAuth2 integration
- Password hashing with bcrypt
- Session management
- Protected routes
- Refresh token rotation
- Logout implementation

**Prerequisites:**
- Medium level tutorials completed
- Basic understanding of HTTP headers

**Files to Create:**
- `docs/en/tutorial/hard/authentication.md`
- Example routes with auth decorators
- JWT utilities

---

### 2. Database Integration
**Status:** Planned
**Priority:** High
**Topics:**
- SQLAlchemy setup and models
- Database connection pooling
- CRUD with database
- Migrations with Alembic
- Tortoise ORM integration
- PostgreSQL integration
- MySQL integration
- MongoDB integration
- Database testing with fixtures

**Prerequisites:**
- Medium level tutorials completed
- Understanding of SQL basics

**Files to Create:**
- `docs/en/tutorial/hard/database-integration.md`
- Database model examples
- Migration scripts

---

### 3. WebSockets
**Status:** Planned
**Priority:** Medium
**Topics:**
- WebSocket connection management
- Real-time bidirectional communication
- Broadcasting to all clients
- Group/room messaging
- Connection lifecycle (connect, message, disconnect)
- WebSocket authentication
- Error handling in WebSockets
- Scaling WebSockets with Redis

**Prerequisites:**
- Medium level tutorials completed
- Understanding of async/await

**Files to Create:**
- `docs/en/tutorial/hard/websockets.md`
- WebSocket route examples
- Connection manager implementation

---

## Difficult Level Tutorials (60+ minutes each)

### 1. Production Deployment
**Status:** Planned
**Priority:** High
**Topics:**
- Docker containerization
- Docker Compose for multi-service apps
- Cloud deployment platforms:
  - Railway
  - Render
  - AWS (ECS, Lambda)
  - Google Cloud Run
  - Azure App Service
- Environment variable management
- CI/CD with GitHub Actions
- Health checks and monitoring
- Logging and observability
- Backup strategies

**Prerequisites:**
- Hard level tutorials completed
- Basic Docker knowledge

**Files to Create:**
- `docs/en/tutorial/difficult/production-deployment.md`
- Dockerfile examples
- docker-compose.yml examples
- GitHub Actions workflow templates

---

### 2. Performance Optimization
**Status:** Planned
**Priority:** Medium
**Topics:**
- Caching strategies:
  - Redis caching
  - In-memory caching
  - HTTP caching headers
- Database query optimization
- Connection pooling
- Async vs sync performance
- Load testing with Locust
- Profiling and bottlenecks
- N+1 query problems
- Database indexing
- CDN integration for static assets

**Prerequisites:**
- Database Integration tutorial
- Production Deployment tutorial

**Files to Create:**
- `docs/en/tutorial/difficult/performance-optimization.md`
- Caching decorator examples
- Performance test scripts

---

### 3. Security Hardening
**Status:** Planned
**Priority:** High
**Topics:**
- OWASP Top 10 mitigation
- CORS configuration
- Rate limiting (per IP, per user)
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection
- Secure headers implementation
- Secret management (environment variables, vaults)
- Dependency scanning
- Security testing with OWASP ZAP
- Penetration testing basics

**Prerequisites:**
- Authentication tutorial
- Production Deployment tutorial

**Files to Create:**
- `docs/en/tutorial/difficult/security-hardening.md`
- Security configuration examples
- Rate limiting decorators
- Security test scripts

---

## Implementation Priority

### Phase 1 (v0.4.0) - Core Auth & Database
1. Authentication tutorial
2. Database Integration tutorial

### Phase 2 (v0.5.0) - Real-time Features
3. WebSockets tutorial

### Phase 3 (v0.6.0) - Production Ready
4. Production Deployment tutorial
5. Security Hardening tutorial

### Phase 4 (v0.7.0) - Advanced Performance
6. Performance Optimization tutorial

---

## Contribution Guidelines

Want to help create these tutorials?

1. **Choose a topic** from the roadmap
2. **Check the template** in existing tutorials for structure
3. **Include all sections**:
   - Difficulty/Time/Prerequisites/Next metadata
   - What You'll Learn
   - Step-by-step instructions
   - Code examples that work
   - Expected output
   - Troubleshooting section
   - Next Steps
4. **Test your tutorial** by following it exactly
5. **Submit PR** with clear description

---

## Notes

- All tutorials should follow the progressive learning model
- Each tutorial must build on previous ones
- Code examples must be tested and working
- Include video demonstrations where helpful
- Add `.http` test files for API testing
- Provide both beginner and advanced patterns

---

**Last Updated:** 2025-03-04
**Version:** 0.3.0