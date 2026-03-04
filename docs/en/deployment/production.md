# Production Deployment

Deploy REROUTE applications to production.

## Production Configuration

```python
from reroute import Config

class ProductionConfig(Config):
    DEBUG = False
    PORT = 8000
    HOST = "0.0.0.0"

    # CORS
    ENABLE_CORS = True
    CORS_ALLOW_ORIGINS = ["https://yourdomain.com"]

    # Logging
    VERBOSE_LOGGING = True
    LOG_LEVEL = "WARNING"
```

## Environment Variables

`.env`:
```bash
REROUTE_PORT=8000
REROUTE_HOST=0.0.0.0
REROUTE_DEBUG=False
REROUTE_CORS_ORIGINS=https://yourdomain.com
```

Load in your app:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Using Uvicorn (FastAPI)

```bash
# Production server
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --no-access-log
```

## Using Gunicorn

```bash
# With Uvicorn workers
gunicorn main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8000
```

## Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Systemd Service

`/etc/systemd/system/reroute-app.service`:
```ini
[Unit]
Description=REROUTE Application
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/app
ExecStart=/usr/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable reroute-app
sudo systemctl start reroute-app
```

## Security Checklist

- [ ] Set DEBUG = False
- [ ] Use HTTPS
- [ ] Configure proper CORS origins
- [ ] Set rate limiting
- [ ] Enable logging
- [ ] Use environment variables for secrets
- [ ] Set up monitoring
- [ ] Configure firewall
- [ ] Use reverse proxy (Nginx/Apache)
- [ ] Implement authentication

## Monitoring

Use tools like:
- Prometheus + Grafana
- Sentry for error tracking
- Datadog
- New Relic

## Performance

- Use multiple workers
- Enable caching
- Use CDN for static files
- Optimize database queries
- Enable compression
