# Tutorial

Welcome to the REROUTE tutorial! This progressive learning path takes you from beginner to advanced, with hands-on examples at every step.

## Tutorial Structure

The tutorial is organized by difficulty level:

### Very Easy (5-10 minutes each)
Perfect for complete beginners. Get your first API running quickly.

- [Hello World](very-easy/hello-world.md) - Your first API in 5 minutes
- [First Server](very-easy/first-server.md) - Running the development server
- [Understanding Routes](very-easy/understanding-routes.md) - How file-based routing works

### Easy (15-20 minutes each)
Build on the basics with common API patterns.

- [Dynamic Routes](easy/dynamic-routes.md) - Working with path parameters
- [HTTP Methods](easy/http-methods.md) - GET, POST, PUT, DELETE
- [Query Parameters](easy/query-params.md) - Request query strings

### Medium (30-45 minutes each)
Real-world applications with more complexity.

- [CRUD Application](medium/crud-app.md) - Full Create, Read, Update, Delete
- [Decorators Intro](medium/decorators-intro.md) - Rate limiting, caching, validation
- [Error Handling](medium/error-handling.md) - Custom error responses

### Hard (45-60 minutes each)
Advanced features for production applications.

Coming soon:
- Authentication - JWT tokens and API keys
- Database Integration - SQLAlchemy models
- WebSockets - Real-time communication

### Difficult (60+ minutes each)
Production-ready implementations.

Coming soon:
- Production Deployment - Docker, cloud hosting
- Performance Optimization - Caching strategies
- Security Hardening - OWASP compliance

---

## How to Use This Tutorial

### Progressive Learning

Each tutorial builds on previous ones. We recommend starting at the beginning and working through sequentially.

### Hands-On Approach

Every tutorial includes:
- Working code examples you can copy and run
- Expected output so you know if it's working
- Troubleshooting sections for common issues
- "Next steps" to continue your learning

### Difficulty Indicators

Each tutorial page shows:
- **Difficulty:** Very Easy | Easy | Medium | Hard | Difficult
- **Time:** Estimated completion time
- **Prerequisites:** What you need to know first
- **Next:** What to learn after this tutorial

---

## Before You Start

### Prerequisites

- Python 3.8 or higher
- Basic Python knowledge (functions, classes)
- Text editor or IDE (VS Code, PyCharm, etc.)
- Command line/terminal basics

### Installation

If you haven't installed REROUTE yet:

```bash
pip install reroute[fastapi]
```

Or with uv (faster):

```bash
uv pip install reroute[fastapi]
```

Need help? See [Installation Troubleshooting](../troubleshooting/installation.md).

### Verification

Check your installation:

```bash
python -c "import reroute; print(reroute.__version__)"
```

You should see version information printed.

---

## Your First Tutorial

Ready to start? Jump into [Hello World](very-easy/hello-world.md) and build your first REROUTE API in 5 minutes!

---

## Learning Path Summary

```
Start Here → Very Easy → Easy → Medium → Hard → Difficult
   ↓            ↓          ↓        ↓        ↓         ↓
Quiz       Hello World  Dynamic   CRUD    Auth    Production
           First Server Routes           WebSockets   Docker
           File Routes HTTP Methods     Database     Security
```

Each step builds on the previous, so you'll always be building on solid foundations.

---

## Need Help?

- **Stuck on installation?** [Installation Troubleshooting](../troubleshooting/installation.md)
- **General issues?** [Troubleshooting Guide](../guides/troubleshooting.md)
- **Want to ask questions?** [GitHub Discussions](https://github.com/cbsajan/reroute/discussions)

---

## Let's Get Started!

Choose your starting point:

1. **Complete Beginner** → Start with [Hello World](very-easy/hello-world.md)
2. **Some Experience** → Jump to [Dynamic Routes](easy/dynamic-routes.md)
3. **Know the Basics** → Go to [CRUD Application](medium/crud-app.md)
4. **Production Ready** → Explore the [Guides](../guides/index.md) section

Happy coding!
