# Database Integration

Learn how to integrate databases with REROUTE using popular Python ORMs.

## Overview

REROUTE includes built-in database migration commands via `reroute db` and auto-generates Pydantic models via `reroute create model`. You can use any Python ORM or database library with REROUTE routes.

## Quick Start Workflow

!!! tip "Future Enhancement (v0.2.0)"
    `reroute init` will soon ask about database support during project setup and automatically configure the database connection, initialize migrations, and generate example models!

**Current Manual Workflow:**

```bash
# 1. Generate Pydantic model schemas
reroute create model --name User

# 2. Initialize database migrations
reroute db init

# 3. Create migration
reroute db migrate "create users table"

# 4. Apply migrations
reroute db upgrade

# 5. Generate CRUD route
reroute create crud --path /users --name User
```

## Supported ORMs

- **SQLAlchemy** - Most popular, works with any SQL database
- **Tortoise ORM** - Async-first ORM for FastAPI
- **Peewee** - Lightweight ORM
- **Raw SQL** - Direct database connections

---

## SQLAlchemy (Recommended)

### Quick Start with CLI

Use REROUTE CLI to generate models automatically:

```bash
# Generate User model with Pydantic schemas
reroute create model --name User

# This creates app/models/user.py with:
# - UserBase, UserCreate, UserUpdate, UserInDB, UserResponse
```

### Installation

```bash
pip install sqlalchemy
pip install psycopg2-binary  # For PostgreSQL
# OR
pip install mysql-connector-python  # For MySQL
```

### Database Setup

```python title="app/database.py"
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL
DATABASE_URL = "postgresql://user:password@localhost/dbname"
# For SQLite: DATABASE_URL = "sqlite:///./app.db"
# For MySQL: DATABASE_URL = "mysql+pymysql://user:password@localhost/dbname"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for database sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Define Models

```python title="app/models/user.py"
from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    is_active = Column(Boolean, default=True)
```

### Use in Routes

```python title="app/routes/users/page.py"
from reroute import RouteBase
from reroute.params import Query, Body
from app.database import SessionLocal
from app.models.user import User

class UsersRoutes(RouteBase):
    tag = "Users"

    def get(self, skip: int = Query(0), limit: int = Query(100)):
        """List all users with pagination"""
        db = SessionLocal()
        try:
            users = db.query(User).offset(skip).limit(limit).all()
            return {"users": [{"id": u.id, "email": u.email, "name": u.name} for u in users]}
        finally:
            db.close()

    def post(self, email: str = Body(...), name: str = Body(...)):
        """Create a new user"""
        db = SessionLocal()
        try:
            user = User(email=email, name=name)
            db.add(user)
            db.commit()
            db.refresh(user)
            return {"id": user.id, "email": user.email, "name": user.name}
        finally:
            db.close()
```

---

## Tortoise ORM (Async for FastAPI)

### Installation

```bash
pip install tortoise-orm
pip install aerich  # For migrations
```

### Database Setup

```python title="app/database.py"
from tortoise import Tortoise

async def init_db():
    await Tortoise.init(
        db_url="postgres://user:password@localhost/dbname",
        modules={"models": ["app.models"]}
    )
    await Tortoise.generate_schemas()

async def close_db():
    await Tortoise.close_connections()
```

### Define Models

```python title="app/models/user.py"
from tortoise import fields
from tortoise.models import Model

class User(Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=255, unique=True)
    name = fields.CharField(max_length=255)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "users"
```

### Use in Async Routes

```python title="app/routes/users/page.py"
from reroute import RouteBase
from reroute.params import Query, Body
from app.models.user import User

class UsersRoutes(RouteBase):
    tag = "Users"

    async def get(self, skip: int = Query(0), limit: int = Query(100)):
        """List all users"""
        users = await User.all().offset(skip).limit(limit)
        return {"users": [{"id": u.id, "email": u.email, "name": u.name} for u in users]}

    async def post(self, email: str = Body(...), name: str = Body(...)):
        """Create a new user"""
        user = await User.create(email=email, name=name)
        return {"id": user.id, "email": user.email, "name": user.name}
```

---

## Database Migrations

### Using REROUTE DB Commands

```bash
# Initialize migrations
reroute db init

# Create a migration
reroute db migrate "create users table"

# Apply migrations
reroute db upgrade

# Check current version
reroute db current

# View history
reroute db history

# Rollback
reroute db downgrade
```

### Using Alembic (SQLAlchemy)

```bash
# Install
pip install alembic

# Initialize
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add users table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Connection Pooling

### PostgreSQL with pg_pool

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "postgresql://user:password@localhost/dbname",
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True  # Verify connections before use
)
```

### Environment-based Configuration

```python title="app/config.py"
import os
from reroute import Config

class DatabaseConfig(Config):
    # Development
    DEV_DATABASE_URL = "sqlite:///./dev.db"

    # Production
    PROD_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/prod")

    # Get appropriate URL
    @classmethod
    def get_database_url(cls):
        return cls.PROD_DATABASE_URL if not cls.DEBUG else cls.DEV_DATABASE_URL
```

---

## Complete Example: CLI-Generated Database App

### Step-by-Step

```bash
# 1. Initialize project
reroute init my-blog --framework fastapi

# 2. Navigate to project
cd my-blog

# 3. Generate Post model
reroute create model --name Post

# 4. Generate User model
reroute create model --name User

# 5. Generate CRUD routes
reroute create crud --path /posts --name Post --http-test
reroute create crud --path /users --name User --http-test

# 6. Initialize database
reroute db init

# 7. Create migration
reroute db migrate "initial schema"

# 8. Apply migration
reroute db upgrade
```

### Generated Structure

```
my-blog/
├── app/
│   ├── models/
│   │   ├── post.py      # PostBase, PostCreate, PostUpdate, PostInDB, PostResponse
│   │   └── user.py      # UserBase, UserCreate, UserUpdate, UserInDB, UserResponse
│   └── routes/
│       ├── posts/
│       │   └── page.py  # Full CRUD: GET, POST, PUT, DELETE
│       └── users/
│           └── page.py  # Full CRUD operations
├── tests/
│   ├── posts.http      # HTTP test file
│   └── users.http      # HTTP test file
├── main.py             # FastAPI app
└── migrations/         # Database migrations
```

### Using Generated Models

The CLI-generated models work seamlessly with your routes:

```python title="app/routes/posts/page.py"
from reroute import RouteBase
from reroute.params import Body
from app.models.post import PostCreate, PostResponse
from app.database import get_db
from sqlalchemy.orm import Session

class PostsRoutes(RouteBase):
    tag = "Posts"

    def post(self, post: PostCreate = Body(...)):
        """Create a new post - using CLI-generated model"""
        db: Session = next(get_db())
        # Your database logic here
        return PostResponse(**post.model_dump())
```

---

## Best Practices

### 1. Use Connection Pooling

Always use connection pools in production to reuse database connections efficiently.

### 2. Handle Transactions

```python
def post(self, data: dict = Body(...)):
    db: Session = next(get_db())
    try:
        user = User(**data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
```

### 3. Use Environment Variables

Never hardcode database credentials. Use environment variables:

```python
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./default.db")
```

### 4. Implement Health Checks

```python title="app/routes/health/page.py"
from reroute import RouteBase
from app.database import engine

class HealthRoutes(RouteBase):
    tag = "Health"

    def get(self):
        """Health check with database connectivity"""
        try:
            # Test database connection
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            return {"status": "unhealthy", "database": str(e)}, 503
```

---

## Peewee ORM

Peewee is a lightweight ORM that's easy to learn and use.

### Installation

```bash
pip install peewee
```

### Setup

```python title="app/database.py"
from peewee import *

# SQLite database
db = SqliteDatabase('app.db')

# PostgreSQL example
# db = PostgresqlDatabase('mydb', user='postgres', password='secret', host='localhost', port=5432)

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    username = CharField(unique=True)
    email = CharField()
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

# Create tables
db.connect()
db.create_tables([User])
```

### Using in Routes

```python title="app/routes/users/page.py"
from reroute import RouteBase
from reroute.params import Body, Query
from app.database import User
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str

class UsersRoutes(RouteBase):
    tag = "Users"

    def get(self, skip: int = Query(0), limit: int = Query(100)):
        """Get all users with pagination"""
        users = list(User.select().offset(skip).limit(limit).dicts())
        return {"users": users, "total": User.select().count()}

    def post(self, user: UserCreate = Body()):
        """Create a new user"""
        new_user = User.create(**user.model_dump())
        return {"id": new_user.id, **user.model_dump()}

    def delete(self, user_id: int = Query(...)):
        """Delete a user by ID"""
        deleted = User.delete_by_id(user_id)
        if deleted:
            return {"deleted": True, "id": user_id}
        return {"error": "User not found"}, 404
```

### Transactions

```python
from peewee import Database

def post(self, user: UserCreate = Body()):
    """Create user with transaction"""
    with db.atomic():  # Automatic rollback on exception
        user = User.create(**user.model_dump())
        # Other operations...
        return {"id": user.id}
```

---

## Raw SQL

For maximum control, use raw SQL queries with a database driver.

### SQLite Example

```python title="app/database.py"
import sqlite3
from contextlib import contextmanager

DATABASE_PATH = 'app.db'

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize database schema"""
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
```

### Using in Routes

```python title="app/routes/users/page.py"
from reroute import RouteBase
from reroute.params import Body, Query
from app.database import get_db
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str

class UsersRoutes(RouteBase):
    tag = "Users"

    def get(self, skip: int = Query(0), limit: int = Query(100)):
        """Get all users with raw SQL"""
        with get_db() as conn:
            cursor = conn.execute(
                'SELECT * FROM users ORDER BY id LIMIT ? OFFSET ?',
                (limit, skip)
            )
            users = [dict(row) for row in cursor.fetchall()]

            count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]

            return {"users": users, "total": count}

    def post(self, user: UserCreate = Body()):
        """Create user with raw SQL"""
        with get_db() as conn:
            cursor = conn.execute(
                'INSERT INTO users (username, email) VALUES (?, ?)',
                (user.username, user.email)
            )
            conn.commit()
            return {"id": cursor.lastrowid, **user.model_dump()}

    def delete(self, user_id: int = Query(...)):
        """Delete user by ID"""
        with get_db() as conn:
            cursor = conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            if cursor.rowcount > 0:
                return {"deleted": True, "id": user_id}
            return {"error": "User not found"}, 404
```

### PostgreSQL Example with psycopg2

```python
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

DATABASE_URL = "postgresql://user:password@localhost/dbname"

@contextmanager
def get_db():
    """PostgreSQL connection context manager"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    else:
        conn.commit()
    finally:
        conn.close()

# Usage in routes (same pattern as SQLite example above)
```

---

## Next Steps

- [API Reference](../api/index.md) - Complete API documentation
- [Deployment](../deployment/production.md) - Production database setup
- [Configuration](../guides/configuration.md) - Database configuration options
