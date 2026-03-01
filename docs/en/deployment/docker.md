# Docker Deployment

Containerize your REROUTE application.

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Requirements

`requirements.txt`:
```txt
reroute[fastapi]
uvicorn[standard]
python-dotenv
```

## Build and Run

```bash
# Build image
docker build -t reroute-app .

# Run container
docker run -p 8000:8000 reroute-app
```

## Docker Compose

`docker-compose.yml`:
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REROUTE_PORT=8000
      - REROUTE_DEBUG=False
    volumes:
      - ./app:/app/app
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app
    restart: unless-stopped
```

## Multi-stage Build

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Docker Commands

```bash
# Build
docker-compose build

# Run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Production Tips

- Use multi-stage builds
- Run as non-root user
- Use .dockerignore
- Pin dependency versions
- Enable health checks
- Set resource limits

## .dockerignore

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
.venv
venv/
.git
.gitignore
.pytest_cache
.coverage
*.log
```

## Health Check

Add to Dockerfile:
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1
```
