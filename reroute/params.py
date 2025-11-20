"""
REROUTE Parameter Injection

Provides FastAPI-style parameter injection for route handlers.
Use these in route method signatures to automatically extract and validate request data.
"""

from typing import Any, Optional, Type
from pydantic import BaseModel


class ParamBase:
    """Base class for all parameter types."""

    def __init__(
        self,
        default: Any = ...,
        *,
        description: Optional[str] = None,
        alias: Optional[str] = None,
        title: Optional[str] = None,
        ge: Optional[float] = None,
        le: Optional[float] = None,
        gt: Optional[float] = None,
        lt: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        regex: Optional[str] = None,
        example: Any = None,
        deprecated: bool = False,
    ):
        self.default = default
        self.description = description
        self.alias = alias
        self.title = title
        self.ge = ge
        self.le = le
        self.gt = gt
        self.lt = lt
        self.min_length = min_length
        self.max_length = max_length
        self.regex = regex
        self.example = example
        self.deprecated = deprecated
        self.required = default is ...


class Query(ParamBase):
    """
    Query parameter injection.

    Extracts values from URL query parameters (?key=value).

    Example:
        def get(self,
                limit: int = Query(10, description="Maximum results"),
                offset: int = Query(0, description="Skip results"),
                search: str = Query(None, description="Search term")):
            return {"limit": limit, "offset": offset}

    Usage:
        GET /users?limit=20&offset=10&search=john
        → limit=20, offset=10, search="john"
    """
    pass


class Path(ParamBase):
    """
    Path parameter injection.

    Extracts values from URL path segments.

    Example:
        def get(self,
                user_id: int = Path(..., description="User ID"),
                post_id: int = Path(..., description="Post ID")):
            return {"user_id": user_id, "post_id": post_id}

    Usage:
        GET /users/123/posts/456
        → user_id=123, post_id=456
    """
    pass


class Header(ParamBase):
    """
    Header parameter injection.

    Extracts values from HTTP headers.

    Example:
        def get(self,
                authorization: str = Header(..., description="Bearer token"),
                user_agent: str = Header(None, description="User agent")):
            return {"auth": authorization}

    Usage:
        GET /users
        Headers:
            Authorization: Bearer abc123
            User-Agent: Mozilla/5.0
        → authorization="Bearer abc123", user_agent="Mozilla/5.0"
    """
    pass


class Body(ParamBase):
    """
    Request body injection.

    Parses and validates JSON request body using Pydantic models.

    Example:
        from app.models.user import UserCreate

        def post(self,
                 user: UserCreate = Body(..., description="User data")):
            return {"user": user.dict()}

    Usage:
        POST /users
        Body: {"name": "John", "email": "john@example.com"}
        → user=UserCreate(name="John", email="john@example.com")
    """

    def __init__(
        self,
        default: Any = ...,
        *,
        embed: bool = False,
        media_type: str = "application/json",
        **kwargs
    ):
        super().__init__(default, **kwargs)
        self.embed = embed
        self.media_type = media_type


class Cookie(ParamBase):
    """
    Cookie parameter injection.

    Extracts values from HTTP cookies.

    Example:
        def get(self,
                session_id: str = Cookie(..., description="Session ID"),
                theme: str = Cookie("light", description="UI theme")):
            return {"session": session_id, "theme": theme}

    Usage:
        GET /profile
        Cookies: session_id=abc123; theme=dark
        → session_id="abc123", theme="dark"
    """
    pass


class Form(ParamBase):
    """
    Form data injection.

    Extracts values from form data (application/x-www-form-urlencoded).

    Example:
        def post(self,
                 username: str = Form(...),
                 password: str = Form(...)):
            return {"username": username}

    Usage:
        POST /login
        Content-Type: application/x-www-form-urlencoded
        Body: username=john&password=secret
        → username="john", password="secret"
    """
    pass


class File(ParamBase):
    """
    File upload injection.

    Handles file uploads (multipart/form-data).

    Example:
        from fastapi import UploadFile

        def post(self,
                 file: UploadFile = File(..., description="Upload file")):
            return {"filename": file.filename, "size": file.size}

    Usage:
        POST /upload
        Content-Type: multipart/form-data
        Body: [file data]
        → file=UploadFile(filename="image.jpg")
    """
    pass


# Aliases for convenience
Param = Query  # Backwards compatibility
Depends = ParamBase  # For dependency injection (future feature)


__all__ = [
    "Query",
    "Path",
    "Header",
    "Body",
    "Cookie",
    "Form",
    "File",
    "Param",
    "Depends",
]
