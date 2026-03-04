# Installation Troubleshooting

This guide helps you troubleshoot and resolve common installation issues with REROUTE.

## Pre-Installation Checklist

Before installing REROUTE, ensure you have:

- [ ] Python 3.8 or higher installed
- [ ] pip or uv package manager installed
- [ ] Virtual environment created (recommended)
- [ ] Write permissions for the installation directory

---

## Python Version Issues

### Check Your Python Version

```bash
python --version
# or
python3 --version
```

**Required:** Python 3.8 or higher

### Issue: Python Too Old

**Symptoms:**
```
ERROR: Package 'reroute' requires a different Python version
```

**Solution:**

1. **Install Python 3.8+**
   - **Windows**: Download from [python.org](https://www.python.org/downloads/)
   - **macOS**: `brew install python@3.11`
   - **Linux**: `sudo apt-get install python3.11` (Ubuntu/Debian)

2. **Use Python Version Manager** (Recommended)
   - **pyenv** (macOS/Linux):
     ```bash
     brew install pyenv
     pyenv install 3.11
     pyenv global 3.11
     ```

---

## Package Manager Issues

### Issue: pip Not Found

**Symptoms:**
```
bash: pip: command not found
```

**Solution:**

```bash
python -m ensurepip --upgrade
```

### Issue: pip Too Old

**Symptoms:**
```
WARNING: You are using pip version X; upgrade to use newer features
```

**Solution:**

```bash
python -m pip install --upgrade pip
```

### Issue: Using uv (Recommended)

**Why uv?** uv is 10-100x faster than pip.

**Install uv:**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Use uv for installation:**
```bash
uv pip install reroute[fastapi]
```

---

## Virtual Environment Issues

### Why Use Virtual Environments?

Virtual environments isolate your project dependencies, preventing conflicts between projects.

### Creating a Virtual Environment

**Using venv (built-in):**
```bash
# Create
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Deactivate
deactivate
```

**Using uv (faster):**
```bash
# Create
uv venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

---

## Installation Errors

### Issue: Permission Denied

**Symptoms:**
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**Solution:**

**Option 1: Use virtual environment (Recommended)**
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
pip install reroute
```

**Option 2: Use --user flag**
```bash
pip install --user reroute
```

### Issue: Network/Proxy Issues

**Symptoms:**
```
ERROR: Could not find a version that satisfies the requirement reroute
```

**Solution:**

1. **Check internet connection:**
   ```bash
   ping pypi.org
   ```

2. **Use PyPI mirror:**
   ```bash
   pip install -i https://pypi.org/simple reroute
   ```

---

## Dependency Issues

### Issue: FastAPI Not Installing

**Symptoms:**
```
ERROR: No matching distribution found for fastapi
```

**Solution:**

Install with extras:
```bash
pip install reroute[fastapi]
```

Or install dependencies separately:
```bash
pip install fastapi uvicorn
pip install reroute
```

---

## OS-Specific Guides

### Windows

**Common Issues:**

1. **Path too long error:**
   ```powershell
   # Install to shorter path
   cd D:\
   mkdir projects
   cd projects
   pip install reroute
   ```

2. **Python not in PATH:**
   - Add Python to PATH during installation
   - Or use full path: `C:\Python311\python.exe -m pip install reroute`

### macOS

**Common Issues:**

1. **Xcode command line tools missing:**
   ```bash
   xcode-select --install
   ```

2. **Homebrew Python vs system Python:**
   ```bash
   # Use Homebrew Python
   brew install python@3.11
   /opt/homebrew/bin/python3 -m pip install reroute
   ```

### Linux (Ubuntu/Debian)

**Common Issues:**

1. **Missing build dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install python3-dev python3-pip build-essential
   ```

2. **System Python restrictions:**
   ```bash
   # Always use virtual environment
   python3 -m venv venv
   source venv/bin/activate
   pip install reroute
   ```

---

## Port Conflict Issues

### Issue: Port Already in Use

**Symptoms:**
```
OSError: [Errno 98] Address already in use
```

**Solution:**

**Option 1: Use different port**
```python
# config.py
class AppConfig(Config):
    PORT = 8080  # Change from default 7376
```

**Option 2: Kill process using port**

**Windows:**
```bash
netstat -ano | findstr :7376
taskkill /PID <process_id> /F
```

**macOS/Linux:**
```bash
lsof -ti:7376 | xargs kill -9
```

---

## Verification Steps

After installation, verify everything works:

### 1. Check Installation

```bash
python -c "import reroute; print(reroute.__version__)"
```

**Expected output:** Current version number

### 2. Check CLI

```bash
reroute --version
```

**Expected output:** Version information

### 3. Create Test Project

```bash
reroute init test-app --framework fastapi
cd test-app
python main.py
```

**Expected:** Server starts successfully

---

## Still Having Issues?

1. **Check Python path:**
   ```bash
   which python  # macOS/Linux
   where python  # Windows
   ```

2. **Clear pip cache:**
   ```bash
   pip cache purge
   ```

3. **Try fresh virtual environment:**
   ```bash
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install reroute
   ```

---

## Getting Help

If you're still stuck:

1. **Check existing issues:** [GitHub Issues](https://github.com/cbsajan/reroute/issues)
2. **Create minimal reproduction:** Isolate the problem
3. **Provide system information:**
   ```bash
   python --version
   pip --version
   uname -a  # macOS/Linux
   systeminfo  # Windows
   ```
4. **File new issue:** Include error messages and system information

---

## Quick Reference

| Problem | Solution |
|---------|----------|
| Python too old | Install Python 3.8+ |
| Permission denied | Use virtual environment |
| Network error | Check internet/proxy |
| Port in use | Change port or kill process |
| Import error | Reinstall in virtual environment |

---

## Next Steps

Once installation is successful:

1. [Quick Start Guide](../getting-started/quickstart.md) - Build your first API
2. [Hello World Tutorial](../tutorial/very-easy/hello-world.md) - Learn by doing
3. [User Guide](../guides/index.md) - Deep dive into features
