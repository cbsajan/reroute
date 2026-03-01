# Deployment

Deploy your REROUTE applications to production.

## Deployment Options

<div class="grid cards" markdown>

-   :material-server: [**Production Setup**](production.md)

    ---

    Best practices for production deployment

-   :material-docker: [**Docker**](docker.md)

    ---

    Containerize your REROUTE app

</div>

## Quick Start

### Production Checklist

- [ ] Set `DEBUG = False` in configuration
- [ ] Configure proper CORS origins
- [ ] Set up rate limiting
- [ ] Enable logging
- [ ] Use HTTPS
- [ ] Set secure headers
- [ ] Configure environment variables
- [ ] Set up monitoring

### Environment Variables

```bash
# .env
REROUTE_PORT=8000
REROUTE_HOST=0.0.0.0
REROUTE_DEBUG=False
REROUTE_CORS_ORIGINS=https://yourdomain.com
```

### Production Configuration

```python
from reroute import Config

class ProductionConfig(Config):
    DEBUG = False
    PORT = 8000
    HOST = "0.0.0.0"
    ENABLE_CORS = True
    CORS_ALLOW_ORIGINS = ["https://yourdomain.com"]
    VERBOSE_LOGGING = True
```

## Deployment Platforms

### Using Uvicorn (FastAPI)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Gunicorn (Flask)

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Cloud Platforms

REROUTE works with all major cloud platforms:

- **AWS** - Elastic Beanstalk, ECS, Lambda
- **Google Cloud** - Cloud Run, App Engine
- **Azure** - App Service, Container Instances
- **Heroku** - Direct deployment
- **DigitalOcean** - App Platform
- **Railway** - One-click deployment
- **Render** - Automatic deployments

## Learn More

- [Production Guide](production.md) - Detailed production setup
- [Docker Guide](docker.md) - Containerization and orchestration
