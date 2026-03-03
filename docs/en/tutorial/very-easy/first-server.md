---
difficulty: very easy
time: 5 minutes
prerequisites:
  - link: hello-world.md
next: understanding-routes.md
---

# First Server

Learn how to run and customize your REROUTE development server.

## What You'll Learn

- How to start the development server
- Server configuration options
- Auto-reload for development
- Hot-reloading changes

## Prerequisites

- Completed [Hello World](hello-world.md) tutorial
- Basic understanding of terminal/command line

---

## Starting the Server

### Basic Start

Navigate to your project and run:

```bash
python main.py
```

Your server will start on the configured host and port (default: `http://localhost:7376`)

---

## Configuration Options

### Using config.py

Edit `config.py` to change default settings:

```python
from reroute import Config

class AppConfig(Config):
    # Server Configuration
    HOST = "127.0.0.1"    # Listen on localhost only
    PORT = 8080            # Use port 8080
    DEBUG = True           # Enable debug mode
    AUTO_RELOAD = True     # Auto-reload on file changes
```

### Using Command Line (Override)

Override config values when starting the server:

```python
# main.py
if __name__ == "__main__":
    adapter.run_server(
        host="127.0.0.1",  # Override HOST
        port=8080,         # Override PORT
        reload=True        # Override AUTO_RELOAD
    )
```

---

## Auto-Reload (Hot Reloading)

Auto-reload automatically restarts the server when you save file changes.

### Enable Auto-Reload

**In config.py:**
```python
class AppConfig(Config):
    AUTO_RELOAD = True
```

**Or in main.py:**
```python
adapter.run_server(reload=True)
```

### How It Works

1. Edit a route file (e.g., `app/routes/hello/page.py`)
2. Save the file
3. Server automatically detects changes and reloads
4. Refresh your browser to see changes

### Example

Edit `app/routes/hello/page.py`:

```python
class HelloRoutes(RouteBase):
    def get(self):
        return {"message": "Hello, REROUTE!"}  # Changed from "Hello, World!"
```

Save the file. The server will reload:

```
INFO:     Detected file change, reloading...
INFO:     Started server process [PID]
```

Test the endpoint:

```bash
curl http://localhost:7376/hello
```

**Output:**
```json
{
  "message": "Hello, REROUTE!"
}
```

---

## Development vs Production

### Development Mode

```python
class DevConfig(Config):
    DEBUG = True
    AUTO_RELOAD = True
    LOG_LEVEL = "DEBUG"
```

**Features:**
- Detailed error messages
- Auto-reload enabled
- Debug logging
- Development-friendly security headers

### Production Mode

```python
class ProdConfig(Config):
    DEBUG = False
    AUTO_RELOAD = False
    LOG_LEVEL = "INFO"
```

**Features:**
- Minimal error messages (security)
- No auto-reload
- Info-level logging
- Strict security headers

---

## Stopping the Server

### Graceful Shutdown

Press `CTRL+C` in your terminal:

```
^CINFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [PID]
```

---

## Troubleshooting

### Server Won't Start

**Check:**
1. Virtual environment activated
2. Dependencies installed: `pip install -r requirements.txt`
3. No other server running on same port
4. Correct Python version (3.8+)

### Can't Access from Other Devices

**Check:**
1. `HOST = "0.0.0.0"` in config
2. Firewall allows connections
3. Devices on same network
4. Correct IP address

---

## Next Steps

Now you know how to run the development server!

**What's next:**
- [Understanding Routes](understanding-routes.md) - Learn how file-based routing works
- [Dynamic Routes](../easy/dynamic-routes.md) - Work with path parameters

---

## Summary

You learned:
- How to start the development server
- Configuration options (host, port, reload)
- Auto-reload for rapid development
- Development vs production modes

**Key takeaways:**
- Use `python main.py` to start the server
- Enable `AUTO_RELOAD = True` for development
- Use `0.0.0.0` to access from other devices
- Press `CTRL+C` to stop the server

Ready to understand how routing works? Continue to [Understanding Routes](understanding-routes.md)!
