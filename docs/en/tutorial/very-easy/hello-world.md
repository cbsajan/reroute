---
difficulty: very easy
time: 5 minutes
prerequisites:
  - link: ../../start-here.md
next: first-server.md
---

# Hello World

Create your first REROUTE API in just 5 minutes!

## What You'll Learn

- How to create a new REROUTE project
- Basic project structure
- Your first API endpoint
- How to test your API

## Prerequisites

- Python 3.8+ installed
- REROUTE installed (`pip install reroute[fastapi]`)
- Basic command line knowledge

---

## Watch the Video Demo

!!! tip "Visual Learner?"
    Prefer watching? Here's a 2-minute video showing the complete process:

    <video width="100%" height="auto" controls style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <source src="https://github.com/cbsajan/reroute/raw/refs/heads/main/assets/demo.mp4" type="video/mp4">
        Your browser does not support the video tag.
    </video>

    **[Download video](https://github.com/cbsajan/reroute/raw/refs/heads/main/assets/demo.mp4)** | **[Watch on GitHub](https://github.com/cbsajan/reroute/blob/main/reroute/assets/demo.mp4)**

    *Video covers: Project initialization, first API endpoint, and testing with Swagger UI*

---

## Step 1: Create a New Project

Use the REROUTE CLI to create a new project:

```bash
reroute init hello-world --framework fastapi
```

You'll be prompted with a few questions. Answer "No" to tests and database for now.

The CLI will create your project structure:

```
hello-world/
├── app/
│   ├── routes/
│   │   └── hello/
│   │       └── page.py
│   ├── root.py
│   └── __init__.py
├── config.py
├── logger.py
├── main.py
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## Step 2: Navigate to Your Project

```bash
cd hello-world
```

---

## Step 3: Install Dependencies

### Using uv (recommended):

```bash
uv venv
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

uv sync
```

### Using pip:

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

---

## Step 4: Run Your Server

```bash
python main.py
```

You should see:

```
==================================================
REROUTE Server Starting
==================================================
  Framework: FastAPI
  Host: 0.0.0.0
  Port: 7376
  Docs: /docs
==================================================

INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:7376
```

---

## Step 5: Test Your API

Open your browser or use curl to test your endpoints:

### Root Endpoint

```bash
curl http://localhost:7376/
```

**Expected Output:**
```json
{
  "message": "Welcome to hello-world API",
  "docs": "/docs",
  "health": "/health"
}
```

### Hello Endpoint

```bash
curl http://localhost:7376/hello
```

**Expected Output:**
```json
{
  "message": "Hello, World!"
}
```

### Health Check

```bash
curl http://localhost:7376/health
```

**Expected Output:**
```json
{
  "status": "healthy",
  "service": "hello-world"
}
```

---

## Step 6: View API Documentation

Open your browser and navigate to:

**Swagger UI:** http://localhost:7376/docs

You'll see interactive API documentation where you can test all your endpoints!

---

## Understanding Your Code

### main.py

```python
from fastapi import FastAPI
from reroute import FastAPIAdapter
from config import AppConfig

app = FastAPI(title="hello-world")
adapter = FastAPIAdapter(
    fastapi_app=app,
    app_dir="./app",
    config=AppConfig
)
adapter.register_routes()

if __name__ == "__main__":
    adapter.run_server()
```

**What's happening:**
1. Create a FastAPI app
2. Initialize REROUTE adapter with the app
3. Register all routes from `app/routes/` directory
4. Start the server

### app/root.py

```python
from fastapi import Request
from reroute import RouteBase

class RootRoutes(RouteBase):
    """Root and health check endpoints."""

    def get(self, request: Request):
        """Root endpoint with welcome message."""
        return {
            "message": f"Welcome to {request.app.title} API",
            "docs": "/docs",
            "health": "/health"
        }

def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "hello-world"}
```

### app/routes/hello/page.py

```python
from reroute import RouteBase

class HelloRoutes(RouteBase):
    """Hello World endpoint."""

    def get(self):
        """Return hello message."""
        return {"message": "Hello, World!"}
```

---

## File-Based Routing

REROUTE uses file-based routing inspired by Next.js:

```
app/routes/
    ├── page.py              → /
    ├── users/
    │   └── page.py          → /users
    └── posts/
        ├── page.py          → /posts
        └── [id]/
            └── page.py      → /posts/{id}
```

**Key concepts:**
- `page.py` files become routes
- Folder names become URL paths
- Class methods (get, post, etc.) handle HTTP methods

---

## Troubleshooting

### Port Already in Use

**Error:** `OSError: [Errno 48] Address already in use`

**Solution:**
1. Change port in `config.py`: `PORT = 8080`
2. Or kill the process using port 7376

### Module Not Found

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
pip install -r requirements.txt
```

### Routes Not Working

**Check:**
1. File is named `page.py` (not `routes.py` or other)
2. Class inherits from `RouteBase`
3. At least one HTTP method defined (get, post, etc.)

---

## Next Steps

Congratulations! You've created your first REROUTE API!

**What's next:**
- [First Server](first-server.md) - Learn more about running the server
- [Understanding Routes](understanding-routes.md) - Deep dive into file-based routing
- [Dynamic Routes](../easy/dynamic-routes.md) - Work with path parameters

---

## Summary

In just 5 minutes, you:
- Created a new REROUTE project
- Understood the basic project structure
- Ran your development server
- Tested your API endpoints
- Viewed interactive API documentation

**Key takeaways:**
- REROUTE uses file-based routing
- `page.py` files become API endpoints
- Class methods handle HTTP methods
- Swagger UI documentation is automatic

Ready to learn more? Continue to [First Server](first-server.md)!
