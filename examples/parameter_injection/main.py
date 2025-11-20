"""
Parameter Injection Example

Demonstrates REROUTE's FastAPI-style parameter injection with:
- Query parameters (limit, offset, search, sort_by)
- Body parameters (Pydantic models)
- Header parameters (Authorization)
- Cookie parameters (session management)
- Form parameters (form data)

Run with: python main.py
Then open: http://localhost:7376/docs
"""

from fastapi import FastAPI
from reroute import FastAPIAdapter, DevConfig

# Create FastAPI app
app = FastAPI(
    title="REROUTE Parameter Injection Example",
    description="Demonstrates all types of parameter injection in REROUTE",
    version="1.0.0"
)

# Configure REROUTE
class Config(DevConfig):
    """Custom configuration for this example"""
    PORT = 7376
    VERBOSE_LOGGING = True
    ENABLE_CORS = True

# Create REROUTE adapter
adapter = FastAPIAdapter(
    fastapi_app=app,
    app_dir="./app",  # Points to directory containing routes/
    config=Config
)

# Register REROUTE routes
adapter.register_routes()

if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*60)
    print("REROUTE Parameter Injection Example")
    print("="*60)
    print(f"\nServer running at: http://localhost:{Config.PORT}")
    print(f"Swagger UI: http://localhost:{Config.PORT}/docs")
    print(f"ReDoc: http://localhost:{Config.PORT}/redoc")
    print("\nPress CTRL+C to stop\n")

    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.RELOAD
    )
