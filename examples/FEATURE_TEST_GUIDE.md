# REROUTE New Features - Testing Guide

## Quick Start

```bash
# 1. Create test app
cd D:/Workspace/Sajan/Python/mylib
reroute init test_app --framework fastapi
cd test_app

# 2. Install dependencies
pip install fastapi uvicorn websockets pyyaml

# 3. Copy example routes to test_app
# (Copy files from examples/ folder)

# 4. Run server
python main.py
# OR
uvicorn main:app --reload
```

## Feature Testing Checklist

### 1. WebSocket Support ✨

**Location**: `routes/ws/page.py`

**Test Steps**:
```bash
# Option 1: Browser Console
# 1. Open http://localhost:7376/docs
# 2. Open DevTools Console (F12)
# 3. Run:
const ws = new WebSocket('ws://localhost:7376/ws/chat');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.send('Hello!');

# Option 2: Python Test Client
python examples/test_websocket_client.py

# Option 3: websocat
websocat ws://localhost:7376/ws/chat
```

**Expected Results**:
- ✅ Connection established
- ✅ Welcome message received
- ✅ Messages broadcast to all clients
- ✅ Echo response received

---

### 2. OpenAPI Import 📥

**Test Import Command**:
```bash
# From test_app directory
cd test_app

# Import from spec file
reroute import openapi ../examples/openapi_test_spec.yaml \
  --output-dir routes \
  --models-dir models \
  --generate-tests

# Or with verbose output
reroute import openapi ../examples/openapi_test_spec.yaml \
  --output-dir routes \
  --verbose
```

**Expected Results**:
- ✅ Routes generated in `routes/products/page.py`
- ✅ Models generated in `models/openapi.py`
- ✅ Test files created (if --generate-tests)

**Test Generated Routes**:
```bash
# Access generated API
curl http://localhost:7376/products
curl http://localhost:7376/products/1
```

---

### 3. CRUD Operations 📝

**Location**: `routes/api/users/page.py`

**Test with HTTP File**:
```bash
# Use the examples/websocket_tests.http file
# Open in VS Code with REST Client extension
```

**Manual Testing**:
```bash
# List users
curl http://localhost:7376/api/users

# Create user
curl -X POST http://localhost:7376/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Charlie","email":"charlie@example.com","age":35}'

# Get user
curl http://localhost:7376/api/users/1

# Update user
curl -X PUT http://localhost:7376/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Charlie Updated"}'

# Delete user
curl -X DELETE http://localhost:7376/api/users/2
```

**Expected Results**:
- ✅ GET returns list of users
- ✅ POST creates new user
- ✅ GET /id returns specific user
- ✅ PUT updates user
- ✅ DELETE removes user

---

### 4. DB Models with OpenAPI Sync 🔄

**Test OpenAPI Sync**:
```bash
# Generate spec from existing routes
reroute import sync routes --output api-spec.yaml --format yaml

# Check generated spec
cat api-spec.yaml
```

**Expected Results**:
- ✅ OpenAPI spec generated
- ✅ All routes documented
- ✅ Schemas extracted

---

### 5. Interactive Documentation 📚

**Test Documentation**:
```bash
# Swagger UI
# Open: http://localhost:7376/docs

# Try it out:
# 1. Click on any endpoint
# 2. Click "Try it out"
# 3. Fill in parameters
# 4. Click "Execute"
```

**Expected Results**:
- ✅ API documentation displays
- ✅ All endpoints listed
- ✅ Try it out works
- ✅ Schemas shown correctly

---

## Performance Benchmarks

**Run Performance Tests**:
```bash
# Install apache bench
ab -n 1000 -c 10 http://localhost:7376/api/users

# Expected: < 100ms response time
# Expected: > 100 requests/second
```

---

## Full Test Script

```bash
#!/bin/bash
# test_all_features.sh

echo "🧪 REROUTE Feature Testing"
echo "=========================="

# 1. Start server
echo "📡 Starting server..."
cd test_app
python main.py &
SERVER_PID=$!
sleep 3

# 2. Test CRUD
echo "📝 Testing CRUD..."
curl -s http://localhost:7376/api/users | jq .

# 3. Test OpenAPI spec
echo "📋 Testing OpenAPI spec..."
curl -s http://localhost:7376/openapi.json | jq .

# 4. Test WebSocket (requires separate terminal)
echo "🔌 WebSocket: Run 'python examples/test_websocket_client.py'"

# 5. Cleanup
echo "🧹 Cleaning up..."
kill $SERVER_PID

echo "✅ Tests complete!"
```

---

## Troubleshooting

### WebSocket not connecting?
- Check if server is running
- Verify `routes/ws/page.py` exists
- Check firewall settings

### OpenAPI import fails?
- Verify spec file is valid YAML/JSON
- Check file path is correct
- Ensure `pyyaml` is installed

### Routes not accessible?
- Check `config.py` for `API_BASE_PATH`
- Verify route files are in correct folder structure
- Check file named `page.py`

---

## Test Results Template

```
Feature           | Status | Notes
------------------|--------|------------------
WebSocket         | [ ]    |
OpenAPI Import    | [ ]    |
CRUD Operations   | [ ]    |
Model Generation  | [ ]    |
API Documentation | [ ]    |
```

Fill this out after testing!
