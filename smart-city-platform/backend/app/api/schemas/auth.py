"""
Request bodies for the auth router. Response shapes stay plain dicts,
matching the rest of the API (see system.py) -- no response schemas here.
"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str
