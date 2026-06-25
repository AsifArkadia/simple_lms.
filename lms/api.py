from ninja_simple_jwt.auth.ninja_auth import HttpJwtAuth
from ninja_simple_jwt.auth.views.api import mobile_auth_router

# Auth dependency untuk endpoint yang membutuhkan JWT (Authorization: Bearer <token>)
apiAuth = HttpJwtAuth()

# Router bawaan ninja_simple_jwt: /auth/sign-in dan /auth/token-refresh
__all__ = ["apiAuth", "mobile_auth_router"]
