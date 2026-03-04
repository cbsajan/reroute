# CORS Setup

Configure Cross-Origin Resource Sharing (CORS) for your API.

## Basic Setup

```python
from reroute import Config

class MyConfig(Config):
    ENABLE_CORS = True
    CORS_ALLOW_ORIGINS = ["*"]
```

## Production Configuration

```python
class ProductionConfig(Config):
    ENABLE_CORS = True
    CORS_ALLOW_ORIGINS = [
        "https://yourdomain.com",
        "https://app.yourdomain.com"
    ]
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE"]
    CORS_ALLOW_HEADERS = ["Content-Type", "Authorization"]
    CORS_ALLOW_CREDENTIALS = True
```

## Options

- `ENABLE_CORS` - Enable/disable CORS
- `CORS_ALLOW_ORIGINS` - Allowed origins
- `CORS_ALLOW_METHODS` - Allowed HTTP methods
- `CORS_ALLOW_HEADERS` - Allowed headers
- `CORS_ALLOW_CREDENTIALS` - Allow credentials
- `CORS_MAX_AGE` - Preflight cache duration

## Security Note

Never use `["*"]` for origins in production. Always specify exact domains.
