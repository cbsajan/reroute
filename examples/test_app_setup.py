"""
Test REROUTE App - New Feature Testing

This app demonstrates all new features:
1. WebSocket support
2. OpenAPI import
3. DB Models with OpenAPI sync
4. CRUD operations

Setup:
    1. Create a new directory for testing
    2. Run: reroute init test_app --framework fastapi
    3. Copy the example files to your test_app
    4. Run: python main.py
"""

# ============================================
# SETUP INSTRUCTIONS
# ============================================
"""
Step 1: Create Test App
-----------------------
cd D:/Workspace/Sajan/Python/mylib
reroute init test_app --framework fastapi

Step 2: Navigate to App
------------------------
cd test_app

Step 3: Install Dependencies
----------------------------
pip install fastapi uvicorn websockets pyyaml

Step 4: Add the Example Routes
-------------------------------
Copy the route files from examples/test_app_routes/
to your test_app/routes/ directory

Step 5: Run the Server
----------------------
python main.py
    OR
uvicorn main:app --reload

Step 6: Test the Features
--------------------------
- WebSocket: ws://localhost:7376/ws/chat
- REST API: http://localhost:7376/api/users
- OpenAPI: http://localhost:7376/docs
"""

print(__doc__)
