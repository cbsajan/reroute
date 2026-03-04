# File-based Routing

Learn how REROUTE maps your folder structure to API routes.

## Basic Concept

REROUTE uses your filesystem to define routes, similar to Next.js:

```
app/routes/
├── user/
│   └── page.py        → /user
└── product/
    └── page.py        → /product
```

## Nested Routes

Create nested paths with folders:

```
app/routes/
└── api/
    └── v1/
        └── user/
            └── page.py  → /api/v1/user
```

## Dynamic Segments

Use brackets for dynamic route segments:

```
app/routes/
└── user/
    └── [id]/
        └── page.py      → /user/:id
```

## Route Files

Each `page.py` exports a class extending `RouteBase`:

```python
from reroute import RouteBase

class UserRoutes(RouteBase):
    def get(self):
        return {"users": []}
```

## Learn More

- [Class-based Routes](class-routes.md)
- [First Route Guide](../getting-started/first-route.md)
